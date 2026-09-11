"""Migration 0018: bài ↔ ngành hai đường (via trong PK), sổ lời gọi model; quyền kiểm dưới ĐÚNG role production (CLAUDE.md §3.5)."""
import sqlalchemy as sa
from tests.conftest import expect_violation


def _article(db, url="https://zz.test/s15-1"):
    return db.execute(sa.text("INSERT INTO news.article (canonical_url, primary_source, fetched_at) VALUES (:u, 'cafef', now()) RETURNING article_id"),
                      {"u": url}).scalar_one()


def _industry(db, code="KIMLOAI"):
    return db.execute(sa.text("SELECT industry_id FROM market.industry WHERE code = :c"), {"c": code}).scalar_one()


def test_article_industry_pk_has_via_and_checks(db):
    a, i = _article(db), _industry(db)
    db.execute(sa.text("INSERT INTO news.article_industry (article_id, industry_id, via, confidence) VALUES (:a, :i, 'ai', 0.8)"), {"a": a, "i": i})
    db.execute(sa.text("INSERT INTO news.article_industry (article_id, industry_id, via) VALUES (:a, :i, 'ticker')"), {"a": a, "i": i})
    assert db.execute(sa.text("SELECT count(*) FROM news.article_industry WHERE article_id = :a"), {"a": a}).scalar_one() == 2
    assert expect_violation(db, f"INSERT INTO news.article_industry (article_id, industry_id, via) VALUES ({a}, {i}, 'ai')")        # PK trùng
    assert expect_violation(db, f"INSERT INTO news.article_industry (article_id, industry_id, via) VALUES ({a}, {i}, 'guess')")     # via lạ
    assert expect_violation(db, f"INSERT INTO news.article_industry (article_id, industry_id, via, confidence) VALUES ({a}, {i}, 'ai', 1.5)")
    assert expect_violation(db, f"INSERT INTO news.article_industry (article_id, industry_id, via) VALUES ({a}, 999999999, 'ai')")  # FK ngành


def test_llm_call_status_check_and_defaults(db):
    a = _article(db, "https://zz.test/s15-2")
    cid = db.execute(sa.text(
        "INSERT INTO ops.llm_call (purpose, model, thinking, article_id, status, input_tokens, cache_read_tokens, output_tokens, thinking_tokens, latency_ms)"
        " VALUES ('news.classify', 'MiniMax-M3', 'adaptive', :a, 'ok', 214, 2816, 250, 120, 5500) RETURNING call_id"), {"a": a}).scalar_one()
    row = db.execute(sa.text("SELECT http_calls, called_at IS NOT NULL, run_id FROM ops.llm_call WHERE call_id = :c"), {"c": cid}).one()
    assert tuple(row) == (1, True, None)
    assert expect_violation(db, "INSERT INTO ops.llm_call (purpose, model, thinking, status, latency_ms) VALUES ('p', 'm', 'adaptive', 'meh', 1)")
    assert expect_violation(db, "INSERT INTO ops.llm_call (purpose, model, thinking, status, latency_ms) VALUES ('p', 'm', 'deep', 'ok', 1)")


def test_every_path_of_the_classify_job_works_under_dlck_etl(db):
    """Mọi đường job đi qua — đọc lẫn ghi — dưới role thật: INSERT hai bảng mới, UPDATE article + revision.summary_ai,
    INSERT article_ticker, SELECT industry / v_issuer_industry / security."""
    a, i = _article(db, "https://zz.test/s15-3"), _industry(db)
    db.execute(sa.text("INSERT INTO news.article_revision (article_id, version, title, content, content_fetched_at) VALUES (:a, 1, 'T', 'C', now())"), {"a": a})
    sid = db.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, status) VALUES ('ZZS', 'ZZ', 'stock', 'listed') RETURNING security_id")).scalar_one()
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text("UPDATE news.article SET group_no = 3, sub = '3d', confidence = 0.9, classified_from = 'content', content_chars = 1, labels = '{}' WHERE article_id = :a"), {"a": a})
    db.execute(sa.text("UPDATE news.article_revision SET summary_ai = 'S' WHERE article_id = :a AND version = 1"), {"a": a})
    db.execute(sa.text("INSERT INTO news.article_ticker (article_id, security_id, via) VALUES (:a, :s, 'ai')"), {"a": a, "s": sid})
    db.execute(sa.text("INSERT INTO news.article_industry (article_id, industry_id, via, confidence) VALUES (:a, :i, 'ai', 0.9)"), {"a": a, "i": i})
    db.execute(sa.text("INSERT INTO ops.llm_call (purpose, model, thinking, article_id, status, latency_ms) VALUES ('news.classify', 'm', 'adaptive', :a, 'ok', 1)"), {"a": a})
    assert db.execute(sa.text("SELECT count(*) FROM market.industry WHERE level = 2")).scalar_one() == 24
    assert db.execute(sa.text("SELECT count(*) FROM market.v_issuer_industry")).scalar_one() >= 0
    assert db.execute(sa.text("SELECT summary_ai FROM news.article_revision WHERE article_id = :a"), {"a": a}).scalar_one() == "S"


def test_api_role_can_read_article_industry(db):
    a, i = _article(db, "https://zz.test/s15-4"), _industry(db)
    db.execute(sa.text("INSERT INTO news.article_industry (article_id, industry_id, via) VALUES (:a, :i, 'ticker')"), {"a": a, "i": i})
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert db.execute(sa.text("SELECT count(*) FROM news.article_industry WHERE article_id = :a"), {"a": a}).scalar_one() == 1
