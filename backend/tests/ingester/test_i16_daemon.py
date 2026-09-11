"""Daemon: ngoài phiên ngủ, trong phiên chạy, lỗi khởi động (≥ 2) thoát để Docker khởi động lại (spec §5.5)."""
import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta

import ingester.main as main_mod
from ingester.config import Config as IngesterConfig
from ingester.main import (
    SESSION_END_MEASURE,
    SESSION_END_RUN,
    SESSION_START,
    TZ,
    _relay,
    _session_with_relay,
    daemon,
    install_loop_stop,
    next_window,
)


def vn(y, m, d, h, mi):
    return datetime(y, m, d, h, mi, tzinfo=TZ)


# 2026-09-08 là thứ 3 · 11/09 thứ 6 · 12/09 thứ 7 · 14/09 thứ 2
def test_next_window_friday_evening_rolls_to_monday():
    assert next_window(vn(2026, 9, 11, 16, 0), SESSION_START, SESSION_END_RUN) == (vn(2026, 9, 14, 8, 30), vn(2026, 9, 14, 15, 5))


def test_next_window_saturday_rolls_to_monday():
    assert next_window(vn(2026, 9, 12, 10, 0), SESSION_START, SESSION_END_RUN) == (vn(2026, 9, 14, 8, 30), vn(2026, 9, 14, 15, 5))


def test_next_window_early_morning_is_the_same_day():
    assert next_window(vn(2026, 9, 8, 7, 0), SESSION_START, SESSION_END_RUN) == (vn(2026, 9, 8, 8, 30), vn(2026, 9, 8, 15, 5))


def test_next_window_inside_session_returns_the_open_window():
    assert next_window(vn(2026, 9, 8, 9, 0), SESSION_START, SESSION_END_RUN) == (vn(2026, 9, 8, 8, 30), vn(2026, 9, 8, 15, 5))


def test_next_window_at_15_05_is_already_tomorrow():
    assert next_window(vn(2026, 9, 8, 15, 5), SESSION_START, SESSION_END_RUN)[0] == vn(2026, 9, 9, 8, 30)


def test_measure_window_ends_15_10():
    assert next_window(vn(2026, 9, 8, 9, 0), SESSION_START, SESSION_END_MEASURE)[1] == vn(2026, 9, 8, 15, 10)


class FakeClock:
    def __init__(self, start):
        self.t = start
        self.sleeps = []

    def now(self):
        return self.t

    async def sleep(self, s):
        self.sleeps.append(s)
        self.t += timedelta(seconds=s)


def test_daemon_sleeps_until_08_30_then_runs_one_session():
    fc = FakeClock(vn(2026, 9, 8, 7, 0))
    stop = asyncio.Event()
    calls = []

    async def session():
        calls.append(fc.now())
        fc.t = vn(2026, 9, 8, 15, 5)      # phiên chạy tới deadline như `_run_run`
        stop.set()
        return 0

    rc = asyncio.run(daemon("run", session, clock=fc.now, sleep=fc.sleep, stop=stop, end_hm=SESSION_END_RUN))
    assert rc == 0
    assert calls == [vn(2026, 9, 8, 8, 30)]
    assert max(fc.sleeps) <= 60 and sum(fc.sleeps) == 90 * 60


def test_daemon_runs_immediately_when_inside_the_window_and_exits_on_startup_failure():
    fc = FakeClock(vn(2026, 9, 8, 9, 0))
    calls = []

    async def session():
        calls.append(fc.now())
        return 3                          # hợp đồng khởi động hỏng ⇒ thoát để Docker restart

    rc = asyncio.run(daemon("run", session, clock=fc.now, sleep=fc.sleep, stop=asyncio.Event(), end_hm=SESSION_END_RUN))
    assert rc == 3 and calls == [vn(2026, 9, 8, 9, 0)] and fc.sleeps == []


def test_daemon_after_a_clean_session_waits_for_the_next_window():
    fc = FakeClock(vn(2026, 9, 8, 9, 0))
    stop = asyncio.Event()
    calls = []

    async def session():
        calls.append(fc.now())
        fc.t = vn(2026, 9, 8, 15, 5)
        if len(calls) == 2:
            stop.set()
        return 1                          # đối chứng lệch = phiên vẫn kết thúc bình thường, không thoát

    asyncio.run(daemon("run", session, clock=fc.now, sleep=fc.sleep, stop=stop, end_hm=SESSION_END_RUN))
    assert calls == [vn(2026, 9, 8, 9, 0), vn(2026, 9, 9, 8, 30)]


def test_install_loop_stop_declines_on_windows_and_arms_on_posix():
    async def scenario():
        stop = asyncio.Event()
        armed = install_loop_stop(stop)
        if sys.platform == "win32":
            assert armed is False and not stop.is_set()
            return
        assert armed is True
        signal.raise_signal(signal.SIGTERM)
        await asyncio.sleep(0.05)          # handler chạy ở vòng lặp kế
        assert stop.is_set()
    asyncio.run(scenario())


def test_daemon_returns_right_after_a_session_ended_by_signal():
    fc = FakeClock(vn(2026, 9, 8, 10, 0))
    stop = asyncio.Event()

    async def session():
        fc.t = vn(2026, 9, 8, 10, 5)
        stop.set()                          # tín hiệu đến giữa phiên: _run_run đóng phiên rồi trả về
        return 0

    rc = asyncio.run(daemon("run", session, clock=fc.now, sleep=fc.sleep, stop=stop, end_hm=SESSION_END_RUN))
    assert rc == 0 and fc.sleeps == []      # không ngủ tới phiên kế — thoát ngay để container dừng


def test_relay_sets_the_session_stop_when_shutdown_fires():
    async def scenario():
        shutdown, stop = asyncio.Event(), asyncio.Event()
        task = asyncio.create_task(_relay(shutdown, stop))
        await asyncio.sleep(0)
        assert not stop.is_set()
        shutdown.set()
        await asyncio.sleep(0.01)
        assert stop.is_set()
        await task
    asyncio.run(scenario())


def test_each_session_gets_a_fresh_stop_and_the_relay_is_cancelled_after_it():
    async def scenario():
        shutdown, seen = asyncio.Event(), []

        async def factory(stop):
            seen.append(stop)
            return 7

        assert await _session_with_relay(shutdown, factory) == 7
        assert await _session_with_relay(shutdown, factory) == 7
        assert seen[0] is not seen[1] and not seen[0].is_set() and not seen[1].is_set()
        shutdown.set()                      # relay đã huỷ: bật shutdown sau khi phiên xong không đụng stop cũ
        await asyncio.sleep(0.01)
        assert not seen[1].is_set()
    asyncio.run(scenario())


def test_loop_stop_is_armed_only_for_run_and_measure(monkeypatch):
    armed = []
    monkeypatch.setattr(main_mod, "install_loop_stop", lambda ev: armed.append(ev) or True)

    async def fake_count(*a, **k):
        return 0

    async def fake_run(cfg, minutes, stop=None):
        return 0

    async def fake_reconcile(cfg, d):
        return 0

    monkeypatch.setattr(main_mod, "_run_count", fake_count)
    monkeypatch.setattr(main_mod, "_run_run", fake_run)
    monkeypatch.setattr(main_mod, "_run_reconcile", fake_reconcile)
    monkeypatch.setattr(main_mod.config, "load", lambda need_db: object())
    monkeypatch.setattr(main_mod, "_day_log_handler", lambda cfg: logging.NullHandler())
    assert asyncio.run(main_mod.run("count", count="20260908")) == 0
    assert armed == []                                        # count: giữ đường KeyboardInterrupt
    assert asyncio.run(main_mod.run("reconcile")) == 0
    assert armed == []                                        # reconcile: lượt ngắn một phát, cũng không arm
    assert asyncio.run(main_mod.run("run", minutes=1)) == 0
    assert len(armed) == 1                                    # run: một lần, trước khi rẽ


def test_run_exits_2_when_the_day_log_cannot_be_opened(tmp_path, monkeypatch, capsys):
    """Mở file log là điều kiện khởi động: volume sai quyền, ổ đầy ⇒ exit 2 có lý do, không traceback exit 1."""
    blocker = tmp_path / "logs"
    blocker.write_text("file, không phải thư mục", encoding="utf-8")
    cfg = IngesterConfig(clickhouse_url="fake://", redis_url="redis://x",
                         log_dir=blocker, measure_dir=tmp_path, spill_dir=tmp_path)
    monkeypatch.setattr(main_mod.config, "load", lambda need_db: cfg)
    assert asyncio.run(main_mod.run("run", minutes=1)) == 2
    assert "không ghi được log" in capsys.readouterr().err
