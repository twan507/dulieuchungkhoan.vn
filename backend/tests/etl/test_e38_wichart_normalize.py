"""Expected là literal đọc tay từ fixture (chụp 2026-09-05) hoặc giải tay — không tính lại theo code."""
import dataclasses
import json
import pathlib
from datetime import date
from decimal import Decimal

import pytest

from etl import wichart_normalize as wn
from etl import wichart_registry as wr

FIX = pathlib.Path(__file__).parent / "fixtures" / "wichart"
REG = {(s.key, s.idx): s for s in wr.build()}


def _series(key):
    return json.loads((FIX / f"{key}.json").read_text(encoding="utf-8"))["chart"]["series"]


def _last(points):
    return max(points, key=lambda p: p.obs_date)


def test_month_anchors_on_day_one_in_vietnam_time_not_utc():
    pts = wn.series_points(REG[("cpi", 0)], _series("cpi"))
    last = _last(pts)
    assert last.obs_date == date(2026, 8, 1) and last.value == Decimal("4.45")   # epoch 1785517200000 = 01/08 00:00 VN
    assert last.obs_date != date(2026, 7, 31)                                  # parse UTC sẽ ra 31/07
    assert last.domain == "macro" and last.code == "vn.cpi" and last.price_type is None


def test_quarter_anchors_on_first_month_of_the_quarter_and_scale_1e9():
    pts = wn.series_points(REG[("gdp", 0)], _series("gdp"))
    last = _last(pts)
    assert last.obs_date == date(2026, 4, 1)                                    # nguồn neo 01/06 = Q2
    assert last.value == Decimal("3479487.23") * Decimal("1000000000")          # 3,479,487.23 tỷ VND
    growth = _last(wn.series_points(REG[("gdp", 2)], _series("gdp")))
    assert growth.value == Decimal("8") and growth.code == "vn.gdp.growth"      # 0.08 × 100


def test_year_anchors_on_january_first_even_when_source_anchors_december():
    last = _last(wn.series_points(REG[("ds", 0)], _series("ds")))
    assert last.obs_date == date(2025, 1, 1) and last.value == Decimal("102345320")   # 102,345.32 nghìn người


def test_td_is_credit_even_though_source_names_it_deposits():
    pts = wn.series_points(REG[("td", 0)], _series("td"))
    assert pts and all(p.code == "vn.credit" for p in pts)
    assert _last(pts).value == Decimal("20150411") * Decimal("1000000000")


def test_asset_scale_and_unit_gold_cotton_fuel():
    gold = _last(wn.series_points(REG[("vang", 0)], _series("vang")))
    assert gold.value == Decimal("145600000") and gold.code == "gold.sjc_buy" and gold.price_type == "spot"
    cotton = _last(wn.series_points(REG[("vai_cotton_my", 0)], _series("vai_cotton_my")))
    assert cotton.value == Decimal("0.8233") and cotton.obs_date == date(2026, 9, 4)
    e5 = _last(wn.series_points(REG[("xang_dau", 1)], _series("xang_dau")))
    assert e5.value == Decimal("22480") and e5.code == "gasoline_e5_vn"


def test_weekend_point_equal_to_previous_is_dropped_but_a_different_one_is_kept():
    by_date = {p.obs_date: p.value for p in wn.series_points(REG[("lua", 0)], _series("lua"))}
    assert date(2024, 10, 5) not in by_date and by_date[date(2024, 10, 4)] == Decimal("8458")   # T7 chép lại T6
    assert by_date[date(2025, 3, 23)] == Decimal("7029")                                        # CN khác T7 (6750)
    gold = {p.obs_date: p.value for p in wn.series_points(REG[("vang_the_gioi", 0)], _series("vang_the_gioi"))}
    assert date(2024, 11, 16) not in gold and gold[date(2024, 11, 15)] == Decimal("2561.24")
    assert gold[date(2024, 9, 8)] == Decimal("2496.93")
    fx = {p.obs_date: p.value for p in wn.series_points(REG[("dhtg", 0)], _series("dhtg"))}
    assert date(2025, 1, 25) not in fx and fx[date(2025, 4, 26)] == Decimal("24963")


def test_weekday_repeat_is_kept_and_macro_weekend_is_kept():
    lua = {p.obs_date: p.value for p in wn.series_points(REG[("lua", 0)], _series("lua"))}
    # 27/08 và 26/08/2026 đều 7550 (điểm cuối fixture) — chép lại TRONG TUẦN phải giữ
    assert lua[date(2026, 8, 27)] == Decimal("7550") and lua[date(2026, 8, 26)] == Decimal("7550")
    # macro chuỗi ngày: điểm T7 bằng T6 vẫn giữ (không áp luật cuối tuần)
    s = dataclasses.replace(REG[("lslnh", 0)])
    api = [{"name": "LS qua đêm liên ngân hàng", "unit": "%",
            "data": [[1756400400000, 4.1], [1756486800000, 4.1], [1756573200000, 4.1]]}]   # 29/08 T6 · 30/08 T7 · 31/08 CN 2025
    pts = wn.series_points(s, api)
    assert [p.obs_date for p in pts] == [date(2025, 8, 29), date(2025, 8, 30), date(2025, 8, 31)]


def test_name_mismatch_freq_mismatch_band_and_bad_anchor_raise_with_reason():
    with pytest.raises(wn.SeriesError) as e:
        wn.series_points(REG[("cpi", 0)], [{"name": "Lạm phát lõi", "data": [[1785517200000, 4.45]]}])
    assert e.value.reason == "shape"
    with pytest.raises(wn.SeriesError) as e:
        wn.series_points(dataclasses.replace(REG[("cpi", 0)], freq="d"), _series("cpi"))
    assert e.value.reason == "freq"
    with pytest.raises(wn.SeriesError) as e:                                   # 141.3 × 1e3 = 141.300 < 1e7
        wn.series_points(REG[("vang", 0)], [{"name": "Giá vàng mua vào", "data": [[1788454800000, 141.3]]},
                                           {"name": "Giá vàng bán ra", "data": [[1788454800000, 148.6]]}])
    assert e.value.reason == "band"
    with pytest.raises(wn.SeriesError) as e:                                   # quý neo tháng 5 — không phải tháng cuối quý
        wn.series_points(REG[("tn", 0)], [{"name": "Tỷ lệ thất nghiệp", "data": [[1777568400000, 2.2]]}])  # 01/05/2026 VN
    assert e.value.reason == "shape"
    with pytest.raises(wn.SeriesError) as e:
        wn.series_points(REG[("vang", 1)], [{"name": "Giá vàng mua vào", "data": [[1, 1]]}])   # thiếu series [1]
    assert e.value.reason == "shape"


def test_real_freq_and_anchor_helpers():
    assert wn.real_freq([0, 86_400_000, 2 * 86_400_000]) == "d"
    assert wn.real_freq([1785517200000, 1782838800000, 1780246800000]) == "m"
    assert wn.real_freq([0, 1]) is None
    assert wn.anchor(date(2026, 6, 1), "q") == date(2026, 4, 1)
    assert wn.anchor(date(2025, 12, 31), "y") == date(2025, 1, 1)
    assert wn.anchor(date(2026, 8, 15), "m") == date(2026, 8, 1)
    assert wn.anchor(date(2026, 9, 4), "d") == date(2026, 9, 4)
