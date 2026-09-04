import pytest
import sqlalchemy as sa


def _issuer(db, name="Test snapshot_check"):
    return db.execute(sa.text("INSERT INTO market.issuer (name) VALUES (:n) RETURNING issuer_id"),
                      {"n": name}).scalar_one()


def test_snapshot_check_keeps_one_row_per_issuer_and_kind(db):
    iid = _issuer(db)
    db.execute(sa.text(
        "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
        " VALUES (:i, 'snapshot', now(), 'abc', 'floor')"), {"i": iid})
    with pytest.raises(sa.exc.IntegrityError):
        db.execute(sa.text(
            "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
            " VALUES (:i, 'snapshot', now(), 'def', 'event')"), {"i": iid})


def test_snapshot_check_refuses_a_kind_outside_the_four(db):
    iid = _issuer(db, "Kind la")
    with pytest.raises(sa.exc.IntegrityError):
        db.execute(sa.text(
            "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
            " VALUES (:i, 'company_score', now(), 'abc', 'floor')"), {"i": iid})


def test_snapshot_check_refuses_a_found_by_outside_the_two(db):
    iid = _issuer(db, "found_by la")
    with pytest.raises(sa.exc.IntegrityError):
        db.execute(sa.text(
            "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
            " VALUES (:i, 'snapshot', now(), 'abc', 'guess')"), {"i": iid})


def test_data_domain_state_accepts_the_new_market_snapshot_domain(db):
    db.execute(sa.text(
        "INSERT INTO ops.data_domain_state (domain, source, status, watermark)"
        " VALUES ('market.snapshot', 'fiintrade', 'active', '2026-09-04')"))
    got = db.execute(sa.text("SELECT watermark FROM ops.data_domain_state"
                             " WHERE domain = 'market.snapshot'")).scalar_one()
    assert got == "2026-09-04"


def test_snapshot_check_works_under_the_etl_role(db):
    """§3.5 ca thứ ba: quyền phải kiểm bằng chính role production, không suy từ migration."""
    iid = _issuer(db, "Quyen dlck_etl")
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text(
        "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
        " VALUES (:i, 'ownership', now(), 'h1', 'floor')"), {"i": iid})
    db.execute(sa.text(
        "UPDATE ops.snapshot_check SET keep_hash = 'h2', changed_at = now()"
        " WHERE issuer_id = :i AND kind = 'ownership'"), {"i": iid})
    assert db.execute(sa.text("SELECT keep_hash FROM ops.snapshot_check"
                              " WHERE issuer_id = :i"), {"i": iid}).scalar_one() == "h2"
