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
