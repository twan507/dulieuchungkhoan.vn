import json
import pathlib
from datetime import date
from decimal import Decimal

from etl import price_normalize as pn

FIX = pathlib.Path(__file__).parent / "fixtures" / "price"


def text(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_maps_the_five_columns_and_the_date_from_the_real_first_row():
    rows, dups = pn.normalize_code("BID", [text("bid-page1-20260903.json")])
    r = rows[0]
    assert (r.organ_code, r.trading_date) == ("BID", date(2026, 9, 3))
    assert (r.close_adj, r.close_raw) == (Decimal("36450"), Decimal("36450"))
    assert (r.open_value, r.highest_value, r.lowest_value) == (Decimal("36750"), Decimal("36750"), Decimal("36400"))
    assert r.payload["totalMatchVolume"] == 3267266.0 and len(r.payload) == 99
    assert len(rows) == 5 and rows[-1].trading_date == date(2026, 8, 25) and dups == 0


def test_deep_row_keeps_adjusted_and_raw_close_apart():
    rows, _ = pn.normalize_code("BID", [text("bid-page52-20260903.json")])
    assert rows[0].trading_date == date(2014, 6, 3)
    assert rows[0].close_adj == Decimal("5747.8202873773")      # closeValue — đã điều chỉnh, giữ đủ chữ số
    assert rows[0].close_raw == Decimal("14500")                # closePrice — thô


def test_dividend_rows_match_the_dividend_slice_2_recorded():
    rows, _ = pn.normalize_code("MWJSC", [text("dmx-page1-20260903.json")])
    by = {r.trading_date: r for r in rows}
    before, on = by[date(2026, 8, 17)], by[date(2026, 8, 18)]
    assert (before.close_raw, before.close_adj) == (Decimal("88500"), Decimal("84499.8"))
    assert on.close_raw == on.close_adj == Decimal("83000")
    assert len(rows) == 18


def test_overlapping_pages_keep_the_first_seen_row_and_count_duplicates():
    page = json.loads(text("bid-page1-20260903.json"))
    # trang "cũ hơn" chồng hai ngày với trang 1, mang closeValue khác — phải bị bỏ
    older = {**page, "items": [{**page["items"][4], "closeValue": 1.0}, {**page["items"][0], "closeValue": 2.0}]}
    rows, dups = pn.normalize_code("BID", [text("bid-page1-20260903.json"), json.dumps(older)])
    got = {r.trading_date: r.close_adj for r in rows}
    assert dups == 2 and len(rows) == 5
    assert got[date(2026, 8, 25)] == Decimal("36700") and got[date(2026, 9, 3)] == Decimal("36450")


def test_null_numbers_become_none_not_zero():
    page = json.loads(text("bid-page1-20260903.json"))
    page["items"] = [{**page["items"][0], "openValue": None}]
    rows, _ = pn.normalize_code("BID", [json.dumps(page)])
    assert rows[0].open_value is None and rows[0].close_adj == Decimal("36450")


def test_summarize_counts_sessions_and_latest_without_keeping_rows():
    s = pn.summarize([text("bid-page1-20260903.json"), text("bid-page52-20260903.json")])
    assert s == pn.CodeSummary(6, date(2026, 9, 3))
    assert pn.summarize(['{"items": []}']) == pn.CodeSummary(0, None)
