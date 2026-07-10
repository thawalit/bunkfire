import base64

import anthropic

import config
from vision.image_utils import guess_media_type
from vision.prompts import SYSTEM_PROMPT
from vision.schema import ExtractionResult

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY or None)
    return _client


def extract(image_bytes: bytes, media_type: str = "image/jpeg", model: str = config.VISION_MODEL) -> ExtractionResult:
    """ส่งรูปเดียวให้ Claude Vision จำแนก+สกัดข้อมูลพร้อมกันในคำขอเดียว

    ฟังก์ชันนี้ไม่แตะ DB — เรียกตรงๆ ได้เพื่อทดสอบกับรูปตัวอย่างโดยไม่ต้องมี scraper/DB
    """
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    client = _get_client()
    response = client.messages.parse(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_b64},
                },
                {"type": "text", "text": "อ่านและสกัดข้อมูลจากรูปนี้ตามคำสั่ง"},
            ],
        }],
        output_format=ExtractionResult,
    )
    return response.parsed_output


def extract_from_path(path, model: str = config.VISION_MODEL) -> ExtractionResult:
    from pathlib import Path

    p = Path(path)
    return extract(p.read_bytes(), media_type=guess_media_type(p), model=model)
