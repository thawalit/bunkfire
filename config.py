import os
from pathlib import Path

# โหลดไฟล์ .env เฉพาะตอนรัน local — บน Streamlit Cloud ไม่มี .env (secrets มาทาง env vars)
# และบางครั้ง python-dotenv ไม่ถูกติดตั้ง จึงทำให้ optional ไม่ให้แอปพังตอน import
try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    pass

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
VISION_MODEL = os.environ.get("VISION_MODEL", "claude-sonnet-5")

DB_PATH = Path(os.environ.get("DB_PATH", str(DATA_DIR / "bunkfire.db")))
FB_STATE_PATH = Path(os.environ.get("FB_STATE_PATH", str(DATA_DIR / "fb_state.json")))

FB_PAGE_URL = os.environ.get("FB_PAGE_URL", "https://www.facebook.com/BANHAOSTATION")
FB_PAGE_NAME = os.environ.get("FB_PAGE_NAME", "BANHAOSTATION")

# นับ "เสมอตัว" เป็นฝั่งไม่ชนะ (win_rate = wins / races) ตามที่ผู้ใช้ระบุไว้
PASS_THRESHOLD = float(os.environ.get("PASS_THRESHOLD", "0.50"))

# เกณฑ์ความคล้ายชื่อ (difflib ratio 0-1) สำหรับจับคู่ชื่อบั้งไฟที่สะกดเพี้ยน เช่น
# "ฟาโรเบิร์ตฟา" -> "ฟาโรเบิกฟ้า"  ต่ำกว่านี้ถือว่าไม่พบ (กันจับคู่มั่ว)
FUZZY_MATCH_THRESHOLD = float(os.environ.get("FUZZY_MATCH_THRESHOLD", "0.7"))

# ฐานหลักร้อยของสูตรคำนวณ tie band จาก (A/B) — พบว่าคงที่ที่ 300 ในตัวอย่างที่มี
TIE_BAND_BASE_HUNDRED = int(os.environ.get("TIE_BAND_BASE_HUNDRED", "300"))

# ขอบเขตการดึงย้อนหลังของ scraper (วัน) ค่าเริ่มต้น 1 เดือน
BACKFILL_DAYS = int(os.environ.get("BACKFILL_DAYS", "30"))

# จำกัดจำนวนโพสต์ต่อรอบ scrape เพื่อลดความเสี่ยงถูกบล็อกและคุมค่าใช้จ่าย Vision
MAX_POSTS_PER_RUN = int(os.environ.get("MAX_POSTS_PER_RUN", "200"))
