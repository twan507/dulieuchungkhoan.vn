import json, os, pathlib
import sqlalchemy as sa
import etl.refdata_job as job_mod
from etl import refdata_store

FIX = pathlib.Path(__file__).parent / "fixtures" / "refdata"


def _raw():
    return {k: (FIX / f"{k}.json").read_text(encoding="utf-8")
            for k in ("quotes", "indexsnaps", "organization", "icb")}


def _patch(monkeypatch, migrated_engine, raw):
    monkeypatch.setattr(job_mod.refdata_fetch, "fetch", lambda: raw)
    # KHÔNG dùng str(engine.url) — SQLAlchemy che mật khẩu thành '***' trong repr
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr(job_mod, "load_dotenv", lambda: None)   # .env thật không được đè env test


def test_job_end_to_end_success_and_baseline(monkeypatch, migrated_engine):
    _patch(monkeypatch, migrated_engine, _raw())
    assert job_mod.run() == 0
    with migrated_engine.connect() as c:
        n_sec = c.execute(sa.text("SELECT count(*) FROM market.security")).scalar_one()
        assert n_sec == 9 + 18 + 2          # 6 CP + 3 ETF + 18 chỉ số + 2 fiin-only (fixture README)
        assert c.execute(sa.text("SELECT count(*) FROM market.icb_industry")).scalar_one() == 176
        run_row = c.execute(sa.text(
            "SELECT status, stats FROM ops.etl_run WHERE job='market.refdata'"
            " ORDER BY run_id DESC LIMIT 1")).one()
        assert run_row.status == "success"
        assert run_row.stats["counts"] == {"quotes": 9, "organization": 8, "icb": 176}
        assert c.execute(sa.text(
            "SELECT count(*) FROM ops.data_domain_state WHERE domain='market.reference'"
        )).scalar_one() == 2
    assert refdata_store.load_baseline(migrated_engine) == {"quotes": 9, "organization": 8, "icb": 176}
    assert job_mod.run() == 0               # idempotent lượt hai


def test_guard_refusal_rolls_back_keeps_baseline_writes_evidence(monkeypatch, migrated_engine):
    _patch(monkeypatch, migrated_engine, _raw())
    assert job_mod.run() == 0               # dựng mốc 9/8/176
    cut = _raw()
    d = json.loads(cut["quotes"])
    d["d"] = [r for r in d["d"] if r["symbol"] not in ("ACV", "VHM", "SHB")]   # cụt 3/9 > 2%
    cut["quotes"] = json.dumps(d)
    _patch(monkeypatch, migrated_engine, cut)
    assert job_mod.run() == 1
    with migrated_engine.connect() as c:
        assert c.execute(sa.text(                                   # dữ liệu KHÔNG đổi
            "SELECT status FROM market.security WHERE ticker='ACV'")).scalar_one() == "listed"
        last = c.execute(sa.text(
            "SELECT run_id, status FROM ops.etl_run WHERE job='market.refdata'"
            " ORDER BY run_id DESC LIMIT 1")).one()
        assert last.status == "failed"
        ev = c.execute(sa.text(
            "SELECT count(*) FROM staging.raw_payload WHERE source='refdata'"
            " AND (meta->>'run_id')::bigint = :r"), {"r": last.run_id}).scalar_one()
        assert ev == 4                                              # đủ 4 payload bằng chứng
    assert refdata_store.load_baseline(migrated_engine) == {"quotes": 9, "organization": 8, "icb": 176}


def test_accept_drop_lets_refused_run_commit(monkeypatch, migrated_engine):
    cut = _raw()
    d = json.loads(cut["quotes"])
    d["d"] = [r for r in d["d"] if r["symbol"] not in ("ACV", "VHM", "SHB")]
    cut["quotes"] = json.dumps(d)
    _patch(monkeypatch, migrated_engine, cut)
    assert job_mod.run(accept_drop=True) == 0
    with migrated_engine.connect() as c:
        assert c.execute(sa.text(
            "SELECT status FROM market.security WHERE ticker='ACV'")).scalar_one() == "delisted"
        assert c.execute(sa.text(
            "SELECT stats->'accept_drop' FROM ops.etl_run WHERE job='market.refdata'"
            " ORDER BY run_id DESC LIMIT 1")).scalar_one() is True
