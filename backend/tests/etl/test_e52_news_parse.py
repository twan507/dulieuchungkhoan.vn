"""Registry 53 nguồn từ feeds.json; parse RSS/sitemap/danh sách thuần — literal từ fixture chụp 2026-09-05 (CAPTURE-2026-09-05.txt)."""
import pathlib
from datetime import datetime, timezone, timedelta

import pytest

from etl import news_parse as np_
from etl import news_registry as nr

FIX = pathlib.Path(__file__).parent / "fixtures" / "news"
VN = timezone(timedelta(hours=7))
REG = {(s.name, s.kind, s.feed_slug): s for s in nr.build()}


def _src(name, kind="rss", slug=None, group=3):
    return nr.Source(name=name, kind=kind, url=f"https://{name}.vn/x", group_from_feed=group, feed_slug=slug or "x")


def _feed(name):
    return np_.decode((FIX / f"feed-{name}.xml").read_bytes())


def test_registry_53_sources_groups_and_slugs():
    s = nr.build()
    assert len(s) == 53 and sum(1 for x in s if x.kind == "rss") == 47
    assert [sum(1 for x in s if x.kind == "rss" and x.group_from_feed == g) for g in (1, 2, 3)] == [14, 12, 21]
    assert {x.name for x in s} == set(nr.SOURCES)
    kinds = [x.kind for x in s if x.kind != "rss"]
    assert sorted(kinds) == ["bcp_list", "cafef_cbtt", "tnck_category", "tnck_category", "tnck_category", "tnck_sitemap"]
    assert REG[("vietstock", "rss", "739/chung-khoan/giao-dich-noi-bo")].url == "https://vietstock.vn/739/chung-khoan/giao-dich-noi-bo.rss"
    assert REG[("cafef", "cafef_cbtt", "cbtt")].group_from_feed == 3 and REG[("baochinhphu", "bcp_list", "chi-dao-dieu-hanh")].group_from_feed == 1
    tn = {x.feed_slug: x.group_from_feed for x in s if x.kind == "tnck_category"}
    assert tn == {"ck-quoc-te": 2, "chung-khoan": 3, "dau-tu": 1}
    assert nr.sitemap_url(datetime(2026, 9, 5, tzinfo=VN)) == "https://www.tinnhanhchungkhoan.vn/sitemaps/news-2026-9.xml"
    # C1 (spec §4.6-III): chuyên mục trước, sitemap sau — sitemap chỉ vá lỗ, không được thắng bản có nhóm.
    assert s[-1].kind == "tnck_sitemap"
    # M5: url của tnck_sitemap là mẫu {y}-{m} (hằng SITEMAP), không phải literal năm cứng 2026 chép từ feeds.json.
    assert REG[("tinnhanhck", "tnck_sitemap", "sitemap")].url == nr.SITEMAP


def test_registry_refuses_when_counts_drift(tmp_path):
    import json
    d = json.loads(nr.FEEDS_JSON.read_text(encoding="utf-8"))
    d["1_vi_mo_trong_nuoc"].pop()
    p = tmp_path / "feeds.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    with pytest.raises(nr.RegistryError):
        nr.build(p)


def test_decode_by_null_bytes_not_by_declared_encoding():
    assert np_.decode((FIX / "feed-bnews.xml").read_bytes())[:5] == "<?xml"           # UTF-16LE thật
    vb = np_.decode((FIX / "feed-vietnambiz.xml").read_bytes())
    assert 'encoding="utf-16"' in vb[:100] and "�" not in vb                        # khai utf-16, byte UTF-8


def test_canonical_url_rules():
    assert np_.canonical_url("https://cafef.vn/du-lieu/HBC-2970021/hbc.chn?utm_source=du-lieu") == "https://cafef.vn/du-lieu/HBC-2970021/hbc.chn"
    assert np_.canonical_url("http://vietstock.vn/2026/09/a-830-1489047.htm#x") == "https://vietstock.vn/2026/09/a-830-1489047.htm"
    assert np_.canonical_url("https://bnews.vn/a/435525.html/") == "https://bnews.vn/a/435525.html"
    assert np_.canonical_url("https://x.vn/a?page=2&utm_medium=rss&gidzl=abc&fbclid=1") == "https://x.vn/a?page=2"
    assert np_.canonical_url("HTTPS://Cafef.VN/a.chn") == "https://cafef.vn/a.chn"


def test_norm_title_strips_accents_prefixes_and_punctuation():
    assert np_.norm_title("(Chinhphu.vn) - Cơ chế, chính sách xác định giá!") == "cochechinhsachxacdinhgia"
    assert np_.norm_title("Đầu tư công: 'ĐTCK' đánh giá") == "dautucongdtckdanhgia"
    assert np_.norm_title("(ĐTCK) VN-Index tăng 25 điểm") == np_.norm_title("VN-INDEX TĂNG 25 ĐIỂM")
    assert np_.norm_title("BNEWS Đà tăng mạnh") == "datangmanh"
    assert np_.norm_title("") == ""


def test_pubdate_four_rules():
    assert np_.parse_pubdate("Sat, 05 Sep 26 17:09:00 +0700", "cafef") == (datetime(2026, 9, 5, 17, 9, tzinfo=VN), "feed")
    assert np_.parse_pubdate("Fri, 04 Sep 2026 02:43:06 GMT", "vneconomy")[0] == datetime(2026, 9, 4, 9, 43, 6, tzinfo=VN)
    assert np_.parse_pubdate("Fri, 04 Sep 2026 18:48:27 GMT+7", "vietnambiz")[0] == datetime(2026, 9, 4, 18, 48, 27, tzinfo=VN)
    assert np_.parse_pubdate("9/5/2026 1:30:00 PM", "baochinhphu") == (datetime(2026, 9, 5, 13, 30, tzinfo=VN), "feed")
    assert np_.parse_pubdate("", "vietnambiz") == (None, "unknown")
    assert np_.parse_pubdate("hôm nay", "cafef") == (None, "unknown")


def test_time_from_url_vietnambiz_and_baochinhphu():
    assert np_.time_from_url("https://vietnambiz.vn/tch-va-hai-ma-202694173243150.htm", "vietnambiz") == datetime(2026, 9, 4, 17, 32, 43, tzinfo=VN)
    assert np_.time_from_url("https://baochinhphu.vn/x-102260905122709839.htm", "baochinhphu") == datetime(2026, 9, 5, 12, 27, 9, tzinfo=VN)
    assert np_.time_from_url("https://cafef.vn/x-188260905170800678.chn", "cafef") is None


def test_parse_rss_literals_per_source():
    cafef = np_.parse_rss(_feed("cafef"), _src("cafef", slug="thi-truong-chung-khoan"))
    assert len(cafef) == 50 and cafef[0].url == "https://cafef.vn/green-sm-co-dong-thai-moi-tai-loat-tinh-thanh-phia-nam-188260905170800678.chn"
    assert cafef[0].title == "Green SM có động thái mới tại loạt tỉnh thành phía Nam" and cafef[0].published_at == datetime(2026, 9, 5, 17, 9, tzinfo=VN)
    assert cafef[0].published_at_src == "feed" and cafef[0].group_from_feed == 3 and cafef[0].rule == "cafef" and cafef[0].feed_slug == "thi-truong-chung-khoan"
    vs = np_.parse_rss(_feed("vietstock"), _src("vietstock"))
    assert len(vs) == 30 and vs[0].url.startswith("http://vietstock.vn/") and vs[0].canonical_url.startswith("https://vietstock.vn/2026/09/chi-2-phien")
    vb = np_.parse_rss(_feed("vietnambiz"), _src("vietnambiz"))
    assert vb[0].title == "TCH và hai mã họ FPT tăng mạnh nhất danh mục PYN Elite trong tháng 8"       # entity đã unescape
    assert vb[0].published_at == datetime(2026, 9, 4, 18, 48, 27, tzinfo=VN) and vb[0].published_at_src == "feed"
    bn = np_.parse_rss(_feed("bnews"), _src("bnews"))
    assert len(bn) == 20 and bn[0].title == "VN-Index tăng hơn 25 điểm nhờ cổ phiếu đầu ngành bất động sản"
    bcp = np_.parse_rss(_feed("baochinhphu"), _src("baochinhphu", group=1))
    assert bcp[0].published_at == datetime(2026, 9, 5, 13, 30, tzinfo=VN) and bcp[0].published_at_src == "feed"
    assert np_.parse_rss(_feed("vneconomy"), _src("vneconomy"))[0].published_at == datetime(2026, 9, 4, 9, 43, 6, tzinfo=VN)
    assert all(it.sapo_raw for it in cafef[:5])


def test_parse_rss_empty_pubdate_falls_back_to_url_then_unknown():
    xml = ('<rss><channel><item><title>A</title><link>https://vietnambiz.vn/a-202694173243150.htm</link><pubDate></pubDate></item>'
           '<item><title>B</title><link>https://vietnambiz.vn/b.htm</link></item></channel></rss>')
    a, b = np_.parse_rss(xml, _src("vietnambiz"))
    assert (a.published_at, a.published_at_src) == (datetime(2026, 9, 4, 17, 32, 43, tzinfo=VN), "url")
    assert (b.published_at, b.published_at_src) == (None, "unknown")
    with pytest.raises(np_.ParseError):
        np_.parse_rss("<html>not rss</html>", _src("cafef"))


def test_parse_sitemap_drops_homepage_entry_and_keeps_lastmod():
    items = np_.parse_sitemap((FIX / "sitemap-2026-9.xml").read_text(encoding="utf-8"), _src("tinnhanhck", "tnck_sitemap", "sitemap", None))
    assert len(items) == 244 and all(it.url.endswith(".html") and "-post" in it.url for it in items)
    assert items[0].url.endswith("-post396857.html") and items[0].published_at == datetime(2026, 9, 1, 20, 41, 41, tzinfo=VN)
    assert items[-1].url.endswith("-post397051.html") and items[-1].published_at == datetime(2026, 9, 5, 20, 39, 34, tzinfo=VN)
    assert items[0].published_at_src == "feed" and items[0].group_from_feed is None and items[0].feed_slug == "sitemap" and items[0].rule == "tinnhanhck"


def test_parse_cafef_cbtt_extracts_ticker_and_drops_exchanges():
    # M2: số chính xác, đếm độc lập với code — grep -oE '/du-lieu/[A-Z0-9]{2,6}-[0-9]+/[^"'"'"' ]*\.chn'
    #   tests/etl/fixtures/news/list-cafef-cbtt.html | sort -u | wc -l  ⇒ 21
    items = np_.parse_cafef_cbtt((FIX / "list-cafef-cbtt.html").read_text(encoding="utf-8"), _src("cafef", "cafef_cbtt", "cbtt"))
    assert len(items) == 21 and items[0].canonical_url == "https://cafef.vn/du-lieu/HBC-2970021/hbc-bao-cao-tai-chinh-ban-nien-nam-2026.chn"
    assert items[0].ticker_from_url == "HBC" and items[0].rule == "cafef_cbtt" and items[0].published_at is None and items[0].published_at_src == "unknown"
    assert all(it.ticker_from_url not in ("HNX", "HOSE", "UPCOM") for it in items)
    html = '<a href="/du-lieu/HNX-1/x.chn">x</a><a href="/du-lieu/ABC-2/y.chn?utm_source=du-lieu">y</a><a href="/du-lieu/ABC-2/y.chn">y</a>'
    only = np_.parse_cafef_cbtt(html, _src("cafef", "cafef_cbtt", "cbtt"))
    assert [(i.ticker_from_url, i.canonical_url) for i in only] == [(None, "https://cafef.vn/du-lieu/HNX-1/x.chn"), ("ABC", "https://cafef.vn/du-lieu/ABC-2/y.chn")]


def test_parse_tnck_category_and_bcp_list_unique_article_links():
    # M2: số chính xác, đếm độc lập với code — grep -oE 'https://www\.tinnhanhchungkhoan\.vn[^"'"'"' >]*-post[0-9]+\.html'
    #   tests/etl/fixtures/news/list-tnck-chung-khoan.html | sort -u | wc -l  ⇒ 98
    tn = np_.parse_tnck_category((FIX / "list-tnck-chung-khoan.html").read_text(encoding="utf-8"), _src("tinnhanhck", "tnck_category", "chung-khoan", 3))
    assert len(tn) == 98 and len({i.canonical_url for i in tn}) == len(tn) and all(i.group_from_feed == 3 and i.rule == "tinnhanhck" for i in tn)
    assert any(i.url.endswith("-post397020.html") for i in tn)
    bcp = np_.parse_bcp_list((FIX / "list-bcp.html").read_text(encoding="utf-8"), _src("baochinhphu", "bcp_list", "chi-dao-dieu-hanh", 1))
    # Brief ước ~102 link, nhưng fixture list-bcp.html thực đo chỉ có 5 href khớp mẫu -102<15 số>.htm (5 bài, mỗi bài lặp href 2 lần -> unique 5).
    assert len(bcp) == 5 and all(i.url.startswith("https://baochinhphu.vn/") and i.url.endswith(".htm") for i in bcp)
    assert all(i.published_at_src == "url" and i.published_at is not None for i in bcp)          # giờ từ 102YYMMDDHHMMSS
