from vision.band_rule import compute_and_classify, compute_tie_band


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
