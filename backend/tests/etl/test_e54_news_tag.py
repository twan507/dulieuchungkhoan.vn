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
