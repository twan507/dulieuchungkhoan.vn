"""Lưới phân loại trên Postgres thật: chọn bài có trần, ghi article/revision/ticker/industry hai đường, sổ llm_call, guard quota,
cầu chì ModelDown, --dry-run không ghi. Client giả trả Structured theo kịch bản — không gọi model thật trong CI (test-strategy luật 1)."""
import json
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import sqlalchemy as sa

from core.llm import LLMError, QuotaRemains, Structured, Usage
from etl import news_classify as nc

VN = timezone(timedelta(hours=7))
CODES = ["NGANHANG", "CHUNGKHOAN", "BAOHIEM", "DANDUNG", "KHUCONGNGHIEP", "XAYDUNG", "VATLIEU", "KIMLOAI", "KHOANGSAN", "HOACHAT", "NHUA", "THIETBI",
         "NONGNGHIEP", "THUYSAN", "DETMAY", "CAOSU", "BANLE", "THUCPHAM", "DULICH", "YTE", "TIENICH", "DAUKHI", "VANTAI", "CONGNGHE"]
LONG = "Nội dung bài thử dài hơn hai trăm ký tự để classified_from là content. " * 5      # 350 ký tự
# (canonical_url, hint, giờ đăng, ticker_step_ran, tiêu đề) — mới nhất trước; A4/A5 cùng bucket NULL
ARTICLES = [("https://zz.test/classify-1", 1, "2026-09-06T10:00:00+07", False, "ZZ bài 1 thép tăng giá"),
            ("https://zz.test/classify-2", 2, "2026-09-06T09:00:00+07", False, "ZZ bài 2 Fed giữ lãi suất"),
            ("https://zz.test/classify-3", 3, "2026-09-06T08:00:00+07", True, "ZZ bài 3 ZZK báo lãi"),
            ("https://zz.test/classify-4", None, "2026-09-06T07:00:00+07", False, "ZZQ tăng vốn"),
            ("https://zz.test/classify-5", None, "2026-09-06T06:00:00+07", False, "ZZ bài 5 không nhóm")]


def _cleanup(engine):
    with engine.begin() as c:
        for t in ("news.article_industry", "ops.llm_call", "news.article_ticker", "news.article_source", "news.article_revision", "news.article"):
            c.execute(sa.text(f"DELETE FROM {t} WHERE {'article_id' if t != 'news.article' else 'article_id'} IN"
                              " (SELECT article_id FROM news.article WHERE canonical_url LIKE 'https://zz.test/classify-%')"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = 'news.classify'"))
        c.execute(sa.text("DELETE FROM market.security WHERE exchange = 'ZZ'"))
        c.execute(sa.text("DELETE FROM market.issuer WHERE name LIKE 'ZZ %'"))


@pytest.fixture()
def seeded(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.news_classify.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    with migrated_engine.begin() as c:
        kim = c.execute(sa.text("SELECT industry_id FROM market.industry WHERE code = 'KIMLOAI'")).scalar_one()
        i1 = c.execute(sa.text("INSERT INTO market.issuer (name, industry_id) VALUES ('ZZ Kim loai', :i) RETURNING issuer_id"), {"i": kim}).scalar_one()
        i2 = c.execute(sa.text("INSERT INTO market.issuer (name) VALUES ('ZZ Quy') RETURNING issuer_id")).scalar_one()
        c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, status, issuer_id)"
                          " VALUES ('ZZK', 'ZZ', 'stock', 'listed', :a), ('ZZQ', 'ZZ', 'stock', 'listed', :b)"), {"a": i1, "b": i2})
        ids = []
        for url, hint, pub, ran, title in ARTICLES:
            aid = c.execute(sa.text(
                "INSERT INTO news.article (canonical_url, primary_source, feed, published_at, published_at_src, fetched_at, group_from_feed, ticker_step_ran)"
                " VALUES (:u, 'cafef', 'zz', :p, 'feed', now(), :g, :r) RETURNING article_id"), {"u": url, "p": pub, "g": hint, "r": ran}).scalar_one()
            c.execute(sa.text("INSERT INTO news.article_revision (article_id, version, title, sapo, content, content_fetched_at)"
                              " VALUES (:a, 1, :t, 'Sapo', :c, now())"), {"a": aid, "t": title, "c": LONG})
            ids.append(aid)
    yield migrated_engine, ids
    _cleanup(migrated_engine)


def _ctx(engine):
    with engine.connect() as c:
        inds = c.execute(sa.text("SELECT industry_id, code, name_vi FROM market.industry WHERE level = 2 ORDER BY sort_order, code")).all()
        listed = dict(c.execute(sa.text("SELECT ticker, security_id FROM market.security WHERE status = 'listed'")).all())
    return {r.code: r.industry_id for r in inds}, listed, nc.build_schema([r.code for r in inds])


def _n(engine, sql, **p):
    with engine.connect() as c:
        return c.execute(sa.text(sql), p).scalar()


def test_select_per_group_takes_newest_per_bucket_and_skips_classified(seeded):
    engine, ids = seeded
    with engine.connect() as c:
        rows = nc.select_articles(c, per_group=1)
        assert [r.article_id for r in rows] == ids[:4]                                # 1 · 2 · 3 · NULL (A4 mới hơn A5)
        assert rows[0].title == "ZZ bài 1 thép tăng giá" and rows[0].content == LONG and rows[3].group_from_feed is None
        assert [r.article_id for r in nc.select_articles(c, limit=2)] == ids[:2]
    with engine.begin() as c:
        c.execute(sa.text("UPDATE news.article SET classified_from = 'content' WHERE article_id = :a"), {"a": ids[0]})
    with engine.connect() as c:
        assert [r.article_id for r in nc.select_articles(c, per_group=1)] == ids[1:4]
        assert len(nc.select_articles(c, per_group=5)) == 4                            # NULL bucket: A4 + A5


def test_apply_group3_with_ai_ticker_filter_and_industries_both_ways(seeded):
    engine, ids = seeded
    industry_ids, listed, S = _ctx(engine)
    v = S.model_validate({"group": "3", "sub": "3d", "confidence": 0.9, "summary_ai": "Tóm tắt 1", "tickers": ["ZZK", "VFM"], "industries": ["KIMLOAI", "XAYDUNG"]})
    with engine.connect() as c:
        row = [r for r in nc.select_articles(c, per_group=1) if r.article_id == ids[0]][0]
    with engine.begin() as c:
        st = nc.apply(c, row, v, content_chars=350, classified_from="content", listed=listed, industry_ids=industry_ids)
    assert st == {"overridden": 1, "tickers_url": 0, "tickers_lookup": 0, "tickers_ai": 1, "tickers_ai_dropped": 1, "industries_ai": 2, "industries_ticker": 1}
    with engine.connect() as c:
        a = c.execute(sa.text("SELECT group_no, sub, confidence, classified_from, content_chars, group_overridden, labels, ticker_step_ran"
                              " FROM news.article WHERE article_id = :a"), {"a": ids[0]}).one()
        assert tuple(a[:2]) == (3, "3d") and float(a[2]) == 0.9 and tuple(a[3:]) == ("content", 350, True, [], True)
        assert c.execute(sa.text("SELECT summary_ai FROM news.article_revision WHERE article_id = :a AND version = 1"), {"a": ids[0]}).scalar_one() == "Tóm tắt 1"
        tk = c.execute(sa.text("SELECT s.ticker, t.via FROM news.article_ticker t JOIN market.security s USING (security_id) WHERE t.article_id = :a"), {"a": ids[0]}).all()
        assert [tuple(x) for x in tk] == [("ZZK", "ai")]
        ind = c.execute(sa.text("SELECT i.code, x.via, x.confidence FROM news.article_industry x JOIN market.industry i USING (industry_id)"
                                " WHERE x.article_id = :a ORDER BY x.via, i.code"), {"a": ids[0]}).all()
        ind_f = [(c, v, float(cf) if cf is not None else None) for c, v, cf in ind]
        assert ind_f == [("KIMLOAI", "ai", 0.9), ("XAYDUNG", "ai", 0.9), ("KIMLOAI", "ticker", None)]
    with engine.begin() as c:                                                             # idempotent
        st2 = nc.apply(c, row, v, content_chars=350, classified_from="content", listed=listed, industry_ids=industry_ids)
    assert st2["industries_ticker"] == 0 and _n(engine, "SELECT count(*) FROM news.article_industry WHERE article_id = :a", a=ids[0]) == 3
    assert _n(engine, "SELECT count(*) FROM news.article_ticker WHERE article_id = :a", a=ids[0]) == 1


def test_apply_x_label_and_tier2_catchup_for_ungrouped(seeded):
    engine, ids = seeded
    industry_ids, listed, S = _ctx(engine)
    with engine.connect() as c:
        rows = {r.article_id: r for r in nc.select_articles(c, per_group=5)}
    x = S.model_validate({"group": "x", "sub": "x", "confidence": 0.6, "summary_ai": "PR.", "tickers": [], "industries": []})
    with engine.begin() as c:
        st = nc.apply(c, rows[ids[1]], x, content_chars=350, classified_from="content", listed=listed, industry_ids=industry_ids)
    assert st["overridden"] == 1
    with engine.connect() as c:
        a = c.execute(sa.text("SELECT group_no, sub, confidence, labels, ticker_step_ran FROM news.article WHERE article_id = :a"), {"a": ids[1]}).one()
        assert tuple(a[:2]) == (None, None) and float(a[2]) == 0.6 and tuple(a[3:]) == (["x"], False)
    g3 = S.model_validate({"group": "3", "sub": "3c", "confidence": 0.8, "summary_ai": "Tăng vốn.", "tickers": [], "industries": ["CHUNGKHOAN", "CHUNGKHOAN"]})
    with engine.begin() as c:
        st = nc.apply(c, rows[ids[3]], g3, content_chars=350, classified_from="content", listed=listed, industry_ids=industry_ids)
    assert st == {"overridden": 0, "tickers_url": 0, "tickers_lookup": 1, "tickers_ai": 0, "tickers_ai_dropped": 0, "industries_ai": 1, "industries_ticker": 0}
    with engine.connect() as c:
        tk = c.execute(sa.text("SELECT s.ticker, t.via FROM news.article_ticker t JOIN market.security s USING (security_id) WHERE t.article_id = :a"), {"a": ids[3]}).all()
        assert [tuple(x) for x in tk] == [("ZZQ", "lookup")]                                # ZZQ không có ngành ⇒ 0 dòng 'ticker'
        assert c.execute(sa.text("SELECT ticker_step_ran, group_overridden FROM news.article WHERE article_id = :a"), {"a": ids[3]}).one() == (True, False)
    g1 = S.model_validate({"group": "1", "sub": "1c", "confidence": 0.7, "summary_ai": "Tỷ giá.", "tickers": ["ZZK"], "industries": ["NGANHANG"]})
    with engine.begin() as c:
        st = nc.apply(c, rows[ids[2]], g1, content_chars=350, classified_from="content", listed=listed, industry_ids=industry_ids)
    assert st["overridden"] == 1 and st["tickers_ai"] == 0                                 # nhóm ≠ 3: không chạm mã (tickers bị bỏ)
    assert _n(engine, "SELECT count(*) FROM news.article_ticker WHERE article_id = :a", a=ids[2]) == 0


def test_log_call_writes_tokens_and_failed_without_key(seeded):
    engine, ids = seeded
    with engine.begin() as c:
        nc.log_call(c, run_id=None, article_id=ids[0], model="MiniMax-M3", thinking="adaptive", status="ok", usage=Usage(214, 2816, 250, 120, 1, 5.5), latency_s=5.5)
        nc.log_call(c, run_id=None, article_id=ids[1], model="MiniMax-M3", thinking="disabled", status="failed", usage=None, latency_s=0.3, error="rate_limit: RateLimitError 429")
    with engine.connect() as c:
        rows = c.execute(sa.text("SELECT status, http_calls, input_tokens, cache_read_tokens, output_tokens, thinking_tokens, latency_ms, error"
                                 " FROM ops.llm_call WHERE purpose = 'news.classify' ORDER BY call_id")).all()
    assert [tuple(r) for r in rows] == [("ok", 1, 214, 2816, 250, 120, 5500, None), ("failed", 1, None, None, None, None, 300, "rate_limit: RateLimitError 429")]
