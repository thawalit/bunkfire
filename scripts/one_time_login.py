"""รันครั้งเดียวเพื่อ login Facebook แบบ manual แล้วบันทึก session สำหรับ scraper

ใช้งาน: python scripts/one_time_login.py
เบราว์เซอร์จะเปิดขึ้นมาแบบเห็นหน้าจอ (headful) ให้ผู้ใช้ login เอง (รวมถึง 2FA/captcha ถ้ามี)
แล้วกลับมากดปุ่ม Enter ในเทอร์มินัลเพื่อบันทึก session — ไม่มีการเก็บ username/password ในโค้ด
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

import config
from scraper.auth import save_storage_state


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.facebook.com/login")

        print("กรุณา login ใน browser ที่เปิดขึ้นมา (รวมถึง 2FA/captcha ถ้ามี)")
        input("เมื่อ login สำเร็จและเห็นหน้า feed แล้ว กด Enter ที่นี่เพื่อบันทึก session...")

        save_storage_state(context, config.FB_STATE_PATH)
        print(f"บันทึก session ไว้ที่ {config.FB_STATE_PATH} แล้ว")

        browser.close()


if __name__ == "__main__":
    main()
