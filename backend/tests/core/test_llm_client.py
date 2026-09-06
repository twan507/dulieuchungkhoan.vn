"""LLMClient offline qua httpx2.MockTransport (SDK anthropic 1.4 dùng httpx2 — đo 2026-09-06). Response hình dạng Anthropic
chép từ lời gọi thật (minimax.md §5–§6). Mọi ca kiểm khoá giả không lọt ra ngoài."""
import json
import pathlib
from typing import Literal

import httpx2
import pytest
from pydantic import BaseModel, ConfigDict, Field

from core.llm import LLMClient, LLMError, LLMSettings, Usage

KEY = "zz-secret-key-0123456789"
FIX = pathlib.Path(__file__).parent / "fixtures"
SET = LLMSettings(api_key=KEY)


class Classification(BaseModel):
    """Kết quả phân loại một bài"""
    model_config = ConfigDict(extra="forbid")
    group: Literal["1", "2", "3", "x"]
    sub: Literal["1c", "3d", "x"]
    confidence: float = Field(ge=0, le=1)
    summary_ai: str
    tickers: list[str]
    industries: list[str]


GOOD = {"group": "3", "sub": "3d", "confidence": 0.9, "summary_ai": "Tóm tắt.", "tickers": ["HPG"], "industries": ["KIMLOAI"]}
USAGE = {"input_tokens": 214, "cache_read_input_tokens": 2816, "output_tokens": 250, "output_tokens_details": {"thinking_tokens": 120}}


def _msg(content, stop="tool_use"):
    return {"id": "m1", "type": "message", "role": "assistant", "model": "MiniMax-M3", "stop_reason": stop, "content": content, "usage": USAGE}


def _tool(inp):
    return {"type": "tool_use", "id": "t1", "name": "Classification", "input": inp}


def _client(responses):
    """responses: list[(status, body_json)] tiêu thụ theo thứ tự cho POST /v1/messages; GET remains đọc fixture. Ghi lại request."""
    seen = []

    def handler(req):
        seen.append(req)
        if req.method == "GET":
            return httpx2.Response(200, json=json.loads((FIX / "token_plan_remains.json").read_text(encoding="utf-8")))
        status, body = responses.pop(0)
        return httpx2.Response(status, json=body)

    c = LLMClient(SET, http_client=httpx2.Client(transport=httpx2.MockTransport(handler)), max_retries=0)
    return c, seen


def test_tool_use_is_validated_and_usage_read():
    c, seen = _client([(200, _msg([{"type": "text", "text": "<tool_call>\n"}, _tool(GOOD)]))])
    r = c.structured(Classification, system="S", user="U")
    assert r.value.group == "3" and r.value.industries == ["KIMLOAI"] and r.repaired is False and r.stop_reason == "tool_use"
    assert r.usage == Usage(214, 2816, 250, 120, 1, r.usage.latency_s) and r.usage.latency_s >= 0
    body = json.loads(seen[0].content)
    assert body["tool_choice"] == {"type": "tool", "name": "Classification"} and body["thinking"] == {"type": "adaptive"}
    assert body["tools"][0]["input_schema"]["additionalProperties"] is False and body["system"] == "S"
    assert str(seen[0].url) == "https://api.minimax.io/anthropic/v1/messages" and seen[0].headers["x-api-key"] == KEY
    assert "temperature" not in body


def test_text_json_without_tool_use_is_repaired():
    c, _ = _client([(200, _msg([{"type": "text", "text": "```json\n" + json.dumps(GOOD) + "\n```"}], stop="end_turn"))])
    r = c.structured(Classification, system="S", user="U", thinking="disabled")
    assert r.value.sub == "3d" and r.repaired is True and r.stop_reason == "end_turn"


def test_invalid_then_valid_resends_user_with_correction():
    bad = dict(GOOD, sub="9z")
    c, seen = _client([(200, _msg([_tool(bad)])), (200, _msg([_tool(GOOD)]))])
    r = c.structured(Classification, system="S", user="U")
    assert r.value.sub == "3d" and r.repaired is True and r.usage.calls == 2 and r.usage.input_tokens == 428
    second = json.loads(seen[1].content)["messages"]
    assert len(second) == 1 and second[0]["role"] == "user"
    assert "U" in second[0]["content"] and "không hợp lệ" in second[0]["content"]


def test_invalid_twice_is_schema_error_not_retryable():
    bad = dict(GOOD, sub="9z")
    c, seen = _client([(200, _msg([_tool(bad)])), (200, _msg([_tool(bad)]))])
    with pytest.raises(LLMError) as e:
        c.structured(Classification, system="S", user="U")
    assert e.value.reason == "schema" and e.value.retryable is False and len(seen) == 2
    assert e.value.usage.calls == 2 and e.value.usage.input_tokens == 428


def test_no_tool_no_json_is_schema_error():
    c, _ = _client([(200, _msg([{"type": "text", "text": "Xin lỗi, không rõ."}], stop="end_turn")),
                    (200, _msg([{"type": "text", "text": "vẫn không"}], stop="end_turn"))])
    with pytest.raises(LLMError) as e:
        c.structured(Classification, system="S", user="U")
    assert e.value.reason == "schema"


@pytest.mark.parametrize(
    "status,reason,retryable",
    [
        (429, "rate_limit", True),
        (500, "server", True),
        (401, "auth", False),
        (400, "bad_request", False),
        (529, "server", True),
        (503, "server", True),
    ],
)
def test_http_errors_map_to_llm_error_without_key(status, reason, retryable):
    c, _ = _client([(status, {"type": "error", "error": {"type": "x", "message": f"boom {KEY}"}})])
    with pytest.raises(LLMError) as e:
        c.structured(Classification, system="S", user="U")
    assert e.value.reason == reason and e.value.retryable is retryable
    assert KEY not in str(e.value) and str(status) in str(e.value)


def test_token_plan_remains_reads_general_row():
    c, seen = _client([])
    q = c.token_plan_remains()
    assert (q.interval_pct, q.weekly_pct) == (97, 86) and q.raw["base_resp"]["status_code"] == 0
    assert str(seen[0].url) == "https://api.minimax.io/v1/token_plan/remains" and seen[0].headers["Authorization"] == f"Bearer {KEY}"


def test_token_plan_remains_base_resp_error_is_retryable():
    def handler(req):
        return httpx2.Response(200, json={"model_remains": [], "base_resp": {"status_code": 1002, "status_msg": "rate limit"}})
    c = LLMClient(SET, http_client=httpx2.Client(transport=httpx2.MockTransport(handler)), max_retries=0)
    with pytest.raises(LLMError) as e:
        c.token_plan_remains()
    assert e.value.retryable is True and e.value.reason == "transport" and "1002" in str(e.value)


def test_token_plan_remains_non_json_200_body_is_transport_error():
    def handler(req):
        return httpx2.Response(200, text="<html>gateway</html>")
    c = LLMClient(SET, http_client=httpx2.Client(transport=httpx2.MockTransport(handler)), max_retries=0)
    with pytest.raises(LLMError) as e:
        c.token_plan_remains()
    assert e.value.reason == "transport" and e.value.retryable is True


@pytest.mark.parametrize("base_url", ["https://x.test/anthropic", "https://x.test/v1"])
def test_token_plan_remains_strips_exactly_one_known_suffix(base_url):
    seen = []

    def handler(req):
        seen.append(req)
        return httpx2.Response(200, json=json.loads((FIX / "token_plan_remains.json").read_text(encoding="utf-8")))
    c = LLMClient(LLMSettings(api_key=KEY, base_url=base_url), http_client=httpx2.Client(transport=httpx2.MockTransport(handler)), max_retries=0)
    c.token_plan_remains()
    assert str(seen[0].url) == "https://x.test/v1/token_plan/remains"


def test_close_only_closes_the_client_it_created():
    """Lát 10 (chatbot, tiến trình dài) phải trả kết nối; client bơm vào là của caller, không được đóng hộ."""
    injected = httpx2.Client(transport=httpx2.MockTransport(lambda r: httpx2.Response(200, json={})))
    c = LLMClient(SET, http_client=injected)
    c.close()
    assert injected.is_closed is False                 # của caller — giữ nguyên
    own = LLMClient(SET)
    inner = own._http
    with own:
        pass
    assert inner.is_closed is True                     # tự tạo — đóng khi thoát context
