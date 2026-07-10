import json
from pathlib import Path

import pytest

from vision.band_rule import compute_and_classify

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXPECTED_FILES = sorted(FIXTURES_DIR.glob("sample_*_expected.json"))


def _load_rows():
    rows = []
    for f in EXPECTED_FILES:
        data = json.loads(f.read_text(encoding="utf-8"))
        for rocket in data["rockets"]:
            if rocket.get("metric_a") is not None and rocket.get("metric_b") is not None:
                rows.append((f.name, rocket))
    return rows


@pytest.mark.parametrize("filename,rocket", _load_rows(), ids=lambda v: v if isinstance(v, str) else v.get("rocket_name", ""))
def test_band_rule_matches_hand_transcribed_icon(filename, rocket):
    computed = compute_and_classify(rocket["metric_a"], rocket["metric_b"], rocket.get("achieved_value"))
    assert computed == rocket["outcome_icon"], (
        f"{filename}: {rocket['rocket_name']} ({rocket['metric_a']}/{rocket['metric_b']})="
        f"{rocket.get('achieved_raw')} -> computed={computed}, expected={rocket['outcome_icon']}"
    )


def test_fixtures_present():
    assert len(EXPECTED_FILES) == 3, "ควรมีไฟล์ sample_0N_expected.json ครบ 3 ไฟล์"
