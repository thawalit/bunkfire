import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import config  # noqa: E402
from db.connection import get_connection, init_db  # noqa: E402
from db.repository import get_all_rocket_stats  # noqa: E402

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")


@st.cache_resource
def get_db():
    conn = get_connection(config.DB_PATH)
    init_db(conn)
    return conn


st.title("📊 Dashboard — สถิติบั้งไฟทั้งหมด")

conn = get_db()
rows = get_all_rocket_stats(conn)
df = pd.DataFrame([dict(r) for r in rows])

if df.empty:
    st.warning("ยังไม่มีข้อมูล — ต้องรัน `python cli.py scrape` และ `python cli.py extract-pending` ก่อน")
else:
    col1, col2 = st.columns([1, 2])
    with col1:
        min_races = st.number_input("แสดงเฉพาะบั้งไฟที่แข่งอย่างน้อย (ครั้ง)", min_value=1, value=2, step=1)
    with col2:
        search = st.text_input("ค้นหาชื่อบั้งไฟ")

    filtered = df[df["races"] >= min_races]
    if search:
        filtered = filtered[filtered["rocket_name"].str.contains(search, case=False, na=False)]

    display_df = filtered.copy()
    display_df["win_rate_pct"] = (display_df["win_rate"] * 100).round(1)
    display_df = display_df[
        ["rocket_name", "races", "wins", "losses", "ties", "win_rate_pct", "championships"]
    ].rename(columns={
        "rocket_name": "ชื่อบั้งไฟ", "races": "แข่งทั้งหมด", "wins": "ชนะ", "losses": "แพ้",
        "ties": "เสมอตัว", "win_rate_pct": "อัตราชนะ (%)", "championships": "แชมป์",
    })
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.caption(f"แสดง {len(display_df)} / {len(df)} รายการ (บั้งไฟที่แข่งน้อยกว่า {min_races} ครั้งถูกซ่อนไว้ตามค่าเริ่มต้น)")
