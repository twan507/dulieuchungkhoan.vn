import sqlalchemy as sa

from conftest import expect_violation


def _mk_security(db, ticker, exchange, status="listed", stype="stock"):
    return db.execute(sa.text(
        "INSERT INTO market.security (ticker, exchange, security_type, status) "
        "VALUES (:t,:e,:st,:s) RETURNING security_id"),
        {"t": ticker, "e": exchange, "st": stype, "s": status}).scalar()


def test_partial_unique_ticker(db):                      # seam 1
    _mk_security(db, "ABC", "HOSE")
    assert expect_violation(db,
        "INSERT INTO market.security (ticker, exchange, security_type, status) "
        "VALUES ('ABC','HOSE','stock','listed')")
    _mk_security(db, "ABC", "HOSE", status="delisted")   # delisted nằm ngoài luật → hợp lệ


def test_external_id_two_subs_same_source(db):           # seam 2 + 2b (F4/I-3)
    sid = _mk_security(db, "VNINDEX", "HOSE", stype="index")
    db.execute(sa.text(
        "INSERT INTO market.security_external_id (security_id, source, external_code, external_sub) "
        "VALUES (:i,'bvsc','VNINDEX','tvc'), (:i,'bvsc','HOSE','snapshot')"), {"i": sid})
    assert expect_violation(db,
        "INSERT INTO market.security_external_id (security_id, source, external_code, external_sub) "
        f"VALUES ({sid},'bvsc','VNINDEX','tvc2')")        # trùng PK (source, external_code)=('bvsc','VNINDEX')
    n = db.execute(sa.text(
        "SELECT count(*) FROM market.security_external_id WHERE security_id=:i AND source='bvsc'"),
        {"i": sid}).scalar()
    assert n == 2


def test_industry_level_checks(db):                      # seam 3
    assert expect_violation(db,
        "INSERT INTO market.industry (code,name_vi,parent_id,level) VALUES ('X1','X',NULL,3)")
    assert expect_violation(db,
        "INSERT INTO market.industry (code,name_vi,parent_id,level) VALUES ('X2','X',NULL,2)")
    gid = db.execute(sa.text(
        "INSERT INTO market.industry (code,name_vi,parent_id,level) "
        "VALUES ('XG','Nhóm X',NULL,1) RETURNING industry_id")).scalar()
    assert expect_violation(db,
        f"INSERT INTO market.industry (code,name_vi,parent_id,level) VALUES ('XG2','X',{gid},1)")


def test_icb_map_fk(db):                                 # seam 4 (dùng seed Task 3? KHÔNG —
    assert expect_violation(db,                          #  test tự tạo ngành, độc lập thứ tự task)
        "INSERT INTO market.industry_icb_map (icb_code, industry_id) VALUES ('9999', 999999)")
