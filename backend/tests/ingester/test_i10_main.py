import asyncio
import json
import logging
from datetime import date

import websockets

import ingester.main as main_mod
from ingester.chwriter import ChWriter
from ingester.config import Config as IngesterConfig
from ingester.dedup import FrameDedup, Stamper
from ingester.main import (
    make_on_packet,
    make_on_reconnect,
    measure_extra_topics,
    run,
    socket_loop,
)
from ingester.normalize import Metrics
from ingester.reconcile import ReconcileResult

HANDSHAKE = '0{"sid":"x","upgrades":[],"pingInterval":25000,"pingTimeout":60000}'
T_PACKET = ('42["t",{"TD":"10/08/2026","FT":"13:08:56","SB":"ACV","FV":"100","LC":"S",'
            '"FMP":"42100.0","FCV":"1000.0","SM":"74027","AVO":"590000","AVA":"24983210000.0"}]')
T_PACKET_BAD_FV = T_PACKET.replace('"FV":"100"', '"FV":"abc"')
XYZ_PACKET = '42["xyz",{"SB":"ACV"}]'


def _args_of(sub_frame: str) -> list[str]:
    i = sub_frame.index("[")
    return json.loads(sub_frame[i:])[1]["data"]["args"]


def test_socket_loop_subscribes_receives_reconnects():
    async def scenario():
        state = {"connects": 0, "subs": []}
        got, resubbed = asyncio.Event(), asyncio.Event()

        async def handler(ws):
            state["connects"] += 1
            await ws.send(HANDSHAKE)
            await ws.send("40")
            msg = await ws.recv()                 # frame subscribe đầu
            state["subs"].append(msg)
            if state["connects"] == 1:
                await ws.send(T_PACKET)
                await asyncio.sleep(0.2)
                await ws.close()                  # ép rớt → client phải nối lại
            else:
                resubbed.set()
                await asyncio.sleep(5)

        packets = []

        def on_packet(raw):
            packets.append(raw)
            if raw == T_PACKET:
                got.set()

        reconnects = []
        async with websockets.serve(handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            stop = asyncio.Event()
            task = asyncio.create_task(socket_loop(
                f"ws://127.0.0.1:{port}/", ["t:ACV", "i:ACV"], on_packet, stop,
                on_reconnect=lambda: reconnects.append(1), reconnect_delay_s=0.1))
            await asyncio.wait_for(got.wait(), 5)
            await asyncio.wait_for(resubbed.wait(), 5)
            # spec §3.1: on_reconnect chạy NỀN (asyncio.create_task) sau khi đăng ký lại
            # TOÀN BỘ đã gửi xong — đợi task nền đó kịp chạy trước khi assert.
            await asyncio.sleep(0.2)
            stop.set()
            await asyncio.wait_for(task, 5)

        assert state["connects"] == 2                          # đã tự nối lại
        assert _args_of(state["subs"][0]) == ["t:ACV", "i:ACV"]
        assert _args_of(state["subs"][1]) == ["t:ACV", "i:ACV"]  # đăng ký lại TOÀN BỘ
        assert reconnects == [1]                               # đồng bộ lại state khi nối lại
        assert T_PACKET in packets
    asyncio.run(scenario())


def test_measure_extra_topics():
    t = measure_extra_topics(["41I1G8000"])
    assert "o10:41I1G8000" in t and "t_ol:41I1G8000" in t and "u:41I1G8000" in t
    assert len([x for x in t if x.endswith(":41I1G8000")]) == 20
    assert "pth:HOSE" in t and "pth:UPCOM" in t


class _NullChClient:
    """Client CH giả cho ChWriter — chỉ ghi nhận, không insert thật (test on_packet)."""

    def __init__(self):
        self.inserted = []

    def insert(self, table, data, column_names):
        self.inserted.append((table, list(data), column_names))


def _make_on_packet():
    writer = ChWriter(_NullChClient())
    metrics = Metrics()
    dedup = FrameDedup()
    stamper = Stamper()
    is_leader = asyncio.Event()
    queue: asyncio.Queue = asyncio.Queue()
    on_packet = make_on_packet(writer, metrics, dedup, stamper, is_leader, queue)
    return writer, metrics, on_packet


def test_on_packet_valid_t_frame_adds_to_writer():
    writer, metrics, on_packet = _make_on_packet()
    on_packet(T_PACKET)
    assert len(writer.buffers["trade"]) == 1


def test_on_packet_duplicate_frame_added_once():
    writer, metrics, on_packet = _make_on_packet()
    on_packet(T_PACKET)
    on_packet(T_PACKET)                              # frame giống hệt lần 2 → dedup bỏ
    assert len(writer.buffers["trade"]) == 1
    assert metrics.counters.get("dup_dropped") == 1


def test_on_packet_normalize_error_not_added():
    writer, metrics, on_packet = _make_on_packet()
    on_packet(T_PACKET_BAD_FV)                        # FV="abc" → NormalizeError
    assert len(writer.buffers["trade"]) == 0
    assert metrics.counters.get("normalize_error") == 1


def test_on_packet_unknown_event_dropped():
    writer, metrics, on_packet = _make_on_packet()
    on_packet(XYZ_PACKET)                             # "xyz" không nằm trong 5 topic
    assert all(len(b) == 0 for b in writer.buffers.values())
    assert metrics.counters == {}


def _fake_reconcile_config(tmp_path):
    return IngesterConfig(clickhouse_url="fake://", redis_url="", log_dir=tmp_path,
                          measure_dir=tmp_path)


def test_run_reconcile_mode_returns_0_when_no_p1_p2(tmp_path, monkeypatch):
    cfg = _fake_reconcile_config(tmp_path)
    monkeypatch.setattr(main_mod.config, "load", lambda need_db: cfg)
    monkeypatch.setattr(main_mod.clickhouse_connect, "get_client", lambda dsn: object())
    monkeypatch.setattr(main_mod, "reconcile", lambda client, d: ReconcileResult([], [], 5))
    rc = asyncio.run(run("reconcile", d=date(2026, 8, 20)))
    assert rc == 0


def test_run_reconcile_mode_returns_1_when_p1(tmp_path, monkeypatch):
    cfg = _fake_reconcile_config(tmp_path)
    monkeypatch.setattr(main_mod.config, "load", lambda need_db: cfg)
    monkeypatch.setattr(main_mod.clickhouse_connect, "get_client", lambda dsn: object())
    monkeypatch.setattr(main_mod, "reconcile",
                        lambda client, d: ReconcileResult([("XYZ", 10, 5)], [], 3))
    rc = asyncio.run(run("reconcile", d=date(2026, 8, 20)))
    assert rc == 1


def test_run_reconcile_mode_returns_1_when_p2(tmp_path, monkeypatch):
    cfg = _fake_reconcile_config(tmp_path)
    monkeypatch.setattr(main_mod.config, "load", lambda need_db: cfg)
    monkeypatch.setattr(main_mod.clickhouse_connect, "get_client", lambda dsn: object())
    monkeypatch.setattr(main_mod, "reconcile",
                        lambda client, d: ReconcileResult([], [("ABC", 3, 100)], 3))
    rc = asyncio.run(run("reconcile", d=date(2026, 8, 20)))
    assert rc == 1


# --- review wave 2 ---------------------------------------------------------

def test_print_reconcile_logs_p1_as_error_p2_as_warning(caplog):
    caplog.set_level(logging.INFO, logger="ingester")
    result = ReconcileResult([("AAA", 10, 5)], [("BBB", 3, 100)], 2)
    main_mod._print_reconcile(result)
    p1_records = [r for r in caplog.records if "AAA" in r.getMessage()]
    p2_records = [r for r in caplog.records if "BBB" in r.getMessage()]
    assert p1_records and p1_records[0].levelno == logging.ERROR    # P1 luôn là lỗi
    assert p2_records and p2_records[0].levelno == logging.WARNING


class _FakeSink:
    """RedisSink giả — chỉ ghi nhận init_state được gọi với base nào."""

    def __init__(self):
        self.calls: list[dict] = []

    async def init_state(self, base):
        self.calls.append(base)


def test_make_on_reconnect_standby_skips_fetch_and_init(monkeypatch):
    fetch_calls = []
    monkeypatch.setattr(main_mod.cat, "fetch_base_state",
                        lambda: fetch_calls.append(1) or {"ACV": {"open": "1"}})

    async def scenario():
        loop = asyncio.get_running_loop()
        is_leader = asyncio.Event()          # KHÔNG set — standby
        sink = _FakeSink()
        on_reconnect = make_on_reconnect(is_leader, sink, loop)
        await asyncio.to_thread(on_reconnect)
        assert fetch_calls == []             # standby: không gọi cả REST
        assert sink.calls == []
    asyncio.run(scenario())


def test_make_on_reconnect_leader_fetches_and_inits(monkeypatch):
    fetch_calls = []
    base = {"ACV": {"open": "1"}}
    monkeypatch.setattr(main_mod.cat, "fetch_base_state",
                        lambda: fetch_calls.append(1) or base)

    async def scenario():
        loop = asyncio.get_running_loop()
        is_leader = asyncio.Event()
        is_leader.set()                      # đang leader
        sink = _FakeSink()
        on_reconnect = make_on_reconnect(is_leader, sink, loop)
        await asyncio.to_thread(on_reconnect)
        assert len(fetch_calls) == 1
        assert sink.calls == [base]
    asyncio.run(scenario())


def test_leader_state_watcher_refetches_fresh_base_each_leadership(monkeypatch):
    bases = iter([{"A": {"open": "1"}}, {"A": {"open": "2"}}])
    monkeypatch.setattr(main_mod.cat, "fetch_base_state", lambda: next(bases))

    async def scenario():
        is_leader = asyncio.Event()
        stop = asyncio.Event()
        sink = _FakeSink()
        task = asyncio.create_task(
            main_mod._leader_state_watcher(is_leader, sink, stop, poll_s=0.01))
        is_leader.set()                                  # giành leader lần đầu
        await asyncio.sleep(0.05)
        assert sink.calls == [{"A": {"open": "1"}}]
        is_leader.clear()                                 # mất leader
        await asyncio.sleep(0.05)
        is_leader.set()                                   # tiếp quản giữa phiên
        await asyncio.sleep(0.05)
        assert sink.calls == [{"A": {"open": "1"}}, {"A": {"open": "2"}}]  # base MỚI, không cache
        stop.set()
        await asyncio.wait_for(task, 1)
    asyncio.run(scenario())
