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
