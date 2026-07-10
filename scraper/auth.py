from pathlib import Path

from playwright.sync_api import BrowserContext

import config


class SessionExpiredError(Exception):
    """FB session หมดอายุ/ยังไม่ได้ login — ต้องรัน scripts/one_time_login.py ใหม่"""


def storage_state_exists(path: Path = config.FB_STATE_PATH) -> bool:
    return path.exists()


def save_storage_state(context: BrowserContext, path: Path = config.FB_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(path))
    path.chmod(0o600)


def load_storage_state_path(path: Path = config.FB_STATE_PATH) -> str:
    if not path.exists():
        raise SessionExpiredError(
            f"ไม่พบไฟล์ session ที่ {path} — รัน `python scripts/one_time_login.py` ก่อน"
        )
    return str(path)
