"""ChWriter v2 — spec spill §2. Task 5: vòng tách + hợp đồng insert; seam 11, 16."""
import sys
import threading
import time

from ingester.chwriter import COLUMNS, ChWriter
from ingester.normalize import Normalized


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


def test_queue_rows_stays_consistent_under_concurrent_add_and_poison_drain():
    """Review Opus, Finding 1 — trước fix, `queue_rows -= 1` của nhánh poison len==1 nằm
    NGOÀI `_lock` trong khi `add()`/`manage_once()` cộng `queue_rows` DƯỚI `_lock` từ luồng
    khác → lost update kinh điển (đọc-sửa-ghi không loại trừ nhau). Task 6 dùng
    `queue_rows` làm input điều khiển trần RAM nên số sai là nguy hiểm, không chỉ là gauge
    lệch.

    KHÔNG đỏ chắc chắn trên bản lỗi: đã thử hạ switchinterval xuống 0.00001 (kỹ thuật của
    test_i08's test_concurrent_add_and_flush_no_lost_no_duplicate_rows) với nhiều cấu hình
    (1 cặp luồng 0,3 s; 2 cặp luồng x 3 lượt x 0,5 s) — cả hai đều XANH NHẦM trên bản lỗi
    6/6 lần chạy vì khe hở chỉ rộng vài bytecode (`LOAD_ATTR; BINARY_SUBTRACT; STORE_ATTR`
    của `queue_rows -= 1`), quá hẹp để GIL luôn trúng so với khe hở "copy rồi clear buffer"
    (hai câu lệnh riêng) mà test kia nhắm tới. Giữ lại làm bài kiểm BẤT BIẾN (không phải
    đỏ-trước) theo đúng phương án dự phòng review đã cho phép khi không đạt đỏ tất định
    trong nỗ lực hợp lý — báo cáo tại `task-5-report.md`."""
    old_interval = sys.getswitchinterval()
    sys.setswitchinterval(0.00001)
    try:
        _run_concurrent_add_and_poison_drain_check()
    finally:
        sys.setswitchinterval(old_interval)


def _run_concurrent_add_and_poison_drain_check():
    class _AlwaysPoison:
        def insert(self, table, data, column_names):
            raise Exception("Code: 117. DB::Exception: x (INCORRECT_DATA)")

    w = ChWriter(_AlwaysPoison())
    stop = threading.Event()

    def adder():
        i = 0
        while not stop.is_set():
            w.add(_n(i))
            i += 1
            w.manage_once()             # cắt buffer -> queue, queue_rows += 1 dưới _lock

    def drainer():
        while not stop.is_set():
            w.write_once(budget_s=0.02)  # mỗi block 1 dòng luôn poison -> nhánh len==1

    t_add = threading.Thread(target=adder)
    t_drain = threading.Thread(target=drainer)
    t_add.start()
    t_drain.start()
    time.sleep(0.3)
    stop.set()
    t_add.join()
    t_drain.join()

    # Bất biến: queue_rows phải luôn khớp tổng số dòng thật còn nằm trong queue — không
    # phải một con số cụ thể (không tautological — tính lại độc lập từ nội dung queue).
    assert w.queue_rows == sum(len(p.block) for p in w.queue)
