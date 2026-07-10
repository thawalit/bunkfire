import datetime
import hashlib
import subprocess
import sys
from pathlib import Path

import click
import requests

import config
from db.connection import get_connection, init_db
from db.repository import (
    find_post_by_image_sha256,
    get_post_status,
    insert_event,
    insert_rocket_results,
    mark_post_status,
    upsert_post,
)
from scraper.auth import SessionExpiredError
from scraper.browser import headless_context
from scraper.page_scraper import scroll_and_collect
from scraper.prefilter import PostCandidate, is_candidate
from scraper.rate_limit import PerRunCap
from vision.date_utils import parse_thai_short_date
from vision.extractor import extract


@click.group()
def cli():
    """คำสั่งจัดการเก็บสถิติบั้งไฟจากเพจ Facebook BANHAOSTATION"""


@cli.command()
def login():
    """เปิด browser แบบ headful ให้ login Facebook ครั้งเดียว แล้วบันทึก session"""
    subprocess.run([sys.executable, str(Path(__file__).parent / "scripts" / "one_time_login.py")])


@cli.command()
@click.option("--limit", default=config.MAX_POSTS_PER_RUN, help="จำนวนโพสต์สูงสุดต่อรอบ")
@click.option("--since-days", default=config.BACKFILL_DAYS, help="ดึงย้อนหลังกี่วัน")
@click.option("--dry-run", is_flag=True, help="แค่แสดงผลที่จะดึง ไม่เขียน DB")
def scrape(limit, since_days, dry_run):
    """ดึงรายการโพสต์จากเพจ Facebook แล้วบันทึกลง DB (สถานะ pending/candidate)"""
    conn = get_connection()
    init_db(conn)
    cap = PerRunCap(max_count=limit)
    started_at = datetime.datetime.now(datetime.timezone.utc)
    posts_scanned = posts_new = 0

    try:
        with headless_context() as context:
            for scraped in scroll_and_collect(context, since_days=since_days, max_posts=limit):
                if not cap.can_continue():
                    break
                posts_scanned += 1
                candidate = PostCandidate(
                    fb_post_id=scraped.fb_post_id,
                    post_url=scraped.post_url,
                    image_url=scraped.image_url,
                    caption_raw=scraped.caption_raw,
                    has_single_photo=scraped.has_single_photo,
                )
                if not is_candidate(candidate):
                    continue

                if dry_run:
                    click.echo(f"[dry-run] {scraped.fb_post_id} {scraped.post_url}")
                    cap.record()
                    continue

                existing_status = get_post_status(conn, scraped.fb_post_id)
                if existing_status in ("vision_processed", "not_result_board"):
                    continue

                upsert_post(
                    conn,
                    fb_post_id=scraped.fb_post_id,
                    post_url=scraped.post_url,
                    image_url=scraped.image_url,
                    caption_raw=scraped.caption_raw,
                )
                posts_new += 1
                cap.record()
    except SessionExpiredError as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(1)

    if not dry_run:
        conn.execute(
            "INSERT INTO scrape_runs (started_at, finished_at, posts_scanned, posts_new) VALUES (?, ?, ?, ?)",
            (started_at, datetime.datetime.now(datetime.timezone.utc), posts_scanned, posts_new),
        )
        conn.commit()
    click.echo(f"scanned={posts_scanned} new={posts_new} dry_run={dry_run}")


@cli.command("extract-pending")
def extract_pending():
    """เรียก Claude Vision สกัดข้อมูลจากทุกโพสต์ที่ยังไม่ประมวลผล"""
    conn = get_connection()
    init_db(conn)
    pending = conn.execute("SELECT * FROM posts WHERE status = 'pending'").fetchall()
    click.echo(f"พบ {len(pending)} โพสต์ที่รอประมวลผล")

    for post in pending:
        if not post["image_url"]:
            mark_post_status(conn, post["id"], "error", error_message="ไม่มี image_url")
            continue

        try:
            resp = requests.get(post["image_url"], timeout=30)
            resp.raise_for_status()
            image_bytes = resp.content
        except Exception as e:
            mark_post_status(conn, post["id"], "error", error_message=str(e))
            continue

        image_sha256 = hashlib.sha256(image_bytes).hexdigest()
        cached = find_post_by_image_sha256(conn, image_sha256)
        if cached is not None:
            mark_post_status(conn, post["id"], "not_result_board", image_sha256=image_sha256)
            click.echo(f"post {post['id']}: รูปซ้ำกับ post {cached['id']} ข้าม Vision call")
            continue

        image_dir = config.IMAGES_DIR
        image_dir.mkdir(parents=True, exist_ok=True)
        image_path = image_dir / f"{post['fb_post_id']}.jpg"
        image_path.write_bytes(image_bytes)

        try:
            result = extract(image_bytes)
        except Exception as e:
            mark_post_status(conn, post["id"], "error", image_sha256=image_sha256, error_message=str(e))
            continue

        raw_json = result.model_dump_json()

        if not result.is_result_board:
            mark_post_status(
                conn, post["id"], "not_result_board",
                image_local_path=str(image_path), image_sha256=image_sha256, vision_raw_response=raw_json,
            )
            continue

        event_date = None
        if result.event_date_day and result.event_date_month_th and result.event_date_year_be:
            event_date = parse_thai_short_date(
                result.event_date_day, result.event_date_month_th, result.event_date_year_be
            )
        event_date_raw = None
        if result.event_date_day and result.event_date_month_th and result.event_date_year_be:
            event_date_raw = f"{result.event_date_day} {result.event_date_month_th} {result.event_date_year_be}"

        event_id = insert_event(
            conn, post_id=post["id"], venue=result.event_venue,
            event_date_raw=event_date_raw, event_date=event_date,
        )
        insert_rocket_results(conn, event_id=event_id, rockets=[r.model_dump() for r in result.rockets])
        mark_post_status(
            conn, post["id"], "vision_processed",
            image_local_path=str(image_path), image_sha256=image_sha256, vision_raw_response=raw_json,
        )
        click.echo(f"post {post['id']}: สกัดสำเร็จ {len(result.rockets)} แถว")


if __name__ == "__main__":
    cli()
