# Lát 7 — ETL quốc tế: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Năm job `python -m etl fred|fx|lbma|yahoo|binance` nạp 71 series quốc tế vào `macro.observation`, `asset.price_daily`, `asset.ohlc_daily` qua ổ cắm registry đã có, guard trước giao dịch ghi, UPSERT chỉ-khi-đổi.

**Architecture:** Phần không phụ thuộc nguồn của lát 6 trích thành ba module chung (`registry.py` · `series_store.py` · `series_guard.py`) cộng một runner chung (`series_job.py`) và một `http_fetch.py`; mỗi nguồn chỉ còn ba file: bảng mã (`<src>_registry.py`), URL + `classify` (`<src>_fetch.py`), luật thời gian + cổng (`<src>_normalize.py`), và một `<src>_job.py` 15 dòng khai `SourceSpec`. Task 1 (lõi) làm trước; Task 2–6 (năm nguồn) **rời file nhau, chạy song song được**; Task 7 tài liệu + chạy thật.

**Tech Stack:** Python 3.12, httpx, SQLAlchemy Core (SQL thuần, `sa.text`), Postgres 16 (schema `macro`/`asset`/`ops`/`staging` — migration head `0017`, **không migration mới**), pytest với fixture `migrated_engine`/`db` ở `backend/tests/conftest.py`.

**Spec:** [`spec.md`](spec.md) cùng thư mục — mọi ngưỡng, mã, `band`, `max_lag` lấy từ Phụ lục A–E của spec; số đo ở `measure-*-2026-09-05.txt`; fixture thật ở `backend/tests/etl/fixtures/global/` (chụp 2026-09-05, danh sách ở Task 1 bước 0).

## Global Constraints

- Chạy mọi lệnh từ `backend/` với `PYTHONIOENCODING=utf-8`; test cần `TEST_DATABASE_URL` (xem `database/README.md` mục Cách chạy). Lệnh test: `uv run pytest tests/etl/<file> -q -p no:cacheprovider`. Toàn bộ: `uv run pytest tests -q` — **650 passed, 2 skipped** trước lát này.
- 🔴 **Khoá FRED (`FRED_API`) không bao giờ xuất hiện trong log, `stats`, message exception, fixture, commit.** Test phải assert điều đó (Task 2).
- Giá trị số vào kho là `Decimal(str(x))`, không `float`. Ngày trong test lấy từ fixture hoặc bơm `now=`; không hardcode cạnh `datetime.now()`.
- Mã (`code`) theo Phụ lục A–E của spec, không đặt thêm. `source` ∈ `{'fred','ecb','lbma','yahoo','binance'}`. Tên job ∈ `{'global.fred','global.ecb','global.lbma','global.yahoo','global.binance'}`.
- Không đụng `wichart_fetch.py`, `wichart_guard.py`, `wichart_normalize.py` (ngoài hai property ở `wichart_registry.Series`); test `test_e36`–`e41` phải xanh nguyên trạng sau Task 1.
- Commit theo mốc, Conventional Commits, message tiếng Anh, kết bằng `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. Subagent **không commit** — ghi file, controller commit (§4.2 CLAUDE.md).
- Mọi test đụng DB dùng fixture `db` (một giao dịch, rollback) khi có thể; test job dùng `migrated_engine` + `_cleanup` theo khuôn `test_e41_wichart_job.py` (xoá đúng dòng của `source` mình, dòng ánh xạ trước, `indicator`/`asset` theo danh sách mã sau).

---

## Bản đồ file

| File | Trách nhiệm | Task |
|---|---|---|
| `backend/etl/registry.py` | `Series` (chung), `Point`, `Bar`, `SeriesError`, `load_registry(conn, series, source)` | 1 |
| `backend/etl/series_store.py` | `Resolved`, `Written`, `apply`, `apply_ohlc`, `store_refusal_evidence`, `upsert_domain_state` | 1 |
| `backend/etl/series_guard.py` | `Tally`, `Verdict`, `check(tally, mode)` | 1 |
| `backend/etl/http_fetch.py` | `Fetcher(get, classify, …)`, `FetchError`, `BadShape`, `open_fetcher` | 1 |
| `backend/etl/series_job.py` | `SourceSpec`, `run(spec, …)` — khuôn job chung | 1 |
| `backend/etl/wichart_registry.py`, `wichart_store.py` | thêm 2 property; store uỷ quyền sang `series_store`, giữ `seed_series_break`/`store_payload_if_changed` | 1 |
| `backend/etl/__main__.py` | 5 subcommand mới | 1 |
| `backend/etl/fred_registry.py` · `fred_fetch.py` · `fred_normalize.py` · `fred_job.py` | FRED | 2 |
| `backend/etl/fx_registry.py` · `fx_fetch.py` · `fx_normalize.py` · `fx_job.py` | ECB/Frankfurter | 3 |
| `backend/etl/lbma_registry.py` · `lbma_fetch.py` · `lbma_normalize.py` · `lbma_job.py` | LBMA | 4 |
| `backend/etl/yahoo_registry.py` · `yahoo_fetch.py` · `yahoo_normalize.py` · `yahoo_job.py` | Yahoo | 5 |
| `backend/etl/binance_registry.py` · `binance_fetch.py` · `binance_normalize.py` · `binance_job.py` | Binance | 6 |
| `backend/tests/etl/test_e43_series_core.py` | lõi chung + role `dlck_etl` trên `ohlc_daily` | 1 |
| `backend/tests/etl/test_e44_fred.py` … `test_e48_binance.py` | mỗi nguồn một file: registry · classify · normalize · job | 2–6 |
| `backend/tests/etl/test_e49_registry_codes_unique.py` | mã không trùng toàn cục (5 nguồn + wichart) | 6 |
| tài liệu §8 spec, `ledger.md` | | 7 |

---

### Task 1: Lõi chung — registry, store, guard, fetch, runner, CLI; wichart chuyển sang dùng

**Files:**
- Create: `backend/etl/registry.py`, `backend/etl/series_store.py`, `backend/etl/series_guard.py`, `backend/etl/http_fetch.py`, `backend/etl/series_job.py`
- Modify: `backend/etl/wichart_registry.py` (lớp `Series`: thêm property `external_key`, `meta`), `backend/etl/wichart_store.py` (uỷ quyền), `backend/etl/__main__.py` (5 subcommand)
- Test: `backend/tests/etl/test_e43_series_core.py`

**Interfaces — Produces (Task 2–6 dựa vào đúng tên và kiểu này):**

```python
# etl/registry.py
@dataclass(frozen=True)
class Series:
    source: str; external_key: str; domain: str; code: str; name_vi: str; unit: str; freq: str
    external_sub: str = ""; scale: Decimal = Decimal(1); role: str = "data"; region: str = "global"
    asset_class: str | None = None; quote_currency: str | None = None; price_type: str | None = None
    calendar: str | None = None; band: tuple[Decimal, Decimal] | None = None; max_lag_days: int = 6
    shape: str = "point"            # 'point' → observation/price_daily · 'ohlc' → ohlc_daily
    extra: dict = field(default_factory=dict)   # vào cột meta jsonb (vd tz, symbol)
    @property
    def meta(self) -> dict            # {"freq", "max_lag_days", "band", **extra}

@dataclass(frozen=True)
class Point: domain: str; code: str; obs_date: date; value: Decimal; price_type: str | None
@dataclass(frozen=True)
class Bar: code: str; obs_date: date; open: Decimal | None; high: Decimal | None; low: Decimal | None; close: Decimal; close_adj: Decimal | None; volume: Decimal | None
class SeriesError(Exception): reason: str   # 'shape' | 'band' | 'stale'
def load_registry(conn, series, source: str) -> tuple[dict[str, Resolved], dict]   # {code: Resolved}, {"macro": n, "asset": n, "removed": n}

# etl/series_store.py
@dataclass(frozen=True) class Resolved: domain: str; row_id: int; price_type: str | None
@dataclass class Written: inserted: int = 0; changed: int = 0; changes_sample: list = field(default_factory=list)  # [(code, iso_date, old, new)] ≤ 50
def apply(conn, points, resolved) -> Written
def apply_ohlc(conn, bars, resolved) -> Written
def store_refusal_evidence(engine, source, texts: dict[str, str], run_id: int, reasons: list[str]) -> None
def upsert_domain_state(engine, source, domains: tuple[str, ...], watermark: str) -> None

# etl/series_guard.py
MIN_SAMPLE = 20; MAX_FAILED = 0.20; MAX_SHAPE = 0.05; MAX_BAND = 0.05; MAX_STALE = 0.20
@dataclass class Tally: total: int = 0; failed: int = 0; shape: int = 0; band: int = 0; stale: int = 0; ok: int = 0; details: list[str] = field(default_factory=list)
@dataclass class Verdict: ok: bool; reasons: list[str] = field(default_factory=list)
def check(t: Tally, mode: str) -> Verdict      # mode 'all_or_nothing' | 'ratio'

# etl/http_fetch.py
class FetchError(Exception); class BadShape(Exception)
class Fetcher:
    def __init__(self, get, classify, sleep=time.sleep, clock=time.monotonic, min_interval=0.0, retries=3, backoff=(2, 4, 8), timeout=30.0)
    calls: int; retries_done: int; last_headers: dict
    def fetch_one(self, url: str, label: str) -> tuple[Any, str]   # (doc, text); raise BadShape | FetchError
@contextmanager
def open_fetcher(classify, get=None, sleep=time.sleep, clock=time.monotonic, headers=None, **kw) -> Fetcher
# get(url, timeout) -> (status: int, text: str, headers: dict)   — test bơm get giả trả 3-tuple

# etl/series_job.py
@dataclass
class SourceSpec:
    job: str; source: str; domains: tuple[str, ...]; guard_mode: str; log_name: str
    build: Callable[[], list[Series]]
    fetch_all: Callable[..., tuple[dict, dict, list[str], int, int]]  # (series, get, sleep, backfill) -> (docs{external_key: doc}, texts{external_key: str}, failed[external_key], calls, retries)
    normalize: Callable[..., list]                                    # (series, doc, now: datetime UTC) -> list[Point] | list[Bar]; raise SeriesError
    supports_backfill: bool = False
def run(spec, keys=None, dry_run=False, backfill=False, get=None, sleep=time.sleep, now=None) -> int
```

Hợp đồng `run`: `open_run` ngay trước `try`; `--keys` (theo `external_key`) = lượt con không guard, không đụng domain state, registry vẫn nạp trọn; `dry_run` không ghi gì; guard từ chối ⇒ `store_refusal_evidence` + `close_run('failed')` + return 1; `KeyboardInterrupt` ⇒ `failed: dừng tay (Ctrl+C)`, return 130; exception khác ⇒ return 2; `stats` = `{"tally": vars(tally), "calls", "retries", "points", "bars", "run_date", "registry", "inserted", "changed", "changes_sample", "watermark"(lượt trọn), "subset"/"dry_run"/"backfill" khi có}`.

- [ ] **Bước 0: kiểm fixture đã có** — `ls backend/tests/etl/fixtures/global/` phải có 14 file: `fred-DGS10-tail.json` · `fred-PAYEMS-tail.json` · `fred-DTWEXBGS-tail.json` · `ecb-2026-08.json` · `lbma-gold_pm-trimmed.json` · `lbma-silver-trimmed.json` · `yahoo-GSPC-10d.json` · `yahoo-N225-10d.json` · `yahoo-DXY-10d.json` · `yahoo-TIO=F-40d.json` · `yahoo-BCOM-40d.json` · `yahoo-MERV-10d.json` · `binance-PAXGUSDT-5.json` · `binance-BTCUSDT-first3.json`. `grep -rl api_key` trong thư mục phải ra 0.

- [ ] **Bước 1: test đỏ cho `registry.py` + `series_store.py`** — tạo `backend/tests/etl/test_e43_series_core.py`:

```python
"""Lõi chung của lát 7: registry theo source, apply/apply_ohlc, guard hai chế độ, runner. DB thật (fixture `db` rollback)."""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import registry as rg
from etl import series_guard as sg
from etl import series_store as ss
from etl import wichart_registry as wr
from etl import wichart_store as ws
from etl.registry import Bar, Point, Series


def _count(db, sql, **p):
    return db.execute(sa.text(sql), p).scalar()


FAKE = [
    Series(source="zz", external_key="DGS10", domain="macro", code="zz.yield.10y", name_vi="ZZ 10y", unit="%", freq="d",
           region="us", band=(Decimal(-1), Decimal(25))),
    Series(source="zz", external_key="DCOILWTICO", domain="asset", code="wti", name_vi="Giá dầu WTI giao ngay", unit="USD/thùng",
           freq="d", region="us", asset_class="commodity", quote_currency="USD", price_type="spot", calendar="trading_days",
           band=(Decimal(5), Decimal(500)), max_lag_days=10),
    Series(source="zz", external_key="^GSPC", domain="asset", code="zz.idx.sp500", name_vi="ZZ S&P", unit="điểm", freq="d",
           region="us", asset_class="index", quote_currency="USD", calendar="trading_days", shape="ohlc",
           band=(Decimal(700), Decimal(80000)), max_lag_days=14, extra={"tz": "America/New_York"}),
]


def test_load_registry_scoped_by_source_reuses_wti_asset_and_leaves_wichart_rows_alone(db):
    ws.load_registry(db, wr.build())                                    # 53 + 52 dòng wichart có trước
    wti_id = _count(db, "SELECT asset_id FROM asset.asset WHERE code='wti'")
    resolved, stats = rg.load_registry(db, FAKE, "zz")
    assert stats == {"macro": 1, "asset": 2, "removed": 0}
    assert resolved["wti"].row_id == wti_id and resolved["wti"].price_type == "spot"   # cùng asset_id, thêm dòng ánh xạ
    assert resolved["zz.idx.sp500"].price_type is None and resolved["zz.yield.10y"].domain == "macro"
    assert _count(db, "SELECT count(*) FROM asset.asset_external_id WHERE asset_id=:a", a=wti_id) == 2   # wichart + zz
    assert _count(db, "SELECT count(*) FROM macro.indicator_source WHERE source='wichart'") == 53
    assert _count(db, "SELECT count(*) FROM asset.asset_external_id WHERE source='wichart'") == 52
    row = db.execute(sa.text("SELECT meta->>'max_lag_days', meta->'band', meta->>'tz' FROM asset.asset_external_id"
                             " WHERE source='zz' AND external_code='^GSPC'")).one()
    assert tuple(row) == ("14", ["700", "80000"], "America/New_York")
    _, stats2 = rg.load_registry(db, FAKE[:2], "zz")                     # bỏ 1 series: xoá đúng dòng của zz
    assert stats2["removed"] == 1
    assert _count(db, "SELECT count(*) FROM asset.asset_external_id WHERE source='wichart'") == 52


def test_apply_reports_a_sample_of_changed_rows_with_old_and_new_values(db):
    resolved, _ = rg.load_registry(db, FAKE, "zz")
    pts = [Point("macro", "zz.yield.10y", date(2026, 9, 2), Decimal("4.79"), None),
           Point("macro", "zz.yield.10y", date(2026, 9, 3), Decimal("4.77"), None),
           Point("asset", "wti", date(2026, 9, 1), Decimal("91.48"), "spot")]
    w = ss.apply(db, pts, resolved)
    assert (w.inserted, w.changed, w.changes_sample) == (3, 0, [])
    w = ss.apply(db, pts, resolved)
    assert (w.inserted, w.changed, w.changes_sample) == (0, 0, [])
    pts[0] = Point("macro", "zz.yield.10y", date(2026, 9, 2), Decimal("4.80"), None)      # vá hồi tố
    w = ss.apply(db, pts, resolved)
    assert (w.inserted, w.changed) == (0, 1)
    assert w.changes_sample == [("zz.yield.10y", "2026-09-02", Decimal("4.79"), Decimal("4.80"))]
    assert _count(db, "SELECT count(*) FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                      " WHERE a.code='wti' AND price_type='spot'") == 1


def test_apply_ohlc_upserts_only_when_a_field_changes_and_keeps_close_when_close_adj_changes(db):
    resolved, _ = rg.load_registry(db, FAKE, "zz")
    bar = Bar("zz.idx.sp500", date(2026, 9, 4), Decimal("7750.19"), Decimal("7760"), Decimal("7700"), Decimal("7718.60"),
              Decimal("7718.60"), Decimal("4103570000"))
    w = ss.apply_ohlc(db, [bar], resolved)
    assert (w.inserted, w.changed) == (1, 0)
    ts1 = _count(db, "SELECT max(ingested_at) FROM asset.ohlc_daily")
    w = ss.apply_ohlc(db, [bar], resolved)
    assert (w.inserted, w.changed) == (0, 0)
    assert _count(db, "SELECT max(ingested_at) FROM asset.ohlc_daily") == ts1
    w = ss.apply_ohlc(db, [Bar("zz.idx.sp500", date(2026, 9, 4), Decimal("7750.19"), Decimal("7760"), Decimal("7700"),
                              Decimal("7718.60"), Decimal("7700.00"), Decimal("4103570000"))], resolved)
    assert (w.inserted, w.changed) == (0, 1)
    row = db.execute(sa.text("SELECT close, close_adj FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id)"
                             " WHERE a.code='zz.idx.sp500'")).one()
    assert tuple(row) == (Decimal("7718.60"), Decimal("7700.00"))          # seam 3 bước 5: close giữ nguyên


def test_wichart_store_still_works_through_the_shared_core(db):
    resolved, stats = ws.load_registry(db, wr.build())
    assert stats == {"macro": 53, "asset": 52, "removed": 0} and resolved["wti"].price_type == "futures"
    w = ws.apply(db, [Point("asset", "wti", date(2026, 9, 4), Decimal("62.1"), "futures")], resolved)
    assert (w.inserted, w.changed) == (1, 0)


def test_core_works_under_etl_role_including_ohlc_daily(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    resolved, _ = rg.load_registry(db, FAKE, "zz")
    assert ss.apply(db, [Point("macro", "zz.yield.10y", date(2026, 9, 3), Decimal("4.77"), None)], resolved).inserted == 1
    assert ss.apply_ohlc(db, [Bar("zz.idx.sp500", date(2026, 9, 4), None, None, None, Decimal("7718.6"), None, None)], resolved).inserted == 1
```

- [ ] **Bước 2: chạy, xác nhận đỏ** — `uv run pytest tests/etl/test_e43_series_core.py -q -p no:cacheprovider` ⇒ `ModuleNotFoundError: etl.registry` (ImportError ở collection là đỏ hợp lệ cho seam module mới).

- [ ] **Bước 3: viết `backend/etl/registry.py`**

```python
"""Registry chung cho mọi nguồn ngoài WiChart (spec lát 7 §4.1): `Series` là 'mã của mình' + tham số cổng;
`load_registry` là ĐƯỜNG GHI DUY NHẤT vào 4 bảng registry, lọc theo `source` — lát 6 đã trả giá vì bộ lọc này
(điểm vào lát 7: gọi thiếu `source` là lượt FRED xoá ánh xạ WiChart)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from etl.series_store import Resolved


@dataclass(frozen=True)
class Series:
    source: str
    external_key: str
    domain: str                      # 'macro' | 'asset'
    code: str
    name_vi: str
    unit: str
    freq: str                        # 'd' | 'm'
    external_sub: str = ""
    scale: Decimal = Decimal(1)
    role: str = "data"
    region: str = "global"
    asset_class: str | None = None
    quote_currency: str | None = None
    price_type: str | None = None    # None cho OHLC
    calendar: str | None = None
    band: tuple[Decimal, Decimal] | None = None
    max_lag_days: int = 6
    shape: str = "point"             # 'point' | 'ohlc'
    extra: dict = field(default_factory=dict)

    @property
    def meta(self) -> dict:
        band = [str(self.band[0]), str(self.band[1])] if self.band else None
        return {"freq": self.freq, "max_lag_days": self.max_lag_days, "band": band, **self.extra}


@dataclass(frozen=True)
class Point:
    domain: str
    code: str
    obs_date: date
    value: Decimal
    price_type: str | None


@dataclass(frozen=True)
class Bar:
    code: str
    obs_date: date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    close_adj: Decimal | None
    volume: Decimal | None


class SeriesError(Exception):
    def __init__(self, reason: str, msg: str):
        self.reason = reason         # 'shape' | 'band' | 'stale'
        super().__init__(msg)


def load_registry(conn, series, source: str) -> tuple[dict[str, Resolved], dict]:
    """Upsert indicator/asset theo `code` (không bao giờ xoá), upsert dòng ánh xạ theo (source, key, sub);
    dòng ánh xạ của `source` vắng mặt trong `series` bị xoá TRƯỚC vòng INSERT (ruling I1 lát 6)."""
    present_m = [f"{s.external_key}/{s.external_sub}" for s in series if s.domain == "macro"]
    present_a = [f"{s.external_key}/{s.external_sub}" for s in series if s.domain == "asset"]
    removed = conn.execute(sa.text(
        "DELETE FROM macro.indicator_source WHERE source = :src"
        " AND NOT (external_key || '/' || external_sub = ANY(:present))"), {"src": source, "present": present_m}).rowcount
    removed += conn.execute(sa.text(
        "DELETE FROM asset.asset_external_id WHERE source = :src"
        " AND NOT (external_code || '/' || external_sub = ANY(:present))"), {"src": source, "present": present_a}).rowcount
    resolved: dict[str, Resolved] = {}
    for s in series:
        meta = json.dumps(s.meta, ensure_ascii=False)
        if s.domain == "macro":
            iid = conn.execute(sa.text(
                "INSERT INTO macro.indicator (code, name_vi, unit, freq, region, role)"
                " VALUES (:code, :name, :unit, :freq, :region, :role)"
                " ON CONFLICT (code) DO UPDATE SET name_vi = excluded.name_vi, unit = excluded.unit,"
                " freq = excluded.freq, role = excluded.role, region = excluded.region RETURNING indicator_id"),
                {"code": s.code, "name": s.name_vi, "unit": s.unit, "freq": s.freq, "region": s.region, "role": s.role}).scalar_one()
            conn.execute(sa.text(
                "INSERT INTO macro.indicator_source (indicator_id, source, external_key, external_sub, scale, active, meta)"
                " VALUES (:iid, :src, :key, :sub, :scale, true, cast(:meta AS jsonb))"
                " ON CONFLICT (source, external_key, external_sub) DO UPDATE SET indicator_id = excluded.indicator_id,"
                " scale = excluded.scale, active = true, meta = excluded.meta"),
                {"iid": iid, "src": source, "key": s.external_key, "sub": s.external_sub, "scale": s.scale, "meta": meta})
            resolved[s.code] = Resolved("macro", iid, None)
        else:
            aid = conn.execute(sa.text(
                "INSERT INTO asset.asset (code, name_vi, asset_class, quote_currency, unit, calendar, region)"
                " VALUES (:code, :name, :cls, :ccy, :unit, :cal, :region)"
                " ON CONFLICT (code) DO UPDATE SET name_vi = excluded.name_vi, asset_class = excluded.asset_class,"
                " quote_currency = excluded.quote_currency, unit = excluded.unit, calendar = excluded.calendar,"
                " region = excluded.region RETURNING asset_id"),
                {"code": s.code, "name": s.name_vi, "cls": s.asset_class, "ccy": s.quote_currency, "unit": s.unit,
                 "cal": s.calendar or "trading_days", "region": s.region}).scalar_one()
            conn.execute(sa.text(
                "INSERT INTO asset.asset_external_id (asset_id, source, external_code, external_sub, scale, active, price_type, meta)"
                " VALUES (:aid, :src, :key, :sub, :scale, true, :pt, cast(:meta AS jsonb))"
                " ON CONFLICT (source, external_code, external_sub) DO UPDATE SET asset_id = excluded.asset_id,"
                " scale = excluded.scale, active = true, price_type = excluded.price_type, meta = excluded.meta"),
                {"aid": aid, "src": source, "key": s.external_key, "sub": s.external_sub, "scale": s.scale,
                 "pt": s.price_type, "meta": meta})
            resolved[s.code] = Resolved("asset", aid, s.price_type)
    return resolved, {"macro": len(present_m), "asset": len(present_a), "removed": removed}
```

⚠️ `wti` của WiChart có `name_vi` "Giá dầu WTI tương lai"; FRED upsert cùng `code` sẽ **đổi `name_vi`** của asset — vì `asset.asset` là một thực thể (dầu WTI) với hai chuỗi giá, `name_vi` phải trung tính: Task 2 dùng `name_vi="Giá dầu WTI"` và Task 1 sửa `wichart_registry.ASSET[("dau_wti", 0)]` thành `("wti", "Giá dầu WTI", …)` — bước 6 dưới, kèm sửa `test_e36` nếu có assert tên (không có: `grep "Giá dầu WTI" backend/tests` ra 0).

- [ ] **Bước 4: viết `backend/etl/series_store.py`**

```python
"""Đường ghi chung cho mọi job series (spec lát 7 §5.5): UPSERT chỉ-khi-đổi, đếm inserted/changed qua xmax,
mẫu dòng đổi (§4.6) thay cho lưu body mỗi lần hash đổi."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal

import sqlalchemy as sa

CHUNK = 5000
SAMPLE_CAP = 50


@dataclass(frozen=True)
class Resolved:
    domain: str
    row_id: int
    price_type: str | None


@dataclass
class Written:
    inserted: int = 0
    changed: int = 0
    changes_sample: list = field(default_factory=list)   # [(code, iso_date, old, new)]


_UPSERT_MACRO = sa.text(
    "INSERT INTO macro.observation (indicator_id, obs_date, value)"
    " SELECT * FROM unnest(cast(:ids AS bigint[]), cast(:dates AS date[]), cast(:vals AS numeric[]))"
    " ON CONFLICT (indicator_id, obs_date) DO UPDATE SET value = excluded.value, ingested_at = clock_timestamp()"
    " WHERE macro.observation.value IS DISTINCT FROM excluded.value"
    " RETURNING (xmax = 0) AS inserted, indicator_id AS rid, obs_date")
_UPSERT_ASSET = sa.text(
    "INSERT INTO asset.price_daily (asset_id, obs_date, price_type, value)"
    " SELECT * FROM unnest(cast(:ids AS bigint[]), cast(:dates AS date[]), cast(:types AS text[]), cast(:vals AS numeric[]))"
    " ON CONFLICT (asset_id, obs_date, price_type) DO UPDATE SET value = excluded.value, ingested_at = clock_timestamp()"
    " WHERE asset.price_daily.value IS DISTINCT FROM excluded.value"
    " RETURNING (xmax = 0) AS inserted, asset_id AS rid, obs_date")
_OLD_MACRO = sa.text(
    "SELECT o.indicator_id, o.obs_date, o.value FROM macro.observation o"
    " JOIN unnest(cast(:ids AS bigint[]), cast(:dates AS date[])) AS u(id, d) ON u.id = o.indicator_id AND u.d = o.obs_date")
_OLD_ASSET = sa.text(
    "SELECT p.asset_id, p.obs_date, p.value FROM asset.price_daily p"
    " JOIN unnest(cast(:ids AS bigint[]), cast(:dates AS date[]), cast(:types AS text[])) AS u(id, d, t)"
    " ON u.id = p.asset_id AND u.d = p.obs_date AND u.t = p.price_type")
_UPSERT_OHLC = sa.text(
    "INSERT INTO asset.ohlc_daily (asset_id, obs_date, open, high, low, close, close_adj, volume)"
    " SELECT * FROM unnest(cast(:ids AS bigint[]), cast(:dates AS date[]), cast(:o AS numeric[]), cast(:h AS numeric[]),"
    " cast(:l AS numeric[]), cast(:c AS numeric[]), cast(:ca AS numeric[]), cast(:v AS numeric[]))"
    " ON CONFLICT (asset_id, obs_date) DO UPDATE SET open = excluded.open, high = excluded.high, low = excluded.low,"
    " close = excluded.close, close_adj = excluded.close_adj, volume = excluded.volume, ingested_at = clock_timestamp()"
    " WHERE (asset.ohlc_daily.open, asset.ohlc_daily.high, asset.ohlc_daily.low, asset.ohlc_daily.close,"
    " asset.ohlc_daily.close_adj, asset.ohlc_daily.volume) IS DISTINCT FROM"
    " (excluded.open, excluded.high, excluded.low, excluded.close, excluded.close_adj, excluded.volume)"
    " RETURNING (xmax = 0) AS inserted")


def _run_points(conn, w: Written, chunk, resolved, code_of, upsert, old_sql, params):
    old = {(r[0], r[1]): r[2] for r in conn.execute(old_sql, params).all()}
    new = {(resolved[p.code].row_id, p.obs_date): p.value for p in chunk}
    for inserted, rid, d in conn.execute(upsert, params).all():
        if inserted:
            w.inserted += 1
        else:
            w.changed += 1
            if len(w.changes_sample) < SAMPLE_CAP:
                w.changes_sample.append((code_of[rid], d.isoformat(), old.get((rid, d)), new[(rid, d)]))


def apply(conn, points, resolved) -> Written:
    w = Written()
    code_of_m = {r.row_id: c for c, r in resolved.items() if r.domain == "macro"}
    code_of_a = {r.row_id: c for c, r in resolved.items() if r.domain == "asset"}
    macro = [p for p in points if p.domain == "macro"]
    asset = [p for p in points if p.domain == "asset"]
    for start in range(0, len(macro), CHUNK):
        chunk = macro[start:start + CHUNK]
        params = {"ids": [resolved[p.code].row_id for p in chunk], "dates": [p.obs_date for p in chunk],
                  "vals": [p.value for p in chunk]}
        _run_points(conn, w, chunk, resolved, code_of_m, _UPSERT_MACRO, _OLD_MACRO, params)
    for start in range(0, len(asset), CHUNK):
        chunk = asset[start:start + CHUNK]
        params = {"ids": [resolved[p.code].row_id for p in chunk], "dates": [p.obs_date for p in chunk],
                  "types": [p.price_type for p in chunk], "vals": [p.value for p in chunk]}
        _run_points(conn, w, chunk, resolved, code_of_a, _UPSERT_ASSET, _OLD_ASSET, params)
    return w


def apply_ohlc(conn, bars, resolved) -> Written:
    w = Written()
    for start in range(0, len(bars), CHUNK):
        chunk = bars[start:start + CHUNK]
        flags = conn.execute(_UPSERT_OHLC, {
            "ids": [resolved[b.code].row_id for b in chunk], "dates": [b.obs_date for b in chunk],
            "o": [b.open for b in chunk], "h": [b.high for b in chunk], "l": [b.low for b in chunk],
            "c": [b.close for b in chunk], "ca": [b.close_adj for b in chunk], "v": [b.volume for b in chunk]}).scalars().all()
        w.inserted += sum(1 for f in flags if f)
        w.changed += sum(1 for f in flags if not f)
    return w


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def store_refusal_evidence(engine, source: str, texts: dict[str, str], run_id: int, reasons: list[str]) -> None:
    """Bằng chứng ở giao dịch RIÊNG — lượt chính không ghi gì. JSON hợp lệ vào payload; body khác vào text."""
    with engine.begin() as conn:
        for key, text in texts.items():
            meta = json.dumps({"run_id": run_id, "reasons": reasons, "refused": True, "hash": _hash(text)}, ensure_ascii=False)
            try:
                json.loads(text)
                conn.execute(sa.text(
                    "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                    " VALUES (:src, :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
                    {"src": source, "ek": f"{source}:{key}", "p": text, "m": meta})
            except ValueError:
                conn.execute(sa.text(
                    "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, body, meta)"
                    " VALUES (:src, :ek, 'text', :b, cast(:m AS jsonb))"),
                    {"src": source, "ek": f"{source}:{key}", "b": text[:100000], "m": meta})


def upsert_domain_state(engine, source: str, domains: tuple[str, ...], watermark: str) -> None:
    with engine.begin() as conn:
        for domain in domains:
            conn.execute(sa.text(
                "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
                " VALUES (:d, :s, 'active', now(), :w)"
                " ON CONFLICT (domain, source) DO UPDATE SET last_success_at = now(), watermark = :w, status = 'active'"),
                {"d": domain, "s": source, "w": watermark})
```

- [ ] **Bước 5: `wichart_store.py` uỷ quyền sang lõi** — thay toàn bộ phần `Resolved`/`Written`/`load_registry`/`_UPSERT_*`/`apply`/`store_refusal_evidence`/`upsert_domain_state` bằng:

```python
from etl.series_store import Resolved, Written, apply  # noqa: F401 — test_e40 import Resolved/Written/apply từ đây
from etl import series_store


def load_registry(conn, series):
    return series_store_load(conn, series)


def series_store_load(conn, series):
    from etl.registry import load_registry as _load       # import trễ: registry.py import series_store, tránh vòng
    return _load(conn, series, SOURCE)


def store_refusal_evidence(engine, texts, run_id, verdict):
    series_store.store_refusal_evidence(engine, SOURCE, texts, run_id, verdict.reasons)


def upsert_domain_state(engine, watermark):
    series_store.upsert_domain_state(engine, SOURCE, DOMAINS, watermark)
```

Giữ nguyên `JOB`, `DOMAINS`, `CHUNK` (bỏ, không còn dùng), `GDP_BREAK`, `seed_series_break`, `_hash`, `store_payload_if_changed`. Bỏ import không dùng (`Decimal` chỉ còn cho `GDP_BREAK` — giữ; `Verdict`, `Point` bỏ nếu mồ côi). `wichart_registry.Series` thêm:

```python
    @property
    def external_key(self) -> str:
        return self.key

    @property
    def meta(self) -> dict:
        return {"flags": list(self.flags), "freq": self.freq, "group": self.group, "tier": self.tier,
                "key_flags": list(self.key_flags)}
```

Và `load_registry` chung dùng `s.calendar or "trading_days"` nên macro `calendar=None` vẫn ghi `asset.calendar` đúng cho asset. Kiểm: `_UPSERT`/`apply` chung có `RETURNING … rid, obs_date` — `wichart_job` chỉ đọc `written.inserted/changed`, không đổi.

- [ ] **Bước 6: sửa tên `wti` trung tính** — `wichart_registry.ASSET[("dau_wti", 0)]` → `("wti", "Giá dầu WTI", _C, "USD", "USD/thùng", "futures", "us")`.

- [ ] **Bước 7: chạy e43 (4 test đầu) + e36–e41** — `uv run pytest tests/etl/test_e43_series_core.py tests/etl/test_e36_wichart_registry.py tests/etl/test_e37_wichart_fetch.py tests/etl/test_e38_wichart_normalize.py tests/etl/test_e39_wichart_guard.py tests/etl/test_e40_wichart_store.py tests/etl/test_e41_wichart_job.py -q -p no:cacheprovider` ⇒ tất cả PASS (e43 5/5; lát 6 43/43).

- [ ] **Bước 8: test đỏ cho guard** — thêm vào `test_e43_series_core.py`:

```python
def test_guard_all_or_nothing_refuses_on_a_single_stale_series():
    t = sg.Tally(total=15, ok=14, stale=1, details=["DTWEXBGS stale: 2026-08-28 < 2026-09-03"])
    v = sg.check(t, "all_or_nothing")
    assert not v.ok and "DTWEXBGS" in v.reasons[0]
    assert sg.check(sg.Tally(total=15, ok=15), "all_or_nothing").ok


def test_guard_ratio_uses_min_sample_and_per_kind_caps():
    assert sg.check(sg.Tally(total=37, ok=36, shape=1), "ratio").ok                   # 2,7 % ≤ 5 %
    assert not sg.check(sg.Tally(total=37, ok=35, shape=2), "ratio").ok               # 5,4 % > 5 %
    assert not sg.check(sg.Tally(total=37, ok=29, stale=8), "ratio").ok               # 21,6 % > 20 %
    assert sg.check(sg.Tally(total=37, ok=30, stale=7), "ratio").ok                   # 18,9 %
    assert sg.check(sg.Tally(total=19, ok=10, failed=9), "ratio").ok                  # dưới MIN_SAMPLE: không xét
    assert not sg.check(sg.Tally(total=20, ok=15, failed=5), "ratio").ok              # 25 % > 20 %
```

- [ ] **Bước 9: chạy đỏ** — `AttributeError: module 'etl.series_guard'` / ImportError.

- [ ] **Bước 10: viết `backend/etl/series_guard.py`**

```python
"""Chốt chặn chung (spec lát 7 §4.5, §5.4). Thuần; đánh giá TRƯỚC khi mở giao dịch ghi."""
from __future__ import annotations

from dataclasses import dataclass, field

MIN_SAMPLE = 20
MAX_FAILED = 0.20
MAX_SHAPE = 0.05
MAX_BAND = 0.05
MAX_STALE = 0.20


@dataclass
class Tally:
    total: int = 0
    failed: int = 0        # fetch hỏng sau mọi lần thử
    shape: int = 0         # response sai hình dạng / cổng lược đồ
    band: int = 0          # điểm mới nhất ngoài dải
    stale: int = 0         # cổng độ tươi
    ok: int = 0
    details: list[str] = field(default_factory=list)


@dataclass
class Verdict:
    ok: bool
    reasons: list[str] = field(default_factory=list)


def check(t: Tally, mode: str) -> Verdict:
    bad = t.failed + t.shape + t.band + t.stale
    if mode == "all_or_nothing":
        if bad:
            return Verdict(False, [f"{bad}/{t.total} series hỏng — nguồn ≤ 20 series: tất cả hoặc không gì; "
                                   + "; ".join(t.details[:10])])
        return Verdict(True)
    if mode != "ratio":
        raise ValueError(f"mode lạ: {mode!r}")
    reasons: list[str] = []
    if t.total >= MIN_SAMPLE:
        for n, cap, label in ((t.failed, MAX_FAILED, "series fetch hỏng"), (t.shape, MAX_SHAPE, "series sai hình dạng"),
                              (t.band, MAX_BAND, "series ngoài dải"), (t.stale, MAX_STALE, "series không tươi")):
            rate = n / t.total
            if rate > cap:
                reasons.append(f"tỷ lệ {label} {rate:.1%} > {cap:.0%} ({n}/{t.total})")
    return Verdict(ok=not reasons, reasons=reasons)
```

- [ ] **Bước 11: chạy xanh** — e43 7/7.

- [ ] **Bước 12: viết `backend/etl/http_fetch.py`** (không test riêng: được phủ qua test job từng nguồn với `get` giả; giữ khuôn `wichart_fetch.Fetcher`)

```python
"""Fetcher chung cho 5 nguồn quốc tế: `get` bơm được (trả (status, text, headers)), `classify` theo nguồn,
retry + backoff, exception vận chuyển đi cùng đường với response xấu (bài học lát 3, e7f80f6)."""
from __future__ import annotations

import contextlib
import time

import httpx

DEFAULT_HEADERS = {"Accept-Encoding": "gzip",
                   "User-Agent": "dulieuchungkhoan.vn/etl (dulieuchungkhoan.official@gmail.com)"}


class FetchError(Exception):
    """Một lời gọi hỏng sau mọi lần thử — series đó CHƯA nạp."""


class BadShape(Exception):
    """Response hợp lệ nhưng không đúng hình dạng/tham số — thử lại vô ích."""


class Fetcher:
    def __init__(self, get, classify, sleep=time.sleep, clock=time.monotonic, min_interval=0.0,
                 retries=3, backoff=(2, 4, 8), timeout=30.0):
        self._get, self._classify, self._sleep, self._clock = get, classify, sleep, clock
        self.min_interval, self.retries, self.backoff, self.timeout = min_interval, retries, backoff, timeout
        self.calls = 0
        self.retries_done = 0
        self.last_headers: dict = {}
        self._last: float | None = None

    def _throttle(self) -> None:
        now = self._clock()
        if self._last is not None:
            wait = self.min_interval - (now - self._last)
            if wait > 0:
                self._sleep(wait)
        self._last = self._clock()

    def fetch_one(self, url: str, label: str):
        self._throttle()
        http, text = 0, ""
        for attempt in range(self.retries + 1):
            try:
                self.calls += 1
                http, text, self.last_headers = self._get(url, self.timeout)
            except httpx.HTTPError as e:
                http, text, self.last_headers = 0, f"{type(e).__name__}", {}
            verdict, doc = self._classify(http, text)
            if verdict == "ok":
                return doc, text
            if verdict == "bad_shape":
                raise BadShape(f"{label}: {text[:200]}")
            if attempt == self.retries:
                break
            self._sleep(self.backoff[attempt])
            self.retries_done += 1
        raise FetchError(f"{label} hỏng sau {self.retries + 1} lần (HTTP {http}): {text[:200]}")


@contextlib.contextmanager
def open_fetcher(classify, get=None, sleep=time.sleep, clock=time.monotonic, headers=None, **kw):
    if get is not None:
        yield Fetcher(get, classify, sleep, clock, **kw)
        return
    with httpx.Client(headers={**DEFAULT_HEADERS, **(headers or {})}, follow_redirects=True) as client:
        def get_one(u: str, timeout: float):
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text, dict(r.headers)
        yield Fetcher(get_one, classify, sleep, clock, **kw)
```

⚠️ `text` khi exception là **tên lớp exception, không có `str(e)`** — vì `str(e)` của httpx chứa URL, mà URL FRED chứa khoá (Bẫy 7). `label` do nguồn đặt, không được chứa khoá.

- [ ] **Bước 13: test đỏ cho runner** — thêm vào `test_e43_series_core.py` một nguồn giả trọn vòng (dùng `migrated_engine`, cleanup theo source `zz`):

```python
import os
from etl import series_job as sj


def _cleanup_zz(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM macro.observation WHERE indicator_id IN (SELECT indicator_id FROM macro.indicator_source WHERE source='zz')"))
        c.execute(sa.text("DELETE FROM asset.price_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='zz')"))
        c.execute(sa.text("DELETE FROM asset.ohlc_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='zz')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='zz'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job='global.zz'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source='zz'"))
        c.execute(sa.text("DELETE FROM macro.indicator_source WHERE source='zz'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='zz'"))
        c.execute(sa.text("DELETE FROM macro.indicator WHERE code='zz.yield.10y'"))
        c.execute(sa.text("DELETE FROM asset.asset WHERE code='zz.idx.sp500'"))
        # 'wti' KHÔNG xoá: có thể là của wichart (test khác)


@pytest.fixture()
def zz(migrated_engine):
    _cleanup_zz(migrated_engine)
    yield migrated_engine
    _cleanup_zz(migrated_engine)


def _fake_fetch_all(series, get, sleep, backfill):
    docs = {s.external_key: {"k": s.external_key} for s in series}
    return docs, {k: '{"k": "%s"}' % k for k in docs}, [], len(docs), 0


def _fake_normalize(s, doc, now):
    if s.shape == "ohlc":
        return [Bar(s.code, date(2026, 9, 4), None, None, None, Decimal("7718.6"), Decimal("7718.6"), None)]
    if s.external_key == "DGS10":
        return [Point("macro", s.code, date(2026, 9, 3), Decimal("4.77"), None)]
    return [Point("asset", s.code, date(2026, 9, 1), Decimal("91.48"), "spot")]


def _spec(normalize=_fake_normalize, mode="all_or_nothing"):
    return sj.SourceSpec(job="global.zz", source="zz", domains=("macro.indicator", "asset"), guard_mode=mode,
                         log_name="zz", build=lambda: FAKE, fetch_all=_fake_fetch_all, normalize=normalize)


def _wire(monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.series_job.load_dotenv", lambda *a, **k: None)


def _last_run(engine, job="global.zz"):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job=:j ORDER BY run_id DESC LIMIT 1"), {"j": job}).one()


def test_runner_full_run_writes_points_and_bars_and_two_domain_states(zz, monkeypatch):
    _wire(monkeypatch)
    now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    assert sj.run(_spec(), get=lambda u, t: (200, "{}", {}), sleep=lambda s: None, now=now) == 0
    status, stats, _ = _last_run(zz)
    assert status == "success" and stats["registry"] == {"macro": 1, "asset": 2, "removed": 0}
    assert (stats["inserted"], stats["changed"], stats["points"], stats["bars"]) == (3, 0, 2, 1)
    assert stats["tally"]["ok"] == 3 and stats["watermark"] == "2026-09-05"
    with zz.connect() as c:
        rows = dict(c.execute(sa.text("SELECT domain, watermark FROM ops.data_domain_state WHERE source='zz'")).all())
        n = c.execute(sa.text("SELECT count(*) FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id) WHERE a.code='zz.idx.sp500'")).scalar()
    assert rows == {"macro.indicator": "2026-09-05", "asset": "2026-09-05"} and n == 1
    assert sj.run(_spec(), get=lambda u, t: (200, "{}", {}), sleep=lambda s: None, now=now) == 0
    assert (_last_run(zz)[1]["inserted"], _last_run(zz)[1]["changed"]) == (0, 0)


def test_runner_refuses_whole_run_on_one_stale_series_and_keeps_evidence(zz, monkeypatch):
    _wire(monkeypatch)

    def stale_one(s, doc, now):
        if s.external_key == "DGS10":
            raise rg.SeriesError("stale", "DGS10 stale")
        return _fake_normalize(s, doc, now)
    assert sj.run(_spec(stale_one), get=lambda u, t: (200, "{}", {}), sleep=lambda s: None,
                  now=datetime(2026, 9, 5, tzinfo=timezone.utc)) == 1
    status, stats, error = _last_run(zz)
    assert status == "failed" and error.startswith("guard refused") and stats["tally"]["stale"] == 1
    with zz.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source='zz' AND (meta->>'refused')::bool")).scalar() == 3
        assert c.execute(sa.text("SELECT count(*) FROM macro.indicator_source WHERE source='zz'")).scalar() == 0   # không ghi gì, kể cả registry


def test_runner_keys_subset_skips_guard_and_domain_state_and_dry_run_writes_nothing(zz, monkeypatch):
    _wire(monkeypatch)
    now = datetime(2026, 9, 5, tzinfo=timezone.utc)

    def stale_one(s, doc, now):
        if s.external_key == "DGS10":
            raise rg.SeriesError("stale", "DGS10 stale")
        return _fake_normalize(s, doc, now)
    assert sj.run(_spec(stale_one), keys=["^GSPC"], get=lambda u, t: (200, "{}", {}), sleep=lambda s: None, now=now) == 0
    status, stats, _ = _last_run(zz)
    assert status == "success" and stats["subset"] is True and "watermark" not in stats and stats["bars"] == 1
    with zz.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM ops.data_domain_state WHERE source='zz'")).scalar() == 0
        assert c.execute(sa.text("SELECT count(*) FROM macro.indicator_source WHERE source='zz'")).scalar() == 1   # registry vẫn nạp trọn
    assert sj.run(_spec(), dry_run=True, get=lambda u, t: (200, "{}", {}), sleep=lambda s: None, now=now) == 0
    status, stats, _ = _last_run(zz)
    assert status == "success" and stats["dry_run"] is True
    with zz.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id) WHERE a.code='zz.idx.sp500'")).scalar() == 0


def test_runner_unknown_key_fails_before_any_call_and_ctrl_c_closes_the_run(zz, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert sj.run(_spec(), keys=["NOPE"], get=lambda u, t: (calls.append(u), (200, "{}", {}))[1], sleep=lambda s: None) == 2
    assert calls == [] and _last_run(zz)[0] == "failed"

    def boom(*a, **k):
        raise KeyboardInterrupt
    spec = _spec()
    spec.fetch_all = boom
    assert sj.run(spec, get=lambda u, t: (200, "{}", {}), sleep=lambda s: None) == 130
    assert _last_run(zz)[2] == "dừng tay (Ctrl+C)"
```

- [ ] **Bước 14: chạy đỏ** — ImportError `etl.series_job`.

- [ ] **Bước 15: viết `backend/etl/series_job.py`**

```python
"""Khuôn job chung cho 5 nguồn quốc tế (spec lát 7 §5.1) — y `wichart_job`, tham số hoá bằng `SourceSpec`."""
from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_store, series_guard, series_store
from etl.registry import SeriesError, load_registry

VN = ZoneInfo("Asia/Ho_Chi_Minh")
MAX_DETAILS = 50


@dataclass
class SourceSpec:
    job: str
    source: str
    domains: tuple[str, ...]
    guard_mode: str
    log_name: str
    build: Callable[[], list]
    fetch_all: Callable[..., tuple[dict, dict, list, int, int]]
    normalize: Callable[..., list]
    supports_backfill: bool = False


def _engine():
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        raise RuntimeError("thiếu ETL_DATABASE_URL")
    return sa.create_engine(url, pool_pre_ping=True)


def _normalize_all(spec, series, docs, failed, now):
    t = series_guard.Tally(total=len(series))
    points: list = []
    bars: list = []
    for s in series:
        if s.external_key in failed:
            t.failed += 1
            t.details.append(f"{s.external_key} failed")
            continue
        try:
            out = spec.normalize(s, docs[s.external_key], now)
            (bars if s.shape == "ohlc" else points).extend(out)
            t.ok += 1
        except SeriesError as e:
            setattr(t, e.reason, getattr(t, e.reason) + 1)
            t.details.append(f"{s.external_key} {e.reason}: {e}")
    t.details = t.details[:MAX_DETAILS]
    return points, bars, t


def run(spec: SourceSpec, keys=None, dry_run=False, backfill=False, get=None, sleep=time.sleep, now=None) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)      # URL FRED có khoá: không để httpx in request
    log = logging.getLogger(f"etl.{spec.log_name}")
    load_dotenv()
    now = now or datetime.now(timezone.utc)
    subset = keys is not None
    if backfill and not spec.supports_backfill:
        log.error("%s không có --backfill", spec.log_name)
        return 2
    try:
        engine = _engine()
    except RuntimeError as e:
        log.error("%s", e)
        return 2
    run_id = omo_store.open_run(engine, spec.job)
    try:
        registry = spec.build()
        series = registry
        if subset:
            known = {s.external_key for s in registry}
            unknown = sorted(set(keys) - known)
            if unknown:
                raise RuntimeError(f"key không có trong registry: {unknown}")
            series = [s for s in registry if s.external_key in set(keys)]
        docs, texts, failed, calls, retries = spec.fetch_all(series, get, sleep, backfill)
        points, bars, tally = _normalize_all(spec, series, docs, failed, now)
        verdict = series_guard.check(tally, spec.guard_mode) if not subset else series_guard.Verdict(ok=True)
        run_date = now.astimezone(VN).date()
        stats: dict = {"tally": vars(tally), "calls": calls, "retries": retries, "points": len(points), "bars": len(bars),
                       "run_date": run_date.isoformat()}
        for flag, on in (("subset", subset), ("dry_run", dry_run), ("backfill", backfill)):
            if on:
                stats[flag] = True
        if dry_run:
            stats["refused"] = verdict.reasons
            omo_store.close_run(engine, run_id, "success" if verdict.ok else "failed", stats,
                                error=None if verdict.ok else "guard refused (dry-run): " + "; ".join(verdict.reasons))
            log.info("%s dry-run: %s", spec.log_name, stats)
            return 0 if verdict.ok else 1
        if not verdict.ok:
            series_store.store_refusal_evidence(engine, spec.source, texts, run_id, verdict.reasons)
            omo_store.close_run(engine, run_id, "failed", stats, error="guard refused: " + "; ".join(verdict.reasons))
            log.error("%s từ chối: %s", spec.log_name, verdict.reasons)
            return 1
        with engine.begin() as conn:
            resolved, reg_stats = load_registry(conn, registry, spec.source)     # registry TRỌN, kể cả lượt con
            w1 = series_store.apply(conn, points, resolved)
            w2 = series_store.apply_ohlc(conn, bars, resolved)
        stats.update({"registry": reg_stats, "inserted": w1.inserted + w2.inserted, "changed": w1.changed + w2.changed,
                      "changes_sample": [list(map(str, c)) for c in w1.changes_sample]})
        if not subset:
            stats["watermark"] = run_date.isoformat()
        omo_store.close_run(engine, run_id, "success", stats)
        if not subset:
            series_store.upsert_domain_state(engine, spec.source, spec.domains, run_date.isoformat())
        log.info("%s xong: %s", spec.log_name, stats)
        return 0
    except KeyboardInterrupt:
        omo_store.close_run(engine, run_id, "failed", error="dừng tay (Ctrl+C)")
        log.warning("%s dừng tay (Ctrl+C)", spec.log_name)
        return 130
    except Exception as e:                    # noqa: BLE001 — job biên ngoài: mọi lỗi vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("%s thất bại", spec.log_name)
        return 2
    finally:
        engine.dispose()
```

⚠️ `changes_sample` giữ `str` (Decimal không JSON-serialisable). Test `w.changes_sample` ở `series_store` giữ Decimal — chỉ `stats` ép str.

- [ ] **Bước 16: chạy xanh** — e43 11/11; rồi cả `tests/etl` để chắc lát 6 và họ job cũ xanh.

- [ ] **Bước 17: CLI** — `backend/etl/__main__.py`, trước dòng `print(f"etl: subcommand không hợp lệ…`:

```python
    if args[0] in ("fred", "fx", "lbma", "yahoo", "binance"):
        import importlib
        mod = importlib.import_module(f"etl.{args[0]}_job")
        parser = argparse.ArgumentParser(prog=f"etl {args[0]}")
        parser.add_argument("--keys", type=lambda s: [k.strip() for k in s.split(",") if k.strip()])
        parser.add_argument("--dry-run", action="store_true", dest="dry_run")
        if args[0] in ("yahoo", "binance"):
            parser.add_argument("--backfill", action="store_true")
        parsed = parser.parse_args(args[1:])
        return mod.run(keys=parsed.keys, dry_run=parsed.dry_run, backfill=getattr(parsed, "backfill", False))
```

và cập nhật chuỗi "hỗ trợ: …" thêm `fred, fx, lbma, yahoo, binance`. Mỗi `<src>_job.py` (Task 2–6) expose `run(keys=None, dry_run=False, backfill=False, get=None, sleep=time.sleep, now=None)`.

- [ ] **Bước 18: toàn bộ test + commit** — `uv run pytest tests -q` ⇒ 650 + 11 = **661 passed, 2 skipped**. Commit: `feat(etl): shared series core (registry, store, guard, runner) extracted from wichart; slice-7 CLI stubs`.

---

### Task 2: FRED — `etl fred`

**Files:**
- Create: `backend/etl/fred_registry.py`, `backend/etl/fred_fetch.py`, `backend/etl/fred_normalize.py`, `backend/etl/fred_job.py`
- Test: `backend/tests/etl/test_e44_fred.py`
- Fixture (có sẵn): `fixtures/global/fred-DGS10-tail.json` (100 điểm desc, `"."` ở 2026-07-03 · 06-19 · 05-25, điểm đầu `2026-09-03=4.77`, `count 16873`), `fred-PAYEMS-tail.json` (`2026-08-01=159075`, `07-01=158913`, `06-01=158892`), `fred-DTWEXBGS-tail.json` (`2026-08-28=118.7479`).

**Interfaces:** Consumes Task 1 (`Series`, `Point`, `SeriesError`, `http_fetch`, `series_job.SourceSpec/run`). Produces `fred_job.run(keys=None, dry_run=False, backfill=False, get=None, sleep=time.sleep, now=None) -> int`; `fred_registry.build() -> list[Series]` (15); `fred_fetch.fetch_all(series, get, sleep, backfill)`; `fred_normalize.series_points(s, doc, now) -> list[Point]`.

- [ ] **Bước 1: test đỏ** — `backend/tests/etl/test_e44_fred.py`:

```python
"""FRED: registry 15 series, classify, normalize từ fixture thật 2026-09-05, job trọn vòng với `get` giả.
Expected là literal đọc tay từ fixture/fred.md — không tính lại theo code. Khoá KHÔNG được lộ (Bẫy 7)."""
import json
import logging
import os
import pathlib
from datetime import date, datetime, timezone
from decimal import Decimal

import httpx
import pytest
import sqlalchemy as sa

from etl import fred_fetch as ff
from etl import fred_job as fj
from etl import fred_normalize as fn
from etl import fred_registry as fr
from etl.registry import SeriesError

FIX = pathlib.Path(__file__).parent / "fixtures" / "global"
REG = {s.external_key: s for s in fr.build()}
NOW = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
KEY = "ZZTESTKEY0000000000000000000000x"


def _doc(name):
    return json.loads((FIX / f"fred-{name}-tail.json").read_text(encoding="utf-8"))


def test_registry_has_15_series_split_11_macro_4_asset_with_spec_codes():
    s = fr.build()
    assert len(s) == 15 and sum(1 for x in s if x.domain == "macro") == 11
    assert REG["DCOILWTICO"].code == "wti" and REG["DCOILWTICO"].price_type == "spot" and REG["DCOILWTICO"].max_lag_days == 10
    assert REG["DTWEXBGS"].price_type == "close" and REG["DTWEXBGS"].code == "dxy.broad" and REG["DTWEXBGS"].max_lag_days == 12
    assert REG["DEXCHUS"].price_type == "fixing" and REG["DEXCHUS"].quote_currency == "CNY" and REG["DEXCHUS"].asset_class == "fx"
    assert REG["PAYEMS"].scale == Decimal(1000) and REG["PAYEMS"].unit == "người" and REG["PAYEMS"].freq == "m"
    assert REG["DGS10"].code == "us.yield.10y" and REG["DGS10"].region == "us" and REG["DGS10"].band == (Decimal(-1), Decimal(25))
    assert all(x.source == "fred" for x in s) and len({x.code for x in s}) == 15


def test_classify_400_is_bad_shape_and_xml_body_is_bad_shape():
    assert ff.classify(400, '{"error_code":400,"error_message":"Bad Request."}') == ("bad_shape", None)
    assert ff.classify(200, "<?xml version='1.0'?><observations/>") == ("bad_shape", None)
    assert ff.classify(503, "") == ("retry", None)
    assert ff.classify(200, '{"observations": []}')[0] == "ok"
    assert ff.classify(200, '{"seriess": []}') == ("bad_shape", None)


def test_dot_values_are_skipped_and_latest_value_is_literal_from_fixture():
    pts = fn.series_points(REG["DGS10"], _doc("DGS10"), NOW)
    assert len(pts) == 97                                              # 100 − 3 điểm "."
    assert {p.obs_date for p in pts}.isdisjoint({date(2026, 7, 3), date(2026, 6, 19), date(2026, 5, 25)})
    last = max(pts, key=lambda p: p.obs_date)
    assert (last.obs_date, last.value, last.domain, last.code, last.price_type) == (date(2026, 9, 3), Decimal("4.77"), "macro", "us.yield.10y", None)


def test_payems_scales_thousands_to_persons():
    last = max(fn.series_points(REG["PAYEMS"], _doc("PAYEMS"), NOW), key=lambda p: p.obs_date)
    assert (last.obs_date, last.value) == (date(2026, 8, 1), Decimal("159075000"))


def test_freshness_gate_uses_per_series_lag():
    assert fn.series_points(REG["DTWEXBGS"], _doc("DTWEXBGS"), NOW)                       # 08-28, 8 ngày ≤ 12
    with pytest.raises(SeriesError) as e:
        fn.series_points(REG["DTWEXBGS"], _doc("DTWEXBGS"), datetime(2026, 9, 10, tzinfo=timezone.utc))   # 13 > 12
    assert e.value.reason == "stale"
    with pytest.raises(SeriesError) as e:
        fn.series_points(REG["DGS10"], _doc("DGS10"), datetime(2026, 9, 15, tzinfo=timezone.utc))
    assert e.value.reason == "stale"


def test_band_and_shape_errors():
    doc = json.loads(json.dumps(_doc("DGS10")))
    doc["observations"][0]["value"] = "477"                            # lỗi 100×
    with pytest.raises(SeriesError) as e:
        fn.series_points(REG["DGS10"], doc, NOW)
    assert e.value.reason == "band"
    with pytest.raises(SeriesError) as e:
        fn.series_points(REG["DGS10"], {"observations": []}, NOW)
    assert e.value.reason == "shape"


def test_transport_error_message_never_contains_the_api_key(monkeypatch, caplog):
    monkeypatch.setenv("FRED_API", KEY)

    def get(u, timeout):
        raise httpx.ConnectError(f"boom {u}")                          # str(e) mang URL có khoá
    with caplog.at_level(logging.WARNING):
        docs, texts, failed, calls, retries = ff.fetch_all([REG["DGS10"]], get, lambda s: None, False)
    assert failed == ["DGS10"] and calls == 4 and retries == 3
    assert KEY not in caplog.text and KEY not in "".join(texts.values())


# ---- job trọn vòng ----
MACRO_CODES = [s.code for s in fr.build() if s.domain == "macro"]
ASSET_CODES = [s.code for s in fr.build() if s.domain == "asset" and s.code != "wti"]   # wti có thể là của wichart


def _synthetic(s):
    d = NOW.date().replace(day=1) if s.freq == "m" else NOW.date()
    lo, hi = s.band
    v = (lo + hi) / 2 / s.scale
    return json.dumps({"observations": [{"date": d.isoformat(), "value": str(v)}], "count": 1})


def _fake_get(calls=None, fail=()):
    def get(u, timeout):
        sid = u.split("series_id=")[1].split("&")[0]
        if calls is not None:
            calls.append(sid)
        if sid in fail:
            return 503, "", {}
        p = FIX / f"fred-{sid}-tail.json"
        return 200, (p.read_text(encoding="utf-8") if p.exists() else _synthetic(REG[sid])), {}
    return get


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM macro.observation WHERE indicator_id IN (SELECT indicator_id FROM macro.indicator_source WHERE source='fred')"))
        c.execute(sa.text("DELETE FROM asset.price_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='fred')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='fred'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job='global.fred'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source='fred'"))
        c.execute(sa.text("DELETE FROM macro.indicator_source WHERE source='fred'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='fred'"))
        c.execute(sa.text("DELETE FROM macro.indicator WHERE code = ANY(:c)"), {"c": MACRO_CODES})
        c.execute(sa.text("DELETE FROM asset.asset WHERE code = ANY(:c)"), {"c": ASSET_CODES})


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setenv("FRED_API", KEY)
    monkeypatch.setattr("etl.series_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def _last(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job='global.fred' ORDER BY run_id DESC LIMIT 1")).one()


def test_job_writes_both_domains_and_wti_spot_beside_futures(clean):
    calls = []
    assert fj.run(get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    assert len(calls) == 15
    status, stats, _ = _last(clean)
    assert status == "success" and stats["registry"] == {"macro": 11, "asset": 4, "removed": 0}
    assert stats["tally"]["ok"] == 15 and stats["inserted"] >= 97 + 12 + 20 + 12 and stats["changed"] == 0
    assert KEY not in json.dumps(stats)
    with clean.connect() as c:
        v = c.execute(sa.text("SELECT value FROM macro.observation o JOIN macro.indicator i USING (indicator_id)"
                              " WHERE i.code='us.yield.10y' AND obs_date='2026-09-03'")).scalar()
        assert v == Decimal("4.77")
        pt = c.execute(sa.text("SELECT price_type FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                               " WHERE a.code='wti' ORDER BY obs_date DESC LIMIT 1")).scalar()
        assert pt == "spot"
        assert c.execute(sa.text("SELECT count(*) FROM asset.asset WHERE code='wti'")).scalar() == 1
        rows = dict(c.execute(sa.text("SELECT domain, watermark FROM ops.data_domain_state WHERE source='fred'")).all())
    assert rows == {"macro.indicator": "2026-09-05", "asset": "2026-09-05"}
    assert fj.run(get=_fake_get(), sleep=lambda s: None, now=NOW) == 0
    assert (_last(clean)[1]["inserted"], _last(clean)[1]["changed"]) == (0, 0)


def test_job_refuses_when_one_series_fails(clean):
    assert fj.run(get=_fake_get(fail=("UNRATE",)), sleep=lambda s: None, now=NOW) == 1
    status, stats, error = _last(clean)
    assert status == "failed" and stats["tally"]["failed"] == 1 and "tất cả hoặc không gì" in error
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM macro.indicator_source WHERE source='fred'")).scalar() == 0
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source='fred' AND (meta->>'refused')::bool")).scalar() == 14


def test_backfill_flag_is_rejected_for_fred(clean):
    assert fj.run(backfill=True, get=_fake_get(), sleep=lambda s: None, now=NOW) == 2
```

- [ ] **Bước 2: chạy đỏ** — `uv run pytest tests/etl/test_e44_fred.py -q -p no:cacheprovider` ⇒ ImportError `etl.fred_fetch`.

- [ ] **Bước 3: `backend/etl/fred_registry.py`** (Phụ lục A của spec, nguyên văn)

```python
"""Registry FRED (spec lát 7 Phụ lục A). Chủ duy nhất của ánh xạ; sự thật đo ở docs/10-sources/global/fred.md."""
from __future__ import annotations

from decimal import Decimal

from etl.registry import Series

SOURCE = "fred"


def _band(a, b):
    return (Decimal(str(a)), Decimal(str(b)))


def _m(key, code, name, unit, freq, band, lag, scale=1):
    return Series(source=SOURCE, external_key=key, domain="macro", code=code, name_vi=name, unit=unit, freq=freq,
                  scale=Decimal(scale), region="us", band=_band(*band), max_lag_days=lag)


def _a(key, code, name, cls, ccy, unit, ptype, region, band, lag):
    return Series(source=SOURCE, external_key=key, domain="asset", code=code, name_vi=name, unit=unit, freq="d",
                  region=region, asset_class=cls, quote_currency=ccy, price_type=ptype, calendar="trading_days",
                  band=_band(*band), max_lag_days=lag)


def build() -> list[Series]:
    return [
        _m("DFF", "us.rate.fedfunds.daily", "Fed funds hiệu lực (ngày)", "%", "d", (-1, 25), 6),
        _m("FEDFUNDS", "us.rate.fedfunds", "Fed funds bình quân tháng", "%", "m", (-1, 25), 60),
        _m("SOFR", "us.rate.sofr", "SOFR", "%", "d", (-1, 25), 6),
        _m("DGS2", "us.yield.2y", "Lợi suất TPCP Mỹ 2 năm", "%", "d", (-1, 25), 6),
        _m("DGS10", "us.yield.10y", "Lợi suất TPCP Mỹ 10 năm", "%", "d", (-1, 25), 6),
        _m("T10Y2Y", "us.yield.spread_10y2y", "Chênh lợi suất 10 năm − 2 năm", "%", "d", (-5, 5), 6),
        _m("T10YIE", "us.breakeven.10y", "Lạm phát hoà vốn 10 năm", "%", "d", (-5, 15), 6),
        _m("CPIAUCSL", "us.cpi", "CPI Mỹ (SA, 1982–84 = 100)", "chỉ số (1982-84=100)", "m", (100, 1000), 60),
        _m("PCEPILFE", "us.pce.core", "PCE lõi (2017 = 100)", "chỉ số (2017=100)", "m", (50, 500), 90),
        _m("UNRATE", "us.unemployment", "Tỷ lệ thất nghiệp Mỹ", "%", "m", (0, 30), 60),
        _m("PAYEMS", "us.payrolls", "Việc làm phi nông nghiệp", "người", "m", (1e8, 3e8), 60, scale=1000),
        _a("DCOILWTICO", "wti", "Giá dầu WTI", "commodity", "USD", "USD/thùng", "spot", "us", (5, 500), 10),
        _a("DTWEXBGS", "dxy.broad", "Chỉ số đô Mỹ broad (Fed, 01/2006 = 100)", "index", "USD", "điểm", "close", "us", (50, 200), 12),
        _a("VIXCLS", "vix", "VIX", "index", "USD", "điểm", "close", "us", (5, 150), 6),
        _a("DEXCHUS", "fx.usd_cny", "Tỷ giá CNY/USD (Fed H.10, noon NY)", "fx", "CNY", "CNY/1 USD", "fixing", "cn", (3, 15), 12),
    ]
```

- [ ] **Bước 4: `backend/etl/fred_fetch.py`**

```python
"""Tải một series FRED (spec lát 7 §5.2). Khoá đi trong URL ⇒ MỌI chuỗi ra log/stats đi qua `redact`."""
from __future__ import annotations

import json
import logging
import os

from etl.http_fetch import BadShape, FetchError, open_fetcher

log = logging.getLogger("etl.fred")
BASE = "https://api.stlouisfed.org/fred/series/observations"
MIN_INTERVAL = 0.5


def url(series_id: str, key: str) -> str:
    return f"{BASE}?series_id={series_id}&api_key={key}&file_type=json"


def redact(text: str, key: str) -> str:
    return text.replace(key, "<REDACTED>") if key else text


def classify(http: int, text: str):
    """('ok', doc) | ('retry', None) | ('bad_shape', None). 400 = tham số/khoá sai — FRED trả lỗi rõ, thử lại vô ích."""
    if http == 400:
        return "bad_shape", None
    if http != 200:
        return "retry", None
    if text.lstrip().startswith("<"):                       # Bẫy 3: quên file_type=json ⇒ XML kèm 200
        return "bad_shape", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    if not isinstance(d, dict) or not isinstance(d.get("observations"), list):
        return "bad_shape", None
    return "ok", d


def fetch_all(series, get, sleep, backfill):
    key = os.environ.get("FRED_API")
    if not key:
        raise RuntimeError("thiếu FRED_API")
    docs, texts, failed = {}, {}, []
    with open_fetcher(classify, get=get, sleep=sleep, min_interval=MIN_INTERVAL) as f:
        for s in series:
            try:
                docs[s.external_key], texts[s.external_key] = f.fetch_one(url(s.external_key, key), s.external_key)
            except (BadShape, FetchError) as e:
                failed.append(s.external_key)
                log.warning("%s", redact(str(e), key))
        return docs, texts, failed, f.calls, f.retries_done
```

- [ ] **Bước 5: `backend/etl/fred_normalize.py`**

```python
"""Chuẩn hoá một series FRED (spec lát 7 §5.3). Thuần. `"."` = thiếu ⇒ không dòng (bước 4 schema)."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from etl.registry import Point, SeriesError


def series_points(s, doc, now) -> list[Point]:
    obs = doc.get("observations") if isinstance(doc, dict) else None
    if not isinstance(obs, list) or not obs:
        raise SeriesError("shape", f"{s.external_key}: không có observations")
    pts: list[Point] = []
    for o in obs:
        v = o.get("value")
        if v is None or v == ".":
            continue
        try:
            pts.append(Point(s.domain, s.code, date.fromisoformat(o["date"]), Decimal(v) * s.scale, s.price_type))
        except (KeyError, ValueError, InvalidOperation) as e:
            raise SeriesError("shape", f"{s.external_key}: điểm hỏng {o!r}") from e
    if not pts:
        raise SeriesError("shape", f"{s.external_key}: mọi điểm đều '.'")
    latest = max(pts, key=lambda p: p.obs_date)
    if latest.obs_date < now.date() - timedelta(days=s.max_lag_days):
        raise SeriesError("stale", f"{s.external_key}: điểm cuối {latest.obs_date} quá {s.max_lag_days} ngày")
    lo, hi = s.band
    if not (lo <= latest.value <= hi):
        raise SeriesError("band", f"{s.external_key}: {latest.value} ngoài dải ({lo}, {hi})")
    return pts
```

- [ ] **Bước 6: `backend/etl/fred_job.py`**

```python
"""`python -m etl fred` — 15 series → macro.observation (11) + asset.price_daily (4). Spec lát 7."""
from __future__ import annotations

import time

from etl import fred_fetch, fred_normalize, fred_registry, series_job

SPEC = series_job.SourceSpec(job="global.fred", source=fred_registry.SOURCE, domains=("macro.indicator", "asset"),
                             guard_mode="all_or_nothing", log_name="fred", build=fred_registry.build,
                             fetch_all=fred_fetch.fetch_all, normalize=fred_normalize.series_points)


def run(keys=None, dry_run=False, backfill=False, get=None, sleep=time.sleep, now=None) -> int:
    return series_job.run(SPEC, keys=keys, dry_run=dry_run, backfill=backfill, get=get, sleep=sleep, now=now)
```

- [ ] **Bước 7: chạy xanh** — e44 11/11. Kiểm nhanh `uv run python -m etl fred --help` in được. **Không commit** (controller commit).

---

### Task 3: ECB qua Frankfurter — `etl fx`

**Files:** Create `backend/etl/fx_registry.py`, `fx_fetch.py`, `fx_normalize.py`, `fx_job.py`; Test `backend/tests/etl/test_e45_fx.py`; Fixture `fixtures/global/ecb-2026-08.json` (`start_date 2026-07-31`, `end_date 2026-08-31`, 22 ngày, `rates["2026-08-14"] = {CAD 1.3875, CHF 0.81179, EUR 0.86453, GBP 0.73874, JPY 159.01, SEK 9.5089}`).

**Interfaces:** như Task 2 với tiền tố `fx_`; `fx_fetch.fetch_all` gọi **một** URL và trả cùng doc cho cả 6 `external_key` (`EUR` … `CHF`), `texts` một khoá `"all"`; nếu lời gọi hỏng thì `failed` = cả 6 khoá.

- [ ] **Bước 1: test đỏ** — `backend/tests/etl/test_e45_fx.py`:

```python
"""ECB/Frankfurter: 6 cặp từ một lời gọi; literal từ fixture 2026-09-05 và fx.md."""
import json
import os
import pathlib
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import fx_fetch as xf
from etl import fx_job as xj
from etl import fx_normalize as xn
from etl import fx_registry as xr
from etl.registry import SeriesError

FIX = pathlib.Path(__file__).parent / "fixtures" / "global"
DOC = json.loads((FIX / "ecb-2026-08.json").read_text(encoding="utf-8"))
REG = {s.external_key: s for s in xr.build()}
NOW = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)            # fixture kết thúc 08-31: trễ 3 ngày ≤ 6


def test_registry_six_fx_assets_fixing():
    s = xr.build()
    assert [x.external_key for x in s] == ["EUR", "JPY", "GBP", "CAD", "SEK", "CHF"]
    assert all(x.asset_class == "fx" and x.price_type == "fixing" and x.source == "ecb" and x.region == "eu" for x in s)
    assert REG["EUR"].code == "fx.usd_eur" and REG["EUR"].quote_currency == "EUR" and REG["EUR"].unit == "EUR/1 USD"


def test_url_is_the_new_host_with_six_quotes():
    assert xf.URL == "https://api.frankfurter.dev/v1/1999-01-04..?from=USD&to=EUR,JPY,GBP,CAD,SEK,CHF"


def test_classify():
    assert xf.classify(200, json.dumps(DOC))[0] == "ok"
    assert xf.classify(200, '{"base":"EUR","rates":{}}') == ("bad_shape", None)      # base phải là USD
    assert xf.classify(301, "<html>") == ("retry", None)
    assert xf.classify(200, "{") == ("retry", None)


def test_eur_point_matches_fx_md_literal_and_direction_is_quote_per_usd():
    pts = xn.series_points(REG["EUR"], DOC, NOW)
    assert len(pts) == 22
    p = next(x for x in pts if x.obs_date == date(2026, 8, 14))
    assert (p.value, p.price_type, p.code, p.domain) == (Decimal("0.86453"), "fixing", "fx.usd_eur", "asset")
    assert next(x for x in xn.series_points(REG["JPY"], DOC, NOW) if x.obs_date == date(2026, 8, 14)).value == Decimal("159.01")


def test_missing_currency_on_last_day_is_shape_and_old_data_is_stale():
    doc = json.loads(json.dumps(DOC))
    del doc["rates"]["2026-08-31"]["SEK"]
    with pytest.raises(SeriesError) as e:
        xn.series_points(REG["SEK"], doc, NOW)
    assert e.value.reason == "shape"
    with pytest.raises(SeriesError) as e:
        xn.series_points(REG["EUR"], DOC, datetime(2026, 9, 10, tzinfo=timezone.utc))
    assert e.value.reason == "stale"


CODES = [s.code for s in xr.build()]


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM asset.price_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='ecb')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='ecb'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job='global.ecb'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source='ecb'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='ecb'"))
        c.execute(sa.text("DELETE FROM asset.asset WHERE code = ANY(:c)"), {"c": CODES})


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.series_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def test_job_one_call_writes_132_fixing_rows(clean):
    calls = []
    assert xj.run(get=lambda u, t: (calls.append(u), (200, json.dumps(DOC), {}))[1], sleep=lambda s: None, now=NOW) == 0
    assert calls == [xf.URL]
    with clean.connect() as c:
        status, stats = c.execute(sa.text("SELECT status, stats FROM ops.etl_run WHERE job='global.ecb' ORDER BY run_id DESC LIMIT 1")).one()
        assert status == "success" and stats["registry"] == {"macro": 0, "asset": 6, "removed": 0} and stats["inserted"] == 132
        assert c.execute(sa.text("SELECT value FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                                 " WHERE a.code='fx.usd_chf' AND obs_date='2026-08-14' AND price_type='fixing'")).scalar() == Decimal("0.81179")
        assert dict(c.execute(sa.text("SELECT domain, watermark FROM ops.data_domain_state WHERE source='ecb'")).all()) == {"asset": "2026-09-03"}


def test_job_refuses_when_the_single_call_fails(clean):
    assert xj.run(get=lambda u, t: (503, "", {}), sleep=lambda s: None, now=NOW) == 1
    with clean.connect() as c:
        stats = c.execute(sa.text("SELECT stats FROM ops.etl_run WHERE job='global.ecb' ORDER BY run_id DESC LIMIT 1")).scalar()
        assert stats["tally"]["failed"] == 6 and stats["calls"] == 4
```

- [ ] **Bước 2: chạy đỏ** — ImportError.

- [ ] **Bước 3: `fx_registry.py`**

```python
"""Registry ECB qua Frankfurter (spec lát 7 Phụ lục B). source='ecb' là danh tính dữ liệu, không phải tên API."""
from __future__ import annotations

from decimal import Decimal

from etl.registry import Series

SOURCE = "ecb"
_ROWS = [("EUR", "fx.usd_eur", "Tỷ giá EUR/USD (fixing ECB 14:15 CET)", "0.5", "2"),
         ("JPY", "fx.usd_jpy", "Tỷ giá JPY/USD (fixing ECB)", "50", "400"),
         ("GBP", "fx.usd_gbp", "Tỷ giá GBP/USD (fixing ECB)", "0.4", "1.5"),
         ("CAD", "fx.usd_cad", "Tỷ giá CAD/USD (fixing ECB)", "0.8", "2.5"),
         ("SEK", "fx.usd_sek", "Tỷ giá SEK/USD (fixing ECB)", "4", "20"),
         ("CHF", "fx.usd_chf", "Tỷ giá CHF/USD (fixing ECB)", "0.5", "2")]


def build() -> list[Series]:
    return [Series(source=SOURCE, external_key=ccy, domain="asset", code=code, name_vi=name, unit=f"{ccy}/1 USD", freq="d",
                   region="eu", asset_class="fx", quote_currency=ccy, price_type="fixing", calendar="trading_days",
                   band=(Decimal(lo), Decimal(hi)), max_lag_days=6) for ccy, code, name, lo, hi in _ROWS]
```

- [ ] **Bước 4: `fx_fetch.py`**

```python
"""Một lời gọi Frankfurter cho trọn chuỗi 6 cặp (spec lát 7 §5.2). Host mới đo 2026-09-05 (host cũ trả 301)."""
from __future__ import annotations

import json
import logging

from etl.http_fetch import BadShape, FetchError, open_fetcher

log = logging.getLogger("etl.fx")
PAIRS = "EUR,JPY,GBP,CAD,SEK,CHF"
URL = f"https://api.frankfurter.dev/v1/1999-01-04..?from=USD&to={PAIRS}"


def classify(http: int, text: str):
    if http != 200:
        return "retry", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    if not isinstance(d, dict) or d.get("base") != "USD" or not isinstance(d.get("rates"), dict):
        return "bad_shape", None
    return "ok", d


def fetch_all(series, get, sleep, backfill):
    keys = [s.external_key for s in series]
    with open_fetcher(classify, get=get, sleep=sleep, timeout=60.0) as f:
        try:
            doc, text = f.fetch_one(URL, "frankfurter")
        except (BadShape, FetchError) as e:
            log.warning("%s", e)
            return {}, {"all": ""}, keys, f.calls, f.retries_done
        return {k: doc for k in keys}, {"all": text}, [], f.calls, f.retries_done
```

- [ ] **Bước 5: `fx_normalize.py`**

```python
"""Một cặp từ document `rates` (spec lát 7 §5.3). Giá trị = số quote trên 1 USD, đúng chiều Frankfurter."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from etl.registry import Point, SeriesError


def series_points(s, doc, now) -> list[Point]:
    rates = doc.get("rates") if isinstance(doc, dict) else None
    if not isinstance(rates, dict) or not rates:
        raise SeriesError("shape", f"{s.external_key}: không có rates")
    days = sorted(rates)
    if s.external_key not in rates[days[-1]]:
        raise SeriesError("shape", f"{s.external_key}: thiếu ở ngày cuối {days[-1]}")
    pts = [Point("asset", s.code, date.fromisoformat(d), Decimal(str(rates[d][s.external_key])), s.price_type)
           for d in days if s.external_key in rates[d]]
    if date.fromisoformat(days[-1]) < now.date() - timedelta(days=s.max_lag_days):
        raise SeriesError("stale", f"{s.external_key}: ngày cuối {days[-1]} quá {s.max_lag_days} ngày")
    lo, hi = s.band
    if not (lo <= pts[-1].value <= hi):
        raise SeriesError("band", f"{s.external_key}: {pts[-1].value} ngoài dải ({lo}, {hi})")
    return pts
```

- [ ] **Bước 6: `fx_job.py`** — y `fred_job.py` với `job="global.ecb"`, `source=fx_registry.SOURCE`, `domains=("asset",)`, `guard_mode="all_or_nothing"`, `log_name="fx"`, `build=fx_registry.build`, `fetch_all=fx_fetch.fetch_all`, `normalize=fx_normalize.series_points`; hàm `run` cùng chữ ký.

- [ ] **Bước 7: chạy xanh** — e45 7/7.

---

### Task 4: LBMA — `etl lbma`

**Files:** Create `backend/etl/lbma_registry.py`, `lbma_fetch.py`, `lbma_normalize.py`, `lbma_job.py`; Test `backend/tests/etl/test_e46_lbma.py`; Fixture `fixtures/global/lbma-gold_pm-trimmed.json` (32 dòng: 2 dòng 1968 có `v[2] = null`, 30 dòng cuối tới `2026-09-04 v=[4415.4, 3269.16, 3803.43]`), `lbma-silver-trimmed.json` (`2026-09-04 v=[66.835, 49.39, 57.51]`).

**Interfaces:** như Task 2 với tiền tố `lbma_`; `external_key` = `gold_pm` | `silver`, `external_sub` = `"0"` (vị trí USD trong `v`).

- [ ] **Bước 1: test đỏ** — `backend/tests/etl/test_e46_lbma.py`:

```python
"""LBMA: mảng {d, v:[USD, GBP, EUR]} đo 2026-09-05; chỉ USD (v[0]) vào kho."""
import json
import os
import pathlib
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import lbma_fetch as lf
from etl import lbma_job as lj
from etl import lbma_normalize as ln
from etl import lbma_registry as lr
from etl.registry import SeriesError

FIX = pathlib.Path(__file__).parent / "fixtures" / "global"
GOLD = json.loads((FIX / "lbma-gold_pm-trimmed.json").read_text(encoding="utf-8"))
SILVER = json.loads((FIX / "lbma-silver-trimmed.json").read_text(encoding="utf-8"))
REG = {s.external_key: s for s in lr.build()}
NOW = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def test_registry_two_usd_fixings():
    s = lr.build()
    assert [(x.external_key, x.external_sub, x.code) for x in s] == [("gold_pm", "0", "gold.lbma"), ("silver", "0", "silver.lbma")]
    assert all(x.price_type == "fixing" and x.unit == "USD/oz" and x.quote_currency == "USD" and x.source == "lbma" for x in s)


def test_url_and_classify():
    assert lf.url("gold_pm") == "https://prices.lbma.org.uk/json/gold_pm.json"
    assert lf.classify(200, json.dumps(GOLD))[0] == "ok"
    assert lf.classify(200, '{"d": "x"}') == ("bad_shape", None)
    assert lf.classify(200, "[]") == ("bad_shape", None)
    assert lf.classify(502, "") == ("retry", None)


def test_usd_column_only_and_null_rows_skipped():
    pts = ln.series_points(REG["gold_pm"], GOLD, NOW)
    assert len(pts) == 32 and pts[0].obs_date == date(1968, 4, 1) and pts[0].value == Decimal("37.7")
    last = pts[-1]
    assert (last.obs_date, last.value, last.code, last.price_type) == (date(2026, 9, 4), Decimal("4415.4"), "gold.lbma", "fixing")
    assert ln.series_points(REG["silver"], SILVER, NOW)[-1].value == Decimal("66.835")
    doc = json.loads(json.dumps(GOLD))
    doc[-1]["v"][0] = None                                          # USD null ở ngày cuối ⇒ không dòng, ngày cuối lùi
    assert ln.series_points(REG["gold_pm"], doc, NOW)[-1].obs_date == date(2026, 9, 3)


def test_shape_stale_band():
    doc = json.loads(json.dumps(GOLD))
    doc[-1]["v"] = [4415.4, 3269.16]
    with pytest.raises(SeriesError) as e:
        ln.series_points(REG["gold_pm"], doc, NOW)
    assert e.value.reason == "shape"
    with pytest.raises(SeriesError) as e:
        ln.series_points(REG["gold_pm"], GOLD, datetime(2026, 9, 12, tzinfo=timezone.utc))
    assert e.value.reason == "stale"
    doc = json.loads(json.dumps(GOLD))
    doc[-1]["v"][0] = 44154.0
    with pytest.raises(SeriesError) as e:
        ln.series_points(REG["gold_pm"], doc, NOW)
    assert e.value.reason == "band"


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM asset.price_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='lbma')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='lbma'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job='global.lbma'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source='lbma'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='lbma'"))
        c.execute(sa.text("DELETE FROM asset.asset WHERE code IN ('gold.lbma','silver.lbma')"))


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.series_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def _get(u, t):
    name = u.rsplit("/", 1)[1].removesuffix(".json")
    return 200, json.dumps(GOLD if name == "gold_pm" else SILVER), {}


def test_job_two_calls_64_rows(clean):
    assert lj.run(get=_get, sleep=lambda s: None, now=NOW) == 0
    with clean.connect() as c:
        stats = c.execute(sa.text("SELECT stats FROM ops.etl_run WHERE job='global.lbma' ORDER BY run_id DESC LIMIT 1")).scalar()
        assert stats["calls"] == 2 and stats["inserted"] == 64 and stats["registry"]["asset"] == 2
        assert c.execute(sa.text("SELECT value FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                                 " WHERE a.code='silver.lbma' AND obs_date='2026-09-04'")).scalar() == Decimal("66.835")
    assert lj.run(get=_get, sleep=lambda s: None, now=NOW) == 0
```

- [ ] **Bước 2: chạy đỏ.**

- [ ] **Bước 3: `lbma_registry.py`**

```python
"""Registry LBMA (spec lát 7 Phụ lục C): chỉ cột USD (v[0]); GBP/EUR loại có chủ đích."""
from __future__ import annotations

from decimal import Decimal

from etl.registry import Series

SOURCE = "lbma"


def build() -> list[Series]:
    rows = [("gold_pm", "gold.lbma", "Vàng LBMA fixing PM (15:00 London)", "100", "20000"),
            ("silver", "silver.lbma", "Bạc LBMA fixing (12:00 London)", "1", "500")]
    return [Series(source=SOURCE, external_key=k, external_sub="0", domain="asset", code=code, name_vi=name, unit="USD/oz",
                   freq="d", region="global", asset_class="commodity", quote_currency="USD", price_type="fixing",
                   calendar="trading_days", band=(Decimal(lo), Decimal(hi)), max_lag_days=6) for k, code, name, lo, hi in rows]
```

- [ ] **Bước 4: `lbma_fetch.py`**

```python
"""Hai file JSON trọn lịch sử LBMA (~900 KB mỗi file, không lọc được ở nguồn — commodities.md Bẫy 2)."""
from __future__ import annotations

import json
import logging

from etl.http_fetch import BadShape, FetchError, open_fetcher

log = logging.getLogger("etl.lbma")
BASE = "https://prices.lbma.org.uk/json"
MIN_INTERVAL = 1.0


def url(name: str) -> str:
    return f"{BASE}/{name}.json"


def classify(http: int, text: str):
    if http != 200:
        return "retry", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    if not isinstance(d, list) or not d or not all(isinstance(r, dict) and "d" in r and "v" in r for r in d[:3] + d[-3:]):
        return "bad_shape", None
    return "ok", d


def fetch_all(series, get, sleep, backfill):
    docs, texts, failed = {}, {}, []
    with open_fetcher(classify, get=get, sleep=sleep, min_interval=MIN_INTERVAL, timeout=60.0) as f:
        for s in series:
            try:
                docs[s.external_key], texts[s.external_key] = f.fetch_one(url(s.external_key), s.external_key)
            except (BadShape, FetchError) as e:
                failed.append(s.external_key)
                log.warning("%s", e)
        return docs, texts, failed, f.calls, f.retries_done
```

- [ ] **Bước 5: `lbma_normalize.py`**

```python
"""Một cột tiền tệ (theo `external_sub`) từ mảng {d, v:[USD, GBP, EUR]} — đo 2026-09-05. `null` = tiền tệ chưa có."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from etl.registry import Point, SeriesError


def series_points(s, doc, now) -> list[Point]:
    idx = int(s.external_sub)
    pts: list[Point] = []
    prev: date | None = None
    for row in doc:
        v = row.get("v")
        if not isinstance(v, list) or len(v) != 3:
            raise SeriesError("shape", f"{s.external_key}: v không phải mảng 3 phần tử tại {row.get('d')}")
        d = date.fromisoformat(row["d"])
        if prev is not None and d <= prev:
            raise SeriesError("shape", f"{s.external_key}: ngày không tăng tại {d}")
        prev = d
        if v[idx] is None:
            continue
        pts.append(Point("asset", s.code, d, Decimal(str(v[idx])), s.price_type))
    if not pts:
        raise SeriesError("shape", f"{s.external_key}: không có điểm")
    if pts[-1].obs_date < now.date() - timedelta(days=s.max_lag_days):
        raise SeriesError("stale", f"{s.external_key}: điểm cuối {pts[-1].obs_date} quá {s.max_lag_days} ngày")
    lo, hi = s.band
    if not (lo <= pts[-1].value <= hi):
        raise SeriesError("band", f"{s.external_key}: {pts[-1].value} ngoài dải ({lo}, {hi})")
    return pts
```

- [ ] **Bước 6: `lbma_job.py`** — y `fred_job.py` với `job="global.lbma"`, `source=lbma_registry.SOURCE`, `domains=("asset",)`, `guard_mode="all_or_nothing"`, `log_name="lbma"`.

- [ ] **Bước 7: chạy xanh** — e46 5/5.

---

### Task 5: Yahoo — `etl yahoo` (37 chỉ số → `ohlc_daily`, có `--backfill`)

**Files:** Create `backend/etl/yahoo_registry.py`, `yahoo_fetch.py`, `yahoo_normalize.py`, `yahoo_job.py`; Test `backend/tests/etl/test_e47_yahoo.py`; Fixture `fixtures/global/yahoo-GSPC-10d.json` (8 nến 13:30 UTC, cuối 2026-09-04 close `7718.60009765625` open `7750.18994140625` volume `4103570000`, `regularMarketTime` 2026-09-04 20:33 UTC, `currentTradingPeriod.regular` 13:30→20:00 UTC, `instrumentType INDEX`, currency `USD`, tz `America/New_York`), `yahoo-N225-10d.json` (nến 00:00 UTC, tz `Asia/Tokyo`, close cuối `65020.94140625`), `yahoo-DXY-10d.json` (9 nến 04:00 UTC, **1 nến close null**, cuối 2026-09-04 close `99.16000366210938`, `regular.end` 2026-09-05 03:59 UTC), `yahoo-TIO=F-40d.json` (`instrumentType ALTSYMBOL`), `yahoo-BCOM-40d.json` (0 nến, `regularMarketTime` 2020-05-28), `yahoo-MERV-10d.json` (`currency ""`, close cuối `3049122.0`).

**Interfaces:** như Task 2 với tiền tố `yahoo_`; `yahoo_normalize.bars(s, doc, now) -> list[Bar]`; `yahoo_fetch.fetch_all(series, get, sleep, backfill)` — `backfill=True` dùng `period1 = -2208988800`, ngược lại `period2 − 400 ngày`; `SourceSpec.supports_backfill=True`, `guard_mode="ratio"`.

- [ ] **Bước 1: test đỏ** — `backend/tests/etl/test_e47_yahoo.py`:

```python
"""Yahoo: 37 chỉ số, ba cổng (granularity · instrumentType · độ tươi), múi giờ sàn, nến chưa đóng — fixture 2026-09-05."""
import json
import os
import pathlib
import urllib.parse
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import yahoo_fetch as yf
from etl import yahoo_job as yj
from etl import yahoo_normalize as yn
from etl import yahoo_registry as yr
from etl.registry import SeriesError

FIX = pathlib.Path(__file__).parent / "fixtures" / "global"
REG = {s.external_key: s for s in yr.build()}
NOW = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def _doc(name):
    return json.loads((FIX / f"yahoo-{name}.json").read_text(encoding="utf-8"))


def test_registry_37_indices_all_ohlc():
    s = yr.build()
    assert len(s) == 37 and all(x.shape == "ohlc" and x.asset_class == "index" and x.price_type is None and x.source == "yahoo"
                                and x.unit == "điểm" and x.calendar == "trading_days" and x.max_lag_days == 14 for x in s)
    assert REG["^GSPC"].code == "idx.sp500" and REG["DX-Y.NYB"].code == "dxy.ice" and REG["^KS11"].code == "idx.kospi"
    assert REG["^N225"].quote_currency == "JPY" and REG["^MERV"].quote_currency == "ARS" and REG["^GSPC"].band == (Decimal(700), Decimal(80000))
    assert len({x.code for x in s}) == 37


def test_url_uses_period_not_range_and_backfill_period1_is_negative():
    assert yf.url("^GSPC", -2208988800, 1000) == "https://query1.finance.yahoo.com/v8/finance/chart/^GSPC?period1=-2208988800&period2=1000&interval=1d"
    assert yf.BACKFILL_PERIOD1 == -2208988800 and yf.DAILY_WINDOW_DAYS == 400


def test_classify():
    assert yf.classify(200, json.dumps(_doc("GSPC-10d")))[0] == "ok"
    assert yf.classify(200, '{"chart":{"result":null,"error":{"code":"Not Found"}}}') == ("bad_shape", None)
    assert yf.classify(404, "") == ("retry", None)                      # Luật 3: 404 nói về tổ hợp tham số
    assert yf.classify(200, "not json") == ("retry", None)


def test_gspc_bars_are_dated_in_new_york_and_carry_literal_close_open_volume():
    bars = yn.bars(REG["^GSPC"], _doc("GSPC-10d"), NOW)
    assert len(bars) == 8 and bars[0].obs_date == date(2026, 8, 26)
    b = bars[-1]
    assert (b.obs_date, b.close, b.open, b.volume, b.close_adj, b.code) == (
        date(2026, 9, 4), Decimal("7718.60009765625"), Decimal("7750.18994140625"), Decimal("4103570000"), Decimal("7718.60009765625"), "idx.sp500")


def test_exchange_timezone_decides_the_date_for_tokyo_and_ice():
    assert yn.bars(REG["^N225"], _doc("N225-10d"), NOW)[-1].obs_date == date(2026, 9, 4)          # 00:00 UTC = 09:00 Tokyo
    dxy = yn.bars(REG["DX-Y.NYB"], _doc("DXY-10d"), NOW)
    assert len(dxy) == 8 and dxy[-1].obs_date == date(2026, 9, 4) and dxy[-1].close == Decimal("99.16000366210938")   # 9 nến − 1 null


def test_open_candle_is_dropped_while_the_regular_session_is_still_running():
    during = datetime(2026, 9, 4, 15, 0, tzinfo=timezone.utc)                          # trong phiên NY (13:30–20:00)
    bars = yn.bars(REG["^GSPC"], _doc("GSPC-10d"), during)
    assert len(bars) == 7 and bars[-1].obs_date == date(2026, 9, 3)
    early = datetime(2026, 9, 5, 2, 0, tzinfo=timezone.utc)                            # DXY regular.end = 03:59 UTC 09-05
    assert yn.bars(REG["DX-Y.NYB"], _doc("DXY-10d"), early)[-1].obs_date == date(2026, 9, 3)


def test_three_gates_altsymbol_stale_granularity_and_currency():
    with pytest.raises(SeriesError) as e:
        yn.bars(REG["^GSPC"], _doc("TIO=F-40d"), NOW)
    assert e.value.reason == "shape" and "ALTSYMBOL" in str(e.value)
    with pytest.raises(SeriesError) as e:
        yn.bars(REG["^GSPC"], _doc("BCOM-40d"), NOW)
    assert e.value.reason == "stale"
    doc = json.loads(json.dumps(_doc("GSPC-10d")))
    doc["chart"]["result"][0]["meta"]["dataGranularity"] = "1mo"
    with pytest.raises(SeriesError) as e:
        yn.bars(REG["^GSPC"], doc, NOW)
    assert e.value.reason == "shape"
    doc = json.loads(json.dumps(_doc("GSPC-10d")))
    doc["chart"]["result"][0]["meta"]["currency"] = "EUR"
    with pytest.raises(SeriesError) as e:
        yn.bars(REG["^GSPC"], doc, NOW)
    assert e.value.reason == "shape"
    assert yn.bars(REG["^MERV"], _doc("MERV-10d"), NOW)[-1].close == Decimal("3049122.0")   # currency rỗng ⇒ qua


def test_band_catches_100x_error():
    doc = json.loads(json.dumps(_doc("GSPC-10d")))
    q = doc["chart"]["result"][0]["indicators"]["quote"][0]
    q["close"] = [c * 100 if c else c for c in q["close"]]
    with pytest.raises(SeriesError) as e:
        yn.bars(REG["^GSPC"], doc, NOW)
    assert e.value.reason == "band"


# ---- job ----
CODES = [s.code for s in yr.build()]
FIXTURE_OF = {"^GSPC": "GSPC-10d", "^N225": "N225-10d", "DX-Y.NYB": "DXY-10d", "^MERV": "MERV-10d"}


def _synthetic(sym):
    doc = _doc("GSPC-10d")
    res = doc["chart"]["result"][0]
    s = REG[sym]
    v = float(s.band[0] * 10)
    res["meta"].update(symbol=sym, currency=s.quote_currency)
    q = res["indicators"]["quote"][0]
    for k in ("open", "high", "low", "close"):
        q[k] = [v] * len(q[k])
    res["indicators"]["adjclose"][0]["adjclose"] = [v] * len(q["close"])
    return json.dumps(doc)


def _fake_get(calls=None, dead=(), stale=()):
    def get(u, timeout):
        sym = urllib.parse.unquote(u.split("/chart/")[1].split("?")[0])
        if calls is not None:
            calls.append(u)
        if sym in dead:
            return 200, json.dumps(_doc("TIO=F-40d")), {}
        if sym in stale:
            return 200, json.dumps(_doc("BCOM-40d")), {}
        return 200, (json.dumps(_doc(FIXTURE_OF[sym])) if sym in FIXTURE_OF else _synthetic(sym)), {}
    return get


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM asset.ohlc_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='yahoo')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='yahoo'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job='global.yahoo'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source='yahoo'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='yahoo'"))
        c.execute(sa.text("DELETE FROM asset.asset WHERE code = ANY(:c)"), {"c": CODES})


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.series_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def _last(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job='global.yahoo' ORDER BY run_id DESC LIMIT 1")).one()


def test_job_writes_296_bars_and_is_idempotent(clean):
    calls = []
    assert yj.run(get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    assert len(calls) == 37 and all("period1=" in u and "range=" not in u for u in calls)
    status, stats, _ = _last(clean)
    assert status == "success" and stats["tally"]["ok"] == 37 and stats["bars"] == 296 and stats["inserted"] == 296
    with clean.connect() as c:
        row = c.execute(sa.text("SELECT close, volume FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id)"
                                " WHERE a.code='idx.sp500' AND obs_date='2026-09-04'")).one()
        assert tuple(row) == (Decimal("7718.60009765625"), Decimal("4103570000"))
        assert c.execute(sa.text("SELECT price_type FROM asset.asset_external_id WHERE source='yahoo' AND external_code='^GSPC'")).scalar() is None
        assert dict(c.execute(sa.text("SELECT domain, watermark FROM ops.data_domain_state WHERE source='yahoo'")).all()) == {"asset": "2026-09-05"}
    assert yj.run(get=_fake_get(), sleep=lambda s: None, now=NOW) == 0
    assert (_last(clean)[1]["inserted"], _last(clean)[1]["changed"]) == (0, 0)


def test_backfill_uses_negative_period1(clean):
    calls = []
    assert yj.run(backfill=True, keys=["^GSPC"], get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    assert len(calls) == 1 and "period1=-2208988800" in calls[0]


def test_ratio_guard_refuses_three_dead_symbols_but_tolerates_one(clean):
    assert yj.run(get=_fake_get(dead=("^AEX", "^BFX", "^OMX")), sleep=lambda s: None, now=NOW) == 1      # 8,1 % > 5 %
    status, stats, error = _last(clean)
    assert status == "failed" and stats["tally"]["shape"] == 3 and "sai hình dạng" in error
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM asset.asset_external_id WHERE source='yahoo'")).scalar() == 0
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source='yahoo' AND (meta->>'refused')::bool")).scalar() == 37
    assert yj.run(get=_fake_get(dead=("^AEX",)), sleep=lambda s: None, now=NOW) == 0                      # 2,7 %: bỏ series đó
    status, stats, _ = _last(clean)
    assert status == "success" and stats["tally"]["shape"] == 1 and stats["bars"] == 288
```

- [ ] **Bước 2: chạy đỏ.**

- [ ] **Bước 3: `yahoo_registry.py`** (Phụ lục D; `band` = (đo ÷ 10, đo × 10) làm tròn)

```python
"""Registry Yahoo (spec lát 7 Phụ lục D): 36 chỉ số + DXY ICE → asset.ohlc_daily. quote_currency chép từ meta.currency đo 2026-09-05."""
from __future__ import annotations

from decimal import Decimal

from etl.registry import Series

SOURCE = "yahoo"
# (symbol, code, name_vi, ccy, region, band_lo, band_hi)
_ROWS = [
    ("^GSPC", "idx.sp500", "S&P 500", "USD", "us", 700, 80000),
    ("^IXIC", "idx.nasdaq", "NASDAQ Composite", "USD", "us", 2500, 270000),
    ("^DJI", "idx.dow", "Dow Jones Industrial", "USD", "us", 5000, 540000),
    ("^RUT", "idx.russell2000", "Russell 2000", "USD", "us", 290, 30000),
    ("^GSPTSE", "idx.tsx", "S&P/TSX Composite", "CAD", "ca", 3600, 370000),
    ("^MXX", "idx.ipc", "IPC Mexico", "MXN", "mx", 6400, 650000),
    ("^BVSP", "idx.bovespa", "Bovespa", "BRL", "br", 18000, 1900000),
    ("^MERV", "idx.merval", "MERVAL", "ARS", "ar", 300000, 31000000),
    ("^FTSE", "idx.ftse100", "FTSE 100", "GBP", "gb", 1000, 110000),
    ("^GDAXI", "idx.dax", "DAX", "EUR", "de", 2600, 270000),
    ("^FCHI", "idx.cac40", "CAC 40", "EUR", "fr", 800, 83000),
    ("^SSMI", "idx.smi", "SMI", "CHF", "ch", 1400, 150000),
    ("^BFX", "idx.bel20", "BEL 20", "EUR", "be", 580, 59000),
    ("^AEX", "idx.aex", "AEX", "EUR", "nl", 110, 12000),
    ("^IBEX", "idx.ibex35", "IBEX 35", "EUR", "es", 2000, 210000),
    ("FTSEMIB.MI", "idx.ftsemib", "FTSE MIB", "EUR", "it", 5200, 530000),
    ("^N100", "idx.euronext100", "Euronext 100", "EUR", "eu", 190, 20000),
    ("^STOXX50E", "idx.stoxx50", "EURO STOXX 50", "EUR", "eu", 640, 64000),
    ("^OMX", "idx.omx30", "OMX Stockholm 30", "SEK", "se", 330, 33000),
    ("^TA125.TA", "idx.ta125", "TA-125", "ILS", "il", 420, 42000),
    ("^N225", "idx.nikkei225", "Nikkei 225", "JPY", "jp", 6500, 660000),
    ("^HSI", "idx.hsi", "Hang Seng", "HKD", "hk", 2500, 260000),
    ("^HSCE", "idx.hscei", "Hang Seng China Enterprises", "HKD", "hk", 850, 86000),
    ("000001.SS", "idx.shcomp", "Thượng Hải Composite", "CNY", "cn", 390, 40000),
    ("399001.SZ", "idx.szcomp", "Thâm Quyến Component", "CNY", "cn", 1350, 140000),
    ("^TWII", "idx.taiex", "TAIEX", "TWD", "tw", 4600, 470000),
    ("^KS11", "idx.kospi", "KOSPI", "KRW", "kr", 660, 67000),
    ("^STI", "idx.sti", "Straits Times", "SGD", "sg", 580, 59000),
    ("^KLSE", "idx.klci", "FTSE Bursa Malaysia KLCI", "MYR", "my", 170, 18000),
    ("^JKSE", "idx.jkse", "Jakarta Composite", "IDR", "id", 660, 67000),
    ("^SET.BK", "idx.set", "SET", "THB", "th", 160, 16000),
    ("PSEI.PS", "idx.psei", "PSEi", "PHP", "ph", 600, 61000),
    ("^BSESN", "idx.sensex", "BSE SENSEX", "INR", "in", 7600, 770000),
    ("^NSEI", "idx.nifty50", "NIFTY 50", "INR", "in", 2300, 240000),
    ("^AXJO", "idx.asx200", "S&P/ASX 200", "AUD", "au", 900, 91000),
    ("^NZ50", "idx.nzx50", "S&P/NZX 50", "NZD", "nz", 1400, 140000),
    ("DX-Y.NYB", "dxy.ice", "Chỉ số đô Mỹ DXY (ICE)", "USD", "us", 10, 1000),
]


def build() -> list[Series]:
    return [Series(source=SOURCE, external_key=sym, domain="asset", code=code, name_vi=name, unit="điểm", freq="d",
                   region=region, asset_class="index", quote_currency=ccy, price_type=None, calendar="trading_days",
                   band=(Decimal(lo), Decimal(hi)), max_lag_days=14, shape="ohlc")
            for sym, code, name, ccy, region, lo, hi in _ROWS]
```

- [ ] **Bước 4: `yahoo_fetch.py`**

```python
"""v8/finance/chart, gọi thẳng REST (không yfinance — yahoo.md §6.5). Đo 2026-09-05: host query1, cửa sổ 400 ngày."""
from __future__ import annotations

import json
import logging
import time

from etl.http_fetch import BadShape, FetchError, open_fetcher

log = logging.getLogger("etl.yahoo")
HOST = "https://query1.finance.yahoo.com/v8/finance/chart"
HEADERS = {"User-Agent": "Mozilla/5.0 (dulieuchungkhoan.vn etl; dulieuchungkhoan.official@gmail.com)"}
DAILY_WINDOW_DAYS = 400          # 40 ngày trả 1 nến ở ^SET.BK/PSEI.PS (measure-yahoo2)
BACKFILL_PERIOD1 = -2208988800   # 1900-01-01: period1=0 cắt câm lịch sử ở 1970 (yahoo.md Bẫy 1)
MIN_INTERVAL = 1.1


def url(symbol: str, period1: int, period2: int) -> str:
    return f"{HOST}/{symbol}?period1={period1}&period2={period2}&interval=1d"


def classify(http: int, text: str):
    if http != 200:
        return "retry", None                                   # kể cả 404 — thử lại rồi mới coi là hỏng (Luật 3)
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    chart = d.get("chart") if isinstance(d, dict) else None
    if not isinstance(chart, dict) or chart.get("error") or not isinstance(chart.get("result"), list) or not chart["result"]:
        return "bad_shape", None
    if not isinstance(chart["result"][0], dict) or "meta" not in chart["result"][0]:
        return "bad_shape", None
    return "ok", d


def fetch_all(series, get, sleep, backfill):
    period2 = int(time.time())
    period1 = BACKFILL_PERIOD1 if backfill else period2 - DAILY_WINDOW_DAYS * 86400
    docs, texts, failed = {}, {}, []
    with open_fetcher(classify, get=get, sleep=sleep, headers=HEADERS, min_interval=MIN_INTERVAL) as f:
        for s in series:
            try:
                docs[s.external_key], texts[s.external_key] = f.fetch_one(url(s.external_key, period1, period2), s.external_key)
            except (BadShape, FetchError) as e:
                failed.append(s.external_key)
                log.warning("%s", e)
        return docs, texts, failed, f.calls, f.retries_done
```

- [ ] **Bước 5: `yahoo_normalize.py`**

```python
"""Nến ngày Yahoo → Bar (spec lát 7 §5.3). Ba cổng bắt buộc + bỏ nến chưa đóng + ngày theo múi giờ SÀN."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from etl.registry import Bar, SeriesError

EPOCH0 = datetime(1970, 1, 1, tzinfo=timezone.utc)   # fromtimestamp không nhận epoch âm trên Windows


def _dec(x):
    return None if x is None else Decimal(str(x))


def _utc(ts: int) -> datetime:
    return EPOCH0 + timedelta(seconds=ts)


def bars(s, doc, now) -> list[Bar]:
    try:
        res = doc["chart"]["result"][0]
        meta = res["meta"]
    except (KeyError, IndexError, TypeError) as e:
        raise SeriesError("shape", f"{s.external_key}: không có chart.result[0].meta") from e
    if meta.get("dataGranularity") != "1d":
        raise SeriesError("shape", f"{s.external_key}: dataGranularity {meta.get('dataGranularity')!r} ≠ '1d'")
    if "ALTSYMBOL" in (meta.get("instrumentType"), meta.get("quoteType")):     # quoteType không còn từ 2026-09-05
        raise SeriesError("shape", f"{s.external_key}: ALTSYMBOL — mã đã ngừng")
    ccy = meta.get("currency")
    if ccy and ccy != s.quote_currency:
        raise SeriesError("shape", f"{s.external_key}: currency {ccy!r} ≠ registry {s.quote_currency!r}")
    ts = res.get("timestamp") or []
    rmt = _utc(meta["regularMarketTime"])
    if not ts or rmt < now - timedelta(days=s.max_lag_days):
        raise SeriesError("stale", f"{s.external_key}: regularMarketTime {rmt.date()} / {len(ts)} nến — quá {s.max_lag_days} ngày")
    tz = ZoneInfo(meta["exchangeTimezoneName"])
    q = res["indicators"]["quote"][0]
    adj = (res["indicators"].get("adjclose") or [{}])[0].get("adjclose") or [None] * len(ts)
    reg = (meta.get("currentTradingPeriod") or {}).get("regular") or {}
    cut = len(ts) - 1 if reg and now.timestamp() < reg["end"] and ts[-1] >= reg["start"] else None
    out: dict = {}
    for i, t in enumerate(ts):
        if i == cut or q["close"][i] is None:
            continue
        d = _utc(t).astimezone(tz).date()
        out[d] = Bar(s.code, d, _dec(q["open"][i]), _dec(q["high"][i]), _dec(q["low"][i]), _dec(q["close"][i]),
                     _dec(adj[i]), _dec(q["volume"][i]))
    if not out:
        return []
    last = out[max(out)]
    lo, hi = s.band
    if not (lo <= last.close <= hi):
        raise SeriesError("band", f"{s.external_key}: close {last.close} ngoài dải ({lo}, {hi})")
    return [out[k] for k in sorted(out)]
```

- [ ] **Bước 6: `yahoo_job.py`** — y `fred_job.py` với `job="global.yahoo"`, `source=yahoo_registry.SOURCE`, `domains=("asset",)`, `guard_mode="ratio"`, `log_name="yahoo"`, `normalize=yahoo_normalize.bars`, **`supports_backfill=True`**.

- [ ] **Bước 7: chạy xanh** — e47 12/12.

---

### Task 6: Binance — `etl binance` (PAXG + 10 coin → `ohlc_daily`, có `--backfill`) + test mã trùng toàn cục

**Files:** Create `backend/etl/binance_registry.py`, `binance_fetch.py`, `binance_normalize.py`, `binance_job.py`; Test `backend/tests/etl/test_e48_binance.py`, `backend/tests/etl/test_e49_registry_codes_unique.py`; Fixture `fixtures/global/binance-PAXGUSDT-5.json` (5 nến mở 00:00 UTC 09-01→09-05, nến 09-04 `open 4481.95 high 4489.97 low 4375.00 close 4431.81 volume 5744.5282`, nến 09-05 `closeTime` 23:59 09-05 **chưa đóng**), `binance-BTCUSDT-first3.json` (nến đầu 2017-08-17 open `4261.48`).

**Interfaces:** như Task 5 với tiền tố `binance_`; `binance_fetch.Banned` (418) thoát cả lượt; `fetch_all` đọc `x-mbx-used-weight-1m` sau mỗi lời gọi, ≥ 3000 ⇒ `sleep(60)`; backfill phân trang `startTime` từ 0, `limit=1000`.

- [ ] **Bước 1: test đỏ** — `backend/tests/etl/test_e48_binance.py`:

```python
"""Binance: nến định danh bằng thời điểm MỞ theo UTC, giá chuỗi ⇒ Decimal, bỏ nến chưa đóng, header weight."""
import json
import os
import pathlib
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import binance_fetch as bf
from etl import binance_job as bj
from etl import binance_normalize as bn
from etl import binance_registry as br
from etl.registry import SeriesError

FIX = pathlib.Path(__file__).parent / "fixtures" / "global"
PAXG = json.loads((FIX / "binance-PAXGUSDT-5.json").read_text(encoding="utf-8"))
BTC3 = json.loads((FIX / "binance-BTCUSDT-first3.json").read_text(encoding="utf-8"))
REG = {s.external_key: s for s in br.build()}
NOW = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def test_registry_11_usdt_24x7():
    s = br.build()
    assert len(s) == 11 and all(x.quote_currency == "USDT" and x.calendar == "24x7" and x.asset_class == "crypto"
                                and x.shape == "ohlc" and x.max_lag_days == 2 and x.source == "binance" for x in s)
    assert REG["PAXGUSDT"].code == "paxg" and REG["BTCUSDT"].code == "btc" and REG["DOGEUSDT"].band == (Decimal("0.008"), Decimal("0.85"))


def test_url_and_classify():
    assert bf.url("PAXGUSDT", 40) == "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1d&limit=40&timeZone=0"
    assert bf.url("BTCUSDT", 1000, 0).endswith("&startTime=0")
    assert bf.classify(200, json.dumps(PAXG))[0] == "ok"
    assert bf.classify(200, "[[1,2,3]]") == ("bad_shape", None)
    assert bf.classify(429, "") == ("retry", None)


def test_open_time_utc_date_string_prices_and_open_candle_dropped():
    bars = bn.bars(REG["PAXGUSDT"], PAXG, NOW)
    assert [b.obs_date for b in bars] == [date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 3), date(2026, 9, 4)]   # 09-05 chưa đóng
    b = bars[-1]
    assert (b.open, b.high, b.low, b.close, b.volume, b.close_adj, b.code) == (
        Decimal("4481.95"), Decimal("4489.97"), Decimal("4375.00"), Decimal("4431.81"), Decimal("5744.5282"), None, "paxg")
    assert len(bn.bars(REG["PAXGUSDT"], PAXG, datetime(2026, 9, 6, 0, 30, tzinfo=timezone.utc))) == 5


def test_seam4_step5_epoch_is_utc_not_vietnam():
    k = [[1786752000000, "1", "1", "1", "1", "1", 1786838399999, "0", 0, "0", "0", "0"]]
    assert bn.bars(REG["BTCUSDT"], [[k[0][0], "70000", "70000", "70000", "70000", "1", k[0][6], "0", 0, "0", "0", "0"]],
                   datetime(2026, 8, 17, tzinfo=timezone.utc))[0].obs_date == date(2026, 8, 15)


def test_first_btc_candle_literal_and_shape_stale():
    assert bn.bars(REG["BTCUSDT"], BTC3, datetime(2017, 8, 21, tzinfo=timezone.utc))[0].open == Decimal("4261.48")
    with pytest.raises(SeriesError) as e:
        bn.bars(REG["PAXGUSDT"], [PAXG[0][:11]], NOW)
    assert e.value.reason == "shape"
    with pytest.raises(SeriesError) as e:
        bn.bars(REG["PAXGUSDT"], PAXG, datetime(2026, 9, 10, tzinfo=timezone.utc))
    assert e.value.reason == "stale"


def test_weight_header_pauses_and_418_aborts():
    slept = []
    docs, texts, failed, calls, _ = bf.fetch_all([REG["PAXGUSDT"]], lambda u, t: (200, json.dumps(PAXG), {"x-mbx-used-weight-1m": "3500"}),
                                                 lambda s: slept.append(s), False)
    assert failed == [] and 60 in slept
    with pytest.raises(bf.Banned):
        bf.fetch_all([REG["PAXGUSDT"]], lambda u, t: (418, "banned", {}), lambda s: None, False)


CODES = [s.code for s in br.build()]


def _synthetic(sym):
    v = str(REG[sym].band[0] * 10)
    return json.dumps([[k[0], v, v, v, v, "1", k[6], "0", 0, "0", "0", "0"] for k in PAXG])


def _fake_get(calls=None):
    def get(u, timeout):
        sym = u.split("symbol=")[1].split("&")[0]
        if calls is not None:
            calls.append(u)
        if "startTime=0" in u:
            page = [[PAXG[0][0] + i * 86400000, "1", "1", "1", "1", "1", PAXG[0][0] + i * 86400000 + 86399999, "0", 0, "0", "0", "0"] for i in range(1000)]
            return 200, json.dumps(page), {}
        if "startTime=" in u:
            return 200, _synthetic(sym), {}
        return 200, (json.dumps(PAXG) if sym == "PAXGUSDT" else _synthetic(sym)), {}
    return get


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM asset.ohlc_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='binance')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='binance'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job='global.binance'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source='binance'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='binance'"))
        c.execute(sa.text("DELETE FROM asset.asset WHERE code = ANY(:c)"), {"c": CODES})


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.series_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def _last(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats FROM ops.etl_run WHERE job='global.binance' ORDER BY run_id DESC LIMIT 1")).one()


def test_job_writes_44_closed_bars(clean):
    calls = []
    assert bj.run(get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    assert len(calls) == 11 and all("limit=40" in u for u in calls)
    status, stats = _last(clean)
    assert status == "success" and stats["bars"] == 44 and stats["inserted"] == 44 and stats["tally"]["ok"] == 11
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT close FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id)"
                                 " WHERE a.code='paxg' AND obs_date='2026-09-04'")).scalar() == Decimal("4431.81")
        assert c.execute(sa.text("SELECT count(*) FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id)"
                                 " WHERE a.code='paxg' AND obs_date='2026-09-05'")).scalar() == 0
        assert c.execute(sa.text("SELECT quote_currency, calendar FROM asset.asset WHERE code='btc'")).one() == ("USDT", "24x7")
    assert bj.run(get=_fake_get(), sleep=lambda s: None, now=NOW) == 0
    assert (_last(clean)[1]["inserted"], _last(clean)[1]["changed"]) == (0, 0)


def test_backfill_pages_from_start_time_zero(clean):
    calls = []
    assert bj.run(backfill=True, keys=["BTCUSDT"], get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    assert len(calls) == 2 and "startTime=0" in calls[0] and "limit=1000" in calls[0] and "startTime=" in calls[1]
```

- [ ] **Bước 2: chạy đỏ.**

- [ ] **Bước 3: `binance_registry.py`**

```python
"""Registry Binance (spec lát 7 Phụ lục E): PAXG + 10 coin, quote USDT (không viết USD ở bất kỳ tầng nào), 24x7."""
from __future__ import annotations

from decimal import Decimal

from etl.registry import Series

SOURCE = "binance"
_ROWS = [("PAXGUSDT", "paxg", "PAX Gold — vàng token hoá 24/7 (1 token ≈ 1 oz)", "440", "45000"),
         ("BTCUSDT", "btc", "Bitcoin", "7900", "800000"), ("ETHUSDT", "eth", "Ethereum", "240", "25000"),
         ("BNBUSDT", "bnb", "BNB", "72", "7300"), ("ADAUSDT", "ada", "Cardano", "0.02", "2.2"),
         ("XRPUSDT", "xrp", "XRP", "0.13", "14"), ("TRXUSDT", "trx", "TRON", "0.03", "3.4"),
         ("LINKUSDT", "link", "Chainlink", "1.1", "120"), ("DOGEUSDT", "doge", "Dogecoin", "0.008", "0.85"),
         ("SOLUSDT", "sol", "Solana", "10", "1020"), ("AVAXUSDT", "avax", "Avalanche", "0.7", "75")]


def build() -> list[Series]:
    return [Series(source=SOURCE, external_key=sym, domain="asset", code=code, name_vi=name, unit="USDT", freq="d",
                   region="global", asset_class="crypto", quote_currency="USDT", price_type=None, calendar="24x7",
                   band=(Decimal(lo), Decimal(hi)), max_lag_days=2, shape="ohlc") for sym, code, name, lo, hi in _ROWS]
```

- [ ] **Bước 4: `binance_fetch.py`**

```python
"""/api/v3/klines — mảng theo vị trí, giá chuỗi (crypto.md Bẫy 2). Header weight thật: tự phanh trước 6.000/phút."""
from __future__ import annotations

import json
import logging

from etl.http_fetch import BadShape, FetchError, open_fetcher

log = logging.getLogger("etl.binance")
BASE = "https://api.binance.com/api/v3/klines"
DAILY_LIMIT = 40
PAGE = 1000
MIN_INTERVAL = 0.3
WEIGHT_PAUSE = 3000


class Banned(Exception):
    """418: IP bị cấm sau khi tiếp tục gọi qua 429 — dừng cả lượt, không thử lại."""


def url(symbol: str, limit: int, start_time: int | None = None) -> str:
    u = f"{BASE}?symbol={symbol}&interval=1d&limit={limit}&timeZone=0"
    return u + (f"&startTime={start_time}" if start_time is not None else "")


def classify(http: int, text: str):
    if http != 200:
        return "retry", None                       # 429 đi đường backoff 2/4/8
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    if not isinstance(d, list) or (d and not (isinstance(d[0], list) and len(d[0]) == 12)):
        return "bad_shape", None
    return "ok", d


def _pause(f, sleep):
    w = f.last_headers.get("x-mbx-used-weight-1m") or f.last_headers.get("X-MBX-USED-WEIGHT-1M")
    if w and int(w) >= WEIGHT_PAUSE:
        log.warning("weight-1m %s ≥ %s — nghỉ 60 s", w, WEIGHT_PAUSE)
        sleep(60)


def fetch_all(series, get, sleep, backfill):
    def get_or_ban(u, timeout):
        st, tx, h = get(u, timeout)
        if st == 418:
            raise Banned(f"418 từ Binance: {tx[:100]}")
        return st, tx, h
    docs, texts, failed = {}, {}, []
    with open_fetcher(classify, get=get_or_ban if get is not None else None, sleep=sleep, min_interval=MIN_INTERVAL) as f:
        if get is None:                            # client thật: bọc get_one của Fetcher
            real = f._get
            f._get = lambda u, t: get_or_ban_real(real, u, t)
        for s in series:
            sym = s.external_key
            try:
                if backfill:
                    rows, start = [], 0
                    while True:
                        doc, text = f.fetch_one(url(sym, PAGE, start), sym)
                        rows.extend(doc)
                        _pause(f, sleep)
                        if len(doc) < PAGE:
                            break
                        start = doc[-1][0] + 1
                    docs[sym], texts[sym] = rows, text
                else:
                    docs[sym], texts[sym] = f.fetch_one(url(sym, DAILY_LIMIT), sym)
                    _pause(f, sleep)
            except (BadShape, FetchError) as e:
                failed.append(sym)
                log.warning("%s", e)
        return docs, texts, failed, f.calls, f.retries_done


def get_or_ban_real(real, u, t):
    st, tx, h = real(u, t)
    if st == 418:
        raise Banned(f"418 từ Binance: {tx[:100]}")
    return st, tx, h
```

- [ ] **Bước 5: `binance_normalize.py`**

```python
"""Nến ngày Binance → Bar: obs_date = ngày UTC của thời điểm MỞ (seam 4 bước 5), bỏ nến closeTime > now."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from etl.registry import Bar, SeriesError


def bars(s, doc, now) -> list[Bar]:
    out: dict = {}
    for k in doc:
        if not isinstance(k, list) or len(k) != 12:
            raise SeriesError("shape", f"{s.external_key}: nến không có 12 phần tử")
        if k[6] / 1000 > now.timestamp():
            continue                                                   # nến đang chạy — đo: limit=40 trả cả hôm nay
        d = datetime.fromtimestamp(k[0] / 1000, timezone.utc).date()
        out[d] = Bar(s.code, d, Decimal(k[1]), Decimal(k[2]), Decimal(k[3]), Decimal(k[4]), None, Decimal(k[5]))
    if not out:
        raise SeriesError("stale", f"{s.external_key}: không có nến đã đóng")
    last_day = max(out)
    if last_day < now.date() - timedelta(days=s.max_lag_days):
        raise SeriesError("stale", f"{s.external_key}: nến đóng cuối {last_day} quá {s.max_lag_days} ngày")
    lo, hi = s.band
    if not (lo <= out[last_day].close <= hi):
        raise SeriesError("band", f"{s.external_key}: close {out[last_day].close} ngoài dải ({lo}, {hi})")
    return [out[k] for k in sorted(out)]
```

- [ ] **Bước 6: `binance_job.py`** — y `fred_job.py` với `job="global.binance"`, `source=binance_registry.SOURCE`, `domains=("asset",)`, `guard_mode="all_or_nothing"` (11 < 20, spec §4.5), `log_name="binance"`, `normalize=binance_normalize.bars`, **`supports_backfill=True`**.

- [ ] **Bước 7: `backend/tests/etl/test_e49_registry_codes_unique.py`**

```python
"""Mã của mình không trùng giữa 5 nguồn quốc tế và WiChart — trừ `wti`, cố ý dùng chung asset cho spot/futures."""
from collections import Counter

from etl import binance_registry, fred_registry, fx_registry, lbma_registry, wichart_registry, yahoo_registry


def test_codes_unique_across_all_registries_except_wti():
    codes = Counter()
    for mod in (fred_registry, fx_registry, lbma_registry, yahoo_registry, binance_registry, wichart_registry):
        codes.update(s.code for s in mod.build())
    dup = {c: n for c, n in codes.items() if n > 1}
    assert dup == {"wti": 2}
    assert sum(codes.values()) == 15 + 6 + 2 + 37 + 11 + 105


def test_external_ids_unique_within_each_source():
    for mod in (fred_registry, fx_registry, lbma_registry, yahoo_registry, binance_registry):
        keys = [(s.source, s.external_key, s.external_sub) for s in mod.build()]
        assert len(keys) == len(set(keys))
```

- [ ] **Bước 8: chạy xanh** — e48 9/9, e49 2/2.

---

### Task 7 (controller): tài liệu sống, chạy thật, ledger, merge

- [ ] **Bước 1:** `uv run pytest tests -q` toàn bộ ⇒ mọi test xanh (dự kiến 661 + 11 + 7 + 5 + 12 + 11 = **707**, 2 skipped). Review hai trục (Chuẩn · Spec) toàn nhánh bằng subagent Opus theo §4.1.5; sửa theo finding.
- [ ] **Bước 2 — AC2:** `set -a; . ./.env; set +a; cd backend` rồi `uv run python -m etl fred --dry-run` · `fx --dry-run` · `lbma --dry-run` · `yahoo --dry-run` · `binance --dry-run` trên nguồn sống; dán `stats` vào `ledger.md`.
- [ ] **Bước 3 — AC3/AC4:** chạy thật 5 job vào kho production dưới `ETL_DATABASE_URL` (role `dlck_etl`); đối chiếu 6 literal của spec §7 bằng truy vấn; chạy lượt hai, dán `inserted/changed/changes_sample`.
- [ ] **Bước 4 — AC5/AC6/AC7:** AC5 qua test job (đã có); AC6 `yahoo --backfill` và `binance --backfill` thật, đếm `min(obs_date)`/`count(*)` của `idx.sp500` (kỳ vọng 1927-12-30 / 24.787), `btc` (2017-08-17), `paxg` (2020-08-28); AC7 `yahoo --keys ^N225` trong giờ Tokyo ngày giao dịch kế (07:00–13:00 VN) — nếu chưa tới giờ thì ghi "chờ" trong ledger, không bịa.
- [ ] **Bước 5 — AC8:** `grep -c "$FRED_API" <log>` ra 0 trên log của lượt fred.
- [ ] **Bước 6 — tài liệu:** checklist §8 spec (roadmap: lát 7 ✅ + "Điểm vào cho lát 8"; yahoo.md · fx.md · commodities.md · fred.md · crypto.md theo số đo 2026-09-05; `10-sources/README.md`; `market-data-store.md`; `backend/README.md`; `database/README.md` số test; `90-records/README.md` trạng thái).
- [ ] **Bước 7:** `ledger.md` (task, review, AC, nợ để lại), commit theo mốc, merge `feat/global-etl` → `main` bằng `--no-ff`.
