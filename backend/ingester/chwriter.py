"""Batch writer ClickHouse — hợp đồng spec CH §5 + spec spill §2: vòng QUẢN (manage_once,
cắt buffer/gauge, không bao giờ chạm ClickHouse) tách khỏi vòng GHI (write_once, một hạn
mức thời gian mỗi lần gọi) — vòng quản không bao giờ bị một insert treo chặn lại (spec
spill §2.1). Hàng đợi là MỘT deque toàn cục (không còn dict theo bảng); mỗi phần tử một
block chờ ghi. Task này CHƯA có chế độ đĩa (spill) — giữ nguyên ngữ nghĩa cũ: retry
NGUYÊN block, chia đôi block độc, hết RETRY_BUDGET_S thì bỏ block (Task 6 sẽ đổi chỗ này
thành tràn xuống đĩa)."""
from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass

from clickhouse_connect.driver.exceptions import DataError

from ingester.normalize import COLUMNS, Metrics, Normalized

log = logging.getLogger("ingester.chwriter")
BLOCK_CAP = 5000
RETRY_BUDGET_S = 60          # < tuổi thọ cửa sổ dedup ~100 s (spec CH §5.5)
ROW_BYTES_EST = 497          # đo brief §3.2 — KHÔNG getsizeof trên đường chạy
WARN_DEPTH_ROWS = 50_000     # brief §5.1 đòi ngưỡng cảnh báo kèm metric
WRITE_CALL_BUDGET_S = 5.0    # hạn mức MỘT LẦN GỌI write_once — vòng lặp ở main gọi lại mỗi nhịp

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


@dataclass
class _Pending:
    """Một block đang chờ ghi trong hàng đợi toàn cục. `first_try` = thời điểm (theo
    `clock`) lần đầu gặp lỗi transient — hạn chót retry tính từ đây, không cấp lại mỗi
    nhịp gọi (giữ đúng bài học "hạn chót tuyệt đối" của bản v1)."""
    table: str
    block: list
    first_try: float | None = None


class ChWriter:
    def __init__(self, client, spill=None, sleep_fn=time.sleep, clock=time.monotonic):
        self.client = client
        self.spill = spill                     # Task 6+: chế độ đĩa. Task này chỉ giữ tham chiếu.
        self.sleep = sleep_fn
        self.clock = clock
        self.metrics = Metrics()
        self.buffers: dict[str, list[list]] = {t: [] for t in COLUMNS}
        self.queue: deque[_Pending] = deque()  # RAM: block đã cắt khỏi buffer, chờ ghi
        self.queue_rows = 0
        self.head: deque[_Pending] = deque()   # Task 6: block đọc lại từ đĩa, ghi trước queue
        self.head_rows = 0
        self.disk_mode = False                 # Task 6: bật khi RAM vượt trần
        self.insert_s: deque[float] = deque(maxlen=4096)
        # (mã, repr) của lỗi insert gần nhất — KHÔNG giữ nguyên exception: nó mang
        # `__traceback__` ghim cả block lỗi (~2,5 MB) sống tới lần lỗi kế tiếp, trong khi
        # log chỉ cần đúng mã + mô tả.
        self._last_err: tuple[int | None, str] | None = None
        # add() chạy trên event-loop thread, manage_once()/write_once() chạy trong thread
        # khác qua asyncio.to_thread — pha cắt buffer (copy+clear) phải atomic với add()
        # (§CRITICAL 1 review wave 2), nếu không có thể mất dòng vừa append đúng lúc buffer
        # bị cắt. `_lock` CHỈ bảo vệ các pha ngắn (cắt buffer, peek/pop hàng đợi) — KHÔNG
        # bao giờ giữ trong lúc gọi `client.insert` (đó là điều làm vòng quản Task 5 khác
        # bản cũ: một insert treo không còn chặn được manage_once — spec spill §2.1, test
        # `test_manage_runs_while_insert_hangs`).
        self._lock = threading.Lock()
        # Mutex riêng cho PHA GHI: lúc tắt, task write bị cancel() nhưng thread `write_once`
        # vẫn có thể đang chạy trong khi code khởi ghi cuối cùng gọi lại — hai thread cùng
        # đọc/pop đầu hàng đợi thì một block có thể bị ghi đôi hoặc bị bỏ qua (review cuối
        # IMPORTANT 4, kế thừa từ `_flush_lock` bản v1). Không lấy được thì về ngay — nhịp
        # sau ghi tiếp. `manage_once()` KHÔNG dùng khoá này — nó chỉ cần `_lock`.
        self._write_lock = threading.Lock()

    def add(self, n: Normalized) -> None:
        with self._lock:
            buf = self.buffers[n.table]
            buf.append([n.row.get(c) for c in COLUMNS[n.table]])
            if len(buf) >= BLOCK_CAP:
                self.queue.append(_Pending(table=n.table, block=buf[:]))
                self.queue_rows += len(buf)
                buf.clear()
                self.metrics.inc(f"block_cap.{n.table}")
                log.warning("bảng %s chạm trần block %d — tải cao bất thường", n.table, BLOCK_CAP)

    def manage_once(self) -> None:
        """Vòng QUẢN: cắt buffer → hàng đợi, cập nhật gauge. KHÔNG BAO GIỜ chạm
        ClickHouse — đây là điều làm nó không thể bị một insert treo chặn lại
        (Task 6 sẽ thêm cửa vào chế độ đĩa + quét spill tại đây)."""
        with self._lock:
            for table, buf in self.buffers.items():
                if buf:
                    self.queue.append(_Pending(table=table, block=buf[:]))
                    self.queue_rows += len(buf)
                    buf.clear()
            depth = self.head_rows + self.queue_rows
            self.metrics.set("pending_depth_rows", depth)
            self.metrics.set("pending_depth_bytes", depth * ROW_BYTES_EST)
        if depth > WARN_DEPTH_ROWS:
            log.warning("pending sâu %d dòng (> %d)", depth, WARN_DEPTH_ROWS)

    def write_once(self, budget_s: float = WRITE_CALL_BUDGET_S) -> None:
        """Vòng GHI: xử lý đầu hàng đợi trong một hạn mức thời gian mỗi lần gọi. Chỉ giữ
        `_lock` để peek/pop — KHÔNG BAO GIỜ trong lúc `client.insert` (RAM mode, Task này;
        Task 6 sẽ thêm nhánh đọc `head`/đĩa khi `disk_mode`)."""
        if not self._write_lock.acquire(blocking=False):
            return                             # đã có thread khác đang ghi — nhịp sau ghi tiếp
        try:
            end = self.clock() + budget_s
            while self.clock() < end:
                with self._lock:
                    if not self.queue:
                        return
                    p = self.queue[0]
                t0 = self.clock()
                status = self._insert(p.table, p.block)
                if status == "done":
                    with self._lock:
                        self.queue.popleft()
                        self.queue_rows -= len(p.block)
                    continue
                if status == "transient":
                    if p.first_try is None:
                        # Tính từ TRƯỚC lúc gọi insert (t0), không phải sau — bài học
                        # send_receive_timeout: một lần thử treo có thể tự ăn hết ngân
                        # sách retry ngay từ lần đầu, hạn chót phải tính cả thời gian NẰM
                        # TRONG lần thử đó, không chỉ thời gian chờ giữa các lần thử.
                        p.first_try = t0
                        # Chỉ log MỘT lần cho mỗi block khi lần đầu thấy transient — một
                        # block có thể còn nằm ở đầu hàng đợi qua rất nhiều nhịp gọi trước
                        # khi hết hạn hoặc thành công, log mỗi nhịp sẽ spam WARNING vô ích.
                        code, rep = self._last_err
                        log.warning("insert %s lỗi transient: code=%s %s", p.table, code, rep)
                    if self.clock() - p.first_try >= RETRY_BUDGET_S:
                        # TASK 5: giữ hành vi cũ — hết hạn thì bỏ block. Task 6 sẽ đổi
                        # nhánh này thành tràn xuống đĩa (spill) thay vì vứt bỏ.
                        with self._lock:
                            self.queue.popleft()
                            self.queue_rows -= len(p.block)
                        self.metrics.inc(f"dropped_block.{p.table}", len(p.block))
                        # In cả MÃ lỗi: khi server tắt show_clickhouse_errors thì repr rút
                        # gọn còn câu chung chung, mã là thứ duy nhất còn dùng để lần ra
                        # nguyên nhân và quyết định có bổ sung vào _DETERMINISTIC_CODES không.
                        code, rep = self._last_err
                        log.error("bỏ block %s (%d dòng) — quá hạn retry %ds: code=%s %s",
                                  p.table, len(p.block), RETRY_BUDGET_S, code, rep)
                        continue
                    return                      # chưa hết hạn — thử lại nhịp sau, không ngủ
                # "poison": lỗi tất định — cô lập dòng hỏng (§5.8)
                with self._lock:
                    self.queue.popleft()
                    if len(p.block) == 1:
                        self.queue_rows -= 1   # mọi thay đổi queue_rows phải nằm trong _lock
                if len(p.block) == 1:
                    self.metrics.inc(f"poison_row.{p.table}")
                    code, rep = self._last_err
                    log.error("dòng độc %s: code=%s %r — %s", p.table, code, p.block[0], rep)
                    continue
                mid = len(p.block) // 2
                first = _Pending(table=p.table, block=p.block[:mid])
                second = _Pending(table=p.table, block=p.block[mid:])
                with self._lock:
                    # appendleft nửa SAU rồi nửa TRƯỚC → nửa TRƯỚC nằm đúng đầu hàng đợi
                    # (giữ vị trí đầu — trần tự nhiên theo độ sâu chia, không đệ quy, không
                    # cấp lại ngân sách thời gian cho từng tầng chia).
                    self.queue.appendleft(second)
                    self.queue.appendleft(first)
                continue
        finally:
            self._write_lock.release()

    def _insert(self, table: str, block: list) -> str:
        """MỘT lần thử `client.insert`. Không sleep, không đệ quy — phân loại kết quả rồi
        trả về ngay cho `write_once` quyết định tiếp. `"done"` | `"transient"` | `"poison"`.
        Log transient/drop là việc của `write_once` (chỉ log lần đầu mỗi block, không mỗi
        lần thử) — ở đây chỉ phân loại và ghi lại (mã, repr) vào `_last_err`."""
        t0 = self.clock()
        try:
            self.client.insert(f"rt.{table}", block, column_names=COLUMNS[table])
        except Exception as e:  # noqa: BLE001 — phân loại rồi xử lý theo hợp đồng
            self.insert_s.append(self.clock() - t0)
            self._last_err = (getattr(e, "code", None), repr(e))
            if not _is_deterministic(e):
                return "transient"
            return "poison"
        else:
            self.insert_s.append(self.clock() - t0)
            self.metrics.inc(f"rows.{table}", len(block))
            return "done"

    def flush_once(self) -> None:
        """Tương thích với đường gọi cũ/test cũ: một lượt quản rồi ghi với ngân sách đủ
        rộng để xả hết những gì vừa cắt (không phải vòng lặp thật — main.py dùng
        `manage_once`/`write_once` riêng, xem `manage_loop`/`write_loop`)."""
        self.manage_once()
        self.write_once(budget_s=RETRY_BUDGET_S + 30)

    def clean(self) -> bool:
        """Buffer + hàng đợi RAM đã rỗng (Task 8 sẽ thêm điều kiện `spill.empty()` khi
        chế độ đĩa tồn tại thật)."""
        return not any(self.buffers.values()) and not self.queue and not self.head

    def insert_percentiles(self) -> dict:
        xs = sorted(self.insert_s)
        if not xs:
            return {}
        pick = lambda q: xs[min(len(xs) - 1, int(q * len(xs)))]  # noqa: E731
        return {"p50": pick(0.50), "p95": pick(0.95), "p99": pick(0.99)}
