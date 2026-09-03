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


def test_organ_name_and_ticker_stay_separate_fields():
    """Không ép sẵn thành một `name_hint`: ba họ không trả tên nào, gộp sớm thì thứ tự
    vòng lặp họ quyết định tên doanh nghiệp (xem `events_store.ensure_issuers`)."""
    ryg = next(r for r in en.normalize(pages("ShareIssuance")).rows if r.organ_code == "12681")
    assert ryg.organ_name is None and ryg.ticker == "RYG"      # họ này không có trường tên
    qnc = next(r for r in en.normalize(pages("AGM")).rows if r.organ_code == "QNC")
    assert qnc.organ_name == "Xi măng Quảng Ninh" and qnc.ticker == "QNC"


def test_earning_maps_report_period_and_has_no_stage_key():
    n = en.normalize(pages("Earning"))
    dic = next(r for r in n.rows if r.organ_code == "DIC")
    assert (dic.year_report, dic.length_report, dic.stage_key) == (2026, 2, None)
    assert dic.exright_date is None and dic.public_date == date(2026, 8, 19)


def test_source_url_only_present_on_agm():
    assert all(r.source_url for r in en.normalize(pages("AGM")).rows)
    assert all(r.source_url is None for r in en.normalize(pages("CashDividend")).rows)


def test_cash_dividend_maps_all_four_date_columns():
    """Seam 1 cho ĐỦ cột: ba test trên chỉ chạm public_date/stage_key, còn record_date và
    payout_date thì không test nào assert — mà kho thật có hơn 20.000 dòng mỗi cột."""
    n = en.normalize(pages("CashDividend"))
    thn = next(r for r in n.rows if r.organ_code == "THANHHOAWATER")
    assert (thn.public_date, thn.exright_date, thn.record_date, thn.payout_date) == (
        date(2026, 8, 13), date(2026, 8, 20), date(2026, 8, 21), date(2026, 8, 28))
    assert thn.year_report is None and thn.length_report is None


def test_ipo_maps_public_date_and_carries_the_raw_payload():
    """Họ IPO trước nay chỉ được đếm trong tổng số, không có assert cột nào."""
    n = en.normalize(pages("IPO"))
    xdc = next(r for r in n.rows if r.organ_code == "0304941312")     # organCode là MÃ SỐ THUẾ
    assert xdc.public_date == date(2022, 9, 8)
    assert xdc.exright_date is None and xdc.stage_key is None
    assert xdc.payload["listingDate"] == "2022-10-21T09:00:00"        # giữ nguyên trong payload


def test_dup_keys_name_the_colliding_keys_not_just_count_them():
    """§5.3 bài học 3: bộ đếm không nêu tên thì để suốt buổi không biết mã nào."""
    n = en.normalize(pages(*ALL))
    assert len(n.dup_keys) == 4
    assert sum(1 for k in n.dup_keys if k.startswith("ShareIssuance|ABI|")) == 2
    assert any(k.startswith("AGM|SASTECO|2018-03-27|") for k in n.dup_keys)
    assert any(k.startswith("StockDividend|ABI|2025-09-04|") for k in n.dup_keys)


def test_whole_fixture_set_yields_the_measured_totals():
    n = en.normalize(pages(*ALL))
    assert len(n.rows) == 24 and n.dup_conflicts == 4
    assert n.counts == {"AGM": 6, "CashDividend": 6, "StockDividend": 4,
                        "Earning": 3, "IPO": 2, "ShareIssuance": 7}
    assert n.collected == n.counts
    assert len({r.organ_code for r in n.rows}) == 17
