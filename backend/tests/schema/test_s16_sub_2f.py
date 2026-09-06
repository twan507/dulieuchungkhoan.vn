"""Migration 0019: sub nhận thêm '2f'; mã lạ vẫn bị chặn; 21 mã cũ vẫn hợp lệ."""
import sqlalchemy as sa

from tests.conftest import expect_violation


def _article(db, url):
    return db.execute(sa.text("INSERT INTO news.article (canonical_url, primary_source, fetched_at) VALUES (:u, 'cafef', now()) RETURNING article_id"),
                      {"u": url}).scalar_one()


def test_sub_2f_accepted_and_unknown_rejected(db):
    a = _article(db, "https://zz.test/s16-1")
    db.execute(sa.text("UPDATE news.article SET group_no = 2, sub = '2f' WHERE article_id = :a"), {"a": a})
    assert db.execute(sa.text("SELECT sub FROM news.article WHERE article_id = :a"), {"a": a}).scalar_one() == "2f"
    assert expect_violation(db, f"UPDATE news.article SET sub = '2g' WHERE article_id = {a}")
    assert expect_violation(db, f"UPDATE news.article SET sub = '1g' WHERE article_id = {a}")
    for s in ("1a", "2e", "3i"):
        db.execute(sa.text("UPDATE news.article SET sub = :s WHERE article_id = :a"), {"s": s, "a": a})
