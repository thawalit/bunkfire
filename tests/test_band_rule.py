from vision.band_rule import classify, compute_and_classify, compute_tie_band, infer_tie_band


def test_win_above_band():
    assert compute_and_classify(40, 80, 425) == "win"


def test_win_close_case_from_sample():
    assert compute_and_classify(40, 80, 420) == "win"


def test_tie_within_band():
    assert compute_and_classify(20, 60, 330) == "tie"


def test_loss_below_band():
    assert compute_and_classify(30, 60, 310) == "loss"


def test_wrap_high_hundred_still_loss():
    # (40/00) -> band [340, 400], achieved 240 -> loss
    assert compute_and_classify(40, 0, 240) == "loss"


def test_wrap_high_hundred_win():
    # (55/05) -> band [355, 405], achieved 415 -> win
    assert compute_and_classify(55, 5, 415) == "win"


def test_wrap_high_hundred_tie_at_boundary():
    # (50/00) -> band [350, 400], achieved 400 -> tie (ขอบบนพอดี รวมขอบ)
    assert compute_and_classify(50, 0, 400) == "tie"


def test_tie_at_lower_boundary():
    low, high = compute_tie_band(30, 70, base_hundred=300)
    assert (low, high) == (330, 370)
    assert compute_and_classify(30, 70, 330) == "tie"


def test_missing_value_is_tie():
    assert compute_and_classify(30, 60, None) == "tie"


def test_no_wrap_needed_when_b_greater_than_a():
    low, high = compute_tie_band(20, 45, base_hundred=300)
    assert (low, high) == (320, 345)


# --- infer_tie_band: เลือกหลักร้อยให้ตรงกับไอคอนสีในภาพ ---

def test_rule1_5000_means_350_400():
    # กติกาข้อ 1: ราคา 50/00 หมายถึง 350-400 (base 300 + ทบหลักร้อย)
    _, low, high = infer_tie_band(50, 0, achieved=380, outcome_icon="tie")
    assert (low, high) == (350, 400)


def test_rule2_5090_score320_green_icon_is_250_290():
    # กติกาข้อ 2: ราคา 50/90 score 320 ไอคอนถูกเขียว -> ที่จริงคือ 250-290 (ยึด icon)
    base, low, high = infer_tie_band(50, 90, achieved=320, outcome_icon="win")
    assert (base, low, high) == (200, 250, 290)
    assert classify(320, low, high) == "win"


def test_infer_two_digit_price_base_200_from_real_data():
    # 20/40 score 265 ไอคอนถูก -> 220-240 (ไม่ใช่ 320-340 ที่ base 300)
    _, low, high = infer_tie_band(20, 40, achieved=265, outcome_icon="win")
    assert (low, high) == (220, 240)


def test_infer_full_three_digit_price_no_base_added():
    # Vision อ่านราคาเต็ม 3 หลักมาแล้ว (310/340) -> แถบคือ 310-340 ตรงๆ ไม่บวกหลักร้อย
    base, low, high = infer_tie_band(310, 340, achieved=330, outcome_icon="tie")
    assert (base, low, high) == (0, 310, 340)


def test_infer_three_digit_low_two_digit_high():
    # ราคา 280/90 = 280-290 (B ย่อ 2 หลักของหลักร้อยเดียวกับ A), ไม่ใช่แถบกลับหัว 280-190
    base, low, high = infer_tie_band(280, 90, achieved=215, outcome_icon="loss")
    assert (base, low, high) == (0, 280, 290)
    assert classify(215, low, high) == "loss"


def test_infer_three_digit_low_wraps_hundred():
    # 290/10 = 290-310 (B<A ในหลักร้อยเดียวกัน จึงทบหลักร้อย)
    _, low, high = infer_tie_band(290, 10, achieved=305, outcome_icon="win")
    assert (low, high) == (290, 310)


def test_infer_falls_back_to_default_when_no_icon():
    # ไม่มีไอคอน/ค่าที่ทำได้ -> ใช้ base ตั้งต้น (2 หลัก = 300)
    _, low, high = infer_tie_band(30, 70, achieved=None, outcome_icon=None)
    assert (low, high) == (330, 370)
