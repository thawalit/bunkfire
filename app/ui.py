"""ตัวช่วย UI ที่ใช้ร่วมกันทุกหน้า — เน้นให้ใช้งานบนมือถือได้สะดวก

แนวคิด: เรนเดอร์ทั้ง "ตาราง" (จอใหญ่) และ "การ์ด" (จอเล็ก) แล้วให้ CSS media query
เลือกโชว์อันเดียวตามความกว้างจอจริง — ไม่ต้องให้ผู้ใช้กดสลับโหมดเอง และไม่ต้องพึ่ง JS
(ใช้ st.container(key=...) ซึ่ง Streamlit จะติด class `st-key-<key>` ให้ผูก CSS ได้)
"""

import html

import streamlit as st

MOBILE_BREAKPOINT = 640

_CSS = f"""
<style>
/* ---------- ทั่วไป: ลดขอบ/ระยะห่างบนจอเล็ก ให้เนื้อหาได้พื้นที่เต็ม ---------- */
@media (max-width: {MOBILE_BREAKPOINT}px) {{
  /* เว้นด้านบนให้พ้น header bar ของ Streamlit (ไม่งั้นชื่อหน้าถูกบัง) */
  .block-container {{ padding: 4.5rem 0.75rem 3rem !important; }}
  h1 {{ font-size: 1.35rem !important; line-height: 1.35 !important; }}
  h2 {{ font-size: 1.15rem !important; }}
  h3 {{ font-size: 1.02rem !important; }}

  /* คอลัมน์ของ Streamlit จะบีบแคบมากบนมือถือ — บังคับให้ซ้อนลงมาทีละแถวแทน */
  [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; gap: 0.5rem !important; }}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
    flex: 1 1 100% !important; width: 100% !important; min-width: 100% !important;
  }}
  /* ยกเว้นแถว metric และเมนูลัด: ให้เรียง 2 ช่องต่อแถว จะได้ไม่กินพื้นที่แนวตั้ง */
  .st-key-metric_row [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  .st-key-nav_row [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
    flex: 1 1 calc(50% - 0.5rem) !important; width: auto !important; min-width: calc(50% - 0.5rem) !important;
  }}
  .st-key-nav_row a {{ min-height: 44px; }}
  [data-testid="stMetricValue"] {{ font-size: 1.35rem !important; }}
  [data-testid="stMetricLabel"] p {{ font-size: 0.78rem !important; }}

  /* เป้ากดให้ใหญ่พอสำหรับนิ้ว (>=44px) และกันเบราว์เซอร์ซูมตอนโฟกัส input (font >=16px) */
  .stButton button, .stDownloadButton button, .stLinkButton a {{
    width: 100%; min-height: 44px; font-size: 1rem;
  }}
  input, textarea, select {{ font-size: 16px !important; }}
  [data-testid="stFileUploaderDropzone"] {{ padding: 0.9rem !important; }}
  [data-testid="stFileUploaderDropzoneInstructions"] span {{ font-size: 0.8rem; }}
  .stTabs [data-baseweb="tab"] {{ padding: 0.5rem 0.6rem; font-size: 0.9rem; }}
}}

/* ---------- สลับตาราง/การ์ดตามขนาดจอ ---------- */
@media (max-width: {MOBILE_BREAKPOINT}px) {{ .st-key-wide_only {{ display: none !important; }} }}
@media (min-width: {MOBILE_BREAKPOINT + 1}px) {{ .st-key-narrow_only {{ display: none !important; }} }}

/* ---------- การ์ดสำหรับมือถือ ---------- */
.bf-card {{
  border: 1px solid rgba(49,51,63,0.15); border-radius: 10px;
  padding: 0.6rem 0.75rem; margin-bottom: 0.5rem; background: #fff;
}}
.bf-card-head {{ display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }}
.bf-card-title {{ font-weight: 600; font-size: 1rem; line-height: 1.3; word-break: break-word; }}
.bf-badge {{
  flex: 0 0 auto; border-radius: 999px; padding: 0.1rem 0.55rem;
  font-size: 0.78rem; font-weight: 600; white-space: nowrap;
}}
.bf-pass {{ background: #d4edda; color: #14532d; }}
.bf-fail {{ background: #f8d7da; color: #7f1d1d; }}
.bf-unknown {{ background: #fff3cd; color: #7c4a03; }}
.bf-neutral {{ background: #eef2f6; color: #334155; }}
.bf-card-body {{
  display: flex; flex-wrap: wrap; gap: 0.15rem 0.9rem;
  margin-top: 0.35rem; font-size: 0.86rem; color: #475569;
}}
.bf-card-body b {{ color: #0f172a; font-weight: 600; }}
.bf-note {{ margin-top: 0.3rem; font-size: 0.78rem; color: #64748b; }}
</style>
"""


def setup_page(title: str, icon: str) -> None:
    """ตั้งค่าหน้า + ใส่ CSS มือถือ (เรียกเป็นบรรทัดแรกของทุกหน้า)"""
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        # บนมือถือ sidebar ที่กางค้างไว้จะบังเนื้อหา — เก็บไว้ก่อน แล้วมีเมนูลัดด้านบนแทน
        initial_sidebar_state="collapsed",
    )
    st.markdown(_CSS, unsafe_allow_html=True)


def nav_links(current: str) -> None:
    """เมนูลัดด้านบนของหน้า — บนมือถือ sidebar ถูกซ่อน ผู้ใช้จึงต้องมีทางไปหน้าอื่นตรงนี้"""
    # path ต้อง relative กับไฟล์ entrypoint (app/streamlit_app.py) ตามข้อกำหนดของ st.page_link
    pages = [
        ("streamlit_app.py", "หน้าแรก", "🏠"),
        ("pages/1_Dashboard.py", "สถิติ", "📊"),
        ("pages/2_Upload_Check.py", "เช็ครายชื่อ", "📋"),
        ("pages/3_Audit.py", "ตรวจข้อมูล", "🔍"),
    ]
    with st.container(key="nav_row"):
        cols = st.columns(len(pages))
        for col, (path, label, icon) in zip(cols, pages):
            with col:
                st.page_link(path, label=label, icon=icon, disabled=(label == current))


def card(title: str, badge: tuple[str, str] | None, fields: list[tuple[str, object]], note: str = "") -> str:
    """สร้าง HTML การ์ด 1 ใบ — badge = (ข้อความ, คลาสสี), fields = [(ป้าย, ค่า), ...]"""
    badge_html = ""
    if badge:
        text, cls = badge
        badge_html = f'<span class="bf-badge {cls}">{html.escape(str(text))}</span>'
    body = "".join(
        f"<span>{html.escape(str(label))} <b>{html.escape('—' if value is None else str(value))}</b></span>"
        for label, value in fields
    )
    note_html = f'<div class="bf-note">{html.escape(note)}</div>' if note else ""
    return (
        '<div class="bf-card">'
        f'<div class="bf-card-head"><div class="bf-card-title">{html.escape(str(title))}</div>{badge_html}</div>'
        f'<div class="bf-card-body">{body}</div>{note_html}</div>'
    )


def render_cards(cards: list[str]) -> None:
    st.markdown("".join(cards), unsafe_allow_html=True)


def paged(items: list, key: str, page_size: int = 25) -> list:
    """แบ่งหน้าแบบ 'โหลดเพิ่ม' — กันไม่ให้การ์ดหลายร้อยใบทำให้มือถือหน่วง"""
    shown = st.session_state.get(f"_shown_{key}", page_size)
    return items[:shown]


def more_button(items: list, key: str, page_size: int = 25) -> None:
    state_key = f"_shown_{key}"
    shown = st.session_state.get(state_key, page_size)
    if len(items) > shown:
        remaining = len(items) - shown
        if st.button(f"โหลดเพิ่ม ({remaining} รายการที่เหลือ)", key=f"more_{key}", width="stretch"):
            st.session_state[state_key] = shown + page_size
            st.rerun()
