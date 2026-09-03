import json

import pytest

from etl import price_fetch as pf


def env(n, total=None, start=0, status="Success"):
    return json.dumps({"page": 1, "pageSize": 60, "totalCount": n if total is None else total,
                       "items": [{"tradingDate": f"2026-01-{(start + i) % 28 + 1:02d}T00:00:00"}
                                 for i in range(n)],
                       "packageId": None, "status": status, "errors": None})


INVALID = json.dumps({"page": 1, "pageSize": 60, "totalCount": 0, "items": None, "packageId": None,
                      "status": "Failed", "errors": ["Code not valid: VHM"]})


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


def fetcher(get, latency=1.8):
    """Fetcher với đồng hồ giả TRÔI theo latency mỗi lời gọi (trung vị thật 1,76 s > MIN_INTERVAL 0,5 s
    nên bộ giãn cách không ngủ) — chỉ backoff mới hiện trong `slept`. Đồng hồ đứng yên sẽ làm
    bộ giãn cách ngủ 0,5 s giữa mọi lời gọi và mọi assert về `slept` sai."""
    clock, slept = Clock(), []

    def timed_get(u):
        clock.t += latency
        return get(u)

    return pf.Fetcher(timed_get, sleep=slept.append, clock=clock), slept


def _code(u):
    return u.split("Code=")[1].split("&")[0]


def test_url_carries_organ_code_daily_page_and_size_60():
    assert pf.url("NHN", 2) == ("https://wlgw-technical.fiintrade.vn/PriceData/GetPriceData"
                                "?Code=NHN&Frequently=Daily&Page=2&PageSize=60&language=vi")


def test_status_zero_and_success_are_both_valid_without_retry():
    # Đo 2026-09-03: cùng endpoint trả lẫn 0 (số) và "Success" (chuỗi) — 2/16 lời gọi
    seen = []

    def get(u):
        seen.append(u)
        return 200, env(60, total=120, status=0) if "Page=1" in u else env(60, total=120)

    f, slept = fetcher(get)
    assert len(f.pages("BID", max_pages=None)) == 2
    assert f.retries == 0 and slept == []


def test_code_not_valid_raises_without_retry_or_sleep():
    f, slept = fetcher(lambda u: (200, INVALID))
    with pytest.raises(pf.CodeInvalid, match="VHM"):
        f.pages("VHM")
    assert slept == [] and f.calls == 1


def test_transient_failure_retries_with_backoff_then_succeeds():
    state = {"fail": 2}

    def get(u):
        if state["fail"]:
            state["fail"] -= 1
            return 500, "boom"
        return 200, env(3)

    f, slept = fetcher(get)
    assert len(f.pages("BID")) == 1
    assert f.retries == 2 and slept == [2, 4]


def test_transport_exception_is_retried_like_a_bad_response_then_succeeds():
    """Sự cố 2026-09-04 02:00: máy ngủ giữa lời gọi ⇒ httpx.ReadTimeout lọt qua vòng retry và giết
    cả lượt backfill ở mã ĐẦU TIÊN. Exception vận chuyển phải đi cùng đường với response xấu."""
    import httpx
    state = {"fail": 2}

    def get(u):
        if state["fail"]:
            state["fail"] -= 1
            raise httpx.ReadTimeout("The read operation timed out")
        return 200, env(3)

    f, slept = fetcher(get)
    assert len(f.pages("BID")) == 1
    assert f.retries == 2 and slept == [2, 4]


def test_transport_exception_every_time_becomes_a_fetch_error_not_a_crash():
    import httpx

    def get(u):
        raise httpx.ConnectError("[Errno 11001] getaddrinfo failed")

    f, slept = fetcher(get)
    with pytest.raises(pf.FetchError, match="ConnectError"):
        f.pages("BID")
    assert slept == [2, 4, 8]
    res = f.many(["A", "B"])                          # đường many: mã hỏng vào failed, không ném
    assert res.failed == ["A", "B"] and res.pages == {}


def test_exhausted_retries_raise_fetch_error_naming_code_and_page():
    body = '{"status":"Failed","errors":["Timeout performing GET (5000ms)"]}'   # 00-conventions §10.5
    f, slept = fetcher(lambda u: (200, body))
    with pytest.raises(pf.FetchError, match="BID trang 1"):
        f.pages("BID")
    assert slept == [2, 4, 8]


def test_pagination_stops_at_short_page_and_at_total_count_cap():
    calls = []

    def get(u):
        calls.append(u)
        p = int(u.split("Page=")[1].split("&")[0])
        return 200, env({1: 60, 2: 60, 3: 22}[p], total=142, start=p * 60)

    f, _ = fetcher(get)
    assert len(f.pages("BID", max_pages=None)) == 3 and len(calls) == 3      # 60·60·22, dừng ở trang ngắn

    calls.clear()
    f2, _ = fetcher(lambda u: (calls.append(u), (200, env(60, total=120)))[1])
    assert len(f2.pages("BID", max_pages=None)) == 2 and len(calls) == 2     # trần totalCount: không gọi trang 3 rỗng
    assert len(fetcher(lambda u: (200, env(60, total=3142)))[0].pages("BID", max_pages=1)) == 1


def test_min_interval_between_call_starts_sleeps_the_remainder():
    f, slept = fetcher(lambda u: (200, env(60, total=120)), latency=0.1)   # lời gọi mất 0,1 s
    f.pages("BID", max_pages=None)                    # 2 lời gọi
    assert slept == [pytest.approx(0.4)]              # 0,5 s giữa hai lần BẮT ĐẦU ⇒ ngủ 0,4


def test_ten_consecutive_failed_codes_abort_the_run():
    calls = []

    def get(u):
        calls.append(u)
        return 500, "down"

    f, _ = fetcher(get)
    with pytest.raises(pf.SourceDown, match="10 mã"):
        f.many([f"C{i}" for i in range(12)])
    assert len({_code(u) for u in calls}) == 10       # mã thứ 11 không được gọi


def test_many_collects_invalid_and_failed_codes_and_a_valid_answer_resets_the_streak():
    def get(u):
        code = _code(u)
        if code == "BAD":
            return 200, INVALID
        if code == "DOWN":
            return 500, "x"
        return 200, env(2)

    f, _ = fetcher(get)
    res = f.many(["A", "DOWN", "BAD", "B"])
    assert sorted(res.pages) == ["A", "B"] and res.invalid == ["BAD"] and res.failed == ["DOWN"]
