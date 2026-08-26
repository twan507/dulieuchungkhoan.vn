import httpx
import pytest

from etl.omo_fetch import MARKER, WafBlocked, check_gate, fetch


def test_gate_rejects_waf_stub():
    with pytest.raises(WafBlocked):
        check_gate("<html><title>Request Rejected</title>Your support ID is: 1</html>")


def test_gate_rejects_big_body_without_marker():
    with pytest.raises(WafBlocked):
        check_gate("x" * 500_000)


def test_gate_accepts_real_shape():
    check_gate(("x" * 400_000) + MARKER)  # không raise


def test_fetch_retries_transport_error_once():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("boom")
        return httpx.Response(200, text=("x" * 400_000) + MARKER)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    body = fetch(client=client, retry_delay_s=0)
    assert MARKER in body and calls["n"] == 2
