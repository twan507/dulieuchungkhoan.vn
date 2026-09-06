"""Gắn mã tầng 1 (URL CafeF CBTT) và tầng 2 (regex + đối chiếu danh sách niêm yết) — news-pipeline §8."""
from etl import news_tag as nt


def test_url_tier_reads_cafef_cbtt_and_drops_exchanges():
    assert nt.tickers_from_url("https://cafef.vn/du-lieu/SGP-2969587/sgp-bao-cao.chn") == ["SGP"]
    assert nt.tickers_from_url("https://cafef.vn/du-lieu/HNX-2951892/x.chn") == []
    assert nt.tickers_from_url("https://cafef.vn/green-sm-188260905170800678.chn") == []


def test_lookup_tier_requires_listed_and_keeps_order_without_duplicates():
    listed = {"HPG": 1, "SME": 2, "VIC": 3, "GDP": 4}
    assert nt.tickers_lookup("HPG tăng trần, USD và GDP quý III; HPG lập đỉnh", "VIC dẫn dắt", listed) == ["HPG", "VIC"]   # GDP: AMBIGUOUS (2026-09-06)
    assert nt.tickers_lookup("SME công bố kết quả", None, listed) == []            # SME là mã thật nhưng AMBIGUOUS (doanh nghiệp nhỏ và vừa)
    assert nt.tickers_lookup("hpg tăng trần", None, listed) == []                 # chữ thường không phải mã
    assert nt.tickers_lookup("Cổ phiếu ABC1 và AB", None, {"AB": 9, "ABC": 8}) == []   # 2 ký tự và 4 ký tự không khớp \b[A-Z][A-Z0-9]{2}\b


def test_lookup_tier_skips_ambiguous_abbreviations_even_when_listed():
    # Đo 2026-09-06 trên kho thật (470 dòng lookup): USD 25 lần, HCM 20, CEO 7, SEA 3, VND 2, BOT 2, PPP 1 — đều là chữ thường
    # (tiền tệ, TP.HCM, chức danh, chỉ số) trùng mã niêm yết thật. Tầng 2 mù ngữ cảnh nên bỏ hẳn; tầng 3 (AI đọc toàn văn) vẫn gắn được.
    listed = {"USD": 1, "HCM": 2, "CEO": 3, "VND": 4, "HPG": 5, "SME": 6, "WTO": 7}
    assert nt.tickers_lookup("Tỷ giá USD tại TP.HCM; CEO Hoà Phát (HPG) nói về SME và WTO", None, listed) == ["HPG"]
    assert {"USD", "HCM", "CEO", "VND", "SME", "CPI", "AGM", "VN30"} <= nt.AMBIGUOUS
