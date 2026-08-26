# Plan — ETL dữ liệu tham chiếu (thực thi spec bản 2)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps dùng checkbox `- [ ]`.

**Goal:** Lấp 5 bảng tham chiếu rỗng (`market.issuer` · `market.security` · `market.issuer_external_id` · `market.security_external_id` · `market.icb_industry`) bằng job `python -m etl refdata` chạy 08:00 mỗi ngày làm việc.

**Architecture:** 4 module thuần (indices · normalize · merge · guard) + 2 module DB (store · job), y khuôn job OMO (`open_run` → việc → `close_run` + domain state). Một giao dịch cho toàn bộ ghi; chốt chặn hai tầng đánh giá TRƯỚC commit; bằng chứng từ chối vào staging ở giao dịch riêng.

**Tech Stack:** Python 3.12 · httpx · SQLAlchemy (text SQL) · Postgres thật trong test (fixture `db`/`migrated_engine` của `tests/schema/conftest.py`) · pytest.

**Spec:** [spec.md](spec.md) — cùng thư mục. **Đọc spec trước khi làm bất kỳ task nào.** Ledger: [ledger.md](ledger.md).

## Global Constraints

- `PYTHONIOENCODING=utf-8` cho MỌI lệnh Python (crash cp1252 nếu thiếu — CLAUDE.md §5).
- Test chạy từ `backend/`: `uv run pytest tests/etl/<file> -q`. Cần env `TEST_DATABASE_URL` (xem `database/README.md` — mục "Cách chạy"); test KHÔNG gọi mạng — fixture ở `tests/etl/fixtures/refdata/` (đọc `README.md` trong đó để biết literal).
- Cấm `TRUNCATE`/`DELETE` bảng đích. Cấm sửa migration đã chạy. Cấm gọi endpoint thật trong test.
- `issuer.industry_id` KHÔNG BAO GIỜ xuất hiện trong câu UPDATE (spec §5 — tay thắng máy).
- `updated_at` chỉ đổi khi trường thật đổi; `ingested_at` chỉ ghi lúc INSERT.
- Commit message tiếng Anh, Conventional Commits, một commit mỗi task.

## Bản đồ file

| File | Vai trò |
|---|---|
| `backend/etl/refdata_indices.py` | Hằng số 18 chỉ số (spec §3.1) |
| `backend/etl/refdata_normalize.py` | Payload thô → bản ghi có kiểu + counters (spec §3 luật 2) |
| `backend/etl/refdata_merge.py` | Trạng thái đích (spec §3 luật 1–5) |
| `backend/etl/refdata_guard.py` | Hai tầng chốt chặn (spec §4) |
| `backend/etl/refdata_fetch.py` | 4 lời gọi HTTP (spec §2) |
| `backend/etl/refdata_store.py` | Baseline · plan_delist · apply · evidence · domain state (spec §4–5) |
| `backend/etl/refdata_job.py` | Điều phối + `--accept-drop` (spec §4.4, §6) |
| `backend/etl/__main__.py` | Thêm subcommand `refdata` |
| `backend/tests/etl/test_e05..e10_*.py` | Seam 1–5 của spec §7 |

---

### Task 1: `refdata_indices` — hằng số 18 chỉ số

**Files:** Create `backend/etl/refdata_indices.py` · Test `backend/tests/etl/test_e05_refdata_indices.py`

**Interfaces (Produces):**
```python
@dataclass(frozen=True)
class IndexDef:
    snap_code: str      # mã trong indexsnaps
    ticker: str         # ticker chuẩn nội bộ (spec §3.1)
    name: str
    exchange: str       # 'HOSE' | 'HNX' | 'UPCOM'
    tvc_code: str | None  # CHỈ 3 mã đã đo; còn lại None

INDICES: tuple[IndexDef, ...]          # đúng 18 phần tử, đúng bảng spec §3.1
SNAP_CODES: frozenset[str]             # {d.snap_code for d in INDICES}
```

- [ ] **Step 1: test đỏ** — viết `test_e05_refdata_indices.py`:

```python
from etl.refdata_indices import INDICES, SNAP_CODES

def test_indices_match_spec_table():
    assert len(INDICES) == 18
    # literal độc lập: chép từ spec §3.1, không import từ module
    assert SNAP_CODES == {"HOSE","30","100","MID","SML","XALL","X50","SI","ALL",
                          "DIAMOND","FINLEAD","FINSELECT","HNX","HNX30","HNXFin",
                          "HNXMSCap","HNXMan","UPCOM"}
    assert len({d.ticker for d in INDICES}) == 18          # ticker chuẩn không trùng
    assert all(d.exchange in ("HOSE","HNX","UPCOM") for d in INDICES)

def test_only_three_tvc_codes_are_measured():
    tvc = {d.snap_code: d.tvc_code for d in INDICES if d.tvc_code is not None}
    assert tvc == {"HOSE": "VNINDEX", "30": "VN30", "HNX": "HNXIndex"}

def test_key_rows_verbatim():
    by = {d.snap_code: d for d in INDICES}
    assert (by["HOSE"].ticker, by["HOSE"].exchange) == ("VNINDEX", "HOSE")
    assert (by["UPCOM"].ticker, by["UPCOM"].exchange) == ("UPINDEX", "UPCOM")
    assert (by["XALL"].ticker, by["XALL"].exchange) == ("VNXALL", "HOSE")
```

- [ ] **Step 2:** chạy `uv run pytest tests/etl/test_e05_refdata_indices.py -q` — Expected: FAIL (ModuleNotFoundError).
- [ ] **Step 3:** viết `refdata_indices.py` — 18 dòng `IndexDef` chép **nguyên văn bảng spec §3.1** (cột Mã→`snap_code`, Ticker chuẩn→`ticker`, Tên→`name`, exchange, Mã TVC — chỉ 3 dòng `HOSE`/`30`/`HNX` có `tvc_code`, còn lại `None`).
- [ ] **Step 4:** chạy lại — Expected: 3 passed.
- [ ] **Step 5:** commit `feat(etl): refdata index constant, 18 rows from spec 3.1`.

---

### Task 2: `refdata_normalize`

**Files:** Create `backend/etl/refdata_normalize.py` · Test `backend/tests/etl/test_e06_refdata_normalize.py`

**Interfaces:**
- Consumes: `refdata_indices.SNAP_CODES`.
- Produces:

```python
class RefdataError(Exception): ...

@dataclass(frozen=True)
class QuoteRec:
    symbol: str; full_name: str | None; exchange: str
    security_type: str        # 'stock' | 'etf' — ĐÃ phân loại theo spec luật 2
    tradelot: int | None

@dataclass(frozen=True)
class OrgRec:
    organ_code: str; ticker: str; com_group_code: str; organ_name: str
    organ_short_name: str | None; com_type_code: str | None; icb_code: str | None

@dataclass(frozen=True)
class IcbRec:
    icb_code: str; icb_name: str | None; parent_icb_code: str | None
    icb_level: int | None; icb_code_path: str | None

@dataclass(frozen=True)
class NormResult:
    quotes: list[QuoteRec]        # chỉ stock/etf đã lọc
    index_codes: frozenset[str]   # mã indexsnaps THẬT xuất hiện, sau lọc rác
    orgs: list[OrgRec]
    icb: list[IcbRec]
    counters: dict[str, int]      # skipped_cw · skipped_bond · junk_stocktype2 · unknown_stocktype · index_junk

def normalize(raw: dict[str, str]) -> NormResult
    # raw keys: 'quotes' | 'indexsnaps' | 'organization' | 'icb' — text JSON nguyên văn
```

Luật (spec §3 luật 2 + §3.1): `StockType=2` **và** `re.fullmatch(r"[A-Z0-9]{3}", symbol)` → `stock`; `StockType=2` khác dạng → bỏ + `junk_stocktype2`; `3`→`etf`; `4`→`skipped_cw`; `12`→`skipped_bond`; khác→`unknown_stocktype` + `log.warning`. `indexsnaps`: giữ bản ghi có `marketCode ∈ SNAP_CODES`, đếm phần loại vào `index_junk`. **Assert giao:** `SNAP_CODES ∩ {symbol của quotes}` ≠ ∅ → `raise RefdataError`. Payload shape: quotes/indexsnaps bọc `{"s","d"}` hoặc list trần (xử cả hai như `catalog.py` ingester); org/icb bọc `{"items": [...]}`.

- [ ] **Step 1: test đỏ** — literal lấy từ `fixtures/refdata/README.md`:

```python
import json, pathlib, pytest
from etl.refdata_normalize import RefdataError, normalize

FIX = pathlib.Path(__file__).parent / "fixtures" / "refdata"

def _raw():
    return {k: (FIX / f"{k}.json").read_text(encoding="utf-8")
            for k in ("quotes", "indexsnaps", "organization", "icb")}

def test_normalize_fixture_literals():
    n = normalize(_raw())
    assert sum(1 for q in n.quotes if q.security_type == "stock") == 6
    assert sum(1 for q in n.quotes if q.security_type == "etf") == 3
    assert n.counters["skipped_cw"] == 2 and n.counters["skipped_bond"] == 2
    assert n.counters["junk_stocktype2"] == 1          # L40_WFT_01
    assert not any(q.symbol == "L40_WFT_01" for q in n.quotes)
    assert len(n.index_codes) == 18 and n.counters["index_junk"] == 2
    assert len(n.orgs) == 8
    assert len(n.icb) == 176                            # icb.json nguyên văn
    by_level = {}
    for r in n.icb: by_level[r.icb_level] = by_level.get(r.icb_level, 0) + 1
    assert by_level == {1: 11, 2: 19, 3: 40, 4: 106}   # đo 2026-08-26

def test_collision_between_index_codes_and_symbols_raises():
    raw = _raw()
    d = json.loads(raw["quotes"]); d["d"].append(
        {"symbol": "ALL", "FullName": "x", "exchange": "HOSE", "StockType": "2", "tradelot": 100})
    raw["quotes"] = json.dumps(d)
    with pytest.raises(RefdataError):
        normalize(raw)

def test_org_rec_carries_identity_fields():
    n = normalize(_raw())
    vhm = next(o for o in n.orgs if o.ticker == "VHM")
    assert vhm.organ_code == "NHN"                     # bẫy organCode ≠ ticker
    assert vhm.com_group_code == "VNINDEX"
```

- [ ] **Step 2:** chạy — Expected: FAIL (ModuleNotFoundError).
- [ ] **Step 3:** viết `refdata_normalize.py` theo luật trên (~90 dòng).
- [ ] **Step 4:** chạy — Expected: 3 passed. Chạy thêm cả cụm: `uv run pytest tests/etl -q` không vỡ gì.
- [ ] **Step 5:** commit `feat(etl): refdata normalize with classification and junk filters`.

---

### Task 3: `refdata_merge`

**Files:** Create `backend/etl/refdata_merge.py` · Test `backend/tests/etl/test_e07_refdata_merge.py`

**Interfaces:**
- Consumes: `NormResult`/`QuoteRec`/`OrgRec`/`IcbRec` (Task 2) · `INDICES` (Task 1).
- Produces:

```python
COM_GROUP_TO_EXCHANGE = {"VNINDEX": "HOSE", "HNXIndex": "HNX", "UpcomIndex": "UPCOM"}

@dataclass(frozen=True)
class SecurityTarget:
    ticker: str; exchange: str; security_type: str; status: str   # 'listed'|'delisted'
    tradelot: int | None; full_name: str | None
    organ_code: str | None                                        # None = không nối issuer
    external_ids: tuple[tuple[str, str, str], ...]                # (source, code, sub)

@dataclass(frozen=True)
class IssuerTarget:
    organ_code: str; name: str; short_name: str | None
    com_type_code: str | None; icb_code: str | None

@dataclass(frozen=True)
class TargetState:
    securities: list[SecurityTarget]
    issuers: list[IssuerTarget]
    icb: list[IcbRec]
    counters: dict[str, int]     # stocks_no_issuer · fiin_only_delisted (+ giữ nguyên counters của normalize)

def merge(n: NormResult) -> TargetState
```

Luật (spec §3): mọi `QuoteRec` → `SecurityTarget` `listed`, `organ_code` = org khớp ticker (stock lẫn etf — luật 4), external id `('bvsc', ticker, '')`; 18 `INDICES` → `index`/`listed`/không organ, external `('bvsc', snap_code, 'snapshot')` + nếu `tvc_code` → `('bvsc', tvc_code, 'tvc')`; org có ticker KHÔNG thuộc quotes/indices → `delisted`, `exchange=COM_GROUP_TO_EXCHANGE[com_group_code]`, `security_type = 'fund_cert' if com_type_code=='QU' else 'stock'`, `full_name=organ_name`, external_ids rỗng (spec §3.2). Issuers = mọi org (kể cả org-only). Đếm `stocks_no_issuer` (stock không khớp org), `fiin_only_delisted`.

- [ ] **Step 1: test đỏ:**

```python
import pathlib
from etl.refdata_merge import merge
from etl.refdata_normalize import normalize

FIX = pathlib.Path(__file__).parent / "fixtures" / "refdata"

def _target():
    raw = {k: (FIX / f"{k}.json").read_text(encoding="utf-8")
           for k in ("quotes", "indexsnaps", "organization", "icb")}
    return merge(normalize(raw))

def test_fiin_only_rows_are_delisted_with_mapped_exchange_and_type():
    t = _target()
    by = {s.ticker: s for s in t.securities}
    egl = by["EGL"]                      # org-only, UpcomIndex
    assert (egl.status, egl.exchange, egl.security_type) == ("delisted", "UPCOM", "stock")
    f4 = by["FUCTVGF4"]                  # org-only, QU, VNINDEX
    assert (f4.status, f4.exchange, f4.security_type) == ("delisted", "HOSE", "fund_cert")
    assert t.counters["fiin_only_delisted"] == 2

def test_indices_present_and_never_delisted_despite_absent_from_quotes():
    t = _target()
    idx = [s for s in t.securities if s.security_type == "index"]
    assert len(idx) == 18 and all(s.status == "listed" for s in idx)
    vni = next(s for s in idx if s.ticker == "VNINDEX")
    assert ("bvsc", "HOSE", "snapshot") in vni.external_ids
    assert ("bvsc", "VNINDEX", "tvc") in vni.external_ids       # seam 2b step-02

def test_issuer_links():
    t = _target()
    by = {s.ticker: s for s in t.securities}
    assert by["VHM"].organ_code == "NHN"
    assert by["FUEMAVND"].organ_code == "2172623"    # ETF khớp QU (luật 4)
    assert by["E1SSHN30"].organ_code is None          # ETF không khớp
    assert by["HTB"].organ_code is None               # CP không issuer
    assert t.counters["stocks_no_issuer"] == 1        # chỉ HTB — giải tay từ fixture (README, sửa 2026-08-26)
    assert len(t.issuers) == 8

def test_target_tickers_are_unique():
    t = _target()
    tickers = [s.ticker for s in t.securities]
    assert len(tickers) == len(set(tickers))
```

- [ ] **Step 2:** chạy — FAIL. **Step 3:** viết `refdata_merge.py` (~70 dòng). **Step 4:** chạy — 4 passed, cả cụm etl xanh. **Step 5:** commit `feat(etl): refdata merge builds run target state`.

---

### Task 4: `refdata_guard` (độc lập — làm song song Task 1–3 được)

**Files:** Create `backend/etl/refdata_guard.py` · Test `backend/tests/etl/test_e08_refdata_guard.py`

**Interfaces (Produces):**
```python
@dataclass(frozen=True)
class GuardVerdict:
    ok: bool
    reasons: tuple[str, ...]     # rỗng khi ok

DROP_RATIO = 0.02        # tầng 1 (spec §4)
DELIST_RATIO = 0.01      # tầng 2

def check(counts: Mapping[str, int],            # keys 'quotes'|'organization'|'icb' — SAU normalize
          baseline: Mapping[str, int] | None,   # None = lần chạy đầu → bỏ tầng 1 tỷ lệ
          index_codes_seen: AbstractSet[str],
          expected_index_codes: AbstractSet[str],
          planned_delist: int, listed_now: int) -> GuardVerdict
```

Luật: tầng 1 — với từng key có trong baseline: `count < baseline * (1 - DROP_RATIO)` → lý do; khớp-tập: `expected_index_codes - index_codes_seen` ≠ ∅ → lý do (chạy **cả khi không baseline**). Tầng 2 — `listed_now > 0 and planned_delist > listed_now * DELIST_RATIO` → lý do. Hàm thuần, không I/O.

- [ ] **Step 1: test đỏ** (expected giải tay, ghi phép tính trong comment):

```python
from etl.refdata_guard import check

IDX = frozenset({"A", "B", "C"})

def _ok(v): return v.ok and v.reasons == ()

def test_tier1_ratio_boundary():
    base = {"quotes": 1000, "organization": 500, "icb": 176}
    # 979/1000 = sụt 2,1% > 2% → từ chối; 981 = 1,9% → qua
    assert not _ok(check({"quotes": 979, "organization": 500, "icb": 176}, base, IDX, IDX, 0, 2000))
    assert _ok(check({"quotes": 981, "organization": 500, "icb": 176}, base, IDX, IDX, 0, 2000))

def test_first_run_without_baseline_passes_ratio_but_still_checks_index_set():
    assert _ok(check({"quotes": 5}, None, IDX, IDX, 0, 0))
    v = check({"quotes": 5}, None, frozenset({"A", "B"}), IDX, 0, 0)
    assert not v.ok and any("C" in r for r in v.reasons)

def test_tier2_delist_boundary():
    # 21/2000 = 1,05% > 1% → từ chối; 19/2000 = 0,95% → qua
    assert not _ok(check({}, None, IDX, IDX, 21, 2000))
    assert _ok(check({}, None, IDX, IDX, 19, 2000))
    assert _ok(check({}, None, IDX, IDX, 0, 0))       # kho rỗng lần đầu

def test_real_weekly_drift_passes():
    # nhịp thật đo được: 2.530 → 2.534 trong 5 ngày; chiều sụt tương đương 4/2530 ≈ 0,16%
    assert _ok(check({"quotes": 2526}, {"quotes": 2530}, IDX, IDX, 4, 2000))
```

- [ ] **Step 2:** FAIL. **Step 3:** viết (~40 dòng). **Step 4:** 4 passed. **Step 5:** commit `feat(etl): refdata two-tier drop guard`.

---

### Task 5: `refdata_store` — Postgres thật, role production

**Files:** Create `backend/etl/refdata_store.py` · Test `backend/tests/etl/test_e09_refdata_store.py`

**Interfaces:**
- Consumes: `TargetState`/`SecurityTarget`/`IssuerTarget` (Task 3), `IcbRec` (Task 2).
- Produces:

```python
JOB = "market.refdata"

def load_baseline(engine) -> dict | None
    # SELECT stats FROM ops.etl_run WHERE job=:j AND status='success'
    # ORDER BY finished_at DESC LIMIT 1 → trả stats['counts'] hoặc None

def plan_delist(conn, target_tickers: set[str]) -> tuple[list[str], int]
    # (danh sách ticker listed ngoài target, tổng số listed hiện tại)

def apply(conn, target: TargetState, delist: list[str]) -> dict
    # upsert 5 bảng TRONG transaction đang mở của caller; trả stats

def store_refusal_evidence(engine, raw: dict[str, str], run_id: int, reasons: list[str]) -> None
    # giao dịch RIÊNG — INSERT staging.raw_payload source='refdata',
    # endpoint_key='refdata:<key>', content_type='json', payload=cast jsonb,
    # meta={'run_id':…, 'reasons':…}

def upsert_domain_state(engine, watermark: str) -> None
    # HAI dòng: ('market.reference','bvsc') và ('market.reference','fiintrade') — spec §5
```

SQL của `apply` (theo spec §5, viết đúng thế này):

1. **issuer:** với mỗi `IssuerTarget`: `SELECT issuer_id FROM market.issuer_external_id WHERE source='fiintrade' AND external_code=:oc`. Không có → `INSERT INTO market.issuer (name, short_name, com_type_code, icb_code) VALUES … RETURNING issuer_id` + `INSERT INTO market.issuer_external_id (issuer_id, source, external_code) VALUES (:i,'fiintrade',:oc)`. Có → `UPDATE market.issuer SET name=:n, short_name=:s, com_type_code=:c, icb_code=:ic, updated_at=now() WHERE issuer_id=:i AND (name, short_name, com_type_code, icb_code) IS DISTINCT FROM (:n, :s, :c, :ic)` — **`industry_id` không có mặt**. Giữ map `organ_code → issuer_id`.
2. **security:** với mỗi `SecurityTarget`: `SELECT security_id, exchange, security_type, status, tradelot, full_name, issuer_id FROM market.security WHERE ticker=:t ORDER BY (status='listed') DESC, updated_at DESC LIMIT 1` *(khớp theo TICKER một mình — spec §5)*. Không có → INSERT đủ cột. Có → UPDATE các cột đó + `updated_at=now()` với đuôi `AND (exchange, security_type, status, tradelot, full_name, issuer_id) IS DISTINCT FROM (…)`; đếm `exchange_moves` khi exchange đổi.
3. **security_external_id:** `INSERT … (security_id, source, external_code, external_sub) VALUES … ON CONFLICT (source, external_code) DO NOTHING`.
4. **icb_industry:** `INSERT … ON CONFLICT (icb_code) DO UPDATE SET icb_name=EXCLUDED.icb_name, parent_icb_code=EXCLUDED.parent_icb_code, icb_level=EXCLUDED.icb_level, icb_code_path=EXCLUDED.icb_code_path WHERE (icb_industry.icb_name, icb_industry.parent_icb_code, icb_industry.icb_level, icb_industry.icb_code_path) IS DISTINCT FROM (EXCLUDED.icb_name, EXCLUDED.parent_icb_code, EXCLUDED.icb_level, EXCLUDED.icb_code_path)` — `ingested_at` không nằm trong SET.
5. **delist:** `UPDATE market.security SET status='delisted', updated_at=now() WHERE ticker = ANY(:t) AND status='listed'`.

Stats trả về: `sec_inserted` `sec_updated` `sec_unchanged` `delisted` `exchange_moves` `issuers_inserted` `icb_rows`.

- [ ] **Step 1: test đỏ** — dùng fixture `db` (transaction rollback mỗi test), **`SET LOCAL ROLE dlck_etl` ngay đầu mỗi test** (khuôn `test_e04_store_flow.py`):

```python
import pathlib
import sqlalchemy as sa
from etl.refdata_merge import merge
from etl.refdata_normalize import normalize
from etl import refdata_store

FIX = pathlib.Path(__file__).parent / "fixtures" / "refdata"

def _target():
    raw = {k: (FIX / f"{k}.json").read_text(encoding="utf-8")
           for k in ("quotes", "indexsnaps", "organization", "icb")}
    return merge(normalize(raw))

def _as_etl(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))

def test_apply_twice_is_idempotent_including_timestamps(db):
    _as_etl(db)
    t = _target()
    delist, _ = refdata_store.plan_delist(db, {s.ticker for s in t.securities})
    refdata_store.apply(db, t, delist)
    snap1 = db.execute(sa.text(
        "SELECT ticker, exchange, security_type, status, updated_at FROM market.security ORDER BY ticker"
    )).all()
    ing1 = db.execute(sa.text(
        "SELECT source, external_code, ingested_at FROM market.security_external_id ORDER BY 1,2"
    )).all()
    stats2 = refdata_store.apply(db, t, [])
    assert db.execute(sa.text(
        "SELECT ticker, exchange, security_type, status, updated_at FROM market.security ORDER BY ticker"
    )).all() == snap1                                   # updated_at KHÔNG đổi lượt hai
    assert db.execute(sa.text(
        "SELECT source, external_code, ingested_at FROM market.security_external_id ORDER BY 1,2"
    )).all() == ing1                                    # ingested_at KHÔNG đổi
    assert stats2["sec_inserted"] == 0 and stats2["sec_updated"] == 0

def test_exchange_move_keeps_security_id(db):
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    sid = db.execute(sa.text("SELECT security_id FROM market.security WHERE ticker='HTB'")).scalar_one()
    # đổi sàn: dựng target mới với HTB ở HOSE
    from dataclasses import replace
    t2 = type(t)(securities=[replace(s, exchange="HOSE") if s.ticker == "HTB" else s
                             for s in t.securities],
                 issuers=t.issuers, icb=t.icb, counters=t.counters)
    stats = refdata_store.apply(db, t2, [])
    row = db.execute(sa.text(
        "SELECT security_id, exchange FROM market.security WHERE ticker='HTB'")).one()
    assert row == (sid, "HOSE") and stats["exchange_moves"] == 1

def test_relist_keeps_security_id_and_delist_never_deletes(db):
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    sid = db.execute(sa.text("SELECT security_id FROM market.security WHERE ticker='ACV'")).scalar_one()
    n_before = db.execute(sa.text("SELECT count(*) FROM market.security")).scalar_one()
    refdata_store.apply(db, t, ["ACV"])                 # lật delisted
    assert db.execute(sa.text("SELECT status FROM market.security WHERE security_id=:i"),
                      {"i": sid}).scalar_one() == "delisted"
    refdata_store.apply(db, t, [])                      # target vẫn chứa ACV ⇒ tái niêm yết
    row = db.execute(sa.text("SELECT security_id, status FROM market.security WHERE ticker='ACV'")).one()
    assert row == (sid, "listed")                       # GIỮ NGUYÊN id
    assert db.execute(sa.text("SELECT count(*) FROM market.security")).scalar_one() == n_before

def test_seam2b_vnindex_dual_external_ids_one_security(db):
    _as_etl(db)
    refdata_store.apply(db, _target(), [])
    rows = db.execute(sa.text(
        "SELECT DISTINCT security_id FROM market.security_external_id"
        " WHERE source='bvsc' AND (external_code, external_sub) IN (('VNINDEX','tvc'), ('HOSE','snapshot'))"
    )).all()
    assert len(rows) == 1                               # cùng một security_id

def test_manual_industry_assignment_survives_rerun(db):
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    iid = db.execute(sa.text(
        "SELECT i.issuer_id FROM market.issuer i JOIN market.issuer_external_id e USING (issuer_id)"
        " WHERE e.source='fiintrade' AND e.external_code='NHN'")).scalar_one()
    ind = db.execute(sa.text(
        "SELECT industry_id FROM market.industry WHERE level=2 ORDER BY industry_id LIMIT 1")).scalar_one()
    db.execute(sa.text("RESET ROLE"))                   # gán tay bằng quyền owner
    db.execute(sa.text("UPDATE market.issuer SET industry_id=:d WHERE issuer_id=:i"),
               {"d": ind, "i": iid})
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    refdata_store.apply(db, t, [])                      # job chạy lại
    assert db.execute(sa.text("SELECT industry_id FROM market.issuer WHERE issuer_id=:i"),
                      {"i": iid}).scalar_one() == ind   # tay THẮNG máy

def test_plan_delist_counts(db):
    _as_etl(db)
    t = _target()
    refdata_store.apply(db, t, [])
    tickers = {s.ticker for s in t.securities}
    delist, listed = refdata_store.plan_delist(db, tickers - {"ACV"})
    assert delist == ["ACV"] and listed == len([s for s in t.securities if s.status == "listed"])
```

- [ ] **Step 2:** FAIL. **Step 3:** viết `refdata_store.py` theo SQL đã cho (~140 dòng). **Step 4:** 6 passed; cả cụm `tests/etl` xanh. **Step 5:** commit `feat(etl): refdata store, atomic apply under production role`.

---

### Task 6: `refdata_fetch` + `refdata_job` + CLI

**Files:** Create `backend/etl/refdata_fetch.py`, `backend/etl/refdata_job.py` · Modify `backend/etl/__main__.py` · Test `backend/tests/etl/test_e10_refdata_job.py`

**Interfaces:**
- Consumes: mọi thứ Task 1–5. Khuôn `omo_job.py` + `omo_store.open_run/close_run`.
- Produces:

```python
# refdata_fetch.py
ENDPOINTS = {
    "quotes":       "https://online.bvsc.com.vn/quotes?symbols=ALL",
    "indexsnaps":   "https://online.bvsc.com.vn/datafeed/indexsnaps",
    "organization": "https://wlgw-core.fiintrade.vn/Master/GetListOrganization?language=vi",
    "icb":          "https://wlgw-core.fiintrade.vn/Master/GetAllIcbIndustry?language=vi",
}
FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"   # bắt buộc cho *.fiintrade.vn (00-conventions §2)
def fetch() -> dict[str, str]                  # httpx, timeout 60 s, raise_for_status

# refdata_job.py
class GuardRefused(Exception):
    def __init__(self, reasons): self.reasons = list(reasons)
def run(accept_drop: bool = False) -> int      # 0 thành công · 1 lỗi/từ chối · 2 thiếu env
```

Luồng `run` (spec §6): `load_dotenv()` → `ETL_DATABASE_URL` (thiếu → 2) → `open_run(engine, "market.refdata")` → `fetch` → `normalize` → `merge` → `counts = {"quotes": len(n.quotes), "organization": len(n.orgs), "icb": len(n.icb)}` → `baseline = load_baseline(engine)` → `with engine.begin() as conn:` `plan_delist` → `guard.check(counts, baseline, n.index_codes, SNAP_CODES, len(delist), listed)` → nếu `not ok and not accept_drop` → `raise GuardRefused` → `apply` → *(thoát with = commit)* → `close_run success` với `stats = {**apply_stats, "counts": counts, **n.counters, **t.counters}` (+`"accept_drop": True` nếu dùng) → `upsert_domain_state(engine, date.today().isoformat())` → 0. `except GuardRefused`: `store_refusal_evidence(engine, raw, run_id, reasons)` → `close_run failed` (error=`"guard refused: …"`) → 1. `except Exception`: `close_run failed` + `log.exception` → 1. `finally: engine.dispose()`.

`__main__.py`: nhánh `refdata` với `argparse` con (`--accept-drop`), sửa help thành `(hỗ trợ: omo, refdata)`.

- [ ] **Step 1: test đỏ** — job chạy trên `migrated_engine` (commit thật vào `dulieu_test`), monkeypatch fetch bằng fixture:

```python
import json, os, pathlib
import sqlalchemy as sa
import etl.refdata_job as job_mod
from etl import refdata_store

FIX = pathlib.Path(__file__).parent / "fixtures" / "refdata"

def _raw():
    return {k: (FIX / f"{k}.json").read_text(encoding="utf-8")
            for k in ("quotes", "indexsnaps", "organization", "icb")}

def _patch(monkeypatch, migrated_engine, raw):
    monkeypatch.setattr(job_mod.refdata_fetch, "fetch", lambda: raw)
    # KHÔNG dùng str(engine.url) — SQLAlchemy che mật khẩu thành '***' trong repr
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr(job_mod, "load_dotenv", lambda: None)   # .env thật không được đè env test

def test_job_end_to_end_success_and_baseline(monkeypatch, migrated_engine):
    _patch(monkeypatch, migrated_engine, _raw())
    assert job_mod.run() == 0
    with migrated_engine.connect() as c:
        n_sec = c.execute(sa.text("SELECT count(*) FROM market.security")).scalar_one()
        assert n_sec == 9 + 18 + 2          # 6 CP + 3 ETF + 18 chỉ số + 2 fiin-only (fixture README)
        assert c.execute(sa.text("SELECT count(*) FROM market.icb_industry")).scalar_one() == 176
        run_row = c.execute(sa.text(
            "SELECT status, stats FROM ops.etl_run WHERE job='market.refdata'"
            " ORDER BY run_id DESC LIMIT 1")).one()
        assert run_row.status == "success"
        assert run_row.stats["counts"] == {"quotes": 9, "organization": 8, "icb": 176}
        assert c.execute(sa.text(
            "SELECT count(*) FROM ops.data_domain_state WHERE domain='market.reference'"
        )).scalar_one() == 2
    assert refdata_store.load_baseline(migrated_engine) == {"quotes": 9, "organization": 8, "icb": 176}
    assert job_mod.run() == 0               # idempotent lượt hai

def test_guard_refusal_rolls_back_keeps_baseline_writes_evidence(monkeypatch, migrated_engine):
    _patch(monkeypatch, migrated_engine, _raw())
    assert job_mod.run() == 0               # dựng mốc 9/8/176
    cut = _raw()
    d = json.loads(cut["quotes"])
    d["d"] = [r for r in d["d"] if r["symbol"] not in ("ACV", "VHM", "SHB")]   # cụt 3/9 > 2%
    cut["quotes"] = json.dumps(d)
    _patch(monkeypatch, migrated_engine, cut)
    assert job_mod.run() == 1
    with migrated_engine.connect() as c:
        assert c.execute(sa.text(                                   # dữ liệu KHÔNG đổi
            "SELECT status FROM market.security WHERE ticker='ACV'")).scalar_one() == "listed"
        last = c.execute(sa.text(
            "SELECT run_id, status FROM ops.etl_run WHERE job='market.refdata'"
            " ORDER BY run_id DESC LIMIT 1")).one()
        assert last.status == "failed"
        ev = c.execute(sa.text(
            "SELECT count(*) FROM staging.raw_payload WHERE source='refdata'"
            " AND (meta->>'run_id')::bigint = :r"), {"r": last.run_id}).scalar_one()
        assert ev == 4                                              # đủ 4 payload bằng chứng
    assert refdata_store.load_baseline(migrated_engine) == {"quotes": 9, "organization": 8, "icb": 176}

def test_accept_drop_lets_refused_run_commit(monkeypatch, migrated_engine):
    cut = _raw()
    d = json.loads(cut["quotes"])
    d["d"] = [r for r in d["d"] if r["symbol"] not in ("ACV", "VHM", "SHB")]
    cut["quotes"] = json.dumps(d)
    _patch(monkeypatch, migrated_engine, cut)
    assert job_mod.run(accept_drop=True) == 0
    with migrated_engine.connect() as c:
        assert c.execute(sa.text(
            "SELECT status FROM market.security WHERE ticker='ACV'")).scalar_one() == "delisted"
        assert c.execute(sa.text(
            "SELECT stats->'accept_drop' FROM ops.etl_run WHERE job='market.refdata'"
            " ORDER BY run_id DESC LIMIT 1")).scalar_one() is True
```

⚠️ Thứ tự test trong file là thứ tự chạy — ba test này **cùng chia sẻ** `dulieu_test` đã commit; expected của test sau đã tính trạng thái test trước để lại (mốc 9/8/176). Không xáo thứ tự.

- [ ] **Step 2:** FAIL. **Step 3:** viết `refdata_fetch.py` (~25 dòng) + `refdata_job.py` (~70 dòng) + sửa `__main__.py`. **Step 4:** 3 passed; **toàn bộ** `uv run pytest tests -q` xanh (cần env đủ như Global Constraints). **Step 5:** commit `feat(etl): refdata job with guard, evidence-on-refusal and accept-drop`.

---

### Task 7 (controller — KHÔNG giao subagent): vận hành + chạy thật + quét tài liệu

- [ ] Đăng ký task `dlck-refdata` 08:00 ngày làm việc trong `scripts/register-tasks.ps1` (khuôn OMO, `Assert-TaskCommand -MustContain "python -m etl refdata"`), chạy script, soi lệnh thật.
- [ ] **Chạy tay dưới credential production** (§3.5): `python -m etl refdata` bằng `ETL_DATABASE_URL` thật — nghiệm thu: `etl_run` success, đếm `market.security` ≈ 1.962 + 31 + 18 + 4 ± nhịp ngày, `stocks_no_issuer` ≈ 437, log không lỗi. Chạy lại lần hai → `sec_updated=0`.
- [ ] Quét tài liệu sống theo **spec §10** (roadmap · architecture §3.1 · market-data-store §4 · database/README · 90-records/README), `git grep` đối chiếu, ghi ledger, commit.
