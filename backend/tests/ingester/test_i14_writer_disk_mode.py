"""ChWriter v2 — spec spill §2. Task 5: vòng tách + hợp đồng insert; seam 11, 16."""
import threading
import time
from collections import deque

from ingester.chwriter import COLUMNS, ChWriter, WRITE_CALL_BUDGET_S
from ingester.normalize import Metrics, Normalized


def _n(seq: int, table: str = "trade") -> Normalized:
    row = {c: None for c in COLUMNS[table]}
    row["symbol"], row["seq"] = "ACV", seq
    return Normalized(table=table, row=row, delta={}, symbol="ACV")


class _Clock:
    def __init__(self): self.now = 1000.0
    def __call__(self): return self.now
    def advance(self, d): self.now += d


def test_manage_runs_while_insert_hangs():
    """Bất biến spec §2.1: vòng quản KHÔNG bị insert treo chặn — chính B1 của review."""
    started, release = threading.Event(), threading.Event()

    class _Hang:
        def insert(self, *a, **k):
            started.set()
            release.wait(5)
            raise ConnectionError("treo")

    w = ChWriter(_Hang())
    w.add(_n(1))
    w.manage_once()                                        # cắt buffer → queue
    t = threading.Thread(target=w.write_once)
    t.start()
    started.wait(5)
    w.add(_n(2))
    w.manage_once()                                        # PHẢI chạy được ngay lúc này
    assert w.metrics.counters["pending_depth_rows"] == 2   # gauge cập nhật giữa lúc treo
    release.set(); t.join()


def test_write_once_call_budget_bounds_blocks_per_call():
    clock = _Clock()

    class _Slow:
        def __init__(self): self.calls = 0
        def insert(self, *a, **k):
            self.calls += 1
            clock.advance(3.0)                             # mỗi insert 3s "đồng hồ"

    c = _Slow()
    w = ChWriter(c, clock=clock)
    for i in range(10):
        w.add(_n(i)); w.manage_once()                      # 10 block một dòng
    w.write_once(budget_s=5.0)
    assert c.calls == 2                                    # 3s + 3s = 6s > 5s → dừng sau block 2
    assert w.queue_rows == 8


def test_transient_leaves_block_for_next_tick_no_sleep():
    class _Fail:
        def __init__(self): self.calls = 0
        def insert(self, *a, **k):
            self.calls += 1
            raise ConnectionError("chập chờn")

    c = _Fail()
    w = ChWriter(c)
    w.add(_n(1)); w.manage_once()
    w.write_once()
    assert c.calls == 1 and w.queue_rows == 1              # còn nguyên, không ngủ, không lặp
    w.write_once()
    assert c.calls == 2                                    # nhịp sau thử lại


def test_poison_bisect_keeps_front_position_and_isolates():
    class _Bad:
        def __init__(self): self.written = []
        def insert(self, table, data, column_names):
            seq_i = COLUMNS["trade"].index("seq")
            if any(r[seq_i] == 2 for r in data):
                raise Exception("Code: 117. DB::Exception: x (INCORRECT_DATA)")
            self.written.extend(data)

    c = _Bad()
    w = ChWriter(c)
    for i in range(4):
        w.add(_n(i))
    w.manage_once()
    w.flush_once()
    seq_i = COLUMNS["trade"].index("seq")
    assert sorted(r[seq_i] for r in c.written) == [0, 1, 3]
    assert w.metrics.counters["poison_row.trade"] == 1
