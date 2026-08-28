import pathlib
import sqlalchemy as sa
from etl.refdata_merge import merge
from etl.refdata_normalize import normalize
from etl import refdata_store

FIX = pathlib.Path(__file__).parent / "fixtures" / "refdata"


def _target():
    raw = {k: (FIX / f"{k}.json").read_text(encoding="utf-8")
           for k in ("quotes", "indexsnaps", "organization", "icb")}
    return merge(normalize(raw))


def _as_etl(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))


def test_apply_twice_is_idempotent_including_timestamps(db):
    """`now()` trong Postgres là transaction_timestamp() — fixture `db` mở MỘT
    transaction cho cả test nên updated_at không đổi trong cùng transaction dù dòng
    có bị ghi lại hay không (không bao giờ đỏ vì lý do timestamp). Chụp thêm `xmin`
    — đổi khi và chỉ khi dòng thật sự được ghi lại, độc lập với `now()` — để phép
    kiểm bắt được đúng thứ nó tuyên bố (final-fix việc 6).

    Lưới `xmin` phủ CẢ BA bảng (nợ Task 5, 2026-08-28). Trước đó chỉ `issuer` có
    `xmin`, nên hai assert `updated_at`/`ingested_at` trên `market.security` và
    `market.security_external_id` là RỖNG NGHĨA trong cùng transaction — chúng xanh
    kể cả khi `apply()` ghi lại toàn bộ hai bảng đó ở lượt hai.

    `xmin` tự nó CŨNG không phân biệt được nếu lượt hai chạy trong CÙNG transaction
    top-level với lượt một — Postgres gán lại y hệt một xmin cho mọi lần ghi trong
    cùng transaction (đã kiểm tay bằng psql: hai UPDATE liên tiếp không SAVEPOINT
    ra CÙNG một xmin). Bọc lượt hai trong SAVEPOINT (`begin_nested`, khuôn
    `expect_violation` ở conftest) để nó có subxact riêng — chỉ khi đó xmin mới đổi
    đúng lúc dòng thật sự bị ghi lại."""
    _as_etl(db)
    t = _target()
    delist, _, _ = refdata_store.plan_delist(db, t)
    refdata_store.apply(db, t, delist)
    snap1 = db.execute(sa.text(
        "SELECT ticker, exchange, security_type, status, updated_at, xmin::text "
        "FROM market.security ORDER BY ticker"
    )).all()
    ing1 = db.execute(sa.text(
        "SELECT source, external_code, ingested_at, xmin::text "
        "FROM market.security_external_id ORDER BY 1,2"
    )).all()
    snap_issuer = db.execute(sa.text(
        "SELECT issuer_id, xmin::text FROM market.issuer ORDER BY issuer_id")).all()
    nested = db.begin_nested()                          # subxact riêng cho lượt hai
    stats2 = refdata_store.apply(db, t, [])
    nested.commit()
    assert db.execute(sa.text(
        "SELECT ticker, exchange, security_type, status, updated_at, xmin::text "
        "FROM market.security ORDER BY ticker"
    )).all() == snap1                                   # updated_at KHÔNG đổi lượt hai
    assert db.execute(sa.text(
        "SELECT source, external_code, ingested_at, xmin::text "
        "FROM market.security_external_id ORDER BY 1,2"
    )).all() == ing1                                    # ingested_at KHÔNG đổi
    assert db.execute(sa.text(
        "SELECT issuer_id, xmin::text FROM market.issuer ORDER BY issuer_id")).all() == snap_issuer
    assert stats2["sec_inserted"] == 0 and stats2["sec_updated"] == 0


def test_exchange_move_keeps_security_id(db):
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    sid = db.execute(sa.text("SELECT security_id FROM market.security WHERE ticker='HTB'")).scalar_one()
    # đổi sàn: dựng target mới với HTB ở HOSE
    from dataclasses import replace
    t2 = type(t)(securities=[replace(s, exchange="HOSE") if s.ticker == "HTB" else s
                             for s in t.securities],
                 issuers=t.issuers, icb=t.icb, counters=t.counters)
    stats = refdata_store.apply(db, t2, [])
    row = db.execute(sa.text(
        "SELECT security_id, exchange FROM market.security WHERE ticker='HTB'")).one()
    assert row == (sid, "HOSE") and stats["exchange_moves"] == 1


def test_relist_keeps_security_id_and_delist_never_deletes(db):
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    sid = db.execute(sa.text("SELECT security_id FROM market.security WHERE ticker='ACV'")).scalar_one()
    n_before = db.execute(sa.text("SELECT count(*) FROM market.security")).scalar_one()
    refdata_store.apply(db, t, ["ACV"])                 # lật delisted
    assert db.execute(sa.text("SELECT status FROM market.security WHERE security_id=:i"),
                      {"i": sid}).scalar_one() == "delisted"
    refdata_store.apply(db, t, [])                      # target vẫn chứa ACV ⇒ tái niêm yết
    row = db.execute(sa.text("SELECT security_id, status FROM market.security WHERE ticker='ACV'")).one()
    assert row == (sid, "listed")                       # GIỮ NGUYÊN id
    assert db.execute(sa.text("SELECT count(*) FROM market.security")).scalar_one() == n_before


def test_seam2b_vnindex_dual_external_ids_one_security(db):
    _as_etl(db)
    refdata_store.apply(db, _target(), [])
    rows = db.execute(sa.text(
        "SELECT DISTINCT security_id FROM market.security_external_id"
        " WHERE source='bvsc' AND (external_code, external_sub) IN (('VNINDEX','tvc'), ('HOSE','snapshot'))"
    )).all()
    assert len(rows) == 1                               # cùng một security_id


def _seed_map(db, icb_code, industry_code):
    """Thêm/đổi một dòng map bằng quyền owner (bảng seed, ETL không ghi)."""
    db.execute(sa.text("RESET ROLE"))
    db.execute(sa.text(
        "INSERT INTO market.industry_icb_map (icb_code, industry_id) "
        "SELECT :c, industry_id FROM market.industry WHERE code = :i "
        "ON CONFLICT (icb_code) DO UPDATE SET industry_id = EXCLUDED.industry_id"),
        {"c": icb_code, "i": industry_code})
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))


def _synthetic(db, icb_leaf, path, com="CT"):
    """Issuer + nút ICB lá dựng riêng cho test — độc lập với nội dung seed 0013."""
    db.execute(sa.text("RESET ROLE"))
    db.execute(sa.text(
        "INSERT INTO market.icb_industry (icb_code, icb_name, parent_icb_code, icb_level, icb_code_path)"
        " VALUES (:c, 'nút thử', :p, 4, :path) ON CONFLICT (icb_code) DO UPDATE"
        " SET icb_code_path = EXCLUDED.icb_code_path"),
        {"c": icb_leaf, "p": path.split("/")[-2] if "/" in path else None, "path": path})
    iid = db.execute(sa.text(
        "INSERT INTO market.issuer (name, com_type_code, icb_code)"
        " VALUES ('DN thử', :com, :c) RETURNING issuer_id"),
        {"com": com, "c": icb_leaf}).scalar_one()
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    return iid


def _industry_code_of(db, issuer_id):
    return db.execute(sa.text(
        "SELECT i.code FROM market.issuer iss"
        " LEFT JOIN market.industry i ON i.industry_id = iss.industry_id"
        " WHERE iss.issuer_id = :i"), {"i": issuer_id}).scalar_one()


def _industry_of(db, organ_code):
    return db.execute(sa.text(
        "SELECT i.code FROM market.issuer iss "
        " JOIN market.issuer_external_id e ON e.issuer_id = iss.issuer_id"
        " LEFT JOIN market.industry i ON i.industry_id = iss.industry_id"
        " WHERE e.source='fiintrade' AND e.external_code=:o"), {"o": organ_code}).scalar_one()


def _icb_of(db, organ_code):
    return db.execute(sa.text(
        "SELECT iss.icb_code FROM market.issuer iss JOIN market.issuer_external_id e"
        " USING (issuer_id) WHERE e.source='fiintrade' AND e.external_code=:o"),
        {"o": organ_code}).scalar_one()


def test_layer1_exact_icb_match_wins_over_ancestor(db):      # seam: luật phân giải
    _as_etl(db)
    # path KHÔNG chứa chính mã lá "9991" — nếu path có chứa nó thì nhánh leo path
    # MỘT MÌNH cũng trả về "9991", nên xoá hẳn nhánh khớp-chính-xác vẫn xanh (lỗ hổng
    # đã bắt được ở final review: final-fix việc 5).
    iid = _synthetic(db, "9991", "9000/9900/9990")
    _seed_map(db, "9990", "XAYDUNG")                          # tổ tiên trực tiếp
    _seed_map(db, "9991", "DANDUNG")                          # khớp chính xác
    refdata_store.apply(db, _target(), [])
    assert _industry_code_of(db, iid) == "DANDUNG"


def test_layer1_climbs_path_to_nearest_ancestor(db):         # seam: leo path
    _as_etl(db)
    iid = _synthetic(db, "9992", "9000/9900/9990/9992")       # mã lá KHÔNG có trong map
    _seed_map(db, "9000", "XAYDUNG")                          # tổ tiên xa
    _seed_map(db, "9990", "TIENICH")                          # tổ tiên GẦN NHẤT
    refdata_store.apply(db, _target(), [])
    assert _industry_code_of(db, iid) == "TIENICH"


def test_layer1_unknown_icb_stays_null_and_counts(db):       # ca sai: không chặn job
    _as_etl(db)
    iid = _synthetic(db, "9993", "9993")                      # không tổ tiên nào trong map
    stats = refdata_store.apply(db, _target(), [])
    assert _industry_code_of(db, iid) is None
    assert stats["issuers_without_industry"] >= 1


def test_manual_override_survives_while_layer1_refreshes(db):    # spec §8.5 — tay thắng máy
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    icb = _icb_of(db, "NHN")
    iid = db.execute(sa.text(
        "SELECT issuer_id FROM market.issuer_external_id"
        " WHERE source='fiintrade' AND external_code='NHN'")).scalar_one()
    _seed_map(db, icb, "XAYDUNG")
    refdata_store.apply(db, t, [])
    assert _industry_of(db, "NHN") == "XAYDUNG"

    db.execute(sa.text("RESET ROLE"))                             # người đè tay
    db.execute(sa.text(
        "INSERT INTO market.issuer_industry_override (issuer_id, industry_id, note)"
        " SELECT :i, industry_id, 'đè tay trong test' FROM market.industry WHERE code='DANDUNG'"),
        {"i": iid})
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))

    _seed_map(db, icb, "TIENICH")                                 # sửa map ICB
    refdata_store.apply(db, t, [])
    row = db.execute(sa.text(
        "SELECT i.code, v.source FROM market.v_issuer_industry v"
        " JOIN market.industry i ON i.industry_id = v.industry_id"
        " WHERE v.issuer_id = :i"), {"i": iid}).one()
    assert row == ("DANDUNG", "manual")                           # tay THẮNG máy
    assert _industry_of(db, "NHN") == "TIENICH"                   # mà lớp 1 VẪN refresh


def test_plan_delist_counts(db):
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    from dataclasses import replace
    t_no_acv = type(t)(securities=[s for s in t.securities if s.ticker != "ACV"],
                       issuers=t.issuers, icb=t.icb, counters=t.counters)
    delist, flips, listed = refdata_store.plan_delist(db, t_no_acv)
    assert delist == ["ACV"] and flips == 1
    assert listed == len([s for s in t.securities if s.status == "listed"])


def test_planned_flips_count_the_common_delisting_path(db):
    """Final review I1: mã rời /quotes nhưng CÒN ở FiinTrade nằm trong đích với
    status='delisted' — plan_delist cũ chỉ đếm ticker VẮNG khỏi đích, nên đường huỷ
    phổ biến nhất (~78% cổ phiếu có issuer) tàng hình trước tầng 2 của chốt chặn."""
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])                       # kho: 27 listed (fixture)
    from dataclasses import replace
    # ACV "rời /quotes nhưng còn ở FiinTrade": đích vẫn chứa ACV, status delisted
    t2 = type(t)(securities=[replace(s, status="delisted") if s.ticker == "ACV" else s
                             for s in t.securities],
                 issuers=t.issuers, icb=t.icb, counters=t.counters)
    absent, planned_flips, listed_now = refdata_store.plan_delist(db, t2)
    assert absent == []                                  # ACV không vắng khỏi đích
    assert planned_flips == 1                            # nhưng PHẢI được đếm là một phép lật
    assert listed_now == len([s for s in t.securities if s.status == "listed"])
    stats = refdata_store.apply(db, t2, absent)
    assert stats["delisted"] == 1                        # và stats phải báo đúng 1, không phải 0


def test_vanished_icb_codes_kept_and_counted(db):
    """Spec §5: mã ICB biến mất khỏi nguồn → GIỮ NGUYÊN dòng, đếm + log (final review)."""
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    n_before = db.execute(sa.text("SELECT count(*) FROM market.icb_industry")).scalar_one()
    assert n_before == 176
    t2 = type(t)(securities=t.securities, issuers=t.issuers,
                 icb=[r for r in t.icb if r.icb_code != "8350"],   # Ngân hàng biến mất
                 counters=t.counters)
    stats = refdata_store.apply(db, t2, [])
    assert stats["icb_orphaned"] == 1
    assert db.execute(sa.text("SELECT count(*) FROM market.icb_industry")).scalar_one() == 176
    assert db.execute(sa.text(
        "SELECT count(*) FROM market.icb_industry WHERE icb_code='8350'")).scalar_one() == 1


BCTC_PROBE = (                                   # dò cả hai chiều, KHÔNG bỏ sót dòng NULL
    "SELECT iss.com_type_code, i.code FROM market.issuer iss"
    " LEFT JOIN market.v_issuer_industry v ON v.issuer_id = iss.issuer_id"
    " LEFT JOIN market.industry i ON i.industry_id = v.industry_id"
    " WHERE (coalesce(iss.com_type_code, '') = 'NH')"
    "        IS DISTINCT FROM (coalesce(i.code, '') = 'NGANHANG')"
    "    OR (coalesce(iss.com_type_code, '') = 'CK')"
    "        IS DISTINCT FROM (coalesce(i.code, '') = 'CHUNGKHOAN')"
    "    OR (coalesce(iss.com_type_code, '') = 'BH')"
    "        IS DISTINCT FROM (coalesce(i.code, '') = 'BAOHIEM')"
)


def test_bctc_rule_is_bidirectional_on_view(db):
    """com_type_code NH|CK|BH ⟺ ngành NGANHANG|CHUNGKHOAN|BAOHIEM, không ngoại lệ.

    Khoá luôn stats["bctc_violations"] trả về từ apply() — chốt chặn chạy lúc
    apply() dùng đúng câu BCTC_PROBE này (spec §2b), không phải chỉ có ở test.
    """
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    icb = _icb_of(db, "NHN")                      # NHN là com_type_code 'CT'
    _seed_map(db, icb, "NGANHANG")                # cố tình đẩy một DN 'CT' vào ngành ngân hàng
    stats_bad = refdata_store.apply(db, t, [])
    assert db.execute(sa.text(BCTC_PROBE)).all(), \
        "câu dò vi phạm phải BẮT được ca dựng sẵn — nếu rỗng thì chính nó hỏng"
    assert stats_bad["bctc_violations"] >= 1

    _seed_map(db, icb, "DANDUNG")                 # trả về đúng
    stats_clean = refdata_store.apply(db, t, [])
    assert db.execute(sa.text(BCTC_PROBE)).all() == []
    assert stats_clean["bctc_violations"] == 0


def test_bctc_probe_catches_bank_without_industry(db):
    """Ngân hàng không tra được ngành là vi phạm nặng nhất — INNER JOIN từng làm nó tàng hình."""
    _as_etl(db)
    _synthetic(db, "9994", "9994", com="NH")      # mã ICB không tổ tiên nào nằm trong map
    refdata_store.apply(db, _target(), [])
    bad = db.execute(sa.text(BCTC_PROBE)).all()
    assert ("NH", None) in bad
