"""Hồi phục — spec spill §4/§5. Seam 8, 10, 13, 14, 17 + nợ Task 6 (M4, gauge spill_bytes).

Task 8: phát lại nợ đĩa lúc khởi động (`ChWriter.replay_debt`), đối chứng lại ngày nợ
(`main._replay_startup_debt`, spec §5.3), và `drain_writer` biết đĩa (spec §5.1/§5.2).
"""
import asyncio
import gc
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import ingester.main as main_mod
from ingester.chwriter import COLUMNS, ChWriter
from ingester.normalize import Normalized
from ingester.main import (
    DRAIN_CLEAN_BUDGET_S,
    DRAIN_HARD_CAP_S,
    _replay_startup_debt,
    drain_writer,
)
from ingester.reconcile import ReconcileResult
from ingester.spill import SpillStore

TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _trade_rows(day: int, n: int) -> list[list]:
    """Dòng `rt.trade` đúng thứ tự COLUMNS — `received_at` là cột CUỐI (index 9)."""
    ts = datetime(2026, 8, day, 9, 15, 1, tzinfo=TZ)
    return [["ACV", ts, i, Decimal("10.00"), 100, "B", Decimal("0.00"),
             100, Decimal("1000.00"), ts] for i in range(n)]


def _ok_client():
    return type("_Ok", (), {"insert": lambda self, *a, **k: None})()


class _Down:
    def insert(self, *a, **k):
        raise ConnectionError("CH chưa dậy")


class _FakeClock:
    """Đồng hồ giả: mỗi lần `sleep(d)` được gọi thì nhảy đúng d giây."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    async def sleep(self, d: float) -> None:
        self.now += d


class _NeverClean:
    """Writer giả không bao giờ sạch — chỉ để đo NGÂN SÁCH mà `drain_writer` tự chọn."""

    def __init__(self, spill=None, disk_mode=False):
        self.spill, self.disk_mode = spill, disk_mode
        self.calls = 0

    def manage_once(self) -> None:
        pass

    def write_once(self, budget_s: float = 0) -> None:
        self.calls += 1

    def clean(self) -> bool:
        return False


# --- replay_debt: xả nợ trước phiên -----------------------------------------------


def test_replay_debt_returns_dates_and_empties_disk(tmp_path):
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire()
    s.write("trade", _trade_rows(day=26, n=3), "n")
    s.write("trade", _trade_rows(day=27, n=2), "r")
    w = ChWriter(_ok_client(), spill=s)
    dates = w.replay_debt()
    assert dates == {date(2026, 8, 26), date(2026, 8, 27)}
    assert s.empty() and w.clean()
    assert w.metrics.counters["replay_blocks"] == 2


def test_replay_debt_stops_on_transient_and_stays_disk_mode(tmp_path):
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire()
    s.write("trade", _trade_rows(day=26, n=3), "n")
    w = ChWriter(_Down(), spill=s)
    dates = w.replay_debt()
    # nợ giữ nguyên trên đĩa, vào phiên ở chế độ đĩa (KHÔNG mất dòng, KHÔNG chặn khởi động)
    assert dates == set() and w.disk_mode and not s.empty()
    assert not w.clean()


def test_replay_debt_does_not_touch_a_store_we_do_not_own(tmp_path):
    """Spec §4: không sở hữu thì KHÔNG đụng, kể cả đọc."""
    owner = SpillStore(tmp_path, cap_bytes=10**9)
    assert owner.try_acquire()
    assert owner.write("trade", _trade_rows(day=27, n=1), "n")
    before = sorted(p.name for p in tmp_path.iterdir())

    calls = []
    intruder = SpillStore(tmp_path, cap_bytes=10**9)   # KHÔNG try_acquire → owned = False
    w = ChWriter(type("_Rec", (), {"insert": lambda s, t, d, column_names:
                                   calls.append(len(d))})(), spill=intruder)
    assert w.replay_debt() == set()
    assert calls == []
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_replay_debt_enters_disk_mode_whenever_it_leaves_files_behind(tmp_path):
    """Bất biến ra khỏi `replay_debt`: đĩa còn file ⇒ PHẢI ở chế độ đĩa. Đường transient
    tự vào, nhưng đường "chia đôi dòng độc hỏng giữa chừng" (giữ file cha, review I3) thì
    KHÔNG — mà bỏ sót nó là hỏng đúng thứ lát này dựng ra: `_adopt_spill_if_possible` chỉ
    vào chế độ đĩa lúc NHẬN NUÔI, store đã sở hữu rồi thì nó về ngay, nên file cha nằm lại
    suốt phiên trong khi block mới đi thẳng vào kho — FIFO vỡ, và `clean()` False tới cuối
    phiên ⇒ phán quyết "KHÔNG ĐÁNG TIN" mỗi ngày."""
    class _Poison:
        def insert(self, *a, **k):
            raise Exception("Code: 117. DB::Exception: x (INCORRECT_DATA)")

    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire()
    assert s.write("trade", _trade_rows(day=27, n=4), "n")
    w = ChWriter(_Poison(), spill=s)
    s.write = lambda *a, **k: False              # mọi file con ghi hỏng → giữ file cha
    assert w.replay_debt() == set()
    assert not s.empty()                         # cha còn nguyên, chưa insert xong chưa xoá
    assert w.disk_mode                           # ...nên phiên phải khởi động ở chế độ đĩa


def test_replay_debt_survives_disk_io_error_and_does_not_kill_startup(tmp_path):
    """Spec §2.1 nới sang đường KHỞI ĐỘNG: lỗi I/O đĩa không được thoát ra ngoài. Thoát ra
    thì nó bay qua `_run_run` thành traceback trần exit 1 — đi vòng đúng hợp đồng exit 3,
    y hệt sự cố ACCESS_DENIED 26/08."""
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire()
    assert s.write("trade", _trade_rows(day=27, n=1), "n")
    w = ChWriter(_ok_client(), spill=s)

    def _boom(item):
        raise OSError("ổ đĩa lỗi lúc xoá")

    s.delete = _boom
    days = w.replay_debt()                       # KHÔNG được ném ra ngoài
    # Ngày 27 VẪN vào tập nợ: insert đã thành công (dòng đã ở trong kho), chỉ khâu xoá
    # file hỏng — nên đúng là ngày đó cần chạy lại đối chứng, và cũng đúng là lần phát lại
    # sau sẽ ghi TRÙNG block này ("ack thất lạc", spec §4: thà trùng hơn mất).
    assert days == {date(2026, 8, 27)}
    assert w.metrics.counters["spill_io_error"] == 1
    assert w.disk_mode and not s.empty()         # nợ giữ nguyên, vòng ghi trong phiên thử lại


# --- Seam 14: mất/giành lại leadership giữa phiên ---------------------------------


def _n(seq: int) -> Normalized:
    row = {c: None for c in COLUMNS["trade"]}
    row["symbol"], row["seq"] = "ACV", seq
    return Normalized(table="trade", row=row, delta={}, symbol="ACV")


def test_lost_leadership_keeps_spilling_and_never_loses_the_frozen_head(tmp_path):
    """Spec §4: mất leadership = NGỪNG insert (main.py: `write_loop` chỉ chạy khi
    `is_leader`), nhưng vòng QUẢN chạy vô điều kiện — spill là I/O cục bộ, không cần
    leadership. Đầu RAM đông cứng phải còn nguyên, dòng mới phải xuống đĩa, và khi giành
    lại leadership thì FIFO toàn cục vẫn là đầu-RAM-trước-rồi-đĩa."""
    seq_i = COLUMNS["trade"].index("seq")
    seen = []
    client = type("_Rec", (), {"insert": lambda s, t, d, column_names:
                               seen.extend(r[seq_i] for r in d)})()
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire()
    w = ChWriter(client, spill=s)
    w.add(_n(1))
    w.manage_once()
    w._enter_disk("test")                       # dòng 1 đông cứng vào đầu RAM

    for seq in (2, 3):                          # mất leader: CHỈ vòng quản chạy
        w.add(_n(seq))
        w.manage_once()
    assert seen == []                           # không leader thì không ghi kho
    assert w.head_rows == 1 and sum(len(p.block) for p in w.head) == 1
    assert not s.empty()                        # ...nhưng vẫn xuống đĩa

    guard = 0
    while w.disk_mode:                           # giành lại leadership: vòng ghi chạy lại
        guard += 1
        assert guard <= 50, "livelock: không thoát chế độ đĩa sau 50 nhịp"
        w.write_once()
        w.manage_once()
    assert seen == [1, 2, 3] and w.clean()


# --- clean(): nợ đĩa CỦA MÌNH mới tính --------------------------------------------


def test_clean_counts_own_disk_but_ignores_another_process_files(tmp_path):
    owner = SpillStore(tmp_path, cap_bytes=10**9)
    assert owner.try_acquire()
    assert owner.write("trade", _trade_rows(day=27, n=1), "n")
    intruder = SpillStore(tmp_path, cap_bytes=10**9)   # KHÔNG try_acquire → owned = False

    assert ChWriter(_ok_client(), spill=intruder).clean() is True   # file của chủ khác
    assert ChWriter(_ok_client(), spill=owner).clean() is False     # nợ của chính mình


# --- Nợ Task 6, M4: try_acquire phải quét TRƯỚC khi tự nhận sở hữu ----------------


def test_try_acquire_scans_before_owning_so_next_write_cannot_collide(tmp_path):
    """M4: `owned = True` đặt TRƯỚC `scan()` mở một khe: block xuống đĩa trong khe đó ghi
    với `seq` cũ (=1) lên đúng tên file đã tồn tại → `seq_collision`, block bị TỪ CHỐI dù
    đĩa hoàn toàn khoẻ. Giành khoá xong là store phải SẴN SÀNG ghi ngay."""
    s1 = SpillStore(tmp_path, cap_bytes=10**9)
    assert s1.try_acquire()
    assert s1.write("trade", _trade_rows(day=26, n=1), "n")        # → seq 1
    del s1
    gc.collect()                                                   # nhả khoá (chủ cũ "chết")

    s2 = SpillStore(tmp_path, cap_bytes=10**9)
    assert s2.try_acquire()                                        # KHÔNG gọi scan() thủ công
    assert s2.seq == 2 and s2.bytes_used > 0
    assert s2.write("trade", _trade_rows(day=27, n=1), "r") is True
    assert s2.counters["seq_collision"] == 0
    names = sorted(p.name for p in tmp_path.iterdir() if p.suffix == ".blk")
    assert names == ["0000000001-trade-n.blk", "0000000002-trade-r.blk"]


# --- Nợ Task 6: gauge spill_bytes (spec §8) ---------------------------------------


def test_spill_bytes_gauge_mirrored_each_tick(tmp_path):
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire()
    w = ChWriter(_ok_client(), spill=s)
    w.manage_once()
    assert w.metrics.counters["spill_bytes"] == 0
    s.write("trade", _trade_rows(day=27, n=2), "n")
    w.manage_once()
    on_disk = sum(p.stat().st_size for p in tmp_path.iterdir() if p.suffix == ".blk")
    assert on_disk > 0
    assert w.metrics.counters["spill_bytes"] == on_disk     # đo độc lập từ chính file


# --- drain_writer biết đĩa (spec §5.1/§5.2) ---------------------------------------


def test_drain_false_when_disk_not_empty(tmp_path, caplog):
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire()
    w = ChWriter(_Down(), spill=s)
    w._enter_disk("test")
    s.write("trade", _trade_rows(day=27, n=1), "n")
    with caplog.at_level(logging.ERROR):
        drained = asyncio.run(drain_writer(w, budget_s=0.3))
    assert drained is False
    assert "còn" in caplog.text                             # log nợ: "còn X block / Y byte"
    assert not s.empty()                                    # nợ ĐỂ LẠI, không vứt


def test_default_budget_short_when_no_debt(tmp_path):
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire()
    w = ChWriter(_ok_client(), spill=s)
    assert asyncio.run(drain_writer(w)) is True             # sạch ngay, không chờ 600s


def test_default_budget_is_hard_cap_when_disk_mode():
    clock = _FakeClock()
    w = _NeverClean(spill=None, disk_mode=True)
    assert asyncio.run(drain_writer(w, sleep_fn=clock.sleep, clock=clock)) is False
    elapsed = clock.now - 1000.0
    assert DRAIN_CLEAN_BUDGET_S < elapsed <= DRAIN_HARD_CAP_S + 1.0


def test_default_budget_is_clean_budget_when_no_spill_and_no_disk_mode():
    clock = _FakeClock()
    w = _NeverClean(spill=None, disk_mode=False)
    assert asyncio.run(drain_writer(w, sleep_fn=clock.sleep, clock=clock)) is False
    assert clock.now - 1000.0 <= DRAIN_CLEAN_BUDGET_S + 1.0


# --- Khởi động: phát lại nợ rồi đối chứng LẠI ngày nợ (spec §5.3) -----------------


class _FakeStore:
    def __init__(self, acquired: bool):
        self._acquired = acquired
        self.owned = False

    def try_acquire(self) -> bool:
        self.owned = self._acquired
        return self._acquired


class _FakeWriter:
    def __init__(self, debt: set):
        self.debt, self.calls = debt, 0

    def replay_debt(self) -> set:
        self.calls += 1
        return self.debt


class _FakeCHClient:
    def __init__(self):
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_startup_debt_reconciles_only_days_before_today(monkeypatch):
    today = datetime.now(TZ).date()
    yday, d2 = today - timedelta(days=1), today - timedelta(days=3)
    seen, clients = [], []

    def _fake_reconcile(client, d):
        seen.append(d)
        return ReconcileResult([], [], 7)

    monkeypatch.setattr(main_mod, "reconcile", _fake_reconcile)

    def _factory():
        clients.append(_FakeCHClient())
        return clients[-1]

    w = _FakeWriter({today, yday, d2})
    days = asyncio.run(_replay_startup_debt(w, _FakeStore(acquired=True), _factory))
    assert w.calls == 1
    assert days == [d2, yday]        # cũ trước, và ngày HÔM NAY KHÔNG đối chứng sớm
    assert seen == [d2, yday]
    assert clients and all(c.closed for c in clients)      # không rò client đối chứng


def test_startup_without_lock_skips_replay_and_warns(caplog):
    w = _FakeWriter({date(2026, 8, 26)})
    with caplog.at_level(logging.WARNING):
        days = asyncio.run(_replay_startup_debt(w, _FakeStore(acquired=False),
                                                _FakeCHClient))
    assert days == [] and w.calls == 0          # không sở hữu → không đụng đĩa
    assert "KHÔNG có lưới đĩa" in caplog.text
