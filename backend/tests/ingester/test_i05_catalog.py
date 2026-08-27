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
     "reference": 1310, "FloorCode": "03", "tradingdate": "27/08/2026", "Status": "00",
     "MaturityDate": "18/09/2026", "underlyingSymbol": "VN30"},
    # Hợp đồng ĐÃ HẾT HẠN — endpoint vẫn trả, chỉ còn ceiling/floor/reference, không
    # tradingdate/Status (đo 2026-08-26: 61 bản ghi FloorCode=03, chỉ 14 còn sống).
    {"symbol": "VN30F2509", "ceiling": 2004.8, "floor": 1742.6, "reference": 1873.7,
     "FloorCode": "03", "underlyingSymbol": "VN30"},
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
    # CP + ETF + phái sinh CÒN SỐNG; không CW/trái phiếu/hợp đồng hết hạn
    assert cat.symbols == ["41I1G8000", "ACB", "FUEVFVND", "VFMVF1"]
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


def test_expired_derivative_contracts_are_excluded():
    """Đo 2026-08-26: `/datafeed/instruments` trả 61 bản ghi FloorCode=03 nhưng chỉ
    **14 còn sống** — 47 hợp đồng hết hạn vẫn nằm đó, mất `tradingdate`/`Status`,
    chỉ còn giá tham chiếu cũ. Đăng ký chúng là 47×20 topic vô ích."""
    syms = fetch_derivative_symbols(client=_client())
    assert syms == ["41I1G8000"]                 # VN30F2509 (hết hạn) bị loại


def test_catalog_includes_live_derivatives():
    """Run mode phải đăng ký phái sinh thì tick mới được GHI — chúng đi chung ba topic
    `i`/`o10`/`t` với cổ phiếu, cấu trúc trường giống hệt (đo 2026-08-26, 2,3 triệu frame)."""
    cat = build_catalog(client=_client())
    assert "41I1G8000" in cat.symbols
    assert "VN30F2509" not in cat.symbols        # hết hạn thì không
    assert cat.base_state["41I1G8000"]["reference"] == "1310"
