# Plan — lát 9a: lưới AI phân loại tin + gắn ngành trên MiniMax M3

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `etl classify --per-group N | --limit N` gọi MiniMax M3 qua module `core/llm` dùng chung, ghi nhóm/sub/confidence/`summary_ai`, mã tầng 2–3, ngành hai đường (`ticker`/`ai`) vào `news.*`, ghi sổ từng lời gọi vào `ops.llm_call`, có guard quota và `--dry-run` để đo.

**Architecture:** `backend/core/llm/` bọc SDK `anthropic` 1.4.0 (trỏ `https://api.minimax.io/anthropic`, HTTP là `httpx2`) — chỉ biết gọi model an toàn, ép công cụ + kiểm Pydantic, đếm token, che khoá. `backend/etl/news_classify.py` biết taxonomy, ngành, đường ghi `news.*`; migration `0018` thêm `news.article_industry` và `ops.llm_call`. Mọi lượt có trần; không gắn vào `--loop`.

**Tech Stack:** Python 3.12+, `uv`, pytest (Postgres thật qua `migrated_engine`), `anthropic` 1.4.0 + `httpx2` (mock bằng `httpx2.MockTransport`), Pydantic 2, SQLAlchemy `text()`, Alembic.

**Spec:** [spec.md](spec.md) — đọc §2.1 (dữ kiện), §4.2 (16 chốt), §5 (thiết kế, hợp đồng, DDL), §6 (seam), §7 (AC).

## Global Constraints

- Chạy lệnh từ `backend/` (Git Bash): `PYTHONIOENCODING=utf-8 uv run pytest tests/<path> -q`. DB test cần `TEST_DATABASE_URL` trong `.env` gốc — fixture `migrated_engine` (`backend/tests/conftest.py`) tự dựng `dulieu_test`.
- **TDD từng seam:** test đỏ → chạy thấy đỏ đúng assertion → code tối thiểu → xanh → commit. Expected là **literal** ghi trong plan.
- **Không sửa ngoài yêu cầu.** Không đổi `news_job`, `news_store`, `news_tag` (chỉ import). Không chép danh sách ngành cứng vào prompt (nạp từ DB).
- **Khoá `LLM_API` không bao giờ xuất hiện** trong log, exception, test output, file. Test có assertion chuỗi khoá giả không lọt.
- Style repo: docstring đầu file kể "vì sao" bằng tiếng Việt; comment tiếng Việt; dòng ≤ 150 ký tự; commit message tiếng Anh, Conventional Commits, kết `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`; không `--no-verify`.
- Nhánh `feat/news-classify-llm` (đã tạo; `uv add anthropic` đã chạy — `pyproject.toml` + `uv.lock` đã có `anthropic>=1.4.0`, commit ở Task 0).
- Tiền tố dữ liệu test: `ZZ*` cho mã/issuer, `https://zz.test/...` cho URL bài (không đụng dòng job khác ghi — test-strategy luật 6).
- Cột `news.article.confidence` là `numeric`; `labels text[]`; `sub` CHECK 20 mã (NULL được); `article_ticker.via` CHECK `('url','lookup','ai')`.
- Hằng số: `CAP_CHARS = 3000`, `TITLE_ONLY_BELOW = 200`, `QUOTA_EVERY = 25`, `QUOTA_MIN_INTERVAL_PCT = 20`, `QUOTA_MIN_WEEKLY_PCT = 10`, `MAX_CONSECUTIVE_FAILED = 5`.

---

### Task 0 (controller, đã làm trước khi giao): fixture + `.env.example` + commit `uv add`

**Files:**
- Create: `backend/tests/core/fixtures/token_plan_remains.json` — JSON gọi thật 2026-09-06 15:12 (spec §2.1), nguyên văn:

```json
{"model_remains":[{"start_time":1788670800000,"end_time":1788688800000,"remains_time":11803663,"current_interval_total_count":0,"current_interval_usage_count":0,"model_name":"general","current_weekly_total_count":0,"current_weekly_usage_count":0,"weekly_start_time":1788134400000,"weekly_end_time":1788739200000,"weekly_remains_time":62203663,"current_interval_status":1,"current_interval_remaining_percent":97,"current_weekly_status":1,"current_weekly_remaining_percent":86},{"start_time":1788652800000,"end_time":1788739200000,"remains_time":62203663,"current_interval_total_count":0,"current_interval_usage_count":0,"model_name":"video","current_weekly_total_count":0,"current_weekly_usage_count":0,"weekly_start_time":1788134400000,"weekly_end_time":1788739200000,"weekly_remains_time":62203663,"current_interval_status":3,"current_interval_remaining_percent":100,"current_weekly_status":3,"current_weekly_remaining_percent":100}],"base_resp":{"status_code":0,"status_msg":"success"}}
```

- Modify: `.env.example` — thêm khối:

```
# MiniMax M3 (docs/10-sources/llm/minimax.md) — khoá Token Plan; production đổi sang Standard API Key, code không đổi
LLM_API=
# LLM_BASE_URL=https://api.minimax.io/anthropic
# LLM_MODEL=MiniMax-M3
```

- Commit: `chore(backend): add anthropic SDK, LLM env keys, token-plan fixture`

---

### Task 1: `core/llm` — errors · settings · usage (thuần)

**Files:**
- Create: `backend/core/llm/__init__.py`, `backend/core/llm/errors.py`, `backend/core/llm/settings.py`, `backend/core/llm/usage.py`
- Test: `backend/tests/core/test_llm_settings.py`, `backend/tests/core/test_llm_usage.py`

**Interfaces:**
- Produces: `LLMError(reason: str, *, retryable: bool, detail: str = "")` với thuộc tính `.reason`, `.retryable`; `LLMConfigError(Exception)`; `from_sdk(e: anthropic.APIError) -> LLMError`; `LLMSettings(api_key, base_url, model, timeout_s)` frozen dataclass, `LLMSettings.from_env(env: Mapping | None = None)`, `LLMSettings.redact(text) -> str`; `Usage(input_tokens, cache_read_tokens, output_tokens, thinking_tokens, calls, latency_s)` với `__add__`, `estimate_usd()`, `Usage.from_sdk(usage, latency_s)`.
- Consumed by: Task 2 (client), Task 5–6 (job).

- [ ] **Step 1: Test đỏ — `tests/core/test_llm_settings.py`**

```python
"""LLMSettings: khoá bắt buộc, mặc định MiniMax, repr/redact không lộ khoá (CLAUDE.md §5)."""
import pytest

from core.llm import LLMConfigError, LLMSettings

KEY = "zz-secret-key-0123456789"          # 24 ký tự


def test_missing_key_raises_named_error():
    with pytest.raises(LLMConfigError) as e:
        LLMSettings.from_env({})
    assert "LLM_API" in str(e.value)
    with pytest.raises(LLMConfigError):
        LLMSettings.from_env({"LLM_API": "   "})


def test_defaults_point_to_minimax_anthropic():
    s = LLMSettings.from_env({"LLM_API": KEY})
    assert s.base_url == "https://api.minimax.io/anthropic"
    assert s.model == "MiniMax-M3"
    assert s.timeout_s == 120.0
    s2 = LLMSettings.from_env({"LLM_API": KEY, "LLM_BASE_URL": "https://x.test/anthropic/", "LLM_MODEL": "M", "LLM_TIMEOUT_S": "30"})
    assert (s2.base_url, s2.model, s2.timeout_s) == ("https://x.test/anthropic", "M", 30.0)


def test_repr_and_redact_never_expose_key():
    s = LLMSettings.from_env({"LLM_API": KEY})
    assert KEY not in repr(s) and KEY not in str(s)
    assert "24 ký tự" in repr(s)
    assert s.redact(f"Bearer {KEY} hết") == "Bearer <REDACTED> hết"
```

- [ ] **Step 2: Test đỏ — `tests/core/test_llm_usage.py`**

```python
"""Usage: cộng dồn và quy giá pay-go MiniMax (minimax.md §3, tài liệu 2026-09-06) — literal tính tay, không tính lại theo code."""
from types import SimpleNamespace

from core.llm import Usage


def test_estimate_usd_literal_from_brainstorm():
    # 1.850 vào mới × $0,30/M + 1.300 đọc cache × $0,06/M + 1.000 ra × $1,20/M = 0,000555 + 0,000078 + 0,0012
    u = Usage(input_tokens=1850, cache_read_tokens=1300, output_tokens=1000)
    assert round(u.estimate_usd(), 5) == 0.00183
    assert Usage().estimate_usd() == 0.0


def test_add_sums_every_field():
    a = Usage(100, 50, 10, 5, 1, 1.5)
    b = Usage(200, 0, 20, 0, 1, 2.5)
    c = a + b
    assert (c.input_tokens, c.cache_read_tokens, c.output_tokens, c.thinking_tokens, c.calls, c.latency_s) == (300, 50, 30, 5, 2, 4.0)
    assert a == Usage(100, 50, 10, 5, 1, 1.5)                    # không đổi toán hạng


def test_from_sdk_reads_cache_and_thinking_and_tolerates_none():
    sdk = SimpleNamespace(input_tokens=214, cache_read_input_tokens=2816, output_tokens=250,
                          output_tokens_details=SimpleNamespace(thinking_tokens=120))
    u = Usage.from_sdk(sdk, 3.2)
    assert (u.input_tokens, u.cache_read_tokens, u.output_tokens, u.thinking_tokens, u.calls, u.latency_s) == (214, 2816, 250, 120, 1, 3.2)
    bare = SimpleNamespace(input_tokens=3030, cache_read_input_tokens=None, output_tokens=7)     # lượt 1: chưa cache, không details
    u2 = Usage.from_sdk(bare, 1.0)
    assert (u2.cache_read_tokens, u2.thinking_tokens) == (0, 0)
```

- [ ] **Step 3: Chạy thấy đỏ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/core/test_llm_settings.py tests/core/test_llm_usage.py -q`
Expected: `ModuleNotFoundError: No module named 'core.llm'`.

- [ ] **Step 4: Code — `core/llm/errors.py`**

```python
"""Lỗi của module LLM: một lớp, hai thuộc tính (`reason`, `retryable`) để job quyết định đếm `failed` hay dừng.
Thông điệp CHỈ giữ tên lớp SDK + status — không `str(e)` của SDK (URL/headers có thể mang khoá; khuôn http_fetch)."""
from __future__ import annotations

import anthropic


class LLMConfigError(Exception):
    """Cấu hình thiếu/sai (LLM_API) — lỗi trước khi gọi, không phải lỗi gọi."""


class LLMError(Exception):
    def __init__(self, reason: str, *, retryable: bool, detail: str = ""):
        self.reason, self.retryable = reason, retryable
        super().__init__(f"{reason}: {detail}" if detail else reason)


def from_sdk(e: anthropic.APIError) -> LLMError:
    status = getattr(e, "status_code", None)
    detail = f"{type(e).__name__} {status}" if status is not None else type(e).__name__
    if isinstance(e, anthropic.RateLimitError):
        return LLMError("rate_limit", retryable=True, detail=detail)
    if isinstance(e, anthropic.InternalServerError):
        return LLMError("server", retryable=True, detail=detail)
    if isinstance(e, anthropic.APIConnectionError):                       # gồm APITimeoutError
        return LLMError("transport", retryable=True, detail=detail)
    if isinstance(e, (anthropic.AuthenticationError, anthropic.PermissionDeniedError)):
        return LLMError("auth", retryable=False, detail=detail)
    return LLMError("bad_request", retryable=False, detail=detail)
```

- [ ] **Step 5: Code — `core/llm/settings.py`**

```python
"""Một chỗ duy nhất biết khoá, base URL, tên model (brainstorm §4.3). Đọc từ mapping (mặc định os.environ — job đã
load_dotenv trước); KHÔNG tự đọc .env. repr che khoá; `redact` cho log."""
from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from core.llm.errors import LLMConfigError

DEFAULT_BASE_URL = "https://api.minimax.io/anthropic"      # minimax.md §1 — giao diện Anthropic, MiniMax khuyến nghị cho M3
DEFAULT_MODEL = "MiniMax-M3"
DEFAULT_TIMEOUT_S = 120.0


@dataclass(frozen=True)
class LLMSettings:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    timeout_s: float = DEFAULT_TIMEOUT_S

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "LLMSettings":
        env = os.environ if env is None else env
        key = (env.get("LLM_API") or "").strip()
        if not key:
            raise LLMConfigError("thiếu LLM_API (khoá MiniMax Token Plan) trong môi trường/.env — xem docs/10-sources/llm/minimax.md")
        return cls(key, (env.get("LLM_BASE_URL") or DEFAULT_BASE_URL).rstrip("/"), env.get("LLM_MODEL") or DEFAULT_MODEL,
                   float(env.get("LLM_TIMEOUT_S") or DEFAULT_TIMEOUT_S))

    def __repr__(self) -> str:
        return f"LLMSettings(model={self.model}, base_url={self.base_url}, api_key=<đặt, {len(self.api_key)} ký tự>)"

    __str__ = __repr__

    def redact(self, text: str) -> str:
        return text.replace(self.api_key, "<REDACTED>") if self.api_key else text
```

- [ ] **Step 6: Code — `core/llm/usage.py`**

```python
"""Đếm token/độ trễ mỗi lời gọi và quy giá pay-go để SO SÁNH (Token Plan tính theo quota, không theo tiền).
Giá M3 ≤ 512K prompt (minimax.md §3, tài liệu 2026-09-06): $0,30/M vào · $1,20/M ra · $0,06/M đọc cache.
`input_tokens` của SDK là phần KHÔNG cache (đo §6: lượt 2 input 214 / cache_read 2.816) — không trừ lại."""
from __future__ import annotations

from dataclasses import dataclass

PRICE_USD_PER_M = {"input": 0.30, "cache_read": 0.06, "output": 1.20}


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    calls: int = 0
    latency_s: float = 0.0

    def __add__(self, o: "Usage") -> "Usage":
        return Usage(self.input_tokens + o.input_tokens, self.cache_read_tokens + o.cache_read_tokens,
                     self.output_tokens + o.output_tokens, self.thinking_tokens + o.thinking_tokens,
                     self.calls + o.calls, self.latency_s + o.latency_s)

    def estimate_usd(self) -> float:
        return (self.input_tokens * PRICE_USD_PER_M["input"] + self.cache_read_tokens * PRICE_USD_PER_M["cache_read"]
                + self.output_tokens * PRICE_USD_PER_M["output"]) / 1_000_000

    @classmethod
    def from_sdk(cls, usage, latency_s: float) -> "Usage":
        details = getattr(usage, "output_tokens_details", None)
        return cls(int(getattr(usage, "input_tokens", 0) or 0), int(getattr(usage, "cache_read_input_tokens", 0) or 0),
                   int(getattr(usage, "output_tokens", 0) or 0), int(getattr(details, "thinking_tokens", 0) or 0), 1, latency_s)
```

- [ ] **Step 7: Code — `core/llm/__init__.py`** (Task 2 sẽ thêm `LLMClient`, `Structured`, `QuotaRemains`)

```python
"""Module LLM dùng chung của dự án — chỉ MiniMax M3 (chủ dự án chốt 2026-09-06), SDK anthropic trỏ giao diện
Anthropic của MiniMax. Consumer (etl.news_classify, api chatbot lát 10) chỉ import từ đây, không import SDK."""
from core.llm.errors import LLMConfigError, LLMError
from core.llm.settings import LLMSettings
from core.llm.usage import Usage

__all__ = ["LLMConfigError", "LLMError", "LLMSettings", "Usage"]
```

- [ ] **Step 8: Chạy thấy xanh**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/core/test_llm_settings.py tests/core/test_llm_usage.py -q`
Expected: `6 passed`.

- [ ] **Step 9: Commit**

```bash
git add backend/core/llm backend/tests/core/test_llm_settings.py backend/tests/core/test_llm_usage.py
git commit -m "feat(core/llm): settings, usage accounting, error mapping for MiniMax M3"
```

---

### Task 2: `core/llm/client.py` — `structured()` + `token_plan_remains()`

**Files:**
- Create: `backend/core/llm/client.py`
- Modify: `backend/core/llm/__init__.py` (export)
- Test: `backend/tests/core/test_llm_client.py` (dùng fixture `tests/core/fixtures/token_plan_remains.json` của Task 0)

**Interfaces:**
- Consumes: Task 1.
- Produces: `Structured(value: T, usage: Usage, repaired: bool, stop_reason: str)`; `QuotaRemains(interval_pct: int, weekly_pct: int, raw: dict)`; `LLMClient(settings, *, http_client=None, max_retries=3)` với `.settings`, `.raw` (`anthropic.Anthropic`), `structured(schema, *, system, user, thinking="adaptive", max_tokens=4000, temperature=None) -> Structured`, `token_plan_remains() -> QuotaRemains`.

- [ ] **Step 1: Test đỏ — `tests/core/test_llm_client.py`**

```python
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


def test_invalid_then_valid_costs_two_calls_and_echoes_history():
    bad = dict(GOOD, sub="9z")
    c, seen = _client([(200, _msg([_tool(bad)])), (200, _msg([_tool(GOOD)]))])
    r = c.structured(Classification, system="S", user="U")
    assert r.value.sub == "3d" and r.repaired is True and r.usage.calls == 2 and r.usage.input_tokens == 428
    second = json.loads(seen[1].content)["messages"]
    assert [m["role"] for m in second] == ["user", "assistant", "user"]
    assert second[1]["content"][0]["type"] == "tool_use" and "Kết quả không hợp lệ" in second[2]["content"]


def test_invalid_twice_is_schema_error_not_retryable():
    bad = dict(GOOD, sub="9z")
    c, seen = _client([(200, _msg([_tool(bad)])), (200, _msg([_tool(bad)]))])
    with pytest.raises(LLMError) as e:
        c.structured(Classification, system="S", user="U")
    assert e.value.reason == "schema" and e.value.retryable is False and len(seen) == 2


def test_no_tool_no_json_is_schema_error():
    c, _ = _client([(200, _msg([{"type": "text", "text": "Xin lỗi, không rõ."}], stop="end_turn")),
                    (200, _msg([{"type": "text", "text": "vẫn không"}], stop="end_turn"))])
    with pytest.raises(LLMError) as e:
        c.structured(Classification, system="S", user="U")
    assert e.value.reason == "schema"


@pytest.mark.parametrize("status,reason,retryable", [(429, "rate_limit", True), (500, "server", True), (401, "auth", False), (400, "bad_request", False)])
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
```

- [ ] **Step 2: Chạy thấy đỏ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/core/test_llm_client.py -q`
Expected: `ImportError: cannot import name 'LLMClient' from 'core.llm'`.

- [ ] **Step 3: Code — `core/llm/client.py`**

```python
"""LLMClient — bọc anthropic.Anthropic trỏ MiniMax. `structured()` = ép công cụ + schema có enum + kiểm Pydantic (đo 232 lời gọi:
0 lỗi schema — minimax.md §5); đường sửa (text JSON → parse; Pydantic lỗi → gọi lại MỘT lần) giữ làm lưới an toàn.
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
                messages = messages + [
                    {"role": "assistant", "content": [b.model_dump(mode="json", exclude_none=True) for b in msg.content]},
                    {"role": "user", "content": f"Kết quả không hợp lệ: {err}. Gọi lại công cụ {tool['name']} cho đúng schema."}]
        raise LLMError("schema", retryable=False, detail=err)

    def token_plan_remains(self) -> QuotaRemains:
        host = self.settings.base_url
        for suffix in ("/anthropic", "/v1"):
            if host.endswith(suffix):
                host = host[: -len(suffix)]
        try:
            r = self._http.get(host + "/v1/token_plan/remains", headers={"Authorization": f"Bearer {self.settings.api_key}"})
        except Exception as e:                                   # noqa: BLE001 — chỉ giữ tên lớp
            raise LLMError("transport", retryable=True, detail=type(e).__name__) from None
        if r.status_code != 200:
            raise LLMError("transport", retryable=True, detail=f"HTTP {r.status_code}")
        d = r.json()
        code = (d.get("base_resp") or {}).get("status_code", 0)
        if code != 0:
            raise LLMError("transport", retryable=True, detail=f"base_resp {code}")
        for m in d.get("model_remains") or []:
            if m.get("model_name") == "general":
                return QuotaRemains(int(m["current_interval_remaining_percent"]), int(m["current_weekly_remaining_percent"]), d)
        raise LLMError("bad_request", retryable=False, detail="không có model_name general trong model_remains")
```

- [ ] **Step 4: `core/llm/__init__.py`** — thêm import và `__all__`:

```python
from core.llm.client import LLMClient, QuotaRemains, Structured
from core.llm.errors import LLMConfigError, LLMError
from core.llm.settings import LLMSettings
from core.llm.usage import Usage

__all__ = ["LLMClient", "LLMConfigError", "LLMError", "LLMSettings", "QuotaRemains", "Structured", "Usage"]
```

- [ ] **Step 5: Chạy thấy xanh**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/core -q`
Expected: tất cả pass (11 test mới + test cũ của `tests/core`). Nếu ca 429/500 đỏ vì SDK tự retry: kiểm `max_retries=0` đã truyền; nếu `test_invalid_then_valid…` đỏ ở `content[0]["type"]` vì `model_dump` đổi tên trường, in `second[1]` và sửa `model_dump(mode="json", exclude_none=True, by_alias=True)`.

- [ ] **Step 6: Commit**

```bash
git add backend/core/llm backend/tests/core/test_llm_client.py
git commit -m "feat(core/llm): LLMClient.structured with forced tool + pydantic repair, token plan quota"
```

---

### Task 3: Migration `0018` — `news.article_industry` + `ops.llm_call`; test schema + role; vá `_cleanup` lát 8

**Files:**
- Create: `database/migrations/versions/0018_news_industry_llm_call.py`
- Test: `backend/tests/schema/test_s15_news_industry_llm_call.py`
- Modify: `backend/tests/etl/test_e56_news_job.py:100-107` (`_cleanup` — xoá hai bảng mới TRƯỚC `news.article`, nếu không FK chặn DELETE)

**Interfaces:**
- Produces: bảng `news.article_industry(article_id, industry_id, via, confidence)` PK `(article_id, industry_id, via)`; `ops.llm_call(call_id, called_at, purpose, model, thinking, run_id, article_id, status, http_calls, input_tokens, cache_read_tokens, output_tokens, thinking_tokens, latency_ms, error)`.

- [ ] **Step 1: Test đỏ — `tests/schema/test_s15_news_industry_llm_call.py`**

```python
"""Migration 0018: bài ↔ ngành hai đường (via trong PK), sổ lời gọi model; quyền kiểm dưới ĐÚNG role production (CLAUDE.md §3.5)."""
import sqlalchemy as sa

from tests.conftest import expect_violation


def _article(db, url="https://zz.test/s15-1"):
    return db.execute(sa.text("INSERT INTO news.article (canonical_url, primary_source, fetched_at) VALUES (:u, 'cafef', now()) RETURNING article_id"),
                      {"u": url}).scalar_one()


def _industry(db, code="KIMLOAI"):
    return db.execute(sa.text("SELECT industry_id FROM market.industry WHERE code = :c"), {"c": code}).scalar_one()


def test_article_industry_pk_has_via_and_checks(db):
    a, i = _article(db), _industry(db)
    db.execute(sa.text("INSERT INTO news.article_industry (article_id, industry_id, via, confidence) VALUES (:a, :i, 'ai', 0.8)"), {"a": a, "i": i})
    db.execute(sa.text("INSERT INTO news.article_industry (article_id, industry_id, via) VALUES (:a, :i, 'ticker')"), {"a": a, "i": i})
    assert db.execute(sa.text("SELECT count(*) FROM news.article_industry WHERE article_id = :a"), {"a": a}).scalar_one() == 2
    assert expect_violation(db, f"INSERT INTO news.article_industry (article_id, industry_id, via) VALUES ({a}, {i}, 'ai')")        # PK trùng
    assert expect_violation(db, f"INSERT INTO news.article_industry (article_id, industry_id, via) VALUES ({a}, {i}, 'guess')")     # via lạ
    assert expect_violation(db, f"INSERT INTO news.article_industry (article_id, industry_id, via, confidence) VALUES ({a}, {i}, 'ai', 1.5)")
    assert expect_violation(db, f"INSERT INTO news.article_industry (article_id, industry_id, via) VALUES ({a}, 999999999, 'ai')")  # FK ngành


def test_llm_call_status_check_and_defaults(db):
    a = _article(db, "https://zz.test/s15-2")
    cid = db.execute(sa.text(
        "INSERT INTO ops.llm_call (purpose, model, thinking, article_id, status, input_tokens, cache_read_tokens, output_tokens, thinking_tokens, latency_ms)"
        " VALUES ('news.classify', 'MiniMax-M3', 'adaptive', :a, 'ok', 214, 2816, 250, 120, 5500) RETURNING call_id"), {"a": a}).scalar_one()
    row = db.execute(sa.text("SELECT http_calls, called_at IS NOT NULL, run_id FROM ops.llm_call WHERE call_id = :c"), {"c": cid}).one()
    assert tuple(row) == (1, True, None)
    assert expect_violation(db, "INSERT INTO ops.llm_call (purpose, model, thinking, status, latency_ms) VALUES ('p', 'm', 'adaptive', 'meh', 1)")
    assert expect_violation(db, "INSERT INTO ops.llm_call (purpose, model, thinking, status, latency_ms) VALUES ('p', 'm', 'deep', 'ok', 1)")


def test_every_path_of_the_classify_job_works_under_dlck_etl(db):
    """Mọi đường job đi qua — đọc lẫn ghi — dưới role thật: INSERT hai bảng mới, UPDATE article + revision.summary_ai,
    INSERT article_ticker, SELECT industry / v_issuer_industry / security."""
    a, i = _article(db, "https://zz.test/s15-3"), _industry(db)
    db.execute(sa.text("INSERT INTO news.article_revision (article_id, version, title, content, content_fetched_at) VALUES (:a, 1, 'T', 'C', now())"), {"a": a})
    sid = db.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, status) VALUES ('ZZS', 'ZZ', 'stock', 'listed') RETURNING security_id")).scalar_one()
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text("UPDATE news.article SET group_no = 3, sub = '3d', confidence = 0.9, classified_from = 'content', content_chars = 1, labels = '{}' WHERE article_id = :a"), {"a": a})
    db.execute(sa.text("UPDATE news.article_revision SET summary_ai = 'S' WHERE article_id = :a AND version = 1"), {"a": a})
    db.execute(sa.text("INSERT INTO news.article_ticker (article_id, security_id, via) VALUES (:a, :s, 'ai')"), {"a": a, "s": sid})
    db.execute(sa.text("INSERT INTO news.article_industry (article_id, industry_id, via, confidence) VALUES (:a, :i, 'ai', 0.9)"), {"a": a, "i": i})
    db.execute(sa.text("INSERT INTO ops.llm_call (purpose, model, thinking, article_id, status, latency_ms) VALUES ('news.classify', 'm', 'adaptive', :a, 'ok', 1)"), {"a": a})
    assert db.execute(sa.text("SELECT count(*) FROM market.industry WHERE level = 2")).scalar_one() == 24
    assert db.execute(sa.text("SELECT count(*) FROM market.v_issuer_industry")).scalar_one() >= 0
    assert db.execute(sa.text("SELECT summary_ai FROM news.article_revision WHERE article_id = :a"), {"a": a}).scalar_one() == "S"


def test_api_role_can_read_article_industry(db):
    a, i = _article(db, "https://zz.test/s15-4"), _industry(db)
    db.execute(sa.text("INSERT INTO news.article_industry (article_id, industry_id, via) VALUES (:a, :i, 'ticker')"), {"a": a, "i": i})
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert db.execute(sa.text("SELECT count(*) FROM news.article_industry WHERE article_id = :a"), {"a": a}).scalar_one() == 1
```

- [ ] **Step 2: Chạy thấy đỏ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/schema/test_s15_news_industry_llm_call.py -q`
Expected: 4 FAIL với `relation "news.article_industry" does not exist`.

- [ ] **Step 3: Code — `database/migrations/versions/0018_news_industry_llm_call.py`**

```python
"""Lát 9a — gắn ngành cho tin + sổ lời gọi model.

- news.article_industry: bài ↔ ngành level 2 (industry-tree.md, 24 ngành). Hai đường: 'ticker' = suy từ article_ticker qua
  market.v_issuer_industry (xác định, không confidence) · 'ai' = model đọc hiểu (mọi nhóm — chủ dự án 2026-09-06: tin vĩ mô
  trong nước/quốc tế cũng thuộc ngành). `via` TRONG PK như article_ticker: cùng (bài, ngành) do hai đường tìm ra là HAI dòng —
  phép đo "AI trùng suy-từ-mã bao nhiêu" chạy bằng SQL. Bảng riêng, không cột mảng: giữ FK, giữ via, giữ confidence.
- ops.llm_call: một dòng mỗi lời gọi model (token 4 loại, độ trễ, trạng thái) — đo token/thời gian là mục tiêu lát này, và
  lát 10 (chatbot) tính quota trên cùng sổ. `error` KHÔNG BAO GIỜ chứa khoá (core/llm chỉ ghi tên lớp + status).
- Quyền: default privileges của 0009 phủ (dlck_etl ghi news/ops, dlck_api đọc news) — test s15 chứng dưới role thật.

Revision ID: 0018
Revises: 0017
Create Date: 2026-09-06
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE news.article_industry (
          article_id  bigint  NOT NULL REFERENCES news.article,
          industry_id bigint  NOT NULL REFERENCES market.industry,      -- luôn level 2 (kỷ luật code; v_issuer_industry chỉ có level 2)
          via         text    NOT NULL CHECK (via IN ('ticker','ai')),
          confidence  numeric CHECK (confidence BETWEEN 0 AND 1),       -- NULL với 'ticker'
          PRIMARY KEY (article_id, industry_id, via)
        );
        CREATE INDEX ON news.article_industry (industry_id);            -- "mọi tin ngành thép" — truy vấn chủ lực

        CREATE TABLE ops.llm_call (
          call_id           bigint generated always as identity PRIMARY KEY,
          called_at         timestamptz NOT NULL DEFAULT now(),
          purpose           text NOT NULL,                              -- 'news.classify' · lát 10: 'chat'
          model             text NOT NULL,
          thinking          text NOT NULL CHECK (thinking IN ('adaptive','disabled')),
          run_id            bigint REFERENCES ops.etl_run,
          article_id        bigint REFERENCES news.article,
          status            text NOT NULL CHECK (status IN ('ok','repaired','failed')),
          http_calls        smallint NOT NULL DEFAULT 1,                -- 2 khi phải gọi lại sửa schema
          input_tokens      int,
          cache_read_tokens int,
          output_tokens     int,
          thinking_tokens   int,
          latency_ms        int NOT NULL,
          error             text                                        -- 'rate_limit: RateLimitError 429' — không khoá
        );
        CREATE INDEX ON ops.llm_call (purpose, called_at);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE ops.llm_call;
        DROP TABLE news.article_industry;
        """
    )
```

- [ ] **Step 4: Vá `_cleanup` ở `tests/etl/test_e56_news_job.py`** — đổi dòng 102 thành:

```python
        for t in ("news.article_industry", "ops.llm_call", "news.article_ticker", "news.article_source", "news.article_revision", "news.article"):
```

- [ ] **Step 5: Chạy thấy xanh — schema + toàn bộ etl news (fixture dựng lại DB nên chạy chung)**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/schema tests/etl/test_e56_news_job.py tests/etl/test_e57_news_backfill.py -q`
Expected: tất cả pass; `test_s15` 4 passed. Nếu `test_s09_grants` đỏ vì liệt kê bảng: đọc assertion — default privileges phải cấp `dlck_etl` SELECT/INSERT/UPDATE/DELETE trên hai bảng mới; nếu test đó quét `information_schema.role_table_grants` thì hai bảng mới đã có grant qua default privileges — sửa expected của test đó (thêm hai bảng) chứ không thêm GRANT vào migration.

- [ ] **Step 6: Commit**

```bash
git add database/migrations/versions/0018_news_industry_llm_call.py backend/tests/schema/test_s15_news_industry_llm_call.py backend/tests/etl/test_e56_news_job.py
git commit -m "feat(db): 0018 news.article_industry (ticker/ai) and ops.llm_call"
```

---

### Task 4: `news_classify.py` phần thuần — schema Pydantic động, system prompt, user prompt

**Files:**
- Create: `backend/etl/news_classify.py` (phần thuần; Task 5–6 nối thêm)
- Test: `backend/tests/etl/test_e59_news_classify.py`

**Interfaces:**
- Produces: `GROUPS`, `SUBS`, `ALL_SUBS`, `CAP_CHARS = 3000`, `TITLE_ONLY_BELOW = 200`; `Row(article_id, primary_source, feed, group_from_feed, ticker_step_ran, url, title, sapo, content)` frozen dataclass; `build_schema(industry_codes: Sequence[str]) -> type[BaseModel]` (tên lớp `Classification`, trường `group, sub, confidence, summary_ai, tickers, industries`); `system_prompt(industries: Sequence[tuple[str, str]]) -> str`; `user_prompt(row: Row, cap: int = CAP_CHARS) -> tuple[str, int, str]` (text, content_chars, classified_from).

- [ ] **Step 1: Test đỏ — `tests/etl/test_e59_news_classify.py`**

```python
"""Phần thuần của lưới phân loại: schema công cụ (enum là thứ cho 0 lỗi schema — minimax.md §5), prompt, trần cắt, đường lui title_only."""
import pytest
from pydantic import ValidationError

from etl import news_classify as nc

CODES = ["NGANHANG", "CHUNGKHOAN", "BAOHIEM", "DANDUNG", "KHUCONGNGHIEP", "XAYDUNG", "VATLIEU", "KIMLOAI", "KHOANGSAN", "HOACHAT", "NHUA", "THIETBI",
         "NONGNGHIEP", "THUYSAN", "DETMAY", "CAOSU", "BANLE", "THUCPHAM", "DULICH", "YTE", "TIENICH", "DAUKHI", "VANTAI", "CONGNGHE"]
INDUSTRIES = [(c, f"Tên {c}") for c in CODES]
GOOD = {"group": "3", "sub": "3d", "confidence": 0.9, "summary_ai": "Tóm tắt.", "tickers": ["HPG"], "industries": ["KIMLOAI"]}


def _row(content, hint=3, title="Tiêu đề HPG", sapo="Sapo", src="cafef", feed="chung-khoan"):
    return nc.Row(1, src, feed, hint, hint == 3, "https://cafef.vn/a.chn", title, sapo, content)


def test_schema_enums_and_shape():
    S = nc.build_schema(CODES)
    js = S.model_json_schema()
    assert S.__name__ == "Classification" and js["additionalProperties"] is False
    assert set(js["required"]) == {"group", "sub", "confidence", "summary_ai", "tickers", "industries"}
    assert js["properties"]["group"]["enum"] == ["1", "2", "3", "x"]
    assert len(js["properties"]["sub"]["enum"]) == 21 and "3i" in js["properties"]["sub"]["enum"] and "x" in js["properties"]["sub"]["enum"]
    assert js["properties"]["industries"]["items"]["enum"] == CODES                 # đúng thứ tự đưa vào
    v = S.model_validate(GOOD)
    assert v.group == "3" and v.industries == ["KIMLOAI"]
    assert S.model_validate(dict(GOOD, group="x", sub="x", tickers=[], industries=[])).sub == "x"


@pytest.mark.parametrize("bad", [dict(GOOD, sub="1a"), dict(GOOD, confidence=1.2), dict(GOOD, industries=["THEP"]), dict(GOOD, extra=1),
                                 dict(GOOD, group="x")])
def test_schema_rejects_sub_outside_group_bad_confidence_unknown_industry_extra(bad):
    with pytest.raises(ValidationError):
        nc.build_schema(CODES).model_validate(bad)


def test_build_schema_rejects_duplicate_or_empty_codes():
    with pytest.raises(ValueError):
        nc.build_schema(["A", "A"])
    with pytest.raises(ValueError):
        nc.build_schema([])


def test_system_prompt_lists_industries_from_input_not_hardcoded():
    s = nc.system_prompt(INDUSTRIES)
    assert s.count(" — Tên ") == 24 and "KIMLOAI — Tên KIMLOAI" in s
    assert "3i Xếp hạng tín nhiệm và ESG" in s and "tối đa 3" in s
    assert nc.system_prompt([("ZZNGANH", "Ngành thử")]).count(" — ") == 1


def test_user_prompt_cuts_at_cap_and_reports_chars():
    text, n, cf = nc.user_prompt(_row("a" * 5000), cap=3000)
    assert (n, cf) == (3000, "content")
    assert "nhóm gợi ý: 3" in text and "Tiêu đề: Tiêu đề HPG" in text and "Sapo: Sapo" in text and "(đã cắt 3000 ký tự)" in text
    assert text.endswith("a" * 3000) and "a" * 3001 not in text


def test_user_prompt_title_only_below_200_and_missing_hint():
    text, n, cf = nc.user_prompt(_row("b" * 150, hint=None), cap=3000)
    assert (n, cf) == (150, "title_only") and "nhóm gợi ý: không có" in text
    text2, n2, cf2 = nc.user_prompt(_row("", hint=1, sapo=None))
    assert (n2, cf2) == (0, "title_only") and "Sapo: \n" in text2
    assert nc.user_prompt(_row("c" * 200))[1:] == (200, "content")                 # biên: đúng 200 là content
```

- [ ] **Step 2: Chạy thấy đỏ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e59_news_classify.py -q`
Expected: `ModuleNotFoundError: No module named 'etl.news_classify'`.

- [ ] **Step 3: Code — `backend/etl/news_classify.py` (phần thuần)**

```python
"""Lưới AI phân loại tin (lát 9a, spec 2026-09-06-news-classify-llm): taxonomy 3 nhóm / 20 sub / x (news-pipeline §3, §7),
gắn mã tầng 3 (§8: mã AI LỌC qua danh sách niêm yết — model bịa `VFM`, minimax.md §7.1), gắn NGÀNH hai đường
(`ticker` suy từ mã, `ai` đọc hiểu, mọi nhóm). Danh sách 24 ngành NẠP TỪ market.industry lúc chạy — industry-tree.md là chủ,
không chép cứng (chatbot-semantic-layer §3.2). Schema công cụ có enum cho mọi trường phân loại: đó là thứ cho 0 lỗi/232 lời gọi.
Phần thuần (schema, prompt) ở trên; phần DB (chọn bài, ghi) và job ở dưới. Mọi lượt có TRẦN, không có chế độ chạy hết."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator

CAP_CHARS = 3000              # trần ký tự thân bài nạp model (news-pipeline §12: 3.000 hay 4.000 chốt sau khi có ca sai thật)
TITLE_ONLY_BELOW = 200        # thân < 200 ký tự (CafeF CBTT) ⇒ classified_from='title_only' (§7.1b)
GROUPS = ("1", "2", "3", "x")
SUBS = {"1": ["1a", "1b", "1c", "1d", "1e", "1f"], "2": ["2a", "2b", "2c", "2d", "2e"],
        "3": ["3a", "3b", "3c", "3d", "3e", "3f", "3g", "3h", "3i"], "x": ["x"]}
ALL_SUBS = [s for v in SUBS.values() for s in v]

# Khối tĩnh — đặt đầu system để cache tự động (≥ 512 token, minimax.md §6). Taxonomy chép từ news-pipeline §3 (đã đo 232 lời gọi).
SYSTEM_TAXONOMY = """Bạn là bộ phân loại tin tài chính Việt Nam của dulieuchungkhoan.vn. Đọc toàn văn bài và trả về đúng một lời gọi công cụ Classification.
Taxonomy 3 nhóm / 20 sub; nhãn x = loại bỏ (tin xã hội, thể thao, giáo dục, y tế thuần; PR, advertorial) — khi group = x thì sub = x.
Nhóm 1 · Vĩ mô trong nước: 1a Thể chế và văn bản pháp quy · 1b Điều hành Chính phủ (gồm kiến nghị, tiếng nói khu vực tư nhân) · 1c Tiền tệ và tỷ giá · 1d Đầu tư công và hạ tầng · 1e Số liệu vĩ mô · 1f Thuế và ngân sách.
Nhóm 2 · Tài chính quốc tế: 2a Chứng khoán thế giới · 2b Ngân hàng trung ương · 2c Hàng hoá và năng lượng · 2d An ninh và địa chính trị · 2e Thương mại và thuế quan.
Nhóm 3 · Doanh nghiệp niêm yết: 3a CBTT và sự kiện quyền · 3b Giao dịch nội bộ và cổ đông lớn · 3c Vốn và cấu trúc · 3d KQKD và vận hành · 3e Nhận định và diễn biến thị trường · 3f Phái sinh, chứng quyền, ETF/quỹ · 3g Vi phạm và xử phạt · 3h Margin và ký quỹ · 3i Xếp hạng tín nhiệm và ESG."""

SYSTEM_RULES = """Quy tắc: nhóm gợi ý từ feed chỉ là tín hiệu, được phép ghi đè (1↔3 nhảy thường xuyên). confidence trong [0,1].
summary_ai: 2–3 câu, 200–300 ký tự, không mở đầu bằng "Bài viết nói về", giữ nguyên mọi con số trong bản gốc.
tickers: mã niêm yết HOSE/HNX/UPCoM là chủ thể của bài (chỉ khi nhóm 3), rỗng nếu không có; không bịa.
industries: mã ngành (trong danh sách trên) mà bài liên quan TRỰC TIẾP — áp cho mọi nhóm (tin chính sách, giá hàng hoá, thuế quan cũng thuộc ngành);
tối đa 3 ngành, xếp ngành liên quan nhất trước; rỗng nếu bài không thuộc ngành nào (vĩ mô thuần, tin loại bỏ)."""


@dataclass(frozen=True)
class Row:
    article_id: int
    primary_source: str
    feed: str | None
    group_from_feed: int | None
    ticker_step_ran: bool
    url: str                       # canonical_url — tầng 1 (CafeF CBTT) đọc mã từ đây
    title: str
    sapo: str | None
    content: str | None


class _ClassificationBase(BaseModel):
    """Kết quả phân loại một bài"""
    model_config = ConfigDict(extra="forbid")
    group: Literal["1", "2", "3", "x"]
    sub: Literal[tuple(ALL_SUBS)]        # noqa: F821 — Literal nhận tuple như nhiều đối số
    confidence: float = Field(ge=0, le=1)
    summary_ai: str
    tickers: list[str]

    @model_validator(mode="after")
    def _sub_in_group(self):
        if self.sub not in SUBS[self.group]:
            raise ValueError(f"sub {self.sub} không thuộc nhóm {self.group}")
        return self


def build_schema(industry_codes: Sequence[str]) -> type[BaseModel]:
    codes = tuple(industry_codes)
    if not codes or len(codes) != len(set(codes)):
        raise ValueError(f"danh sách ngành rỗng hoặc trùng: {codes}")
    return create_model("Classification", __base__=_ClassificationBase, __doc__="Kết quả phân loại một bài",
                        industries=(list[Literal[codes]], ...))   # type: ignore[valid-type]


def system_prompt(industries: Sequence[tuple[str, str]]) -> str:
    lines = "\n".join(f"{code} — {name}" for code, name in industries)
    return f"{SYSTEM_TAXONOMY}\nNgành (level 2 của dulieuchungkhoan.vn — dùng đúng mã):\n{lines}\n{SYSTEM_RULES}"


def user_prompt(row: Row, cap: int = CAP_CHARS) -> tuple[str, int, str]:
    body = (row.content or "")[:cap]
    n = len(body)
    classified_from = "content" if n >= TITLE_ONLY_BELOW else "title_only"
    hint = row.group_from_feed if row.group_from_feed is not None else "không có"
    text = (f"Nguồn: {row.primary_source} · feed: {row.feed or ''} · nhóm gợi ý: {hint}\nTiêu đề: {row.title}\nSapo: {row.sapo or ''}\n\n"
            f"Toàn văn (đã cắt {cap} ký tự):\n{body}")
    return text, n, classified_from
```

Nếu `Literal[tuple(ALL_SUBS)]` bị Pydantic/Python từ chối trong thân lớp: thay bằng `sub: Literal["1a","1b","1c","1d","1e","1f","2a","2b","2c","2d","2e","3a","3b","3c","3d","3e","3f","3g","3h","3i","x"]` và giữ `ALL_SUBS` để test đối chiếu độ dài 21; `industries` trong `build_schema` dùng `Literal.__getitem__(codes)`.

- [ ] **Step 4: Chạy thấy xanh**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e59_news_classify.py -q`
Expected: `10 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/etl/news_classify.py backend/tests/etl/test_e59_news_classify.py
git commit -m "feat(etl): classification schema with industry enum, system/user prompts"
```

---

### Task 5: `news_classify.py` phần DB — `select_articles`, `apply`, `log_call`

**Files:**
- Modify: `backend/etl/news_classify.py` (nối sau phần thuần)
- Test: `backend/tests/etl/test_e60_classify_job.py` (phần 1; Task 6 nối thêm)

**Interfaces:**
- Consumes: Task 4 (`Row`, `build_schema`), `etl.news_tag.tickers_from_url/tickers_lookup`, `etl.news_store.load_listed`, Task 1 `Usage`.
- Produces: `select_articles(conn, *, limit: int | None = None, per_group: int | None = None) -> list[Row]`; `apply(conn, row, value, *, content_chars, classified_from, listed: dict[str, int], industry_ids: dict[str, int]) -> dict` với khoá `overridden, tickers_url, tickers_lookup, tickers_ai, tickers_ai_dropped, industries_ai, industries_ticker` (int); `log_call(conn, *, run_id, article_id, model, thinking, status, usage: Usage | None, latency_s: float, error: str | None = None) -> None`.

- [ ] **Step 1: Test đỏ — `tests/etl/test_e60_classify_job.py` (phần 1)**

```python
"""Lưới phân loại trên Postgres thật: chọn bài có trần, ghi article/revision/ticker/industry hai đường, sổ llm_call, guard quota,
cầu chì ModelDown, --dry-run không ghi. Client giả trả Structured theo kịch bản — không gọi model thật trong CI (test-strategy luật 1)."""
import json
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import sqlalchemy as sa

from core.llm import LLMError, QuotaRemains, Structured, Usage
from etl import news_classify as nc

VN = timezone(timedelta(hours=7))
CODES = ["NGANHANG", "CHUNGKHOAN", "BAOHIEM", "DANDUNG", "KHUCONGNGHIEP", "XAYDUNG", "VATLIEU", "KIMLOAI", "KHOANGSAN", "HOACHAT", "NHUA", "THIETBI",
         "NONGNGHIEP", "THUYSAN", "DETMAY", "CAOSU", "BANLE", "THUCPHAM", "DULICH", "YTE", "TIENICH", "DAUKHI", "VANTAI", "CONGNGHE"]
LONG = "Nội dung bài thử dài hơn hai trăm ký tự để classified_from là content. " * 5      # 350 ký tự
# (canonical_url, hint, giờ đăng, ticker_step_ran, tiêu đề) — mới nhất trước; A4/A5 cùng bucket NULL
ARTICLES = [("https://zz.test/classify-1", 1, "2026-09-06T10:00:00+07", False, "ZZ bài 1 thép tăng giá"),
            ("https://zz.test/classify-2", 2, "2026-09-06T09:00:00+07", False, "ZZ bài 2 Fed giữ lãi suất"),
            ("https://zz.test/classify-3", 3, "2026-09-06T08:00:00+07", True, "ZZ bài 3 ZZK báo lãi"),
            ("https://zz.test/classify-4", None, "2026-09-06T07:00:00+07", False, "ZZQ tăng vốn"),
            ("https://zz.test/classify-5", None, "2026-09-06T06:00:00+07", False, "ZZ bài 5 không nhóm")]


def _cleanup(engine):
    with engine.begin() as c:
        for t in ("news.article_industry", "ops.llm_call", "news.article_ticker", "news.article_source", "news.article_revision", "news.article"):
            c.execute(sa.text(f"DELETE FROM {t} WHERE {'article_id' if t != 'news.article' else 'article_id'} IN"
                              " (SELECT article_id FROM news.article WHERE canonical_url LIKE 'https://zz.test/classify-%')"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = 'news.classify'"))
        c.execute(sa.text("DELETE FROM market.security WHERE exchange = 'ZZ'"))
        c.execute(sa.text("DELETE FROM market.issuer WHERE name LIKE 'ZZ %'"))


@pytest.fixture()
def seeded(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.news_classify.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    with migrated_engine.begin() as c:
        kim = c.execute(sa.text("SELECT industry_id FROM market.industry WHERE code = 'KIMLOAI'")).scalar_one()
        i1 = c.execute(sa.text("INSERT INTO market.issuer (name, industry_id) VALUES ('ZZ Kim loai', :i) RETURNING issuer_id"), {"i": kim}).scalar_one()
        i2 = c.execute(sa.text("INSERT INTO market.issuer (name) VALUES ('ZZ Quy') RETURNING issuer_id")).scalar_one()
        c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, status, issuer_id)"
                          " VALUES ('ZZK', 'ZZ', 'stock', 'listed', :a), ('ZZQ', 'ZZ', 'stock', 'listed', :b)"), {"a": i1, "b": i2})
        ids = []
        for url, hint, pub, ran, title in ARTICLES:
            aid = c.execute(sa.text(
                "INSERT INTO news.article (canonical_url, primary_source, feed, published_at, published_at_src, fetched_at, group_from_feed, ticker_step_ran)"
                " VALUES (:u, 'cafef', 'zz', :p, 'feed', now(), :g, :r) RETURNING article_id"), {"u": url, "p": pub, "g": hint, "r": ran}).scalar_one()
            c.execute(sa.text("INSERT INTO news.article_revision (article_id, version, title, sapo, content, content_fetched_at)"
                              " VALUES (:a, 1, :t, 'Sapo', :c, now())"), {"a": aid, "t": title, "c": LONG})
            ids.append(aid)
    yield migrated_engine, ids
    _cleanup(migrated_engine)


def _ctx(engine):
    with engine.connect() as c:
        inds = c.execute(sa.text("SELECT industry_id, code, name_vi FROM market.industry WHERE level = 2 ORDER BY sort_order, code")).all()
        listed = dict(c.execute(sa.text("SELECT ticker, security_id FROM market.security WHERE status = 'listed'")).all())
    return {r.code: r.industry_id for r in inds}, listed, nc.build_schema([r.code for r in inds])


def _n(engine, sql, **p):
    with engine.connect() as c:
        return c.execute(sa.text(sql), p).scalar()


def test_select_per_group_takes_newest_per_bucket_and_skips_classified(seeded):
    engine, ids = seeded
    with engine.connect() as c:
        rows = nc.select_articles(c, per_group=1)
        assert [r.article_id for r in rows] == ids[:4]                                # 1 · 2 · 3 · NULL (A4 mới hơn A5)
        assert rows[0].title == "ZZ bài 1 thép tăng giá" and rows[0].content == LONG and rows[3].group_from_feed is None
        assert [r.article_id for r in nc.select_articles(c, limit=2)] == ids[:2]
    with engine.begin() as c:
        c.execute(sa.text("UPDATE news.article SET classified_from = 'content' WHERE article_id = :a"), {"a": ids[0]})
    with engine.connect() as c:
        assert [r.article_id for r in nc.select_articles(c, per_group=1)] == ids[1:4]
        assert len(nc.select_articles(c, per_group=5)) == 4                            # NULL bucket: A4 + A5


def test_apply_group3_with_ai_ticker_filter_and_industries_both_ways(seeded):
    engine, ids = seeded
    industry_ids, listed, S = _ctx(engine)
    v = S.model_validate({"group": "3", "sub": "3d", "confidence": 0.9, "summary_ai": "Tóm tắt 1", "tickers": ["ZZK", "VFM"], "industries": ["KIMLOAI", "XAYDUNG"]})
    with engine.connect() as c:
        row = [r for r in nc.select_articles(c, per_group=1) if r.article_id == ids[0]][0]
    with engine.begin() as c:
        st = nc.apply(c, row, v, content_chars=350, classified_from="content", listed=listed, industry_ids=industry_ids)
    assert st == {"overridden": 1, "tickers_url": 0, "tickers_lookup": 0, "tickers_ai": 1, "tickers_ai_dropped": 1, "industries_ai": 2, "industries_ticker": 1}
    with engine.connect() as c:
        a = c.execute(sa.text("SELECT group_no, sub, confidence, classified_from, content_chars, group_overridden, labels, ticker_step_ran"
                              " FROM news.article WHERE article_id = :a"), {"a": ids[0]}).one()
        assert tuple(a) == (3, "3d", 0.9, "content", 350, True, [], True)
        assert c.execute(sa.text("SELECT summary_ai FROM news.article_revision WHERE article_id = :a AND version = 1"), {"a": ids[0]}).scalar_one() == "Tóm tắt 1"
        tk = c.execute(sa.text("SELECT s.ticker, t.via FROM news.article_ticker t JOIN market.security s USING (security_id) WHERE t.article_id = :a"), {"a": ids[0]}).all()
        assert [tuple(x) for x in tk] == [("ZZK", "ai")]
        ind = c.execute(sa.text("SELECT i.code, x.via, x.confidence FROM news.article_industry x JOIN market.industry i USING (industry_id)"
                                " WHERE x.article_id = :a ORDER BY x.via, i.code"), {"a": ids[0]}).all()
        assert [tuple(x) for x in ind] == [("KIMLOAI", "ai", 0.9), ("XAYDUNG", "ai", 0.9), ("KIMLOAI", "ticker", None)]
    with engine.begin() as c:                                                             # idempotent
        st2 = nc.apply(c, row, v, content_chars=350, classified_from="content", listed=listed, industry_ids=industry_ids)
    assert st2["industries_ticker"] == 0 and _n(engine, "SELECT count(*) FROM news.article_industry WHERE article_id = :a", a=ids[0]) == 3
    assert _n(engine, "SELECT count(*) FROM news.article_ticker WHERE article_id = :a", a=ids[0]) == 1


def test_apply_x_label_and_tier2_catchup_for_ungrouped(seeded):
    engine, ids = seeded
    industry_ids, listed, S = _ctx(engine)
    with engine.connect() as c:
        rows = {r.article_id: r for r in nc.select_articles(c, per_group=5)}
    x = S.model_validate({"group": "x", "sub": "x", "confidence": 0.6, "summary_ai": "PR.", "tickers": [], "industries": []})
    with engine.begin() as c:
        st = nc.apply(c, rows[ids[1]], x, content_chars=350, classified_from="content", listed=listed, industry_ids=industry_ids)
    assert st["overridden"] == 1
    with engine.connect() as c:
        a = c.execute(sa.text("SELECT group_no, sub, confidence, labels, ticker_step_ran FROM news.article WHERE article_id = :a"), {"a": ids[1]}).one()
        assert tuple(a) == (None, None, 0.6, ["x"], False)
    g3 = S.model_validate({"group": "3", "sub": "3c", "confidence": 0.8, "summary_ai": "Tăng vốn.", "tickers": [], "industries": ["CHUNGKHOAN", "CHUNGKHOAN"]})
    with engine.begin() as c:
        st = nc.apply(c, rows[ids[3]], g3, content_chars=350, classified_from="content", listed=listed, industry_ids=industry_ids)
    assert st == {"overridden": 0, "tickers_url": 0, "tickers_lookup": 1, "tickers_ai": 0, "tickers_ai_dropped": 0, "industries_ai": 1, "industries_ticker": 0}
    with engine.connect() as c:
        tk = c.execute(sa.text("SELECT s.ticker, t.via FROM news.article_ticker t JOIN market.security s USING (security_id) WHERE t.article_id = :a"), {"a": ids[3]}).all()
        assert [tuple(x) for x in tk] == [("ZZQ", "lookup")]                                # ZZQ không có ngành ⇒ 0 dòng 'ticker'
        assert c.execute(sa.text("SELECT ticker_step_ran, group_overridden FROM news.article WHERE article_id = :a"), {"a": ids[3]}).one() == (True, False)
    g1 = S.model_validate({"group": "1", "sub": "1c", "confidence": 0.7, "summary_ai": "Tỷ giá.", "tickers": ["ZZK"], "industries": ["NGANHANG"]})
    with engine.begin() as c:
        st = nc.apply(c, rows[ids[2]], g1, content_chars=350, classified_from="content", listed=listed, industry_ids=industry_ids)
    assert st["overridden"] == 1 and st["tickers_ai"] == 0                                 # nhóm ≠ 3: không chạm mã (tickers bị bỏ)
    assert _n(engine, "SELECT count(*) FROM news.article_ticker WHERE article_id = :a", a=ids[2]) == 0


def test_log_call_writes_tokens_and_failed_without_key(seeded):
    engine, ids = seeded
    with engine.begin() as c:
        nc.log_call(c, run_id=None, article_id=ids[0], model="MiniMax-M3", thinking="adaptive", status="ok", usage=Usage(214, 2816, 250, 120, 1, 5.5), latency_s=5.5)
        nc.log_call(c, run_id=None, article_id=ids[1], model="MiniMax-M3", thinking="disabled", status="failed", usage=None, latency_s=0.3, error="rate_limit: RateLimitError 429")
    with engine.connect() as c:
        rows = c.execute(sa.text("SELECT status, http_calls, input_tokens, cache_read_tokens, output_tokens, thinking_tokens, latency_ms, error"
                                 " FROM ops.llm_call WHERE purpose = 'news.classify' ORDER BY call_id")).all()
    assert [tuple(r) for r in rows] == [("ok", 1, 214, 2816, 250, 120, 5500, None), ("failed", 1, None, None, None, None, 300, "rate_limit: RateLimitError 429")]
```

- [ ] **Step 2: Chạy thấy đỏ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e60_classify_job.py -q`
Expected: 4 FAIL, `AttributeError: module 'etl.news_classify' has no attribute 'select_articles'` (và `load_dotenv` chưa import ⇒ monkeypatch lỗi — thêm import ở Step 3 trước).

- [ ] **Step 3: Code — nối vào `backend/etl/news_classify.py`** (thêm import đầu file: `import sqlalchemy as sa`, `from core.env import load_dotenv`, `from core.llm import Usage`, `from etl import news_tag`)

```python
PURPOSE = "news.classify"
MAX_INDUSTRIES = 3


def _bucket_sql(hint) -> str:
    return "a.group_from_feed IS NULL" if hint is None else "a.group_from_feed = :g"


_SELECT = """
SELECT a.article_id, a.primary_source, a.feed, a.group_from_feed, a.ticker_step_ran, a.canonical_url, r.title, r.sapo, r.content
FROM news.article a
JOIN LATERAL (SELECT title, sapo, content FROM news.article_revision r WHERE r.article_id = a.article_id ORDER BY version DESC LIMIT 1) r ON true
WHERE a.classified_from IS NULL AND {bucket}
ORDER BY a.published_at DESC NULLS LAST, a.article_id DESC
LIMIT :n"""


def select_articles(conn, *, limit: int | None = None, per_group: int | None = None) -> list[Row]:
    """Bài chưa phân loại, mới nhất trước (spec §4.2-XI). per_group: N bài đầu của MỖI bucket group_from_feed 1 · 2 · 3 · NULL."""
    if (limit is None) == (per_group is None):
        raise ValueError("cần đúng một trong limit / per_group")
    out: list[Row] = []
    if limit is not None:
        rows = conn.execute(sa.text(_SELECT.format(bucket="true")), {"n": limit}).all()
        return [Row(*r) for r in rows]
    for hint in (1, 2, 3, None):
        rows = conn.execute(sa.text(_SELECT.format(bucket=_bucket_sql(hint))), {"n": per_group, "g": hint}).all()
        out.extend(Row(*r) for r in rows)
    return out


def apply(conn, row: Row, value, *, content_chars: int, classified_from: str, listed: dict[str, int], industry_ids: dict[str, int]) -> dict:
    """Ghi MỘT bài trong giao dịch của caller. x ⇒ group_no NULL + labels {x} (0007). Mã: chỉ nhóm 3 — tầng 2 bù nếu chưa chạy
    (bài backfill), tầng 3 = mã model ∩ niêm yết. Ngành: 'ai' từ model (≤ 3), 'ticker' từ MỌI article_ticker qua v_issuer_industry."""
    st = {"overridden": 0, "tickers_url": 0, "tickers_lookup": 0, "tickers_ai": 0, "tickers_ai_dropped": 0, "industries_ai": 0, "industries_ticker": 0}
    group_no = None if value.group == "x" else int(value.group)
    sub = None if value.group == "x" else value.sub
    overridden = row.group_from_feed is not None and group_no != row.group_from_feed
    st["overridden"] = int(overridden)
    conn.execute(sa.text(
        "UPDATE news.article SET group_no = :g, sub = :s, confidence = :c, classified_from = :cf, content_chars = :cc,"
        " group_overridden = :o, labels = :l, ticker_step_ran = ticker_step_ran OR :g3 WHERE article_id = :a"),
        {"g": group_no, "s": sub, "c": value.confidence, "cf": classified_from, "cc": content_chars, "o": overridden,
         "l": ["x"] if group_no is None else [], "g3": group_no == 3, "a": row.article_id})
    conn.execute(sa.text(
        "UPDATE news.article_revision SET summary_ai = :s WHERE article_id = :a AND summary_ai IS NULL"
        " AND version = (SELECT max(version) FROM news.article_revision WHERE article_id = :a)"), {"s": value.summary_ai, "a": row.article_id})
    if group_no == 3:
        tickers: list[tuple[str, str]] = []
        if not row.ticker_step_ran:                                    # tầng 1–2 chưa chạy (group_from_feed ≠ 3 ở lát 8) ⇒ chạy bù
            for t in news_tag.tickers_from_url(row.url):
                if t in listed:
                    tickers.append((t, "url"))
                    st["tickers_url"] += 1
            for t in news_tag.tickers_lookup(row.title, row.sapo, listed):
                tickers.append((t, "lookup"))
                st["tickers_lookup"] += 1
        for t in dict.fromkeys(x.strip().upper() for x in value.tickers if x.strip()):
            if t in listed:
                tickers.append((t, "ai"))
                st["tickers_ai"] += 1
            else:
                st["tickers_ai_dropped"] += 1                          # VFM bịa (minimax.md §7.1) — không vào kho
        for t, via in tickers:
            conn.execute(sa.text("INSERT INTO news.article_ticker (article_id, security_id, via) VALUES (:a, :s, :v) ON CONFLICT DO NOTHING"),
                         {"a": row.article_id, "s": listed[t], "v": via})
    for code in list(dict.fromkeys(value.industries))[:MAX_INDUSTRIES]:
        conn.execute(sa.text("INSERT INTO news.article_industry (article_id, industry_id, via, confidence) VALUES (:a, :i, 'ai', :c) ON CONFLICT DO NOTHING"),
                     {"a": row.article_id, "i": industry_ids[code], "c": value.confidence})
        st["industries_ai"] += 1
    st["industries_ticker"] = conn.execute(sa.text(
        "INSERT INTO news.article_industry (article_id, industry_id, via)"
        " SELECT DISTINCT t.article_id, v.industry_id, 'ticker' FROM news.article_ticker t"
        " JOIN market.security s USING (security_id) JOIN market.v_issuer_industry v ON v.issuer_id = s.issuer_id"
        " WHERE t.article_id = :a AND v.industry_id IS NOT NULL ON CONFLICT DO NOTHING"), {"a": row.article_id}).rowcount
    return st


def log_call(conn, *, run_id, article_id, model: str, thinking: str, status: str, usage: Usage | None, latency_s: float, error: str | None = None) -> None:
    u = usage
    conn.execute(sa.text(
        "INSERT INTO ops.llm_call (purpose, model, thinking, run_id, article_id, status, http_calls, input_tokens, cache_read_tokens,"
        " output_tokens, thinking_tokens, latency_ms, error)"
        " VALUES (:p, :m, :t, :r, :a, :s, :hc, :i, :c, :o, :th, :ms, :e)"),
        {"p": PURPOSE, "m": model, "t": thinking, "r": run_id, "a": article_id, "s": status, "hc": u.calls if u else 1,
         "i": u.input_tokens if u else None, "c": u.cache_read_tokens if u else None, "o": u.output_tokens if u else None,
         "th": u.thinking_tokens if u else None, "ms": int(round(latency_s * 1000)), "e": error})
```

- [ ] **Step 4: Chạy thấy xanh**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e60_classify_job.py tests/etl/test_e59_news_classify.py -q`
Expected: `14 passed`. Nếu `labels` không bind được (`can't adapt type 'list'`): dùng `sa.bindparam("l", type_=sa.ARRAY(sa.Text))` trên `sa.text(...).bindparams(...)`. Nếu `confidence` trả `Decimal('0.9')` khiến `== 0.9` đỏ: đúng là numeric — đổi assertion sang `float(a[2]) == 0.9` **và** ghi vào báo cáo (không đổi kiểu cột).

- [ ] **Step 5: Commit**

```bash
git add backend/etl/news_classify.py backend/tests/etl/test_e60_classify_job.py
git commit -m "feat(etl): select/apply/log for news classification with two-way industry tagging"
```

---

### Task 6: `classify_run` + `run` + CLI `etl classify`

**Files:**
- Modify: `backend/etl/news_classify.py` (nối), `backend/etl/__main__.py` (thêm subcommand trước khối `if args[0] in ("fred", …)`; sửa thông điệp cuối "subcommand không hợp lệ" thêm `classify`)
- Test: `backend/tests/etl/test_e60_classify_job.py` (phần 2), `backend/tests/etl/test_e61_classify_cli.py`

**Interfaces:**
- Consumes: Task 2 (`LLMClient`, `Structured`, `QuotaRemains`, `LLMError`), Task 5.
- Produces: `ModelDown(Exception)` với `.stats`; `classify_run(engine, client, rows, *, run_id, schema, system, thinking, listed, industry_ids, dry_run=False, out=None, max_minutes=None, cap=CAP_CHARS, clock=time.monotonic) -> dict`; `run(limit=None, per_group=None, thinking="adaptive", dry_run=False, out=None, max_minutes=None, cap=CAP_CHARS, client=None, clock=time.monotonic) -> int`; CLI `etl classify`.

- [ ] **Step 1: Test đỏ — nối vào `tests/etl/test_e60_classify_job.py`**

```python
class FakeClient:
    """Trả Structured theo kịch bản (dict ⇒ ok, Exception ⇒ raise). quota: (interval_pct, weekly_pct)."""
    def __init__(self, results, quota=(97, 86)):
        self.results, self.quota, self.calls, self.quota_calls = list(results), quota, 0, 0
        self.settings = SimpleNamespace(model="MiniMax-M3")

    def token_plan_remains(self):
        self.quota_calls += 1
        return QuotaRemains(self.quota[0], self.quota[1], {})

    def structured(self, schema, *, system, user, thinking="adaptive", **kw):
        self.calls += 1
        r = self.results.pop(0)
        if isinstance(r, Exception):
            raise r
        return Structured(schema.model_validate(r["value"]), Usage(2000, 1300, 500, 200, 1, r["lat"]), r.get("repaired", False), "tool_use")


R1 = {"value": {"group": "3", "sub": "3d", "confidence": 0.9, "summary_ai": "Tóm tắt 1", "tickers": ["ZZK", "VFM"], "industries": ["KIMLOAI", "XAYDUNG"]}, "lat": 1.0}
R2 = {"value": {"group": "x", "sub": "x", "confidence": 0.6, "summary_ai": "PR.", "tickers": [], "industries": []}, "lat": 2.0}
R4 = {"value": {"group": "3", "sub": "3c", "confidence": 0.8, "summary_ai": "Tăng vốn.", "tickers": [], "industries": ["CHUNGKHOAN"]}, "lat": 4.0, "repaired": True}
SCHEMA_ERR = LLMError("schema", retryable=False, detail="sub: không thuộc nhóm")


def _run_row(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job = 'news.classify' ORDER BY run_id DESC LIMIT 1")).one()


def test_run_writes_stats_and_llm_calls_and_keeps_failed_article_null(seeded):
    engine, ids = seeded
    fake = FakeClient([R1, R2, SCHEMA_ERR, R4])
    assert nc.run(per_group=1, client=fake) == 0
    assert fake.calls == 4 and fake.quota_calls == 2                                      # trước lượt + sau lượt
    status, st, err = _run_row(engine)
    assert status == "success" and err is None
    assert st["selected"] == 4 and st["classified"] == 3 and st["failed"] == 1 and st["failed_schema"] == 1 and st["repaired"] == 1
    assert st["groups"] == {"1": 0, "2": 0, "3": 2, "x": 1} and st["overridden"] == 2 and st["title_only"] == 0
    assert (st["tickers_ai"], st["tickers_ai_dropped"], st["tickers_lookup"], st["tickers_url"]) == (1, 1, 1, 0)
    assert (st["industries_ai"], st["industries_ticker"]) == (3, 1)
    assert st["tokens"] == {"input": 6000, "cache_read": 3900, "output": 1500, "thinking": 600}
    assert st["latency_s"] == {"p50": 2.0, "p90": 2.0, "max": 4.0, "total": 7.0} and st["usd_estimate"] == 0.0038
    assert st["quota"] == {"before": {"interval_pct": 97, "weekly_pct": 86}, "after": {"interval_pct": 97, "weekly_pct": 86}}
    assert st["thinking"] == "adaptive" and st["cap_chars"] == 3000 and st["quota_stop"] is False and st["budget_hit"] is False
    with engine.connect() as c:
        calls = c.execute(sa.text("SELECT article_id, status, input_tokens, error FROM ops.llm_call WHERE purpose = 'news.classify' ORDER BY call_id")).all()
        assert [tuple(r) for r in calls] == [(ids[0], "ok", 2000, None), (ids[1], "ok", 2000, None), (ids[2], "failed", None, "schema: sub: không thuộc nhóm"), (ids[3], "repaired", 2000, None)]
        assert c.execute(sa.text("SELECT run_id FROM ops.llm_call WHERE article_id = :a"), {"a": ids[0]}).scalar_one() is not None
        assert c.execute(sa.text("SELECT classified_from, group_no FROM news.article WHERE article_id = :a"), {"a": ids[2]}).one() == (None, None)
    # lượt hai: bài đã phân loại không chọn lại; bài lỗi được chọn lại
    fake2 = FakeClient([R1, R2])
    assert nc.run(per_group=1, client=fake2) == 0
    assert fake2.calls == 2                                                                # A3 (lỗi lượt 1) + A5 (bucket NULL còn lại)


def test_quota_below_threshold_stops_before_any_call(seeded):
    engine, ids = seeded
    fake = FakeClient([R1], quota=(15, 50))
    assert nc.run(limit=1, client=fake) == 0
    status, st, _ = _run_row(engine)
    assert status == "success" and st["quota_stop"] is True and st["classified"] == 0 and fake.calls == 0
    fake2 = FakeClient([R1], quota=(50, 9))
    assert nc.run(limit=1, client=fake2) == 0 and fake2.calls == 0


def test_five_consecutive_retryable_failures_is_model_down(seeded):
    engine, ids = seeded
    fake = FakeClient([LLMError("rate_limit", retryable=True, detail="RateLimitError 429")] * 5 + [R1])
    assert nc.run(limit=5, client=fake) == 1
    status, st, err = _run_row(engine)
    assert status == "failed" and "5 lời gọi liên tiếp" in err and st["failed"] == 5 and fake.calls == 5
    assert _n(engine, "SELECT count(*) FROM ops.llm_call WHERE status = 'failed'") == 5


def test_auth_error_stops_immediately_with_exit_2(seeded):
    engine, ids = seeded
    fake = FakeClient([LLMError("auth", retryable=False, detail="AuthenticationError 401"), R1])
    assert nc.run(limit=2, client=fake) == 2
    assert _run_row(engine)[0] == "failed" and fake.calls == 1


def test_dry_run_calls_model_but_writes_nothing(seeded, tmp_path):
    engine, ids = seeded
    out = tmp_path / "dry.jsonl"
    fake = FakeClient([R1, R2, SCHEMA_ERR, R4])
    assert nc.run(per_group=1, dry_run=True, out=str(out), client=fake, thinking="disabled") == 0
    lines = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert [x["article_id"] for x in lines] == [ids[0], ids[1], ids[3]]
    assert lines[0]["value"]["industries"] == ["KIMLOAI", "XAYDUNG"] and lines[0]["usage"]["input_tokens"] == 2000 and lines[0]["hint"] == 1
    assert lines[2]["repaired"] is True and lines[0]["classified_from"] == "content" and lines[0]["content_chars"] == 350
    assert _n(engine, "SELECT count(*) FROM ops.llm_call") == 0 and _n(engine, "SELECT count(*) FROM ops.etl_run WHERE job = 'news.classify'") == 0
    assert _n(engine, "SELECT count(*) FROM news.article WHERE canonical_url LIKE 'https://zz.test/classify-%' AND classified_from IS NOT NULL") == 0


def test_max_minutes_budget_hit(seeded):
    engine, ids = seeded
    ticks = iter([0.0, 0.0, 0.0, 400.0, 400.0, 400.0, 400.0, 400.0, 400.0])
    fake = FakeClient([R1, R2, R4, R4])
    assert nc.run(limit=4, client=fake, max_minutes=5, clock=lambda: next(ticks)) == 0
    status, st, _ = _run_row(engine)
    assert st["budget_hit"] is True and st["classified"] < 4 and fake.calls == st["classified"]
```

- [ ] **Step 2: Test đỏ — `tests/etl/test_e61_classify_cli.py`**

```python
"""CLI `etl classify`: trần bắt buộc (mọi lượt tốn quota), --out chỉ đi với --dry-run, thinking hai giá trị."""
import pytest

import etl.__main__ as m


def test_classify_flags_reach_run(monkeypatch):
    import etl.news_classify
    seen = {}
    monkeypatch.setattr(etl.news_classify, "run", lambda **kw: seen.update(kw) or 0)
    assert m.main(["classify", "--per-group", "100"]) == 0
    assert seen == {"limit": None, "per_group": 100, "thinking": "adaptive", "dry_run": False, "out": None, "max_minutes": None, "cap": 3000}
    assert m.main(["classify", "--limit", "5", "--dry-run", "--out", "x.jsonl", "--thinking", "disabled", "--max-minutes", "2.5", "--cap-chars", "4000"]) == 0
    assert seen == {"limit": 5, "per_group": None, "thinking": "disabled", "dry_run": True, "out": "x.jsonl", "max_minutes": 2.5, "cap": 4000}


@pytest.mark.parametrize("bad", [["classify"], ["classify", "--limit", "5", "--per-group", "5"], ["classify", "--limit", "5", "--out", "x"],
                                 ["classify", "--limit", "5", "--thinking", "deep"], ["classify", "--limit", "0"]])
def test_classify_rejects_missing_or_conflicting_bounds(bad):
    with pytest.raises(SystemExit) as e:
        m.main(bad)
    assert e.value.code == 2
```

- [ ] **Step 3: Chạy thấy đỏ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e60_classify_job.py tests/etl/test_e61_classify_cli.py -q`
Expected: 6 FAIL `AttributeError: … no attribute 'run'`/`ModelDown`; CLI: `etl: subcommand không hợp lệ: 'classify'` ⇒ return 2 làm `test_classify_flags_reach_run` FAIL ở `seen == …`, còn `test_classify_rejects…` **có thể xanh giả** (exit 2 vì subcommand lạ) — chấp nhận, ca này chỉ có nghĩa sau Step 4.

- [ ] **Step 4: Code — nối vào `backend/etl/news_classify.py`** (thêm import: `import json, logging, sys, time`; `from datetime import datetime, timezone` không cần; `from core.llm import LLMClient, LLMConfigError, LLMError, LLMSettings, Usage`; `from etl import news_store, omo_store`; `from etl.news_job import _engine`)

```python
log = logging.getLogger("etl.classify")
JOB = "news.classify"
QUOTA_EVERY = 25
QUOTA_MIN_INTERVAL_PCT = 20       # cửa sổ 5 giờ — giữ phần cho chatbot/dev (brainstorm §4.4)
QUOTA_MIN_WEEKLY_PCT = 10
MAX_CONSECUTIVE_FAILED = 5


class ModelDown(Exception):
    """5 lời gọi liên tiếp lỗi thử-lại-được — model/mạng/quota chết, dừng lượt (khuôn SourceDown)."""

    def __init__(self, msg: str, stats: dict):
        self.stats = stats
        super().__init__(msg)


def _empty_stats(thinking: str, cap: int, selected: int) -> dict:
    return {"thinking": thinking, "cap_chars": cap, "selected": selected, "classified": 0, "failed": 0, "failed_schema": 0, "repaired": 0,
            "groups": {"1": 0, "2": 0, "3": 0, "x": 0}, "overridden": 0, "title_only": 0, "tickers_url": 0, "tickers_lookup": 0,
            "tickers_ai": 0, "tickers_ai_dropped": 0, "industries_ai": 0, "industries_ticker": 0,
            "tokens": {"input": 0, "cache_read": 0, "output": 0, "thinking": 0}, "latency_s": {"p50": None, "p90": None, "max": None, "total": 0.0},
            "usd_estimate": 0.0, "quota": {}, "quota_stop": False, "budget_hit": False, "warnings": []}


def _quota_ok(client, st: dict, key: str) -> bool:
    try:
        q = client.token_plan_remains()
    except LLMError as e:                                          # guard hỏng ⇒ cảnh báo, không chặn (spec §4.2-VIII)
        st["warnings"].append(f"quota: {e}")
        return True
    st["quota"][key] = {"interval_pct": q.interval_pct, "weekly_pct": q.weekly_pct}
    return q.interval_pct >= QUOTA_MIN_INTERVAL_PCT and q.weekly_pct >= QUOTA_MIN_WEEKLY_PCT


def _pct(xs: list[float], p: float) -> float:
    s = sorted(xs)
    return s[int(p * (len(s) - 1))]


def classify_run(engine, client, rows: list[Row], *, run_id, schema, system: str, thinking: str, listed: dict, industry_ids: dict,
                 dry_run: bool = False, out=None, max_minutes: float | None = None, cap: int = CAP_CHARS, clock=time.monotonic) -> dict:
    t0 = clock()
    st = _empty_stats(thinking, cap, len(rows))
    lat: list[float] = []
    tok = Usage()
    try:
        if not _quota_ok(client, st, "before"):
            st["quota_stop"] = True
            return st
        streak = 0
        for i, row in enumerate(rows):
            if i and i % QUOTA_EVERY == 0 and not _quota_ok(client, st, "after"):
                st["quota_stop"] = True
                break
            if max_minutes is not None and clock() - t0 >= max_minutes * 60:
                st["budget_hit"] = True
                break
            user, content_chars, classified_from = user_prompt(row, cap)
            t1 = clock()
            try:
                r = client.structured(schema, system=system, user=user, thinking=thinking)
            except LLMError as e:
                st["failed"] += 1
                if e.reason == "schema":
                    st["failed_schema"] += 1
                if not dry_run:
                    with engine.begin() as c:
                        log_call(c, run_id=run_id, article_id=row.article_id, model=client.settings.model, thinking=thinking, status="failed",
                                 usage=None, latency_s=clock() - t1, error=str(e))
                log.warning("bài %s: %s", row.article_id, e)
                if e.reason == "auth":
                    raise
                if e.retryable:
                    streak += 1
                    if streak >= MAX_CONSECUTIVE_FAILED:
                        raise ModelDown(f"{streak} lời gọi liên tiếp lỗi thử-lại-được — model/mạng/quota chết, dừng lượt", st) from e
                continue
            streak = 0
            lat.append(r.usage.latency_s)
            tok = tok + r.usage
            st["repaired"] += int(r.repaired)
            st["groups"][r.value.group] += 1
            st["title_only"] += int(classified_from == "title_only")
            if dry_run:
                out.write(json.dumps({"article_id": row.article_id, "hint": row.group_from_feed, "source": row.primary_source, "title": row.title[:80],
                                      "classified_from": classified_from, "content_chars": content_chars, "value": r.value.model_dump(),
                                      "usage": r.usage.__dict__, "repaired": r.repaired}, ensure_ascii=False) + "\n")
                st["classified"] += 1
                continue
            with engine.begin() as c:
                a = apply(c, row, r.value, content_chars=content_chars, classified_from=classified_from, listed=listed, industry_ids=industry_ids)
                log_call(c, run_id=run_id, article_id=row.article_id, model=client.settings.model, thinking=thinking,
                         status="repaired" if r.repaired else "ok", usage=r.usage, latency_s=r.usage.latency_s)
            for k, v in a.items():
                st[k] += v
            st["classified"] += 1
        if not st["quota_stop"]:
            _quota_ok(client, st, "after")
        return st
    finally:
        st["tokens"] = {"input": tok.input_tokens, "cache_read": tok.cache_read_tokens, "output": tok.output_tokens, "thinking": tok.thinking_tokens}
        if lat:
            st["latency_s"] = {"p50": _pct(lat, 0.5), "p90": _pct(lat, 0.9), "max": max(lat), "total": round(sum(lat), 3)}
        st["usd_estimate"] = round(tok.estimate_usd(), 4)


def run(limit: int | None = None, per_group: int | None = None, thinking: str = "adaptive", dry_run: bool = False, out: str | None = None,
        max_minutes: float | None = None, cap: int = CAP_CHARS, client=None, clock=time.monotonic) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    load_dotenv()
    try:
        engine = _engine()
        if client is None:
            client = LLMClient(LLMSettings.from_env())
        with engine.connect() as c:
            inds = c.execute(sa.text("SELECT industry_id, code, name_vi FROM market.industry WHERE level = 2 ORDER BY sort_order, code")).all()
            if len(inds) != 24:
                raise RuntimeError(f"market.industry level 2 có {len(inds)} mã, mong 24 (industry-tree.md)")
            listed = news_store.load_listed(c)
            rows = select_articles(c, limit=limit, per_group=per_group)
    except (RuntimeError, ValueError, LLMConfigError) as e:
        log.error("%s", e)
        return 2
    schema = build_schema([r.code for r in inds])
    system = system_prompt([(r.code, r.name_vi) for r in inds])
    industry_ids = {r.code: r.industry_id for r in inds}
    log.info("classify: %s bài, thinking %s, dry_run %s, trần %s ký tự", len(rows), thinking, dry_run, cap)
    kw = dict(schema=schema, system=system, thinking=thinking, listed=listed, industry_ids=industry_ids, max_minutes=max_minutes, cap=cap, clock=clock)
    if dry_run:
        fh = open(out, "w", encoding="utf-8") if out else sys.stdout
        try:
            st = classify_run(engine, client, rows, run_id=None, dry_run=True, out=fh, **kw)
            log.info("classify dry-run xong: %s", st)
            return 0
        except ModelDown as e:
            log.error("%s — stats %s", e, e.stats)
            return 1
        except LLMError as e:
            log.error("%s", e)
            return 2
        except KeyboardInterrupt:
            log.warning("classify dừng tay (Ctrl+C)")
            return 130
        finally:
            if out:
                fh.close()
            engine.dispose()
    run_id = omo_store.open_run(engine, JOB)
    try:
        st = classify_run(engine, client, rows, run_id=run_id, **kw)
        omo_store.close_run(engine, run_id, "success", st)
        log.info("classify xong: %s", st)
        return 0
    except ModelDown as e:
        omo_store.close_run(engine, run_id, "failed", e.stats, error=str(e))
        log.error("%s", e)
        return 1
    except KeyboardInterrupt:
        omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
        return 130
    except LLMError as e:                                          # 'auth' — gọi tiếp vô ích
        omo_store.close_run(engine, run_id, "failed", error=str(e))
        log.error("%s", e)
        return 2
    except Exception as e:                                         # noqa: BLE001 — job biên ngoài
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("classify thất bại")
        return 2
    finally:
        engine.dispose()
```

⚠️ `classify_run` không giữ `stats` khi `ModelDown` vì `finally` đã ghi tokens vào `st` — `ModelDown.stats` là cùng object `st`, nên `close_run(... e.stats)` vẫn có tokens. Với `KeyboardInterrupt` giữa chừng, `stats` không được đưa vào `close_run` (khuôn lát 8) — chấp nhận.

- [ ] **Step 5: Code — `backend/etl/__main__.py`**, chèn trước `if args[0] in ("fred", "fx", "lbma", "yahoo", "binance"):`

```python
    if args[0] == "classify":
        import etl.news_classify
        parser = argparse.ArgumentParser(prog="etl classify")
        parser.add_argument("--limit", type=int, help="tối đa N bài chưa phân loại, mới nhất trước")
        parser.add_argument("--per-group", type=int, dest="per_group", help="N bài mới nhất của MỖI nhóm gợi ý feed (1 · 2 · 3 · không nhóm)")
        parser.add_argument("--thinking", choices=("adaptive", "disabled"), default="adaptive")
        parser.add_argument("--dry-run", action="store_true", dest="dry_run", help="gọi model thật nhưng KHÔNG ghi kho — để đo")
        parser.add_argument("--out", help="file JSONL từng bài (chỉ với --dry-run; mặc định stdout)")
        parser.add_argument("--max-minutes", type=float, dest="max_minutes")
        parser.add_argument("--cap-chars", type=int, dest="cap", default=etl.news_classify.CAP_CHARS)
        parsed = parser.parse_args(args[1:])
        if (parsed.limit is None) == (parsed.per_group is None):
            parser.error("cần đúng một trong --limit N / --per-group N — mọi lượt phân loại phải có trần (tốn quota)")
        if (parsed.limit is not None and parsed.limit <= 0) or (parsed.per_group is not None and parsed.per_group <= 0):
            parser.error("--limit/--per-group phải > 0")
        if parsed.out and not parsed.dry_run:
            parser.error("--out chỉ đi cùng --dry-run")
        return etl.news_classify.run(limit=parsed.limit, per_group=parsed.per_group, thinking=parsed.thinking, dry_run=parsed.dry_run,
                                     out=parsed.out, max_minutes=parsed.max_minutes, cap=parsed.cap)
```

và sửa dòng thông điệp cuối: `"… wichart, news, classify, fred, fx, lbma, yahoo, binance)"`.

- [ ] **Step 6: Chạy thấy xanh, rồi toàn bộ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e60_classify_job.py tests/etl/test_e61_classify_cli.py -q` ⇒ Expected: `13 passed`.
Run: `PYTHONIOENCODING=utf-8 uv run pytest tests -q` ⇒ Expected: **≥ 809 + 42 passed, 2 skipped** (số chính xác ghi vào ledger). Nếu `test_max_minutes_budget_hit` đỏ vì số lần gọi `clock` khác dự kiến: đếm lại — `t0`, kiểm budget mỗi bài (1), `t1` mỗi bài (1) ⇒ với 4 bài không lỗi: `t0`, [budget, t1] × 4 = 9 lần; sửa `ticks` cho khớp thứ tự thật rồi ghi vào báo cáo.

- [ ] **Step 7: Commit**

```bash
git add backend/etl/news_classify.py backend/etl/__main__.py backend/tests/etl/test_e60_classify_job.py backend/tests/etl/test_e61_classify_cli.py
git commit -m "feat(etl): classify job with quota guard, dry-run, model-down fuse; CLI etl classify"
```

---

### Task 7 (controller): nghiệm thu thật — AC2 → AC7

Chạy từ `backend/`, credential production (`ETL_DATABASE_URL` = `etl_worker`), khoá thật trong `.env`. Ghi mọi số vào `ledger.md` §2. Thứ tự **bắt buộc**: AC2 → AC3 → AC5 (dry-run disabled, KHÔNG ghi) → AC4 (ghi, adaptive) → AC6 → AC7.

- [ ] **AC2** — `uv run --project backend alembic -c database/alembic.ini upgrade head` (từ gốc repo, env theo database/README) ⇒ `Running upgrade 0017 -> 0018`. Trên `dulieu_test`: `downgrade 0017` rồi `upgrade head` sạch (fixture pytest đã chạy `upgrade head` từ đầu — bằng chứng đủ; downgrade kiểm tay một lần).
- [ ] **AC3** — `PYTHONIOENCODING=utf-8 uv run python -m etl classify --dry-run --per-group 3 --out <scratchpad>/ac3.jsonl 2> <scratchpad>/ac3.log` ⇒ exit 0, JSONL 12 dòng, `failed 0`; `grep -c "<8 ký tự đầu khoá>" ac3.log ac3.jsonl` ⇒ 0.
- [ ] **AC5** — `… classify --dry-run --thinking disabled --per-group 25 --out <plan>/measure/dry-disabled-2026-09-06.jsonl` ⇒ 100 bài; ghi p50/p90 latency, token vào/ra, phân bố group.
- [ ] **AC4** — mở tách tiến trình (memory: lượt > 10 phút): `Start-Process cmd -ArgumentList '/c','cd /d D:\twan_projects\dulieuchungkhoan.vn\backend && set PYTHONIOENCODING=utf-8 && uv run python -m etl classify --per-group 100 > <scratchpad>\ac4.log 2>&1'`; theo dõi `ops.etl_run` job `news.classify` (`status`, `stats`). Khi xong: chép `stats` vào ledger; truy vấn `ops.llm_call` cho p50/p90 token và latency; đối chiếu 100 bài AC5 theo `article_id` (JSONL vs `ops.llm_call` + `news.article`): bảng hai chế độ (token ra, latency, tỷ lệ cùng `group`/`sub`); soi tay 10 bài (5 nhóm 1/2 có ngành, 5 nhóm 3) — ghi nhận định tính.
- [ ] **AC6** — `… classify --per-group 100 --max-minutes 5` lượt hai ⇒ `article_id` không trùng lượt một (`SELECT count(*) FROM ops.llm_call GROUP BY article_id HAVING count(*) > 1` chỉ ra bài `failed` lượt 1 nếu có); không dòng trùng `article_industry`/`article_ticker` (PK bảo đảm — truy vấn đếm).
- [ ] **AC7** — SQL: số bài có ngành `ai` ∩ `ticker` / chỉ `ai` / chỉ `ticker` ở nhóm 3; phân bố 24 ngành; `overridden` theo feed (feed nào bị ghi đè > 50% ⇒ ghi để lát sau rà); `tickers_ai_dropped` với mã nào (mã bịa).

---

### Task 8: Tài liệu sống (spec §8) + roadmap + ledger

**Files:** theo spec §8 — `docs/20-design/news-pipeline.md` (§7.1, **§8b mới**, §12, §14), `docs/10-sources/llm/minimax.md` (số đo AC4/AC5 kèm ngày), `database/README.md` (18 migration, số test), `backend/README.md` (mục "Chạy job classify", dependency, trạng thái, số test), `docs/00-overview/architecture.md` (cây `core/llm/`), `docs/00-overview/roadmap.md` (bảng lát 9a ✅/9b, gạch "Điểm vào cho lát 9", viết "Điểm vào cho lát 9b"), `docs/90-records/README.md` (dòng plan), `docs/90-records/surveys/2026-09-06-llm-module-minimax/README.md` (trỏ plan), `ledger.md`.

- [ ] Viết §8b news-pipeline: hai đường, bảng, `via` trong PK, ngành áp mọi nhóm, tối đa 3, danh sách nạp từ DB; §7.1 đầu ra `industries[]`; §12: dedupe 0,5% (đo 2026-09-06), trần/ngưỡng còn ngỏ với số nền AC4, embedding → 9b.
- [ ] `backend/README.md` mục job: lệnh `uv run python -m etl classify --per-group N | --limit N [--thinking adaptive|disabled] [--dry-run [--out f]] [--max-minutes N] [--cap-chars 3000]`; đọc `stats`; quota guard; `ops.llm_call`; ước chi phí từ AC4; "không có chế độ chạy hết".
- [ ] roadmap: "Điểm vào cho lát 9b" gồm trạng thái bàn giao (test, migration head `0018`, số bài đã phân loại, quota), số đo AC4/AC5, việc còn (gold, ngưỡng, `--loop`, embedding, `--force`).
- [ ] `git grep -n "article_industry\|llm_call\|etl classify\|core/llm"` ngoài `90-records/` — mọi hit đúng.
- [ ] Commit: `docs: slice 9a — classify job, industry tagging, measurements, entry point for 9b`.

---

## Self-review (đã chạy khi viết plan)

- **Spec coverage:** §3.1 `core/llm` → Task 1–2; `uv add` + `.env.example` → Task 0; migration + test role → Task 3; `news_classify` thuần → Task 4; DB → Task 5; job/CLI/guard/dry-run → Task 6; AC2–AC7 → Task 7; §8 → Task 8. §4.2-I…XVI: I/II (Task 6 CLI), III (Task 6 dry-run), IV (Task 3/5 `llm_call`), V (Task 5 `apply` labels/overridden), VI (Task 5 tầng 2 bù + lọc listed), VII (Task 4 `user_prompt`), VIII (Task 6 `_quota_ok`, `ModelDown`), IX (Task 5 UPDATE `summary_ai`), X (Task 5 INSERT `ticker` từ mọi via), XI (Task 5 `select_articles`), XII (Task 6 tuần tự), XIII (Task 2 chỉ `structured`/`remains`/`raw`), XIV (Task 4 `system_prompt` nạp từ DB — Task 6 `run` nạp), XV (Task 4 schema), XVI (Task 3 `industry_id`).
- **Placeholder scan:** không có TBD/TODO; mọi bước code có code; literal test tính tay (usd 0,00183; 6000/3900/1500/600; p50 2,0; 0,0038).
- **Type consistency:** `Row` 9 trường khớp `_SELECT` 9 cột; `apply` trả 7 khoá và `classify_run` cộng đúng 7 khoá vào `st` (đều có trong `_empty_stats`); `log_call` chữ ký giống nhau ở Task 5 test và Task 6; `FakeClient.settings.model` khớp `client.settings.model`; `QuotaRemains(interval_pct, weekly_pct, raw)` khớp Task 2; `Structured(value, usage, repaired, stop_reason)` khớp.
- **Điểm rủi ro đã ghi cách xử lý trong bước:** `Literal[tuple]` (Task 4), `labels` bind array (Task 5), `Decimal` (Task 5), số lần gọi `clock` (Task 6), `test_s09_grants` (Task 3), `model_dump` alias (Task 2).
