import datetime

from vision.date_utils import be_year_to_ce, parse_thai_short_date


def test_be_year_to_ce_two_digit():
    assert be_year_to_ce(69) == 2026


def test_be_year_to_ce_full():
    assert be_year_to_ce(2569) == 2026


def test_sample_dates_from_images():
    assert parse_thai_short_date(7, "ก.ค.", 69) == datetime.date(2026, 7, 7)
    assert parse_thai_short_date(8, "ก.ค.", 69) == datetime.date(2026, 7, 8)
    assert parse_thai_short_date(6, "ก.ค.", 69) == datetime.date(2026, 7, 6)


def test_various_months():
    assert parse_thai_short_date(1, "ม.ค.", 69) == datetime.date(2026, 1, 1)
    assert parse_thai_short_date(15, "ธ.ค.", 68) == datetime.date(2025, 12, 15)


def test_unknown_month_returns_none():
    assert parse_thai_short_date(1, "xx.", 69) is None


def test_invalid_day_returns_none():
    assert parse_thai_short_date(31, "ก.พ.", 69) is None
