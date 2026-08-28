import json
import pathlib

import sqlalchemy as sa

from tests.schema.conftest import expect_violation

MAP_JSON = pathlib.Path(__file__).resolve().parents[3] / "docs" / "20-design" / "industry-mapping.json"


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


def test_override_note_cannot_be_blank(db):              # seam 1b: CHECK note_not_blank
    """Chuỗi rỗng và chuỗi toàn khoảng trắng đều bị chặn — NOT NULL không bắt được ca này."""
    iid, ind = _issuer(db), _ind(db, "DANDUNG")
    for blank in ("", "   "):
        assert expect_violation(
            db,
            "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note) "
            "VALUES (:i, :d, :n)", {"i": iid, "d": ind, "n": blank}), f"note={blank!r} phải bị chặn"


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


def test_etl_role_cannot_read_override_table_but_view_still_works(db):   # seam 4d
    """Bảng nền cấm đọc; view vẫn đọc được vì chạy bằng quyền chủ view."""
    iid, ind = _issuer(db), _ind(db, "DANDUNG")
    db.execute(sa.text(
        "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note) "
        "VALUES (:i,:d,'đè tay')"), {"i": iid, "d": ind})
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    nested = db.begin_nested()
    try:
        db.execute(sa.text("SELECT count(*) FROM market.issuer_industry_override"))
        nested.commit()
        denied = False
    except sa.exc.ProgrammingError as e:
        nested.rollback()
        denied = "permission denied" in str(e).lower()
    assert denied
    assert db.execute(sa.text(
        "SELECT industry_id FROM market.v_issuer_industry WHERE issuer_id=:i"),
        {"i": iid}).scalar_one() == ind      # view vẫn trả đúng giá trị đè tay


def test_etl_role_can_read_view(db):                     # seam 4b: đường ĐỌC của production
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text("SELECT count(*) FROM market.v_issuer_industry")).scalar_one()


def test_api_role_can_read_view(db):                     # seam 4c: đường đọc của API
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    db.execute(sa.text("SELECT count(*) FROM market.v_issuer_industry")).scalar_one()


def test_icb_map_seed_matches_json(db):                  # seam 5: seed không trôi khỏi tài liệu
    doc = json.loads(MAP_JSON.read_text(encoding="utf-8"))
    want = {r["icb_code"]: r["industry_code"]
            for r in doc["layer1"] if r["industry_code"] is not None}
    got = dict(db.execute(sa.text(
        "SELECT m.icb_code, i.code FROM market.industry_icb_map m "
        "JOIN market.industry i USING (industry_id)")).all())
    assert got == want
    assert len(want) == 55                               # 56 dòng lớp 1 trừ 8980 không nạp


def test_icb_map_targets_level_2_only(db):               # seam 5, ca biên
    # Gác trước: bảng rỗng thì phép kiểm dưới cũng ra 0 và XANH VÔ ĐIỀU KIỆN — nó sẽ
    # không gác được gì cả, kể cả khi seed lớp 2 hỏng hoàn toàn.
    total = db.execute(sa.text(
        "SELECT count(*) FROM market.industry_icb_map")).scalar_one()
    assert total > 0, "industry_icb_map rỗng — phép kiểm level <> 2 sẽ xanh giả"
    assert db.execute(sa.text(
        "SELECT count(*) FROM market.industry_icb_map m JOIN market.industry i "
        "USING (industry_id) WHERE i.level <> 2")).scalar_one() == 0
