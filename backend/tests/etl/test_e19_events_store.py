import json
import pathlib

import sqlalchemy as sa

from etl import events_normalize as en
from etl import events_store as es

FIX = pathlib.Path(__file__).parent / "fixtures" / "events"
NAME = {"AGM": "agm", "CashDividend": "cashdividend", "StockDividend": "stockdividend",
        "Earning": "earning", "IPO": "ipo", "ShareIssuance": "shareissuance"}


def pages(*families):
    return {f: [(FIX / f"{NAME[f]}-sample-20260903.json").read_text(encoding="utf-8")]
            for f in families}


ALL = ("AGM", "CashDividend", "StockDividend", "Earning", "IPO", "ShareIssuance")


def test_ensure_issuers_mints_one_per_organ_code_and_is_idempotent(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    rows = en.normalize(pages(*ALL)).rows
    codes = {r.organ_code for r in rows}
    by_organ, created = es.ensure_issuers(db, rows)
    # `by_organ` là BẢNG TRA TOÀN CỤC (apply() cần tra issuer_id cho mọi dòng), không phải
    # của riêng lô này ⇒ CẤM assert len(by_organ): test khác commit issuer thật và không dọn
    # (test_e10 để lại 8 dòng `fiintrade` sống qua cả phiên pytest) sẽ làm số đó đổi.
    # Tiêu chí phải bất biến, không phải số thời điểm — CLAUDE.md §4.4.4.
    assert created == 17 and codes <= set(by_organ)
    again_by_organ, again_created = es.ensure_issuers(db, rows)
    assert again_created == 0 and again_by_organ == by_organ


def test_minimal_issuer_name_prefers_a_real_name_and_falls_back_to_the_code(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    rows = en.normalize(pages(*ALL)).rows
    by_organ, _ = es.ensure_issuers(db, rows)
    got = dict(db.execute(sa.text(
        "SELECT external_code, i.name FROM market.issuer i"
        " JOIN market.issuer_external_id x USING (issuer_id)"
        " WHERE x.external_code IN ('QNC','12681','0304941312')")).all())
    assert got == {"QNC": "Xi măng Quảng Ninh",       # organShortName
                   "0304941312": "Xây dựng Công trình Tân Cảng",   # organName
                   "12681": "RYG"}                    # không trường tên nào ⇒ lùi về ticker


def test_ensure_issuers_never_updates_an_existing_issuer(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = db.execute(sa.text(
        "INSERT INTO market.issuer (name) VALUES ('TÊN CŨ CỦA REFDATA') RETURNING issuer_id")).scalar_one()
    db.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                       " VALUES (:i, 'fiintrade', 'QNC')"), {"i": iid})
    es.ensure_issuers(db, en.normalize(pages("AGM")).rows)
    assert db.execute(sa.text("SELECT name FROM market.issuer WHERE issuer_id = :i"),
                      {"i": iid}).scalar_one() == "TÊN CŨ CỦA REFDATA"


def test_apply_writes_every_row_then_upserts_in_place(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    n = en.normalize(pages(*ALL))
    by_organ, _ = es.ensure_issuers(db, n.rows)
    assert es.apply(db, n.rows, by_organ) == {"rows_written": 24}
    assert db.execute(sa.text("SELECT count(*) FROM market.corporate_event")).scalar_one() == 24
    ids = set(db.execute(sa.text("SELECT event_id FROM market.corporate_event")).scalars())
    es.apply(db, n.rows, by_organ)                       # chạy lại: đè, không thêm
    assert db.execute(sa.text("SELECT count(*) FROM market.corporate_event")).scalar_one() == 24
    assert set(db.execute(sa.text("SELECT event_id FROM market.corporate_event")).scalars()) == ids


def test_apply_replaces_the_payload_not_just_the_timestamp(db):
    """Seam 9 đúng nghĩa: ghi lại cùng khoá với payload KHÁC phải thay được nội dung.
    Bản cũ ghi lại đúng cùng payload nên không chứng minh được `DO UPDATE SET payload`."""
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    n = en.normalize(pages("IPO"))
    by_organ, _ = es.ensure_issuers(db, n.rows)
    es.apply(db, n.rows, by_organ)
    doi = [type(r)(**{**r.__dict__, "payload": {**r.payload, "prices": 99999.0}}) for r in n.rows]
    es.apply(db, doi, by_organ)
    got = db.execute(sa.text(
        "SELECT count(*), count(*) FILTER (WHERE payload->>'prices' = '99999.0')"
        " FROM market.corporate_event WHERE event_type = 'IPO'")).one()
    assert got == (2, 2)                      # vẫn 2 dòng, và nội dung đã bị thay


def test_minimal_issuer_falls_back_to_the_organ_code_when_no_name_at_all(db):
    """Seam 10 nhánh cuối: fixture nào cũng có `ticker` nên nhánh `names[code] or code`
    chưa từng chạy — trong khi kho thật có 177 issuer rơi đúng ca này."""
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    rows = en.normalize(pages("CashDividend")).rows
    khong_ten = [type(r)(**{**r.__dict__, "organ_code": "ZZKHONGTEN", "name_hint": None})
                 for r in rows[:1]]
    by_organ, created = es.ensure_issuers(db, khong_ten)
    assert created == 1
    assert db.execute(sa.text("SELECT name FROM market.issuer WHERE issuer_id = :i"),
                      {"i": by_organ["ZZKHONGTEN"]}).scalar_one() == "ZZKHONGTEN"


def test_baseline_is_none_when_no_successful_run_exists(migrated_engine):
    """Lượt đầu tiên chưa có mốc — guard vế (ii) phải bỏ qua thay vì nổ."""
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = :j"), {"j": es.JOB})
    assert es.load_baseline(migrated_engine) is None


def test_apply_keeps_two_rows_for_two_dividend_years_on_the_same_day(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    n = en.normalize(pages("CashDividend"))
    by_organ, _ = es.ensure_issuers(db, n.rows)
    es.apply(db, n.rows, by_organ)
    got = db.execute(sa.text(
        "SELECT stage_key FROM market.corporate_event ce"
        " JOIN market.issuer_external_id x USING (issuer_id)"
        " WHERE x.external_code = 'SD9' ORDER BY stage_key")).scalars().all()
    assert got == ["2019|Cả năm", "2021|Cả năm"]


def test_apply_stores_source_url_for_agm_and_null_elsewhere(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    n = en.normalize(pages("AGM", "CashDividend"))
    by_organ, _ = es.ensure_issuers(db, n.rows)
    es.apply(db, n.rows, by_organ)
    with_url, without = db.execute(sa.text(
        "SELECT count(*) FILTER (WHERE source_url IS NOT NULL),"
        "       count(*) FILTER (WHERE source_url IS NULL) FROM market.corporate_event")).one()
    assert (with_url, without) == (5, 6)


def test_refusal_evidence_stores_only_the_implicated_family(db, migrated_engine):
    from etl import events_guard as eg
    verdict = eg.GuardVerdict(ok=False, reasons=("AGM: thiếu trang",), families=("AGM",))
    es.store_refusal_evidence(migrated_engine, pages("AGM", "Earning"), 99, verdict,
                              {"AGM": 6, "Earning": 3}, {"AGM": 5, "Earning": 3})
    with migrated_engine.begin() as c:
        payload, meta = c.execute(sa.text(
            "SELECT payload, meta FROM staging.raw_payload"
            " WHERE endpoint_key = 'events:refusal' ORDER BY payload_id DESC LIMIT 1")).one()
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE endpoint_key = 'events:refusal'"))
    assert list(payload["sample"]) == ["AGM"] and len(payload["sample"]["AGM"]) == 6
    assert meta["run_id"] == 99 and meta["reasons"] == ["AGM: thiếu trang"]


def test_domain_state_and_baseline_round_trip(migrated_engine):
    es.upsert_domain_state(migrated_engine, "2026-09-03")
    with migrated_engine.begin() as c:
        got = c.execute(sa.text(
            "SELECT status, watermark FROM ops.data_domain_state"
            " WHERE domain = 'market.events' AND source = 'fiintrade'")).one()
        assert got == ("active", "2026-09-03")
        rid = c.execute(sa.text(
            "INSERT INTO ops.etl_run (job, finished_at, status, stats) VALUES"
            " (:j, now(), 'success', cast(:s AS jsonb)) RETURNING run_id"),
            {"j": es.JOB, "s": json.dumps({"counts": {"AGM": 23467}})}).scalar_one()
    assert es.load_baseline(migrated_engine) == {"AGM": 23467}
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE run_id = :r"), {"r": rid})
