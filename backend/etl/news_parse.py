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
from datetime import datetime
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
        text = raw.decode("utf-16-le", errors="replace")
    else:
        text = raw.decode("utf-8", errors="replace")
    return unicodedata.normalize("NFC", text)               # BNews đo được ở dạng tổ hợp dựng sẵn khác NFC — chuẩn hoá một lần ở nguồn


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
        s = m.group(1)                                     # YYYY + M(1–2, không đệm 0) + D(1–2, không đệm 0) + HHMMSS + serial
        for mlen in (2, 1):
            for dlen in (2, 1):
                try:
                    return datetime(int(s[:4]), int(s[4:4 + mlen]), int(s[4 + mlen:4 + mlen + dlen]),
                                     int(s[4 + mlen + dlen:6 + mlen + dlen]), int(s[6 + mlen + dlen:8 + mlen + dlen]),
                                     int(s[8 + mlen + dlen:10 + mlen + dlen]), tzinfo=VN)
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
        # url = canonical (không phải href thô): href thật kèm ?utm_source=du-lieu — giữ canonical để article_source.url
        # không mang tham số rác (mọi tham chiếu CBTT của cùng bài đổ về đúng MỘT giá trị url, không lệch theo utm).
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
