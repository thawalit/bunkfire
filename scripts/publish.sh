#!/usr/bin/env bash
#
# publish.sh — อัปเดตข้อมูลบน Streamlit Cloud (bunkfire.streamlit.app)
#
# Cloud ไม่ได้ต่อ DB สด แต่ "อ่าน data/bunkfire.db จาก GitHub" — ดังนั้นทุกครั้งที่
# scrape/extract ใหม่ ต้อง commit + push snapshot ขึ้น repo สคริปต์นี้รวบขั้นตอนให้:
#   1) force-add รูปตารางผล (data/images/ อยู่ใน .gitignore จึงต้อง -f) + DB
#   2) commit (ข้ามถ้าไม่มีอะไรเปลี่ยน)
#   3) pull --rebase กันชนกับ commit อื่นบน GitHub แล้ว push
#
# ใช้งาน (รันหลัง scrape/extract):
#   python cli.py scrape --limit 20 && python cli.py extract-pending
#   ./scripts/publish.sh                 # ใช้ข้อความ commit อัตโนมัติ
#   ./scripts/publish.sh "ข้อความเอง"    # กำหนดข้อความ commit เอง
#
# หลัง push เสร็จ อย่าลืมไป share.streamlit.io → ⋮ → Reboot app เพื่อให้ Cloud ดึง snapshot ใหม่
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$SCRIPT_DIR")"
cd "$REPO"

PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

echo "▶ จัดเตรียมไฟล์ (DB + รูปตารางผล) ..."
# ใช้ Python stage ไฟล์ให้ (พกพากว่า xargs บน macOS/Linux) แล้วคืนสรุปจำนวน
SUMMARY="$("$PY" - <<'PYEOF'
import sqlite3, subprocess, sys
sys.path.insert(0, ".")
import config

conn = sqlite3.connect(config.DB_PATH)
# รูปที่ Audit ต้องใช้ = โพสต์ที่เป็นตารางผล (vision_processed) เท่านั้น
imgs = []
for (fid,) in conn.execute("SELECT fb_post_id FROM posts WHERE status='vision_processed'"):
    p = config.IMAGES_DIR / f"{fid}.jpg"
    if p.exists():
        imgs.append(str(p))

subprocess.run(["git", "add", "-f", "data/bunkfire.db", *imgs], check=True)

boards = conn.execute("SELECT COUNT(*) FROM posts WHERE status='vision_processed'").fetchone()[0]
rockets = conn.execute("SELECT COUNT(DISTINCT rocket_name_normalized) FROM rocket_results").fetchone()[0]
print(f"{boards} boards, {rockets} rockets, {len(imgs)} board images")
PYEOF
)"
echo "  → $SUMMARY"

if git diff --cached --quiet; then
  echo "✓ ไม่มีข้อมูลใหม่ให้ publish (DB/รูปไม่เปลี่ยน) — จบการทำงาน"
  exit 0
fi

MSG="${1:-Update data snapshot: $SUMMARY}"
echo "▶ commit: $MSG"
git commit -q -m "$MSG"

echo "▶ pull --rebase origin main (กันชนกับ commit บน GitHub) ..."
git pull --rebase --quiet origin main

echo "▶ push origin main ..."
git push --quiet origin main

echo ""
echo "✅ push สำเร็จ — เหลือขั้นตอนสุดท้าย (ต้องทำเองบนเว็บ):"
echo "   share.streamlit.io → app → ⋮ → Reboot app   (Cloud จะดึง snapshot ใหม่)"
