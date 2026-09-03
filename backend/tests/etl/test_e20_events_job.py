import json
import pathlib

import sqlalchemy as sa

from etl import events_job

FIX = pathlib.Path(__file__).parent / "fixtures" / "events"
NAME = {"AGM": "agm", "CashDividend": "cashdividend", "StockDividend": "stockdividend",
        "Earning": "earning", "IPO": "ipo", "ShareIssuance": "shareissuance"}


def _pages(broken=None):
    out = {}
    for fam, stem in NAME.items():
        text = (FIX / f"{stem}-sample-20260903.json").read_text(encoding="utf-8")
        if fam == broken:                                  # bỏ 1 bản ghi ⇒ vế (i) đỏ
            d = json.loads(text)
            d["items"] = d["items"][:-1]
            text = json.dumps(d, ensure_ascii=False)
        out[fam] = [text]
    return out


def _wire(monkeypatch, engine, pages):
    monkeypatch.setenv("ETL_DATABASE_URL", str(engine.url.render_as_string(hide_password=False)))
    monkeypatch.setattr("etl.events_fetch.fetch", lambda: (pages, 0))
    monkeypatch.setattr("etl.events_job.load_dotenv", lambda *a, **k: None)
    # 🔴 Fixture CỐ Ý dày đặc ca biên: 4 trùng / 28 bản ghi = 14,3%, trong khi lượt thật là
    # 42/110.737 = 0,037%. Ngưỡng 0,5% của vế (iv) đúng cho lượt thật và SAI cho fixture —
    # không có dòng này thì job bị chính guard của nó từ chối và 3 test dưới đỏ.
    # File này kiểm ĐẤU NỐI của job; ngưỡng do test_e18 sở hữu — nới ở đây, KHÔNG nới ở đó.
    monkeypatch.setattr("etl.events_guard.DUP_RATIO", 0.5)


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM market.corporate_event"))
        c.execute(sa.text("DELETE FROM market.issuer_external_id WHERE source = 'fiintrade'"))
        c.execute(sa.text("DELETE FROM market.issuer WHERE issuer_id NOT IN"
                          " (SELECT issuer_id FROM market.security WHERE issuer_id IS NOT NULL)"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = 'market.events'"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE endpoint_key = 'events:refusal'"))


def test_missing_env_exits_two(monkeypatch):
    monkeypatch.delenv("ETL_DATABASE_URL", raising=False)
    monkeypatch.setattr("etl.events_job.load_dotenv", lambda *a, **k: None)
    assert events_job.run() == 2


def test_full_run_writes_rows_and_records_stats(migrated_engine, monkeypatch):
    _cleanup(migrated_engine)
    _wire(monkeypatch, migrated_engine, _pages())
    assert events_job.run(accept_new=True) == 0            # 17 issuer > ngưỡng 20? không, nhưng
    with migrated_engine.begin() as c:                     # cờ vẫn hợp lệ và không đổi kết quả
        n = c.execute(sa.text("SELECT count(*) FROM market.corporate_event")).scalar_one()
        stats = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = 'market.events'"
            " ORDER BY run_id DESC LIMIT 1")).scalar_one()
        wm = c.execute(sa.text(
            "SELECT watermark FROM ops.data_domain_state"
            " WHERE domain = 'market.events'")).scalar_one()
    assert n == 24
    assert stats["rows_written"] == 24 and stats["issuers_created"] == 17
    assert stats["dup_conflicts"] == 4 and len(stats["dup_keys"]) == 4
    assert wm == "2026-09-03"                              # publicDate lớn nhất trong fixture
    _cleanup(migrated_engine)


def test_second_run_is_idempotent(migrated_engine, monkeypatch):
    _cleanup(migrated_engine)
    _wire(monkeypatch, migrated_engine, _pages())
    assert events_job.run(accept_new=True) == 0
    assert events_job.run() == 0
    with migrated_engine.begin() as c:
        n = c.execute(sa.text("SELECT count(*) FROM market.corporate_event")).scalar_one()
        stats = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = 'market.events'"
            " ORDER BY run_id DESC LIMIT 1")).scalar_one()
    assert n == 24 and stats["issuers_created"] == 0
    _cleanup(migrated_engine)


def test_guard_refusal_writes_nothing_and_leaves_evidence(migrated_engine, monkeypatch):
    _cleanup(migrated_engine)
    _wire(monkeypatch, migrated_engine, _pages(broken="AGM"))
    assert events_job.run() == 1
    with migrated_engine.begin() as c:
        assert c.execute(sa.text("SELECT count(*) FROM market.corporate_event")).scalar_one() == 0
        # 🔴 issuer cũng phải bị rollback — chúng được tạo TRONG cùng giao dịch
        assert c.execute(sa.text(
            "SELECT count(*) FROM market.issuer_external_id"
            " WHERE external_code = '12681'")).scalar_one() == 0
        status, err = c.execute(sa.text(
            "SELECT status, error FROM ops.etl_run WHERE job = 'market.events'"
            " ORDER BY run_id DESC LIMIT 1")).one()
        ev = c.execute(sa.text(
            "SELECT count(*) FROM staging.raw_payload"
            " WHERE endpoint_key = 'events:refusal'")).scalar_one()
    assert status == "failed" and "thiếu trang" in err and ev == 1
    _cleanup(migrated_engine)


def test_job_runs_under_the_etl_role(migrated_engine, monkeypatch):
    """§3.5: mọi đường đọc/ghi của job phải chạy dưới đúng quyền production."""
    _cleanup(migrated_engine)
    _wire(monkeypatch, migrated_engine, _pages())
    real_create = events_job.sa.create_engine

    def create_engine_with_role(url, **kw):
        eng = real_create(url, **kw)

        @sa.event.listens_for(eng, "connect")
        def _set_role(dbapi_conn, _rec):
            cur = dbapi_conn.cursor(); cur.execute("SET ROLE dlck_etl"); cur.close()

        return eng

    monkeypatch.setattr(events_job.sa, "create_engine", create_engine_with_role)
    assert events_job.run(accept_new=True) == 0
    _cleanup(migrated_engine)
