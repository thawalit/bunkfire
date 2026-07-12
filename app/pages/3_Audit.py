import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import config  # noqa: E402
from db.connection import get_connection, init_db  # noqa: E402
from db.repository import mark_post_status  # noqa: E402

st.set_page_config(page_title="Audit", page_icon="🔍", layout="wide")


@st.cache_resource
def get_db():
    conn = get_connection(config.DB_PATH)
    init_db(conn)
    return conn


st.title("🔍 Audit — ตรวจสอบการอ่านข้อมูลจากรูป")
st.caption("ใช้หน้านี้จับกรณี Claude อ่านภาษาไทยผิด เทียบรูปต้นฉบับกับ JSON ที่สกัดได้")

conn = get_db()

only_mismatch = st.checkbox("แสดงเฉพาะโพสต์ที่ตัวเลขกับไอคอนไม่ตรงกัน (outcome_mismatch)")

if only_mismatch:
    post_ids = [r["post_id"] for r in conn.execute(
        "SELECT DISTINCT p.id AS post_id FROM posts p "
        "JOIN events e ON e.post_id = p.id "
        "JOIN rocket_results rr ON rr.event_id = e.id "
        "WHERE rr.outcome_mismatch = 1"
    ).fetchall()]
    posts = conn.execute(
        f"SELECT * FROM posts WHERE id IN ({','.join('?' * len(post_ids)) or 'NULL'}) ORDER BY scraped_at DESC",
        post_ids,
    ).fetchall() if post_ids else []
else:
    posts = conn.execute(
        "SELECT * FROM posts WHERE status = 'vision_processed' ORDER BY scraped_at DESC LIMIT 50"
    ).fetchall()

if not posts:
    st.info("ยังไม่มีโพสต์ที่ประมวลผลแล้ว")

for post in posts:
    with st.expander(f"โพสต์ #{post['id']} — {post['post_url']}"):
        col1, col2 = st.columns([1, 1])
        with col1:
            # สร้าง path จาก fb_post_id ให้พกพาได้ (image_local_path เดิมเป็น absolute ของเครื่องที่ scrape
            # จึงหาไม่เจอบน Streamlit Cloud) — รูปถูก commit ไว้ใน data/images/<fb_post_id>.jpg
            img_path = config.IMAGES_DIR / f"{post['fb_post_id']}.jpg"
            if img_path.exists():
                st.image(str(img_path), width="stretch")
            else:
                st.warning("ไม่พบไฟล์รูป (ยังไม่ได้ commit รูปนี้ขึ้น repo)")
        with col2:
            if post["vision_raw_response"]:
                st.json(json.loads(post["vision_raw_response"]))
            mismatches = conn.execute(
                "SELECT rr.* FROM rocket_results rr JOIN events e ON e.id = rr.event_id "
                "WHERE e.post_id = ? AND rr.outcome_mismatch = 1", (post["id"],),
            ).fetchall()
            if mismatches:
                st.error(f"⚠️ พบ {len(mismatches)} แถวที่ตัวเลขกับไอคอนไม่ตรงกัน")
                for m in mismatches:
                    st.write(
                        f"- {m['rocket_name_raw']}: icon={m['outcome_icon']}, "
                        f"computed={m['computed_outcome']} (band {m['tie_band_low']}-{m['tie_band_high']}, "
                        f"achieved={m['achieved_raw']})"
                    )
            if st.button("ทำเครื่องหมายให้ประมวลผลใหม่", key=f"reprocess_{post['id']}"):
                mark_post_status(conn, post["id"], "pending")
                st.success("ตั้งสถานะกลับเป็น pending แล้ว รันคำสั่ง `python cli.py extract-pending` เพื่อประมวลผลใหม่")
                st.rerun()
