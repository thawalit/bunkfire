# โปรเจกต์เก็บสถิติแพ้ชนะบั้งไฟ จากเพจ Facebook BANHAOSTATION

## บริบท (Context)

ผู้ใช้ติดตามเพจ Facebook สาธารณะ **BANHAOSTATION** ซึ่งจะโพสต์รูป "สรุปผลการแข่งขัน" บั้งไฟเป็นระยะๆ โดยแต่ละรูปมีตารางผล 1 แถวต่อบั้งไฟ 1 ตัว ประกอบด้วยชื่อบั้งไฟ ตัวเลขคู่ (A/B) ที่ความหมายไม่ทราบแน่ชัด ค่า "= ตัวเลข" หรือ "หาย" และสัญลักษณ์ผลแพ้ชนะ พร้อมถ้วยรางวัลสำหรับแชมป์ของงาน ผู้ใช้ต้องการเครื่องมือที่:
1. ดึงโพสต์ผลการแข่งขันจากเพจนี้โดยอัตโนมัติ
2. อ่านข้อมูลจากรูปด้วย AI (เพราะเป็นภาษาไทยในรูปภาพ ไม่ใช่ข้อความ)
3. เก็บสถิติแพ้ชนะสะสมของบั้งไฟแต่ละตัว
4. ให้ผู้ใช้อัปโหลดรายชื่อบั้งไฟที่จะแข่งในงานถัดไป แล้วระบบทำนายว่าจะ "ผ่าน" หรือ "ไม่ผ่าน" พร้อมคะแนน โดยอ้างอิงจากสถิติในอดีต

โปรเจกต์นี้เริ่มจากศูนย์ (โฟลเดอร์ว่าง ยังไม่ใช่ git repo) ผู้ใช้ได้ส่งตัวอย่างรูปผลการแข่งขันจริง 3 รูปมาให้ ทำให้ยืนยันรูปแบบข้อมูลที่ชัดเจนแล้ว (ดูหัวข้อ "รูปแบบข้อมูลที่ยืนยันแล้ว")

การตัดสินใจสำคัญที่ได้คุยกับผู้ใช้แล้ว (ไม่ใช่การเดาเอง):
- **วิธีดึงข้อมูลจาก Facebook**: ใช้ browser automation (Playwright) ไม่ใช้ Graph API หรืออัปโหลดเอง — ผู้ใช้รับทราบความเสี่ยงเรื่องผิด ToS ของ Facebook และความไม่เสถียรของวิธีนี้แล้ว
- **การอ่านข้อความจากรูป (OCR)**: ใช้ Claude Vision (ผ่าน Anthropic API) ไม่ใช้ Tesseract/Google Vision — เพราะต้องอ่านภาษาไทยจาก layout ที่หลากหลาย
- **หน้าตาโปรแกรม**: เว็บแอป (Python + Streamlit เพื่อความเร็วในการสร้าง dashboard + ฟีเจอร์อัปโหลดไฟล์)
- **ความหมายของผลลัพธ์**: ✅✅ = ชนะ, ❌❌ = แพ้, 🟠🟠 = เสมอตัว, 🏆 = แชมป์ของงาน โดย **คำว่า "หาย" กับสัญลักษณ์ 🟠🟠 คือผลเดียวกัน** คือ "เสมอตัว" — ไม่ใช่กรณียกเว้นของกันและกัน ตัวสกัดข้อมูลต้องอ่านทั้งสองสัญญาณ (ข้อความ "หาย" และไอคอนสีส้ม) แล้ว map เป็น `outcome: tie` เหมือนกันเสมอ อัตราชนะ = ชนะ / จำนวนแข่งทั้งหมด โดยนับ "เสมอตัว" เป็นฝั่งไม่ชนะ (รวมกับแพ้) ตามที่ผู้ใช้ระบุไว้ชัดเจน
- **การจับคู่ชื่อ**: ต้องตรงกันแบบ exact match (ตัด whitespace หัวท้ายเท่านั้น) เพราะบั้งไฟหลายตัวใช้คำต่อท้ายชื่อร่วมกัน (เช่น "เบิกฟ้า", "เจริญ" ซึ่งเป็นชื่อค่าย/ฟาร์ม) การจับคู่แบบ fuzzy จะทำให้จับผิดตัว
- **เกณฑ์ผ่าน/ไม่ผ่าน**: คำว่า "ผ่าน"/"ไม่ผ่าน" หมายถึง "ชนะ"/"แพ้" ตรงตัว (✅=ชนะ=ผ่าน, ❌=แพ้=ไม่ผ่าน — เป็นคำคู่ความหมายเดียวกันในวงการนี้) ดังนั้นฟีเจอร์อัปโหลดรายชื่อคือการ **ทำนายว่ารอบหน้าจะชนะ(ผ่าน)หรือแพ้(ไม่ผ่าน)** โดยอิงจากอัตราชนะในอดีต ค่าเริ่มต้น win rate ≥ 50% = ทำนาย "ผ่าน" น้อยกว่านั้น = ทำนาย "ไม่ผ่าน" ตั้งเป็นค่าคงที่ที่ปรับได้ ไม่ฝังในโค้ด บั้งไฟที่ไม่มีข้อมูลในอดีตเลยต้องแสดงเป็น **"ไม่มีข้อมูล"** ห้ามตัดสินว่า "ไม่ผ่าน" ไปเอง และต้องแสดงจำนวนครั้งที่แข่ง (sample size) กำกับคะแนนเสมอ เพราะบั้งไฟที่ชนะ 1/1 ครั้งกับที่ชนะ 20/40 ครั้ง ความน่าเชื่อถือต่างกันมาก

### รูปแบบข้อมูลที่ยืนยันแล้ว (จากตัวอย่างจริง)
แต่ละรูปมีหัวเรื่องแบบ `สรุปผล..สร้างแป้น (7 ก.ค. 69)` หรือ `แห้งๆ..มั่งมีศรีสุข (6 ก.ค. 69)` คือ คำนำ + ชื่อสถานที่ + วันที่แบบย่อ (ปี พ.ศ. 2 หลัก) ด้านล่างเป็นรายการทีละแถว: `<ชื่อบั้งไฟ>  (A/B) = <ตัวเลขหรือ "หาย">  <สัญลักษณ์ผล>  [🏆]` บางรูปมีลายน้ำแนวตั้ง (ตัวอักษรเรียงทีละตัวจากบนลงล่างตรงกลางภาพ เช่น ชื่อเพจที่แชร์ต่อ) และมี caption พร้อม hashtag ซึ่งทั้งสองส่วนนี้ต้องถูก "มองข้าม" ไม่ใช่ข้อมูลจริง

**สูตรคำนวณผลแพ้ชนะจากตัวเลข (ยืนยันกับผู้ใช้แล้ว และตรวจสอบตรงกับทุกแถวใน 3 รูปตัวอย่าง 100%):**
ตัวเลข `(A/B)` คือขอบเขต "เสมอตัว" แบบย่อ (พิมพ์แค่ 2 หลักท้าย โดยนัยว่าหลักร้อยคือ 3): `ขอบล่าง = 300 + A`, `ขอบบน = 300 + B` — แต่ถ้า B (2 หลักท้ายของขอบบน) น้อยกว่า A ให้ทบไปหลักร้อยถัดไป คือ `ขอบบน = 400 + B` (เช่น `(55/05)` → ขอบบน = 405 ไม่ใช่ 305) ค่า `= <ตัวเลข>` ท้ายบรรทัดคือเวลาที่ทำได้จริงแบบเต็ม (ไม่ย่อ) แล้วนำมาเทียบ:
- ทำได้ **มากกว่า** ขอบบน → ชนะ (✅✅)
- ทำได้ **น้อยกว่า** ขอบล่าง → แพ้ (❌❌)
- ทำได้อยู่ **ระหว่าง** ขอบล่างถึงขอบบน (รวมขอบ) → เสมอตัว (🟠🟠)
- ถ้าไม่มีตัวเลข (ขึ้น "หาย" แทน) → เสมอตัวเช่นกัน ตามที่ตกลงไว้ก่อนหน้า

ตัวอย่างยืนยัน: `(40/80) = 425` → ขอบ [340,380], 425>380 → ชนะ ตรงกับ ✅✅ ในรูป | `(20/60) = 330` → ขอบ[320,360], 330 อยู่ในช่วง → เสมอ ตรงกับ 🟠🟠 | `(55/05) = 415` → ขอบ[355,405] (ทบหลักร้อย) → 415>405 → ชนะ ตรงกับ ✅✅ | `(50/00) = 400` → ขอบ[350,400] (ทบหลักร้อย) → 400 ชนกับขอบบนพอดี → เสมอ ตรงกับ 🟠🟠

เลข "300" ที่เป็นฐานนี้พบว่าคงที่ในทุกแถวของทั้ง 3 รูป (ยังไม่เคยเห็นฐานอื่น) จึงตั้งเป็นค่าคงที่ `TIE_BAND_BASE_HUNDRED = 300` ที่ปรับได้ใน config หากพบรุ่น/หมวดการแข่งขันในอนาคตที่ใช้ฐานต่างออกไป ระบบตรวจจับความคลาดเคลื่อนอัตโนมัติ (ดูหัวข้อ "การสกัดข้อมูล") จะช่วยเตือนกรณีนี้

---

## สถาปัตยกรรมโปรเจกต์

```
bunkfire/
├── README.md                  # วิธีติดตั้ง, คำเตือนความเสี่ยง ToS, วิธี login ครั้งแรก
├── pyproject.toml             # anthropic, playwright, pydantic, streamlit, pandas, click, python-dotenv, pillow
├── .env.example                # ANTHROPIC_API_KEY, DB_PATH, FB_STATE_PATH, VISION_MODEL
├── .gitignore                  # data/fb_state.json, data/*.db, data/images/, .env
├── config.py                   # PASS_THRESHOLD=0.50, VISION_MODEL, ค่าคงที่ rate-limit, path ต่างๆ
├── cli.py                      # subcommand: login, scrape, extract-pending, stats-refresh
├── db/
│   ├── schema.sql              # โครงสร้างตาราง (ดูหัวข้อ Data Model)
│   ├── connection.py           # สร้าง sqlite3 connection: เปิด WAL mode, foreign_keys=ON
│   └── repository.py           # upsert_post(), mark_post_status(), insert_event(),
│                                #   insert_rocket_results(), get_rocket_stats()
├── scraper/
│   ├── auth.py                 # เซฟ/โหลด Playwright storage_state
│   ├── browser.py               # สร้าง headless browser context (UA, viewport)
│   ├── page_scraper.py          # เลื่อนหน้า+เก็บ: fb_post_id, permalink, image_url, caption_raw
│   ├── prefilter.py             # กรองขั้นแรก: โพสต์ที่มีรูปเดียว (+ signal คำ/รูปแบบวันที่ใน caption)
│   └── rate_limit.py             # หน่วงเวลาแบบสุ่ม, จำกัดจำนวนโพสต์ต่อรอบ
├── vision/
│   ├── schema.py                 # Pydantic model: ExtractionResult / RocketResult
│   ├── prompts.py                 # system prompt (รวมคำสั่งให้มองข้ามลายน้ำ/hashtag)
│   ├── image_utils.py             # โหลดรูป, คำนวณ sha256 (ใช้กันประมวลผลซ้ำ)
│   ├── date_utils.py              # แปลงวันที่ พ.ศ. แบบย่อ -> ค.ศ. แบบ deterministic (lookup table เดือน ไม่ใช้ AI คำนวณ)
│   ├── band_rule.py                # compute_tie_band(a,b) และ classify(achieved,low,high) ตามสูตรที่ยืนยันแล้ว, ใช้ตรวจสอบผลจากไอคอนซ้ำอีกชั้น
│   └── extractor.py               # extract(image_bytes) -> ExtractionResult; ข้ามถ้า hash ซ้ำ; เรียก band_rule เพื่อ flag ความไม่ตรงกัน
├── stats/
│   └── scoring.py                  # score_rocket() / score_rocket_list()
├── app/
│   ├── streamlit_app.py             # จุดเริ่มแอป, เมนู sidebar, connection DB (cache)
│   └── pages/
│       ├── 1_Dashboard.py            # ตารางบั้งไฟทั้งหมดเรียงตาม win rate, ตัวกรอง, สรุปภาพรวม
│       ├── 2_Upload_Check.py         # อัปโหลด CSV/txt -> ตาราง found/races/win_rate/score/verdict + ดาวน์โหลดผล
│       └── 3_Audit.py                # ดูรูปคู่กับ JSON ที่สกัดได้ เพื่อตรวจสอบความถูกต้อง
├── data/                              # ไม่เก็บใน git: fb_state.json, bunkfire.db, images/
├── tests/
│   ├── fixtures/                      # รูปตัวอย่าง 3 รูปที่มี + ไฟล์ expected.json ที่เขียนมือ
│   ├── test_extractor.py              # ทดสอบกับ API จริง (รันเองตามต้องการ ไม่ใช่ CI อัตโนมัติ)
│   ├── test_scoring.py                # เคส exact-match / ไม่มีข้อมูล / เกณฑ์ผ่าน-ไม่ผ่าน
│   ├── test_repository.py             # upsert ซ้ำแล้วไม่เกิด row ซ้ำ
│   └── test_date_utils.py             # แปลงวันที่ พ.ศ. -> ค.ศ.
└── scripts/
    └── one_time_login.py               # สคริปต์ช่วย login Facebook ครั้งแรกแบบ manual
```

### การดึงข้อมูล (Scraping) และการกันทำงานซ้ำ
- **Session**: `scripts/one_time_login.py` เปิดเบราว์เซอร์แบบ headful ให้ผู้ใช้ login เอง 1 ครั้ง แล้วบันทึก `storage_state` ลง `data/fb_state.json` (ไม่ commit เข้า git) การรันครั้งถัดไปใช้ session นี้แบบ headless — ไม่มีการเก็บ username/password ในโค้ดเลย
- **ตรวจ session หมดอายุ**: ถ้าโหลดหน้าแล้วถูก redirect ไปหน้า login ให้หยุดทำงานทันทีพร้อม error ชัดเจน ไม่ทำงานต่อแบบเงียบๆ บนหน้าที่ไม่ได้ login
- **กันข้อมูลซ้ำ**: ใช้ `fb_post_id` (ดึงจาก permalink ของโพสต์) เป็น UNIQUE key ในตาราง posts ก่อนดาวน์โหลด/เรียก Vision จะเช็คก่อนว่า id นี้เคยมีสถานะ `vision_processed` หรือ `not_result_board` แล้วหรือยัง ถ้าใช่ให้ข้าม หยุดเลื่อนหน้าเมื่อเจอโพสต์ใหม่ 0 รายการติดต่อกันหลายรอบ หรือครบจำนวนที่ตั้งไว้ต่อรอบ
- **ขอบเขตการดึงย้อนหลัง**: ค่าเริ่มต้นดึงเฉพาะโพสต์ **ย้อนหลัง 1 เดือน** จากวันที่รัน (`config.BACKFILL_DAYS = 30`) โดยอ่านวันที่โพสต์จาก timestamp ของ Facebook (ไม่ใช่วันที่ในรูป เพราะต้องเช็คก่อนเปิดรูปด้วยซ้ำ) เมื่อเจอโพสต์ที่เก่ากว่า 30 วันติดต่อกันให้หยุดเลื่อนหน้าได้เลย (โพสต์เรียงตามเวลาจากใหม่ไปเก่า) ค่านี้ปรับได้ผ่าน `cli.py scrape --since-days N` สำหรับกรณีต้องการดึงย้อนหลังมากกว่านี้ในอนาคต
- **กรอง 2 ขั้น**: ขั้นที่ 1 (ฟรี) — เก็บเฉพาะโพสต์ที่มีรูปเดียว ใช้คำ/รูปแบบวันที่ใน caption เป็นแค่ตัวช่วยจัดลำดับความสำคัญ ไม่ใช่ตัวคัดออกเด็ดขาด (เพราะชื่อสถานที่/วันที่จริงอยู่ในรูป ไม่ใช่ caption เสมอไป) ขั้นที่ 2 — เรียก Claude Vision ครั้งเดียวต่อโพสต์ ให้ทำทั้งจำแนกและสกัดข้อมูลพร้อมกัน (ถ้าไม่ใช่ผลการแข่งขันจะได้ `is_result_board: false` และ list ว่าง) ไม่ต้องเรียก 2 ครั้ง
- **ลดความเสี่ยงถูกบล็อก**: หน่วงเวลาแบบสุ่มระหว่างการกระทำ, ใช้แท็บเดียว headless, User-Agent คงที่, จำกัดจำนวนโพสต์ต่อรอบ, รันไม่ถี่ (รายวัน/รายสัปดาห์ ไม่ใช่ต่อเนื่อง) — ระบุไว้ใน README ว่าเป็นการลดความเสี่ยงเท่าที่ทำได้ ไม่ใช่การรับประกัน

### การสกัดข้อมูลด้วย Claude Vision
- ใช้ Pydantic schema (`vision/schema.py`): `ExtractionResult{is_result_board, event_venue, event_date_day, event_date_month_th, event_date_year_be, rockets: [RocketResult{rocket_name, metric_a: int|null, metric_b: int|null, metric_category_text: str|null, achieved_raw: str, outcome_icon: win|loss|tie, is_champion}]}` — `metric_a`/`metric_b` คือตัวเลข A/B ใน `(A/B)` (เก็บเป็นตัวเลขจริง ไม่ใช่ raw text แล้ว เพราะนำไปคำนวณต่อ), `metric_category_text` ไว้รองรับกรณีที่ในวงเล็บเป็นตัวอักษรแทนตัวเลข เช่น `(ชมต.)` (จะไม่มี metric_a/metric_b ในเคสนี้), `achieved_raw` คือค่า "= ..." ตามที่พิมพ์จริง (ตัวเลข หรือคำว่า "หาย" แบบ verbatim), `outcome_icon` คือผลที่อ่านได้จากสัญลักษณ์สี (✅✅/❌❌/🟠🟠) ซึ่งเป็นแหล่งความจริงหลัก วิธีเรียก API แบบ structured output ที่แน่นอนจะตรวจสอบกับเอกสาร Anthropic SDK ปัจจุบัน (ผ่าน skill `claude-api`) ตอนเริ่มเขียนโค้ดจริง ไม่ใช่เดาไว้ล่วงหน้า
- Prompt จะสั่งชัดเจนว่า: ให้ดึงชื่อบั้งไฟ/ตัวเลข A, B/ค่า achieved ตามที่พิมพ์จริง (ไม่ต้องคำนวณอะไรเอง เดี๋ยวโค้ด Python คำนวณต่อ), ข้อความ "หาย" และไอคอน 🟠🟠 คือสัญญาณของผลเดียวกัน ให้ map เป็น `outcome_icon: tie` เสมอไม่ว่าจะเห็นสัญญาณใดสัญญาณหนึ่งหรือทั้งคู่, ให้มองข้ามลายน้ำแนวตั้งและ caption/hashtag ทั้งหมด, ถ้ารูปไม่ใช่ผลการแข่งขันให้ตอบ `is_result_board: false` แทนการเดา
- **ตรวจสอบซ้ำด้วยสูตรคำนวณ (`vision/band_rule.py`)**: หลังได้ผลจาก Vision แล้ว โค้ด Python คำนวณ `tie_band = compute_tie_band(metric_a, metric_b, base_hundred=config.TIE_BAND_BASE_HUNDRED)` แล้วเทียบ `achieved_raw` (ถ้าเป็นตัวเลข) กับขอบเขตนี้เพื่อได้ `computed_outcome` แล้วเทียบกับ `outcome_icon` ที่ Vision อ่านได้ — ถ้าไม่ตรงกันให้ตั้ง `outcome_mismatch = true` และเก็บ `outcome` สุดท้ายตาม `outcome_icon` (ไอคอนยังเป็นความจริงหลักเพราะอ่านง่ายกว่าเลข) แต่แสดงเตือนในหน้า Audit ให้คนตรวจสอบ เป็นการดักทั้งกรณี Vision อ่านไอคอนผิด และกรณีฐาน 300 ใช้ไม่ได้กับหมวดการแข่งขันบางประเภท
- การแปลงวันที่ (ปี พ.ศ., เดือนย่อภาษาไทย) ทำแบบ deterministic ด้วยโค้ด Python (`vision/date_utils.py` แบบ lookup table) ไม่ให้ AI คำนวณเอง
- ควบคุมค่าใช้จ่าย: กันซ้ำด้วย SHA-256 hash ของรูป, เรียก Vision ต่อโพสต์แค่ครั้งเดียวตลอดชีพ (ผ่าน status ในตาราง posts), กรองขั้นแรกก่อนเรียก API เสมอ แนะนำให้ลองเทียบความแม่นยำ `claude-sonnet-5` กับ `claude-opus-4-8` บนรูปตัวอย่าง 3 รูปก่อนเลือกใช้จริง โดยเริ่มจาก `claude-sonnet-5` เว้นแต่จะอ่านชื่อผิดชัดเจนเมื่อเทียบกับ Opus

### โครงสร้างข้อมูล (SQLite, `db/schema.sql`)
- `posts(id, fb_post_id UNIQUE, post_url, scraped_at, image_url, image_local_path, image_sha256, caption_raw, status CHECK IN (pending, candidate, vision_processed, not_result_board, error), vision_processed_at, vision_raw_response, error_message)`
- `events(id, post_id UNIQUE FK, venue, event_date_raw, event_date DATE)`
- `rocket_results(id, event_id FK, rocket_name_raw, rocket_name_normalized, metric_a INTEGER, metric_b INTEGER, metric_category_text TEXT, achieved_raw TEXT, achieved_value INTEGER, tie_band_low INTEGER, tie_band_high INTEGER, computed_outcome TEXT, outcome_icon TEXT NOT NULL CHECK (outcome_icon IN (win, loss, tie)), outcome TEXT NOT NULL CHECK (outcome IN (win, loss, tie)), outcome_mismatch BOOLEAN NOT NULL DEFAULT 0, is_champion BOOLEAN)` — `outcome` (ใช้คำนวณสถิติจริง) = `outcome_icon` เสมอ, ส่วน `computed_outcome`/`outcome_mismatch` ไว้สำหรับ QA เท่านั้น
- VIEW `v_rocket_stats`: `rocket_name, races, wins, losses, ties, championships, win_rate = wins/races` (เสมอตัวถูกนับรวมในตัวหาร แต่ไม่นับเป็นตัวเศษ) เริ่มจาก VIEW ธรรมดาก่อน (ข้อมูลไม่เยอะ) ค่อยทำเป็นตาราง cache ถ้าช้าในอนาคต
- การ normalize ชื่อ = `.strip()` เท่านั้น — ไม่ fuzzy, ไม่รวมชื่อที่มีคำร่วมกัน

### การให้คะแนน (`stats/scoring.py`)
`score_rocket(name, conn, threshold=PASS_THRESHOLD)` ค้นหาใน `v_rocket_stats` ด้วยชื่อที่ trim แล้วแบบ exact match คืนค่า `{found, races, wins, losses, ties, championships, win_rate, score=win_rate*100, verdict}` ถ้า `found=False` จะได้ `verdict="ไม่มีข้อมูล"` เสมอ ไม่มีทางถูกตัดสินเป็น "ไม่ผ่าน" ไปเอง `score_rocket_list(names, conn)` วนใช้ฟังก์ชันนี้กับรายชื่อที่อัปโหลด โดยรักษาลำดับ/รายการซ้ำตามที่ผู้ใช้อัปโหลดมา เพื่อให้ตรวจสอบ 1:1 ได้ง่าย

### เว็บแอป Streamlit
- อ่านข้อมูลจาก DB อย่างเดียว (เปิด WAL mode กัน lock ชนกับ CLI ที่ scrape/เรียก Vision แยกโปรเซส — ตัวเว็บแอปไม่ scrape หรือเรียก Vision เอง)
- **Dashboard**: แสดง `v_rocket_stats` เรียงตาม win rate มาก→น้อย, ตัวกรองจำนวนแข่งขั้นต่ำ (ซ่อนบั้งไฟที่แข่งแค่ 1 ครั้งเป็นค่าเริ่มต้น), ช่องค้นหาชื่อ, สรุปตัวเลขภาพรวม (จำนวนบั้งไฟ, จำนวนงาน, จำนวนโพสต์ที่ประมวลผลแล้ว, เวลา scrape ล่าสุด)
- **Upload & Check**: `st.file_uploader` รับ `.csv`/`.txt`, parse ทั้งสองแบบ, แสดงตาราง `name, found, races, wins/losses/ties, win_rate%, score, championships, verdict`, ปุ่มดาวน์โหลดผลเป็น CSV
- **Audit**: ดูโพสต์ที่ประมวลผลแล้ว พร้อมรูปคู่กับ JSON ที่สกัดได้ และปุ่ม flag ให้ประมวลผลใหม่ (reset status กลับเป็น pending) — เป็นเครื่องมือหลักในการจับกรณี Claude อ่านภาษาไทยผิด

---

## แผนการทดสอบ
0. **ทดสอบสูตรคำนวณ (`test_band_rule.py`) ก่อนอื่นเลย** เพราะเป็นตรรกะล้วนๆ ไม่ต้องพึ่ง API ใช้ค่าที่ตรวจสอบด้วยมือแล้วจากรูปตัวอย่างจริงเป็น fixture โดยตรง เช่น `compute_and_classify(40,80,425)=="win"`, `(20,60,330)=="tie"`, `(30,60,310)=="loss"`, `(40,0,240)=="loss"` (กรณีทบหลักร้อยของขอบบนแต่ยังแพ้), `(55,5,415)=="win"` (กรณีทบหลักร้อย), `(50,0,400)=="tie"` (กรณีชนขอบบนพอดี)
1. **ทดสอบตัวสกัดข้อมูลเป็นลำดับถัดไป**: เก็บรูปตัวอย่าง 3 รูปที่มีอยู่แล้วไว้ใน `tests/fixtures/`, เขียน `expected.json` ด้วยมือทีละรูป (รวม `metric_a/metric_b/achieved_raw` และ `outcome_icon` ที่ถูกต้องของทุกแถว), รัน `vision/extractor.py` เทียบผลโดยตรง (ไม่ต้องมี browser หรือ DB) — ใช้ยืนยัน prompt/schema และตรวจว่า `outcome_mismatch` ไม่ควรเกิดกับข้อมูลชุดนี้เลย (เพราะตรวจด้วยมือแล้วว่าทุกแถวสอดคล้องกับสูตร 100%) ก่อนเริ่มเขียนตัว scraper เลย
2. **Unit test ส่วนตรรกะล้วนๆ** (รันได้ทุก commit): `test_scoring.py`, `test_date_utils.py`, `test_repository.py`
3. **Dry run ตัว scraper**: `cli.py scrape --dry-run --limit 5` กับหน้าเพจจริง (ไม่เขียน DB) เพื่อยืนยันว่า selector ยังใช้ได้
4. **Backfill เล็กๆ จริง**: `cli.py scrape --limit 10` + `cli.py extract-pending` แล้วตรวจผลด้วยตาผ่านหน้า Audit
5. **ทดสอบเว็บแอป**: รันแอปกับ DB ที่ seed จากขั้นตอนที่ 4 ตรวจว่า Dashboard เรียงลำดับถูก และ Upload & Check แยกแยะ ผ่าน/ไม่ผ่าน/ไม่มีข้อมูล ได้ถูกต้อง รวมถึงเคสตัวอย่างที่มีข้อมูลแค่ 1 ครั้ง
6. `test_extractor.py` (เรียก API จริง มีค่าใช้จ่าย) และตัว scraper เอง (แตะเว็บจริง) ให้รันเองตามต้องการ ไม่ใส่ใน CI อัตโนมัติ

## ไฟล์สำคัญที่ต้องเขียน
- `vision/extractor.py`, `vision/schema.py`, `vision/prompts.py`, `vision/band_rule.py` — แกนหลักของการอ่าน/สกัดข้อมูลจากรูป และสูตรคำนวณผลแพ้ชนะที่ยืนยันแล้ว
- `db/schema.sql`, `db/repository.py` — โครงสร้างข้อมูลและการเขียนแบบกันซ้ำ
- `scraper/page_scraper.py`, `scraper/auth.py` — ระบบดึงข้อมูลจาก Facebook และจัดการ session
- `stats/scoring.py` — ตรรกะให้คะแนนผ่าน/ไม่ผ่าน
- `app/pages/2_Upload_Check.py` — ฟีเจอร์อัปโหลด/เช็กที่ผู้ใช้จะใช้งานจริง
