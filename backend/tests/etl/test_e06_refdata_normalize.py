import json, pathlib, pytest
from etl.refdata_normalize import RefdataError, normalize

FIX = pathlib.Path(__file__).parent / "fixtures" / "refdata"

def _raw():
    return {k: (FIX / f"{k}.json").read_text(encoding="utf-8")
            for k in ("quotes", "indexsnaps", "organization", "icb")}

def test_normalize_fixture_literals():
    n = normalize(_raw())
    assert sum(1 for q in n.quotes if q.security_type == "stock") == 6
    assert sum(1 for q in n.quotes if q.security_type == "etf") == 3
    assert n.counters["skipped_cw"] == 2 and n.counters["skipped_bond"] == 2
    assert n.counters["junk_stocktype2"] == 1          # L40_WFT_01
    assert not any(q.symbol == "L40_WFT_01" for q in n.quotes)
    assert len(n.index_codes) == 18 and n.counters["index_junk"] == 2
    assert len(n.orgs) == 8
    assert len(n.icb) == 176                            # icb.json nguyên văn
    by_level = {}
    for r in n.icb: by_level[r.icb_level] = by_level.get(r.icb_level, 0) + 1
    assert by_level == {1: 11, 2: 19, 3: 40, 4: 106}   # đo 2026-08-26

def test_collision_between_index_codes_and_symbols_raises():
    raw = _raw()
    d = json.loads(raw["quotes"]); d["d"].append(
        {"symbol": "ALL", "FullName": "x", "exchange": "HOSE", "StockType": "2", "tradelot": 100})
    raw["quotes"] = json.dumps(d)
    with pytest.raises(RefdataError):
        normalize(raw)

def test_org_rec_carries_identity_fields():
    n = normalize(_raw())
    vhm = next(o for o in n.orgs if o.ticker == "VHM")
    assert vhm.organ_code == "NHN"                     # bẫy organCode ≠ ticker
    assert vhm.com_group_code == "VNINDEX"
