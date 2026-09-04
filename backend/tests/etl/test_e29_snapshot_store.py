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
    _quiet_events(db)     # dập corporate_event thật của bộ test khác — nhánh trigger đọc TOÀN
                           # CỤC, không lọc theo mã như floor (review, phát hiện #5)
    _issuer(db, "Da huy niem yet", "ZZDELIST", "ZZD", listed=False)
    due = ss.due_list(db, date(1900, 1, 1))
    assert [t.organ_code for t in due] == []


def test_due_list_takes_an_issuer_never_checked_before(db):
    _quiet_universe(db)
    _quiet_events(db)
    _issuer(db, "Chua kiem bao gio", "ZZNEW", "ZZN")
    due = ss.due_list(db, date(1900, 1, 1))
    assert {t.kind for t in due} == set(ss.CADENCE_DAYS)
    assert all(t.found_by == "floor" and t.ticker == "ZZN" for t in due)


def test_due_list_skips_a_kind_still_inside_its_cadence(db):
    _quiet_universe(db)
    _quiet_events(db)
    iid = _issuer(db, "Vua kiem hom qua", "ZZFRESH", "ZZF")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    assert ss.due_list(db, date(1900, 1, 1)) == []


def test_due_list_takes_back_a_kind_past_its_cadence(db):
    _quiet_universe(db)
    _quiet_events(db)
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
    _event(db, "ZZCD", "CashDividend", date.today())          # trigger đọc public_date, không
    due = _mine(ss.due_list(db, date.today() - timedelta(days=1)), "ZZCD")  # còn đọc exright_date
    assert [(t.kind, t.found_by) for t in due] == [("dividend", "event")]


def test_an_event_older_than_the_watermark_does_not_fire(db):
    _quiet_universe(db)
    iid = _issuer(db, "Su kien cu", "ZZOLDEV", "ZZL")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    _event(db, "ZZOLDEV", "Earning", date.today() - timedelta(days=10))
    due = _mine(ss.due_list(db, date.today() - timedelta(days=1)), "ZZOLDEV")
    assert due == []


def test_due_list_fires_on_publish_even_when_the_ex_right_date_is_far_in_the_future(db):
    """Chiều ngược của bug đo 2026-09-22: trigger đọc `public_date`, không đọc
    `exright_date` — một sự kiện vừa công bố phải bắn ngay dù ngày không hưởng quyền của
    nó còn rất xa, đừng để lần sửa `new_watermark`/`due_list` làm hỏng chiều này."""
    _quiet_universe(db)
    iid = _issuer(db, "Cong bo som, ex xa", "ZZPUB", "ZZP")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    _event(db, "ZZPUB", "CashDividend", date.today(), exright_date=date(2030, 6, 30))
    due = _mine(ss.due_list(db, date.today() - timedelta(days=1)), "ZZPUB")
    assert [(t.kind, t.found_by) for t in due] == [("dividend", "event")]


def test_a_target_hit_by_both_paths_appears_once_and_counts_as_event(db):
    _quiet_universe(db)
    iid = _issuer(db, "Ca hai duong", "ZZBOTH", "ZZB")
    _checked(db, iid, "snapshot", days_ago=100)              # quá hạn quý
    _event(db, "ZZBOTH", "Earning", date.today())
    due = [t for t in _mine(ss.due_list(db, date.today() - timedelta(days=1)), "ZZBOTH")
           if t.kind == "snapshot"]
    assert len(due) == 1 and due[0].found_by == "event"


def test_due_list_skips_the_trigger_branch_on_a_cold_start_watermark(db):
    """CRITICAL #2: mốc `1900-01-01` nghĩa là CHƯA từng ghi mốc nước — nếu không chặn, nhánh
    trigger sẽ đọc TOÀN BỘ `corporate_event` lịch sử (gần trọn vũ trụ × nhiều kind, hàng nghìn
    lời gọi). Quét sàn đã có quota chặn cold start; nhánh trigger thì chưa, đây là chỗ vá."""
    _quiet_universe(db)
    _quiet_events(db)
    _issuer(db, "Cold start co su kien", "ZZCOLD", "ZZK")
    _event(db, "ZZCOLD", "Earning", date.today() - timedelta(days=500))
    due = ss.due_list(db, date(1900, 1, 1), kinds=["snapshot"])
    assert all(t.found_by != "event" for t in due)


def test_due_list_caps_the_trigger_branch_and_takes_the_oldest_public_date_first(db):
    """CRITICAL #2: một mã hỏng dai dẳng giữ mốc đứng yên ⇒ danh sách trigger phình mỗi ngày,
    không có đường tự thoát nếu không có trần. `max_trigger` cho phép test không cần chèn
    hàng trăm dòng thật để chạm `MAX_TRIGGER` mặc định."""
    _quiet_universe(db)
    _quiet_events(db)
    for i in range(8):
        iid = _issuer(db, f"Trigger {i}", f"ZZT{i}", f"ZT{i}")
        _checked(db, iid, "snapshot", days_ago=1)          # trong nhịp — chỉ trigger mới bắn
        _event(db, f"ZZT{i}", "Earning", date.today() - timedelta(days=8 - i))  # i=0 cũ nhất
    due = ss.due_list(db, date.today() - timedelta(days=9), kinds=["snapshot"], max_trigger=3)
    assert [t.ticker for t in due] == ["ZT0", "ZT1", "ZT2"]


def test_due_list_floor_returns_exactly_quota_when_cold_start_has_more_issuers_than_quota(db):
    """IMPORTANT #6: spec §6 chốt seam 'bảng rỗng đi theo NULLS FIRST' — cơ chế DUY NHẤT giữ
    quét sàn khỏi nổ 6.092 lời gọi ở lượt đầu — nhưng chưa test bao giờ ở tổ hợp thật: N issuer
    chưa kiểm bao giờ, N > quota. Test cũ chỉ phủ 1 issuer NULL hoặc 5 issuer đều có checked_at."""
    _quiet_universe(db)
    tickers = [f"ZC{i}" for i in range(5)]
    for i, t in enumerate(tickers):
        _issuer(db, f"Cold start floor {i}", f"ZZCS{i}", t)
    due = ss.due_list(db, date(1900, 1, 1), kinds=["ownership"], quota={"ownership": 3})
    assert [t.ticker for t in due] == tickers[:3]


def test_a_share_issuance_event_triggers_both_snapshot_and_valuation(db):
    """IMPORTANT #7: `valuation` không có loại sự kiện nào trong spec gốc ⇒ chỉ đi đường quét
    sàn — nhưng tập trắng của nó có `outstandingShare`, đúng đại lượng mà `ShareIssuance` làm
    đổi, và `snapshot` cũng track `outstandingShare`. Một `ShareIssuance` mới phải bắn CẢ HAI
    kind, không chỉ `snapshot`, để `valuation` khỏi ôm dữ liệu cũ tới 30 ngày."""
    _quiet_universe(db)
    iid = _issuer(db, "Phat hanh them", "ZZSI", "ZZI")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    _event(db, "ZZSI", "ShareIssuance", date.today())
    due = _mine(ss.due_list(db, date.today() - timedelta(days=1)), "ZZSI")
    assert sorted((t.kind, t.found_by) for t in due) == [("snapshot", "event"), ("valuation", "event")]


def test_a_stock_dividend_event_triggers_snapshot_valuation_and_dividend(db):
    """Vá lượt trước ghi đè `("snapshot", "valuation")` lên chỗ của `("dividend",)` cũ thay vì
    cộng thêm — StockDividend vừa đổi số cổ phiếu lưu hành (chạm `snapshot`/`valuation`, giống
    ShareIssuance) VỪA là một sự kiện cổ tức (chạm `dividend`) — cả ba đều đúng, thiếu vế nào
    cũng sai."""
    _quiet_universe(db)
    iid = _issuer(db, "Chia co phieu", "ZZSD2", "ZZ2")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    _event(db, "ZZSD2", "StockDividend", date.today())
    due = _mine(ss.due_list(db, date.today() - timedelta(days=1)), "ZZSD2")
    assert sorted((t.kind, t.found_by) for t in due) == [
        ("dividend", "event"), ("snapshot", "event"), ("valuation", "event")]


def test_codes_forces_every_kind_and_ignores_cadence(db):
    iid = _issuer(db, "Ep bang codes", "ZZFORCE", "ZZR")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    due = ss.due_list(db, date.today(), codes=["ZZR"])
    assert sorted(t.kind for t in due) == sorted(ss.CADENCE_DAYS)


def test_load_watermark_falls_back_to_1900_when_the_row_is_missing(db):
    # Dập dòng THẬT (nếu có) mà lượt job chạy thật khác để lại trong DB test dùng chung — nằm
    # trong giao dịch của fixture `db`, rollback khi test xong, không đụng dữ liệu thật ngoài
    # giao dịch này (review, phát hiện #5 — trước đây test này xanh chỉ nhờ dọn dẹp của file
    # khác chạy trước, không phải bảo đảm; đo thật: seed một dòng qua `migrated_engine` rồi
    # chạy lại test KHÔNG có DELETE này ⇒ đỏ, `datetime.date(2026, 5, 1) != date(1900, 1, 1)`).
    db.execute(sa.text("DELETE FROM ops.data_domain_state WHERE domain = :d AND source = :s"),
              {"d": ss.DOMAIN, "s": ss.SOURCE})
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


def test_new_watermark_tracks_the_announcement_date_not_the_ex_right_date(db):
    """Bug thật đo 2026-09-22: `--codes A32,BAB,BVB` để lại watermark `2026-09-22` — nhảy
    vào tương lai — vì bản cũ lấy `max(greatest(public_date, exright_date))` và một
    `exright_date` xa kéo mốc vượt luôn hôm nay, làm trigger chết ba tuần (không sự kiện
    công bố nào có `public_date` lớn hơn nổi cái mốc giả đó). `new_watermark()` giờ chỉ đo
    'sự kiện MỚI CÔNG BỐ' — cột `public_date` — bỏ hẳn `exright_date` khỏi phép tính."""
    _quiet_events(db)
    _issuer(db, "Ngay ex xa", "ZZFAR", "ZZX")
    _event(db, "ZZFAR", "CashDividend", date(2030, 1, 5), exright_date=date(2030, 6, 30))
    assert ss.new_watermark(db) == date(2030, 1, 5)


def test_recrawl_codes_picks_only_a_ticker_whose_ex_right_date_just_passed(db):
    """Không còn watermark: cửa sổ ngày (mặc định 3) quanh HÔM NAY. Ba mã, ba đáp số khác
    nhau — hôm nay lấy, tương lai bỏ, quá cũ (ngoài cửa sổ) cũng bỏ."""
    _quiet_events(db)
    _issuer(db, "Ex hom nay", "ZZTODAY", "ZZT")
    _issuer(db, "Ex tuong lai", "ZZFUTURE", "ZZU")
    _issuer(db, "Ex qua cu", "ZZSTALE", "ZZS")
    _event(db, "ZZTODAY", "CashDividend", date.today() - timedelta(days=5), exright_date=date.today())
    _event(db, "ZZFUTURE", "CashDividend", date.today(), exright_date=date.today() + timedelta(days=1))
    _event(db, "ZZSTALE", "CashDividend", date.today() - timedelta(days=10),
           exright_date=date.today() - timedelta(days=10))
    assert ss.recrawl_codes(db) == ["ZZT"]


def test_recrawl_codes_ignores_agm_but_keeps_a_price_moving_event_type(db):
    """Spec §5.6 bản gốc bị đánh rơi ở vòng sửa 3: re-crawl chỉ dành cho ba loại sự kiện
    ĐỔI HỆ SỐ ĐIỀU CHỈNH GIÁ — CashDividend/StockDividend/ShareIssuance. Số đo thật (kho
    production, 2026-09-04): bản không lọc loại trả 8 mã (DCF·KSV·PVO·RYG·SAS·SMT·TCH·VXT)
    mà 6/10 sự kiện của chúng là AGM (ngày chốt quyền dự đại hội — không cổ tức, không phát
    hành, hệ số điều chỉnh KHÔNG đổi); chỉ RYG (StockDividend+ShareIssuance) và TCH
    (ShareIssuance) thật sự cần kéo lại — còn lại 2/8. Ở đây: AGM và StockDividend có cùng
    `exright_date` hôm nay, chỉ mã StockDividend được chọn."""
    _quiet_events(db)
    _issuer(db, "Chi hop dai hoi", "ZZAGM", "ZZG")
    _issuer(db, "Chia co phieu", "ZZSD", "ZZV")
    _event(db, "ZZAGM", "AGM", date.today() - timedelta(days=5), exright_date=date.today())
    _event(db, "ZZSD", "StockDividend", date.today() - timedelta(days=5), exright_date=date.today())
    assert ss.recrawl_codes(db) == ["ZZV"]
