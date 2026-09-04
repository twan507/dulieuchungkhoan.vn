import pathlib

from etl import snapshot_fetch as sf

FIX = pathlib.Path(__file__).parent / "fixtures" / "snapshot"


def _text(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_url_picks_the_bank_endpoint_only_for_com_type_nh():
    assert sf.url("snapshot", "NASB", "BAB", "NH").endswith(
        "/Snapshot/GetSnapshot?OrganCode=NASB&language=vi")
    assert sf.url("snapshot", "ASECO32", "A32", "CT").endswith(
        "/Snapshot/GetSnapshotNoneBank?OrganCode=ASECO32&language=vi")
    assert sf.url("snapshot", "HAMIS", "AAS", None).endswith(
        "/Snapshot/GetSnapshotNoneBank?OrganCode=HAMIS&language=vi")


def test_url_of_dividend_carries_both_the_organ_code_and_the_ticker():
    u = sf.url("dividend", "ASECO32", "A32", "CT")
    assert "OrganCode=ASECO32" in u and "Code=A32" in u
    assert u.startswith("https://wlgw-fundamental.fiintrade.vn/CashDividendAnalysis/GetAnalysis?")


def test_url_of_valuation_lives_on_the_tools_host():
    assert sf.url("valuation", "ASECO32", "A32", "CT") == (
        "https://wlgw-tools.fiintrade.vn/Valuation/GetValuation?OrganCode=ASECO32&language=vi")


def test_classify_accepts_status_zero_from_the_bank_endpoint():
    verdict, item = sf.classify("snapshot", 200, _text("BAB-snapshot-bank-status0.json"))
    assert verdict == "ok"
    assert item["summary"]["organCode"] == "NASB"


def test_classify_accepts_status_success_from_the_non_bank_endpoint():
    verdict, item = sf.classify("snapshot", 200, _text("A32-snapshot.json"))
    assert verdict == "ok" and "summary" in item


def test_classify_sends_a_failed_status_back_to_the_retry_path():
    """status Failed = timeout Redis phía nguồn (quy ước §10.5), KHÔNG phải 'mã rỗng'."""
    verdict, item = sf.classify("valuation", 200, _text("BVB-valuation-failed.json"))
    assert verdict == "retry" and item is None


def test_classify_calls_a_missing_root_key_bad_shape_not_retry():
    verdict, item = sf.classify("valuation", 200, '{"items": [{"khac": 1}], "status": "Success"}')
    assert verdict == "bad_shape" and item is None


def test_classify_treats_broken_json_and_non_200_as_retry():
    assert sf.classify("ownership", 200, "<html>502</html>") == ("retry", None)
    assert sf.classify("ownership", 503, "") == ("retry", None)


import httpx
import pytest

from etl.snapshot_fetch import BadShape, FetchError, Target


def _t(kind="ownership"):
    return Target(kind=kind, issuer_id=1, organ_code="ASECO32", ticker="A32",
                  com_type="CT", found_by="floor")


def test_fetch_one_retries_a_transport_exception_then_succeeds():
    """Bài học lát 3: ReadTimeout phải đi CÙNG đường với response xấu, không ném thẳng."""
    calls = []

    def get(u, timeout):
        calls.append(u)
        if len(calls) == 1:
            raise httpx.ReadTimeout("máy ngủ giữa lời gọi")
        return 200, _text("A32-ownership.json")

    with sf.open_fetcher(get=get, sleep=lambda s: None, clock=lambda: 0.0) as f:
        item, _ = f.fetch_one(_t())
    assert len(calls) == 2 and f.retries == 1
    assert "majorShareHolders" in item


def test_fetch_one_gives_up_after_four_attempts_on_a_failed_status():
    def get(u, timeout):
        return 200, _text("BVB-valuation-failed.json")

    with sf.open_fetcher(get=get, sleep=lambda s: None, clock=lambda: 0.0) as f:
        with pytest.raises(FetchError):
            f.fetch_one(_t("valuation"))
        assert f.calls == 4 and f.retries == 3


def test_fetch_one_does_not_retry_a_bad_shape():
    def get(u, timeout):
        return 200, '{"items": [{"khac": 1}], "status": 0}'

    with sf.open_fetcher(get=get, sleep=lambda s: None, clock=lambda: 0.0) as f:
        with pytest.raises(BadShape):
            f.fetch_one(_t())
        assert f.calls == 1


def test_fetch_one_waits_between_two_calls_to_keep_two_per_second():
    slept, now = [], [0.0]

    def get(u, timeout):
        return 200, _text("A32-ownership.json")

    with sf.open_fetcher(get=get, sleep=slept.append, clock=lambda: now[0]) as f:
        f.fetch_one(_t())
        now[0] = 0.1                                  # mới trôi 0,1 s kể từ lời gọi trước
        f.fetch_one(_t())
    assert slept and abs(slept[-1] - 0.4) < 1e-9      # phải ngủ bù đúng 0,4 s


def test_fetch_one_passes_the_wider_timeout_for_valuation():
    seen = []

    def get(u, timeout):
        seen.append(timeout)
        return 200, _text("A32-valuation.json")

    with sf.open_fetcher(get=get, sleep=lambda s: None, clock=lambda: 0.0) as f:
        f.fetch_one(_t("valuation"))
    assert seen == [30.0]
