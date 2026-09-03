import json, pathlib

from etl import screener_guard as sg
from etl import screener_normalize as sn

FIX = pathlib.Path(__file__).parent / "fixtures" / "screener"


def test_preopen_real_sample_is_refused_as_non_trading_day():
    res = sn.normalize([(FIX / "page1-20260903-preopen.json").read_text(encoding="utf-8")])
    priced = sum(1 for r in res.rows if r.close_price > 0)
    v = sg.check(total_count=30, collected=30, priced=priced, unmapped=0, baseline_items=None)
    assert v.ok is False
    assert v.reasons == ("chỉ 0/30 mã có closePrice > 0 — không phải ngày giao dịch",)


def test_postclose_real_sample_passes_without_baseline():
    res = sn.normalize([(FIX / "page1-20260828-postclose.json").read_text(encoding="utf-8")])
    priced = sum(1 for r in res.rows if r.close_price > 0)
    assert priced == 30
    assert sg.check(total_count=30, collected=30, priced=priced, unmapped=0, baseline_items=None).ok is True


def test_drop_against_baseline_refuses_beyond_two_percent():
    assert sg.check(1545, 1545, 1500, 0, baseline_items=1600).ok is False      # sụt 3,4%
    assert sg.check(1545, 1545, 1500, 0, baseline_items=1560).ok is True       # sụt 1,0%


def test_incomplete_pages_refused():
    v = sg.check(total_count=1545, collected=1515, priced=1500, unmapped=0, baseline_items=None)
    assert v.ok is False and "1515" in v.reasons[0] and "1545" in v.reasons[0]


def test_unmapped_ratio_refused_beyond_two_percent():
    assert sg.check(1545, 1545, 1500, unmapped=40, baseline_items=None).ok is False   # 2,6%
    assert sg.check(1545, 1545, 1500, unmapped=30, baseline_items=None).ok is True    # 1,9%


def test_priced_ratio_boundary():
    """Vế (i) là TỶ LỆ ≥ 50 %: một nhúm mã có giá không đủ mở cửa cho cả bộ 1.545 dòng.

    Ngưỡng tính tay: 1.545 × 0,5 = 772,5 ⇒ 772 (49,97 %) từ chối, 773 (50,03 %) qua.
    """
    assert sg.check(1545, 1545, 772, 0, None).ok is False
    assert sg.check(1545, 1545, 773, 0, None).ok is True


def test_unknown_com_group_ratio_refused_beyond_two_percent():
    """Vế (iv): nguồn đổi tên sàn thì mất trọn một sàn — không được im lặng."""
    assert sg.check(1545, 1545, 1500, 0, None, unknown=40).ok is False    # 2,6%
    assert sg.check(1545, 1545, 1500, 0, None, unknown=30).ok is True     # 1,9%
