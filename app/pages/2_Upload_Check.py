import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import config  # noqa: E402
from db.connection import get_connection, init_db  # noqa: E402
from stats.scoring import score_rocket_list  # noqa: E402
from vision.extractor import extract_rocket_names  # noqa: E402

st.set_page_config(page_title="Upload & Check", page_icon="📋", layout="wide")


@st.cache_resource
def get_db():
    conn = get_connection(config.DB_PATH)
    init_db(conn)
    return conn


@st.cache_data(show_spinner=False)
def _names_from_image(image_bytes: bytes, media_type: str) -> list[str]:
    # cache ตาม bytes ของรูป → รูปเดิมจะไม่เรียก Claude Vision ซ้ำเมื่อ Streamlit rerun
    return extract_rocket_names(image_bytes, media_type=media_type)


st.title("📋 อัปโหลดรายชื่อบั้งไฟ เพื่อเช็คผ่าน/ไม่ผ่าน")
st.caption(
    f"ทำนายจากอัตราชนะในอดีต — เกณฑ์ผ่านปัจจุบัน: win rate ≥ {config.PASS_THRESHOLD * 100:.0f}% "
    "(ชนะ=ผ่าน, แพ้=ไม่ผ่าน, เสมอตัวนับรวมฝั่งไม่ชนะ) บั้งไฟที่ไม่มีข้อมูลจะแสดงว่า \"ไม่มีข้อมูล\" เสมอ"
)

conn = get_db()

names: list[str] = []

st.subheader("📷 อัปโหลดรูปตารางแข่ง (ยังไม่มีผลก็ได้)")
st.caption("ระบบจะให้ Claude Vision อ่าน 'ชื่อบั้งไฟ' จากรูป แล้วทำนายผ่าน/ไม่ผ่านจากสถิติในอดีต")
img_file = st.file_uploader("อัปโหลดรูป (.jpg / .png)", type=["jpg", "jpeg", "png"])

st.subheader("⌨️ หรือใส่รายชื่อเอง")
uploaded = st.file_uploader("อัปโหลดไฟล์ .csv หรือ .txt (1 ชื่อต่อบรรทัด)", type=["csv", "txt"])
manual_text = st.text_area("หรือพิมพ์/วางรายชื่อที่นี่ (1 ชื่อต่อบรรทัด)")

if img_file is not None:
    col_img, col_names = st.columns([1, 1])
    with col_img:
        st.image(img_file, caption="รูปที่อัปโหลด", width="stretch")
    with col_names:
        try:
            with st.spinner("กำลังอ่านชื่อบั้งไฟจากรูปด้วย Claude Vision..."):
                names = _names_from_image(img_file.getvalue(), img_file.type or "image/jpeg")
            st.success(f"อ่านชื่อบั้งไฟได้ {len(names)} รายการ")
            # ให้ผู้ใช้ตรวจ/แก้ชื่อที่ Vision อ่านผิดก่อนทำนาย
            edited = st.text_area("ตรวจ/แก้ชื่อก่อนทำนาย (1 ชื่อต่อบรรทัด)", value="\n".join(names), height=300)
            names = [line for line in edited.splitlines() if line.strip()]
        except Exception as e:
            names = []
            st.error(
                "อ่านรูปไม่สำเร็จ — ตรวจว่าตั้งค่า ANTHROPIC_API_KEY แล้ว "
                f"(บน Streamlit Cloud ต้องเพิ่มใน Secrets)\n\nรายละเอียด: {e}"
            )
elif uploaded is not None:
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

    def _found_label(r):
        if not r.found:
            return "ไม่พบ"
        return "ใกล้เคียง" if r.matched_name else "พบ"

    def _matched_label(r):
        # โชว์ชื่อในฐานข้อมูลที่จับคู่ได้ + %ความคล้าย เฉพาะกรณีสะกดเพี้ยน (match ใกล้เคียง)
        if r.matched_name and r.match_score is not None:
            return f"{r.matched_name} ({r.match_score * 100:.0f}%)"
        return ""

    df_out = pd.DataFrame([{
        "ชื่อที่อัปโหลด": r.name,
        "พบข้อมูล": _found_label(r),
        "จับคู่กับ (ชื่อเพี้ยน)": _matched_label(r),
        "จำนวนแข่ง": r.races,
        "ชนะ": r.wins,
        "แพ้": r.losses,
        "เสมอตัว": r.ties,
        "อัตราชนะ (%)": round(r.win_rate * 100, 1) if r.win_rate is not None else None,
        "คะแนนเฉลี่ย": r.avg_score,
        "คะแนนสูงสุด": r.top_score,
        "คะแนนต่ำสุด": r.low_score,
        "เฉลี่ย 5 นัดล่าสุด": r.last5_avg,
        "ผล 5 นัดล่าสุด": r.last5_results,
        "แชมป์": r.championships,
        "ผลทำนาย": r.verdict,
    } for r in results])

    def _verdict_color(v):
        return {"ผ่าน": "background-color: #d4edda", "ไม่ผ่าน": "background-color: #f8d7da",
                "ไม่มีข้อมูล": "background-color: #fff3cd"}.get(v, "")

    st.dataframe(
        df_out.style.map(_verdict_color, subset=["ผลทำนาย"]),
        width="stretch", hide_index=True,
        column_config={
            "อัตราชนะ (%)": st.column_config.NumberColumn(format="%.1f"),
            "คะแนนเฉลี่ย": st.column_config.NumberColumn(format="%.1f"),
            "เฉลี่ย 5 นัดล่าสุด": st.column_config.NumberColumn(format="%.1f"),
        },
    )
    st.download_button(
        "ดาวน์โหลดผลเป็น CSV",
        df_out.to_csv(index=False).encode("utf-8-sig"),
        file_name="bunkfire_check_results.csv",
        mime="text/csv",
    )
else:
    st.info("อัปโหลดไฟล์หรือพิมพ์รายชื่อบั้งไฟด้านบนเพื่อเริ่มเช็ค")
