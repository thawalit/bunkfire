import base64

from pydantic import BaseModel

import config
from vision.image_utils import guess_media_type
from vision.prompts import SYSTEM_PROMPT
from vision.schema import ExtractionResult

# หมายเหตุ: import anthropic แบบ lazy (ในฟังก์ชัน) ไม่ใช่ระดับโมดูล — หน้า Upload & Check
# ต้อง import โมดูลนี้เพื่อใช้ฟีเจอร์ "วางรายชื่อ -> ทำนาย" ซึ่งไม่ต้องใช้ anthropic
# ถ้า anthropic ไม่พร้อม (เช่นไม่ได้ติดตั้ง) หน้าเว็บส่วนที่เหลือต้องยังทำงานได้


class RocketNames(BaseModel):
    rocket_names: list[str]


NAMES_ONLY_PROMPT = (
    "รูปนี้เป็นตารางรายชื่อบั้งไฟที่จะแข่ง (อาจยังไม่มีผลการแข่งขัน) "
    "อ่านเฉพาะ 'ชื่อบั้งไฟ' ในแต่ละแถวออกมาเป็นรายการเรียงตามลำดับในรูป "
    "เอาเฉพาะชื่อบั้งไฟเท่านั้น ไม่ต้องอ่านตัวเลข เกณฑ์ หรือผลแพ้ชนะ "
    "รักษาตัวสะกดภาษาไทยให้ตรงกับในรูปทุกตัวอักษร ห้ามเดา/เติมชื่อที่ไม่มีในรูป"
)

_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic  # lazy: โหลดเฉพาะตอนเรียกใช้ Vision จริง

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
        max_tokens=8192,  # ตารางผลที่มีบั้งไฟหลายสิบแถวทำให้ JSON เกิน 4096 tokens แล้วถูกตัดกลางคัน
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


def extract_rocket_names(
    image_bytes: bytes, media_type: str = "image/jpeg", model: str = config.VISION_MODEL
) -> list[str]:
    """อ่านเฉพาะ 'ชื่อบั้งไฟ' จากรูปตารางแข่ง — ใช้กับตารางที่ยังไม่มีผลเพื่อเอาไปทำนาย"""
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    client = _get_client()
    response = client.messages.parse(
        model=model,
        max_tokens=2048,
        system=NAMES_ONLY_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_b64},
                },
                {"type": "text", "text": "อ่านชื่อบั้งไฟทุกแถวจากรูปนี้"},
            ],
        }],
        output_format=RocketNames,
    )
    # ตัดชื่อว่าง/ช่องว่างเกินออก และคงลำดับเดิม
    return [n.strip() for n in response.parsed_output.rocket_names if n and n.strip()]
