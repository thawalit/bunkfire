# Deploy ขึ้น Streamlit Community Cloud

Web app (`app/streamlit_app.py`) เป็น **read-only viewer** อ่านข้อมูลจาก `data/bunkfire.db`
อย่างเดียว — ไม่เรียก browser (Playwright) และไม่เรียก Claude API จึงรันบน Cloud ได้เลย
โดย**ไม่ต้องตั้งค่า secret ใด ๆ**

> ⚠️ **scraper รันบน Cloud ไม่ได้** — การ scrape (Playwright + login Facebook) และ
> `extract-pending` (Claude Vision) เป็นงานฝั่ง **local เท่านั้น** วิธีอัปเดตข้อมูลบน Cloud
> คือรันสองคำสั่งนี้ที่เครื่อง แล้ว commit `data/bunkfire.db` ตัวใหม่ push ขึ้นไป (ดูข้อ 5)

## ขั้นตอน (ทำครั้งเดียว)

### 1. สร้าง GitHub repo แล้ว push
repo นี้ init git + commit ไว้ให้แล้ว เหลือแค่สร้าง remote แล้ว push:

```bash
# ถ้ายังไม่ได้ login gh:  gh auth login
gh repo create bunkfire --public --source=. --remote=origin --push
# หรือแบบ manual:
#   git remote add origin https://github.com/<user>/bunkfire.git
#   git push -u origin main
```

### 2. เปิด Streamlit Community Cloud
ไปที่ https://share.streamlit.io → **Sign in with GitHub** → อนุญาตสิทธิ์

### 3. New app → เลือก repo
- **Repository**: `<user>/bunkfire`
- **Branch**: `main`
- **Main file path**: `app/streamlit_app.py`
- กด **Deploy**

### 4. เสร็จ
Cloud จะติดตั้งจาก `requirements.txt` (streamlit, pandas, python-dotenv) แล้วเปิดแอปที่
`https://<something>.streamlit.app` — Dashboard จะมีข้อมูลจาก snapshot ที่ commit ไว้ทันที

## อัปเดตข้อมูลภายหลัง

```bash
python cli.py scrape --limit 20        # ดึงรูปใหม่ (ต้องมี session FB ที่ยัง valid)
python cli.py extract-pending          # ให้ Claude Vision อ่าน (ใช้ ANTHROPIC_API_KEY ใน .env)
sqlite3 data/bunkfire.db 'PRAGMA wal_checkpoint(TRUNCATE);'   # flush WAL เข้าไฟล์หลัก
git add data/bunkfire.db && git commit -m "update data snapshot" && git push
```
Streamlit Cloud จะ redeploy อัตโนมัติเมื่อ push

## หมายเหตุ
- **ไม่ commit**: `.env` (API key) และ `data/fb_state.json` (session Facebook) — ถูก `.gitignore` กันไว้แล้ว
- หน้า **Audit** จะไม่โชว์รูปต้นฉบับบน Cloud เพราะ `data/images/` ไม่ได้ commit
  (ถ้าต้องการรูปด้วย ให้เพิ่ม `git add -f data/images/` — แต่รูปจะเปิดสาธารณะเช่นกัน)
- repo เป็น **public** = โค้ด + `data/bunkfire.db` (ข้อมูลที่ scrape จาก FB) เปิดสาธารณะ
