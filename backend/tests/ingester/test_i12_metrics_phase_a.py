"""Phase A spec spill §8/§10 — quan trắc phải có TRƯỚC khi cơ chế tràn tồn tại."""
import asyncio
import json
from collections import deque

from ingester.chwriter import COLUMNS, ChWriter, WARN_DEPTH_ROWS
from ingester.main import make_on_packet
from ingester.dedup import FrameDedup, Stamper
from ingester.normalize import Metrics, Normalized


def _n(seq: int) -> Normalized:
    row = {c: None for c in COLUMNS["trade"]}
    row["symbol"], row["seq"] = "ACV", seq
    return Normalized(table="trade", row=row, delta={}, symbol="ACV")


class _OkClient:
    def insert(self, table, data, column_names):
        pass


def test_metrics_set_overwrites_not_accumulates():
    m = Metrics()
    m.set("g", 7)
    m.set("g", 3)
    assert m.counters["g"] == 3        # gauge: ghi đè, khác inc


def test_insert_percentiles_hand_solved():
    w = ChWriter(_OkClient())
    w.insert_s = deque([0.010, 0.020, 0.030, 0.040, 0.100], maxlen=4096)
    p = w.insert_percentiles()
    # giải tay trên 5 mẫu đã sort: idx p50 = int(0.5*5)=2 → 0.030;
    # p95 = int(0.95*5)=4 → 0.100; p99 = min(4, int(0.99*5))=4 → 0.100
    assert p == {"p50": 0.030, "p95": 0.100, "p99": 0.100}


def test_insert_duration_recorded_per_call():
    w = ChWriter(_OkClient())
    w.add(_n(1))
    w.flush_once()
    assert len(w.insert_s) == 1 and w.insert_s[0] >= 0.0


def test_pending_depth_gauge_and_warning(caplog):
    class _Null:
        def insert(self, *a, **k):
            raise ConnectionError("chết")
    w = ChWriter(_Null(), sleep_fn=lambda s: None)
    for i in range(3):
        w.add(_n(i))
    with caplog.at_level("WARNING"):
        w.flush_once()
    assert w.metrics.counters["pending_depth_rows"] == 3
    assert w.metrics.counters["pending_depth_bytes"] == 3 * 497
    assert WARN_DEPTH_ROWS == 50_000
    assert "pending sâu" not in caplog.text        # 3 dòng < ngưỡng thì im


def test_frames_topic_counter_and_not_leader_dropped():
    metrics = Metrics()
    is_leader = asyncio.Event()                    # KHÔNG set — đường standby
    class _NoWriter:
        def add(self, n):
            raise AssertionError("standby không được add")
    on_packet = make_on_packet(_NoWriter(), metrics, FrameDedup(), Stamper(),
                               is_leader, asyncio.Queue())
    t_rec = {"TD": "10/08/2026", "FT": "13:08:56", "SB": "ACV", "FV": "100",
             "LC": "S", "FMP": "42100.0", "FCV": "1000.0", "SM": "74027",
             "AVO": "590000", "AVA": "24983210000.0"}
    raw = "42" + json.dumps(["t", {"a": "i", "d": [t_rec]}])
    on_packet(raw)
    assert metrics.counters["frames.t"] == 1
    assert metrics.counters["not_leader_dropped"] == 1
