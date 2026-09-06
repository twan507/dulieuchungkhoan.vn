"""Lỗi của module LLM: một lớp, hai thuộc tính (`reason`, `retryable`) để job quyết định đếm `failed` hay dừng.
Thông điệp CHỈ giữ tên lớp SDK + status — không `str(e)` của SDK (URL/headers có thể mang khoá; khuôn http_fetch)."""
from __future__ import annotations

import anthropic


class LLMConfigError(Exception):
    """Cấu hình thiếu/sai (LLM_API) — lỗi trước khi gọi, không phải lỗi gọi."""


class LLMError(Exception):
    def __init__(self, reason: str, *, retryable: bool, detail: str = ""):
        self.reason, self.retryable = reason, retryable
        self.usage = None                      # gắn Usage tích luỹ khi có (M5 — schema error vẫn tốn token, log_call cần biết)
        super().__init__(f"{reason}: {detail}" if detail else reason)


def from_sdk(e: anthropic.APIError) -> LLMError:
    status = getattr(e, "status_code", None)
    detail = f"{type(e).__name__} {status}" if status is not None else type(e).__name__
    if isinstance(e, anthropic.RateLimitError):
        return LLMError("rate_limit", retryable=True, detail=detail)
    if isinstance(e, anthropic.APIStatusError) and status is not None and status >= 500:
        return LLMError("server", retryable=True, detail=detail)
    if isinstance(e, anthropic.APIConnectionError):                       # gồm APITimeoutError
        return LLMError("transport", retryable=True, detail=detail)
    if isinstance(e, (anthropic.AuthenticationError, anthropic.PermissionDeniedError)):
        return LLMError("auth", retryable=False, detail=detail)
    return LLMError("bad_request", retryable=False, detail=detail)
