"""สูตรคำนวณผลแพ้ชนะจากตัวเลข (A/B) และค่าที่ทำได้จริง

ตัวเลข (A/B) บนป้ายผลคือขอบเขต "เสมอตัว": ขอบล่าง = base_hundred + A, ขอบบน = base_hundred + B
โดย base_hundred คือหลักร้อยที่ถูกละไว้เวลาพิมพ์แบบย่อ 2 หลัก เช่น (50/90) ที่ base=200
หมายถึง 250-290  ถ้า B น้อยกว่า A ให้ทบไปหลักร้อยถัดไป (ขอบบน = base_hundred + 100 + B)
เช่น (50/00) ที่ base=300 -> 350-400 (ไม่ใช่ 350-300)

ปัญหา: ราคาพิมพ์แค่ 2 หลักท้าย หลักร้อยจึงกำกวม — (50/90) เป็นได้ทั้ง 250-290 หรือ 350-390
เราจึงยึด "ไอคอนสีในภาพ" (ถูกเขียว/ผิดแดง/เสมอ) เป็นความจริง แล้วเลือก base_hundred ที่ทำให้
ผลคำนวณตรงกับไอคอน (ดู infer_tie_band) นอกจากนี้บางรูป Vision อ่านราคาเป็นเลข 3 หลักเต็มมาเลย
(เช่น 310/340) กรณีนั้น base=0 คือแถบราคาตรงๆ ไม่ต้องบวกหลักร้อยอีก
"""

from typing import Literal, Optional

Outcome = Literal["win", "loss", "tie"]

# หลักร้อยที่เป็นไปได้ของราคา (A/B) — รวม 0 ไว้เผื่อกรณี Vision อ่านราคาเป็นเลขเต็ม 3 หลักมาแล้ว
_CANDIDATE_BASES = (0, 100, 200, 300, 400, 500, 600, 700)

# ยอมรับ base ที่ทำให้ค่าที่ทำได้จริงห่างจากแถบราคาไม่เกินเท่านี้ — ป้องกันการเลือก base เพี้ยนๆ
# (เช่นตั้งราคา 530-555 เพื่ออธิบายว่าได้ 430) ถ้าไม่มี base ที่สมเหตุสมผล ถือว่าข้อมูลขัดกันจริง
_MAX_BAND_DISTANCE = 100


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


def _distance_to_band(achieved: int, low: int, high: int) -> int:
    """ระยะห่างจาก achieved ถึงแถบราคา (0 ถ้าอยู่ในแถบ) ใช้เลือก base ที่ 'สมเหตุสมผล' ที่สุด"""
    if achieved < low:
        return low - achieved
    if achieved > high:
        return achieved - high
    return 0


def _literal_band(a: int, b: int) -> tuple[int, int]:
    """แถบราคาที่ A เป็นเลข 3 หลักเต็มอยู่แล้ว (ไม่ต้องเดาหลักร้อย): ขอบล่าง = A
    ขอบบน = B โดย B อาจพิมพ์ย่อ 2 หลักของหลักร้อยเดียวกับ A เช่น 280/90 -> 280-290,
    290/10 -> 290-310 (ทบหลักร้อย)  ถ้า B เป็นเลข 3 หลักอยู่แล้วก็ใช้ตรงๆ (ทบถ้าน้อยกว่า A)
    """
    if b >= 100:
        return a, b if b >= a else b + 100
    hundred = (a // 100) * 100
    high = hundred + b
    return a, high if high >= a else high + 100


def infer_tie_band(
    a: int,
    b: int,
    achieved: Optional[int],
    outcome_icon: Optional[str],
    default_base: int = 300,
) -> tuple[int, int, int]:
    """คืน (base_hundred, low, high) ของแถบราคาที่ 'ตรงกับไอคอนสีในภาพมากที่สุด'

    - ราคาเลข 3 หลักเต็ม (A>=100): หลักร้อยชัดเจนอยู่แล้ว ใช้แถบตรงๆ (base=0)
    - ราคาย่อ 2 หลัก (A<100): หลักร้อยกำกวม จึงยึด outcome_icon เป็นความจริง แล้วเลือก
      base_hundred ที่ (1) ทำให้ผลคำนวณตรงกับไอคอน และ (2) แถบราคาอยู่ใกล้ค่าที่ทำได้จริงที่สุด
      ถ้าไม่มี achieved/ไอคอน หรือหา base ที่ตรงไอคอนไม่ได้ ให้ถอยไปใช้ default_base
    """
    if a >= 100:
        low, high = _literal_band(a, b)
        return 0, low, high

    if achieved is not None and outcome_icon in ("win", "loss", "tie"):
        matches = []
        for base in _CANDIDATE_BASES:
            low, high = compute_tie_band(a, b, base)
            dist = _distance_to_band(achieved, low, high)
            if dist <= _MAX_BAND_DISTANCE and classify(achieved, low, high) == outcome_icon:
                # จัดอันดับ: แถบใกล้ achieved ที่สุดก่อน, เสมอกันใช้ base ใกล้ default ก่อน
                matches.append((dist, abs(base - default_base), base, low, high))
        if matches:
            matches.sort()
            _, _, base, low, high = matches[0]
            return base, low, high

    low, high = compute_tie_band(a, b, default_base)
    return default_base, low, high


def compute_and_classify(a: int, b: int, achieved: Optional[int], base_hundred: int = 300) -> Outcome:
    low, high = compute_tie_band(a, b, base_hundred)
    return classify(achieved, low, high)
