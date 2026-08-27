"""Orchestration ingester — spec §2.

Mode `measure` (đo, không ghi CH) và mode `run`/`reconcile` (ghi thật, spec §2.1)
cùng dùng chung `socket_loop`. Trình tự khởi động cứng mode run: config →
assert_migrated (trước khi nối socket) → Redis ping → catalog → tasks (init_state
khi giành được leader nằm trong task `_leader_state_watcher`, xem `_run_run`).
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import clickhouse_connect
from clickhouse_connect.driver.exceptions import ClickHouseError
import redis.asyncio as aioredis
import websockets

from core import ch_migrate
from ingester import catalog as cat
from ingester import config, eio
from ingester import leader as leader_mod
from ingester import state as state_mod
from ingester.chwriter import RETRY_BUDGET_S, ChWriter
from ingester.dedup import FrameDedup, Stamper, frame_key
from ingester.measure import MeasureWriter, prune_old
from ingester.normalize import (
    Metrics,
    NormalizeError,
    normalize,
    records_of,
    symbol_of,
)
from ingester.reconcile import reconcile

log = logging.getLogger("ingester")
TZ = ZoneInfo("Asia/Ho_Chi_Minh")
SESSION_END_MEASURE = (15, 10)   # đo tới 15:10 — trọn đuôi phiên + PLO
SESSION_END_RUN = (15, 5)        # ghi thật dừng đúng 15:05 — spec §2.1
EVENTS = {"i", "t", "o", "idx", "ptm"}     # 5 topic có normalize (spec §3.3)
ALL20 = ["i", "i_ol", "o10", "o_ol10", "o", "o_ol", "t", "t_ol", "tm", "e", "e_ol",
         "im", "e_im", "om", "idx", "pth", "ptm", "p", "u", "d"]


def measure_extra_topics(deriv_symbols: list[str]) -> list[str]:
    """20 topic × mã phái sinh + pth 3 sàn — quy trình đo roadmap §5.1."""
    out = [f"{p}:{s}" for s in deriv_symbols for p in ALL20]
    out += [f"pth:{f}" for f in cat.FLOORS]
    return out


async def socket_loop(url, topics, on_packet, stop: asyncio.Event,
                      on_reconnect=None, reconnect_delay_s: float = 5.0):
    first = True
    while not stop.is_set():
        is_reconnect = not first
        if is_reconnect:
            await asyncio.sleep(reconnect_delay_s)      # client gốc BVSC: 5 s
            if stop.is_set():
                break
        first = False
        try:
            async with websockets.connect(url, max_size=2 ** 22) as ws:
                ping_ms, timeout_ms = 25000, 60000
                ready = opened = False
                while not (ready and opened):           # đợi Open + "40"
                    pkt = eio.parse_packet(await asyncio.wait_for(ws.recv(), 10))
                    if isinstance(pkt, eio.Open):
                        ping_ms, timeout_ms = pkt.ping_interval_ms, pkt.ping_timeout_ms
                        opened = True
                    elif isinstance(pkt, eio.Control) and pkt.kind == "40":
                        ready = True
                ack = 0
                for batch in eio.chunk(topics, 100):
                    ack += 1
                    await ws.send(eio.build_subscribe(ack, batch))
                log.info("đã subscribe %d topic trong %d lô", len(topics), ack)

                # spec §3.1: nối lại → đăng ký lại TOÀN BỘ (xong ở trên) → mới gọi
                # /datafeed/instruments đồng bộ state. Chạy nền (không await) để không
                # chặn luồng nhận frame; chỉ khi đây thực sự là một lần NỐI LẠI.
                reconnect_task = (asyncio.create_task(asyncio.to_thread(on_reconnect))
                                  if is_reconnect and on_reconnect else None)

                async def pinger():
                    while True:
                        await asyncio.sleep(ping_ms / 1000)
                        await ws.send(eio.PING)

                async def closer():        # stop bật giữa chừng → đóng ws để recv thoát
                    await stop.wait()
                    await ws.close()

                ping_task = asyncio.create_task(pinger())
                closer_task = asyncio.create_task(closer())
                try:
                    while not stop.is_set():
                        raw = await asyncio.wait_for(ws.recv(), timeout_ms / 1000)
                        on_packet(raw)
                finally:
                    ping_task.cancel()
                    closer_task.cancel()
                    if reconnect_task is not None:
                        reconnect_task.cancel()
        except Exception as e:  # noqa: BLE001 — rớt là bình thường (2 lần/4 phút)
            if stop.is_set():
                break
            log.warning("socket rớt: %r — nối lại sau %ss", e, reconnect_delay_s)


def _measure_deadline(minutes: float | None) -> datetime:
    now = datetime.now(TZ)
    if minutes is not None:
        return now + timedelta(minutes=minutes)
    end = now.replace(hour=SESSION_END_MEASURE[0], minute=SESSION_END_MEASURE[1],
                      second=0, microsecond=0)
    return end if end > now else now + timedelta(minutes=5)


async def _run_measure(minutes: float | None, out: str | None) -> int:
    cfg = config.load(need_db=False)
    removed = prune_old(cfg.measure_dir)
    if removed:
        log.info("measure: dọn %d thư mục đo quá 30 ngày: %s", len(removed), removed)
    out_dir = Path(out) if out else cfg.measure_dir / datetime.now(TZ).strftime("%Y%m%d")
    catalog = await asyncio.to_thread(cat.build_catalog)
    deriv = await asyncio.to_thread(cat.fetch_derivative_symbols)
    topics = cat.topics(catalog) + measure_extra_topics(deriv)
    log.info("measure: %d mã CP/ETF, %d mã phái sinh, %d topic, ghi vào %s",
             len(catalog.symbols), len(deriv), len(topics), out_dir)
    writer = MeasureWriter(out_dir)
    stop = asyncio.Event()
    counters: dict[str, int] = {}

    def on_packet(raw: str) -> None:
        writer.write(int(time.time() * 1000), raw)
        pkt = eio.parse_packet(raw)
        name = pkt.name if isinstance(pkt, eio.Event) else type(pkt).__name__
        counters[name] = counters.get(name, 0) + 1

    async def log_loop():
        while not stop.is_set():
            await asyncio.sleep(60)
            log.info("measure counters: %s", dict(sorted(counters.items())))

    deadline = _measure_deadline(minutes)
    log.info("measure chạy tới %s", deadline.isoformat())

    async def timer():
        while datetime.now(TZ) < deadline and not stop.is_set():
            await asyncio.sleep(1)
        stop.set()

    tasks = [asyncio.create_task(t) for t in
             (socket_loop(eio.WSS_URL, topics, on_packet, stop), log_loop(), timer())]
    await asyncio.wait(tasks)
    writer.close()
    log.info("measure xong: %s", dict(sorted(counters.items())))
    return 0


def make_on_packet(writer: ChWriter, metrics: Metrics, dedup: FrameDedup, stamper: Stamper,
                   is_leader: asyncio.Event, redis_queue: asyncio.Queue):
    """Đường xử lý một packet mode run (docstring — plan Task 16 §Interfaces):

    raw → parse_packet → Event? name trong 5 topic? → frame_key + dedup.seen? bỏ
        → symbol_of → None? bỏ → stamper.stamp → normalize
        → NormalizeError? log+metric, bỏ
        → is_leader? writer.add + đẩy vào queue cho task redis_consumer gọi RedisSink.apply

    Standby KHÔNG tích dòng vào ChWriter (review cuối CRITICAL 3): buffer standby mà
    được thăng cấp giữa chừng sẽ flush lại đúng những dòng leader cũ đã ghi — ghi đôi,
    và lưới dedup block của ClickHouse không bắt được vì received_at khác. Standby vẫn
    chạy dedup + stamper để giữ seen-set/mốc thời gian ấm, sẵn sàng tiếp quản.
    """
    def on_packet(raw: str) -> None:
        pkt = eio.parse_packet(raw)
        if not isinstance(pkt, eio.Event) or pkt.name not in EVENTS:
            return
        event = pkt.name
        metrics.inc(f"frames.{event}")
        now = time.time()
        # Frame thật có vỏ sails.io: mỗi bản ghi trong `d` là MỘT dòng (đo 2026-08-26).
        for record in records_of(pkt.payload):
            if dedup.seen(frame_key(event, record), now):
                metrics.inc("dup_dropped")
                continue
            symbol = symbol_of(event, record)
            if symbol is None:
                metrics.inc("no_symbol_dropped")
                continue
            stamped_ms = stamper.stamp(symbol, int(now * 1000))
            try:
                n = normalize(event, record, stamped_ms, metrics)
            except NormalizeError as e:
                log.warning("normalize lỗi %s %s: %r", event, symbol, e)
                metrics.inc("normalize_error")
                continue
            if is_leader.is_set():
                writer.add(n)
                redis_queue.put_nowait(n)
            else:
                metrics.inc("not_leader_dropped")
    return on_packet


def _run_deadline(minutes: float | None, end_hm: tuple[int, int]) -> datetime:
    now = datetime.now(TZ)
    if minutes is not None:
        return now + timedelta(minutes=minutes)
    end = now.replace(hour=end_hm[0], minute=end_hm[1], second=0, microsecond=0)
    return end if end > now else now


def _print_reconcile(result) -> None:
    msg = f"reconcile: p1={len(result.p1)} p2={len(result.p2)} ok={result.ok}"
    print(msg)
    log.info(msg)
    for symbol, bar_vol, avo in result.p1:
        line = f"  P1 (đếm đôi) {symbol}: bar_vol={bar_vol} avo={avo}"
        print(line)
        log.error(line)         # P1 luôn là lỗi (spec §3.7) — mức error, khác P2
    for symbol, bar_vol, avo in result.p2:
        line = f"  P2 (mất quá ngưỡng) {symbol}: bar_vol={bar_vol} avo={avo}"
        print(line)
        log.warning(line)


def _merge_base_state(boot: dict, fresh: dict, symbols) -> dict:
    """State nền để nạp vào Redis: nền boot + bản tươi ĐÈ LÊN, lọc theo danh mục.

    - Nền boot là `catalog.base_state`: hợp nhất /datafeed/instruments VỚI fallback
      ceiling/floor/reference từ /quotes (spec §3.2). Mã kiểu VFMVF1 chỉ có ở /quotes,
      nếu chỉ dùng bản tươi (chỉ /datafeed/instruments) thì thủng state nền — trước
      review cuối, cả boot lẫn reconnect đều gọi thẳng `fetch_base_state()` nên nền này
      không bao giờ được dùng (IMPORTANT 2).
    - Bản tươi thắng vì có thể đã đổi so với lúc boot (giá tham chiếu phiên mới).
    - Lọc theo `catalog.symbols`: /datafeed/instruments trả CẢ chứng quyền, trái phiếu và
      phái sinh — bốn khối dự án loại CÓ CHỦ ĐÍCH, không được ghi `rt:state:*` (IMPORTANT 3).
    """
    keep = set(symbols)
    return {s: v for s, v in {**boot, **fresh}.items() if s in keep}


def make_on_reconnect(is_leader: asyncio.Event, sink: state_mod.RedisSink,
                      loop: asyncio.AbstractEventLoop, catalog: cat.Catalog):
    """`on_reconnect` cho `socket_loop` — CHỈ leader mới ghi Redis (spec §3.6).
    Standby không leader thì bỏ qua NGAY, kể cả không gọi REST (review wave 2 CRITICAL 2).
    Chạy trong thread riêng (socket_loop gọi qua `asyncio.to_thread`) — REST đồng bộ,
    rồi lịch lại `init_state` (bất đồng bộ) lên event loop chính và chờ xong.
    """
    def on_reconnect() -> None:
        if not is_leader.is_set():
            return
        fresh = cat.fetch_base_state()
        base = _merge_base_state(catalog.base_state, fresh, catalog.symbols)
        fut = asyncio.run_coroutine_threadsafe(sink.init_state(base), loop)
        fut.result(timeout=30)
    return on_reconnect


async def _leader_state_watcher(is_leader: asyncio.Event, sink: state_mod.RedisSink,
                                stop: asyncio.Event, catalog: cat.Catalog,
                                poll_s: float = 0.2) -> None:
    """init_state khi GIÀNH được leader — cả lần đầu lẫn tiếp quản giữa phiên
    (leader.run tự tranh/giữ khoá — hàm này chỉ bắt cạnh lên False→True).
    Luôn RE-FETCH base mới từ REST — KHÔNG dùng cache lúc boot vì có thể đã cũ
    (review wave 2 CRITICAL 2) — rồi merge lên nền boot và lọc (xem `_merge_base_state`)."""
    was_leader = False
    while not stop.is_set():
        now_leader = is_leader.is_set()
        if now_leader and not was_leader:
            fresh = await asyncio.to_thread(cat.fetch_base_state)
            base = _merge_base_state(catalog.base_state, fresh, catalog.symbols)
            await sink.init_state(base)
            log.info("đã init_state (giành leader)")
        was_leader = now_leader
        await asyncio.sleep(poll_s)


async def _run_reconcile(cfg: config.Config, d) -> int:
    client = clickhouse_connect.get_client(dsn=cfg.clickhouse_url)
    day = d or datetime.now(TZ).date()
    result = reconcile(client, day)
    _print_reconcile(result)
    return 1 if (result.p1 or result.p2) else 0


# Ngân sách xả cuối phiên phải DÀI HƠN ngân sách retry của ChWriter: lúc đóng phiên,
# thread `write_once` cũ có thể còn kẹt trong nhịp retry transient tới `RETRY_BUDGET_S`
# giây, mà `_write_lock` làm mọi lời gọi mới về ngay nên vòng dưới chỉ quay rỗng chờ nó.
# Trần cũ 3 s (30 vòng x 0,1 s) cạn trước ⇒ `reconcile()` đọc kho khi đuôi phiên chưa
# ghi xong ⇒ P2 giả + exit code 1 (M-new-3). Suy từ hằng số kia để hai bên không trôi lệch.
DRAIN_BUDGET_S = RETRY_BUDGET_S + 15.0


async def drain_writer(writer, budget_s: float = DRAIN_BUDGET_S,
                       sleep_fn=asyncio.sleep, clock=time.monotonic) -> bool:
    """Xả nốt đuôi phiên trước khi reconcile. True nếu `writer.clean()`.

    `write_loop` bị cancel ở tầng await nhưng THREAD `write_once` của nó vẫn chạy tiếp;
    `_write_lock` (review cuối IMPORTANT 4) làm lời gọi ở đây về ngay thay vì giẫm lên nó.
    """
    end = clock() + budget_s
    while True:
        await asyncio.to_thread(writer.manage_once)
        await asyncio.to_thread(writer.write_once)
        if writer.clean():
            return True
        if clock() >= end:
            log.error("hết %.0fs ngân sách xả mà buffer chưa sạch — phán quyết "
                      "reconcile bên dưới có thể sai lệch (thiếu đuôi phiên)", budget_s)
            return False
        # >= 1s giữa các nhịp CHƯA sạch: 0,1s cũ (đúng cho vòng xả bản v1, tick rồi mới
        # xả) giờ nghĩa khác — mỗi nhịp ở đây gọi thẳng `write_once`, nên một server đang
        # lỗi nhanh (transient tức thời) sẽ bị bắn ~600 lần insert trong ngân sách 75s thay
        # vì ~7 lần như backoff cũ (review Opus Finding 2). Nhịp sạch (return True ở trên)
        # không đi qua đường này nên không mất tốc độ phát hiện sạch.
        await sleep_fn(1.0)


# Mặc định `send_receive_timeout` của clickhouse_connect là 300 s — gấp 5 lần cả ngân
# sách retry 60 s, nên một lần thử treo là đã vượt trần trước khi kịp thử lại lần nào.
# 20 s cho phép ~3 lần thử nằm gọn trong ngân sách; ghi 5.000 dòng bình thường mất dưới
# một giây, nên chạm 20 s nghĩa là server đang thật sự có vấn đề.
CH_IO_TIMEOUT_S = 20


async def _run_run(cfg: config.Config, minutes: float | None) -> int:
    try:
        # get_client PHẢI nằm trong try: autoconnect nối ngay, nên ClickHouse sập lúc khởi
        # động ném ngay tại đây — ngoài try thì thoát ra traceback trần exit 1, đi vòng
        # qua đúng hợp đồng exit 3 dựng ra để báo lỗi khởi động.
        client = clickhouse_connect.get_client(dsn=cfg.clickhouse_url,
                                               send_receive_timeout=CH_IO_TIMEOUT_S)
        ch_migrate.assert_migrated(client)
    except (RuntimeError, ClickHouseError) as e:
        # Bắt cả lỗi ClickHouse: sự cố ACCESS_DENIED 2026-08-26 thoát ra dạng traceback
        # trần với exit 1, đi vòng qua đúng hợp đồng exit 3 dựng ra để báo lỗi khởi động.
        print(f"ingester: {e}", file=sys.stderr)
        log.error("assert_migrated thất bại: %s", e)
        return 3

    redis = aioredis.Redis.from_url(cfg.redis_url, decode_responses=True)
    if not await redis.ping():
        print("ingester: Redis không phản hồi ping", file=sys.stderr)
        log.error("Redis ping thất bại")
        return 3

    catalog = await asyncio.to_thread(cat.build_catalog)
    topics = cat.topics(catalog)
    log.info("run: %d mã, %d topic", len(catalog.symbols), len(topics))

    writer = ChWriter(client)
    sink = state_mod.RedisSink(redis)
    dedup = FrameDedup()
    stamper = Stamper()
    metrics = Metrics()
    is_leader = asyncio.Event()
    redis_queue: asyncio.Queue = asyncio.Queue()
    stop = asyncio.Event()
    leader_lock = leader_mod.LeaderLock(redis)
    loop = asyncio.get_running_loop()

    on_packet = make_on_packet(writer, metrics, dedup, stamper, is_leader, redis_queue)
    on_reconnect = make_on_reconnect(is_leader, sink, loop, catalog)

    deadline = _run_deadline(minutes, SESSION_END_RUN)
    log.info("run chạy tới %s", deadline.isoformat())

    async def session_timer():
        while datetime.now(TZ) < deadline and not stop.is_set():
            await asyncio.sleep(1)
        stop.set()

    async def redis_consumer():
        while True:
            n = await redis_queue.get()
            try:
                await sink.apply(n)
            except Exception:  # noqa: BLE001 — không để một lỗi apply giết cả consumer
                log.exception("redis apply lỗi")
            finally:
                redis_queue.task_done()

    async def manage_loop():
        # Vòng QUẢN chạy vô điều kiện (không chờ is_leader): standby không tích dòng nào
        # (on_packet chỉ add khi là leader — review cuối CRITICAL 3) nên buffer/queue của
        # nó luôn rỗng, cắt/gauge trên buffer rỗng vô hại. Quan trọng hơn: vòng quản KHÔNG
        # BAO GIỜ được chết vì nó không chạm ClickHouse (spec spill §2.1).
        while not stop.is_set():
            await asyncio.sleep(1.0)
            try:
                await asyncio.to_thread(writer.manage_once)
            except Exception:   # noqa: BLE001 — bất biến spec §2.1: vòng quản không được chết
                log.exception("manage_once lỗi không lường")
                writer.metrics.inc("spill_io_error")

    async def write_loop():
        # Chỉ leader ghi ClickHouse.
        while not stop.is_set():
            await asyncio.sleep(1.0)
            if is_leader.is_set():
                try:
                    await asyncio.to_thread(writer.write_once)
                except Exception:   # noqa: BLE001
                    log.exception("write_once lỗi không lường")
                    writer.metrics.inc("spill_io_error")

    async def log_loop():
        while not stop.is_set():
            await asyncio.sleep(60)
            log.info("run counters: %s", {**metrics.counters, **writer.metrics.counters})
            log.info("insert percentiles: %s", writer.insert_percentiles())

    tasks = [
        asyncio.create_task(leader_lock.run(is_leader)),
        asyncio.create_task(socket_loop(eio.WSS_URL, topics, on_packet, stop,
                                        on_reconnect=on_reconnect)),
        asyncio.create_task(manage_loop()),
        asyncio.create_task(write_loop()),
        asyncio.create_task(log_loop()),
        asyncio.create_task(session_timer()),
        asyncio.create_task(redis_consumer()),
        asyncio.create_task(_leader_state_watcher(is_leader, sink, stop, catalog)),
    ]
    socket_task = tasks[1]

    await stop.wait()
    await asyncio.wait_for(socket_task, 30)   # socket_loop tự thoát qua closer task nội bộ
    for t in tasks:
        if not t.done():
            t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    drained = True
    if is_leader.is_set():
        drained = await drain_writer(writer)
    await redis.aclose()

    # Client riêng cho đối chứng: 20 s là trần hợp lý cho một INSERT, nhưng reconcile
    # quét FULL OUTER JOIN trọn ngày nên cần trần mặc định của driver. Dùng chung client
    # ghi sẽ biến một phiên sạch thành exit 1 vì hết giờ đọc, dù dữ liệu đã vào đủ.
    rc_client = clickhouse_connect.get_client(dsn=cfg.clickhouse_url)
    try:
        result = reconcile(rc_client, datetime.now(TZ).date())
    finally:
        rc_client.close()
    _print_reconcile(result)
    if not drained:
        # Xả chưa sạch thì kho còn thiếu đuôi phiên, nên P2 ở trên có thể là báo động giả.
        # Nói thẳng ra thay vì để người đọc tưởng đây là kết luận toàn vẹn dữ liệu.
        print("reconcile: PHÁN QUYẾT KHÔNG ĐÁNG TIN — xả cuối phiên chưa sạch",
              file=sys.stderr)
    return 1 if (result.p1 or result.p2) else 0


async def run(mode: str, minutes: float | None = None, out: str | None = None, d=None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if mode == "measure":
        return await _run_measure(minutes, out)

    cfg = config.load(need_db=True)
    file_handler = logging.FileHandler(
        cfg.log_dir / f"ingester-{datetime.now(TZ):%Y%m%d}.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.getLogger().addHandler(file_handler)

    if mode == "reconcile":
        return await _run_reconcile(cfg, d)
    if mode == "run":
        return await _run_run(cfg, minutes)
    print(f"ingester: mode không biết: {mode!r}")
    return 4
