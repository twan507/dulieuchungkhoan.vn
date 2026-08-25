import sqlalchemy as sa

from conftest import expect_violation

L1 = {"TAICHINH","BATDONGSAN","SANXUAT","XUATKHAU","TIEUDUNG","NANGLUONG"}
L2 = {"NGANHANG","CHUNGKHOAN","BAOHIEM","BDS","KCN","XAYDUNG","VLXD",
      "KIMLOAI","TAINGUYEN","HOACHAT","NHUA","THIETBI",
      "NONGNGHIEP","THUYSAN","DETMAY","CAOSU",
      "BANLE","THUCPHAM","DULICH","YTEGD",
      "DIENNUOC","DAUKHI","VANTAI","CONGNGHE"}   # literal từ industry-tree.md §2


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


def test_industry_seed_matches_tree(db):
    l1 = {r[0] for r in db.execute(sa.text("SELECT code FROM market.industry WHERE level=1"))}
    l2 = {r[0] for r in db.execute(sa.text("SELECT code FROM market.industry WHERE level=2"))}
    assert l1 == L1 and l2 == L2
    fanout = db.execute(sa.text(
        "SELECT p.code, count(*) FROM market.industry c JOIN market.industry p ON p.industry_id=c.parent_id "
        "GROUP BY p.code ORDER BY p.code")).all()
    assert dict(fanout) == {"BATDONGSAN":4,"NANGLUONG":4,"SANXUAT":5,
                            "TAICHINH":3,"TIEUDUNG":4,"XUATKHAU":4}   # phân bố 3·4·5·4·4·4
