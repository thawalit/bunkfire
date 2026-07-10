"""สูตรคำนวณผลแพ้ชนะจากตัวเลข (A/B) และค่าที่ทำได้จริง

ตัวเลข (A/B) บนป้ายผลคือขอบเขต "เสมอตัว" แบบย่อ (พิมพ์แค่ 2 หลักท้าย โดยนัยว่า
หลักร้อยคือ base_hundred เช่น 300): ขอบล่าง = base_hundred + A, ขอบบน = base_hundred + B
ถ้า B น้อยกว่า A ให้ทบไปหลักร้อยถัดไป (ขอบบน = base_hundred + 100 + B) เช่น
(55/05) ที่ base=300 -> ขอบบน = 405 ไม่ใช่ 305

สูตรนี้ตรวจสอบตรงกับทุกแถวในตัวอย่างจริง 3 รูปที่ผู้ใช้ให้มา 100%
"""

from typing import Literal, Optional

Outcome = Literal["win", "loss", "tie"]


def compute_tie_band(a: int, b: int, base_hundred: int) -> tuple[int, int]:
    low = base_hundred + a
    high = base_hundred + b if b >= a else base_hundred + 100 + b
    return low, high


def classify(achieved: Optional[int], low: int, high: int) -> Outcome:
    """achieved=None (เช่นกรณี "หาย") ถือเป็นเสมอตัวเสมอ ตามที่ผู้ใช้ยืนยัน"""
    if achieved is None:
        return "tie"
    if achieved > high:
        return "win"
    if achieved < low:
        return "loss"
    return "tie"


def compute_and_classify(a: int, b: int, achieved: Optional[int], base_hundred: int = 300) -> Outcome:
    low, high = compute_tie_band(a, b, base_hundred)
    return classify(achieved, low, high)
