import json, pathlib
from datetime import date

import sqlalchemy as sa

from etl import screener_normalize as sn
from etl import screener_store as st

FIX = pathlib.Path(__file__).parent / "fixtures" / "screener"
POST = (FIX / "page1-20260828-postclose.json").read_text(encoding="utf-8")


def _seed_securities(conn, rows):
    """Cắm 30 mã của mẫu vào market.security — bỏ qua mã đã có (test_e10 để lại CLI/UPCOM
    trong DB test ngoài rollback; unique là (ticker, exchange) WHERE status='listed')."""
    for r in rows:
        conn.execute(sa.text(
            "INSERT INTO market.security (ticker, exchange, security_type)"
            " SELECT :t, :e, :k WHERE NOT EXISTS"
            " (SELECT 1 FROM market.security WHERE ticker=:t AND exchange=:e AND status='listed')"),
            {"t": r.ticker, "e": r.exchange, "k": "etf" if r.ticker.startswith("FUE") else "stock"})


def test_merge_maps_by_ticker_and_exchange_and_counts_unmapped(db):
    rows = sn.normalize([POST]).rows
    _seed_securities(db, rows[:-1])                     # bỏ 1 mã cuối (FUEIP100) → 1 unmapped
    mapped, missing = st.merge(db, rows)
    assert len(mapped) == 29
    # nêu TÊN, không chỉ đếm — mã cuối của mẫu là FUEIP100 trên VNINDEX ⇒ HOSE
    assert missing == ["FUEIP100/HOSE"]
    sid_ddb = db.execute(sa.text("SELECT security_id FROM market.security WHERE ticker='DDB'")).scalar_one()
    assert (sid_ddb, next(r for r in rows if r.ticker == "DDB")) in mapped


def test_merge_ignores_delisted_rows(db):
    rows = sn.normalize([POST]).rows
    _seed_securities(db, rows)
    db.execute(sa.text("UPDATE market.security SET status='delisted' WHERE ticker='DDB'"))
    mapped, missing = st.merge(db, rows)
    assert missing == ["DDB/UPCOM"] and all(r.ticker != "DDB" for _, r in mapped)


def test_apply_twice_same_day_is_idempotent_and_bumps_ingested_at(db):
    rows = sn.normalize([POST]).rows
    _seed_securities(db, rows)
    mapped, _ = st.merge(db, rows)
    assert st.apply(db, mapped) == {"rows_written": 30}
    t1 = db.execute(sa.text("SELECT max(ingested_at) FROM market.screener_daily")).scalar_one()
    db.execute(sa.text("SELECT pg_sleep(0.01)"))
    assert st.apply(db, mapped) == {"rows_written": 30}
    n, t2 = db.execute(sa.text("SELECT count(*), max(ingested_at) FROM market.screener_daily")).one()
    assert n == 30 and t2 > t1
    got = db.execute(sa.text(
        "SELECT payload->'stockScreenerItem'->>'rtd7', trading_date FROM market.screener_daily sd"
        " JOIN market.security s USING (security_id) WHERE s.ticker='DDB'")).one()
    assert float(got[0]) == 12750.50715092 and got[1] == date(2026, 8, 28)


def test_baseline_reads_items_of_last_success(migrated_engine):
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job=:j"), {"j": st.JOB})
        assert st.load_baseline(migrated_engine) is None
        c.execute(sa.text("INSERT INTO ops.etl_run (job, status, finished_at, stats)"
                          " VALUES (:j,'failed',now(),cast(:s AS jsonb))"), {"j": st.JOB, "s": json.dumps({"counts": {"items": 9}})})
        c.execute(sa.text("INSERT INTO ops.etl_run (job, status, finished_at, stats)"
                          " VALUES (:j,'success',now(),cast(:s AS jsonb))"), {"j": st.JOB, "s": json.dumps({"counts": {"items": 1545}})})
    try:
        assert st.load_baseline(migrated_engine) == 1545
    finally:                                            # assert đỏ vẫn phải dọn: DB test không rollback
        with migrated_engine.begin() as c:
            c.execute(sa.text("DELETE FROM ops.etl_run WHERE job=:j"), {"j": st.JOB})


def test_refusal_evidence_and_domain_state(migrated_engine):
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='screener'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state"
                          " WHERE domain='market.scores' AND source='fiintrade'"))
    try:
        # Lý do thường: chỉ cần trang 1 làm bằng chứng (Ruling 16 — tránh ~9,6 MB jsonb mỗi ngày nghỉ)
        st.store_refusal_evidence(migrated_engine, [POST, POST], run_id=7, reasons=["x"])
        with migrated_engine.connect() as c:
            keys = c.execute(sa.text("SELECT endpoint_key, meta->>'run_id' FROM staging.raw_payload"
                                     " WHERE source='screener' ORDER BY endpoint_key")).all()
        assert [k for k, _ in keys] == ["screener:page1"] and keys[0][1] == "7"
        with migrated_engine.begin() as c:
            c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='screener'"))
        # Lý do "thiếu trang" thì mọi trang là bằng chứng — đúng cái đang bị nghi
        st.store_refusal_evidence(migrated_engine, [POST, POST], run_id=7,
                                  reasons=["gom được 1 mã, totalCount báo 2 — thiếu trang"])
        with migrated_engine.connect() as c:
            keys = c.execute(sa.text("SELECT endpoint_key FROM staging.raw_payload"
                                     " WHERE source='screener' ORDER BY endpoint_key")).all()
        assert [k for (k,) in keys] == ["screener:page1", "screener:page2"]
        st.upsert_domain_state(migrated_engine, "2026-08-28")
        st.upsert_domain_state(migrated_engine, "2026-08-29")
        with migrated_engine.connect() as c:
            w = c.execute(sa.text("SELECT watermark, status FROM ops.data_domain_state"
                                  " WHERE domain='market.scores' AND source='fiintrade'")).one()
        assert w == ("2026-08-29", "active")
    finally:                                            # assert đỏ vẫn phải dọn: DB test không rollback
        with migrated_engine.begin() as c:
            c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='screener'"))
            c.execute(sa.text("DELETE FROM ops.data_domain_state"
                              " WHERE domain='market.scores' AND source='fiintrade'"))
