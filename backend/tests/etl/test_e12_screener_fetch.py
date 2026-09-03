import json

import pytest

from etl import screener_fetch as sf


def _ok(page, total=61):      # 61 mã ⇒ 3 trang (30/30/1)
    return 200, json.dumps({"page": page, "pageSize": 30, "totalCount": total,
                            "items": [{"priceInfo": {"ticker": f"T{page}{i}"}} for i in range(min(30, total - 30 * (page - 1)))],
                            "status": "Success", "errors": None})


def test_paginates_by_total_count_and_returns_raw_pages():
    calls = []
    def post(body):
        calls.append(body["page"]); return _ok(body["page"])
    pages, retries = sf.fetch(post=post, sleep=lambda s: None)
    assert calls == [1, 2, 3] and retries == 0
    assert json.loads(pages[2])["items"][0]["priceInfo"]["ticker"] == "T30"


def test_transient_failed_status_is_retried_once_not_returned_as_empty_page():
    seq = {2: [(200, json.dumps({"status": "Failed", "errors": ["Timeout performing GET (5000ms)"]}))]}
    def post(body):
        p = body["page"]
        if seq.get(p):
            return seq[p].pop(0)
        return _ok(p)
    slept = []
    pages, retries = sf.fetch(post=post, sleep=slept.append)
    assert retries == 1 and slept == [2]
    assert len(pages) == 3 and json.loads(pages[1])["status"] == "Success"


def test_four_consecutive_failures_raise_and_nothing_is_returned():
    def post(body):
        if body["page"] == 2:
            return 500, "boom"
        return _ok(body["page"])
    with pytest.raises(sf.FetchError) as ei:
        sf.fetch(post=post, sleep=lambda s: None)
    assert "trang 2" in str(ei.value)


def test_body_sends_exactly_one_criterion_and_page_size_30():
    seen = {}
    def post(body):
        seen.update(body); return _ok(body["page"], total=5)
    sf.fetch(post=post, sleep=lambda s: None)
    assert seen["pageSize"] == 30 and seen["comGroupCode"] == "ALL" and seen["icbCode"] == "ALL"
    assert len(seen["parameters"]) == 1 and seen["parameters"][0]["code"] == "ClosePrice"
