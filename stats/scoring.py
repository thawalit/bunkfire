import sqlite3
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional

import config
from db.repository import (
    get_distinct_rocket_names,
    get_rocket_last_results,
    get_rocket_score_stats,
    get_rocket_stats,
)

# แปลงผลการแข่ง (outcome) เป็นคำไทยที่ผู้ใช้คุ้น — เสมอตัวถือเป็นฝั่งไม่ชนะตามกติกาของแอป
_OUTCOME_TH = {"win": "ผ่าน", "loss": "ไม่ผ่าน", "tie": "เสมอ"}


@dataclass
class RocketScoreResult:
    name: str
    found: bool
    races: int = 0
    wins: int = 0
    losses: int = 0
    ties: int = 0
    championships: int = 0
    win_rate: Optional[float] = None
    score: Optional[float] = None
    verdict: str = "ไม่มีข้อมูล"
    avg_score: Optional[float] = None
    top_score: Optional[int] = None
    low_score: Optional[int] = None
    last5_avg: Optional[float] = None
    last5_results: Optional[str] = None
    matched_name: Optional[str] = None  # ชื่อในฐานข้อมูลที่จับคู่ได้ (ตั้งเมื่อ match แบบใกล้เคียงเท่านั้น)
    match_score: Optional[float] = None  # ความคล้าย 0-1 ของการจับคู่ใกล้เคียง


def normalize_name(name: str) -> str:
    return name.strip()


def _name_similarity(query: str, cand: str) -> float:
    """ความคล้ายของชื่อ (difflib ratio 0-1) พร้อมกันจับคู่แบบตัดคำ: ถ้าความยาวต่างกันมาก
    (เช่นพิมพ์คำสั้นที่บังเอิญเป็นส่วนหนึ่งของชื่อยาว) คืน 0 — การสะกดเพี้ยนจริงความยาวจะใกล้กัน"""
    if not cand or min(len(query), len(cand)) / max(len(query), len(cand)) < 0.6:
        return 0.0
    return SequenceMatcher(None, query, cand).ratio()


def rank_name_matches(
    query: str, candidates: list[str], threshold: float = config.FUZZY_MATCH_THRESHOLD
) -> list[tuple[str, float]]:
    """คืนชื่อที่คล้าย query ทั้งหมดที่ >= threshold เรียงจากคล้ายมากไปน้อย (ชื่อ, คะแนน)"""
    query = query.strip()
    if not query:
        return []
    scored = [(c, _name_similarity(query, c)) for c in candidates]
    scored = [(c, s) for c, s in scored if s >= threshold]
    scored.sort(key=lambda cs: cs[1], reverse=True)
    return scored


def find_closest_name(
    name: str, candidates: list[str], threshold: float = config.FUZZY_MATCH_THRESHOLD
) -> Optional[tuple[str, float]]:
    """หาชื่อในฐานข้อมูลที่คล้าย name ที่สุด (difflib ratio) คืน (ชื่อ, คะแนน) ถ้า >= threshold
    ใช้จับชื่อที่ Vision อ่านเพี้ยน เช่น "ฟาโรเบิร์ตฟา" -> "ฟาโรเบิกฟ้า" """
    ranked = rank_name_matches(name, candidates, threshold)
    return ranked[0] if ranked else None


def score_rocket(
    name: str,
    conn: sqlite3.Connection,
    threshold: float = config.PASS_THRESHOLD,
    candidate_names: Optional[list[str]] = None,
) -> RocketScoreResult:
    query = normalize_name(name)
    row = get_rocket_stats(conn, query)
    matched_name: Optional[str] = None
    match_score: Optional[float] = None
    if row is None:
        # ไม่พบชื่อตรงเป๊ะ -> ลองจับคู่ชื่อใกล้เคียง (กรณีสะกดเพี้ยน/Vision อ่านผิด)
        if candidate_names is None:
            candidate_names = get_distinct_rocket_names(conn)
        hit = find_closest_name(query, candidate_names)
        if hit is not None:
            matched_name, match_score = hit
            row = get_rocket_stats(conn, matched_name)
    if row is None:
        return RocketScoreResult(name=name, found=False)
    # ชื่อที่ใช้ดึงสถิติต่อจากนี้: ถ้าจับคู่ใกล้เคียงให้ใช้ชื่อในฐานข้อมูล ไม่ใช่ชื่อที่พิมพ์มา
    lookup = matched_name or query
    win_rate = row["win_rate"]
    score_stats = get_rocket_score_stats(conn, lookup) or {}
    avg_score = score_stats.get("avg_score")
    last5_avg = score_stats.get("last5_avg")
    last_rows = get_rocket_last_results(conn, lookup)
    last5_results = ", ".join(
        f"{r['achieved_value']}({_OUTCOME_TH.get(r['outcome'], r['outcome'])})" for r in last_rows
    ) or None
    return RocketScoreResult(
        name=name,
        found=True,
        races=row["races"],
        wins=row["wins"],
        losses=row["losses"],
        ties=row["ties"],
        championships=row["championships"],
        win_rate=win_rate,
        score=round(win_rate * 100, 1),
        verdict="ผ่าน" if win_rate >= threshold else "ไม่ผ่าน",
        avg_score=round(avg_score, 1) if avg_score is not None else None,
        top_score=score_stats.get("top_score"),
        low_score=score_stats.get("low_score"),
        last5_avg=round(last5_avg, 1) if last5_avg is not None else None,
        last5_results=last5_results,
        matched_name=matched_name,
        match_score=round(match_score, 2) if match_score is not None else None,
    )


def score_rocket_list(
    names: list[str], conn: sqlite3.Connection, threshold: float = config.PASS_THRESHOLD
) -> list[RocketScoreResult]:
    # ดึงรายชื่อผู้สมัครจับคู่ครั้งเดียว แล้วใช้ซ้ำทุกชื่อ (เลี่ยงคิวรีซ้ำในลูป)
    candidate_names = get_distinct_rocket_names(conn)
    return [score_rocket(name, conn, threshold, candidate_names) for name in names]
