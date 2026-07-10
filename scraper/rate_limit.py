import random
import time


def jittered_sleep(min_seconds: float = 2.0, max_seconds: float = 6.0) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


class PerRunCap:
    """จำกัดจำนวนโพสต์ที่ประมวลผลได้ในรอบเดียว เพื่อลดความเสี่ยงถูกบล็อกและคุมค่าใช้จ่าย"""

    def __init__(self, max_count: int):
        self.max_count = max_count
        self.count = 0

    def can_continue(self) -> bool:
        return self.count < self.max_count

    def record(self) -> None:
        self.count += 1
