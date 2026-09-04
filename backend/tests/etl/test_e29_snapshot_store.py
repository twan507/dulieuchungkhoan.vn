from datetime import date, timedelta

import sqlalchemy as sa

from etl import snapshot_store as ss


def _issuer(db, name, organ, ticker, com_type="CT", listed=True):
    iid = db.execute(sa.text("INSERT INTO market.issuer (name, com_type_code)"
                             " VALUES (:n, :c) RETURNING issuer_id"),
                     {"n": name, "c": com_type}).scalar_one()
    db.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                       " VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": organ})
    db.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id, status)"
                       " VALUES (:t, 'HOSE', 'stock', :i, :s)"),
               {"t": ticker, "i": iid, "s": "listed" if listed else "delisted"})
    return iid


def _checked(db, iid, kind, days_ago, keep_hash="h0"):
    db.execute(sa.text(
        "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
        " VALUES (:i, :k, now() - make_interval(days => :d), :h, 'floor')"),
        {"i": iid, "k": kind, "d": days_ago, "h": keep_hash})


def _event(db, organ, event_type, public_date, exright_date=None):
    # market.corporate_event khoá theo issuer_id, không có cột organ_code (migration 0004,
    # đối chiếu information_schema thật 2026-09-04) — tra issuer_id qua issuer_external_id
    # giống cách _issuer() vừa ghi.
    iid = db.execute(sa.text(
        "SELECT issuer_id FROM market.issuer_external_id"
        " WHERE source = 'fiintrade' AND external_code = :o"), {"o": organ}).scalar_one()
    db.execute(sa.text(
        "INSERT INTO market.corporate_event (event_type, issuer_id, public_date, exright_date, payload)"
        " VALUES (:t, :i, :p, :e, '{}'::jsonb)"),
        {"t": event_type, "i": iid, "p": public_date, "e": exright_date})


def test_due_list_leaves_out_an_issuer_with_no_listed_stock(db):
    _issuer(db, "Da huy niem yet", "ZZDELIST", "ZZD", listed=False)
    due = ss.due_list(db, date(1900, 1, 1))
    assert [t.organ_code for t in due] == []


def test_due_list_takes_an_issuer_never_checked_before(db):
    _issuer(db, "Chua kiem bao gio", "ZZNEW", "ZZN")
    due = ss.due_list(db, date(1900, 1, 1))
    assert {t.kind for t in due} == set(ss.CADENCE_DAYS)
    assert all(t.found_by == "floor" and t.ticker == "ZZN" for t in due)


def test_due_list_skips_a_kind_still_inside_its_cadence(db):
    iid = _issuer(db, "Vua kiem hom qua", "ZZFRESH", "ZZF")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    assert ss.due_list(db, date(1900, 1, 1)) == []


def test_due_list_takes_back_a_kind_past_its_cadence(db):
    iid = _issuer(db, "Qua han thang", "ZZOLD", "ZZO")
    _checked(db, iid, "ownership", days_ago=31)      # nhịp tháng: quá hạn
    _checked(db, iid, "snapshot", days_ago=31)       # nhịp quý: CHƯA tới hạn
    _checked(db, iid, "valuation", days_ago=1)
    _checked(db, iid, "dividend", days_ago=1)
    assert [t.kind for t in ss.due_list(db, date(1900, 1, 1))] == ["ownership"]


def test_due_list_respects_the_daily_quota_and_takes_the_oldest_first(db):
    ids = [_issuer(db, f"Ma {i}", f"ZZQ{i}", f"ZQ{i}") for i in range(5)]
    for n, iid in enumerate(ids):
        _checked(db, iid, "ownership", days_ago=40 + n)     # ZZQ4 cũ nhất
    due = ss.due_list(db, date(1900, 1, 1), kinds=["ownership"], quota={"ownership": 2})
    assert [t.organ_code for t in due] == ["ZZQ4", "ZZQ3"]


def test_due_list_pulls_a_kind_in_early_when_an_event_fired(db):
    iid = _issuer(db, "Vua ra bao cao", "ZZEV", "ZZE")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)                  # mọi kind còn trong nhịp
    _event(db, "ZZEV", "Earning", date.today())
    due = ss.due_list(db, date.today() - timedelta(days=1))
    assert [(t.kind, t.found_by) for t in due] == [("snapshot", "event")]


def test_a_dividend_event_triggers_the_dividend_kind_not_the_snapshot_kind(db):
    iid = _issuer(db, "Chia co tuc", "ZZCD", "ZZC")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    _event(db, "ZZCD", "CashDividend", date.today() - timedelta(days=2),
           exright_date=date.today())
    due = ss.due_list(db, date.today() - timedelta(days=1))
    assert [(t.kind, t.found_by) for t in due] == [("dividend", "event")]


def test_an_event_older_than_the_watermark_does_not_fire(db):
    iid = _issuer(db, "Su kien cu", "ZZOLDEV", "ZZL")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    _event(db, "ZZOLDEV", "Earning", date.today() - timedelta(days=10))
    assert ss.due_list(db, date.today() - timedelta(days=1)) == []


def test_a_target_hit_by_both_paths_appears_once_and_counts_as_event(db):
    iid = _issuer(db, "Ca hai duong", "ZZBOTH", "ZZB")
    _checked(db, iid, "snapshot", days_ago=100)              # quá hạn quý
    _event(db, "ZZBOTH", "Earning", date.today())
    due = [t for t in ss.due_list(db, date.today() - timedelta(days=1)) if t.kind == "snapshot"]
    assert len(due) == 1 and due[0].found_by == "event"


def test_codes_forces_every_kind_and_ignores_cadence(db):
    iid = _issuer(db, "Ep bang codes", "ZZFORCE", "ZZR")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    due = ss.due_list(db, date.today(), codes=["ZZR"])
    assert sorted(t.kind for t in due) == sorted(ss.CADENCE_DAYS)


def test_load_watermark_falls_back_to_1900_when_the_row_is_missing(db):
    assert ss.load_watermark(db) == date(1900, 1, 1)


def test_load_watermark_reads_the_row_it_wrote(db):
    db.execute(sa.text("INSERT INTO ops.data_domain_state (domain, source, status, watermark)"
                       " VALUES ('market.snapshot', 'fiintrade', 'active', '2026-09-01')"))
    assert ss.load_watermark(db) == date(2026, 9, 1)
