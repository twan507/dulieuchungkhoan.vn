import json
import os
import pathlib
from datetime import date

import pytest
import sqlalchemy as sa

from etl import fundamentals_job as fj
from etl import fundamentals_store as fs

FIX = pathlib.Path(__file__).parent / "fixtures" / "fundamentals"
ORGAN, TICKER = "ZZFUND", "ZZF"
BATCH = [f"ZZFB{i:02d}" for i in range(20)]        # guard MIN_SAMPLE = 20
ALL_ORGANS = [ORGAN] + BATCH


def _payload(kind):
    return (FIX / f"A32-{kind}.json").read_text(encoding="utf-8")


def _fake_get(calls=None, fail=False):
    def get(u, timeout):
        if calls is not None:
            calls.append(u)
        if fail:
            return 503, ""
        kind = ("bs" if "GetBalanceSheet" in u else "is" if "GetIncomeStatement" in u
                else "cf" if "GetCashFlow" in u else "reports")
        return 200, _payload(kind)
    return get


def _wire(monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.fundamentals_job.load_dotenv", lambda *a, **k: None)


def _cleanup(engine):
    with engine.begin() as c:
        iids = c.execute(sa.text("SELECT issuer_id FROM market.issuer_external_id"
                                 " WHERE source = 'fiintrade' AND external_code = ANY(:o)"), {"o": ALL_ORGANS}).scalars().all()
        if iids:
            for tbl in ("market.financial_statement", "market.financial_report_file", "ops.fundamentals_check",
                        "market.corporate_event", "market.security", "market.issuer_external_id"):
                c.execute(sa.text(f"DELETE FROM {tbl} WHERE issuer_id = ANY(:i)"), {"i": iids})
            c.execute(sa.text("DELETE FROM market.issuer WHERE issuer_id = ANY(:i)"), {"i": iids})
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = :j"), {"j": fs.JOB})
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source = 'fundamentals'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE domain = :d AND source = :s"), {"d": fs.DOMAIN, "s": fs.SOURCE})
        c.execute(sa.text("DELETE FROM ops.fundamentals_check WHERE payload_hash = 'nen'"))


def _seed(engine, organ=ORGAN, ticker=TICKER):
    with engine.begin() as c:
        iid = c.execute(sa.text("INSERT INTO market.issuer (name, com_type_code) VALUES ('Job test', 'CT') RETURNING issuer_id")).scalar_one()
        c.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code) VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": organ})
        c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id) VALUES (:t, 'HOSE', 'stock', :i)"), {"t": ticker, "i": iid})
    return iid


def _last_run(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job = :j ORDER BY run_id DESC LIMIT 1"), {"j": fs.JOB}).one()


@pytest.fixture()
def clean(migrated_engine):
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def test_codes_run_writes_four_kinds_and_holds_the_watermark(clean, monkeypatch):
    _wire(monkeypatch)
    iid = _seed(clean)
    calls = []
    assert fj.run(codes=[TICKER], get=_fake_get(calls), sleep=lambda s: None) == 0
    assert len(calls) == 4
    run = _last_run(clean)
    assert run.status == "success"
    assert run.stats["rows_written"] == 1749 + 980 + 916 + 8 and run.stats["subset"] is True
    assert run.stats["dictionary_rows"] == 729 and "watermark" not in run.stats
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM market.financial_statement WHERE issuer_id = :i"), {"i": iid}).scalar_one() == 3645
        assert c.execute(sa.text("SELECT count(*) FROM ops.fundamentals_check WHERE issuer_id = :i"), {"i": iid}).scalar_one() == 4
        assert c.execute(sa.text("SELECT count(*) FROM ops.data_domain_state WHERE domain = :d"), {"d": fs.DOMAIN}).scalar_one() == 0


def test_second_codes_run_is_idempotent(clean, monkeypatch):
    _wire(monkeypatch)
    _seed(clean)
    fj.run(codes=[TICKER], get=_fake_get(), sleep=lambda s: None)
    assert fj.run(codes=[TICKER], get=_fake_get(), sleep=lambda s: None) == 0
    stats = _last_run(clean).stats
    assert stats["tally"]["unchanged"] == 4 and stats["rows_written"] == 0
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source = 'fundamentals'")).scalar_one() == 4


def test_backfill_run_covers_the_batch_and_reports_remaining(clean, monkeypatch):
    """--backfill: mọi (issuer, kind) chưa kiểm, không quota, mốc nước tiến nếu trọn."""
    _wire(monkeypatch)
    for o in BATCH:
        _seed(clean, o, o[-3:] + "X")
    with clean.begin() as c:                                         # dập nền: mã khác trong DB test coi như đã kiểm
        for k in fs.KINDS:
            c.execute(sa.text("INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
                              " SELECT issuer_id, :k, now(), 'nen', 'floor' FROM market.issuer"
                              " WHERE issuer_id NOT IN (SELECT issuer_id FROM market.issuer_external_id WHERE external_code = ANY(:o))"
                              " ON CONFLICT DO NOTHING"), {"k": k, "o": BATCH})
    calls = []
    assert fj.run(backfill=True, get=_fake_get(calls), sleep=lambda s: None) == 0
    stats = _last_run(clean).stats
    assert len(calls) == 80 and stats["backfill"] is True and stats["remaining"] == 0
    assert stats["tally"]["first"] == 80 and "watermark" in stats


def test_max_minutes_stops_after_the_current_target_and_holds_the_watermark(clean, monkeypatch):
    _wire(monkeypatch)
    for o in BATCH[:3]:
        _seed(clean, o, o[-3:] + "X")
    clock = iter([0.0, 0.0] + [10_000.0] * 100)     # lần 1: tính hạn; lần 2: kiểm trước target 1 (còn giờ); từ lần 3: hết giờ
    monkeypatch.setattr(fj, "_wall_clock", lambda: next(clock))
    calls = []
    assert fj.run(codes=[o[-3:] + "X" for o in BATCH[:3]], max_minutes=1, get=_fake_get(calls), sleep=lambda s: None) == 0
    stats = _last_run(clean).stats
    assert stats["stopped_early"] is True and 1 <= len(calls) < 12


def test_an_outage_refuses_the_run_and_writes_nothing(clean, monkeypatch):
    _wire(monkeypatch)
    for o in BATCH:
        _seed(clean, o, o[-3:] + "X")
    assert fj.run(codes=[o[-3:] + "X" for o in BATCH], kinds=["bs"], get=_fake_get(fail=True), sleep=lambda s: None) == 1
    run = _last_run(clean)
    assert run.status == "failed" and "hỏng" in run.error
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM market.financial_statement WHERE issuer_id IN"
                                 " (SELECT issuer_id FROM market.issuer_external_id WHERE external_code = ANY(:o))"), {"o": BATCH}).scalar_one() == 0
        assert c.execute(sa.text("SELECT count(*) FROM ops.fundamentals_check WHERE issuer_id IN"
                                 " (SELECT issuer_id FROM market.issuer_external_id WHERE external_code = ANY(:o))"), {"o": BATCH}).scalar_one() == 0
        # Không target nào ra được Fetched (mọi call đều lỗi) ⇒ không có gì để lưu bằng chứng —
        # giới hạn đã biết của đường bằng chứng (store_refusal_evidence chỉ ghi cái ĐÃ fetch được).
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source = 'fundamentals'")).scalar_one() == 0


def test_a_broken_dictionary_file_fails_before_any_call(clean, monkeypatch, tmp_path):
    _wire(monkeypatch)
    _seed(clean)
    bad = tmp_path / "fd.json"
    bad.write_text('{"_meta": {}}', encoding="utf-8")
    monkeypatch.setattr(fs, "DICTIONARY_JSON", bad)
    calls = []
    assert fj.run(codes=[TICKER], get=_fake_get(calls), sleep=lambda s: None) == 2
    assert calls == [] and _last_run(clean).status == "failed"


def test_main_parses_the_fundamentals_flags(monkeypatch):
    import etl.__main__ as m
    seen = {}
    monkeypatch.setattr("etl.fundamentals_job.run", lambda **kw: seen.update(kw) or 0)
    assert m.main(["fundamentals", "--codes", "a32,bab", "--kinds", "bs,cf", "--backfill",
                   "--max-minutes", "30", "--stop-before-open"]) == 0
    assert seen == {"codes": ["A32", "BAB"], "kinds": ["bs", "cf"], "backfill": True,
                    "max_minutes": 30.0, "stop_before_open": True}
