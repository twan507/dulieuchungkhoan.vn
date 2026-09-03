import json
import pathlib
from datetime import date
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import price_normalize as pn
from etl import price_store as ps

FIX = pathlib.Path(__file__).parent / "fixtures" / "price"


def _seed(db, ticker, organ, security_type="stock"):
    iid = None
    if organ:
        iid = db.execute(sa.text("INSERT INTO market.issuer (name) VALUES (:n) RETURNING issuer_id"),
                         {"n": f"Test {ticker}"}).scalar_one()
        db.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                           " VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": organ})
    return db.execute(sa.text(
        "INSERT INTO market.security (ticker, exchange, security_type, issuer_id)"
        " VALUES (:t, 'HOSE', :ty, :i) RETURNING security_id"),
        {"t": ticker, "ty": security_type, "i": iid}).scalar_one()


def _rows(name="bid-page1-20260903.json", organ="BID"):
    return pn.normalize_code(organ, [(FIX / name).read_text(encoding="utf-8")])[0]


def _row(db, sid, col, d="2026-09-03"):
    return db.execute(sa.text(f"SELECT {col} FROM market.price_daily"
                              " WHERE security_id = :s AND trading_date = :d"), {"s": sid, "d": d}).scalar_one()


def test_list_codes_joins_the_organ_code_and_names_the_ones_without(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    sid = _seed(db, "ZZA", "ZZAORG")
    _seed(db, "ZZB", None)                                   # cổ phiếu niêm yết không có issuer
    _seed(db, "ZZE", "ZZEORG", security_type="etf")
    cl = ps.list_codes(db, ["ZZA", "ZZB"])
    assert cl.codes == [ps.Code(sid, "ZZA", "ZZAORG")] and cl.no_organ_code == ["ZZB"]
    with pytest.raises(ValueError, match="ZZE"):
        ps.list_codes(db, ["ZZA", "ZZE"])                    # ETF không phải cổ phiếu niêm yết


def test_list_codes_refuses_one_organ_code_pointing_at_two_listed_stocks(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = db.execute(sa.text("INSERT INTO market.issuer (name) VALUES ('Hai mã') RETURNING issuer_id")).scalar_one()
    db.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                       " VALUES (:i, 'fiintrade', 'ZZDUP')"), {"i": iid})
    for t in ("ZZX", "ZZY"):
        db.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id)"
                           " VALUES (:t, 'HOSE', 'stock', :i)"), {"t": t, "i": iid})
    with pytest.raises(ValueError, match="ZZDUP"):
        ps.list_codes(db, ["ZZX", "ZZY"])


def test_apply_inserts_then_skips_unchanged_then_updates_changed(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    sid = _seed(db, "ZZA", "BID")
    rows = _rows()
    assert ps.apply(db, [(sid, rows)], "2026-09-04T00:00:00+00:00") == {"rows_sent": 5, "rows_changed": 5}
    assert ps.apply(db, [(sid, rows)], "2026-09-04T00:01:00+00:00")["rows_changed"] == 0   # payload y hệt ⇒ bỏ qua
    assert _row(db, sid, "raw->'fiintrade'->>'fetched_at'") == "2026-09-04T00:00:00+00:00"
    changed = [type(r)(**{**r.__dict__, "close_adj": Decimal("1"),
                          "payload": {**r.payload, "closeValue": 1.0}}) for r in rows[:1]]
    assert ps.apply(db, [(sid, changed)], "2026-09-04T00:02:00+00:00")["rows_changed"] == 1
    assert _row(db, sid, "close_adj") == Decimal("1")
    assert _row(db, sid, "raw->'fiintrade'->>'fetched_at'") == "2026-09-04T00:02:00+00:00"
    assert db.execute(sa.text("SELECT count(*) FROM market.price_daily WHERE security_id = :s"),
                      {"s": sid}).scalar_one() == 5


def test_close_raw_is_filled_once_and_a_mismatch_is_counted_and_named(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    sid = _seed(db, "ZZA", "BID")
    db.execute(sa.text("INSERT INTO market.price_daily (security_id, trading_date, close_raw)"
                       " VALUES (:s, '2026-09-03', 999)"), {"s": sid})
    ps.apply(db, [(sid, _rows())], "2026-09-04T00:00:00+00:00")
    assert _row(db, sid, "close_raw") == Decimal("999")                     # điền một lần, không đè
    assert _row(db, sid, "close_raw", "2026-08-28") == Decimal("36850")     # dòng mới thì điền
    n, sample = ps.raw_close_mismatches(db, [sid], date(2026, 8, 1))
    assert n == 1 and sample == ["ZZA 2026-09-03 close_raw=999 closePrice=36450.0"]


def test_apply_merges_its_own_adapter_key_and_keeps_the_others(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    sid = _seed(db, "ZZA", "BID")
    db.execute(sa.text("INSERT INTO market.price_daily (security_id, trading_date, raw)"
                       " VALUES (:s, '2026-09-03', cast(:r AS jsonb))"),
               {"s": sid, "r": json.dumps({"bvsc": {"payload": {"closePrice": 36450}}})})
    ps.apply(db, [(sid, _rows()[:1])], "2026-09-04T00:00:00+00:00")
    raw = _row(db, sid, "raw")
    assert raw["bvsc"] == {"payload": {"closePrice": 36450}}                # khoá của writer khác nguyên vẹn
    assert raw["fiintrade"]["fetched_at"] == "2026-09-04T00:00:00+00:00"
    assert raw["fiintrade"]["payload"]["closeValue"] == 36450.0 and len(raw["fiintrade"]["payload"]) == 99
