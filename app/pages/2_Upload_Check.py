import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import config  # noqa: E402
from app import ui  # noqa: E402
from db.connection import get_connection, init_db  # noqa: E402
from stats.scoring import score_rocket_list  # noqa: E402
from vision.extractor import extract_rocket_names  # noqa: E402

ui.setup_page("Upload & Check", "📋")


@st.cache_resource
def get_db():
    conn = get_connection(config.DB_PATH)
    init_db(conn)
    return conn


@st.cache_data(show_spinner=False)
def _names_from_image(image_bytes: bytes, media_type: str) -> list[str]:
    # cache ตาม bytes ของรูป → รูปเดิมจะไม่เรียก Claude Vision ซ้ำเมื่อ Streamlit rerun
    return extract_rocket_names(image_bytes, media_type=media_type)


st.title("📋 เช็ครายชื่อบั้งไฟ ผ่าน/ไม่ผ่าน")
st.caption(
    f"ทำนายจากอัตราชนะในอดีต — เกณฑ์ผ่านปัจจุบัน: win rate ≥ {config.PASS_THRESHOLD * 100:.0f}% "
    "(ชนะ=ผ่าน, แพ้=ไม่ผ่าน, เสมอตัวนับรวมฝั่งไม่ชนะ) บั้งไฟที่ไม่มีข้อมูลจะแสดงว่า \"ไม่มีข้อมูล\" เสมอ"
)
ui.nav_links(current="เช็ครายชื่อ")

conn = get_db()

names: list[str] = []

# แยกช่องทางใส่ข้อมูลเป็นแท็บ — บนมือถือจะได้ไม่ต้องเลื่อนผ่าน uploader หลายอันซ้อนกัน
tab_img, tab_text, tab_file = st.tabs(["📷 ถ่าย/อัปรูป", "⌨️ พิมพ์เอง", "📄 ไฟล์ .csv/.txt"])

with tab_img:
    st.caption("ถ่ายรูปตารางแข่งหรือเลือกจากคลังรูป — Claude Vision จะอ่าน 'ชื่อบั้งไฟ' ให้ (ยังไม่มีผลก็ได้)")
    img_file = st.file_uploader("อัปโหลดรูป (.jpg / .png)", type=["jpg", "jpeg", "png"])
with tab_text:
    manual_text = st.text_area("พิมพ์/วางรายชื่อที่นี่ (1 ชื่อต่อบรรทัด)", height=160)
with tab_file:
    uploaded = st.file_uploader("อัปโหลดไฟล์ .csv หรือ .txt (1 ชื่อต่อบรรทัด)", type=["csv", "txt"])

if img_file is not None:
    try:
        with st.spinner("กำลังอ่านชื่อบั้งไฟจากรูปด้วย Claude Vision..."):
            names = _names_from_image(img_file.getvalue(), img_file.type or "image/jpeg")
        st.success(f"อ่านชื่อบั้งไฟได้ {len(names)} รายการ")
        # รูปเก็บใน expander ให้กดดูเทียบได้ แต่ไม่ดันรายชื่อ/ผลลัพธ์ให้ตกจอบนมือถือ
        with st.expander("ดูรูปที่อัปโหลด"):
            st.image(img_file, width="stretch")
        # ให้ผู้ใช้ตรวจ/แก้ชื่อที่ Vision อ่านผิดก่อนทำนาย
        edited = st.text_area(
            "ตรวจ/แก้ชื่อก่อนทำนาย (1 ชื่อต่อบรรทัด)",
            value="\n".join(names), height=min(300, max(96, 60 + 24 * len(names))),
        )
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

    # สรุปรวมก่อน — บนมือถือเห็นภาพรวมได้ทันทีโดยไม่ต้องไล่อ่านทีละแถว
    n_pass = sum(1 for r in results if r.verdict == "ผ่าน")
    n_fail = sum(1 for r in results if r.verdict == "ไม่ผ่าน")
    n_unknown = len(results) - n_pass - n_fail
    with st.container(key="metric_row"):
        m1, m2, m3 = st.columns(3)
        m1.metric("✅ ผ่าน", n_pass)
        m2.metric("❌ ไม่ผ่าน", n_fail)
        m3.metric("❓ ไม่มีข้อมูล", n_unknown)

    def _verdict_color(v):
        return {"ผ่าน": "background-color: #d4edda", "ไม่ผ่าน": "background-color: #f8d7da",
                "ไม่มีข้อมูล": "background-color: #fff3cd"}.get(v, "")

    # จอใหญ่: ตารางเต็มทุกคอลัมน์ / มือถือ: การ์ดต่อบั้งไฟ อ่านจบไม่ต้องเลื่อนซ้ายขวา
    with st.container(key="wide_only"):
        st.dataframe(
            df_out.style.map(_verdict_color, subset=["ผลทำนาย"]),
            width="stretch", hide_index=True,
            column_config={
                "อัตราชนะ (%)": st.column_config.NumberColumn(format="%.1f"),
                "คะแนนเฉลี่ย": st.column_config.NumberColumn(format="%.1f"),
                "เฉลี่ย 5 นัดล่าสุด": st.column_config.NumberColumn(format="%.1f"),
            },
        )
    with st.container(key="narrow_only"):
        badge_cls = {"ผ่าน": "bf-pass", "ไม่ผ่าน": "bf-fail", "ไม่มีข้อมูล": "bf-unknown"}
        cards = []
        for r in results:
            fields = []
            if r.found:
                win_pct = f"{r.win_rate * 100:.0f}%" if r.win_rate is not None else None
                fields = [
                    ("แข่ง", r.races), ("ชนะ", r.wins), ("แพ้", r.losses), ("อัตราชนะ", win_pct),
                    ("คะแนนเฉลี่ย", r.avg_score), ("5 นัดล่าสุด", r.last5_results),
                ]
                if r.championships:
                    fields.append(("แชมป์ 🏆", r.championships))
            note = ""
            if r.matched_name and r.match_score is not None:
                note = f"จับคู่กับชื่อในฐานข้อมูล: {r.matched_name} ({r.match_score * 100:.0f}%)"
            cards.append(ui.card(
                r.name, (r.verdict, badge_cls.get(r.verdict, "bf-neutral")), fields, note=note,
            ))
        ui.render_cards(cards)

    st.download_button(
        "ดาวน์โหลดผลเป็น CSV",
        df_out.to_csv(index=False).encode("utf-8-sig"),
        file_name="bunkfire_check_results.csv",
        mime="text/csv",
    )
else:
    st.info("อัปโหลดไฟล์หรือพิมพ์รายชื่อบั้งไฟด้านบนเพื่อเริ่มเช็ค")
