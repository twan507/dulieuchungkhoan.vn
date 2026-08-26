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
    "TOO_LARGE_STRING_SIZE", "INCORRECT_DATA", "DECIMAL_OVERFLOW",
)
# DataError = clickhouse_connect không đóng gói nổi giá trị vào mảng native — lỗi ở PHÍA
# CLIENT, thông điệp không mang mã của server nhưng chắc chắn không tự lành.
_DETERMINISTIC_TYPES = (DataError,)

# Nguồn sự thật thật sự: MÃ SỐ lỗi. `build_http_error` của clickhouse_connect đặt
# `code` từ HEADER HTTP nên nó LUÔN có với mọi lỗi từ server, kể cả khi
# `show_clickhouse_errors=False` nuốt mất `name` lẫn toàn bộ chi tiết trong `str(e)`
# (lúc đó thông điệp rút gọn thành "The ClickHouse server returned an error").
# Dò chuỗi như luật cũ vì thế trượt hai đường: (a) tên không nằm trong danh sách
# marker — DECIMAL_OVERFLOW là ca gặp thật khi giá tràn Decimal64(2); (b) chi tiết bị
# tắt. Trượt = lỗi dữ liệu bị đọc thành transient ⇒ retry 60 s vô ích rồi VỨT CẢ BLOCK
# (5.000 dòng) thay vì chia đôi cô lập một dòng (M-new-1).
# Mã tra bằng `errorCodeToName` trên ClickHouse 26.3.22.7 (đo 2026-08-26), giới hạn
# trong những lỗi có thể sinh ra trên đường INSERT mảng native vào `rt.*`.
_DETERMINISTIC_CODES = frozenset({
    6,    # CANNOT_PARSE_TEXT
    26,   # CANNOT_PARSE_QUOTED_STRING
    27,   # CANNOT_PARSE_INPUT_ASSERTION_FAILED
    38,   # CANNOT_PARSE_DATE
    41,   # CANNOT_PARSE_DATETIME
    43,   # ILLEGAL_TYPE_OF_ARGUMENT
    53,   # TYPE_MISMATCH
    69,   # ARGUMENT_OUT_OF_BOUND
    70,   # CANNOT_CONVERT_TYPE
    72,   # CANNOT_PARSE_NUMBER
    117,  # INCORRECT_DATA
    131,  # TOO_LARGE_STRING_SIZE
    321,  # VALUE_IS_OUT_OF_RANGE_OF_DATA_TYPE
    407,  # DECIMAL_OVERFLOW
})


def _is_deterministic(e: Exception) -> bool:
    """Lỗi dữ liệu (không retry được) hay không. Mọi lỗi KHÁC coi là transient."""
    if isinstance(e, _DETERMINISTIC_TYPES):
        return True
    code = getattr(e, "code", None)
    if isinstance(code, int):
        return code in _DETERMINISTIC_CODES   # có mã thì mã là phán quyết cuối
    text = str(e).upper()                     # không mã (lỗi transport/lỗi lạ) → đường lùi
    return any(m in text for m in _DETERMINISTIC_MARKERS)


class ChWriter:
    def __init__(self, client, sleep_fn=time.sleep, clock=time.monotonic):
        self.client = client
        self.sleep = sleep_fn
        self.clock = clock
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

    def _write_block(self, table: str, block: list, deadline: float | None = None) -> None:
        # HẠN CHÓT TUYỆT ĐỐI, không phải "khoảng ngân sách". Bản trước truyền xuống một
        # KHOẢNG, nên mỗi tầng chia đôi được cấp lại trọn 60 s: một dòng độc gặp đúng lúc
        # server trục trặc nhân ngân sách lên theo độ sâu cây đệ quy (đo được 778 s cho
        # một lần xả). Hạn chót chung làm cả cây đệ quy nằm gọn trong một ngân sách.
        if deadline is None:
            deadline = self.clock() + RETRY_BUDGET_S
        # Đếm THỜI GIAN THỰC, không phải tổng thời gian ngủ. Bản cũ chỉ cộng `delay` nên
        # thời gian nằm trong `client.insert` không vào sổ — mà driver mặc định
        # `send_receive_timeout=300`, nên một server treo cho ra 8 lần thử × 300 s = 40
        # PHÚT trong khi bộ đếm mới tới 63 s. Vượt xa cửa sổ dedup ~100 s mà hằng số này
        # tự khai là phải nằm dưới, và làm ngân sách xả cuối phiên (suy ra từ đây) mất căn cứ.
        delay = 1.0
        while True:
            try:
                self.client.insert(f"rt.{table}", block, column_names=COLUMNS[table])
                self.metrics.inc(f"rows.{table}", len(block))
                return
            except Exception as e:  # noqa: BLE001 — phân loại rồi xử lý theo hợp đồng
                if not _is_deterministic(e):
                    if self.clock() >= deadline:
                        self.metrics.inc(f"dropped_block.{table}", len(block))
                        # In cả MÃ lỗi: khi server tắt show_clickhouse_errors thì `%r` rút
                        # gọn còn câu chung chung, mã là thứ duy nhất còn dùng để lần ra
                        # nguyên nhân và quyết định có bổ sung vào _DETERMINISTIC_CODES không.
                        log.error("bỏ block %s (%d dòng) — quá hạn chung %ds thêm %.1fs: code=%s %r",
                                  table, len(block), RETRY_BUDGET_S, self.clock() - deadline,
                                  getattr(e, "code", None), e)
                        return
                    self.sleep(delay)
                    delay = min(delay * 2, 16.0)
                    continue                      # retry NGUYÊN block — không gộp dòng mới
                if len(block) == 1:
                    self.metrics.inc(f"poison_row.{table}")
                    log.error("dòng độc %s: code=%s %r — %r",
                              table, getattr(e, "code", None), block[0], e)
                    return
                mid = len(block) // 2             # lỗi tất định → cô lập dòng hỏng (§5.8)
                self._write_block(table, block[:mid], deadline)   # hạn chót CHUNG
                self._write_block(table, block[mid:], deadline)
                return
