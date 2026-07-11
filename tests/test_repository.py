import datetime

import pytest

from db.connection import get_connection, init_db
from db.repository import (
    get_all_rocket_stats,
    get_mismatched_results,
    get_post_status,
    get_rocket_stats,
    insert_event,
    insert_rocket_results,
    mark_post_status,
    upsert_post,
)


@pytest.fixture()
def conn():
    c = get_connection(":memory:")
    init_db(c)
    yield c
    c.close()


def test_upsert_post_is_idempotent(conn):
    id1 = upsert_post(conn, fb_post_id="abc123", post_url="https://facebook.com/x/posts/abc123")
    id2 = upsert_post(conn, fb_post_id="abc123", post_url="https://facebook.com/x/posts/abc123")
    assert id1 == id2
    count = conn.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"]
    assert count == 1


def test_mark_post_status_and_lookup(conn):
    post_id = upsert_post(conn, fb_post_id="p1", post_url="https://x/p1")
    assert get_post_status(conn, "p1") == "pending"
    mark_post_status(conn, post_id, "vision_processed", image_sha256="deadbeef")
    assert get_post_status(conn, "p1") == "vision_processed"


def test_insert_rocket_results_computes_band_and_flags_mismatch(conn):
    post_id = upsert_post(conn, fb_post_id="p2", post_url="https://x/p2")
    event_id = insert_event(
        conn, post_id=post_id, venue="สร้างแป้น", event_date_raw="7 ก.ค. 69",
        event_date=datetime.date(2026, 7, 7),
    )
    rockets = [
        {
            "rocket_name": "เสมียนศิลป์",
            "metric_a": 30, "metric_b": 55,
            "achieved_raw": "430", "achieved_value": 430,
            "outcome_icon": "win", "is_champion": False,
        },
        {
            # จงใจให้ icon ขัดกับตัวเลขแบบที่ไม่มีหลักร้อยไหนอธิบายได้ (แถบกว้างแค่ 5 คือ x80-x85
            # ไม่มี base ที่ทำให้ 430 อยู่ในแถบ) เพื่อทดสอบว่า outcome_mismatch ยังจับได้
            "rocket_name": "ตัวทดสอบ",
            "metric_a": 80, "metric_b": 85,
            "achieved_raw": "430", "achieved_value": 430,
            "outcome_icon": "tie", "is_champion": False,
        },
        {
            "rocket_name": "พงษ์เจริญ",
            "metric_a": 30, "metric_b": 60,
            "achieved_raw": "หาย", "achieved_value": None,
            "outcome_icon": "tie", "is_champion": False,
        },
    ]
    insert_rocket_results(conn, event_id=event_id, rockets=rockets)

    stats = get_rocket_stats(conn, "เสมียนศิลป์")
    assert stats["races"] == 1
    assert stats["wins"] == 1
    assert stats["win_rate"] == 1.0

    mismatches = get_mismatched_results(conn)
    assert len(mismatches) == 1
    assert mismatches[0]["rocket_name_raw"] == "ตัวทดสอบ"
    assert mismatches[0]["outcome"] == "tie"  # ยึดตาม icon เสมอ แม้ตัวเลขจะขัดกัน


def test_win_rate_counts_ties_as_non_win(conn):
    post_id = upsert_post(conn, fb_post_id="p3", post_url="https://x/p3")
    event_id = insert_event(conn, post_id=post_id, venue="v", event_date_raw="d", event_date=None)
    rockets = [
        {"rocket_name": "นก", "metric_a": None, "metric_b": None, "achieved_raw": "300",
         "achieved_value": 300, "outcome_icon": "win", "is_champion": False},
        {"rocket_name": "นก", "metric_a": None, "metric_b": None, "achieved_raw": "หาย",
         "achieved_value": None, "outcome_icon": "tie", "is_champion": False},
        {"rocket_name": "นก", "metric_a": None, "metric_b": None, "achieved_raw": "100",
         "achieved_value": 100, "outcome_icon": "loss", "is_champion": False},
    ]
    insert_rocket_results(conn, event_id=event_id, rockets=rockets)
    stats = get_rocket_stats(conn, "นก")
    assert stats["races"] == 3
    assert stats["wins"] == 1
    assert stats["ties"] == 1
    assert stats["losses"] == 1
    assert stats["win_rate"] == pytest.approx(1 / 3, rel=1e-3)


def test_get_all_rocket_stats_orders_by_win_rate(conn):
    post_id = upsert_post(conn, fb_post_id="p4", post_url="https://x/p4")
    event_id = insert_event(conn, post_id=post_id, venue="v", event_date_raw="d", event_date=None)
    rockets = [
        {"rocket_name": "A", "metric_a": None, "metric_b": None, "achieved_raw": "1",
         "achieved_value": 1, "outcome_icon": "loss", "is_champion": False},
        {"rocket_name": "B", "metric_a": None, "metric_b": None, "achieved_raw": "1",
         "achieved_value": 1, "outcome_icon": "win", "is_champion": True},
    ]
    insert_rocket_results(conn, event_id=event_id, rockets=rockets)
    all_stats = get_all_rocket_stats(conn)
    assert all_stats[0]["rocket_name"] == "B"
