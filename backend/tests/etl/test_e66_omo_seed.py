"""Seed OMO từ CSV FiinProX (spec lát 13 §5.1): gộp dòng cùng kỳ hạn, ghi qua store_seed, idempotent, flow tính đúng."""
import os
import pathlib
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import omo_seed
from etl.omo_flow import rebuild
from etl.omo_store import store_seed

CSV = pathlib.Path(__file__).parent / "fixtures" / "omo" / "seed_sample.csv"


def test_read_csv_converts_units_and_keeps_zero_rows():
    rows = omo_seed.read_csv(CSV)
    assert len(rows) == 8
    r = rows[0]
    assert (r.session_date, r.tenor_days, r.participants, r.winners) == (date(2026, 8, 14), 7, 4, 4)
    assert r.volume_vnd == Decimal("6307470000000")
    assert r.rate_pct == Decimal("4.5")
    assert rows[-1].volume_vnd == 0 and rows[-1].rate_pct == 0


def test_to_results_merges_same_tenor_and_orders_by_date():
    results = omo_seed.to_results(omo_seed.read_csv(CSV))
    assert [x.session_date for x in results] == [date(2026, 2, 3), date(2026, 7, 17), date(2026, 8, 14)]
    feb = results[0]
    assert feb.merged == 1 and len(feb.rows) == 2
    seven = next(x for x in feb.rows if x.tenor_days == 7)
    assert seven.volume_vnd == Decimal("40731.40") * 10**9 and (seven.participants, seven.winners) == (16, 16)
    assert all(x.op_type == "reverse_repo" for r in results for x in r.rows)


def test_read_csv_rejects_unknown_columns(tmp_path):
    bad = tmp_path / "x.csv"
    bad.write_text("session_date,tenor_days,op_type,volume_bn,rate\n2026-01-05,7,repo,1,0.04\n", encoding="utf-8")
    with pytest.raises(ValueError, match="cột"):
        omo_seed.read_csv(bad)


def test_read_csv_rejects_same_tenor_different_rate(tmp_path):
    bad = tmp_path / "x.csv"
    bad.write_text("session_date,tenor_days,participants,winners,volume_bn,rate\n"
                   "2026-01-05,7,1,1,10,0.04\n2026-01-05,7,1,1,10,0.045\n", encoding="utf-8")
    with pytest.raises(ValueError, match="lãi suất"):
        omo_seed.to_results(omo_seed.read_csv(bad))


def test_store_seed_writes_session_with_note_and_is_idempotent(db):
    feb = omo_seed.to_results(omo_seed.read_csv(CSV))[0]
    st = store_seed(feb, db, crawled_at=datetime(2026, 9, 8, 3, 52, tzinfo=timezone.utc), note="seed FiinProX export 2026-09-08")
    assert st == {"sessions": 1, "auctions": 2}
    s = db.execute(sa.text("SELECT note, has_reverse_repo, has_repo, has_outright_sale, crawled_at FROM macro.omo_session WHERE session_date = '2026-02-03'")).one()
    assert s.note == "seed FiinProX export 2026-09-08 · gộp 1 dòng cùng kỳ hạn"
    assert (s.has_reverse_repo, s.has_repo, s.has_outright_sale) == (True, False, False)
    assert s.crawled_at == datetime(2026, 9, 8, 3, 52, tzinfo=timezone.utc)
    assert db.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source = 'sbv'")).scalar_one() == 0
    assert store_seed(feb, db, crawled_at=datetime(2026, 9, 8, 3, 52, tzinfo=timezone.utc), note="x") == {"skipped": True}


def test_flow_after_seed_hand_solved(db):
    for r in omo_seed.to_results(omo_seed.read_csv(CSV)):
        store_seed(r, db, crawled_at=datetime(2026, 9, 8, 3, 52, tzinfo=timezone.utc), note="seed")
    rebuild(db)
    inj = db.execute(sa.text("SELECT injection_vnd FROM macro.omo_flow WHERE flow_date = '2026-08-14'")).scalar_one()
    mat = db.execute(sa.text("SELECT maturing_vnd FROM macro.omo_flow WHERE flow_date = '2026-08-21'")).scalar_one()
    assert inj == Decimal("10894.10") * 10**9          # 6307.47 + 3466.54 + 210.17 + 909.92
    assert mat == Decimal("6307.47") * 10**9           # kỳ hạn 7 của 14/08 đáo hạn 21/08


def test_run_dry_run_reports_and_writes_nothing(migrated_engine, monkeypatch, capsys):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.omo_seed.load_dotenv", lambda *a, **k: None)
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM macro.omo_auction WHERE session_date IN ('2026-02-03','2026-07-17','2026-08-14')"))
        c.execute(sa.text("DELETE FROM macro.omo_session WHERE session_date IN ('2026-02-03','2026-07-17','2026-08-14')"))
    rc = omo_seed.run(str(CSV), dry_run=True, checks=(date(2026, 8, 14), date(2026, 8, 21)))
    out = capsys.readouterr().out
    assert rc == 0
    assert "sessions_new=3" in out and "rows_merged=1" in out
    assert "outstanding_2026-08-14=10894.10" in out
    with migrated_engine.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM macro.omo_session WHERE session_date = '2026-08-14'")).scalar_one() == 0
        assert c.execute(sa.text("SELECT count(*) FROM ops.etl_run WHERE job = 'macro.omo_seed'")).scalar_one() == 0


def test_run_real_writes_and_second_run_skips(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.omo_seed.load_dotenv", lambda *a, **k: None)
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM macro.omo_auction WHERE session_date IN ('2026-02-03','2026-07-17','2026-08-14')"))
        c.execute(sa.text("DELETE FROM macro.omo_session WHERE session_date IN ('2026-02-03','2026-07-17','2026-08-14')"))
    try:
        assert omo_seed.run(str(CSV), checks=(date(2026, 8, 14),)) == 0
        with migrated_engine.connect() as c:
            row = c.execute(sa.text("SELECT status, stats FROM ops.etl_run WHERE job = 'macro.omo_seed' ORDER BY run_id DESC LIMIT 1")).one()
            assert row.status == "success" and row.stats["sessions_new"] == 3 and row.stats["rows_merged"] == 1
            assert row.stats["min_session_date"] == "2026-02-03" and row.stats["max_session_date"] == "2026-08-14"
        assert omo_seed.run(str(CSV), checks=(date(2026, 8, 14),)) == 0
        with migrated_engine.connect() as c:
            row = c.execute(sa.text("SELECT stats FROM ops.etl_run WHERE job = 'macro.omo_seed' ORDER BY run_id DESC LIMIT 1")).one()
            assert row.stats["sessions_new"] == 0 and row.stats["sessions_skipped"] == 3
    finally:
        with migrated_engine.begin() as c:
            c.execute(sa.text("DELETE FROM macro.omo_auction WHERE session_date IN ('2026-02-03','2026-07-17','2026-08-14')"))
            c.execute(sa.text("DELETE FROM macro.omo_session WHERE session_date IN ('2026-02-03','2026-07-17','2026-08-14')"))
            c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = 'macro.omo_seed'"))
