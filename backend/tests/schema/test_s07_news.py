import sqlalchemy as sa

from tests.schema.conftest import expect_violation


def _article(db, url="https://x.vn/a1", pub="2026-08-20T09:00:00+07"):
    return db.execute(sa.text(
        "INSERT INTO news.article (canonical_url,primary_source,published_at,fetched_at) "
        "VALUES (:u,'cafef',:p,now()) RETURNING article_id"), {"u": url, "p": pub}).scalar()

def _rev(db, aid, ver, title, content):
    db.execute(sa.text("INSERT INTO news.article_revision (article_id,version,title,content,content_fetched_at) "
                       "VALUES (:a,:v,:t,:c,now())"), {"a": aid, "v": ver, "t": title, "c": content})

def test_tsv_unaccented_search(db):                                 # seam 1 + 6
    a = _article(db)
    _rev(db, a, 1, "Tin thị trường", "HPG dẫn dắt nhóm chứng khoán hôm nay")
    b = _article(db, url="https://x.vn/a2")
    _rev(db, b, 1, "Tin khác", "Giá dầu tăng mạnh")
    hits = [r[0] for r in db.execute(sa.text(
        "SELECT article_id FROM news.article_revision "
        "WHERE tsv @@ to_tsquery('simple', news.immutable_unaccent('chung') || ' & ' || news.immutable_unaccent('khoan'))"))]
    assert a in hits and b not in hits

def test_revision_no_overwrite(db):                                 # seam 2
    a = _article(db, url="https://x.vn/a3")
    _rev(db, a, 1, "Bản 1", "nội dung 1")
    _rev(db, a, 2, "Bản 2", "nội dung 2")
    assert expect_violation(db,
        f"INSERT INTO news.article_revision (article_id,version,title,content,content_fetched_at) "
        f"VALUES ({a},1,'đè','x',now())")
    t1 = db.execute(sa.text("SELECT title FROM news.article_revision WHERE article_id=:a AND version=1"),
                    {"a": a}).scalar()
    assert t1 == "Bản 1"

def test_ticker_via_in_pk(db):                                      # seam 3 + 3b (I-1)
    a = _article(db, url="https://x.vn/a4")
    s = db.execute(sa.text("INSERT INTO market.security (ticker,exchange,security_type) "
                           "VALUES ('HPG','HOSE','stock') RETURNING security_id")).scalar()
    db.execute(sa.text("INSERT INTO news.article_ticker (article_id,security_id,via) "
                       "VALUES (:a,:s,'lookup'), (:a,:s,'ai')"), {"a": a, "s": s})
    assert expect_violation(db, f"INSERT INTO news.article_ticker VALUES ({a},{s},'ai')")
    assert expect_violation(db, f"INSERT INTO news.article_ticker (article_id,security_id,via) "
                                f"VALUES ({a},999999,'url')")

def test_published_unknown(db):                                     # seam 3c (I-2)
    aid = db.execute(sa.text(
        "INSERT INTO news.article (canonical_url,primary_source,published_at,published_at_src,fetched_at) "
        "VALUES ('https://x.vn/a5','vietnambiz',NULL,'unknown',now()) RETURNING article_id")).scalar()
    assert aid is not None

def test_trade_name_fuzzy(db):                                      # seam 4 + 4b — Levenshtein
    s = db.execute(sa.text("INSERT INTO market.security (ticker,exchange,security_type) "
                           "VALUES ('HPG2','HOSE','stock') RETURNING security_id")).scalar()
    db.execute(sa.text("INSERT INTO news.trade_name (name,security_id) VALUES ('Hòa Phát',:s)"), {"s": s})
    lev = db.execute(sa.text("SELECT extensions.levenshtein('ngui','nguoi')")).scalar()
    assert lev == 1                                                 # giải tay: thêm 1 chữ 'o'
    hit = db.execute(sa.text(
        "SELECT security_id FROM news.trade_name "
        "WHERE news.immutable_unaccent(name) OPERATOR(extensions.%) news.immutable_unaccent('Hoà Phát')")).scalar()
    assert hit == s                                                 # trgm bắt khác dấu thanh

def test_url_unique_and_labels(db):                                 # seam 5 + M13
    a = _article(db, url="https://x.vn/a6")
    b = _article(db, url="https://x.vn/a7")
    db.execute(sa.text("INSERT INTO news.article_source (article_id,source_name,url) "
                       "VALUES (:a,'cafef','https://cafef.vn/z1')"), {"a": a})
    assert expect_violation(db, f"INSERT INTO news.article_source (article_id,source_name,url) "
                                f"VALUES ({b},'vietstock','https://cafef.vn/z1')")
    assert expect_violation(db, f"UPDATE news.article SET group_no = 9 WHERE article_id = {a}")

def test_sub_taxonomy_check(db):                                    # fix round 1 — CHECK 20 sub (M-3)
    a = _article(db, url="https://x.vn/a8")
    assert expect_violation(db, f"UPDATE news.article SET sub = '9z' WHERE article_id = {a}")
    db.execute(sa.text("UPDATE news.article SET sub = '3b' WHERE article_id = :a"), {"a": a})
    sub = db.execute(sa.text("SELECT sub FROM news.article WHERE article_id = :a"), {"a": a}).scalar()
    assert sub == "3b"
