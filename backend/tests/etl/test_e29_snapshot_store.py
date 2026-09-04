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


def _quiet_universe(db):
    """Coi như mọi issuer đang có trong kho test vừa được kiểm xong.

    CSDL test dùng chung: các test job khác commit issuer thật và chúng nằm lại vĩnh viễn,
    nên `due_list` toàn cục sẽ trả cả mã của người khác. Dập nền trước, seed sau — issuer
    của chính test này vẫn chưa có dòng sổ kiểm nên vẫn tới hạn đúng như ý đồ test.
    Mọi thay đổi ở đây nằm trong giao dịch của fixture `db` và bị rollback khi test xong.
    """
    for kind in ss.CADENCE_DAYS:
        db.execute(sa.text(
            "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
            " SELECT i.issuer_id, :k, clock_timestamp(), 'nen', 'floor' FROM market.issuer i"
            " ON CONFLICT (issuer_id, kind) DO UPDATE SET checked_at = clock_timestamp()"),
            {"k": kind})


def _mine(due, *organ_codes):
    """Chỉ giữ target của những mã test này tự seed — xem chú thích `_quiet_universe`."""
    return [t for t in due if t.organ_code in organ_codes]


def _quiet_events(db):
    """Dọn `market.corporate_event` thật do bộ test khác để lại, trước khi seed sự kiện
    của chính test này.

    `new_watermark()` và `recrawl_codes()` quét TOÀN CỤC bảng này — không lọc theo mã như
    `due_list()` — nên `_quiet_universe` (dập `ops.snapshot_check`) không đủ, phải dọn
    thẳng bảng nguồn. Vòng sửa 1 chỉ chữa `due_list`; hai hàm này cùng bệnh nhưng lộ ra
    ở review vòng 2 vì `test_new_watermark_...` từng xanh chỉ do TRÙNG HỢP dữ liệu thật để
    lại nhỏ hơn mốc kỳ vọng — không phải bảo đảm. Nằm trong giao dịch của fixture `db`,
    rollback khi test xong — không đụng dữ liệu thật của file khác ngoài giao dịch này.
    """
    db.execute(sa.text("DELETE FROM market.corporate_event"))


def test_due_list_leaves_out_an_issuer_with_no_listed_stock(db):
    _quiet_universe(db)
    _issuer(db, "Da huy niem yet", "ZZDELIST", "ZZD", listed=False)
    due = ss.due_list(db, date(1900, 1, 1))
    assert [t.organ_code for t in due] == []


def test_due_list_takes_an_issuer_never_checked_before(db):
    _quiet_universe(db)
    _issuer(db, "Chua kiem bao gio", "ZZNEW", "ZZN")
    due = ss.due_list(db, date(1900, 1, 1))
    assert {t.kind for t in due} == set(ss.CADENCE_DAYS)
    assert all(t.found_by == "floor" and t.ticker == "ZZN" for t in due)


def test_due_list_skips_a_kind_still_inside_its_cadence(db):
    _quiet_universe(db)
    iid = _issuer(db, "Vua kiem hom qua", "ZZFRESH", "ZZF")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    assert ss.due_list(db, date(1900, 1, 1)) == []


def test_due_list_takes_back_a_kind_past_its_cadence(db):
    _quiet_universe(db)
    iid = _issuer(db, "Qua han thang", "ZZOLD", "ZZO")
    _checked(db, iid, "ownership", days_ago=31)      # nhịp tháng: quá hạn
    _checked(db, iid, "snapshot", days_ago=31)       # nhịp quý: CHƯA tới hạn
    _checked(db, iid, "valuation", days_ago=1)
    _checked(db, iid, "dividend", days_ago=1)
    assert [t.kind for t in ss.due_list(db, date(1900, 1, 1))] == ["ownership"]


def test_due_list_respects_the_daily_quota_and_takes_the_oldest_first(db):
    _quiet_universe(db)
    ids = [_issuer(db, f"Ma {i}", f"ZZQ{i}", f"ZQ{i}") for i in range(5)]
    for n, iid in enumerate(ids):
        _checked(db, iid, "ownership", days_ago=40 + n)     # ZZQ4 cũ nhất
    due = ss.due_list(db, date(1900, 1, 1), kinds=["ownership"], quota={"ownership": 2})
    assert [t.organ_code for t in due] == ["ZZQ4", "ZZQ3"]


def test_due_list_pulls_a_kind_in_early_when_an_event_fired(db):
    _quiet_universe(db)
    iid = _issuer(db, "Vua ra bao cao", "ZZEV", "ZZE")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)                  # mọi kind còn trong nhịp
    _event(db, "ZZEV", "Earning", date.today())
    due = _mine(ss.due_list(db, date.today() - timedelta(days=1)), "ZZEV")
    assert [(t.kind, t.found_by) for t in due] == [("snapshot", "event")]


def test_a_dividend_event_triggers_the_dividend_kind_not_the_snapshot_kind(db):
    _quiet_universe(db)
    iid = _issuer(db, "Chia co tuc", "ZZCD", "ZZC")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    _event(db, "ZZCD", "CashDividend", date.today() - timedelta(days=2),
           exright_date=date.today())
    due = _mine(ss.due_list(db, date.today() - timedelta(days=1)), "ZZCD")
    assert [(t.kind, t.found_by) for t in due] == [("dividend", "event")]


def test_an_event_older_than_the_watermark_does_not_fire(db):
    _quiet_universe(db)
    iid = _issuer(db, "Su kien cu", "ZZOLDEV", "ZZL")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    _event(db, "ZZOLDEV", "Earning", date.today() - timedelta(days=10))
    due = _mine(ss.due_list(db, date.today() - timedelta(days=1)), "ZZOLDEV")
    assert due == []


def test_a_target_hit_by_both_paths_appears_once_and_counts_as_event(db):
    _quiet_universe(db)
    iid = _issuer(db, "Ca hai duong", "ZZBOTH", "ZZB")
    _checked(db, iid, "snapshot", days_ago=100)              # quá hạn quý
    _event(db, "ZZBOTH", "Earning", date.today())
    due = [t for t in _mine(ss.due_list(db, date.today() - timedelta(days=1)), "ZZBOTH")
           if t.kind == "snapshot"]
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


import json
import pathlib

from etl import snapshot_normalize as sn

FIX = pathlib.Path(__file__).parent / "fixtures" / "snapshot"


def _item(name="A32-ownership.json"):
    return json.loads((FIX / name).read_text(encoding="utf-8"))["items"][0]


def _fetched(iid, kind="ownership", found_by="floor", item=None, organ="ZZAP", ticker="ZZA"):
    from etl.snapshot_fetch import Target
    obj = item if item is not None else _item()
    return ss.Fetched(target=Target(kind=kind, issuer_id=iid, organ_code=organ, ticker=ticker,
                                    com_type="CT", found_by=found_by),
                      item=obj, text=json.dumps({"items": [obj], "status": 0}))


def _rows(db, iid):
    return db.execute(sa.text("SELECT count(*) FROM market.snapshot_daily WHERE issuer_id = :i"),
                      {"i": iid}).scalar_one()


def test_apply_writes_a_row_and_a_ledger_line_on_the_first_check(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = _issuer(db, "Lan dau", "ZZAP", "ZZA")
    tally, written = ss.apply(db, [_fetched(iid)], date(2026, 9, 4))
    assert (tally.first, tally.floor_compared, written) == (1, 0, 1)
    assert _rows(db, iid) == 1
    got = db.execute(sa.text("SELECT keep_hash, found_by, changed_at IS NOT NULL AS c"
                             " FROM ops.snapshot_check WHERE issuer_id = :i"), {"i": iid}).one()
    assert got.keep_hash == sn.keep_hash("ownership", _item()) and got.found_by == "floor" and got.c


def test_apply_writes_nothing_the_second_time_but_still_moves_the_ledger(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = _issuer(db, "Khong doi", "ZZAP", "ZZA")
    ss.apply(db, [_fetched(iid)], date(2026, 9, 4))
    before = db.execute(sa.text("SELECT checked_at FROM ops.snapshot_check WHERE issuer_id = :i"),
                        {"i": iid}).scalar_one()
    tally, written = ss.apply(db, [_fetched(iid)], date(2026, 9, 5))
    after = db.execute(sa.text("SELECT checked_at, changed_at FROM ops.snapshot_check"
                               " WHERE issuer_id = :i"), {"i": iid}).one()
    assert (tally.unchanged, tally.changed_floor, written) == (1, 0, 0)
    assert _rows(db, iid) == 1                       # KHÔNG có dòng thứ hai
    assert after.checked_at > before                 # nhưng vẫn "đã nhìn"
    assert after.changed_at < after.checked_at


def test_apply_writes_a_new_row_when_the_allowlist_content_changes(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = _issuer(db, "Co doi", "ZZAP", "ZZA")
    ss.apply(db, [_fetched(iid)], date(2026, 9, 4))
    changed = _item()
    changed["majorShareHolders"] = changed["majorShareHolders"][:5]
    tally, written = ss.apply(db, [_fetched(iid, item=changed)], date(2026, 9, 5))
    assert (tally.changed_floor, tally.floor_compared, written) == (1, 1, 1)
    assert _rows(db, iid) == 2


def test_apply_ignores_a_change_that_only_touches_a_price_derived_field(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = _issuer(db, "Chi doi theo gia", "ZZAP", "ZZA", com_type="CT")
    snap = _item("A32-snapshot.json")
    ss.apply(db, [_fetched(iid, kind="snapshot", item=snap)], date(2026, 9, 4))
    moved = json.loads(json.dumps(snap))
    moved["summary"]["rtd11"] = 999_000_000_000.0
    tally, written = ss.apply(db, [_fetched(iid, kind="snapshot", item=moved)], date(2026, 9, 5))
    assert (tally.unchanged, written) == (1, 0)
    assert _rows(db, iid) == 1


def test_apply_counts_an_event_change_apart_from_a_floor_change(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = _issuer(db, "Theo su kien", "ZZAP", "ZZA")
    ss.apply(db, [_fetched(iid)], date(2026, 9, 4))
    changed = _item()
    changed["boardOfDirectors"] = []
    tally, _ = ss.apply(db, [_fetched(iid, found_by="event", item=changed)], date(2026, 9, 5))
    assert (tally.changed_event, tally.changed_floor, tally.floor_compared) == (1, 0, 0)


def test_apply_run_twice_on_the_same_day_is_idempotent(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = _issuer(db, "Cung ngay", "ZZAP", "ZZA")
    ss.apply(db, [_fetched(iid)], date(2026, 9, 4))
    ss.apply(db, [_fetched(iid)], date(2026, 9, 4))
    assert _rows(db, iid) == 1


def test_new_watermark_takes_the_latest_of_both_event_dates(db):
    _quiet_events(db)
    _issuer(db, "Moc nuoc", "ZZWM", "ZZW")
    _event(db, "ZZWM", "Earning", date(2026, 8, 1))
    _event(db, "ZZWM", "CashDividend", date(2026, 8, 20), exright_date=date(2026, 9, 10))
    assert ss.new_watermark(db) == date(2026, 9, 10)


def test_recrawl_codes_names_only_tickers_with_a_new_exright_date(db):
    _quiet_events(db)
    _issuer(db, "Co quyen", "ZZRC", "ZZQ")
    _issuer(db, "Khong quyen", "ZZNC", "ZZK")
    _event(db, "ZZRC", "CashDividend", date(2026, 9, 1), exright_date=date(2026, 9, 3))
    _event(db, "ZZNC", "Earning", date(2026, 9, 2))
    assert ss.recrawl_codes(db, date(2026, 9, 1)) == ["ZZQ"]
