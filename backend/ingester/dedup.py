"""Lưới dedup mức frame (hash nội dung, cửa sổ trượt) + received_at đơn điệu.

KHÔNG dùng luật thứ tự SM trước phiên đo (spec §1 quyết định #8; spec CH §5.4).
Frame lọt lại sau khi ra khỏi cửa sổ: chấp nhận — lưới block CH và tính idempotent
của MV chỉ số đỡ tầng dưới.
"""
from __future__ import annotations

import hashlib
import json


def frame_key(event: str, payload: dict) -> bytes:
    blob = event + "\x00" + json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                       ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).digest()


class FrameDedup:
    def __init__(self, window_s: float = 600.0):
        self.window_s = window_s
        self._seen: dict[bytes, float] = {}
        self._last_purge = 0.0

    def seen(self, key: bytes, now: float) -> bool:
        if now - self._last_purge > 60.0:
            cutoff = now - self.window_s
            self._seen = {k: t for k, t in self._seen.items() if t >= cutoff}
            self._last_purge = now
        prev = self._seen.get(key)
        self._seen[key] = now
        return prev is not None and now - prev < self.window_s


class Stamper:
    def __init__(self):
        self._last: dict[str, int] = {}

    def stamp(self, symbol: str, now_ms: int) -> int:
        v = max(now_ms, self._last.get(symbol, -1) + 1)
        self._last[symbol] = v
        return v
