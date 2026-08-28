"""Batch writer ClickHouse — hợp đồng spec CH §5 + spec spill §2: vòng QUẢN (manage_once,
cắt buffer/gauge, không bao giờ chạm ClickHouse) tách khỏi vòng GHI (write_once, một hạn
mức thời gian mỗi lần gọi) — vòng quản không bao giờ bị một insert treo chặn lại (spec
spill §2.1). Hàng đợi là MỘT deque toàn cục (không còn dict theo bảng); mỗi phần tử một
block chờ ghi.

Task 6 thêm CHẾ ĐỘ ĐĨA với hai cửa vào (spec spill §2.3): trần RAM theo DÒNG, và block
cạn ngân sách retry. Hệ quả lớn: **`dropped_block` chết hẳn** — không còn đường bỏ dòng
theo thời gian ở mode run. Đường mất dòng duy nhất còn lại là trần đĩa / không có đĩa,
và đường đó có sổ sách đầy đủ (`spill_drop_newest.<bảng>` + log cấu trúc, spec §6)."""
from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import date

from clickhouse_connect.driver.exceptions import ClickHouseError, DataError

from ingester.normalize import COLUMNS, Metrics, Normalized

log = logging.getLogger("ingester.chwriter")
BLOCK_CAP = 5000
RETRY_BUDGET_S = 60          # hạn CỬA 2 (spec spill §2.3) — cửa sổ dedup CH đếm bằng
                              # BLOCK (100/bảng, spec spill §7), KHÔNG bằng giây; "< ~100 s"
                              # là hằng số giả đã sửa 2026-08-27, xem market-data-store §3.7
ROW_BYTES_EST = 497          # đo brief §3.2 — KHÔNG getsizeof trên đường chạy
WARN_DEPTH_ROWS = 50_000     # brief §5.1 đòi ngưỡng cảnh báo kèm metric
WRITE_CALL_BUDGET_S = 5.0    # hạn mức MỘT LẦN GỌI write_once — vòng lặp ở main gọi lại mỗi nhịp

# --- Hằng số chế độ đĩa — điền theo gate đo 2026-08-27 (spec spill §2.5) --------------
# Không con số nào bốc thuốc: probe `tests/clickhouse/test_c99_dedup_probe.py` + số phiên
# thật 27/08 (brief §3) là căn cứ, ghi ngay tại chỗ theo luật CLAUDE.md §1.2.
N_CAP_ROWS = 100_000      # 100.000 × 497 B = 49,7 MB ≤ ngân sách hàng đợi ~50 MB
                          # (200 − 97 writer nền − 13 tiến trình đo − ~12 buffers);
                          # ≈ 15 s ATO đỉnh (6.496 dòng/s) ≈ 5 s × hệ số 3.
K_REPLAY_ROWS = 20_000    # > 6.496 dòng/s × hệ số 3 = 19.488. Điều kiện khả thi spec §2.4
                          # ĐẠT với biên ≈2,8× — KHÔNG phải 8,7× như bản đầu ghi (đính
                          # chính review cuối 2026-08-27, spec §2.5): 8,7× lấy p95 88 ms
                          # của insert 5.000 DÒNG rồi chia đều, chỉ đúng nếu phát lại toàn
                          # block đầy. Với interleave 5 bảng thật, file '-n' liền kề hiếm
                          # khi cùng bảng ⇒ run cùng-bảng dài 1, gộp gần như không ăn, chi
                          # phí bám p95 block NHỎ ≈ 55 µs/dòng ⇒ 6.496 × 55 µs ≈ 0,36 < 1.
                          # Vẫn đạt nên K giữ nguyên; đây là số SUY từ p95 block nhỏ, chưa
                          # đo interleave thật (AC2 chỉ feed trade nên không thấy). p95 hồ
                          # sơ VPS hẹp ≈ hồ sơ dev (88,2 vs 87,5 ms) nên không hiệu chỉnh.
SPILL_CAP_BYTES = 10 * 2**30   # 10 GiB — pickle đo 65 B/dòng (§9.2): 6.496 dòng/s ×
                               # 7.200 s × 65 B × 3 ≈ 9,1 GB ≤ 10 GiB (≥ 2 giờ sự cố ở
                               # tải đỉnh × hệ số 3).

# Vị trí cột `received_at` tra SẴN một lần — log bỏ block (spec §6) cần min/max của nó
# trên đường nóng, không được `cols.index(...)` lại cho từng block.
RA_IDX = {t: cols.index("received_at") for t, cols in COLUMNS.items()}

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


def _block_days(table: str, block: list) -> set[date]:
    """Tập ngày (giờ VN — `received_at` do writer cấp, đã tz-aware) mà một block chạm tới,
    đọc từ dòng ĐẦU và CUỐI. Dòng thiếu `received_at` bỏ qua, không đoán."""
    out: set[date] = set()
    if not block:
        return out
    ra = RA_IDX[table]
    for row in (block[0], block[-1]):
        ts = row[ra]
        if ts is not None:
            out.add(ts.date())
    return out


def _is_deterministic(e: Exception) -> bool:
    """Lỗi dữ liệu (không retry được) hay không. Mọi lỗi KHÁC coi là transient."""
    if isinstance(e, _DETERMINISTIC_TYPES):
        return True
    # Lỗi serialize PHÍA CLIENT: `driver.transform` gói giá trị vào cột native và ném
    # AttributeError/TypeError/ValueError TRẦN — không `.code`, không phải
    # ClickHouseError — TRƯỚC khi byte nào rời tiến trình. Không byte nào đi thì thử lại
    # bao nhiêu lần cũng hỏng y hệt ⇒ tất định. Lỗi server LUÔN mang `.code`, còn
    # ConnectionError/TimeoutError là OSError nên không lọt vào isinstance dưới đây.
    # Vì sao đáng sửa dù `normalize.py` đã che đường thật: sau lát tràn-ra-đĩa, một dòng
    # hỏng vĩnh viễn bị đọc nhầm thành transient sẽ đi 60 s → cửa 2 → file `-r` → phát
    # lại lại hỏng, KẸT ĐẦU HÀNG ĐỢI ĐĨA và không thoát chế độ đĩa cả phiên.
    if (isinstance(e, (AttributeError, TypeError, ValueError))
            and not isinstance(e, ClickHouseError)
            and getattr(e, "code", None) is None):
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
        self.spill = spill                     # SpillStore | None (None = chạy KHÔNG có lưới đĩa)
        self.sleep = sleep_fn
        self.clock = clock
        self.metrics = Metrics()
        self.buffers: dict[str, list[list]] = {t: [] for t in COLUMNS}
        self.queue: deque[_Pending] = deque()  # RAM: block đã cắt khỏi buffer, chờ ghi
        self.queue_rows = 0
        # Chế độ đĩa: `head` = phần `queue` bị ĐÔNG CỨNG lúc vào chế độ (cũ nhất, ghi
        # trước đĩa để giữ FIFO toàn cục — spec §2.3.4); `queue` từ đó chỉ còn là chỗ tạm
        # giữa hai nhịp vòng quản trước khi xuống đĩa.
        self.head: deque[_Pending] = deque()
        self.head_rows = 0
        self.disk_mode = False
        self._disk_since = 0.0                 # mốc `clock()` lúc vào chế độ đĩa (cho log ra)
        self._disk_blocks = 0                  # số block đã xuống đĩa trong LƯỢT đĩa này
        # Giá trị counter store đã chép sang `metrics` lần gần nhất — để chép tiếp bằng
        # DELTA thay vì ghi đè (xem `manage_once`).
        self._mirrored: dict[str, int] = {}
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
        """Vòng QUẢN: cắt buffer → hàng đợi, cập nhật gauge, kiểm hai cửa vào chế độ đĩa,
        đẩy block mới xuống đĩa khi đang ở chế độ đĩa. KHÔNG BAO GIỜ chạm ClickHouse — đây
        là điều làm nó không thể bị một insert treo chặn lại (spec §2.1)."""
        self._adopt_spill_if_possible()
        if self.spill is not None and self.spill.owned:
            # Sao chép MỖI NHỊP, không chỉ lúc nhận nuôi: `replay_corrupt` là một sự kiện
            # MẤT DÒNG và nó xảy ra trong lúc chạy: chỉ chép một lần lúc khởi động thì mọi
            # file hỏng về sau không bao giờ lên metric (spec §6 — mọi mất mát phải đếm
            # được). Chép dict 4 khoá, rẻ (review M3).
            #
            # 🔴 Chép bằng DELTA + `inc`, không phải `set`: đây đều là counter đơn điệu chứ
            # không phải gauge, và `spill_io_error` có HAI nguồn — store tự đếm lỗi đọc/ghi
            # bên trong nó, còn `replay_debt`/`manage_loop`/`write_loop` `inc` thêm cho lỗi
            # I/O bắt được ở tầng ngoài. `set` sẽ NUỐT phần tầng ngoài mỗi nhịp. Delta 0
            # vẫn gọi `inc` để khoá luôn có mặt trên bảng đếm ngay từ nhịp đầu.
            for key, val in self.spill.counters.items():
                self.metrics.inc(key, val - self._mirrored.get(key, 0))
                self._mirrored[key] = val
            # Gauge `spill_bytes` (spec §8) — miễn phí: `bytes_used` là biến đếm store đã
            # duy trì sẵn. KHÔNG kèm `spill_files` ở đây: đếm file là một lần liệt kê thư
            # mục trên đường nóng mỗi nhịp, mà `spill_blocks`/`replay_blocks` đã nói đủ về
            # số block vào/ra. Số file chỉ lấy ở đường nguội (`SpillStore.pending_files`).
            self.metrics.set("spill_bytes", self.spill.bytes_used)
        with self._lock:
            for table, buf in self.buffers.items():
                if buf:
                    self.queue.append(_Pending(table=table, block=buf[:]))
                    self.queue_rows += len(buf)
                    buf.clear()
            queue_rows = self.queue_rows       # chụp DƯỚI khoá — đây là input điều khiển
            depth = self.head_rows + queue_rows
            self.metrics.set("pending_depth_rows", depth)
            self.metrics.set("pending_depth_bytes", depth * ROW_BYTES_EST)
        if depth > WARN_DEPTH_ROWS:
            log.warning("pending sâu %d dòng (> %d)", depth, WARN_DEPTH_ROWS)
        if not self.disk_mode and queue_rows > N_CAP_ROWS:
            self._enter_disk("ram_cap")        # CỬA 1: trần RAM theo DÒNG (spec §2.3)
        if self.disk_mode:
            self._spill_tail()
            self._maybe_exit_disk()

    def _adopt_spill_if_possible(self) -> None:
        """Mỗi nhịp, mọi chế độ: có thư mục spill mà chưa sở hữu thì thử giành. Giành được
        nghĩa là chủ cũ đã CHẾT THẬT (OS nhả khoá) — mới được đụng file (spec §4). Còn file
        sót ⇒ đó là nợ của tiến trình trước, vào thẳng chế độ đĩa để phát lại theo FIFO."""
        if self.spill is None or self.spill.owned:
            return
        if not self.spill.try_acquire():
            return                             # chủ cũ còn sống — KHÔNG đụng, kể cả đọc
        # `try_acquire` đã quét ngay trong lúc giành khoá (spill.py, nợ M4) — KHÔNG quét
        # lại ở đây: quét xoá cả `.tmp` mồ côi, mà từ nhịp này trở đi thread vòng ghi có
        # thể đang có một `.tmp` sống giữa chừng. Counter quét được do `manage_once` sao
        # chép ngay bên dưới.
        if not self.spill.empty():
            self._enter_disk("adopt")

    def _enter_disk(self, door: str) -> None:
        """Vào chế độ đĩa: `queue` hiện tại ĐÔNG CỨNG thành `head` (không xuống đĩa — nó đã
        ở RAM rồi, ghi ra rồi đọc lại chỉ tốn I/O), `queue` thành deque rỗng để nhận block
        cắt mới; từ nhịp sau mọi block mới đi thẳng xuống đĩa (spec §2.3.3)."""
        with self._lock:
            # 🔴 Kiểm-VÀ-đặt phải NGUYÊN TỬ, cùng một lần giữ khoá. Chốt nằm ngoài khoá thì
            # cửa 1 (thread vòng quản) và cửa 2 (thread vòng ghi) cùng lọt qua khi
            # `disk_mode` còn False; lần đông cứng thứ hai gán `head` = `queue` MỚI (rỗng)
            # và NUỐT SẠCH phần đã đông cứng lần đầu — tới N_CAP_ROWS dòng, không counter,
            # không log. (review C1, test `test_concurrent_enter_disk_never_discards_...`)
            if self.disk_mode:
                return                         # đã ở chế độ đĩa — không đông cứng chồng head
            self.head = self.queue
            self.head_rows = self.queue_rows
            self.queue = deque()
            self.queue_rows = 0
            self.disk_mode = True
            head_rows = self.head_rows
        self._disk_since = self.clock()
        log.warning("VÀO chế độ đĩa (cửa %s) — đầu RAM đông cứng %d dòng", door, head_rows)

    def _maybe_exit_disk(self) -> None:
        """Ra chế độ đĩa CHỈ khi cả ba cùng rỗng: đầu RAM, hàng đợi mới, và đĩa (spec
        §2.3.6). Rỗng một phần mà ra sớm sẽ phá FIFO toàn cục."""
        with self._lock:
            if self.head or self.queue:
                return
        # `.owned` là một phần của điều kiện, không phải chi tiết thừa (ruling T8-2): tiến
        # trình THUA `try_acquire` vẫn vào chế độ đĩa được (cửa 1 vô điều kiện), mà file
        # của CHỦ THẬT thì không bao giờ tự biến mất dưới tay nó ⇒ không có `.owned` thì
        # nó KẸT chế độ đĩa cả phiên: mọi block mới rơi vào `spill_drop_newest` (ghi vào
        # đĩa của người khác là không được phép) trong khi `clean()` vẫn True nên phán
        # quyết cuối phiên in ra như đáng tin. Đĩa của người khác = coi như không có đĩa.
        if self.spill is not None and self.spill.owned and not self.spill.empty():
            return
        self.disk_mode = False
        log.warning("RA chế độ đĩa sau %.1fs — %d block đã qua đĩa",
                    self.clock() - self._disk_since, self._disk_blocks)
        self._disk_blocks = 0

    def _spill_tail(self) -> None:
        """Chế độ đĩa: đẩy TOÀN BỘ hàng đợi hiện tại xuống đĩa trong nhịp này. Pop DƯỚI
        `_lock` từng cái một, ghi đĩa NGOÀI `_lock` — I/O đĩa không bao giờ được giữ khoá
        (nếu giữ thì `add()` trên event-loop kẹt theo, đúng cái spec §2.1 cấm)."""
        while True:
            with self._lock:
                if not self.queue:
                    return
                p = self.queue.popleft()
                self.queue_rows -= len(p.block)
            self._spill_block(p, "n")

    def _spill_block(self, p: _Pending, kind: str) -> None:
        """Ghi một block xuống đĩa. Không ghi được (đĩa đầy, lỗi I/O, hoặc KHÔNG CÓ đĩa)
        → đường thoát cuối duy nhất còn lại của mode run: bỏ block MỚI đến, kèm sổ sách đủ
        để dựng lại thủ công từ bản đo (spec §6) — counter tách theo bảng + một dòng log
        cấu trúc chỉ đúng khoảng `received_at` bị thủng."""
        if self.spill is not None and self.spill.write(p.table, p.block, kind):
            self.metrics.inc("spill_blocks")
            self.metrics.inc("spill_rows", len(p.block))
            self._disk_blocks += 1
            return
        self._drop_ledger(p, "spill_drop_newest", "không ghi được xuống đĩa")

    def _drop_ledger(self, p: _Pending, counter: str, reason: str) -> None:
        """Bỏ một block KÈM SỔ SÁCH — nguyên tắc spec §6: mọi mất mát phải đếm được và
        định vị được. Counter tách theo bảng, đếm theo DÒNG; một dòng log cấu trúc chỉ đúng
        khoảng `received_at` bị thủng để người dựng lại thủ công từ bản đo biết tìm ở đâu.
        Hai đường gọi, hai counter — đừng gộp làm một vì chúng nói hai chuyện khác nhau:
        `spill_drop_newest` = có đĩa nhưng đĩa từ chối (đầy/lỗi I/O) hoặc đang ở chế độ đĩa
        mà không có đĩa; `no_spill_dropped` = cấu hình suy giảm, chạy không có lưới đĩa."""
        n_rows = len(p.block)
        self.metrics.inc(f"{counter}.{p.table}", n_rows)
        ra = RA_IDX[p.table]
        stamps = [r[ra] for r in p.block if r[ra] is not None]
        log.error("BỎ block %s — n_rows=%d received_at_min=%s received_at_max=%s (%s)",
                  p.table, n_rows, min(stamps, default=None),
                  max(stamps, default=None), reason)

    def write_once(self, budget_s: float = WRITE_CALL_BUDGET_S) -> None:
        """Vòng GHI: một hạn mức thời gian mỗi lần gọi. Chỉ giữ `_lock` để peek/pop —
        KHÔNG BAO GIỜ trong lúc `client.insert`. Chế độ RAM xả `queue`; chế độ đĩa xả đầu
        RAM rồi tới đĩa, có thêm hạn mức K theo DÒNG (spec §2.3.4)."""
        if not self._write_lock.acquire(blocking=False):
            return                             # đã có thread khác đang ghi — nhịp sau ghi tiếp
        try:
            if self.disk_mode:
                self._drain_disk_step(budget_s)
            else:
                self._drain_ram(budget_s)
        finally:
            self._write_lock.release()

    def _drain_ram(self, budget_s: float) -> None:
        """Chế độ RAM: xả `queue` theo FIFO tới khi hết hạn mức thời gian của lần gọi."""
        end = self.clock() + budget_s
        while self.clock() < end:
            if self.disk_mode:
                # Vòng quản (thread khác) vừa lật chế độ giữa lần gọi này. Về NGAY: từ đây
                # `queue` là chỗ tạm của `_spill_tail`, ta mà bốc tiếp thì cùng một block
                # vừa vào kho vừa thành file '-n' — phát lại có gộp nên hash đổi, lưới
                # dedup của ClickHouse không bắt được bản trùng đó (review I2).
                return
            with self._lock:
                if not self.queue:
                    return
                p = self.queue[0]
            t0 = self.clock()
            status = self._insert(p.table, p.block)
            if status == "done":
                self._detach_front(p)
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
                    # CỬA 2 (spec §2.3): cạn ngân sách retry KHÔNG còn là bỏ block. Block
                    # xuống đĩa loại '-r' (phát lại nguyên văn, giữ hash cho lưới dedup) và
                    # cả writer chuyển sang chế độ đĩa. Đây là lý do `dropped_block` chết:
                    # ở tải nhẹ hàng đợi không bao giờ chạm N, nên nếu giữ drop-theo-hạn-chót
                    # thì một lần `docker stop` vài phút chắc chắn mất dòng (review A-B2).
                    # In cả MÃ lỗi: khi server tắt show_clickhouse_errors thì repr rút gọn
                    # còn câu chung chung, mã là thứ duy nhất còn dùng để lần ra nguyên nhân
                    # và quyết định có bổ sung vào _DETERMINISTIC_CODES không.
                    if self._detach_front(p) is None:
                        return
                    code, rep = self._last_err
                    if self.spill is None or not self.spill.owned:
                        # CẤU HÌNH SUY GIẢM — chạy KHÔNG có lưới đĩa (chưa dựng spill, hoặc
                        # thư mục đang bị tiến trình khác giữ, spec §4). Cửa 2 KHÔNG mở ở
                        # đây: vào chế độ đĩa mà không có đĩa thì mọi block MỚI bị bỏ suốt
                        # sự cố, tệ hơn hẳn bỏ đúng một block cạn hạn chót rồi xả tiếp. Bỏ
                        # block cũ nhất, có sổ đầy đủ (spec §6), ở lại chế độ RAM — trần RAM
                        # vẫn do CỬA 1 canh, nên không quay lại được bệnh phình vô hạn.
                        self._drop_ledger(
                            p, "no_spill_dropped",
                            f"cạn ngân sách retry {RETRY_BUDGET_S}s, không có lưới đĩa: "
                            f"code={code} {rep}")
                        continue                # hàng đợi xả tiếp block sau, không kẹt
                    log.warning("block %s (%d dòng) cạn ngân sách retry %ds → xuống đĩa: "
                                "code=%s %s", p.table, len(p.block), RETRY_BUDGET_S, code, rep)
                    self._spill_block(p, "r")
                    self._enter_disk("retry_budget")
                    return
                return                          # chưa hết hạn — thử lại nhịp sau, không ngủ
            # "poison": lỗi tất định — cô lập dòng hỏng (§5.8)
            self._isolate_poison(p)

    def _drain_disk_step(self, budget_s: float) -> None:
        """Chế độ đĩa: FIFO toàn cục — đầu RAM (cũ nhất) trước, rồi đĩa theo thứ tự tên
        file. `K_REPLAY_ROWS` là trần TỔNG số dòng insert cho CẢ lần gọi, tính cả phần lấy
        từ đầu RAM (spec §2.3.4) — không có nhịp "xả dồn" nào lúc ClickHouse vừa gượng dậy.
        KHÔNG có drop theo thời gian ở đây: transient thì về, nhịp sau thử tiếp (§2.3.5)."""
        end = self.clock() + budget_s
        budget = K_REPLAY_ROWS
        while budget > 0 and self.clock() < end:
            with self._lock:
                p = self.head[0] if self.head else None
            if p is not None:
                status = self._insert(p.table, p.block)
                if status == "done":
                    self._detach_front(p)
                    budget -= len(p.block)
                    continue
                if status == "transient":
                    return
                self._isolate_poison(p)
                continue
            # KHÔNG sở hữu thì KHÔNG đụng, kể cả ĐỌC (spec §4). Trạng thái này đến được:
            # cửa 1 vô điều kiện nên tiến trình thua `try_acquire` vẫn vào chế độ đĩa —
            # đọc/xoá ở đó là lấy mất file của chủ thật (chủ mất vĩnh viễn, kho nhận bản
            # trùng). Coi phần đĩa như rỗng cho tới khi `_adopt_spill_if_possible` giành
            # được khoá (review I1).
            if self.spill is None or not self.spill.owned:
                return
            item = self.spill.next_batch(max_rows=budget)
            if item is None:
                return
            status = self._insert(item.table, item.block)
            if status == "done":
                self.spill.delete(item)        # XOÁ CHỈ SAU insert thành công (spec §3)
                self.metrics.inc("replay_blocks", len(item.paths))
                # Đếm cả DÒNG, không chỉ file: số hạng `trùng_replay` của AC3 tính theo
                # dòng, mà một file chứa từ 1 tới BLOCK_CAP dòng — chỉ có `replay_blocks`
                # thì trùng_replay chỉ CHẶN TRÊN được chứ không tính được.
                self.metrics.inc("replay_rows", item.n_rows)
                budget -= item.n_rows
                continue
            if status == "transient":
                return                          # file nằm nguyên đó — nhịp sau thử tiếp
            if not self._split_disk_item(item):
                return                          # giữ cha — đừng chia lại ngay trong lần gọi

    def _front_deque(self, p: _Pending) -> deque | None:
        """Hàng đợi RAM đang giữ `p` ở ĐẦU (`queue` hay `head`), `None` nếu không hàng đợi
        nào. GỌI KHI ĐANG GIỮ `_lock`.

        🔴 Tìm theo ĐỊNH DANH, không theo vị trí. Vòng quản chạy ở THREAD KHÁC có thể
        `_enter_disk` ngay giữa lúc `client.insert` — lúc đó `queue` cũ đã thành `head` còn
        `self.queue` là deque MỚI. `self.queue.popleft()` mù khi ấy hoặc nổ `IndexError`,
        hoặc (tệ hơn, im lặng) gỡ một block KHÁC chưa từng được ghi ⇒ mất dòng không dấu
        vết — đúng họ lỗi mà cả lát này sinh ra để đóng."""
        if self.queue and self.queue[0] is p:
            return self.queue
        if self.head and self.head[0] is p:
            return self.head
        return None

    def _detach_front(self, p: _Pending) -> deque | None:
        """Gỡ `p` khỏi đầu hàng đợi đang chứa nó, trừ đúng số dòng của hàng đợi ĐÓ, trả về
        chính deque đó (`None` nếu không tìm thấy)."""
        with self._lock:
            dq = self._front_deque(p)
            if dq is None:
                found = False
            else:
                found = True
                dq.popleft()
                if dq is self.head:
                    self.head_rows -= len(p.block)
                else:
                    self.queue_rows -= len(p.block)
        if not found:
            log.error("block %s (%d dòng) không còn ở đầu hàng đợi nào — không gỡ",
                      p.table, len(p.block))
            return None
        return dq

    def _isolate_poison(self, p: _Pending) -> None:
        """Cô lập dòng độc cho block NẰM TRONG RAM (`queue` ở chế độ RAM, `head` ở chế độ
        đĩa) — cùng một luật, hai hàng đợi, nên viết một chỗ. Gỡ và đẩy hai nửa trở lại
        nằm TRONG CÙNG một lần giữ `_lock`: nửa chừng mà vòng quản chen vào thì hai nửa có
        thể rơi vào deque đã mồ côi."""
        one_row = len(p.block) == 1
        first = second = None
        if not one_row:
            mid = len(p.block) // 2
            first = _Pending(table=p.table, block=p.block[:mid])
            second = _Pending(table=p.table, block=p.block[mid:])
        with self._lock:
            dq = self._front_deque(p)
            if dq is not None:
                dq.popleft()
                if one_row:                    # mọi thay đổi *_rows phải nằm trong _lock
                    if dq is self.head:
                        self.head_rows -= 1
                    else:
                        self.queue_rows -= 1
                else:
                    # appendleft nửa SAU rồi nửa TRƯỚC → nửa TRƯỚC nằm đúng đầu hàng đợi
                    # (giữ vị trí đầu — trần tự nhiên theo độ sâu chia, không đệ quy, không
                    # cấp lại ngân sách thời gian cho từng tầng chia). Tổng dòng không đổi
                    # nên không đụng tới *_rows.
                    dq.appendleft(second)
                    dq.appendleft(first)
        if dq is None:
            log.error("block độc %s (%d dòng) không còn ở đầu hàng đợi nào — không chia",
                      p.table, len(p.block))
            return
        if one_row:
            self.metrics.inc(f"poison_row.{p.table}")
            code, rep = self._last_err
            log.error("dòng độc %s: code=%s %r — %s", p.table, code, p.block[0], rep)

    def _split_disk_item(self, item) -> bool:
        """Dòng độc trên một item ĐÃ Ở ĐĨA: ghi HAI file con rồi xoá file cha TRƯỚC khi
        insert bất kỳ con nào (spec §3) — biến một block không nguyên tử thành hai block
        nguyên tử, đóng ca "insert nửa block rồi chết → phát lại trùng nửa đầu".

        Hai file con nằm ở CUỐI hàng đợi đĩa (seq mới), không giữ vị trí đầu như nhánh RAM.
        Đây là ngoại lệ FIFO có chủ đích và vô hại: spec §2.3.6 ghi rõ FIFO toàn cục là
        ràng buộc tự đặt cho dễ suy luận, KHÔNG bất biến đọc nào đòi thứ tự insert (MV nến
        khoá theo giá trị cột). Đổi lại: cô lập dòng độc không chặn phần còn lại của đĩa.

        Trả về False khi giữ lại file cha — caller PHẢI dừng vòng xả khi đó (review I3)."""
        if item.n_rows == 1:
            self.metrics.inc(f"poison_row.{item.table}")
            code, rep = self._last_err
            log.error("dòng độc %s (đĩa): code=%s %r — %s",
                      item.table, code, item.block[0], rep)
            self.spill.delete(item)
            return True
        mid = item.n_rows // 2
        ok_first = self.spill.write(item.table, item.block[:mid], item.kind)
        ok_second = ok_first and self.spill.write(item.table, item.block[mid:], item.kind)
        if not ok_second:
            # Ghi con hỏng → GIỮ file cha, NHỊP SAU chia lại (SpillStore đã đếm lỗi I/O).
            # Nhịp sau, không phải vòng sau: cùng lần gọi mà bốc lại đúng item cha đó thì
            # mỗi vòng lặp đẻ thêm một file con mồ côi (review I3).
            # Nếu con đầu đã ghi được thì lần phát lại tới sẽ trùng nửa đầu — chấp nhận
            # theo quyết định #4 "thà trùng hơn mất": trùng có dấu ở đối chứng d[], mất thì
            # không có gì lần ra.
            log.error("spill: chia đôi block độc %s hỏng giữa chừng — giữ file cha",
                      item.table)
            return False
        self.spill.delete(item)
        return True

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
        """Buffer + hàng đợi RAM + ĐĨA đều rỗng (spec §5.1).

        Đĩa chỉ tính khi TA sở hữu nó: file trong một store chưa giành được khoá là hàng
        đợi của tiến trình KHÁC (spec §4) — ta không có quyền đọc/xoá nên cũng không có
        món nợ nào để trả; để nó chặn `clean()` thì phiên nào cũng kết thúc bằng phán
        quyết "không đáng tin" vì nợ của người khác."""
        if self.spill is not None and self.spill.owned and not self.spill.empty():
            return False
        return not any(self.buffers.values()) and not self.queue and not self.head

    def replay_debt(self) -> set[date]:
        """Xả TOÀN BỘ nợ đĩa TRƯỚC PHIÊN — trả về tập ngày mà nợ đó thuộc về (spec §5.3).

        Hết tốc lực, KHÔNG có trần `K_REPLAY_ROWS`: tiết lưu K sinh ra để chừa băng thông
        ClickHouse cho dòng ĐANG chảy của phiên (spec §2.4), mà ở đây chưa có socket, chưa
        có leader, chưa có dòng nào — nhường ai. Đổi lại nợ phải sạch trước 9h.

        Ngày lấy từ `received_at` của dòng ĐẦU và CUỐI mỗi block: một block luôn được cắt
        trong vài giây nên hai đầu đã kẹp trọn khoảng ngày của nó; quét cả 5.000 dòng chỉ
        để ra cùng một tập ngày là phí.

        Bốn lối ra, không lối nào làm mất dòng:
        - hết file → trả tập ngày, phiên vào chế độ RAM bình thường;
        - transient (ClickHouse chưa dậy) → dừng, nợ giữ nguyên;
        - dòng độc → `_split_disk_item` cô lập; nó giữ file cha thì dừng luôn (review I3);
        - lỗi I/O đĩa → nuốt, đếm, dừng: spec §2.1 cấm lỗi đường đĩa thoát ra khỏi vòng
          quản/vòng ghi, mà ở đây thoát ra còn tệ hơn — nó bay thẳng qua `_run_run` thành
          traceback trần exit 1, đi vòng đúng hợp đồng exit 3 (bài học ACCESS_DENIED
          26/08). Nợ nằm lại đĩa, vòng ghi trong phiên thử tiếp.

        🔴 Bất biến ĐẦU RA (khối `finally`): còn file trên đĩa ⇒ writer PHẢI ở chế độ đĩa.
        Không thể để một lối ra nào quên: `_adopt_spill_if_possible` chỉ vào chế độ đĩa
        lúc NHẬN NUÔI, mà lúc này store đã sở hữu rồi nên nó về ngay — file sót sẽ nằm đó
        suốt phiên trong khi block mới đi thẳng vào kho (FIFO vỡ) và `clean()` False tới
        cuối phiên (phán quyết "KHÔNG ĐÁNG TIN" mỗi ngày).
        """
        if self.spill is None or not self.spill.owned:
            return set()               # không sở hữu thì KHÔNG đụng, kể cả đọc (spec §4)
        days: set[date] = set()
        try:
            while True:
                item = self.spill.next_batch(max_rows=BLOCK_CAP)
                if item is None:
                    if days:
                        log.warning("đã phát lại xong nợ đĩa của ngày %s",
                                    sorted(str(d) for d in days))
                    return days
                status = self._insert(item.table, item.block)
                if status == "done":
                    days |= _block_days(item.table, item.block)
                    self.spill.delete(item)   # XOÁ CHỈ SAU insert thành công (spec §3)
                    self.metrics.inc("replay_blocks", len(item.paths))
                    self.metrics.inc("replay_rows", item.n_rows)   # xem `_drain_disk_step`
                    continue
                if status == "transient":
                    code, rep = self._last_err
                    log.warning("phát lại nợ đĩa dừng ở lỗi transient: code=%s %s — "
                                "vào phiên ở CHẾ ĐỘ ĐĨA, nợ giữ nguyên", code, rep)
                    return days
                if not self._split_disk_item(item):
                    return days
        except OSError:
            self.metrics.inc("spill_io_error")
            log.exception("lỗi I/O khi phát lại nợ đĩa — dừng phát lại, vào phiên ở "
                          "CHẾ ĐỘ ĐĨA, nợ giữ nguyên")
            return days
        finally:
            # `finally` chạy SAU `except` nên một `OSError` từ `empty()` (iterdir) ở đây
            # vẫn thoát được ra ngoài hàm — bọc riêng. Không đọc nổi thư mục thì mặc định
            # là CÒN NỢ: vào chế độ đĩa thừa chỉ tốn một lượt xả, còn bỏ sót thì FIFO vỡ.
            try:
                leftover = not self.spill.empty()
            except OSError:
                self.metrics.inc("spill_io_error")
                log.exception("không đọc được thư mục spill lúc kết thúc phát lại — coi "
                              "như CÒN nợ")
                leftover = True
            if leftover:
                # `_enter_disk` tự bỏ qua nếu đã ở chế độ đĩa; `queue` lúc khởi động rỗng
                # nên đầu RAM đông cứng cũng rỗng — vô hại.
                self._enter_disk("debt_replay")

    def insert_percentiles(self) -> dict:
        xs = sorted(self.insert_s)
        if not xs:
            return {}
        pick = lambda q: xs[min(len(xs) - 1, int(q * len(xs)))]  # noqa: E731
        return {"p50": pick(0.50), "p95": pick(0.95), "p99": pick(0.99)}
