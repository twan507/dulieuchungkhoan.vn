"""Gắn mã cổ phiếu tầng 1 (URL CafeF CBTT — chắc chắn) và tầng 2 (regex + ĐỐI CHIẾU danh sách niêm yết — news-pipeline §8:
USD/GDP/CPI đều là 3 chữ in hoa, SME lại là mã thật). Chỉ quét tiêu đề + sapo (spec 7b… lát 8 §4.6-I). Thuần."""
from __future__ import annotations

import re

from etl.news_parse import CBTT_HREF, EXCHANGES

TICKER = re.compile(r"\b[A-Z][A-Z0-9]{2}\b")
# Mã niêm yết THẬT nhưng trùng chữ viết tắt thường gặp trong tin — tầng 2 mù ngữ cảnh nên bỏ hẳn (đo 2026-09-06 trên 470 dòng lookup:
# USD 25 · HCM 20 · CEO 7 · SEA 3 · VND 2 · BOT 2 · PPP 1 — toàn bộ là tiền tệ / TP.HCM / chức danh / chỉ số). Tầng 3 (AI đọc toàn văn)
# vẫn gắn được khi bài thật sự nói về doanh nghiệp đó. Thêm mã mới vào đây khi đo thấy false positive, không thêm ngoại lệ ngữ cảnh.
AMBIGUOUS = frozenset({"USD", "EUR", "GBP", "JPY", "CNY", "KRW", "THB", "SGD", "CAD", "AUD", "CHF", "VND", "CPI", "GDP", "PMI", "FDI",
                       "ODA", "IMF", "WTO", "WHO", "ADB", "ETF", "IPO", "ESG", "EVN", "VAT", "BOT", "PPP", "CEO", "CFO", "AGM", "ATC",
                       "ATO", "HCM", "NAV", "API", "SEA", "CNG", "LNG", "POS", "TOP", "NET", "VNX", "ABC", "SME", "OTC", "ROE", "ROA",
                       "EPS", "DXY", "BTC", "ETH", "ECB", "FED", "BOJ", "BOE", "VN30", "HNX30", "VN100"})


def tickers_from_url(url: str) -> list[str]:
    m = CBTT_HREF.search(url)
    if not m or m.group(1) in EXCHANGES:
        return []
    return [m.group(1)]


def tickers_lookup(title: str, sapo: str | None, listed: dict[str, int]) -> list[str]:
    out: list[str] = []
    for tok in TICKER.findall(f"{title or ''} {sapo or ''}"):
        if tok in listed and tok not in AMBIGUOUS and tok not in out:
            out.append(tok)
    return out
