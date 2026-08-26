"""Batch writer ClickHouse — hợp đồng spec CH §5: flush 1 s cố định (vòng lặp ở main),
retry NGUYÊN block, chia đôi block độc, trần BLOCK_CAP không flush sớm."""
from __future__ import annotations

import logging
import threading
import time
from collections import deque

from clickhouse_connect.driver.exceptions import DataError

from ingester.normalize import COLUMNS, Metrics, Normalized

log = logging.getLogger("ingester.chwriter")
BLOCK_CAP = 5000
RETRY_BUDGET_S = 60          # < tuổi thọ cửa sổ dedup ~100 s (spec CH §5.5)

# Mã lỗi DỮ LIỆU của ClickHouse — chỉ những mã này mới là lỗi tất định (chia đôi block
# để cô lập dòng hỏng). Danh sách kín có chủ đích: luật cũ dò "timeout|connection|
# temporarily" rồi coi PHẦN CÒN LẠI là tất định, nên lỗi BACKPRESSURE (TOO_MANY_PARTS,
# MEMORY_LIMIT_EXCEEDED) bị chia đôi đệ quy thành 5.000 INSERT một dòng — làm đúng cái
# việc khiến ClickHouse ngộp thêm — rồi vứt sạch dữ liệu (review cuối IMPORTANT 1).
_DETERMINISTIC_MARKERS = (
    "ARGUMENT_OUT_OF_BOUND", "TYPE_MISMATCH", "CANNOT_PARSE",
    "VALUE_IS_OUT_OF_RANGE_OF_DATA_TYPE", "ILLEGAL_TYPE_OF_ARGUMENT",
    "TOO_LARGE_STRING_SIZE",
)
# DataError = clickhouse_connect không đóng gói nổi giá trị vào mảng native — lỗi ở PHÍA
# CLIENT, thông điệp không mang mã của server nhưng chắc chắn không tự lành.
_DETERMINISTIC_TYPES = (DataError,)


def _is_deterministic(e: Exception) -> bool:
    """Lỗi dữ liệu (không retry được) hay không. Mọi lỗi KHÁC coi là transient."""
    if isinstance(e, _DETERMINISTIC_TYPES):
        return True
    text = str(e).upper()
    return any(m in text for m in _DETERMINISTIC_MARKERS)


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
        # Mutex riêng cho CẢ PHA XẢ: lúc tắt, task flush bị cancel() nhưng thread
        # `flush_once` vẫn chạy tiếp trong khi code khởi flush cuối cùng — hai thread
        # cùng duyệt `pending` thì `_write_block(q[0])` rồi `q.popleft()` (ngoài lock dữ
        # liệu) làm một block bị ghi đôi và block kế bị popleft mà chưa từng ghi
        # (review cuối IMPORTANT 4). Không lấy được thì về ngay — nhịp sau xả tiếp.
        # Thứ tự lấy khoá luôn là _flush_lock → _lock (add() chỉ lấy _lock) ⇒ không deadlock.
        self._flush_lock = threading.Lock()

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
        if not self._flush_lock.acquire(blocking=False):
            return                             # đã có thread khác đang xả — nhịp sau xả tiếp
        try:
            with self._lock:                   # chỉ pha cắt buffer — KHÔNG giữ lock khi I/O
                for table, buf in self.buffers.items():
                    if buf:
                        self.pending[table].append(buf[:])
                        buf.clear()
            for table, q in self.pending.items():
                while q:
                    self._write_block(table, q[0])
                    q.popleft()
        finally:
            self._flush_lock.release()

    def _write_block(self, table: str, block: list, budget: float | None = None) -> None:
        budget = RETRY_BUDGET_S if budget is None else budget
        delay, spent = 1.0, 0.0
        while True:
            try:
                self.client.insert(f"rt.{table}", block, column_names=COLUMNS[table])
                self.metrics.inc(f"rows.{table}", len(block))
                return
            except Exception as e:  # noqa: BLE001 — phân loại rồi xử lý theo hợp đồng
                if not _is_deterministic(e):
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
