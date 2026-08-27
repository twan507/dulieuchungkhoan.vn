"""AC2 spec spill §12 — kịch bản sự cố dàn dựng: nạp N_ROWS dòng qua ChWriter, `docker
stop` ClickHouse GIỮA lúc nạp, `docker start` lại, chứng minh KHÔNG MẤT dòng nào (kho =
nạp + trùng-có-sổ) và RSS đỉnh không vượt ngân sách service-topology §7b (200 MB).

Chạy tay: RUN_CHAOS=1 uv run pytest tests/ingester/test_i17_chaos_ch_restart.py -s -q
Dán output (nạp/kho/trùng/RSS/counter spill) vào ledger — đây là phép nghiệm thu của cả
lát spill-to-disk, không phải một test đơn vị.
"""
import os
import socket
import subprocess
import threading
import time
import uuid

import psutil
import pytest

if not os.environ.get("RUN_CHAOS"):
    pytest.skip("chaos thủ công — RUN_CHAOS=1", allow_module_level=True)

from datetime import datetime
from decimal import Decimal

import clickhouse_connect  # noqa: E402

from ingester.normalize import Normalized  # noqa: E402
from tests.clickhouse.conftest import CH_CONF_DIR, IMAGE  # noqa: E402

N_ROWS = 200_000
RSS_BUDGET_BYTES = 200 * 2**20
_TRADE_TS = datetime(2026, 8, 27, 9, 15, 1)


def _valid_trade(seq: int) -> Normalized:
    """Dòng THẬT cho insert vào ClickHouse thật — KHÔNG dùng stub `_trade_normalized`
    của test_i08 (nó để `ts`/`received_at` là None, chỉ an toàn với client GIẢ không bao
    giờ serialize). Ở đây `ts` là `DateTime('Asia/Ho_Chi_Minh')` NOT NULL theo schema
    database/clickhouse/versions/0002_rt_schema.sql — None sẽ ném AttributeError phía
    client lúc serialize, bị `_is_deterministic()` xếp nhầm là transient (không phải
    `DataError`, không mã lỗi) nên retry vô hạn, không bao giờ xả sạch. Mỗi dòng chỉ khác
    nhau ở `seq` — đủ để đếm chính xác nạp/kho/trùng."""
    row = {
        "symbol": "ACV",
        "ts": _TRADE_TS,
        "seq": seq,
        "price": Decimal("42100.00"),
        "volume": 100,
        "side": "S",
        "change": Decimal("0.00"),
        "cum_volume": seq,
        "cum_value": Decimal("1000.00"),
        "received_at": _TRADE_TS,
    }
    return Normalized(table="trade", row=row, delta={}, symbol="ACV")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture()
def chaos_container_name():
    return f"ch-chaos-{uuid.uuid4().hex[:8]}"


@pytest.fixture()
def chaos_ch(chaos_container_name, tmp_path_factory):
    """Container ClickHouse ephemeral RIÊNG (không phải fixture `ch`/`migrated` dùng
    chung) — test này docker stop/start giữa chừng, dùng chung sẽ phá các test khác chạy
    song song trong cùng phiên pytest. Chép cách dựng + migrate từ
    tests/clickhouse/conftest.py, chỉ đổi tên container."""
    name = chaos_container_name
    backup_dir = tmp_path_factory.mktemp("ch-chaos-backups")
    port = _free_port()
    cmd = [
        "docker", "run", "-d", "--name", name,
        "--ulimit", "nofile=262144:262144",
        "-e", "CLICKHOUSE_PASSWORD=testpass",
        "-e", "CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1",
        "-e", "TZ=Asia/Ho_Chi_Minh",
        "-v", f"{CH_CONF_DIR / 'backups.xml'}:/etc/clickhouse-server/config.d/backups.xml:ro",
        "-v", f"{backup_dir}:/backups",
        "-p", f"127.0.0.1:{port}:8123",
        IMAGE,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    url = f"http://default:testpass@127.0.0.1:{port}"
    client = None
    try:
        for _ in range(60):
            try:
                client = clickhouse_connect.get_client(dsn=url)
                client.command("SELECT 1")
                break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("ClickHouse test container không lên sau 60s")
        from core import ch_migrate
        ch_migrate.upgrade(client)
        # Gắn DSN thẳng vào client — test cần dựng lại client MỚI sau docker start (client
        # cũ có thể còn giữ socket chết trong connection pool, xem controller amendment).
        client._chaos_dsn = url
        yield client
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)


def _try_reconnect(w, dsn: str) -> bool:
    """Thử dựng CLIENT MỚI và gắn vào writer nếu nó `SELECT 1` được. Trả True nếu
    `w.client` đang là một client sống (dù cũ hay mới) — False nếu vẫn chết.
    Không đắt: chỉ gọi ở các mốc kiểm tra (mỗi 500 dòng), không phải mỗi insert."""
    try:
        w.client.command("SELECT 1")
        return True
    except Exception:
        pass
    try:
        candidate = clickhouse_connect.get_client(dsn=dsn)
        candidate.command("SELECT 1")
        w.client = candidate
        return True
    except Exception:
        return False


def test_docker_stop_mid_feed_zero_loss(chaos_ch, chaos_container_name, tmp_path):
    from ingester.chwriter import ChWriter
    from ingester.spill import SpillStore

    dsn = chaos_ch._chaos_dsn
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire()
    s.scan()
    w = ChWriter(chaos_ch, spill=s)

    rss_peak = 0
    sampling = True

    def _sample():
        nonlocal rss_peak
        p = psutil.Process()
        while sampling:
            rss_peak = max(rss_peak, p.memory_info().rss)
            time.sleep(1.0)

    threading.Thread(target=_sample, daemon=True).start()

    stopped = False
    started = False
    reconnected = True    # client ban đầu (từ fixture) đã sống
    for i in range(N_ROWS):                     # nạp qua add() — số dòng biết trước
        w.add(_valid_trade(i))
        if i % 500 == 0:
            w.manage_once()
            w.write_once()
            if started and not reconnected:
                reconnected = _try_reconnect(w, dsn)
        if i == N_ROWS // 3 and not stopped:
            subprocess.run(["docker", "stop", chaos_container_name], check=True)
            stopped = True
        if i == 2 * N_ROWS // 3 and not started:
            subprocess.run(["docker", "start", chaos_container_name], check=True)
            started = True
            reconnected = False    # từ đây thử dựng lại client mỗi mốc kiểm tra

    deadline = time.time() + 600
    while not w.clean() and time.time() < deadline:
        w.manage_once()
        w.write_once()
        if not reconnected:
            reconnected = _try_reconnect(w, dsn)
        time.sleep(0.2)

    sampling = False
    assert w.clean(), "xả không sạch trong 10 phút"

    # Đếm bằng client MỚI, DSN gốc — client trong `w` có thể đã bị hoán trong lúc chaos.
    verify_client = clickhouse_connect.get_client(dsn=dsn)
    total = verify_client.query("SELECT count() FROM rt.trade").result_rows[0][0]
    dup = total - N_ROWS
    assert dup >= 0, f"MẤT {-dup} dòng"        # đẳng thức spec AC2: kho = nạp + trùng-có-sổ

    counters_snapshot = dict(w.metrics.counters)
    print(f"\nAC2: nạp {N_ROWS}, kho {total}, trùng {dup}, "
          f"RSS đỉnh {rss_peak / 2**20:.1f} MB, counters={counters_snapshot}")

    assert rss_peak <= RSS_BUDGET_BYTES         # ngân sách service-topology §7b
