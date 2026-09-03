import json
import pytest
from etl import events_fetch as ef


def _envelope(total, n, start=0):
    return json.dumps({"totalCount": total,
                       "items": [{"organCode": f"C{start + i}"} for i in range(n)],
                       "status": "Success"})


def test_url_carries_pagesize_20000_and_language():
    seen = []

    def get(url):
        seen.append(url)
        return 200, _envelope(3, 3)

    ef.fetch(get=get, sleep=lambda s: None)
    assert seen[0] == ("https://wlgw-market.fiintrade.vn/Calendar/GetCorporateAGM"
                       "?Page=1&PageSize=20000&language=vi")
    assert len(seen) == 6                      # đúng sáu họ, mỗi họ một trang


def test_pages_until_collected_reaches_total_count():
    calls = {"n": 0}

    def get(url):
        calls["n"] += 1
        # họ đầu cần 2 trang (25.000/20.000), năm họ sau 1 trang
        if "GetCorporateAGM" in url:
            return (200, _envelope(25000, 20000)) if "Page=1" in url else (200, _envelope(25000, 5000, 20000))
        return 200, _envelope(1, 1)

    pages, retries = ef.fetch(get=get, sleep=lambda s: None)
    assert len(pages["AGM"]) == 2 and retries == 0
    assert calls["n"] == 7                     # 2 + 5


def test_retries_then_succeeds_and_counts():
    state = {"fail": 2}

    def get(url):
        if "GetCorporateAGM" in url and state["fail"]:
            state["fail"] -= 1
            return 500, "boom"
        return 200, _envelope(1, 1)

    slept = []
    pages, retries = ef.fetch(get=get, sleep=slept.append)
    assert retries == 2 and slept == [2, 4]


def test_raises_after_all_retries_exhausted():
    def get(url):
        return 500, "boom"

    with pytest.raises(ef.FetchError, match="GetCorporateAGM"):
        ef.fetch(get=get, sleep=lambda s: None)


def test_raises_on_empty_page_before_total_reached():
    def get(url):
        if "Page=1" in url:
            return 200, _envelope(25000, 20000)
        return 200, _envelope(25000, 0, 20000)

    with pytest.raises(ef.FetchError, match="rỗng"):
        ef.fetch(get=get, sleep=lambda s: None)


def test_transport_exception_is_retried_like_a_bad_response_then_succeeds():
    """Cùng lỗi lát 3 vá ở e7f80f6: httpx.ReadTimeout (máy ngủ giữa lời gọi) lọt qua vòng retry
    và giết cả lượt. Exception vận chuyển phải đi cùng đường với response xấu."""
    import httpx
    state = {"fail": 2}

    def get(url):
        if state["fail"]:
            state["fail"] -= 1
            raise httpx.ReadTimeout("The read operation timed out")
        return 200, _envelope(1, 1)

    slept = []
    pages, retries = ef.fetch(get=get, sleep=slept.append)
    assert retries == 2 and slept == [2, 4] and len(pages) == 6


def test_transport_exception_every_time_becomes_a_fetch_error_not_a_crash():
    import httpx

    def get(url):
        raise httpx.ConnectError("[Errno 11001] getaddrinfo failed")

    with pytest.raises(ef.FetchError, match="ConnectError"):
        ef.fetch(get=get, sleep=lambda s: None)
