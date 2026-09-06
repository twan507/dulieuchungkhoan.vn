"""LLMClient — bọc anthropic.Anthropic trỏ MiniMax. `structured()` = ép công cụ + schema có enum + kiểm Pydantic (đo 232 lời gọi:
0 lỗi schema — minimax.md §5); đường sửa (text JSON → parse; Pydantic lỗi → gọi lại MỘT lần, gửi lại NGUYÊN một lượt user kèm
lỗi — không echo lượt assistant cũ, vì server strict kiểu Anthropic đòi tool_result cho mọi tool_use) giữ làm lưới an toàn.
`token_plan_remains()` gọi endpoint quota bằng http_client (không qua SDK). Exception chỉ mang tên lớp + status."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Generic, TypeVar

import anthropic
import httpx2
from pydantic import BaseModel, ValidationError

from core.llm.errors import LLMError, from_sdk
from core.llm.settings import LLMSettings
from core.llm.usage import Usage

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class Structured(Generic[T]):
    value: T
    usage: Usage
    repaired: bool          # True: phải parse text JSON hoặc gọi lại sửa
    stop_reason: str


@dataclass(frozen=True)
class QuotaRemains:
    interval_pct: int       # cửa sổ 5 giờ, model_name 'general'
    weekly_pct: int
    raw: dict


def _json_from_text(txt: str):
    txt = (txt or "").strip()
    if "```" in txt:
        parts = txt.split("```")
        if len(parts) > 1:
            txt = parts[1][4:] if parts[1].startswith("json") else parts[1]
    i, j = txt.find("{"), txt.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        return json.loads(txt[i:j + 1])
    except ValueError:
        return None


class LLMClient:
    def __init__(self, settings: LLMSettings, *, http_client: httpx2.Client | None = None, max_retries: int = 3):
        self.settings = settings
        self._http = http_client or httpx2.Client(timeout=settings.timeout_s)
        self.raw = anthropic.Anthropic(api_key=settings.api_key, base_url=settings.base_url, http_client=self._http,
                                       max_retries=max_retries, timeout=settings.timeout_s)

    def structured(self, schema: type[T], *, system: str, user: str, thinking: str = "adaptive",
                   max_tokens: int = 4000, temperature: float | None = None) -> Structured[T]:
        tool = {"name": schema.__name__, "description": (schema.__doc__ or schema.__name__).strip(), "input_schema": schema.model_json_schema()}
        messages: list[dict] = [{"role": "user", "content": user}]
        usage, repaired, err = Usage(), False, ""
        for attempt in range(2):
            kw = dict(model=self.settings.model, max_tokens=max_tokens, system=system, messages=messages, tools=[tool],
                      tool_choice={"type": "tool", "name": tool["name"]}, thinking={"type": thinking})
            if temperature is not None:
                kw["temperature"] = temperature
            t0 = time.monotonic()
            try:
                msg = self.raw.messages.create(**kw)
            except anthropic.APIError as e:
                raise from_sdk(e) from None                       # `from None`: không kéo theo str(e) của SDK vào traceback
            usage = usage + Usage.from_sdk(msg.usage, time.monotonic() - t0)
            tools = [b for b in msg.content if b.type == "tool_use"]
            if tools:
                data = tools[0].input
            else:
                repaired = True
                data = _json_from_text("".join(b.text for b in msg.content if b.type == "text"))
            if data is None:
                err = "không có lời gọi công cụ và không có JSON trong text"
            else:
                try:
                    return Structured(schema.model_validate(data), usage, repaired, msg.stop_reason or "")
                except ValidationError as e:
                    err = "; ".join(f"{'.'.join(str(p) for p in x['loc'])}: {x['msg']}" for x in e.errors())[:500]
            if attempt == 0:
                repaired = True
                # KHÔNG echo lượt assistant cũ: server strict kiểu Anthropic đòi tool_result cho mọi tool_use trong lịch sử,
                # mà mình không phát tool_result ⇒ 400. Gửi lại một lượt user DUY NHẤT mang cả câu gốc lẫn lỗi (option b, I2).
                messages = [{"role": "user", "content": user + f"\n\nLần trước kết quả không hợp lệ: {err}. Gọi lại công cụ {tool['name']} cho đúng schema."}]
        err_obj = LLMError("schema", retryable=False, detail=err)
        err_obj.usage = usage                  # M5: giữ token đã tốn dù lỗi schema, để log_call ghi được input/output
        raise err_obj

    def token_plan_remains(self) -> QuotaRemains:
        host = self.settings.base_url
        for suffix in ("/anthropic", "/v1"):
            if host.endswith(suffix):
                host = host[: -len(suffix)]
                break                                            # M9: chỉ bóc MỘT hậu tố — tránh bóc chồng '/anthropic/v1'
        try:
            r = self._http.get(host + "/v1/token_plan/remains", headers={"Authorization": f"Bearer {self.settings.api_key}"})
        except Exception as e:                                   # noqa: BLE001 — chỉ giữ tên lớp
            raise LLMError("transport", retryable=True, detail=type(e).__name__) from None
        if r.status_code != 200:
            raise LLMError("transport", retryable=True, detail=f"HTTP {r.status_code}")
        try:
            d = r.json()                                         # I1: HTTP 200 không đảm bảo body là JSON (gateway trả HTML)
        except Exception as e:                                   # noqa: BLE001 — chỉ giữ tên lớp
            raise LLMError("transport", retryable=True, detail=type(e).__name__) from None
        code = (d.get("base_resp") or {}).get("status_code", 0)
        if code != 0:
            raise LLMError("transport", retryable=True, detail=f"base_resp {code}")
        for m in d.get("model_remains") or []:
            if m.get("model_name") == "general":
                return QuotaRemains(int(m["current_interval_remaining_percent"]), int(m["current_weekly_remaining_percent"]), d)
        raise LLMError("bad_request", retryable=False, detail="không có model_name general trong model_remains")
