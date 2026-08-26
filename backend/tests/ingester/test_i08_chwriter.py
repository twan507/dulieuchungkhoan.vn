"""Test cho ChWriter — buffer/flush/retry nguyên block/chia đôi block độc/block cap.
Spec CH §5: transient retry nguyên block backoff 1->16s tổng <=60s rồi bỏ block;
tất định -> chia đôi đệ quy, cô lập dòng hỏng; chạm BLOCK_CAP -> cắt block chờ nhịp sau.
"""
import sys
import threading
import time
from decimal import Decimal

from clickhouse_connect.driver.exceptions import DatabaseError as ChDatabaseError

from ingester.chwriter import COLUMNS, ChWriter
from ingester.normalize import Metrics, Normalized, normalize

RECV = 1786342136000
T = {"TD": "10/08/2026", "FT": "13:08:56", "SB": "ACV", "FV": "100", "LC": "S",
     "FMP": "42100.0", "FCV": "1000.0", "SM": "74027", "AVO": "590000", "AVA": "24983210000.0"}


def _n(**kw):
    return normalize("t", {**T, **kw}, RECV, Metrics())


def test_flush_writes_rows(migrated):
    w = ChWriter(migrated)
    w.add(_n())
    w.add(_n(SM="74028", FMP="42200.0"))
    w.flush_once()
    rows = migrated.query(
        "SELECT price, volume FROM rt.trade WHERE symbol='ACV' AND seq IN (74027,74028)"
        " ORDER BY seq").result_rows
    assert rows == [(Decimal("42100.00"), 100), (Decimal("42200.00"), 100)]
    migrated.command("ALTER TABLE rt.trade DELETE WHERE symbol='ACV'")


def test_poison_row_isolated(migrated):
    w = ChWriter(migrated)
    w.add(_n(SM="80001"))
    w.add(_n(SM="80002", FMP="99999999999999999.0"))   # tràn Decimal64(2) → lỗi tất định
    w.add(_n(SM="80003"))
    w.flush_once()
    n = migrated.query(
        "SELECT count() FROM rt.trade WHERE symbol='ACV' AND seq BETWEEN 80001 AND 80003"
    ).result_rows[0][0]
    assert n == 2
    assert w.metrics.counters.get("poison_row.trade") == 1
    migrated.command("ALTER TABLE rt.trade DELETE WHERE symbol='ACV'")


class FlakyClient:
    def __init__(self, real, fail_times):
        self.real, self.left = real, fail_times
        self.blocks = []

    def insert(self, table, data, column_names):
        if self.left > 0:
            self.left -= 1
            raise ConnectionError("mạng chập chờn")
        self.blocks.append(list(data))
        return self.real.insert(table, data, column_names=column_names)


def test_transient_retries_same_block(migrated):
    flaky = FlakyClient(migrated, fail_times=2)
    w = ChWriter(flaky, sleep_fn=lambda s: None)
    w.add(_n(SM="90001"))
    w.flush_once()
    assert len(flaky.blocks) == 1 and len(flaky.blocks[0]) == 1   # block nguyên vẹn, không gộp thêm
    migrated.command("ALTER TABLE rt.trade DELETE WHERE symbol='ACV'")


def test_block_cap_cuts_without_flush():
    class NullClient:
        def insert(self, *a, **k):
            raise AssertionError("không được insert khi chưa flush")
    w = ChWriter(NullClient())
    import ingester.chwriter as m
    for i in range(m.BLOCK_CAP + 3):
        w.add(_n(SM=str(100000 + i)))
    assert w.metrics.counters.get("block_cap.trade") == 1


def _trade_normalized(seq: int) -> Normalized:
    # Bỏ qua normalize() để test nhanh — dựng thẳng Normalized như add() cần.
    row = {c: None for c in COLUMNS["trade"]}
    row["symbol"] = "ACV"
    row["seq"] = seq
    return Normalized(table="trade", row=row, delta={}, symbol="ACV")


def test_concurrent_add_and_flush_no_lost_no_duplicate_rows():
    """CRITICAL 1 review wave 2 — add() (thread khác) và flush_once() (to_thread)
    cắt buffer không atomic từng làm mất dòng. 2 thread add tổng 20.000 dòng trong
    khi thread chính flush_once() liên tục; cuối cùng tổng dòng đã insert + còn lại
    trong buffers/pending phải đúng 20.000, không đôi. Lặp 3 lần cho chắc.

    Hạ switchinterval để GIL nhường quyền dày hơn — không làm vậy thì race hiếm khi
    trúng đúng khe hở giữa "copy buffer" và "clear buffer" (đã xác nhận thủ công:
    không hạ switchinterval, bản LỖI (không lock) thỉnh thoảng vẫn xanh nhầm — không
    phải test đỏ đáng tin; hạ switchinterval thì bản lỗi ĐỎ chắc chắn cả 3 lần).
    """
    old_interval = sys.getswitchinterval()
    sys.setswitchinterval(0.00001)
    try:
        _run_concurrent_add_flush_check()
    finally:
        sys.setswitchinterval(old_interval)


def _run_concurrent_add_flush_check():
    for _attempt in range(3):
        class _StubClient:
            def __init__(self):
                self._lock = threading.Lock()
                self.written: list[list] = []

            def insert(self, table, data, column_names):
                with self._lock:
                    self.written.append(list(data))

        client = _StubClient()
        w = ChWriter(client, sleep_fn=lambda s: None)
        stop_flush = threading.Event()

        def flusher():
            while not stop_flush.is_set():
                w.flush_once()

        def add_range(start: int, count: int):
            for i in range(start, start + count):
                w.add(_trade_normalized(i))

        t_flush = threading.Thread(target=flusher)
        t1 = threading.Thread(target=add_range, args=(0, 10_000))
        t2 = threading.Thread(target=add_range, args=(10_000, 10_000))
        t_flush.start()
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        stop_flush.set()
        t_flush.join()
        w.flush_once()             # gom nốt phần còn lại trong buffer sau khi thread add xong

        seq_col = COLUMNS["trade"].index("seq")
        inserted_seqs = [row[seq_col] for block in client.written for row in block]
        remaining_seqs = [row[seq_col] for buf in w.buffers.values() for row in buf]
        remaining_seqs += [row[seq_col] for q in w.pending.values() for block in q for row in block]

        all_seqs = inserted_seqs + remaining_seqs
        assert len(all_seqs) == 20_000                 # không mất dòng
        assert len(set(all_seqs)) == 20_000             # không đôi dòng


# --- review cuối: phân loại lỗi ClickHouse ---------------------------------

class _FailNTimesClient:
    """Client CH giả: N lời gọi insert đầu ném `exc`, sau đó ghi nhận block."""

    def __init__(self, fail_times: int, exc: Exception):
        self.left, self.exc = fail_times, exc
        self.blocks: list[list] = []

    def insert(self, table, data, column_names):
        if self.left > 0:
            self.left -= 1
            raise self.exc
        self.blocks.append(list(data))


def test_backpressure_error_retries_whole_block():
    """IMPORTANT 1 review cuối — lỗi BACKPRESSURE của ClickHouse (TOO_MANY_PARTS,
    MEMORY_LIMIT_EXCEEDED) không chứa chữ "timeout|connection|temporarily" nên luật cũ
    xếp nhầm là TẤT ĐỊNH → chia đôi đệ quy thành 5.000 INSERT một dòng (làm vấn đề parts
    tệ hơn) rồi vứt sạch dữ liệu. Phải retry NGUYÊN block theo ngân sách cũ.
    """
    exc = Exception("Code: 252. DB::Exception: Too many parts (300). "
                    "Merges are processing significantly slower than inserts")
    client = _FailNTimesClient(fail_times=2, exc=exc)
    w = ChWriter(client, sleep_fn=lambda s: None)
    for i in range(4):
        w.add(_trade_normalized(70_000 + i))
    w.flush_once()
    assert [len(b) for b in client.blocks] == [4]          # một block nguyên, không chia đôi
    assert w.metrics.counters.get("rows.trade") == 4       # không mất dòng nào
    assert w.metrics.counters.get("poison_row.trade") is None
    assert w.metrics.counters.get("dropped_block.trade") is None


def test_memory_limit_error_retries_whole_block():
    exc = Exception("Code: 241. DB::Exception: Memory limit (total) exceeded: "
                    "would use 56.00 GiB (MEMORY_LIMIT_EXCEEDED)")
    client = _FailNTimesClient(fail_times=1, exc=exc)
    w = ChWriter(client, sleep_fn=lambda s: None)
    for i in range(4):
        w.add(_trade_normalized(71_000 + i))
    w.flush_once()
    assert [len(b) for b in client.blocks] == [4]
    assert w.metrics.counters.get("rows.trade") == 4


def test_data_error_marker_splits_to_isolate_bad_row():
    """Mã lỗi DỮ LIỆU đã biết → vẫn chia đôi đệ quy để cô lập đúng dòng hỏng (§5.8)."""
    class _OneBadRowClient:
        def __init__(self, bad_seq: int):
            self.bad_seq, self.blocks = bad_seq, []

        def insert(self, table, data, column_names):
            seq_col = COLUMNS["trade"].index("seq")
            if any(row[seq_col] == self.bad_seq for row in data):
                raise Exception("Code: 69. DB::Exception: Decimal value is too big: "
                                "17 digits were read (ARGUMENT_OUT_OF_BOUND)")
            self.blocks.append(list(data))

    client = _OneBadRowClient(bad_seq=72_002)
    w = ChWriter(client, sleep_fn=lambda s: None)
    for i in range(4):
        w.add(_trade_normalized(72_000 + i))
    w.flush_once()
    seq_col = COLUMNS["trade"].index("seq")
    written = sorted(row[seq_col] for b in client.blocks for row in b)
    assert written == [72_000, 72_001, 72_003]             # chỉ dòng hỏng bị bỏ
    assert w.metrics.counters.get("poison_row.trade") == 1


def test_two_flush_threads_do_not_lose_a_block():
    """IMPORTANT 4 review cuối — lúc tắt, task flush đang chạy bị cancel() nhưng THREAD
    `flush_once` vẫn chạy tiếp, rồi code khởi flush cuối cùng ⇒ hai thread cùng xả
    `pending`. Vòng `self._write_block(table, q[0]); q.popleft()` nằm NGOÀI lock nên cả
    hai popleft: một block được ghi hai lần, block kế bị popleft mà chưa từng ghi — mất
    nguyên một block (tới 5.000 dòng).

    Ở đây nạp sẵn 20.003 dòng (4 block đầy do BLOCK_CAP + phần dư), rồi cho HAI thread
    cùng gọi flush_once() liên tục. `insert` giả ngủ 1 ms để mở rộng đúng khe hở giữa
    "ghi xong" và "popleft" — không có mutex thì mất block gần như chắc chắn.
    """
    for _attempt in range(3):
        class _SlowRecordingClient:
            def __init__(self):
                self._lock = threading.Lock()
                self.written: list[list] = []

            def insert(self, table, data, column_names):
                time.sleep(0.001)
                with self._lock:
                    self.written.append(list(data))

        client = _SlowRecordingClient()
        w = ChWriter(client, sleep_fn=lambda s: None)
        for i in range(20_003):
            w.add(_trade_normalized(i))

        stop = threading.Event()
        errors: list[BaseException] = []

        def flusher():
            while not stop.is_set():
                try:
                    w.flush_once()
                except BaseException as e:      # noqa: BLE001 — thu để assert, không nuốt
                    errors.append(e)
                    return

        threads = [threading.Thread(target=flusher) for _ in range(2)]
        for t in threads:
            t.start()
        while any(w.pending[t] for t in w.pending) or any(w.buffers.values()):
            time.sleep(0.005)
        stop.set()
        for t in threads:
            t.join()

        seq_col = COLUMNS["trade"].index("seq")
        all_seqs = [row[seq_col] for block in client.written for row in block]
        all_seqs += [row[seq_col] for buf in w.buffers.values() for row in buf]
        all_seqs += [row[seq_col] for q in w.pending.values() for blk in q for row in blk]
        assert errors == []                            # hai thread giẫm nhau -> popleft rỗng
        assert set(all_seqs) == set(range(20_003))     # không dòng nào biến mất
        assert len(all_seqs) == 20_003                 # cũng không block nào bị ghi hai lần


# --- M-new-1: phân loại lỗi phải bắt theo MÃ SỐ, không theo chuỗi trong str(e) --------
#
# Đo trên ClickHouse 26.3.22.7 thật (2026-08-26) + đọc `build_http_error` của
# clickhouse_connect: `code` lấy từ HEADER HTTP nên LUÔN có, còn `name` và phần chi tiết
# trong `str(e)` chỉ có khi `show_clickhouse_errors` bật. Bắt theo chuỗi ⇒ lỗi DỮ LIỆU bị
# đọc nhầm thành transient ⇒ retry 60 s vô nghĩa rồi VỨT CẢ BLOCK (tới 5.000 dòng) thay
# vì chia đôi để cô lập đúng một dòng hỏng.
#
# Mã số lấy từ danh mục lỗi của ClickHouse, không suy từ code của mình.

CH_ERR = {                       # mã: (tên ký hiệu, có phải lỗi dữ liệu không)
    407: ("DECIMAL_OVERFLOW", True),
    117: ("INCORRECT_DATA", True),
    252: ("TOO_MANY_PARTS", False),      # backpressure — PHẢI giữ transient
}


def _server_error(code: int, *, detail: bool = True):
    """Dựng đúng hình dạng exception mà clickhouse_connect sinh ra."""
    name, _ = CH_ERR[code]
    if detail:
        msg = (f"Received ClickHouse exception, code: {code}, server response: "
               f"Code: {code}. DB::Exception: ... ({name}) (for url http://127.0.0.1:8123)")
        return ChDatabaseError(msg, code=code, name=name)
    # show_clickhouse_errors=False: body bị nuốt, CHỈ còn code từ header
    return ChDatabaseError("The ClickHouse server returned an error", code=code, name=None)


class _RejectingClient:
    """Ném `exc` với mọi block còn chứa dòng độc; block sạch thì ghi nhận."""

    def __init__(self, exc, poison_seq: int):
        self.exc, self.poison_seq = exc, poison_seq
        self.written: list[list] = []
        self.attempts = 0

    def insert(self, table, data, column_names):
        self.attempts += 1
        seq_i = COLUMNS[table.split(".")[-1]].index("seq")   # caller truyền "rt.<bảng>"
        if any(row[seq_i] == self.poison_seq for row in data):
            raise self.exc
        self.written.extend(data)


def _run_with(exc):
    client = _RejectingClient(exc, poison_seq=70002)
    w = ChWriter(client, sleep_fn=lambda s: None)
    for seq in (70001, 70002, 70003):
        w.add(_n(SM=str(seq)))
    w.flush_once()
    return w, client


def test_decimal_overflow_isolates_poison_row_instead_of_dropping_block():
    w, client = _run_with(_server_error(407))
    assert w.metrics.counters.get("poison_row.trade") == 1
    assert w.metrics.counters.get("dropped_block.trade") is None
    assert len(client.written) == 2                  # hai dòng lành vẫn vào kho


def test_incorrect_data_isolates_poison_row():
    w, client = _run_with(_server_error(117))
    assert w.metrics.counters.get("poison_row.trade") == 1
    assert len(client.written) == 2


def test_data_error_still_classified_when_server_detail_suppressed():
    """show_clickhouse_errors=False nuốt cả `name` lẫn chuỗi — chỉ `code` sống sót."""
    exc = _server_error(407, detail=False)
    assert getattr(exc, "name", None) is None        # tiền đề: `name` KHÔNG dùng được
    assert "DECIMAL_OVERFLOW" not in str(exc)        # tiền đề: chuỗi KHÔNG dùng được
    w, client = _run_with(exc)
    assert w.metrics.counters.get("poison_row.trade") == 1
    assert len(client.written) == 2


def test_backpressure_code_stays_transient():
    """Ranh giới ngược: TOO_MANY_PARTS là quá tải, KHÔNG được chia đôi block."""
    w, client = _run_with(_server_error(252))
    assert w.metrics.counters.get("poison_row.trade") is None
    assert w.metrics.counters.get("dropped_block.trade") == 3   # giữ nguyên block rồi bỏ
    assert client.written == []
