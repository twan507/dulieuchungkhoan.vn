"""Test cho ChWriter — buffer/cắt block/retry nguyên block/cô lập dòng độc/block cap.

Hợp đồng hiện hành (spec CH §5 + spec spill §2.3, thay hẳn hợp đồng "backoff 1->16s rồi
bỏ block" của bản v1): lỗi transient KHÔNG ngủ và KHÔNG lặp trong một lần gọi — block ở
lại đầu hàng đợi, nhịp sau thử tiếp, hạn chót `RETRY_BUDGET_S` đếm bằng THỜI GIAN THỰC từ
lần thử đầu. Cạn hạn chót là CỬA 2 vào chế độ đĩa: block xuống đĩa nguyên văn dạng '-r',
chỉ khi KHÔNG có lưới đĩa mới bỏ, và bỏ thì có sổ `no_spill_dropped.<bảng>`. Lỗi tất định
-> chia đôi (vòng lặp, không đệ quy) để cô lập đúng dòng hỏng; chạm BLOCK_CAP -> cắt block
chờ nhịp sau.
"""
import sys
import threading
import time
from decimal import Decimal

from clickhouse_connect.driver.exceptions import DatabaseError as ChDatabaseError

from ingester.chwriter import COLUMNS, ChWriter, RETRY_BUDGET_S
from ingester.normalize import Metrics, Normalized, normalize
from ingester.spill import SpillStore

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
    # v2: write_once không còn tự lặp trong một lần gọi (retry theo nhịp, không sleep) —
    # mỗi lần gọi flush_once() là MỘT nhịp. fail_times=2 nên cần 3 nhịp mới thành công.
    flaky = FlakyClient(migrated, fail_times=2)
    w = ChWriter(flaky)
    w.add(_n(SM="90001"))
    w.flush_once()
    w.flush_once()
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
        w = ChWriter(client)
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
        remaining_seqs += [row[seq_col] for p in w.queue for row in p.block]

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
    # v2: write_once không còn tự lặp trong một lần gọi (retry theo nhịp, không sleep) —
    # mỗi lần gọi flush_once() là MỘT nhịp. fail_times=2 nên cần 3 nhịp mới thành công.
    exc = Exception("Code: 252. DB::Exception: Too many parts (300). "
                    "Merges are processing significantly slower than inserts")
    client = _FailNTimesClient(fail_times=2, exc=exc)
    w = ChWriter(client)
    for i in range(4):
        w.add(_trade_normalized(70_000 + i))
    w.flush_once()
    w.flush_once()
    w.flush_once()
    assert [len(b) for b in client.blocks] == [4]          # một block nguyên, không chia đôi
    assert w.metrics.counters.get("rows.trade") == 4       # không mất dòng nào
    assert w.metrics.counters.get("poison_row.trade") is None
    assert w.metrics.counters.get("dropped_block.trade") is None


def test_memory_limit_error_retries_whole_block():
    # v2: fail_times=1 nên cần 2 nhịp (2 lần gọi flush_once()) để thành công.
    exc = Exception("Code: 241. DB::Exception: Memory limit (total) exceeded: "
                    "would use 56.00 GiB (MEMORY_LIMIT_EXCEEDED)")
    client = _FailNTimesClient(fail_times=1, exc=exc)
    w = ChWriter(client)
    for i in range(4):
        w.add(_trade_normalized(71_000 + i))
    w.flush_once()
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
    w = ChWriter(client)
    for i in range(4):
        w.add(_trade_normalized(72_000 + i))
    w.flush_once()
    seq_col = COLUMNS["trade"].index("seq")
    written = sorted(row[seq_col] for b in client.blocks for row in b)
    assert written == [72_000, 72_001, 72_003]             # chỉ dòng hỏng bị bỏ
    assert w.metrics.counters.get("poison_row.trade") == 1


def test_two_flush_threads_do_not_lose_a_block():
    """IMPORTANT 4 review cuối — lúc tắt, task ghi đang chạy bị cancel() nhưng THREAD
    `write_once` vẫn chạy tiếp, rồi code khởi ghi cuối cùng ⇒ hai thread cùng xả hàng đợi
    toàn cục. `_write_lock` (v2 — kế thừa `_flush_lock` bản v1) chặn đúng việc này: không
    lấy được thì về ngay, không cùng peek/pop một block.

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
        w = ChWriter(client)
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
        while w.queue or any(w.buffers.values()):
            time.sleep(0.005)
        stop.set()
        for t in threads:
            t.join()

        seq_col = COLUMNS["trade"].index("seq")
        all_seqs = [row[seq_col] for block in client.written for row in block]
        all_seqs += [row[seq_col] for buf in w.buffers.values() for row in buf]
        all_seqs += [row[seq_col] for p in w.queue for row in p.block]
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

class _FakeClock:
    """Đồng hồ giả: `sleep(d)` nhảy d giây; `advance(d)` mô phỏng thời gian trôi trong I/O."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, d: float) -> None:
        self.now += d

    def sleep(self, d: float) -> None:
        self.now += d



CH_ERR = {                       # mã ClickHouse -> tên ký hiệu
    407: "DECIMAL_OVERFLOW",
    117: "INCORRECT_DATA",
    252: "TOO_MANY_PARTS",           # backpressure — PHẢI giữ transient
}


def _server_error(code: int, *, detail: bool = True):
    """Dựng đúng hình dạng exception mà clickhouse_connect sinh ra."""
    name = CH_ERR[code]
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
    # Dùng cho lỗi TẤT ĐỊNH (poison) — chia đôi cô lập xong ngay trong một nhịp gọi, không
    # cần đồng hồ trôi qua nhiều nhịp như nhánh transient bên dưới.
    client = _RejectingClient(exc, poison_seq=70002)
    clock = _FakeClock()
    w = ChWriter(client, clock=clock)
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


def test_backpressure_code_stays_transient(tmp_path):
    """Ranh giới ngược: TOO_MANY_PARTS là quá tải, KHÔNG được chia đôi block.

    v2: transient không tự lặp trong một lần gọi (retry theo nhịp, không sleep) — nhịp 1
    chỉ đặt `first_try`; tự advance đồng hồ giả qua khỏi RETRY_BUDGET_S rồi gọi nhịp 2 mới
    chạm hạn chót.

    TASK 6 (spec spill §2.3, cửa vào 2): cạn hạn chót KHÔNG còn bỏ block — block NGUYÊN
    VẸN xuống đĩa thành file '-r' và writer vào chế độ đĩa. Điều cần giữ ở test này vẫn là
    ranh giới cũ: block không bị CHIA ĐÔI (không `poison_row`), chỉ đổi đích đến.
    """
    client = _RejectingClient(_server_error(252), poison_seq=70002)
    clock = _FakeClock()
    store = SpillStore(tmp_path, cap_bytes=10**9)
    assert store.try_acquire()
    store.scan()
    w = ChWriter(client, spill=store, clock=clock)
    for seq in (70001, 70002, 70003):
        w.add(_n(SM=str(seq)))
    w.flush_once()                                  # nhịp 1: transient, chưa hết hạn
    assert store.empty() and not w.disk_mode
    clock.advance(RETRY_BUDGET_S + 1)                # mô phỏng nhịp sau, đã hết hạn
    w.flush_once()                                   # nhịp 2: hết hạn -> xuống đĩa
    assert w.metrics.counters.get("poison_row.trade") is None
    assert w.metrics.counters.get("dropped_block.trade") is None
    assert w.disk_mode
    item = store.next_batch(max_rows=100)
    assert item.kind == "r" and item.n_rows == 3     # nguyên block, không chia, không bỏ
    assert client.written == []


# --- Ngân sách retry phải là THỜI GIAN THỰC, không phải tổng thời gian ngủ -----------
#
# `RETRY_BUDGET_S` phải là hạn CỬA 2 tính bằng THỜI GIAN THỰC (spec spill §2.3), không
# phải tổng thời gian ngủ. Nếu chỉ cộng `delay` của mỗi lần ngủ, thời gian nằm TRONG
# `client.insert` không vào sổ — mà driver mặc định `send_receive_timeout=300`, nên một
# server treo làm mỗi lần thử ăn tới 300 s thời gian thực trong khi bộ đếm vẫn gần 0.
# Hệ quả: block treo hàng chục phút trước khi cửa 2 mở (market-data-store §3.7 luật 3).


class _HangingClient:
    """Mỗi lần insert ăn hết read-timeout của driver rồi hỏng theo kiểu transient."""

    def __init__(self, clock, cost_s: float):
        self.clock, self.cost_s, self.attempts = clock, cost_s, 0

    def insert(self, table, data, column_names):
        self.attempts += 1
        self.clock.advance(self.cost_s)
        raise ConnectionError("server treo, đọc quá hạn")


def test_retry_budget_counts_wall_clock_not_sleep_time():
    # TASK 6 (spec spill §2.3): cạn ngân sách retry → block xuống đĩa, không bỏ. Writer này
    # KHÔNG có spill (spill=None — cấu hình suy giảm "chạy không có lưới đĩa") nên cửa 2
    # không mở: bỏ block cạn hạn chót có sổ `no_spill_dropped.<bảng>` theo DÒNG và Ở LẠI
    # chế độ RAM (ruling C-1). Điều test này canh vẫn không đổi: ngân sách đếm bằng THỜI
    # GIAN THỰC, một lần thử treo 300 s tự nó cạn ngân sách 60 s ⇒ không có lần thử thứ hai.
    clock = _FakeClock()
    # 300 s = mặc định `send_receive_timeout` của clickhouse_connect.
    client = _HangingClient(clock, cost_s=300.0)
    w = ChWriter(client, clock=clock)
    w.add(_n(SM="60001"))
    w.flush_once()

    assert client.attempts == 1
    assert w.metrics.counters.get("dropped_block.trade") is None   # tên cũ đã chết
    assert w.metrics.counters.get("no_spill_dropped.trade") == 1
    assert not w.disk_mode                        # không có đĩa thì không vào chế độ đĩa
    assert clock.now - 1000.0 == 300.0            # không kéo dài thêm bằng backoff


def test_bisect_does_not_consume_time_budget():
    """v2: chia đôi block độc không còn ĐỆ QUY (`_write_block` cũ) mà là vòng lặp trong
    `write_once` — mỗi lần chia chỉ gọi `client.insert` thêm một lần, không sleep, nên
    không tự cộng dồn thời gian. Bài học cũ (778 s cho một lần xả vì mỗi tầng đệ quy được
    cấp lại trọn ngân sách) không còn cách tái hiện được ở kiến trúc này; giữ lại phép
    kiểm dưới dạng bất biến biên trên — bisect không được ngốn quá 2 lần ngân sách.
    """
    clock = _FakeClock()

    class _PoisonThenOutage:
        """Dòng độc ở giữa; sau vài lần insert thì server chết hẳn kiểu transient."""

        def __init__(self, die_after: int):
            self.die_after, self.attempts = die_after, 0

        def insert(self, table, data, column_names):
            self.attempts += 1
            if self.attempts > self.die_after:
                clock.advance(20.0)                       # chạm read-timeout
                raise ConnectionError("server chết giữa lúc chia đôi")
            seq_i = COLUMNS[table.split(".")[-1]].index("seq")
            if any(row[seq_i] == 80500 for row in data):
                raise ChDatabaseError("hỏng", code=407, name="DECIMAL_OVERFLOW")

    client = _PoisonThenOutage(die_after=3)
    w = ChWriter(client, clock=clock)
    for seq in range(80001, 80001 + 1000):
        w.add(_n(SM=str(seq)))
    w.add(_n(SM="80500"))
    t0 = clock.now
    w.flush_once()

    elapsed = clock.now - t0
    import ingester.chwriter as m
    assert elapsed <= m.RETRY_BUDGET_S * 2, f"một lần xả ngốn {elapsed:.0f}s, ngân sách {m.RETRY_BUDGET_S}s"


def test_fallback_markers_cover_the_two_codes_when_exception_has_no_code():
    """Nhánh lùi dùng khi exception KHÔNG mang mã (lỗi transport, client lạ)."""
    import ingester.chwriter as m
    for name in ("INCORRECT_DATA", "DECIMAL_OVERFLOW"):
        e = Exception(f"Code: 0. DB::Exception: ... ({name})")
        assert not hasattr(e, "code")
        assert m._is_deterministic(e) is True, name
    # Ranh giới ngược: backpressure không mang mã vẫn phải là transient.
    assert m._is_deterministic(Exception("DB::Exception: ... (TOO_MANY_PARTS)")) is False


def test_drop_log_carries_error_code_when_message_is_scrubbed(caplog):
    """show_clickhouse_errors=False ⇒ `str(e)` mất hết dấu vết, mã là thứ duy nhất còn lại.

    v2: nhịp 1 chỉ đặt `first_try` (chưa hết hạn nên chưa log ERROR); tự advance đồng hồ
    giả qua khỏi RETRY_BUDGET_S rồi gọi nhịp 2 mới chạm hạn chót và log.
    """
    clock = _FakeClock()
    scrubbed = ChDatabaseError("The ClickHouse server returned an error", code=252, name=None)

    class _AlwaysFails:
        def insert(self, table, data, column_names):
            clock.advance(1.0)
            raise scrubbed

    w = ChWriter(_AlwaysFails(), clock=clock)
    w.add(_n(SM="90501"))
    w.flush_once()                       # nhịp 1: transient, đặt first_try
    clock.advance(RETRY_BUDGET_S)        # mô phỏng nhịp sau, đã hết hạn
    with caplog.at_level("ERROR"):
        w.flush_once()                   # nhịp 2: hết hạn -> log ERROR kèm mã lỗi
    assert "code=252" in caplog.text


# --- Lỗi serialize PHÍA CLIENT (nợ Task 5, điều tra 2026-08-28) ------------------
# Tầng `driver.transform` của clickhouse_connect gói giá trị vào cột native TRƯỚC khi
# byte nào rời tiến trình, và ném AttributeError/TypeError/ValueError TRẦN — không
# `.code`, không phải ClickHouseError. Đọc thành "transient" là retry vĩnh viễn.
# Blast radius tăng hẳn sau lát spill: dòng hỏng vĩnh viễn đi transient 60 s -> cửa 2
# -> file '-r' -> phát lại lại lỗi -> KẸT ĐẦU HÀNG ĐỢI ĐĨA cả phiên (trước lát spill
# chỉ mất 1 block sau 60 s).

def test_client_side_serialize_errors_are_deterministic():
    from ingester.chwriter import _is_deterministic
    for exc in (AttributeError("'NoneType' object has no attribute 'timestamp'"),
                TypeError("an integer is required"),
                ValueError("Decimal('NaN') is not valid")):
        assert _is_deterministic(exc) is True, f"{type(exc).__name__} phải là tất định"


def test_transport_errors_stay_transient():
    """Ranh giới ngược — lỗi mạng KHÔNG được rơi vào nhánh mới."""
    from ingester.chwriter import _is_deterministic
    for exc in (ConnectionError("connection reset by peer"),
                OSError("socket hang up"),
                TimeoutError("read timed out")):
        assert _is_deterministic(exc) is False, f"{type(exc).__name__} phải là transient"


def test_client_side_serialize_error_isolates_poison_row():
    w, client = _run_with(AttributeError("'NoneType' object has no attribute 'timestamp'"))
    assert w.metrics.counters.get("poison_row.trade") == 1
    assert w.metrics.counters.get("dropped_block.trade") is None
    assert len(client.written) == 2                  # hai dòng lành vẫn vào kho
