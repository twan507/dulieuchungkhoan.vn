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
        url = SITEMAP if kind == "tnck_sitemap" else c["url"]     # M5: mẫu {y}-{m}, không phải literal năm cứng của feeds.json
        out.append(Source(c["nguon"], kind, url, c.get("nhom_mac_dinh"), slug))
    # C1 (spec §4.6-III): chuyên mục trước, sitemap sau — sitemap chỉ vá lỗ, không được thắng bản có nhóm.
    # Giữ nguyên thứ tự tương đối còn lại, chỉ đẩy tnck_sitemap xuống cuối.
    out = [s for s in out if s.kind != "tnck_sitemap"] + [s for s in out if s.kind == "tnck_sitemap"]
    meta = d["_meta"]
    n_rss = sum(1 for s in out if s.kind == "rss")
    if n_rss != meta["feed_rss"] or len(out) - n_rss != meta["crawl_html"]:
        raise RegistryError(f"feeds.json: {n_rss} feed / {len(out) - n_rss} crawl != _meta {meta['feed_rss']} / {meta['crawl_html']}")
    return out


def sitemap_url(now_vn: datetime) -> str:
    return SITEMAP.format(y=now_vn.year, m=now_vn.month)
