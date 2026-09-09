"""Registry nguồn tin (spec lát 8 §5.1): 47 feed RSS đọc từ `etl/data/feeds.json` (chủ duy nhất của danh sách feed — dời
từ `docs/` vào code 2026-09-08, lát 12 Task 10a) + 8 nguồn crawl (3 sitemap: TinnhanhCK vá lỗ, BNews/NguoiQuanSat chỉ
backfill — lát 8b); phần "của mình" là tên báo chuẩn, kind, feed_slug, group_from_feed. Số đếm phải khớp `_meta` — lệch là
chết trước fetch (hợp đồng khởi động)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

FEEDS_JSON = Path(__file__).resolve().parent / "data" / "feeds.json"
SOURCES = ("cafef", "vietstock", "vneconomy", "vietnambiz", "bnews", "nguoiquansat", "baochinhphu", "tinnhanhck")
KINDS = ("rss", "cafef_cbtt", "tnck_category", "sitemap", "bcp_list")
GROUP_KEYS = (("1_vi_mo_trong_nuoc", 1), ("2_tai_chinh_quoc_te", 2), ("3_doanh_nghiep_niem_yet", 3))


class RegistryError(Exception):
    """feeds.json lệch với số đếm khai trong _meta hoặc tên báo lạ."""


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
MONTH_KEY = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")                       # cùng luật với news_job.MONTH
DAY_KEY = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")


@dataclass(frozen=True)
class Source:
    name: str
    kind: str
    url: str
    group_from_feed: int | None
    feed_slug: str
    backfill_only: bool = False   # 8b: chỉ dùng ở --backfill-sitemap, collect bỏ qua (feeds.json chi_backfill)


def _slug(url: str) -> str:
    return re.sub(r"\.(rss|html?|chn|xml)$", "", urlparse(url).path.strip("/"))


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
