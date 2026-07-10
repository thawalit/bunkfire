import sqlite3
from dataclasses import dataclass
from typing import Optional

import config
from db.repository import get_rocket_stats


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


def normalize_name(name: str) -> str:
    return name.strip()


def score_rocket(name: str, conn: sqlite3.Connection, threshold: float = config.PASS_THRESHOLD) -> RocketScoreResult:
    row = get_rocket_stats(conn, name)
    if row is None:
        return RocketScoreResult(name=name, found=False)
    win_rate = row["win_rate"]
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
    )


def score_rocket_list(
    names: list[str], conn: sqlite3.Connection, threshold: float = config.PASS_THRESHOLD
) -> list[RocketScoreResult]:
    return [score_rocket(name, conn, threshold) for name in names]
