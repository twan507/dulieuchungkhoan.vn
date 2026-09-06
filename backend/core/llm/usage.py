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
