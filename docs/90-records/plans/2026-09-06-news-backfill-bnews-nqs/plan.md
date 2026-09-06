# Plan — lát 8b: backfill sitemap BNews + NguoiQuanSat

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `etl news --backfill-sitemap --source {tinnhanhck|bnews|nguoiquansat}` kéo lịch sử ba nguồn từ sitemap bằng một job, con trỏ riêng từng nguồn, luật bóc NguoiQuanSat nhận cả template cũ.

**Architecture:** Registry là chủ của mẫu URL sitemap + đơn vị kỳ (tháng/ngày) + regex URL bài theo nguồn (`SITEMAPS`); `parse_sitemap` và `backfill_sitemap` tham số hoá theo `source`; kind `tnck_sitemap` đổi thành `sitemap` chung với cờ `backfill_only` để `collect` bỏ qua hai nguồn mới. Đường ghi (`Seen`, `insert_article`, `store_refused`, `etl_run`) giữ nguyên lát 8.

**Tech Stack:** Python 3.12, `uv`, pytest (Postgres test thật qua `migrated_engine`), bs4, stdlib `xml.etree`.

**Spec:** [spec.md](spec.md) — đọc §3.1 (phạm vi), §4.2 (8 chốt), §6 (seam), §7 (AC). Số đo: [measure-sitemap-bnews-nqs-2026-09-06.md](measure-sitemap-bnews-nqs-2026-09-06.md).

## Global Constraints

- Chạy lệnh từ `backend/`: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/<file> -q` (Git Bash). Test DB cần `TEST_DATABASE_URL` trong `.env` gốc — fixture `migrated_engine` đã lo.
- **TDD từng seam:** viết test đỏ → chạy thấy đỏ đúng assertion → code tối thiểu → xanh → commit. Expected là **literal** ghi trong plan, không tính lại theo code.
- **Không sửa ngoài yêu cầu**: không refactor `news_job.collect` ngoài hai dòng nêu ở Task 4; không đổi rule `bnews`; không đổi UA.
- Style repo: comment tiếng Việt, docstring đầu file kể "vì sao"; dòng ≤ 150 ký tự như file hiện có; commit message tiếng Anh, Conventional Commits, kết `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Nhánh `feat/news-backfill-sitemaps`; commit từng task; không `--no-verify`.
- Tên báo cố định 8 giá trị `news_registry.SOURCES`; `published_at_src` chỉ `'feed'|'url'|'unknown'`.
- Fixture đã có sẵn ở `backend/tests/etl/fixtures/news/` (Task 0 do controller làm): `sitemap-bnews-2026-9.xml` (3 phần tử đầu + 5 bài), `sitemap-nguoiquansat-2026-09-05.xml` (5 bài, có `image:image`), `article-nguoiquansat-2024.html` (template cũ), `article-bnews-2020.html`.

---

### Task 0 (controller, đã làm): fixture + ghi chú chụp

**Files:** `backend/tests/etl/fixtures/news/{sitemap-bnews-2026-9.xml, sitemap-nguoiquansat-2026-09-05.xml, article-nguoiquansat-2024.html, article-bnews-2020.html}`, `CAPTURE-2026-09-05.txt` (thêm mục 2026-09-06).

Literal đọc từ fixture (dùng cho các task sau):
- `sitemap-bnews-2026-9.xml`: 8 `<url>`; [0..2] `https://bnews.vn`, `/photo/trang-1.html`, `/video/trang-1.html` (`lastmod 2026-09-05T22:57:40Z`); [3] `https://bnews.vn/lich-thi-dau-va-truc-tiep-ngoai-hang-anh-arsenal-vs-chelsea-luc-22h30-ngay-6-9/435626.html` `2026-09-06T05:30:00+07:00`; [7] `https://bnews.vn/le-hoi-den-long-viet-nam-thu-hut-5-000-nguoi-tai-australia/435662.html` `2026-09-05T22:05:14+07:00`.
- `sitemap-nguoiquansat-2026-09-05.xml`: 5 `<url>`, mỗi cái có `<image:image>`; [0] `https://nguoiquansat.vn/viet-nam-dau-tu-4-500-ty-dong-xay-benh-vien-1-500-giuong-tren-khu-dat-rong-16ha-co-2-bai-dap-truc-thang-du-kien-hoat-dong-nam-2027-314422.html` `2026-09-05T23:48:01+07:00`; [4] `https://nguoiquansat.vn/bidv-tung-goi-vay-30-000-ty-dong-lai-suat-thap-hon-2-cho-khach-hang-mua-nha-314417.html` `2026-09-05T23:04:01+07:00`.
- `article-nguoiquansat-2024.html` (bài 110172, 2024-01-15): `h1.c-detail-head__title` = `Đây là những tấm hộ chiếu quyền lực nhất thế giới năm 2024`; `span.c-detail-head__time` = `15-01-2024 13:04`; container `article.entry` sau khi bỏ `div.c-box`: **2.387** ký tự, bắt đầu `Đã có một “sự rung chuyển” trong thế giới hộ chiếu.`, kết thúc `nhưng chỉ 15% công dân muốn sở hữu`; không có `p.sc-longform-header-sapo`; `div.c-author-page` (ngoài container) chứa `Theo Kiến thức Đầu tư`.
- `article-bnews-2020.html` (bài 169672): tiêu đề `Thị trường chứng khoán Mỹ tăng điểm trong phiên 14/9`; text sạch **1.844** ký tự, bắt đầu `Trong phiên giao dịch ngày 14/9, thị trường chứng khoán Phố Wall (Mỹ) tăng điểm`, kết thúc `61 mã đứng giá và 59 mã giảm giá.`

---

### Task 1: Registry — `SITEMAPS`, kind `sitemap`, `backfill_only`, feeds.json 8 crawl

**Files:**
- Modify: `backend/etl/news_registry.py` (toàn file, 70 dòng)
- Modify: `docs/10-sources/news/feeds.json` (`crawl_html`, `_meta`)
- Modify: `backend/etl/news_parse.py:218` (`PARSERS` key), `backend/etl/news_job.py:89-91,103` (`collect`), `backend/etl/news_job.py:290,301-302` (chỉ đổi tên kind/URL — Task 4 sẽ viết lại hàm)
- Test: `backend/tests/etl/test_e52_news_parse.py` (`test_registry_53_sources_groups_and_slugs` → 55), `backend/tests/etl/test_e56_news_job.py` (không đổi assert 53 — phải vẫn xanh)

**Interfaces:**
- Produces: `SitemapSpec(period: str, url: str, article_url: re.Pattern)`; `SITEMAPS: dict[str, SitemapSpec]` với ba khoá `tinnhanhck`, `bnews`, `nguoiquansat`; `Source(name, kind, url, group_from_feed, feed_slug, backfill_only=False)`; `KINDS = ("rss", "cafef_cbtt", "tnck_category", "sitemap", "bcp_list")`; `sitemap_url(source: str, key: str) -> str` với `key` = `"YYYY-MM"` hoặc `"YYYY-MM-DD"`.
- `SITEMAP` (hằng cũ) **bị xoá**; `sitemap_url(now_vn)` cũ **bị thay**.

- [ ] **Step 1: Test đỏ — sửa và thêm ở `test_e52_news_parse.py`**

Thay hàm `test_registry_53_sources_groups_and_slugs` bằng:

```python
def test_registry_55_sources_groups_and_slugs():
    s = nr.build()
    assert len(s) == 55 and sum(1 for x in s if x.kind == "rss") == 47
    assert [sum(1 for x in s if x.kind == "rss" and x.group_from_feed == g) for g in (1, 2, 3)] == [14, 12, 21]
    assert {x.name for x in s} == set(nr.SOURCES)
    kinds = [x.kind for x in s if x.kind != "rss"]
    assert sorted(kinds) == ["bcp_list", "cafef_cbtt", "sitemap", "sitemap", "sitemap", "tnck_category", "tnck_category", "tnck_category"]
    assert REG[("vietstock", "rss", "739/chung-khoan/giao-dich-noi-bo")].url == "https://vietstock.vn/739/chung-khoan/giao-dich-noi-bo.rss"
    assert REG[("cafef", "cafef_cbtt", "cbtt")].group_from_feed == 3 and REG[("baochinhphu", "bcp_list", "chi-dao-dieu-hanh")].group_from_feed == 1
    tn = {x.feed_slug: x.group_from_feed for x in s if x.kind == "tnck_category"}
    assert tn == {"ck-quoc-te": 2, "chung-khoan": 3, "dau-tu": 1}
    # C1 (spec lát 8 §4.6-III): chuyên mục trước, sitemap sau — ba sitemap nằm cuối.
    assert [x.kind for x in s[-3:]] == ["sitemap", "sitemap", "sitemap"]
    # 8b: sitemap TinnhanhCK vẫn vá lỗ trong collect; BNews/NguoiQuanSat chỉ backfill (feeds.json chi_backfill).
    assert REG[("tinnhanhck", "sitemap", "sitemap")].backfill_only is False
    assert REG[("bnews", "sitemap", "sitemap")].backfill_only is True and REG[("nguoiquansat", "sitemap", "sitemap")].backfill_only is True
    assert all(x.backfill_only is False for x in s if x.kind != "sitemap")
    # M5 lát 8: url của sitemap là mẫu (SITEMAPS), không phải literal năm cứng chép từ feeds.json.
    assert REG[("bnews", "sitemap", "sitemap")].url == nr.SITEMAPS["bnews"].url
    assert nr.SITEMAPS["tinnhanhck"].period == "month" and nr.SITEMAPS["bnews"].period == "month" and nr.SITEMAPS["nguoiquansat"].period == "day"


def test_sitemap_url_month_not_zero_padded_and_day_padded():
    assert nr.sitemap_url("tinnhanhck", "2026-09") == "https://www.tinnhanhchungkhoan.vn/sitemaps/news-2026-9.xml"
    assert nr.sitemap_url("bnews", "2026-08") == "https://bnews.vn/sitemap/news-2026-8.xml"
    assert nr.sitemap_url("bnews", "2015-12") == "https://bnews.vn/sitemap/news-2015-12.xml"
    assert nr.sitemap_url("nguoiquansat", "2026-08-05") == "https://nguoiquansat.vn/sitemap-article-2026-08-05.xml"
    with pytest.raises(ValueError):
        nr.sitemap_url("nguoiquansat", "2026-08")          # nguồn ngày cần khoá ngày
    with pytest.raises(ValueError):
        nr.sitemap_url("bnews", "2026-08-05")               # nguồn tháng không nhận khoá ngày


def test_sitemap_article_url_regex_per_source():
    assert nr.SITEMAPS["tinnhanhck"].article_url.search("https://www.tinnhanhchungkhoan.vn/a-post396857.html")
    assert not nr.SITEMAPS["tinnhanhck"].article_url.search("https://www.tinnhanhchungkhoan.vn")
    assert nr.SITEMAPS["bnews"].article_url.search("https://bnews.vn/han-quoc-lap-ky-luc/435658.html")
    assert not nr.SITEMAPS["bnews"].article_url.search("https://bnews.vn/photo/trang-1.html")
    assert nr.SITEMAPS["nguoiquansat"].article_url.search("https://nguoiquansat.vn/bidv-tung-goi-vay-314417.html")
    assert not nr.SITEMAPS["nguoiquansat"].article_url.search("https://nguoiquansat.vn/")
```

Sửa `test_parse_sitemap_drops_homepage_entry_and_keeps_lastmod` (dòng 117): `_src("tinnhanhck", "tnck_sitemap", "sitemap", None)` → `_src("tinnhanhck", "sitemap", "sitemap", None)`.

- [ ] **Step 2: Chạy thấy đỏ**

```bash
PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e52_news_parse.py -q -k "registry_55 or sitemap_url or article_url_regex"
```
Expected: 3 FAIL — `AttributeError: module 'etl.news_registry' has no attribute 'SITEMAPS'` / `len(s) == 55` sai (53).

- [ ] **Step 3: feeds.json — thêm hai dòng `crawl_html`, `_meta`**

Trong `docs/10-sources/news/feeds.json`, sau dòng `crawl_html` của `tinnhanhck` sitemap, thêm hai object (giữ đúng kiểu key hiện có, không dấu tiếng Việt trong key):

```json
{"nguon": "bnews", "url": "https://bnews.vn/sitemap/news-{Y}-{M}.xml", "nhom_mac_dinh": null, "chi_backfill": true,
 "ghi_chu": "Chi backfill (lat 8b), khong poll trong collect (da co 8 feed RSS). Sitemap thang, M KHONG dem 0, 3 phan tu dau la trang chu/photo/video, giam dan, lastmod = gio dang (do 2026-09-06: khop feed 20/20, ld+json 3/3). Lui toi 2015-08, ~4.000 bai/thang."},
{"nguon": "nguoiquansat", "url": "https://nguoiquansat.vn/sitemap-article-{YYYY-MM-DD}.xml", "nhom_mac_dinh": null, "chi_backfill": true,
 "ghi_chu": "Chi backfill (lat 8b). Sitemap theo NGAY tu 2021-07-16, khong co phan tu trang chu, giam dan, lastmod = gio dang (do 2026-09-06). WAF 403 chap chon khong theo UA (5/12 lan dau, retry qua) - de Fetcher retry. 25-200 bai/ngay."}
```

`_meta`: `"crawl_html": 8`, `"cap_nhat": "2026-09-06"`, `"trang_thai"` thêm `"; lat 8b: backfill sitemap BNews + NguoiQuanSat (2026-09-06)"`. Giữ JSON hợp lệ: `python -c "import json;json.load(open('docs/10-sources/news/feeds.json',encoding='utf-8'))"` từ gốc repo.

- [ ] **Step 4: Viết registry**

Thay toàn bộ `backend/etl/news_registry.py` (giữ docstring đầu, cập nhật "6 nguồn crawl" → "8 nguồn crawl (3 sitemap: TinnhanhCK vá lỗ, BNews/NguoiQuanSat chỉ backfill — lát 8b)"):

```python
KINDS = ("rss", "cafef_cbtt", "tnck_category", "sitemap", "bcp_list")
GROUP_KEYS = (("1_vi_mo_trong_nuoc", 1), ("2_tai_chinh_quoc_te", 2), ("3_doanh_nghiep_niem_yet", 3))


@dataclass(frozen=True)
class SitemapSpec:
    period: str                 # 'month' | 'day' — đơn vị một file sitemap
    url: str                    # mẫu format: {y} {m} (không đệm 0 — đo 2026-09-05/06) hoặc {y:04d}-{m:02d}-{d:02d}
    article_url: re.Pattern     # <loc> khớp mới là bài; trang chủ/photo/video/category rơi hết vào đây (spec 8b §4.2-VI)


# Chủ duy nhất của hình dạng sitemap từng nguồn (đo 2026-09-05 TNCK, 2026-09-06 BNews/NQS — measure-sitemap-bnews-nqs-2026-09-06.md).
SITEMAPS: dict[str, SitemapSpec] = {
    "tinnhanhck": SitemapSpec("month", "https://www.tinnhanhchungkhoan.vn/sitemaps/news-{y}-{m}.xml", re.compile(r"-post\d+\.html$")),
    "bnews": SitemapSpec("month", "https://bnews.vn/sitemap/news-{y}-{m}.xml", re.compile(r"/\d+\.html$")),
    "nguoiquansat": SitemapSpec("day", "https://nguoiquansat.vn/sitemap-article-{y:04d}-{m:02d}-{d:02d}.xml", re.compile(r"-\d+\.html$")),
}
MONTH_KEY = re.compile(r"^\d{4}-\d{2}$")
DAY_KEY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class Source:
    name: str
    kind: str
    url: str
    group_from_feed: int | None
    feed_slug: str
    backfill_only: bool = False   # 8b: chỉ dùng ở --backfill-sitemap, collect bỏ qua (feeds.json chi_backfill)


def _crawl_kind(nguon: str, url: str) -> str:
    if nguon == "cafef":
        return "cafef_cbtt"
    if nguon == "baochinhphu":
        return "bcp_list"
    return "sitemap" if "sitemap" in url else "tnck_category"


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
        slug = {"cafef_cbtt": "cbtt", "bcp_list": "chi-dao-dieu-hanh", "sitemap": "sitemap"}.get(kind) or _slug(c["url"])
        if kind == "sitemap":
            if c["nguon"] not in SITEMAPS:
                raise RegistryError(f"feeds.json khai sitemap cho {c['nguon']!r} nhưng SITEMAPS không có mẫu")
            url = SITEMAPS[c["nguon"]].url     # M5: mẫu {y}-{m}, không phải literal năm cứng của feeds.json
        else:
            url = c["url"]
        out.append(Source(c["nguon"], kind, url, c.get("nhom_mac_dinh"), slug, bool(c.get("chi_backfill", False))))
    # C1 (spec lát 8 §4.6-III): chuyên mục trước, sitemap sau — sitemap chỉ vá lỗ, không được thắng bản có nhóm.
    out = [s for s in out if s.kind != "sitemap"] + [s for s in out if s.kind == "sitemap"]
    meta = d["_meta"]
    n_rss = sum(1 for s in out if s.kind == "rss")
    if n_rss != meta["feed_rss"] or len(out) - n_rss != meta["crawl_html"]:
        raise RegistryError(f"feeds.json: {n_rss} feed / {len(out) - n_rss} crawl != _meta {meta['feed_rss']} / {meta['crawl_html']}")
    return out


def sitemap_url(source: str, key: str) -> str:
    """URL file sitemap của một kỳ: key 'YYYY-MM' cho nguồn tháng, 'YYYY-MM-DD' cho nguồn ngày."""
    spec = SITEMAPS[source]
    if spec.period == "month":
        if not MONTH_KEY.match(key):
            raise ValueError(f"{source}: khoá tháng phải dạng YYYY-MM, nhận {key!r}")
        return spec.url.format(y=int(key[:4]), m=int(key[5:7]))
    if not DAY_KEY.match(key):
        raise ValueError(f"{source}: khoá ngày phải dạng YYYY-MM-DD, nhận {key!r}")
    return spec.url.format(y=int(key[:4]), m=int(key[5:7]), d=int(key[8:10]))
```

Xoá `SITEMAP` và `sitemap_url(now_vn)` cũ; xoá `from datetime import datetime` nếu không còn dùng.

- [ ] **Step 5: Đổi tên kind ở ba chỗ dùng (chỉ đủ để test xanh, Task 4 mới viết lại backfill)**

`backend/etl/news_parse.py:218`: `"tnck_sitemap": parse_sitemap` → `"sitemap": parse_sitemap`.

`backend/etl/news_job.py` trong `collect` (dòng 89–91):
```python
            if s.backfill_only:                                   # 8b: BNews/NguoiQuanSat sitemap chỉ dùng ở backfill
                continue
            if s.kind == "sitemap" and cycle % SITEMAP_EVERY != 0:
                continue
            url = news_registry.sitemap_url(s.name, now_vn.strftime("%Y-%m")) if s.kind == "sitemap" else s.url
```
dòng 103: `"text" if s.kind in ("rss", "sitemap") else "html"`.

`backend/etl/news_job.py` trong `backfill_sitemap` (tạm, Task 4 thay hẳn): dòng 290 `news_registry.Source("tinnhanhck", "sitemap", news_registry.SITEMAPS["tinnhanhck"].url, None, "sitemap")`; dòng 301 `f.fetch_one(news_registry.sitemap_url("tinnhanhck", ym), f"sitemap {ym}")`; dòng 302 `PARSERS["sitemap"]`.

- [ ] **Step 6: Chạy xanh e52 + toàn bộ news**

```bash
PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e52_news_parse.py tests/etl/test_e56_news_job.py tests/etl/test_e57_news_backfill.py -q
```
Expected: PASS toàn bộ (e56 `lists_ok == 53` vẫn đúng vì hai nguồn `backfill_only` bị bỏ; e57 vẫn xanh vì fake `get` khớp `/sitemaps/news-`).

- [ ] **Step 7: Commit**

```bash
git add backend/etl/news_registry.py backend/etl/news_parse.py backend/etl/news_job.py docs/10-sources/news/feeds.json backend/tests/etl/test_e52_news_parse.py
git commit -m "feat(etl): news registry — SITEMAPS per source (month/day, article regex), kind sitemap + backfill_only, feeds.json 8 crawl"
```

---

### Task 2: `parse_sitemap` theo nguồn

**Files:**
- Modify: `backend/etl/news_parse.py:26` (`POST_URL` giữ cho `parse_tnck_category`), `:146-168` (`parse_sitemap`), docstring đầu file
- Test: `backend/tests/etl/test_e52_news_parse.py`

**Interfaces:**
- Consumes: `news_registry.SITEMAPS[src.name].article_url` (Task 1).
- Produces: `parse_sitemap(text: str, src: Source) -> list[Item]` với `Item.source == Item.rule == src.name`, `feed_slug == "sitemap"`, `group_from_feed None`, `published_at` từ `lastmod` (VN), `published_at_src 'feed'`.

- [ ] **Step 1: Test đỏ**

Thêm vào `test_e52_news_parse.py`:

```python
def test_parse_sitemap_bnews_drops_home_photo_video_by_regex():
    # Fixture cắt từ https://bnews.vn/sitemap/news-2026-9.xml (đo 2026-09-06): 3 phần tử đầu không phải bài + 5 bài, giảm dần.
    items = np_.parse_sitemap((FIX / "sitemap-bnews-2026-9.xml").read_text(encoding="utf-8"), _src("bnews", "sitemap", "sitemap", None))
    assert len(items) == 5
    assert items[0].url == "https://bnews.vn/lich-thi-dau-va-truc-tiep-ngoai-hang-anh-arsenal-vs-chelsea-luc-22h30-ngay-6-9/435626.html"
    assert items[0].published_at == datetime(2026, 9, 6, 5, 30, 0, tzinfo=VN) and items[0].published_at_src == "feed"
    assert items[-1].url == "https://bnews.vn/le-hoi-den-long-viet-nam-thu-hut-5-000-nguoi-tai-australia/435662.html"
    assert items[-1].published_at == datetime(2026, 9, 5, 22, 5, 14, tzinfo=VN)
    assert all(it.source == "bnews" and it.rule == "bnews" and it.feed_slug == "sitemap" and it.group_from_feed is None for it in items)
    assert not any("/photo/" in it.url or "/video/" in it.url or it.url == "https://bnews.vn" for it in items)


def test_parse_sitemap_nguoiquansat_day_file_with_image_extension():
    # Fixture cắt từ sitemap-article-2026-09-05.xml (đo 2026-09-06): không có phần tử trang chủ, có <image:image>, giảm dần.
    items = np_.parse_sitemap((FIX / "sitemap-nguoiquansat-2026-09-05.xml").read_text(encoding="utf-8"), _src("nguoiquansat", "sitemap", "sitemap", None))
    assert len(items) == 5
    assert items[0].url.endswith("-du-kien-hoat-dong-nam-2027-314422.html") and items[0].published_at == datetime(2026, 9, 5, 23, 48, 1, tzinfo=VN)
    assert items[4].url.endswith("-cho-khach-hang-mua-nha-314417.html") and items[4].published_at == datetime(2026, 9, 5, 23, 4, 1, tzinfo=VN)
    assert items[0].source == "nguoiquansat" and items[0].rule == "nguoiquansat" and items[0].canonical_url == items[0].url


def test_parse_sitemap_unknown_source_is_a_registry_bug_not_silent():
    with pytest.raises(KeyError):
        np_.parse_sitemap("<urlset></urlset>", _src("cafef", "sitemap", "sitemap", None))
```

- [ ] **Step 2: Chạy thấy đỏ**

```bash
PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e52_news_parse.py -q -k "parse_sitemap"
```
Expected: BNews FAIL `ParseError: sitemap: 0 URL bài` (regex `-post` không khớp); NQS FAIL cùng lý do; unknown-source FAIL (không raise KeyError).

- [ ] **Step 3: Viết `parse_sitemap`**

```python
def parse_sitemap(text: str, src: Source) -> list[Item]:
    """8b: lọc <loc> bằng regex URL bài của nguồn (SITEMAPS) — trang chủ (TNCK), trang chủ/photo/video (BNews) rơi hết;
    NguoiQuanSat không có phần tử thừa. Item mang source = rule = src.name."""
    spec = SITEMAPS[src.name]                                   # KeyError = registry khai sitemap cho nguồn không có mẫu (bug cấu hình)
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
        if not spec.article_url.search(loc):
            continue
        mod = (u.findtext(tag("lastmod"), namespaces=ns) or "").strip()
        try:
            pub = datetime.fromisoformat(mod).astimezone(VN)
            psrc = "feed"
        except ValueError:
            pub, psrc = None, "unknown"
        out.append(Item(src.name, "sitemap", loc, canonical_url(loc), "", None, pub, psrc, None, None, src.name))
    if not out:
        raise ParseError("sitemap: 0 URL bài")
    return out
```

Import: `from etl.news_registry import SITEMAPS, Source`. Docstring đầu file: thay câu "sitemap TinnhanhCK phần tử đầu là trang chủ…" bằng "sitemap: phần tử không phải bài (trang chủ TNCK; trang chủ/photo/video BNews) lọc bằng regex theo nguồn — lát 8b". Lưu ý `<image:image>` nằm trong namespace khác, `findall(tag("url"))` không bị ảnh hưởng.

- [ ] **Step 4: Chạy xanh**

```bash
PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e52_news_parse.py -q
```
Expected: PASS, kể cả test TNCK cũ (244 item).

- [ ] **Step 5: Commit**

```bash
git add backend/etl/news_parse.py backend/tests/etl/test_e52_news_parse.py backend/tests/etl/fixtures/news/sitemap-bnews-2026-9.xml backend/tests/etl/fixtures/news/sitemap-nguoiquansat-2026-09-05.xml
git commit -m "feat(etl): parse_sitemap per source — article-URL regex from SITEMAPS, BNews/NguoiQuanSat fixtures"
```

---

### Task 3: Rule NguoiQuanSat nhận template cũ; kiểm rule BNews trên bài 2020

**Files:**
- Modify: `backend/etl/news_extract.py:64-66` (rule `nguoiquansat`), dòng docstring của `Rule.title`/`Rule.time`
- Test: `backend/tests/etl/test_e53_news_extract.py`

**Interfaces:**
- Produces: `extract(html, "nguoiquansat")` trả tiêu đề/giờ từ `h1.c-detail-head__title` / `span.c-detail-head__time` khi template mới vắng mặt.

- [ ] **Step 1: Test đỏ**

Thêm vào `test_e53_news_extract.py`:

```python
def test_nguoiquansat_old_template_2024_title_time_and_body():
    # Template cũ (bài ≤ ~2024, đo 2026-09-06): không có sc-longform-header; tiêu đề h1.c-detail-head__title,
    # giờ span.c-detail-head__time '15-01-2024 13:04'; container article.entry và rác div.c-box vẫn đúng.
    x = ne.extract((FIX / "article-nguoiquansat-2024.html").read_text(encoding="utf-8"), "nguoiquansat")
    assert x.title == "Đây là những tấm hộ chiếu quyền lực nhất thế giới năm 2024"
    assert x.published_at == datetime(2024, 1, 15, 13, 4, tzinfo=VN)
    assert x.sapo is None
    assert x.content.startswith("Đã có một “sự rung chuyển” trong thế giới hộ chiếu.")
    assert x.content.endswith("nhưng chỉ 15% công dân muốn sở hữu")
    assert len(x.content) == 2387
    assert "Theo Kiến thức Đầu tư" not in x.content and "ads_after_sapo" not in x.content


def test_bnews_old_template_2020_still_extracts():
    # Rule bnews không đổi ở 8b — chốt bằng bài 2020 (169672) để backfill lịch sử có bằng chứng (spec 8b A3).
    x = ne.extract((FIX / "article-bnews-2020.html").read_text(encoding="utf-8"), "bnews")
    assert x.title == "Thị trường chứng khoán Mỹ tăng điểm trong phiên 14/9"
    assert x.content.startswith("Trong phiên giao dịch ngày 14/9, thị trường chứng khoán Phố Wall (Mỹ) tăng điểm")
    assert x.content.endswith("61 mã đứng giá và 59 mã giảm giá.")
    assert len(x.content) == 1844 and x.published_at is None
```

- [ ] **Step 2: Chạy thấy đỏ**

```bash
PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e53_news_extract.py -q -k "old_template"
```
Expected: NQS FAIL `ExtractError: nguoiquansat: không thấy h1.sc-longform-header-title`; BNews PASS ngay (rule đã đúng — đó là test hồi quy, chấp nhận xanh từ đầu và ghi nhận trong commit).

- [ ] **Step 3: Sửa rule**

```python
    "nguoiquansat": Rule("article.entry", "h1.sc-longform-header-title, h1.c-detail-head__title",     # 8b: template cũ (≤ 2024)
                         ("div.sc-longform-header", "div.sc-hightlight-box", "div.c-box", "figure", "figcaption", "div.sc-empty-layer", "table"),
                         sapo="p.sc-longform-header-sapo", time="span.sc-longform-header-date, span.c-detail-head__time",
                         time_fmt=("%d/%m/%Y - %H:%M", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M")),
```
Docstring `Rule.title`: thêm comment `# selector CSS, cho phép danh sách "a, b" — select_one lấy phần tử đầu theo thứ tự tài liệu`. `time` tương tự.

- [ ] **Step 4: Chạy xanh e53 toàn bộ**

```bash
PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e53_news_extract.py -q
```
Expected: PASS (test `test_nguoiquansat_drops_header_block` template mới không đổi kết quả).

- [ ] **Step 5: Commit**

```bash
git add backend/etl/news_extract.py backend/tests/etl/test_e53_news_extract.py backend/tests/etl/fixtures/news/article-nguoiquansat-2024.html backend/tests/etl/fixtures/news/article-bnews-2020.html
git commit -m "feat(etl): nguoiquansat rule accepts old template (c-detail-head), bnews 2020 regression fixture"
```

---

### Task 4: `backfill_sitemap` theo nguồn — `periods_desc`, job name, con trỏ riêng

**Files:**
- Modify: `backend/etl/news_job.py:26` (`JOB_BACKFILL`), `:255-350` (`months_desc`, `load_cursor`, `_prev_month`, `backfill_sitemap`), `:353-395` (`run_backfill`), docstring đầu file
- Test: `backend/tests/etl/test_e57_news_backfill.py`, `backend/tests/etl/test_e55_news_store.py:198` (chuỗi job)

**Interfaces:**
- Consumes: `news_registry.SITEMAPS`, `sitemap_url(source, key)` (Task 1); `PARSERS["sitemap"]` (Task 2).
- Produces:
  - `job_name(source: str) -> str` = `f"news.backfill_sitemap:{source}"`; `LEGACY_JOB = "news.backfill_sitemap"`.
  - `periods_desc(source: str, from_month: str, to_month: str, today: date | None = None) -> list[str]` — tháng: `["2026-09","2026-08",…]`; ngày: `["2026-08-31",…,"2026-08-01"]`, không vượt `today` (mặc định hôm nay VN).
  - `load_cursor(engine, source: str) -> str | None`.
  - `backfill_sitemap(engine, source, from_month, to_month, *, run_id, max_minutes, stop_before_open, get, sleep, now, rng, clock) -> dict` với stats `{"source", "period_unit", "cursor", "periods_done", "periods_failed", "period", "urls_in_sitemap", "skipped_seen", "skipped_refused", "articles_ok", "articles_failed", "refused", "budget_hit", "calls", "retries", "stop_at"}`.
  - `run_backfill(from_month, to_month=None, max_minutes=None, stop_before_open=False, source="tinnhanhck", get=None, sleep=time.sleep, now=None, rng=None, clock=time.monotonic) -> int`.
  - `months_desc` **bị xoá** (thay bằng `periods_desc`).

- [ ] **Step 1: Test đỏ — sửa e57 và e55**

`test_e55_news_store.py:198`: `{"j": "news.backfill_sitemap"}` → `{"j": "news.backfill_sitemap:tinnhanhck"}`.

Trong `test_e57_news_backfill.py`:
- `_last(engine)`: `WHERE job='news.backfill_sitemap'` → `WHERE job='news.backfill_sitemap:tinnhanhck'`.
- Thay `test_months_desc_and_cursor_resume` bằng:

```python
def test_periods_desc_month_and_day():
    from datetime import date
    assert nj.periods_desc("tinnhanhck", "2026-07", "2026-09") == ["2026-09", "2026-08", "2026-07"]
    assert nj.periods_desc("bnews", "2025-11", "2026-01") == ["2026-01", "2025-12", "2025-11"]
    d = nj.periods_desc("nguoiquansat", "2026-08", "2026-08", today=date(2026, 9, 6))
    assert len(d) == 31 and d[0] == "2026-08-31" and d[-1] == "2026-08-01" and d == sorted(d, reverse=True)
    assert len(nj.periods_desc("nguoiquansat", "2026-02", "2026-03", today=date(2026, 9, 6))) == 59      # 2026 không nhuận
    # tháng hiện tại: không sinh ngày tương lai
    assert nj.periods_desc("nguoiquansat", "2026-09", "2026-09", today=date(2026, 9, 6))[0] == "2026-09-06"
    assert nj.periods_desc("nguoiquansat", "2026-10", "2026-10", today=date(2026, 9, 6)) == []
    with pytest.raises(ValueError):
        nj.periods_desc("bnews", "2026-9", "2026-09")
```

- Sửa `test_cursor_resumes_from_month_before_last_done`: `nj.load_cursor(clean)` → `nj.load_cursor(clean, "tinnhanhck")` (giữ mọi assert khác: months `["2026-9","2026-8","2026-7"]`, cursor `"2026-07"`, lượt hai `["2026-6","2026-5"]`).
- Thêm:

```python
BN = ('<?xml version="1.0" encoding="utf-8" ?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
      '<url><loc>https://bnews.vn</loc><lastmod>2026-09-05T22:57:40Z</lastmod></url>'
      '<url><loc>https://bnews.vn/photo/trang-1.html</loc><lastmod>2026-09-05T22:57:40Z</lastmod></url>'
      '<url><loc>https://bnews.vn/video/trang-1.html</loc><lastmod>2026-09-05T22:57:40Z</lastmod></url>'
      '<url><loc>https://bnews.vn/a/435003.html</loc><lastmod>2026-08-31T21:00:00+07:00</lastmod></url>'
      '<url><loc>https://bnews.vn/b/435002.html</loc><lastmod>2026-08-15T09:00:00+07:00</lastmod></url>'
      '<url><loc>https://bnews.vn/c/435001.html</loc><lastmod>2026-08-01T05:30:00+07:00</lastmod></url></urlset>')
NQ = ('<?xml version="1.0" encoding="utf-8"?><urlset xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
      '<url><loc>https://nguoiquansat.vn/x-{d}01.html</loc><image:image><image:loc>https://nqs.1cdn.vn/a.jpg</image:loc></image:image><lastmod>2026-08-{d}T23:00:01+07:00</lastmod></url>'
      '<url><loc>https://nguoiquansat.vn/y-{d}02.html</loc><lastmod>2026-08-{d}T08:00:01+07:00</lastmod></url></urlset>')


def _get_src(seen=None, fail=()):
    """Fake get cho ba nguồn: sitemap theo URL mẫu, trang bài dựng theo RULES của nguồn (×9 để qua sàn 5 KB)."""
    def get(u, timeout):
        if "bnews.vn/sitemap/news-" in u:
            if seen is not None:
                seen.append(u.rsplit("news-", 1)[1].replace(".xml", ""))
            return 200, BN, {}
        if "nguoiquansat.vn/sitemap-article-" in u:
            d = u.rsplit("-", 1)[1].replace(".xml", "")
            if seen is not None:
                seen.append(d)
            return 200, NQ.replace("{d}", d), {}
        if "/sitemaps/news-" in u:
            if seen is not None:
                seen.append(u.rsplit("news-", 1)[1].replace(".xml", ""))
            return 200, SM, {}
        if any(f in u for f in fail):
            return 403, "<html>Access Denied..</html>", {}
        rule = "bnews" if "bnews.vn" in u else "nguoiquansat" if "nguoiquansat.vn" in u else "tinnhanhck"
        return 200, _page(rule, "Bài " + u.rsplit("/", 1)[1]) * 9, {}
    return get


def _last_of(engine, source):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats FROM ops.etl_run WHERE job=:j ORDER BY run_id DESC LIMIT 1"),
                         {"j": f"news.backfill_sitemap:{source}"}).one()


def test_backfill_bnews_month_skips_non_articles_and_seen_and_sets_own_cursor(clean):
    with clean.begin() as c:
        aid = c.execute(sa.text("INSERT INTO news.article (canonical_url, primary_source, fetched_at) VALUES ('https://bnews.vn/b/435002.html','bnews',now()) RETURNING article_id")).scalar()
        c.execute(sa.text("INSERT INTO news.article_source (article_id, source_name, url) VALUES (:a,'bnews','https://bnews.vn/b/435002.html')"), {"a": aid})
    months = []
    assert nj.run_backfill("2026-08", "2026-08", source="bnews", get=_get_src(months), sleep=lambda s: None, now=NOW) == 0
    assert months == ["2026-8"]
    status, stats = _last_of(clean, "bnews")
    assert status == "success" and stats["source"] == "bnews" and stats["period_unit"] == "month"
    assert stats["urls_in_sitemap"] == 3 and stats["skipped_seen"] == 1 and stats["articles_ok"] == 2 and stats["articles_failed"] == 0
    assert stats["periods_done"] == ["2026-08"] and stats["cursor"] == "2026-08" and stats["periods_failed"] == []
    assert _n(clean, "SELECT count(*) FROM news.article WHERE primary_source='bnews' AND feed='sitemap' AND group_from_feed IS NULL") == 3
    assert _n(clean, "SELECT published_at FROM news.article WHERE canonical_url='https://bnews.vn/c/435001.html'") == datetime(2026, 8, 1, 5, 30, tzinfo=VN)
    assert _n(clean, "SELECT published_at_src FROM news.article WHERE canonical_url='https://bnews.vn/c/435001.html'") == "feed"
    assert _n(clean, "SELECT count(*) FROM news.article_source WHERE source_name='bnews'") == 3
    assert nj.load_cursor(clean, "bnews") == "2026-08" and nj.load_cursor(clean, "tinnhanhck") is None and nj.load_cursor(clean, "nguoiquansat") is None


def test_backfill_nguoiquansat_walks_days_desc_and_cursor_is_a_day(clean):
    from datetime import date
    days = []
    assert nj.run_backfill("2026-08", "2026-08", source="nguoiquansat", get=_get_src(days), sleep=lambda s: None, now=NOW) == 0
    assert days[0] == "2026-08-31" and days[-1] == "2026-08-01" and len(days) == 31
    status, stats = _last_of(clean, "nguoiquansat")
    assert status == "success" and stats["period_unit"] == "day" and stats["cursor"] == "2026-08-01" and len(stats["periods_done"]) == 31
    assert stats["articles_ok"] == 62 and stats["urls_in_sitemap"] == 62
    assert _n(clean, "SELECT count(*) FROM news.article WHERE primary_source='nguoiquansat'") == 62
    # lượt hai cùng tham số: con trỏ đã ở ngày 1 ⇒ không còn kỳ nào — không mở etl_run mới, exit 0
    n_runs = _n(clean, "SELECT count(*) FROM ops.etl_run WHERE job='news.backfill_sitemap:nguoiquansat'")
    assert nj.run_backfill("2026-08", "2026-08", source="nguoiquansat", get=_get_src(), sleep=lambda s: None, now=NOW) == 0
    assert _n(clean, "SELECT count(*) FROM ops.etl_run WHERE job='news.backfill_sitemap:nguoiquansat'") == n_runs


def test_day_budget_resumes_from_day_before_cursor(clean):
    ticks = iter([0.0] * 10 + [10 * 60.0] * 500)            # ~4 bài rồi hết 5 phút (mỗi URL kiểm clock sau khi xong)
    assert nj.run_backfill("2026-08", "2026-08", source="nguoiquansat", max_minutes=5, get=_get_src(), sleep=lambda s: None, now=NOW, clock=lambda: next(ticks)) == 0
    status, stats = _last_of(clean, "nguoiquansat")
    assert status == "success" and stats["budget_hit"] is True and 1 <= len(stats["periods_done"]) <= 5
    cur = stats["cursor"]
    assert cur is not None and cur.startswith("2026-08-")
    days = []
    assert nj.run_backfill("2026-08", "2026-08", source="nguoiquansat", get=_get_src(days), sleep=lambda s: None, now=NOW) == 0
    assert days[0] < cur and days[-1] == "2026-08-01" and cur not in days    # nối sau con trỏ, không lặp ngày đã xong


def test_day_sitemap_403_after_retries_is_periods_failed_not_cursor(clean):
    def get(u, timeout):
        if "sitemap-article-2026-08-30" in u:
            return 403, "<html>Access Denied..</html>", {}
        return _get_src()(u, timeout)
    assert nj.run_backfill("2026-08", "2026-08", source="nguoiquansat", get=get, sleep=lambda s: None, now=NOW) == 0
    status, stats = _last_of(clean, "nguoiquansat")
    assert status == "success" and stats["periods_failed"] == ["2026-08-30"] and "2026-08-30" not in stats["periods_done"]
    assert stats["cursor"] == "2026-08-01" and stats["articles_ok"] == 60


def test_tinnhanhck_cursor_falls_back_to_legacy_job_name(clean):
    with clean.begin() as c:
        c.execute(sa.text("INSERT INTO ops.etl_run (job, started_at, finished_at, status, stats) VALUES ('news.backfill_sitemap', now(), now(), 'success', '{\"cursor\": \"2026-08\"}'::jsonb)"))
    assert nj.load_cursor(clean, "tinnhanhck") == "2026-08"
    assert nj.load_cursor(clean, "bnews") is None
    months = []
    assert nj.run_backfill("2026-07", "2026-09", get=_get_src(months), sleep=lambda s: None, now=NOW) == 0
    assert months == ["2026-7"]                                             # nối sau con trỏ cũ 2026-08 của lát 8
    with clean.begin() as c:
        c.execute(sa.text("INSERT INTO ops.etl_run (job, started_at, finished_at, status, stats) VALUES ('news.backfill_sitemap:tinnhanhck', now(), now(), 'success', '{\"cursor\": \"2026-05\"}'::jsonb)"))
    assert nj.load_cursor(clean, "tinnhanhck") == "2026-05"                  # run_id lớn hơn thắng, bất kể tên


def test_unknown_source_returns_2_without_a_run(clean):
    assert nj.run_backfill("2026-08", "2026-08", source="cafef", get=_get_src(), sleep=lambda s: None, now=NOW) == 2
    assert _n(clean, "SELECT count(*) FROM ops.etl_run WHERE job LIKE 'news.backfill_sitemap%'") == 0
```

Kiểm cột `ops.etl_run` trước khi chạy (`INSERT` ở test legacy): `grep -n "etl_run" database/migrations/versions/0008_staging_ops.py` — nếu cột bắt buộc khác (`run_id` serial, `job`, `started_at`, `status`, `stats`, `finished_at`, `error`), sửa câu INSERT cho khớp; không có cột nào ngoài các cột đó là NOT NULL không default.

- [ ] **Step 2: Chạy thấy đỏ**

```bash
PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e57_news_backfill.py -q
```
Expected: FAIL — `AttributeError: periods_desc`; `run_backfill() got an unexpected keyword argument 'source'`; `load_cursor() takes 1 positional argument`.

- [ ] **Step 3: Viết lại phần backfill của `news_job.py`**

Thay từ `JOB_BACKFILL = …` (dòng 26) và khối `months_desc` … `run_backfill`:

```python
LEGACY_JOB = "news.backfill_sitemap"          # lát 8: chỉ TinnhanhCK, một job — 8b đọc thêm để không mất con trỏ


def job_name(source: str) -> str:
    return f"news.backfill_sitemap:{source}"
```

```python
def periods_desc(source: str, from_month: str, to_month: str, today: date | None = None) -> list[str]:
    """Khoá kỳ đi LÙI: nguồn tháng 'YYYY-MM'; nguồn ngày 'YYYY-MM-DD' mọi ngày của các tháng đó, không vượt hôm nay (VN)."""
    if not (MONTH.match(from_month) and MONTH.match(to_month)):
        raise ValueError(f"tháng phải dạng YYYY-MM: {from_month!r}, {to_month!r}")
    y, m = int(to_month[:4]), int(to_month[5:])
    months = []
    while f"{y:04d}-{m:02d}" >= from_month:
        months.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    if news_registry.SITEMAPS[source].period == "month":
        return months
    today = today or datetime.now(VN).date()
    out = []
    for ym in months:
        yy, mm = int(ym[:4]), int(ym[5:])
        for dd in range(calendar.monthrange(yy, mm)[1], 0, -1):
            d = date(yy, mm, dd)
            if d <= today:
                out.append(d.isoformat())
    return out


def load_cursor(engine, source: str) -> str | None:
    jobs = [job_name(source)] + ([LEGACY_JOB] if source == "tinnhanhck" else [])
    with engine.connect() as c:
        return c.execute(sa.text(
            "SELECT stats->>'cursor' FROM ops.etl_run WHERE job = ANY(:j) AND stats->>'cursor' IS NOT NULL"
            " ORDER BY run_id DESC LIMIT 1"), {"j": jobs}).scalar()
```

`backfill_sitemap(engine, source, periods, *, run_id, max_minutes, stop_before_open, get, sleep, now, rng, clock)` — nhận **danh sách kỳ đã cắt theo con trỏ** (run_backfill tính), thân hàm như cũ với các thay đổi:

```python
    st = {"source": source, "period_unit": news_registry.SITEMAPS[source].period, "cursor": None, "periods_done": [], "periods_failed": [],
          "period": None, "urls_in_sitemap": 0, "skipped_seen": 0, "skipped_refused": 0, "articles_ok": 0, "articles_failed": 0,
          "refused": 0, "budget_hit": False, "calls": 0, "retries": 0, "stop_at": stop_at.isoformat(timespec="minutes") if stop_at else None}
    ...
        src = news_registry.Source(source, "sitemap", news_registry.SITEMAPS[source].url, None, "sitemap", True)
    ...
            for key in periods:
                st["period"] = key
                try:
                    text = f.fetch_one(news_registry.sitemap_url(source, key), f"sitemap {source} {key}")[1]
                    items = PARSERS["sitemap"](text, src)
                except (news_fetch.BadShape, news_fetch.FetchError, ParseError) as e:
                    st["periods_failed"].append(key)        # I2 lát 8: kỳ hỏng không mất stats/cursor, không đếm vào cầu chì
                    log.warning("%s", e)
                    continue
                ...
                            html_text = f.fetch_one(it.url, source)[1]
                ...
                            ext = news_extract.extract(html_text, it.rule)
                ...
                                news_store.store_refused(c, source, it.url, html_text, e.reason, run_id)
                ...
                st["periods_done"].append(key)
                st["cursor"] = key
```

`run_backfill`:

```python
def run_backfill(from_month, to_month=None, max_minutes=None, stop_before_open=False, source="tinnhanhck",
                 get=None, sleep=time.sleep, now=None, rng=None, clock=time.monotonic) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    load_dotenv()
    now = now or datetime.now(timezone.utc)
    to_month = to_month or now.astimezone(VN).strftime("%Y-%m")
    try:
        if source not in news_registry.SITEMAPS:
            raise ValueError(f"--source phải là một trong {sorted(news_registry.SITEMAPS)}, nhận {source!r}")
        engine = _engine()
        periods = periods_desc(source, from_month, to_month, today=now.astimezone(VN).date())
        cursor = load_cursor(engine, source)
        if cursor and periods and cursor < periods[0]:            # nối sau kỳ đã xong (lùi dần); cursor == kỳ đầu ⇒ chạy lại đúng kỳ đó
            periods = [p for p in periods if p < cursor]
        if not periods:
            log.info("%s: con trỏ %s đã qua --from %s — không còn gì để làm", source, cursor, from_month)
            return 0
    except (RuntimeError, ValueError) as e:
        log.error("%s", e)
        return 2
    run_id = omo_store.open_run(engine, job_name(source))
    try:
        st = backfill_sitemap(engine, source, periods, run_id=run_id, max_minutes=max_minutes, stop_before_open=stop_before_open,
                              get=get, sleep=sleep, now=now, rng=rng, clock=clock)
        ...  # phần còn lại giữ nguyên (close_run success / SourceDown / KeyboardInterrupt / Exception / dispose)
```

Import thêm: `import calendar` và `from datetime import date, datetime, timedelta, timezone`. Xoá `_prev_month` và `months_desc`. Docstring đầu file: thêm "8b: `--backfill-sitemap --source`, kỳ tháng/ngày theo `SITEMAPS`, job `news.backfill_sitemap:<source>` (TinnhanhCK đọc thêm tên cũ)". Lưu ý: khi `periods` rỗng thì **không** `open_run` (test kiểm số dòng `etl_run` không đổi). Trường hợp nguồn tháng chạy lại đúng tháng con trỏ (cursor == periods[0]) giữ hành vi lát 8: chạy lại, `skipped_seen` lo phần còn lại.

- [ ] **Step 4: Chạy xanh e55 + e56 + e57**

```bash
PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e55_news_store.py tests/etl/test_e56_news_job.py tests/etl/test_e57_news_backfill.py -q
```
Expected: PASS toàn bộ. Nếu `test_day_budget_resumes…` lệch vì số tick: chỉnh dãy `ticks` của test (không chỉnh code), ghi rõ trong commit.

- [ ] **Step 5: Commit**

```bash
git add backend/etl/news_job.py backend/tests/etl/test_e57_news_backfill.py backend/tests/etl/test_e55_news_store.py
git commit -m "feat(etl): news backfill per source — periods_desc month/day, job news.backfill_sitemap:<source>, cursor per source with legacy fallback"
```

---

### Task 5: CLI `--source`

**Files:**
- Modify: `backend/etl/__main__.py:81-105`
- Test: `backend/tests/etl/test_e58_news_cli.py`

**Interfaces:**
- Consumes: `news_job.run_backfill(..., source=...)` (Task 4).

- [ ] **Step 1: Test đỏ**

Sửa `test_backfill_flags_and_exclusions`: assert `seen == {"from_month": "2026-08", "to_month": "2026-09", "max_minutes": 30.0, "stop_before_open": True, "source": "tinnhanhck"}`. Thêm:

```python
def test_backfill_source_flag(monkeypatch):
    import etl.news_job
    seen = {}
    monkeypatch.setattr(etl.news_job, "run_backfill", lambda **kw: seen.update(kw) or 0)
    assert m.main(["news", "--backfill-sitemap", "--source", "bnews", "--from", "2026-08", "--to", "2026-08"]) == 0
    assert seen["source"] == "bnews" and seen["from_month"] == "2026-08"
    assert m.main(["news", "--backfill-sitemap", "--source", "nguoiquansat", "--from", "2024-01"]) == 0 and seen["source"] == "nguoiquansat"
    for bad in (["news", "--backfill-sitemap", "--source", "cafef", "--from", "2026-08"],       # không có sitemap
                ["news", "--source", "bnews"],                                                 # --source chỉ đi cùng --backfill-sitemap
                ["news", "--loop", "--source", "bnews"]):
        with pytest.raises(SystemExit) as e:
            m.main(bad)
        assert e.value.code == 2
```

- [ ] **Step 2: Chạy thấy đỏ**

```bash
PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e58_news_cli.py -q
```
Expected: FAIL `unrecognized arguments: --source` (exit 2 ở ca hợp lệ) và `seen` thiếu `source`.

- [ ] **Step 3: Sửa CLI**

Thêm sau `--backfill-sitemap`:
```python
        parser.add_argument("--source", choices=sorted(etl.news_registry.SITEMAPS), default=None,
                            help="nguồn sitemap cho --backfill-sitemap (mặc định tinnhanhck)")
```
(`import etl.news_registry` cạnh `import etl.news_job`). Trong nhánh `if parsed.backfill_sitemap:` truyền `source=parsed.source or "tinnhanhck"` vào `run_backfill`. Nhánh không backfill: thêm `parsed.source is not None` vào điều kiện `parser.error("--to/--max-minutes/--stop-before-open/--source chỉ đi cùng --backfill-sitemap")`.

- [ ] **Step 4: Chạy xanh + toàn bộ bộ test**

```bash
PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e58_news_cli.py -q
PYTHONIOENCODING=utf-8 uv run pytest -q
```
Expected: e58 PASS; toàn bộ ≥ 791 passed (+~12), 2 skipped, 0 failed. Ghi số thật vào commit message.

- [ ] **Step 5: Commit**

```bash
git add backend/etl/__main__.py backend/tests/etl/test_e58_news_cli.py
git commit -m "feat(etl): etl news --source for --backfill-sitemap (tinnhanhck|bnews|nguoiquansat)"
```

---

### Task 6 (controller): nghiệm thu thật — AC2–AC6

Chạy từ `backend/`, credential production (`.env`), **tách tiến trình** cho lượt dài (memory: `Start-Process cmd /c …`, theo dõi qua `ops.etl_run`). `--loop` đang chạy — không mở loop thứ hai.

- [ ] AC2: `etl news --dry-run` ⇒ `lists_ok` 52–53, `sources_total` 55, không lời gọi nào tới `bnews.vn/sitemap` hay `nguoiquansat.vn/sitemap-article` (đếm trong log).
- [ ] AC3 BNews: `etl news --backfill-sitemap --source bnews --from 2026-08 --to 2026-08 --max-minutes 60` lặp tới `cursor == "2026-08"` (≈ 3,5 giờ tổng, nhiều lượt). Sau lượt đầu: đối chiếu 3 bài (`published_at` = `lastmod` = ld+json trên trang), `refused` theo `reason`, `articles_failed`.
- [ ] AC3 NQS: `--source nguoiquansat --from 2026-08 --to 2026-08 --max-minutes 60` lặp tới `cursor == "2026-08-01"`; ghi tỷ lệ `periods_failed`/31 và `articles_failed`/`urls_in_sitemap` (A1: ≤ 5 % sau retry).
- [ ] AC4: `--source nguoiquansat --from 2024-01 --to 2024-01 --max-minutes 10` ⇒ bài template cũ vào kho, `refused` ≈ 0, 3 bài `published_at` khớp `c-detail-head__time`. **Con trỏ NQS sau AC4 sẽ ở 2024-01-xx** — lượt nào sau đó với `--from 2026-08` sẽ báo "không còn gì" — chấp nhận, spec §4.1 không lùi thêm; ghi ledger.
- [ ] AC5: lượt hai BNews cùng tham số ⇒ `articles_ok 0`, `skipped_seen` = tổng; NQS lượt hai ⇒ "không còn gì để làm", không `etl_run` mới; `load_cursor(engine, "tinnhanhck")` trả `2026-08`… của lát 8 (kiểm bằng `--backfill-sitemap --from 2026-08 --to 2026-08 --max-minutes 1` với TNCK ⇒ log nối đúng).
- [ ] AC6: `SELECT primary_source, feed, count(*) FROM news.article WHERE feed='sitemap' GROUP BY 1,2`; `article_source` mỗi bài backfill đúng `source_name`.
- [ ] Ghi tất cả vào `ledger.md` §2 với `run_id`, số, ngày giờ.

---

### Task 7: Tài liệu sống (spec §8) + roadmap

**Files:** `docs/10-sources/news/README.md` (§5 tiêu đề, §5.4, §5.5, "Trạng thái"), `docs/10-sources/news/article-structure.md` (§2.6 dòng kiểm lại, §2.7 template cũ), `docs/20-design/news-pipeline.md` (§9.6, §14 mục 6), `backend/README.md` (mục job news), `docs/00-overview/roadmap.md` (bảng lát: 8b ✅; gạch "Điểm vào cho lát 8b"; việc gấp [5]; số test), `docs/90-records/README.md` (dòng 8b ⇒ ✅), `ledger.md`.

- [ ] Viết nội dung theo đúng số đo trong `measure-sitemap-bnews-nqs-2026-09-06.md` và kết quả Task 6, mỗi số kèm *(đo 2026-09-06)*.
- [ ] Phép kiểm §1.7: `git grep -n "tnck_sitemap\|months_desc\|JOB_BACKFILL\|6 nguồn crawl\|sáu nguồn crawl"` — mọi hit còn lại phải thuộc `90-records/` (lịch sử) hoặc đã đúng.
- [ ] Commit: `docs: slice 8b — BNews/NguoiQuanSat sitemap measured 2026-09-06, backfill per source, roadmap`.

---

## Self-review (đã chạy khi viết plan)

- **Spec coverage:** §3.1 registry → T1; parse → T2; extract → T3; job/cursor/periods → T4; CLI → T5; feeds.json → T1; fixture → T0; AC → T6; §8 → T7. §4.2-V (403 = retry sẵn có) không cần code: `news_fetch.classify` đã trả `retry` cho 403 — T4 có test kỳ 403 ⇒ `periods_failed`.
- **Placeholder scan:** không có TBD/TODO; mọi bước code có code.
- **Type consistency:** `SitemapSpec.period ∈ {'month','day'}`; `sitemap_url(source, key)` dùng ở T1 test, T1 collect, T4; `periods_desc(source, from, to, today)`; `load_cursor(engine, source)`; `run_backfill(..., source=)`; `job_name(source)`; `backfill_sitemap(engine, source, periods, *, …)` — T4 test gọi qua `run_backfill` nên chữ ký nội bộ không lộ ra test.
- **Khác spec một điểm, ghi rõ:** spec §3.1 nói `backfill_sitemap(engine, source, from_month, to_month, …)`; plan chuyển việc tính kỳ + cắt theo con trỏ lên `run_backfill` và truyền `periods` xuống — giữ cấu trúc "run tính con trỏ, hàm lõi chỉ đi qua danh sách" của lát 8, đơn giản hơn cho test. Ledger ghi ruling.
