# Plan thực thi — lược đồ ClickHouse kho realtime

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dựng database `rt` trên ClickHouse (migration runner + DDL 12 object + role/profile + compose profile `realtime` + script backup) kèm bộ test seam trên CH thật, và cập nhật tài liệu sống theo checklist §13 của spec.

**Architecture:** Runner Python nhỏ đọc `database/clickhouse/versions/*.sql` tuần tự, ghi sổ `rt.schema_migrations`; DDL là bản đã kiểm T1–T15 trong spec §12; test chạy trên container ClickHouse ephemeral (không đụng CH dev). Compose thêm service `clickhouse` dưới profile `realtime`, mặc định không chạy.

**Tech Stack:** Python 3.12 + `clickhouse-connect` · pytest · Docker (image pin `clickhouse/clickhouse-server:26.3.22.7`) · Node `node:test` cho `stack.mjs`.

**Spec:** [spec.md](spec.md) — cùng thư mục. Mọi con số/DDL trong plan chép từ spec (đã kiểm trên CH 26.3.22.7 thật, biên bản §12). Đọc spec trước khi làm bất kỳ task nào.

## Global Constraints

- **Nhánh làm việc: `feat/clickhouse-realtime-store`** — không commit thẳng `main` (CLAUDE.md §4.7). Conventional Commits, message tiếng Anh.
- Image ClickHouse pin đúng **`clickhouse/clickhouse-server:26.3.22.7`** — đổi bản là phải chạy lại bộ kiểm §12 của spec, không tự đổi.
- Mọi `DateTime`/`DateTime64` khai tường minh `'Asia/Ho_Chi_Minh'`; container đặt `TZ=Asia/Ho_Chi_Minh`.
- Mọi statement trong `versions/*.sql` phải **idempotent** (`IF NOT EXISTS`/`IF EXISTS`; `GRANT` vốn idempotent). File không được chứa `;` bên trong string literal và không chứa `;` trong comment (quy ước để parser split-`;` đúng).
- Python: luôn chạy qua `uv run` từ `backend/`; env `PYTHONIOENCODING=utf-8`.
- Test CH **không dùng CH dev đang chạy** — container ephemeral riêng mỗi session test (xoá khi xong).
- KHÔNG viết code ingester/api trong plan này (spec §11 — plan riêng). Ba seam gắn nhãn "plan ingester"/"plan api" trong spec §9 KHÔNG thực thi ở đây.
- Artifact tạm (log subagent, report) để ở scratchpad ngoài repo — cấm tạo `.superpowers/` trong repo.

---

### Task 1: Dependency + fixture container ClickHouse cho test

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/tests/clickhouse/__init__.py` (rỗng)
- Create: `backend/tests/clickhouse/conftest.py`
- Test: `backend/tests/clickhouse/test_t01_fixture.py`

**Interfaces:**
- Produces: fixture pytest `ch` (session-scoped, trả `clickhouse_connect` client đã nối container ephemeral, đã set `os.environ["CLICKHOUSE_URL"]`); fixture `migrated` (function-scoped, đảm bảo đã `upgrade()` — Task 2 mới có runner nên Task 1 chỉ dựng `ch`); hằng `IMAGE` = `"clickhouse/clickhouse-server:26.3.22.7"`.

- [ ] **Step 1: Thêm dependency**

Trong `backend/pyproject.toml`, thêm vào mảng `dependencies`:

```toml
    "clickhouse-connect>=0.8",
```

Chạy: `cd backend && uv sync` — Expected: lock cập nhật, không lỗi.

- [ ] **Step 2: Viết test đỏ cho fixture**

`backend/tests/clickhouse/test_t01_fixture.py`:

```python
def test_fixture_connects(ch):
    assert ch.command("SELECT 1") == 1

def test_fixture_version_pinned(ch):
    assert ch.command("SELECT version()").startswith("26.3.22")

def test_fixture_timezone(ch):
    assert ch.command("SELECT timezone()") == "Asia/Ho_Chi_Minh"
```

Chạy: `cd backend && uv run pytest tests/clickhouse/test_t01_fixture.py -v`
Expected: FAIL/ERROR — `fixture 'ch' not found`.

- [ ] **Step 3: Viết conftest**

`backend/tests/clickhouse/conftest.py`:

```python
import os
import socket
import subprocess
import time
import uuid
from pathlib import Path

import clickhouse_connect
import pytest

IMAGE = "clickhouse/clickhouse-server:26.3.22.7"
REPO_ROOT = Path(__file__).resolve().parents[3]
CH_CONF_DIR = REPO_ROOT / "deploy" / "infra" / "clickhouse"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def ch_backup_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("ch-backups")


@pytest.fixture(scope="session")
def ch(ch_backup_dir):
    """Container ClickHouse ephemeral — không đụng CH dev. Xoá khi hết session."""
    name = f"ch-test-{uuid.uuid4().hex[:8]}"
    port = _free_port()
    cmd = [
        "docker", "run", "-d", "--name", name,
        "--ulimit", "nofile=262144:262144",
        "-e", "CLICKHOUSE_PASSWORD=testpass",
        "-e", "CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1",
        "-e", "TZ=Asia/Ho_Chi_Minh",
        "-v", f"{CH_CONF_DIR / 'backups.xml'}:/etc/clickhouse-server/config.d/backups.xml:ro",
        "-v", f"{ch_backup_dir}:/backups",
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
        os.environ["CLICKHOUSE_URL"] = url
        yield client
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
```

Lưu ý: conftest mount `deploy/infra/clickhouse/backups.xml` — file này tạo ở **Task 7**, nhưng Task 6 (backup) cần trước. Để Task 1 tự chạy được, tạo luôn file tối thiểu ngay bây giờ:

`deploy/infra/clickhouse/backups.xml`:

```xml
<clickhouse>
  <storage_configuration>
    <disks>
      <backups>
        <type>local</type>
        <path>/backups/</path>
      </backups>
    </disks>
  </storage_configuration>
  <backups>
    <allowed_disk>backups</allowed_disk>
    <allowed_path>/backups/</allowed_path>
  </backups>
</clickhouse>
```

- [ ] **Step 4: Chạy test xanh**

`cd backend && uv run pytest tests/clickhouse/test_t01_fixture.py -v`
Expected: 3 PASS (lần đầu có thể chậm ~30s do khởi động container; image đã có sẵn trên máy).

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/tests/clickhouse/ deploy/infra/clickhouse/backups.xml
git commit -m "feat(clickhouse): test fixture with ephemeral CH 26.3.22.7 container"
```

---

### Task 2: Migration runner `core.ch_migrate`

**Files:**
- Create: `backend/core/ch_migrate.py`
- Create: `database/clickhouse/versions/` (thư mục — file SQL thật ở Task 3; test dùng thư mục tạm)
- Test: `backend/tests/clickhouse/test_t02_migrate.py`

**Interfaces:**
- Consumes: fixture `ch` (Task 1).
- Produces: module `core.ch_migrate` với:
  - `get_client(url: str | None = None)` — trả client từ `CLICKHOUSE_URL`.
  - `split_statements(sql: str) -> list[str]`
  - `upgrade(client, versions_dir: Path | None = None) -> list[str]` — trả danh sách version vừa chạy.
  - `applied_versions(client) -> set[str]`
  - `assert_migrated(client, required: str = REQUIRED_CH_MIGRATION) -> None` — raise `RuntimeError` nếu thiếu (hợp đồng khởi động spec §8 — ingester sau này gọi hàm này).
  - Hằng `REQUIRED_CH_MIGRATION = "0002_rt_schema"`.
  - CLI: `uv run python -m core.ch_migrate upgrade` / `status`.

- [ ] **Step 1: Viết test đỏ**

`backend/tests/clickhouse/test_t02_migrate.py`:

```python
from pathlib import Path

import pytest

from core import ch_migrate


def _reset(ch):
    ch.command("DROP DATABASE IF EXISTS rt")


def _write(d: Path, name: str, sql: str) -> None:
    (d / name).write_text(sql, encoding="utf-8")


def test_split_statements_bo_comment_va_rong():
    sql = "-- chi comment\nCREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;\n\n-- nua\n;\nGRANT SELECT ON rt.* TO r1;"
    stmts = ch_migrate.split_statements(sql)
    assert len(stmts) == 2
    assert stmts[0].startswith("-- chi comment")  # comment dính statement sau vô hại
    assert "GRANT SELECT" in stmts[1]


def test_upgrade_bootstrap_va_ap_dung_tuan_tu(ch, tmp_path):
    _reset(ch)
    _write(tmp_path, "0001_a.sql", "CREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;")
    _write(tmp_path, "0002_b.sql", "CREATE TABLE IF NOT EXISTS rt.b (x UInt8) ENGINE = MergeTree ORDER BY x;")
    ran = ch_migrate.upgrade(ch, versions_dir=tmp_path)
    assert ran == ["0001_a", "0002_b"]
    assert ch_migrate.applied_versions(ch) == {"0001_a", "0002_b"}
    # sổ migration dùng ReplacingMergeTree, đọc DISTINCT
    assert ch.command("SELECT engine FROM system.tables WHERE database='rt' AND name='schema_migrations'") == "ReplacingMergeTree"


def test_upgrade_lan_hai_khong_lam_gi(ch, tmp_path):
    _reset(ch)
    _write(tmp_path, "0001_a.sql", "CREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;")
    ch_migrate.upgrade(ch, versions_dir=tmp_path)
    assert ch_migrate.upgrade(ch, versions_dir=tmp_path) == []


def test_file_moi_them_duoc_chay_tiep(ch, tmp_path):
    _reset(ch)
    _write(tmp_path, "0001_a.sql", "CREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;")
    ch_migrate.upgrade(ch, versions_dir=tmp_path)
    _write(tmp_path, "0002_b.sql", "CREATE TABLE IF NOT EXISTS rt.b (x UInt8) ENGINE = MergeTree ORDER BY x;")
    assert ch_migrate.upgrade(ch, versions_dir=tmp_path) == ["0002_b"]


def test_chet_giua_chung_chay_lai_di_qua_duoc(ch, tmp_path):
    """DDL không transaction: statement 1 chạy xong, statement 2 lỗi, sổ chưa ghi.
    Sửa file rồi chạy lại: statement 1 (IF NOT EXISTS) đi qua, version được ghi."""
    _reset(ch)
    _write(tmp_path, "0001_a.sql",
           "CREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;\nSAI CU PHAP;")
    with pytest.raises(Exception):
        ch_migrate.upgrade(ch, versions_dir=tmp_path)
    assert ch_migrate.applied_versions(ch) == set()          # sổ chưa ghi
    assert ch.command("SELECT count() FROM system.tables WHERE database='rt' AND name='a'") == 1
    _write(tmp_path, "0001_a.sql",
           "CREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;")
    assert ch_migrate.upgrade(ch, versions_dir=tmp_path) == ["0001_a"]


def test_assert_migrated(ch, tmp_path):
    _reset(ch)
    _write(tmp_path, "0002_rt_schema.sql", "CREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;")
    with pytest.raises(RuntimeError):
        ch_migrate.assert_migrated(ch)                        # rt chưa tồn tại / sổ trống
    ch_migrate.upgrade(ch, versions_dir=tmp_path)
    ch_migrate.assert_migrated(ch)                            # không raise
```

Chạy: `cd backend && uv run pytest tests/clickhouse/test_t02_migrate.py -v`
Expected: FAIL — `ModuleNotFoundError: core.ch_migrate`.

- [ ] **Step 2: Viết runner**

`backend/core/ch_migrate.py`:

```python
"""Migration runner cho ClickHouse — spec docs/90-records/plans/2026-08-25-clickhouse-realtime-store/spec.md §8.

Không có downgrade. Mọi statement trong versions/ phải idempotent
(DDL không transaction — file chết giữa chừng thì lần chạy lại phải đi qua được).
"""
import os
import re
import sys
from pathlib import Path

import clickhouse_connect

REQUIRED_CH_MIGRATION = "0002_rt_schema"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VERSIONS_DIR = REPO_ROOT / "database" / "clickhouse" / "versions"
_VERSION_RE = re.compile(r"^\d{4}_[a-z0-9_]+$")

_BOOTSTRAP = [
    "CREATE DATABASE IF NOT EXISTS rt",
    "CREATE TABLE IF NOT EXISTS rt.schema_migrations ("
    " version String,"
    " applied_at DateTime('Asia/Ho_Chi_Minh')"
    ") ENGINE = ReplacingMergeTree ORDER BY version",
]


def get_client(url: str | None = None):
    return clickhouse_connect.get_client(dsn=url or os.environ["CLICKHOUSE_URL"])


def split_statements(sql: str) -> list[str]:
    """Tách theo ';'. Quy ước migration: không có ';' trong string literal hay comment."""
    out = []
    for chunk in sql.split(";"):
        lines = [ln for ln in chunk.splitlines() if ln.strip() and not ln.strip().startswith("--")]
        if lines:
            out.append(chunk.strip())
    return out


def _bootstrap(client) -> None:
    for stmt in _BOOTSTRAP:
        client.command(stmt)


def applied_versions(client) -> set[str]:
    _bootstrap(client)
    rows = client.query("SELECT DISTINCT version FROM rt.schema_migrations").result_rows
    return {r[0] for r in rows}


def upgrade(client=None, versions_dir: Path | None = None) -> list[str]:
    client = client or get_client()
    versions_dir = versions_dir or DEFAULT_VERSIONS_DIR
    done = applied_versions(client)
    ran: list[str] = []
    for path in sorted(versions_dir.glob("*.sql")):
        version = path.stem
        if not _VERSION_RE.fullmatch(version):
            raise ValueError(f"Tên file migration sai quy ước NNNN_ten_thuong: {path.name}")
        if version in done:
            continue
        for stmt in split_statements(path.read_text(encoding="utf-8")):
            client.command(stmt)
        client.command(
            f"INSERT INTO rt.schema_migrations (version, applied_at) VALUES ('{version}', now())"
        )
        ran.append(version)
    return ran


def assert_migrated(client, required: str = REQUIRED_CH_MIGRATION) -> None:
    """Hợp đồng khởi động (spec §8): ingester gọi hàm này TRƯỚC khi nối socket."""
    have = applied_versions(client)
    if required not in have:
        raise RuntimeError(
            f"ClickHouse chưa migrate tới {required} (đã có: {sorted(have) or 'rỗng'}). "
            "Chạy: uv run python -m core.ch_migrate upgrade"
        )


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    client = get_client()
    if cmd == "upgrade":
        ran = upgrade(client)
        print(f"đã chạy: {ran or 'không có gì mới'}")
    elif cmd == "status":
        print(f"đã áp dụng: {sorted(applied_versions(client))}")
    else:
        sys.exit(f"lệnh không biết: {cmd} (upgrade | status)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Chạy test xanh**

`cd backend && uv run pytest tests/clickhouse/test_t02_migrate.py -v` — Expected: 6 PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/core/ch_migrate.py backend/tests/clickhouse/test_t02_migrate.py
git commit -m "feat(clickhouse): migration runner with statement-level idempotency"
```

---

### Task 3: Migration 0001 (role/profile) + 0002 (DDL 11 object) + seam DDL/quyền

**Files:**
- Create: `database/clickhouse/versions/0001_roles.sql`
- Create: `database/clickhouse/versions/0002_rt_schema.sql`
- Create: `database/clickhouse/create_users.sql.example`
- Test: `backend/tests/clickhouse/test_t03_schema.py`

**Interfaces:**
- Consumes: `ch_migrate.upgrade` (Task 2).
- Produces: database `rt` đầy đủ 12 object (kể cả sổ); ROLE `dlck_ingester` (kèm SETTINGS PROFILE), `dlck_api`; fixture `migrated` (đặt trong conftest ở step 3) cho Task 4–6 dùng.

- [ ] **Step 1: Viết `0001_roles.sql`**

Thứ tự CỨNG: `CREATE ROLE` trước `CREATE SETTINGS PROFILE … TO role` (spec §5.4 — chiều ngược lỗi `Code: 511`, đo lượt 3). GRANT trước khi bảng tồn tại là hợp lệ và phủ cả bảng tạo sau (đo lượt 3).

```sql
-- Role + profile — spec §6. User login thật KHÔNG ở đây (create_users.sql.example).
CREATE ROLE IF NOT EXISTS dlck_ingester;
CREATE ROLE IF NOT EXISTS dlck_api;

-- Dây đai server-side chống nến đếm đôi khi retry (spec §5.4, đo T9)
CREATE SETTINGS PROFILE IF NOT EXISTS dlck_ingester_profile
  SETTINGS deduplicate_blocks_in_dependent_materialized_views = 1
  TO dlck_ingester;

GRANT SELECT, INSERT ON rt.* TO dlck_ingester;
GRANT SELECT ON rt.* TO dlck_api;
```

- [ ] **Step 2: Viết `0002_rt_schema.sql`**

Chép **nguyên văn** DDL đã kiểm (spec §3–§4, biên bản §12 T11/T14 — khoá argMin 3 thành phần ở `bar_1m`, 2 thành phần `(event_ts, received_at)` ở `index_bar_1m`, dedup window trên cả 5 bảng frame + `bar_1m`, guard `index_value > 0`):

```sql
-- DDL kho realtime — spec §2–§4, đã kiểm trên CH 26.3.22.7 (spec §12).
-- Không sửa file này sau khi đã chạy; sửa = migration kế tiếp.

CREATE TABLE IF NOT EXISTS rt.trade (
  symbol        LowCardinality(String),
  ts            DateTime('Asia/Ho_Chi_Minh'),
  seq           UInt64,
  price         Decimal64(2),
  volume        UInt64,
  side          LowCardinality(String),
  change        Decimal64(2),
  cum_volume    UInt64,
  cum_value     Decimal64(2),
  received_at   DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, seq)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;

CREATE TABLE IF NOT EXISTS rt.quote (
  symbol      LowCardinality(String),
  ts          DateTime64(3, 'Asia/Ho_Chi_Minh'),
  top         UInt8,
  action      LowCardinality(String),
  bid_price   Decimal64(2),
  bid_qty     UInt64,
  ask_price   Decimal64(2),
  ask_qty     UInt64,
  cum_bid     UInt64,
  cum_ask     UInt64,
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, top)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;

CREATE TABLE IF NOT EXISTS rt.snapshot_delta (
  symbol      LowCardinality(String),
  exchange    LowCardinality(String),
  ts          DateTime64(3, 'Asia/Ho_Chi_Minh'),
  b1 Nullable(Decimal64(2)), b2 Nullable(Decimal64(2)), b3 Nullable(Decimal64(2)),
  v1 Nullable(UInt64),       v2 Nullable(UInt64),       v3 Nullable(UInt64),
  s1 Nullable(Decimal64(2)), s2 Nullable(Decimal64(2)), s3 Nullable(Decimal64(2)),
  u1 Nullable(UInt64),       u2 Nullable(UInt64),       u3 Nullable(UInt64),
  total_bid   Nullable(UInt64),
  total_offer Nullable(UInt64),
  close_price Nullable(Decimal64(2)),
  change      Nullable(Decimal64(2)),
  change_pct  Nullable(Decimal64(2)),
  avg_price   Nullable(Decimal64(2)),
  high        Nullable(Decimal64(2)),
  last_vol    Nullable(UInt64),
  last_vol2   Nullable(UInt64),
  last_price  Nullable(Decimal64(2)),
  total_vol   Nullable(UInt64),
  total_value Nullable(Decimal64(2)),
  foreign_buy    Nullable(UInt64),
  foreign_sell   Nullable(UInt64),
  foreign_remain Nullable(UInt64),
  pt_price     Nullable(Decimal64(2)),
  pt_qty       Nullable(UInt64),
  pt_total_qty Nullable(UInt64),
  pt_total_val Nullable(Decimal64(2)),
  extra       String DEFAULT '',
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;

CREATE TABLE IF NOT EXISTS rt.index_delta (
  symbol      LowCardinality(String),
  ts          DateTime64(3, 'Asia/Ho_Chi_Minh'),
  index_value Nullable(Decimal64(2)),
  change      Nullable(Decimal64(2)),
  change_pct  Nullable(Decimal64(2)),
  total_vol   Nullable(UInt64),
  total_value Nullable(Decimal64(2)),
  advances    Nullable(UInt16),
  declines    Nullable(UInt16),
  unchanged   Nullable(UInt16),
  ceiling_cnt Nullable(UInt16),
  adv_vol     Nullable(UInt64),
  dec_vol     Nullable(UInt64),
  unch_vol    Nullable(UInt64),
  pt_total    Nullable(UInt64),
  pt_value    Nullable(Decimal64(2)),
  extra       String DEFAULT '',
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;

CREATE TABLE IF NOT EXISTS rt.pt_match (
  symbol      LowCardinality(String),
  market      LowCardinality(String),
  ts          DateTime('Asia/Ho_Chi_Minh'),
  price       Decimal64(2),
  volume      UInt64,
  ref_price   Nullable(Decimal64(2)),
  ceil_price  Nullable(Decimal64(2)),
  floor_price Nullable(Decimal64(2)),
  order_id    String,
  extra       String DEFAULT '',
  received_at DateTime64(3, 'Asia/Ho_Chi_Minh') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(toDate(ts))
ORDER BY (symbol, ts, order_id)
TTL toDate(ts) + INTERVAL 3 MONTH DELETE
SETTINGS ttl_only_drop_parts = 1, non_replicated_deduplication_window = 100;

CREATE TABLE IF NOT EXISTS rt.bar_1m (
  symbol LowCardinality(String),
  ts     DateTime('Asia/Ho_Chi_Minh'),
  o    AggregateFunction(argMin, Decimal64(2), Tuple(DateTime('Asia/Ho_Chi_Minh'), UInt64, DateTime64(3, 'Asia/Ho_Chi_Minh'))),
  h    AggregateFunction(max, Decimal64(2)),
  l    AggregateFunction(min, Decimal64(2)),
  c    AggregateFunction(argMax, Decimal64(2), Tuple(DateTime('Asia/Ho_Chi_Minh'), UInt64, DateTime64(3, 'Asia/Ho_Chi_Minh'))),
  v    AggregateFunction(sum, UInt64),
  val  AggregateFunction(sum, Decimal128(2)),
  v_bu AggregateFunction(sum, UInt64),
  v_sd AggregateFunction(sum, UInt64)
)
ENGINE = AggregatingMergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (symbol, ts)
SETTINGS non_replicated_deduplication_window = 100;

CREATE MATERIALIZED VIEW IF NOT EXISTS rt.mv_trade_to_bar_1m TO rt.bar_1m AS
SELECT
  symbol,
  toStartOfMinute(event_ts)                            AS ts,
  argMinState(price, (event_ts, seq, received_at))     AS o,
  maxState(price)                                      AS h,
  minState(price)                                      AS l,
  argMaxState(price, (event_ts, seq, received_at))     AS c,
  sumState(volume)                                     AS v,
  sumState(toDecimal128(price, 2) * volume)            AS val,
  sumState(if(side = 'B', volume, toUInt64(0)))        AS v_bu,
  sumState(if(side = 'S', volume, toUInt64(0)))        AS v_sd
FROM (SELECT symbol, ts AS event_ts, seq, price, volume, side, received_at FROM rt.trade)
GROUP BY symbol, ts;

CREATE VIEW IF NOT EXISTS rt.bar_1m_v AS
SELECT symbol, ts,
       argMinMerge(o) AS o, maxMerge(h) AS h, minMerge(l) AS l, argMaxMerge(c) AS c,
       sumMerge(v) AS v, sumMerge(val) AS val,
       sumMerge(v_bu) AS v_bu, sumMerge(v_sd) AS v_sd
FROM rt.bar_1m
GROUP BY symbol, ts;

CREATE TABLE IF NOT EXISTS rt.index_bar_1m (
  symbol LowCardinality(String),
  ts     DateTime('Asia/Ho_Chi_Minh'),
  o AggregateFunction(argMin, Decimal64(2), Tuple(DateTime64(3, 'Asia/Ho_Chi_Minh'), DateTime64(3, 'Asia/Ho_Chi_Minh'))),
  h AggregateFunction(max, Decimal64(2)),
  l AggregateFunction(min, Decimal64(2)),
  c AggregateFunction(argMax, Decimal64(2), Tuple(DateTime64(3, 'Asia/Ho_Chi_Minh'), DateTime64(3, 'Asia/Ho_Chi_Minh'))),
  cum_vol   AggregateFunction(max, Nullable(UInt64)),
  cum_value AggregateFunction(max, Nullable(Decimal64(2)))
)
ENGINE = AggregatingMergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (symbol, ts);

CREATE MATERIALIZED VIEW IF NOT EXISTS rt.mv_index_to_bar_1m TO rt.index_bar_1m AS
SELECT
  symbol,
  toStartOfMinute(toDateTime(event_ts))                             AS ts,
  argMinState(assumeNotNull(index_value), (event_ts, received_at))  AS o,
  maxState(assumeNotNull(index_value))                              AS h,
  minState(assumeNotNull(index_value))                              AS l,
  argMaxState(assumeNotNull(index_value), (event_ts, received_at))  AS c,
  maxState(total_vol)                                               AS cum_vol,
  maxState(total_value)                                             AS cum_value
FROM (SELECT symbol, ts AS event_ts, index_value, total_vol, total_value, received_at
      FROM rt.index_delta WHERE index_value IS NOT NULL AND index_value > 0)
GROUP BY symbol, ts;

CREATE VIEW IF NOT EXISTS rt.index_bar_1m_v AS
SELECT symbol, ts,
       argMinMerge(o) AS o, maxMerge(h) AS h, minMerge(l) AS l, argMaxMerge(c) AS c,
       maxMerge(cum_vol) AS cum_vol, maxMerge(cum_value) AS cum_value
FROM rt.index_bar_1m
GROUP BY symbol, ts;
```

- [ ] **Step 3: Thêm fixture `migrated` vào conftest**

Thêm cuối `backend/tests/clickhouse/conftest.py`:

```python
@pytest.fixture()
def migrated(ch):
    """Đảm bảo đã upgrade (idempotent — chạy lại là no-op). Test dùng symbol riêng để cách ly."""
    from core import ch_migrate
    ch_migrate.upgrade(ch)
    return ch
```

Và helper **ngày động** (luật CLAUDE.md §4.4.4 — tiêu chí phải bất biến theo thời gian: ngày cứng sẽ rơi khỏi cửa sổ TTL 3 tháng và bị loại ngay tại INSERT, spec §12/T13):

```python
from datetime import date, datetime, timedelta

TODAY = date.today()


def dt_ago(days: int, h: int = 9, m: int = 15, s: int = 1, micro: int = 0) -> datetime:
    d = TODAY - timedelta(days=days)
    return datetime(d.year, d.month, d.day, h, m, s, micro)


def part_of(dt: datetime) -> str:
    return dt.strftime("%Y%m")
```

- [ ] **Step 4: Viết test đỏ seam DDL + quyền**

`backend/tests/clickhouse/test_t03_schema.py`:

```python
import uuid

import clickhouse_connect
import pytest

EXPECTED_OBJECTS = {
    "trade": "MergeTree", "quote": "MergeTree", "snapshot_delta": "MergeTree",
    "index_delta": "MergeTree", "pt_match": "MergeTree",
    "bar_1m": "AggregatingMergeTree", "index_bar_1m": "AggregatingMergeTree",
    "schema_migrations": "ReplacingMergeTree",
    "mv_trade_to_bar_1m": "MaterializedView", "mv_index_to_bar_1m": "MaterializedView",
    "bar_1m_v": "View", "index_bar_1m_v": "View",
}


def test_du_12_object_dung_engine(migrated):
    rows = migrated.query("SELECT name, engine FROM system.tables WHERE database='rt'").result_rows
    assert {r[0]: r[1] for r in rows} == EXPECTED_OBJECTS


def test_create_table_query_khop_ky_vong_chong_drift(migrated):
    """IF NOT EXISTS che drift — đối chiếu định nghĩa thật với các mảnh bất biến (spec §8)."""
    ddl = {r[0]: r[1] for r in migrated.query(
        "SELECT name, create_table_query FROM system.tables WHERE database='rt'").result_rows}
    for t in ["trade", "quote", "snapshot_delta", "index_delta", "pt_match"]:
        assert "TTL toDate(ts) + toIntervalMonth(3)" in ddl[t]
        assert "ttl_only_drop_parts = 1" in ddl[t]
        assert "non_replicated_deduplication_window = 100" in ddl[t]
    assert "non_replicated_deduplication_window = 100" in ddl["bar_1m"]
    assert "TTL" not in ddl["bar_1m"] and "TTL" not in ddl["index_bar_1m"]
    assert "Tuple(DateTime('Asia/Ho_Chi_Minh'), UInt64, DateTime64(3, 'Asia/Ho_Chi_Minh'))" in ddl["bar_1m"]
    assert "Tuple(DateTime64(3, 'Asia/Ho_Chi_Minh'), DateTime64(3, 'Asia/Ho_Chi_Minh'))" in ddl["index_bar_1m"]
    assert "index_value > 0" in ddl["mv_index_to_bar_1m"]


def test_profile_gan_role_ingester(migrated):
    row = migrated.query(
        "SELECT value FROM system.settings_profile_elements WHERE profile_name='dlck_ingester_profile'"
        " AND setting_name='deduplicate_blocks_in_dependent_materialized_views'").result_rows
    assert row and str(row[0][0]) == "1"


@pytest.fixture()
def api_user(migrated):
    name = f"t_api_{uuid.uuid4().hex[:6]}"
    migrated.command(f"CREATE USER {name} IDENTIFIED WITH plaintext_password BY 'x' DEFAULT ROLE dlck_api")
    yield name
    migrated.command(f"DROP USER IF EXISTS {name}")


def test_quyen_dlck_api(migrated, api_user):
    import os
    base = os.environ["CLICKHOUSE_URL"].rsplit("@", 1)[1]      # 127.0.0.1:PORT
    c = clickhouse_connect.get_client(dsn=f"http://{api_user}:x@{base}")
    assert c.command("SELECT count() >= 0 FROM rt.bar_1m_v") in (0, 1)   # SELECT qua view được
    with pytest.raises(Exception):
        c.command("INSERT INTO rt.trade (symbol, ts, seq, price, volume, side, change, cum_volume, cum_value) VALUES ('X', now(), 1, 1, 1, 'B', 0, 1, 1)")
    with pytest.raises(Exception):
        c.command("DROP TABLE rt.trade")
    dbs = [r[0] for r in c.query("SHOW DATABASES").result_rows]
    assert "rt" in dbs and all(d in ("rt", "system", "INFORMATION_SCHEMA", "information_schema", "default") for d in dbs)
```

Chạy: `cd backend && uv run pytest tests/clickhouse/test_t03_schema.py -v`
Expected: FAIL (chưa có file versions thật → thiếu object).

Ghi chú cho người thực thi: hai assertion chuỗi trong `test_create_table_query_khop_ky_vong_chong_drift` (dạng `toIntervalMonth(3)` và format Tuple) là **định dạng CH chuẩn hoá lại DDL** — nếu đỏ vì format khác, chạy `SELECT create_table_query` bằng tay, đối chiếu ngữ nghĩa với spec rồi chỉnh **chuỗi expected trong test** theo format thật (KHÔNG chỉnh DDL), ghi vào ledger.

- [ ] **Step 5: Tạo hai file versions (nội dung ở Step 1–2) rồi chạy test xanh**

`cd backend && uv run pytest tests/clickhouse/test_t03_schema.py -v` — Expected: PASS toàn bộ.

- [ ] **Step 6: Viết `database/clickhouse/create_users.sql.example`**

```sql
-- Template tạo user login per-môi-trường (spec §6) — KHÔNG commit bản có mật khẩu thật.
-- Chạy bằng user quản trị:  clickhouse-client --password ... --multiquery < create_users.sql
CREATE USER IF NOT EXISTS ingester_worker IDENTIFIED WITH sha256_password BY 'CHANGE-ME' DEFAULT ROLE dlck_ingester;
CREATE USER IF NOT EXISTS api_reader     IDENTIFIED WITH sha256_password BY 'CHANGE-ME' DEFAULT ROLE dlck_api;
```

- [ ] **Step 7: Commit**

```bash
git add database/clickhouse/ backend/tests/clickhouse/
git commit -m "feat(clickhouse): rt schema migrations 0001-0002 with roles and verified DDL"
```

---

### Task 4: Seam MV nến — cổ phiếu và chỉ số

**Files:**
- Test: `backend/tests/clickhouse/test_t04_bars.py`

**Interfaces:**
- Consumes: fixture `migrated` (Task 3). Mỗi test dùng symbol riêng (không reset DB).

- [ ] **Step 1: Viết test (đỏ trước khi có DDL thì Task 3 đã lo; ở đây test hành vi — vẫn viết từng test, chạy, xác nhận PASS vì DDL đã đúng; nếu FAIL tức DDL sai, phải dừng báo)**

`backend/tests/clickhouse/test_t04_bars.py` — expected là **giải tay** (trùng biên bản spec §12 T1/T2/T3/T14, đã kiểm độc lập trên CH thật):

```python
from decimal import Decimal

from tests.clickhouse.conftest import dt_ago

IDX_COLS = ["symbol", "ts", "index_value", "total_vol", "total_value", "received_at"]


def _ins_trade(ch, rows):
    ch.insert(
        "rt.trade", rows,
        column_names=["symbol", "ts", "seq", "price", "volume", "side",
                      "change", "cum_volume", "cum_value", "received_at"],
        settings={"insert_deduplicate": 0},   # test hành vi MV, không test dedup ở đây
    )


def test_bar_1m_giai_tay(migrated):
    """3 tick một phút: (s+1,seq5,100.00,100,B) (s+2,seq7,101.00,200,S) (s+59,seq9,99.00,50,B)
    → o=100 h=101 l=99 c=99 v=350 val=10000+20200+4950=35150 v_bu=150 v_sd=200 (spec §12 T1)."""
    rows = [
        ["TBID", dt_ago(6, 9, 15, 1), 5, Decimal("100.00"), 100, "B", Decimal("0.00"), 100, Decimal("10000.00"), dt_ago(6, 9, 15, 1, 100000)],
        ["TBID", dt_ago(6, 9, 15, 2), 7, Decimal("101.00"), 200, "S", Decimal("1.00"), 300, Decimal("30200.00"), dt_ago(6, 9, 15, 2, 100000)],
        ["TBID", dt_ago(6, 9, 15, 59), 9, Decimal("99.00"), 50, "B", Decimal("-1.00"), 350, Decimal("35150.00"), dt_ago(6, 9, 15, 59, 100000)],
    ]
    _ins_trade(migrated, rows[:1])
    _ins_trade(migrated, rows[1:])            # rải 2 block cùng phút — state phải gộp đúng
    r = migrated.query("SELECT o, h, l, c, v, val, v_bu, v_sd FROM rt.bar_1m_v WHERE symbol='TBID'").result_rows
    assert r == [(Decimal("100.00"), Decimal("101.00"), Decimal("99.00"), Decimal("99.00"),
                  350, Decimal("35150.00"), 150, 200)]


def test_side_la_vao_v_khong_vao_bu_sd(migrated):
    _ins_trade(migrated, [["TVNM", dt_ago(6, 9, 16, 10), 11, Decimal("50.00"), 30, "X",
                           Decimal("0.00"), 30, Decimal("1500.00"), dt_ago(6, 9, 16, 10)]])
    r = migrated.query("SELECT v, v_bu, v_sd FROM rt.bar_1m_v WHERE symbol='TVNM'").result_rows
    assert r == [(30, 0, 0)]


def test_o_c_on_dinh_qua_merge_khi_hoa_ts_seq(migrated):
    """Khoá total (ts, seq, received_at) — spec §4.1, đo T12: hai tick hoà (ts,seq) khác received_at."""
    _ins_trade(migrated, [["TTIE", dt_ago(6, 9, 17, 10), 7, Decimal("100.00"), 10, "B",
                           Decimal("0.00"), 10, Decimal("1000.00"), dt_ago(6, 9, 17, 10, 100000)]])
    _ins_trade(migrated, [["TTIE", dt_ago(6, 9, 17, 10), 7, Decimal("200.00"), 20, "B",
                           Decimal("0.00"), 30, Decimal("5000.00"), dt_ago(6, 9, 17, 10, 250000)]])
    before = migrated.query("SELECT o, c FROM rt.bar_1m_v WHERE symbol='TTIE'").result_rows
    migrated.command("OPTIMIZE TABLE rt.bar_1m FINAL")
    after = migrated.query("SELECT o, c FROM rt.bar_1m_v WHERE symbol='TTIE'").result_rows
    assert before == after == [(Decimal("100.00"), Decimal("200.00"))]


def test_index_bar_null_khong_thanh_0(migrated):
    """Phút không frame nào mang TV → cum_vol NULL (spec §4.2, đo T3)."""
    migrated.insert("rt.index_delta",
        [["THOSE", dt_ago(6, 9, 20, 5), Decimal("1300.50"), None, None, dt_ago(6, 9, 20, 5)],
         ["THOSE", dt_ago(6, 9, 20, 35), Decimal("1301.20"), None, None, dt_ago(6, 9, 20, 35)]],
        column_names=IDX_COLS)
    migrated.insert("rt.index_delta",
        [["THOSE", dt_ago(6, 9, 21, 5), Decimal("1302.00"), 500000, Decimal("12000000.00"), dt_ago(6, 9, 21, 5)]],
        column_names=IDX_COLS)
    r = migrated.query(
        "SELECT ts, o, c, cum_vol, cum_value FROM rt.index_bar_1m_v WHERE symbol='THOSE' ORDER BY ts").result_rows
    assert r[0][3] is None and r[0][4] is None          # phút đầu — NULL, không phải 0
    assert r[1][3] == 500000 and r[1][4] == Decimal("12000000.00")


def test_index_guard_mi_bang_0_khong_sinh_nen(migrated):
    migrated.insert("rt.index_delta",
        [["TGRD", dt_ago(6, 8, 50, 0), Decimal("0.00"), None, None, dt_ago(6, 8, 50, 0)]],
        column_names=IDX_COLS)
    assert migrated.query("SELECT count() FROM rt.index_bar_1m_v WHERE symbol='TGRD'").result_rows[0][0] == 0


def test_index_o_c_on_dinh_qua_merge_khi_hoa_ms(migrated):
    """Khoá total (event_ts, received_at) — spec §4.2, đo T14: hai frame hoà mili-giây."""
    migrated.insert("rt.index_delta",
        [["THNX", dt_ago(6, 13, 9, 0, 500000), Decimal("700.00"), None, None, dt_ago(6, 13, 9, 0, 600000)]],
        column_names=IDX_COLS)
    migrated.insert("rt.index_delta",
        [["THNX", dt_ago(6, 13, 9, 0, 500000), Decimal("800.00"), None, None, dt_ago(6, 13, 9, 0, 700000)]],
        column_names=IDX_COLS)
    before = migrated.query("SELECT o, c FROM rt.index_bar_1m_v WHERE symbol='THNX'").result_rows
    migrated.command("OPTIMIZE TABLE rt.index_bar_1m FINAL")
    after = migrated.query("SELECT o, c FROM rt.index_bar_1m_v WHERE symbol='THNX'").result_rows
    assert before == after == [(Decimal("700.00"), Decimal("800.00"))]
```

⚠️ Lưu ý datetime: client `clickhouse-connect` gửi datetime naive theo cột đã khai tz `Asia/Ho_Chi_Minh`, container chạy `TZ=Asia/Ho_Chi_Minh`. Ngày test là **`dt_ago(...)` động** — không được thay bằng ngày cứng: dòng quá cửa sổ TTL bị loại ngay tại INSERT (spec §12/T13), ngày cứng sẽ làm bộ test tự đỏ sau 3 tháng.

- [ ] **Step 2: Chạy** `cd backend && uv run pytest tests/clickhouse/test_t04_bars.py -v` — Expected: 6 PASS. Nếu bất kỳ test nào FAIL: **dừng, không sửa expected** — expected là số giải tay đã kiểm; FAIL nghĩa là DDL/môi trường sai, báo lại controller.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/clickhouse/test_t04_bars.py
git commit -m "test(clickhouse): candle MV seams - hand-solved OHLCV, null semantics, total-order keys"
```

---

### Task 5: Seam dedup block + TTL + thủ tục sửa nến

**Files:**
- Test: `backend/tests/clickhouse/test_t05_dedup_ttl.py`

**Interfaces:**
- Consumes: fixture `migrated`, user role từ 0001.

- [ ] **Step 1: Viết test**

`backend/tests/clickhouse/test_t05_dedup_ttl.py`:

```python
import os
import uuid
from decimal import Decimal

import clickhouse_connect
import pytest

from tests.clickhouse.conftest import dt_ago, part_of

COLS = ["symbol", "ts", "seq", "price", "volume", "side", "change", "cum_volume", "cum_value", "received_at"]


@pytest.fixture()
def ing_client(migrated):
    """Client nối bằng user gắn role dlck_ingester — dedup dựa PROFILE, KHÔNG truyền setting phía client."""
    name = f"t_ing_{uuid.uuid4().hex[:6]}"
    migrated.command(f"CREATE USER {name} IDENTIFIED WITH plaintext_password BY 'x' DEFAULT ROLE dlck_ingester")
    base = os.environ["CLICKHOUSE_URL"].rsplit("@", 1)[1]
    c = clickhouse_connect.get_client(dsn=f"http://{name}:x@{base}")
    yield c
    migrated.command(f"DROP USER IF EXISTS {name}")


def test_retry_nguyen_block_bi_nuot_ca_trade_lan_nen(migrated, ing_client):
    """Spec §5.4 + §12 T4/T9: retry block y nguyên → trade không thêm dòng, nến không đếm đôi."""
    row = [["TDDP", dt_ago(6, 10, 0, 1), 1, Decimal("100.00"), 100, "B",
            Decimal("0.00"), 100, Decimal("10000.00"), dt_ago(6, 10, 30, 0)]]
    ing_client.insert("rt.trade", row, column_names=COLS)
    ing_client.insert("rt.trade", row, column_names=COLS)          # retry giả lập
    assert migrated.query("SELECT count() FROM rt.trade WHERE symbol='TDDP'").result_rows[0][0] == 1
    assert migrated.query("SELECT v FROM rt.bar_1m_v WHERE symbol='TDDP'").result_rows == [(100,)]


def test_block_khac_noi_dung_trung_khoa_van_ghi(migrated, ing_client):
    """Dedup theo hash block, không theo khoá."""
    r1 = [["TDD2", dt_ago(6, 10, 1, 1), 1, Decimal("100.00"), 100, "B",
           Decimal("0.00"), 100, Decimal("10000.00"), dt_ago(6, 10, 30, 0)]]
    r2 = [["TDD2", dt_ago(6, 10, 1, 1), 1, Decimal("100.00"), 999, "B",
           Decimal("0.00"), 100, Decimal("10000.00"), dt_ago(6, 10, 30, 0)]]
    ing_client.insert("rt.trade", r1, column_names=COLS)
    ing_client.insert("rt.trade", r2, column_names=COLS)
    assert migrated.query("SELECT count() FROM rt.trade WHERE symbol='TDD2'").result_rows[0][0] == 2


def test_ttl_part_level(migrated):
    """Spec §2 + §12 T5/T13: dòng ~5 tháng tuổi bị TTL loại (tại INSERT hoặc MATERIALIZE);
    dòng ~1 tháng còn; nến sinh từ tick cũ (không TTL) vẫn còn sau OPTIMIZE FINAL."""
    migrated.insert("rt.trade",
        [["TOLD", dt_ago(150, 10, 0, 0), 1, Decimal("10.00"), 10, "B", Decimal("0.00"), 10, Decimal("100.00"), dt_ago(150, 10, 0, 0)],
         ["TOLD", dt_ago(30, 10, 0, 0), 2, Decimal("11.00"), 20, "S", Decimal("0.00"), 30, Decimal("320.00"), dt_ago(30, 10, 0, 0)]],
        column_names=COLS, settings={"insert_deduplicate": 0})
    migrated.command("ALTER TABLE rt.trade MATERIALIZE TTL SETTINGS mutations_sync = 2")
    rows = migrated.query("SELECT ts, price FROM rt.trade WHERE symbol='TOLD' ORDER BY ts").result_rows
    assert len(rows) == 1 and rows[0][1] == Decimal("11.00")
    # bảng nến không TTL: dòng bar sinh từ tick cũ (MV chạy trước khi part bị loại) phải còn
    migrated.command("OPTIMIZE TABLE rt.bar_1m FINAL")
    assert migrated.query("SELECT count() FROM rt.bar_1m_v WHERE symbol='TOLD'").result_rows[0][0] == 2


def test_sua_nen_voi_token(migrated):
    """Thủ tục §4.1 + §12 T13: DROP PARTITION → backfill có token → retry cùng token bị nuốt."""
    d = dt_ago(6, 9, 30, 1)
    part = part_of(d)
    migrated.insert("rt.trade",
        [["TREP", d, 1, Decimal("100.00"), 10, "B",
          Decimal("0.00"), 10, Decimal("1000.00"), d]],
        column_names=COLS, settings={"insert_deduplicate": 0})
    migrated.command(f"ALTER TABLE rt.bar_1m DROP PARTITION {part}")
    backfill = f"""
      INSERT INTO rt.bar_1m
      SELECT symbol, toStartOfMinute(event_ts) AS ts,
             argMinState(price, (event_ts, seq, received_at)) AS o,
             maxState(price) AS h, minState(price) AS l,
             argMaxState(price, (event_ts, seq, received_at)) AS c,
             sumState(volume) AS v, sumState(toDecimal128(price, 2) * volume) AS val,
             sumState(if(side = 'B', volume, toUInt64(0))) AS v_bu,
             sumState(if(side = 'S', volume, toUInt64(0))) AS v_sd
      FROM (SELECT symbol, ts AS event_ts, seq, price, volume, side, received_at
            FROM rt.trade WHERE toYYYYMM(toDate(ts)) = {part})
      GROUP BY symbol, ts
    """
    tok = {"insert_deduplication_token": f"repair-{part}-test1"}
    migrated.command(backfill, settings=tok)
    migrated.command(backfill, settings=tok)               # retry cùng token → bị nuốt
    assert migrated.query("SELECT v FROM rt.bar_1m_v WHERE symbol='TREP'").result_rows == [(10,)]
```

⚠️ Test cuối **gom lại cả partition** (mọi symbol cùng tháng của các test trước trong session) — vì thế chỉ assert symbol của chính nó, không assert count toàn bảng.

- [ ] **Step 2: Chạy** `cd backend && uv run pytest tests/clickhouse/test_t05_dedup_ttl.py -v` — Expected: 4 PASS. FAIL nào cũng là dừng-và-báo (expected từ biên bản đo, không được sửa).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/clickhouse/test_t05_dedup_ttl.py
git commit -m "test(clickhouse): dedup window, part-level TTL, repair-with-token seams"
```

---

### Task 6: Script backup `core.ch_backup` (quyết định #10)

**Files:**
- Create: `backend/core/ch_backup.py`
- Test: `backend/tests/clickhouse/test_t06_backup.py`

**Interfaces:**
- Consumes: fixture `ch`/`migrated` + `ch_backup_dir` (Task 1 — thư mục host mount vào `/backups` của container).
- Produces: `run_backup(client, backup_dir: Path, today: date) -> list[str]` (danh sách hành động); CLI `uv run python -m core.ch_backup` (env `CLICKHOUSE_URL`, `CLICKHOUSE_BACKUP_DIR`). Lịch hoá: chạy tay ở dev; khi deploy Linux thì cron gọi lệnh này sau 15:30 — ghi ở README (Task 8).

- [ ] **Step 1: Viết test đỏ**

`backend/tests/clickhouse/test_t06_backup.py`:

```python
from datetime import timedelta
from decimal import Decimal

from core import ch_backup
from tests.clickhouse.conftest import TODAY, dt_ago, part_of

COLS = ["symbol", "ts", "seq", "price", "volume", "side", "change", "cum_volume", "cum_value", "received_at"]

PM = part_of(dt_ago(45))                  # partition tháng ĐÃ ĐÓNG (45 ngày trước luôn khác tháng hiện tại)
CUR = TODAY.strftime("%Y%m")
STAMP = TODAY.strftime("%Y%m%d")
STAMP2 = (TODAY + timedelta(days=1)).strftime("%Y%m%d")


def _seed(ch):
    ch.insert("rt.trade",
        [["TBK", dt_ago(45, 9, 15, 1), 1, Decimal("50.00"), 10, "B", Decimal("0.00"), 10, Decimal("500.00"), dt_ago(45, 9, 15, 1)],
         ["TBK", dt_ago(0, 9, 15, 1), 2, Decimal("60.00"), 20, "S", Decimal("0.00"), 30, Decimal("1700.00"), dt_ago(0, 9, 15, 1)]],
        column_names=COLS, settings={"insert_deduplicate": 0})


def test_backup_lan_dau_thang_dong_mot_lan_thang_mo_theo_ngay(migrated, ch_backup_dir):
    _seed(migrated)
    ch_backup.run_backup(migrated, ch_backup_dir, today=TODAY)
    names = {p.name for p in ch_backup_dir.iterdir()}
    assert f"trade-{PM}.zip" in names                      # tháng đóng — tên không ngày
    assert f"trade-{CUR}-{STAMP}.zip" in names             # tháng mở — tên theo ngày
    assert f"bar_1m-{STAMP}.zip" in names                  # bảng nến full
    assert f"index_bar_1m-{STAMP}.zip" in names


def test_chay_lai_cung_ngay_khong_lam_gi(migrated, ch_backup_dir):
    ch_backup.run_backup(migrated, ch_backup_dir, today=TODAY)
    a2 = ch_backup.run_backup(migrated, ch_backup_dir, today=TODAY)
    assert a2 == []                                        # idempotent trong ngày


def test_ngay_moi_de_ban_thang_mo_xoa_ban_cu(migrated, ch_backup_dir):
    ch_backup.run_backup(migrated, ch_backup_dir, today=TODAY)
    ch_backup.run_backup(migrated, ch_backup_dir, today=TODAY + timedelta(days=1))
    names = {p.name for p in ch_backup_dir.iterdir()}
    assert f"trade-{CUR}-{STAMP2}.zip" in names or (TODAY + timedelta(days=1)).strftime("%Y%m") != CUR
    assert f"trade-{CUR}-{STAMP}.zip" not in names         # bản cũ của tháng mở đã xoá (hoặc tháng vừa đóng — cũng xoá daily)
    assert f"trade-{PM}.zip" in names                      # tháng đóng không chép lại


def test_restore_partition_du_dong_khong_kich_mv(migrated, ch_backup_dir):
    """Spec §12 T15: RESTORE cần allow_non_empty_tables, gắn part trực tiếp — nến không đổi."""
    ch_backup.run_backup(migrated, ch_backup_dir, today=TODAY)
    bars_before = migrated.query("SELECT count() FROM rt.bar_1m_v").result_rows[0][0]
    migrated.command(f"ALTER TABLE rt.trade DROP PARTITION {PM}")
    migrated.command(f"RESTORE TABLE rt.trade PARTITION '{PM}' FROM Disk('backups', 'trade-{PM}.zip')"
                     " SETTINGS allow_non_empty_tables = true")
    assert migrated.query("SELECT count() FROM rt.trade WHERE symbol='TBK'").result_rows[0][0] == 2
    assert migrated.query("SELECT count() FROM rt.bar_1m_v").result_rows[0][0] == bars_before
```

*(Ngày động theo luật §4.4.4 — xem chú thích Task 4. `dt_ago(45)` luôn rơi vào tháng đã đóng; hàng seed tháng hiện tại dùng `dt_ago(0)` = hôm nay.)*

Chạy: `cd backend && uv run pytest tests/clickhouse/test_t06_backup.py -v`
Expected: FAIL — `ModuleNotFoundError: core.ch_backup`.

- [ ] **Step 2: Viết script**

`backend/core/ch_backup.py`:

```python
"""Backup hằng đêm theo quyết định #10 của spec ClickHouse realtime store.

Hai lớp: (a) hai bảng nến vĩnh viễn — full backup mỗi ngày, giữ 7 bản gần nhất
+ mọi bản ngày 01; (b) 5 bảng frame — theo partition tháng, lăn theo cửa sổ TTL:
tháng đóng backup một lần, tháng mở đè mỗi ngày (ghi tên mới → xoá bản cũ),
partition đã TTL drop thì xoá file backup. Dung lượng chặn trên ≈ 1× cửa sổ.
"""
import os
import re
from datetime import date
from pathlib import Path

BAR_TABLES = ["bar_1m", "index_bar_1m"]
FRAME_TABLES = ["trade", "quote", "snapshot_delta", "index_delta", "pt_match"]
_PART_RE = re.compile(r"^\d{6}$")


def _active_partitions(client, table: str) -> set[str]:
    rows = client.query(
        "SELECT DISTINCT partition FROM system.parts"
        " WHERE database = 'rt' AND table = %(t)s AND active", parameters={"t": table}
    ).result_rows
    return {r[0] for r in rows if _PART_RE.fullmatch(str(r[0]))}


def _prune_bars(backup_dir: Path, table: str, keep: int = 7) -> list[str]:
    files = sorted(backup_dir.glob(f"{table}-????????.zip"), reverse=True)
    removed = []
    for f in files[keep:]:
        day = f.stem.rsplit("-", 1)[1]
        if day.endswith("01"):                     # giữ bản đầu tháng
            continue
        f.unlink()
        removed.append(f"prune:{f.name}")
    return removed


def run_backup(client, backup_dir: Path, today: date | None = None) -> list[str]:
    today = today or date.today()
    stamp = today.strftime("%Y%m%d")
    cur_month = today.strftime("%Y%m")
    actions: list[str] = []

    for t in BAR_TABLES:                                          # (a) nến — full mỗi ngày
        fname = f"{t}-{stamp}.zip"
        if not (backup_dir / fname).exists():
            client.command(f"BACKUP TABLE rt.{t} TO Disk('backups', '{fname}')")
            actions.append(fname)
        actions += _prune_bars(backup_dir, t)

    for t in FRAME_TABLES:                                        # (b) frame — theo partition
        parts = _active_partitions(client, t)
        for p in sorted(parts):
            if p == cur_month:
                fname = f"{t}-{p}-{stamp}.zip"
                if not (backup_dir / fname).exists():
                    client.command(f"BACKUP TABLE rt.{t} PARTITION '{p}' TO Disk('backups', '{fname}')")
                    for old in backup_dir.glob(f"{t}-{p}-????????.zip"):
                        if old.name != fname:
                            old.unlink()
                    actions.append(fname)
            else:
                fname = f"{t}-{p}.zip"
                if not (backup_dir / fname).exists():
                    client.command(f"BACKUP TABLE rt.{t} PARTITION '{p}' TO Disk('backups', '{fname}')")
                    for old in backup_dir.glob(f"{t}-{p}-????????.zip"):
                        old.unlink()                              # bản daily khi tháng còn mở
                    actions.append(fname)
        for f in backup_dir.glob(f"{t}-*.zip"):                   # (c) prune partition đã TTL drop
            m = re.fullmatch(rf"{t}-(\d{{6}})(-\d{{8}})?\.zip", f.name)
            if m and m.group(1) not in parts:
                f.unlink()
                actions.append(f"prune:{f.name}")
    return actions


def main() -> None:
    from core.ch_migrate import get_client
    backup_dir = Path(os.environ["CLICKHOUSE_BACKUP_DIR"])
    acts = run_backup(get_client(), backup_dir)
    print(f"backup: {acts or 'không có gì mới'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Chạy test xanh** — `cd backend && uv run pytest tests/clickhouse/test_t06_backup.py -v` — Expected: 4 PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/core/ch_backup.py backend/tests/clickhouse/test_t06_backup.py
git commit -m "feat(clickhouse): rolling partition backup per spec decision 10"
```

---

### Task 7: Compose profile `realtime` + `.env.example` + `stack.mjs`

**Files:**
- Modify: `deploy/infra/docker-compose.yml`
- Create: `deploy/infra/clickhouse/system-logs.xml` · `deploy/infra/clickhouse/memory.xml` (backups.xml đã tạo ở Task 1)
- Modify: `.env.example` · `.gitignore` · `scripts/stack.mjs`
- Test: `scripts/stack.test.mjs`

**Interfaces:**
- Consumes: —. Produces: profile `realtime`; helper thuần `realtimeMisconfigured(envText)` trong `stack.mjs`.

- [ ] **Step 1: Viết test đỏ cho helper `stack.mjs`**

Thêm vào `scripts/stack.test.mjs`:

```js
import { realtimeMisconfigured } from "./stack.mjs";

test("realtimeMisconfigured: không bật realtime thì không đòi gì", () => {
  assert.equal(realtimeMisconfigured("POSTGRES_DB=x\n"), null);
  assert.equal(realtimeMisconfigured("COMPOSE_PROFILES=web\nCLICKHOUSE_PASSWORD=\n"), null);
});

test("realtimeMisconfigured: bật realtime mà thiếu CLICKHOUSE_PASSWORD thì báo", () => {
  const msg = realtimeMisconfigured("COMPOSE_PROFILES=realtime\n");
  assert.ok(msg && msg.includes("CLICKHOUSE_PASSWORD"));
  assert.equal(realtimeMisconfigured("COMPOSE_PROFILES=web,realtime\nCLICKHOUSE_PASSWORD=abc\n"), null);
});
```

Chạy: `node --test scripts/` — Expected: 2 test mới FAIL (hàm chưa tồn tại), test cũ PASS.

- [ ] **Step 2: Sửa `stack.mjs`**

(a) Thêm helper thuần (đầu file, cạnh các export hiện có):

```js
export function realtimeMisconfigured(envText) {
  const env = {};
  for (const line of String(envText).split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$/);
    if (m) env[m[1]] = m[2].trim();
  }
  const profiles = (env.COMPOSE_PROFILES || "").split(",").map((s) => s.trim());
  if (!profiles.includes("realtime")) return null;
  if (!env.CLICKHOUSE_PASSWORD) return "COMPOSE_PROFILES có realtime nhưng CLICKHOUSE_PASSWORD chưa đặt trong .env";
  return null;
}
```

(b) Gọi trong `ensureEnv()` — thêm cuối hàm (sau khi chắc chắn `.env` tồn tại):

```js
  const err = realtimeMisconfigured(fs.readFileSync(ENV_FILE, "utf8"));
  if (err) die(err);
```

(c) Volume bất biến — sửa **cả hai** call site (dòng ~127 và ~141), thay danh sách:

```js
  for (const name of ["dlck-infra_pgdata", "dlck-infra_redisdata", "dlck-infra_chdata"]) {
```

(`assertVolumeSurvived` fail-open với tên chưa tồn tại — chấp nhận: khi profile realtime chưa từng bật, `chdata` chưa có là bình thường; smoke Step 6 kiểm `existed=true` sau khi bật.)

- [ ] **Step 3: Chạy test xanh** — `node --test scripts/` — Expected: toàn bộ PASS.

- [ ] **Step 4: Compose + config + env**

(a) `deploy/infra/docker-compose.yml` — thêm service (sau `redis`) và volume:

```yaml
  clickhouse:
    image: clickhouse/clickhouse-server:26.3.22.7
    profiles: ["realtime"]
    restart: unless-stopped
    environment:
      TZ: Asia/Ho_Chi_Minh
      CLICKHOUSE_PASSWORD: ${CLICKHOUSE_PASSWORD:-}
      CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: "1"
    ulimits:
      nofile:
        soft: 262144
        hard: 262144
    ports:
      - "127.0.0.1:8123:8123"
      - "127.0.0.1:9000:9000"
    volumes:
      - chdata:/var/lib/clickhouse
      - ./clickhouse/backups.xml:/etc/clickhouse-server/config.d/backups.xml:ro
      - ./clickhouse/system-logs.xml:/etc/clickhouse-server/config.d/system-logs.xml:ro
      - ./clickhouse/memory.xml:/etc/clickhouse-server/config.d/memory.xml:ro
      - ${CLICKHOUSE_BACKUP_DIR:-./clickhouse-backups}:/backups
    healthcheck:
      test: ["CMD-SHELL", "clickhouse-client --password \"$$CLICKHOUSE_PASSWORD\" -q 'SELECT 1'"]
      interval: 5s
      timeout: 3s
      retries: 20
    networks:
      - dlck-net
```

và trong khối `volumes:` cuối file thêm dòng `  chdata:`.

⚠️ **Không dùng `${CLICKHOUSE_PASSWORD:?}`** — Compose nội suy khi nạp file bất kể profile, sẽ phá `dev-start` của người chưa có khoá (spec §7); fail-fast đã nằm ở `stack.mjs`.

(b) `deploy/infra/clickhouse/system-logs.xml` — TTL 30 ngày cho 7 bảng log (spec §7):

```xml
<clickhouse>
  <query_log><ttl>event_date + INTERVAL 30 DAY DELETE</ttl></query_log>
  <part_log><ttl>event_date + INTERVAL 30 DAY DELETE</ttl></part_log>
  <trace_log><ttl>event_date + INTERVAL 30 DAY DELETE</ttl></trace_log>
  <text_log><ttl>event_date + INTERVAL 30 DAY DELETE</ttl></text_log>
  <metric_log><ttl>event_date + INTERVAL 30 DAY DELETE</ttl></metric_log>
  <asynchronous_metric_log><ttl>event_date + INTERVAL 30 DAY DELETE</ttl></asynchronous_metric_log>
  <query_metric_log><ttl>event_date + INTERVAL 30 DAY DELETE</ttl></query_metric_log>
</clickhouse>
```

(c) `deploy/infra/clickhouse/memory.xml`:

```xml
<clickhouse>
  <max_server_memory_usage_to_ram_ratio>0.6</max_server_memory_usage_to_ram_ratio>
</clickhouse>
```

(d) `.env.example` — thêm khối (sau khối Redis):

```
# ClickHouse (kho realtime — bật bằng cách bỏ comment dòng COMPOSE_PROFILES)
# COMPOSE_PROFILES=realtime
CLICKHOUSE_PASSWORD=change-me-in-production
CLICKHOUSE_URL=http://default:change-me-in-production@127.0.0.1:8123
CLICKHOUSE_BACKUP_DIR=./clickhouse-backups
```

(e) `.gitignore` — thêm dòng: `deploy/infra/clickhouse-backups/`

- [ ] **Step 5: Smoke render compose**

```bash
docker compose -p dlck-infra -f deploy/infra/docker-compose.yml --env-file .env.example config --quiet && echo OK
docker compose -p dlck-infra -f deploy/infra/docker-compose.yml --env-file .env.example --profile realtime config | grep -c "clickhouse-server:26.3.22.7"
```

Expected: `OK` (nạp file không profile không đòi biến) và `1`.

- [ ] **Step 6: Smoke bật profile thật (một lần, rồi hạ)**

```bash
docker network create dlck-net 2>/dev/null; docker compose -p dlck-infra -f deploy/infra/docker-compose.yml --env-file .env --profile realtime up -d --wait clickhouse
docker exec dlck-infra-clickhouse-1 clickhouse-client --password "$CLICKHOUSE_PASSWORD_FROM_ENV" -q "SELECT timezone()"
docker volume ls --format '{{.Name}}' | grep dlck-infra_chdata
docker compose -p dlck-infra -f deploy/infra/docker-compose.yml --env-file .env --profile realtime stop clickhouse
```

Expected: `Asia/Ho_Chi_Minh` · volume `dlck-infra_chdata` tồn tại (`existed=true` — đóng lỗ fail-open §13). (Thay `$CLICKHOUSE_PASSWORD_FROM_ENV` bằng giá trị trong `.env`; yêu cầu `.env` đã có khối ClickHouse — copy từ `.env.example` nếu chưa.)

- [ ] **Step 7: Commit**

```bash
git add deploy/infra/ .env.example .gitignore scripts/
git commit -m "feat(infra): clickhouse service under realtime profile with safety rails"
```

---

### Task 8: Cập nhật tài liệu sống (checklist §13 của spec) + verify

**Files:**
- Modify: `docs/20-design/market-data-store.md` · `docs/20-design/service-topology.md` · `database/README.md` · `docs/00-overview/roadmap.md`

Làm đúng **từng mục checklist §13 trong spec** (mở spec, đi từng ô — nội dung từng mục đã ghi sẵn ở đó, kể cả số dòng cần sửa). Tóm tắt các mục:

- [ ] **Step 1: `market-data-store.md`** — thêm banner "phần realtime (§3.2 điểm 4, §5.3, §5.7 dòng bar_1m) được thay bởi spec ClickHouse, khoá nến đổi `organ_code` → `symbol` (ticker)" trỏ tới `docs/90-records/plans/2026-08-25-clickhouse-realtime-store/spec.md`; sửa/chú thích 3 chỗ hết hiệu lực: dòng 18 ("Kho ~10 GB"), dòng 46 (sơ đồ ingester → "PostgreSQL + TimescaleDB"), dòng 380 ("dưới 10 GB + ~1 GB/năm nến"). Giữ nguyên văn phần cũ làm lịch sử, chú thích bằng banner/ghi chú cạnh chỗ sai — không xoá.
- [ ] **Step 2: `service-topology.md` §4** — thêm nhắc TTL frame thô 3–4 tháng / nến vĩnh viễn; **sửa câu "data thị trường crawl lại được nên không cần [backup]"** thành có ngoại lệ `bar_1m`/`index_bar_1m` + cửa sổ frame (trỏ quyết định #10 của spec); ghi câu chốt mới về điểm nối factor ("`api` cần view hệ số, ClickHouse không phụ thuộc Postgres").
- [ ] **Step 3: `database/README.md`** — gỡ banner dòng 12 ("chưa cập nhật theo ClickHouse"); thêm mục ClickHouse: trạng thái (2 migration, N test seam), cách chạy (`export CLICKHOUSE_URL=...` → `uv run python -m core.ch_migrate upgrade` · test: `uv run pytest tests/clickhouse -v` — cần Docker · backup: `uv run python -m core.ch_backup`, lịch cron sau 15:30 khi deploy Linux, dev chạy tay); một câu phân định **hai role trùng tên `dlck_api`** (Postgres đọc 4 schema ≠ ClickHouse đọc `rt`); luật user login tạo per-môi-trường từ `create_users.sql.example`.
- [ ] **Step 4: `roadmap.md` §5.2** — đánh dấu dòng "Cập nhật market-data-store theo ClickHouse" ✅ xong, trỏ hồ sơ `plans/2026-08-25-clickhouse-realtime-store/`.
- [ ] **Step 5: Phép kiểm §1.7** — chạy và dán kết quả vào ledger:

```bash
git grep -n "TimescaleDB\|hypertable" -- docs/ database/ backend/ deploy/ | grep -v "90-records\|decisions"
```

Expected: mọi hit còn lại đều là ghi chú lịch sử có chủ đích (banner "trước đây là Timescale") — hit nào là khẳng định sống sai thì sửa nốt.
- [ ] **Step 6: Commit**

```bash
git add docs/ database/README.md
git commit -m "docs: update living docs per clickhouse spec checklist 13"
```

---

## Sau khi xong 8 task

1. Chạy toàn bộ: `cd backend && uv run pytest tests/ -v` (schema Postgres + clickhouse) và `node --test scripts/` — dán output vào ledger.
2. Review theo §4.1.5 (hai trục Chuẩn/Spec) → verify (§4.1.6) → báo chủ dự án quyết merge nhánh `feat/clickhouse-realtime-store`.
3. Ledger: `docs/90-records/plans/2026-08-25-clickhouse-realtime-store/ledger.md` — ghi theo từng task, commit cùng nhánh.
