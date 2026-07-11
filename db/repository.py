import datetime
import sqlite3
from typing import Iterable, Optional

import config
from vision.band_rule import classify, infer_tie_band


def upsert_post(
    conn: sqlite3.Connection,
    *,
    fb_post_id: str,
    post_url: str,
    page_name: str = config.FB_PAGE_NAME,
    posted_at: Optional[datetime.datetime] = None,
    scraped_at: Optional[datetime.datetime] = None,
    image_url: Optional[str] = None,
    caption_raw: Optional[str] = None,
) -> int:
    """สร้าง/อัปเดตแถวโพสต์ตาม fb_post_id (idempotent) คืนค่า posts.id"""
    scraped_at = scraped_at or datetime.datetime.now(datetime.timezone.utc)
    conn.execute(
        """
        INSERT INTO posts (fb_post_id, post_url, page_name, posted_at, scraped_at, image_url, caption_raw)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(fb_post_id) DO UPDATE SET
            post_url = excluded.post_url,
            image_url = excluded.image_url,
            caption_raw = excluded.caption_raw
        """,
        (fb_post_id, post_url, page_name, posted_at, scraped_at, image_url, caption_raw),
    )
    conn.commit()
    row = conn.execute("SELECT id FROM posts WHERE fb_post_id = ?", (fb_post_id,)).fetchone()
    return row["id"]


def get_post_status(conn: sqlite3.Connection, fb_post_id: str) -> Optional[str]:
    row = conn.execute("SELECT status FROM posts WHERE fb_post_id = ?", (fb_post_id,)).fetchone()
    return row["status"] if row else None


def mark_post_status(
    conn: sqlite3.Connection,
    post_id: int,
    status: str,
    *,
    image_local_path: Optional[str] = None,
    image_sha256: Optional[str] = None,
    vision_raw_response: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    conn.execute(
        """
        UPDATE posts SET
            status = ?,
            image_local_path = COALESCE(?, image_local_path),
            image_sha256 = COALESCE(?, image_sha256),
            vision_raw_response = COALESCE(?, vision_raw_response),
            error_message = ?,
            vision_processed_at = CASE WHEN ? IN ('vision_processed', 'not_result_board')
                                        THEN CURRENT_TIMESTAMP ELSE vision_processed_at END
        WHERE id = ?
        """,
        (status, image_local_path, image_sha256, vision_raw_response, error_message, status, post_id),
    )
    conn.commit()


def find_post_by_image_sha256(conn: sqlite3.Connection, image_sha256: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM posts WHERE image_sha256 = ? AND status IN ('vision_processed', 'not_result_board')",
        (image_sha256,),
    ).fetchone()


def insert_event(
    conn: sqlite3.Connection,
    *,
    post_id: int,
    venue: Optional[str],
    event_date_raw: Optional[str],
    event_date: Optional[datetime.date],
) -> int:
    conn.execute(
        """
        INSERT INTO events (post_id, venue, event_date_raw, event_date)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            venue = excluded.venue,
            event_date_raw = excluded.event_date_raw,
            event_date = excluded.event_date
        """,
        (post_id, venue, event_date_raw, event_date),
    )
    conn.commit()
    row = conn.execute("SELECT id FROM events WHERE post_id = ?", (post_id,)).fetchone()
    return row["id"]


def insert_rocket_results(
    conn: sqlite3.Connection,
    *,
    event_id: int,
    rockets: Iterable[dict],
    base_hundred: int = config.TIE_BAND_BASE_HUNDRED,
) -> None:
    """rockets: list of dict ตามรูปแบบที่ได้จาก vision.schema.RocketResult.model_dump()

    คำนวณ tie band / computed_outcome / outcome_mismatch แบบ deterministic ที่นี่
    (ไม่ใช้ค่าที่ Claude Vision คำนวณเอง) แล้ว outcome สุดท้ายที่ใช้คิดสถิติจะยึดตาม
    outcome_icon (ไอคอนสีในภาพ) เสมอ ส่วน computed_outcome/outcome_mismatch มีไว้ตรวจสอบ (QA) เท่านั้น
    """
    for r in rockets:
        metric_a = r.get("metric_a")
        metric_b = r.get("metric_b")
        achieved_value = r.get("achieved_value")
        outcome_icon = r["outcome_icon"]

        tie_band_low = tie_band_high = computed_outcome = None
        outcome_mismatch = False
        if metric_a is not None and metric_b is not None:
            # เลือก base หลักร้อยที่ทำให้แถบราคาตรงกับไอคอนสีในภาพ (ไอคอน = ความจริง)
            _, tie_band_low, tie_band_high = infer_tie_band(
                metric_a, metric_b, achieved_value, outcome_icon, base_hundred
            )
            computed_outcome = classify(achieved_value, tie_band_low, tie_band_high)
            outcome_mismatch = computed_outcome != outcome_icon

        conn.execute(
            """
            INSERT INTO rocket_results (
                event_id, rocket_name_raw, rocket_name_normalized,
                metric_a, metric_b, metric_category_text,
                achieved_raw, achieved_value,
                tie_band_low, tie_band_high, computed_outcome,
                outcome_icon, outcome, outcome_mismatch, is_champion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                r["rocket_name"],
                r["rocket_name"].strip(),
                metric_a,
                metric_b,
                r.get("metric_category_text"),
                r.get("achieved_raw"),
                achieved_value,
                tie_band_low,
                tie_band_high,
                computed_outcome,
                outcome_icon,
                outcome_icon,
                outcome_mismatch,
                bool(r.get("is_champion", False)),
            ),
        )
    conn.commit()


def get_rocket_stats(conn: sqlite3.Connection, rocket_name: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM v_rocket_stats WHERE rocket_name = ?", (rocket_name.strip(),)
    ).fetchone()


def get_all_rocket_stats(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM v_rocket_stats ORDER BY win_rate DESC, races DESC").fetchall()


def get_rocket_score_stats(conn: sqlite3.Connection, rocket_name: str) -> Optional[sqlite3.Row]:
    """สถิติ 'คะแนน' (achieved_value) ของบั้งไฟ: เฉลี่ย/สูงสุด/ต่ำสุด และเฉลี่ย 5 นัดล่าสุด
    คืน None ถ้าไม่มีค่า achieved_value เลย"""
    name = rocket_name.strip()
    overall = conn.execute(
        "SELECT COUNT(achieved_value) n, AVG(achieved_value) avg_score, "
        "MAX(achieved_value) top_score, MIN(achieved_value) low_score "
        "FROM rocket_results WHERE rocket_name_normalized = ? AND achieved_value IS NOT NULL",
        (name,),
    ).fetchone()
    if overall is None or overall["n"] == 0:
        return None
    last5 = conn.execute(
        "SELECT AVG(achieved_value) last5_avg FROM ("
        "  SELECT rr.achieved_value FROM rocket_results rr JOIN events e ON rr.event_id = e.id"
        "  WHERE rr.rocket_name_normalized = ? AND rr.achieved_value IS NOT NULL"
        "  ORDER BY e.event_date DESC, rr.id DESC LIMIT 5"
        ")",
        (name,),
    ).fetchone()
    return {
        "avg_score": overall["avg_score"],
        "top_score": overall["top_score"],
        "low_score": overall["low_score"],
        "last5_avg": last5["last5_avg"] if last5 else None,
    }


# แปลงผลการแข่ง (outcome) เป็นคำไทย — ต่อท้ายคะแนนใน "3 นัดล่าสุด" เช่น 430(ผ่าน)
_OUTCOME_TH = {"win": "ผ่าน", "loss": "ไม่ผ่าน", "tie": "เสมอ"}


def get_all_rocket_score_summary(conn: sqlite3.Connection) -> dict[str, dict]:
    """สรุป 'คะแนน' ของบั้งไฟทุกตัวในคิวรีเดียว (ไว้โชว์หน้า Dashboard)
    คืน dict: rocket_name_normalized -> {'avg_score': float|None, 'last3': '430(ผ่าน), 360(เสมอ)'|None}
    """
    summary: dict[str, dict] = {}
    for r in conn.execute(
        "SELECT rocket_name_normalized nm, AVG(achieved_value) avg_score "
        "FROM rocket_results WHERE achieved_value IS NOT NULL "
        "GROUP BY rocket_name_normalized"
    ):
        summary[r["nm"]] = {"avg_score": r["avg_score"], "last3": None}

    last: dict[str, list] = {}
    for r in conn.execute(
        "SELECT nm, av, oc FROM ("
        "  SELECT rr.rocket_name_normalized nm, rr.achieved_value av, rr.outcome oc, "
        "         ROW_NUMBER() OVER (PARTITION BY rr.rocket_name_normalized "
        "                            ORDER BY e.event_date DESC, rr.id DESC) rn "
        "  FROM rocket_results rr JOIN events e ON rr.event_id = e.id "
        "  WHERE rr.achieved_value IS NOT NULL"
        ") WHERE rn <= 3 ORDER BY nm, rn"
    ):
        last.setdefault(r["nm"], []).append(f"{r['av']}({_OUTCOME_TH.get(r['oc'], r['oc'])})")
    for nm, results in last.items():
        if nm in summary:
            summary[nm]["last3"] = ", ".join(results)
    return summary


def get_rocket_last_results(
    conn: sqlite3.Connection, rocket_name: str, limit: int = 5
) -> list[sqlite3.Row]:
    """ผลจริง N นัดล่าสุด (ใหม่ไปเก่า) — คืน achieved_value + outcome ต่อแถว"""
    return conn.execute(
        "SELECT rr.achieved_value, rr.outcome FROM rocket_results rr "
        "JOIN events e ON rr.event_id = e.id "
        "WHERE rr.rocket_name_normalized = ? AND rr.achieved_value IS NOT NULL "
        "ORDER BY e.event_date DESC, rr.id DESC LIMIT ?",
        (rocket_name.strip(), limit),
    ).fetchall()


def get_mismatched_results(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM rocket_results WHERE outcome_mismatch = 1 ORDER BY created_at DESC"
    ).fetchall()
