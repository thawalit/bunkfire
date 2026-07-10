"""ทดสอบ vision/extractor.py กับ Claude Vision จริง — เรียก API จริง มีค่าใช้จ่าย
รันเองด้วย `pytest tests/test_extractor.py` หลังบันทึกรูปตัวอย่างตาม tests/fixtures/README.md
ไม่รวมใน CI อัตโนมัติ ข้ามอัตโนมัติถ้าไม่พบไฟล์รูปหรือไม่ได้ตั้ง ANTHROPIC_API_KEY
"""
import json
import os
from pathlib import Path

import pytest

import config
from vision.extractor import extract_from_path

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLES = ["sample_01", "sample_02", "sample_03"]

pytestmark = pytest.mark.skipif(
    not config.ANTHROPIC_API_KEY, reason="ต้องตั้งค่า ANTHROPIC_API_KEY เพื่อรันเทสนี้"
)


@pytest.mark.parametrize("sample", SAMPLES)
def test_extract_matches_expected(sample):
    image_path = FIXTURES_DIR / f"{sample}.jpg"
    if not image_path.exists():
        pytest.skip(f"ไม่พบ {image_path} — ดูวิธีเตรียมรูปใน tests/fixtures/README.md")

    expected = json.loads((FIXTURES_DIR / f"{sample}_expected.json").read_text(encoding="utf-8"))
    result = extract_from_path(image_path)

    assert result.is_result_board is True
    assert len(result.rockets) == len(expected["rockets"])
    for actual_rocket, expected_rocket in zip(result.rockets, expected["rockets"]):
        assert actual_rocket.rocket_name == expected_rocket["rocket_name"]
        assert actual_rocket.outcome_icon == expected_rocket["outcome_icon"]
        assert actual_rocket.is_champion == expected_rocket["is_champion"]
