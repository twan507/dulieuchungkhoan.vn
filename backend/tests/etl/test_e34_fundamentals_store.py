import json
import pathlib
from datetime import date, timedelta

import sqlalchemy as sa

from etl import fundamentals_normalize as fn
from etl import fundamentals_store as fs
from etl.fundamentals_fetch import Target

FIX = pathlib.Path(__file__).parent / "fixtures" / "fundamentals"


def _issuer(db, name, organ, ticker, com_type="CT", listed=True):
    iid = db.execute(sa.text("INSERT INTO market.issuer (name, com_type_code) VALUES (:n, :c) RETURNING issuer_id"),
                     {"n": name, "c": com_type}).scalar_one()
    db.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                       " VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": organ})
    db.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id, status)"
                       " VALUES (:t, 'HOSE', 'stock', :i, :s)"),
               {"t": ticker, "i": iid, "s": "listed" if listed else "delisted"})
    return iid


def _checked(db, iid, kind, days_ago, h="h0"):
    db.execute(sa.text(
        "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
        " VALUES (:i, :k, now() - make_interval(days => :d), :h, 'floor')"),
        {"i": iid, "k": kind, "d": days_ago, "h": h})


def _earning(db, iid, public_date):
    db.execute(sa.text(
        "INSERT INTO market.corporate_event (event_type, issuer_id, public_date, year_report, length_report, payload)"
        " VALUES ('Earning', :i, :p, 2026, 2, '{}'::jsonb)"), {"i": iid, "p": public_date})


def _quiet(db):
    """Dập nền CSDL dùng chung: coi mọi issuer đang có như vừa kiểm xong, và dọn corporate_event
    thật của bộ test khác (nhánh trigger và new_watermark đọc TOÀN CỤC). Rollback cuối test."""
    for kind in fs.KINDS:
        db.execute(sa.text(
            "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
            " SELECT i.issuer_id, :k, clock_timestamp(), 'nen', 'floor' FROM market.issuer i"
            " ON CONFLICT (issuer_id, kind) DO UPDATE SET checked_at = clock_timestamp()"), {"k": kind})
    db.execute(sa.text("DELETE FROM market.corporate_event"))


def _mine(due, *organs):
    return [t for t in due if t.organ_code in organs]


def _item(name):
    d = json.loads((FIX / name).read_text(encoding="utf-8"))
    return {"items": d["items"]} if name.endswith("reports.json") else d["items"][0]


def _fetched(iid, kind, name, found_by="floor", item=None):
    item = item if item is not None else _item(name)
    t = Target(kind=kind, issuer_id=iid, organ_code="ASECO32", ticker="A32", found_by=found_by)
    return fs.Fetched(target=t, text=json.dumps({"items": [item]} if kind != "reports" else item),
                      rows=fn.rows(kind, item))


# ---------- due_list ----------

def test_due_list_floor_takes_never_checked_first_then_the_oldest_within_quota(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    b = _issuer(db, "B", "ZZB", "ZZB")
    c = _issuer(db, "C", "ZZC", "ZZC")
    _checked(db, b, "bs", 100)                  # quá nhịp 90 ⇒ tới hạn
    _checked(db, c, "bs", 10)                   # còn trong nhịp ⇒ không
    due = _mine(fs.due_list(db, fs.COLD_START, kinds=["bs"], quota=2), "ZZA", "ZZB", "ZZC")
    assert [t.organ_code for t in due] == ["ZZA", "ZZB"]
    assert all(t.found_by == "floor" and t.kind == "bs" for t in due)
    assert _mine(fs.due_list(db, fs.COLD_START, kinds=["bs"], quota=1), "ZZA", "ZZB", "ZZC")[0].organ_code == "ZZA"


def test_due_list_trigger_fires_all_four_kinds_for_an_earning_after_the_watermark(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    b = _issuer(db, "B", "ZZB", "ZZB")
    for iid in (a, b):
        for k in fs.KINDS:
            _checked(db, iid, k, 30)            # quét sàn TRƯỚC ngày công bố ⇒ chỉ trigger mới đưa vào
    _earning(db, a, date(2026, 9, 3))
    _earning(db, b, date(2026, 8, 1))
    due = _mine(fs.due_list(db, date(2026, 8, 15)), "ZZA", "ZZB")
    assert {(t.organ_code, t.kind, t.found_by) for t in due} == {("ZZA", k, "event") for k in fs.KINDS}


def test_due_list_skips_the_trigger_branch_on_cold_start(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    for k in fs.KINDS:
        _checked(db, a, k, 1)
    _earning(db, a, date(2026, 9, 3))
    assert _mine(fs.due_list(db, fs.COLD_START), "ZZA") == []


def test_due_list_caps_the_trigger_branch_oldest_first(db):
    _quiet(db)
    ids = [_issuer(db, f"T{i}", f"ZZT{i}", f"ZT{i}") for i in range(3)]
    for i, iid in enumerate(ids):
        for k in fs.KINDS:
            _checked(db, iid, k, 30)            # quét sàn TRƯỚC ngày công bố ⇒ không bị loại vì đã phục vụ
        _earning(db, iid, date(2026, 9, 1 + i))
    due = _mine(fs.due_list(db, date(2026, 8, 1), kinds=["bs"], max_trigger=2), "ZZT0", "ZZT1", "ZZT2")
    assert [t.organ_code for t in due] == ["ZZT0", "ZZT1"]


def test_due_list_merges_trigger_and_floor_into_one_target_per_issuer_and_kind(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")          # chưa kiểm ⇒ floor; có Earning ⇒ trigger
    _earning(db, a, date(2026, 9, 3))
    due = _mine(fs.due_list(db, date(2026, 8, 1), kinds=["cf"]), "ZZA")
    assert len(due) == 1 and due[0].found_by == "event"


def test_due_list_backfill_ignores_the_quota_but_only_takes_never_checked(db):
    _quiet(db)
    ids = [_issuer(db, f"B{i}", f"ZZB{i}", f"ZB{i}") for i in range(5)]
    _checked(db, ids[0], "is", 200)             # quá nhịp nhưng ĐÃ từng kiểm ⇒ backfill bỏ qua
    due = _mine(fs.due_list(db, fs.COLD_START, kinds=["is"], backfill=True, quota=1),
                *[f"ZZB{i}" for i in range(5)])
    assert [t.organ_code for t in due] == ["ZZB1", "ZZB2", "ZZB3", "ZZB4"]


def test_due_list_codes_forces_every_kind_and_ignores_cadence(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    for k in fs.KINDS:
        _checked(db, a, k, 1)
    due = fs.due_list(db, fs.COLD_START, codes=["ZZA"])
    assert {t.kind for t in due} == set(fs.KINDS) and all(t.found_by == "floor" for t in due)


def test_due_list_leaves_out_an_issuer_without_a_listed_stock(db):
    _quiet(db)
    _issuer(db, "D", "ZZD", "ZZD", listed=False)
    assert _mine(fs.due_list(db, fs.COLD_START, backfill=True), "ZZD") == []


def test_new_watermark_is_the_latest_earning_public_date(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    _earning(db, a, date(2026, 9, 3))
    db.execute(sa.text("INSERT INTO market.corporate_event (event_type, issuer_id, public_date, exright_date, payload)"
                       " VALUES ('CashDividend', :i, '2026-09-04', '2026-09-30', '{}'::jsonb)"), {"i": a})
    assert fs.new_watermark(db) == date(2026, 9, 3)      # chỉ Earning, chỉ public_date


def test_trigger_skips_a_pair_already_checked_after_publication(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    _earning(db, a, date(2026, 9, 1))
    _checked(db, a, "bs", 0)                            # kiểm hôm nay — sau ngày công bố ⇒ đã phục vụ
    assert _mine(fs.due_list(db, date(2026, 8, 1), kinds=["bs"]), "ZZA") == []

    b = _issuer(db, "B", "ZZB", "ZZB")
    _earning(db, b, date(2026, 9, 1))
    _checked(db, b, "bs", 10)                           # kiểm 10 ngày trước — trước ngày công bố ⇒ còn tới hạn
    due = _mine(fs.due_list(db, date(2026, 8, 1), kinds=["bs"]), "ZZB")
    assert len(due) == 1 and due[0].found_by == "event"


def test_same_day_burst_is_served_across_runs_without_starving_anyone(db):
    _quiet(db)
    d = date(2026, 9, 3)
    ids = [_issuer(db, f"S{i}", f"ZZS{i}", f"ZS{i}") for i in range(3)]
    for iid in ids:
        _earning(db, iid, d)

    # quota=0: tắt hẳn nhánh floor để cô lập đúng nhánh trigger đang kiểm
    due1 = fs.plan_due(db, date(2026, 8, 1), kinds=["bs"], max_trigger=2, quota=0)
    served = _mine(due1.targets, "ZZS0", "ZZS1", "ZZS2")
    assert len(served) == 2 and due1.trigger_cut == d
    assert fs.new_watermark(db, d) == d - timedelta(days=1)

    for t in served:
        _checked(db, t.issuer_id, "bs", 0)              # mô phỏng đã phục vụ hai issuer đầu (hôm nay, sau ngày công bố)

    due2 = fs.plan_due(db, d - timedelta(days=1), kinds=["bs"], max_trigger=2, quota=0)
    remaining = _mine(due2.targets, "ZZS0", "ZZS1", "ZZS2")
    served_organs = {t.organ_code for t in served}
    assert {t.organ_code for t in remaining} == {"ZZS0", "ZZS1", "ZZS2"} - served_organs
    assert due2.trigger_cut is None
    assert fs.new_watermark(db, None) == d


# ---------- load_dictionary ----------

def test_load_dictionary_upserts_729_codes_with_data_units(db):
    n = fs.load_dictionary(db)
    assert n == 729 and fs.load_dictionary(db) == 729
    got = db.execute(sa.text("SELECT name_vi, unit FROM market.metric_dictionary"
                             " WHERE dictionary = 'field_dictionary' AND code = 'bsa1'")).one()
    assert got.name_vi == "TÀI SẢN NGẮN HẠN" and got.unit == "VND"
    r = db.execute(sa.text("SELECT unit, value_min, value_max FROM market.metric_dictionary"
                           " WHERE dictionary = 'field_dictionary' AND code = 'rtq29'")).one()
    assert r.unit == "ty_le_thap_phan" and float(r.value_min) == -524.47799765 and float(r.value_max) == 756.70410797
    total = db.execute(sa.text("SELECT count(*) FROM market.metric_dictionary WHERE dictionary = 'field_dictionary'")).scalar_one()
    assert total == 729


# ---------- apply ----------

def _count(db, iid, st=None):
    q = "SELECT count(*) FROM market.financial_statement WHERE issuer_id = :i" + (" AND statement_type = :s" if st else "")
    return db.execute(sa.text(q), {"i": iid, "s": st}).scalar_one()


def test_apply_first_check_writes_every_row_and_one_raw_payload(db):
    a = _issuer(db, "A", "ASECO32", "A32")
    tally, written = fs.apply(db, [_fetched(a, "bs", "A32-bs.json"), _fetched(a, "reports", "A32-reports.json")], run_id=1)
    assert tally.first == 2 and tally.checked == 2 and written == 1749 + 8
    assert _count(db, a, "BS") == 1749
    v = db.execute(sa.text("SELECT value FROM market.financial_statement WHERE issuer_id = :i AND year_report = 2025"
                           " AND length_report = 5 AND statement_type = 'BS' AND metric_code = 'bsa1'"), {"i": a}).scalar_one()
    assert float(v) == 365335639678.0
    assert db.execute(sa.text("SELECT count(*) FROM market.financial_report_file WHERE issuer_id = :i"), {"i": a}).scalar_one() == 8
    raw = db.execute(sa.text("SELECT endpoint_key, meta FROM staging.raw_payload WHERE source = 'fundamentals'"
                             " AND endpoint_key LIKE '%ASECO32' ORDER BY payload_id")).all()
    assert [r.endpoint_key for r in raw] == ["fundamentals:bs:ASECO32", "fundamentals:reports:ASECO32"]
    assert raw[0].meta["rows"] == 1749 and raw[0].meta["run_id"] == 1


def test_apply_unchanged_writes_nothing_but_advances_checked_at(db):
    a = _issuer(db, "A", "ASECO32", "A32")
    fs.apply(db, [_fetched(a, "bs", "A32-bs.json")], run_id=1)
    t0 = db.execute(sa.text("SELECT checked_at FROM ops.fundamentals_check WHERE issuer_id = :i AND kind = 'bs'"), {"i": a}).scalar_one()
    tally, written = fs.apply(db, [_fetched(a, "bs", "A32-bs.json")], run_id=2)
    t1 = db.execute(sa.text("SELECT checked_at FROM ops.fundamentals_check WHERE issuer_id = :i AND kind = 'bs'"), {"i": a}).scalar_one()
    assert tally.unchanged == 1 and tally.floor_compared == 1 and tally.changed_floor == 0 and written == 0
    assert t1 > t0 and _count(db, a, "BS") == 1749
    assert db.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source = 'fundamentals'"
                              " AND endpoint_key = 'fundamentals:bs:ASECO32'")).scalar_one() == 1


def test_apply_a_restated_value_changes_exactly_one_row_and_keeps_the_count(db):
    a = _issuer(db, "A", "ASECO32", "A32")
    fs.apply(db, [_fetched(a, "bs", "A32-bs.json")], run_id=1)
    item = _item("A32-bs.json")
    item["yearly"] = [dict(item["yearly"][0], bsa1=1.0)] + item["yearly"][1:]        # yearly[0] là 2025
    tally, written = fs.apply(db, [_fetched(a, "bs", "A32-bs.json", found_by="event", item=item)], run_id=2)
    assert tally.changed_event == 1 and written == 1749 and _count(db, a, "BS") == 1749
    v = db.execute(sa.text("SELECT value FROM market.financial_statement WHERE issuer_id = :i AND year_report = 2025"
                           " AND length_report = 5 AND statement_type = 'BS' AND metric_code = 'bsa1'"), {"i": a}).scalar_one()
    assert float(v) == 1.0
    assert db.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source = 'fundamentals'"
                              " AND endpoint_key = 'fundamentals:bs:ASECO32'")).scalar_one() == 2


def test_apply_a_vanished_cell_removes_its_row(db):
    a = _issuer(db, "A", "ASECO32", "A32")
    fs.apply(db, [_fetched(a, "bs", "A32-bs.json")], run_id=1)
    item = _item("A32-bs.json")
    item["yearly"] = [dict(item["yearly"][0], bsa23=None)] + item["yearly"][1:]
    tally, _ = fs.apply(db, [_fetched(a, "bs", "A32-bs.json", item=item)], run_id=2)
    assert tally.changed_floor == 1 and _count(db, a, "BS") == 1748


def test_apply_an_empty_payload_on_a_known_issuer_deletes_nothing_and_does_not_count_as_checked(db):
    a = _issuer(db, "A", "ASECO32", "A32")
    fs.apply(db, [_fetched(a, "is", "A32-is.json")], run_id=1)
    t0 = db.execute(sa.text("SELECT checked_at FROM ops.fundamentals_check WHERE issuer_id = :i AND kind = 'is'"), {"i": a}).scalar_one()
    tally, written = fs.apply(db, [_fetched(a, "is", "A32-is.json", item={"quarterly": [], "yearly": []})], run_id=2)
    t1 = db.execute(sa.text("SELECT checked_at FROM ops.fundamentals_check WHERE issuer_id = :i AND kind = 'is'"), {"i": a}).scalar_one()
    assert tally.empty == 1 and tally.checked == 0 and written == 0
    assert _count(db, a, "IS") == 980 and t1 == t0


def test_apply_an_empty_payload_on_a_new_issuer_is_a_normal_first_check(db):
    """Mã UPCOM chưa có báo cáo: rỗng là trạng thái thật, ghi sổ kiểm để quét sàn không gọi lại mỗi ngày."""
    a = _issuer(db, "A", "ASECO32", "A32")
    tally, _ = fs.apply(db, [_fetched(a, "cf", "A32-cf.json", item={"quarterly": [], "yearly": []})], run_id=1)
    assert tally.first == 1 and tally.empty == 0
    tally, _ = fs.apply(db, [_fetched(a, "cf", "A32-cf.json", item={"quarterly": [], "yearly": []})], run_id=2)
    assert tally.unchanged == 1 and tally.empty == 0                 # rỗng → rỗng là 'không đổi', không phải 'rỗng'


def test_apply_reports_upserts_by_source_id_and_never_deletes(db):
    a = _issuer(db, "A", "ASECO32", "A32")
    fs.apply(db, [_fetched(a, "reports", "A32-reports.json")], run_id=1)
    item = _item("A32-reports.json")
    item["items"] = [dict(item["items"][0], title="BCTC đã kiểm toán năm 2025 (bản sửa)")] + item["items"][2:]   # đổi 1, bỏ 1
    tally, _ = fs.apply(db, [_fetched(a, "reports", "A32-reports.json", item=item)], run_id=2)
    assert tally.changed_floor == 1
    rows = db.execute(sa.text("SELECT source_id, title FROM market.financial_report_file WHERE issuer_id = :i ORDER BY source_id"), {"i": a}).all()
    assert len(rows) == 8 and [r.title for r in rows if r.source_id == 9412069] == ["BCTC đã kiểm toán năm 2025 (bản sửa)"]


def test_remaining_counts_issuer_kinds_never_checked(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    b = _issuer(db, "B", "ZZB", "ZZB")
    before = fs.remaining(db)
    _checked(db, a, "bs", 0)
    assert fs.remaining(db) == before - 1
    fs.apply(db, [_fetched(b, "cf", "A32-cf.json")], run_id=1)
    assert fs.remaining(db) == before - 2
