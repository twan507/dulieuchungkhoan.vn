"""Registry WiChart: hai chủ sở hữu (khối §9 của wichart.md · bảng mã trong module) phải khớp từng series."""
import dataclasses
import pathlib
from decimal import Decimal

import pytest

from etl import wichart_registry as wr


def _by_key_idx(series):
    return {(s.key, s.idx): s for s in series}


def test_build_resolves_53_macro_and_52_asset_series():
    series = wr.build()
    dom = {"macro": 0, "asset": 0}
    for s in series:
        dom[s.domain] += 1
    assert dom == {"macro": 53, "asset": 52}
    assert len({s.code for s in series}) == 105                       # mã không trùng
    assert sum(1 for s in series if s.role == "growth_ref") == 13


def test_dead_series_and_tier_x_keys_are_absent():
    m = _by_key_idx(wr.build())
    assert ("xang_dau", 0) not in m and ("xang_dau", 1) in m           # RON 95 chết, E5 sống
    assert ("ncp", 1) not in m and ("ncp", 0) in m and ("ncp", 2) in m
    assert not {k for k, _ in m} & {"thiec", "cao_su", "gdpbinhquan", "gao_tpxk", "xi_mang", "da_1x2"}
    assert ("ca_tra", 0) in m                                          # sống lại 22/08, đo 2026-09-05


def test_td_maps_to_credit_by_key_not_by_source_name():
    m = _by_key_idx(wr.build())
    assert m[("td", 0)].code == "vn.credit" and m[("td", 0)].doc_name == "Tổng tín dụng"
    assert m[("hd", 0)].code == "vn.deposits"
    assert "NAMEWRONG" in m[("td", 0)].flags


def test_scale_and_unit_come_from_the_doc_or_ours_as_designed():
    m = _by_key_idx(wr.build())
    assert m[("vang", 0)].scale == Decimal("1000") and m[("vang", 0)].code == "gold.sjc_buy"
    assert m[("vai_cotton_my", 0)].scale == Decimal("0.01") and m[("vai_cotton_my", 0)].unit == "USD/lb"
    assert m[("gdp", 0)].scale == Decimal("1000000000") and m[("gdp", 0)].unit == "VND"
    assert m[("gdp", 2)].role == "growth_ref" and m[("gdp", 2)].code == "vn.gdp.growth"
    assert m[("dau_wti", 0)].price_type == "futures" and m[("dhtg", 0)].price_type == "fixing"
    assert m[("dhtg", 3)].price_type == "spot" and m[("dhtg", 3)].external_sub == "3"
    assert all(s.calendar == "trading_days" for s in m.values() if s.domain == "asset")


def test_build_raises_when_module_maps_a_series_the_doc_does_not_collect(tmp_path):
    md = wr.WICHART_MD.read_text(encoding="utf-8")
    broken = md.replace('("Giá xăng E5","VND/lít",1e3,D,[])', '("Giá xăng E5","VND/lít",1e3,None,["DEAD"])')
    assert broken != md
    p = tmp_path / "wichart.md"
    p.write_text(broken, encoding="utf-8")
    with pytest.raises(wr.RegistryError, match=r"xang_dau\[1\]"):
        wr.build(p)


def test_build_raises_when_doc_collects_a_series_the_module_lacks(monkeypatch):
    trimmed = {k: v for k, v in wr.MACRO.items() if k != ("cpi", 0)}
    monkeypatch.setattr(wr, "MACRO", trimmed)
    with pytest.raises(wr.RegistryError, match=r"cpi\[0\]"):
        wr.build()


def test_key_groups_lists_each_key_once_with_its_namespace():
    kg = dict(wr.key_groups(wr.build()))
    assert len(kg) == 68
    assert kg["cpi"] == "vi_mo" and kg["vang"] == "hang_hoa" and kg["dhtg"] == "vi_mo"
