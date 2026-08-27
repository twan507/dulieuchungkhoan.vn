import sqlalchemy as sa

from conftest import expect_violation


def _issuer(db, name="DN thử", icb="8355", com="NH"):
    return db.execute(sa.text(
        "INSERT INTO market.issuer (name, com_type_code, icb_code) "
        "VALUES (:n,:c,:i) RETURNING issuer_id"),
        {"n": name, "c": com, "i": icb}).scalar_one()


def _ind(db, code):
    return db.execute(sa.text(
        "SELECT industry_id FROM market.industry WHERE code=:c"), {"c": code}).scalar_one()


def test_override_note_is_mandatory(db):                 # seam 1: không cho đè vô danh
    iid, ind = _issuer(db), _ind(db, "DANDUNG")
    assert expect_violation(
        db,
        "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note) "
        "VALUES (:i, :d, NULL)", {"i": iid, "d": ind})


def test_override_one_row_per_issuer(db):                # seam 2: PK issuer_id
    iid, ind = _issuer(db), _ind(db, "DANDUNG")
    db.execute(sa.text(
        "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note) "
        "VALUES (:i,:d,'lần 1')"), {"i": iid, "d": ind})
    assert expect_violation(
        db,
        "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note) "
        "VALUES (:i,:d,'lần 2')", {"i": iid, "d": ind})


def test_view_prefers_manual_over_icb(db):               # seam 3: COALESCE + cột source
    iid = _issuer(db)
    icb_ind, man_ind = _ind(db, "XAYDUNG"), _ind(db, "DANDUNG")
    db.execute(sa.text("UPDATE market.issuer SET industry_id=:d WHERE issuer_id=:i"),
               {"d": icb_ind, "i": iid})
    assert db.execute(sa.text(
        "SELECT industry_id, source FROM market.v_issuer_industry WHERE issuer_id=:i"),
        {"i": iid}).one() == (icb_ind, "icb")
    db.execute(sa.text(
        "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note) "
        "VALUES (:i,:d,'đè tay')"), {"i": iid, "d": man_ind})
    assert db.execute(sa.text(
        "SELECT industry_id, source FROM market.v_issuer_industry WHERE issuer_id=:i"),
        {"i": iid}).one() == (man_ind, "manual")


def test_view_source_is_null_when_no_industry(db):       # seam 3, ca biên
    iid = _issuer(db)
    assert db.execute(sa.text(
        "SELECT industry_id, source FROM market.v_issuer_industry WHERE issuer_id=:i"),
        {"i": iid}).one() == (None, None)


def test_etl_role_cannot_write_override(db):             # seam 4: luật một bảng một người ghi
    iid, ind = _issuer(db), _ind(db, "DANDUNG")
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    nested = db.begin_nested()
    try:
        db.execute(sa.text(
            "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note) "
            "VALUES (:i,:d,'etl không được ghi')"), {"i": iid, "d": ind})
        nested.commit()
        denied = False
    except sa.exc.ProgrammingError as e:
        nested.rollback()
        denied = "permission denied" in str(e).lower()
    assert denied


def test_etl_role_can_read_view(db):                     # seam 4b: đường ĐỌC của production
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text("SELECT count(*) FROM market.v_issuer_industry")).scalar_one()


def test_api_role_can_read_view(db):                     # seam 4c: đường đọc của API
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    db.execute(sa.text("SELECT count(*) FROM market.v_issuer_industry")).scalar_one()
