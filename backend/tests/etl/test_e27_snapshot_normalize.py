import json
import pathlib

from etl import snapshot_normalize as sn

FIX = pathlib.Path(__file__).parent / "fixtures" / "snapshot"


def _item(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))["items"][0]


def test_keep_of_a_non_bank_snapshot_has_fifteen_fields_and_the_newest_year():
    """Phi ngân hàng KHÔNG có rtq44/rtq137/rqq41 (đo 9/9 mã) ⇒ 15 chứ không 18, và đó không phải lỗi."""
    got = sn.keep("snapshot", _item("A32-snapshot.json"))
    assert len(got) == 15
    assert got["ceo"] == "Ngô Thành Thắng"
    assert got["outstandingShare"] == 6800000.0
    assert got["valuePerShare"] == 2500.0
    assert got["statePercentage"] == 0.51
    assert got["rtq10"] == 1.12836626
    assert got["year"] == 2025 and got["quarter"] == 0        # yearly mới nhất, KHÔNG phải [0]=2020
    assert "rtq44" not in got


def test_keep_of_a_bank_snapshot_has_eighteen_fields_and_the_newest_quarter():
    got = sn.keep("snapshot", _item("BAB-snapshot-bank-status0.json"))
    assert len(got) == 18
    assert got["ceo"] == "Thái Hương"
    assert got["rtq10"] == 14.60120886
    assert got["year"] == 2026 and got["quarter"] == 2        # quarterly mới nhất, KHÔNG phải [0]=2024Q2
    assert got["rtq44"] == 0.02058553 and got["rtq137"] == 0.0113022 and got["rqq41"] == 0.10735799


def test_keep_of_snapshot_leaves_out_every_field_computed_from_price():
    got = sn.keep("snapshot", _item("A32-snapshot.json"))
    for code in ("rtd11", "rtd14", "rtd21", "rtd25", "rtd53",
                 "highestPrice1Year", "lowestPrice1Year", "averageMatchVolume1Month",
                 "foreignerPercentage", "foreignerRoom", "freeFloatRate"):
        assert code not in got


def test_keep_of_valuation_takes_the_forecast_block_and_drops_the_sector_list():
    got = sn.keep("valuation", _item("A32-valuation.json"))
    assert got["riskFreeRate"] == 0.04337
    assert got["recommendMethod"] == "PE"
    assert got["rtd7"] == 33937.05626397
    assert got["rtq180"] == -25807827544.0
    assert got["estimatedEPS"] is None                        # trường dự phóng rỗng vẫn phải vào hash
    assert "valuationSector" not in got and "vnIndexEquityRisk" not in got and "rtd35" not in got


def test_keep_of_dividend_drops_the_two_ratios_that_move_with_price():
    got = sn.keep("dividend", _item("A32-dividend.json"))
    assert set(got) == {"cashDividendPayouts", "cashDividendPlans", "dps", "dividendPayoutRatio", "eps"}
    assert len(got["cashDividendPayouts"]) == 20
    assert got["dps"]["ratioYears"][0] == {"yearReport": 2025, "ratioValue": 2500.0}


def test_keep_of_ownership_takes_the_four_blocks():
    got = sn.keep("ownership", _item("A32-ownership.json"))
    assert [len(got[k]) for k in ("overviewChartData", "majorOwnershipsChartData",
                                  "majorShareHolders", "boardOfDirectors")] == [3, 5, 11, 10]


def test_hash_ignores_a_field_that_moves_with_price():
    """Tính chất, không tautology: đổi rtd11 (vốn hoá) thì hash PHẢI đứng yên."""
    item = _item("A32-snapshot.json")
    before = sn.keep_hash("snapshot", item)
    item["summary"]["rtd11"] = 999_000_000_000.0
    item["summary"]["rtd21"] = 42.0
    assert sn.keep_hash("snapshot", item) == before


def test_hash_reacts_to_a_field_inside_the_allowlist():
    item = _item("A32-snapshot.json")
    before = sn.keep_hash("snapshot", item)
    item["summary"]["outstandingShare"] = 7_000_000.0
    assert sn.keep_hash("snapshot", item) != before


def test_hash_reacts_to_a_new_report_arriving():
    item = _item("BAB-snapshot-bank-status0.json")
    before = sn.keep_hash("snapshot", item)
    item["quarterly"].append(dict(item["quarterly"][-1], year=2026, quarter=3, rtq44=0.02))
    assert sn.keep_hash("snapshot", item) != before


def test_hash_ignores_a_key_the_source_adds_later():
    item = _item("A32-ownership.json")
    before = sn.keep_hash("ownership", item)
    item["truongMoiCuaNguon"] = {"gi": "do"}
    assert sn.keep_hash("ownership", item) == before


def test_hash_is_stable_across_key_order():
    item = _item("A32-dividend.json")
    reordered = {k: item[k] for k in reversed(list(item))}
    assert sn.keep_hash("dividend", reordered) == sn.keep_hash("dividend", item)
