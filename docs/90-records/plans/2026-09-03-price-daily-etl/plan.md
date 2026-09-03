# Kế hoạch thực thi — `etl price` (lát 3 của [7] ETL REST hằng ngày)

> **Cho người/agent thực thi:** dùng skill `superpowers:executing-plans` (người điều phối tự làm — mỗi task là 1–2 file và cần nhìn output của vòng đỏ→xanh, đúng ô *"Tự làm"* của bảng CLAUDE.md §4.1) hoặc `subagent-driven-development`, chạy **từng task một**. Bước đánh dấu `- [ ]` để theo dõi.

**Mục tiêu:** job `python -m etl price` nạp giá theo ngày từ `getPriceData` vào `market.price_daily` — trang 1 mọi cổ phiếu niêm yết mỗi ngày, và backfill trọn lịch sử tiếp tục được qua nhiều lượt.

**Kiến trúc:** năm module thuần/IO tách bạch y khuôn lát 2 (`events_*`) — `price_fetch` (I/O, giãn cách, retry, phân trang) → `price_normalize` (thuần) → `price_guard` (thuần, chỉ chế độ hằng ngày) → `price_store` (UPSERT một câu mang ba luật: điền-một-lần `close_raw`, merge khoá adapter, bỏ qua dòng không đổi) → `price_job` (hai chế độ). Không migration.

**Stack:** Python 3.12 · `httpx` · SQLAlchemy 2 (`sa.text`, không ORM) · Postgres · pytest.

**Spec:** [`spec.md`](spec.md) — đọc trước, plan này chỉ nói *chính xác thế nào*. Số đo nền: [`measurements.md`](measurements.md).

## Ràng buộc toàn cục

- **`PYTHONIOENCODING=utf-8`** trên mọi lệnh chạy Python — không đặt thì crash cp1252 khi in tiếng Việt.
- Mọi lệnh chạy từ thư mục `backend/`, bằng `uv run`.
- Test cần `TEST_DATABASE_URL` — **kể cả test thuần**, vì `tests/etl/conftest.py` nạp `tests/schema/conftest.py` đọc biến này lúc import. Nạp bằng `set -a; . ../.env; set +a`. Job cần `ETL_DATABASE_URL` (qua `core.env.load_dotenv`).
- **Không `--no-verify`, không force push.** Nhánh `feat/price-daily-etl`, commit nhỏ một mục đích, message tiếng Anh.
- Mỗi test **assert giá trị cụ thể**, expected lấy từ fixture thật — **cấm tính lại theo đúng cách code tính** (§4.5.3).
- Vòng TDD: **một seam → một test đỏ → code tối thiểu cho xanh**.
- Test đụng database chạy **dưới role `dlck_etl`** (`SET LOCAL ROLE dlck_etl` trong fixture `db`, listener `SET ROLE` ở test job) — §3.5.
- Header `Origin: https://fiinapp.bvsc.com.vn` bắt buộc; `PageSize=60` (whitelist cứng 30|60); hợp lệ là `status ∈ {0, "Success"}`.

## Cây file

| File | Trách nhiệm | Trạng thái |
|---|---|---|
| `backend/etl/price_fetch.py` | I/O — `Fetcher` giãn cách ≥ 0,5 s, retry, phân trang, ngắt khẩn 10 mã | tạo mới |
| `backend/etl/price_normalize.py` | Thuần — `PriceRow`, gộp trang chồng ngày, `summarize` | tạo mới |
| `backend/etl/price_guard.py` | Thuần — 5 vế chốt chặn lượt hằng ngày | tạo mới |
| `backend/etl/price_store.py` | Ghi kho — `list_codes`, UPSERT, `raw_close_mismatches`, mốc, con trỏ, bằng chứng, công tắc miền | tạo mới |
| `backend/etl/price_job.py` | Điều phối hai chế độ | tạo mới |
| `backend/etl/__main__.py` | Nhánh `price` + 3 cờ | sửa |
| `backend/tests/etl/test_e21..e25_price_*.py` | 5 file test theo module | tạo mới |
| `backend/tests/etl/fixtures/price/` | 3 fixture + README | ✅ **đã có sẵn** (commit cùng plan này) |
| `scripts/register-tasks.ps1` | Task thứ 10 `dlck-price` 15:40 | sửa |

**Fixture đã dựng sẵn** từ bản tải thật 2026-09-03 (README trong thư mục fixture ghi ca biên từng file): BID trang 1 **5 phiên** · BID trang 52 **1 phiên** · DMX trang 1 **18 phiên** = **24 phiên**.

---

## Task 1 — `price_fetch`

**Files:** Create `backend/etl/price_fetch.py` · Test `backend/tests/etl/test_e21_price_fetch.py`

**Interfaces — Produces:**
- `url(code: str, page: int) -> str`
- `class FetchError(Exception)` · `class SourceDown(FetchError)` · `class CodeInvalid(Exception)`
- `@dataclass FetchResult(pages: dict[str, list[str]], invalid: list[str], failed: list[str])`
- `class Fetcher(get, sleep=time.sleep, clock=time.monotonic)` với thuộc tính `retries`, `calls`; phương thức `pages(code, max_pages=1) -> list[str]` và `many(codes, max_pages=1) -> FetchResult`
- `open_fetcher(get=None, sleep=time.sleep, clock=time.monotonic)` — context manager, mở `httpx.Client` khi `get` là None

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/etl/test_e21_price_fetch.py
import json

import pytest

from etl import price_fetch as pf


def env(n, total=None, start=0, status="Success"):
    return json.dumps({"page": 1, "pageSize": 60, "totalCount": n if total is None else total,
                       "items": [{"tradingDate": f"2026-01-{(start + i) % 28 + 1:02d}T00:00:00"}
                                 for i in range(n)],
                       "packageId": None, "status": status, "errors": None})


INVALID = json.dumps({"page": 1, "pageSize": 60, "totalCount": 0, "items": None, "packageId": None,
                      "status": "Failed", "errors": ["Code not valid: VHM"]})


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


def fetcher(get, latency=1.8):
    """Fetcher với đồng hồ giả TRÔI theo latency mỗi lời gọi (trung vị thật 1,76 s > MIN_INTERVAL 0,5 s
    nên bộ giãn cách không ngủ) — chỉ backoff mới hiện trong `slept`. Đồng hồ đứng yên sẽ làm
    bộ giãn cách ngủ 0,5 s giữa mọi lời gọi và mọi assert về `slept` sai."""
    clock, slept = Clock(), []

    def timed_get(u):
        clock.t += latency
        return get(u)

    return pf.Fetcher(timed_get, sleep=slept.append, clock=clock), slept


def _code(u):
    return u.split("Code=")[1].split("&")[0]


def test_url_carries_organ_code_daily_page_and_size_60():
    assert pf.url("NHN", 2) == ("https://wlgw-technical.fiintrade.vn/PriceData/GetPriceData"
                                "?Code=NHN&Frequently=Daily&Page=2&PageSize=60&language=vi")


def test_status_zero_and_success_are_both_valid_without_retry():
    # Đo 2026-09-03: cùng endpoint trả lẫn 0 (số) và "Success" (chuỗi) — 2/16 lời gọi
    seen = []

    def get(u):
        seen.append(u)
        return 200, env(60, total=120, status=0) if "Page=1" in u else env(60, total=120)

    f, slept = fetcher(get)
    assert len(f.pages("BID", max_pages=None)) == 2
    assert f.retries == 0 and slept == []


def test_code_not_valid_raises_without_retry_or_sleep():
    f, slept = fetcher(lambda u: (200, INVALID))
    with pytest.raises(pf.CodeInvalid, match="VHM"):
        f.pages("VHM")
    assert slept == [] and f.calls == 1


def test_transient_failure_retries_with_backoff_then_succeeds():
    state = {"fail": 2}

    def get(u):
        if state["fail"]:
            state["fail"] -= 1
            return 500, "boom"
        return 200, env(3)

    f, slept = fetcher(get)
    assert len(f.pages("BID")) == 1
    assert f.retries == 2 and slept == [2, 4]


def test_exhausted_retries_raise_fetch_error_naming_code_and_page():
    body = '{"status":"Failed","errors":["Timeout performing GET (5000ms)"]}'   # 00-conventions §10.5
    f, slept = fetcher(lambda u: (200, body))
    with pytest.raises(pf.FetchError, match="BID trang 1"):
        f.pages("BID")
    assert slept == [2, 4, 8]


def test_pagination_stops_at_short_page_and_at_total_count_cap():
    calls = []

    def get(u):
        calls.append(u)
        p = int(u.split("Page=")[1].split("&")[0])
        return 200, env({1: 60, 2: 60, 3: 22}[p], total=142, start=p * 60)

    f, _ = fetcher(get)
    assert len(f.pages("BID", max_pages=None)) == 3 and len(calls) == 3      # 60·60·22, dừng ở trang ngắn

    calls.clear()
    f2, _ = fetcher(lambda u: (calls.append(u), (200, env(60, total=120)))[1])
    assert len(f2.pages("BID", max_pages=None)) == 2 and len(calls) == 2     # trần totalCount: không gọi trang 3 rỗng
    assert len(fetcher(lambda u: (200, env(60, total=3142)))[0].pages("BID", max_pages=1)) == 1


def test_min_interval_between_call_starts_sleeps_the_remainder():
    f, slept = fetcher(lambda u: (200, env(60, total=120)), latency=0.1)   # lời gọi mất 0,1 s
    f.pages("BID", max_pages=None)                    # 2 lời gọi
    assert slept == [pytest.approx(0.4)]              # 0,5 s giữa hai lần BẮT ĐẦU ⇒ ngủ 0,4


def test_ten_consecutive_failed_codes_abort_the_run():
    calls = []

    def get(u):
        calls.append(u)
        return 500, "down"

    f, _ = fetcher(get)
    with pytest.raises(pf.SourceDown, match="10 mã"):
        f.many([f"C{i}" for i in range(12)])
    assert len({_code(u) for u in calls}) == 10       # mã thứ 11 không được gọi


def test_many_collects_invalid_and_failed_codes_and_a_valid_answer_resets_the_streak():
    def get(u):
        code = _code(u)
        if code == "BAD":
            return 200, INVALID
        if code == "DOWN":
            return 500, "x"
        return 200, env(2)

    f, _ = fetcher(get)
    res = f.many(["A", "DOWN", "BAD", "B"])
    assert sorted(res.pages) == ["A", "B"] and res.invalid == ["BAD"] and res.failed == ["DOWN"]
```

- [ ] **Bước 2: Chạy để chắc chắn nó ĐỎ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e21_price_fetch.py -v`
Expected: FAIL — `ImportError: cannot import name 'price_fetch' from 'etl'`

- [ ] **Bước 3: Viết code tối thiểu cho xanh**

```python
# backend/etl/price_fetch.py
"""Tải PriceData/GetPriceData theo mã, tuần tự, có giãn cách (spec §5.2). I/O thuần.

Ba điều đo 2026-09-03 quyết định hình dạng module (measurements.md):
- `status` trả lẫn 0 và "Success" trên CÙNG endpoint ⇒ hợp lệ là status ∈ {0, "Success"};
  kiểm `== "Success"` như lát 1–2 sẽ thử lại vô ích ~1/8 lời gọi.
- Mã sai trả {"status":"Failed","errors":["Code not valid: X"]} ⇒ CodeInvalid, không thử lại.
- Trang trả < 60 bản ghi là trang cuối; totalCount chính xác ⇒ ceil(totalCount/60) làm trần.
"""
from __future__ import annotations

import contextlib
import json
import logging
import math
import time
from dataclasses import dataclass, field

import httpx

log = logging.getLogger("etl.price")

URL = "https://wlgw-technical.fiintrade.vn/PriceData/GetPriceData"
FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"      # bắt buộc cho *.fiintrade.vn (00-conventions §2)
PAGE_SIZE = 60                                    # whitelist cứng: chỉ 30 | 60 (09-fiin-market-price)
TIMEOUT = 60.0                                    # ~200 KB/trang, ~1,8 s
RETRIES = 3
BACKOFF = (2, 4, 8)
MIN_INTERVAL = 0.5                                # trần 2 request/giây (market-data-store §4.2)
MAX_CONSECUTIVE_FAILURES = 10                     # 10 mã liên tiếp hỏng = nguồn/mạng chết


class FetchError(Exception):
    """Một mã hỏng sau mọi lần thử."""


class SourceDown(FetchError):
    """Nhiều mã liên tiếp hỏng — dừng cả lượt thay vì đi hết 1.523 mã mà không ghi gì."""


class CodeInvalid(Exception):
    """Nguồn không biết mã này (`Code not valid`) — lỗi có tên, không thử lại."""


@dataclass
class FetchResult:
    pages: dict[str, list[str]] = field(default_factory=dict)
    invalid: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


def url(code: str, page: int) -> str:
    return f"{URL}?Code={code}&Frequently=Daily&Page={page}&PageSize={PAGE_SIZE}&language=vi"


def _parse(status: int, text: str) -> dict | None:
    if status != 200:
        return None
    try:
        d = json.loads(text)
    except ValueError:
        return None
    return d if isinstance(d, dict) else None


def _valid(d: dict | None) -> bool:
    return d is not None and d.get("status") in (0, "Success") and isinstance(d.get("items"), list)


def _code_invalid(d: dict | None) -> bool:
    return (d is not None and d.get("status") == "Failed"
            and any("Code not valid" in str(e) for e in (d.get("errors") or [])))


class Fetcher:
    """Giữ trạng thái giãn cách và bộ đếm cho trọn lượt. `get`/`sleep`/`clock` tiêm được để test."""

    def __init__(self, get, sleep=time.sleep, clock=time.monotonic):
        self._get, self._sleep, self._clock = get, sleep, clock
        self._last_start: float | None = None
        self._streak = 0
        self.retries = 0
        self.calls = 0

    def _request(self, code: str, page: int) -> tuple[int, str]:
        now = self._clock()
        if self._last_start is not None:
            wait = self._last_start + MIN_INTERVAL - now
            if wait > 0:
                self._sleep(wait)
                now = self._clock()
        self._last_start = now
        self.calls += 1
        return self._get(url(code, page))

    def _page(self, code: str, page: int) -> tuple[dict, str]:
        status, text = 0, ""
        for attempt in range(RETRIES + 1):
            status, text = self._request(code, page)
            d = _parse(status, text)
            if _valid(d):
                return d, text
            if _code_invalid(d):
                raise CodeInvalid(f"{code}: {d['errors']}")
            if attempt == RETRIES:
                break
            self._sleep(BACKOFF[attempt])
            self.retries += 1
        raise FetchError(f"{code} trang {page} hỏng sau {RETRIES + 1} lần (HTTP {status}): {text[:200]}")

    def _pages(self, code: str, max_pages: int | None) -> list[str]:
        d, text = self._page(code, 1)
        texts = [text]
        total = d.get("totalCount")
        cap = math.ceil(total / PAGE_SIZE) if isinstance(total, int) and total > 0 else None
        n = 1
        while (len(d["items"]) == PAGE_SIZE
               and (max_pages is None or n < max_pages)
               and (cap is None or n < cap)):
            n += 1
            d, text = self._page(code, n)
            texts.append(text)
        return texts

    def pages(self, code: str, max_pages: int | None = 1) -> list[str]:
        """Text các trang 1..n của một mã. Dừng ở trang < 60 bản ghi, ở max_pages, hoặc ở trần totalCount."""
        try:
            texts = self._pages(code, max_pages)
        except CodeInvalid:
            self._streak = 0                          # nguồn CÓ trả lời — không phải mạng chết
            raise
        except FetchError:
            self._streak += 1
            if self._streak >= MAX_CONSECUTIVE_FAILURES:
                raise SourceDown(f"{self._streak} mã liên tiếp hỏng — nguồn hoặc mạng chết, dừng lượt")
            raise
        self._streak = 0
        return texts

    def many(self, codes: list[str], max_pages: int | None = 1) -> FetchResult:
        res = FetchResult()
        for i, code in enumerate(codes, 1):
            try:
                res.pages[code] = self.pages(code, max_pages)
            except CodeInvalid:
                res.invalid.append(code)
            except SourceDown:
                raise
            except FetchError as e:
                res.failed.append(code)
                log.warning("%s", e)
            if i % 100 == 0:
                log.info("đã gọi %d/%d mã (%d lời gọi, %d retry)", i, len(codes), self.calls, self.retries)
        return res


@contextlib.contextmanager
def open_fetcher(get=None, sleep=time.sleep, clock=time.monotonic):
    if get is not None:                                   # test tiêm get giả, không mở kết nối
        yield Fetcher(get, sleep, clock)
        return
    # MỘT client cho trọn lượt (khuôn events_fetch) — mở lại mỗi mã là 1.523 lần bắt tay TLS
    with httpx.Client(timeout=TIMEOUT, headers={"Origin": FIIN_ORIGIN}) as client:
        def get_one(u: str) -> tuple[int, str]:
            r = client.get(u)
            return r.status_code, r.text
        yield Fetcher(get_one, sleep, clock)
```

- [ ] **Bước 4: Chạy lại, xanh**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e21_price_fetch.py -v`
Expected: `9 passed`

- [ ] **Bước 5: Commit**

```bash
git add etl/price_fetch.py tests/etl/test_e21_price_fetch.py
git commit -m "feat(etl): price fetch - paced, paginated, status 0 and Success both valid"
```

---

## Task 2 — `price_normalize`

**Files:** Create `backend/etl/price_normalize.py` · Test `backend/tests/etl/test_e22_price_normalize.py`

**Interfaces — Produces:**
- `@dataclass(frozen=True) PriceRow(organ_code, trading_date: date, close_adj, close_raw, open_value, highest_value, lowest_value: Decimal | None, payload: dict)`
- `@dataclass(frozen=True) CodeSummary(n_rows: int, latest: date | None)`
- `normalize_code(organ_code: str, texts: list[str]) -> tuple[list[PriceRow], int]` — dòng đã gộp theo ngày + số dòng chồng
- `summarize(texts: list[str]) -> CodeSummary`

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/etl/test_e22_price_normalize.py
import json
import pathlib
from datetime import date
from decimal import Decimal

from etl import price_normalize as pn

FIX = pathlib.Path(__file__).parent / "fixtures" / "price"


def text(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_maps_the_five_columns_and_the_date_from_the_real_first_row():
    rows, dups = pn.normalize_code("BID", [text("bid-page1-20260903.json")])
    r = rows[0]
    assert (r.organ_code, r.trading_date) == ("BID", date(2026, 9, 3))
    assert (r.close_adj, r.close_raw) == (Decimal("36450"), Decimal("36450"))
    assert (r.open_value, r.highest_value, r.lowest_value) == (Decimal("36750"), Decimal("36750"), Decimal("36400"))
    assert r.payload["totalMatchVolume"] == 3267266.0 and len(r.payload) == 99
    assert len(rows) == 5 and rows[-1].trading_date == date(2026, 8, 25) and dups == 0


def test_deep_row_keeps_adjusted_and_raw_close_apart():
    rows, _ = pn.normalize_code("BID", [text("bid-page52-20260903.json")])
    assert rows[0].trading_date == date(2014, 6, 3)
    assert rows[0].close_adj == Decimal("5747.8202873773")      # closeValue — đã điều chỉnh, giữ đủ chữ số
    assert rows[0].close_raw == Decimal("14500")                # closePrice — thô


def test_dividend_rows_match_the_dividend_slice_2_recorded():
    rows, _ = pn.normalize_code("MWJSC", [text("dmx-page1-20260903.json")])
    by = {r.trading_date: r for r in rows}
    before, on = by[date(2026, 8, 17)], by[date(2026, 8, 18)]
    assert (before.close_raw, before.close_adj) == (Decimal("88500"), Decimal("84499.8"))
    assert on.close_raw == on.close_adj == Decimal("83000")
    assert len(rows) == 18


def test_overlapping_pages_keep_the_first_seen_row_and_count_duplicates():
    page = json.loads(text("bid-page1-20260903.json"))
    # trang "cũ hơn" chồng hai ngày với trang 1, mang closeValue khác — phải bị bỏ
    older = {**page, "items": [{**page["items"][4], "closeValue": 1.0}, {**page["items"][0], "closeValue": 2.0}]}
    rows, dups = pn.normalize_code("BID", [text("bid-page1-20260903.json"), json.dumps(older)])
    got = {r.trading_date: r.close_adj for r in rows}
    assert dups == 2 and len(rows) == 5
    assert got[date(2026, 8, 25)] == Decimal("36700") and got[date(2026, 9, 3)] == Decimal("36450")


def test_null_numbers_become_none_not_zero():
    page = json.loads(text("bid-page1-20260903.json"))
    page["items"] = [{**page["items"][0], "openValue": None}]
    rows, _ = pn.normalize_code("BID", [json.dumps(page)])
    assert rows[0].open_value is None and rows[0].close_adj == Decimal("36450")


def test_summarize_counts_sessions_and_latest_without_keeping_rows():
    s = pn.summarize([text("bid-page1-20260903.json"), text("bid-page52-20260903.json")])
    assert s == pn.CodeSummary(6, date(2026, 9, 3))
    assert pn.summarize(['{"items": []}']) == pn.CodeSummary(0, None)
```

- [ ] **Bước 2: Chạy để chắc chắn nó ĐỎ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e22_price_normalize.py -v`
Expected: FAIL — `ImportError: cannot import name 'price_normalize' from 'etl'`

- [ ] **Bước 3: Viết code tối thiểu cho xanh**

```python
# backend/etl/price_normalize.py
"""Chuẩn hoá bản ghi getPriceData → PriceRow (spec §5.3). Thuần, không I/O.

Đo 2026-09-03: `closePrice` là giá THÔ khớp sàn, `closeValue` là giá đã điều chỉnh hồi tố
(measurements.md §1) — hai cột khác nhau của lược đồ, không phải hai tên của một giá.
Số đi qua Decimal(str(v)) để giữ đúng chữ số nguồn (5747.8202873773), không qua float8.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class PriceRow:
    organ_code: str
    trading_date: date
    close_adj: Decimal | None
    close_raw: Decimal | None
    open_value: Decimal | None
    highest_value: Decimal | None
    lowest_value: Decimal | None
    payload: dict


@dataclass(frozen=True)
class CodeSummary:
    n_rows: int
    latest: date | None


def _dec(v):
    return None if v is None else Decimal(str(v))


def _date(s: str) -> date:
    return date.fromisoformat(s[:10])


def _items(texts: list[str]):
    for text in texts:
        yield from json.loads(text)["items"]


def normalize_code(organ_code: str, texts: list[str]) -> tuple[list[PriceRow], int]:
    rows: list[PriceRow] = []
    seen: set[date] = set()
    dups = 0
    for it in _items(texts):
        d = _date(it["tradingDate"])
        if d in seen:
            dups += 1          # trang chồng ngày (phiên mới chen vào giữa hai lời gọi) — giữ bản thấy trước
            continue
        seen.add(d)
        rows.append(PriceRow(organ_code, d, _dec(it.get("closeValue")), _dec(it.get("closePrice")),
                             _dec(it.get("openValue")), _dec(it.get("highestValue")),
                             _dec(it.get("lowestValue")), it))
    return rows, dups


def summarize(texts: list[str]) -> CodeSummary:
    """Số phiên và ngày mới nhất — KHÔNG giữ bản ghi (guard trước khi parse 91.000 dict)."""
    dates = {_date(it["tradingDate"]) for it in _items(texts)}
    return CodeSummary(len(dates), max(dates) if dates else None)
```

- [ ] **Bước 4: Chạy lại, xanh**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e22_price_normalize.py -v`
Expected: `6 passed`

- [ ] **Bước 5: Commit**

```bash
git add etl/price_normalize.py tests/etl/test_e22_price_normalize.py
git commit -m "feat(etl): normalize price rows - closePrice is the raw close, closeValue the adjusted one"
```

---

## Task 3 — `price_guard`

**Files:** Create `backend/etl/price_guard.py` · Test `backend/tests/etl/test_e23_price_guard.py`

**Interfaces — Produces:**
- `MISSING_RATIO = 0.02` · `DROP_RATIO = 0.02`
- `@dataclass(frozen=True) GuardVerdict(ok: bool, reasons: tuple[str, ...])`
- `check(codes: int, with_data: int, invalid: int, failed: int, latest: date | None, today: date, baseline: dict | None) -> GuardVerdict` — `baseline = {"with_data": int, "latest_trading_date": "YYYY-MM-DD"}` hoặc None

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/etl/test_e23_price_guard.py
from datetime import date

from etl import price_guard as pg

TODAY = date(2026, 9, 4)
D = date(2026, 9, 3)
BASE = {"with_data": 1523, "latest_trading_date": "2026-09-03"}


def test_missing_codes_over_two_percent_are_refused_and_under_are_not():
    bad = pg.check(1523, 1492, invalid=21, failed=10, latest=D, today=TODAY, baseline=None)
    ok = pg.check(1523, 1493, invalid=20, failed=10, latest=D, today=TODAY, baseline=None)
    assert not bad.ok and "31/1523" in bad.reasons[0] and "21 mã sai" in bad.reasons[0]
    assert ok.ok


def test_drop_against_the_last_success_uses_two_percent():
    assert not pg.check(1523, 1480, 0, 0, D, TODAY, BASE).ok        # −2,8 %
    assert pg.check(1523, 1500, 0, 0, D, TODAY, BASE).ok             # −1,5 %


def test_future_or_regressing_latest_date_is_refused_with_the_dates_named():
    fut = pg.check(1523, 1523, 0, 0, date(2026, 9, 5), TODAY, BASE)
    back = pg.check(1523, 1523, 0, 0, date(2026, 9, 2), TODAY, BASE)
    assert not fut.ok and "2026-09-05" in fut.reasons[0] and "2026-09-04" in fut.reasons[0]
    assert not back.ok and "2026-09-02" in back.reasons[0] and "2026-09-03" in back.reasons[0]


def test_no_data_at_all_is_refused_even_without_a_baseline():
    v = pg.check(1523, 0, 0, 0, None, TODAY, None)
    assert not v.ok and "nguồn hỏng" in v.reasons[0]


def test_first_run_without_baseline_passes_on_clean_numbers():
    assert pg.check(1523, 1523, 0, 0, D, TODAY, None) == pg.GuardVerdict(True, ())
```

- [ ] **Bước 2: Chạy để chắc chắn nó ĐỎ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e23_price_guard.py -v`
Expected: FAIL — `ImportError: cannot import name 'price_guard' from 'etl'`

- [ ] **Bước 3: Viết code tối thiểu cho xanh**

```python
# backend/etl/price_guard.py
"""Chốt chặn lượt hằng ngày — năm vế (spec §5.4). Module thuần.

KHÁC lát 1 và 2: không có vế "ngày giao dịch" (nguồn không đóng dấu ngày nghỉ — đo 2026-09-03)
và không có vế "thiếu trang" (trang 1 luôn trọn). Chế độ --backfill không qua guard này.
"""
from dataclasses import dataclass
from datetime import date

MISSING_RATIO = 0.02   # mã sai + mã hỏng. Dự kiến ~0; mã mới lên sàn chưa có ở FiinTrade là ca hợp lệ, vài mã
DROP_RATIO = 0.02      # số mã có dữ liệu sụt so mốc lượt success gần nhất


@dataclass(frozen=True)
class GuardVerdict:
    ok: bool
    reasons: tuple[str, ...]


def check(codes: int, with_data: int, invalid: int, failed: int, latest: date | None,
          today: date, baseline: dict | None) -> GuardVerdict:
    reasons: list[str] = []
    if with_data == 0:                                                              # (0)
        reasons.append("không mã nào có dữ liệu — nguồn hỏng")
    missing = invalid + failed
    if codes and missing > codes * MISSING_RATIO:                                   # (i)
        reasons.append(f"{missing}/{codes} mã không có dữ liệu ({invalid} mã sai, {failed} mã hỏng)"
                       f" — quá {MISSING_RATIO:.0%}")
    base_n = (baseline or {}).get("with_data")
    if base_n and with_data < base_n * (1 - DROP_RATIO):                            # (ii)
        reasons.append(f"chỉ {with_data} mã có dữ liệu — sụt quá {DROP_RATIO:.0%} so mốc {base_n}")
    if latest is not None and latest > today:                                       # (iii)
        reasons.append(f"ngày mới nhất {latest} ở tương lai (hôm nay {today})")
    base_latest = (baseline or {}).get("latest_trading_date")
    if latest is not None and base_latest and latest < date.fromisoformat(base_latest):   # (iv)
        reasons.append(f"ngày mới nhất {latest} lùi so mốc {base_latest}")
    return GuardVerdict(ok=not reasons, reasons=tuple(reasons))
```

- [ ] **Bước 4: Chạy lại, xanh**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e23_price_guard.py -v`
Expected: `5 passed`

- [ ] **Bước 5: Commit**

```bash
git add etl/price_guard.py tests/etl/test_e23_price_guard.py
git commit -m "feat(etl): price guard - missing codes, drop, and date sanity"
```

---

## Task 4 — `price_store`

**Files:** Create `backend/etl/price_store.py` · Test `backend/tests/etl/test_e24_price_store.py`

**Interfaces — Consumes:** `PriceRow` (Task 2).
**Produces:**
- `JOB_DAILY = "market.price_daily"` · `JOB_BACKFILL = "market.price_backfill"` · `DOMAIN = "market.price"` · `SAMPLE = 20`
- `@dataclass(frozen=True) Code(security_id: int, ticker: str, organ_code: str)` · `@dataclass(frozen=True) CodeList(codes: list[Code], no_organ_code: list[str])`
- `list_codes(conn, tickers: list[str] | None = None) -> CodeList` — `ValueError` khi ticker lạ hoặc một organCode trỏ nhiều mã
- `apply(conn, batch: list[tuple[int, list[PriceRow]]], fetched_at: str) -> dict` — `{"rows_sent", "rows_changed"}`
- `raw_close_mismatches(conn, security_ids: list[int], since: date) -> tuple[int, list[str]]`
- `load_baseline(engine) -> dict | None` · `load_cursor(engine) -> str | None` · `save_progress(engine, run_id, stats)` · `store_refusal_evidence(engine, run_id, reasons, stats, pages)` · `upsert_domain_state(engine, watermark)`

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/etl/test_e24_price_store.py
import json
import pathlib
from datetime import date
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import price_normalize as pn
from etl import price_store as ps

FIX = pathlib.Path(__file__).parent / "fixtures" / "price"


def _seed(db, ticker, organ, security_type="stock"):
    iid = None
    if organ:
        iid = db.execute(sa.text("INSERT INTO market.issuer (name) VALUES (:n) RETURNING issuer_id"),
                         {"n": f"Test {ticker}"}).scalar_one()
        db.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                           " VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": organ})
    return db.execute(sa.text(
        "INSERT INTO market.security (ticker, exchange, security_type, issuer_id)"
        " VALUES (:t, 'HOSE', :ty, :i) RETURNING security_id"),
        {"t": ticker, "ty": security_type, "i": iid}).scalar_one()


def _rows(name="bid-page1-20260903.json", organ="BID"):
    return pn.normalize_code(organ, [(FIX / name).read_text(encoding="utf-8")])[0]


def _row(db, sid, col, d="2026-09-03"):
    return db.execute(sa.text(f"SELECT {col} FROM market.price_daily"
                              " WHERE security_id = :s AND trading_date = :d"), {"s": sid, "d": d}).scalar_one()


def test_list_codes_joins_the_organ_code_and_names_the_ones_without(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    sid = _seed(db, "ZZA", "ZZAORG")
    _seed(db, "ZZB", None)                                   # cổ phiếu niêm yết không có issuer
    _seed(db, "ZZE", "ZZEORG", security_type="etf")
    cl = ps.list_codes(db, ["ZZA", "ZZB"])
    assert cl.codes == [ps.Code(sid, "ZZA", "ZZAORG")] and cl.no_organ_code == ["ZZB"]
    with pytest.raises(ValueError, match="ZZE"):
        ps.list_codes(db, ["ZZA", "ZZE"])                    # ETF không phải cổ phiếu niêm yết


def test_list_codes_refuses_one_organ_code_pointing_at_two_listed_stocks(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = db.execute(sa.text("INSERT INTO market.issuer (name) VALUES ('Hai mã') RETURNING issuer_id")).scalar_one()
    db.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                       " VALUES (:i, 'fiintrade', 'ZZDUP')"), {"i": iid})
    for t in ("ZZX", "ZZY"):
        db.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id)"
                           " VALUES (:t, 'HOSE', 'stock', :i)"), {"t": t, "i": iid})
    with pytest.raises(ValueError, match="ZZDUP"):
        ps.list_codes(db, ["ZZX", "ZZY"])


def test_apply_inserts_then_skips_unchanged_then_updates_changed(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    sid = _seed(db, "ZZA", "BID")
    rows = _rows()
    assert ps.apply(db, [(sid, rows)], "2026-09-04T00:00:00+00:00") == {"rows_sent": 5, "rows_changed": 5}
    assert ps.apply(db, [(sid, rows)], "2026-09-04T00:01:00+00:00")["rows_changed"] == 0   # payload y hệt ⇒ bỏ qua
    assert _row(db, sid, "raw->'fiintrade'->>'fetched_at'") == "2026-09-04T00:00:00+00:00"
    changed = [type(r)(**{**r.__dict__, "close_adj": Decimal("1"),
                          "payload": {**r.payload, "closeValue": 1.0}}) for r in rows[:1]]
    assert ps.apply(db, [(sid, changed)], "2026-09-04T00:02:00+00:00")["rows_changed"] == 1
    assert _row(db, sid, "close_adj") == Decimal("1")
    assert _row(db, sid, "raw->'fiintrade'->>'fetched_at'") == "2026-09-04T00:02:00+00:00"
    assert db.execute(sa.text("SELECT count(*) FROM market.price_daily WHERE security_id = :s"),
                      {"s": sid}).scalar_one() == 5


def test_close_raw_is_filled_once_and_a_mismatch_is_counted_and_named(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    sid = _seed(db, "ZZA", "BID")
    db.execute(sa.text("INSERT INTO market.price_daily (security_id, trading_date, close_raw)"
                       " VALUES (:s, '2026-09-03', 999)"), {"s": sid})
    ps.apply(db, [(sid, _rows())], "2026-09-04T00:00:00+00:00")
    assert _row(db, sid, "close_raw") == Decimal("999")                     # điền một lần, không đè
    assert _row(db, sid, "close_raw", "2026-08-28") == Decimal("36850")     # dòng mới thì điền
    n, sample = ps.raw_close_mismatches(db, [sid], date(2026, 8, 1))
    assert n == 1 and sample == ["ZZA 2026-09-03 close_raw=999 closePrice=36450.0"]


def test_apply_merges_its_own_adapter_key_and_keeps_the_others(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    sid = _seed(db, "ZZA", "BID")
    db.execute(sa.text("INSERT INTO market.price_daily (security_id, trading_date, raw)"
                       " VALUES (:s, '2026-09-03', cast(:r AS jsonb))"),
               {"s": sid, "r": json.dumps({"bvsc": {"payload": {"closePrice": 36450}}})})
    ps.apply(db, [(sid, _rows()[:1])], "2026-09-04T00:00:00+00:00")
    raw = _row(db, sid, "raw")
    assert raw["bvsc"] == {"payload": {"closePrice": 36450}}                # khoá của writer khác nguyên vẹn
    assert raw["fiintrade"]["fetched_at"] == "2026-09-04T00:00:00+00:00"
    assert raw["fiintrade"]["payload"]["closeValue"] == 36450.0 and len(raw["fiintrade"]["payload"]) == 99
```

- [ ] **Bước 2: Chạy để chắc chắn nó ĐỎ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e24_price_store.py -v`
Expected: FAIL — `ImportError: cannot import name 'price_store' from 'etl'`

- [ ] **Bước 3: Viết code tối thiểu cho xanh**

```python
# backend/etl/price_store.py
"""Ghi kho cho job price (spec §5.5).

Một câu UPSERT mang ba luật: `coalesce` = điền `close_raw` MỘT LẦN (lược đồ: "không bao giờ
sửa"); `raw || EXCLUDED.raw` = writer chỉ đụng khoá adapter của mình (review vòng 2, C5);
`WHERE … IS DISTINCT FROM` = bỏ qua dòng payload không đổi — lượt hằng ngày ghi lại 60 phiên/mã
(91.000 dòng) mà thường chỉ 1–2 phiên/mã đổi. `rowcount` vì thế là số dòng THẬT SỰ đổi.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

import sqlalchemy as sa

from etl.price_normalize import PriceRow

JOB_DAILY = "market.price_daily"
JOB_BACKFILL = "market.price_backfill"
DOMAIN = "market.price"
BATCH = 2000
SAMPLE = 20            # bộ đếm phải nêu tên (bài học 3 lát 1) — nhưng không phình etl_run.stats

SQL_UPSERT = (
    "INSERT INTO market.price_daily (security_id, trading_date, close_adj, close_raw,"
    "   open_value, highest_value, lowest_value, raw)"
    " VALUES (:sid, :d, :ca, :cr, :o, :h, :l,"
    "   jsonb_build_object('fiintrade', jsonb_build_object('fetched_at', cast(:fa AS text),"
    "                                                      'payload', cast(:p AS jsonb))))"
    # cast(:fa AS text) bắt buộc: jsonb_build_object là hàm variadic "any", tham số trần trong đó
    # làm Postgres ném IndeterminateDatatype "could not determine data type of parameter $8".
    " ON CONFLICT (security_id, trading_date) DO UPDATE SET"
    "   close_adj = EXCLUDED.close_adj,"
    "   close_raw = coalesce(market.price_daily.close_raw, EXCLUDED.close_raw),"
    "   open_value = EXCLUDED.open_value, highest_value = EXCLUDED.highest_value,"
    "   lowest_value = EXCLUDED.lowest_value,"
    "   raw = market.price_daily.raw || EXCLUDED.raw,"
    "   ingested_at = clock_timestamp()"
    " WHERE market.price_daily.raw->'fiintrade'->'payload'"
    "   IS DISTINCT FROM EXCLUDED.raw->'fiintrade'->'payload'"
)


@dataclass(frozen=True)
class Code:
    security_id: int
    ticker: str
    organ_code: str


@dataclass(frozen=True)
class CodeList:
    codes: list[Code]
    no_organ_code: list[str]


def list_codes(conn, tickers: list[str] | None = None) -> CodeList:
    rows = conn.execute(sa.text(
        "SELECT s.security_id, s.ticker, x.external_code"
        " FROM market.security s"
        " LEFT JOIN market.issuer_external_id x"
        "   ON x.issuer_id = s.issuer_id AND x.source = 'fiintrade'"
        " WHERE s.security_type = 'stock' AND s.status = 'listed'"
        " ORDER BY s.ticker")).all()
    if tickers is not None:
        want = set(tickers)
        unknown = sorted(want - {r.ticker for r in rows})
        if unknown:
            raise ValueError(f"--codes có mã không phải cổ phiếu đang niêm yết: {unknown}")
        rows = [r for r in rows if r.ticker in want]
    codes = [Code(r.security_id, r.ticker, r.external_code) for r in rows if r.external_code]
    by_organ: dict[str, list[str]] = {}
    for c in codes:
        by_organ.setdefault(c.organ_code, []).append(c.ticker)
    dup = {k: v for k, v in by_organ.items() if len(v) > 1}
    if dup:
        raise ValueError(f"một organCode trỏ tới nhiều cổ phiếu niêm yết: {dup}")
    return CodeList(codes, [r.ticker for r in rows if not r.external_code])


def apply(conn, batch: list[tuple[int, list[PriceRow]]], fetched_at: str) -> dict:
    params = [{"sid": sid, "d": r.trading_date, "ca": r.close_adj, "cr": r.close_raw,
               "o": r.open_value, "h": r.highest_value, "l": r.lowest_value,
               "fa": fetched_at, "p": json.dumps(r.payload, ensure_ascii=False)}
              for sid, rows in batch for r in rows]
    stmt = sa.text(SQL_UPSERT)
    changed = 0
    for i in range(0, len(params), BATCH):
        changed += conn.execute(stmt, params[i:i + BATCH]).rowcount
    return {"rows_sent": len(params), "rows_changed": changed}


def raw_close_mismatches(conn, security_ids: list[int], since: date) -> tuple[int, list[str]]:
    """Mắt của quyết định spec §4.2: `close_raw` đã điền có còn khớp `closePrice` mới nhất không."""
    rows = conn.execute(sa.text(
        "SELECT s.ticker, p.trading_date, p.close_raw,"
        "       (p.raw->'fiintrade'->'payload'->>'closePrice')::numeric AS src"
        " FROM market.price_daily p JOIN market.security s USING (security_id)"
        " WHERE p.security_id = ANY(:ids) AND p.trading_date >= :since"
        "   AND p.close_raw IS DISTINCT FROM (p.raw->'fiintrade'->'payload'->>'closePrice')::numeric"
        " ORDER BY s.ticker, p.trading_date"), {"ids": security_ids, "since": since}).all()
    return len(rows), [f"{t} {d} close_raw={cr} closePrice={src}" for t, d, cr, src in rows[:SAMPLE]]


def load_baseline(engine) -> dict | None:
    """Mốc cho vế (ii)/(iv) — lượt success TOÀN TẬP gần nhất; lượt `--codes` (subset) không làm mốc."""
    with engine.connect() as c:
        row = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = :j AND status = 'success'"
            "   AND coalesce((stats->>'subset')::boolean, false) = false"
            " ORDER BY finished_at DESC LIMIT 1"), {"j": JOB_DAILY}).first()
    if row is None or not row[0]:
        return None
    return {"with_data": row[0].get("with_data"), "latest_trading_date": row[0].get("latest_trading_date")}


def load_cursor(engine) -> str | None:
    with engine.connect() as c:
        row = c.execute(sa.text(
            "SELECT stats->>'cursor' FROM ops.etl_run WHERE job = :j AND stats->>'cursor' IS NOT NULL"
            " ORDER BY run_id DESC LIMIT 1"), {"j": JOB_BACKFILL}).first()
    return row[0] if row else None


def save_progress(engine, run_id: int, stats: dict) -> None:
    """Ghi tiến độ vào chính dòng etl_run của lượt — chết giữa chừng vẫn giữ con trỏ."""
    with engine.begin() as c:
        c.execute(sa.text("UPDATE ops.etl_run SET stats = cast(:s AS jsonb) WHERE run_id = :r"),
                  {"s": json.dumps(stats, ensure_ascii=False), "r": run_id})


def store_refusal_evidence(engine, run_id: int, reasons, stats: dict,
                           pages: dict[str, list[str]]) -> None:
    """Bằng chứng vào staging.raw_payload — bộ đếm + 3 bản ghi đầu của ≤ 5 mã, KHÔNG lưu 300 MB trang thô."""
    sample = {}
    for code, texts in list(pages.items())[:5]:
        sample[code] = json.loads(texts[0])["items"][:3] if texts else []
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
            " VALUES ('fiintrade', 'price:refusal', 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
            {"p": json.dumps({"stats": stats, "sample": sample}, ensure_ascii=False),
             "m": json.dumps({"run_id": run_id, "reasons": list(reasons)}, ensure_ascii=False)})


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
            " VALUES (:dom, 'fiintrade', 'active', now(), :w)"
            " ON CONFLICT (domain, source) DO UPDATE"
            " SET last_success_at = now(), watermark = :w, status = 'active'"),
            {"dom": DOMAIN, "w": watermark})
```

- [ ] **Bước 4: Chạy lại, xanh**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e24_price_store.py -v`
Expected: `5 passed`. ⚠️ Nếu `rows_changed` ra `-1` hay `10` thay vì `5`/`0`/`1`: `rowcount` của executemany qua psycopg3 không cộng dồn như tin — **dừng, báo lại**, không sửa test cho khớp; đường lùi là đếm bằng `RETURNING 1` từng lô.

- [ ] **Bước 5: Commit**

```bash
git add etl/price_store.py tests/etl/test_e24_price_store.py
git commit -m "feat(etl): price store - one upsert carrying fill-once close_raw, adapter-key merge, no-op skip"
```

---

## Task 5 — `price_job` + CLI

**Files:** Create `backend/etl/price_job.py` · Modify `backend/etl/__main__.py` (thêm nhánh `price` trước dòng `print(f"etl: subcommand không hợp lệ…`) · Test `backend/tests/etl/test_e25_price_job.py`

**Interfaces — Consumes:** mọi thứ của Task 1–4; `omo_store.open_run(engine, job) -> int`, `omo_store.close_run(engine, run_id, status, stats=None, error=None)`.
**Produces:** `run(backfill: bool = False, codes: list[str] | None = None, max_minutes: float | None = None) -> int` — 0 xong · 1 guard từ chối · 2 lỗi/thiếu env.

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/etl/test_e25_price_job.py
import contextlib
import json
import os
import pathlib

import pytest
import sqlalchemy as sa

from etl import __main__ as cli
from etl import price_fetch, price_job, price_store

FIX = pathlib.Path(__file__).parent / "fixtures" / "price"
TEXT = {"ZZAORG": (FIX / "bid-page1-20260903.json").read_text(encoding="utf-8"),
        "ZZBORG": (FIX / "dmx-page1-20260903.json").read_text(encoding="utf-8"),
        "ZZCORG": (FIX / "bid-page52-20260903.json").read_text(encoding="utf-8")}
EMPTY = json.dumps({"page": 1, "pageSize": 60, "totalCount": 0, "items": [], "status": "Success", "errors": None})
INVALID = json.dumps({"page": 1, "pageSize": 60, "totalCount": 0, "items": None,
                      "status": "Failed", "errors": ["Code not valid: ZZBORG"]})
SEED = [("ZZA", "ZZAORG"), ("ZZB", "ZZBORG"), ("ZZC", "ZZCORG")]
MINE = ["ZZA", "ZZB", "ZZC"]


def _get(invalid=()):
    def get(url):
        code = url.split("Code=")[1].split("&")[0]
        if code in invalid:
            return 200, INVALID
        return 200, TEXT.get(code, EMPTY)        # mã của test khác trong DB test: rỗng, không phải lỗi
    return get


def _wire(monkeypatch, invalid=()):
    # KHÔNG dựng DSN từ engine.url — mật khẩu lộ ra traceback (§5). Đọc thẳng biến môi trường.
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.price_job.load_dotenv", lambda *a, **k: None)

    @contextlib.contextmanager
    def fake_open_fetcher():
        yield price_fetch.Fetcher(_get(invalid), sleep=lambda s: None)

    monkeypatch.setattr("etl.price_fetch.open_fetcher", fake_open_fetcher)


def _cleanup(engine):
    """Dọn ĐÚNG thứ mình cắm (mã ZZ*), không dọn cả bảng — bài học review lát 2 (#5)."""
    with engine.begin() as c:
        sids = c.execute(sa.text("SELECT security_id FROM market.security WHERE ticker LIKE 'ZZ%'")).scalars().all()
        iids = c.execute(sa.text("SELECT issuer_id FROM market.issuer_external_id"
                                 " WHERE source = 'fiintrade' AND external_code LIKE 'ZZ%ORG'")).scalars().all()
        c.execute(sa.text("DELETE FROM market.price_daily WHERE security_id = ANY(:s)"), {"s": sids})
        c.execute(sa.text("DELETE FROM market.security WHERE security_id = ANY(:s)"), {"s": sids})
        c.execute(sa.text("DELETE FROM market.issuer_external_id WHERE issuer_id = ANY(:i)"), {"i": iids})
        c.execute(sa.text("DELETE FROM market.issuer WHERE issuer_id = ANY(:i)"), {"i": iids})
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job IN ('market.price_daily', 'market.price_backfill')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE endpoint_key = 'price:refusal'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE domain = 'market.price'"))


@pytest.fixture()
def price_db(migrated_engine):
    """Dọn TRƯỚC và SAU — teardown chạy cả khi test đỏ."""
    _cleanup(migrated_engine)
    with migrated_engine.begin() as c:
        for t, org in SEED:
            iid = c.execute(sa.text("INSERT INTO market.issuer (name) VALUES (:n) RETURNING issuer_id"),
                            {"n": t}).scalar_one()
            c.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                              " VALUES (:i, 'fiintrade', :c)"), {"i": iid, "c": org})
            c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type, issuer_id)"
                              " VALUES (:t, 'HOSE', 'stock', :i)"), {"t": t, "i": iid})
    yield migrated_engine
    _cleanup(migrated_engine)


ROWS = ("SELECT count(*) FROM market.price_daily p JOIN market.security s USING (security_id)"
        " WHERE s.ticker LIKE 'ZZ%'")
LAST = "SELECT status, stats, error FROM ops.etl_run WHERE job = :j ORDER BY run_id DESC LIMIT 1"


def _last(engine, job):
    with engine.begin() as c:
        return c.execute(sa.text(LAST), {"j": job}).one()


def _rows(engine):
    with engine.begin() as c:
        return c.execute(sa.text(ROWS)).scalar_one()


def test_missing_env_exits_two(monkeypatch):
    monkeypatch.delenv("ETL_DATABASE_URL", raising=False)
    monkeypatch.setattr("etl.price_job.load_dotenv", lambda *a, **k: None)
    assert price_job.run() == 2


def test_daily_run_writes_rows_records_stats_and_domain_state_then_is_idempotent(price_db, monkeypatch):
    _wire(monkeypatch)
    assert price_job.run() == 0
    status, stats, _ = _last(price_db, "market.price_daily")
    with price_db.begin() as c:
        wm = c.execute(sa.text("SELECT watermark FROM ops.data_domain_state WHERE domain = 'market.price'")).scalar_one()
    assert _rows(price_db) == 24 and status == "success"                 # 5 + 18 + 1 phiên của ba fixture
    assert stats["with_data"] == 3 and stats["rows_sent"] == 24 and stats["rows_changed"] == 24
    assert stats["invalid"] == 0 and stats["failed"] == 0 and stats["raw_close_mismatch"] == 0
    assert stats["latest_trading_date"] == "2026-09-03" and wm == "2026-09-03"
    assert "subset" not in stats
    assert price_job.run() == 0                                          # lượt hai: không dòng nào đổi
    _, stats2, _ = _last(price_db, "market.price_daily")
    assert _rows(price_db) == 24 and stats2["rows_sent"] == 24 and stats2["rows_changed"] == 0


def test_guard_refusal_writes_nothing_and_leaves_evidence(price_db, monkeypatch):
    _wire(monkeypatch, invalid=("ZZBORG",))                              # 1/3 mã sai = 33 % > 2 %
    assert price_job.run(codes=MINE) == 1
    status, stats, err = _last(price_db, "market.price_daily")
    with price_db.begin() as c:
        ev = c.execute(sa.text("SELECT meta FROM staging.raw_payload WHERE endpoint_key = 'price:refusal'")).scalar_one()
    assert _rows(price_db) == 0 and status == "failed" and "1/3 mã" in err
    assert stats["invalid_tickers"] == ["ZZB"] and stats["subset"] is True
    assert ev["reasons"] and "quá 2%" in ev["reasons"][0]


def test_subset_run_does_not_become_the_baseline_nor_move_the_domain_watermark(price_db, monkeypatch):
    _wire(monkeypatch)
    assert price_job.run(codes=["ZZA"]) == 0
    assert price_store.load_baseline(price_db) is None
    with price_db.begin() as c:
        assert c.execute(sa.text("SELECT count(*) FROM ops.data_domain_state WHERE domain = 'market.price'")).scalar_one() == 0


def test_backfill_budget_stops_after_one_code_and_the_next_run_resumes_to_the_end(price_db, monkeypatch):
    _wire(monkeypatch)
    with price_db.connect() as c:
        order = [x.ticker for x in price_store.list_codes(c).codes]
    assert price_job.run(backfill=True, max_minutes=0) == 0            # ngân sách 0: xong mã đầu rồi dừng
    _, s1, _ = _last(price_db, "market.price_backfill")
    assert (s1["cursor"], s1["codes_done"], s1["budget_hit"], s1["pass_complete"]) == (order[0], 1, True, False)
    assert price_job.run(backfill=True) == 0
    _, s2, _ = _last(price_db, "market.price_backfill")
    assert (s2["cursor"], s2["codes_done"], s2["pass_complete"]) == (order[-1], len(order) - 1, True)
    assert _rows(price_db) == 24
    assert price_job.run(backfill=True, max_minutes=0) == 0            # hết vòng ⇒ vòng mới từ mã đầu
    _, s3, _ = _last(price_db, "market.price_backfill")
    assert s3["cursor"] == order[0]


def test_backfill_with_codes_touches_neither_cursor_nor_pass_flag(price_db, monkeypatch):
    _wire(monkeypatch)
    assert price_job.run(backfill=True, codes=["ZZB"]) == 0
    _, s, _ = _last(price_db, "market.price_backfill")
    assert s["subset"] is True and s["cursor"] is None and s["pass_complete"] is False
    assert s["codes_done"] == 1 and s["rows_sent"] == 18 and price_store.load_cursor(price_db) is None


def test_job_runs_under_the_etl_role(price_db, monkeypatch):
    """§3.5: mọi đường đọc/ghi của cả hai chế độ phải chạy dưới đúng quyền production."""
    _wire(monkeypatch)
    real_create = price_job.sa.create_engine

    def create_engine_with_role(url, **kw):
        eng = real_create(url, **kw)

        @sa.event.listens_for(eng, "connect")
        def _set_role(dbapi_conn, _rec):
            cur = dbapi_conn.cursor(); cur.execute("SET ROLE dlck_etl"); cur.close()

        return eng

    monkeypatch.setattr(price_job.sa, "create_engine", create_engine_with_role)
    assert price_job.run(codes=MINE) == 0
    assert price_job.run(backfill=True, codes=["ZZA"]) == 0


def test_cli_parses_backfill_codes_and_max_minutes(monkeypatch):
    seen = {}
    monkeypatch.setattr("etl.price_job.run", lambda **kw: seen.update(kw) or 0)
    assert cli.main(["price", "--backfill", "--codes", "bid, dmx", "--max-minutes", "5"]) == 0
    assert seen == {"backfill": True, "codes": ["BID", "DMX"], "max_minutes": 5.0}
    assert cli.main(["price"]) == 0
    assert seen == {"backfill": False, "codes": None, "max_minutes": None}
```

- [ ] **Bước 2: Chạy để chắc chắn nó ĐỎ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e25_price_job.py -v`
Expected: FAIL — `ImportError: cannot import name 'price_job' from 'etl'`

- [ ] **Bước 3: Viết code tối thiểu cho xanh**

```python
# backend/etl/price_job.py
"""Một lần chạy price: list_codes → fetch → (summarize → guard) → apply → close_run (spec §5).

Hai chế độ dùng chung fetch/normalize/store:
- hằng ngày: trang 1 mọi mã, MỘT giao dịch, guard TRƯỚC commit (khuôn events_job);
- --backfill: mọi trang, mỗi mã một giao dịch, con trỏ ghi sau từng mã, ngân sách --max-minutes
  kiểm GIỮA hai mã (mã đang dở luôn được làm xong).
"""
from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_store, price_fetch, price_guard, price_normalize, price_store

log = logging.getLogger("etl.price")
VN = ZoneInfo("Asia/Ho_Chi_Minh")


class GuardRefused(Exception):
    def __init__(self, verdict):
        self.verdict = verdict
        super().__init__("; ".join(verdict.reasons))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _names(by_organ, codes):
    return [by_organ[c].ticker for c in codes[:price_store.SAMPLE]]


def run(backfill: bool = False, codes: list[str] | None = None,
        max_minutes: float | None = None) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    load_dotenv()
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        log.error("thiếu ETL_DATABASE_URL")
        return 2
    engine = sa.create_engine(url)
    try:
        return _backfill(engine, codes, max_minutes) if backfill else _daily(engine, codes)
    finally:
        engine.dispose()


def _daily(engine, tickers: list[str] | None) -> int:
    run_id = omo_store.open_run(engine, price_store.JOB_DAILY)
    t0 = time.monotonic()
    stats: dict = {}
    try:
        with engine.connect() as conn:
            cl = price_store.list_codes(conn, tickers)
        by_organ = {c.organ_code: c for c in cl.codes}
        with price_fetch.open_fetcher() as f:
            res = f.many([c.organ_code for c in cl.codes], max_pages=1)
            retries = f.retries
        summaries = {code: price_normalize.summarize(texts) for code, texts in res.pages.items()}
        with_data = sum(1 for s in summaries.values() if s.n_rows)
        latest = max((s.latest for s in summaries.values() if s.latest), default=None)
        subset = tickers is not None
        baseline = None if subset else price_store.load_baseline(engine)
        stats = {"codes": len(cl.codes), "with_data": with_data,
                 "invalid": len(res.invalid), "invalid_tickers": _names(by_organ, res.invalid),
                 "failed": len(res.failed), "failed_tickers": _names(by_organ, res.failed),
                 "no_organ_code": cl.no_organ_code[:price_store.SAMPLE], "retries": retries,
                 "latest_trading_date": latest.isoformat() if latest else None}
        if subset:
            stats["subset"] = True                 # lượt --codes không được làm mốc cho lượt toàn tập
        try:
            verdict = price_guard.check(len(cl.codes), with_data, len(res.invalid), len(res.failed),
                                        latest, datetime.now(VN).date(), baseline)
            if not verdict.ok:
                raise GuardRefused(verdict)
            fetched_at = _now_iso()
            sent = changed = dups = 0
            sids: list[int] = []
            since = None
            with engine.begin() as conn:
                for code, texts in res.pages.items():
                    rows, d = price_normalize.normalize_code(code, texts)
                    if not rows:
                        continue
                    a = price_store.apply(conn, [(by_organ[code].security_id, rows)], fetched_at)
                    sent += a["rows_sent"]
                    changed += a["rows_changed"]
                    dups += d
                    sids.append(by_organ[code].security_id)
                    lo = min(r.trading_date for r in rows)
                    since = lo if since is None or lo < since else since
                mism, sample = price_store.raw_close_mismatches(conn, sids, since) if sids else (0, [])
        except GuardRefused as e:
            price_store.store_refusal_evidence(engine, run_id, e.verdict.reasons, stats, res.pages)
            omo_store.close_run(engine, run_id, "failed", stats,
                                error="guard refused: " + "; ".join(e.verdict.reasons))
            log.error("price từ chối: %s", e.verdict.reasons)
            return 1
        stats.update({"rows_sent": sent, "rows_changed": changed, "dup_dates": dups,
                      "raw_close_mismatch": mism, "raw_close_mismatch_sample": sample,
                      "elapsed_s": round(time.monotonic() - t0)})
        omo_store.close_run(engine, run_id, "success", stats)
        if not subset:
            price_store.upsert_domain_state(engine, stats["latest_trading_date"])
        log.info("price xong: %s", stats)
        return 0
    except Exception as e:  # noqa: BLE001 — job biên ngoài: mọi lỗi đều phải vào etl_run
        omo_store.close_run(engine, run_id, "failed", stats or None, error=f"{type(e).__name__}: {e}")
        log.exception("price thất bại")
        return 2


def _backfill(engine, tickers: list[str] | None, max_minutes: float | None) -> int:
    run_id = omo_store.open_run(engine, price_store.JOB_BACKFILL)
    t0 = time.monotonic()
    deadline = None if max_minutes is None else t0 + max_minutes * 60
    stats: dict = {"cursor": None, "codes_done": 0, "pages": 0, "rows_sent": 0, "rows_changed": 0,
                   "invalid_tickers": [], "failed_tickers": [], "retries": 0,
                   "budget_hit": False, "pass_complete": False, "elapsed_s": 0}
    try:
        with engine.connect() as conn:
            cl = price_store.list_codes(conn, tickers)
        todo = cl.codes
        if tickers is None:
            cursor = price_store.load_cursor(engine)
            after = [c for c in todo if c.ticker > cursor] if cursor else todo
            if cursor and not after:
                log.info("con trỏ %s đã ở cuối danh sách — bắt đầu vòng mới từ %s", cursor, todo[0].ticker)
            elif cursor:
                log.info("tiếp tục sau con trỏ %s: còn %d mã", cursor, len(after))
                todo = after
        else:
            stats["subset"] = True
        with price_fetch.open_fetcher() as f:
            for i, c in enumerate(todo, 1):
                texts: list[str] = []
                try:
                    texts = f.pages(c.organ_code, max_pages=None)
                except price_fetch.CodeInvalid:
                    stats["invalid_tickers"].append(c.ticker)
                except price_fetch.SourceDown:
                    raise
                except price_fetch.FetchError as e:
                    stats["failed_tickers"].append(c.ticker)
                    log.warning("%s hỏng: %s", c.ticker, e)
                if texts:
                    rows, _ = price_normalize.normalize_code(c.organ_code, texts)
                    if rows:
                        with engine.begin() as conn:
                            a = price_store.apply(conn, [(c.security_id, rows)], _now_iso())
                        stats["rows_sent"] += a["rows_sent"]
                        stats["rows_changed"] += a["rows_changed"]
                    stats["pages"] += len(texts)
                stats["codes_done"] += 1
                stats["retries"] = f.retries
                if tickers is None:
                    stats["cursor"] = c.ticker
                stats["elapsed_s"] = round(time.monotonic() - t0)
                price_store.save_progress(engine, run_id, stats)
                if i % 20 == 0:
                    log.info("backfill %d/%d mã, %d trang, %d dòng đổi", i, len(todo), stats["pages"],
                             stats["rows_changed"])
                if deadline is not None and time.monotonic() >= deadline and i < len(todo):
                    stats["budget_hit"] = True
                    break
            else:
                stats["pass_complete"] = tickers is None       # hết danh sách, không vì ngân sách
        omo_store.close_run(engine, run_id, "success", stats)
        log.info("backfill xong: %s", stats)
        return 0
    except Exception as e:  # noqa: BLE001
        omo_store.close_run(engine, run_id, "failed", stats, error=f"{type(e).__name__}: {e}")
        log.exception("backfill thất bại")
        return 2
```

Nhánh CLI — chèn vào `backend/etl/__main__.py` ngay trước dòng `print(f"etl: subcommand không hợp lệ…`, và sửa chuỗi hỗ trợ thành `(hỗ trợ: omo, refdata, screener, events, price)`:

```python
    if args[0] == "price":
        import etl.price_job
        parser = argparse.ArgumentParser(prog="etl price")
        parser.add_argument("--backfill", action="store_true")
        parser.add_argument("--codes", type=lambda s: [t.strip().upper() for t in s.split(",") if t.strip()])
        parser.add_argument("--max-minutes", type=float, dest="max_minutes")
        parsed = parser.parse_args(args[1:])
        return etl.price_job.run(backfill=parsed.backfill, codes=parsed.codes,
                                 max_minutes=parsed.max_minutes)
```

- [ ] **Bước 4: Chạy lại, xanh**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e25_price_job.py -v`
Expected: `8 passed`

- [ ] **Bước 5: Chạy TRỌN bộ test backend**

Run: `PYTHONIOENCODING=utf-8 uv run pytest -q`
Expected: `432 passed, 2 skipped` *(399 mốc sau lát 2 + 9 + 6 + 5 + 5 + 8 = 33 mới)*. Có test đỏ ngoài 5 file mới ⇒ **dừng, báo nguyên trạng**, không sửa test có sẵn.

- [ ] **Bước 6: Commit**

```bash
git add etl/price_job.py etl/__main__.py tests/etl/test_e25_price_job.py
git commit -m "feat(etl): price job - daily page-1 run and resumable backfill, 'etl price' subcommand"
```

---

## Task 6 — Chạy thật dưới credential production (AC2 → AC7)

Người điều phối tự chạy từ `backend/` với `set -a; . ../.env; set +a`. **Không giao subagent.** Ghi output thật vào [`ledger.md`](ledger.md).

- [ ] **AC2 — chạy thử 3 mã trước** (§3.5: chạy tay chính lệnh đó dưới đúng credential trước lượt toàn tập)

```bash
PYTHONIOENCODING=utf-8 uv run python -m etl price --codes BID,VHM,TD6
```
Expected: exit 0; log `price xong: {'codes': 3, 'with_data': 3, … 'rows_sent': 180, 'rows_changed': 180, 'raw_close_mismatch': 0, 'subset': True}`; `SELECT count(*) FROM market.price_daily` = 180.

- [ ] **AC3 — lượt hằng ngày toàn tập** (~45 phút)

```bash
PYTHONIOENCODING=utf-8 uv run python -m etl price
```
Expected: exit 0; `with_data + invalid + failed = codes`; `raw_close_mismatch = 0`; tổng `count(*)` = `rows_sent` + 0 dòng mới ngoài 3 mã đã có; mỗi `security_id` có đúng số phiên trang 1 trả (≤ 60). Ghi `elapsed_s` và `retries` vào ledger — **đây là phép đo nhịp tuần tự 1.523 lời gọi** cho 00-conventions §10.

- [ ] **AC4 — idempotent**

```bash
PYTHONIOENCODING=utf-8 uv run python -m etl price
```
Expected: exit 0; `rows_changed = 0` *(hoặc = số phiên T+1 vừa được điền dòng tiền nếu lượt hai chạy sang ngày khác — nêu rõ trong ledger)*; `count(*)` không đổi.

- [ ] **AC5 — guard từ chối bằng đột biến**: tạm sửa `price_fetch._valid`/`_code_invalid` bằng script thay chuỗi *(không dùng `git checkout` để khôi phục — bài học lát 2)* để ~3 % mã đầu bảng trả `Code not valid`, chạy `--codes` 100 mã đầu ⇒ exit 1, `count(*)` trước/sau bằng nhau, 1 dòng `price:refusal`. Khôi phục bằng thay chuỗi ngược; `git diff --stat` = 0.

- [ ] **AC6 — `price_factor` có nghĩa trên lịch sử**

```bash
PYTHONIOENCODING=utf-8 uv run python -m etl price --backfill --codes DMX,BID
```
rồi `SELECT trading_date, factor FROM market.price_factor pf JOIN market.security USING (security_id) WHERE ticker = 'DMX' AND trading_date BETWEEN '2026-08-14' AND '2026-08-19' ORDER BY 1` ⇒ `0.9548 · 0.9548 · 1 · 1`; BID có ≥ 3.100 dòng, dòng 2014 có `factor ≈ 0.3964`.

- [ ] **AC7 — backfill tiếp tục được**

```bash
PYTHONIOENCODING=utf-8 uv run python -m etl price --backfill --max-minutes 3
PYTHONIOENCODING=utf-8 uv run python -m etl price --backfill --max-minutes 3
```
Expected: lượt 1 `cursor = X`, `budget_hit = true`; lượt 2 bắt đầu sau `X` (log *"tiếp tục sau con trỏ X"*), `codes_done` không chồng.

---

## Task 7 — Task Scheduler + tài liệu sống

**Files:** Modify `scripts/register-tasks.ps1` · `backend/README.md` · `README.md` · `docs/20-design/service-topology.md` · `docs/10-sources/market/09-fiin-market-price.md` · `docs/10-sources/market/00-conventions.md` · `docs/20-design/market-data-store.md` · `docs/00-overview/roadmap.md` · `docs/90-records/README.md` · Create `docs/90-records/plans/2026-09-03-price-daily-etl/ledger.md`

- [ ] **Bước 1: Task thứ 10** — chèn sau khối `dlck-events` trong `scripts/register-tasks.ps1`:

```powershell
Write-Host "Đăng ký price (15:40 ngày làm việc — sau screener 15:20 và OMO 15:30; ~45 phút tuần tự, xong trước 18:00 của OMO):"
Register-DlckTask -TaskName "dlck-price" -AtTime "15:40" -ModuleArgs "etl price" -LogFile "price.log"
# -MustNotContain: task tự động KHÔNG BAO GIỜ chạy backfill (25–40 giờ, chạy tay ngoài giờ có người nhìn).
Assert-TaskCommand -TaskName "dlck-price" -MustContain "python -m etl price" -MustNotContain "--backfill"
```
và đổi ba chuỗi `9 task` → `10 task` trong cùng file (`Đã kiểm lệnh của cả 9 task`, `Cả 9 task đăng ký S4U`). AC8 (đăng ký thật) cần cửa sổ admin — chủ dự án chạy; kiểm `(Get-ScheduledTask -TaskName dlck-price).Triggers[0].StartBoundary` có `T15:40:00+07:00`, rồi `Disable-ScheduledTask`.

- [ ] **Bước 2: Tài liệu** theo bảng spec §8 — mỗi file một mục sửa, kèm *(đo 2026-09-03)* ở tầng reference. Sau khi sửa chạy phép quét:

```bash
git grep -n "1\.974\|Cả 9 task\|9 task\|chỉ có ở phiên hiện tại\|close_raw" -- ':!docs/90-records' ':!docs/00-overview/decisions'
```
Mọi hit còn lại phải **hoặc đã đúng, hoặc thuộc vùng lịch sử**.

- [ ] **Bước 3: Ledger** — `ledger.md` ghi output thật của Task 6, số test, review hai trục (Task 8).

- [ ] **Bước 4: Commit** từng mốc: `chore(ops): register dlck-price at 15:40` · `docs(price): sync the living docs to what getPriceData actually returns` · `docs(ledger): …`.

---

## Task 8 — Review toàn nhánh hai trục, verify, merge

- [ ] Hai reviewer độc lập (subagent **`opus`**, chạy song song, không thấy nhau): trục **Chuẩn** (đúng repo + code smell) và trục **Spec** (thiếu/sai/scope-creep) — báo riêng, không xếp hạng chéo. Sửa cái thật, ghi ledger.
- [ ] `PYTHONIOENCODING=utf-8 uv run pytest -q` — dán output thật.
- [ ] Merge `feat/price-daily-etl` vào `main` bằng `git merge --no-ff`, không force push.

## Tự kiểm plan (đã chạy trước khi giao)

- **Phủ spec:** §5.2 → Task 1 · §5.3 → Task 2 · §5.4 → Task 3 · §5.5 → Task 4 · §5.1/§5.6 → Task 5, 7 · §6 seam 1–22 → test e21–e25 (seam 1–8 e21 · 9–11 e22 · 12–14 e23 · 15–18 e24 · 19–22 e25) · §7 AC1 → Task 5 bước 5 · AC2–AC7 → Task 6 · AC8 → Task 7 · §8 → Task 7.
- **Placeholder:** không có.
- **Nhất quán kiểu:** `Fetcher.many` trả `FetchResult` với `pages/invalid/failed` — Task 5 đọc đúng ba tên; `price_store.apply` nhận `list[tuple[int, list[PriceRow]]]` và trả `rows_sent/rows_changed` — Task 5 cộng đúng hai khoá; `list_codes` trả `CodeList(codes, no_organ_code)` — Task 5 dùng `.codes`/`.no_organ_code`; `close_run(engine, run_id, status, stats, error=)` — đúng chữ ký `omo_store`.
