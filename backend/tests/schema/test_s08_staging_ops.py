import sqlalchemy as sa

from tests.conftest import expect_violation


def test_raw_payload_content_type_check(db):                        # seam 1 (M5 siết)
    db.execute(sa.text("INSERT INTO staging.raw_payload (source,endpoint_key,content_type,body) "
                       "VALUES ('sbv','omo','html','<html>KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ (14.08.26)</html>')"))
    back = db.execute(sa.text("SELECT body FROM staging.raw_payload WHERE source='sbv'")).scalar()
    assert "KẾT QUẢ ĐẤU THẦU" in back                               # đọc lại nguyên văn
    assert expect_violation(db, "INSERT INTO staging.raw_payload (source,endpoint_key,content_type,body) "
                                "VALUES ('x','k','json','not-json-slot')")
    assert expect_violation(db, "INSERT INTO staging.raw_payload (source,endpoint_key,content_type) "
                                "VALUES ('x','k','html')")

def test_domain_state(db):                                          # seam 2 (M-8)
    ins = ("INSERT INTO ops.data_domain_state (domain,source,status) VALUES ('macro.omo','sbv',:s) "
           "ON CONFLICT (domain,source) DO UPDATE SET status=EXCLUDED.status")
    db.execute(sa.text(ins), {"s": "active"})
    db.execute(sa.text(ins), {"s": "frozen"})
    got = db.execute(sa.text("SELECT count(*), max(status) FROM ops.data_domain_state "
                             "WHERE domain='macro.omo'")).one()
    assert (got[0], got[1]) == (1, "frozen")
    assert expect_violation(db, "INSERT INTO ops.data_domain_state (domain,source,status) "
                                "VALUES ('market.unknown','x','active')")
    assert expect_violation(db, "INSERT INTO ops.data_domain_state (domain,source,status) "
                                "VALUES ('macro.omo','y','paused')")

def test_etl_run_lifecycle(db):                                     # seam 3
    rid = db.execute(sa.text("INSERT INTO ops.etl_run (job) VALUES ('macro.omo_crawl') RETURNING run_id")).scalar()
    db.execute(sa.text("UPDATE ops.etl_run SET status='success', finished_at=now() WHERE run_id=:r"), {"r": rid})
    last = db.execute(sa.text("SELECT status FROM ops.etl_run WHERE job='macro.omo_crawl' "
                              "ORDER BY started_at DESC LIMIT 1")).scalar()
    assert last == "success"

def test_snapshots_append(db):                                      # seam 4 + source_build/series_health
    db.execute(sa.text("INSERT INTO ops.contract_snapshot (endpoint,checked_at) "
                       "VALUES ('getAllQuotes','2026-08-25 08:00+07'), ('getAllQuotes','2026-08-25 09:00+07')"))
    n = db.execute(sa.text("SELECT count(*) FROM ops.contract_snapshot WHERE endpoint='getAllQuotes'")).scalar()
    assert n == 2
    db.execute(sa.text("INSERT INTO ops.source_build (source,bundle_hash) VALUES ('bvsc','3241ea7a')"))
    db.execute(sa.text("INSERT INTO ops.series_health (source,external_key,external_sub,days_since_change,"
                       "source_last_updated) VALUES ('wichart','xang_dau','0',76,NULL)"))
