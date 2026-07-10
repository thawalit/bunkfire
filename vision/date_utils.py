"""แปลงวันที่แบบย่อภาษาไทย (พ.ศ.) ที่พิมพ์บนป้ายผลการแข่งขัน เป็นวันที่ ค.ศ. แบบ deterministic

ตัวอย่าง: "7 ก.ค. 69" -> date(2026, 7, 7)

ทำแบบ lookup table ล้วนๆ ไม่ให้ Claude Vision คำนวณวันที่เอง เพราะ LLM ไม่แม่นยำ
เรื่องเลขคำนวณปฏิทิน
"""

import datetime
from typing import Optional

THAI_MONTH_ABBR_TO_NUM = {
    "ม.ค.": 1,
    "ก.พ.": 2,
    "มี.ค.": 3,
    "เม.ย.": 4,
    "พ.ค.": 5,
    "มิ.ย.": 6,
    "ก.ค.": 7,
    "ส.ค.": 8,
    "ก.ย.": 9,
    "ต.ค.": 10,
    "พ.ย.": 11,
    "ธ.ค.": 12,
}

BE_TO_CE_OFFSET = 543


def be_year_to_ce(year_be: int) -> int:
    """รับปี พ.ศ. แบบ 2 หลัก (เช่น 69) หรือเต็ม (เช่น 2569) แล้วคืนปี ค.ศ. เต็ม

    ปี พ.ศ. 2 หลัก จะเติม 2500 นำหน้าเสมอ (ครอบคลุมช่วง พ.ศ. 2500-2599 ซึ่งเป็นช่วงเวลาที่ใช้งานจริง)
    """
    if year_be < 100:
        year_be_full = 2500 + year_be
    else:
        year_be_full = year_be
    return year_be_full - BE_TO_CE_OFFSET


def parse_thai_short_date(day: int, month_th: str, year_be: int) -> Optional[datetime.date]:
    month_num = THAI_MONTH_ABBR_TO_NUM.get(month_th.strip())
    if month_num is None:
        return None
    year_ce = be_year_to_ce(year_be)
    try:
        return datetime.date(year_ce, month_num, day)
    except ValueError:
        return None
