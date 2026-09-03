# backend/tests/etl/test_e17_events_normalize.py
import json
import pathlib
from datetime import date

from etl import events_normalize as en

FIX = pathlib.Path(__file__).parent / "fixtures" / "events"


def pages(*families):
    """Dựng đúng hình dạng events_fetch trả về: {event_type: [text từng trang]}."""
    name = {"AGM": "agm", "CashDividend": "cashdividend", "StockDividend": "stockdividend",
            "Earning": "earning", "IPO": "ipo", "ShareIssuance": "shareissuance"}
    return {f: [(FIX / f"{name[f]}-sample-20260903.json").read_text(encoding="utf-8")]
            for f in families}


ALL = ("AGM", "CashDividend", "StockDividend", "Earning", "IPO", "ShareIssuance")


def test_public_date_with_a_time_part_truncates_to_the_date():
    n = en.normalize(pages("AGM"))
    sasteco = [r for r in n.rows if r.organ_code == "SASTECO"]
    # Nguồn trả '2018-03-27T11:03:28.023' VÀ '2018-03-27T00:00:00' — cùng một ngày công bố
    assert len(sasteco) == 1 and sasteco[0].public_date == date(2018, 3, 27)
    assert n.dup_conflicts == 1


def test_agm_stage_key_is_the_meeting_date_so_two_convocations_stay_apart():
    n = en.normalize(pages("AGM"))
    shx = sorted(r.stage_key for r in n.rows if r.organ_code == "SHX")
    assert shx == ["2022-10-18", "2022-12-23"]        # hai lần triệu tập, giữ cả hai


def test_cash_dividend_stage_key_carries_dividend_year():
    n = en.normalize(pages("CashDividend"))
    sd9 = sorted(r.stage_key for r in n.rows if r.organ_code == "SD9")
    assert sd9 == ["2019|Cả năm", "2021|Cả năm"]      # trả bù hai kỳ cùng ngày ⇒ 2 dòng
    assert len(n.rows) == 6 and n.dup_conflicts == 0


def test_share_issuance_keeps_the_record_that_has_a_listing_date():
    n = en.normalize(pages("ShareIssuance"))
    abi = [r for r in n.rows if r.organ_code == "ABI"]
    assert len(abi) == 2                              # hai issueMethodName, mỗi cái một dòng
    assert all(r.payload["listingDate"] == "2025-10-17T00:00:00" for r in abi)
    vic = [r for r in n.rows if r.organ_code == "VIC"]
    assert sorted(r.payload["planVolumn"] for r in vic) == [-27460872.0, 56155405.0]


def test_identical_duplicate_records_collapse_to_one():
    n = en.normalize(pages("StockDividend"))
    assert len(n.rows) == 3 and n.dup_conflicts == 1


def test_name_hint_falls_back_to_ticker_when_no_name_field_exists():
    n = en.normalize(pages("ShareIssuance"))
    ryg = next(r for r in n.rows if r.organ_code == "12681")
    assert ryg.name_hint == "RYG"                     # họ này không trả trường tên nào
    agm = next(r for r in en.normalize(pages("AGM")).rows if r.organ_code == "QNC")
    assert agm.name_hint == "Xi măng Quảng Ninh"


def test_earning_maps_report_period_and_has_no_stage_key():
    n = en.normalize(pages("Earning"))
    dic = next(r for r in n.rows if r.organ_code == "DIC")
    assert (dic.year_report, dic.length_report, dic.stage_key) == (2026, 2, None)
    assert dic.exright_date is None and dic.public_date == date(2026, 8, 19)


def test_source_url_only_present_on_agm():
    assert all(r.source_url for r in en.normalize(pages("AGM")).rows)
    assert all(r.source_url is None for r in en.normalize(pages("CashDividend")).rows)


def test_whole_fixture_set_yields_the_measured_totals():
    n = en.normalize(pages(*ALL))
    assert len(n.rows) == 24 and n.dup_conflicts == 4
    assert n.counts == {"AGM": 6, "CashDividend": 6, "StockDividend": 4,
                        "Earning": 3, "IPO": 2, "ShareIssuance": 7}
    assert n.collected == n.counts
    assert len({r.organ_code for r in n.rows}) == 17
