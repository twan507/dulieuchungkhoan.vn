import pytest
import sqlalchemy as sa

from tests.conftest import expect_violation


def _issuer(db, name="Test fundamentals"):
    return db.execute(sa.text("INSERT INTO market.issuer (name) VALUES (:n) RETURNING issuer_id"),
                      {"n": name}).scalar_one()


def test_report_file_accepts_half_year_and_nine_month_but_statement_does_not(db):
    """Đo 2026-09-04: getFinancialReports phát lengthReport 6/9 (28/307 dòng); ba endpoint số liệu
    thì KHÔNG (0 dòng trên 5 mã) — nên chỉ bảng PDF và corporate_event được nới."""
    iid = _issuer(db)
    for length in (6, 9):
        db.execute(sa.text(
            "INSERT INTO market.financial_report_file (issuer_id, year_report, length_report, title, source_url, source_id)"
            " VALUES (:i, 2026, :l, 't', :u, :s)"),
            {"i": iid, "l": length, "u": f"https://x/{length}.pdf", "s": 1000 + length})
        db.execute(sa.text(
            "INSERT INTO market.corporate_event (event_type, issuer_id, public_date, year_report, length_report, payload)"
            " VALUES ('Earning', :i, '2026-08-01', 2026, :l, '{}'::jsonb)"), {"i": iid, "l": length})
    assert expect_violation(db,
        "INSERT INTO market.financial_statement (issuer_id, year_report, length_report, statement_type, metric_code, value)"
        " VALUES (:i, 2026, 6, 'BS', 'bsa1', 1)", {"i": iid})
    assert expect_violation(db,
        "INSERT INTO market.financial_report_file (issuer_id, length_report, source_url, source_id)"
        " VALUES (:i, 7, 'https://x/7.pdf', 1007)", {"i": iid})       # 7, 8 chưa ai thấy — dải liền sẽ lọt


def test_report_file_is_keyed_by_source_id_and_tolerates_a_duplicate_url(db):
    """BAB thật: id 9322194 (lengthReport 9) và 9322093 (lengthReport 3) trỏ CÙNG một PDF Q3/2024."""
    iid = _issuer(db, "BAB gia")
    url = "https://cmsv5.fiingroup.vn/medialib/FG/2024/2024-10/2024-10-30/20550225108400700_BAB_BCTC_Q3_2024_HN.pdf"
    for sid, length in ((9322194, 9), (9322093, 3)):
        db.execute(sa.text(
            "INSERT INTO market.financial_report_file (issuer_id, year_report, length_report, title, source_url, source_id)"
            " VALUES (:i, 2024, :l, 'BCTC Q3 2024', :u, :s)"), {"i": iid, "l": length, "u": url, "s": sid})
    assert expect_violation(db,
        "INSERT INTO market.financial_report_file (issuer_id, source_url, source_id)"
        " VALUES (:i, 'https://x/khac.pdf', 9322194)", {"i": iid})
    n = db.execute(sa.text("SELECT count(*) FROM market.financial_report_file WHERE issuer_id = :i"),
                   {"i": iid}).scalar_one()
    assert n == 2


def test_fundamentals_check_keeps_one_row_per_issuer_and_kind(db):
    iid = _issuer(db, "Check")
    db.execute(sa.text(
        "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
        " VALUES (:i, 'bs', now(), 'abc', 'floor')"), {"i": iid})
    assert expect_violation(db,
        "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
        " VALUES (:i, 'bs', now(), 'def', 'event')", {"i": iid})
    assert expect_violation(db,
        "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
        " VALUES (:i, 'snapshot', now(), 'abc', 'floor')", {"i": iid})


def test_fundamentals_tables_work_under_the_etl_role(db):
    """§3.5: quyền kiểm bằng đúng role production — kể cả DELETE trên financial_statement,
    đường mà lát này dùng ở mỗi lần nội dung đổi."""
    iid = _issuer(db, "Quyen dlck_etl")
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text(
        "INSERT INTO market.financial_statement (issuer_id, year_report, length_report, statement_type, metric_code, value)"
        " VALUES (:i, 2025, 5, 'BS', 'bsa1', 365335639678)"), {"i": iid})
    db.execute(sa.text("DELETE FROM market.financial_statement WHERE issuer_id = :i AND statement_type = 'BS'"), {"i": iid})
    db.execute(sa.text(
        "INSERT INTO market.financial_report_file (issuer_id, source_url, source_id) VALUES (:i, 'https://x/r.pdf', 1)"),
        {"i": iid})
    db.execute(sa.text(
        "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
        " VALUES (:i, 'reports', now(), 'h', 'floor')"), {"i": iid})
    db.execute(sa.text(
        "INSERT INTO market.metric_dictionary (dictionary, code, name_vi, unit) VALUES ('field_dictionary', 'zz_test', 'x', 'VND')"
        " ON CONFLICT (dictionary, code) DO UPDATE SET name_vi = excluded.name_vi"))
    db.execute(sa.text(
        "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
        " VALUES ('fundamentals', 'fundamentals:bs:ZZ', 'json', '{}'::jsonb, '{}'::jsonb)"))
    got = db.execute(sa.text("SELECT count(*) FROM ops.fundamentals_check WHERE issuer_id = :i"), {"i": iid}).scalar_one()
    assert got == 1
