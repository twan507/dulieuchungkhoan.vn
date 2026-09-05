import json
import pathlib

import pytest

from etl import wichart_fetch as wf

FIX = pathlib.Path(__file__).parent / "fixtures" / "wichart"
CPI = (FIX / "cpi.json").read_text(encoding="utf-8")


def test_url_uses_hang_hoa_namespace_only_for_commodities():
    assert wf.url("cpi", "vi_mo") == "https://api.wichart.vn/vietnambiz/vi-mo?name=cpi"
    assert wf.url("vang", "hang_hoa") == "https://api.wichart.vn/vietnambiz/vi-mo?key=hang_hoa&name=vang"


def test_classify_ok_retry_bad_shape():
    verdict, doc = wf.classify(200, CPI)
    assert verdict == "ok" and doc["timeUpdate"] == "Tháng 08/2026"
    assert wf.classify(500, '{"message":"Có lỗi xảy ra"}') == ("retry", None)
    assert wf.classify(200, "<html>") == ("retry", None)
    assert wf.classify(200, json.dumps({"title": "x", "chart": {}})) == ("bad_shape", None)
    assert wf.classify(200, json.dumps({"chart": {"series": []}}))[0] == "ok"       # rỗng là chuyện của normalize
    assert wf.classify(200, json.dumps({"chart": []})) == ("bad_shape", None)       # chart không phải dict
    assert wf.classify(200, json.dumps({"chart": "x"})) == ("bad_shape", None)


def test_fetch_one_retries_a_500_then_returns_the_doc():
    answers = [(500, "boom"), (200, CPI)]
    slept = []
    f = wf.Fetcher(get=lambda u, t: answers.pop(0), sleep=slept.append, clock=lambda: 0.0)
    doc, text = f.fetch_one("cpi", "vi_mo")
    assert doc["timeUpdate"] == "Tháng 08/2026" and text == CPI
    assert f.calls == 2 and f.retries == 1 and slept == [2]                       # BACKOFF[0]


def test_fetch_one_raises_after_four_failures_including_transport_errors():
    import httpx
    def get(u, t):
        raise httpx.ReadTimeout("slow")
    f = wf.Fetcher(get=get, sleep=lambda s: None, clock=lambda: 0.0)
    with pytest.raises(wf.FetchError, match="cpi hỏng sau 4 lần"):
        f.fetch_one("cpi", "vi_mo")
    assert f.calls == 4 and f.retries == 3


def test_bad_shape_is_not_retried():
    f = wf.Fetcher(get=lambda u, t: (200, json.dumps({"chart": {}})), sleep=lambda s: None, clock=lambda: 0.0)
    with pytest.raises(wf.BadShape):
        f.fetch_one("cpi", "vi_mo")
    assert f.calls == 1


def test_min_interval_sleeps_between_two_calls():
    clock = iter([0.0, 0.0, 0.05, 0.05, 1.0, 1.0])
    slept = []
    f = wf.Fetcher(get=lambda u, t: (200, CPI), sleep=slept.append, clock=lambda: next(clock))
    f.fetch_one("cpi", "vi_mo")
    f.fetch_one("cpi", "vi_mo")
    assert slept and abs(slept[0] - 0.15) < 1e-9                                   # MIN_INTERVAL 0.2 − 0.05
