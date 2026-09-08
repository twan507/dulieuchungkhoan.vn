from datetime import date, datetime, timezone

import pytest

from core.clock import VN, today_vn


def test_today_vn_is_the_next_day_while_utc_is_still_the_evening_before():
    # 2026-09-07 17:30 UTC = 2026-09-08 00:30 giờ VN — đúng cửa sổ 00:00–07:00 từng làm hai test đỏ
    assert today_vn(datetime(2026, 9, 7, 17, 30, tzinfo=timezone.utc)) == date(2026, 9, 8)


def test_today_vn_keeps_a_vn_datetime():
    assert today_vn(datetime(2026, 9, 8, 0, 30, tzinfo=VN)) == date(2026, 9, 8)


def test_today_vn_rejects_naive_input():
    with pytest.raises(ValueError):
        today_vn(datetime(2026, 9, 8, 0, 30))
