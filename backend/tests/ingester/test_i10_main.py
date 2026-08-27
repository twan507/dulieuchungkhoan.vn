import asyncio
import json
import logging
from datetime import date

import websockets

import ingester.chwriter as chwriter_mod
import ingester.main as main_mod
from ingester.catalog import Catalog
from ingester.chwriter import ChWriter
from ingester.config import Config as IngesterConfig
from ingester.dedup import FrameDedup, Stamper
from ingester.main import (
    _merge_base_state,
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


def _make_on_packet(leader: bool = True):
    writer = ChWriter(_NullChClient())
    metrics = Metrics()
    dedup = FrameDedup()
    stamper = Stamper()
    is_leader = asyncio.Event()
    if leader:
        is_leader.set()
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
                          measure_dir=tmp_path, spill_dir=tmp_path)


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


# Danh mục boot: VFMVF1 chỉ có nền từ /quotes (spec §3.2) — /datafeed/instruments không
# trả mã này, nên nó phải SỐNG SÓT qua merge. CACB2602 là chứng quyền: ngoài catalog.symbols.
_CATALOG = Catalog(
    symbols=["ACV", "VFMVF1"],
    base_state={"ACV": {"open": "0"}, "VFMVF1": {"reference": "12000"}},
)
_A_CATALOG = Catalog(symbols=["A"], base_state={"A": {"open": "0"}})


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
        on_reconnect = make_on_reconnect(is_leader, sink, loop, _CATALOG)
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
        on_reconnect = make_on_reconnect(is_leader, sink, loop, _CATALOG)
        await asyncio.to_thread(on_reconnect)
        assert len(fetch_calls) == 1
        # fresh đè lên nền boot, lọc theo catalog.symbols (IMPORTANT 2 + 3 review cuối)
        assert sink.calls == [{"ACV": {"open": "1"}, "VFMVF1": {"reference": "12000"}}]
    asyncio.run(scenario())


def test_leader_state_watcher_refetches_fresh_base_each_leadership(monkeypatch):
    bases = iter([{"A": {"open": "1"}}, {"A": {"open": "2"}}])
    monkeypatch.setattr(main_mod.cat, "fetch_base_state", lambda: next(bases))

    async def scenario():
        is_leader = asyncio.Event()
        stop = asyncio.Event()
        sink = _FakeSink()
        task = asyncio.create_task(
            main_mod._leader_state_watcher(is_leader, sink, stop, _A_CATALOG, poll_s=0.01))
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


# --- vỏ bọc sails.io (đo thật 2026-08-26) ---------------------------------

REAL_T_PACKET = ('42["t",{"a":"i","d":[{"TD":"26/08/2026","FV":"1","LC":"B","FMP":"1942.3",'
                 '"FCV":"2.4","SM":"550316","AVO":"130589","AVA":"25356027540000.0",'
                 '"FT":"13:00:01","SB":"41I1G9000"}]}]')
REAL_T_PACKET_2REC = REAL_T_PACKET.replace(
    '"SB":"41I1G9000"}]', '"SB":"41I1G9000"},{"TD":"26/08/2026","FV":"2","LC":"S",'
    '"FMP":"1942.5","FCV":"2.6","SM":"550317","AVO":"130591","AVA":"25356031425000.0",'
    '"FT":"13:00:02","SB":"41I1G9000"}]')


def test_on_packet_unwraps_real_envelope():
    writer, metrics, on_packet = _make_on_packet()
    on_packet(REAL_T_PACKET)
    assert len(writer.buffers["trade"]) == 1
    assert metrics.counters.get("normalize_error") is None


def test_on_packet_handles_multi_record_envelope():
    writer, metrics, on_packet = _make_on_packet()
    on_packet(REAL_T_PACKET_2REC)
    assert len(writer.buffers["trade"]) == 2      # mỗi bản ghi trong `d` là một dòng


# --- review cuối ------------------------------------------------------------

def test_on_packet_standby_does_not_buffer_rows():
    """CRITICAL 3 review cuối — standby KHÔNG được tích dòng vào ChWriter.

    Trước fix, `writer.add(n)` chạy vô điều kiện: standby tích buffer tới 120 s rồi mới
    xả bỏ; nếu được thăng cấp trước mốc đó, phần còn lại bị flush = ghi ĐÔI đúng những
    dòng leader cũ đã ghi (lưới dedup block của ClickHouse không bắt được vì received_at
    khác). Standby vẫn phải chạy dedup/stamper để giữ seen-set ấm.
    """
    writer, metrics, on_packet = _make_on_packet(leader=False)
    on_packet(T_PACKET)
    assert all(len(b) == 0 for b in writer.buffers.values())
    assert len(writer.queue) == 0
    on_packet(T_PACKET)                              # seen-set vẫn ấm: frame lặp bị dedup
    assert metrics.counters.get("dup_dropped") == 1


def test_on_packet_leader_buffers_rows():
    writer, metrics, on_packet = _make_on_packet(leader=True)
    on_packet(T_PACKET)
    assert len(writer.buffers["trade"]) == 1


def test_merge_base_state_fresh_wins_boot_survives_outsiders_dropped():
    """IMPORTANT 2 + 3 review cuối.

    I2: `catalog.base_state` (có fallback ceiling/floor/reference từ /quotes cho mã kiểu
    VFMVF1) KHÔNG BAO GIỜ được dùng — boot lẫn reconnect đều gọi thẳng `fetch_base_state()`
    (chỉ /datafeed/instruments) ⇒ mã chỉ-có-ở-/quotes thủng state nền.
    I3: init_state ghi `rt:state:*` cho MỌI mã của /datafeed/instruments, gồm chứng quyền /
    trái phiếu / phái sinh — bốn khối loại CÓ CHỦ ĐÍCH của dự án.
    """
    boot = {"ACV": {"open": "1", "reference": "10"},
            "VFMVF1": {"ceiling": "0", "floor": "0", "reference": "12000"}}
    fresh = {"ACV": {"open": "2"},                 # tươi hơn → thắng
             "41I1G8000": {"open": "9"}}           # phái sinh → phải bị loại
    merged = _merge_base_state(boot, fresh, ["ACV", "VFMVF1"])
    assert merged == {"ACV": {"open": "2"},
                      "VFMVF1": {"ceiling": "0", "floor": "0", "reference": "12000"}}


# --- M-new-3: cửa sổ xả cuối phiên phải dài hơn ngân sách retry của ChWriter ---------
#
# Lúc đóng phiên, `write_loop` bị cancel nhưng THREAD `write_once` của nó có thể vẫn
# đang kẹt trong nhịp retry transient — tối đa `RETRY_BUDGET_S` giây. `_write_lock` làm
# mọi lời gọi `write_once` mới về NGAY (không chờ), nên vòng xả cuối phiên chỉ quay rỗng.
# Nếu ngân sách của nó ngắn hơn ngân sách retry thì nó bỏ cuộc trước khi đuôi phiên kịp
# ghi, và `reconcile()` chạy sau đó đọc kho thiếu dữ liệu ⇒ P2 giả + exit code 1.
#
# Mốc so sánh là hằng số của hợp đồng ChWriter, KHÔNG phải số của chính vòng xả.


class _StuckWriter:
    """Giả lập thread ghi cũ còn kẹt: `write_once` về ngay không làm gì, buffer chỉ sạch
    sau `clears_after_s` giây (theo đồng hồ giả)."""

    def __init__(self, clock, clears_after_s: float):
        self._clock, self._at = clock, clock() + clears_after_s
        self.buffers = {"trade": [["giữ chỗ"]]}
        self.queue = []
        self.head = []
        self.calls = 0

    def manage_once(self) -> None:
        pass

    def write_once(self, budget_s: float = 0) -> None:
        self.calls += 1
        if self._clock() >= self._at:
            self.buffers["trade"].clear()

    def clean(self) -> bool:
        return not any(self.buffers.values()) and not self.queue and not self.head


class _FakeClock:
    """Đồng hồ giả: mỗi lần `sleep(d)` được gọi thì nhảy đúng d giây."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    async def sleep(self, d: float) -> None:
        self.now += d


def test_drain_budget_strictly_exceeds_writer_retry_budget():
    """Bất biến thật, độc lập với con số cụ thể của cả hai bên."""
    assert main_mod.DRAIN_BUDGET_S > chwriter_mod.RETRY_BUDGET_S


def test_drain_writer_outlasts_chwriter_retry_budget():
    clock = _FakeClock()
    # Đúng biên: thread cũ ngốn TRỌN ngân sách retry rồi mới ghi xong. Lấy đúng hằng số
    # kia làm mốc, không cộng thêm biên nới tay — nới thì một chỉnh sửa thu hẹp
    # DRAIN_BUDGET_S vẫn lọt qua.
    stuck = _StuckWriter(clock, clears_after_s=chwriter_mod.RETRY_BUDGET_S)

    ok = asyncio.run(main_mod.drain_writer(stuck, sleep_fn=clock.sleep, clock=clock))

    assert ok is True
    assert not stuck.buffers["trade"]


def test_drain_writer_gives_up_and_reports_when_never_drains():
    clock = _FakeClock()
    stuck = _StuckWriter(clock, clears_after_s=float("inf"))

    ok = asyncio.run(main_mod.drain_writer(stuck, sleep_fn=clock.sleep, clock=clock))

    assert ok is False
    # Bỏ cuộc đúng lúc, không quay vô tận.
    assert clock.now - 1000.0 <= main_mod.DRAIN_BUDGET_S + 1.0


def test_drain_writer_backs_off_at_least_1s_between_failed_write_once_calls():
    """Review Opus, Finding 2 — trước fix, `drain_writer` ngủ 0,1 s giữa các nhịp CHƯA
    sạch rồi gọi thẳng `write_once`: với một server lỗi nhanh (transient trả về ngay,
    không tự ngủ bên trong `write_once`), đó là ~750 lần insert trong ngân sách 75 s thay
    vì ~7 lần như backoff mũ cũ (1->2->4->8->16 s). `stuck.calls` đếm số lần `write_once`
    được gọi — phải bị chặn dưới xấp xỉ một lần/giây, không phải gấp mười lần đó.
    """
    clock = _FakeClock()
    stuck = _StuckWriter(clock, clears_after_s=float("inf"))    # không bao giờ sạch

    ok = asyncio.run(main_mod.drain_writer(stuck, sleep_fn=clock.sleep, clock=clock))

    assert ok is False
    # sleep_fn giả nhảy đúng d khi được gọi -> số lần gọi write_once phải xấp xỉ số giây
    # trong ngân sách (nhịp >= 1s), không phải gấp mười (nhịp 0,1s cũ).
    assert stuck.calls <= main_mod.DRAIN_BUDGET_S + 2


def test_run_mode_returns_exit_3_when_clickhouse_unreachable(tmp_path, monkeypatch, capsys):
    """get_client nối ngay (autoconnect); nó phải nằm TRONG hợp đồng exit 3."""
    from clickhouse_connect.driver.exceptions import OperationalError

    cfg = IngesterConfig(clickhouse_url="fake://", redis_url="redis://x",
                         log_dir=tmp_path, measure_dir=tmp_path, spill_dir=tmp_path)
    monkeypatch.setattr(main_mod.config, "load", lambda need_db: cfg)

    def _boom(**kw):
        raise OperationalError("không nối được ClickHouse")

    monkeypatch.setattr(main_mod.clickhouse_connect, "get_client", _boom)
    rc = asyncio.run(run("run"))
    assert rc == 3
    assert "ingester:" in capsys.readouterr().err
