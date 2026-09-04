# Plan — lát 5 `etl fundamentals`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Job `python -m etl fundamentals` nạp ba báo cáo tài chính (bỏ null) + danh sách PDF + từ điển 729 mã vào Postgres, kích hoạt theo sự kiện `Earning`, quét sàn 90 ngày, ghi khi đổi, có `--backfill` cho lượt điền đầu.

**Architecture:** Nhân bản khuôn năm module của lát 4 (`snapshot_*`): `fundamentals_fetch` (I/O) → `fundamentals_normalize` (thuần: payload → dòng dạng dài + hash) → `fundamentals_guard` (thuần: ngưỡng) → `fundamentals_store` (SQL: danh sách tới hạn, apply xoá-chèn, sổ kiểm `ops.fundamentals_check`, từ điển) → `fundamentals_job` (một lượt, một giao dịch dữ liệu, guard trước commit). Migration `0017` đi trước.

**Tech Stack:** Python 3.12 · SQLAlchemy 2 (`sa.text`) · psycopg 3 · httpx · pytest trên Postgres thật (`TEST_DATABASE_URL`) · Alembic.

**Spec:** [spec.md](spec.md) — plan chỉ nói *chính xác thế nào*; *cái gì* và *vì sao* ở spec.

## Global Constraints

- Mọi lệnh Python chạy từ `backend/` bằng `uv run`, đặt `PYTHONIOENCODING=utf-8`. Test cần `.env` của repo: `set -a; . ../.env; set +a` (Git Bash) trước `uv run pytest`.
- Giãn cách ≥ **0,5 s** giữa hai lần bắt đầu lời gọi; header `Origin: https://fiinapp.bvsc.com.vn`; timeout **30 s**; retry **3**, backoff **2/4/8 s**; `status ∈ {0, "Success"}` (spec §5.2).
- `metric_code` **chữ thường**; bỏ null; bỏ đúng 8 khoá `NON_METRIC` (spec §5.3).
- `quarterReport` của báo cáo phải ∈ 1..5; `lengthReport` của PDF phải ∈ {1,2,3,4,5,6,9} (spec §4.5).
- Quota quét sàn **20** mã/kind/ngày, nhịp **90** ngày, trần trigger **300** issuer/lượt (spec §5.4).
- Guard: đổi nhóm quét sàn > 20 % · hỏng > 20 % · sai hình dạng > 5 % · rỗng > 5 %, `MIN_SAMPLE = 20` (spec §5.5).
- Test đụng CSDL dùng chung phải dập nền và lọc theo mã của chính test (bài học 3 lát 4). Test quyền chạy `SET LOCAL ROLE dlck_etl`.
- Không tạo `.superpowers/` trong repo; artifact tạm ở scratchpad. Commit message tiếng Anh, Conventional Commits, kết bằng `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Không `--no-verify`, không force push. Nhánh: `feat/fundamentals-etl`.

## File map

| File | Trách nhiệm |
|---|---|
| `database/migrations/versions/0017_fundamentals.py` | nới CHECK hai bảng, `source_id`, bảng `ops.fundamentals_check` |
| `backend/tests/schema/test_s14_fundamentals.py` | seam của migration, kể cả dưới role `dlck_etl` |
| `backend/tests/etl/fixtures/fundamentals/` | 5 mẫu thật chép từ khảo sát: `A32-bs.json` `A32-is.json` `A32-cf.json` `A32-reports.json` `BAB-reports.json` |
| `backend/etl/fundamentals_fetch.py` | URL, `classify`, `Fetcher` |
| `backend/etl/fundamentals_normalize.py` | `statement_rows`, `report_rows`, `rows`, `payload_hash`, `BadRecord` |
| `backend/etl/fundamentals_guard.py` | `Tally`, `Verdict`, `check` |
| `backend/etl/fundamentals_store.py` | `_UNIVERSE`, `due_list`, `load_dictionary`, `apply`, `remaining`, mốc nước, bằng chứng |
| `backend/etl/fundamentals_job.py` | `run(...)` |
| `backend/etl/__main__.py` | subcommand `fundamentals` |
| `backend/tests/etl/test_e31…e35_fundamentals_*.py` | một file test mỗi module |

---

### Task 1: Migration `0017` và test schema

**Files:**
- Create: `database/migrations/versions/0017_fundamentals.py`
- Create: `backend/tests/schema/test_s14_fundamentals.py`

**Interfaces:**
- Produces: bảng `ops.fundamentals_check(issuer_id, kind, checked_at, payload_hash, changed_at, found_by)`; cột `market.financial_report_file.source_id bigint NOT NULL UNIQUE`; CHECK `length_report IN (1,2,3,4,5,6,9)` trên `financial_report_file` và `corporate_event`. Tên ràng buộc thật (đọc từ `pg_constraint` 2026-09-04): `financial_report_file_source_url_key`, `financial_report_file_length_report_check`, `corporate_event_length_report_check`.

- [ ] **Step 1: Viết test đỏ**

```python
# backend/tests/schema/test_s14_fundamentals.py
import pytest
import sqlalchemy as sa

from tests.schema.conftest import expect_violation


def _issuer(db, name="Test fundamentals"):
    return db.execute(sa.text("INSERT INTO market.issuer (name) VALUES (:n) RETURNING issuer_id"),
                      {"n": name}).scalar_one()


def test_report_file_accepts_half_year_and_nine_month_but_statement_does_not(db):
    """Đo 2026-09-04: getFinancialReports phát lengthReport 6/9 (28/307 dòng); ba endpoint số liệu
    thì KHÔNG (0 dòng trên 5 mã) — nên chỉ bảng PDF và corporate_event được nới."""
    iid = _issuer(db)
    for length in (6, 9):
        db.execute(sa.text(
            "INSERT INTO market.financial_report_file (issuer_id, year_report, length_report, title, source_url, source_id)"
            " VALUES (:i, 2026, :l, 't', :u, :s)"),
            {"i": iid, "l": length, "u": f"https://x/{length}.pdf", "s": 1000 + length})
        db.execute(sa.text(
            "INSERT INTO market.corporate_event (event_type, issuer_id, public_date, year_report, length_report, payload)"
            " VALUES ('Earning', :i, '2026-08-01', 2026, :l, '{}'::jsonb)"), {"i": iid, "l": length})
    assert expect_violation(db,
        "INSERT INTO market.financial_statement (issuer_id, year_report, length_report, statement_type, metric_code, value)"
        " VALUES (:i, 2026, 6, 'BS', 'bsa1', 1)", {"i": iid})
    assert expect_violation(db,
        "INSERT INTO market.financial_report_file (issuer_id, length_report, source_url, source_id)"
        " VALUES (:i, 7, 'https://x/7.pdf', 1007)", {"i": iid})       # 7, 8 chưa ai thấy — dải liền sẽ lọt


def test_report_file_is_keyed_by_source_id_and_tolerates_a_duplicate_url(db):
    """BAB thật: id 9322194 (lengthReport 9) và 9322093 (lengthReport 3) trỏ CÙNG một PDF Q3/2024."""
    iid = _issuer(db, "BAB gia")
    url = "https://cmsv5.fiingroup.vn/medialib/FG/2024/2024-10/2024-10-30/20550225108400700_BAB_BCTC_Q3_2024_HN.pdf"
    for sid, length in ((9322194, 9), (9322093, 3)):
        db.execute(sa.text(
            "INSERT INTO market.financial_report_file (issuer_id, year_report, length_report, title, source_url, source_id)"
            " VALUES (:i, 2024, :l, 'BCTC Q3 2024', :u, :s)"), {"i": iid, "l": length, "u": url, "s": sid})
    assert expect_violation(db,
        "INSERT INTO market.financial_report_file (issuer_id, source_url, source_id)"
        " VALUES (:i, 'https://x/khac.pdf', 9322194)", {"i": iid})
    n = db.execute(sa.text("SELECT count(*) FROM market.financial_report_file WHERE issuer_id = :i"),
                   {"i": iid}).scalar_one()
    assert n == 2


def test_fundamentals_check_keeps_one_row_per_issuer_and_kind(db):
    iid = _issuer(db, "Check")
    db.execute(sa.text(
        "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
        " VALUES (:i, 'bs', now(), 'abc', 'floor')"), {"i": iid})
    assert expect_violation(db,
        "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
        " VALUES (:i, 'bs', now(), 'def', 'event')", {"i": iid})
    assert expect_violation(db,
        "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
        " VALUES (:i, 'snapshot', now(), 'abc', 'floor')", {"i": iid})


def test_fundamentals_tables_work_under_the_etl_role(db):
    """§3.5: quyền kiểm bằng đúng role production — kể cả DELETE trên financial_statement,
    đường mà lát này dùng ở mỗi lần nội dung đổi."""
    iid = _issuer(db, "Quyen dlck_etl")
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text(
        "INSERT INTO market.financial_statement (issuer_id, year_report, length_report, statement_type, metric_code, value)"
        " VALUES (:i, 2025, 5, 'BS', 'bsa1', 365335639678)"), {"i": iid})
    db.execute(sa.text("DELETE FROM market.financial_statement WHERE issuer_id = :i AND statement_type = 'BS'"), {"i": iid})
    db.execute(sa.text(
        "INSERT INTO market.financial_report_file (issuer_id, source_url, source_id) VALUES (:i, 'https://x/r.pdf', 1)"),
        {"i": iid})
    db.execute(sa.text(
        "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
        " VALUES (:i, 'reports', now(), 'h', 'floor')"), {"i": iid})
    db.execute(sa.text(
        "INSERT INTO market.metric_dictionary (dictionary, code, name_vi, unit) VALUES ('field_dictionary', 'zz_test', 'x', 'VND')"
        " ON CONFLICT (dictionary, code) DO UPDATE SET name_vi = excluded.name_vi"))
    db.execute(sa.text(
        "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
        " VALUES ('fundamentals', 'fundamentals:bs:ZZ', 'json', '{}'::jsonb, '{}'::jsonb)"))
    got = db.execute(sa.text("SELECT count(*) FROM ops.fundamentals_check WHERE issuer_id = :i"), {"i": iid}).scalar_one()
    assert got == 1
```

- [ ] **Step 2: Chạy test, phải đỏ**

Run: `cd backend && set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run pytest tests/schema/test_s14_fundamentals.py -q -p no:cacheprovider`
Expected: FAIL — `relation "ops.fundamentals_check" does not exist` / `column "source_id" ... does not exist`.

- [ ] **Step 3: Viết migration**

```python
# database/migrations/versions/0017_fundamentals.py
"""Lát 5 — báo cáo tài chính.

- financial_report_file: khoá theo `source_id` (id của nguồn). Đo 2026-09-04: BID và BAB mỗi mã có
  hai `id` khác nhau trỏ CÙNG một URL (bản quý 3 và bản 9 tháng luỹ kế cùng một file PDF), nên
  UNIQUE (source_url) cũ vỡ ngay trong một response.
- length_report: nguồn phát 6 (bán niên) và 9 (9 tháng) ở getFinancialReports — 28/307 dòng trên
  4 mã — nới cho financial_report_file và corporate_event (getCorporateEarning cùng họ, chưa phát
  nhưng không có gì chặn). Viết IN (...) chứ không BETWEEN: 7, 8 chưa ai thấy, dải liền sẽ lọt.
- financial_statement GIỮ 1–5: ba endpoint số liệu chỉ phát quarterReport 1–5 (0 dòng khác trên
  5 mã). Nếu một ngày phát 6/9, normalize xếp bad_shape và guard báo — không lặng lẽ nạp dòng bán
  niên làm sai mọi phép cộng quý.
- ops.fundamentals_check: sổ kiểm cùng hình với ops.snapshot_check (0016).

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE market.financial_report_file ADD COLUMN source_id bigint;
        UPDATE market.financial_report_file SET source_id = file_id WHERE source_id IS NULL;
        ALTER TABLE market.financial_report_file
          ALTER COLUMN source_id SET NOT NULL,
          ADD CONSTRAINT financial_report_file_source_id_key UNIQUE (source_id),
          DROP CONSTRAINT financial_report_file_source_url_key,
          DROP CONSTRAINT financial_report_file_length_report_check,
          ADD CONSTRAINT financial_report_file_length_report_check
              CHECK (length_report IN (1,2,3,4,5,6,9));   -- 1-4 quý · 5 năm · 6 bán niên · 9 chín tháng
        ALTER TABLE market.corporate_event
          DROP CONSTRAINT corporate_event_length_report_check,
          ADD CONSTRAINT corporate_event_length_report_check
              CHECK (length_report IN (1,2,3,4,5,6,9));

        CREATE TABLE ops.fundamentals_check (
          issuer_id    bigint NOT NULL REFERENCES market.issuer,
          kind         text   NOT NULL CHECK (kind IN ('bs','is','cf','reports')),
          checked_at   timestamptz NOT NULL,
          payload_hash text   NOT NULL,      -- sha256 của TOÀN BỘ dòng đã chuẩn hoá (không tập trắng)
          changed_at   timestamptz,          -- lần đầu kiểm cũng tính là đổi — không NULL trong thực tế
          found_by     text   NOT NULL CHECK (found_by IN ('event','floor')),
          PRIMARY KEY (issuer_id, kind)
        );
        CREATE INDEX ON ops.fundamentals_check (kind, checked_at);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE ops.fundamentals_check;
        ALTER TABLE market.corporate_event
          DROP CONSTRAINT corporate_event_length_report_check,
          ADD CONSTRAINT corporate_event_length_report_check CHECK (length_report BETWEEN 1 AND 5);
        ALTER TABLE market.financial_report_file
          DROP CONSTRAINT financial_report_file_length_report_check,
          ADD CONSTRAINT financial_report_file_length_report_check CHECK (length_report BETWEEN 1 AND 5),
          ADD CONSTRAINT financial_report_file_source_url_key UNIQUE (source_url),
          DROP CONSTRAINT financial_report_file_source_id_key,
          DROP COLUMN source_id;
        """
    )
```

- [ ] **Step 4: Chạy lại test, phải xanh** — cùng lệnh Step 2. Expected: `4 passed`. Rồi chạy cả bộ schema: `uv run pytest tests/schema -q -p no:cacheprovider` → tất cả xanh (fixture `migrated_engine` dựng lại DB test từ đầu, nên migration mới được kiểm cả `upgrade`).

- [ ] **Step 5: Commit**

```bash
git add database/migrations/versions/0017_fundamentals.py backend/tests/schema/test_s14_fundamentals.py
git commit -m "feat(db): 0017 - fundamentals_check, source_id on report files, length_report 6/9 where the source emits them"
```

---

### Task 2: Fixture và `fundamentals_fetch`

**Files:**
- Create: `backend/tests/etl/fixtures/fundamentals/{A32-bs,A32-is,A32-cf,A32-reports,BAB-reports}.json` — chép nguyên văn từ `docs/90-records/surveys/2026-09-04-bctc-endpoints/samples/` (`A32-balance_sheet.json → A32-bs.json`, `A32-income_statement.json → A32-is.json`, `A32-cash_flow.json → A32-cf.json`, hai file reports giữ tên).
- Create: `backend/etl/fundamentals_fetch.py`
- Create: `backend/tests/etl/test_e31_fundamentals_fetch.py`

**Interfaces:**
- Produces: `KINDS = ("bs","is","cf","reports")` · `url(kind, organ_code) -> str` · `classify(kind, http, text) -> tuple[str, dict|None]` (ok/retry/bad_shape; với báo cáo `item` có `quarterly` và `yearly` là list; với `reports` `item = {"items": [...]}`) · `Target(kind, issuer_id, organ_code, ticker, found_by)` · `FetchError`, `BadShape` · `open_fetcher(get=None, sleep=time.sleep, clock=time.monotonic)` cho `Fetcher.fetch_one(t) -> (item, text)`, thuộc tính `calls`, `retries`.

- [ ] **Step 1: Chép fixture**

```bash
cd backend && mkdir -p tests/etl/fixtures/fundamentals
S=../docs/90-records/surveys/2026-09-04-bctc-endpoints/samples
cp $S/A32-balance_sheet.json tests/etl/fixtures/fundamentals/A32-bs.json
cp $S/A32-income_statement.json tests/etl/fixtures/fundamentals/A32-is.json
cp $S/A32-cash_flow.json tests/etl/fixtures/fundamentals/A32-cf.json
cp $S/A32-reports.json $S/BAB-reports.json tests/etl/fixtures/fundamentals/
```

- [ ] **Step 2: Viết test đỏ**

```python
# backend/tests/etl/test_e31_fundamentals_fetch.py
import pathlib

import httpx
import pytest

from etl import fundamentals_fetch as ff

FIX = pathlib.Path(__file__).parent / "fixtures" / "fundamentals"


def _text(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_url_of_each_kind_lives_on_the_fundamental_host():
    assert ff.url("bs", "ASECO32") == (
        "https://wlgw-fundamental.fiintrade.vn/FinancialStatement/GetBalanceSheet?OrganCode=ASECO32&language=vi")
    assert ff.url("is", "NASB").endswith("/FinancialStatement/GetIncomeStatement?OrganCode=NASB&language=vi")
    assert ff.url("cf", "NASB").endswith("/FinancialStatement/GetCashFlow?OrganCode=NASB&language=vi")
    assert ff.url("reports", "NASB").endswith("/FinancialStatement/GetFinancialReports?OrganCode=NASB&language=vi")
    with pytest.raises(ValueError):
        ff.url("snapshot", "NASB")


def test_classify_accepts_status_success_and_returns_the_statement_item():
    verdict, item = ff.classify("bs", 200, _text("A32-bs.json"))
    assert verdict == "ok"
    assert item["quarterly"] == [] and len(item["yearly"]) == 10        # A32: chỉ kỳ năm (đo 2026-09-04)


def test_classify_accepts_status_zero_too():
    """Tài liệu 2026-08-10 đo status 0, 2026-09-04 đo "Success" — cùng endpoint (quy ước §6.1)."""
    body = '{"items": [{"quarterly": [], "yearly": []}], "status": 0}'
    assert ff.classify("cf", 200, body)[0] == "ok"


def test_classify_of_reports_returns_the_item_list_even_when_empty():
    verdict, item = ff.classify("reports", 200, _text("A32-reports.json"))
    assert verdict == "ok" and len(item["items"]) == 8 and item["items"][0]["id"] == 9412069
    verdict, item = ff.classify("reports", 200, '{"items": [], "totalCount": 0, "status": "Success"}')
    assert verdict == "ok" and item == {"items": []}                   # TAH thật trả 0 báo cáo — không phải lỗi


def test_classify_treats_an_empty_statement_item_list_as_an_empty_statement():
    verdict, item = ff.classify("is", 200, '{"items": [], "status": "Success"}')
    assert verdict == "ok" and item == {"quarterly": [], "yearly": []}


def test_classify_sends_failed_status_broken_json_and_non_200_to_retry():
    assert ff.classify("bs", 200, '{"items": null, "status": "Failed"}') == ("retry", None)
    assert ff.classify("bs", 200, "<html>502</html>") == ("retry", None)
    assert ff.classify("bs", 503, "") == ("retry", None)


def test_classify_calls_a_missing_root_key_bad_shape():
    assert ff.classify("bs", 200, '{"items": [{"yearly": []}], "status": "Success"}') == ("bad_shape", None)
    assert ff.classify("reports", 200, '{"items": [1, 2], "status": "Success"}') == ("bad_shape", None)


def _target(kind="bs"):
    return ff.Target(kind=kind, issuer_id=1, organ_code="ASECO32", ticker="A32", found_by="floor")


def test_fetch_one_spaces_calls_half_a_second_apart_and_retries_with_backoff():
    clock = [0.0]
    slept = []
    answers = iter([(503, ""), (200, _text("A32-bs.json")), (200, _text("A32-cf.json"))])

    def get(u, timeout):
        return next(answers)

    def sleep(s):
        slept.append(s)
        clock[0] += s

    with ff.open_fetcher(get=get, sleep=sleep, clock=lambda: clock[0]) as f:
        item, text = f.fetch_one(_target())
        f.fetch_one(_target("cf"))                     # lời gọi thứ hai ngay sau — phải ngủ để đủ 0,5 s
    assert len(item["yearly"]) == 10
    assert f.calls == 3 and f.retries == 1
    assert slept[0] == 2                               # backoff đầu tiên
    assert any(0 < s <= 0.5 for s in slept[1:])        # giãn cách


def test_fetch_one_gives_up_after_four_attempts_and_names_the_code():
    with ff.open_fetcher(get=lambda u, t: (500, "loi"), sleep=lambda s: None) as f:
        with pytest.raises(ff.FetchError, match="ASECO32/bs"):
            f.fetch_one(_target())
    assert f.calls == 4 and f.retries == 3


def test_fetch_one_treats_a_transport_exception_like_a_bad_response():
    """Bài học e7f80f6: timeout qua giấc ngủ 02:00 từng lọt qua vòng retry và giết cả lượt."""
    answers = iter([httpx.ReadTimeout("ngu"), (200, _text("A32-cf.json"))])

    def get(u, timeout):
        a = next(answers)
        if isinstance(a, Exception):
            raise a
        return a

    with ff.open_fetcher(get=get, sleep=lambda s: None) as f:
        item, _ = f.fetch_one(_target("cf"))
    assert len(item["yearly"]) == 10 and f.retries == 1


def test_fetch_one_raises_bad_shape_without_retrying():
    with ff.open_fetcher(get=lambda u, t: (200, '{"items": [{"yearly": []}], "status": "Success"}'),
                         sleep=lambda s: None) as f:
        with pytest.raises(ff.BadShape):
            f.fetch_one(_target())
    assert f.calls == 1
```

- [ ] **Step 3: Chạy test, phải đỏ** — `uv run pytest tests/etl/test_e31_fundamentals_fetch.py -q -p no:cacheprovider` → `ModuleNotFoundError: etl.fundamentals_fetch`.

- [ ] **Step 4: Viết module**

```python
# backend/etl/fundamentals_fetch.py
"""Tải ba báo cáo tài chính và danh sách PDF theo organCode, tuần tự, có giãn cách (spec §5.2). I/O thuần.

Đo 2026-09-04 (khảo sát BCTC §6): `status` = "Success" 21/21, tài liệu 2026-08-10 đo 0 — cùng
endpoint ⇒ hợp lệ là status ∈ {0, "Success"} (quy ước §6.1). Payload tới 408 KB (VNM) ⇒ timeout
30 s cho mọi kind. `items: []` ở báo cáo số liệu KHÔNG phải sai hình dạng: coi là báo cáo rỗng,
normalize/apply xử lý (spec §5.4 bước 2).
"""
from __future__ import annotations

import contextlib
import json
import time
from dataclasses import dataclass

import httpx

FUND = "https://wlgw-fundamental.fiintrade.vn"
FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"       # bắt buộc cho *.fiintrade.vn (00-conventions §2)

KINDS = ("bs", "is", "cf", "reports")
ENDPOINT = {"bs": "GetBalanceSheet", "is": "GetIncomeStatement",
            "cf": "GetCashFlow", "reports": "GetFinancialReports"}
TIMEOUT = 30.0
RETRIES = 3
BACKOFF = (2, 4, 8)
MIN_INTERVAL = 0.5                                 # trần 2 request/giây (market-data-store §4.2)
_EMPTY_STATEMENT = {"quarterly": [], "yearly": []}


def url(kind: str, organ_code: str) -> str:
    if kind not in ENDPOINT:
        raise ValueError(f"kind lạ: {kind!r}")
    return f"{FUND}/FinancialStatement/{ENDPOINT[kind]}?OrganCode={organ_code}&language=vi"


def classify(kind: str, http: int, text: str) -> tuple[str, dict | None]:
    """('ok', item) | ('retry', None) | ('bad_shape', None)."""
    if http != 200:
        return "retry", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    if not isinstance(d, dict) or d.get("status") not in (0, "Success"):
        return "retry", None                       # gồm "Failed" — lỗi tạm thời của nguồn (quy ước §10.5)
    items = d.get("items")
    if not isinstance(items, list):
        return "bad_shape", None
    if kind == "reports":
        if not all(isinstance(i, dict) for i in items):
            return "bad_shape", None
        return "ok", {"items": items}
    if not items:
        return "ok", dict(_EMPTY_STATEMENT)
    item = items[0]
    if not isinstance(item, dict) or not isinstance(item.get("quarterly"), list) \
            or not isinstance(item.get("yearly"), list):
        return "bad_shape", None
    return "ok", item


@dataclass(frozen=True)
class Target:
    kind: str
    issuer_id: int
    organ_code: str
    ticker: str
    found_by: str                                  # 'event' | 'floor'


class FetchError(Exception):
    """Một mã/kind hỏng sau mọi lần thử — để nó CHƯA KIỂM, không ghi gì."""


class BadShape(Exception):
    """Response hợp lệ nhưng sai hình dạng — nguồn đổi, thử lại vô ích."""


class Fetcher:
    def __init__(self, get, sleep=time.sleep, clock=time.monotonic):
        self._get, self._sleep, self._clock = get, sleep, clock
        self.calls = 0
        self.retries = 0
        self._last: float | None = None

    def _request(self, u: str) -> tuple[int, str]:
        if self._last is not None:
            wait = MIN_INTERVAL - (self._clock() - self._last)
            if wait > 0:
                self._sleep(wait)
        self._last = self._clock()
        self.calls += 1
        return self._get(u, TIMEOUT)

    def fetch_one(self, t: Target) -> tuple[dict, str]:
        u = url(t.kind, t.organ_code)
        http, text = 0, ""
        for attempt in range(RETRIES + 1):
            try:
                http, text = self._request(u)
            except httpx.HTTPError as e:
                # Timeout/đứt kết nối đi CÙNG đường với response xấu (bài học lát 3, e7f80f6)
                http, text = 0, f"{type(e).__name__}: {e}"
            verdict, item = classify(t.kind, http, text)
            if verdict == "ok":
                return item, text
            if verdict == "bad_shape":
                raise BadShape(f"{t.organ_code}/{t.kind}: sai hình dạng response")
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
    with httpx.Client(headers={"Origin": FIIN_ORIGIN}) as client:
        def get_one(u: str, timeout: float) -> tuple[int, str]:
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text
        yield Fetcher(get_one, sleep, clock)
```

- [ ] **Step 5: Chạy test, phải xanh** — cùng lệnh Step 3. Expected: `11 passed`.

- [ ] **Step 6: Commit**

```bash
git add backend/etl/fundamentals_fetch.py backend/tests/etl/test_e31_fundamentals_fetch.py backend/tests/etl/fixtures/fundamentals/
git commit -m "feat(etl): fundamentals_fetch - four FiinTrade statement endpoints with spacing, retry and shape check"
```

---

### Task 3: `fundamentals_normalize`

**Files:**
- Create: `backend/etl/fundamentals_normalize.py`
- Create: `backend/tests/etl/test_e32_fundamentals_normalize.py`

**Interfaces:**
- Produces: `NON_METRIC` · `STATEMENT = {"bs":"BS","is":"IS","cf":"CF"}` · `StatementRow(year, length, statement_type, metric_code, value)` · `ReportRow(source_id, year, length, title, url)` · `rows(kind, item) -> list` · `payload_hash(rows) -> str` · `EMPTY_HASH` · `class BadRecord(ValueError)`.

- [ ] **Step 1: Viết test đỏ**

```python
# backend/tests/etl/test_e32_fundamentals_normalize.py
import json
import pathlib

import pytest

from etl import fundamentals_normalize as fn

FIX = pathlib.Path(__file__).parent / "fixtures" / "fundamentals"


def _item(name):
    d = json.loads((FIX / name).read_text(encoding="utf-8"))
    return {"items": d["items"]} if name.endswith("reports.json") else d["items"][0]


def test_rows_of_a32_match_the_independent_count():
    """1.749 / 980 / 916 do docs/.../count_rows.py đếm riêng trên cùng mẫu — không chung code."""
    assert len(fn.rows("bs", _item("A32-bs.json"))) == 1749
    assert len(fn.rows("is", _item("A32-is.json"))) == 980
    assert len(fn.rows("cf", _item("A32-cf.json"))) == 916


def test_rows_carry_the_literal_values_of_the_2025_annual_report():
    got = {(r.year, r.length, r.metric_code): r for r in fn.rows("bs", _item("A32-bs.json"))}
    r = got[(2025, 5, "bsa1")]
    assert r.statement_type == "BS" and r.value == 365335639678.0
    assert got[(2025, 5, "bsa23")].value == 125782590230.0
    assert got[(2025, 5, "bsa53")].value == 491118229908.0                # bsa1 + bsa23 = bsa53 (Phụ lục A)
    assert (2025, 5, "bsb98") not in got                                  # null ⇒ không có dòng
    assert (2025, 5, "organcode") not in got and (2025, 5, "organCode") not in got
    cf = {(r.year, r.metric_code): r.value for r in fn.rows("cf", _item("A32-cf.json"))}
    assert cf[(2025, "cfa18")] == -55721888430.0


def test_rows_lower_case_the_two_mixed_case_keys_and_drop_the_eight_non_metric_keys():
    codes = {r.metric_code for r in fn.rows("bs", _item("A32-bs.json"))}
    assert "bsi141" in codes and "bsI141" not in codes                   # đo 2026-09-04, 4/4 mã
    is_codes = {r.metric_code for r in fn.rows("is", _item("A32-is.json"))}
    assert not ({"ebit", "ebitda", "operating", "rtq29"} & is_codes)


def test_rows_refuse_a_quarter_report_outside_one_to_five():
    item = {"quarterly": [{"yearReport": 2026, "quarterReport": 6, "bsa1": 1.0}], "yearly": []}
    with pytest.raises(fn.BadRecord, match="quarterReport"):
        fn.rows("bs", item)


def test_rows_refuse_a_duplicated_period():
    item = {"quarterly": [], "yearly": [{"yearReport": 2025, "quarterReport": 5, "bsa1": 1.0},
                                        {"yearReport": 2025, "quarterReport": 5, "bsa1": 2.0}]}
    with pytest.raises(fn.BadRecord, match="trùng"):
        fn.rows("bs", item)


def test_report_rows_keep_the_source_id_and_the_seven_allowed_lengths():
    got = fn.rows("reports", _item("A32-reports.json"))
    assert len(got) == 8 and got[0].source_id == 9412069 and got[0].year == 2025 and got[0].length == 5
    assert got[0].title == "BCTC đã kiểm toán năm 2025"
    assert got[0].url.endswith("A32_BCTC_CN_2025_HN_KT.pdf")
    bab = fn.rows("reports", _item("BAB-reports.json"))
    assert len(bab) == 106 and {r.length for r in bab} == {1, 2, 3, 4, 5, 6, 9}
    with pytest.raises(fn.BadRecord):
        fn.rows("reports", {"items": [{"id": 1, "yearReport": 2024, "lengthReport": 7, "sourceUrl": "u"}]})
    with pytest.raises(fn.BadRecord):
        fn.rows("reports", {"items": [{"yearReport": 2024, "lengthReport": 1, "sourceUrl": "u"}]})   # thiếu id


def test_payload_hash_ignores_order_and_nulls_but_sees_a_value_change():
    item = _item("A32-bs.json")
    h0 = fn.payload_hash(fn.rows("bs", item))

    shuffled = {"quarterly": [], "yearly": list(reversed(item["yearly"]))}
    assert fn.payload_hash(fn.rows("bs", shuffled)) == h0                # đổi thứ tự kỳ

    rec = dict(item["yearly"][0]); rec = {k: rec[k] for k in reversed(list(rec))}
    reordered = {"quarterly": [], "yearly": [rec] + item["yearly"][1:]}
    assert fn.payload_hash(fn.rows("bs", reordered)) == h0               # đổi thứ tự khoá

    extra_null = {"quarterly": [], "yearly": [dict(item["yearly"][0], zzz_new=None)] + item["yearly"][1:]}
    assert fn.payload_hash(fn.rows("bs", extra_null)) == h0              # thêm ô null

    changed = {"quarterly": [], "yearly": [dict(item["yearly"][0], bsa1=1.0)] + item["yearly"][1:]}
    assert fn.payload_hash(fn.rows("bs", changed)) != h0                 # đổi một giá trị

    assert fn.payload_hash([]) == fn.EMPTY_HASH
```

- [ ] **Step 2: Chạy test, phải đỏ** — `uv run pytest tests/etl/test_e32_fundamentals_normalize.py -q -p no:cacheprovider` → `ModuleNotFoundError`.

- [ ] **Step 3: Viết module**

```python
# backend/etl/fundamentals_normalize.py
"""Payload BCTC → dòng dạng dài + hash (spec §5.3). Thuần, không I/O.

Không có danh sách trắng: ba endpoint không có trường nào tính từ giá (đã kiểm 557 khoá, khảo sát
§6.2), nên hash trên TOÀN BỘ dòng đã chuẩn hoá — bớt đúng cái luật hay hỏng nhất của lát 4.
Hash tính trên dòng ĐÃ SẮP XẾP, nên nguồn đổi thứ tự khoá/kỳ hay thêm ô null không gây báo đổi giả.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass

# 8 khoá không phải mã chỉ tiêu, có mặt trong response (đối chiếu từ điển 2026-09-04, khảo sát §6.2).
NON_METRIC = frozenset({"organCode", "ebit", "ebitDa", "operating",
                        "otherAssetBank", "otherAssetNonBank", "otherLiabilties", "rtq29"})
STATEMENT = {"bs": "BS", "is": "IS", "cf": "CF"}
STATEMENT_LENGTHS = frozenset({1, 2, 3, 4, 5})            # 1-4 quý, 5 năm — 0 dòng khác trên 5 mã
REPORT_LENGTHS = frozenset({1, 2, 3, 4, 5, 6, 9})         # PDF có thêm 6 bán niên, 9 chín tháng


class BadRecord(ValueError):
    """Bản ghi sai hợp đồng — cùng nhóm với BadShape của fetch, job đếm vào bad_shape."""


@dataclass(frozen=True)
class StatementRow:
    year: int
    length: int
    statement_type: str
    metric_code: str
    value: float


@dataclass(frozen=True)
class ReportRow:
    source_id: int
    year: int | None
    length: int | None
    title: str | None
    url: str


def statement_rows(kind: str, item: dict) -> list[StatementRow]:
    st = STATEMENT[kind]
    out: list[StatementRow] = []
    seen: set[tuple[int, int]] = set()
    for rec in (item.get("quarterly") or []) + (item.get("yearly") or []):
        year, length = rec.get("yearReport"), rec.get("quarterReport")
        if not isinstance(year, int) or length not in STATEMENT_LENGTHS:
            raise BadRecord(f"{kind}: quarterReport/yearReport lạ: {year!r}/{length!r}")
        if (year, length) in seen:
            raise BadRecord(f"{kind}: kỳ trùng {year}/{length}")
        seen.add((year, length))
        for k, v in rec.items():
            if k in ("yearReport", "quarterReport") or k in NON_METRIC or v is None:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise BadRecord(f"{kind}: {k} không phải số: {v!r}")
            out.append(StatementRow(year, length, st, k.lower(), float(v)))
    return out


def report_rows(item: dict) -> list[ReportRow]:
    out: list[ReportRow] = []
    for it in item.get("items") or []:
        sid, u, length = it.get("id"), it.get("sourceUrl"), it.get("lengthReport")
        if not isinstance(sid, int) or not u:
            raise BadRecord(f"reports: thiếu id hoặc sourceUrl: {it!r}"[:200])
        if length is not None and length not in REPORT_LENGTHS:
            raise BadRecord(f"reports: lengthReport lạ {length!r} (id {sid})")
        out.append(ReportRow(sid, it.get("yearReport"), length, it.get("title"), u))
    return out


def rows(kind: str, item: dict) -> list:
    return report_rows(item) if kind == "reports" else statement_rows(kind, item)


def payload_hash(rows_: list) -> str:
    parts = sorted(json.dumps(dataclasses.astuple(r), separators=(",", ":"), ensure_ascii=False)
                   for r in rows_)
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


EMPTY_HASH = payload_hash([])
```

- [ ] **Step 4: Chạy test, phải xanh** — Expected: `7 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/etl/fundamentals_normalize.py backend/tests/etl/test_e32_fundamentals_normalize.py
git commit -m "feat(etl): fundamentals_normalize - long-form rows without nulls, lower-cased codes, order-free hash"
```

---

### Task 4: `fundamentals_guard`

**Files:**
- Create: `backend/etl/fundamentals_guard.py`
- Create: `backend/tests/etl/test_e33_fundamentals_guard.py`

**Interfaces:**
- Produces: `Tally(attempted, failed, bad_shape, empty, checked, first, floor_compared, changed_floor, changed_event, unchanged)` · `Verdict(ok, reasons)` · `check(t) -> Verdict` · `MIN_SAMPLE = 20`.

- [ ] **Step 1: Viết test đỏ**

```python
# backend/tests/etl/test_e33_fundamentals_guard.py
from etl import fundamentals_guard as fg


def test_a_normal_run_passes():
    t = fg.Tally(attempted=80, checked=80, first=10, floor_compared=70, changed_floor=5, unchanged=65)
    assert fg.check(t).ok


def test_first_checks_do_not_count_as_changes():
    """Cold start: mọi mã đều 'first' — hệ thống chạy bình thường không được tự phạm luật (§4.4.4)."""
    t = fg.Tally(attempted=80, checked=80, first=80)
    assert fg.check(t).ok


def test_floor_change_rate_above_twenty_percent_refuses():
    t = fg.Tally(attempted=80, checked=80, floor_compared=80, changed_floor=17, unchanged=63)
    v = fg.check(t)
    assert not v.ok and "quét sàn" in v.reasons[0] and "21.2%" in v.reasons[0]


def test_floor_change_rate_needs_a_minimum_sample():
    t = fg.Tally(attempted=12, checked=12, floor_compared=12, changed_floor=12)     # lượt --codes 3 mã
    assert fg.check(t).ok


def test_failed_bad_shape_and_empty_each_have_their_own_gate():
    assert not fg.check(fg.Tally(attempted=40, failed=9)).ok            # 22.5 % > 20 %
    assert fg.check(fg.Tally(attempted=40, failed=8)).ok                # 20 % không vượt
    assert not fg.check(fg.Tally(attempted=40, bad_shape=3)).ok         # 7.5 % > 5 %
    assert not fg.check(fg.Tally(attempted=40, empty=3)).ok             # rỗng trên mã từng có dữ liệu
    assert fg.check(fg.Tally(attempted=40, empty=2)).ok
    v = fg.check(fg.Tally(attempted=40, failed=9, bad_shape=3, empty=3))
    assert len(v.reasons) == 3


def test_an_empty_due_list_is_a_success():
    assert fg.check(fg.Tally()).ok
```

- [ ] **Step 2: Chạy test, phải đỏ** — `uv run pytest tests/etl/test_e33_fundamentals_guard.py -q -p no:cacheprovider`.

- [ ] **Step 3: Viết module**

```python
# backend/etl/fundamentals_guard.py
"""Năm chốt chặn của một lượt `etl fundamentals` (spec §5.5). Thuần, đánh giá TRƯỚC commit.

Khác lát 4 ở chốt (iv): payload RỖNG trên mã từng có dữ liệu. Rỗng không bao giờ được xoá dữ liệu
cũ (apply bỏ qua và không tiến sổ kiểm), nhưng rỗng hàng loạt là nguồn hỏng — dừng lượt.
"""
from __future__ import annotations

from dataclasses import dataclass, field

MIN_SAMPLE = 20
MAX_FLOOR_CHANGED = 0.20
MAX_FAILED = 0.20
MAX_BAD_SHAPE = 0.05
MAX_EMPTY = 0.05


@dataclass
class Tally:
    attempted: int = 0          # số (mã × kind) định gọi trong lượt
    failed: int = 0             # hỏng sau mọi lần thử ⇒ CHƯA KIỂM
    bad_shape: int = 0          # sai hình dạng (fetch) hoặc sai hợp đồng bản ghi (normalize)
    empty: int = 0              # rỗng trên mã từng có dữ liệu ⇒ CHƯA KIỂM, không xoá gì
    checked: int = 0            # số bản ghi apply() đã ghi sổ kiểm
    first: int = 0              # lần kiểm đầu của (mã, kind)
    floor_compared: int = 0     # mã quét sàn CÓ hash cũ để so
    changed_floor: int = 0      # trong số đó, nội dung đổi — LỖ của lịch sự kiện
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
                           f" ({t.changed_floor}/{t.floor_compared}) — nguồn đổi cách tính,"
                           f" hoặc mùa báo cáo mà lịch sự kiện sót (đọc README trước khi nới)")
    if t.attempted >= MIN_SAMPLE:
        for n, cap, label in ((t.failed, MAX_FAILED, "lời gọi hỏng"),
                              (t.bad_shape, MAX_BAD_SHAPE, "sai hình dạng"),
                              (t.empty, MAX_EMPTY, "rỗng trên mã từng có dữ liệu")):
            rate = n / t.attempted
            if rate > cap:
                reasons.append(f"tỷ lệ {label} {rate:.1%} > {cap:.0%} ({n}/{t.attempted}) — nguồn đang sự cố")
    return Verdict(ok=not reasons, reasons=reasons)
```

- [ ] **Step 4: Chạy test, phải xanh** — Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/etl/fundamentals_guard.py backend/tests/etl/test_e33_fundamentals_guard.py
git commit -m "feat(etl): fundamentals_guard - four rate gates with a minimum sample, empties never delete"
```

---

### Task 5: `fundamentals_store` — danh sách tới hạn, từ điển, apply

**Files:**
- Create: `backend/etl/fundamentals_store.py`
- Create: `backend/tests/etl/test_e34_fundamentals_store.py`

**Interfaces:**
- Consumes: `Target`, `KINDS` (Task 2); `rows`, `payload_hash`, `EMPTY_HASH`, `StatementRow`, `ReportRow`, `STATEMENT` (Task 3); `Tally`, `Verdict` (Task 4).
- Produces: `JOB = DOMAIN = "market.fundamentals"`, `SOURCE = "fiintrade"` · `CADENCE_DAYS = 90`, `QUOTA = 20`, `MAX_TRIGGER = 300`, `COLD_START` · `load_watermark(conn) -> date` · `new_watermark(conn) -> date` · `due_list(conn, watermark, kinds=None, codes=None, backfill=False, quota=QUOTA, cadence=CADENCE_DAYS, max_trigger=MAX_TRIGGER) -> list[Target]` · `Fetched(target, text, rows)` · `apply(conn, fetched, run_id) -> tuple[Tally, int]` · `remaining(conn, kinds=None) -> int` · `load_dictionary(conn) -> int` · `upsert_domain_state(engine, watermark)` · `store_refusal_evidence(engine, fetched, run_id, verdict)`.

- [ ] **Step 1: Viết test đỏ**

```python
# backend/tests/etl/test_e34_fundamentals_store.py
import json
import pathlib
from datetime import date

import sqlalchemy as sa

from etl import fundamentals_normalize as fn
from etl import fundamentals_store as fs
from etl.fundamentals_fetch import Target

FIX = pathlib.Path(__file__).parent / "fixtures" / "fundamentals"


def _issuer(db, name, organ, ticker, com_type="CT", listed=True):
    iid = db.execute(sa.text("INSERT INTO market.issuer (name, com_type_code) VALUES (:n, :c) RETURNING issuer_id"),
                     {"n": name, "c": com_type}).scalar_one()
    db.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                       " VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": organ})
    db.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id, status)"
                       " VALUES (:t, 'HOSE', 'stock', :i, :s)"),
               {"t": ticker, "i": iid, "s": "listed" if listed else "delisted"})
    return iid


def _checked(db, iid, kind, days_ago, h="h0"):
    db.execute(sa.text(
        "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
        " VALUES (:i, :k, now() - make_interval(days => :d), :h, 'floor')"),
        {"i": iid, "k": kind, "d": days_ago, "h": h})


def _earning(db, iid, public_date):
    db.execute(sa.text(
        "INSERT INTO market.corporate_event (event_type, issuer_id, public_date, year_report, length_report, payload)"
        " VALUES ('Earning', :i, :p, 2026, 2, '{}'::jsonb)"), {"i": iid, "p": public_date})


def _quiet(db):
    """Dập nền CSDL dùng chung: coi mọi issuer đang có như vừa kiểm xong, và dọn corporate_event
    thật của bộ test khác (nhánh trigger và new_watermark đọc TOÀN CỤC). Rollback cuối test."""
    for kind in fs.KINDS:
        db.execute(sa.text(
            "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
            " SELECT i.issuer_id, :k, clock_timestamp(), 'nen', 'floor' FROM market.issuer i"
            " ON CONFLICT (issuer_id, kind) DO UPDATE SET checked_at = clock_timestamp()"), {"k": kind})
    db.execute(sa.text("DELETE FROM market.corporate_event"))


def _mine(due, *organs):
    return [t for t in due if t.organ_code in organs]


def _item(name):
    d = json.loads((FIX / name).read_text(encoding="utf-8"))
    return {"items": d["items"]} if name.endswith("reports.json") else d["items"][0]


def _fetched(iid, kind, name, found_by="floor", item=None):
    item = item if item is not None else _item(name)
    t = Target(kind=kind, issuer_id=iid, organ_code="ASECO32", ticker="A32", found_by=found_by)
    return fs.Fetched(target=t, text=json.dumps({"items": [item]} if kind != "reports" else item),
                      rows=fn.rows(kind, item))


# ---------- due_list ----------

def test_due_list_floor_takes_never_checked_first_then_the_oldest_within_quota(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    b = _issuer(db, "B", "ZZB", "ZZB")
    c = _issuer(db, "C", "ZZC", "ZZC")
    _checked(db, b, "bs", 100)                  # quá nhịp 90 ⇒ tới hạn
    _checked(db, c, "bs", 10)                   # còn trong nhịp ⇒ không
    due = _mine(fs.due_list(db, fs.COLD_START, kinds=["bs"], quota=2), "ZZA", "ZZB", "ZZC")
    assert [t.organ_code for t in due] == ["ZZA", "ZZB"]
    assert all(t.found_by == "floor" and t.kind == "bs" for t in due)
    assert _mine(fs.due_list(db, fs.COLD_START, kinds=["bs"], quota=1), "ZZA", "ZZB", "ZZC")[0].organ_code == "ZZA"


def test_due_list_trigger_fires_all_four_kinds_for_an_earning_after_the_watermark(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    b = _issuer(db, "B", "ZZB", "ZZB")
    for iid in (a, b):
        for k in fs.KINDS:
            _checked(db, iid, k, 1)             # cả hai vừa quét sàn ⇒ chỉ trigger mới đưa vào
    _earning(db, a, date(2026, 9, 3))
    _earning(db, b, date(2026, 8, 1))
    due = _mine(fs.due_list(db, date(2026, 8, 15)), "ZZA", "ZZB")
    assert {(t.organ_code, t.kind, t.found_by) for t in due} == {("ZZA", k, "event") for k in fs.KINDS}


def test_due_list_skips_the_trigger_branch_on_cold_start(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    for k in fs.KINDS:
        _checked(db, a, k, 1)
    _earning(db, a, date(2026, 9, 3))
    assert _mine(fs.due_list(db, fs.COLD_START), "ZZA") == []


def test_due_list_caps_the_trigger_branch_oldest_first(db):
    _quiet(db)
    ids = [_issuer(db, f"T{i}", f"ZZT{i}", f"ZT{i}") for i in range(3)]
    for i, iid in enumerate(ids):
        for k in fs.KINDS:
            _checked(db, iid, k, 1)
        _earning(db, iid, date(2026, 9, 1 + i))
    due = _mine(fs.due_list(db, date(2026, 8, 1), kinds=["bs"], max_trigger=2), "ZZT0", "ZZT1", "ZZT2")
    assert [t.organ_code for t in due] == ["ZZT0", "ZZT1"]


def test_due_list_merges_trigger_and_floor_into_one_target_per_issuer_and_kind(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")          # chưa kiểm ⇒ floor; có Earning ⇒ trigger
    _earning(db, a, date(2026, 9, 3))
    due = _mine(fs.due_list(db, date(2026, 8, 1), kinds=["cf"]), "ZZA")
    assert len(due) == 1 and due[0].found_by == "event"


def test_due_list_backfill_ignores_the_quota_but_only_takes_never_checked(db):
    _quiet(db)
    ids = [_issuer(db, f"B{i}", f"ZZB{i}", f"ZB{i}") for i in range(5)]
    _checked(db, ids[0], "is", 200)             # quá nhịp nhưng ĐÃ từng kiểm ⇒ backfill bỏ qua
    due = _mine(fs.due_list(db, fs.COLD_START, kinds=["is"], backfill=True, quota=1),
                *[f"ZZB{i}" for i in range(5)])
    assert [t.organ_code for t in due] == ["ZZB1", "ZZB2", "ZZB3", "ZZB4"]


def test_due_list_codes_forces_every_kind_and_ignores_cadence(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    for k in fs.KINDS:
        _checked(db, a, k, 1)
    due = fs.due_list(db, fs.COLD_START, codes=["ZZA"])
    assert {t.kind for t in due} == set(fs.KINDS) and all(t.found_by == "floor" for t in due)


def test_due_list_leaves_out_an_issuer_without_a_listed_stock(db):
    _quiet(db)
    _issuer(db, "D", "ZZD", "ZZD", listed=False)
    assert _mine(fs.due_list(db, fs.COLD_START, backfill=True), "ZZD") == []


def test_new_watermark_is_the_latest_earning_public_date(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    _earning(db, a, date(2026, 9, 3))
    db.execute(sa.text("INSERT INTO market.corporate_event (event_type, issuer_id, public_date, exright_date, payload)"
                       " VALUES ('CashDividend', :i, '2026-09-04', '2026-09-30', '{}'::jsonb)"), {"i": a})
    assert fs.new_watermark(db) == date(2026, 9, 3)      # chỉ Earning, chỉ public_date


# ---------- load_dictionary ----------

def test_load_dictionary_upserts_729_codes_with_data_units(db):
    n = fs.load_dictionary(db)
    assert n == 729 and fs.load_dictionary(db) == 729
    got = db.execute(sa.text("SELECT name_vi, unit FROM market.metric_dictionary"
                             " WHERE dictionary = 'field_dictionary' AND code = 'bsa1'")).one()
    assert got.name_vi == "TÀI SẢN NGẮN HẠN" and got.unit == "VND"
    r = db.execute(sa.text("SELECT unit, value_min, value_max FROM market.metric_dictionary"
                           " WHERE dictionary = 'field_dictionary' AND code = 'rtq29'")).one()
    assert r.unit == "ty_le_thap_phan" and float(r.value_min) == -524.47799765 and float(r.value_max) == 756.70410797
    total = db.execute(sa.text("SELECT count(*) FROM market.metric_dictionary WHERE dictionary = 'field_dictionary'")).scalar_one()
    assert total == 729


# ---------- apply ----------

def _count(db, iid, st=None):
    q = "SELECT count(*) FROM market.financial_statement WHERE issuer_id = :i" + (" AND statement_type = :s" if st else "")
    return db.execute(sa.text(q), {"i": iid, "s": st}).scalar_one()


def test_apply_first_check_writes_every_row_and_one_raw_payload(db):
    a = _issuer(db, "A", "ASECO32", "A32")
    tally, written = fs.apply(db, [_fetched(a, "bs", "A32-bs.json"), _fetched(a, "reports", "A32-reports.json")], run_id=1)
    assert tally.first == 2 and tally.checked == 2 and written == 1749 + 8
    assert _count(db, a, "BS") == 1749
    v = db.execute(sa.text("SELECT value FROM market.financial_statement WHERE issuer_id = :i AND year_report = 2025"
                           " AND length_report = 5 AND statement_type = 'BS' AND metric_code = 'bsa1'"), {"i": a}).scalar_one()
    assert float(v) == 365335639678.0
    assert db.execute(sa.text("SELECT count(*) FROM market.financial_report_file WHERE issuer_id = :i"), {"i": a}).scalar_one() == 8
    raw = db.execute(sa.text("SELECT endpoint_key, meta FROM staging.raw_payload WHERE source = 'fundamentals'"
                             " AND endpoint_key LIKE '%ASECO32' ORDER BY payload_id")).all()
    assert [r.endpoint_key for r in raw] == ["fundamentals:bs:ASECO32", "fundamentals:reports:ASECO32"]
    assert raw[0].meta["rows"] == 1749 and raw[0].meta["run_id"] == 1


def test_apply_unchanged_writes_nothing_but_advances_checked_at(db):
    a = _issuer(db, "A", "ASECO32", "A32")
    fs.apply(db, [_fetched(a, "bs", "A32-bs.json")], run_id=1)
    t0 = db.execute(sa.text("SELECT checked_at FROM ops.fundamentals_check WHERE issuer_id = :i AND kind = 'bs'"), {"i": a}).scalar_one()
    tally, written = fs.apply(db, [_fetched(a, "bs", "A32-bs.json")], run_id=2)
    t1 = db.execute(sa.text("SELECT checked_at FROM ops.fundamentals_check WHERE issuer_id = :i AND kind = 'bs'"), {"i": a}).scalar_one()
    assert tally.unchanged == 1 and tally.floor_compared == 1 and tally.changed_floor == 0 and written == 0
    assert t1 > t0 and _count(db, a, "BS") == 1749
    assert db.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source = 'fundamentals'"
                              " AND endpoint_key = 'fundamentals:bs:ASECO32'")).scalar_one() == 1


def test_apply_a_restated_value_changes_exactly_one_row_and_keeps_the_count(db):
    a = _issuer(db, "A", "ASECO32", "A32")
    fs.apply(db, [_fetched(a, "bs", "A32-bs.json")], run_id=1)
    item = _item("A32-bs.json")
    item["yearly"] = [dict(item["yearly"][0], bsa1=1.0)] + item["yearly"][1:]        # yearly[0] là 2025
    tally, written = fs.apply(db, [_fetched(a, "bs", "A32-bs.json", found_by="event", item=item)], run_id=2)
    assert tally.changed_event == 1 and written == 1749 and _count(db, a, "BS") == 1749
    v = db.execute(sa.text("SELECT value FROM market.financial_statement WHERE issuer_id = :i AND year_report = 2025"
                           " AND length_report = 5 AND statement_type = 'BS' AND metric_code = 'bsa1'"), {"i": a}).scalar_one()
    assert float(v) == 1.0
    assert db.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source = 'fundamentals'"
                              " AND endpoint_key = 'fundamentals:bs:ASECO32'")).scalar_one() == 2


def test_apply_a_vanished_cell_removes_its_row(db):
    a = _issuer(db, "A", "ASECO32", "A32")
    fs.apply(db, [_fetched(a, "bs", "A32-bs.json")], run_id=1)
    item = _item("A32-bs.json")
    item["yearly"] = [dict(item["yearly"][0], bsa23=None)] + item["yearly"][1:]
    tally, _ = fs.apply(db, [_fetched(a, "bs", "A32-bs.json", item=item)], run_id=2)
    assert tally.changed_floor == 1 and _count(db, a, "BS") == 1748


def test_apply_an_empty_payload_on_a_known_issuer_deletes_nothing_and_does_not_count_as_checked(db):
    a = _issuer(db, "A", "ASECO32", "A32")
    fs.apply(db, [_fetched(a, "is", "A32-is.json")], run_id=1)
    t0 = db.execute(sa.text("SELECT checked_at FROM ops.fundamentals_check WHERE issuer_id = :i AND kind = 'is'"), {"i": a}).scalar_one()
    tally, written = fs.apply(db, [_fetched(a, "is", "A32-is.json", item={"quarterly": [], "yearly": []})], run_id=2)
    t1 = db.execute(sa.text("SELECT checked_at FROM ops.fundamentals_check WHERE issuer_id = :i AND kind = 'is'"), {"i": a}).scalar_one()
    assert tally.empty == 1 and tally.checked == 0 and written == 0
    assert _count(db, a, "IS") == 980 and t1 == t0


def test_apply_an_empty_payload_on_a_new_issuer_is_a_normal_first_check(db):
    """Mã UPCOM chưa có báo cáo: rỗng là trạng thái thật, ghi sổ kiểm để quét sàn không gọi lại mỗi ngày."""
    a = _issuer(db, "A", "ASECO32", "A32")
    tally, _ = fs.apply(db, [_fetched(a, "cf", "A32-cf.json", item={"quarterly": [], "yearly": []})], run_id=1)
    assert tally.first == 1 and tally.empty == 0
    tally, _ = fs.apply(db, [_fetched(a, "cf", "A32-cf.json", item={"quarterly": [], "yearly": []})], run_id=2)
    assert tally.unchanged == 1 and tally.empty == 0                 # rỗng → rỗng là 'không đổi', không phải 'rỗng'


def test_apply_reports_upserts_by_source_id_and_never_deletes(db):
    a = _issuer(db, "A", "ASECO32", "A32")
    fs.apply(db, [_fetched(a, "reports", "A32-reports.json")], run_id=1)
    item = _item("A32-reports.json")
    item["items"] = [dict(item["items"][0], title="BCTC đã kiểm toán năm 2025 (bản sửa)")] + item["items"][2:]   # đổi 1, bỏ 1
    tally, _ = fs.apply(db, [_fetched(a, "reports", "A32-reports.json", item=item)], run_id=2)
    assert tally.changed_floor == 1
    rows = db.execute(sa.text("SELECT source_id, title FROM market.financial_report_file WHERE issuer_id = :i ORDER BY source_id"), {"i": a}).all()
    assert len(rows) == 8 and [r.title for r in rows if r.source_id == 9412069] == ["BCTC đã kiểm toán năm 2025 (bản sửa)"]


def test_remaining_counts_issuer_kinds_never_checked(db):
    _quiet(db)
    a = _issuer(db, "A", "ZZA", "ZZA")
    b = _issuer(db, "B", "ZZB", "ZZB")
    before = fs.remaining(db)
    _checked(db, a, "bs", 0)
    assert fs.remaining(db) == before - 1
    fs.apply(db, [_fetched(b, "cf", "A32-cf.json")], run_id=1)
    assert fs.remaining(db) == before - 2
```

- [ ] **Step 2: Chạy test, phải đỏ** — `uv run pytest tests/etl/test_e34_fundamentals_store.py -q -p no:cacheprovider`.

- [ ] **Step 3: Viết module**

```python
# backend/etl/fundamentals_store.py
"""Danh sách tới hạn, từ điển và ghi kết quả BCTC (spec §5.4). SQL thuần.

Không có con trỏ: `ops.fundamentals_check.checked_at` CHÍNH LÀ con trỏ — kể cả ở chế độ
--backfill (lấy mọi dòng chưa kiểm, ORDER BY issuer_id), nên lượt bị giết giữa chừng không mất chỗ.

Khi nội dung đổi: XOÁ trọn (issuer, statement_type) rồi CHÈN lại trong cùng giao dịch — một luật,
điều chỉnh hồi tố / ô biến mất / ô đổi giá trị đều tự đúng (spec §4.4). Lịch sử đổi nằm ở
staging.raw_payload, một dòng mỗi lần đổi.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import sqlalchemy as sa

from etl.fundamentals_fetch import KINDS, Target
from etl.fundamentals_guard import Tally, Verdict
from etl.fundamentals_normalize import EMPTY_HASH, STATEMENT, ReportRow, StatementRow, payload_hash

log = logging.getLogger("etl.fundamentals")

JOB = "market.fundamentals"
DOMAIN = "market.fundamentals"
SOURCE = "fiintrade"

MAX_EVIDENCE = 20
MAX_TRIGGER = 300                                  # trần nhánh trigger/lượt — xem due_list()
COLD_START = dt.date(1900, 1, 1)
CADENCE_DAYS = 90
QUOTA = 20                                         # mã/kind/ngày ⇒ 80 lời gọi/ngày, phủ 1.523 mã sau 77 ngày
INSERT_CHUNK = 5000

DICTIONARY_JSON = Path(__file__).resolve().parents[2] / "docs" / "10-sources" / "market" / "field-dictionary.json"
DICTIONARY_GROUPS = ("chi_tieu_bao_cao_tai_chinh", "chi_tieu_ty_so_va_thi_truong")

# Vũ trụ: issuer có ÍT NHẤT một cổ phiếu đang niêm yết — nguyên văn snapshot_store._UNIVERSE.
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
        "SELECT watermark FROM ops.data_domain_state WHERE domain = :d AND source = :s"),
        {"d": DOMAIN, "s": SOURCE}).scalar()
    return dt.date.fromisoformat(got) if got else COLD_START


def new_watermark(conn) -> dt.date:
    """Mốc 'sự kiện MỚI CÔNG BỐ' — CHỈ `public_date` của `Earning`. Không trộn `exright_date`
    (bài học mốc nước tương lai của lát 4)."""
    got = conn.execute(sa.text(
        "SELECT max(public_date) FROM market.corporate_event WHERE event_type = 'Earning'")).scalar()
    return got or COLD_START


def _target(row, kind: str, found_by: str) -> Target:
    return Target(kind=kind, issuer_id=row.issuer_id, organ_code=row.organ_code,
                  ticker=row.ticker, found_by=found_by)


def due_list(conn, watermark: dt.date, kinds=None, codes=None, backfill: bool = False,
             quota: int = QUOTA, cadence: int = CADENCE_DAYS, max_trigger: int = MAX_TRIGGER) -> list[Target]:
    kinds = list(kinds or KINDS)
    if codes:                                       # lượt ép: mọi kind, bỏ nhịp và quota
        rows = conn.execute(sa.text(
            _UNIVERSE + "SELECT * FROM uni WHERE ticker = ANY(:codes) ORDER BY ticker"),
            {"codes": list(codes)}).all()
        return [_target(r, k, "floor") for r in rows for k in kinds]

    out: list[Target] = []
    seen: set[tuple[int, str]] = set()

    if watermark == COLD_START:
        log.info("bỏ qua nhánh trigger: mốc nước còn ở mốc khởi tạo (cold start) — quét sàn/backfill tự phủ")
    else:
        rows = conn.execute(sa.text(
            _UNIVERSE + """
            SELECT u.issuer_id, u.organ_code, u.com_type_code, u.ticker, min(e.public_date) AS public_date
            FROM uni u
            JOIN market.corporate_event e ON e.issuer_id = u.issuer_id
            WHERE e.event_type = 'Earning' AND e.public_date > :wm
            GROUP BY u.issuer_id, u.organ_code, u.com_type_code, u.ticker
            ORDER BY min(e.public_date) ASC, u.issuer_id
            LIMIT :limit
            """), {"wm": watermark, "limit": max_trigger + 1}).all()
        if len(rows) > max_trigger:
            log.info("nhánh trigger vượt trần %d: cắt %d issuer, giữ cũ nhất theo public_date",
                     max_trigger, len(rows) - max_trigger)
            rows = rows[:max_trigger]
        for r in rows:
            for kind in kinds:
                if (r.issuer_id, kind) not in seen:
                    seen.add((r.issuer_id, kind))
                    out.append(_target(r, kind, "event"))

    for kind in kinds:
        if backfill:
            sql = (_UNIVERSE + """
                SELECT u.* FROM uni u
                LEFT JOIN ops.fundamentals_check c ON c.issuer_id = u.issuer_id AND c.kind = :kind
                WHERE c.checked_at IS NULL
                ORDER BY u.issuer_id
                """)
            params = {"kind": kind}
        else:
            sql = (_UNIVERSE + """
                SELECT u.* FROM uni u
                LEFT JOIN ops.fundamentals_check c ON c.issuer_id = u.issuer_id AND c.kind = :kind
                WHERE c.checked_at IS NULL
                   OR c.checked_at < now() - make_interval(days => :cadence)
                ORDER BY c.checked_at NULLS FIRST, u.issuer_id
                LIMIT :quota
                """)
            params = {"kind": kind, "cadence": cadence, "quota": quota}
        for r in conn.execute(sa.text(sql), params).all():
            if (r.issuer_id, kind) not in seen:
                seen.add((r.issuer_id, kind))
                out.append(_target(r, kind, "floor"))
    return out


def remaining(conn, kinds=None) -> int:
    """Số (issuer, kind) chưa từng kiểm — tiến độ của lượt điền đầu."""
    kinds = list(kinds or KINDS)
    return conn.execute(sa.text(
        _UNIVERSE + """
        SELECT count(*) FROM uni u
        CROSS JOIN unnest(cast(:kinds AS text[])) AS k(kind)
        LEFT JOIN ops.fundamentals_check c ON c.issuer_id = u.issuer_id AND c.kind = k.kind
        WHERE c.checked_at IS NULL
        """), {"kinds": kinds}).scalar_one()


def load_dictionary(conn) -> int:
    """Upsert 729 mã từ file trong repo — hợp đồng khởi động: file hỏng thì raise TRƯỚC khi fetch."""
    data = json.loads(DICTIONARY_JSON.read_text(encoding="utf-8"))
    rows = []
    for group in DICTIONARY_GROUPS:
        entries = data.get(group)
        if not isinstance(entries, dict) or not entries:
            raise RuntimeError(f"từ điển thiếu nhóm {group!r}: {DICTIONARY_JSON}")
        for code, e in entries.items():
            rng = e.get("dai_gia_tri") or [None, None]
            rows.append({"code": code.lower(), "vi": e.get("ten_vi"), "en": e.get("ten_en"),
                         "unit": e.get("don_vi_du_lieu"), "lo": rng[0], "hi": rng[1]})
    conn.execute(sa.text(
        "INSERT INTO market.metric_dictionary (dictionary, code, name_vi, name_en, unit, value_min, value_max)"
        " VALUES ('field_dictionary', :code, :vi, :en, :unit, :lo, :hi)"
        " ON CONFLICT (dictionary, code) DO UPDATE SET name_vi = excluded.name_vi, name_en = excluded.name_en,"
        " unit = excluded.unit, value_min = excluded.value_min, value_max = excluded.value_max"), rows)
    return len(rows)


@dataclass
class Fetched:
    target: Target
    text: str
    rows: list                                     # StatementRow | ReportRow, đã chuẩn hoá


def _write_statement(conn, iid: int, st: str, rows: list[StatementRow]) -> None:
    conn.execute(sa.text(
        "DELETE FROM market.financial_statement WHERE issuer_id = :i AND statement_type = :s"), {"i": iid, "s": st})
    params = [{"i": iid, "y": r.year, "l": r.length, "s": st, "m": r.metric_code, "v": r.value} for r in rows]
    for start in range(0, len(params), INSERT_CHUNK):
        conn.execute(sa.text(
            "INSERT INTO market.financial_statement (issuer_id, year_report, length_report, statement_type, metric_code, value)"
            " VALUES (:i, :y, :l, :s, :m, :v)"), params[start:start + INSERT_CHUNK])


def _write_reports(conn, iid: int, rows: list[ReportRow]) -> None:
    if not rows:
        return
    conn.execute(sa.text(
        "INSERT INTO market.financial_report_file (issuer_id, year_report, length_report, title, source_url, source_id)"
        " VALUES (:i, :y, :l, :t, :u, :sid)"
        " ON CONFLICT (source_id) DO UPDATE SET issuer_id = excluded.issuer_id, year_report = excluded.year_report,"
        " length_report = excluded.length_report, title = excluded.title, source_url = excluded.source_url,"
        " ingested_at = clock_timestamp()"),
        [{"i": iid, "y": r.year, "l": r.length, "t": r.title, "u": r.url, "sid": r.source_id} for r in rows])


def apply(conn, fetched: list[Fetched], run_id: int) -> tuple[Tally, int]:
    """Ghi KHI ĐỔI; mọi lượt kiểm (trừ rỗng-trên-mã-từng-có-dữ-liệu) đều cập nhật sổ kiểm."""
    tally, written = Tally(), 0
    for f in fetched:
        t = f.target
        h = payload_hash(f.rows)
        prev = conn.execute(sa.text(
            "SELECT payload_hash FROM ops.fundamentals_check WHERE issuer_id = :i AND kind = :k"),
            {"i": t.issuer_id, "k": t.kind}).scalar()

        if not f.rows and prev is not None and prev != EMPTY_HASH:
            # Rỗng trên mã từng có dữ liệu: KHÔNG xoá, KHÔNG tiến sổ kiểm — lượt sau thử lại (spec §5.4 bước 2)
            tally.empty += 1
            log.warning("%s/%s: nguồn trả rỗng trên mã từng có dữ liệu — giữ nguyên kho", t.organ_code, t.kind)
            continue

        tally.checked += 1
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
            if t.kind in STATEMENT:
                _write_statement(conn, t.issuer_id, STATEMENT[t.kind], f.rows)
            else:
                _write_reports(conn, t.issuer_id, f.rows)
            written += len(f.rows)
            conn.execute(sa.text(
                "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                " VALUES ('fundamentals', :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
                {"ek": f"fundamentals:{t.kind}:{t.organ_code}", "p": f.text,
                 "m": json.dumps({"hash": h, "run_id": run_id, "rows": len(f.rows)})})

        # clock_timestamp(), KHÔNG now(): now() đứng yên trong một giao dịch (bài học sổ kiểm lát 4)
        conn.execute(sa.text(
            "INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, changed_at, found_by)"
            " VALUES (:i, :k, clock_timestamp(), :h, clock_timestamp(), :f)"
            " ON CONFLICT (issuer_id, kind) DO UPDATE"
            " SET checked_at = clock_timestamp(), payload_hash = :h, found_by = :f,"
            "     changed_at = CASE WHEN :c THEN clock_timestamp() ELSE ops.fundamentals_check.changed_at END"),
            {"i": t.issuer_id, "k": t.kind, "h": h, "f": t.found_by, "c": changed})
    return tally, written


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
            " VALUES (:d, :s, 'active', now(), :w)"
            " ON CONFLICT (domain, source) DO UPDATE"
            " SET last_success_at = now(), watermark = :w, status = 'active'"),
            {"d": DOMAIN, "s": SOURCE, "w": watermark})


def store_refusal_evidence(engine, fetched: list[Fetched], run_id: int, verdict: Verdict) -> None:
    """Bằng chứng ở giao dịch RIÊNG — lượt chính đã rollback. Ưu tiên nhóm quét sàn."""
    picked = [f for f in fetched if f.target.found_by == "floor"][:MAX_EVIDENCE] or fetched[:MAX_EVIDENCE]
    meta = json.dumps({"run_id": run_id, "reasons": verdict.reasons}, ensure_ascii=False)
    with engine.begin() as conn:
        for f in picked:
            conn.execute(sa.text(
                "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                " VALUES ('fundamentals', :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
                {"ek": f"fundamentals:{f.target.kind}:{f.target.organ_code}", "p": f.text, "m": meta})
```

- [ ] **Step 4: Chạy test, phải xanh** — Expected: `18 passed`. Nếu `test_load_dictionary...` đỏ ở `name_vi`, kiểm `PYTHONIOENCODING=utf-8` đã đặt.

- [ ] **Step 5: Commit**

```bash
git add backend/etl/fundamentals_store.py backend/tests/etl/test_e34_fundamentals_store.py
git commit -m "feat(etl): fundamentals_store - due list with backfill mode, delete-and-insert on change, dictionary upsert"
```

---

### Task 6: `fundamentals_job` và subcommand

**Files:**
- Create: `backend/etl/fundamentals_job.py`
- Modify: `backend/etl/__main__.py` (thêm nhánh `fundamentals` trước dòng `print(f"etl: subcommand không hợp lệ…`, và thêm `fundamentals` vào chuỗi "hỗ trợ: …")
- Create: `backend/tests/etl/test_e35_fundamentals_job.py`

**Interfaces:**
- Consumes: mọi thứ của Task 2–5; `omo_store.open_run/close_run`; `price_job._next_open`, `price_job.VN`.
- Produces: `run(codes=None, kinds=None, max_minutes=None, backfill=False, stop_before_open=False, get=None, sleep=time.sleep) -> int`; `stats` gồm `tally`, `rows_written`, `calls`, `retries`, `stopped_early`, `run_date`, `dictionary_rows`, `remaining`, `watermark`/`watermark_held`, `subset`, `backfill`, `stop_at`.

- [ ] **Step 1: Viết test đỏ**

```python
# backend/tests/etl/test_e35_fundamentals_job.py
import json
import os
import pathlib
from datetime import date

import pytest
import sqlalchemy as sa

from etl import fundamentals_job as fj
from etl import fundamentals_store as fs

FIX = pathlib.Path(__file__).parent / "fixtures" / "fundamentals"
ORGAN, TICKER = "ZZFUND", "ZZF"
BATCH = [f"ZZFB{i:02d}" for i in range(20)]        # guard MIN_SAMPLE = 20
ALL_ORGANS = [ORGAN] + BATCH


def _payload(kind):
    return (FIX / f"A32-{kind}.json").read_text(encoding="utf-8")


def _fake_get(calls=None, fail=False):
    def get(u, timeout):
        if calls is not None:
            calls.append(u)
        if fail:
            return 503, ""
        kind = ("bs" if "GetBalanceSheet" in u else "is" if "GetIncomeStatement" in u
                else "cf" if "GetCashFlow" in u else "reports")
        return 200, _payload(kind)
    return get


def _wire(monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.fundamentals_job.load_dotenv", lambda *a, **k: None)


def _cleanup(engine):
    with engine.begin() as c:
        iids = c.execute(sa.text("SELECT issuer_id FROM market.issuer_external_id"
                                 " WHERE source = 'fiintrade' AND external_code = ANY(:o)"), {"o": ALL_ORGANS}).scalars().all()
        if iids:
            for tbl in ("market.financial_statement", "market.financial_report_file", "ops.fundamentals_check",
                        "market.corporate_event", "market.security", "market.issuer_external_id"):
                c.execute(sa.text(f"DELETE FROM {tbl} WHERE issuer_id = ANY(:i)"), {"i": iids})
            c.execute(sa.text("DELETE FROM market.issuer WHERE issuer_id = ANY(:i)"), {"i": iids})
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = :j"), {"j": fs.JOB})
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source = 'fundamentals'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE domain = :d AND source = :s"), {"d": fs.DOMAIN, "s": fs.SOURCE})


def _seed(engine, organ=ORGAN, ticker=TICKER):
    with engine.begin() as c:
        iid = c.execute(sa.text("INSERT INTO market.issuer (name, com_type_code) VALUES ('Job test', 'CT') RETURNING issuer_id")).scalar_one()
        c.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code) VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": organ})
        c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id) VALUES (:t, 'HOSE', 'stock', :i)"), {"t": ticker, "i": iid})
    return iid


def _last_run(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job = :j ORDER BY run_id DESC LIMIT 1"), {"j": fs.JOB}).one()


@pytest.fixture()
def clean(migrated_engine):
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def test_codes_run_writes_four_kinds_and_holds_the_watermark(clean, monkeypatch):
    _wire(monkeypatch)
    iid = _seed(clean)
    calls = []
    assert fj.run(codes=[TICKER], get=_fake_get(calls), sleep=lambda s: None) == 0
    assert len(calls) == 4
    run = _last_run(clean)
    assert run.status == "success"
    assert run.stats["rows_written"] == 1749 + 980 + 916 + 8 and run.stats["subset"] is True
    assert run.stats["dictionary_rows"] == 729 and "watermark" not in run.stats
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM market.financial_statement WHERE issuer_id = :i"), {"i": iid}).scalar_one() == 3645
        assert c.execute(sa.text("SELECT count(*) FROM ops.fundamentals_check WHERE issuer_id = :i"), {"i": iid}).scalar_one() == 4
        assert c.execute(sa.text("SELECT count(*) FROM ops.data_domain_state WHERE domain = :d"), {"d": fs.DOMAIN}).scalar_one() == 0


def test_second_codes_run_is_idempotent(clean, monkeypatch):
    _wire(monkeypatch)
    _seed(clean)
    fj.run(codes=[TICKER], get=_fake_get(), sleep=lambda s: None)
    assert fj.run(codes=[TICKER], get=_fake_get(), sleep=lambda s: None) == 0
    stats = _last_run(clean).stats
    assert stats["tally"]["unchanged"] == 4 and stats["rows_written"] == 0
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source = 'fundamentals'")).scalar_one() == 4


def test_backfill_run_covers_the_batch_and_reports_remaining(clean, monkeypatch):
    """--backfill: mọi (issuer, kind) chưa kiểm, không quota, mốc nước tiến nếu trọn."""
    _wire(monkeypatch)
    for o in BATCH:
        _seed(clean, o, o[-3:] + "X")
    monkeypatch.setattr(fs, "QUOTA", 1)                              # quota 1 mà backfill vẫn lấy hết
    with clean.begin() as c:                                         # dập nền: mã khác trong DB test coi như đã kiểm
        for k in fs.KINDS:
            c.execute(sa.text("INSERT INTO ops.fundamentals_check (issuer_id, kind, checked_at, payload_hash, found_by)"
                              " SELECT issuer_id, :k, now(), 'nen', 'floor' FROM market.issuer"
                              " WHERE issuer_id NOT IN (SELECT issuer_id FROM market.issuer_external_id WHERE external_code = ANY(:o))"
                              " ON CONFLICT DO NOTHING"), {"k": k, "o": BATCH})
    calls = []
    assert fj.run(backfill=True, get=_fake_get(calls), sleep=lambda s: None) == 0
    stats = _last_run(clean).stats
    assert len(calls) == 80 and stats["backfill"] is True and stats["remaining"] == 0
    assert stats["tally"]["first"] == 80 and "watermark" in stats


def test_max_minutes_stops_after_the_current_target_and_holds_the_watermark(clean, monkeypatch):
    _wire(monkeypatch)
    for o in BATCH[:3]:
        _seed(clean, o, o[-3:] + "X")
    clock = iter([0.0, 0.0] + [10_000.0] * 100)     # lần 1: tính hạn; lần 2: kiểm trước target 1 (còn giờ); từ lần 3: hết giờ
    monkeypatch.setattr(fj, "_wall_clock", lambda: next(clock))
    calls = []
    assert fj.run(codes=[o[-3:] + "X" for o in BATCH[:3]], max_minutes=1, get=_fake_get(calls), sleep=lambda s: None) == 0
    stats = _last_run(clean).stats
    assert stats["stopped_early"] is True and 1 <= len(calls) < 12


def test_an_outage_refuses_the_run_and_leaves_evidence(clean, monkeypatch):
    _wire(monkeypatch)
    for o in BATCH:
        _seed(clean, o, o[-3:] + "X")
    assert fj.run(codes=[o[-3:] + "X" for o in BATCH], kinds=["bs"], get=_fake_get(fail=True), sleep=lambda s: None) == 1
    run = _last_run(clean)
    assert run.status == "failed" and "hỏng" in run.error
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM market.financial_statement WHERE issuer_id IN"
                                 " (SELECT issuer_id FROM market.issuer_external_id WHERE external_code = ANY(:o))"), {"o": BATCH}).scalar_one() == 0
        assert c.execute(sa.text("SELECT count(*) FROM ops.fundamentals_check WHERE issuer_id IN"
                                 " (SELECT issuer_id FROM market.issuer_external_id WHERE external_code = ANY(:o))"), {"o": BATCH}).scalar_one() == 0


def test_a_broken_dictionary_file_fails_before_any_call(clean, monkeypatch, tmp_path):
    _wire(monkeypatch)
    _seed(clean)
    bad = tmp_path / "fd.json"
    bad.write_text('{"_meta": {}}', encoding="utf-8")
    monkeypatch.setattr(fs, "DICTIONARY_JSON", bad)
    calls = []
    assert fj.run(codes=[TICKER], get=_fake_get(calls), sleep=lambda s: None) == 2
    assert calls == [] and _last_run(clean).status == "failed"


def test_main_parses_the_fundamentals_flags(monkeypatch):
    import etl.__main__ as m
    seen = {}
    monkeypatch.setattr("etl.fundamentals_job.run", lambda **kw: seen.update(kw) or 0)
    assert m.main(["fundamentals", "--codes", "a32,bab", "--kinds", "bs,cf", "--backfill",
                   "--max-minutes", "30", "--stop-before-open"]) == 0
    assert seen == {"codes": ["A32", "BAB"], "kinds": ["bs", "cf"], "backfill": True,
                    "max_minutes": 30.0, "stop_before_open": True}
```

Ghi chú cho người thực thi: `main(argv: list[str] | None = None)` đã nhận list (đọc `backend/etl/__main__.py`), nên gọi `m.main([...])` là đúng. Đừng đổi chữ ký `main`.

- [ ] **Step 2: Chạy test, phải đỏ** — `uv run pytest tests/etl/test_e35_fundamentals_job.py -q -p no:cacheprovider`.

- [ ] **Step 3: Viết job và nối subcommand**

```python
# backend/etl/fundamentals_job.py
"""Một lượt chạy fundamentals: từ điển → due_list → fetch+normalize → guard → apply (spec §5.1).

Y khuôn `snapshot_job.run`: MỘT giao dịch cho dữ liệu, guard đánh giá TRƯỚC commit — từ chối thì
raise bên trong `engine.begin()` để tự rollback; bằng chứng ghi ở giao dịch riêng. Không re-crawl.
Hạn theo đồng hồ TƯỜNG như `price_job._backfill`: máy ngủ 02:00 rồi thức dậy là hết ngân sách.
"""
from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime

import sqlalchemy as sa

from core.env import load_dotenv
from etl import fundamentals_fetch, fundamentals_guard, fundamentals_normalize, fundamentals_store, omo_store
from etl.fundamentals_fetch import BadShape, FetchError
from etl.fundamentals_normalize import BadRecord
from etl.price_job import VN, _next_open

log = logging.getLogger("etl.fundamentals")
JOB = fundamentals_store.JOB
_wall_clock = time.time                  # seam cho test


class GuardRefused(Exception):
    def __init__(self, verdict):
        self.verdict = verdict
        super().__init__("; ".join(verdict.reasons))


def _engine():
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        raise RuntimeError("thiếu ETL_DATABASE_URL")
    return sa.create_engine(url, pool_pre_ping=True)


def _fetch_all(targets, get, sleep, deadline):
    fetched, failed, bad_shape, stopped = [], 0, 0, False
    with fundamentals_fetch.open_fetcher(get=get, sleep=sleep) as f:
        for i, t in enumerate(targets, 1):
            if deadline is not None and _wall_clock() > deadline:
                stopped = True
                log.info("hết ngân sách thời gian sau %d/%d target", i - 1, len(targets))
                break
            try:
                item, text = f.fetch_one(t)
                rows = fundamentals_normalize.rows(t.kind, item)
                fetched.append(fundamentals_store.Fetched(target=t, text=text, rows=rows))
            except (BadShape, BadRecord) as e:
                bad_shape += 1
                log.warning("%s/%s sai hợp đồng: %s", t.organ_code, t.kind, e)
            except FetchError as e:
                failed += 1
                log.warning("%s", e)
            if i % 50 == 0:
                log.info("đã gọi %d/%d target (%d lời gọi, %d retry)", i, len(targets), f.calls, f.retries)
        return fetched, failed, bad_shape, stopped, f.calls, f.retries


def run(codes=None, kinds=None, max_minutes=None, backfill=False, stop_before_open=False,
        get=None, sleep=time.sleep) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    load_dotenv()
    subset = codes is not None or kinds is not None      # lượt con: không đẩy mốc nước toàn bảng
    try:
        engine = _engine()
    except RuntimeError as e:
        log.error("%s", e)
        return 2
    run_id = omo_store.open_run(engine, JOB)
    try:
        with engine.begin() as conn:
            n_dict = fundamentals_store.load_dictionary(conn)       # hợp đồng khởi động: hỏng thì chết trước fetch
            watermark = fundamentals_store.load_watermark(conn)
            targets = fundamentals_store.due_list(conn, watermark, kinds=kinds, codes=codes, backfill=backfill)
            new_wm = fundamentals_store.new_watermark(conn)          # cùng giao dịch với due_list — không đọc lại sau fetch
        log.info("từ điển %d mã; tới hạn: %d target (%d theo sự kiện)", n_dict, len(targets),
                 sum(1 for t in targets if t.found_by == "event"))

        deadlines = []
        if max_minutes is not None:
            deadlines.append(_wall_clock() + max_minutes * 60)
        if stop_before_open:
            deadlines.append(_next_open(datetime.now(VN)).timestamp())
        deadline = min(deadlines) if deadlines else None
        stop_at = datetime.fromtimestamp(deadline, VN).isoformat(timespec="minutes") if deadline else None

        fetched, failed, bad_shape, stopped, calls, retries = _fetch_all(targets, get, sleep, deadline)
        run_date = datetime.now(VN).date()
        try:
            with engine.begin() as conn:
                tally, written = fundamentals_store.apply(conn, fetched, run_id)
                tally.attempted = len(targets)
                tally.failed, tally.bad_shape = failed, bad_shape
                verdict = fundamentals_guard.check(tally)
                if not verdict.ok:
                    raise GuardRefused(verdict)
                left = fundamentals_store.remaining(conn, kinds)
        except GuardRefused as e:
            fundamentals_store.store_refusal_evidence(engine, fetched, run_id, e.verdict)
            omo_store.close_run(engine, run_id, "failed", error="guard refused: " + "; ".join(e.verdict.reasons))
            log.error("fundamentals từ chối: %s", e.verdict.reasons)
            return 1

        stats = {"tally": vars(tally), "rows_written": written, "calls": calls, "retries": retries,
                 "stopped_early": stopped, "run_date": run_date.isoformat(),
                 "dictionary_rows": n_dict, "remaining": left, "stop_at": stop_at}
        if subset:
            stats["subset"] = True
        if backfill:
            stats["backfill"] = True

        # Mốc nước chỉ tiến khi lượt ĐẦY ĐỦ và KHÔNG target nào hỏng/sai hình dạng/rỗng/bị cắt —
        # đẩy mốc khi còn target chưa phục vụ là mất trigger vĩnh viễn (bài học lát 4).
        push = not subset and failed == 0 and bad_shape == 0 and tally.empty == 0 and not stopped
        if push:
            stats["watermark"] = new_wm.isoformat()
        elif not subset:
            stats["watermark_held"] = True
        omo_store.close_run(engine, run_id, "success", stats)       # close_run TRƯỚC, domain state SAU
        if push:
            fundamentals_store.upsert_domain_state(engine, new_wm.isoformat())
        log.info("fundamentals xong: %s", stats)
        return 0
    except Exception as e:                    # noqa: BLE001 — job biên ngoài: mọi lỗi vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("fundamentals thất bại")
        return 2
    finally:
        engine.dispose()
```

Trong `backend/etl/__main__.py`, ngay trước `print(f"etl: subcommand không hợp lệ…`:

```python
    if args[0] == "fundamentals":
        import etl.fundamentals_job
        parser = argparse.ArgumentParser(prog="etl fundamentals")
        parser.add_argument("--codes", type=lambda s: [t.strip().upper() for t in s.split(",") if t.strip()])
        parser.add_argument("--kinds", type=lambda s: [k.strip() for k in s.split(",") if k.strip()])
        parser.add_argument("--max-minutes", type=float, dest="max_minutes")
        parser.add_argument("--backfill", action="store_true")
        parser.add_argument("--stop-before-open", action="store_true", dest="stop_before_open")
        parsed = parser.parse_args(args[1:])
        return etl.fundamentals_job.run(codes=parsed.codes, kinds=parsed.kinds, max_minutes=parsed.max_minutes,
                                        backfill=parsed.backfill, stop_before_open=parsed.stop_before_open)
```

và sửa chuỗi "hỗ trợ: omo, refdata, screener, events, price, snapshot" thành "…, snapshot, fundamentals".

- [ ] **Step 4: Chạy test, phải xanh** — Expected: `7 passed`. Rồi chạy cả `tests/etl` và `tests/schema`: mọi test cũ vẫn xanh (số trước lát: 533 passed, 2 skipped).

- [ ] **Step 5: Commit**

```bash
git add backend/etl/fundamentals_job.py backend/etl/__main__.py backend/tests/etl/test_e35_fundamentals_job.py
git commit -m "feat(etl): fundamentals job - one transaction, guard before commit, backfill mode with wall-clock budget"
```

---

### Task 7: Chạy thật dưới credential production và tài liệu sống

*(Kiến trúc sư tự làm — cần nhìn output rồi quyết; §4.1 bảng giao/tự làm.)*

- [ ] **Step 1: Migration lên kho production**

```bash
uv run --project backend alembic -c database/alembic.ini upgrade head
```
Expected: `Running upgrade 0016 -> 0017`.

- [ ] **Step 2: AC2** — `cd backend && set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl fundamentals --codes A32,BAB,AAS` → exit 0; đếm `financial_statement` theo issuer: A32 = **3.645**; BAB và AAS so với `python docs/90-records/plans/2026-09-04-fundamentals-etl/count_rows.py` chạy trên payload lấy từ `staging.raw_payload` (xuất ra file tạm ở scratchpad); `financial_report_file` 8 / 106 / 48; `metric_dictionary` 729.
- [ ] **Step 3: AC4** — chạy lại cùng lệnh: `unchanged 12`, `rows_written 0`, số dòng `raw_payload` không tăng.
- [ ] **Step 4: AC3** — `uv run python -m etl fundamentals --backfill --max-minutes 30` ngoài giờ giao dịch; ghi `calls`, `retries`, thời gian, `remaining` trước/sau vào ledger. Lặp các buổi tối với `--backfill --stop-before-open` tới `remaining = 0`.
- [ ] **Step 5: AC7** — sau khi có mốc nước: seed thử bằng cách chạy lượt thường ngày kế tiếp, đối chiếu target `event` với `corporate_event.public_date > watermark`.
- [ ] **Step 6: Tài liệu** — theo checklist spec §8: roadmap (lát 5 ✅ + *Điểm vào cho lát 6*), market-data-store §4.1/§4.2/§5.4, conventions §10.1, database/README (head `0017`, `test_s14`), backend/README (mục "Chạy job fundamentals"), 90-records/README (dòng plan), `ledger.md`. `git grep` các số cũ ("0016", "533 passed") và đối chiếu.
- [ ] **Step 7: Review hai trục** (skill `requesting-code-review`) rồi merge `main`.

## Self-review

- **Spec coverage:** §4.1 (bỏ null, raw payload) → Task 3 + Task 5 `apply`; §4.2 (trọn lịch sử) → normalize duyệt cả hai mảng; §4.3 (trigger + quét sàn, hash trọn payload) → Task 5 `due_list`, Task 3 `payload_hash`; §4.4 (xoá-chèn, reports không xoá) → Task 5 `_write_statement`/`_write_reports`; §4.5 (migration, `source_id`, CHECK) → Task 1; §4.6 (từ điển trong job) → Task 5 `load_dictionary`, Task 6 gọi ở đầu; §5.1 ba chế độ → Task 5 `due_list(backfill, codes)`, Task 6 cờ; §5.2 → Task 2; §5.3 → Task 3; §5.4 → Task 5; §5.5 (bốn chốt + rỗng) → Task 4; §5.6 → Task 7 tài liệu; §6 seam → mỗi task một file test, test quyền ở Task 1; §7 AC → Task 7.
- **Placeholder scan:** không có TBD/TODO; mọi bước code có code.
- **Type consistency:** `Fetched(target, text, rows)` dùng thống nhất ở Task 5/6; `apply(conn, fetched, run_id)` trả `(Tally, int)`; `due_list(conn, watermark, kinds, codes, backfill, quota, cadence, max_trigger)`; `Tally` có `empty`; `classify` trả `{"items": [...]}` cho reports và `report_rows` đọc `item["items"]`; `_fetched` trong test e34 tạo `text` đúng hình `{"items": [item]}` cho báo cáo và `item` (đã là `{"items": [...]}`) cho reports.
