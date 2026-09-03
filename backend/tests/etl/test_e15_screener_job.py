import json
import os
import pathlib

import sqlalchemy as sa

import etl.screener_job as job_mod
from etl import screener_normalize as sn
from etl import screener_store as st
from etl.__main__ import main as etl_main

FIX = pathlib.Path(__file__).parent / "fixtures" / "screener"
POST = (FIX / "page1-20260828-postclose.json").read_text(encoding="utf-8")
PRE = (FIX / "page1-20260903-preopen.json").read_text(encoding="utf-8")

# Ruling 1: mẫu chỉ có 1 trang nhưng totalCount báo 1545 (cỡ thật của bộ đầy đủ).
# Guard vế (ii) (collected != total_count ⇒ từ chối) là ĐÚNG và phải giữ nguyên —
# nên test phải mô phỏng một bộ trang ĐẦY ĐỦ bằng cách ghi đè totalCount = số item thật.
POST = json.dumps({**json.loads(POST), "totalCount": len(json.loads(POST)["items"])})
PRE = json.dumps({**json.loads(PRE), "totalCount": len(json.loads(PRE)["items"])})


def _patch(monkeypatch, pages):
    monkeypatch.setattr(job_mod.screener_fetch, "fetch", lambda: (pages, 0))
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])   # KHÔNG str(engine.url) — mật khẩu bị che
    monkeypatch.setattr(job_mod, "load_dotenv", lambda: None)


def _seed(engine):
    rows = sn.normalize([POST]).rows
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM market.screener_daily"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job=:j"), {"j": st.JOB})
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='screener'"))
        for r in rows:
            c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type)"
                              " SELECT :t, :e, :k WHERE NOT EXISTS"
                              " (SELECT 1 FROM market.security WHERE ticker=:t AND exchange=:e AND status='listed')"),
                      {"t": r.ticker, "e": r.exchange, "k": "etf" if r.ticker.startswith("FUE") else "stock"})


def test_success_writes_rows_run_and_domain_state(monkeypatch, migrated_engine):
    _seed(migrated_engine); _patch(monkeypatch, [POST])
    assert job_mod.run() == 0
    with migrated_engine.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM market.screener_daily")).scalar_one() == 30
        run = c.execute(sa.text("SELECT status, stats FROM ops.etl_run WHERE job=:j ORDER BY run_id DESC LIMIT 1"),
                        {"j": st.JOB}).one()
        assert run.status == "success"
        assert run.stats["counts"] == {"items": 30, "pages": 1, "priced": 30}
        assert run.stats["rows_written"] == 30 and run.stats["unmapped"] == 0 and run.stats["trading_date"] == "2026-08-28"
        w = c.execute(sa.text("SELECT watermark FROM ops.data_domain_state WHERE domain='market.scores' AND source='fiintrade'")).scalar_one()
        assert w == "2026-08-28"
    assert st.load_baseline(migrated_engine) == 30
    assert job_mod.run() == 0                                   # idempotent lượt hai
    with migrated_engine.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM market.screener_daily")).scalar_one() == 30


def test_preopen_sample_is_refused_nothing_written_evidence_kept(monkeypatch, migrated_engine):
    _seed(migrated_engine); _patch(monkeypatch, [PRE])
    assert job_mod.run() == 1
    with migrated_engine.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM market.screener_daily")).scalar_one() == 0
        run = c.execute(sa.text("SELECT status, error FROM ops.etl_run WHERE job=:j ORDER BY run_id DESC LIMIT 1"),
                        {"j": st.JOB}).one()
        assert run.status == "failed" and "không phải ngày giao dịch" in run.error
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source='screener'")).scalar_one() == 1


def test_job_works_under_etl_role(monkeypatch, migrated_engine):
    """§3.5: mọi đường đọc/ghi của job phải chạy dưới đúng quyền production (role dlck_etl)."""
    _seed(migrated_engine); _patch(monkeypatch, [POST])
    real_create = job_mod.sa.create_engine
    def create_engine_with_role(url, **kw):
        eng = real_create(url, **kw)
        @sa.event.listens_for(eng, "connect")
        def _set_role(dbapi_conn, _rec):
            cur = dbapi_conn.cursor(); cur.execute("SET ROLE dlck_etl"); cur.close()
        return eng
    monkeypatch.setattr(job_mod.sa, "create_engine", create_engine_with_role)
    assert job_mod.run() == 0


def test_cli_dispatch_and_help_lists_screener(monkeypatch, migrated_engine, capsys):
    _seed(migrated_engine); _patch(monkeypatch, [POST])
    assert etl_main(["screener"]) == 0
    assert etl_main(["nope"]) == 2
    assert "screener" in capsys.readouterr().err
