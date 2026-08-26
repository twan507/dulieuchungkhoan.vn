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
    _as_etl(db)
    t = _target()
    delist, _, _ = refdata_store.plan_delist(db, t)
    refdata_store.apply(db, t, delist)
    snap1 = db.execute(sa.text(
        "SELECT ticker, exchange, security_type, status, updated_at FROM market.security ORDER BY ticker"
    )).all()
    ing1 = db.execute(sa.text(
        "SELECT source, external_code, ingested_at FROM market.security_external_id ORDER BY 1,2"
    )).all()
    stats2 = refdata_store.apply(db, t, [])
    assert db.execute(sa.text(
        "SELECT ticker, exchange, security_type, status, updated_at FROM market.security ORDER BY ticker"
    )).all() == snap1                                   # updated_at KHÔNG đổi lượt hai
    assert db.execute(sa.text(
        "SELECT source, external_code, ingested_at FROM market.security_external_id ORDER BY 1,2"
    )).all() == ing1                                    # ingested_at KHÔNG đổi
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


def test_manual_industry_assignment_survives_rerun(db):
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    iid = db.execute(sa.text(
        "SELECT i.issuer_id FROM market.issuer i JOIN market.issuer_external_id e USING (issuer_id)"
        " WHERE e.source='fiintrade' AND e.external_code='NHN'")).scalar_one()
    ind = db.execute(sa.text(
        "SELECT industry_id FROM market.industry WHERE level=2 ORDER BY industry_id LIMIT 1")).scalar_one()
    db.execute(sa.text("RESET ROLE"))                   # gán tay bằng quyền owner
    db.execute(sa.text("UPDATE market.issuer SET industry_id=:d WHERE issuer_id=:i"),
               {"d": ind, "i": iid})
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    # Đích lượt sau phải THẬT SỰ đổi một trường issuer — không thì câu UPDATE bị đuôi
    # IS DISTINCT FROM lọc, dòng SET không bao giờ chạy, và test xanh cả với mutant
    # `SET industry_id = NULL` (final review I2, kiểm bằng thí nghiệm đột biến).
    from dataclasses import replace
    t2 = type(t)(securities=t.securities,
                 issuers=[replace(x, name=x.name + " (đổi tên)") if x.organ_code == "NHN" else x
                          for x in t.issuers],
                 icb=t.icb, counters=t.counters)
    refdata_store.apply(db, t2, [])                     # job chạy lại, UPDATE thật sự nổ
    assert db.execute(sa.text("SELECT industry_id FROM market.issuer WHERE issuer_id=:i"),
                      {"i": iid}).scalar_one() == ind   # tay THẮNG máy


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
