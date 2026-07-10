import pytest

from db.connection import get_connection, init_db
from db.repository import insert_event, insert_rocket_results, upsert_post
from stats.scoring import score_rocket, score_rocket_list


@pytest.fixture()
def conn():
    c = get_connection(":memory:")
    init_db(c)
    post_id = upsert_post(c, fb_post_id="p1", post_url="https://x/p1")
    event_id = insert_event(c, post_id=post_id, venue="v", event_date_raw="d", event_date=None)
    rockets = [
        {"rocket_name": "เสมียนศิลป์", "metric_a": None, "metric_b": None, "achieved_raw": "1",
         "achieved_value": 1, "outcome_icon": "win", "is_champion": False},
        {"rocket_name": "เสมียนศิลป์", "metric_a": None, "metric_b": None, "achieved_raw": "1",
         "achieved_value": 1, "outcome_icon": "win", "is_champion": False},
        {"rocket_name": "เสมียนศิลป์", "metric_a": None, "metric_b": None, "achieved_raw": "1",
         "achieved_value": 1, "outcome_icon": "loss", "is_champion": False},
        {"rocket_name": "ส.ไพศาล", "metric_a": None, "metric_b": None, "achieved_raw": "1",
         "achieved_value": 1, "outcome_icon": "loss", "is_champion": False},
    ]
    insert_rocket_results(c, event_id=event_id, rockets=rockets)
    yield c
    c.close()


def test_found_rocket_above_threshold_passes(conn):
    result = score_rocket("เสมียนศิลป์", conn)
    assert result.found is True
    assert result.races == 3
    assert result.wins == 2
    assert result.verdict == "ผ่าน"
    assert result.score == pytest.approx(66.7, abs=0.1)


def test_found_rocket_below_threshold_fails(conn):
    result = score_rocket("ส.ไพศาล", conn)
    assert result.found is True
    assert result.win_rate == 0.0
    assert result.verdict == "ไม่ผ่าน"


def test_unknown_rocket_is_no_data_not_fail(conn):
    result = score_rocket("ไม่มีตัวนี้แน่นอน", conn)
    assert result.found is False
    assert result.verdict == "ไม่มีข้อมูล"
    assert result.score is None


def test_exact_match_whitespace_trim_only(conn):
    # ชื่อที่ขึ้นต้น/ลงท้ายด้วยช่องว่างต้อง match ได้ (trim), แต่ไม่ fuzzy กับชื่อที่ไม่ตรงกันเป๊ะ
    assert score_rocket("  เสมียนศิลป์  ", conn).found is True
    assert score_rocket("เสมียน", conn).found is False


def test_threshold_boundary_exact_50_percent_passes(conn):
    result = score_rocket("เสมียนศิลป์", conn, threshold=2 / 3)
    assert result.verdict == "ผ่าน"


def test_score_rocket_list_preserves_order_and_duplicates(conn):
    names = ["ส.ไพศาล", "เสมียนศิลป์", "ส.ไพศาล", "ไม่มีตัวนี้"]
    results = score_rocket_list(names, conn)
    assert [r.name for r in results] == names
    assert [r.verdict for r in results] == ["ไม่ผ่าน", "ผ่าน", "ไม่ผ่าน", "ไม่มีข้อมูล"]
