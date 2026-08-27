"""ChWriter v2 — spec spill §2. Task 5: vòng tách + hợp đồng insert; seam 11, 16.
Task 6: hai cửa vào chế độ đĩa + đường bỏ-mới có sổ sách; seam 3, 4, 12."""
import logging
import sys
import threading
import time

from ingester.chwriter import COLUMNS, N_CAP_ROWS, ChWriter, _Pending
from ingester.normalize import Normalized
from ingester.spill import SpillStore


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


# --- Task 6: hai cửa vào chế độ đĩa (spec §2.3) ---------------------------------------


def _writer_with_spill(tmp_path, client, clock=None) -> ChWriter:
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire()
    s.scan()
    return ChWriter(client, spill=s, clock=clock or time.monotonic)


def test_door1_ram_cap_enters_disk_mode(tmp_path):
    class _Down:
        def insert(self, *a, **k): raise ConnectionError("CH chết")

    w = _writer_with_spill(tmp_path, _Down())
    # vượt trần bằng block to đã cắt sẵn — không add N_CAP_ROWS dòng lẻ cho nhanh
    w.queue.append(_Pending("trade", [[None] * len(COLUMNS["trade"])] * (N_CAP_ROWS + 1)))
    w.queue_rows = N_CAP_ROWS + 1
    w.manage_once()
    assert w.disk_mode and w.head_rows == N_CAP_ROWS + 1   # queue cũ thành đầu đông cứng
    w.add(_n(9)); w.manage_once()
    assert w.queue_rows == 0 and not w.spill.empty()       # block mới xuống đĩa '-n'


def test_door2_retry_budget_spills_as_r_not_drop(tmp_path):
    clock = _Clock()

    class _Down:
        def insert(self, *a, **k):
            clock.advance(61.0)                            # một lần thử ăn hết ngân sách
            raise ConnectionError("treo")

    w = _writer_with_spill(tmp_path, _Down(), clock=clock)
    w.add(_n(1)); w.manage_once(); w.write_once(); w.write_once()
    assert w.disk_mode
    assert w.metrics.counters.get("dropped_block.trade") is None      # KHÔNG còn drop
    item = w.spill.next_batch(max_rows=10)
    assert item.kind == "r" and item.n_rows == 1                      # thành file -r


def test_no_spill_available_drops_newest_with_ledger(tmp_path, caplog):
    """spill=None (không sở hữu đĩa) — đường thoát cuối thống nhất spec §6."""
    clock = _Clock()

    class _Down:
        def insert(self, *a, **k):
            clock.advance(61.0); raise ConnectionError("treo")

    w = ChWriter(_Down(), spill=None, clock=clock)
    w.add(_n(1)); w.manage_once()
    with caplog.at_level(logging.ERROR):
        w.write_once(); w.write_once()
    assert w.metrics.counters["spill_drop_newest.trade"] == 1
    assert "BỎ block trade" in caplog.text


def test_enter_disk_during_insert_removes_the_right_block(tmp_path):
    """Vòng QUẢN và vòng GHI chạy ở HAI THREAD (main.py `manage_loop`/`write_loop`), nên
    `_enter_disk` có thể rơi vào ĐÚNG lúc vòng ghi đang nằm trong `client.insert`: khi đó
    `queue` cũ đã thành `head` còn `self.queue` là deque MỚI. Vòng ghi peek block TRƯỚC
    insert rồi popleft SAU insert — popleft "mù" theo vị trí lúc đó gỡ nhầm hàng đợi (nổ
    IndexError, hoặc tệ hơn: gỡ một block khác chưa từng được ghi ⇒ mất dòng im lặng).

    Tái hiện tất định không cần thread: cho `insert` giả tự gọi `manage_once()` giữa
    chừng — đúng thứ tự sự kiện của ca đua, chạy trong một luồng."""
    seq_i = COLUMNS["trade"].index("seq")
    seen = []
    w = None

    class _OkThenManageEntersDisk:
        def insert(self, table, data, column_names):
            seen.extend(r[seq_i] for r in data)
            w.queue_rows = N_CAP_ROWS + 1      # ép cửa 1 nổ ngay trong lúc insert
            w.manage_once()

    w = _writer_with_spill(tmp_path, _OkThenManageEntersDisk())
    w.add(_n(1)); w.manage_once()
    w.write_once()

    assert seen == [1]                          # block đã ghi đúng một lần
    assert not w.head and not w.queue           # ...và đã được gỡ khỏi hàng đợi CHỨA nó
    assert w.queue_rows == sum(len(p.block) for p in w.queue)
    assert w.head_rows == N_CAP_ROWS            # trừ đúng 1 dòng vừa ghi khỏi đầu đông cứng


def test_exit_disk_only_when_all_empty(tmp_path):
    ok = type("_Ok", (), {"insert": lambda self, *a, **k: None})()
    w = _writer_with_spill(tmp_path, ok)
    w.add(_n(1)); w.manage_once()
    w._enter_disk("test")
    w.add(_n(2)); w.manage_once()                          # dòng 2 xuống đĩa
    assert w.disk_mode
    w.write_once()                                         # xả đầu RAM + đĩa
    w.manage_once()                                        # kiểm điều kiện ra
    assert not w.disk_mode and w.clean()
