import re

from dataclasses import dataclass

# ตัวช่วยจัดลำดับความสำคัญเท่านั้น ไม่ใช้คัดโพสต์ออกเด็ดขาด เพราะสถานที่/วันที่จริงอยู่ในรูป
DATE_PATTERN = re.compile(r"\(\d{1,2}\s?[ก-ฮ]{1,2}\.?\s?\d{2,4}\)")
KEYWORDS = ("สรุปผล", "แห้งๆ", "ผลการแข่งขัน")


@dataclass
class PostCandidate:
    fb_post_id: str
    post_url: str
    image_url: str | None
    caption_raw: str | None
    has_single_photo: bool


def is_candidate(post: PostCandidate) -> bool:
    """ขั้นกรองแรก (ฟรี ไม่เรียก API): เก็บเฉพาะโพสต์ที่มีรูปเดียว
    bias ไปทาง recall สูง — ไม่คัดออกด้วย caption เพราะข้อมูลจริงอยู่ในรูป
    """
    return post.has_single_photo and post.image_url is not None


def priority_score(post: PostCandidate) -> int:
    """คะแนนช่วยจัดลำดับ (ไม่ใช้คัดออก) — โพสต์ที่ caption มีคำ/รูปแบบวันที่ที่เข้าเค้าได้คะแนนสูงกว่า"""
    caption = post.caption_raw or ""
    score = 0
    if DATE_PATTERN.search(caption):
        score += 2
    if any(k in caption for k in KEYWORDS):
        score += 1
    return score
