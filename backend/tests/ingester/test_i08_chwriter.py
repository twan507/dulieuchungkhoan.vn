"""Test cho ChWriter — buffer/flush/retry nguyên block/chia đôi block độc/block cap.
Spec CH §5: transient retry nguyên block backoff 1->16s tổng <=60s rồi bỏ block;
tất định -> chia đôi đệ quy, cô lập dòng hỏng; chạm BLOCK_CAP -> cắt block chờ nhịp sau.
"""
import sys
import threading
import time
from decimal import Decimal

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
