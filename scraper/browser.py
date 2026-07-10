from contextlib import contextmanager

from playwright.sync_api import BrowserContext, sync_playwright

from scraper.auth import load_storage_state_path

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
VIEWPORT = {"width": 1366, "height": 900}


@contextmanager
def headless_context():
    """เปิด Chromium headless พร้อม session ที่บันทึกไว้จาก one_time_login.py"""
    storage_state = load_storage_state_path()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=storage_state, user_agent=USER_AGENT, viewport=VIEWPORT
        )
        try:
            yield context
        finally:
            context.close()
            browser.close()


def is_login_redirect(context: BrowserContext, url: str) -> bool:
    return "/login" in url or "checkpoint" in url
