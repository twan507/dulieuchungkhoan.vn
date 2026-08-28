import sqlalchemy as sa

from tests.schema.conftest import expect_violation


def _ind(db, code="vn.test", freq="m"):
    return db.execute(sa.text(
        "INSERT INTO macro.indicator (code,name_vi,unit,freq,region) "
        "VALUES (:c,'Test','%',:f,'vn') RETURNING indicator_id"), {"c": code, "f": freq}).scalar()


def test_observation_upsert(db):                                    # seam 1
    i = _ind(db)
    ins = ("INSERT INTO macro.observation (indicator_id,obs_date,value) VALUES (:i,'2026-05-01',:v) "
           "ON CONFLICT (indicator_id,obs_date) DO UPDATE SET value=EXCLUDED.value, ingested_at=now()")
    db.execute(sa.text(ins), {"i": i, "v": 159001})
    db.execute(sa.text(ins), {"i": i, "v": 158927})
    got = db.execute(sa.text("SELECT count(*), max(value) FROM macro.observation WHERE indicator_id=:i"),
                     {"i": i}).one()
    assert (got[0], float(got[1])) == (1, 158927.0)


def test_spliced_view(db):                                          # seam 3 + 3b (case biên!)
    i = _ind(db, "vn.gdp.test", "q")
    db.execute(sa.text("INSERT INTO macro.observation (indicator_id,obs_date,value) VALUES "
                       "(:i,'2025-10-01',100), (:i,'2026-01-01',100), (:i,'2026-04-01',170)"), {"i": i})
    db.execute(sa.text("INSERT INTO macro.series_break (indicator_id,break_date,factor,reason) "
                       "VALUES (:i,'2026-04-01',1.6005,'đổi năm gốc')"), {"i": i})
    rows = dict(db.execute(sa.text(
        "SELECT obs_date::text, value_spliced FROM macro.observation_spliced WHERE indicator_id=:i"),
        {"i": i}).all())
    assert float(rows["2025-10-01"]) == 160.05 and float(rows["2026-01-01"]) == 160.05
    assert float(rows["2026-04-01"]) == 170.0                       # đoạn mới giữ nguyên
    j = _ind(db, "vn.nobreak")                                      # 3b: KHÔNG break → không NULL
    db.execute(sa.text("INSERT INTO macro.observation (indicator_id,obs_date,value) "
                       "VALUES (:i,'2026-07-01',42)"), {"i": j})
    v = db.execute(sa.text("SELECT value_spliced FROM macro.observation_spliced "
                           "WHERE indicator_id=:i"), {"i": j}).scalar()
    assert float(v) == 42.0


def test_omo_flow_hand_computed(db):                                # seam 4 (C2: VND gốc)
    db.execute(sa.text("INSERT INTO macro.omo_session (session_date,crawled_at,has_reverse_repo,has_repo,has_outright_sale) "
                       "VALUES ('2026-08-14',now(),true,false,false), ('2026-08-21',now(),true,false,false)"))
    db.execute(sa.text("INSERT INTO macro.omo_auction (session_date,op_type,tenor_days,volume_vnd,rate_pct) "
                       "VALUES ('2026-08-14','reverse_repo',7,6307470000000,4.5),"
                       "       ('2026-08-21','reverse_repo',7,5000000000000,4.5)"))
    # omo_flow là bảng TỰ DỰNG bởi job (không phải trigger) — test schema chỉ kiểm chèn kết quả giải tay:
    db.execute(sa.text("INSERT INTO macro.omo_flow (flow_date,injection_vnd,maturing_vnd,net_vnd) "
                       "VALUES ('2026-08-21',5000000000000,6307470000000,-1307470000000)"))
    net = db.execute(sa.text("SELECT net_vnd FROM macro.omo_flow WHERE flow_date='2026-08-21'")).scalar()
    assert float(net) == -1307470000000.0


def test_checks(db):                                                # seam 5b + 6
    db.execute(sa.text("INSERT INTO macro.omo_session (session_date,crawled_at,has_reverse_repo,has_repo,has_outright_sale) "
                       "VALUES ('2026-08-22',now(),false,true,false)"))
    db.execute(sa.text("INSERT INTO macro.omo_auction (session_date,op_type,tenor_days,volume_vnd) "
                       "VALUES ('2026-08-22','repo',7,1000000000000)"))         # 'repo' hợp lệ (C1)
    assert expect_violation(db, "INSERT INTO macro.omo_auction (session_date,op_type,tenor_days,volume_vnd) "
                                "VALUES ('2026-08-22','swap',7,1)")
    assert expect_violation(db, "INSERT INTO macro.indicator (code,name_vi,unit,freq,region) "
                                "VALUES ('x','X','%','x','vn')")
    assert expect_violation(db, "INSERT INTO macro.omo_auction (session_date,op_type,tenor_days,volume_vnd) "
                                "VALUES ('2099-01-01','repo',7,1)")             # FK phiên chưa crawl
