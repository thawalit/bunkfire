import hashlib
import mimetypes
from pathlib import Path


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def guess_media_type(path: Path) -> str:
    media_type, _ = mimetypes.guess_type(str(path))
    return media_type or "image/jpeg"


def load_image_bytes(path: Path) -> bytes:
    return path.read_bytes()
