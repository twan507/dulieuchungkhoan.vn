"""Runner — lớp giám sát tiến trình con của scheduler (spec lát 13 §5.10–5.11).

Một việc duy nhất: **spawn / poll / kill** `python -m etl <job>`, ghi stdout+stderr của mỗi con vào
một file log theo ngày. Không đọc sổ `ops.etl_run` (planner lo), không có vòng lặp (loop.py lo) —
mọi phương thức nhận `now` từ ngoài nên kiểm được bằng literal, không cần ngủ thật.

Trạng thái trong RAM (`_last_spawn`, backoff daemon) là **vô hại** theo spec §4.3: mất khi khởi
động lại thì cùng lắm một nhịp intraday chạy sớm, còn mọi quyết định "đã chạy chưa" đều nằm ở sổ.

Chống chạy chồng lớp ngoài (§5.9): một `spec.name` chỉ có một con sống — bản trọn ngày và bản
`--intraday` mang cùng tên nên tự không giẫm nhau.

`_last_failed` (R24, 2026-09-09): con thoát mã khác 0 trước cả khi kịp mở `ops.etl_run` (auth hỏng,
DNS, schema drift — `news.classify` đo được ngoài đời) khiến planner thuần-sổ cứ ra lệnh lại mỗi
nhịp; guard này chặn respawn cùng tên 10 phút sau lần thoát lỗi. Cùng loại RAM-state như
`_last_spawn`: mất khi restart chỉ tốn nhiều nhất một lượt thử sớm, vô hại — không phải nguồn sự thật.
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from core.clock import now_vn, today_vn
from core.env import REPO_ROOT
from etl.scheduler.planner import Task
from etl.scheduler.schedule import (
    LOG_KEEP_DAYS,
    MAX_CONCURRENT_CHILDREN,
    RETRY_AFTER_MIN,
    SHUTDOWN_GRACE_S,
    JobSpec,
)

BACKEND_DIR = REPO_ROOT / "backend"     # `python -m etl` chỉ import được khi cwd là backend/

DAEMON_BACKOFF_START_S = 30     # §5.11: chết lại trong 5 phút ⇒ giãn 30 s, nhân đôi
DAEMON_BACKOFF_MAX_S = 300
DAEMON_HEALTHY_S = 300          # sống quá ngần này ⇒ coi như lành, reset giãn cách
STOP_POLL_S = 1                 # nhịp hỏi lại trong lúc chờ con tự tắt

# Windows gửi CTRL_BREAK_EVENT (== 1) cho cả nhóm tiến trình; hằng số này không tồn tại trên POSIX
# nên phải lấy qua getattr — nhánh Windows vẫn kiểm được khi test chạy trong container Linux.
CTRL_BREAK_EVENT = getattr(signal, "CTRL_BREAK_EVENT", 1)
CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)

LOG_NAME_RE = re.compile(r".+-(\d{8})\.log")


@dataclass
class Child:
    spec: JobSpec
    proc: object             # subprocess.Popen thật, hoặc con giả trong test
    started_at: datetime
    log_fh: object
    reason: str              # lý do planner sinh ra lượt này, in lại lúc con thoát


@dataclass(frozen=True)
class Finished:
    name: str
    rc: int
    seconds: int
    reason: str


def _platform_kwargs() -> dict:
    """Tách con khỏi nhóm tiến trình của runner: Ctrl-C ở terminal không giết cả đàn, và lúc dừng
    runner mới chủ động gửi tín hiệu cho từng con theo thứ tự (§5.10)."""
    if os.name == "nt":
        return {"creationflags": CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def _stop_child(proc) -> None:
    """Xin con tự đóng sổ: POSIX SIGTERM (job bắt được, ghi `ops.etl_run` rồi thoát 130),
    Windows CTRL_BREAK_EVENT — `terminate()` trên Windows là TerminateProcess, giết cứng, con
    không kịp đóng dòng đang chạy."""
    if os.name == "nt":
        proc.send_signal(CTRL_BREAK_EVENT)
    else:
        proc.terminate()


class Runner:
    def __init__(self, log_dir: Path, *, spawn_fn=subprocess.Popen, clock=now_vn,
                 max_children: int = MAX_CONCURRENT_CHILDREN, python: str = sys.executable):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.spawn_fn = spawn_fn
        self.clock = clock
        self.max_children = max_children
        self.python = python
        # Con đã thoát vẫn NẰM LẠI trong dict (bản ghi lượt gần nhất): `proc.returncode is None`
        # vừa là "còn sống" vừa là "chưa báo cáo", nên `poll` không bao giờ in hai lần một cái chết.
        self._children: dict[str, Child] = {}
        self._last_spawn: dict[str, datetime] = {}
        self._last_failed: dict[str, tuple[int, datetime]] = {}
        self._daemon_last_exit: datetime | None = None
        self._daemon_wait_s = 0             # giãn cách đang áp cho lần chết vừa rồi
        self._daemon_backoff_s = DAEMON_BACKOFF_START_S   # giãn cách cho lần chết TIẾP THEO

    # ---- trạng thái ------------------------------------------------------
    def alive(self, name: str) -> bool:
        child = self._children.get(name)
        return child is not None and child.proc.returncode is None

    def _live_children(self) -> list[Child]:
        return [c for c in self._children.values() if c.proc.returncode is None]

    def _live_non_daemon_children(self) -> list[Child]:
        """Trần §5.9 chỉ áp cho task thường: daemon được đảm bảo sống riêng (§5.10), không chiếm
        một trong sáu chỗ — nếu tính cả daemon, trần thực tế còn 5."""
        return [c for c in self._children.values()
                if c.proc.returncode is None and c.spec.kind != "daemon"]

    def log_path(self, name: str, now: datetime) -> Path:
        return self.log_dir / f"{name}-{now:%Y%m%d}.log"

    # ---- spawn -----------------------------------------------------------
    def spawn(self, spec: JobSpec, now: datetime, reason: str) -> Child | None:
        """Chạy `python -m etl <cmd>`, stdout+stderr nối vào log của ngày. None khi từ chối.

        Ba lý do từ chối, mỗi lý do một dòng stdout (§5.9): con cùng tên còn sống, vừa thoát mã khác
        0 chưa đủ 10 phút nguội (R24), hoặc đã đủ trần. Daemon không tính trần, không chịu nguội —
        được đảm bảo trước (§5.10) và có backoff riêng của nó.
        """
        if self.alive(spec.name):
            print(f"[{now:%Y-%m-%d %H:%M:%S}] {spec.name} đang chạy, bỏ qua lượt ({reason})", flush=True)
            return None
        if spec.kind != "daemon":
            failed = self._last_failed.get(spec.name)
            if failed is not None:
                rc, failed_at = failed
                if now < failed_at + timedelta(minutes=RETRY_AFTER_MIN):
                    print(f"[{now:%Y-%m-%d %H:%M:%S}] {spec.name} vừa thoát mã {rc} lúc {failed_at:%H:%M}, "
                          f"chờ {RETRY_AFTER_MIN} phút ({reason})", flush=True)
                    return None
        if spec.kind != "daemon" and len(self._live_non_daemon_children()) >= self.max_children:
            print(f"[{now:%Y-%m-%d %H:%M:%S}] {spec.name} hoãn: đủ {self.max_children} tiến trình con ({reason})", flush=True)
            return None
        fh = self.log_path(spec.name, now).open("a", encoding="utf-8")
        cmd = [self.python, "-m", "etl", *spec.cmd]
        try:
            proc = self.spawn_fn(cmd, cwd=BACKEND_DIR, env=os.environ.copy(),
                                 stdout=fh, stderr=subprocess.STDOUT, **_platform_kwargs())
        except OSError as exc:
            fh.close()
            print(f"[{now:%Y-%m-%d %H:%M:%S}] {spec.name} lỗi khởi động: {exc} ({reason})", flush=True)
            return None
        child = Child(spec, proc, now, fh, reason)
        self._children[spec.name] = child
        self._last_spawn[spec.name] = now
        return child

    def reconcile(self, tasks: list[Task], now: datetime) -> list[str]:
        """Spawn các lượt planner báo tới hạn; trả tên đã spawn (task bị trần chặn để nhịp sau)."""
        return [t.spec.name for t in tasks if self.spawn(t.spec, now, t.reason) is not None]

    def tick_intraday(self, specs: list[JobSpec], now: datetime) -> list[str]:
        """Đồng hồ intraday của runner: đủ `interval_s` kể từ lần spawn trước VÀ không có con cùng
        tên đang sống. Con còn sống thì bỏ qua im lặng — nhịp 300 s mà job chạy lâu là chuyện thường,
        không phải sự cố đáng in ra."""
        started: list[str] = []
        for spec in specs:
            if self.alive(spec.name):
                continue
            last = self._last_spawn.get(spec.name)
            if last is not None and (now - last).total_seconds() < spec.interval_s:
                continue
            if self.spawn(spec, now, f"nhịp intraday {spec.interval_s}s") is not None:
                started.append(spec.name)
        return started

    def ensure_daemon(self, spec: JobSpec, now: datetime) -> bool:
        """`news --loop` phải luôn sống (§5.11). True nếu vừa spawn lại ở nhịp này."""
        if self.alive(spec.name):
            return False
        if self._daemon_last_exit is not None:
            waited = (now - self._daemon_last_exit).total_seconds()
            if waited < self._daemon_wait_s:
                return False
        reason = "daemon khởi động" if self._daemon_last_exit is None else f"daemon chạy lại sau {self._daemon_wait_s}s"
        return self.spawn(spec, now, reason) is not None

    def _daemon_died(self, now: datetime, lifetime_s: int) -> None:
        """Giãn cách 30 s nhân đôi tới trần 300 s khi daemon chết lại nhanh; sống quá 5 phút thì
        coi như lành, lần chết sau lại bắt đầu từ 30 s."""
        if lifetime_s > DAEMON_HEALTHY_S:
            self._daemon_backoff_s = DAEMON_BACKOFF_START_S
        self._daemon_last_exit = now
        self._daemon_wait_s = self._daemon_backoff_s
        self._daemon_backoff_s = min(self._daemon_backoff_s * 2, DAEMON_BACKOFF_MAX_S)

    # ---- thu hoạch -------------------------------------------------------
    def poll(self, now: datetime) -> list[Finished]:
        """Con nào vừa thoát: đóng log, in một dòng, trả bản ghi. Mỗi con chỉ báo cáo đúng một lần."""
        done: list[Finished] = []
        for name, child in self._children.items():
            if child.proc.returncode is not None:
                continue
            rc = child.proc.poll()
            if rc is None:
                continue
            seconds = int((now - child.started_at).total_seconds())
            child.log_fh.close()
            if child.spec.kind == "daemon":
                self._daemon_died(now, seconds)
            elif rc != 0:
                self._last_failed[name] = (rc, now)
            else:
                self._last_failed.pop(name, None)
            print(f"[{now:%Y-%m-%d %H:%M:%S}] {name} rc={rc} {seconds}s ({child.reason})", flush=True)
            done.append(Finished(name, rc, seconds, child.reason))
        return done

    # ---- dừng ------------------------------------------------------------
    def shutdown(self, *, grace_s: int = SHUTDOWN_GRACE_S, sleep=time.sleep) -> None:
        """Xin từng con tự tắt, chờ tối đa `grace_s`, còn sống thì giết. Không có `now` truyền vào
        (loop.py gọi từ nhánh tín hiệu) nên dòng tổng kết đọc thẳng `self.clock`."""
        live = self._live_children()
        for child in live:
            _stop_child(child.proc)
        waited = 0
        while waited < grace_s and any(c.proc.poll() is None for c in live):
            sleep(STOP_POLL_S)
            waited += STOP_POLL_S
        killed = 0
        for child in live:
            if child.proc.poll() is None:
                child.proc.kill()
                killed += 1
            child.log_fh.close()
        print(f"[{self.clock():%Y-%m-%d %H:%M:%S}] dừng {len(live)} tiến trình con, giết cứng {killed}", flush=True)

    # ---- dọn log ---------------------------------------------------------
    def prune_old_logs(self, now: datetime, keep_days: int = LOG_KEEP_DAYS) -> list[str]:
        """Xoá log có ngày TRONG TÊN quá `keep_days` ngày; trả tên đã xoá (khuôn `ingester.measure`).

        Cắt theo ngày trong tên chứ không theo `mtime`: log của một job chạy hiếm vẫn bị chạm mtime
        mỗi lần mở, còn ngày trong tên là bất biến kể cả sau khi copy cây log sang máy khác.
        """
        cutoff = today_vn(now) - timedelta(days=keep_days)
        removed: list[str] = []
        for p in sorted(self.log_dir.iterdir()):
            m = LOG_NAME_RE.fullmatch(p.name)
            if not (p.is_file() and m):
                continue
            try:
                d = datetime.strptime(m.group(1), "%Y%m%d").date()
            except ValueError:
                continue
            if d < cutoff:
                p.unlink()
                removed.append(p.name)
        return removed
