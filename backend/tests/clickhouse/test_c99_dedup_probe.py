"""Phép kiểm một-lần spec spill §9 — chạy tay: RUN_PROBE=1 uv run pytest
tests/clickhouse/test_c99_dedup_probe.py -s -q
Kết quả DÁN vào spec §9 + ledger. Đơn vị cửa sổ là BLOCK (spec §7)."""
import os
import pickle
import subprocess
import tempfile
import time
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import clickhouse_connect
import pytest

if not os.environ.get("RUN_PROBE"):
    pytest.skip("probe thủ công — đặt RUN_PROBE=1 để chạy", allow_module_level=True)

from tests.clickhouse.conftest import CH_CONF_DIR, IMAGE, _free_port  # noqa: E402

TZ = ZoneInfo("Asia/Ho_Chi_Minh")
COLS = ["symbol", "ts", "seq", "price", "volume", "side", "change",
        "cum_volume", "cum_value", "received_at"]

# Trần cứng docker của hồ sơ VPS — khớp deploy/infra/docker-compose.vps.yml service clickhouse
# (mem_limit: 2600m, memswap_limit: 2600m, cpus: 2.0).
VPS_MEM_LIMIT = "2600m"
VPS_CPUS = "2.0"


def _rows(sym: str, n: int, seq0: int = 1) -> list[list]:
    ts = datetime(2026, 8, 20, 9, 15, 1, tzinfo=TZ)
    return [[sym, ts, seq0 + i, Decimal("10.00"), 100, "B", Decimal("0.00"),
             100 * (i + 1), Decimal("1000.00"), ts] for i in range(n)]


def _count(c, sym: str) -> int:
    return c.query(f"SELECT count() FROM rt.trade WHERE symbol='{sym}'").result_rows[0][0]


def test_probe_dedup_and_pickle_size(migrated):
    c = migrated
    # 1a — trong cửa sổ, QUA ĐƯỜNG ĐĨA: pickle roundtrip không được đổi hash block
    b = _rows("PRB1", 100)
    c.insert("rt.trade", b, column_names=COLS)
    b2 = pickle.loads(pickle.dumps(("trade", b), protocol=5))[1]
    c.insert("rt.trade", b2, column_names=COLS)
    n_1a = _count(c, "PRB1")
    print(f"\nPROBE 1a (pickle roundtrip, insert lại ngay): count={n_1a} "
          f"(100 = nuốt/hash giữ nguyên; 200 = KHÔNG dedup)")

    # 1b — NGOÀI cửa sổ theo block: chen >100 block khác cùng bảng rồi insert lại
    x = _rows("PRB2", 50)
    c.insert("rt.trade", x, column_names=COLS)
    for i in range(105):
        c.insert("rt.trade", _rows("PRBF", 1, seq0=10_000 + i), column_names=COLS)
    c.insert("rt.trade", x, column_names=COLS)
    n_1b = _count(c, "PRB2")
    print(f"PROBE 1b (chen 105 block rồi insert lại): count={n_1b} "
          f"(100 = NHÂN ĐÔI ngoài cửa sổ — đúng dự đoán spec; 50 = vẫn nuốt)")

    # 1c — chiều thời gian: có giới hạn theo GIÂY không (spec §9: đo, không suy)
    y = _rows("PRB3", 10)
    c.insert("rt.trade", y, column_names=COLS)
    import time; time.sleep(130)
    c.insert("rt.trade", y, column_names=COLS)
    n_1c = _count(c, "PRB3")
    print(f"PROBE 1c (chờ 130s, KHÔNG chen block): count={n_1c} "
          f"(10 = cửa sổ không co theo giây; 20 = có chiều thời gian)")

    # 2 — kích thước pickle một block 5.000 dòng (đầu vào trần đĩa §2.5)
    big = _rows("PRB4", 5000)
    size = len(pickle.dumps(("trade", big), protocol=5))
    print(f"PROBE 2  (pickle 5000 dòng trade): {size} bytes ≈ {size/1024:.0f} KiB")

    for s in ("PRB1", "PRB2", "PRB3", "PRBF"):
        c.command(f"ALTER TABLE rt.trade DELETE WHERE symbol='{s}'")
    assert n_1a in (100, 200) and n_1b in (50, 100)   # chống đọc nhầm cột


# --- Bổ sung theo Ruling PF-1: probe timing insert, hai hồ sơ tài nguyên ---
#
# Ruling T2-1 của controller: KHÔNG dừng/khởi động lại compose dev để đổi hồ sơ (probe
# dùng container test ephemeral, overlay compose không đụng tới nó; và trỏ probe vào CH
# dev thật sẽ ghi rác vào kho thật). Thay vào đó, fixture `vps_ch` dưới đây tự dựng MỘT
# container CH ephemeral riêng, giống hệt cách `ch`/`migrated` trong conftest.py dựng,
# cộng thêm: mount deploy/infra/clickhouse/memory-vps.xml (hồ sơ RAM hẹp) và trần
# memory/cpu docker khớp deploy/infra/docker-compose.vps.yml.

@pytest.fixture(scope="session")
def vps_ch(tmp_path_factory):
    """Container CH ephemeral RIÊNG — hồ sơ RAM/CPU hẹp như VPS thật, không đụng CH dev."""
    backup_dir = tmp_path_factory.mktemp("ch-vps-backups")
    name = f"ch-vps-probe-{uuid.uuid4().hex[:8]}"
    port = _free_port()
    cmd = [
        "docker", "run", "-d", "--name", name,
        "--ulimit", "nofile=262144:262144",
        "-e", "CLICKHOUSE_PASSWORD=testpass",
        "-e", "CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1",
        "-e", "TZ=Asia/Ho_Chi_Minh",
        "-v", f"{CH_CONF_DIR / 'backups.xml'}:/etc/clickhouse-server/config.d/backups.xml:ro",
        "-v", f"{backup_dir}:/backups",
        "-v", f"{CH_CONF_DIR / 'memory-vps.xml'}:/etc/clickhouse-server/config.d/memory-vps.xml:ro",
        "--memory", VPS_MEM_LIMIT, "--memory-swap", VPS_MEM_LIMIT, "--cpus", VPS_CPUS,
        "-p", f"127.0.0.1:{port}:8123",
        IMAGE,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    url = f"http://default:testpass@127.0.0.1:{port}"
    client = None
    def _dump_diag():
        status = subprocess.run(["docker", "inspect", name, "--format",
                                  "{{.State.Status}} ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}}"],
                                 capture_output=True, text=True).stdout
        diag_dir = Path(tempfile.mkdtemp(prefix="ch-vps-diag-"))
        subprocess.run(["docker", "cp", f"{name}:/var/log/clickhouse-server/clickhouse-server.err.log",
                         str(diag_dir / "err.log")], capture_output=True, text=True)
        errtext = ""
        errfile = diag_dir / "err.log"
        if errfile.exists():
            errtext = errfile.read_text(encoding="utf-8", errors="replace")[-3000:]
        print(f"\n[DEBUG-VPS] container state: {status}")
        print(f"[DEBUG-VPS] err.log tail:\n{errtext}")

    try:
        # 180s (thay vì 60s như fixture `ch` DEV): container này khởi động NGAY sau khi
        # container DEV vừa hứng 400 insert liền (benchmark timing) — Docker Desktop trên
        # máy dev có thể vẫn còn bận flush/merge nền của DEV khi ta xin cấp thêm container
        # bị trói CPU 2 lõi/RAM 2,6 GiB. Đo thật (2026-08-27): 60s không đủ, cần dư ra.
        # Thoát SỚM nếu container đã chết hẳn (crash cấu hình, ~1s) — khỏi phải đợi hết 180s.
        for _ in range(180):
            state = subprocess.run(["docker", "inspect", name, "--format", "{{.State.Status}}"],
                                    capture_output=True, text=True).stdout.strip()
            if state == "exited":
                _dump_diag()
                raise RuntimeError("ClickHouse hồ sơ VPS thoát ngay sau khi start (xem log trên)")
            try:
                client = clickhouse_connect.get_client(dsn=url)
                client.command("SELECT 1")
                break
            except Exception:
                time.sleep(1)
        else:
            _dump_diag()
            raise RuntimeError("ClickHouse hồ sơ VPS không lên sau 180s")
        from core import ch_migrate
        ch_migrate.upgrade(client)
        yield client
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)


def _insert_timing_probe(client, label: str) -> None:
    """Insert 200 block 5.000 dòng (PRBT) + 200 block 50 dòng (PRBS), đo p50/p95/p99."""
    big_times = []
    for i in range(200):
        block = _rows("PRBT", 5000, seq0=i * 5000 + 1)
        t0 = time.perf_counter()
        client.insert("rt.trade", block, column_names=COLS)
        big_times.append(time.perf_counter() - t0)

    small_times = []
    for i in range(200):
        block = _rows("PRBS", 50, seq0=i * 50 + 1)
        t0 = time.perf_counter()
        client.insert("rt.trade", block, column_names=COLS)
        small_times.append(time.perf_counter() - t0)

    print(f"\n=== PROBE insert-timing [{label}] ===")
    for xs, n_rows, tag in ((big_times, 5000, "PRBT"), (small_times, 50, "PRBS")):
        xs_sorted = sorted(xs)
        pick = lambda q: xs_sorted[min(len(xs_sorted) - 1, int(q * len(xs_sorted)))]  # noqa: E731
        p50, p95, p99 = pick(0.50), pick(0.95), pick(0.99)
        print(f"PROBE timing [{label}] {tag} block={n_rows} dòng (n={len(xs_sorted)} inserts): "
              f"p50={p50*1000:.1f}ms p95={p95*1000:.1f}ms p99={p99*1000:.1f}ms "
              f"~{n_rows/p95:.0f} dòng/giây tại p95")

    client.command("ALTER TABLE rt.trade DELETE WHERE symbol IN ('PRBT','PRBS')")


def test_probe_insert_timing_dev(migrated):
    _insert_timing_probe(migrated, "DEV profile")
    print("Lưu ý: số DEV ở trên — xem khối PROBE timing [VPS profile] cùng output "
          "(test_probe_insert_timing_vps, cùng lượt chạy này) để lấy số điền K.")


def test_probe_insert_timing_vps(vps_ch):
    _insert_timing_probe(vps_ch, "VPS profile")
