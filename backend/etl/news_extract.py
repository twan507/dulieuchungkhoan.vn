"""Bóc bài ba tầng (article-structure §1.3, §2, §3): tầng 0 chọn ĐÚNG container; tầng 1 xoá node Comment trước rồi mới lấy
text (BaoChinhPhu giấu dấu thời gian trong comment); tầng 2 bỏ boilerplate theo selector từng nguồn + luật văn bản. Duyệt
text node qua get_text (BNews có template đoạn văn là text node trần — find_all('p') trả 0). Thuần, không I/O.
Chủ của bảng selector là article-structure.md — sửa ở đó trước, chép vào đây sau."""
from __future__ import annotations

import re
import unicodedata
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
                  sapo="p.sapo", time="span.pdate", time_fmt=("%d-%m-%Y - %H:%M %p",)),
    "cafef_cbtt": Rule("div#newscontent", "td.text_noibat_cacbaikhac span.cms_blue", ("div.FileWrapper", "table"), min_chars=0),
    "vietstock": Rule("div#vst_detail", "h1.article-title",
                      ("p.pTitle", "p.pHead", "p.pAuthor", "p.pSource", "p.pPublishTimeSource", "table.img-content", "div.article-sharing"),
                      sapo="p.pHead", time="p.pPublishTimeSource", time_fmt=("- %H:%M %d/%m/%Y",)),
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
    # NFC: trang BNews (template B) trả tiêu đề/thân bài ở dạng NFD (dấu tổ hợp rời) — chuẩn hoá về
    # NFC để so khớp chuỗi (dedupe tiêu đề) không vỡ vì hai cách biểu diễn cùng một ký tự.
    raw = unicodedata.normalize("NFC", node.get_text(" "))
    return _WS.sub(" ", raw).strip()


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
