"""Runner: spawn/poll/kill tiến trình con, log theo ngày, trần, backoff daemon (spec lát 13 §5.10–5.11).

`vn(h, mi, s)` là giờ VN trong ngày 2026-09-09 (thứ 4) — KHUÔN KHÁC `vn(d, h, mi)` của
`test_sch01_planner.py` là có chủ ý: planner quyết định theo mốc PHÚT nên không cần giây, còn runner
đo tuổi tiến trình bằng GIÂY (`Finished.seconds`, backoff 30→300 s), nên mọi literal ở đây phải đi
tới giây. Ngày cố định 2026-09-09 để tên file log `-20260909.log` kiểm được bằng literal.
"""
import subprocess
from datetime import datetime, timedelta

import etl.scheduler.runner as runner_mod
from core.clock import VN
from etl.scheduler.planner import Task
from etl.scheduler.runner import BACKEND_DIR, Finished, Runner
from etl.scheduler.schedule import ALL_DAYS, JobSpec


def vn(h, mi, s):
    return datetime(2026, 9, 9, h, mi, s, tzinfo=VN)


PRICE = JobSpec("market.price_daily", ("price",), "daily", times=((15, 40),))
INTRA = JobSpec("global.yahoo", ("yahoo", "--intraday"), "intraday", weekdays=ALL_DAYS, interval_s=600)
DAEMON = JobSpec("news.collect", ("news", "--loop"), "daemon")


class FakeClock:
    def __init__(self, start):
        self.t = start

    def now(self):
        return self.t


class FakePopen:
    def __init__(self, exits_after: int | None = 0, rc: int = 0):   # số lần poll trả None trước khi thoát; None = sống mãi
        self.left, self.returncode, self.terminated, self.killed = exits_after, None, 0, 0
        self.rc = rc

    def poll(self):
        if self.left is None:
            return None
        if self.left == 0:
            self.returncode = self.rc
        else:
            self.left -= 1
        return self.returncode

    def terminate(self): self.terminated += 1

    def send_signal(self, _s): self.terminated += 1

    def kill(self): self.killed += 1; self.returncode = -9

    def wait(self, timeout=None): return self.returncode


def test_spawn_writes_a_daily_log_file_and_blocks_duplicates(tmp_path):
    spawned = []
    r = Runner(tmp_path, spawn_fn=lambda cmd, **kw: spawned.append((cmd, kw)) or FakePopen(None), clock=lambda: vn(9, 15, 40))
    assert r.spawn(PRICE, vn(9, 15, 40), "mốc 15:40") is not None
    assert (tmp_path / "market.price_daily-20260909.log").exists()
    assert spawned[0][0][1:] == ["-m", "etl", "price"]
    assert r.spawn(PRICE, vn(9, 15, 41), "mốc 15:40") is None and len(spawned) == 1


def test_duplicate_refusal_line_prints_once_per_living_child(tmp_path, capsys):
    # R26: planner re-issue cùng job mỗi nhịp 20s trong lúc con còn sống (đo lượt thật: ~360
    # dòng/ngày chỉ riêng `price`) — spec §5.9 "log một dòng" nghĩa là một dòng mỗi CON, không phải
    # mỗi lần từ chối.
    r, _ = _runner(tmp_path, lambda: vn(9, 15, 40), exits_after=None)
    child1 = r.spawn(PRICE, vn(9, 15, 40), "mốc 15:40")
    assert child1 is not None
    capsys.readouterr()   # bỏ output của lần spawn thành công (không in dòng "đang chạy")

    assert r.spawn(PRICE, vn(9, 16, 0), "nhịp tick") is None
    assert r.spawn(PRICE, vn(9, 16, 20), "nhịp tick") is None
    assert r.spawn(PRICE, vn(9, 16, 40), "nhịp tick") is None
    out = capsys.readouterr().out
    assert out.count("đang chạy, bỏ qua lượt") == 1

    child1.proc.left = 0                                    # con thoát
    fin = r.poll(vn(9, 16, 41))
    assert fin != []
    child2 = r.spawn(PRICE, vn(9, 16, 42), "mốc 15:40 lại")
    assert child2 is not None

    assert r.spawn(PRICE, vn(9, 17, 0), "nhịp tick") is None
    out2 = capsys.readouterr().out
    assert out2.count("đang chạy, bỏ qua lượt") == 1         # tổng cả bài test: đúng 2 dòng


def _runner(tmp_path, clock, exits_after=None, log=None):
    log = [] if log is None else log
    return Runner(tmp_path, spawn_fn=lambda cmd, **kw: log.append(cmd) or FakePopen(exits_after), clock=clock), log


def test_cap_of_six_children_excludes_the_daemon(tmp_path):
    r, log = _runner(tmp_path, lambda: vn(9, 15, 40))
    specs = [JobSpec(f"zz.j{i}", ("omo",), "daily", times=((15, 40),)) for i in range(7)]
    spawned = r.reconcile([Task(s, "mốc 15:40") for s in specs], vn(9, 15, 40))
    assert spawned == [f"zz.j{i}" for i in range(6)]                       # con thứ 7 chờ nhịp sau
    assert r.ensure_daemon(DAEMON, vn(9, 15, 40)) is True                     # daemon không tính vào trần
    assert len(log) == 7


def test_poll_reports_exit_code_and_duration(tmp_path, capsys):
    r, _ = _runner(tmp_path, lambda: vn(9, 15, 40), exits_after=2)
    r.spawn(PRICE, vn(9, 15, 40), "mốc 15:40")
    assert r.poll(vn(9, 16, 0)) == [] and r.poll(vn(9, 16, 20)) == []
    fin = r.poll(vn(9, 16, 20))
    assert fin == [Finished("market.price_daily", 0, 40, "mốc 15:40")]
    assert "market.price_daily rc=0 40s (mốc 15:40)" in capsys.readouterr().out
    assert r.alive("market.price_daily") is False


def test_non_zero_exit_blocks_respawn_for_ten_minutes_then_allows(tmp_path):
    # R24: news.classify chết mã 2 trước khi mở ops.etl_run trong lượt thật 2026-09-09 17:35 —
    # planner thuần-sổ không thấy dòng nào nên ra lệnh lại mỗi nhịp, runner phải tự chặn.
    log = []
    r = Runner(tmp_path, spawn_fn=lambda cmd, **kw: log.append(cmd) or FakePopen(0, rc=2), clock=lambda: vn(15, 40, 0))
    assert r.spawn(PRICE, vn(15, 40, 0), "mốc 15:40") is not None
    fin = r.poll(vn(15, 40, 20))
    assert fin == [Finished("market.price_daily", 2, 20, "mốc 15:40")]
    assert r.spawn(PRICE, vn(15, 45, 0), "mốc 15:40 lại") is None      # 5 phút sau: còn nguội
    assert len(log) == 1
    child = r.spawn(PRICE, vn(15, 50, 20), "mốc 15:40 lại")             # đúng 10 phút sau lúc thoát
    assert child is not None
    assert len(log) == 2


def test_cooldown_refusal_line_prints_once_per_window(tmp_path, capsys):
    """M1 (review toàn nhánh lát 13): dòng từ chối vì hạ nhiệt KHÔNG có chống lặp, trong khi R24
    sinh ra nó cho đúng cảnh con chết trước `open_run` — planner cấp lại mốc mỗi nhịp 20 s, nên
    một sự cố 10 phút in ~30 dòng. `tick_intraday` cũng đi qua đây (`_last_spawn` không được cập
    nhật khi spawn bị từ chối). Đúng như dòng "đang chạy, bỏ qua lượt": một dòng cho mỗi CỬA SỔ
    hạ nhiệt, không phải mỗi lần từ chối."""
    log = []
    r = Runner(tmp_path, spawn_fn=lambda cmd, **kw: log.append(cmd) or FakePopen(0, rc=2), clock=lambda: vn(15, 40, 0))
    assert r.spawn(PRICE, vn(15, 40, 0), "mốc 15:40") is not None
    assert r.poll(vn(15, 40, 20)) == [Finished("market.price_daily", 2, 20, "mốc 15:40")]
    capsys.readouterr()                                   # bỏ dòng báo con thoát

    assert r.spawn(PRICE, vn(15, 41, 0), "nhịp tick") is None
    assert r.spawn(PRICE, vn(15, 42, 0), "nhịp tick") is None
    assert r.spawn(PRICE, vn(15, 43, 0), "nhịp tick") is None
    assert capsys.readouterr().out.count("vừa thoát mã 2") == 1

    assert r.spawn(PRICE, vn(15, 50, 20), "mốc 15:40 lại") is not None    # hết 10 phút: chạy lại được
    assert len(log) == 2


def test_clean_exit_does_not_block_respawn(tmp_path):
    log = []
    r = Runner(tmp_path, spawn_fn=lambda cmd, **kw: log.append(cmd) or FakePopen(0, rc=0), clock=lambda: vn(15, 40, 0))
    assert r.spawn(PRICE, vn(15, 40, 0), "mốc 15:40") is not None
    fin = r.poll(vn(15, 40, 20))
    assert fin == [Finished("market.price_daily", 0, 20, "mốc 15:40")]
    child = r.spawn(PRICE, vn(15, 40, 21), "mốc 15:40 lại")             # 1 giây sau: thoát sạch, không nguội
    assert child is not None
    assert len(log) == 2


def test_daemon_is_not_subject_to_the_failure_cooldown(tmp_path):
    fc = FakeClock(vn(15, 40, 0))
    log = []
    r = Runner(tmp_path, spawn_fn=lambda cmd, **kw: log.append(cmd) or FakePopen(0, rc=2), clock=fc.now)
    assert r.ensure_daemon(DAEMON, fc.now()) is True
    r.poll(fc.now())                                        # chết ngay (0s), rc=2
    fc.t += timedelta(seconds=29)
    assert r.ensure_daemon(DAEMON, fc.now()) is False        # backoff daemon riêng: 30s chưa đủ
    fc.t += timedelta(seconds=1)
    assert r.ensure_daemon(DAEMON, fc.now()) is True         # đúng 30s là đủ — không chờ 10 phút như task thường


def test_intraday_spawns_on_interval_only_when_not_alive(tmp_path):
    r, log = _runner(tmp_path, lambda: vn(9, 12, 0), exits_after=None)
    t0 = vn(9, 12, 0)
    assert r.tick_intraday([INTRA], t0) == ["global.yahoo"]
    assert r.tick_intraday([INTRA], t0 + timedelta(seconds=300)) == []
    assert r.tick_intraday([INTRA], t0 + timedelta(seconds=600)) == []      # đủ nhịp nhưng con còn sống
    r._children["global.yahoo"].proc.left = 0                                # cho con "chết"
    r.poll(t0 + timedelta(seconds=620))
    assert r.tick_intraday([INTRA], t0 + timedelta(seconds=620)) == ["global.yahoo"]
    assert len(log) == 2


def test_daemon_backoff_30_60_120_and_reset(tmp_path):
    fc = FakeClock(vn(9, 12, 0))
    r, log = _runner(tmp_path, fc.now, exits_after=0)                        # con chết ngay ở lần poll đầu
    marks = []
    for _ in range(4):
        if r.ensure_daemon(DAEMON, fc.now()):
            marks.append(fc.now())
        r.poll(fc.now())
        fc.t += timedelta(seconds=10)
        while not r.ensure_daemon(DAEMON, fc.now()):
            fc.t += timedelta(seconds=10)
        marks.append(fc.now())
        r.poll(fc.now())
    gaps = [(b - a).total_seconds() for a, b in zip(marks, marks[1:])][:3]
    assert gaps == [30.0, 60.0, 120.0]
    fc.t += timedelta(seconds=400)                                            # sống quá 300 s ⇒ reset
    r._children["news.collect"].proc.left = 0
    r.poll(fc.now())
    fc.t += timedelta(seconds=30)
    assert r.ensure_daemon(DAEMON, fc.now()) is True


def test_cap_of_six_excludes_an_already_alive_daemon(tmp_path):
    # F1 (review): daemon giành chỗ trước (§5.10) rồi mới reconcile task thường — trần 6 vẫn phải
    # để đủ 6 task thường spawn, daemon không ăn vào một trong sáu chỗ đó.
    r, log = _runner(tmp_path, lambda: vn(9, 15, 40))
    assert r.ensure_daemon(DAEMON, vn(9, 15, 40)) is True
    specs = [JobSpec(f"zz.j{i}", ("omo",), "daily", times=((15, 40),)) for i in range(7)]
    spawned = r.reconcile([Task(s, "mốc 15:40") for s in specs], vn(9, 15, 40))
    assert spawned == [f"zz.j{i}" for i in range(6)]
    assert len(log) == 7                                                    # 1 daemon + 6 task thường


def test_daemon_backoff_resets_to_30s_after_a_healthy_run(tmp_path):
    # F2 (review): bản cũ của test backoff không thực sự chạy tới nhánh reset (con đã bị thu hoạch
    # trước khi tới đoạn "sống quá 300s"). Test này spawn daemon thật, cho nó chết ngay một lần để
    # đẩy giãn cách lên 60s cho lần sau, rồi cho nó SỐNG hơn 300s trước khi chết lần hai — nếu reset
    # đúng, giãn cách quay về 30s (chờ 30s là đủ); nếu không reset, giãn cách vẫn là 60s (30s chưa đủ).
    fc = FakeClock(vn(9, 12, 0))
    r, log = _runner(tmp_path, fc.now, exits_after=None)
    assert r.ensure_daemon(DAEMON, fc.now()) is True
    r._children["news.collect"].proc.left = 0
    r.poll(fc.now())                                       # chết ngay (0s) -> chờ=30s, giãn kế=60s
    fc.t += timedelta(seconds=30)
    assert r.ensure_daemon(DAEMON, fc.now()) is True        # spawn lại đúng lúc hết 30s chờ
    fc.t += timedelta(seconds=400)                          # sống > 300s -> lần chết sau phải reset
    r._children["news.collect"].proc.left = 0
    r.poll(fc.now())
    fc.t += timedelta(seconds=30)
    assert r.ensure_daemon(DAEMON, fc.now()) is True        # đúng 30s là đủ; 60s (chưa reset) sẽ False


def test_spawn_failure_closes_log_handle_and_returns_none(tmp_path):
    # F3 (review): spawn_fn ném lỗi (vd. thiếu file thực thi) không được văng ra ngoài caller, và
    # handle log đã mở phải được đóng lại — không rò.
    def boom(cmd, **kw):
        raise OSError("boom")

    r = Runner(tmp_path, spawn_fn=boom, clock=lambda: vn(9, 15, 40))
    result = r.spawn(PRICE, vn(9, 15, 40), "mốc 15:40")
    assert result is None
    assert r.alive("market.price_daily") is False
    assert "market.price_daily" not in r._children
    log_file = tmp_path / "market.price_daily-20260909.log"
    assert log_file.exists()
    log_file.unlink()                                       # handle còn mở thì unlink lỗi trên Windows


def test_shutdown_terminates_then_kills_after_grace(tmp_path):
    r, _ = _runner(tmp_path, lambda: vn(9, 15, 40), exits_after=None)
    r.spawn(PRICE, vn(9, 15, 40), "mốc 15:40")
    proc = r._children["market.price_daily"].proc
    slept = []
    r.shutdown(grace_s=60, sleep=lambda s: slept.append(s))
    assert proc.terminated == 1 and proc.killed == 1 and sum(slept) >= 60
    assert r.alive("market.price_daily") is False


def test_prune_old_logs_keeps_30_days(tmp_path):
    (tmp_path / "zz-20260101.log").write_text("cũ", encoding="utf-8")
    (tmp_path / "zz-20260909.log").write_text("mới", encoding="utf-8")
    r, _ = _runner(tmp_path, lambda: vn(9, 15, 40))
    assert r.prune_old_logs(vn(9, 15, 40)) == ["zz-20260101.log"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["zz-20260909.log"]


# Hai nhánh nền tảng dưới đây phải kiểm được trên MỘT máy: dev là Windows, production là container
# Linux — chạy `FakePopen` nên không cần tiến trình thật, chỉ cần đọc `os.name` lúc gọi.
def test_stop_signal_is_ctrl_break_on_windows_and_sigterm_on_posix(monkeypatch):
    proc, sent = FakePopen(None), []
    proc.send_signal = sent.append
    monkeypatch.setattr(runner_mod.os, "name", "nt")
    runner_mod._stop_child(proc)
    assert sent == [1] and proc.terminated == 0        # CTRL_BREAK_EVENT == 1 trên Windows
    monkeypatch.setattr(runner_mod.os, "name", "posix")
    runner_mod._stop_child(proc)
    assert sent == [1] and proc.terminated == 1        # POSIX: SIGTERM qua terminate()


def test_spawn_kwargs_put_the_child_in_its_own_process_group(tmp_path, monkeypatch):
    monkeypatch.setattr(runner_mod.os, "name", "posix")
    assert runner_mod._platform_kwargs() == {"start_new_session": True}
    monkeypatch.setattr(runner_mod.os, "name", "nt")
    assert runner_mod._platform_kwargs() == {"creationflags": 0x00000200}   # CREATE_NEW_PROCESS_GROUP
    spawned = []
    r = Runner(tmp_path, spawn_fn=lambda cmd, **kw: spawned.append(kw) or FakePopen(None), clock=lambda: vn(9, 15, 40))
    child = r.spawn(PRICE, vn(9, 15, 40), "mốc 15:40")
    kw = spawned[0]
    assert kw["cwd"] == BACKEND_DIR and kw["stderr"] == subprocess.STDOUT   # `python -m etl` chỉ chạy từ backend/
    assert kw["stdout"] is child.log_fh and kw["creationflags"] == 0x00000200
    child.log_fh.close()
