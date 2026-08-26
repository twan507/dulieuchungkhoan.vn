"""Orchestration ingester — spec §2.

Lượt này (trước gate AC3) chỉ mode `measure` chạy được; mode `run`/`reconcile`
hoàn thiện ở Task 16 của plan. Trình tự khởi động cứng: config → (run: assert_migrated
→ Redis) → catalog → socket. Đường xử lý packet mode run xem plan Task 16.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import websockets

from ingester import catalog as cat
from ingester import config, eio
from ingester.measure import MeasureWriter

log = logging.getLogger("ingester")
TZ = ZoneInfo("Asia/Ho_Chi_Minh")
SESSION_END_MEASURE = (15, 10)   # đo tới 15:10 — trọn đuôi phiên + PLO
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
        if not first:
            await asyncio.sleep(reconnect_delay_s)      # client gốc BVSC: 5 s
            if stop.is_set():
                break
            if on_reconnect:
                await asyncio.to_thread(on_reconnect)   # đồng bộ state từ REST
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


async def run(mode: str, minutes: float | None = None, out: str | None = None, d=None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if mode == "measure":
        return await _run_measure(minutes, out)
    # mode run/reconcile hoàn thiện ở Task 16 — GATE: cấm ghi thật trước phiên đo (spec §3.5)
    print(f"ingester: mode {mode!r} chưa được bật trong lượt này (gate phiên đo — spec §3.5)")
    return 4
