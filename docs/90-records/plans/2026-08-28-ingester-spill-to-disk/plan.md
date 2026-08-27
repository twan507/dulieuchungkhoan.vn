# Plan — Hàng đợi ghi có trần, tràn ra đĩa

> **For agentic workers:** REQUIRED SUB-SKILL: dùng superpowers:subagent-driven-development (khuyến nghị) hoặc superpowers:executing-plans, từng task một. Bước dùng checkbox (`- [ ]`).

**Goal:** đóng chỗ hở `pending` không trần của ingester — RAM có trần cứng theo dòng, phần vượt tràn ra đĩa (pickle từng block, hai loại `-r`/`-n`), phát lại trong phiên có tiết lưu, và chứng minh "không mất dòng nào" bằng bộ đếm `d[]` độc lập.

**Architecture:** tách vòng flush hiện tại thành **vòng quản** (luôn chạy, không I/O ClickHouse: cắt buffer, gauge, chuyển chế độ, ghi đĩa) và **vòng ghi** (insert có ngân sách theo lời gọi, hợp đồng `done|transient|poison`). Hai cửa vào chế độ đĩa: vượt trần N dòng, hoặc một block cạn 60 s transient (thay cho drop). `SpillStore` sở hữu thư mục phẳng bằng OS exclusive lock.

**Tech Stack:** Python 3.12 · clickhouse_connect · pickle protocol 5 · pytest với ClickHouse/Redis container thật (fixture sẵn có).

**Spec:** [spec.md](spec.md) — đọc trước khi làm bất kỳ task nào. Brief số đo: [brief.md](brief.md).

## Global Constraints

- Chạy lệnh từ `backend/`: `uv run pytest tests/ingester/<file> -q`. Test DB cần env như [database/README.md](../../../../database/README.md) mục "Cách chạy" (`TEST_DATABASE_URL` cho fixture Postgres — không cần ở đây; fixture CH/Redis tự dựng container, chỉ cần Docker chạy). Luôn `PYTHONIOENCODING=utf-8`.
- **TDD đỏ trước xanh từng seam** (CLAUDE.md §4.5): mỗi bước test phải chạy và THẤY đỏ trước khi viết code.
- **Subagent: Sonnet mặc định, cấm Fable, chỉ định model tường minh** (CLAUDE.md §4.1). Artifact tạm ở scratchpad ngoài repo; cấm tạo `.superpowers/` trong repo.
- Commit nhỏ theo task, Conventional Commits, message tiếng Anh. Nhánh: `feat/ingester-spill-phase-a` (Task 1–2) rồi `feat/ingester-spill` (Task 4+).
- Sổ thực thi: `ledger.md` cùng thư mục plan này — ghi output thật từng task.
- Hằng số `N_CAP_ROWS = 100_000` · `K_REPLAY_ROWS = 20_000` · `SPILL_CAP_BYTES = 10 * 2**30` là **giá trị tạm theo công thức spec §2.5**; Task 3 (gate đo) PHẢI cập nhật theo số đo trước khi Task 6 bắt đầu — cấm sửa ngược lại sau đó mà không có số đo mới.
- Đơn vị cửa sổ dedup ClickHouse là **BLOCK** (100 block/bảng — spec §7), không phải giây. Mọi test/probe viết theo block.

## Bản đồ file

| File | Vai trò |
|---|---|
| `backend/ingester/spill.py` *(mới)* | `SpillStore` — hàng đợi block trên đĩa: lock sở hữu, seq bền, ghi `O_EXCL`+rename, đọc FIFO + gộp `-n`, xoá sau insert, trần byte |
| `backend/ingester/pipeline.py` *(mới)* | `process_record()` — một bản ghi qua dedup→symbol→stamp→normalize; nguồn sự thật CHUNG cho mode run và bộ đếm `d[]` |
| `backend/ingester/measure_count.py` *(mới)* | Bộ đếm `d[]` offline đọc bản đo, cắt cửa sổ `--from/--to`, so với kho |
| `backend/ingester/chwriter.py` *(sửa lớn)* | ChWriter v2: deque toàn cục, `manage_once`/`write_once`, chế độ đĩa, K, timing |
| `backend/ingester/main.py` *(sửa)* | hai loop thay `flush_loop`, counter mới, `drain_writer` biết đĩa, replay nợ + reconcile ngày nợ lúc khởi động |
| `backend/ingester/config.py` *(sửa)* | thêm `spill_dir` (`INGESTER_SPILL_DIR`, mặc định `dlck-runtime/spill`) |
| `backend/ingester/__main__.py` *(sửa)* | mode `--count` |
| `backend/tests/ingester/test_i12_metrics_phase_a.py` *(mới)* | Task 1 |
| `backend/tests/clickhouse/test_c99_dedup_probe.py` *(mới)* | Task 2 — probe thủ công, gate bằng env `RUN_PROBE` |
| `backend/tests/ingester/test_i13_spill_store.py` *(mới)* | Task 4 |
| `backend/tests/ingester/test_i14_writer_disk_mode.py` *(mới)* | Task 5–7 |
| `backend/tests/ingester/test_i15_recovery_drain.py` *(mới)* | Task 8 |
| `backend/tests/ingester/test_i16_measure_count.py` *(mới)* | Task 9 |
| `backend/tests/ingester/test_i17_chaos_ch_restart.py` *(mới)* | Task 10 — gate env `RUN_CHAOS` |

---

# PHASE A — đo trước (merge riêng, chạy một phiên thật, rồi mới Phase B)

### Task 1: Metrics nền — gauge độ sâu, timing insert, hai counter còn thiếu

**Files:**
- Modify: `backend/ingester/normalize.py` (thêm `Metrics.set`)
- Modify: `backend/ingester/chwriter.py` (timing + gauge + WARN trong `flush_once`)
- Modify: `backend/ingester/main.py` (counter `frames.<topic>` + `not_leader_dropped` trong `make_on_packet`; log percentiles trong `log_loop`)
- Test: `backend/tests/ingester/test_i12_metrics_phase_a.py`

**Interfaces:**
- Produces: `Metrics.set(key: str, value: int) -> None` · `ChWriter.insert_s: deque[float]` · `ChWriter.insert_percentiles() -> dict` (khoá `p50/p95/p99`, giây float) · counter `pending_depth_rows`, `pending_depth_bytes` (gauge qua `set`), `frames.<event>`, `not_leader_dropped` · hằng `WARN_DEPTH_ROWS = 50_000` trong `chwriter.py`.
- Consumes: `Metrics`, `ChWriter`, `make_on_packet` hiện hành (không đổi hành vi ghi).

- [ ] **Bước 1: viết test đỏ**

```python
# backend/tests/ingester/test_i12_metrics_phase_a.py
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
```

- [ ] **Bước 2: chạy thấy đỏ** — `uv run pytest tests/ingester/test_i12_metrics_phase_a.py -q` → FAIL (`ImportError: WARN_DEPTH_ROWS` / `AttributeError: set`).

- [ ] **Bước 3: code tối thiểu**

`normalize.py` — trong `class Metrics` thêm:

```python
    def set(self, key: str, value: int) -> None:
        """Gauge: ghi đè giá trị hiện tại (khác inc — không cộng dồn)."""
        self.counters[key] = value
```

`chwriter.py` — đầu file thêm `from collections import deque` (đã có) và hằng:

```python
ROW_BYTES_EST = 497          # đo brief §3.2 — KHÔNG getsizeof trên đường chạy
WARN_DEPTH_ROWS = 50_000     # brief §5.1 đòi ngưỡng cảnh báo kèm metric
```

Trong `__init__` thêm `self.insert_s: deque[float] = deque(maxlen=4096)`. Trong `_write_block`, bọc riêng lời gọi insert:

```python
            t0 = self.clock()
            try:
                self.client.insert(f"rt.{table}", block, column_names=COLUMNS[table])
            except Exception as e:  # noqa: BLE001 — phân loại rồi xử lý theo hợp đồng
                self.insert_s.append(self.clock() - t0)
                ...   # phần except giữ NGUYÊN nội dung cũ, chỉ thụt vào try mới
            else:
                self.insert_s.append(self.clock() - t0)
                self.metrics.inc(f"rows.{table}", len(block))
                return
```

Thêm method:

```python
    def insert_percentiles(self) -> dict:
        xs = sorted(self.insert_s)
        if not xs:
            return {}
        pick = lambda q: xs[min(len(xs) - 1, int(q * len(xs)))]  # noqa: E731
        return {"p50": pick(0.50), "p95": pick(0.95), "p99": pick(0.99)}
```

Đầu `flush_once` (sau khi cắt buffer, trước vòng ghi):

```python
            depth = sum(len(b) for q in self.pending.values() for b in q)
            self.metrics.set("pending_depth_rows", depth)
            self.metrics.set("pending_depth_bytes", depth * ROW_BYTES_EST)
            if depth > WARN_DEPTH_ROWS:
                log.warning("pending sâu %d dòng (> %d)", depth, WARN_DEPTH_ROWS)
```

`main.py` — trong `make_on_packet`, ngay sau `event = pkt.name`: `metrics.inc(f"frames.{event}")`; và đổi đuôi hàm:

```python
            if is_leader.is_set():
                writer.add(n)
                redis_queue.put_nowait(n)
            else:
                metrics.inc("not_leader_dropped")
```

`log_loop` thêm một dòng: `log.info("insert percentiles: %s", writer.insert_percentiles())`.

- [ ] **Bước 4: chạy xanh** — file mới PASS, và toàn bộ suite cũ: `uv run pytest tests/ingester -q` → 100+5 pass (test cũ không đổi hành vi).
- [ ] **Bước 5: commit** — `git add -A && git commit -m "feat(ingester): pending depth gauge, insert timing, missing drop counters"`

### Task 2: Probe một-lần trên ClickHouse thật — dedup theo block + kích thước pickle

**Files:**
- Create: `backend/tests/clickhouse/test_c99_dedup_probe.py`

**Interfaces:**
- Consumes: fixture `migrated` (`tests/clickhouse/conftest.py`) — client CH container thật đã migrate schema `rt`.
- Produces: **số đo in ra stdout** — người chạy dán vào `ledger.md` và spec §9. Không phải test hồi quy: gate bằng env `RUN_PROBE`.

- [ ] **Bước 1: viết probe** (không có pha đỏ — đây là phép đo, không phải TDD; assert chỉ chống đọc nhầm)

```python
# backend/tests/clickhouse/test_c99_dedup_probe.py
"""Phép kiểm một-lần spec spill §9 — chạy tay: RUN_PROBE=1 uv run pytest
tests/clickhouse/test_c99_dedup_probe.py -s -q
Kết quả DÁN vào spec §9 + ledger. Đơn vị cửa sổ là BLOCK (spec §7)."""
import os
import pickle
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

if not os.environ.get("RUN_PROBE"):
    pytest.skip("probe thủ công — đặt RUN_PROBE=1 để chạy", allow_module_level=True)

TZ = ZoneInfo("Asia/Ho_Chi_Minh")
COLS = ["symbol", "ts", "seq", "price", "volume", "side", "change",
        "cum_volume", "cum_value", "received_at"]


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
```

- [ ] **Bước 2: chạy hai lần và DÁN OUTPUT vào ledger** — (a) hồ sơ dev thường; (b) hồ sơ VPS hẹp (spec §10.3): dừng compose, bật lại với overlay theo [service-topology §7b](../../../20-design/service-topology.md) *"Cách chạy hồ sơ VPS"*, chạy lại probe. Lệnh: `$env:RUN_PROBE='1'; uv run pytest tests/clickhouse/test_c99_dedup_probe.py -s -q`.
- [ ] **Bước 3: ghi kết quả vào spec §9** (chỉ thêm số đo — ranh giới spec §15) và `ledger.md`.
- [ ] **Bước 4: commit** — `git commit -m "test(clickhouse): one-shot dedup-window and pickle-size probe"`

### Task 3 🔴 GATE — controller + chủ dự án, KHÔNG giao subagent

- [ ] Merge nhánh Phase A vào `main` (đủ suite xanh), để phiên giao dịch kế tiếp chạy với metrics mới.
- [ ] Sau phiên: đọc log lấy `pending_depth` p99 nền, `insert percentiles` (dev), nhịp block/dòng đến đỉnh (từ gauge + counters, KHÔNG dùng ước lượng 1,3 block/s — spec §10.2).
- [ ] Điền hằng số theo công thức spec §2.5: `N_CAP_ROWS` (≥ 10× p99 nền, × 497 B ≤ ~50 MB) · `K_REPLAY_ROWS` (> nhịp dòng đỉnh × 3, và × p95 < 1 s — dùng p95 hồ sơ VPS hẹp từ Task 2b) · `SPILL_CAP_BYTES` (≥ 2 giờ tải đỉnh × 3, theo byte/dòng đo ở PROBE 2).
- [ ] **Kiểm điều kiện khả thi spec §2.4** — `nhịp_dòng_đỉnh × p95_per_dòng < 1`. Vỡ ⇒ DỪNG, báo chủ dự án, không tự chọn K.
- [ ] Cập nhật giá trị tạm trong Global Constraints của plan này + ghi số vào spec §2.5 (kèm ngày đo). Báo chủ dự án số chốt trước khi mở Phase B.

---

# PHASE B — cơ chế (nhánh `feat/ingester-spill`, sau gate Task 3)

### Task 4: `SpillStore` — hàng đợi block trên đĩa

**Files:**
- Create: `backend/ingester/spill.py`
- Modify: `backend/ingester/config.py` (thêm `spill_dir`)
- Modify: `.env.example` (thêm dòng `INGESTER_SPILL_DIR` cạnh `INGESTER_MEASURE_DIR`)
- Test: `backend/tests/ingester/test_i13_spill_store.py`

**Interfaces (Produces — Task 5–8 dựa đúng chữ ký này):**

```python
@dataclass(frozen=True)
class SpillItem:
    paths: tuple[Path, ...]; table: str; kind: str   # 'r' | 'n'
    block: list; n_rows: int; n_bytes: int

class SpillStore:
    def __init__(self, root: Path, cap_bytes: int): ...
    owned: bool; seq: int; bytes_used: int
    counters: dict[str, int]                  # 'orphan_tmp' | 'replay_corrupt' | 'seq_collision'
    def try_acquire(self) -> bool             # OS exclusive lock owner.lock; giữ suốt đời tiến trình
    def scan(self) -> None                    # sau acquire: seq=max+1, bytes_used, bỏ .tmp (đếm)
    def write(self, table: str, block: list, kind: str) -> bool   # False = không ghi được (chưa sở hữu/trần/I-O)
    def next_batch(self, max_rows: int) -> SpillItem | None       # FIFO; '-n' gộp liền kề cùng bảng ≤ min(BLOCK_CAP, max_rows)
    def delete(self, item: SpillItem) -> None
    def empty(self) -> bool
```

`config.Config` thêm trường `spill_dir: Path`; `load()` thêm:

```python
    spill_dir = Path(os.environ.get("INGESTER_SPILL_DIR") or runtime / "spill")
    spill_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Bước 1: test đỏ**

```python
# backend/tests/ingester/test_i13_spill_store.py
"""SpillStore — spec spill §3/§4/§6. Seam 1, 2, 10, 12, 13 của spec §13."""
import os
import pickle
import subprocess
import sys
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from ingester.spill import SpillStore

TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _block(n: int, seq0: int = 1) -> list[list]:
    ts = datetime(2026, 8, 20, 9, 15, 1, tzinfo=TZ)
    return [["ACV", ts, seq0 + i, Decimal("10.00"), 100, "B", Decimal("0.00"),
             100, Decimal("1000.00"), ts] for i in range(n)]


def _store(tmp_path, cap=10**9) -> SpillStore:
    s = SpillStore(tmp_path, cap_bytes=cap)
    assert s.try_acquire()
    s.scan()
    return s


def test_roundtrip_exact_and_fifo_order(tmp_path):
    s = _store(tmp_path)
    b1, b2 = _block(3), _block(2, seq0=100)
    assert s.write("trade", b1, "n") and s.write("quote", b2, "n")
    i1 = s.next_batch(max_rows=10_000)
    assert i1.table == "trade" and i1.block == b1          # FIFO + byte-exact (Decimal/datetime)
    s.delete(i1)
    i2 = s.next_batch(max_rows=10_000)
    assert i2.table == "quote" and i2.block == b2
    s.delete(i2)
    assert s.empty() and s.bytes_used == 0


def test_merge_adjacent_n_same_table_up_to_max_rows(tmp_path):
    s = _store(tmp_path)
    for k in range(3):
        s.write("trade", _block(2, seq0=k * 10), "n")
    s.write("trade", _block(2, seq0=99), "r")              # '-r' chặn gộp
    item = s.next_batch(max_rows=10_000)
    assert item.n_rows == 6 and len(item.paths) == 3       # 3 file -n gộp, dừng trước -r
    s.delete(item)
    r = s.next_batch(max_rows=10_000)
    assert r.kind == "r" and len(r.paths) == 1             # -r nguyên văn một file


def test_merge_respects_max_rows(tmp_path):
    s = _store(tmp_path)
    for k in range(3):
        s.write("trade", _block(2, seq0=k * 10), "n")
    item = s.next_batch(max_rows=4)
    assert item.n_rows == 4 and len(item.paths) == 2       # 2 file = 4 dòng ≤ max


def test_tmp_orphan_skipped_and_counted(tmp_path):
    (tmp_path / "0000000007-trade-n.blk.tmp").write_bytes(b"nua block")
    s = _store(tmp_path)
    assert s.counters["orphan_tmp"] == 1
    assert not (tmp_path / "0000000007-trade-n.blk.tmp").exists()
    assert s.empty()


def test_seq_survives_restart_no_clobber(tmp_path):
    s1 = _store(tmp_path)
    s1.write("trade", _block(1), "n")                      # → seq 1
    del s1
    # tiến trình "mới": KHÔNG giữ lock cũ (mô phỏng chết) — mở store thứ hai
    s2 = SpillStore(tmp_path, cap_bytes=10**9)
    # lock cũ còn giữ bởi file handle s1? s1 đã del → GC đóng. Windows cần chắc chắn:
    import gc; gc.collect()
    assert s2.try_acquire()
    s2.scan()
    assert s2.seq == 2                                     # max quét được + 1, KHÔNG đè
    s2.write("trade", _block(1, seq0=50), "n")
    names = sorted(p.name for p in tmp_path.iterdir() if p.suffix == ".blk")
    assert names == ["0000000001-trade-n.blk", "0000000002-trade-n.blk"]


def test_cap_rejects_write(tmp_path):
    s = _store(tmp_path, cap=200)                          # trần bé tí
    assert s.write("trade", _block(500), "n") is False     # pickle 500 dòng >> 200 B
    assert s.empty()


def test_corrupt_file_moved_aside_and_counted(tmp_path):
    s = _store(tmp_path)
    s.write("trade", _block(1), "n")
    files = [p for p in tmp_path.iterdir() if p.suffix == ".blk"]
    files[0].write_bytes(b"khong phai pickle")
    assert s.next_batch(max_rows=100) is None
    assert s.counters["replay_corrupt"] == 1
    assert any(p.suffix == ".corrupt" for p in tmp_path.iterdir())


def test_lock_excludes_second_process(tmp_path):
    s = _store(tmp_path)
    # lock là CỦA TIẾN TRÌNH — phải kiểm bằng tiến trình con thật, không phải store thứ hai in-process
    code = ("import sys; from pathlib import Path; from ingester.spill import SpillStore; "
            "s = SpillStore(Path(sys.argv[1]), cap_bytes=10**9); "
            "sys.exit(0 if not s.try_acquire() else 1)")
    r = subprocess.run([sys.executable, "-c", code, str(tmp_path)],
                       capture_output=True, cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    assert r.returncode == 0, r.stderr.decode()
```

- [ ] **Bước 2: chạy thấy đỏ** — `uv run pytest tests/ingester/test_i13_spill_store.py -q` → FAIL `ModuleNotFoundError: ingester.spill`.
- [ ] **Bước 3: implement `spill.py`**

```python
"""Hàng đợi block trên đĩa cho ChWriter — spec spill §3/§4/§6.

Thư mục PHẲNG, mỗi block một file pickle `{seq:010d}-{table}-{kind}.blk`
(kind 'r' = từng gửi, phát lại nguyên văn giữ hash; 'n' = chưa từng gửi, được gộp).
Sở hữu = OS exclusive lock trên `owner.lock`, giữ suốt đời tiến trình, OS tự nhả
khi tiến trình chết (kể cả OOM-kill). Xoá file CHỈ SAU insert thành công — caller
gọi delete() khi ClickHouse trả OK. KHÔNG fsync: mô hình đe doạ là tiến trình
chết (page cache OS sống sót), không phải mất điện (spec §3).
"""
from __future__ import annotations

import logging
import os
import pickle
import re
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("ingester.spill")
_NAME = re.compile(r"^(\d{10})-([a-z_0-9]+)-([rn])\.blk$")


@dataclass(frozen=True)
class SpillItem:
    paths: tuple[Path, ...]
    table: str
    kind: str
    block: list
    n_rows: int
    n_bytes: int


class SpillStore:
    def __init__(self, root: Path, cap_bytes: int):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.cap_bytes = cap_bytes
        self.owned = False
        self.seq = 1
        self.bytes_used = 0
        self.counters: dict[str, int] = {"orphan_tmp": 0, "replay_corrupt": 0,
                                         "seq_collision": 0}
        self._lock_fh = None

    def try_acquire(self) -> bool:
        if self.owned:
            return True
        fh = open(self.root / "owner.lock", "a+b")
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            return False
        self._lock_fh = fh                    # giữ mở suốt đời — nhả = chết
        self.owned = True
        return True

    def scan(self) -> None:
        assert self.owned, "scan() chỉ sau khi try_acquire() thành công"
        max_seq = 0
        self.bytes_used = 0
        for p in list(self.root.iterdir()):
            if p.name.endswith(".blk.tmp"):
                p.unlink()
                self.counters["orphan_tmp"] += 1
                continue
            m = _NAME.match(p.name)
            if m:
                max_seq = max(max_seq, int(m.group(1)))
                self.bytes_used += p.stat().st_size
        self.seq = max_seq + 1

    def _files(self) -> list[Path]:
        return sorted(p for p in self.root.iterdir() if _NAME.match(p.name))

    def empty(self) -> bool:
        return not self._files()

    def write(self, table: str, block: list, kind: str) -> bool:
        if not self.owned:
            return False
        data = pickle.dumps((table, block), protocol=5)
        if self.bytes_used + len(data) > self.cap_bytes:
            return False
        name = f"{self.seq:010d}-{table}-{kind}.blk"
        final, tmp = self.root / name, self.root / (name + ".tmp")
        try:
            fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                         | getattr(os, "O_BINARY", 0))
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            if final.exists():                # không bao giờ đè (spec §3)
                tmp.unlink()
                self.counters["seq_collision"] += 1
                log.error("spill: %s đã tồn tại — seq hỏng, không đè", name)
                return False
            os.replace(tmp, final)
        except OSError:
            log.exception("spill: lỗi I/O khi ghi %s", name)
            return False
        self.seq += 1
        self.bytes_used += len(data)
        return True

    def next_batch(self, max_rows: int, block_cap: int = 5000) -> SpillItem | None:
        files = self._files()
        i = 0
        while i < len(files):
            p = files[i]
            loaded = self._load(p)
            if loaded is None:
                i += 1
                continue
            table, block = loaded
            kind = _NAME.match(p.name).group(3)
            if kind == "r":
                return SpillItem((p,), table, "r", block, len(block), p.stat().st_size)
            paths, rows = [p], list(block)
            limit = min(block_cap, max_rows)
            for q in files[i + 1:]:
                mq = _NAME.match(q.name)
                if mq.group(2) != table or mq.group(3) != "n":
                    break
                nxt = self._load(q)
                if nxt is None or len(rows) + len(nxt[1]) > limit:
                    break
                paths.append(q)
                rows.extend(nxt[1])
            nb = sum(x.stat().st_size for x in paths)
            return SpillItem(tuple(paths), table, "n", rows, len(rows), nb)
        return None

    def _load(self, p: Path):
        try:
            return pickle.loads(p.read_bytes())
        except Exception:  # noqa: BLE001 — file cụt/hỏng: dạt sang bên, có đếm
            self.counters["replay_corrupt"] += 1
            p.rename(p.with_suffix(".corrupt"))
            log.error("spill: file hỏng %s — dạt sang .corrupt", p.name)
            return None

    def delete(self, item: SpillItem) -> None:
        for p in item.paths:
            self.bytes_used -= p.stat().st_size
            p.unlink()
```

- [ ] **Bước 4: xanh** — file test PASS; `.env.example` thêm `INGESTER_SPILL_DIR=` (cạnh `INGESTER_MEASURE_DIR`, cùng format); `config.py` thêm `spill_dir` như Interfaces; test config hiện có (`test_i02_config.py`) chạy lại xanh.
- [ ] **Bước 5: commit** — `git commit -m "feat(ingester): SpillStore disk block queue with ownership lock"`

### Task 5: ChWriter v2 — tách vòng quản/vòng ghi, deque toàn cục (chưa có chế độ đĩa)

**Files:**
- Modify: `backend/ingester/chwriter.py` (viết lại phần hàng đợi; GIỮ `_is_deterministic` + bảng mã nguyên trạng)
- Modify: `backend/ingester/main.py` (`flush_loop` → `manage_loop` + `write_loop`; `drain_writer` dùng `writer.clean()`)
- Modify: `backend/tests/ingester/test_i08_chwriter.py` (thích nghi: `w.pending` dict → `w.queue` deque; hành vi hết-60s đổi ở Task 6, task NÀY giữ nguyên drop)
- Test: `backend/tests/ingester/test_i14_writer_disk_mode.py` (phần vòng tách)

**Interfaces (Produces):**

```python
class ChWriter:
    def __init__(self, client, spill: SpillStore | None = None,
                 sleep_fn=time.sleep, clock=time.monotonic): ...
    buffers: dict[str, list]; queue: deque[_Pending]; queue_rows: int
    head: deque[_Pending]; head_rows: int; disk_mode: bool
    def add(self, n: Normalized) -> None
    def manage_once(self) -> None        # vòng quản: cắt buffer, gauge, (Task 6: cửa vào + spill)
    def write_once(self, budget_s: float = WRITE_CALL_BUDGET_S) -> None
    def flush_once(self) -> None         # tương thích: manage_once() rồi write_once(budget lớn)
    def clean(self) -> bool              # buffers+queue+head rỗng (Task 8 thêm: và spill.empty())
    def insert_percentiles(self) -> dict # giữ từ Task 1

@dataclass
class _Pending:
    table: str; block: list; first_try: float | None = None
```

Hằng: `WRITE_CALL_BUDGET_S = 5.0`. `spill=None` nghĩa là không có đĩa (test cũ chạy được); mọi đường cần spill kiểm None → hành vi "không ghi được xuống đĩa".

**Thiết kế `write_once` (RAM mode — task này):** vòng `while clock < end`: peek `queue[0]` dưới `_lock`; `status = self._insert(table, block)` (một LẦN thử, timing như Task 1):
- `"done"` → popleft (trừ rows), tiếp.
- `"transient"` → đặt `first_try` nếu None; **nếu `clock - first_try >= RETRY_BUDGET_S`: task NÀY giữ hành vi cũ** (popleft + `dropped_block` + log có code) — Task 6 mới đổi thành spill; chưa hết hạn → return (thử lại nhịp sau — backoff = nhịp gọi, thay backoff ngủ cũ).
- `"poison"` → nếu `len(block) == 1`: popleft + `poison_row` + log; ngược lại popleft, chia đôi, `appendleft` nửa SAU rồi nửa TRƯỚC (giữ vị trí đầu hàng — trần tự nhiên theo độ sâu chia, không đệ quy, không cấp lại ngân sách).

`_insert(self, table, block) -> str` — một lần `client.insert`, phân loại bằng `_is_deterministic` (giữ nguyên hàm), KHÔNG sleep, KHÔNG đệ quy.

`main.py`:

```python
    async def manage_loop():
        while not stop.is_set():
            await asyncio.sleep(1.0)
            try:
                await asyncio.to_thread(writer.manage_once)
            except Exception:   # noqa: BLE001 — bất biến spec §2.1: vòng quản không được chết
                log.exception("manage_once lỗi không lường")
                writer.metrics.inc("spill_io_error")

    async def write_loop():
        while not stop.is_set():
            await asyncio.sleep(1.0)
            if is_leader.is_set():
                try:
                    await asyncio.to_thread(writer.write_once)
                except Exception:   # noqa: BLE001
                    log.exception("write_once lỗi không lường")
                    writer.metrics.inc("spill_io_error")
```

(thay `flush_loop` trong danh sách tasks — hai entry). `drain_writer`: điều kiện sạch → `writer.clean()`; vòng gọi `manage_once` rồi `write_once` mỗi lượt.

- [ ] **Bước 1: test đỏ** — trong `test_i14_writer_disk_mode.py`:

```python
"""ChWriter v2 — spec spill §2. Task 5: vòng tách + hợp đồng insert; seam 11, 16."""
import threading
import time
from collections import deque

from ingester.chwriter import COLUMNS, ChWriter, WRITE_CALL_BUDGET_S
from ingester.normalize import Metrics, Normalized


def _n(seq: int, table: str = "trade") -> Normalized:
    row = {c: None for c in COLUMNS[table]}
    row["symbol"], row["seq"] = "ACV", seq
    return Normalized(table=table, row=row, delta={}, symbol="ACV")


class _Clock:
    def __init__(self): self.now = 1000.0
    def __call__(self): return self.now
    def advance(self, d): self.now += d


def test_manage_runs_while_insert_hangs():
    """Bất biến spec §2.1: vòng quản KHÔNG bị insert treo chặn — chính B1 của review."""
    started, release = threading.Event(), threading.Event()

    class _Hang:
        def insert(self, *a, **k):
            started.set()
            release.wait(5)
            raise ConnectionError("treo")

    w = ChWriter(_Hang())
    w.add(_n(1))
    w.manage_once()                                        # cắt buffer → queue
    t = threading.Thread(target=w.write_once)
    t.start()
    started.wait(5)
    w.add(_n(2))
    w.manage_once()                                        # PHẢI chạy được ngay lúc này
    assert w.metrics.counters["pending_depth_rows"] == 2   # gauge cập nhật giữa lúc treo
    release.set(); t.join()


def test_write_once_call_budget_bounds_blocks_per_call():
    clock = _Clock()

    class _Slow:
        def __init__(self): self.calls = 0
        def insert(self, *a, **k):
            self.calls += 1
            clock.advance(3.0)                             # mỗi insert 3s "đồng hồ"

    c = _Slow()
    w = ChWriter(c, clock=clock)
    for i in range(10):
        w.add(_n(i)); w.manage_once()                      # 10 block một dòng
    w.write_once(budget_s=5.0)
    assert c.calls == 2                                    # 3s + 3s = 6s > 5s → dừng sau block 2
    assert w.queue_rows == 8


def test_transient_leaves_block_for_next_tick_no_sleep():
    class _Fail:
        def __init__(self): self.calls = 0
        def insert(self, *a, **k):
            self.calls += 1
            raise ConnectionError("chập chờn")

    c = _Fail()
    w = ChWriter(c)
    w.add(_n(1)); w.manage_once()
    w.write_once()
    assert c.calls == 1 and w.queue_rows == 1              # còn nguyên, không ngủ, không lặp
    w.write_once()
    assert c.calls == 2                                    # nhịp sau thử lại


def test_poison_bisect_keeps_front_position_and_isolates():
    class _Bad:
        def __init__(self): self.written = []
        def insert(self, table, data, column_names):
            seq_i = COLUMNS["trade"].index("seq")
            if any(r[seq_i] == 2 for r in data):
                raise Exception("Code: 117. DB::Exception: x (INCORRECT_DATA)")
            self.written.extend(data)

    c = _Bad()
    w = ChWriter(c)
    for i in range(4):
        w.add(_n(i))
    w.manage_once()
    w.flush_once()
    seq_i = COLUMNS["trade"].index("seq")
    assert sorted(r[seq_i] for r in c.written) == [0, 1, 3]
    assert w.metrics.counters["poison_row.trade"] == 1
```

- [ ] **Bước 2: đỏ** — `uv run pytest tests/ingester/test_i14_writer_disk_mode.py -q` → FAIL (API chưa có).
- [ ] **Bước 3: viết lại `chwriter.py`** theo Interfaces + thiết kế trên. Điểm giữ nguyên: `_is_deterministic`, `_DETERMINISTIC_*`, `BLOCK_CAP`, `RETRY_BUDGET_S`, timing Task 1, comment lịch sử về mã lỗi. `add()`: giữ `_lock` + cap-cut (cắt vào `queue` kèm `queue_rows`, counter `block_cap.<table>` giữ nguyên). `flush_once()` = `self.manage_once(); self.write_once(budget_s=RETRY_BUDGET_S + 30)` (đủ cho test cũ chạy trọn).
- [ ] **Bước 4: thích nghi `test_i08_chwriter.py`** — thay mọi `w.pending[...]`/`w.pending.values()` bằng duyệt `w.queue` (mỗi phần tử `_Pending(table, block)`); các test transient dùng `sleep_fn` bỏ tham số đó (không còn sleep — retry theo nhịp): với `FlakyClient(fail_times=2)` gọi `w.flush_once()` **ba lần** thay vì một; `test_retry_budget_counts_wall_clock`: hết 60 s → vẫn `dropped_block` (Task 6 sẽ đổi test này lần nữa — ghi chú tại chỗ); `test_retry_budget_is_shared_across_bisect_recursion` đổi tên/asserts: chia đôi không còn ăn ngân sách thời gian — assert tổng thời gian xả ≤ 2 × ngân sách vẫn đúng. Chạy: `uv run pytest tests/ingester/test_i08_chwriter.py tests/ingester/test_i14_writer_disk_mode.py -q` → xanh hết.
- [ ] **Bước 5: sửa `main.py`** (hai loop + drain) — chạy toàn suite `uv run pytest tests/ingester -q` xanh.
- [ ] **Bước 6: commit** — `git commit -m "refactor(ingester): split writer into manage/write loops with per-call budget"`

### Task 6: Hai cửa vào chế độ đĩa — trần N theo dòng, hết-60s thành spill

**Files:**
- Modify: `backend/ingester/chwriter.py`
- Test: thêm vào `backend/tests/ingester/test_i14_writer_disk_mode.py`

**Interfaces (Produces):** hằng `N_CAP_ROWS`, `K_REPLAY_ROWS`, `SPILL_CAP_BYTES` (giá trị từ Task 3, ghi kèm comment ngày đo + công thức spec §2.5); `ChWriter._enter_disk(door: str)`; hành vi: `manage_once` trong disk mode chuyển hết `queue` → `spill.write(kind='n')`; thoát khi `head` rỗng + `queue` rỗng + `spill.empty()`; `dropped_block` không còn tồn tại ở đường run — thay bằng `_spill_block(item, kind)` với nhánh False = `spill_drop_newest.<table>` + log cấu trúc `(table, n_rows, received_at_min, received_at_max)`.

- [ ] **Bước 1: test đỏ** (thêm vào `test_i14_...`; dùng `SpillStore` thật trên `tmp_path`)

```python
from ingester.spill import SpillStore
from ingester.chwriter import N_CAP_ROWS


def _writer_with_spill(tmp_path, client, clock=None) -> ChWriter:
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire(); s.scan()
    return ChWriter(client, spill=s, clock=clock or time.monotonic)


def test_door1_ram_cap_enters_disk_mode(tmp_path):
    class _Down:
        def insert(self, *a, **k): raise ConnectionError("CH chết")
    w = _writer_with_spill(tmp_path, _Down())
    # vượt trần bằng block to đã cắt sẵn — không add N_CAP_ROWS dòng lẻ cho nhanh
    from ingester.chwriter import _Pending
    w.queue.append(_Pending("trade", [[None] * len(COLUMNS["trade"])] * (N_CAP_ROWS + 1)))
    w.queue_rows = N_CAP_ROWS + 1
    w.manage_once()
    assert w.disk_mode and w.head_rows == N_CAP_ROWS + 1   # queue cũ thành đầu đông cứng
    w.add(_n(9)); w.manage_once()
    assert w.queue_rows == 0 and not w.spill.empty()       # block mới xuống đĩa '-n'


def test_door2_retry_budget_spills_as_r_not_drop(tmp_path):
    clock = _Clock()
    class _Down:
        def insert(self, *a, **k):
            clock.advance(61.0)                            # một lần thử ăn hết ngân sách
            raise ConnectionError("treo")
    w = _writer_with_spill(tmp_path, _Down(), clock=clock)
    w.add(_n(1)); w.manage_once(); w.write_once(); w.write_once()
    assert w.disk_mode
    assert w.metrics.counters.get("dropped_block.trade") is None      # KHÔNG còn drop
    item = w.spill.next_batch(max_rows=10)
    assert item.kind == "r" and item.n_rows == 1                      # thành file -r


def test_no_spill_available_drops_newest_with_ledger(tmp_path, caplog):
    """spill=None (không sở hữu đĩa) — đường thoát cuối thống nhất spec §6."""
    clock = _Clock()
    class _Down:
        def insert(self, *a, **k):
            clock.advance(61.0); raise ConnectionError("treo")
    w = ChWriter(_Down(), spill=None, clock=clock)
    w.add(_n(1)); w.manage_once()
    import logging
    with caplog.at_level(logging.ERROR):
        w.write_once(); w.write_once()
    assert w.metrics.counters["spill_drop_newest.trade"] == 1
    assert "BỎ block trade" in caplog.text


def test_exit_disk_only_when_all_empty(tmp_path):
    ok = type("_Ok", (), {"insert": lambda self, *a, **k: None})()
    w = _writer_with_spill(tmp_path, ok)
    w.add(_n(1)); w.manage_once()
    w._enter_disk("test")
    w.add(_n(2)); w.manage_once()                          # dòng 2 xuống đĩa
    assert w.disk_mode
    w.write_once()                                         # xả đầu RAM + đĩa
    w.manage_once()                                        # kiểm điều kiện ra
    assert not w.disk_mode and w.clean()
```

- [ ] **Bước 2: đỏ**, rồi **Bước 3: implement** — `manage_once` thêm: (a) nếu `spill` chưa owned → `try_acquire` + `scan` + nếu có file thì `_enter_disk("adopt")`; (b) cửa 1; (c) disk mode: `_spill_tail()` (pop hết `queue` → `_spill_block(kind='n')`) + điều kiện ra. `write_once` disk mode → `_drain_disk_step()`: đầu RAM trước (cùng hạn mức K theo DÒNG), rồi `spill.next_batch(max_rows=budget_còn_lại)`; transient → return giữ nguyên; poison trên item đĩa → `_split_disk_item` (ghi 2 file con cùng kind rồi `spill.delete(cha)` TRƯỚC insert — spec §3; con 1 dòng lỗi → `poison_row` + delete). Cửa 2 trong `_drain_ram`: hết hạn → popleft + `_spill_block(item, 'r')` + `_enter_disk("retry_budget")` + return. `_spill_block` nhánh False: `spill_drop_newest.<table>` + log ERROR cấu trúc — index `received_at` tra sẵn `RA_IDX = {t: cols.index("received_at") for t, cols in COLUMNS.items()}`.
- [ ] **Bước 4: sửa test cũ lần cuối** — `test_retry_budget_counts_wall_clock_not_sleep_time` và `test_backpressure_code_stays_transient` đổi kỳ vọng: `dropped_block` → `spill_drop_newest` (writer không spill) hoặc file `-r` (writer có spill); ghi chú spec §2.3 tại chỗ. Toàn suite ingester xanh.
- [ ] **Bước 5: commit** — `git commit -m "feat(ingester): disk mode with two entry doors, retry-exhaustion spills instead of dropping"`

### Task 7: Phát lại có tiết lưu K + kiểm FIFO xuyên RAM–đĩa

**Files:** Modify `backend/ingester/chwriter.py` (nếu Task 6 chưa đủ) · Test: thêm `test_i14_...`

- [ ] **Bước 1: test đỏ**

```python
def test_k_caps_total_rows_per_tick_head_included(tmp_path):
    import ingester.chwriter as m
    ok_calls = []
    ok = type("_Ok", (), {"insert": lambda self, t, d, column_names: ok_calls.append(len(d))})()
    w = _writer_with_spill(tmp_path, ok)
    old_k = m.K_REPLAY_ROWS
    m.K_REPLAY_ROWS = 5
    try:
        from ingester.chwriter import _Pending
        w._enter_disk("test")
        w.head.append(_Pending("trade", [[None] * len(COLUMNS["trade"])] * 3))
        w.head_rows = 3
        for i in range(4):
            w.spill.write("trade", [[None] * len(COLUMNS["trade"])] * 2, "n")
        w.write_once()
        # K=5: đầu RAM 3 dòng + đĩa chỉ còn được 2 dòng (1 file) — KHÔNG phải cả 8
        assert sum(ok_calls) == 5
    finally:
        m.K_REPLAY_ROWS = old_k


def test_fifo_across_ram_and_disk(tmp_path):
    seen = []
    seq_i = COLUMNS["trade"].index("seq")
    ok = type("_Ok", (), {"insert": lambda self, t, d, column_names:
                          seen.extend(r[seq_i] for r in d)})()
    w = _writer_with_spill(tmp_path, ok)
    w.add(_n(1)); w.manage_once()
    w._enter_disk("test")
    w.add(_n(2)); w.manage_once()
    w.add(_n(3)); w.manage_once()
    while w.disk_mode:
        w.write_once(); w.manage_once()
    assert seen == [1, 2, 3]                               # đầu RAM trước, đĩa theo seq
```

- [ ] **Bước 2–4: đỏ → implement (nếu thiếu) → xanh toàn suite → commit** `git commit -m "feat(ingester): K-throttled replay, global FIFO across ram head and disk"`

### Task 8: Hồi phục — replay nợ lúc khởi động, reconcile ngày nợ, drain biết đĩa, mất/giành leadership

**Files:**
- Modify: `backend/ingester/chwriter.py` (`replay_debt`, `clean` gồm `spill.empty()`)
- Modify: `backend/ingester/main.py` (`_run_run`: dựng SpillStore + acquire + replay nợ + reconcile ngày nợ; `drain_writer` ngân sách mới; log vào/ra chế độ đĩa đã có ở `_enter_disk`)
- Test: `backend/tests/ingester/test_i15_recovery_drain.py`

**Interfaces (Produces):**

```python
ChWriter.replay_debt(self) -> set[date]    # xả toàn bộ đĩa full-speed (trước phiên);
                                           # transient → dừng, disk_mode=True, trả ngày đã thấy
ChWriter.clean(self) -> bool               # nay gồm: spill None hoặc spill.empty()
# main.py:
DRAIN_HARD_CAP_S = 600.0                   # spec §5.1 — thay DRAIN_BUDGET_S suy từ retry
async def drain_writer(writer, budget_s=None, ...) -> bool
#   budget mặc định: 75.0 nếu không disk_mode và spill rỗng; ngược lại DRAIN_HARD_CAP_S
```

`_run_run` sau Redis ping, trước socket:

```python
    store = spill_mod.SpillStore(cfg.spill_dir, SPILL_CAP_BYTES)
    writer = ChWriter(client, spill=store)
    if store.try_acquire():
        store.scan()
        debt_dates = await asyncio.to_thread(writer.replay_debt)
        today = datetime.now(TZ).date()
        for dd in sorted(d for d in debt_dates if d < today):
            log.info("nợ đĩa ngày %s đã phát lại — chạy lại đối chứng", dd)
            r = reconcile(client, dd)
            _print_reconcile(r)                            # spec §5.3
    else:
        log.warning("spill dir đang bị tiến trình khác giữ — chạy KHÔNG có lưới đĩa")
```

(`writer.manage_once` tự thử acquire lại mỗi nhịp — đường giành leadership giữa phiên, đã có từ Task 6.)

- [ ] **Bước 1: test đỏ**

```python
# backend/tests/ingester/test_i15_recovery_drain.py
"""Spec spill §4/§5 — seam 8, 13, 14, 17."""
import asyncio
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from ingester.chwriter import COLUMNS, ChWriter
from ingester.main import drain_writer
from ingester.spill import SpillStore

TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _trade_rows(day: int, n: int) -> list[list]:
    ts = datetime(2026, 8, day, 9, 15, 1, tzinfo=TZ)
    return [["ACV", ts, i, Decimal("10.00"), 100, "B", Decimal("0.00"),
             100, Decimal("1000.00"), ts] for i in range(n)]


def test_replay_debt_returns_dates_and_empties_disk(tmp_path):
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire(); s.scan()
    s.write("trade", _trade_rows(day=26, n=3), "n")
    s.write("trade", _trade_rows(day=27, n=2), "r")
    ok = type("_Ok", (), {"insert": lambda self, *a, **k: None})()
    w = ChWriter(ok, spill=s)
    dates = w.replay_debt()
    assert dates == {date(2026, 8, 26), date(2026, 8, 27)}
    assert s.empty() and w.clean()


def test_replay_debt_stops_on_transient_and_stays_disk_mode(tmp_path):
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire(); s.scan()
    s.write("trade", _trade_rows(day=26, n=3), "n")
    class _Down:
        def insert(self, *a, **k): raise ConnectionError("CH chưa dậy")
    w = ChWriter(_Down(), spill=s)
    dates = w.replay_debt()
    assert dates == set() and w.disk_mode and not s.empty()   # nợ giữ nguyên, vào phiên ở chế độ đĩa


def test_drain_false_when_disk_not_empty(tmp_path, caplog):
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire(); s.scan()
    class _Down:
        def insert(self, *a, **k): raise ConnectionError("chết")
    w = ChWriter(_Down(), spill=s)
    w._enter_disk("test")
    s.write("trade", _trade_rows(day=27, n=1), "n")
    import logging
    with caplog.at_level(logging.ERROR):
        drained = asyncio.run(drain_writer(w, budget_s=0.3))
    assert drained is False
    assert "còn" in caplog.text                             # log nợ: "còn X block / Y dòng"


def test_default_budget_short_when_no_debt(tmp_path):
    ok = type("_Ok", (), {"insert": lambda self, *a, **k: None})()
    s = SpillStore(tmp_path, cap_bytes=10**9)
    assert s.try_acquire(); s.scan()
    w = ChWriter(ok, spill=s)
    assert asyncio.run(drain_writer(w)) is True             # sạch ngay, không chờ 600s
```

- [ ] **Bước 2: đỏ → Bước 3: implement** (`replay_debt` đọc ngày từ `received_at` của dòng đầu/cuối mỗi item qua `RA_IDX`; drain log `"hết %ss ngân sách xả — còn %d block / %d dòng trên đĩa"`).
- [ ] **Bước 4: xanh toàn suite** + `uv run pytest tests/ingester -q`.
- [ ] **Bước 5: commit** — `git commit -m "feat(ingester): startup debt replay with per-day reconcile, disk-aware drain"`

### Task 9: `process_record` + bộ đếm `d[]`

**Files:**
- Create: `backend/ingester/pipeline.py`
- Create: `backend/ingester/measure_count.py`
- Modify: `backend/ingester/main.py` (`make_on_packet` dùng `process_record`)
- Modify: `backend/ingester/__main__.py` (mode `--count`)
- Test: `backend/tests/ingester/test_i16_measure_count.py`

**Interfaces (Produces):**

```python
# pipeline.py — nguồn sự thật CHUNG (spec §11: không hai bộ luật)
def process_record(event: str, record: dict, now: float, dedup: FrameDedup,
                   stamper: Stamper, metrics: Metrics) -> Normalized | None
# measure_count.py
def count_measure(day_dir: Path, t_from_ms: int, t_to_ms: int) -> tuple[dict[str, int], Metrics]
# __main__: python -m ingester --count <YYYYMMDD|DIR> [--from ISO] [--to ISO] [--db]
#   --db: so với count() rt.* cùng cửa sổ received_at, in bảng expected/actual/khoản trừ/dư
```

`process_record` = đúng thân vòng `for record ...` của `make_on_packet` hiện tại (dedup → symbol → stamp → normalize, kèm metric `dup_dropped`/`no_symbol_dropped`/`normalize_error` + log warning normalize); `make_on_packet` gọi nó, giữ nguyên phần `is_leader`/frames-counter. `count_measure`: duyệt `sorted(day_dir.glob("frames-*.jsonl*"))`, mở gzip hoặc trần theo đuôi, JSON từng dòng `{"r","p"}`, lọc `t_from_ms <= r <= t_to_ms`, `eio.parse_packet`, chỉ `Event` trong `EVENTS`, `records_of`, `process_record(..., now=r/1000.0, ...)` — **đồng hồ là `r`** (spec §11.1).

- [ ] **Bước 1: test đỏ** — golden giải tay:

```python
# backend/tests/ingester/test_i16_measure_count.py
"""Bộ đếm d[] — spec spill §11; seam 18, 19 (golden giải tay, chống tautological)."""
import gzip
import json

from ingester.measure_count import count_measure

T_REC = {"TD": "10/08/2026", "FT": "13:08:56", "SB": "ACV", "FV": "100", "LC": "S",
         "FMP": "42100.0", "FCV": "1000.0", "SM": "74027", "AVO": "590000",
         "AVA": "24983210000.0"}


def _frame(rec=T_REC) -> str:
    return "42" + json.dumps(["t", {"a": "i", "d": [rec]}])


def _write(day_dir, name, lines, gz=False):
    day_dir.mkdir(exist_ok=True)
    p = day_dir / name
    data = "".join(json.dumps(x) + "\n" for x in lines)
    if gz:
        with gzip.open(p, "wt", encoding="utf-8") as fh:
            fh.write(data)
    else:
        p.write_text(data, encoding="utf-8")


def test_count_hand_solved_with_dedup_by_r_clock(tmp_path):
    d = tmp_path / "20260810"
    base = 1_786_342_136_000
    _write(d, "frames-20260810-13.jsonl.gz", [
        {"r": base, "p": _frame()},                        # đếm: 1
        {"r": base + 1_000, "p": _frame()},                # trùng nội dung, cách 1s < 600s → dup
        {"r": base + 700_000, "p": _frame()},              # cách 700s > cửa sổ 600s → đếm: 2
        {"r": base + 700_500, "p": "42" + json.dumps(      # SM khác → nội dung khác → đếm: 3
            ["t", {"a": "i", "d": [{**T_REC, "SM": "74028"}]}])},
    ], gz=True)
    # file TRẦN chưa gzip cũng phải được đọc (spec §11.2)
    _write(d, "frames-20260810-14.jsonl", [
        {"r": base + 800_000, "p": _frame({**T_REC, "SM": "74029"})},   # đếm: 4
    ])
    counts, metrics = count_measure(d, t_from_ms=0, t_to_ms=2 * base)
    # GIẢI TAY: 5 frame 't' → 1 dup (theo đồng hồ r) → 4 dòng trade
    assert counts["trade"] == 4
    assert metrics.counters["dup_dropped"] == 1


def test_window_cut_excludes_frames_outside(tmp_path):
    d = tmp_path / "20260810"
    base = 1_786_342_136_000
    _write(d, "frames-20260810-13.jsonl", [
        {"r": base, "p": _frame()},
        {"r": base + 5_000, "p": _frame({**T_REC, "SM": "74030"})},
    ])
    counts, _ = count_measure(d, t_from_ms=base, t_to_ms=base + 1_000)
    assert counts["trade"] == 1                            # frame thứ hai ngoài cửa sổ — seam 18
```

- [ ] **Bước 2: đỏ → Bước 3: implement** `pipeline.py` + `measure_count.py` + `__main__` (`--from/--to` parse ISO giờ VN → ms; mặc định trọn ngày; `--db` dùng `CLICKHOUSE_INGESTER_URL`, query `SELECT count() FROM rt.<t> WHERE received_at BETWEEN ...`, in bảng kèm khoản trừ từ metrics và nhắc các counter phiên (`not_leader_dropped`, `replay_blocks`) phải lấy từ log phiên chạy).
- [ ] **Bước 4: refactor `make_on_packet`** dùng `process_record` — toàn suite xanh (test i12 frames-counter vẫn xanh).
- [ ] **Bước 5: commit** — `git commit -m "feat(ingester): d[] record counter reusing the live pipeline dry"`

### Task 10: AC2 — kịch bản sự cố dàn dựng (chaos)

**Files:**
- Create: `backend/tests/ingester/test_i17_chaos_ch_restart.py`
- Modify: `backend/pyproject.toml` (dev-dependency `psutil` — `uv add --dev psutil`)

Gate env `RUN_CHAOS=1` (chạy tay, module-level skip như Task 2). Kịch bản đúng spec §12 AC2:

- [ ] **Bước 1: viết test** — container CH **riêng** (KHÔNG dùng fixture `migrated` — chaos stop/start container sẽ phá các test khác; copy cách dựng + migrate của `tests/clickhouse/conftest.py` vào fixture cục bộ `chaos_ch` với tên container riêng):

```python
# Khung — giữ đúng các mốc; phần dựng container chép từ tests/clickhouse/conftest.py
import os, subprocess, threading, time
import psutil, pytest
if not os.environ.get("RUN_CHAOS"):
    pytest.skip("chaos thủ công — RUN_CHAOS=1", allow_module_level=True)

N_ROWS = 200_000

def test_docker_stop_mid_feed_zero_loss(chaos_ch, chaos_container_name, tmp_path):
    from ingester.chwriter import ChWriter, COLUMNS
    from ingester.spill import SpillStore
    s = SpillStore(tmp_path, cap_bytes=10**9); assert s.try_acquire(); s.scan()
    w = ChWriter(chaos_ch, spill=s)
    rss_peak = 0
    def _sample():
        nonlocal rss_peak
        p = psutil.Process()
        while sampling:
            rss_peak = max(rss_peak, p.memory_info().rss)
            time.sleep(1.0)
    sampling = True; threading.Thread(target=_sample, daemon=True).start()
    stopped = False
    for i in range(N_ROWS):                     # nạp qua add() — số dòng biết trước
        w.add(_trade_normalized(i))             # helper như test_i08
        if i % 500 == 0:
            w.manage_once(); w.write_once()
        if i == N_ROWS // 3 and not stopped:
            subprocess.run(["docker", "stop", chaos_container_name], check=True)
            stopped = True
        if i == 2 * N_ROWS // 3:
            subprocess.run(["docker", "start", chaos_container_name], check=True)
    deadline = time.time() + 600
    while not w.clean() and time.time() < deadline:
        w.manage_once(); w.write_once(); time.sleep(0.2)
    sampling = False
    assert w.clean(), "xả không sạch trong 10 phút"
    total = chaos_ch.query("SELECT count() FROM rt.trade").result_rows[0][0]
    dup = total - N_ROWS
    assert dup >= 0, f"MẤT {-dup} dòng"        # đẳng thức spec AC2: kho = nạp + trùng-có-sổ
    print(f"\nAC2: nạp {N_ROWS}, kho {total}, trùng {dup}, RSS đỉnh {rss_peak/2**20:.0f} MB")
    assert rss_peak <= 200 * 2**20             # ngân sách service-topology §7b
```

*(client `chaos_ch` phải dựng lại connection sau `docker start` — dùng client factory trong vòng `while`, bắt exception khi CH chết: chi tiết để executor xử theo hành vi thật của clickhouse_connect, miễn giữ nguyên các assert.)*

- [ ] **Bước 2: chạy** `$env:RUN_CHAOS='1'; uv run pytest tests/ingester/test_i17_chaos_ch_restart.py -s -q` → dán output (số nạp/kho/trùng/RSS) vào ledger. Đỏ thì sửa cơ chế, không sửa assert.
- [ ] **Bước 3: commit** — `git commit -m "test(ingester): AC2 chaos scenario - docker stop mid-feed, zero loss"`

### Task 11: Tài liệu — checklist spec §15, đủ và cùng lượt

- [ ] [market-data-store §3.7](../../../20-design/market-data-store.md): viết lại luật 3 (cửa sổ = **100 block/bảng**, không phải ~100 giây; điều kiện đảo quyết định #4 khi có spill + `d[]`; luật cũ giữ cho ca không spill) và luật 4 (ngân sách xả = công thức spec §5, không suy từ `RETRY_BUDGET_S`); bổ sung chế độ đĩa vào hợp đồng ghi.
- [ ] `git grep -n "100 giây" && git grep -n "tệ hơn mất dòng"` toàn repo — sửa/đối chiếu mọi hit ngoài vùng lịch sử (gồm comment `chwriter.py` dòng `RETRY_BUDGET_S`); dán kết quả grep sau khi sửa vào ledger (phép kiểm §1.7).
- [ ] [service-topology §7b](../../../20-design/service-topology.md): dòng đĩa vùng spill (trần + số đo Task 3) + tách ngân sách RAM hàng đợi khỏi 97 MB nền.
- [ ] [backend/README.md](../../../../backend/README.md): mode `--count` (chế độ chạy thứ tư — sửa câu "Ba chế độ"); nhắc `INGESTER_SPILL_DIR`.
- [ ] [roadmap](../../../00-overview/roadmap.md): mục §2 lát này; gỡ ⚠️ "chưa làm xong ngày nào thì ngày đó vẫn hở" §2.1; đính chính câu "rút bản đo xuống vài ngày" (bản đo nay là hạ tầng nghiệm thu — giữ 30 ngày).
- [ ] `docs/90-records/README.md`: cập nhật trạng thái dòng plan này.
- [ ] Commit: `git commit -m "docs: spill slice - rewrite write-contract rules, budgets, run modes"`

### Task 12 🔴 GATE nghiệm thu cuối — controller + chủ dự án

- [ ] AC1: `uv run pytest tests/ingester tests/clickhouse -q` — dán số pass vào ledger.
- [ ] AC2: output chaos Task 10 (0 mất, trùng có sổ, RSS đỉnh ≤ 200 MB).
- [ ] AC3: phiên thật kế tiếp — chạy `python -m ingester --count <YYYYMMDD> --from <mốc log run bắt đầu> --to <mốc log run dừng> --db`; hằng đẳng thức spec §12 dư = 0; dán bảng vào ledger. Mốc cắt lấy từ log `"run chạy tới ..."` và dòng dừng của writer.
- [ ] AC4: hằng số + căn cứ đo trong code; kết quả probe trong spec §9.
- [ ] Review theo §4.1.5 (hai trục Chuẩn/Spec) trên toàn nhánh, rồi merge `main`, báo chủ dự án.

---

## Self-review của plan (đã chạy)

- **Phủ spec:** §2.1→T5 · §2.2/§2.3→T1+T6 · §2.4/§2.5→T3+T7 · §3→T4+T6 · §4→T6 (adopt qua manage) + T8 · §5→T8 · §6→T6 · §7→T2 · §8→T1+T6 · §9→T2 · §10→T1+T2+T3 · §11→T9 · §12→T10+T12 · §13 seam 1–19→T4(1,2,10,12,13) T5(11,16) T6(3,4) T7(5,6,7) T6(8→qua adopt trong manage; 9) T8(14,17) T9(18,19) T1(15 qua gauge test) · §14 không sinh task (đúng) · §15→T11.
- **Placeholder:** không còn "TBD"; ba hằng số có giá trị tạm chạy được + gate Task 3 bắt buộc cập nhật; hai chỗ chủ đích để executor tự xử (reconnect client trong chaos T10) có nêu ranh giới assert bất biến.
- **Nhất quán kiểu:** `SpillStore.write(table, block, kind)` / `next_batch(max_rows)` / `SpillItem` dùng thống nhất T4→T8; `_Pending(table, block, first_try)` T5→T7; `manage_once`/`write_once`/`clean`/`replay_debt` T5→T10 cùng chữ ký.
