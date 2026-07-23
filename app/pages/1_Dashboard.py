import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import config  # noqa: E402
from app import ui  # noqa: E402
from db.connection import get_connection, init_db  # noqa: E402
from db.repository import get_all_rocket_score_summary, get_all_rocket_stats  # noqa: E402
from stats.scoring import rank_name_matches  # noqa: E402

ui.setup_page("Dashboard", "📊")


@st.cache_resource
def get_db():
    conn = get_connection(config.DB_PATH)
    init_db(conn)
    return conn


st.title("📊 Dashboard — สถิติบั้งไฟทั้งหมด")
ui.nav_links(current="สถิติ")

conn = get_db()
rows = get_all_rocket_stats(conn)
df = pd.DataFrame([dict(r) for r in rows])

if df.empty:
    st.warning("ยังไม่มีข้อมูล — ต้องรัน `python cli.py scrape` และ `python cli.py extract-pending` ก่อน")
else:
    # ครอบด้วย form + ปุ่มค้นหา — บนมือถือกด Enter จากคีย์บอร์ดไม่สะดวก ให้กดปุ่มแทน
    # (ค้นหามาก่อนเพราะใช้บ่อยสุด; บนมือถือคอลัมน์จะซ้อนเป็นแนวตั้งตามลำดับนี้)
    with st.form("filter_form", border=False):
        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input("ค้นหาชื่อบั้งไฟ", placeholder="พิมพ์บางส่วนของชื่อก็ได้ เช่น เจ้าพายุ")
        with col2:
            min_races = st.number_input("แข่งอย่างน้อย (ครั้ง)", min_value=1, value=2, step=1)
        st.form_submit_button("🔍 ค้นหา", type="primary", width="stretch")

    if search:
        # ค้นหาข้ามทุกตัว (ไม่ติดเงื่อนไข min_races) เพื่อให้เจอชื่อที่เจาะจงเสมอ แม้แข่งน้อยครั้ง
        q = search.strip()
        # หาแบบ substring (พิมพ์บางส่วนของชื่อ) รวมกับ fuzzy (เผื่อสะกดเพี้ยน เช่น "ฟาโรเบิร์ตฟา")
        sub_mask = df["rocket_name"].str.contains(q, case=False, na=False, regex=False)
        ranked = rank_name_matches(q, df["rocket_name"].tolist())
        fuzzy_names = [n for n, _ in ranked]
        filtered = df[sub_mask | df["rocket_name"].isin(fuzzy_names)]
        # แจ้งชื่อใกล้เคียงที่ดึงเข้ามาเพิ่ม (ที่ไม่ได้ตรงแบบ substring) เผื่อผู้ใช้พิมพ์เพี้ยน
        extra = [f"{n} ({s * 100:.0f}%)" for n, s in ranked if q.lower() not in n.lower()]
        if extra:
            st.caption("รวมชื่อใกล้เคียง (เผื่อสะกดเพี้ยน): " + ", ".join(extra))
    else:
        filtered = df[df["races"] >= min_races]

    score_summary = get_all_rocket_score_summary(conn)

    display_df = filtered.copy()
    display_df["win_rate_pct"] = (display_df["win_rate"] * 100).round(1)
    display_df["avg_score"] = display_df["rocket_name"].map(
        lambda n: round(v, 1) if (v := score_summary.get(n, {}).get("avg_score")) is not None else None
    )
    display_df["last3"] = display_df["rocket_name"].map(lambda n: score_summary.get(n, {}).get("last3"))
    display_df = display_df[
        ["rocket_name", "races", "wins", "losses", "ties", "win_rate_pct",
         "avg_score", "last3", "championships"]
    ].rename(columns={
        "rocket_name": "ชื่อบั้งไฟ", "races": "แข่งทั้งหมด", "wins": "ชนะ", "losses": "แพ้",
        "ties": "เสมอตัว", "win_rate_pct": "อัตราชนะ (%)",
        "avg_score": "คะแนนเฉลี่ย", "last3": "3 นัดล่าสุด", "championships": "แชมป์",
    })
    # จอใหญ่: ตารางเต็ม / มือถือ: การ์ดอ่านง่ายไม่ต้องเลื่อนซ้ายขวา (CSS ใน app/ui.py เลือกให้เอง)
    with st.container(key="wide_only"):
        st.dataframe(
            display_df, width="stretch", hide_index=True,
            column_config={
                "อัตราชนะ (%)": st.column_config.NumberColumn(format="%.1f"),
                "คะแนนเฉลี่ย": st.column_config.NumberColumn(format="%.1f"),
            },
        )
    with st.container(key="narrow_only"):
        rows_all = display_df.to_dict("records")
        cards = []
        for row in ui.paged(rows_all, key="dash_cards"):
            rate = row["อัตราชนะ (%)"]
            badge = None
            if pd.notna(rate):
                badge = (f"ชนะ {rate:.0f}%", "bf-pass" if rate >= 50 else "bf-fail")
            fields = [
                ("แข่ง", row["แข่งทั้งหมด"]), ("ชนะ", row["ชนะ"]), ("แพ้", row["แพ้"]), ("เสมอ", row["เสมอตัว"]),
                ("คะแนนเฉลี่ย", row["คะแนนเฉลี่ย"]), ("3 นัดล่าสุด", row["3 นัดล่าสุด"]),
            ]
            if row["แชมป์"]:
                fields.append(("แชมป์ 🏆", row["แชมป์"]))
            cards.append(ui.card(row["ชื่อบั้งไฟ"], badge, fields))
        ui.render_cards(cards)
        ui.more_button(rows_all, key="dash_cards")
    if search:
        note = "ค้นหาข้ามทุกตัว (ไม่ติดเงื่อนไขจำนวนครั้งที่แข่ง)"
    else:
        note = f"บั้งไฟที่แข่งน้อยกว่า {min_races} ครั้งถูกซ่อนไว้ตามค่าเริ่มต้น"
    st.caption(f"แสดง {len(display_df)} / {len(df)} รายการ ({note})")
