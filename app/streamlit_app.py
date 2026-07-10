import sqlite3
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
from db.connection import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="สถิติบั้งไฟ BANHAOSTATION", page_icon="🚀", layout="wide")


@st.cache_resource
def get_db() -> sqlite3.Connection:
    conn = get_connection(config.DB_PATH)
    init_db(conn)
    return conn


st.title("🚀 สถิติแพ้ชนะบั้งไฟ — BANHAOSTATION")
st.caption(
    "ข้อมูลสกัดจากโพสต์ผลการแข่งขันด้วย Claude Vision — ใช้เมนูด้านซ้ายเพื่อดูสถิติ "
    "หรืออัปโหลดรายชื่อบั้งไฟเพื่อเช็คผ่าน/ไม่ผ่าน"
)

conn = get_db()
posts_count = conn.execute("SELECT COUNT(*) c FROM posts WHERE status = 'vision_processed'").fetchone()["c"]
events_count = conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
rockets_count = conn.execute("SELECT COUNT(DISTINCT rocket_name_normalized) c FROM rocket_results").fetchone()["c"]
last_scrape = conn.execute("SELECT MAX(finished_at) t FROM scrape_runs").fetchone()["t"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("บั้งไฟที่มีข้อมูล", rockets_count)
col2.metric("งานที่ประมวลผลแล้ว", events_count)
col3.metric("โพสต์ที่ประมวลผลแล้ว", posts_count)
col4.metric("Scrape ล่าสุด", last_scrape or "ยังไม่เคยรัน")

st.info("เลือกหน้าจากเมนูด้านซ้าย: Dashboard, Upload & Check, Audit")
