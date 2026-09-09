"""Migration 0021: news.article.classify_attempts smallint NOT NULL DEFAULT 0 — đếm số lần model trả lỗi (lát 13 §5.4)."""
import sqlalchemy as sa


def test_classify_attempts_defaults_to_zero_and_counts_up(db):
    a = db.execute(sa.text("INSERT INTO news.article (canonical_url, primary_source, fetched_at) VALUES ('https://zz.test/s17-1', 'cafef', now()) RETURNING article_id")).scalar_one()
    assert db.execute(sa.text("SELECT classify_attempts FROM news.article WHERE article_id = :a"), {"a": a}).scalar_one() == 0
    db.execute(sa.text("UPDATE news.article SET classify_attempts = classify_attempts + 1 WHERE article_id = :a"), {"a": a})
    assert db.execute(sa.text("SELECT classify_attempts FROM news.article WHERE article_id = :a"), {"a": a}).scalar_one() == 1
    col = db.execute(sa.text("SELECT data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'news' AND table_name = 'article' AND column_name = 'classify_attempts'")).one()
    assert tuple(col) == ("smallint", "NO")
