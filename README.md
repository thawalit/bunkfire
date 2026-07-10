# bunkfire — สถิติแพ้ชนะบั้งไฟจากเพจ Facebook BANHAOSTATION

เก็บสถิติแพ้ชนะบั้งไฟจากโพสต์ผลการแข่งขันของเพจ [BANHAOSTATION](https://www.facebook.com/BANHAOSTATION)
โดยอ่านรูปด้วย Claude Vision แล้วให้อัปโหลดรายชื่อบั้งไฟเพื่อทำนายผ่าน/ไม่ผ่านพร้อมคะแนน

## ⚠️ คำเตือนความเสี่ยง

โปรเจกต์นี้ใช้ browser automation (Playwright) ดึงข้อมูลจากหน้าเพจ Facebook ซึ่ง**ผิดข้อกำหนดการใช้งาน
(ToS) ของ Facebook** และมีความเสี่ยงที่บัญชีที่ใช้ login จะถูกจำกัด/บล็อก รวมถึง selector อาจใช้ไม่ได้
เมื่อ Facebook เปลี่ยน layout — ผู้ใช้รับทราบและยอมรับความเสี่ยงนี้แล้ว โปรดใช้บัญชีสำรอง ไม่ใช่บัญชีหลัก
และรันไม่ถี่ (รายวัน/รายสัปดาห์)

## ติดตั้ง

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
playwright install chromium
cp .env.example .env   # ใส่ ANTHROPIC_API_KEY
```

## วิธีใช้งาน

1. **Login ครั้งแรก** (เปิด browser ให้ login เอง แล้วบันทึก session):
   ```bash
   python cli.py login
   ```
2. **ดึงโพสต์ + ทดสอบ selector ก่อนใช้งานจริง**:
   ```bash
   python cli.py scrape --dry-run --limit 5
   ```
3. **ดึงโพสต์จริง แล้วสกัดข้อมูลด้วย Claude Vision**:
   ```bash
   python cli.py scrape --limit 20
   python cli.py extract-pending
   ```
4. **เปิดเว็บแอป** (ดู Dashboard / อัปโหลดรายชื่อเช็คผ่าน-ไม่ผ่าน / Audit):
   ```bash
   streamlit run app/streamlit_app.py
   ```

## รันเทส

```bash
pytest tests/ -q -m "not api"          # เทสตรรกะล้วนๆ ไม่เรียก API จริง
pytest tests/test_extractor.py -q      # ต้องมี ANTHROPIC_API_KEY + รูปตัวอย่างใน tests/fixtures/ (ดู README ในโฟลเดอร์นั้น)
```

## โครงสร้างโปรเจกต์

ดูรายละเอียดสถาปัตยกรรมและการตัดสินใจออกแบบทั้งหมดใน `docs/DESIGN.md` (คัดลอกจากแผนตอนวางแผนโปรเจกต์)
