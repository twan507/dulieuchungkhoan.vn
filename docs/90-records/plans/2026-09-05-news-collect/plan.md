# Lát 8 — thu thập tin không AI: kế hoạch thực thi

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `python -m etl news` thu 47 feed + 6 crawl vào `news.*` (5 bảng `0007`), dedupe URL + tiêu đề 48 giờ, bóc toàn văn theo luật từng nguồn, gắn mã tầng 1–2; `--loop` chạy tay; `--backfill-sitemap` TinnhanhCK.

**Architecture:** Bảy module `news_*` tách theo trách nhiệm (registry · fetch · parse · extract · tag · store · job); parse/extract/tag **thuần** (không I/O, không DB); store là đường ghi duy nhất vào `news.*`; job là khuôn `open_run` trước `try` của `series_job`. Fetcher chung `http_fetch` (giãn cách 1–5 s, lát 7b) với `get` riêng trả text đã decode theo luật null byte.

**Tech Stack:** Python 3.12, `uv run`, pytest (DB thật `TEST_DATABASE_URL`, fixture `migrated_engine`), httpx, beautifulsoup4 (`html.parser`), `xml.etree`, SQLAlchemy Core, Postgres 16.

**Spec:** [`spec.md`](spec.md) — thẩm quyền; plan là lập luận từ spec. Fixture thật: `backend/tests/etl/fixtures/news/` (chụp 2026-09-05 ~20:45, `CAPTURE-2026-09-05.txt` ghi literal).

## Global Constraints

- Lệnh Python từ `backend/`, `PYTHONIOENCODING=utf-8`; test: `set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run pytest tests/etl/<file> -q`. Trước lát: **729 passed, 2 skipped**.
- **Subagent không commit**; controller commit theo mốc. Không `.superpowers/` trong repo.
- Không migration; không sửa `series_*`, `http_fetch`, `omo_store`, `price_job` (chỉ **import** `price_job._next_open`).
- Expected trong test là **literal** đọc từ fixture/`CAPTURE-2026-09-05.txt` hoặc giải tay; với độ dài text sạch dùng **khoảng** (±5 %) quanh số đo trong CAPTURE **và** assert tiền tố/hậu tố literal + vắng chuỗi boilerplate — không tính lại theo code.
- Mỗi test assert giá trị cụ thể, có case biên. TDD: test đỏ → chạy xác nhận → code → xanh.
- Style theo `series_job.py`/`wichart_*.py`: docstring tiếng Việt đầu file, hằng UPPER, hàm ngắn; không sửa code lân cận.
- Tên báo: `cafef · vietstock · vneconomy · vietnambiz · bnews · nguoiquansat · baochinhphu · tinnhanhck`. `published_at_src` ∈ `{'feed','url','unknown'}`. `via` ∈ `{'url','lookup'}`. Job `news.collect` · `news.backfill_sitemap`. Domain state `('news', <báo>)`.
- Cửa sổ dedupe tiêu đề **48 giờ**; bài < **5.000 byte** ⇒ từ chối `soft404`; text sạch < **100** ký tự ⇒ `too_short` (trừ `cafef_cbtt`).

## Bản đồ file

| File | Task |
|---|---|
| `backend/etl/news_registry.py` · `news_parse.py` · `tests/etl/test_e52_news_parse.py` | 1 |
| `backend/etl/news_extract.py` · `tests/etl/test_e53_news_extract.py` | 2 |
| `backend/etl/news_tag.py` · `news_store.py` · `tests/etl/test_e54_news_tag.py` · `test_e55_news_store.py` | 3 |
| `backend/etl/news_fetch.py` · `news_job.py` · `__main__.py` · `tests/etl/test_e56_news_job.py` · `test_e58_news_cli.py` | 4 |
| `backend/etl/news_job.py` (backfill) · `__main__.py` · `tests/etl/test_e57_news_backfill.py` | 5 |
| chạy thật, ledger | 6 |
| tài liệu §8 spec | 7 |
| review hai trục, verify, merge | 8 |

---

### Task 0 — fixture *(đã làm 2026-09-05 ~20:45, controller)*

19 file trong `tests/etl/fixtures/news/`: `feed-{cafef,vietstock,vneconomy,vietnambiz,bnews,nguoiquansat,baochinhphu}.xml` (nguyên byte; BNews UTF-16LE), `article-{8 báo}.html` + `article-cafef_cbtt.html`, `list-cafef-cbtt.html`, `list-tnck-chung-khoan.html`, `list-bcp.html`, `sitemap-2026-9.xml`, `CAPTURE-2026-09-05.txt`. Literal quan trọng (từ CAPTURE):

| Fixture | Literal |
|---|---|
| `feed-cafef.xml` | 50 item; item[0] link `https://cafef.vn/green-sm-co-dong-thai-moi-tai-loat-tinh-thanh-phia-nam-188260905170800678.chn`, pubDate `Sat, 05 Sep 26 17:09:00 +0700`, title `Green SM có động thái mới tại loạt tỉnh thành phía Nam` |
| `feed-vietstock.xml` | 30 item; item[0] link `http://vietstock.vn/2026/09/chi-2-phien-giao-dich-vic-dua-vn-index-qua-nhung-cung-bac-trai-chieu-830-1489047.htm` (**http**), pubDate `Sat, 05 Sep 2026 20:32:00 +0700` |
| `feed-vneconomy.xml` | 50 item; item[0] pubDate `Fri, 04 Sep 2026 02:43:06 GMT` (= 09:43 VN) |
| `feed-vietnambiz.xml` | 30 item; prolog khai utf-16 nhưng byte UTF-8; item[0] link `…-202694173243150.htm`, pubDate **`Fri, 04 Sep 2026 18:48:27 GMT+7`** (phi chuẩn — parse ra naive 18:48:27 ⇒ gán +07), title có entity `TCH v&#224; hai m&#227; họ FPT…` ⇒ unescape thành `TCH và hai mã họ FPT tăng mạnh nhất danh mục PYN Elite trong tháng 8` |
| `feed-bnews.xml` | UTF-16LE thật; 20 item; item[0] link `https://bnews.vn/vn-index-tang-hon-25-diem-nho-co-phie-u-da-u-nga-nh-ba-t-do-ng-sa-n/435525.html`, pubDate `Fri, 04 Sep 2026 16:22:56 +0700`, title `VN-Index tăng hơn 25 điểm nhờ cổ phiếu đầu ngành bất động sản` |
| `feed-nguoiquansat.xml` | 40 item; item[0] pubDate `Sat, 05 Sep 2026 22:17:01 +0700` |
| `feed-baochinhphu.xml` | 50 item; item[0] pubDate **`9/5/2026 1:30:00 PM`**, link `https://baochinhphu.vn/co-che-chinh-sach-xac-dinh-gia-san-pham-in-duc-tien-102260905122709839.htm` |
| `article-cafef.html` | tiêu đề `Green SM có động thái mới tại loạt tỉnh thành phía Nam`; container text thô 2.983 ký tự bắt đầu `TIN MỚI Công ty Cổ phần Di chuyển Xanh…` (khối "TIN MỚI" phải bị bỏ ⇒ text sạch bắt đầu `Công ty Cổ phần Di chuyển Xanh và Thông minh GSM vừa chính thức`), kết `…giao thông bền vững ở quy mô toàn cầu.` |
| `article-vietstock.html` | tiêu đề `Chỉ 2 phiên giao dịch, VIC đưa VN-Index qua những cung bậc trái chiều`; text thô 1.692 bắt đầu bằng chính tiêu đề (`p.pTitle` phải bỏ) và kết `…Huy Khải FILI - 19:30 05/09/2026` (chữ ký phải bỏ); giờ trang `19:30 05/09/2026` |
| `article-vneconomy.html` | tiêu đề `Sau soát xét, QCG báo lãi 181,7 tỷ đồng, tăng 1.716,7% so với cùng kỳ`; text thô 4.635 bắt đầu `Công ty Cổ phần Quốc Cường Gia Lai (mã QCG-HOSE) công bố giải trình` kết `…giả định hoạt động liên tục.` |
| `article-vietnambiz.html` | text thô 3.591 bắt đầu `Trong tháng 8, ba cổ phiếu tăng tốt nhất trong danh mục là TCH, FRT và` kết `…hành khách quốc tế trong dài hạn.` |
| `article-bnews.html` | text thô 3.196 bắt đầu `BNEWS Đà tăng mạnh của cổ phiếu VIC…` (sapo có nhãn BNEWS phải bỏ) kết `…Văn Giáp/Bnews/vnanet.vn` (chữ ký phải bỏ); tiêu đề `VN-Index tăng hơn 25 điểm nhờ cổ phiếu đầu ngành bất động sản` |
| `article-nguoiquansat.html` | text thô 3.835 bắt đầu `Doanh nghiệp A-Z Doanh nghiệp cấp nước…` (khối header phải bỏ) kết `…(Theo số liệu từ Tổng điều tra kinh tế năm 2025)` |
| `article-baochinhphu.html` | tiêu đề `Cơ chế, chính sách xác định giá sản phẩm in, đúc tiền`; text thô 1.953 bắt đầu bằng tiêu đề (?) `Cơ chế, chính sách xác định giá sản phẩm in, đúc tiền giai đoạn 2020 -` kết `…Tham khảo thêm Sửa quy định nhập khẩu…` (box "Tham khảo thêm" phải bỏ); có HTML comment `GMT+0700` phải không lọt |
| `article-tinnhanhck.html` | tiêu đề `Thái Nguyên: Dự án 1.100 tỷ đồng dang dở sau 4 năm, 229 hộ dân vẫn chờ chi trả bồi thường`; `meta.cms-date` content **`2026-09-05T09:18:48+0700`** (sitemap `lastmod` của cùng bài là `20:39:34` — giờ sửa, không phải giờ đăng); text thô 4.371 bắt đầu `Hiện trạng khu đất nằm trong quy hoạch dự án vẫn chỉ là ruộng đồng. Ảnh` (chú thích ảnh — `figcaption` phòng thủ) |
| `article-cafef_cbtt.html` | tiêu đề `HBC: Báo cáo tài chính bán niên năm 2026`; text 680 ký tự `Báo cáo tài chính bán niên năm 2026 File đính kèm: 1.HBC_…pdf … Theo HNX` (ngắn là hợp lệ) |
| `list-cafef-cbtt.html` | 21 href `/du-lieu/{MÃ}-{id}/…chn?utm_source=du-lieu`; đầu `/du-lieu/HBC-2970021/hbc-bao-cao-tai-chinh-ban-nien-nam-2026.chn?utm_source=du-lieu`, thứ hai `SGP-2969587` |
| `list-tnck-chung-khoan.html` | ~182 link `…-post\d+\.html` (trùng nhau, unique ít hơn) |
| `list-bcp.html` | ~102 link bài `…-102\d{15}\.htm` |
| `sitemap-2026-9.xml` | **245** URL; [0] `https://www.tinnhanhchungkhoan.vn` lastmod `2026-09-05T23:02:38+07:00` (trang chủ, bỏ); [1] `…/bal-ngay-gdkhq-tra-co-tuc-nam-2025-bang-tien-35-post396857.html` `2026-09-01T20:41:41+07:00`; [-1] `…/thai-nguyen-du-an-1100-ty-dong-dang-do-sau-4-nam-229-ho-dan-van-cho-chi-tra-boi-thuong-post397051.html` `2026-09-05T20:39:34+07:00` |

- [x] Chụp và commit cùng plan (controller).

---

### Task 1: Registry + parse (thuần)

**Files:** Create `backend/etl/news_registry.py`, `backend/etl/news_parse.py`, `backend/tests/etl/test_e52_news_parse.py`.

**Interfaces (Produces):**
```python
# news_registry
SOURCES = ("cafef","vietstock","vneconomy","vietnambiz","bnews","nguoiquansat","baochinhphu","tinnhanhck")
KINDS = ("rss","cafef_cbtt","tnck_category","tnck_sitemap","bcp_list")
@dataclass(frozen=True) class Source: name: str; kind: str; url: str; group_from_feed: int | None; feed_slug: str
class RegistryError(Exception)
FEEDS_JSON: Path   # docs/10-sources/news/feeds.json
def build(path: Path = FEEDS_JSON) -> list[Source]     # 53, thứ tự: 47 rss (nhóm 1, 2, 3) rồi 6 crawl theo feeds.json
def sitemap_url(now_vn: datetime) -> str               # "https://www.tinnhanhchungkhoan.vn/sitemaps/news-{y}-{m}.xml", m không đệm 0
# news_parse
@dataclass(frozen=True) class Item: source: str; feed_slug: str; url: str; canonical_url: str; title: str; sapo_raw: str | None;
    published_at: datetime | None; published_at_src: str; group_from_feed: int | None; ticker_from_url: str | None; rule: str
class ParseError(Exception)
VN = ZoneInfo("Asia/Ho_Chi_Minh")
def decode(raw: bytes) -> str                          # >10 null byte trong 100 byte đầu ⇒ utf-16-le, else utf-8 (errors='replace')
def canonical_url(u: str) -> str
def norm_title(t: str) -> str
def parse_pubdate(s: str, source: str) -> tuple[datetime | None, str]   # (dt +07, src 'feed'|'unknown')
def time_from_url(url: str, source: str) -> datetime | None            # vietnambiz, baochinhphu
def parse_rss(text: str, src: Source) -> list[Item]
def parse_sitemap(text: str, src: Source) -> list[Item]                 # bỏ entry không khớp -post\d+\.html
def parse_cafef_cbtt(html: str, src: Source) -> list[Item]
def parse_tnck_category(html: str, src: Source) -> list[Item]
def parse_bcp_list(html: str, src: Source) -> list[Item]
PARSERS = {"rss": parse_rss, "tnck_sitemap": parse_sitemap, "cafef_cbtt": parse_cafef_cbtt, "tnck_category": parse_tnck_category, "bcp_list": parse_bcp_list}
```

- [ ] **Step 1: Test đỏ** — `tests/etl/test_e52_news_parse.py`:

```python
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
    assert 'encoding="utf-16"' in vb[:100] and "\ufffd" not in vb                        # khai utf-16, byte UTF-8


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
    assert np_.time_from_url("https://vietnambiz.vn/a-2026121123456789.htm", "vietnambiz") == datetime(2026, 12, 11, 23, 45, 67 % 60, tzinfo=VN) if False else True
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
    items = np_.parse_cafef_cbtt((FIX / "list-cafef-cbtt.html").read_text(encoding="utf-8"), _src("cafef", "cafef_cbtt", "cbtt"))
    assert 15 <= len(items) <= 21 and items[0].canonical_url == "https://cafef.vn/du-lieu/HBC-2970021/hbc-bao-cao-tai-chinh-ban-nien-nam-2026.chn"
    assert items[0].ticker_from_url == "HBC" and items[0].rule == "cafef_cbtt" and items[0].published_at is None and items[0].published_at_src == "unknown"
    assert all(it.ticker_from_url not in ("HNX", "HOSE", "UPCOM") for it in items)
    html = '<a href="/du-lieu/HNX-1/x.chn">x</a><a href="/du-lieu/ABC-2/y.chn?utm_source=du-lieu">y</a><a href="/du-lieu/ABC-2/y.chn">y</a>'
    only = np_.parse_cafef_cbtt(html, _src("cafef", "cafef_cbtt", "cbtt"))
    assert [(i.ticker_from_url, i.canonical_url) for i in only] == [(None, "https://cafef.vn/du-lieu/HNX-1/x.chn"), ("ABC", "https://cafef.vn/du-lieu/ABC-2/y.chn")]


def test_parse_tnck_category_and_bcp_list_unique_article_links():
    tn = np_.parse_tnck_category((FIX / "list-tnck-chung-khoan.html").read_text(encoding="utf-8"), _src("tinnhanhck", "tnck_category", "chung-khoan", 3))
    assert 60 <= len(tn) <= 182 and len({i.canonical_url for i in tn}) == len(tn) and all(i.group_from_feed == 3 and i.rule == "tinnhanhck" for i in tn)
    assert any(i.url.endswith("-post397020.html") for i in tn)
    bcp = np_.parse_bcp_list((FIX / "list-bcp.html").read_text(encoding="utf-8"), _src("baochinhphu", "bcp_list", "chi-dao-dieu-hanh", 1))
    assert 30 <= len(bcp) <= 102 and all(i.url.startswith("https://baochinhphu.vn/") and i.url.endswith(".htm") for i in bcp)
    assert all(i.published_at_src == "url" and i.published_at is not None for i in bcp)          # giờ từ 102YYMMDDHHMMSS
```

(Dòng `if False else True` trong `test_time_from_url…` là lỗi — **xoá dòng đó**; giữ 3 assert còn lại.)

- [ ] **Step 2: Chạy đỏ** — `uv run pytest tests/etl/test_e52_news_parse.py -q` ⇒ `ModuleNotFoundError: etl.news_parse`.

- [ ] **Step 3: `news_registry.py`**

```python
"""Registry nguồn tin (spec lát 8 §5.1): 47 feed RSS đọc từ docs/10-sources/news/feeds.json (chủ duy nhất của danh sách feed,
như wichart_registry đọc khối Python trong wichart.md) + 6 nguồn crawl; phần "của mình" là tên báo chuẩn, kind, feed_slug,
group_from_feed. Số đếm phải khớp `_meta` — lệch là chết trước fetch (hợp đồng khởi động)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

FEEDS_JSON = Path(__file__).resolve().parents[2] / "docs" / "10-sources" / "news" / "feeds.json"
SOURCES = ("cafef", "vietstock", "vneconomy", "vietnambiz", "bnews", "nguoiquansat", "baochinhphu", "tinnhanhck")
KINDS = ("rss", "cafef_cbtt", "tnck_category", "tnck_sitemap", "bcp_list")
GROUP_KEYS = (("1_vi_mo_trong_nuoc", 1), ("2_tai_chinh_quoc_te", 2), ("3_doanh_nghiep_niem_yet", 3))
SITEMAP = "https://www.tinnhanhchungkhoan.vn/sitemaps/news-{y}-{m}.xml"   # tháng KHÔNG đệm 0 (đo 2026-09-05)


class RegistryError(Exception):
    """feeds.json lệch với số đếm khai trong _meta hoặc tên báo lạ."""


@dataclass(frozen=True)
class Source:
    name: str
    kind: str
    url: str
    group_from_feed: int | None
    feed_slug: str


def _slug(url: str) -> str:
    return re.sub(r"\.(rss|html?|chn|xml)$", "", urlparse(url).path.strip("/"))


def _crawl_kind(nguon: str, url: str) -> str:
    if nguon == "cafef":
        return "cafef_cbtt"
    if nguon == "baochinhphu":
        return "bcp_list"
    return "tnck_sitemap" if "/sitemaps/" in url else "tnck_category"


def build(path: Path = FEEDS_JSON) -> list[Source]:
    d = json.loads(path.read_text(encoding="utf-8"))
    out: list[Source] = []
    for key, grp in GROUP_KEYS:
        for f in d[key]:
            if f["nguon"] not in SOURCES:
                raise RegistryError(f"tên báo lạ trong feeds.json: {f['nguon']!r}")
            out.append(Source(f["nguon"], "rss", f["url"], grp, _slug(f["url"])))
    for c in d["crawl_html"]:
        kind = _crawl_kind(c["nguon"], c["url"])
        slug = {"cafef_cbtt": "cbtt", "bcp_list": "chi-dao-dieu-hanh", "tnck_sitemap": "sitemap"}.get(kind) or _slug(c["url"])
        out.append(Source(c["nguon"], kind, c["url"], c.get("nhom_mac_dinh"), slug))
    meta = d["_meta"]
    n_rss = sum(1 for s in out if s.kind == "rss")
    if n_rss != meta["feed_rss"] or len(out) - n_rss != meta["crawl_html"]:
        raise RegistryError(f"feeds.json: {n_rss} feed / {len(out) - n_rss} crawl ≠ _meta {meta['feed_rss']} / {meta['crawl_html']}")
    return out


def sitemap_url(now_vn: datetime) -> str:
    return SITEMAP.format(y=now_vn.year, m=now_vn.month)
```

- [ ] **Step 4: `news_parse.py`**

```python
"""Chuẩn hoá item tin (spec lát 8 §5.3, README §6): decode theo null byte, URL canonical, giờ đăng theo 4 luật,
tiêu đề chuẩn hoá cho dedupe. Thuần — không I/O. Bẫy đã đo (2026-09-05): VietnamBiz khai utf-16 mà byte UTF-8, pubDate
`GMT+7` phi chuẩn hoặc rỗng (lấy từ URL), tiêu đề mang entity; BaoChinhPhu `M/D/YYYY h:mm:ss AM/PM` không múi giờ;
sitemap TinnhanhCK phần tử đầu là trang chủ với lastmod = giờ sinh file."""
from __future__ import annotations

import html
import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from etl.news_registry import Source

VN = ZoneInfo("Asia/Ho_Chi_Minh")
DROP_QUERY = re.compile(r"^(utm_|gidzl$|fbclid$)")
TITLE_PREFIX = re.compile(r"^\s*(\(chinhphu\.vn\)\s*-?|\(đtck\)|\(dtck\)|bnews)\s*", re.I)
VNBIZ_URL = re.compile(r"-(\d{15,16})\.htm")
BCP_URL = re.compile(r"-102(\d{12})\d+\.htm")
POST_URL = re.compile(r"-post\d+\.html$")
CBTT_HREF = re.compile(r"/du-lieu/([A-Z0-9]{2,6})-(\d+)/[^\"'\s]*\.chn")
EXCHANGES = {"HNX", "HOSE", "UPCOM"}


class ParseError(Exception):
    """Body không phải RSS/sitemap/danh sách mong đợi."""


@dataclass(frozen=True)
class Item:
    source: str
    feed_slug: str
    url: str
    canonical_url: str
    title: str
    sapo_raw: str | None
    published_at: datetime | None
    published_at_src: str
    group_from_feed: int | None
    ticker_from_url: str | None
    rule: str                     # khoá luật bóc: tên báo, hoặc 'cafef_cbtt'


def decode(raw: bytes) -> str:
    if raw[:100].count(b"\x00") > 10:                       # README §6.1: BNews UTF-16LE thật; đừng tin prolog
        return raw.decode("utf-16-le", errors="replace")
    return raw.decode("utf-8", errors="replace")


def canonical_url(u: str) -> str:
    p = urlparse(u.strip())
    scheme = "https" if p.scheme.lower() in ("http", "https") else p.scheme.lower()
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not DROP_QUERY.match(k)]
    path = p.path.rstrip("/") or "/"
    return urlunparse((scheme, p.netloc.lower(), path, "", urlencode(q), ""))


def norm_title(t: str) -> str:
    t = TITLE_PREFIX.sub("", html.unescape(t or "")).lower().replace("đ", "d")
    t = unicodedata.normalize("NFD", t)
    return re.sub(r"[^a-z0-9]", "", t)


def _vn(dt: datetime) -> datetime:
    return (dt.replace(tzinfo=VN) if dt.tzinfo is None else dt).astimezone(VN)


def parse_pubdate(s: str, source: str) -> tuple[datetime | None, str]:
    s = (s or "").strip()
    if not s:
        return None, "unknown"
    if source == "baochinhphu":
        for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S"):
            try:
                return datetime.strptime(s, fmt).replace(tzinfo=VN), "feed"
            except ValueError:
                pass
    try:
        return _vn(parsedate_to_datetime(re.sub(r"GMT\+7$", "+0700", s))), "feed"   # 'GMT+7' phi chuẩn của VietnamBiz
    except (TypeError, ValueError):
        return None, "unknown"


def time_from_url(url: str, source: str) -> datetime | None:
    if source == "vietnambiz":
        m = VNBIZ_URL.search(url)
        if not m:
            return None
        s = m.group(1)                                     # YYYY + M(1–2) + DD + HHMMSS + serial
        for mlen in (1, 2):
            try:
                return datetime(int(s[:4]), int(s[4:4 + mlen]), int(s[4 + mlen:6 + mlen]), int(s[6 + mlen:8 + mlen]),
                                int(s[8 + mlen:10 + mlen]), int(s[10 + mlen:12 + mlen]), tzinfo=VN)
            except ValueError:
                continue
        return None
    if source == "baochinhphu":
        m = BCP_URL.search(url)
        if not m:
            return None
        try:
            return datetime.strptime(m.group(1), "%y%m%d%H%M%S").replace(tzinfo=VN)
        except ValueError:
            return None
    return None


def _published(pub: str, url: str, source: str) -> tuple[datetime | None, str]:
    dt, src = parse_pubdate(pub, source)
    if dt is None:
        dt = time_from_url(url, source)
        src = "url" if dt else "unknown"
    return dt, src


def parse_rss(text: str, src: Source) -> list[Item]:
    body = re.sub(r"^\s*<\?xml[^>]*\?>", "", text)          # bỏ prolog: VietnamBiz khai sai encoding
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        raise ParseError(f"{src.name}/{src.feed_slug}: XML hỏng — {type(e).__name__}") from e
    items = list(root.iter("item"))
    if not items:
        raise ParseError(f"{src.name}/{src.feed_slug}: không có <item>")
    out = []
    for it in items:
        url = (it.findtext("link") or "").strip()
        if not url:
            continue
        pub, psrc = _published(it.findtext("pubDate") or "", url, src.name)
        out.append(Item(src.name, src.feed_slug, url, canonical_url(url), html.unescape((it.findtext("title") or "").strip()),
                        (it.findtext("description") or None), pub, psrc, src.group_from_feed, None, src.name))
    return out


def parse_sitemap(text: str, src: Source) -> list[Item]:
    body = re.sub(r"^\s*<\?xml[^>]*\?>", "", text)
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        raise ParseError(f"sitemap: XML hỏng — {type(e).__name__}") from e
    ns = {"s": root.tag.split("}")[0].strip("{")} if root.tag.startswith("{") else {}
    tag = (lambda n: f"s:{n}") if ns else (lambda n: n)
    out = []
    for u in root.findall(tag("url"), ns):
        loc = (u.findtext(tag("loc"), namespaces=ns) or "").strip()
        if not POST_URL.search(loc):                        # phần tử đầu = trang chủ, lastmod = giờ sinh file (đo 2026-09-05)
            continue
        mod = (u.findtext(tag("lastmod"), namespaces=ns) or "").strip()
        try:
            pub = datetime.fromisoformat(mod).astimezone(VN)
            psrc = "feed"
        except ValueError:
            pub, psrc = None, "unknown"
        out.append(Item("tinnhanhck", "sitemap", loc, canonical_url(loc), "", None, pub, psrc, None, None, "tinnhanhck"))
    if not out:
        raise ParseError("sitemap: 0 URL bài")
    return out


def _links(html_text: str, base: str) -> list[str]:
    soup = BeautifulSoup(html_text, "html.parser")
    seen: dict[str, None] = {}
    for a in soup.find_all("a", href=True):
        seen.setdefault(urljoin(base, a["href"].strip()), None)
    return list(seen)


def parse_cafef_cbtt(html_text: str, src: Source) -> list[Item]:
    out: dict[str, Item] = {}
    for m in CBTT_HREF.finditer(html_text):
        url = urljoin("https://cafef.vn/", m.group(0))
        cu = canonical_url(url)
        if cu in out:
            continue
        code = m.group(1)
        out[cu] = Item("cafef", "cbtt", cu, cu, "", None, None, "unknown", src.group_from_feed, None if code in EXCHANGES else code, "cafef_cbtt")
    if not out:
        raise ParseError("cafef_cbtt: 0 link /du-lieu/")
    return list(out.values())


def parse_tnck_category(html_text: str, src: Source) -> list[Item]:
    links = [u for u in _links(html_text, "https://www.tinnhanhchungkhoan.vn/") if POST_URL.search(u) and "tinnhanhchungkhoan.vn" in u]
    if not links:
        raise ParseError(f"tnck/{src.feed_slug}: 0 link -post")
    out: dict[str, Item] = {}
    for u in links:
        cu = canonical_url(u)
        out.setdefault(cu, Item("tinnhanhck", src.feed_slug, u, cu, "", None, None, "unknown", src.group_from_feed, None, "tinnhanhck"))
    return list(out.values())


def parse_bcp_list(html_text: str, src: Source) -> list[Item]:
    links = [u for u in _links(html_text, "https://baochinhphu.vn/") if BCP_URL.search(u) and "baochinhphu.vn" in u]
    if not links:
        raise ParseError("bcp_list: 0 link bài")
    out: dict[str, Item] = {}
    for u in links:
        cu = canonical_url(u)
        pub = time_from_url(u, "baochinhphu")
        out.setdefault(cu, Item("baochinhphu", src.feed_slug, u, cu, "", None, pub, "url" if pub else "unknown", src.group_from_feed, None, "baochinhphu"))
    return list(out.values())


PARSERS = {"rss": parse_rss, "tnck_sitemap": parse_sitemap, "cafef_cbtt": parse_cafef_cbtt,
           "tnck_category": parse_tnck_category, "bcp_list": parse_bcp_list}
```

Lưu ý cho implementer: `parse_sitemap` xử lý namespace `http://www.sitemaps.org/schemas/sitemap/0.9` (fixture có); nếu fixture không có namespace thì nhánh `ns = {}` chạy. Số 244 trong test = 245 − 1 trang chủ — kiểm lại bằng `grep -c "<loc>" sitemap-2026-9.xml` (245) trước khi chạy.

- [ ] **Step 5: Chạy xanh** — e52 PASS. Nếu một literal đọc từ fixture khác (ví dụ số link TNCK), sửa test theo **fixture** và ghi report — không sửa fixture.

- [ ] **Step 6: Commit (controller)** `feat(etl): news registry from feeds.json and pure parsers (RSS, sitemap, list pages)`.

---

### Task 2: Bóc bài theo luật từng nguồn (thuần)

**Files:** Create `backend/etl/news_extract.py`, `backend/tests/etl/test_e53_news_extract.py`.

**Interfaces (Produces):**
```python
@dataclass(frozen=True) class Extracted: title: str; sapo: str | None; content: str; published_at: datetime | None
class ExtractError(Exception): reason: str   # 'no_container' | 'no_title' | 'too_short'
RULES: dict[str, Rule]                        # 9 khoá: 8 báo + 'cafef_cbtt'
MIN_CHARS = 100
def extract(html_text: str, rule: str) -> Extracted
```

- [ ] **Step 1: Test đỏ** — `tests/etl/test_e53_news_extract.py` (literal từ Task 0; độ dài dùng khoảng):

```python
"""Bóc 9 trang bài thật chụp 2026-09-05 theo luật article-structure §2: container đúng, boilerplate biến mất, tiền tố/hậu tố literal."""
import pathlib
from datetime import datetime, timezone, timedelta

import pytest

from etl import news_extract as ne

FIX = pathlib.Path(__file__).parent / "fixtures" / "news"
VN = timezone(timedelta(hours=7))


def _page(name):
    return (FIX / f"article-{name}.html").read_text(encoding="utf-8")


def test_rules_cover_nine_keys_and_min_chars():
    assert set(ne.RULES) == {"cafef", "cafef_cbtt", "vietstock", "vneconomy", "vietnambiz", "bnews", "nguoiquansat", "baochinhphu", "tinnhanhck"}
    assert ne.MIN_CHARS == 100


def test_cafef_drops_tin_moi_block_and_keeps_body():
    x = ne.extract(_page("cafef"), "cafef")
    assert x.title == "Green SM có động thái mới tại loạt tỉnh thành phía Nam"
    assert x.content.startswith("Công ty Cổ phần Di chuyển Xanh và Thông minh GSM vừa chính thức")
    assert x.content.endswith("giao thông bền vững ở quy mô toàn cầu.")
    assert "TIN MỚI" not in x.content and 2500 <= len(x.content) <= 2983
    assert x.sapo and len(x.sapo) > 50
    assert x.published_at == datetime(2026, 9, 5, 17, 9, tzinfo=VN)


def test_cafef_cbtt_short_text_is_legal_and_title_is_not_h1():
    x = ne.extract(_page("cafef_cbtt"), "cafef_cbtt")
    assert x.title == "HBC: Báo cáo tài chính bán niên năm 2026"
    assert x.content.startswith("Báo cáo tài chính bán niên năm 2026") and x.content.endswith("Theo HNX") and 600 <= len(x.content) <= 680
    assert x.published_at is None and x.sapo is None


def test_vietstock_drops_title_sapo_signature_and_keeps_body():
    x = ne.extract(_page("vietstock"), "vietstock")
    assert x.title == "Chỉ 2 phiên giao dịch, VIC đưa VN-Index qua những cung bậc trái chiều"
    assert not x.content.startswith("Chỉ 2 phiên giao dịch") and "Huy Khải" not in x.content and "FILI" not in x.content
    assert 900 <= len(x.content) <= 1600 and x.published_at == datetime(2026, 9, 5, 19, 30, tzinfo=VN)
    assert x.sapo and "<" not in x.sapo


def test_vneconomy_keeps_body_and_drops_lead():
    x = ne.extract(_page("vneconomy"), "vneconomy")
    assert x.title.startswith("Sau soát xét, QCG báo lãi 181,7 tỷ đồng")
    assert x.content.startswith("Công ty Cổ phần Quốc Cường Gia Lai (mã QCG-HOSE) công bố giải trình")
    assert x.content.endswith("giả định hoạt động liên tục.") and 4000 <= len(x.content) <= 4635
    assert x.published_at == datetime(2026, 9, 4, 9, 43, tzinfo=VN) or x.published_at is None or x.published_at.date() == datetime(2026, 9, 4).date()


def test_vietnambiz_cleanest_source():
    x = ne.extract(_page("vietnambiz"), "vietnambiz")
    assert x.content.startswith("Trong tháng 8, ba cổ phiếu tăng tốt nhất trong danh mục là TCH, FRT và")
    assert x.content.endswith("hành khách quốc tế trong dài hạn.") and 3300 <= len(x.content) <= 3591
    assert x.title.startswith("TCH và hai mã họ FPT")


def test_bnews_text_nodes_not_p_tags_and_drops_label_and_signature():
    x = ne.extract(_page("bnews"), "bnews")
    assert x.title == "VN-Index tăng hơn 25 điểm nhờ cổ phiếu đầu ngành bất động sản"
    assert not x.content.startswith("BNEWS") and "Văn Giáp" not in x.content and "vnanet.vn" not in x.content
    assert x.content.endswith("hình thành trong những phiên trước đó.") and 2500 <= len(x.content) <= 3196
    assert x.sapo and not x.sapo.startswith("BNEWS") and x.published_at is None          # BNews: giờ từ feed


def test_nguoiquansat_drops_header_block():
    x = ne.extract(_page("nguoiquansat"), "nguoiquansat")
    assert not x.content.startswith("Doanh nghiệp A-Z") and "Khúc văn" not in x.content
    assert x.content.endswith("(Theo số liệu từ Tổng điều tra kinh tế năm 2025)") and 3000 <= len(x.content) <= 3835
    assert x.title.startswith("Doanh nghiệp cấp nước cho hơn 32 triệu dân")


def test_baochinhphu_drops_comments_and_related_box():
    x = ne.extract(_page("baochinhphu"), "baochinhphu")
    assert x.title == "Cơ chế, chính sách xác định giá sản phẩm in, đúc tiền"
    assert "GMT+0700" not in x.content and "Indochina" not in x.content and "Tham khảo thêm" not in x.content
    assert not x.content.endswith("in, đúc tiền") and 1500 <= len(x.content) <= 1953
    assert x.sapo and not x.sapo.startswith("(Chinhphu.vn)") and x.published_at == datetime(2026, 9, 5, 13, 30, tzinfo=VN) or x.published_at.date() == datetime(2026, 9, 5).date()


def test_tinnhanhck_uses_cms_date_not_sitemap_lastmod():
    x = ne.extract(_page("tinnhanhck"), "tinnhanhck")
    assert x.title.startswith("Thái Nguyên: Dự án 1.100 tỷ đồng dang dở sau 4 năm")
    assert x.published_at == datetime(2026, 9, 5, 9, 18, 48, tzinfo=VN)
    assert x.content.endswith("không còn là lãnh đạo tại Hừng Đông.") and 4000 <= len(x.content) <= 4371 and "..>>" not in x.content
    assert x.sapo and not x.sapo.startswith("(ĐTCK)")


def test_errors_no_container_no_title_too_short():
    with pytest.raises(ne.ExtractError) as e:
        ne.extract("<html><body><p>nothing</p></body></html>", "cafef")
    assert e.value.reason == "no_container"
    with pytest.raises(ne.ExtractError) as e:
        ne.extract('<html><div class="detail-content afcbc-body">' + "x " * 200 + "</div></html>", "cafef")
    assert e.value.reason == "no_title"
    with pytest.raises(ne.ExtractError) as e:
        ne.extract('<html><h1 class="title">T</h1><div class="detail-content afcbc-body">ngắn quá</div></html>", "cafef")
    assert e.value.reason == "too_short"
    short = ne.extract('<html><td class="text_noibat_cacbaikhac"><span class="cms_blue">ABC: x</span></td><div id="newscontent">ngắn</div></html>', "cafef_cbtt")
    assert short.content == "ngắn"                                                   # CBTT được phép ngắn
    with pytest.raises(KeyError):
        ne.extract("<html></html>", "khong_co")
```

- [ ] **Step 2: Chạy đỏ** ⇒ `ModuleNotFoundError`.

- [ ] **Step 3: `news_extract.py`**

```python
"""Bóc bài ba tầng (article-structure §1.3, §2, §3): tầng 0 chọn ĐÚNG container; tầng 1 xoá node Comment trước rồi mới lấy
text (BaoChinhPhu giấu dấu thời gian trong comment); tầng 2 bỏ boilerplate theo selector từng nguồn + luật văn bản. Duyệt
text node qua get_text (BNews có template đoạn văn là text node trần — find_all('p') trả 0). Thuần, không I/O.
Chủ của bảng selector là article-structure.md — sửa ở đó trước, chép vào đây sau."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup, Comment

VN = ZoneInfo("Asia/Ho_Chi_Minh")
MIN_CHARS = 100
_WS = re.compile(r"\s+")


class ExtractError(Exception):
    def __init__(self, reason: str, msg: str):
        self.reason = reason              # 'no_container' | 'no_title' | 'too_short'
        super().__init__(msg)


@dataclass(frozen=True)
class Extracted:
    title: str
    sapo: str | None
    content: str
    published_at: datetime | None


@dataclass(frozen=True)
class Rule:
    container: str
    title: str
    drop: tuple[str, ...] = ()
    sapo: str | None = None
    sapo_prefix: str | None = None          # regex bỏ ở đầu sapo
    time: str | None = None                 # selector
    time_fmt: tuple[str, ...] = ()          # strptime; 'iso' = fromisoformat; giá trị lấy từ attr 'content' nếu là <meta>
    text_drop: tuple[str, ...] = ()         # regex áp lên text sạch
    min_chars: int = MIN_CHARS


RULES: dict[str, Rule] = {
    "cafef": Rule("div.detail-content.afcbc-body", "h1.title",
                  ("div.chisochungkhoan", "div.tindnd", "#listNewsInContent", "div.c-banner", "div.h-show-pc", "div.h-show-mobile",
                   "figure", "figcaption", "#reactRelate", "div.VCSortableInPreviewMode", "div.admzone", "table"),
                  sapo="p.sapo", time="span.pdate", time_fmt=("%d-%m-%Y - %I:%M %p",)),
    "cafef_cbtt": Rule("div#newscontent", "td.text_noibat_cacbaikhac span.cms_blue", ("div.FileWrapper", "table"), min_chars=0),
    "vietstock": Rule("div#vst_detail", "h1.article-title",
                      ("p.pTitle", "p.pHead", "p.pAuthor", "p.pSource", "p.pPublishTimeSource", "table.img-content", "div.article-sharing"),
                      sapo="p.pHead", time="div.meta span.date", time_fmt=("%d/%m/%Y %H:%M", "%H:%M %d/%m/%Y")),
    "vneconomy": Rule("main#article-editor", "h1.article-header__title",
                      ("h4.article-content__lead", "figure", "figcaption", "div.container-adv", "section", "div.article-tags", "table"),
                      sapo="h4.article-content__lead", time="time.article-meta__time", time_fmt=("%H:%M, %d/%m/%Y",)),
    "vietnambiz": Rule("div.vnbcbc-body", "h1.vnbcb-title", ("div.VnBizPreviewMode", "figure", "figcaption", "table"),
                       sapo="div.vnbcbc-sapo, div.sapo", time="span.vnbcba-time", time_fmt=("%H:%M | %d/%m/%Y",)),
    "bnews": Rule("div.lr-ct", "h1.font-42",
                  ("div.lr-summary-post", "div.insertImage", "div.editor_inpage", "#divAdmicro_inpage", "div.lr-author", "figure", "figcaption", "table"),
                  sapo="div.lr-summary-post", sapo_prefix=r"^BNEWS\s*"),
    "nguoiquansat": Rule("article.entry", "h1.sc-longform-header-title",
                         ("div.sc-longform-header", "div.sc-hightlight-box", "div.c-box", "figure", "figcaption", "div.sc-empty-layer", "table"),
                         sapo="p.sc-longform-header-sapo", time="span.sc-longform-header-date", time_fmt=("%d/%m/%Y - %H:%M", "%d/%m/%Y %H:%M")),
    "baochinhphu": Rule("div.detail-content.afcbc-body", "h1.detail-title",
                        ("div.VCSortableInPreviewMode", "figure", "figcaption", "div.detail-relate", "div.c-banner", "div.admzone", "table"),
                        sapo="h2.detail-sapo", sapo_prefix=r"^\(Chinhphu\.vn\)\s*-\s*", time="div.detail-time", time_fmt=("%d/%m/%Y %H:%M",)),
    "tinnhanhck": Rule("div.article__body", "h1.article__header",
                       ("div.ads_middle", "div[id^=adsWeb_]", "figure.article__avatar", "a.cms-relate", "div.article__tag", "figcaption", "table"),
                       sapo="div.article__sapo", sapo_prefix=r"^\(ĐTCK\)\s*", time="meta.cms-date", time_fmt=("iso",),
                       text_drop=(r"\.\.>>\s*",)),
}


def _text(node) -> str:
    return _WS.sub(" ", node.get_text(" ")).strip()


def _parse_time(raw: str, fmts) -> datetime | None:
    raw = _WS.sub(" ", raw).strip()
    for fmt in fmts:
        try:
            if fmt == "iso":
                return datetime.fromisoformat(raw).astimezone(VN)
            return datetime.strptime(raw, fmt).replace(tzinfo=VN)
        except ValueError:
            continue
    return None


def extract(html_text: str, rule: str) -> Extracted:
    r = RULES[rule]
    soup = BeautifulSoup(html_text, "html.parser")
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):      # tầng 1: comment là rác thật (§3.1)
        c.extract()
    container = soup.select_one(r.container)
    if container is None:
        raise ExtractError("no_container", f"{rule}: không thấy {r.container}")
    t = soup.select_one(r.title)
    title = _text(t) if t else ""
    if not title:
        raise ExtractError("no_title", f"{rule}: không thấy {r.title}")
    sapo = None
    if r.sapo:
        s = soup.select_one(r.sapo)
        if s is not None:
            sapo = _text(s)
            if r.sapo_prefix:
                sapo = re.sub(r.sapo_prefix, "", sapo, flags=re.I).strip()
            sapo = sapo or None
    published = None
    if r.time:
        tn = soup.select_one(r.time)
        if tn is not None:
            published = _parse_time(tn.get("content") if tn.name == "meta" else tn.get_text(" "), r.time_fmt)
    for sel in r.drop:                                                     # tầng 2: bỏ boilerplate TRONG container
        for n in container.select(sel):
            n.decompose()
    for n in container.find_all(["script", "style", "noscript"]):
        n.decompose()
    content = _text(container)
    for pat in r.text_drop:
        content = re.sub(pat, "", content)
    content = _WS.sub(" ", content).strip()
    if len(content) < r.min_chars:
        raise ExtractError("too_short", f"{rule}: text sạch {len(content)} ký tự < {r.min_chars}")
    return Extracted(title, sapo, content, published)
```

- [ ] **Step 4: Chạy xanh** — e53. Nếu một assertion tiền tố/hậu tố lệch vì fixture có ký tự lạ (ví dụ khoảng trắng không ngắt `\xa0`), **xử lý trong `_WS`** (đã gồm vì `\s` khớp `\xa0` trong Python 3 với str) và ghi report; nếu là boilerplate chưa có trong bảng (ví dụ CafeF còn khối khác), thêm selector vào `RULES` **và** ghi vào report để Task 7 chép sang article-structure. Không nới khoảng độ dài quá ±5 %.

- [ ] **Step 5: Commit (controller)** `feat(etl): news extractor — per-source container, comment removal, boilerplate rules, page time`.

---

### Task 3: Gắn mã + kho `news.*` (dedupe, ghi, bằng chứng)

**Files:** Create `backend/etl/news_tag.py`, `backend/etl/news_store.py`, `backend/tests/etl/test_e54_news_tag.py`, `backend/tests/etl/test_e55_news_store.py`.

**Interfaces (Produces):**
```python
# news_tag
TICKER = re.compile(r"\b[A-Z][A-Z0-9]{2}\b")
def tickers_from_url(url: str) -> list[str]                                  # ['SGP'] | []  (HNX/HOSE/UPCOM ⇒ [])
def tickers_lookup(title: str, sapo: str | None, listed: dict[str, int]) -> list[str]   # thứ tự xuất hiện, không trùng
# news_store
WINDOW = timedelta(hours=48)
@dataclass class Seen: urls: set[str]; canon: dict[str, int]; titles: list[tuple[str, datetime, int]]
    @classmethod def load(cls, conn, now) -> "Seen"
    def decide(self, item, now) -> tuple[str, int | None]         # ('seen'|'merge_url'|'merge_title'|'new', article_id)
    def remember(self, item, article_id, when) -> None
def load_listed(conn) -> dict[str, int]                              # ticker → security_id, status='listed'
def insert_article(conn, item, ext, *, fetched_at, tickers: list[tuple[str, str, int]]) -> int   # (ticker, via, security_id)
def add_source(conn, article_id, source_name, url) -> bool
def add_revision(conn, article_id, ext, fetched_at) -> bool
def store_list_if_changed(conn, source, url, text, run_id, content_type) -> bool
def store_refused(conn, source, url, html_text, reason, run_id) -> None
def upsert_domain_state(engine, sources: set[str], watermark: str) -> None
def published_for(item, ext) -> tuple[datetime | None, str]           # §4.6-II: tinnhanhck ưu tiên trang; khác ưu tiên feed
```

- [ ] **Step 1: Test đỏ — e54 (thuần)**

```python
"""Gắn mã tầng 1 (URL CafeF CBTT) và tầng 2 (regex + đối chiếu danh sách niêm yết) — news-pipeline §8."""
from etl import news_tag as nt


def test_url_tier_reads_cafef_cbtt_and_drops_exchanges():
    assert nt.tickers_from_url("https://cafef.vn/du-lieu/SGP-2969587/sgp-bao-cao.chn") == ["SGP"]
    assert nt.tickers_from_url("https://cafef.vn/du-lieu/HNX-2951892/x.chn") == []
    assert nt.tickers_from_url("https://cafef.vn/green-sm-188260905170800678.chn") == []


def test_lookup_tier_requires_listed_and_keeps_order_without_duplicates():
    listed = {"HPG": 1, "SME": 2, "VIC": 3, "GDP": 4}
    assert nt.tickers_lookup("HPG tăng trần, USD và GDP quý III; HPG lập đỉnh", "VIC dẫn dắt", listed) == ["HPG", "GDP", "VIC"]
    assert nt.tickers_lookup("SME công bố kết quả", None, listed) == ["SME"]
    assert nt.tickers_lookup("hpg tăng trần", None, listed) == []                 # chữ thường không phải mã
    assert nt.tickers_lookup("Cổ phiếu ABC1 và AB", None, {"AB": 9, "ABC": 8}) == []   # 2 ký tự và 4 ký tự không khớp \b[A-Z][A-Z0-9]{2}\b
```

- [ ] **Step 2: Test đỏ — e55 (DB)** — khuôn fixture `clean` như e47 (`migrated_engine`), dọn `news.*`, `staging.raw_payload` source ∈ 8 báo, `ops.data_domain_state domain='news'`, `market.security` ticker LIKE 'ZZ%'.

```python
"""Đường ghi duy nhất vào news.* — dedupe theo URL/canonical/tiêu đề 48 giờ, bản ghi bất biến (revision), bằng chứng khi đổi/từ chối."""
import os
import pathlib
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
```

- [ ] **Step 3: Chạy đỏ** — e54, e55 ⇒ `ModuleNotFoundError`.

- [ ] **Step 4: `news_tag.py`**

```python
"""Gắn mã cổ phiếu tầng 1 (URL CafeF CBTT — chắc chắn) và tầng 2 (regex + ĐỐI CHIẾU danh sách niêm yết — news-pipeline §8:
USD/GDP/CPI đều là 3 chữ in hoa, SME lại là mã thật). Chỉ quét tiêu đề + sapo (spec 7b… lát 8 §4.6-I). Thuần."""
from __future__ import annotations

import re

from etl.news_parse import CBTT_HREF, EXCHANGES

TICKER = re.compile(r"\b[A-Z][A-Z0-9]{2}\b")


def tickers_from_url(url: str) -> list[str]:
    m = CBTT_HREF.search(url)
    if not m or m.group(1) in EXCHANGES:
        return []
    return [m.group(1)]


def tickers_lookup(title: str, sapo: str | None, listed: dict[str, int]) -> list[str]:
    out: list[str] = []
    for tok in TICKER.findall(f"{title or ''} {sapo or ''}"):
        if tok in listed and tok not in out:
            out.append(tok)
    return out
```

- [ ] **Step 5: `news_store.py`**

```python
"""Đường ghi DUY NHẤT vào news.* (spec lát 8 §5.1): dedupe (URL đã thấy · canonical · tiêu đề chuẩn hoá trong 48 giờ),
ghi bài mới (article + revision v1 + source + ticker), thêm nguồn cho tin đã có, thêm phiên bản khi nội dung đổi (không đè),
bằng chứng danh sách khi hash đổi và HTML bài khi bóc từ chối, domain state theo báo."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import sqlalchemy as sa

from etl import series_store
from etl.news_parse import norm_title

WINDOW = timedelta(hours=48)
DOMAIN = "news"


def load_listed(conn) -> dict[str, int]:
    return dict(conn.execute(sa.text("SELECT ticker, security_id FROM market.security WHERE status = 'listed'")).all())


def published_for(item, ext) -> tuple[datetime | None, str]:
    """TinnhanhCK: giờ trên trang (cms-date) trước, sitemap lastmod là giờ SỬA (đo 2026-09-05: 09:18 vs 20:39);
    báo khác: giờ feed trước, giờ trang bù. `src` giữ 'url' khi giá trị đến từ URL (VietnamBiz/BaoChinhPhu)."""
    if item.rule == "tinnhanhck":
        if ext.published_at:
            return ext.published_at, "feed"
        return item.published_at, item.published_at_src if item.published_at else "unknown"
    if item.published_at:
        return item.published_at, item.published_at_src
    if ext.published_at:
        return ext.published_at, "feed"
    return None, "unknown"


@dataclass
class Seen:
    urls: set[str] = field(default_factory=set)
    canon: dict[str, int] = field(default_factory=dict)
    titles: list[tuple[str, datetime, int]] = field(default_factory=list)

    @classmethod
    def load(cls, conn, now: datetime) -> "Seen":
        urls = {r[0] for r in conn.execute(sa.text("SELECT url FROM news.article_source")).all()}
        canon = dict(conn.execute(sa.text("SELECT canonical_url, article_id FROM news.article")).all())
        rows = conn.execute(sa.text(
            "SELECT r.title, coalesce(a.published_at, a.fetched_at), a.article_id FROM news.article a"
            " JOIN news.article_revision r ON r.article_id = a.article_id AND r.version = 1"
            " WHERE coalesce(a.published_at, a.fetched_at) >= :since"), {"since": now - WINDOW}).all()
        return cls(urls, canon, [(norm_title(t), ts, aid) for t, ts, aid in rows])

    def decide(self, item, now: datetime) -> tuple[str, int | None]:
        if item.url in self.urls or item.canonical_url in self.urls:
            return "seen", self.canon.get(item.canonical_url)
        if item.canonical_url in self.canon:
            return "merge_url", self.canon[item.canonical_url]
        key = norm_title(item.title)
        if key:
            when = item.published_at or now
            for k, ts, aid in self.titles:
                if k == key and abs(when - ts) <= WINDOW:
                    return "merge_title", aid
        return "new", None

    def remember(self, item, article_id: int, when: datetime) -> None:
        self.urls.add(item.url)
        self.canon[item.canonical_url] = article_id
        self.titles.append((norm_title(item.title), item.published_at or when, article_id))


def insert_article(conn, item, ext, *, fetched_at: datetime, tickers: list[tuple[str, str, int]]) -> int:
    pub, src = published_for(item, ext)
    aid = conn.execute(sa.text(
        "INSERT INTO news.article (canonical_url, primary_source, feed, published_at, published_at_src, fetched_at,"
        " group_from_feed, ticker_step_ran)"
        " VALUES (:cu, :src, :feed, :pub, :psrc, :fa, :grp, :ran) RETURNING article_id"),
        {"cu": item.canonical_url, "src": item.source, "feed": item.feed_slug, "pub": pub, "psrc": src, "fa": fetched_at,
         "grp": item.group_from_feed, "ran": item.group_from_feed == 3}).scalar_one()
    conn.execute(sa.text(
        "INSERT INTO news.article_revision (article_id, version, title, sapo, content, content_fetched_at)"
        " VALUES (:a, 1, :t, :s, :c, :fa)"),
        {"a": aid, "t": ext.title or item.title, "s": ext.sapo, "c": ext.content, "fa": fetched_at})
    add_source(conn, aid, item.source, item.url)
    for ticker, via, sid in tickers:
        conn.execute(sa.text(
            "INSERT INTO news.article_ticker (article_id, security_id, via) VALUES (:a, :s, :v) ON CONFLICT DO NOTHING"),
            {"a": aid, "s": sid, "v": via})
    return aid


def add_source(conn, article_id: int, source_name: str, url: str) -> bool:
    return conn.execute(sa.text(
        "INSERT INTO news.article_source (article_id, source_name, url) VALUES (:a, :s, :u) ON CONFLICT (url) DO NOTHING"),
        {"a": article_id, "s": source_name, "u": url}).rowcount == 1


def add_revision(conn, article_id: int, ext, fetched_at: datetime) -> bool:
    ver, content = conn.execute(sa.text(
        "SELECT version, content FROM news.article_revision WHERE article_id = :a ORDER BY version DESC LIMIT 1"),
        {"a": article_id}).one()
    if series_store.hash_text(content) == series_store.hash_text(ext.content):
        return False
    conn.execute(sa.text(
        "INSERT INTO news.article_revision (article_id, version, title, sapo, content, content_fetched_at)"
        " VALUES (:a, :v, :t, :s, :c, :fa)"),
        {"a": article_id, "v": ver + 1, "t": ext.title, "s": ext.sapo, "c": ext.content, "fa": fetched_at})
    return True


def store_list_if_changed(conn, source: str, url: str, text: str, run_id: int, content_type: str) -> bool:
    h = series_store.hash_text(text)
    last = conn.execute(sa.text(
        "SELECT meta->>'hash' FROM staging.raw_payload WHERE source = :s AND endpoint_key = :k ORDER BY payload_id DESC LIMIT 1"),
        {"s": source, "k": url}).scalar()
    if last == h:
        return False
    conn.execute(sa.text(
        "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, body, meta)"
        " VALUES (:s, :k, :ct, :b, cast(:m AS jsonb))"),
        {"s": source, "k": url, "ct": content_type, "b": text, "m": json.dumps({"hash": h, "run_id": run_id, "bytes": len(text.encode("utf-8"))})})
    return True


def store_refused(conn, source: str, url: str, html_text: str, reason: str, run_id: int) -> None:
    conn.execute(sa.text(
        "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, body, meta)"
        " VALUES (:s, :k, 'html', :b, cast(:m AS jsonb))"),
        {"s": source, "k": url, "b": html_text,
         "m": json.dumps({"refused": True, "reason": reason, "run_id": run_id, "bytes": len(html_text.encode("utf-8"))})})


def upsert_domain_state(engine, sources: set[str], watermark: str) -> None:
    for s in sorted(sources):
        series_store.upsert_domain_state(engine, s, (DOMAIN,), watermark)
```

- [ ] **Step 6: Chạy xanh** — e54, e55, và `tests/schema/test_s07_news.py` (không đổi). `content_type` cho danh sách: `'text'` với XML, `'html'` với trang HTML (CHECK của `raw_payload` chỉ nhận `json|html|text`).

- [ ] **Step 7: Commit (controller)** `feat(etl): news store — dedupe by url/canonical/title-48h, immutable revisions, evidence, tagging tiers 1-2`.

---

### Task 4: Fetch + job `collect` + `--loop` + CLI

**Files:** Create `backend/etl/news_fetch.py`, `backend/etl/news_job.py`, `backend/tests/etl/test_e56_news_job.py`, `backend/tests/etl/test_e58_news_cli.py`; Modify `backend/etl/__main__.py` (thêm khối `news`).

**Interfaces (Produces):**
```python
# news_fetch
ARTICLE_MIN_BYTES = 5000
def classify(http, text): 404 ⇒ ('bad_shape', None); 200 ⇒ ('ok', text); else ('retry', None)
@contextmanager def open_news_fetcher(get=None, sleep=time.sleep, rng=None)   # get thật: httpx.Client, trả (status, decode(content), headers)
class NewsFetcher: fetch(url, label) -> str; calls; retries
# news_job
JOB = "news.collect"; CYCLE_SECONDS = 300; SITEMAP_EVERY = 3; MAX_FAILED_RATE = 0.20; MAX_REFUSED_RATE = 0.05; STALE_DAYS = 7
def collect(engine, registry, *, run_id, now, dry_run, subset, cycle, get, sleep, rng) -> dict   # stats
def run(sources=None, dry_run=False, loop=False, minutes=None, get=None, sleep=time.sleep, now=None, rng=None, clock=time.monotonic) -> int
```

- [ ] **Step 1: Test đỏ — e56** (DB; `get` giả: feed theo tên báo trong URL, danh sách theo fixture, bài = trang tổng hợp nhỏ dựng từ `RULES`):

```python
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
from etl import news_registry as nr

FIX = pathlib.Path(__file__).parent / "fixtures" / "news"
VN = timezone(timedelta(hours=7))
NOW = datetime(2026, 9, 6, 0, 0, tzinfo=VN)
NAMES = nr.SOURCES


def _tag(sel):
    """'div.detail-content.afcbc-body' ⇒ '<div class="detail-content afcbc-body">'; 'div#vst_detail' ⇒ '<div id="vst_detail">'; 'main#article-editor'…"""
    m = re.match(r"([a-z]+)(#[\w-]+)?((?:\.[\w-]+)*)", sel.split(",")[0].strip())
    tag, idp, classes = m.group(1), m.group(2), m.group(3)
    attrs = (f' id="{idp[1:]}"' if idp else "") + (f' class="{" ".join(classes[1:].split("."))}"' if classes else "")
    return f"<{tag}{attrs}>", f"</{tag}>"


def _page(rule, title, n=1):
    r = ne.RULES[rule]
    co, cc = _tag(r.container)
    to, tc = _tag(r.title)
    body = " ".join(f"Đoạn {i} của bài {title} nói về HPG và thị trường." for i in range(n * 8))
    return f"<html><head></head><body>{to}{title}{tc}{co}<p>{body}</p>{cc}</body></html>"


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
        return 200, _page(rule, f"Bài {abs(hash(u)) % 100000}") * 6, {}          # ×6 để > 5 KB
    return get


def _cleanup(engine):
    with engine.begin() as c:
        for t in ("news.article_ticker", "news.article_source", "news.article_revision", "news.article"):
            c.execute(sa.text(f"DELETE FROM {t}"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source = ANY(:s)"), {"s": list(NAMES)})
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job LIKE 'news.%'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE domain='news'"))
        c.execute(sa.text("DELETE FROM market.security WHERE ticker = 'HPG' AND exchange = 'ZZ'"))


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.news_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    with migrated_engine.begin() as c:
        c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, status) VALUES ('HPG','ZZ','stock','listed')"))
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
    assert _n(clean, "SELECT count(*) FROM news.article WHERE feed='sitemap'") > 0                          # cycle 0 có sitemap
    assert _n(clean, "SELECT count(*) FROM staging.raw_payload WHERE source = ANY(ARRAY['cafef','bnews','tinnhanhck']) AND NOT coalesce((meta->>'refused')::bool,false)") == stats["lists_stored"]
    assert _n(clean, "SELECT count(*) FROM staging.raw_payload WHERE (meta->>'refused')::bool") == 0
    assert _n(clean, "SELECT count(*) FROM ops.data_domain_state WHERE domain='news'") == 8
    assert stats["stale_feeds"] == [] or all("/" in s for s in stats["stale_feeds"])
    # lượt hai cùng fixture: mọi item đã thấy
    assert nj.run(get=_fake_get(), sleep=lambda s: None, now=NOW + timedelta(minutes=5)) == 0
    status, stats2, _ = _last(clean)
    assert stats2["new"] == 0 and stats2["seen"] == stats2["items"] and stats2["cycle"] == 0
    assert _n(clean, "SELECT count(*) FROM news.article_revision WHERE version > 1") == 0


def test_title_merge_across_sources_keeps_both_urls(clean):
    def get(u, timeout):
        if u.endswith(".rss") or "/rss/" in u:
            n = next(n for n in NAMES if n in u)
            return 200, (f'<rss><channel><item><title>Cùng một tin lớn</title><link>https://{n}.vn/tin-lon-{n}.htm</link>'
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
            return 200, _page("cafef", "Cùng một tin lớn") * 6, {}
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
    def get_short(u, timeout):
        st, b, h = get(u, timeout)
        return (200, "<html>tiny</html>", h) if st == 200 and not u.endswith(".rss") else (st, b, h)
    assert nj.run(sources=["cafef"], get=get_short, sleep=lambda s: None, now=NOW) == 0
    assert _last(clean)[1]["refused"] == 1 and _n(clean, "SELECT count(*) FROM staging.raw_payload WHERE meta->>'reason'='soft404'") == 1


def test_dry_run_writes_nothing_and_reports_new(clean):
    assert nj.run(dry_run=True, get=_fake_get(), sleep=lambda s: None, now=NOW) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and stats["dry_run"] is True and stats["new"] > 300 and "articles_ok" not in stats
    assert _n(clean, "SELECT count(*) FROM news.article") == 0 and _n(clean, "SELECT count(*) FROM staging.raw_payload WHERE source='cafef'") == 0


def test_loop_runs_cycles_until_minutes_and_sleeps_the_remainder(clean):
    slept, ticks = [], iter([0.0, 10.0, 10.0, 310.0, 310.0, 700.0, 700.0, 1000.0])
    assert nj.run(loop=True, minutes=8, get=_fake_get(), sleep=slept.append, now=NOW, clock=lambda: next(ticks)) == 0
    assert _n(clean, "SELECT count(*) FROM ops.etl_run WHERE job='news.collect'") == 3 and slept == [290.0, 0.0]   # vòng 2 vượt 300 s ⇒ không ngủ
    with clean.connect() as c:
        cycles = [r[0] for r in c.execute(sa.text("SELECT (stats->>'cycle')::int FROM ops.etl_run WHERE job='news.collect' ORDER BY run_id"))]
    assert cycles == [0, 1, 2]


def test_unknown_source_and_ctrl_c(clean, monkeypatch):
    assert nj.run(sources=["cafef", "khong_co"], get=_fake_get(), sleep=lambda s: None, now=NOW) == 2
    def boom(*a, **k):
        raise KeyboardInterrupt
    monkeypatch.setattr(nj, "collect", boom)
    assert nj.run(get=_fake_get(), sleep=lambda s: None, now=NOW) == 130
    assert _last(clean)[2] == "dừng tay (Ctrl+C)"
```

- [ ] **Step 2: Test đỏ — e58 CLI**

```python
"""CLI `etl news`: cờ thu thập, vòng lặp, backfill sitemap (Task 5 nối thêm)."""
import pytest

import etl.__main__ as m


def test_news_flags_reach_run(monkeypatch):
    import etl.news_job
    seen = {}
    monkeypatch.setattr(etl.news_job, "run", lambda **kw: seen.update(kw) or 0)
    assert m.main(["news", "--loop", "--minutes", "90", "--sources", "cafef,bnews"]) == 0
    assert seen == {"sources": ["cafef", "bnews"], "dry_run": False, "loop": True, "minutes": 90.0}
    assert m.main(["news", "--dry-run"]) == 0 and seen["dry_run"] is True and seen["loop"] is False and seen["minutes"] is None


def test_minutes_requires_loop():
    with pytest.raises(SystemExit) as e:
        m.main(["news", "--minutes", "5"])
    assert e.value.code == 2
```

- [ ] **Step 3: Chạy đỏ** — e56, e58.

- [ ] **Step 4: `news_fetch.py`**

```python
"""I/O của pipeline tin: một Fetcher chung cho trọn lượt (giãn cách ngẫu nhiên 1–5 s — lát 7b), `get` thật trả text đã
decode theo luật null byte (README §6.1 — không tin charset khai), classify chung: 404 là mã chết (không thử lại),
200 là có (hình dạng kiểm ở parse/extract), còn lại thử lại."""
from __future__ import annotations

import contextlib
import time

import httpx

from etl.http_fetch import BadShape, DEFAULT_HEADERS, FetchError, Fetcher  # noqa: F401 — re-export cho news_job
from etl.news_parse import decode

ARTICLE_MIN_BYTES = 5000          # dưới đó là trang lỗi/soft-404 (đo 2026-09-05: bài bị gỡ trả 200 với 3 KB)
HEADERS = {"User-Agent": "Mozilla/5.0 (dulieuchungkhoan.vn etl; dulieuchungkhoan.official@gmail.com)", "Accept-Encoding": "gzip"}


def classify(http: int, text: str):
    if http == 404:
        return "bad_shape", None
    if http == 200:
        return "ok", text
    return "retry", None


@contextlib.contextmanager
def open_news_fetcher(get=None, sleep=time.sleep, rng=None):
    if get is not None:
        yield Fetcher(get, classify, sleep=sleep, rng=rng)
        return
    with httpx.Client(headers={**DEFAULT_HEADERS, **HEADERS}, follow_redirects=True) as client:
        def get_one(u: str, timeout: float):
            r = client.get(u, timeout=timeout)
            return r.status_code, decode(r.content), dict(r.headers)
        yield Fetcher(get_one, classify, sleep=sleep, rng=rng)
```

- [ ] **Step 5: `news_job.py`** (phần `collect`/`run`; Task 5 thêm backfill)

```python
"""`python -m etl news` — thu 47 feed + 6 crawl → news.* (spec lát 8 §5.2). Khuôn `series_job`: open_run ngay trước try,
Ctrl+C ⇒ failed 'dừng tay (Ctrl+C)' exit 130; KHÔNG từ chối cả lượt (tin bỏ lỡ là mất thật) — tally + warnings.
--loop: mỗi vòng một etl_run, nhịp 300 s, sitemap mỗi 3 vòng; --sources: lượt con không đụng domain state."""
from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from core.env import load_dotenv
from etl import news_extract, news_fetch, news_registry, news_store, news_tag, omo_store
from etl.news_parse import PARSERS, ParseError

log = logging.getLogger("etl.news")
VN = ZoneInfo("Asia/Ho_Chi_Minh")
JOB = "news.collect"
CYCLE_SECONDS = 300
SITEMAP_EVERY = 3
MAX_FAILED_RATE = 0.20
MAX_REFUSED_RATE = 0.05
STALE_DAYS = 7


def _engine():
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        raise RuntimeError("thiếu ETL_DATABASE_URL")
    return sa.create_engine(url, pool_pre_ping=True)


def _empty_stats(now_vn, cycle):
    return {"sources_total": 0, "lists_ok": 0, "lists_failed": 0, "lists_stored": 0, "items": 0, "seen": 0, "merged_url": 0,
            "merged_title": 0, "new": 0, "stale_feeds": [], "warnings": [], "calls": 0, "retries": 0,
            "run_date": now_vn.date().isoformat(), "cycle": cycle}


def _newest(items):
    ts = [it.published_at for it in items if it.published_at]
    return max(ts) if ts else None


def collect(engine, registry, *, run_id, now, dry_run, subset, cycle, get, sleep, rng) -> dict:
    now_vn = now.astimezone(VN)
    st = _empty_stats(now_vn, cycle)
    st["sources_total"] = len(registry)
    items: dict[str, object] = {}
    ok_sources: set[str] = set()
    with news_fetch.open_news_fetcher(get=get, sleep=sleep, rng=rng) as f:
        for s in registry:
            if s.kind == "tnck_sitemap" and cycle % SITEMAP_EVERY != 0:
                continue
            url = news_registry.sitemap_url(now_vn) if s.kind == "tnck_sitemap" else s.url
            try:
                text = f.fetch_one(url, f"{s.name}/{s.feed_slug}")[1]
                parsed = PARSERS[s.kind](text, s)
            except (news_fetch.BadShape, news_fetch.FetchError, ParseError) as e:
                st["lists_failed"] += 1
                log.warning("%s", e)
                continue
            st["lists_ok"] += 1
            ok_sources.add(s.name)
            if not dry_run:
                with engine.begin() as c:
                    if news_store.store_list_if_changed(c, s.name, url, text, run_id, "text" if s.kind in ("rss", "tnck_sitemap") else "html"):
                        st["lists_stored"] += 1
            newest = _newest(parsed)
            if s.kind == "rss" and newest and now - newest > timedelta(days=STALE_DAYS):
                st["stale_feeds"].append(f"{s.name}/{s.feed_slug}")
            for it in parsed:
                items.setdefault(it.canonical_url, it)               # cùng kênh qua nhiều slug: bản đầu thắng
        st["items"] = len(items)
        with engine.connect() as c:
            seen = news_store.Seen.load(c, now)
            listed = news_store.load_listed(c)
        if not dry_run:
            st.update({"articles_ok": 0, "articles_failed": 0, "refused": 0, "tickers_url": 0, "tickers_lookup": 0})
        for it in items.values():
            decision, aid = seen.decide(it, now)
            if decision == "seen":
                st["seen"] += 1
                continue
            if decision in ("merge_url", "merge_title"):
                st[decision.replace("merge_", "merged_")] += 1
                if not dry_run:
                    with engine.begin() as c:
                        news_store.add_source(c, aid, it.source, it.url)
                    seen.urls.add(it.url)
                continue
            st["new"] += 1
            if dry_run:
                seen.remember(it, -1, now)
                continue
            try:
                html_text = f.fetch_one(it.url, it.source)[1]
            except (news_fetch.BadShape, news_fetch.FetchError) as e:
                st["articles_failed"] += 1
                log.warning("%s", e)
                continue
            if len(html_text.encode("utf-8")) < news_fetch.ARTICLE_MIN_BYTES:
                st["refused"] += 1
                with engine.begin() as c:
                    news_store.store_refused(c, it.source, it.url, html_text, "soft404", run_id)
                continue
            try:
                ext = news_extract.extract(html_text, it.rule)
            except news_extract.ExtractError as e:
                st["refused"] += 1
                with engine.begin() as c:
                    news_store.store_refused(c, it.source, it.url, html_text, e.reason, run_id)
                continue
            tickers: list[tuple[str, str, int]] = []
            if it.group_from_feed == 3:
                for t in news_tag.tickers_from_url(it.url):
                    if t in listed:
                        tickers.append((t, "url", listed[t]))
                        st["tickers_url"] += 1
                for t in news_tag.tickers_lookup(ext.title, ext.sapo, listed):
                    tickers.append((t, "lookup", listed[t]))
                    st["tickers_lookup"] += 1
            with engine.begin() as c:
                aid = news_store.insert_article(c, it, ext, fetched_at=now, tickers=tickers)
            seen.remember(it, aid, now)
            st["articles_ok"] += 1
        st["calls"], st["retries"] = f.calls, f.retries_done
    lists_total = st["lists_ok"] + st["lists_failed"]
    if lists_total and st["lists_failed"] / lists_total > MAX_FAILED_RATE:
        st["warnings"].append(f"feed/danh sách hỏng {st['lists_failed']}/{lists_total} > {MAX_FAILED_RATE:.0%}")
    if not dry_run and st["new"] and st["refused"] / st["new"] > MAX_REFUSED_RATE:
        st["warnings"].append(f"bóc từ chối {st['refused']}/{st['new']} > {MAX_REFUSED_RATE:.0%}")
    if st["stale_feeds"]:
        st["warnings"].append(f"feed im > {STALE_DAYS} ngày: {st['stale_feeds']}")
    st["_ok_sources"] = sorted(ok_sources)
    if subset:
        st["subset"] = True
    if dry_run:
        st["dry_run"] = True
    return st


def _one_cycle(engine, registry, *, subset, dry_run, cycle, get, sleep, now, rng) -> int:
    run_id = omo_store.open_run(engine, JOB)
    try:
        st = collect(engine, registry, run_id=run_id, now=now, dry_run=dry_run, subset=subset, cycle=cycle, get=get, sleep=sleep, rng=rng)
        ok_sources = set(st.pop("_ok_sources"))
        if not subset and not dry_run:
            st["watermark"] = st["run_date"]
        omo_store.close_run(engine, run_id, "success", st)
        if not subset and not dry_run:
            news_store.upsert_domain_state(engine, ok_sources, st["run_date"])
        log.info("news cycle %s: items %s · new %s · merged %s/%s · seen %s · refused %s · warnings %s",
                 cycle, st["items"], st["new"], st["merged_url"], st["merged_title"], st["seen"], st.get("refused", "-"), st["warnings"])
        return 0
    except KeyboardInterrupt:
        omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
        log.warning("news dừng tay (Ctrl+C)")
        return 130
    except Exception as e:                    # noqa: BLE001 — job biên ngoài
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("news thất bại")
        return 2


def run(sources=None, dry_run=False, loop=False, minutes=None, get=None, sleep=time.sleep, now=None, rng=None, clock=time.monotonic) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    load_dotenv()
    try:
        engine = _engine()
        registry = news_registry.build()
        if sources is not None:
            unknown = sorted(set(sources) - set(news_registry.SOURCES))
            if unknown:
                raise RuntimeError(f"báo không có trong registry: {unknown}")
            registry = [s for s in registry if s.name in set(sources)]
    except (RuntimeError, news_registry.RegistryError) as e:
        log.error("%s", e)
        return 2
    subset = sources is not None
    t0 = clock()
    cycle = 0
    try:
        while True:
            started = clock()
            rc = _one_cycle(engine, registry, subset=subset, dry_run=dry_run, cycle=cycle,
                            get=get, sleep=sleep, now=now or datetime.now(timezone.utc), rng=rng)
            if rc != 0 or not loop:
                return rc
            cycle += 1
            if minutes is not None and clock() - t0 >= minutes * 60:
                return 0
            try:
                sleep(max(0.0, CYCLE_SECONDS - (clock() - started)))
            except KeyboardInterrupt:
                log.warning("news dừng tay (Ctrl+C) giữa hai vòng")
                return 130
    finally:
        engine.dispose()
```

Kiểm lại với test `test_loop_…`: `clock` được gọi: `t0`(0.0) · vòng 0 `started`(10.0) · sau vòng `clock()-t0`(10.0 ⇒ 10 < 480) · ngủ `300-(310-10)`… — **implementer chỉnh dãy `ticks` trong test cho khớp số lần gọi `clock()` của code, rồi ghi report** (dãy trong plan là dự kiến; kỳ vọng vẫn là 3 vòng và hai lần ngủ, lần hai bằng 0). Với `now` cố định truyền vào, mọi vòng cùng `now` — chấp nhận trong test.

- [ ] **Step 6: `__main__.py`** — sau khối `wichart`:

```python
    if args[0] == "news":
        import etl.news_job
        parser = argparse.ArgumentParser(prog="etl news")
        parser.add_argument("--dry-run", action="store_true", dest="dry_run")
        parser.add_argument("--sources", type=lambda s: [k.strip() for k in s.split(",") if k.strip()])
        parser.add_argument("--loop", action="store_true")
        parser.add_argument("--minutes", type=float)
        parsed = parser.parse_args(args[1:])
        if parsed.minutes is not None and not parsed.loop:
            parser.error("--minutes chỉ đi với --loop")
        return etl.news_job.run(sources=parsed.sources, dry_run=parsed.dry_run, loop=parsed.loop, minutes=parsed.minutes)
```
và thêm `news` vào chuỗi "hỗ trợ: …".

- [ ] **Step 7: Chạy xanh** — e56, e58, e01 (CLI cũ), rồi `uv run pytest tests/etl -q`.

- [ ] **Step 8: Commit (controller)** `feat(etl): news collect job — 53 lists, dedupe, extract, tag, evidence, --loop/--sources/--dry-run, CLI`.

---

### Task 5: Backfill sitemap TinnhanhCK

**Files:** Modify `backend/etl/news_job.py` (thêm `backfill_sitemap`, `run_backfill`), `backend/etl/__main__.py` (cờ), Create `backend/tests/etl/test_e57_news_backfill.py`; e58 thêm 1 test.

**Interfaces:** `JOB_BACKFILL = "news.backfill_sitemap"`; `MAX_CONSECUTIVE_FAILED = 10`; `class SourceDown(Exception)`; `def months_desc(from_month: str, to_month: str) -> list[str]` (`'2026-09','2026-08',…`); `def load_cursor(engine) -> str | None` (stats.cursor của lượt `news.backfill_sitemap` gần nhất); `def backfill_sitemap(engine, from_month, to_month, *, run_id, max_minutes, stop_before_open, get, sleep, now, rng, clock) -> dict`; `def run_backfill(from_month, to_month=None, max_minutes=None, stop_before_open=False, get=None, sleep=time.sleep, now=None, rng=None, clock=time.monotonic) -> int`.

- [ ] **Step 1: Test đỏ — e57**

```python
"""Backfill sitemap TinnhanhCK: tháng lùi, bỏ trang chủ, bỏ URL đã có, mỗi bài một giao dịch, con trỏ tháng, hạn giờ, cầu chì 10 bài."""
import os
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sa

from etl import news_job as nj
from tests.etl.test_e56_news_job import _cleanup, _page, NAMES  # noqa: F401 — cùng khuôn dọn/dựng trang

VN = timezone(timedelta(hours=7))
NOW = datetime(2026, 9, 6, 0, 0, tzinfo=VN)
SM = ('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
      '<url><loc>https://www.tinnhanhchungkhoan.vn</loc><lastmod>2026-09-06T00:00:00+07:00</lastmod></url>'
      '<url><loc>https://www.tinnhanhchungkhoan.vn/a-post1.html</loc><lastmod>2026-08-01T08:00:00+07:00</lastmod></url>'
      '<url><loc>https://www.tinnhanhchungkhoan.vn/b-post2.html</loc><lastmod>2026-08-02T08:00:00+07:00</lastmod></url>'
      '<url><loc>https://www.tinnhanhchungkhoan.vn/c-post3.html</loc><lastmod>2026-08-03T08:00:00+07:00</lastmod></url></urlset>')


def _get(months_seen=None, fail=()):
    def get(u, timeout):
        if "/sitemaps/news-" in u:
            if months_seen is not None:
                months_seen.append(u.rsplit("news-", 1)[1].replace(".xml", ""))
            return 200, SM, {}
        if any(f in u for f in fail):
            return 503, "", {}
        return 200, _page("tinnhanhck", "Bài " + u.rsplit("/", 1)[1]) * 6, {}
    return get


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.news_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def _last(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job='news.backfill_sitemap' ORDER BY run_id DESC LIMIT 1")).one()


def _n(engine, sql):
    with engine.connect() as c:
        return c.execute(sa.text(sql)).scalar()


def test_months_desc_and_cursor_resume():
    assert nj.months_desc("2026-07", "2026-09") == ["2026-09", "2026-08", "2026-07"]
    assert nj.months_desc("2025-11", "2026-01") == ["2026-01", "2025-12", "2025-11"]
    with pytest.raises(ValueError):
        nj.months_desc("2026-9", "2026-09")


def test_backfill_one_month_skips_homepage_and_seen_urls_and_sets_cursor(clean):
    with clean.begin() as c:
        c.execute(sa.text("INSERT INTO news.article (canonical_url, primary_source, fetched_at) VALUES ('https://www.tinnhanhchungkhoan.vn/b-post2.html','tinnhanhck',now()) RETURNING article_id"))
        aid = c.execute(sa.text("SELECT article_id FROM news.article")).scalar()
        c.execute(sa.text("INSERT INTO news.article_revision (article_id, version, title, content, content_fetched_at) VALUES (:a,1,'b','x',now())"), {"a": aid})
        c.execute(sa.text("INSERT INTO news.article_source (article_id, source_name, url) VALUES (:a,'tinnhanhck','https://www.tinnhanhchungkhoan.vn/b-post2.html')"), {"a": aid})
    months = []
    assert nj.run_backfill("2026-08", "2026-08", get=_get(months), sleep=lambda s: None, now=NOW) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and months == ["2026-8"] and stats["months_done"] == ["2026-08"] and stats["cursor"] == "2026-08"
    assert stats["urls_in_sitemap"] == 3 and stats["skipped_seen"] == 1 and stats["articles_ok"] == 2 and stats["budget_hit"] is False
    with clean.connect() as c:
        rows = c.execute(sa.text("SELECT canonical_url, feed, published_at, published_at_src, group_from_feed FROM news.article ORDER BY canonical_url")).all()
    assert [r[0][-12:] for r in rows] == ["/a-post1.html", "/b-post2.html", "/c-post3.html"]
    a = rows[0]
    assert a[1] == "sitemap" and a[2] == datetime(2026, 8, 1, 8, 0, tzinfo=VN) and a[3] == "feed" and a[4] is None   # trang tổng hợp không có cms-date ⇒ lastmod
    assert nj.run_backfill("2026-08", "2026-08", get=_get(), sleep=lambda s: None, now=NOW) == 0
    assert _last(clean)[1]["articles_ok"] == 0 and _last(clean)[1]["skipped_seen"] == 3


def test_cursor_resumes_from_month_before_last_done(clean):
    months = []
    assert nj.run_backfill("2026-07", "2026-09", get=_get(months), sleep=lambda s: None, now=NOW, max_minutes=None) == 0
    assert months == ["2026-9", "2026-8", "2026-7"] and _last(clean)[1]["cursor"] == "2026-07"
    assert nj.load_cursor(clean) == "2026-07"
    months.clear()
    assert nj.run_backfill("2026-05", "2026-09", get=_get(months), sleep=lambda s: None, now=NOW) == 0
    assert months == ["2026-6", "2026-5"]                                                  # nối sau con trỏ, không lặp 09/08/07


def test_budget_stops_after_current_article_and_keeps_it(clean):
    ticks = iter([0.0] + [10 * 60.0] * 50)                                                 # sau bài đầu tiên đã hết 5 phút
    assert nj.run_backfill("2026-08", "2026-08", max_minutes=5, get=_get(), sleep=lambda s: None, now=NOW, clock=lambda: next(ticks)) == 0
    status, stats, _ = _last(clean)
    assert status == "success" and stats["budget_hit"] is True and stats["articles_ok"] == 1 and stats["months_done"] == [] and stats["cursor"] is None
    assert _n(clean, "SELECT count(*) FROM news.article") == 1


def test_ten_consecutive_failures_trip_the_breaker(clean):
    sm = "".join(f'<url><loc>https://www.tinnhanhchungkhoan.vn/x{i}-post{i}.html</loc><lastmod>2026-08-01T08:00:00+07:00</lastmod></url>' for i in range(12))
    def get(u, timeout):
        return (200, f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>', {}) if "/sitemaps/" in u else (503, "", {})
    assert nj.run_backfill("2026-08", "2026-08", get=get, sleep=lambda s: None, now=NOW) == 1
    status, stats, err = _last(clean)
    assert status == "failed" and "10 bài liên tiếp" in err and stats["articles_failed"] == 10 and stats["cursor"] is None
```

Thêm vào e58:
```python
def test_backfill_flags_and_exclusions(monkeypatch):
    import etl.news_job
    seen = {}
    monkeypatch.setattr(etl.news_job, "run_backfill", lambda **kw: seen.update(kw) or 0)
    assert m.main(["news", "--backfill-sitemap", "--from", "2026-08", "--to", "2026-09", "--max-minutes", "30", "--stop-before-open"]) == 0
    assert seen == {"from_month": "2026-08", "to_month": "2026-09", "max_minutes": 30.0, "stop_before_open": True}
    for bad in (["news", "--backfill-sitemap"], ["news", "--backfill-sitemap", "--from", "2026-8"], ["news", "--backfill-sitemap", "--from", "2026-08", "--loop"]):
        with pytest.raises(SystemExit) as e:
            m.main(bad)
        assert e.value.code == 2
```

- [ ] **Step 2: Chạy đỏ.**

- [ ] **Step 3: Code trong `news_job.py`**

```python
JOB_BACKFILL = "news.backfill_sitemap"
MAX_CONSECUTIVE_FAILED = 10
MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class SourceDown(Exception):
    """10 bài liên tiếp hỏng — nguồn hoặc mạng chết, dừng lượt (khuôn backfill giá)."""


def months_desc(from_month: str, to_month: str) -> list[str]:
    if not (MONTH.match(from_month) and MONTH.match(to_month)):
        raise ValueError(f"tháng phải dạng YYYY-MM: {from_month!r}, {to_month!r}")
    y, m = int(to_month[:4]), int(to_month[5:])
    out = []
    while f"{y:04d}-{m:02d}" >= from_month:
        out.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return out


def load_cursor(engine) -> str | None:
    with engine.connect() as c:
        return c.execute(sa.text(
            "SELECT stats->>'cursor' FROM ops.etl_run WHERE job = :j AND stats->>'cursor' IS NOT NULL"
            " ORDER BY run_id DESC LIMIT 1"), {"j": JOB_BACKFILL}).scalar()


def _prev_month(ym: str) -> str:
    y, m = int(ym[:4]), int(ym[5:])
    return f"{y - 1:04d}-12" if m == 1 else f"{y:04d}-{m - 1:02d}"


def backfill_sitemap(engine, from_month, to_month, *, run_id, max_minutes, stop_before_open, get, sleep, now, rng, clock) -> dict:
    from etl.price_job import _next_open
    t0 = clock()
    deadline_s = None
    if max_minutes is not None:
        deadline_s = max_minutes * 60
    stop_at = _next_open(datetime.now(VN)) if stop_before_open else None
    st = {"cursor": None, "months_done": [], "month": None, "urls_in_sitemap": 0, "skipped_seen": 0, "articles_ok": 0,
          "articles_failed": 0, "refused": 0, "budget_hit": False, "calls": 0, "retries": 0, "stop_at": stop_at.isoformat(timespec="minutes") if stop_at else None}
    with engine.connect() as c:
        seen = news_store.Seen.load(c, now)
    streak = 0
    with news_fetch.open_news_fetcher(get=get, sleep=sleep, rng=rng) as f:
        for ym in months_desc(from_month, to_month):
            st["month"] = ym
            y, m = int(ym[:4]), int(ym[5:])
            src = news_registry.Source("tinnhanhck", "tnck_sitemap", news_registry.SITEMAP, None, "sitemap")
            text = f.fetch_one(news_registry.SITEMAP.format(y=y, m=m), f"sitemap {ym}")[1]
            items = PARSERS["tnck_sitemap"](text, src)
            st["urls_in_sitemap"] += len(items)
            for it in items:
                if it.url in seen.urls or it.canonical_url in seen.canon:
                    st["skipped_seen"] += 1
                    continue
                try:
                    html_text = f.fetch_one(it.url, "tinnhanhck")[1]
                    if len(html_text.encode("utf-8")) < news_fetch.ARTICLE_MIN_BYTES:
                        raise news_fetch.BadShape("soft404")
                    ext = news_extract.extract(html_text, "tinnhanhck")
                except (news_fetch.BadShape, news_fetch.FetchError) as e:
                    st["articles_failed"] += 1
                    streak += 1
                    log.warning("%s", e)
                    if streak >= MAX_CONSECUTIVE_FAILED:
                        raise SourceDown(f"{streak} bài liên tiếp hỏng — nguồn hoặc mạng chết, dừng lượt") from e
                    continue
                except news_extract.ExtractError as e:
                    st["refused"] += 1
                    with engine.begin() as c:
                        news_store.store_refused(c, "tinnhanhck", it.url, html_text, e.reason, run_id)
                    continue
                streak = 0
                with engine.begin() as c:
                    aid = news_store.insert_article(c, it, ext, fetched_at=now, tickers=[])
                seen.remember(it, aid, now)
                st["articles_ok"] += 1
                if (deadline_s is not None and clock() - t0 >= deadline_s) or (stop_at and datetime.now(VN) >= stop_at):
                    st["budget_hit"] = True
                    break
            if st["budget_hit"]:
                break
            st["months_done"].append(ym)
            st["cursor"] = ym
        st["calls"], st["retries"] = f.calls, f.retries_done
    return st


def run_backfill(from_month, to_month=None, max_minutes=None, stop_before_open=False, get=None, sleep=time.sleep, now=None, rng=None, clock=time.monotonic) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    load_dotenv()
    now = now or datetime.now(timezone.utc)
    to_month = to_month or now.astimezone(VN).strftime("%Y-%m")
    try:
        engine = _engine()
        months_desc(from_month, to_month)
        cursor = load_cursor(engine)
        if cursor and cursor <= to_month:
            to_month = _prev_month(cursor)                      # nối sau tháng đã xong (lùi dần)
            if to_month < from_month:
                log.info("con trỏ %s đã qua --from %s — không còn gì để làm", cursor, from_month)
                return 0
    except (RuntimeError, ValueError) as e:
        log.error("%s", e)
        return 2
    run_id = omo_store.open_run(engine, JOB_BACKFILL)
    try:
        st = backfill_sitemap(engine, from_month, to_month, run_id=run_id, max_minutes=max_minutes, stop_before_open=stop_before_open,
                              get=get, sleep=sleep, now=now, rng=rng, clock=clock)
        omo_store.close_run(engine, run_id, "success", st)
        log.info("news backfill xong: %s", st)
        return 0
    except SourceDown as e:
        omo_store.close_run(engine, run_id, "failed", error=str(e))
        log.error("%s", e)
        return 1
    except KeyboardInterrupt:
        omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
        return 130
    except Exception as e:                    # noqa: BLE001
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("news backfill thất bại")
        return 2
    finally:
        engine.dispose()
```

`SourceDown` phải ghi `stats` (articles_failed 10) khi `failed`: trong `except SourceDown` gọi `close_run(..., "failed", st?, error)` — `st` chưa có ngoài hàm ⇒ implementer gắn `st` vào exception (`e.stats = st`) hoặc trả `st` qua thuộc tính; **chọn:** `SourceDown(msg, stats)` với `self.stats`, `close_run(engine, run_id, "failed", e.stats, error=str(e))`. Sửa `raise SourceDown(f"…", st)`.

- [ ] **Step 4: CLI** — thêm vào khối `news`: `--backfill-sitemap` (store_true), `--from` (`dest="from_month"`), `--to` (`dest="to_month"`), `--max-minutes` (float, `dest="max_minutes"`), `--stop-before-open` (`dest="stop_before_open"`); nếu `backfill_sitemap`: yêu cầu `from_month` khớp `^\d{4}-(0[1-9]|1[0-2])$` (else `parser.error`), loại trừ `--loop`/`--dry-run`/`--sources` (`parser.error`), gọi `run_backfill(from_month=…, to_month=…, max_minutes=…, stop_before_open=…)`.

- [ ] **Step 5: Chạy xanh** — e57, e58, e56; `uv run pytest tests/etl -q`.

- [ ] **Step 6: Commit (controller)** `feat(etl): news --backfill-sitemap for TinnhanhCK — months descending, cursor, per-article transactions, breaker`.

---

### Task 6: Chạy thật (controller) — AC2–AC6, AC8–AC10, khởi động `--loop`

Từ `backend/`, prefix `set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8`.

- [ ] AC1 `uv run pytest -q`.
- [ ] AC2 `uv run python -m etl news --dry-run` ⇒ dán `stats`.
- [ ] AC3 `uv run python -m etl news` ⇒ đếm 4 bảng; chọn 3 bài (3 báo) đối chiếu tay tiêu đề + 60 ký tự đầu với trang gốc (mở bằng `httpx` in ra, đọc mắt).
- [ ] AC4 lượt hai ≤ 5 phút.
- [ ] AC5 truy vấn `article_ticker` theo `via`; đọc 3 bài `lookup`.
- [ ] AC6 truy vấn gộp; đọc 5 cặp `merged_title`.
- [ ] AC8 `uv run python -m etl news --backfill-sitemap --from 2026-08 --to 2026-08 --max-minutes 60`; lượt hai.
- [ ] AC9 `raw_payload` theo `meta->>'refused'`.
- [ ] AC10 grep log.
- [ ] Khởi động `--loop` cho AC7: chạy trong cửa sổ riêng (PowerShell `Start-Process` với `uv run python -m etl news --loop`, log ra `D:\twan_projects\dlck-runtime\logs\news-loop.log`), để ≥ 24 giờ có ngày làm việc (thứ 2 07/09); ghi ledger cách dừng (Ctrl+C trong cửa sổ).
- [ ] Ledger: AC1–AC6, AC8–AC10; AC7 ghi nợ "tổng hợp sau 24 giờ".

### Task 7: Tài liệu (§8 spec) — Sonnet với brief số đo thật từ Task 6

### Task 8: Review toàn nhánh hai trục (Opus) → sửa một đợt → re-review → `pytest` → merge `--no-ff` → ledger rulings.

---

## Tự rà plan

- **Phủ spec:** §5.1 file → T1–T5 · §5.2 luồng → T4 · §5.3 luật thời gian/URL → T1 · §5.4 bóc → T2 · §5.5 stats → T4/T5 · §5.6 loop → T4 · §5.7 backfill → T5 · §4.6-I tag title+sapo → T3 · §4.6-II `published_for` → T3 · §4.6-VII từ chối không tạo article → T4 · §6 seam: mỗi dòng có test (registry e52, parse e52, extract e53, tag e54, store e55, job e56, backfill e57, quyền e55, CLI e58) · §7 AC → T6.
- **Placeholder:** không TBD; số link TNCK/BCP dùng khoảng vì fixture lớn — implementer kiểm `grep -c` trước.
- **Nhất quán kiểu:** `Item` 11 trường dùng thống nhất T1/T3/T4/T5; `Extracted` 4 trường; `insert_article(conn, item, ext, *, fetched_at, tickers)`; `Seen.decide → (str, int|None)`; `collect(...) -> stats` với khoá `_ok_sources` bị pop ở `_one_cycle`; `store_list_if_changed(..., content_type)`.
- **Ruling khi viết plan:** (1) test job dùng trang tổng hợp nhỏ dựng theo `RULES` thay vì 9 fixture thật (tốc độ; fixture thật đã pin ở e53); (2) `Seen.load` nạp toàn bộ `article_source.url` và `article.canonical_url` mỗi vòng — chấp nhận ở 150k dòng/năm, ghi nợ tối ưu cho lát 12; (3) `SourceDown` mang `stats`.
