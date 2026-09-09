"""loop.py: nối planner + runner với sổ thật (spec lát 13 §5.6, §5.8, §5.10). Ngày giả cố định 2026-09-09 (thứ 4)."""
import json
from datetime import datetime

import pytest
import sqlalchemy as sa

from core.clock import VN
from etl.scheduler import loop
from etl.scheduler.runner import Runner
from etl.scheduler.schedule import ALL_DAYS, JobSpec

JOB = "zz.loop.a"


def vn(d, h, mi):
    return datetime(2026, 9, d, h, mi, tzinfo=VN)


def _insert(engine, job, started, status="success", stats=None):
    with engine.begin() as c:
        c.execute(sa.text("INSERT INTO ops.etl_run (job, started_at, finished_at, status, stats)"
                          " VALUES (:j, :s, :s, :st, cast(:x AS jsonb))"),
                  {"j": job, "s": started, "st": status, "x": json.dumps(stats or {})})


@pytest.fixture()
def clean(migrated_engine):
    yield migrated_engine
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job LIKE 'zz.loop.%'"))


def test_resolve_log_dir_prefers_env_and_creates_it(tmp_path):
    p = loop.resolve_log_dir({"ETL_LOG_DIR": str(tmp_path / "x")})
    assert p == tmp_path / "x" and p.is_dir()
    assert loop.resolve_log_dir({}).as_posix().endswith("dlck-runtime/etl-logs")


def test_read_today_filters_by_vn_day_and_drops_intraday_subset_dry_run(clean):
    _insert(clean, JOB, vn(9, 8, 5))
    _insert(clean, JOB, vn(9, 9, 0), stats={"intraday": True})
    _insert(clean, JOB, vn(9, 9, 5), stats={"subset": True})
    _insert(clean, JOB, vn(9, 9, 10), stats={"dry_run": True})
    _insert(clean, JOB, vn(8, 23, 0))
    rows = loop.read_today(clean, vn(9, 10, 0), [JOB])
    assert [(r.job, r.started_at.astimezone(VN).hour, r.status) for r in rows] == [(JOB, 8, "success")]


def test_once_done_lists_jobs_that_ever_completed_a_pass(clean):
    _insert(clean, "zz.loop.bf", vn(5, 0, 5), stats={"pass_complete": True})
    _insert(clean, "zz.loop.nb", vn(5, 0, 5), stats={"pass_complete": False})
    done = loop.once_done(clean)
    assert "zz.loop.bf" in done and "zz.loop.nb" not in done


def test_summary_lines_count_last_24h_by_outcome(clean):
    _insert(clean, JOB, vn(9, 8, 5))
    _insert(clean, JOB, vn(9, 8, 6), "failed", {"guard_refused": True})
    _insert(clean, JOB, vn(9, 8, 7), "failed", {"guard_refused": True, "lock_busy": True})
    lines = loop.summary_lines(clean, vn(9, 9, 0))
    assert "zz.loop.a success=1 refused=2 lock_busy=1 failed=0 interrupted=0" in lines


class FakePopen:
    """Popen giả — `returncode` CHỈ do `poll()` đặt, đúng như `subprocess.Popen` thật.

    Con "đã thoát nhưng runner chưa thu hoạch" là trạng thái `exited` đã có giá trị mà `returncode`
    còn None: `runner.poll()` bỏ qua mọi con `returncode is not None` (đã báo cáo rồi, không báo hai
    lần), nên đặt thẳng `returncode` là mô phỏng một cái chết ĐÃ báo cáo, không phải cái chết mới.
    """

    def __init__(self):
        self.returncode = None
        self.exited = None                 # mã thoát thật, chưa ai hỏi tới

    def poll(self):
        if self.returncode is None:
            self.returncode = self.exited
        return self.returncode

    def terminate(self):
        self.exited = 130

    def send_signal(self, _s):
        self.exited = 130

    def kill(self):
        self.exited = -9

    def wait(self, timeout=None):
        return self.poll()


def test_run_once_spawns_daemon_intraday_then_due_marks_in_order(clean, tmp_path):
    schedule = [JobSpec("zz.loop.a", ("omo",), "daily", weekdays=ALL_DAYS, times=((8, 0),)),
                JobSpec("zz.loop.b", ("omo",), "daily", weekdays=ALL_DAYS, depends_on="zz.loop.a"),
                JobSpec("zz.loop.i", ("yahoo", "--intraday"), "intraday", weekdays=ALL_DAYS, interval_s=600),
                JobSpec("zz.loop.d", ("news", "--loop"), "daemon")]
    spawned = []
    runner = Runner(tmp_path, spawn_fn=lambda cmd, **kw: spawned.append(cmd[3]) or FakePopen(), clock=lambda: vn(9, 8, 16))
    out = loop.run_once(clean, runner, vn(9, 8, 16), schedule=schedule)
    assert out["spawned"] == ["zz.loop.d", "zz.loop.i", "zz.loop.a"] and out["finished"] == []
    _insert(clean, "zz.loop.a", vn(9, 8, 17))                       # cha success ⇒ con tới hạn ở nhịp sau
    runner._children["zz.loop.a"].proc.exited = 0                   # con thoát, nhịp sau mới thu hoạch
    out = loop.run_once(clean, runner, vn(9, 8, 18), schedule=schedule)
    assert out["spawned"] == ["zz.loop.b"] and [f.name for f in out["finished"]] == ["zz.loop.a"]
    assert spawned == ["news", "yahoo", "omo", "omo"]
