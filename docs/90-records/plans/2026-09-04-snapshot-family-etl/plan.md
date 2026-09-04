# Kế hoạch thực thi — `etl snapshot` (lát 4)

> **Cho người/agent thực thi:** dùng skill `superpowers:subagent-driven-development` hoặc `superpowers:executing-plans`, làm **tuần tự từng task**, mỗi bước một hành động. Bước có checkbox `- [ ]`.

**Mục tiêu:** job `python -m etl snapshot` nạp bốn kind của họ Snapshot vào `market.snapshot_daily` theo kiến trúc trigger + quét sàn cuốn chiếu, **chỉ ghi khi nội dung đổi**.

**Kiến trúc:** năm module thuần/I-O tách bạch y khuôn lát 1–3 (`fetch` → `normalize` → `guard` → `store` → `job`), cộng một bảng sổ kiểm `ops.snapshot_check` vừa cấp danh sách tới hạn vừa là thước đo lỗ của lịch sự kiện. Không có con trỏ: `checked_at` chính là con trỏ.

**Stack:** Python 3.12 · httpx · SQLAlchemy Core (SQL thuần, không ORM) · Alembic · pytest trên Postgres thật.

**Spec:** [spec.md](spec.md) — đọc cùng plan. **Số đo:** [measurements.md](measurements.md). **Mẫu payload:** [`samples/`](samples/).

## Ràng buộc toàn cục

Áp cho **mọi** task, không nhắc lại trong từng task:

- `PYTHONIOENCODING=utf-8` khi chạy Python (CLAUDE.md §5) — nếu không sẽ crash cp1252 khi in tiếng Việt.
- Chạy test và job bằng venv của backend: `backend/.venv/Scripts/python.exe`, hoặc `uv run` từ thư mục `backend/`.
- Kết nối kho: biến `ETL_DATABASE_URL` (job) và `TEST_DATABASE_URL` (test) đọc từ `.env` ở gốc repo qua `core.env.load_dotenv()`. **Không bao giờ in giá trị ra output hay ghi vào file.**
- Mọi lời gọi `*.fiintrade.vn` phải có header `Origin: https://fiinapp.bvsc.com.vn`, nếu không là `HTTP 403` body rỗng.
- Hợp lệ của response FiinTrade: `status ∈ {0, "Success"}` — **không** so `== "Success"` (quy ước §6.1; lát 1–2 viết sai mà may chưa gặp).
- Exception vận chuyển (`httpx.HTTPError`) phải đi **cùng đường retry** với response xấu, không được ném thẳng ra ngoài (bài học lát 3, `e7f80f6`).
- Giãn cách ≥ **0,5 s** giữa hai lần bắt đầu lời gọi (trần 2 request/giây).
- Comment và log tiếng Việt; message commit tiếng Anh, Conventional Commits.
- Nhánh `feat/snapshot-family-etl`. Commit theo mốc — mỗi task một commit.
- TDD: **đỏ trước xanh**, mỗi seam một vòng. Không viết hết test rồi code hết.
- Expected trong test lấy từ mẫu thật ở `samples/` hoặc giải tay — **không tính lại theo đúng cách code tính**.

## Cây file

| File | Trách nhiệm |
|---|---|
| `database/migrations/versions/0016_snapshot_check.py` | Bảng `ops.snapshot_check` + mở CHECK của `data_domain_state` |
| `backend/etl/snapshot_fetch.py` | I/O: dựng URL 4 kind, gọi, phân loại kết quả, retry, giãn cách |
| `backend/etl/snapshot_normalize.py` | Thuần: bóc `items[0]`, lấy tập trắng, tính hash |
| `backend/etl/snapshot_guard.py` | Thuần: bốn chốt chặn, trả `Verdict` |
| `backend/etl/snapshot_store.py` | SQL: danh sách tới hạn, ghi `snapshot_daily`, upsert sổ kiểm, watermark, bằng chứng |
| `backend/etl/snapshot_job.py` | Ghép một lượt chạy, quản giao dịch, `ops.etl_run` |
| `backend/etl/__main__.py` | Thêm nhánh `snapshot` vào CLI |
| `backend/tests/schema/test_s13_snapshot_check.py` | Lược đồ + quyền role `dlck_etl` |
| `backend/tests/etl/test_e26_snapshot_fetch.py` | Seam `url` · `classify` · vòng retry |
| `backend/tests/etl/test_e27_snapshot_normalize.py` | Seam `keep` · `keep_hash` |
| `backend/tests/etl/test_e28_snapshot_guard.py` | Seam `check` |
| `backend/tests/etl/test_e29_snapshot_store.py` | Seam `due_list` · `apply` trên Postgres thật |
| `backend/tests/etl/test_e30_snapshot_job.py` | Lượt chạy trọn, guard từ chối, idempotent |
| `backend/tests/etl/fixtures/snapshot/*.json` | 6 mẫu thật chép từ `samples/` |

## Một số đo bổ sung, phát hiện khi soi mẫu để viết plan này

*(2026-09-04, trên cả 9 mã của lượt đo — bổ sung cho [measurements §4](measurements.md))*

| Trường | Ở đâu | Ghi chú |
|---|---|---|
| `rtq10` | **luôn** trong `summary` | 9/9 mã |
| `rtq44` · `rtq137` · `rqq41` | `quarterly[0]` **và** `yearly[0]` | **CHỈ có ở ngân hàng** (BAB, BVB qua `GetSnapshot`) — vắng ở cả 7 mã phi ngân hàng |
| `year` · `quarter` | `quarterly[0]` / `yearly[0]` | A32 có `quarterly` **rỗng** (1/9 mã) ⇒ phải rơi về `yearly[0]` |

**Hệ quả:** tập trắng của kind `snapshot` là **18 trường ở ngân hàng, 15 ở phi ngân hàng** — thiếu 3 trường không phải lỗi, và `keep()` phải bỏ qua khoá vắng thay vì ném lỗi.

---

## Task 1 — Migration `0016` + lược đồ

**Files:** Create `database/migrations/versions/0016_snapshot_check.py` · Test `backend/tests/schema/test_s13_snapshot_check.py`

**Interfaces:**
- Produces: bảng `ops.snapshot_check(issuer_id, kind, checked_at, keep_hash, changed_at, found_by)` PK `(issuer_id, kind)`; giá trị `'market.snapshot'` hợp lệ cho `ops.data_domain_state.domain`.

- [ ] **Bước 1: Viết test đỏ**

Tạo `backend/tests/schema/test_s13_snapshot_check.py`:

```python
import pytest
import sqlalchemy as sa


def _issuer(db, name="Test snapshot_check"):
    return db.execute(sa.text("INSERT INTO market.issuer (name) VALUES (:n) RETURNING issuer_id"),
                      {"n": name}).scalar_one()


def test_snapshot_check_keeps_one_row_per_issuer_and_kind(db):
    iid = _issuer(db)
    db.execute(sa.text(
        "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
        " VALUES (:i, 'snapshot', now(), 'abc', 'floor')"), {"i": iid})
    with pytest.raises(sa.exc.IntegrityError):
        db.execute(sa.text(
            "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
            " VALUES (:i, 'snapshot', now(), 'def', 'event')"), {"i": iid})


def test_snapshot_check_refuses_a_kind_outside_the_four(db):
    iid = _issuer(db, "Kind la")
    with pytest.raises(sa.exc.IntegrityError):
        db.execute(sa.text(
            "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
            " VALUES (:i, 'company_score', now(), 'abc', 'floor')"), {"i": iid})


def test_snapshot_check_refuses_a_found_by_outside_the_two(db):
    iid = _issuer(db, "found_by la")
    with pytest.raises(sa.exc.IntegrityError):
        db.execute(sa.text(
            "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
            " VALUES (:i, 'snapshot', now(), 'abc', 'guess')"), {"i": iid})


def test_data_domain_state_accepts_the_new_market_snapshot_domain(db):
    db.execute(sa.text(
        "INSERT INTO ops.data_domain_state (domain, source, status, watermark)"
        " VALUES ('market.snapshot', 'fiintrade', 'active', '2026-09-04')"))
    got = db.execute(sa.text("SELECT watermark FROM ops.data_domain_state"
                             " WHERE domain = 'market.snapshot'")).scalar_one()
    assert got == "2026-09-04"


def test_snapshot_check_works_under_the_etl_role(db):
    """§3.5 ca thứ ba: quyền phải kiểm bằng chính role production, không suy từ migration."""
    iid = _issuer(db, "Quyen dlck_etl")
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text(
        "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
        " VALUES (:i, 'ownership', now(), 'h1', 'floor')"), {"i": iid})
    db.execute(sa.text(
        "UPDATE ops.snapshot_check SET keep_hash = 'h2', changed_at = now()"
        " WHERE issuer_id = :i AND kind = 'ownership'"), {"i": iid})
    assert db.execute(sa.text("SELECT keep_hash FROM ops.snapshot_check"
                              " WHERE issuer_id = :i"), {"i": iid}).scalar_one() == "h2"
```

- [ ] **Bước 2: Chạy để thấy đỏ**

```bash
cd backend && uv run pytest tests/schema/test_s13_snapshot_check.py -v
```

Expected: 5 test FAIL, lỗi `psycopg.errors.UndefinedTable: relation "ops.snapshot_check" does not exist` (và test domain FAIL vì CHECK từ chối `'market.snapshot'`).

- [ ] **Bước 3: Viết migration**

Tạo `database/migrations/versions/0016_snapshot_check.py`:

```python
"""ops.snapshot_check + domain market.snapshot

Sổ kiểm của họ Snapshot (lát 4). Bảng TRẠNG THÁI HIỆN TẠI, một dòng mỗi
(issuer, kind) — 6.092 dòng đứng yên, không phình:

  - cấp danh sách tới hạn cho job (ORDER BY checked_at NULLS FIRST),
  - và là thước đo lỗ của lịch sự kiện: đổi mà found_by='floor' nghĩa là
    lịch sự kiện KHÔNG bắn cho thay đổi đó.

Lịch sử nội dung nằm ở market.snapshot_daily; lịch sử phép đếm nằm ở
ops.etl_run.stats. Không dựng bảng lịch sử thứ ba.

Domain 'market.snapshot' thêm vào CHECK vì lát 1 (screener) đã chiếm
('market.scores','fiintrade'); dùng chung thì hai job đè watermark của nhau.

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-04

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ops.snapshot_check (
          issuer_id  bigint NOT NULL REFERENCES market.issuer,
          kind       text   NOT NULL CHECK (kind IN
                       ('snapshot','valuation','ownership','dividend')),
          checked_at timestamptz NOT NULL,
          keep_hash  text   NOT NULL,       -- sha256 của TẬP TRẮNG, không phải payload trọn
          changed_at timestamptz,           -- lần nội dung đổi gần nhất; NULL = chưa đổi lần nào
          found_by   text   NOT NULL CHECK (found_by IN ('event','floor')),
          PRIMARY KEY (issuer_id, kind)
        );
        CREATE INDEX ON ops.snapshot_check (kind, checked_at);

        ALTER TABLE ops.data_domain_state DROP CONSTRAINT data_domain_state_domain_check;
        ALTER TABLE ops.data_domain_state ADD CONSTRAINT data_domain_state_domain_check
          CHECK (domain IN ('market.reference','market.price','market.fundamentals',
                            'market.events','market.scores','market.index_stat',
                            'macro.indicator','macro.omo','asset','news',
                            'market.snapshot'));
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM ops.data_domain_state WHERE domain = 'market.snapshot';
        ALTER TABLE ops.data_domain_state DROP CONSTRAINT data_domain_state_domain_check;
        ALTER TABLE ops.data_domain_state ADD CONSTRAINT data_domain_state_domain_check
          CHECK (domain IN ('market.reference','market.price','market.fundamentals',
                            'market.events','market.scores','market.index_stat',
                            'macro.indicator','macro.omo','asset','news'));
        DROP TABLE ops.snapshot_check;
        """
    )
```

- [ ] **Bước 4: Chạy test lại**

```bash
cd backend && uv run pytest tests/schema/test_s13_snapshot_check.py -v
```

Expected: 5 PASS.

- [ ] **Bước 5: Kiểm migration lên/xuống trên kho dev**

```bash
uv run --project backend alembic -c database/alembic.ini upgrade head
uv run --project backend alembic -c database/alembic.ini downgrade -1
uv run --project backend alembic -c database/alembic.ini upgrade head
```

*(Lệnh theo `database/README.md`. `database/` không có `pyproject.toml` riêng nên `cd database && uv run alembic` KHÔNG chạy — sửa 2026-09-04 sau khi Task 1 vấp thật.)*

Expected: cả ba lệnh exit 0; lệnh cuối để head ở `0016`.

- [ ] **Bước 6: Commit**

```bash
git add database/migrations/versions/0016_snapshot_check.py backend/tests/schema/test_s13_snapshot_check.py
git commit -m "feat(db): ops.snapshot_check ledger and a market.snapshot domain"
```

---

## Task 2 — `snapshot_fetch`: URL và `classify`

**Files:** Create `backend/etl/snapshot_fetch.py` · Test `backend/tests/etl/test_e26_snapshot_fetch.py` · Copy fixtures

**Interfaces:**
- Produces: `KINDS: tuple[str, ...]` · `ROOT_KEY: dict[str, str]` · `url(kind, organ_code, ticker, com_type) -> str` · `classify(kind, http: int, text: str) -> tuple[str, dict | None]` với verdict ∈ `{"ok","retry","bad_shape"}`.

- [ ] **Bước 1: Chép 6 mẫu thật vào fixtures**

```bash
mkdir -p backend/tests/etl/fixtures/snapshot
cp docs/90-records/plans/2026-09-04-snapshot-family-etl/samples/*.json backend/tests/etl/fixtures/snapshot/
ls backend/tests/etl/fixtures/snapshot/
```

Expected: 6 file — `A32-snapshot.json` `A32-ownership.json` `A32-dividend.json` `A32-valuation.json` `BAB-snapshot-bank-status0.json` `BVB-valuation-failed.json`.

- [ ] **Bước 2: Viết test đỏ**

Tạo `backend/tests/etl/test_e26_snapshot_fetch.py`:

```python
import pathlib

from etl import snapshot_fetch as sf

FIX = pathlib.Path(__file__).parent / "fixtures" / "snapshot"


def _text(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_url_picks_the_bank_endpoint_only_for_com_type_nh():
    assert sf.url("snapshot", "NASB", "BAB", "NH").endswith(
        "/Snapshot/GetSnapshot?OrganCode=NASB&language=vi")
    assert sf.url("snapshot", "ASECO32", "A32", "CT").endswith(
        "/Snapshot/GetSnapshotNoneBank?OrganCode=ASECO32&language=vi")
    assert sf.url("snapshot", "HAMIS", "AAS", None).endswith(
        "/Snapshot/GetSnapshotNoneBank?OrganCode=HAMIS&language=vi")


def test_url_of_dividend_carries_both_the_organ_code_and_the_ticker():
    u = sf.url("dividend", "ASECO32", "A32", "CT")
    assert "OrganCode=ASECO32" in u and "Code=A32" in u
    assert u.startswith("https://wlgw-fundamental.fiintrade.vn/CashDividendAnalysis/GetAnalysis?")


def test_url_of_valuation_lives_on_the_tools_host():
    assert sf.url("valuation", "ASECO32", "A32", "CT") == (
        "https://wlgw-tools.fiintrade.vn/Valuation/GetValuation?OrganCode=ASECO32&language=vi")


def test_classify_accepts_status_zero_from_the_bank_endpoint():
    verdict, item = sf.classify("snapshot", 200, _text("BAB-snapshot-bank-status0.json"))
    assert verdict == "ok"
    assert item["summary"]["organCode"] == "NASB"


def test_classify_accepts_status_success_from_the_non_bank_endpoint():
    verdict, item = sf.classify("snapshot", 200, _text("A32-snapshot.json"))
    assert verdict == "ok" and "summary" in item


def test_classify_sends_a_failed_status_back_to_the_retry_path():
    """status Failed = timeout Redis phía nguồn (quy ước §10.5), KHÔNG phải 'mã rỗng'."""
    verdict, item = sf.classify("valuation", 200, _text("BVB-valuation-failed.json"))
    assert verdict == "retry" and item is None


def test_classify_calls_a_missing_root_key_bad_shape_not_retry():
    verdict, item = sf.classify("valuation", 200, '{"items": [{"khac": 1}], "status": "Success"}')
    assert verdict == "bad_shape" and item is None


def test_classify_treats_broken_json_and_non_200_as_retry():
    assert sf.classify("ownership", 200, "<html>502</html>") == ("retry", None)
    assert sf.classify("ownership", 503, "") == ("retry", None)
```

- [ ] **Bước 3: Chạy để thấy đỏ**

```bash
cd backend && uv run pytest tests/etl/test_e26_snapshot_fetch.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'etl.snapshot_fetch'`.

- [ ] **Bước 4: Viết phần tối thiểu cho xanh**

Tạo `backend/etl/snapshot_fetch.py`:

```python
"""Tải bốn endpoint họ Snapshot theo mã, tuần tự, có giãn cách (spec §5.2). I/O thuần.

Ba điều đo 2026-09-04 quyết định hình dạng module (measurements.md):
- `status` trả **0** ở `GetSnapshot` (ngân hàng) và **"Success"** ở `GetSnapshotNoneBank` —
  cùng một họ, cùng một lượt gọi ⇒ hợp lệ là status ∈ {0, "Success"} (quy ước §6.1).
- `status: "Failed"` của `GetValuation` là timeout Redis PHÍA NGUỒN (quy ước §10.5) ⇒ THỬ LẠI.
  Đọc `items: null` thành "mã này rỗng" là ghi kết luận sai rồi đánh dấu đã kiểm.
- Lượt hỏng tốn 12,3 s ⇒ timeout của `valuation` phải rộng hơn hẳn ba kind còn lại.
"""
from __future__ import annotations

import contextlib
import json
import time
from dataclasses import dataclass

import httpx

FUND = "https://wlgw-fundamental.fiintrade.vn"
TOOLS = "https://wlgw-tools.fiintrade.vn"
FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"       # bắt buộc cho *.fiintrade.vn (00-conventions §2)

KINDS = ("snapshot", "valuation", "ownership", "dividend")
ROOT_KEY = {"snapshot": "summary", "ownership": "overviewChartData",
            "dividend": "organCode", "valuation": "valuationStock"}
TIMEOUT = {"snapshot": 15.0, "ownership": 15.0, "dividend": 15.0, "valuation": 30.0}
RETRIES = 3
BACKOFF = (2, 4, 8)
MIN_INTERVAL = 0.5                                 # trần 2 request/giây (market-data-store §4.2)


def url(kind: str, organ_code: str, ticker: str, com_type: str | None) -> str:
    if kind == "snapshot":
        ep = "GetSnapshot" if com_type == "NH" else "GetSnapshotNoneBank"
        return f"{FUND}/Snapshot/{ep}?OrganCode={organ_code}&language=vi"
    if kind == "ownership":
        return f"{FUND}/Ownership/GetOwnership?OrganCode={organ_code}&language=vi"
    if kind == "dividend":
        # Endpoint DUY NHẤT của cả nguồn nhận cả organCode lẫn ticker (00-conventions §5)
        return f"{FUND}/CashDividendAnalysis/GetAnalysis?OrganCode={organ_code}&Code={ticker}&language=vi"
    if kind == "valuation":
        return f"{TOOLS}/Valuation/GetValuation?OrganCode={organ_code}&language=vi"
    raise ValueError(f"kind lạ: {kind!r}")


def classify(kind: str, http: int, text: str) -> tuple[str, dict | None]:
    """('ok', bản ghi) | ('retry', None) | ('bad_shape', None)."""
    if http != 200:
        return "retry", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    if d.get("status") not in (0, "Success"):     # gồm "Failed" — lỗi tạm thời của nguồn
        return "retry", None
    items = d.get("items")
    if not isinstance(items, list) or not items or not isinstance(items[0], dict):
        return "bad_shape", None
    if ROOT_KEY[kind] not in items[0]:
        return "bad_shape", None
    return "ok", items[0]
```

- [ ] **Bước 5: Chạy test lại**

```bash
cd backend && uv run pytest tests/etl/test_e26_snapshot_fetch.py -v
```

Expected: 8 PASS.

- [ ] **Bước 6: Commit**

```bash
git add backend/etl/snapshot_fetch.py backend/tests/etl/test_e26_snapshot_fetch.py backend/tests/etl/fixtures/snapshot
git commit -m "feat(etl): snapshot family urls and response classification"
```

---

## Task 3 — `snapshot_fetch`: vòng gọi có retry và giãn cách

**Files:** Modify `backend/etl/snapshot_fetch.py` · Modify `backend/tests/etl/test_e26_snapshot_fetch.py`

**Interfaces:**
- Consumes: `url`, `classify` (Task 2).
- Produces: `@dataclass Target(kind, issuer_id, organ_code, ticker, com_type, found_by)` · `class FetchError(Exception)` · `class BadShape(Exception)` · `class Fetcher` với `fetch_one(t: Target) -> tuple[dict, str]`, thuộc tính `calls: int`, `retries: int` · `open_fetcher(get=None, sleep=time.sleep, clock=time.monotonic)` là context manager. Hàm `get` được tiêm có chữ ký `get(url: str, timeout: float) -> tuple[int, str]`.

- [ ] **Bước 1: Viết test đỏ (thêm vào cuối file test)**

```python
import httpx
import pytest

from etl.snapshot_fetch import BadShape, FetchError, Target


def _t(kind="ownership"):
    return Target(kind=kind, issuer_id=1, organ_code="ASECO32", ticker="A32",
                  com_type="CT", found_by="floor")


def test_fetch_one_retries_a_transport_exception_then_succeeds():
    """Bài học lát 3: ReadTimeout phải đi CÙNG đường với response xấu, không ném thẳng."""
    calls = []

    def get(u, timeout):
        calls.append(u)
        if len(calls) == 1:
            raise httpx.ReadTimeout("máy ngủ giữa lời gọi")
        return 200, _text("A32-ownership.json")

    with sf.open_fetcher(get=get, sleep=lambda s: None, clock=lambda: 0.0) as f:
        item, _ = f.fetch_one(_t())
    assert len(calls) == 2 and f.retries == 1
    assert "majorShareHolders" in item


def test_fetch_one_gives_up_after_four_attempts_on_a_failed_status():
    def get(u, timeout):
        return 200, _text("BVB-valuation-failed.json")

    with sf.open_fetcher(get=get, sleep=lambda s: None, clock=lambda: 0.0) as f:
        with pytest.raises(FetchError):
            f.fetch_one(_t("valuation"))
        assert f.calls == 4 and f.retries == 3


def test_fetch_one_does_not_retry_a_bad_shape():
    def get(u, timeout):
        return 200, '{"items": [{"khac": 1}], "status": 0}'

    with sf.open_fetcher(get=get, sleep=lambda s: None, clock=lambda: 0.0) as f:
        with pytest.raises(BadShape):
            f.fetch_one(_t())
        assert f.calls == 1


def test_fetch_one_waits_between_two_calls_to_keep_two_per_second():
    slept, now = [], [0.0]

    def get(u, timeout):
        return 200, _text("A32-ownership.json")

    with sf.open_fetcher(get=get, sleep=slept.append, clock=lambda: now[0]) as f:
        f.fetch_one(_t())
        now[0] = 0.1                                  # mới trôi 0,1 s kể từ lời gọi trước
        f.fetch_one(_t())
    assert slept and abs(slept[-1] - 0.4) < 1e-9      # phải ngủ bù đúng 0,4 s


def test_fetch_one_passes_the_wider_timeout_for_valuation():
    seen = []

    def get(u, timeout):
        seen.append(timeout)
        return 200, _text("A32-valuation.json")

    with sf.open_fetcher(get=get, sleep=lambda s: None, clock=lambda: 0.0) as f:
        f.fetch_one(_t("valuation"))
    assert seen == [30.0]
```

- [ ] **Bước 2: Chạy để thấy đỏ**

```bash
cd backend && uv run pytest tests/etl/test_e26_snapshot_fetch.py -k "fetch_one" -v
```

Expected: 5 FAIL — `ImportError: cannot import name 'BadShape' from 'etl.snapshot_fetch'`.

- [ ] **Bước 3: Viết phần tối thiểu cho xanh (thêm vào `snapshot_fetch.py`)**

```python
@dataclass(frozen=True)
class Target:
    kind: str
    issuer_id: int
    organ_code: str
    ticker: str
    com_type: str | None
    found_by: str                                  # 'event' | 'floor'


class FetchError(Exception):
    """Một mã/kind hỏng sau mọi lần thử — để nó CHƯA KIỂM, không ghi gì."""


class BadShape(Exception):
    """Response hợp lệ nhưng thiếu khoá gốc — nguồn đổi hình dạng, thử lại vô ích."""


class Fetcher:
    def __init__(self, get, sleep=time.sleep, clock=time.monotonic):
        self._get, self._sleep, self._clock = get, sleep, clock
        self.calls = 0
        self.retries = 0
        self._last: float | None = None

    def _request(self, kind: str, u: str) -> tuple[int, str]:
        if self._last is not None:
            wait = MIN_INTERVAL - (self._clock() - self._last)
            if wait > 0:
                self._sleep(wait)
        self._last = self._clock()
        self.calls += 1
        return self._get(u, TIMEOUT[kind])

    def fetch_one(self, t: Target) -> tuple[dict, str]:
        u = url(t.kind, t.organ_code, t.ticker, t.com_type)
        http, text = 0, ""
        for attempt in range(RETRIES + 1):
            try:
                http, text = self._request(t.kind, u)
            except httpx.HTTPError as e:
                # Timeout/đứt kết nối đi CÙNG đường với response xấu (bài học lát 3, e7f80f6)
                http, text = 0, f"{type(e).__name__}: {e}"
            verdict, item = classify(t.kind, http, text)
            if verdict == "ok":
                return item, text
            if verdict == "bad_shape":
                raise BadShape(f"{t.organ_code}/{t.kind}: thiếu khoá gốc {ROOT_KEY[t.kind]!r}")
            if attempt == RETRIES:
                break
            self._sleep(BACKOFF[attempt])
            self.retries += 1
        raise FetchError(f"{t.organ_code}/{t.kind} hỏng sau {RETRIES + 1} lần"
                         f" (HTTP {http}): {text[:200]}")


@contextlib.contextmanager
def open_fetcher(get=None, sleep=time.sleep, clock=time.monotonic):
    if get is not None:                            # test tiêm get giả, không mở kết nối
        yield Fetcher(get, sleep, clock)
        return
    # MỘT client cho trọn lượt — mở lại mỗi lời gọi là ~234 lần bắt tay TLS
    with httpx.Client(headers={"Origin": FIIN_ORIGIN}) as client:
        def get_one(u: str, timeout: float) -> tuple[int, str]:
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text
        yield Fetcher(get_one, sleep, clock)
```

- [ ] **Bước 4: Chạy test lại**

```bash
cd backend && uv run pytest tests/etl/test_e26_snapshot_fetch.py -v
```

Expected: 13 PASS.

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/snapshot_fetch.py backend/tests/etl/test_e26_snapshot_fetch.py
git commit -m "feat(etl): snapshot fetch loop with retry, spacing and per-kind timeout"
```

---

## Task 4 — `snapshot_normalize`: tập trắng và hash

**Files:** Create `backend/etl/snapshot_normalize.py` · Test `backend/tests/etl/test_e27_snapshot_normalize.py`

**Interfaces:**
- Consumes: bản ghi `items[0]` do `snapshot_fetch.classify` trả.
- Produces: `keep(kind: str, item: dict) -> dict` · `keep_hash(kind: str, item: dict) -> str` (sha256 hex) · hằng `KEEP_SUMMARY`, `KEEP_PERIOD`, `KEEP`.

🔴 **Quy tắc chọn kỳ — đo 2026-09-04:** `quarterly` và `yearly` sắp xếp **cũ → mới** (A32 `yearly` là 2020…2025; BAB `quarterly` là 2024Q2…2026Q2). Lấy phần tử `[0]` là lấy **kỳ cũ nhất**, tức hash sẽ **không bao giờ** phản ứng khi có báo cáo mới. Phải chọn theo `max(year, quarter)`, không theo chỉ số mảng.

- [ ] **Bước 1: Viết test đỏ**

Tạo `backend/tests/etl/test_e27_snapshot_normalize.py`:

```python
import json
import pathlib

from etl import snapshot_normalize as sn

FIX = pathlib.Path(__file__).parent / "fixtures" / "snapshot"


def _item(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))["items"][0]


def test_keep_of_a_non_bank_snapshot_has_fifteen_fields_and_the_newest_year():
    """Phi ngân hàng KHÔNG có rtq44/rtq137/rqq41 (đo 9/9 mã) ⇒ 15 chứ không 18, và đó không phải lỗi."""
    got = sn.keep("snapshot", _item("A32-snapshot.json"))
    assert len(got) == 15
    assert got["ceo"] == "Ngô Thành Thắng"
    assert got["outstandingShare"] == 6800000.0
    assert got["valuePerShare"] == 2500.0
    assert got["statePercentage"] == 0.51
    assert got["rtq10"] == 1.12836626
    assert got["year"] == 2025 and got["quarter"] == 0        # yearly mới nhất, KHÔNG phải [0]=2020
    assert "rtq44" not in got


def test_keep_of_a_bank_snapshot_has_eighteen_fields_and_the_newest_quarter():
    got = sn.keep("snapshot", _item("BAB-snapshot-bank-status0.json"))
    assert len(got) == 18
    assert got["ceo"] == "Thái Hương"
    assert got["rtq10"] == 14.60120886
    assert got["year"] == 2026 and got["quarter"] == 2        # quarterly mới nhất, KHÔNG phải [0]=2024Q2
    assert got["rtq44"] == 0.01998059 and got["rtq137"] == 0.01482075 and got["rqq41"] == 0.03434761


def test_keep_of_snapshot_leaves_out_every_field_computed_from_price():
    got = sn.keep("snapshot", _item("A32-snapshot.json"))
    for code in ("rtd11", "rtd14", "rtd21", "rtd25", "rtd53",
                 "highestPrice1Year", "lowestPrice1Year", "averageMatchVolume1Month",
                 "foreignerPercentage", "foreignerRoom", "freeFloatRate"):
        assert code not in got


def test_keep_of_valuation_takes_the_forecast_block_and_drops_the_sector_list():
    got = sn.keep("valuation", _item("A32-valuation.json"))
    assert got["riskFreeRate"] == 0.04337
    assert got["recommendMethod"] == "PE"
    assert got["rtd7"] == 33937.05626397
    assert got["rtq180"] == -25807827544.0
    assert got["estimatedEPS"] is None                        # trường dự phóng rỗng vẫn phải vào hash
    assert "valuationSector" not in got and "vnIndexEquityRisk" not in got and "rtd35" not in got


def test_keep_of_dividend_drops_the_two_ratios_that_move_with_price():
    got = sn.keep("dividend", _item("A32-dividend.json"))
    assert set(got) == {"cashDividendPayouts", "cashDividendPlans", "dps", "dividendPayoutRatio", "eps"}
    assert len(got["cashDividendPayouts"]) == 20
    assert got["dps"]["ratioYears"][0] == {"yearReport": 2025, "ratioValue": 2500.0}


def test_keep_of_ownership_takes_the_four_blocks():
    got = sn.keep("ownership", _item("A32-ownership.json"))
    assert [len(got[k]) for k in ("overviewChartData", "majorOwnershipsChartData",
                                  "majorShareHolders", "boardOfDirectors")] == [3, 5, 11, 10]


def test_hash_ignores_a_field_that_moves_with_price():
    """Tính chất, không tautology: đổi rtd11 (vốn hoá) thì hash PHẢI đứng yên."""
    item = _item("A32-snapshot.json")
    before = sn.keep_hash("snapshot", item)
    item["summary"]["rtd11"] = 999_000_000_000.0
    item["summary"]["rtd21"] = 42.0
    assert sn.keep_hash("snapshot", item) == before


def test_hash_reacts_to_a_field_inside_the_allowlist():
    item = _item("A32-snapshot.json")
    before = sn.keep_hash("snapshot", item)
    item["summary"]["outstandingShare"] = 7_000_000.0
    assert sn.keep_hash("snapshot", item) != before


def test_hash_reacts_to_a_new_report_arriving():
    item = _item("BAB-snapshot-bank-status0.json")
    before = sn.keep_hash("snapshot", item)
    item["quarterly"].append(dict(item["quarterly"][-1], year=2026, quarter=3, rtq44=0.02))
    assert sn.keep_hash("snapshot", item) != before


def test_hash_ignores_a_key_the_source_adds_later():
    item = _item("A32-ownership.json")
    before = sn.keep_hash("ownership", item)
    item["truongMoiCuaNguon"] = {"gi": "do"}
    assert sn.keep_hash("ownership", item) == before


def test_hash_is_stable_across_key_order():
    item = _item("A32-dividend.json")
    reordered = {k: item[k] for k in reversed(list(item))}
    assert sn.keep_hash("dividend", reordered) == sn.keep_hash("dividend", item)
```

- [ ] **Bước 2: Chạy để thấy đỏ**

```bash
cd backend && uv run pytest tests/etl/test_e27_snapshot_normalize.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'etl.snapshot_normalize'`.

- [ ] **Bước 3: Viết phần tối thiểu cho xanh**

Tạo `backend/etl/snapshot_normalize.py`:

```python
"""Bóc tập trắng và tính hash cho bốn kind họ Snapshot (spec §4.3, §5.3). Thuần, không I/O.

Vì sao có tập trắng thay vì hash cả payload: đo 2026-09-04 cho thấy `rtd11` `rtd21` `rtd25`
(snapshot) và `priceEarningRatio` `dividendYield` (dividend) tính TỪ GIÁ, đổi mỗi ngày —
hash trọn payload thì 100% mã "đổi" mỗi lượt và kiến trúc trigger mất nghĩa.

Danh sách TRẮNG chứ không phải danh sách đen: nguồn thêm một trường theo giá về sau cũng
không tự sinh báo động giả.
"""
from __future__ import annotations

import hashlib
import json

# 13 trường lấy từ `summary`; 5 trường còn lại nằm ở khối kỳ báo cáo (KEEP_PERIOD).
# Tổng 18 ở ngân hàng, 15 ở phi ngân hàng — rtq44/rtq137/rqq41 CHỈ ngân hàng mới có (đo 9/9 mã).
KEEP_SUMMARY = ("ceo", "comTypeCode", "competitors", "majorHoldings", "statePercentage",
                "stateVolumn", "foreignerVolumn", "totalForeignRoom",
                "maximumForeignPercentage", "outstandingShare", "freeFloat",
                "valuePerShare", "rtq10")
KEEP_PERIOD = ("year", "quarter", "rtq44", "rtq137", "rqq41")

KEEP = {
    "dividend": ("cashDividendPayouts", "cashDividendPlans", "dps", "dividendPayoutRatio", "eps"),
    "valuation": ("estimatedEPS", "forecastEPS", "estimatedBookValue", "forcastBookValue",
                  "riskFreeRate", "recommendMethod", "rtd7", "rtq180", "outstandingShare"),
    "ownership": ("majorShareHolders", "boardOfDirectors", "overviewChartData",
                  "majorOwnershipsChartData"),
}


def _newest_period(item: dict) -> dict:
    """Kỳ báo cáo mới nhất. Hai mảng sắp xếp CŨ → MỚI (đo 2026-09-04) nên [0] là kỳ cũ nhất —
    chọn theo max(year, quarter) để không phụ thuộc thứ tự nguồn trả."""
    rows = item.get("quarterly") or item.get("yearly") or []
    if not rows:
        return {}
    return max(rows, key=lambda r: (r.get("year") or 0, r.get("quarter") or 0))


def keep(kind: str, item: dict) -> dict:
    """Tập trắng của một bản ghi. Khoá vắng thì BỎ QUA, không ném lỗi."""
    if kind == "snapshot":
        summary = item.get("summary") or {}
        out = {k: summary[k] for k in KEEP_SUMMARY if k in summary}
        period = _newest_period(item)
        out.update({k: period[k] for k in KEEP_PERIOD if k in period})
        return out
    if kind == "valuation":
        block = item.get("valuationStock") or {}
        return {k: block[k] for k in KEEP[kind] if k in block}
    if kind in KEEP:
        return {k: item[k] for k in KEEP[kind] if k in item}
    raise ValueError(f"kind lạ: {kind!r}")


def keep_hash(kind: str, item: dict) -> str:
    body = json.dumps(keep(kind, item), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
```

- [ ] **Bước 4: Chạy test lại**

```bash
cd backend && uv run pytest tests/etl/test_e27_snapshot_normalize.py -v
```

Expected: 11 PASS.

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/snapshot_normalize.py backend/tests/etl/test_e27_snapshot_normalize.py
git commit -m "feat(etl): per-kind allowlist and change hash for the snapshot family"
```

---

## Task 5 — `snapshot_guard`: bốn chốt chặn

**Files:** Create `backend/etl/snapshot_guard.py` · Test `backend/tests/etl/test_e28_snapshot_guard.py`

**Interfaces:**
- Produces: `@dataclass Tally(attempted, failed, bad_shape, first, floor_compared, changed_floor, changed_event, unchanged)` (mọi trường `int`, mặc định 0) · `@dataclass Verdict(ok: bool, reasons: list[str])` · `check(t: Tally) -> Verdict` · hằng `MIN_SAMPLE = 20`, `MAX_FLOOR_CHANGED = 0.20`, `MAX_FAILED = 0.20`, `MAX_BAD_SHAPE = 0.05`.

- [ ] **Bước 1: Viết test đỏ**

Tạo `backend/tests/etl/test_e28_snapshot_guard.py`:

```python
from etl import snapshot_guard as sg


def test_a_normal_run_passes():
    t = sg.Tally(attempted=234, floor_compared=200, changed_floor=3, changed_event=8, unchanged=220)
    assert sg.check(t).ok


def test_an_empty_due_list_is_success_not_failure():
    """Chốt (iv): không có mã nào tới hạn là chuyện bình thường, không phải lỗi."""
    v = sg.check(sg.Tally())
    assert v.ok and v.reasons == []


def test_too_many_floor_changes_refuse_the_run():
    """Tập trắng sai hoặc nguồn đổi cách tính trông y hệt 'cả sàn cùng công bố'."""
    t = sg.Tally(attempted=234, floor_compared=200, changed_floor=60)
    v = sg.check(t)
    assert not v.ok and any("đổi" in r for r in v.reasons)


def test_a_small_sample_does_not_trip_the_change_threshold():
    """§4.4.4: lượt --codes 3 mã mà 1 mã đổi là 33% — hệ thống chạy bình thường không được tự phạm luật."""
    assert sg.check(sg.Tally(attempted=3, floor_compared=3, changed_floor=1)).ok


def test_a_cold_start_run_does_not_trip_the_change_threshold():
    """Lượt đầu tiên: mọi mã là 'first', chưa có hash cũ để so ⇒ floor_compared = 0."""
    assert sg.check(sg.Tally(attempted=234, first=234, floor_compared=0)).ok


def test_too_many_failed_calls_refuse_the_run():
    t = sg.Tally(attempted=234, failed=60, floor_compared=170)
    v = sg.check(t)
    assert not v.ok and any("hỏng" in r for r in v.reasons)


def test_too_many_bad_shapes_refuse_the_run():
    t = sg.Tally(attempted=234, bad_shape=20, floor_compared=210)
    v = sg.check(t)
    assert not v.ok and any("hình dạng" in r for r in v.reasons)


def test_all_broken_reasons_are_reported_together():
    t = sg.Tally(attempted=234, failed=60, bad_shape=20, floor_compared=100, changed_floor=50)
    assert len(sg.check(t).reasons) == 3
```

- [ ] **Bước 2: Chạy để thấy đỏ**

```bash
cd backend && uv run pytest tests/etl/test_e28_snapshot_guard.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'etl.snapshot_guard'`.

- [ ] **Bước 3: Viết phần tối thiểu cho xanh**

Tạo `backend/etl/snapshot_guard.py`:

```python
"""Bốn chốt chặn của một lượt `etl snapshot` (spec §5.5). Thuần, đánh giá TRƯỚC commit.

Chốt (i) là cái đắt nhất: nó bắt 'tập trắng sai' và 'nguồn đổi cách tính' — hai thứ trông
y hệt 'cả sàn cùng công bố'. Mọi chốt đều có ngưỡng mẫu tối thiểu, vì lượt --codes vài mã
hoặc lượt cold start sẽ tự vi phạm ngưỡng phần trăm nếu không có nó (§4.4.4).
"""
from __future__ import annotations

from dataclasses import dataclass, field

MIN_SAMPLE = 20
MAX_FLOOR_CHANGED = 0.20
MAX_FAILED = 0.20
MAX_BAD_SHAPE = 0.05


@dataclass
class Tally:
    attempted: int = 0          # số (mã × kind) định gọi trong lượt
    failed: int = 0             # hỏng sau mọi lần thử ⇒ để CHƯA KIỂM
    bad_shape: int = 0          # response hợp lệ nhưng thiếu khoá gốc
    first: int = 0              # lần kiểm đầu tiên của (mã, kind) — chưa có hash cũ để so
    floor_compared: int = 0     # mã quét sàn CÓ hash cũ để so
    changed_floor: int = 0      # trong số đó, nội dung đổi — đây là LỖ của lịch sự kiện
    changed_event: int = 0
    unchanged: int = 0


@dataclass
class Verdict:
    ok: bool
    reasons: list[str] = field(default_factory=list)


def check(t: Tally) -> Verdict:
    reasons: list[str] = []
    if t.floor_compared >= MIN_SAMPLE:
        rate = t.changed_floor / t.floor_compared
        if rate > MAX_FLOOR_CHANGED:
            reasons.append(f"tỷ lệ đổi của nhóm quét sàn {rate:.1%} > {MAX_FLOOR_CHANGED:.0%}"
                           f" ({t.changed_floor}/{t.floor_compared}) — nghi tập trắng sai"
                           f" hoặc nguồn đổi cách tính")
    if t.attempted >= MIN_SAMPLE:
        rate = t.failed / t.attempted
        if rate > MAX_FAILED:
            reasons.append(f"tỷ lệ lời gọi hỏng {rate:.1%} > {MAX_FAILED:.0%}"
                           f" ({t.failed}/{t.attempted}) — nguồn đang sự cố")
        rate = t.bad_shape / t.attempted
        if rate > MAX_BAD_SHAPE:
            reasons.append(f"tỷ lệ sai hình dạng {rate:.1%} > {MAX_BAD_SHAPE:.0%}"
                           f" ({t.bad_shape}/{t.attempted}) — nguồn đổi hình dạng response")
    return Verdict(ok=not reasons, reasons=reasons)
```

- [ ] **Bước 4: Chạy test lại**

```bash
cd backend && uv run pytest tests/etl/test_e28_snapshot_guard.py -v
```

Expected: 8 PASS.

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/snapshot_guard.py backend/tests/etl/test_e28_snapshot_guard.py
git commit -m "feat(etl): four guards for a snapshot run, each with a minimum sample"
```

---

## Task 6 — `snapshot_store`: danh sách tới hạn

**Files:** Create `backend/etl/snapshot_store.py` · Test `backend/tests/etl/test_e29_snapshot_store.py`

**Interfaces:**
- Consumes: `snapshot_fetch.Target`.
- Produces: hằng `JOB = "market.snapshot"` · `DOMAIN = "market.snapshot"` · `SOURCE = "fiintrade"` · `CADENCE_DAYS` · `QUOTA` · `TRIGGER_KINDS` · `load_watermark(conn) -> datetime.date` · `due_list(conn, watermark, kinds=None, codes=None, quota=QUOTA, cadence=CADENCE_DAYS) -> list[Target]`.

- [ ] **Bước 1: Viết test đỏ**

Tạo `backend/tests/etl/test_e29_snapshot_store.py`:

```python
from datetime import date, timedelta

import sqlalchemy as sa

from etl import snapshot_store as ss


def _issuer(db, name, organ, ticker, com_type="CT", listed=True):
    iid = db.execute(sa.text("INSERT INTO market.issuer (name, com_type_code)"
                             " VALUES (:n, :c) RETURNING issuer_id"),
                     {"n": name, "c": com_type}).scalar_one()
    db.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                       " VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": organ})
    db.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id, status)"
                       " VALUES (:t, 'HOSE', 'stock', :i, :s)"),
               {"t": ticker, "i": iid, "s": "listed" if listed else "delisted"})
    return iid


def _checked(db, iid, kind, days_ago, keep_hash="h0"):
    db.execute(sa.text(
        "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash, found_by)"
        " VALUES (:i, :k, now() - make_interval(days => :d), :h, 'floor')"),
        {"i": iid, "k": kind, "d": days_ago, "h": keep_hash})


def _event(db, organ, event_type, public_date, exright_date=None):
    db.execute(sa.text(
        "INSERT INTO market.corporate_event (event_type, organ_code, public_date, exright_date, payload)"
        " VALUES (:t, :o, :p, :e, '{}'::jsonb)"),
        {"t": event_type, "o": organ, "p": public_date, "e": exright_date})


def test_due_list_leaves_out_an_issuer_with_no_listed_stock(db):
    _issuer(db, "Da huy niem yet", "ZZDELIST", "ZZD", listed=False)
    due = ss.due_list(db, date(1900, 1, 1))
    assert [t.organ_code for t in due] == []


def test_due_list_takes_an_issuer_never_checked_before(db):
    _issuer(db, "Chua kiem bao gio", "ZZNEW", "ZZN")
    due = ss.due_list(db, date(1900, 1, 1))
    assert {t.kind for t in due} == set(ss.CADENCE_DAYS)
    assert all(t.found_by == "floor" and t.ticker == "ZZN" for t in due)


def test_due_list_skips_a_kind_still_inside_its_cadence(db):
    iid = _issuer(db, "Vua kiem hom qua", "ZZFRESH", "ZZF")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    assert ss.due_list(db, date(1900, 1, 1)) == []


def test_due_list_takes_back_a_kind_past_its_cadence(db):
    iid = _issuer(db, "Qua han thang", "ZZOLD", "ZZO")
    _checked(db, iid, "ownership", days_ago=31)      # nhịp tháng: quá hạn
    _checked(db, iid, "snapshot", days_ago=31)       # nhịp quý: CHƯA tới hạn
    _checked(db, iid, "valuation", days_ago=1)
    _checked(db, iid, "dividend", days_ago=1)
    assert [t.kind for t in ss.due_list(db, date(1900, 1, 1))] == ["ownership"]


def test_due_list_respects_the_daily_quota_and_takes_the_oldest_first(db):
    ids = [_issuer(db, f"Ma {i}", f"ZZQ{i}", f"ZQ{i}") for i in range(5)]
    for n, iid in enumerate(ids):
        _checked(db, iid, "ownership", days_ago=40 + n)     # ZZQ4 cũ nhất
    due = ss.due_list(db, date(1900, 1, 1), kinds=["ownership"], quota={"ownership": 2})
    assert [t.organ_code for t in due] == ["ZZQ4", "ZZQ3"]


def test_due_list_pulls_a_kind_in_early_when_an_event_fired(db):
    iid = _issuer(db, "Vua ra bao cao", "ZZEV", "ZZE")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)                  # mọi kind còn trong nhịp
    _event(db, "ZZEV", "Earning", date.today())
    due = ss.due_list(db, date.today() - timedelta(days=1))
    assert [(t.kind, t.found_by) for t in due] == [("snapshot", "event")]


def test_a_dividend_event_triggers_the_dividend_kind_not_the_snapshot_kind(db):
    iid = _issuer(db, "Chia co tuc", "ZZCD", "ZZC")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    _event(db, "ZZCD", "CashDividend", date.today() - timedelta(days=2),
           exright_date=date.today())
    due = ss.due_list(db, date.today() - timedelta(days=1))
    assert [(t.kind, t.found_by) for t in due] == [("dividend", "event")]


def test_an_event_older_than_the_watermark_does_not_fire(db):
    iid = _issuer(db, "Su kien cu", "ZZOLDEV", "ZZL")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    _event(db, "ZZOLDEV", "Earning", date.today() - timedelta(days=10))
    assert ss.due_list(db, date.today() - timedelta(days=1)) == []


def test_a_target_hit_by_both_paths_appears_once_and_counts_as_event(db):
    iid = _issuer(db, "Ca hai duong", "ZZBOTH", "ZZB")
    _checked(db, iid, "snapshot", days_ago=100)              # quá hạn quý
    _event(db, "ZZBOTH", "Earning", date.today())
    due = [t for t in ss.due_list(db, date.today() - timedelta(days=1)) if t.kind == "snapshot"]
    assert len(due) == 1 and due[0].found_by == "event"


def test_codes_forces_every_kind_and_ignores_cadence(db):
    iid = _issuer(db, "Ep bang codes", "ZZFORCE", "ZZR")
    for kind in ss.CADENCE_DAYS:
        _checked(db, iid, kind, days_ago=1)
    due = ss.due_list(db, date.today(), codes=["ZZR"])
    assert sorted(t.kind for t in due) == sorted(ss.CADENCE_DAYS)


def test_load_watermark_falls_back_to_1900_when_the_row_is_missing(db):
    assert ss.load_watermark(db) == date(1900, 1, 1)


def test_load_watermark_reads_the_row_it_wrote(db):
    db.execute(sa.text("INSERT INTO ops.data_domain_state (domain, source, status, watermark)"
                       " VALUES ('market.snapshot', 'fiintrade', 'active', '2026-09-01')"))
    assert ss.load_watermark(db) == date(2026, 9, 1)
```

- [ ] **Bước 2: Chạy để thấy đỏ**

```bash
cd backend && uv run pytest tests/etl/test_e29_snapshot_store.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'etl.snapshot_store'`.

- [ ] **Bước 3: Viết phần tối thiểu cho xanh**

Tạo `backend/etl/snapshot_store.py`:

```python
"""Danh sách tới hạn và ghi kết quả họ Snapshot (spec §5.4). SQL thuần.

KHÔNG có con trỏ, và không cần: `ops.snapshot_check.checked_at` CHÍNH LÀ con trỏ —
lượt sau tự lấy nhóm cũ nhất chưa tới lượt, nên lượt bị giết giữa chừng không mất chỗ.
"""
from __future__ import annotations

import datetime as dt

import sqlalchemy as sa

from etl.snapshot_fetch import KINDS, Target

JOB = "market.snapshot"
DOMAIN = "market.snapshot"
SOURCE = "fiintrade"

CADENCE_DAYS = {"snapshot": 90, "valuation": 30, "ownership": 30, "dividend": 30}
QUOTA = {"snapshot": 24, "valuation": 70, "ownership": 70, "dividend": 70}
TRIGGER_KINDS = {"Earning": "snapshot", "ShareIssuance": "snapshot",
                 "CashDividend": "dividend", "StockDividend": "dividend"}

# Vũ trụ: issuer có ÍT NHẤT một cổ phiếu đang niêm yết. Quỹ/ETF tự rơi ra vì không có
# security dạng stock (đo 2026-09-04) — không cần luật loại riêng.
_UNIVERSE = """
WITH uni AS (
  SELECT i.issuer_id, x.external_code AS organ_code, i.com_type_code,
         (SELECT s.ticker FROM market.security s
           WHERE s.issuer_id = i.issuer_id AND s.status = 'listed' AND s.security_type = 'stock'
           ORDER BY s.security_id LIMIT 1) AS ticker
  FROM market.issuer i
  JOIN market.issuer_external_id x ON x.issuer_id = i.issuer_id AND x.source = 'fiintrade'
  WHERE EXISTS (SELECT 1 FROM market.security s
                 WHERE s.issuer_id = i.issuer_id AND s.status = 'listed'
                   AND s.security_type = 'stock')
)
"""


def load_watermark(conn) -> dt.date:
    got = conn.execute(sa.text(
        "SELECT watermark FROM ops.data_domain_state"
        " WHERE domain = :d AND source = :s"), {"d": DOMAIN, "s": SOURCE}).scalar()
    return dt.date.fromisoformat(got) if got else dt.date(1900, 1, 1)


def _target(row, kind: str, found_by: str) -> Target:
    return Target(kind=kind, issuer_id=row.issuer_id, organ_code=row.organ_code,
                  ticker=row.ticker, com_type=row.com_type_code, found_by=found_by)


def due_list(conn, watermark: dt.date, kinds=None, codes=None,
             quota=None, cadence=None) -> list[Target]:
    kinds = list(kinds or KINDS)
    quota = quota or QUOTA
    cadence = cadence or CADENCE_DAYS

    if codes:                                   # lượt ép: mọi kind, bỏ qua nhịp và quota
        rows = conn.execute(sa.text(
            _UNIVERSE + "SELECT * FROM uni WHERE ticker = ANY(:codes) ORDER BY ticker"),
            {"codes": list(codes)}).all()
        return [_target(r, k, "floor") for r in rows for k in kinds]

    out: list[Target] = []
    seen: set[tuple[int, str]] = set()

    event_types = [t for t, k in TRIGGER_KINDS.items() if k in kinds]
    if event_types:
        rows = conn.execute(sa.text(
            _UNIVERSE + """
            SELECT DISTINCT u.*, e.event_type
            FROM uni u
            JOIN market.corporate_event e ON e.organ_code = u.organ_code
            WHERE e.event_type = ANY(:types)
              AND greatest(coalesce(e.public_date, DATE '1900-01-01'),
                           coalesce(e.exright_date, DATE '1900-01-01')) > :wm
            ORDER BY u.issuer_id
            """), {"types": event_types, "wm": watermark}).all()
        for r in rows:
            kind = TRIGGER_KINDS[r.event_type]
            if (r.issuer_id, kind) not in seen:
                seen.add((r.issuer_id, kind))
                out.append(_target(r, kind, "event"))

    for kind in kinds:
        rows = conn.execute(sa.text(
            _UNIVERSE + """
            SELECT u.* FROM uni u
            LEFT JOIN ops.snapshot_check c ON c.issuer_id = u.issuer_id AND c.kind = :kind
            WHERE c.checked_at IS NULL
               OR c.checked_at < now() - make_interval(days => :cadence)
            ORDER BY c.checked_at NULLS FIRST, u.issuer_id
            LIMIT :quota
            """), {"kind": kind, "cadence": cadence[kind], "quota": quota[kind]}).all()
        for r in rows:
            if (r.issuer_id, kind) not in seen:      # trigger đã lấy rồi thì thôi
                seen.add((r.issuer_id, kind))
                out.append(_target(r, kind, "floor"))
    return out
```

- [ ] **Bước 4: Chạy test lại**

```bash
cd backend && uv run pytest tests/etl/test_e29_snapshot_store.py -v
```

Expected: 12 PASS.

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/snapshot_store.py backend/tests/etl/test_e29_snapshot_store.py
git commit -m "feat(etl): due list from event triggers plus a quota-capped rolling floor scan"
```

---

## Task 7 — `snapshot_store`: ghi khi đổi, sổ kiểm, watermark, bằng chứng

**Files:** Modify `backend/etl/snapshot_store.py` · Modify `backend/tests/etl/test_e29_snapshot_store.py`

**Interfaces:**
- Consumes: `snapshot_normalize.keep_hash`, `snapshot_guard.Tally`.
- Produces: `@dataclass Fetched(target: Target, item: dict, text: str)` · `apply(conn, fetched: list[Fetched], run_date: dt.date) -> tuple[Tally, int]` (trả `Tally` và số dòng đã ghi) · `new_watermark(conn) -> dt.date` · `recrawl_codes(conn, watermark) -> list[str]` · `upsert_domain_state(engine, watermark: str) -> None` · `store_refusal_evidence(engine, fetched, run_id, verdict) -> None` (ghi tối đa 20 bản ghi).

- [ ] **Bước 1: Viết test đỏ (thêm vào cuối file test)**

```python
import json
import pathlib

from etl import snapshot_normalize as sn

FIX = pathlib.Path(__file__).parent / "fixtures" / "snapshot"


def _item(name="A32-ownership.json"):
    return json.loads((FIX / name).read_text(encoding="utf-8"))["items"][0]


def _fetched(iid, kind="ownership", found_by="floor", item=None, organ="ZZAP", ticker="ZZA"):
    from etl.snapshot_fetch import Target
    obj = item if item is not None else _item()
    return ss.Fetched(target=Target(kind=kind, issuer_id=iid, organ_code=organ, ticker=ticker,
                                    com_type="CT", found_by=found_by),
                      item=obj, text=json.dumps({"items": [obj], "status": 0}))


def _rows(db, iid):
    return db.execute(sa.text("SELECT count(*) FROM market.snapshot_daily WHERE issuer_id = :i"),
                      {"i": iid}).scalar_one()


def test_apply_writes_a_row_and_a_ledger_line_on_the_first_check(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = _issuer(db, "Lan dau", "ZZAP", "ZZA")
    tally, written = ss.apply(db, [_fetched(iid)], date(2026, 9, 4))
    assert (tally.first, tally.floor_compared, written) == (1, 0, 1)
    assert _rows(db, iid) == 1
    got = db.execute(sa.text("SELECT keep_hash, found_by, changed_at IS NOT NULL AS c"
                             " FROM ops.snapshot_check WHERE issuer_id = :i"), {"i": iid}).one()
    assert got.keep_hash == sn.keep_hash("ownership", _item()) and got.found_by == "floor" and got.c


def test_apply_writes_nothing_the_second_time_but_still_moves_the_ledger(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = _issuer(db, "Khong doi", "ZZAP", "ZZA")
    ss.apply(db, [_fetched(iid)], date(2026, 9, 4))
    before = db.execute(sa.text("SELECT checked_at FROM ops.snapshot_check WHERE issuer_id = :i"),
                        {"i": iid}).scalar_one()
    tally, written = ss.apply(db, [_fetched(iid)], date(2026, 9, 5))
    after = db.execute(sa.text("SELECT checked_at, changed_at FROM ops.snapshot_check"
                               " WHERE issuer_id = :i"), {"i": iid}).one()
    assert (tally.unchanged, tally.changed_floor, written) == (1, 0, 0)
    assert _rows(db, iid) == 1                       # KHÔNG có dòng thứ hai
    assert after.checked_at > before                 # nhưng vẫn "đã nhìn"
    assert after.changed_at < after.checked_at


def test_apply_writes_a_new_row_when_the_allowlist_content_changes(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = _issuer(db, "Co doi", "ZZAP", "ZZA")
    ss.apply(db, [_fetched(iid)], date(2026, 9, 4))
    changed = _item()
    changed["majorShareHolders"] = changed["majorShareHolders"][:5]
    tally, written = ss.apply(db, [_fetched(iid, item=changed)], date(2026, 9, 5))
    assert (tally.changed_floor, tally.floor_compared, written) == (1, 1, 1)
    assert _rows(db, iid) == 2


def test_apply_ignores_a_change_that_only_touches_a_price_derived_field(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = _issuer(db, "Chi doi theo gia", "ZZAP", "ZZA", com_type="CT")
    snap = _item("A32-snapshot.json")
    ss.apply(db, [_fetched(iid, kind="snapshot", item=snap)], date(2026, 9, 4))
    moved = json.loads(json.dumps(snap))
    moved["summary"]["rtd11"] = 999_000_000_000.0
    tally, written = ss.apply(db, [_fetched(iid, kind="snapshot", item=moved)], date(2026, 9, 5))
    assert (tally.unchanged, written) == (1, 0)
    assert _rows(db, iid) == 1


def test_apply_counts_an_event_change_apart_from_a_floor_change(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = _issuer(db, "Theo su kien", "ZZAP", "ZZA")
    ss.apply(db, [_fetched(iid)], date(2026, 9, 4))
    changed = _item()
    changed["boardOfDirectors"] = []
    tally, _ = ss.apply(db, [_fetched(iid, found_by="event", item=changed)], date(2026, 9, 5))
    assert (tally.changed_event, tally.changed_floor, tally.floor_compared) == (1, 0, 0)


def test_apply_run_twice_on_the_same_day_is_idempotent(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = _issuer(db, "Cung ngay", "ZZAP", "ZZA")
    ss.apply(db, [_fetched(iid)], date(2026, 9, 4))
    ss.apply(db, [_fetched(iid)], date(2026, 9, 4))
    assert _rows(db, iid) == 1


def test_new_watermark_takes_the_latest_of_both_event_dates(db):
    _issuer(db, "Moc nuoc", "ZZWM", "ZZW")
    _event(db, "ZZWM", "Earning", date(2026, 8, 1))
    _event(db, "ZZWM", "CashDividend", date(2026, 8, 20), exright_date=date(2026, 9, 10))
    assert ss.new_watermark(db) == date(2026, 9, 10)


def test_recrawl_codes_names_only_tickers_with_a_new_exright_date(db):
    _issuer(db, "Co quyen", "ZZRC", "ZZQ")
    _issuer(db, "Khong quyen", "ZZNC", "ZZK")
    _event(db, "ZZRC", "CashDividend", date(2026, 9, 1), exright_date=date(2026, 9, 3))
    _event(db, "ZZNC", "Earning", date(2026, 9, 2))
    assert ss.recrawl_codes(db, date(2026, 9, 1)) == ["ZZQ"]
```

- [ ] **Bước 2: Chạy để thấy đỏ**

```bash
cd backend && uv run pytest tests/etl/test_e29_snapshot_store.py -k "apply or watermark or recrawl" -v
```

Expected: 8 FAIL — `AttributeError: module 'etl.snapshot_store' has no attribute 'Fetched'`.

- [ ] **Bước 3: Viết phần tối thiểu cho xanh (thêm vào `snapshot_store.py`)**

```python
import json
from dataclasses import dataclass

from etl.snapshot_guard import Tally, Verdict
from etl.snapshot_normalize import keep_hash

MAX_EVIDENCE = 20                                  # đủ để nhìn ra vì sao guard từ chối


@dataclass
class Fetched:
    target: Target
    item: dict
    text: str


def apply(conn, fetched: list[Fetched], run_date: dt.date) -> tuple[Tally, int]:
    """Ghi KHI ĐỔI vào snapshot_daily; mọi lượt kiểm đều cập nhật sổ kiểm."""
    tally, written = Tally(), 0
    for f in fetched:
        t = f.target
        tally.checked += 1
        h = keep_hash(t.kind, f.item)
        prev = conn.execute(sa.text(
            "SELECT keep_hash FROM ops.snapshot_check"
            " WHERE issuer_id = :i AND kind = :k"), {"i": t.issuer_id, "k": t.kind}).scalar()

        if prev is None:
            tally.first += 1
            changed = True
        else:
            changed = prev != h
            if t.found_by == "floor":
                tally.floor_compared += 1
                tally.changed_floor += int(changed)
            elif changed:
                tally.changed_event += 1
            if not changed:
                tally.unchanged += 1

        if changed:
            conn.execute(sa.text(
                "INSERT INTO market.snapshot_daily (issuer_id, trading_date, kind, payload)"
                " VALUES (:i, :d, :k, cast(:p AS jsonb))"
                " ON CONFLICT (issuer_id, trading_date, kind) DO UPDATE"
                " SET payload = excluded.payload, ingested_at = now()"),
                {"i": t.issuer_id, "d": run_date, "k": t.kind,
                 "p": json.dumps(f.item, ensure_ascii=False)})
            written += 1

        conn.execute(sa.text(
            "INSERT INTO ops.snapshot_check (issuer_id, kind, checked_at, keep_hash,"
            " changed_at, found_by) VALUES (:i, :k, now(), :h, now(), :f)"
            " ON CONFLICT (issuer_id, kind) DO UPDATE"
            " SET checked_at = now(), keep_hash = :h, found_by = :f,"
            "     changed_at = CASE WHEN :c THEN now() ELSE ops.snapshot_check.changed_at END"),
            {"i": t.issuer_id, "k": t.kind, "h": h, "f": t.found_by, "c": changed})
    return tally, written


def new_watermark(conn) -> dt.date:
    got = conn.execute(sa.text(
        "SELECT max(greatest(coalesce(public_date, DATE '1900-01-01'),"
        "                    coalesce(exright_date, DATE '1900-01-01')))"
        " FROM market.corporate_event")).scalar()
    return got or dt.date(1900, 1, 1)


def recrawl_codes(conn, watermark: dt.date) -> list[str]:
    """Mã có ngày giao dịch không hưởng quyền MỚI — chuỗi close_adj của chúng đã sai."""
    rows = conn.execute(sa.text(
        _UNIVERSE + """
        SELECT DISTINCT u.ticker FROM uni u
        JOIN market.corporate_event e ON e.organ_code = u.organ_code
        WHERE e.exright_date > :wm ORDER BY u.ticker
        """), {"wm": watermark}).scalars().all()
    return list(rows)


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
            " VALUES (:d, :s, 'active', now(), :w)"
            " ON CONFLICT (domain, source) DO UPDATE"
            " SET last_success_at = now(), watermark = :w, status = 'active'"),
            {"d": DOMAIN, "s": SOURCE, "w": watermark})


def store_refusal_evidence(engine, fetched: list[Fetched], run_id: int, verdict: Verdict) -> None:
    """Bằng chứng ở giao dịch RIÊNG — lượt chính đã rollback. Ưu tiên bản ghi của nhóm quét sàn."""
    picked = [f for f in fetched if f.target.found_by == "floor"][:MAX_EVIDENCE] or fetched[:MAX_EVIDENCE]
    meta = json.dumps({"run_id": run_id, "reasons": verdict.reasons}, ensure_ascii=False)
    with engine.begin() as conn:
        for f in picked:
            conn.execute(sa.text(
                "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                " VALUES ('snapshot', :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
                {"ek": f"snapshot:{f.target.kind}:{f.target.organ_code}", "p": f.text, "m": meta})
```

- [ ] **Bước 4: Chạy test lại**

```bash
cd backend && uv run pytest tests/etl/test_e29_snapshot_store.py -v
```

Expected: 20 PASS.

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/snapshot_store.py backend/tests/etl/test_e29_snapshot_store.py
git commit -m "feat(etl): write snapshot rows only when the allowlist content changes"
```

---

## Task 8 — `snapshot_job` + CLI + re-crawl giá

**Files:** Create `backend/etl/snapshot_job.py` · Modify `backend/etl/__main__.py` · Test `backend/tests/etl/test_e30_snapshot_job.py`

**Interfaces:**
- Consumes: tất cả module trên · `etl.omo_store.open_run/close_run` · `etl.price_job.run`.
- Produces: `run(codes=None, kinds=None, max_minutes=None) -> int` (0 xong · 1 guard từ chối · 2 lỗi khác) · `class GuardRefused(Exception)`.

🔴 **Hai chỗ dễ hỏng, phải làm đúng ngay:**

1. **Cold start không được kéo theo backfill giá 20 giờ.** `recrawl_codes` với watermark `1900-01-01` trả **mọi mã từng có ngày không hưởng quyền** — gọi `price_job` với 1.523 mã là một lượt backfill trọn vòng. Chặn bằng: bỏ qua re-crawl khi watermark là mốc khởi tạo, và trần `MAX_RECRAWL = 50` mã mỗi lượt.
2. **Watermark chỉ tiến khi không mã nào hỏng.** Nếu một target `failed`, trigger của nó chưa được phục vụ; đẩy watermark lên là **mất trigger vĩnh viễn**. Hỏng thì giữ nguyên watermark cũ để lượt sau bắn lại.

- [ ] **Bước 1: Viết test đỏ**

Tạo `backend/tests/etl/test_e30_snapshot_job.py`:

```python
import json
import pathlib
from datetime import date

import pytest
import sqlalchemy as sa

from etl import snapshot_job as sj
from etl import snapshot_store as ss

FIX = pathlib.Path(__file__).parent / "fixtures" / "snapshot"


def _payload(kind):
    name = {"snapshot": "A32-snapshot.json", "ownership": "A32-ownership.json",
            "dividend": "A32-dividend.json", "valuation": "A32-valuation.json"}[kind]
    return (FIX / name).read_text(encoding="utf-8")


def _fake_get(counters=None):
    """get(url, timeout) giả — trả đúng mẫu thật theo endpoint trong URL."""
    def get(u, timeout):
        if counters is not None:
            counters.append(u)
        kind = ("snapshot" if "/Snapshot/" in u else
                "ownership" if "/Ownership/" in u else
                "dividend" if "/CashDividendAnalysis/" in u else "valuation")
        return 200, _payload(kind)
    return get


def _seed(db, organ="ZZJOB", ticker="ZZJ"):
    iid = db.execute(sa.text("INSERT INTO market.issuer (name, com_type_code)"
                             " VALUES ('Job test', 'CT') RETURNING issuer_id")).scalar_one()
    db.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                       " VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": organ})
    db.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id)"
                       " VALUES (:t, 'HOSE', 'stock', :i)"), {"t": ticker, "i": iid})
    return iid


def test_one_run_writes_four_kinds_and_closes_the_run_row(db, monkeypatch):
    iid = _seed(db)
    monkeypatch.setattr(sj, "_engine", lambda: db.engine)
    rc = sj.run(codes=["ZZJ"], get=_fake_get())
    assert rc == 0
    kinds = db.execute(sa.text("SELECT kind FROM market.snapshot_daily WHERE issuer_id = :i"
                               " ORDER BY kind"), {"i": iid}).scalars().all()
    assert kinds == ["dividend", "ownership", "snapshot", "valuation"]
    row = db.execute(sa.text("SELECT status, stats FROM ops.etl_run WHERE job = :j"
                             " ORDER BY run_id DESC LIMIT 1"), {"j": ss.JOB}).one()
    assert row.status == "success" and row.stats["rows_written"] == 4


def test_a_second_run_on_the_same_day_writes_nothing_new(db, monkeypatch):
    iid = _seed(db)
    monkeypatch.setattr(sj, "_engine", lambda: db.engine)
    sj.run(codes=["ZZJ"], get=_fake_get())
    sj.run(codes=["ZZJ"], get=_fake_get())
    n = db.execute(sa.text("SELECT count(*) FROM market.snapshot_daily WHERE issuer_id = :i"),
                   {"i": iid}).scalar_one()
    assert n == 4
    stats = db.execute(sa.text("SELECT stats FROM ops.etl_run WHERE job = :j"
                               " ORDER BY run_id DESC LIMIT 1"), {"j": ss.JOB}).scalar_one()
    assert stats["rows_written"] == 0 and stats["tally"]["unchanged"] == 4


def test_a_source_wide_outage_refuses_the_run_and_writes_no_row(db, monkeypatch):
    iid = _seed(db)
    monkeypatch.setattr(sj, "_engine", lambda: db.engine)
    failing = (FIX / "BVB-valuation-failed.json").read_text(encoding="utf-8")
    rc = sj.run(codes=["ZZJ"], get=lambda u, timeout: (200, failing), sleep=lambda s: None)
    assert rc == 1
    assert db.execute(sa.text("SELECT count(*) FROM market.snapshot_daily WHERE issuer_id = :i"),
                      {"i": iid}).scalar_one() == 0
    row = db.execute(sa.text("SELECT status, error FROM ops.etl_run WHERE job = :j"
                             " ORDER BY run_id DESC LIMIT 1"), {"j": ss.JOB}).one()
    assert row.status == "failed" and "hỏng" in row.error


def test_a_refused_run_leaves_evidence_behind(db, monkeypatch):
    _seed(db)
    monkeypatch.setattr(sj, "_engine", lambda: db.engine)
    failing = (FIX / "BVB-valuation-failed.json").read_text(encoding="utf-8")
    sj.run(codes=["ZZJ"], get=lambda u, timeout: (200, failing), sleep=lambda s: None)
    n = db.execute(sa.text("SELECT count(*) FROM staging.raw_payload"
                           " WHERE source = 'snapshot'")).scalar_one()
    assert n >= 0        # lượt này 0 bản ghi ok ⇒ không có gì để làm bằng chứng, không được nổ


def test_the_watermark_stays_put_when_a_target_failed(db, monkeypatch):
    """Đẩy watermark khi còn mã hỏng là mất trigger vĩnh viễn."""
    _seed(db)
    monkeypatch.setattr(sj, "_engine", lambda: db.engine)
    db.execute(sa.text("INSERT INTO ops.data_domain_state (domain, source, status, watermark)"
                       " VALUES ('market.snapshot', 'fiintrade', 'active', '2026-09-01')"))
    ok = _payload("ownership")
    bad = (FIX / "BVB-valuation-failed.json").read_text(encoding="utf-8")
    calls = {"n": 0}

    def flaky(u, timeout):
        calls["n"] += 1
        return (200, bad) if "/Valuation/" in u else (200, ok if "/Ownership/" in u else _payload(
            "snapshot" if "/Snapshot/" in u else "dividend"))

    sj.run(codes=["ZZJ"], get=flaky, sleep=lambda s: None)
    assert ss.load_watermark(db) == date(2026, 9, 1)
```

- [ ] **Bước 2: Chạy để thấy đỏ**

```bash
cd backend && uv run pytest tests/etl/test_e30_snapshot_job.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'etl.snapshot_job'`.

- [ ] **Bước 3: Viết phần tối thiểu cho xanh**

Tạo `backend/etl/snapshot_job.py`:

```python
"""Một lượt chạy snapshot: due_list → fetch → guard → apply → re-crawl giá (spec §5.1).

Y khuôn `events_job.run`: MỘT giao dịch cho dữ liệu, guard đánh giá TRƯỚC commit — từ chối
thì raise bên trong `engine.begin()` để tự rollback; bằng chứng ghi ở giao dịch riêng.
"""
from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_store, snapshot_fetch, snapshot_guard, snapshot_store
from etl.snapshot_fetch import BadShape, FetchError

log = logging.getLogger("etl.snapshot")
JOB = snapshot_store.JOB
VN = ZoneInfo("Asia/Ho_Chi_Minh")
MAX_RECRAWL = 50                       # trần re-crawl giá một lượt — xem chú thích trong _recrawl


class GuardRefused(Exception):
    def __init__(self, verdict):
        self.verdict = verdict
        super().__init__("; ".join(verdict.reasons))


def _engine():
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        raise RuntimeError("thiếu ETL_DATABASE_URL")
    # pool_pre_ping: kết nối nằm trong pool suốt lượt fetch dài có thể chết sau giấc ngủ 02:00
    return sa.create_engine(url, pool_pre_ping=True)


def _fetch_all(targets, get, sleep, deadline):
    fetched, failed, bad_shape, stopped = [], 0, 0, False
    with snapshot_fetch.open_fetcher(get=get, sleep=sleep) as f:
        for i, t in enumerate(targets, 1):
            if deadline is not None and time.monotonic() > deadline:
                stopped = True
                log.info("hết ngân sách thời gian sau %d/%d target", i - 1, len(targets))
                break
            try:
                item, text = f.fetch_one(t)
                fetched.append(snapshot_store.Fetched(target=t, item=item, text=text))
            except BadShape as e:
                bad_shape += 1
                log.warning("hình dạng lạ: %s", e)
            except FetchError as e:
                failed += 1
                log.warning("%s", e)
            if i % 50 == 0:
                log.info("đã gọi %d/%d target (%d lời gọi, %d retry)", i, len(targets), f.calls, f.retries)
        return fetched, failed, bad_shape, stopped, f.calls, f.retries


def _recrawl(engine, watermark_before, stats):
    """Sự kiện quyền làm chuỗi close_adj của mã đó sai — kéo lại bằng đường có sẵn của lát 3.

    Bỏ qua ở lượt khởi tạo: watermark 1900-01-01 nghĩa là 'mọi mã từng có ngày không hưởng
    quyền', tức 1.523 mã — đúng bằng một lượt backfill trọn vòng ~20 giờ.
    """
    import datetime as dt

    if watermark_before == dt.date(1900, 1, 1):
        stats["recrawl"] = {"skipped": "lượt khởi tạo"}
        return
    with engine.begin() as conn:
        codes = snapshot_store.recrawl_codes(conn, watermark_before)
    if not codes:
        return
    if len(codes) > MAX_RECRAWL:
        stats["recrawl"] = {"skipped": f"{len(codes)} mã > trần {MAX_RECRAWL}", "codes": codes}
        log.warning("re-crawl bỏ qua: %d mã vượt trần %d", len(codes), MAX_RECRAWL)
        return
    try:
        import etl.price_job
        rc = etl.price_job.run(backfill=True, codes=codes)
        stats["recrawl"] = {"codes": codes, "exit": rc}
    except Exception as e:                    # noqa: BLE001 — re-crawl hỏng KHÔNG kéo đổ lượt snapshot
        stats["recrawl"] = {"codes": codes, "error": f"{type(e).__name__}: {e}"}
        log.exception("re-crawl giá thất bại — lượt snapshot vẫn tính là xong")


def run(codes=None, kinds=None, max_minutes=None, get=None, sleep=time.sleep) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    load_dotenv()
    try:
        engine = _engine()
    except RuntimeError as e:
        log.error("%s", e)
        return 2
    run_id = omo_store.open_run(engine, JOB)
    try:
        with engine.begin() as conn:
            watermark = snapshot_store.load_watermark(conn)
            targets = snapshot_store.due_list(conn, watermark, kinds=kinds, codes=codes)
        log.info("tới hạn: %d target (%d theo sự kiện)", len(targets),
                 sum(1 for t in targets if t.found_by == "event"))

        deadline = time.monotonic() + max_minutes * 60 if max_minutes else None
        fetched, failed, bad_shape, stopped, calls, retries = _fetch_all(targets, get, sleep, deadline)

        run_date = datetime.now(VN).date()
        try:
            with engine.begin() as conn:
                tally, written = snapshot_store.apply(conn, fetched, run_date)
                tally.attempted = len(targets)
                tally.failed, tally.bad_shape = failed, bad_shape
                verdict = snapshot_guard.check(tally)
                if not verdict.ok:
                    raise GuardRefused(verdict)
        except GuardRefused as e:
            snapshot_store.store_refusal_evidence(engine, fetched, run_id, e.verdict)
            omo_store.close_run(engine, run_id, "failed",
                                error="guard refused: " + "; ".join(e.verdict.reasons))
            log.error("snapshot từ chối: %s", e.verdict.reasons)
            return 1

        stats = {"tally": vars(tally), "rows_written": written, "calls": calls,
                 "retries": retries, "stopped_early": stopped, "run_date": run_date.isoformat()}
        _recrawl(engine, watermark, stats)

        # Watermark chỉ tiến khi KHÔNG mã nào hỏng: đẩy mốc lên trong lúc còn target chưa
        # phục vụ là mất trigger vĩnh viễn (§5.1 chú thích 2 của plan).
        if failed == 0 and not stopped:
            with engine.begin() as conn:
                wm = snapshot_store.new_watermark(conn)
            snapshot_store.upsert_domain_state(engine, wm.isoformat())
            stats["watermark"] = wm.isoformat()
        else:
            stats["watermark"] = watermark.isoformat()
            stats["watermark_held"] = True

        omo_store.close_run(engine, run_id, "success", stats)
        log.info("snapshot xong: %s", stats)
        return 0
    except Exception as e:                    # noqa: BLE001 — job biên ngoài: mọi lỗi vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("snapshot thất bại")
        return 2
    finally:
        engine.dispose()
```

- [ ] **Bước 4: Nối CLI**

Trong `backend/etl/__main__.py`, thêm **trước** dòng `print(f"etl: subcommand không hợp lệ…`:

```python
    if args[0] == "snapshot":
        import etl.snapshot_job
        parser = argparse.ArgumentParser(prog="etl snapshot")
        parser.add_argument("--codes", type=lambda s: [t.strip().upper() for t in s.split(",") if t.strip()])
        parser.add_argument("--kinds", type=lambda s: [k.strip() for k in s.split(",") if k.strip()])
        parser.add_argument("--max-minutes", type=float, dest="max_minutes")
        parsed = parser.parse_args(args[1:])
        return etl.snapshot_job.run(codes=parsed.codes, kinds=parsed.kinds,
                                    max_minutes=parsed.max_minutes)
```

Và sửa dòng thông báo cuối cho khớp:

```python
    print(f"etl: subcommand không hợp lệ: {args[0]!r} (hỗ trợ: omo, refdata, screener, events, price, snapshot)",
          file=sys.stderr)
```

- [ ] **Bước 5: Chạy test lại**

```bash
cd backend && uv run pytest tests/etl/test_e30_snapshot_job.py -v
```

Expected: 5 PASS.

- [ ] **Bước 6: Chạy TOÀN BỘ bộ test**

```bash
cd backend && uv run pytest -q
```

Expected: **456 + 44 = 500 PASS**, 0 fail. *(Nếu lệch, dán số thật vào ledger — không sửa con số trong plan cho khớp.)*

- [ ] **Bước 7: Commit**

```bash
git add backend/etl/snapshot_job.py backend/etl/__main__.py backend/tests/etl/test_e30_snapshot_job.py
git commit -m "feat(etl): etl snapshot job, CLI wiring and event-driven price re-crawl"
```

---

## Task 9 — Chạy thật dưới credential production (AC2 → AC4, AC6, AC7)

**Files:** Create `docs/90-records/plans/2026-09-04-snapshot-family-etl/ledger.md`

> 🔴 **Luật §3.5:** trước khi tin bất cứ điều gì, chạy tay chính lệnh đó **dưới đúng credential production** ít nhất một lần. 500 test xanh không thay được bước này — ca `assert_migrated` đã chứng minh.

- [ ] **Bước 1: AC2 — ba mã, đường ghi thật**

```bash
cd backend && uv run python -m etl snapshot --codes A32,BAB,BVB
```

Expected: exit 0; log `tới hạn: 12 target`; `rows_written` 12 (lượt đầu của ba mã này).

Kiểm bằng SQL:

```sql
SELECT kind, count(*) FROM market.snapshot_daily
 WHERE trading_date = current_date GROUP BY kind ORDER BY kind;
```

Expected: 4 dòng, mỗi dòng `count = 3`.

- [ ] **Bước 2: AC4 — chạy lại cùng ngày**

```bash
cd backend && uv run python -m etl snapshot --codes A32,BAB,BVB
```

Expected: exit 0, `rows_written: 0`, `tally.unchanged: 12`, số dòng trong bảng **không đổi**.

- [ ] **Bước 3: AC3 — lượt đầy đủ vào kho production**

```bash
cd backend && uv run python -m etl snapshot
```

Expected: exit 0. Ghi vào ledger: số target tới hạn · số lời gọi · thời gian · `retries` · `failed` · `rows_written`. Ngân sách dự kiến **234 target**, **4–8 phút**.

- [ ] **Bước 4: AC7 — ép nguồn hỏng, guard phải từ chối**

```bash
cd backend && uv run python -c "
import os; os.environ['no_proxy']=''
from etl import snapshot_job as sj
rc = sj.run(get=lambda u, t: (503, ''), sleep=lambda s: None)
print('exit', rc)"
```

Expected: `exit 1`; `ops.etl_run` dòng cuối `status='failed'`, `error` chứa `tỷ lệ lời gọi hỏng`; **0 dòng mới** trong `market.snapshot_daily`.

- [ ] **Bước 5: AC6 — re-crawl giá theo sự kiện quyền**

Tìm một mã có `exright_date` gần đây rồi ép một lượt:

```sql
SELECT u.ticker, e.exright_date FROM market.corporate_event e
  JOIN market.issuer_external_id x ON x.external_code = e.organ_code AND x.source='fiintrade'
  JOIN market.security u ON u.issuer_id = x.issuer_id AND u.status='listed'
 WHERE e.exright_date BETWEEN current_date - 30 AND current_date
 ORDER BY e.exright_date DESC LIMIT 5;
```

Đặt watermark lùi lại đúng trước ngày đó, chạy `uv run python -m etl snapshot --kinds dividend`, rồi đọc `stats.recrawl` và so `close_adj` của mã đó trước/sau.

Expected: `stats.recrawl.codes` chứa mã đó, `exit: 0`; `close_adj` của các phiên trước ngày ex đổi, `close_raw` **không** đổi.

- [ ] **Bước 6: Viết `ledger.md`**

Ghi theo khuôn ledger lát 3: mỗi AC một mục, **dán output thật**, ghi cả chỗ hỏng và cách sửa. Không viết "đã thử X" nếu chưa chạy X (§3.2).

- [ ] **Bước 7: Commit**

```bash
git add docs/90-records/plans/2026-09-04-snapshot-family-etl/ledger.md
git commit -m "docs(ledger): AC2, AC3, AC4, AC6, AC7 run against the production store"
```

---

## Task 10 — Tài liệu sống

**Files:** Modify `docs/00-overview/roadmap.md` · `docs/20-design/market-data-store.md` · `database/README.md` · `backend/README.md` · `docs/90-records/plans/2026-09-04-snapshot-family-etl/ledger.md`

- [ ] **Bước 1: `market-data-store.md`**

§4.1 bảng lịch chạy: dòng họ Snapshot ghi **nhịp thật** (quý/tháng), **quota thật** (24/70/70/70), số lời gọi thật/ngày từ AC3. §4.1b: thêm đoạn về `ops.snapshot_check` — nó là chỗ đếm lỗ của lịch, và ghi rõ *"máy dò Screener cho `ownership` hoãn có lý do, điều kiện làm ở spec §3.2"*.

- [ ] **Bước 2: `database/README.md`** — migration head `0015` → `0016`, thêm một dòng mô tả `ops.snapshot_check`.

- [ ] **Bước 3: `backend/README.md`** — mục `etl snapshot`: ba cờ, ý nghĩa `checked_at` là con trỏ, trần `MAX_RECRAWL`, và **không có task Scheduler** (lịch thuộc lát 7).

- [ ] **Bước 4: `roadmap.md`** — lát 4 ✅ kèm số thật; cập nhật số test; viết mục **"Điểm vào cho lát 5 — BCTC"** theo đúng khuôn mục "Điểm vào cho lát 4"; sửa bảng §0 dòng code sản phẩm.

- [ ] **Bước 5: Quét chéo §1.7**

```bash
git grep -n "16/54" -- docs
git grep -n "200–260\|200-260" -- docs
git grep -n "quarterly\[0\]\|yearly\[0\]" -- docs
```

Expected: mọi hit **hoặc đã đúng, hoặc thuộc vùng lịch sử** (`decisions/`, `90-records/`). Riêng `16/54` trong `market-field-selection.md` §1 đá với §5.1 (*18 trường*) — sửa cho khớp, ghi rõ 18 ở ngân hàng / 15 ở phi ngân hàng theo số đo 2026-09-04.

- [ ] **Bước 6: Commit**

```bash
git add docs backend/README.md database/README.md
git commit -m "docs: slice 4 done - snapshot family cadence, ledger table and slice 5 entry point"
```

---

## Task 11 — AC5 (ngày hôm sau), review hai trục, merge

> AC5 **không chạy được trong hôm nay** — nó là phép đo ngày-qua-ngày. Task này mở lại vào phiên kế tiếp.

- [ ] **Bước 1: AC5 — chạy lại đúng tập mã của hôm trước**

```bash
cd backend && uv run python -m etl snapshot --codes A32,BAB,BVB
```

Expected: `tally.unchanged = 12`, `rows_written = 0`. **Nếu có mã đổi:** đọc `snapshot_daily` hai dòng liền nhau, tìm trường nào lệch, và **bỏ trường đó khỏi tập trắng** — đây chính là điều kiện đảo ngược của spec §4.3, không phải lý do nới ngưỡng guard.

- [ ] **Bước 2: Kiểm cả nhóm quét sàn của lượt AC3**

```sql
SELECT stats->'tally'->>'changed_floor' AS changed_floor,
       stats->'tally'->>'floor_compared' AS floor_compared
  FROM ops.etl_run WHERE job = 'market.snapshot' ORDER BY run_id DESC LIMIT 2;
```

Expected: lượt hôm sau `changed_floor` nhỏ (vài mã, do công bố thật), không phải hàng trăm.

- [ ] **Bước 3: Review hai trục** — dùng skill `superpowers:requesting-code-review`, hai trục **Chuẩn** (đúng repo, code smell) và **Spec** (thiếu/sai/scope-creep), báo riêng, không gộp.

- [ ] **Bước 4: Sửa mọi phát hiện, chạy lại toàn bộ test, dán số thật vào ledger.**

- [ ] **Bước 5: Merge**

```bash
git checkout main && git merge --no-ff feat/snapshot-family-etl -m "Merge: slice 4 - snapshot family ETL"
```

---

## Tự kiểm plan (đã chạy trước khi giao)

**1 · Phủ spec.** Từng mục spec → task: §4.1 sổ kiểm → Task 1, 7 · §4.2 quét sàn cuốn chiếu → Task 6 · §4.3 tập trắng → Task 4 · §4.4 domain → Task 1 · §5.2 fetch → Task 2, 3 · §5.3 normalize → Task 4 · §5.4 store → Task 6, 7 · §5.5 guard → Task 5 · §5.6 re-crawl → Task 8 · §5.7 lịch → Task 10 · §6 seam → rải trong Task 1–8 · §7 AC1–AC7 → Task 8 (AC1), Task 9 (AC2–4, 6, 7), Task 11 (AC5) · §8 checklist → Task 10. **Không mục nào không có task.**

**2 · Quét placeholder.** Không có "TBD", không có "xử lý lỗi cho phù hợp", không có "test tương tự Task N". Mọi bước code đều có khối code thật.

**3 · Nhất quán kiểu.** `Target` (Task 3) dùng nguyên vẹn ở Task 6, 7, 8 · `Tally` (Task 5) là thứ `apply` trả và `check` nhận · `Fetched` (Task 7) là thứ `_fetch_all` dựng · `keep_hash(kind, item)` một chữ ký duy nhất · `get(url, timeout)` một chữ ký duy nhất ở cả `open_fetcher` lẫn test giả.

**4 · Ba chỗ plan sửa spec** *(spec đã vá cùng ngày, xem git log của `spec.md`)*: quy tắc chọn kỳ báo cáo là `max(year, quarter)` chứ không phải `[0]`; tập trắng `snapshot` là 18 trường ở ngân hàng và **15 ở phi ngân hàng**; và re-crawl giá phải có trần cộng luật bỏ qua lượt khởi tạo, nếu không cold start kéo theo một lượt backfill 20 giờ.

