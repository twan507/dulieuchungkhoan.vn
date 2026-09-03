import json, pathlib
from datetime import date

from etl import screener_normalize as sn

FIX = pathlib.Path(__file__).parent / "fixtures" / "screener"
POST = (FIX / "page1-20260828-postclose.json").read_text(encoding="utf-8")
PRE = (FIX / "page1-20260903-preopen.json").read_text(encoding="utf-8")


def test_keep_set_loaded_from_selection_json():
    # Nguồn độc lập: đếm thẳng file JSON, không qua code normalize
    rows = json.loads((pathlib.Path(sn.SELECTION_JSON)).read_text(encoding="utf-8"))
    expected = {r["code"] for r in rows if r["source"] == "Screener" and r["keep"] is True}
    got = set().union(*sn.KEEP.values())
    assert got == expected
    assert "rtd26" in got and "closePrice" not in got and "icbRank" not in got


def test_ddb_row_values_from_real_sample():
    res = sn.normalize([POST])
    ddb = next(r for r in res.rows if r.ticker == "DDB")
    assert ddb.exchange == "UPCOM"
    assert ddb.organ_code == "0101264009"
    assert ddb.trading_date == date(2026, 8, 28)
    assert ddb.close_price == 9100.0
    assert ddb.payload["stockScreenerItem"]["rtd7"] == 12750.50715092
    assert ddb.payload["stockScreenerItem"]["rtd11"] == 107400000000.0
    assert ddb.payload["financial"]["rtd14"] == 113.41451175
    assert "closePrice" not in ddb.payload.get("priceInfo", {})      # metadata/BVSC không lưu
    assert "technical" not in ddb.payload                             # khối không còn khoá keep → bỏ khối
    assert res.total_count == 1545 and len(res.rows) == 30


def test_null_block_is_dropped_not_crashed():
    res = sn.normalize([POST])
    v68 = next(r for r in res.rows if r.ticker == "V68")
    assert "technical" not in v68.payload
    assert v68.close_price == 19500.0
    assert res.null_blocks == 1


def test_trading_date_is_cut_from_per_ticker_timestamp_1445():
    res = sn.normalize([POST])
    ccc = next(r for r in res.rows if r.ticker == "CCC")
    assert ccc.exchange == "HOSE"
    assert ccc.trading_date == date(2026, 8, 28)      # dấu 14:45, không phải 15:00


def test_unknown_com_group_is_counted_and_skipped():
    d = json.loads(POST)
    d["items"][0]["priceInfo"]["comGroupCode"] = "XYZ"
    res = sn.normalize([json.dumps(d)])
    assert res.unknown_com_group == 1 and len(res.rows) == 29


def test_preopen_sample_has_zero_priced_rows():
    res = sn.normalize([PRE])
    assert sum(1 for r in res.rows if r.close_price > 0) == 0
    assert all(r.trading_date == date(2026, 9, 3) for r in res.rows)


def test_dup_conflicts_counted_on_real_sample():
    """Mã keep nằm ở nhiều khối thì giữ cả hai bản — `dup_conflicts` đếm số cặp LỆCH.

    Kỳ vọng tính ĐỘC LẬP: đi thẳng JSON thô theo cùng luật (mã keep có mặt ở ≥2 khối,
    giá trị không bằng nhau), không gọi lại code normalize. Con số 52/90 cặp là số đo
    của review cuối 2026-09-03 trên mẫu 28/08 (`rtq12` · `rtq27` · `rtq83`).
    """
    keep = set().union(*sn.KEEP.values())
    expected = 0
    for item in json.loads(POST)["items"]:
        vals: dict[str, list] = {}
        for b in sn.BLOCKS:
            blk = item.get(b)
            if blk is None:
                continue
            for k, v in blk.items():
                if k in keep:
                    vals.setdefault(k, []).append(v)
        expected += sum(1 for vs in vals.values() if len(vs) > 1 and any(v != vs[0] for v in vs[1:]))
    assert expected == 52
    assert sn.normalize([POST]).dup_conflicts == expected
