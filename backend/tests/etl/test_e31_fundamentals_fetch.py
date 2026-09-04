import pathlib

import httpx
import pytest

from etl import fundamentals_fetch as ff

FIX = pathlib.Path(__file__).parent / "fixtures" / "fundamentals"


def _text(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_url_of_each_kind_lives_on_the_fundamental_host():
    assert ff.url("bs", "ASECO32") == (
        "https://wlgw-fundamental.fiintrade.vn/FinancialStatement/GetBalanceSheet?OrganCode=ASECO32&language=vi")
    assert ff.url("is", "NASB").endswith("/FinancialStatement/GetIncomeStatement?OrganCode=NASB&language=vi")
    assert ff.url("cf", "NASB").endswith("/FinancialStatement/GetCashFlow?OrganCode=NASB&language=vi")
    assert ff.url("reports", "NASB").endswith("/FinancialStatement/GetFinancialReports?OrganCode=NASB&language=vi")
    with pytest.raises(ValueError):
        ff.url("snapshot", "NASB")


def test_classify_accepts_status_success_and_returns_the_statement_item():
    verdict, item = ff.classify("bs", 200, _text("A32-bs.json"))
    assert verdict == "ok"
    assert item["quarterly"] == [] and len(item["yearly"]) == 10        # A32: chỉ kỳ năm (đo 2026-09-04)


def test_classify_accepts_status_zero_too():
    """Tài liệu 2026-08-10 đo status 0, 2026-09-04 đo "Success" — cùng endpoint (quy ước §6.1)."""
    body = '{"items": [{"quarterly": [], "yearly": []}], "status": 0}'
    assert ff.classify("cf", 200, body)[0] == "ok"


def test_classify_of_reports_returns_the_item_list_even_when_empty():
    verdict, item = ff.classify("reports", 200, _text("A32-reports.json"))
    assert verdict == "ok" and len(item["items"]) == 8 and item["items"][0]["id"] == 9412069
    verdict, item = ff.classify("reports", 200, '{"items": [], "totalCount": 0, "status": "Success"}')
    assert verdict == "ok" and item == {"items": []}                   # TAH thật trả 0 báo cáo — không phải lỗi


def test_classify_treats_an_empty_statement_item_list_as_an_empty_statement():
    verdict, item = ff.classify("is", 200, '{"items": [], "status": "Success"}')
    assert verdict == "ok" and item == {"quarterly": [], "yearly": []}


def test_classify_sends_failed_status_broken_json_and_non_200_to_retry():
    assert ff.classify("bs", 200, '{"items": null, "status": "Failed"}') == ("retry", None)
    assert ff.classify("bs", 200, "<html>502</html>") == ("retry", None)
    assert ff.classify("bs", 503, "") == ("retry", None)


def test_classify_calls_a_missing_root_key_bad_shape():
    assert ff.classify("bs", 200, '{"items": [{"yearly": []}], "status": "Success"}') == ("bad_shape", None)
    assert ff.classify("reports", 200, '{"items": [1, 2], "status": "Success"}') == ("bad_shape", None)


def _target(kind="bs"):
    return ff.Target(kind=kind, issuer_id=1, organ_code="ASECO32", ticker="A32", found_by="floor")


def test_fetch_one_spaces_calls_half_a_second_apart_and_retries_with_backoff():
    clock = [0.0]
    slept = []
    answers = iter([(503, ""), (200, _text("A32-bs.json")), (200, _text("A32-cf.json"))])

    def get(u, timeout):
        return next(answers)

    def sleep(s):
        slept.append(s)
        clock[0] += s

    with ff.open_fetcher(get=get, sleep=sleep, clock=lambda: clock[0]) as f:
        item, text = f.fetch_one(_target())
        f.fetch_one(_target("cf"))                     # lời gọi thứ hai ngay sau — phải ngủ để đủ 0,5 s
    assert len(item["yearly"]) == 10
    assert f.calls == 3 and f.retries == 1
    assert slept[0] == 2                               # backoff đầu tiên
    assert any(0 < s <= 0.5 for s in slept[1:])        # giãn cách


def test_fetch_one_gives_up_after_four_attempts_and_names_the_code():
    with ff.open_fetcher(get=lambda u, t: (500, "loi"), sleep=lambda s: None) as f:
        with pytest.raises(ff.FetchError, match="ASECO32/bs"):
            f.fetch_one(_target())
    assert f.calls == 4 and f.retries == 3


def test_fetch_one_treats_a_transport_exception_like_a_bad_response():
    """Bài học e7f80f6: timeout qua giấc ngủ 02:00 từng lọt qua vòng retry và giết cả lượt."""
    answers = iter([httpx.ReadTimeout("ngu"), (200, _text("A32-cf.json"))])

    def get(u, timeout):
        a = next(answers)
        if isinstance(a, Exception):
            raise a
        return a

    with ff.open_fetcher(get=get, sleep=lambda s: None) as f:
        item, _ = f.fetch_one(_target("cf"))
    assert len(item["yearly"]) == 10 and f.retries == 1


def test_fetch_one_raises_bad_shape_without_retrying():
    with ff.open_fetcher(get=lambda u, t: (200, '{"items": [{"yearly": []}], "status": "Success"}'),
                         sleep=lambda s: None) as f:
        with pytest.raises(ff.BadShape):
            f.fetch_one(_target())
    assert f.calls == 1
