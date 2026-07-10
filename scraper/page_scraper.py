"""ดึงรายการโพสต์รูปภาพจากแท็บ Photos ของหน้าเพจ Facebook ด้วย Playwright

วิธีการ: หน้าไทม์ไลน์ของเพจ FB ปัจจุบันเรนเดอร์เป็น [role=article] ที่ปนคอมเมนต์/
featured post และนับรูปไม่คงที่ จึงเปลี่ยนมาใช้แท็บ Photos (/photos_by) ที่สะอาดกว่า:
grid ของรูปเพจ แต่ละรูปมี fbid ตัวเลข → เก็บ fbid ทั้งหมดก่อน แล้วเข้าหน้ารูปแต่ละอัน
(/photo/?fbid=...) เพื่อดึง URL รูปเต็มความละเอียด (thumbnail ใน grid เล็กเกินไปสำหรับ Vision)

หมายเหตุสำคัญ: Facebook เปลี่ยน DOM/selector บ่อยและมักบล็อก/ตรวจจับ automation
ตรวจสอบด้วย `python cli.py scrape --dry-run --limit 5` (ดู README) ก่อนใช้งานจริงเสมอ
"""

import datetime
import re
from dataclasses import dataclass
from typing import Iterator, Optional

from playwright.sync_api import BrowserContext, Page

import config
from scraper.browser import is_login_redirect
from scraper.auth import SessionExpiredError
from scraper.rate_limit import jittered_sleep

# แต่ละรูปในแท็บ Photos ของเพจมีลิงก์ /photo/?fbid=<เลข> หรือ /photo.php?fbid=<เลข>
FBID_PATTERN = re.compile(r"[?&]fbid=(\d+)")


@dataclass
class ScrapedPost:
    fb_post_id: str
    post_url: str
    image_url: Optional[str]
    caption_raw: Optional[str]
    has_single_photo: bool
    posted_at: Optional[datetime.datetime]


def _extract_fbid(url: str) -> Optional[str]:
    match = FBID_PATTERN.search(url)
    return match.group(1) if match else None


def _largest_photo_src(page: Page) -> Optional[str]:
    """หา URL รูปหลัก (พื้นที่ใหญ่สุด) บนหน้ารูป — โพสต์รูปของ FB ใช้ path t39.30808"""
    imgs = page.locator("img[src*='scontent']")
    best_src = None
    best_area = 0.0
    for i in range(imgs.count()):
        img = imgs.nth(i)
        src = img.get_attribute("src")
        if not src:
            continue
        try:
            w, h = img.evaluate("e => [e.naturalWidth, e.naturalHeight]")
        except Exception:
            w = h = 0
        area = float(w) * float(h)
        if area > best_area:
            best_area = area
            best_src = src
    return best_src


def _collect_photo_ids(page: Page, max_posts: int, max_idle_scrolls: int) -> list[str]:
    """เลื่อน grid ของแท็บ Photos แล้วเก็บ fbid เรียงจากใหม่ไปเก่าจนครบ max_posts"""
    seen: set[str] = set()
    ordered: list[str] = []
    idle_scrolls = 0

    while len(ordered) < max_posts and idle_scrolls < max_idle_scrolls:
        links = page.locator("a[href*='fbid=']").all()
        new_this_scroll = 0
        for link in links:
            href = link.get_attribute("href")
            if not href:
                continue
            fbid = _extract_fbid(href)
            if not fbid or fbid in seen:
                continue
            seen.add(fbid)
            ordered.append(fbid)
            new_this_scroll += 1
            if len(ordered) >= max_posts:
                break

        idle_scrolls = 0 if new_this_scroll > 0 else idle_scrolls + 1
        page.mouse.wheel(0, 2000)
        jittered_sleep()

    return ordered


def scroll_and_collect(
    context: BrowserContext,
    page_url: str = config.FB_PAGE_URL,
    max_posts: int = config.MAX_POSTS_PER_RUN,
    since_days: int = config.BACKFILL_DAYS,
    max_idle_scrolls: int = 5,
) -> Iterator[ScrapedPost]:
    """เก็บ fbid จาก grid ของแท็บ Photos แล้ว yield โพสต์รูปทีละอัน (ดึง URL รูปเต็มจากหน้ารูป)

    since_days ถูกส่งผ่านมาเพื่อความเข้ากันได้ของ signature แต่แท็บ Photos ไม่แสดงวันที่
    บน grid — การจำกัดช่วงเวลาทำผ่าน max_posts (จำนวนรูปล่าสุด) แทน
    """
    photos_url = page_url.rstrip("/") + "/photos_by"
    page: Page = context.new_page()
    page.goto(photos_url, wait_until="domcontentloaded")

    if is_login_redirect(context, page.url):
        raise SessionExpiredError(
            f"ถูก redirect ไปหน้า login/checkpoint ที่ {page.url} — session หมดอายุ "
            "รัน `python scripts/one_time_login.py` ใหม่"
        )

    page.wait_for_timeout(3000)
    fbids = _collect_photo_ids(page, max_posts=max_posts, max_idle_scrolls=max_idle_scrolls)

    for fbid in fbids:
        photo_url = f"https://www.facebook.com/photo/?fbid={fbid}"
        page.goto(photo_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        if is_login_redirect(context, page.url):
            raise SessionExpiredError(
                f"ถูก redirect ไปหน้า login/checkpoint ที่ {page.url} — session หมดอายุ "
                "รัน `python scripts/one_time_login.py` ใหม่"
            )

        image_url = _largest_photo_src(page)

        yield ScrapedPost(
            fb_post_id=fbid,
            post_url=photo_url,
            image_url=image_url,
            caption_raw=None,  # ข้อมูลผลการแข่งขันอยู่ในรูป — caption เป็นเพียงตัวช่วยจัดลำดับ (ไม่ใช้คัดออก)
            has_single_photo=True,  # แต่ละรายการในแท็บ Photos คือรูปเดี่ยวเสมอ
            posted_at=None,
        )
        jittered_sleep()

    page.close()
