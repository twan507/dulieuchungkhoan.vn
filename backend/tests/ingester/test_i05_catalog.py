import httpx

from ingester.catalog import BASE, Catalog, INDEX_CODES, build_catalog, fetch_derivative_symbols, topics

QUOTES = {"s": "ok", "d": [
    {"symbol": "ACB", "StockType": "2", "ceiling": 23950, "floor": 20850, "reference": 22400, "exchange": "HOSE"},
    {"symbol": "FUEVFVND", "StockType": "3", "ceiling": 30000, "floor": 26000, "reference": 28000, "exchange": "HOSE"},
    {"symbol": "CACB2602", "StockType": "4", "ceiling": 1000, "floor": 800, "reference": 900, "exchange": "HOSE"},
    {"symbol": "HDC425001", "StockType": "12", "ceiling": 0, "floor": 0, "reference": 0, "exchange": "HNX"},
    {"symbol": "VFMVF1", "StockType": "3", "ceiling": 0, "floor": 0, "reference": 12000, "exchange": "UPCOM"},
]}
INSTR = {"s": "ok", "d": [
    {"symbol": "ACB", "open": 22500, "low": 22300, "ceiling": 23950, "floor": 20850,
     "reference": 22400, "FloorCode": "10"},
    {"symbol": "41I1G8000", "open": 1300, "low": 1290, "ceiling": 1400, "floor": 1200,
     "reference": 1310, "FloorCode": "03"},
]}


def _client():
    def handler(request):
        if request.url.path == "/quotes":
            return httpx.Response(200, json=QUOTES)
        if request.url.path == "/datafeed/instruments":
            return httpx.Response(200, json=INSTR)
        return httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(handler), base_url=BASE)


def test_catalog_merges_and_filters():
    cat = build_catalog(client=_client())
    assert cat.symbols == ["ACB", "FUEVFVND", "VFMVF1"]  # CP+ETF; không CW/TP/phái sinh
    assert cat.base_state["ACB"]["open"] == "22500"      # nền từ instruments
    assert cat.base_state["VFMVF1"] == {"ceiling": "0", "floor": "0", "reference": "12000"}


def test_topics_shape():
    cat = Catalog(["ACB"], {})
    t = topics(cat)
    assert set(t[:3]) == {"i:ACB", "o10:ACB", "t:ACB"}   # o10, KHÔNG PHẢI o (bẫy §3)
    assert "idx:HOSE" in t and "idx:FINLEAD" in t
    assert len([x for x in t if x.startswith("idx:")]) == len(INDEX_CODES)
    assert "ptm:UPCOM" in t


def test_fetch_derivative_symbols():
    assert fetch_derivative_symbols(client=_client()) == ["41I1G8000"]
