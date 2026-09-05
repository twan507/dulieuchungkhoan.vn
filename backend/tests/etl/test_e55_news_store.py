"""Đường ghi duy nhất vào news.* — dedupe theo URL/canonical/tiêu đề 48 giờ, bản ghi bất biến (revision), bằng chứng khi đổi/từ chối."""
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sa

from etl import news_extract as ne
from etl import news_parse as np_
from etl import news_store as ns
from etl.news_registry import Source

VN = timezone(timedelta(hours=7))
NOW = datetime(2026, 9, 6, 0, 0, tzinfo=VN)
SRC = Source("cafef", "rss", "https://cafef.vn/thi-truong-chung-khoan.rss", 3, "thi-truong-chung-khoan")
NAMES = ("cafef", "vietstock", "vneconomy", "vietnambiz", "bnews", "nguoiquansat", "baochinhphu", "tinnhanhck")


def _item(url, title="Tiêu đề A", pub=NOW - timedelta(hours=1), src="feed", group=3, ticker=None, rule="cafef", source="cafef"):
    return np_.Item(source, "x", url, np_.canonical_url(url), title, "sapo", pub, src, group, ticker, rule)


def _ext(content="Nội dung dài " * 20, title="Tiêu đề A", published=None):
    return ne.Extracted(title, "sapo sạch", content.strip(), published)


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM news.article_ticker"))
        c.execute(sa.text("DELETE FROM news.article_source"))
        c.execute(sa.text("DELETE FROM news.article_revision"))
        c.execute(sa.text("DELETE FROM news.article"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source = ANY(:s)"), {"s": list(NAMES)})
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE domain='news'"))
        c.execute(sa.text("DELETE FROM market.security WHERE ticker LIKE 'ZZ%'"))


@pytest.fixture()
def db(migrated_engine):
    _cleanup(migrated_engine)
    with migrated_engine.begin() as c:
        c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, status) VALUES ('ZZA','HOSE','stock','listed'), ('ZZB','HNX','stock','delisted')"))
    yield migrated_engine
    _cleanup(migrated_engine)


def _scalar(engine, sql, **p):
    with engine.connect() as c:
        return c.execute(sa.text(sql), p).scalar()


def test_load_listed_only_listed(db):
    with db.connect() as c:
        listed = ns.load_listed(c)
    assert "ZZA" in listed and "ZZB" not in listed and isinstance(listed["ZZA"], int)


def test_insert_article_writes_four_tables_and_second_time_is_seen(db):
    it = _item("https://cafef.vn/a-1.chn?utm_source=rss", ticker=None)
    with db.begin() as c:
        listed = ns.load_listed(c)
        aid = ns.insert_article(c, it, _ext(), fetched_at=NOW, tickers=[("ZZA", "lookup", listed["ZZA"])])
    assert _scalar(db, "SELECT canonical_url FROM news.article WHERE article_id=:a", a=aid) == "https://cafef.vn/a-1.chn"
    assert _scalar(db, "SELECT primary_source || '|' || feed || '|' || published_at_src || '|' || group_from_feed::text || '|' || ticker_step_ran::text FROM news.article WHERE article_id=:a", a=aid) == "cafef|x|feed|3|true"
    assert _scalar(db, "SELECT version FROM news.article_revision WHERE article_id=:a", a=aid) == 1
    assert _scalar(db, "SELECT url FROM news.article_source WHERE article_id=:a", a=aid) == "https://cafef.vn/a-1.chn?utm_source=rss"
    assert _scalar(db, "SELECT via FROM news.article_ticker WHERE article_id=:a", a=aid) == "lookup"
    with db.connect() as c:
        seen = ns.Seen.load(c, NOW)
    assert seen.decide(it, NOW) == ("seen", aid)


def test_decide_merge_url_merge_title_and_new(db):
    with db.begin() as c:
        aid = ns.insert_article(c, _item("https://cafef.vn/a-2.chn", title="VN-Index tăng 25 điểm"), _ext(), fetched_at=NOW, tickers=[])
    with db.connect() as c:
        seen = ns.Seen.load(c, NOW)
    assert seen.decide(_item("https://cafef.vn/a-2.chn?utm_medium=x"), NOW) == ("merge_url", aid)              # khác URL, cùng canonical
    assert seen.decide(_item("https://bnews.vn/b/1.html", title="VN-INDEX TĂNG 25 ĐIỂM!", source="bnews"), NOW) == ("merge_title", aid)
    assert seen.decide(_item("https://bnews.vn/b/2.html", title="VN-Index tăng 25 điểm", pub=NOW - timedelta(hours=49), source="bnews"), NOW)[0] == "new"
    assert seen.decide(_item("https://bnews.vn/b/3.html", title="Tin hoàn toàn khác", source="bnews"), NOW) == ("new", None)
    assert seen.decide(_item("https://bnews.vn/b/4.html", title="VN-Index tăng 25 điểm", pub=None, src="unknown", source="bnews"), NOW) == ("merge_title", aid)   # NULL ⇒ fetched_at
    seen.remember(_item("https://x.vn/n", title="Mới toanh"), 999, NOW)
    assert seen.decide(_item("https://y.vn/n2", title="mới toanh"), NOW) == ("merge_title", 999)


def test_add_source_is_idempotent_and_keeps_coverage(db):
    with db.begin() as c:
        aid = ns.insert_article(c, _item("https://cafef.vn/a-3.chn"), _ext(), fetched_at=NOW, tickers=[])
        assert ns.add_source(c, aid, "bnews", "https://bnews.vn/c/3.html") is True
        assert ns.add_source(c, aid, "bnews", "https://bnews.vn/c/3.html") is False
    assert _scalar(db, "SELECT count(DISTINCT source_name) FROM news.article_source WHERE article_id=:a", a=aid) == 2


def test_add_revision_appends_version_only_when_content_differs(db):
    with db.begin() as c:
        aid = ns.insert_article(c, _item("https://cafef.vn/a-4.chn"), _ext("bản một " * 30), fetched_at=NOW, tickers=[])
        assert ns.add_revision(c, aid, _ext("bản một " * 30), NOW + timedelta(hours=1)) is False
        assert ns.add_revision(c, aid, _ext("bản hai " * 30, title="Sửa tiêu đề"), NOW + timedelta(hours=2)) is True
    assert _scalar(db, "SELECT max(version) FROM news.article_revision WHERE article_id=:a", a=aid) == 2
    assert _scalar(db, "SELECT title FROM news.article_revision WHERE article_id=:a AND version=1", a=aid) == "Tiêu đề A"


def test_tsv_search_unaccented(db):
    with db.begin() as c:
        ns.insert_article(c, _item("https://cafef.vn/a-5.chn", title="Chứng khoán hôm nay"), _ext("HPG dẫn dắt nhóm chứng khoán " * 5), fetched_at=NOW, tickers=[])
    n = _scalar(db, "SELECT count(*) FROM news.article_revision WHERE tsv @@ to_tsquery('simple', 'chung & khoan')")
    assert n == 1


def test_published_for_prefers_feed_except_tinnhanhck(db):
    feed_t, page_t = NOW - timedelta(hours=3), NOW - timedelta(hours=5)
    assert ns.published_for(_item("https://cafef.vn/p", pub=feed_t), _ext(published=page_t)) == (feed_t, "feed")
    assert ns.published_for(_item("https://cafef.vn/p", pub=None, src="unknown"), _ext(published=page_t)) == (page_t, "feed")
    assert ns.published_for(_item("https://t.vn/p", pub=feed_t, source="tinnhanhck", rule="tinnhanhck"), _ext(published=page_t)) == (page_t, "feed")
    assert ns.published_for(_item("https://t.vn/p", pub=feed_t, source="tinnhanhck", rule="tinnhanhck"), _ext(published=None)) == (feed_t, "feed")
    assert ns.published_for(_item("https://v.vn/p", pub=feed_t, src="url", source="vietnambiz"), _ext(published=None)) == (feed_t, "url")
    assert ns.published_for(_item("https://v.vn/p", pub=None, src="unknown"), _ext(published=None)) == (None, "unknown")


def test_list_evidence_only_when_hash_changes_and_refusal_evidence(db):
    with db.begin() as c:
        assert ns.store_list_if_changed(c, "cafef", "https://cafef.vn/x.rss", "<rss>1</rss>", 1, "text") is True
        assert ns.store_list_if_changed(c, "cafef", "https://cafef.vn/x.rss", "<rss>1</rss>", 2, "text") is False
        assert ns.store_list_if_changed(c, "cafef", "https://cafef.vn/x.rss", "<rss>2</rss>", 3, "text") is True
        ns.store_refused(c, "bnews", "https://bnews.vn/dead.html", "<html>short</html>", "too_short", 3)
    assert _scalar(db, "SELECT count(*) FROM staging.raw_payload WHERE source='cafef' AND endpoint_key='https://cafef.vn/x.rss'") == 2
    assert _scalar(db, "SELECT meta->>'reason' FROM staging.raw_payload WHERE source='bnews' AND (meta->>'refused')::bool") == "too_short"


def test_domain_state_per_source(db):
    ns.upsert_domain_state(db, {"cafef", "bnews"}, "2026-09-06")
    with db.connect() as c:
        rows = dict(c.execute(sa.text("SELECT source, watermark FROM ops.data_domain_state WHERE domain='news'")).all())
    assert rows == {"cafef": "2026-09-06", "bnews": "2026-09-06"}


def test_store_works_under_etl_role(db):
    with db.begin() as c:
        c.execute(sa.text("SET LOCAL ROLE dlck_etl"))
        listed = ns.load_listed(c)
        aid = ns.insert_article(c, _item("https://cafef.vn/a-9.chn"), _ext(), fetched_at=NOW, tickers=[("ZZA", "url", listed["ZZA"])])
        ns.add_source(c, aid, "bnews", "https://bnews.vn/z/9.html")
        ns.add_revision(c, aid, _ext("khác " * 30), NOW)
        ns.store_list_if_changed(c, "cafef", "u", "t", 1, "text")
        ns.store_refused(c, "cafef", "u2", "<html></html>", "no_container", 1)
    assert _scalar(db, "SELECT count(*) FROM news.article_revision WHERE article_id=:a", a=aid) == 2
