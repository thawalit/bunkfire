import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import config  # noqa: E402
from db.connection import get_connection, init_db  # noqa: E402
from stats.scoring import score_rocket_list  # noqa: E402

st.set_page_config(page_title="Upload & Check", page_icon="📋", layout="wide")


@st.cache_resource
def get_db():
    conn = get_connection(config.DB_PATH)
    init_db(conn)
    return conn


st.title("📋 อัปโหลดรายชื่อบั้งไฟ เพื่อเช็คผ่าน/ไม่ผ่าน")
st.caption(
    f"ทำนายจากอัตราชนะในอดีต — เกณฑ์ผ่านปัจจุบัน: win rate ≥ {config.PASS_THRESHOLD * 100:.0f}% "
    "(ชนะ=ผ่าน, แพ้=ไม่ผ่าน, เสมอตัวนับรวมฝั่งไม่ชนะ) บั้งไฟที่ไม่มีข้อมูลจะแสดงว่า \"ไม่มีข้อมูล\" เสมอ"
)

conn = get_db()

names: list[str] = []
uploaded = st.file_uploader("อัปโหลดไฟล์ .csv หรือ .txt (1 ชื่อต่อบรรทัด)", type=["csv", "txt"])
manual_text = st.text_area("หรือพิมพ์/วางรายชื่อที่นี่ (1 ชื่อต่อบรรทัด)")

if uploaded is not None:
    raw = uploaded.read().decode("utf-8-sig")
    if uploaded.name.endswith(".csv"):
        df_in = pd.read_csv(io.StringIO(raw), header=None)
        names = [str(v) for v in df_in.iloc[:, 0].tolist()]
    else:
        names = [line for line in raw.splitlines() if line.strip()]
elif manual_text.strip():
    names = [line for line in manual_text.splitlines() if line.strip()]

if names:
    results = score_rocket_list(names, conn)
    df_out = pd.DataFrame([{
        "ชื่อที่อัปโหลด": r.name,
        "พบข้อมูล": "พบ" if r.found else "ไม่พบ",
        "จำนวนแข่ง": r.races,
        "ชนะ": r.wins,
        "แพ้": r.losses,
        "เสมอตัว": r.ties,
        "อัตราชนะ (%)": round(r.win_rate * 100, 1) if r.win_rate is not None else None,
        "คะแนน": r.score,
        "แชมป์": r.championships,
        "ผลทำนาย": r.verdict,
    } for r in results])

    def _verdict_color(v):
        return {"ผ่าน": "background-color: #d4edda", "ไม่ผ่าน": "background-color: #f8d7da",
                "ไม่มีข้อมูล": "background-color: #fff3cd"}.get(v, "")

    st.dataframe(
        df_out.style.map(_verdict_color, subset=["ผลทำนาย"]),
        use_container_width=True, hide_index=True,
    )
    st.download_button(
        "ดาวน์โหลดผลเป็น CSV",
        df_out.to_csv(index=False).encode("utf-8-sig"),
        file_name="bunkfire_check_results.csv",
        mime="text/csv",
    )
else:
    st.info("อัปโหลดไฟล์หรือพิมพ์รายชื่อบั้งไฟด้านบนเพื่อเริ่มเช็ค")
