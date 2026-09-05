"""Job news.collect trọn vòng trên Postgres thật: 53 danh sách từ fixture, bài tổng hợp nhỏ dựng theo RULES (nhanh),
dedupe, ghi 4 bảng, domain state 8 báo, guard không chặn lượt, --dry-run/--sources, Ctrl+C, --loop."""
import os
import pathlib
import re
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sa

from etl import news_extract as ne
from etl import news_job as nj
from etl import news_parse as np_
from etl import news_registry as nr

FIX = pathlib.Path(__file__).parent / "fixtures" / "news"
VN = timezone(timedelta(hours=7))
NOW = datetime(2026, 9, 6, 0, 0, tzinfo=VN)
NAMES = nr.SOURCES
# 21 mã CBTT thật trong list-cafef-cbtt.html (đo: CIG CTD DLG DRH GSP HAP HBC LLM NAF PDV PLP SDT SGI SGP SJS TCR TDH VEC VPG VPH YBM) —
# phải nằm trong market.security 'listed' để tầng URL (§8 tầng 1) có security_id mà gắn (article_ticker.security_id NOT NULL FK).
CBTT_TICKERS = ("CIG", "CTD", "DLG", "DRH", "GSP", "HAP", "HBC", "LLM", "NAF", "PDV", "PLP",
                "SDT", "SGI", "SGP", "SJS", "TCR", "TDH", "VEC", "VPG", "VPH", "YBM")


def _it(url, group, pub=None, psrc="unknown"):
    cu = np_.canonical_url(url)
    return np_.Item("tinnhanhck", "x", url, cu, "T", None, pub, psrc, group, None, "tinnhanhck")


def test_merge_items_ungrouped_never_beats_grouped_regardless_of_order():
    # C1 (spec §4.6-III), hàm thuần — sitemap (group None) chỉ vá lỗ, không được thắng bản có nhóm, bất kể thứ tự đưa vào.
    grouped = _it("https://t.vn/a-post1.html", 3)
    ungrouped = _it("https://t.vn/a-post1.html", None, pub=NOW, psrc="feed")
    out1 = nj.merge_items([grouped, ungrouped])       # nhóm trước
    out2 = nj.merge_items([ungrouped, grouped])       # nhóm sau — vẫn phải thắng
    assert out1["https://t.vn/a-post1.html"].group_from_feed == 3
    assert out2["https://t.vn/a-post1.html"].group_from_feed == 3
    # nhóm thắng nhưng thiếu published_at ⇒ mượn published_at/psrc của bản thua (không mất ngày)
    assert out2["https://t.vn/a-post1.html"].published_at == NOW
    assert out2["https://t.vn/a-post1.html"].published_at_src == "feed"


def test_merge_items_keeps_url_absent_from_the_other_feed():
    only_grouped = _it("https://t.vn/b-post2.html", 1)
    only_ungrouped = _it("https://t.vn/c-post3.html", None)
    out = nj.merge_items([only_grouped, only_ungrouped])
    assert set(out) == {"https://t.vn/b-post2.html", "https://t.vn/c-post3.html"}


def _tag(sel):
    """'div.detail-content.afcbc-body' ⇒ '<div class="detail-content afcbc-body">'; 'div#vst_detail' ⇒ '<div id="vst_detail">'; 'main#article-editor'…
    Selector nhiều token cách nhau bởi khoảng trắng (vd 'td.a span.b', cafef_cbtt) ⇒ lồng nhau: mở theo thứ tự, đóng ngược lại.
    Tên thẻ chấp nhận chữ số ('h1')."""
    opens, closes = [], []
    for tok in sel.split(",")[0].strip().split():
        m = re.match(r"([a-z][a-z0-9]*)(#[\w-]+)?((?:\.[\w-]+)*)", tok)
        tag, idp, classes = m.group(1), m.group(2), m.group(3)
        attrs = (f' id="{idp[1:]}"' if idp else "") + (f' class="{" ".join(classes[1:].split("."))}"' if classes else "")
        opens.append(f"<{tag}{attrs}>")
        closes.append(f"</{tag}>")
    return "".join(opens), "".join(reversed(closes))


def _page(rule, title, n=1):
    # tickers_lookup chỉ quét title/sapo (không quét content) — nhét "HPG" vào TIÊU ĐỀ BÓC (không phải `title`
    # tham số dùng cho dedupe theo item.title feed thật) để tầng lookup nhóm 3 có mã mà bắt.
    r = ne.RULES[rule]
    co, cc = _tag(r.container)
    to, tc = _tag(r.title)
    body = " ".join(f"Đoạn {i} của bài {title} nói về HPG và thị trường." for i in range(n * 8))
    return f"<html><head></head><body>{to}{title} HPG{tc}{co}<p>{body}</p>{cc}</body></html>"


def _fake_get(calls=None, dead=(), feed_503=()):
    def get(u, timeout):
        if calls is not None:
            calls.append(u)
        for n in NAMES:
            if u.endswith(".rss") or "/rss/" in u:
                if n in u:
                    if any(x in u for x in feed_503):
                        return 503, "", {}
                    return 200, (FIX / f"feed-{n}.xml").read_bytes().decode("utf-16-le" if n == "bnews" else "utf-8", errors="replace"), {}
        if "tin-doanh-nghiep.chn" in u:
            return 200, (FIX / "list-cafef-cbtt.html").read_text(encoding="utf-8"), {}
        if "/sitemaps/" in u:
            return 200, (FIX / "sitemap-2026-9.xml").read_text(encoding="utf-8"), {}
        if u.rstrip("/").endswith(("/ck-quoc-te", "/chung-khoan", "/dau-tu")):
            return 200, (FIX / "list-tnck-chung-khoan.html").read_text(encoding="utf-8"), {}
        if "chi-dao-dieu-hanh.htm" in u:
            return 200, (FIX / "list-bcp.html").read_text(encoding="utf-8"), {}
        if any(d in u for d in dead):
            return 404, "", {}
        rule = "cafef_cbtt" if "/du-lieu/" in u else next((n for n in NAMES if n in u or (n == "tinnhanhck" and "tinnhanhchungkhoan" in u)), "cafef")
        return 200, _page(rule, f"Bài {abs(hash(u)) % 100000}") * 9, {}          # ×6 không đủ 5 KB (đo: bnews 4.984 B) — ×9 an toàn
    return get


def _cleanup(engine):
    with engine.begin() as c:
        for t in ("news.article_ticker", "news.article_source", "news.article_revision", "news.article"):
            c.execute(sa.text(f"DELETE FROM {t}"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source = ANY(:s)"), {"s": list(NAMES)})
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job LIKE 'news.%'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE domain='news'"))
        c.execute(sa.text("DELETE FROM market.security WHERE exchange = 'ZZ'"))


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.news_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    with migrated_engine.begin() as c:
        c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, status) VALUES ('HPG','ZZ','stock','listed')"))
        c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, status) SELECT unnest(cast(:ts AS text[])), 'ZZ', 'stock', 'listed'"),
                  {"ts": list(CBTT_TICKERS)})
    yield migrated_engine
    _cleanup(migrated_engine)


def _last(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job='news.collect' ORDER BY run_id DESC LIMIT 1")).one()


def _n(engine, sql):
    with engine.connect() as c:
        return c.execute(sa.text(sql)).scalar()


def test_full_cycle_writes_articles_sources_tickers_and_domain_state(clean):
    calls = []
    assert nj.run(get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and stats["lists_ok"] == 53 and stats["lists_failed"] == 0 and stats["cycle"] == 0
    assert stats["items"] > 300 and stats["new"] == stats["items"] and stats["articles_ok"] + stats["articles_failed"] + stats["refused"] == stats["new"]
    assert stats["articles_ok"] > 300 and stats["refused"] == 0 and stats["articles_failed"] == 0
    assert _n(clean, "SELECT count(*) FROM news.article") == stats["articles_ok"]
    assert _n(clean, "SELECT count(*) FROM news.article_revision") == stats["articles_ok"]
    assert _n(clean, "SELECT count(*) FROM news.article_source") >= stats["articles_ok"]
    assert _n(clean, "SELECT count(*) FROM news.article_ticker WHERE via='url'") >= 15                       # CBTT: mã từ URL
    assert _n(clean, "SELECT count(*) FROM news.article_ticker WHERE via='lookup'") > 0                      # 'HPG' trong bài tổng hợp nhóm 3
    assert _n(clean, "SELECT count(*) FROM news.article WHERE group_from_feed = 3 AND NOT ticker_step_ran") == 0
    assert _n(clean, "SELECT count(*) FROM news.article WHERE group_from_feed IN (1,2) AND ticker_step_ran") == 0
    # C1 (spec §4.6-III): sitemap chỉ vá lỗ — mọi URL sitemap CŨNG có mặt ở trang chuyên mục phải thắng bởi bản chuyên
    # mục (có nhóm), không phải sitemap. feed='sitemap' chỉ còn lại cho URL sitemap KHÔNG có trong trang chuyên mục —
    # đếm độc lập bằng cách parse hai fixture ngay trong test (không tái dùng PARSERS của job).
    cat_html = (FIX / "list-tnck-chung-khoan.html").read_text(encoding="utf-8")           # fixture dùng chung cho cả 3 chuyên mục
    sm_xml = (FIX / "sitemap-2026-9.xml").read_text(encoding="utf-8")
    cat_urls = set(re.findall(r"https://www\.tinnhanhchungkhoan\.vn/[^\"'<> ]*-post\d+\.html", cat_html))
    sm_urls = set(re.findall(r"<loc>(https://www\.tinnhanhchungkhoan\.vn/[^<]*-post\d+\.html)</loc>", sm_xml))
    only_in_sitemap = sm_urls - cat_urls
    assert _n(clean, "SELECT count(*) FROM news.article WHERE feed='sitemap' AND group_from_feed IS NULL") == len(only_in_sitemap)
    # đo thật: 53 danh sách khác nhau (source,url), raw_payload trống trước lượt ⇒ CẢ 53 đều "đổi hash" lần đầu —
    # không chỉ 3 báo cbtt/bnews/tinnhanhck (12 dòng) như phác thảo ban đầu; sửa vế truy vấn khớp toàn bộ 8 báo.
    assert _n(clean, "SELECT count(*) FROM staging.raw_payload WHERE source = ANY(ARRAY['cafef','vietstock','vneconomy','vietnambiz','bnews','nguoiquansat','baochinhphu','tinnhanhck']) AND NOT coalesce((meta->>'refused')::bool,false)") == stats["lists_stored"] == 53
    assert _n(clean, "SELECT count(*) FROM staging.raw_payload WHERE (meta->>'refused')::bool") == 0
    assert _n(clean, "SELECT count(*) FROM ops.data_domain_state WHERE domain='news'") == 8
    assert stats["stale_feeds"] == [] or all("/" in s for s in stats["stale_feeds"])
    # lượt hai cùng fixture: mọi item đã thấy
    assert nj.run(get=_fake_get(), sleep=lambda s: None, now=NOW + timedelta(minutes=5)) == 0
    status, stats2, _ = _last(clean)
    assert stats2["new"] == 0 and stats2["seen"] == stats2["items"] and stats2["cycle"] == 0
    assert _n(clean, "SELECT count(*) FROM news.article_revision WHERE version > 1") == 0


def test_title_merge_across_sources_keeps_both_urls(clean):
    # I3: tiêu đề dùng khoá chuẩn hoá >= TITLE_MIN_CHARS (32 ký tự) — "Cùng một tin lớn" (13 ký tự) không còn dedupe được.
    TITLE = "VN-Index giảm điểm mạnh phiên chiều nay"
    def get(u, timeout):
        if u.endswith(".rss") or "/rss/" in u:
            n = next(n for n in NAMES if n in u)
            return 200, (f'<rss><channel><item><title>{TITLE}</title><link>https://{n}.vn/tin-lon-{n}.htm</link>'
                         f'<pubDate>Sat, 05 Sep 2026 20:00:00 +0700</pubDate></item></channel></rss>'), {}
        return 404, "", {}
    assert nj.run(sources=["cafef", "bnews"], get=get, sleep=lambda s: None, now=NOW) == 0
    _, stats, _ = _last(clean)
    assert stats["subset"] is True and "watermark" not in stats
    assert _n(clean, "SELECT count(*) FROM news.article") == 0 and stats["articles_failed"] > 0           # bài 404 ⇒ không article
    # bài thật cho cafef, bnews merge theo tiêu đề
    def get2(u, timeout):
        st, body, h = get(u, timeout)
        if st == 404 and "tin-lon-cafef" in u:
            return 200, _page("cafef", TITLE) * 9, {}
        return st, body, h
    assert nj.run(sources=["cafef", "bnews"], get=get2, sleep=lambda s: None, now=NOW) == 0
    _, stats, _ = _last(clean)
    assert stats["articles_ok"] == 1 and stats["merged_title"] == 1
    assert _n(clean, "SELECT count(DISTINCT source_name) FROM news.article_source") == 2
    assert _n(clean, "SELECT count(*) FROM ops.data_domain_state WHERE domain='news'") == 0


def test_feed_failures_do_not_refuse_the_run_but_warn_over_20_percent(clean):
    bad = ("cafef.vn", "vietstock.vn", "vneconomy.vn", "vietnambiz.vn", "bnews.vn", "nguoiquansat.vn", "baochinhphu.vn")   # 47/47 feed 503
    assert nj.run(get=_fake_get(feed_503=bad), sleep=lambda s: None, now=NOW) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and stats["lists_failed"] == 47 and stats["lists_ok"] == 6 and any("feed" in w for w in stats["warnings"])
    assert _n(clean, "SELECT count(*) FROM ops.data_domain_state WHERE domain='news' AND source IN ('cafef','tinnhanhck','baochinhphu')") == 3


def test_refused_extraction_stores_evidence_and_no_article(clean, monkeypatch):
    def get(u, timeout):
        if u.endswith(".rss") or "/rss/" in u:
            return 200, ('<rss><channel><item><title>Rỗng</title><link>https://cafef.vn/rong-1.chn</link>'
                         '<pubDate>Sat, 05 Sep 2026 20:00:00 +0700</pubDate></item></channel></rss>'), {}
        return 200, "<html><h1 class='title'>Rỗng</h1><div class='detail-content afcbc-body'>x</div></html>" + " " * 6000, {}
    assert nj.run(sources=["cafef"], get=get, sleep=lambda s: None, now=NOW) == 0
    _, stats, _ = _last(clean)
    assert stats["refused"] == 1 and _n(clean, "SELECT count(*) FROM news.article") == 0
    assert _n(clean, "SELECT meta->>'reason' FROM staging.raw_payload WHERE source='cafef' AND (meta->>'refused')::bool") == "too_short"
    # Part C (§4.6-VII): cùng URL, lượt 2 — đã từ chối trong 7 ngày ⇒ KHÔNG tải lại, KHÔNG ghi bằng chứng lại.
    def get_short(u, timeout):
        st, b, h = get(u, timeout)
        return (200, "<html>tiny</html>", h) if st == 200 and not u.endswith(".rss") else (st, b, h)
    assert nj.run(sources=["cafef"], get=get_short, sleep=lambda s: None, now=NOW) == 0
    _, stats2, _ = _last(clean)
    assert stats2["skipped_refused"] == 1 and stats2["new"] == 0 and stats2.get("refused", 0) == 0
    assert _n(clean, "SELECT count(*) FROM staging.raw_payload WHERE (meta->>'refused')::bool") == 1
    assert not any("bóc từ chối" in w for w in stats2["warnings"])


def test_dry_run_writes_nothing_and_reports_new(clean):
    assert nj.run(dry_run=True, get=_fake_get(), sleep=lambda s: None, now=NOW) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and stats["dry_run"] is True and stats["new"] > 300 and "articles_ok" not in stats
    assert _n(clean, "SELECT count(*) FROM news.article") == 0 and _n(clean, "SELECT count(*) FROM staging.raw_payload WHERE source='cafef'") == 0


def test_loop_runs_cycles_until_minutes_and_sleeps_the_remainder(clean, monkeypatch):
    # `sleep` dùng chung cho hai việc: giãn cách ngẫu nhiên [1,5) s giữa các lời gọi HTTP của Fetcher (news_fetch.py) VÀ
    # nhịp nghỉ giữa hai vòng thu — cả hai đi qua CÙNG một callable `run(sleep=...)`. Tắt hẳn throttle của Fetcher
    # (không dùng clock() — xác nhận trong etl/http_fetch.py: Fetcher._throttle chỉ gọi self._sleep, không đụng clock)
    # để `sleep` giả chỉ còn nhận đúng nhịp giữa-vòng, khỏi phải lọc theo dải giá trị.
    # Dãy `clock()`: t0 · (started·kiểm phút·tính ngủ) × 3 vòng — số lần gọi đúng bằng code thật (news_job.run),
    # đã đo lại (dãy dự kiến trong plan không khớp số lần gọi thật, sửa theo code, ghi report).
    monkeypatch.setattr("etl.http_fetch.Fetcher._throttle", lambda self: None)
    slept, ticks = [], iter([0.0, 10.0, 10.0, 20.0, 20.0, 20.0, 320.0, 320.0, 500.0])
    assert nj.run(loop=True, minutes=8, get=_fake_get(), sleep=slept.append, now=NOW, clock=lambda: next(ticks)) == 0
    assert _n(clean, "SELECT count(*) FROM ops.etl_run WHERE job='news.collect'") == 3 and slept == [290.0, 0.0]   # vòng 2 vượt 300 s ⇒ không ngủ
    with clean.connect() as c:
        cycles = [r[0] for r in c.execute(sa.text("SELECT (stats->>'cycle')::int FROM ops.etl_run WHERE job='news.collect' ORDER BY run_id"))]
    assert cycles == [0, 1, 2]


def test_loop_minutes_one_stops_after_a_single_cycle_and_never_sleeps_past_it(clean, monkeypatch):
    # I5: --minutes là TRẦN tổng thời gian, không phải "một vòng + một nhịp đầy". Với minutes=1 (60 s ngân sách),
    # cycle 0 đã ăn hết ngân sách (đo clock 70 s > 60 s) ⇒ `remaining <= 0` trả về NGAY, không mở vòng 2, không ngủ.
    # Dãy clock(): t0 · started(vòng 0) · kiểm phút (remaining<=0 ⇒ return trước khi tính-ngủ).
    monkeypatch.setattr("etl.http_fetch.Fetcher._throttle", lambda self: None)
    slept, ticks = [], iter([0.0, 0.0, 70.0])
    assert nj.run(loop=True, minutes=1, get=_fake_get(), sleep=slept.append, now=NOW, clock=lambda: next(ticks)) == 0
    assert _n(clean, "SELECT count(*) FROM ops.etl_run WHERE job='news.collect'") == 1
    assert slept == [] and all(s <= 60 for s in slept)


def test_ctrl_c_between_cycles_returns_130_without_a_dangling_run(clean, monkeypatch):
    # Ctrl+C rơi đúng vào nhịp NGỦ GIỮA HAI VÒNG (news_job.run: except KeyboardInterrupt bọc quanh sleep(...) sau
    # vòng 0), không phải throttle HTTP của Fetcher trong lúc thu (news_fetch.py dùng chung Fetcher với các job khác).
    # Tắt throttle như test_loop_… ở trên để `sleep` giả chỉ được gọi đúng một lần — bởi vòng ngủ thật — nên "ném luôn"
    # là đủ, không cần phân biệt theo giá trị.
    monkeypatch.setattr("etl.http_fetch.Fetcher._throttle", lambda self: None)
    def sleep_boom(s):
        raise KeyboardInterrupt
    ticks = iter([0.0, 10.0, 20.0])                    # t0 · started(vòng 0) · tính-ngủ-giữa-vòng — vòng 1 không kịp mở
    assert nj.run(loop=True, minutes=None, get=_fake_get(), sleep=sleep_boom, now=NOW, clock=lambda: next(ticks)) == 130
    with clean.connect() as c:
        rows = c.execute(sa.text("SELECT status FROM ops.etl_run WHERE job='news.collect' ORDER BY run_id")).all()
    assert [r[0] for r in rows] == ["success"]          # vòng 0 đã đóng thành công; không dòng running/failed của vòng 1


def test_unknown_source_and_ctrl_c(clean, monkeypatch):
    assert nj.run(sources=["cafef", "khong_co"], get=_fake_get(), sleep=lambda s: None, now=NOW) == 2
    def boom(*a, **k):
        raise KeyboardInterrupt
    monkeypatch.setattr(nj, "collect", boom)
    assert nj.run(get=_fake_get(), sleep=lambda s: None, now=NOW) == 130
    assert _last(clean)[2] == "dừng tay (Ctrl+C)"
