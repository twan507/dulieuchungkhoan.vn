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
