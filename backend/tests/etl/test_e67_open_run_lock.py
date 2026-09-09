"""Advisory lock Postgres ở open_run — lớp trong của chặn chạy chồng (spec lát 13 §5.9)."""
import pytest
import sqlalchemy as sa

from etl import omo_store

JOB = "zz.lock.test"


def _hold(engine):
    conn = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    assert conn.execute(sa.text("SELECT pg_try_advisory_lock(hashtext(:j))"), {"j": JOB}).scalar_one() is True
    return conn


def _release(conn):
    conn.execute(sa.text("SELECT pg_advisory_unlock(hashtext(:j))"), {"j": JOB})
    conn.close()


def _rows(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT run_id, status, error, stats FROM ops.etl_run WHERE job = :j ORDER BY run_id"), {"j": JOB}).all()


@pytest.fixture()
def clean(migrated_engine):
    yield migrated_engine
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = :j"), {"j": JOB})


def test_busy_lock_writes_a_refused_row_and_exits_1(clean):
    holder = _hold(clean)
    try:
        with pytest.raises(SystemExit) as e:
            omo_store.open_run(clean, JOB)
        assert e.value.code == 1
        rows = _rows(clean)
        assert len(rows) == 1 and rows[0].status == "failed"
        assert rows[0].error == "lock busy: lượt khác đang chạy"
        assert rows[0].stats == {"lock_busy": True, "guard_refused": True}
    finally:
        _release(holder)


def test_open_run_holds_the_lock_until_close_run(clean):
    rid = omo_store.open_run(clean, JOB)
    probe = clean.connect().execution_options(isolation_level="AUTOCOMMIT")
    try:
        assert probe.execute(sa.text("SELECT pg_try_advisory_lock(hashtext(:j))"), {"j": JOB}).scalar_one() is False
        omo_store.close_run(clean, rid, "success", {"x": 1})
        assert probe.execute(sa.text("SELECT pg_try_advisory_lock(hashtext(:j))"), {"j": JOB}).scalar_one() is True
        probe.execute(sa.text("SELECT pg_advisory_unlock(hashtext(:j))"), {"j": JOB})
    finally:
        probe.close()
    rows = _rows(clean)
    assert [r.status for r in rows] == ["success"] and rows[0].stats == {"x": 1}


def test_close_run_refused_flags_stats(clean):
    rid = omo_store.open_run(clean, JOB)
    omo_store.close_run_refused(clean, rid, "guard refused: thử", {"calls": 3})
    rows = _rows(clean)
    assert rows[0].status == "failed" and rows[0].error == "guard refused: thử"
    assert rows[0].stats == {"calls": 3, "guard_refused": True}
    rid2 = omo_store.open_run(clean, JOB)               # khoá đã nhả
    omo_store.close_run_refused(clean, rid2, "model down")
    assert _rows(clean)[1].stats == {"guard_refused": True}
