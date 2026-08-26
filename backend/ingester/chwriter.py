"""Batch writer ClickHouse — hợp đồng spec CH §5: flush 1 s cố định (vòng lặp ở main),
retry NGUYÊN block, chia đôi block độc, trần BLOCK_CAP không flush sớm."""
from __future__ import annotations

import logging
import threading
import time
from collections import deque

from ingester.normalize import COLUMNS, Metrics, Normalized

log = logging.getLogger("ingester.chwriter")
BLOCK_CAP = 5000
RETRY_BUDGET_S = 60          # < tuổi thọ cửa sổ dedup ~100 s (spec CH §5.5)
_TRANSIENT = (ConnectionError, TimeoutError, OSError)


def _is_transient(e: Exception) -> bool:
    if isinstance(e, _TRANSIENT):
        return True
    text = str(e).lower()
    return "timeout" in text or "connection" in text or "temporarily" in text


class ChWriter:
    def __init__(self, client, sleep_fn=time.sleep):
        self.client = client
        self.sleep = sleep_fn
        self.metrics = Metrics()
        self.buffers: dict[str, list[list]] = {t: [] for t in COLUMNS}
        self.pending: dict[str, deque] = {t: deque() for t in COLUMNS}
        # add() chạy trên event-loop thread, flush_once() chạy trong thread khác qua
        # asyncio.to_thread — pha cắt buffer (copy+clear) phải atomic với add() (§CRITICAL 1
        # review wave 2), nếu không có thể mất dòng vừa append đúng lúc buffer bị cắt.
        self._lock = threading.Lock()

    def add(self, n: Normalized) -> None:
        with self._lock:
            buf = self.buffers[n.table]
            buf.append([n.row.get(c) for c in COLUMNS[n.table]])
            if len(buf) >= BLOCK_CAP:
                self.pending[n.table].append(buf[:])
                buf.clear()
                self.metrics.inc(f"block_cap.{n.table}")
                log.warning("bảng %s chạm trần block %d — tải cao bất thường", n.table, BLOCK_CAP)

    def flush_once(self) -> None:
        with self._lock:                       # chỉ pha cắt buffer — KHÔNG giữ lock khi I/O
            for table, buf in self.buffers.items():
                if buf:
                    self.pending[table].append(buf[:])
                    buf.clear()
        for table, q in self.pending.items():
            while q:
                self._write_block(table, q[0])
                q.popleft()

    def _write_block(self, table: str, block: list, budget: float | None = None) -> None:
        budget = RETRY_BUDGET_S if budget is None else budget
        delay, spent = 1.0, 0.0
        while True:
            try:
                self.client.insert(f"rt.{table}", block, column_names=COLUMNS[table])
                self.metrics.inc(f"rows.{table}", len(block))
                return
            except Exception as e:  # noqa: BLE001 — phân loại rồi xử lý theo hợp đồng
                if _is_transient(e):
                    if spent >= budget:
                        self.metrics.inc(f"dropped_block.{table}", len(block))
                        log.error("bỏ block %s (%d dòng) sau %ss retry: %r", table, len(block), spent, e)
                        return
                    self.sleep(delay)
                    spent += delay
                    delay = min(delay * 2, 16.0)
                    continue                      # retry NGUYÊN block — không gộp dòng mới
                if len(block) == 1:
                    self.metrics.inc(f"poison_row.{table}")
                    log.error("dòng độc %s: %r — %r", table, block[0], e)
                    return
                mid = len(block) // 2             # lỗi tất định → cô lập dòng hỏng (§5.8)
                self._write_block(table, block[:mid], budget)
                self._write_block(table, block[mid:], budget)
                return
