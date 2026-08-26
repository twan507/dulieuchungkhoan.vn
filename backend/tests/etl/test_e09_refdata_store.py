import pathlib
import sqlalchemy as sa
from etl.refdata_merge import merge
from etl.refdata_normalize import normalize
from etl import refdata_store

FIX = pathlib.Path(__file__).parent / "fixtures" / "refdata"


def _target():
    raw = {k: (FIX / f"{k}.json").read_text(encoding="utf-8")
           for k in ("quotes", "indexsnaps", "organization", "icb")}
    return merge(normalize(raw))


def _as_etl(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))


def test_apply_twice_is_idempotent_including_timestamps(db):
    _as_etl(db)
    t = _target()
    delist, _ = refdata_store.plan_delist(db, {s.ticker for s in t.securities})
    refdata_store.apply(db, t, delist)
    snap1 = db.execute(sa.text(
        "SELECT ticker, exchange, security_type, status, updated_at FROM market.security ORDER BY ticker"
    )).all()
    ing1 = db.execute(sa.text(
        "SELECT source, external_code, ingested_at FROM market.security_external_id ORDER BY 1,2"
    )).all()
    stats2 = refdata_store.apply(db, t, [])
    assert db.execute(sa.text(
        "SELECT ticker, exchange, security_type, status, updated_at FROM market.security ORDER BY ticker"
    )).all() == snap1                                   # updated_at KHÔNG đổi lượt hai
    assert db.execute(sa.text(
        "SELECT source, external_code, ingested_at FROM market.security_external_id ORDER BY 1,2"
    )).all() == ing1                                    # ingested_at KHÔNG đổi
    assert stats2["sec_inserted"] == 0 and stats2["sec_updated"] == 0


def test_exchange_move_keeps_security_id(db):
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    sid = db.execute(sa.text("SELECT security_id FROM market.security WHERE ticker='HTB'")).scalar_one()
    # đổi sàn: dựng target mới với HTB ở HOSE
    from dataclasses import replace
    t2 = type(t)(securities=[replace(s, exchange="HOSE") if s.ticker == "HTB" else s
                             for s in t.securities],
                 issuers=t.issuers, icb=t.icb, counters=t.counters)
    stats = refdata_store.apply(db, t2, [])
    row = db.execute(sa.text(
        "SELECT security_id, exchange FROM market.security WHERE ticker='HTB'")).one()
    assert row == (sid, "HOSE") and stats["exchange_moves"] == 1


def test_relist_keeps_security_id_and_delist_never_deletes(db):
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    sid = db.execute(sa.text("SELECT security_id FROM market.security WHERE ticker='ACV'")).scalar_one()
    n_before = db.execute(sa.text("SELECT count(*) FROM market.security")).scalar_one()
    refdata_store.apply(db, t, ["ACV"])                 # lật delisted
    assert db.execute(sa.text("SELECT status FROM market.security WHERE security_id=:i"),
                      {"i": sid}).scalar_one() == "delisted"
    refdata_store.apply(db, t, [])                      # target vẫn chứa ACV ⇒ tái niêm yết
    row = db.execute(sa.text("SELECT security_id, status FROM market.security WHERE ticker='ACV'")).one()
    assert row == (sid, "listed")                       # GIỮ NGUYÊN id
    assert db.execute(sa.text("SELECT count(*) FROM market.security")).scalar_one() == n_before


def test_seam2b_vnindex_dual_external_ids_one_security(db):
    _as_etl(db)
    refdata_store.apply(db, _target(), [])
    rows = db.execute(sa.text(
        "SELECT DISTINCT security_id FROM market.security_external_id"
        " WHERE source='bvsc' AND (external_code, external_sub) IN (('VNINDEX','tvc'), ('HOSE','snapshot'))"
    )).all()
    assert len(rows) == 1                               # cùng một security_id


def test_manual_industry_assignment_survives_rerun(db):
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    iid = db.execute(sa.text(
        "SELECT i.issuer_id FROM market.issuer i JOIN market.issuer_external_id e USING (issuer_id)"
        " WHERE e.source='fiintrade' AND e.external_code='NHN'")).scalar_one()
    ind = db.execute(sa.text(
        "SELECT industry_id FROM market.industry WHERE level=2 ORDER BY industry_id LIMIT 1")).scalar_one()
    db.execute(sa.text("RESET ROLE"))                   # gán tay bằng quyền owner
    db.execute(sa.text("UPDATE market.issuer SET industry_id=:d WHERE issuer_id=:i"),
               {"d": ind, "i": iid})
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    refdata_store.apply(db, t, [])                      # job chạy lại
    assert db.execute(sa.text("SELECT industry_id FROM market.issuer WHERE issuer_id=:i"),
                      {"i": iid}).scalar_one() == ind   # tay THẮNG máy


def test_plan_delist_counts(db):
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    tickers = {s.ticker for s in t.securities}
    delist, listed = refdata_store.plan_delist(db, tickers - {"ACV"})
    assert delist == ["ACV"] and listed == len([s for s in t.securities if s.status == "listed"])
