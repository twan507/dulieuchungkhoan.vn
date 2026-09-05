# Lát 7b — cập nhật trong phiên: kế hoạch thực thi

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ba job `yahoo`/`binance`/`wichart` chạy được lượt `--intraday` cửa sổ ngắn, nến/điểm đang chạy vào kho và bị ghi đè tới khi phiên đóng; mọi nguồn giãn cách ngẫu nhiên 1–5 s; Yahoo bao 17 cặp FX; CNY về ECB.

**Architecture:** Không migration. Lõi `series_job` nhận cờ `intraday` và truyền xuống `fetch_all` của từng nguồn (chỉ đổi cửa sổ); hai luật cắt nến đang chạy bị bỏ ở `yahoo_normalize`/`binance_normalize`, dedupe theo ngày sàn giữ nguyên. `http_fetch.Fetcher` thay `min_interval` bằng giãn cách ngẫu nhiên có `rng` bơm được; `wichart_fetch` thành lớp bọc mỏng quanh fetcher chung. Registry đổi ở ba module (Yahoo +17, ECB +CNY, FRED −1).

**Tech Stack:** Python 3.12, `uv run`, pytest (DB test thật qua `TEST_DATABASE_URL`, fixture `migrated_engine`), httpx, SQLAlchemy Core, Postgres 16.

**Spec:** [`spec.md`](spec.md) — plan này lập luận từ spec; executor đọc cả hai. Brief gốc: [`brief.md`](brief.md).

## Global Constraints

- Chạy mọi lệnh Python từ `backend/` với `PYTHONIOENCODING=utf-8` (CLAUDE.md §5); test: `uv run pytest tests/etl/<file> -q`. Toàn bộ bộ test: `uv run pytest -q` (trước lát: **709 passed, 2 skipped**).
- **Subagent không commit** — ghi file, controller commit theo mốc (CLAUDE.md §4.2). Không tạo `.superpowers/` trong repo; artifact tạm ở scratchpad ngoài repo.
- Không đụng lược đồ (`database/migrations/`), `series_store.py`, `registry.py`, `series_guard.py`, FRED/LBMA fetch-normalize ngoài chữ ký `fetch_all`.
- Expected trong test là **literal** từ fixture/spec, không tính lại theo cách code tính (CLAUDE.md §4.5.3). Mỗi test assert giá trị cụ thể và có ít nhất một case biên.
- Style: theo file hiện có (docstring tiếng Việt một đoạn đầu file, hằng UPPER, hàm ngắn, không abstraction mới). Không "tiện tay" sửa code lân cận.
- Mã FX Yahoo: `fx.usd_<ccy>.market` (spec §4.3). `INTRADAY` WiChart = `freq == 'd'` (spec §4.4). Giãn cách `[1.0, 5.0]` s, không trước lời gọi đầu (spec §4.6-III).
- Khoá FRED không được xuất hiện trong log/stats/test output (fred.md Bẫy 7).

## Bản đồ file

| File | Task | Trách nhiệm sau lát |
|---|---|---|
| `backend/etl/http_fetch.py` | 1 | Fetcher chung: giãn cách ngẫu nhiên, retry/backoff, `gaps` |
| `backend/etl/{fred,lbma,yahoo,binance}_fetch.py` | 1, 3 | bỏ `min_interval`; nhận `intraday` |
| `backend/etl/wichart_fetch.py` | 2 | mặt ngoài lát 6, ruột `http_fetch` |
| `backend/etl/series_job.py` | 3 | cờ `intraday`, `supports_intraday`, loại trừ backfill |
| `backend/etl/{yahoo,binance}_job.py` · `__main__.py` | 3, 6 | tham số/cờ `--intraday` |
| `backend/etl/yahoo_normalize.py` · `binance_normalize.py` | 4 | bỏ luật cắt nến đang chạy |
| `backend/etl/yahoo_registry.py` · `fx_registry.py` · `fx_fetch.py` · `fred_registry.py` | 5 | +17 FX · +CNY · −DEXCHUS |
| `backend/etl/wichart_job.py` | 6 | `intraday=True` = lượt trên `freq == 'd'` |
| `backend/tests/etl/test_e50_http_fetch_gap.py` (mới) · `test_e51_cli_intraday.py` (mới) | 1, 3 | seam fetcher chung, CLI |
| `backend/tests/etl/test_e37`, `e41`, `e43`, `e44`, `e45`, `e47`, `e48`, `e49` | 2–6 | cập nhật |
| `backend/tests/etl/fixtures/global/yahoo-EURX-5d.json` · `yahoo-CADX-5d.json` · `binance-BTCUSDT-3.json` · `ecb-2026-08.json` (thay) | 0 | mẫu thật 2026-09-05 |

---

### Task 0: Chụp fixture thật và chốt số đo vào spec *(controller tự làm — cần nhìn output)*

**Files:**
- Create: `backend/tests/etl/fixtures/global/yahoo-EURX-5d.json`, `yahoo-CADX-5d.json`, `binance-BTCUSDT-3.json`
- Replace: `backend/tests/etl/fixtures/global/ecb-2026-08.json` (cùng cửa sổ `2026-07-31..2026-08-31`, thêm `CNY`)
- Modify: `spec.md` §2.1 (số A2/A4), `ledger.md` (tạo)

**Produces:** 4 fixture cho Task 4–5. Literal phải kiểm bằng mắt sau khi chụp: `EUR=X` có hai nến ngày London 09-04 (`2026-09-03T23:00Z` close `0.859969973564148`, `2026-09-04T21:29Z` close `0.8604999780654907`, high `0.8626999855041504`); `CAD=X` nến cuối `2026-09-05T04:21Z`; BTC 3 nến với nến `2026-09-05` có `closeTime` `1788047999999`; ECB ngày `2026-08-14` có `CNY`.

- [ ] **Step 1: Chụp 4 fixture** (4 lời gọi thật, từ `backend/`)

```bash
PYTHONIOENCODING=utf-8 uv run python - <<'EOF'
import json, pathlib, time, httpx
FIX = pathlib.Path("tests/etl/fixtures/global")
now = int(time.time()); p1 = now - 5 * 86400
H = {"User-Agent": "Mozilla/5.0 (dulieuchungkhoan.vn etl; dulieuchungkhoan.official@gmail.com)"}
for sym, name in (("EUR=X", "EURX-5d"), ("CAD=X", "CADX-5d")):
    r = httpx.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1={p1}&period2={now}&interval=1d", headers=H, timeout=30)
    (FIX / f"yahoo-{name}.json").write_text(json.dumps(r.json(), ensure_ascii=False, indent=1), encoding="utf-8")
    res = r.json()["chart"]["result"][0]; print(sym, r.status_code, len(res["timestamp"]), res["timestamp"][-2:], res["indicators"]["quote"][0]["close"][-2:])
r = httpx.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=3&timeZone=0", timeout=30)
(FIX / "binance-BTCUSDT-3.json").write_text(json.dumps(r.json()), encoding="utf-8"); print("BTC", r.status_code, [(k[0], k[6], k[4]) for k in r.json()])
r = httpx.get("https://api.frankfurter.dev/v1/2026-07-31..2026-08-31?from=USD&to=EUR,JPY,GBP,CAD,SEK,CHF,CNY", timeout=60, follow_redirects=True)
(FIX / "ecb-2026-08.json").write_text(json.dumps(r.json(), ensure_ascii=False, indent=1), encoding="utf-8")
d = r.json(); print("ECB", r.status_code, len(d["rates"]), d["rates"]["2026-08-14"])
EOF
```

Expected: `EUR=X 200 6 [...]`, hai timestamp cuối `1788742800` (= 2026-09-03T23:00Z) và `1788902940`-ish (21:29Z), close `[0.859969973564148, 0.8604999780654907]`; `CAD=X` 6 nến, cuối `1788927660`-ish (04:21Z 09-05); `BTC 200 [(1788393600000, 1788479999999, ...), (1788480000000, ...), (1788566400000, 1788652799999, '...')]`; `ECB 200 22 {'CAD': 1.3923, 'CHF': 0.8081..., 'CNY': 6.7..., 'EUR': 0.86453, 'GBP': ..., 'JPY': 159.01, 'SEK': ...}` — **EUR 0.86453 và JPY 159.01 phải khớp literal test e45 hiện có**; ghi số CNY ngày 08-14 và số ngày vào ledger để Task 5 dùng.

⚠️ Nếu Yahoo lúc chụp (thứ 7 tối) trả cấu trúc khác bản đo 17:00 (ví dụ nến live đã đổi timestamp) thì **ghi số thật vào ledger và Task 4 dùng số thật**, không ép fixture theo con số ở trên.

- [ ] **Step 2: Ghi số A2/A4 vào spec §2.1** — dòng mới trong bảng "Đã đo": A2 `216 lời gọi/4 lượt/16 phút, 216 × 200, 0 lỗi, không header rate-limit, TB 81 ms` (từ `a2_yahoo_load.jsonl`); A4 từ `a4_wichart_load.jsonl` khi xong (số lời gọi, HTTP, ms, tỷ lệ `hit-cached`). Chép hai file jsonl vào thư mục plan dưới tên `measure-yahoo-load-2026-09-05.jsonl`, `measure-wichart-load-2026-09-05.jsonl`. Sửa §2.2: A2/A4 chuyển thành dữ kiện.

- [ ] **Step 3: Chạy bộ test nền** — `uv run pytest -q` ⇒ ghi số vào ledger (kỳ vọng 709 passed, 2 skipped).

- [ ] **Step 4: Commit** `docs(plan): slice 7b plan, fixtures captured 2026-09-05, A2/A4 load numbers`.

---

### Task 1: `http_fetch.Fetcher` — giãn cách ngẫu nhiên đều 1–5 s, `rng` bơm được

**Files:**
- Modify: `backend/etl/http_fetch.py` (toàn bộ lớp `Fetcher`, `open_fetcher`)
- Modify: `backend/etl/fred_fetch.py:12,45`, `lbma_fetch.py:12,32`, `yahoo_fetch.py:15,43`, `binance_fetch.py:18,63` — bỏ `MIN_INTERVAL` và đối số `min_interval=`
- Test: `backend/tests/etl/test_e50_http_fetch_gap.py` (mới)

**Interfaces:**
- Produces: `Fetcher(get, classify, sleep=time.sleep, rng=None, gap=GAP, retries=3, backoff=(2, 4, 8), timeout=30.0)`; thuộc tính `gaps: list[float]`, `calls`, `retries_done`, `last_headers`; `open_fetcher(classify, get=None, sleep=time.sleep, headers=None, rng=None, **kw)`. **Bỏ** `min_interval` và `clock` (Task 2 bọc `clock` cho WiChart).
- Consumers: 4 module `*_fetch` (task này), `wichart_fetch` (Task 2).

- [ ] **Step 1: Viết test đỏ** — `backend/tests/etl/test_e50_http_fetch_gap.py`

```python
"""Giãn cách ngẫu nhiên đều [1, 5] s giữa hai lời gọi liên tiếp cùng Fetcher, kể cả lần thử lại (spec lát 7b §5.1, §4.6-III)."""
import random

import httpx
import pytest

from etl import http_fetch as hf


def _ok(http, text):
    return ("ok", {"t": text}) if http == 200 else ("retry", None)


class _Rng:
    """rng giả: trả lần lượt các giá trị đã định, ghi lại (a, b) được hỏi."""
    def __init__(self, values):
        self.values, self.seen = list(values), []

    def uniform(self, a, b):
        self.seen.append((a, b))
        return self.values.pop(0)


def test_no_gap_before_the_first_call_and_one_gap_between_two_calls():
    slept = []
    f = hf.Fetcher(lambda u, t: (200, "a", {}), _ok, sleep=slept.append, rng=_Rng([1.0, 4.99]))
    f.fetch_one("u1", "a")
    assert slept == [] and f.gaps == []
    f.fetch_one("u2", "b")
    assert slept == [1.0] and f.gaps == [1.0] and f._rng.seen == [(1.0, 5.0)]


def test_retry_sleeps_backoff_then_a_gap_before_the_next_attempt():
    answers = [(500, "boom", {}), (200, "ok", {})]
    slept = []
    f = hf.Fetcher(lambda u, t: answers.pop(0), _ok, sleep=slept.append, rng=_Rng([3.2]))
    doc, text = f.fetch_one("u", "x")
    assert text == "ok" and slept == [2, 3.2] and f.calls == 2 and f.retries_done == 1 and f.gaps == [3.2]


def test_real_rng_stays_inside_one_to_five_and_is_not_constant():
    f = hf.Fetcher(lambda u, t: (200, "a", {}), _ok, sleep=lambda s: None, rng=random.Random(0))
    for i in range(21):
        f.fetch_one(f"u{i}", "a")
    assert len(f.gaps) == 20 and all(1.0 <= g <= 5.0 for g in f.gaps) and len(set(f.gaps)) > 1


def test_transport_error_walks_the_retry_path_with_backoff_and_gaps():
    def get(u, t):
        raise httpx.ReadTimeout("slow")
    slept = []
    f = hf.Fetcher(get, _ok, sleep=slept.append, rng=_Rng([1.5, 2.5, 3.5]))
    with pytest.raises(hf.FetchError, match="x hỏng sau 4 lần"):
        f.fetch_one("u", "x")
    assert slept == [2, 1.5, 4, 2.5, 8, 3.5] and f.calls == 4 and f.retries_done == 3


def test_open_fetcher_passes_rng_and_no_longer_accepts_min_interval():
    with hf.open_fetcher(_ok, get=lambda u, t: (200, "a", {}), sleep=lambda s: None, rng=_Rng([2.0])) as f:
        f.fetch_one("u1", "a")
        f.fetch_one("u2", "a")
        assert f.gaps == [2.0]
    with pytest.raises(TypeError):
        with hf.open_fetcher(_ok, get=lambda u, t: (200, "a", {}), min_interval=0.5):
            pass
```

- [ ] **Step 2: Chạy, xác nhận đỏ** — `uv run pytest tests/etl/test_e50_http_fetch_gap.py -q` ⇒ 5 FAIL (`TypeError: unexpected keyword 'rng'` ở 4 test đầu; test cuối đỏ vì `min_interval` còn được nhận).

- [ ] **Step 3: Viết `http_fetch.py`** — thay toàn bộ lớp và `open_fetcher`:

```python
"""Fetcher chung cho mọi nguồn HTTP: `get` bơm được (trả (status, text, headers)), `classify` theo nguồn,
retry + backoff, exception vận chuyển đi cùng đường với response xấu (bài học lát 3, e7f80f6).
Từ lát 7b: giãn cách NGẪU NHIÊN đều [1, 5] s trước mỗi lời gọi có lời gọi trước đó trong cùng Fetcher — kể cả
lần thử lại và trang backfill (D5, spec 7b §4.6-III); `rng` bơm được để test cố định.

⚠️ Khi exception, `text` là TÊN LỚP exception, không có `str(e)` — `str(e)` của httpx chứa URL, mà URL FRED chứa
khoá (fred.md Bẫy 7). `label` do nguồn đặt, không được chứa khoá."""
from __future__ import annotations

import contextlib
import random
import time

import httpx

DEFAULT_HEADERS = {"Accept-Encoding": "gzip",
                   "User-Agent": "dulieuchungkhoan.vn/etl (dulieuchungkhoan.official@gmail.com)"}
GAP = (1.0, 5.0)            # giây, phân bố đều — mô phỏng request thường, tránh dồn cục (brief D5)


class FetchError(Exception):
    """Một lời gọi hỏng sau mọi lần thử — series đó CHƯA nạp."""


class BadShape(Exception):
    """Response hợp lệ nhưng không đúng hình dạng/tham số — thử lại vô ích."""


class Fetcher:
    def __init__(self, get, classify, sleep=time.sleep, rng=None, gap=GAP, retries=3, backoff=(2, 4, 8), timeout=30.0):
        self._get, self._classify, self._sleep = get, classify, sleep
        self._rng = rng if rng is not None else random.Random()
        self.gap, self.retries, self.backoff, self.timeout = gap, retries, backoff, timeout
        self.calls = 0
        self.retries_done = 0
        self.last_headers: dict = {}
        self.gaps: list[float] = []

    def _throttle(self) -> None:
        # Không ngủ trước lời gọi ĐẦU TIÊN của lượt; mọi lời gọi sau (kể cả thử lại) cách lời gọi trước một khoảng ngẫu nhiên
        if self.calls:
            g = self._rng.uniform(*self.gap)
            self.gaps.append(g)
            self._sleep(g)

    def fetch_one(self, url: str, label: str):
        http, text = 0, ""
        for attempt in range(self.retries + 1):
            self._throttle()
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
def open_fetcher(classify, get=None, sleep=time.sleep, headers=None, rng=None, **kw):
    if get is not None:                            # test tiêm get giả, không mở kết nối
        yield Fetcher(get, classify, sleep, rng, **kw)
        return
    with httpx.Client(headers={**DEFAULT_HEADERS, **(headers or {})}, follow_redirects=True) as client:  # MỘT client cho trọn lượt
        def get_one(u: str, timeout: float):
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text, dict(r.headers)
        yield Fetcher(get_one, classify, sleep, rng, **kw)
```

- [ ] **Step 4: Bỏ `min_interval` ở 4 nguồn** — trong `fred_fetch.py` xoá dòng `MIN_INTERVAL = 0.5` và đổi `open_fetcher(classify, get=get, sleep=sleep, min_interval=MIN_INTERVAL)` → `open_fetcher(classify, get=get, sleep=sleep)`; `lbma_fetch.py` xoá `MIN_INTERVAL = 1.0`, gọi `open_fetcher(classify, get=get, sleep=sleep, timeout=60.0)`; `yahoo_fetch.py` xoá `MIN_INTERVAL = 1.1`, gọi `open_fetcher(classify, get=get, sleep=sleep, headers=HEADERS)`; `binance_fetch.py` xoá `MIN_INTERVAL = 0.3`, gọi `open_fetcher(classify, get=get, sleep=sleep)`. Docstring đầu `yahoo_fetch.py`/`binance_fetch.py` không đổi.

- [ ] **Step 5: Chạy xanh** — `uv run pytest tests/etl/test_e50_http_fetch_gap.py tests/etl/test_e44_fred.py tests/etl/test_e45_fx.py tests/etl/test_e46_lbma.py tests/etl/test_e47_yahoo.py tests/etl/test_e48_binance.py -q` ⇒ tất cả PASS (e37/e41 của WiChart còn dùng fetcher riêng, chưa đụng). Nếu một test cũ đỏ vì đếm `slept` (ví dụ `60 in slept` vẫn đúng; một assert `slept == [...]` nào đó thì đổi thành kiểm phần tử backoff + khoảng ∈ [1, 5]) — ghi vào report.

- [ ] **Step 6: Commit (controller)** `feat(etl): random 1-5 s gap between consecutive calls in the shared fetcher (D5)`.

---

### Task 2: `wichart_fetch` — mặt ngoài lát 6, ruột `http_fetch`

**Files:**
- Modify: `backend/etl/wichart_fetch.py` (viết lại toàn bộ)
- Test: `backend/tests/etl/test_e37_wichart_fetch.py:28-34` (retry), `:54-60` (thay test giãn cách)

**Interfaces:**
- Consumes: `http_fetch.Fetcher`, `BadShape`, `FetchError`, `DEFAULT_HEADERS` (Task 1).
- Produces (giữ nguyên với `wichart_job` và e41): `url(key, group)`, `classify(http, text)`, `Fetcher(get, sleep=time.sleep, clock=None, rng=None)` với `fetch_one(key, group) -> (doc, text)`, thuộc tính `calls`, `retries`, `gaps`; `open_fetcher(get=None, sleep=time.sleep, clock=None, rng=None)`; `FetchError`/`BadShape` **là** lớp của `http_fetch`.

- [ ] **Step 1: Sửa hai test e37 thành đỏ**

Thay thân `test_fetch_one_retries_a_500_then_returns_the_doc` dòng cuối:

```python
    assert f.calls == 2 and f.retries == 1
    assert slept[0] == 2 and len(slept) == 2 and 1.0 <= slept[1] <= 5.0         # BACKOFF[0] rồi giãn cách ngẫu nhiên trước lần thử lại (lát 7b)
```

Thay toàn bộ `test_min_interval_sleeps_between_two_calls` bằng:

```python
def test_random_gap_between_two_calls_is_inside_one_to_five_seconds():
    slept = []
    f = wf.Fetcher(get=lambda u, t: (200, CPI), sleep=slept.append, clock=lambda: 0.0)
    f.fetch_one("cpi", "vi_mo")
    assert slept == []                                                             # không ngủ trước lời gọi đầu
    f.fetch_one("cpi", "vi_mo")
    assert len(slept) == 1 and 1.0 <= slept[0] <= 5.0 and f.gaps == slept


def test_errors_are_the_shared_fetcher_classes():
    from etl import http_fetch as hf
    assert wf.FetchError is hf.FetchError and wf.BadShape is hf.BadShape
```

- [ ] **Step 2: Chạy, xác nhận đỏ** — `uv run pytest tests/etl/test_e37_wichart_fetch.py -q` ⇒ 3 FAIL (retry: `slept == [2]`; gap: `slept` rỗng sau hai lời gọi vì MIN_INTERVAL 0,2 với clock 0; classes khác nhau).

- [ ] **Step 3: Viết lại `wichart_fetch.py`**

```python
"""Tải một key WiChart (spec lát 6 §5.2). Từ lát 7b ruột là `http_fetch.Fetcher` (giãn cách ngẫu nhiên 1–5 s,
retry 3, backoff 2/4/8 — đóng nợ "wichart_fetch chưa chuyển sang http_fetch" của lát 7); file này giữ MẶT NGOÀI
của lát 6 — `url`, `classify`, `Fetcher(get, sleep, clock)`, `fetch_one(key, group)`, `calls`/`retries`,
`FetchError`/`BadShape` — để `wichart_job` và test lát 6 không đổi.

`get` của WiChart trả 2-tuple `(status, text)` (test e37/e41 tiêm vậy) — bọc thành 3-tuple cho fetcher chung.
Đo 2026-09-05: 90 lời gọi liên tiếp không giãn cách sạch; 282 lời gọi/14 phút với giãn cách 1–5 s sạch (A4)."""
from __future__ import annotations

import contextlib
import json
import time

import httpx

from etl.http_fetch import DEFAULT_HEADERS, BadShape, FetchError  # noqa: F401 — re-export cho wichart_job/test lát 6
from etl.http_fetch import Fetcher as _SharedFetcher

BASE = "https://api.wichart.vn/vietnambiz/vi-mo"
TIMEOUT = 30.0


def url(key: str, group: str) -> str:
    return f"{BASE}?key=hang_hoa&name={key}" if group == "hang_hoa" else f"{BASE}?name={key}"


def classify(http: int, text: str) -> tuple[str, dict | None]:
    """('ok', doc) | ('retry', None) | ('bad_shape', None)."""
    if http != 200:
        return "retry", None
    try:
        d = json.loads(text)
    except ValueError:
        return "retry", None
    chart = d.get("chart") if isinstance(d, dict) else None
    series = chart.get("series") if isinstance(chart, dict) else None
    if not isinstance(series, list):
        return "bad_shape", None
    return "ok", d


def _three(get):
    """(status, text) của WiChart → (status, text, headers) cho fetcher chung."""
    def get3(u: str, timeout: float):
        http, text = get(u, timeout)
        return http, text, {}
    return get3


class Fetcher:
    def __init__(self, get, sleep=time.sleep, clock=None, rng=None):
        # `clock` giữ cho chữ ký lát 6 (test e37 truyền vào), không còn dùng — giãn cách nay ngẫu nhiên, không theo đồng hồ
        self._inner = _SharedFetcher(_three(get), classify, sleep=sleep, rng=rng, timeout=TIMEOUT)

    @property
    def calls(self) -> int:
        return self._inner.calls

    @property
    def retries(self) -> int:
        return self._inner.retries_done

    @property
    def gaps(self) -> list[float]:
        return self._inner.gaps

    def fetch_one(self, key: str, group: str) -> tuple[dict, str]:
        try:
            return self._inner.fetch_one(url(key, group), key)
        except BadShape as e:
            raise BadShape(f"{key}: response không có chart.series") from e


@contextlib.contextmanager
def open_fetcher(get=None, sleep=time.sleep, clock=None, rng=None):
    if get is not None:                            # test tiêm get giả, không mở kết nối
        yield Fetcher(get, sleep, clock, rng)
        return
    with httpx.Client(headers=DEFAULT_HEADERS) as client:  # MỘT client cho trọn lượt
        def get_one(u: str, timeout: float) -> tuple[int, str]:
            r = client.get(u, timeout=timeout)
            return r.status_code, r.text
        yield Fetcher(get_one, sleep, clock, rng)
```

- [ ] **Step 4: Chạy xanh** — `uv run pytest tests/etl/test_e37_wichart_fetch.py tests/etl/test_e41_wichart_job.py tests/etl/test_e36_wichart_registry.py tests/etl/test_e38_wichart_normalize.py tests/etl/test_e39_wichart_guard.py tests/etl/test_e40_wichart_store.py -q` (tên file e36/e38–e40 kiểm bằng `ls tests/etl | grep e3`; chạy mọi file `test_e3*` và `e4[01]`) ⇒ PASS. `test_classify_ok_retry_bad_shape` phải còn xanh nguyên văn (`classify` giữ).

- [ ] **Step 5: Commit (controller)** `refactor(etl): wichart_fetch on the shared http_fetch core (slice-7 debt), lát-6 surface kept`.

---

### Task 3: Cờ `--intraday` xuyên suốt: `series_job` → 5 `fetch_all` → Yahoo 5 ngày / Binance `limit=3` → CLI

**Files:**
- Modify: `backend/etl/series_job.py:27-38` (`SourceSpec`), `:92-102` (`run`), `:118`, `:124`
- Modify: `backend/etl/fred_fetch.py:40`, `fx_fetch.py:26`, `lbma_fetch.py:31` (chữ ký), `yahoo_fetch.py:13,39-41`, `binance_fetch.py:16,61,78,86-93`
- Modify: `backend/etl/yahoo_job.py`, `binance_job.py`, `__main__.py:78-87`
- Test: `backend/tests/etl/test_e43_series_core.py` (`_fake_fetch_all`, +2 test), `test_e44_fred.py:189` (`boom`), `test_e47_yahoo.py` (+1), `test_e48_binance.py` (+1), `test_e51_cli_intraday.py` (mới)

**Interfaces:**
- Produces: `SourceSpec.supports_intraday: bool = False`; `SourceSpec.fetch_all(series, get, sleep, backfill, intraday)`; `series_job.run(spec, keys=None, dry_run=False, backfill=False, intraday=False, get=None, sleep=time.sleep, now=None)`; `yahoo_job.run(...)`/`binance_job.run(...)` cùng tham số `intraday=False`; `yahoo_fetch.INTRADAY_WINDOW_DAYS = 5`; `binance_fetch.INTRADAY_LIMIT = 3`; `stats["intraday"] = True` khi bật; CLI `etl yahoo|binance --intraday`.
- Consumes: Task 1 (`open_fetcher` không `min_interval`).

- [ ] **Step 1: Test đỏ — e43** (đổi `_fake_fetch_all` và thêm 2 test sau `test_backfill_per_code_...`)

```python
def _fake_fetch_all(series, get, sleep, backfill, intraday=False):
    docs = {s.external_key: {"k": s.external_key} for s in series}
    return docs, {k: '{"k": "%s"}' % k for k in docs}, [], len(docs), 0
```

```python
def test_runner_intraday_passes_the_flag_to_fetch_all_and_still_pushes_the_watermark(zz, monkeypatch):
    _wire(monkeypatch)
    seen = []

    def fa(series, get, sleep, backfill, intraday):
        seen.append((backfill, intraday))
        return _fake_fetch_all(series, get, sleep, backfill, intraday)
    spec = _spec()
    spec.fetch_all, spec.supports_intraday = fa, True
    now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    assert sj.run(spec, intraday=True, get=lambda u, t: (200, "{}", {}), sleep=lambda s: None, now=now) == 0
    status, stats, _ = _last_run(zz)
    assert seen == [(False, True)] and status == "success" and stats["intraday"] is True and stats["watermark"] == "2026-09-05"
    with zz.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM ops.data_domain_state WHERE source='zz'")).scalar() == 2   # lượt trọn registry ⇒ đẩy mốc (spec §4.6-I)


def test_runner_rejects_intraday_when_unsupported_or_combined_with_backfill_before_open_run(zz, monkeypatch):
    _wire(monkeypatch)
    assert sj.run(_spec(), intraday=True, get=lambda u, t: (200, "{}", {}), sleep=lambda s: None) == 2
    spec = _spec(supports_backfill=True)
    spec.supports_intraday = True
    assert sj.run(spec, intraday=True, backfill=True, get=lambda u, t: (200, "{}", {}), sleep=lambda s: None) == 2
    with zz.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM ops.etl_run WHERE job='global.zz'")).scalar() == 0
```

Trong `test_e44_fred.py` hàm `boom(series, get, sleep, backfill)` ⇒ `boom(series, get, sleep, backfill, intraday=False)`.

- [ ] **Step 2: Test đỏ — e47** (thêm sau `test_url_uses_period_not_range...`)

```python
def test_intraday_window_is_five_days_daily_is_400_and_backfill_is_1900():
    def window(**kw):
        calls = []
        yf.fetch_all([REG["^GSPC"]], lambda u, t: (calls.append(u), (200, json.dumps(_doc("GSPC-10d")), {}))[1], lambda s: None, **kw)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(calls[0]).query)
        return int(q["period2"][0]) - int(q["period1"][0])
    assert yf.INTRADAY_WINDOW_DAYS == 5
    assert window(backfill=False, intraday=True) == 5 * 86400
    assert window(backfill=False, intraday=False) == 400 * 86400
    assert window(backfill=True, intraday=False) > 100 * 365 * 86400          # period1 = 1900-01-01
```

- [ ] **Step 3: Test đỏ — e48** (thêm sau `test_weight_header_pauses_and_418_aborts`)

```python
def test_intraday_uses_limit_3_and_the_job_reports_the_flag(clean):
    calls = []
    docs, *_ = bf.fetch_all([REG["PAXGUSDT"]], lambda u, t: (calls.append(u), (200, json.dumps(PAXG), {}))[1], lambda s: None, False, True)
    assert bf.INTRADAY_LIMIT == 3 and calls and "limit=3" in calls[0] and "limit=40" not in calls[0]
    calls.clear()
    assert bj.run(intraday=True, get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    assert len(calls) == 11 and all("limit=3" in u for u in calls)
    status, stats = _last(clean)
    assert status == "success" and stats["intraday"] is True and "watermark" in stats
```

- [ ] **Step 4: Test đỏ — CLI** `backend/tests/etl/test_e51_cli_intraday.py`

```python
"""CLI lát 7b: `--intraday` cho yahoo/binance, loại trừ `--backfill`, fred/fx/lbma không có cờ này (spec §4.6-IV)."""
import pytest

import etl.__main__ as m


def test_yahoo_and_binance_intraday_flag_reaches_the_job(monkeypatch):
    import etl.binance_job
    import etl.yahoo_job
    seen = {}
    monkeypatch.setattr(etl.yahoo_job, "run", lambda **kw: seen.setdefault("yahoo", kw) and 0)
    monkeypatch.setattr(etl.binance_job, "run", lambda **kw: seen.setdefault("binance", kw) and 0)
    assert m.main(["yahoo", "--intraday"]) == 0
    assert m.main(["binance", "--keys", "BTCUSDT", "--intraday", "--dry-run"]) == 0
    assert seen["yahoo"] == {"keys": None, "dry_run": False, "backfill": False, "intraday": True}
    assert seen["binance"] == {"keys": ["BTCUSDT"], "dry_run": True, "backfill": False, "intraday": True}


def test_intraday_and_backfill_are_mutually_exclusive_and_fred_has_no_intraday():
    with pytest.raises(SystemExit) as e:
        m.main(["yahoo", "--intraday", "--backfill"])
    assert e.value.code == 2
    with pytest.raises(SystemExit) as e:
        m.main(["fred", "--intraday"])
    assert e.value.code == 2
```

- [ ] **Step 5: Chạy, xác nhận đỏ** — `uv run pytest tests/etl/test_e43_series_core.py tests/etl/test_e47_yahoo.py tests/etl/test_e48_binance.py tests/etl/test_e51_cli_intraday.py -q` ⇒ các test mới FAIL (`TypeError` tham số `intraday`, `AttributeError INTRADAY_WINDOW_DAYS`, argparse `unrecognized arguments: --intraday`).

- [ ] **Step 6: `series_job.py`**

```python
@dataclass
class SourceSpec:
    job: str
    source: str
    domains: tuple[str, ...]
    guard_mode: str
    log_name: str
    build: Callable[[], list]
    fetch_all: Callable[..., tuple[dict, dict, list, int, int]]   # (series, get, sleep, backfill, intraday) -> docs, texts, failed, calls, retries
    normalize: Callable[..., list]                                # (series, doc, now) -> list[Point] | list[Bar]; raise SeriesError
    supports_backfill: bool = False
    supports_intraday: bool = False                               # lát 7b: cửa sổ ngắn, chạy trong phiên — KHÔNG phải dữ liệu intraday
    redact: Callable[[str], str] = staticmethod(lambda s: s)      # che khoá trong lỗi/log (FRED — khoá đi trong URL)
```

`run` — chữ ký `def run(spec: SourceSpec, keys=None, dry_run=False, backfill=False, intraday=False, get=None, sleep=time.sleep, now=None) -> int:`; ngay sau khối `if backfill and not spec.supports_backfill:` thêm:

```python
    if intraday and not spec.supports_intraday:
        log.error("%s không có --intraday", spec.log_name)
        return 2
    if intraday and backfill:
        log.error("%s: --intraday và --backfill loại trừ nhau", spec.log_name)
        return 2
```

Dòng fetch: `docs, texts, failed, calls, retries = spec.fetch_all(series, get, sleep, backfill, intraday)`. Vòng cờ: `for flag, on in (("subset", subset), ("dry_run", dry_run), ("backfill", backfill), ("intraday", intraday)):`. Docstring đầu file thêm một câu: "`--intraday` = lượt trọn registry với cửa sổ ngắn (Yahoo 5 ngày, Binance 3 nến): guard và mốc nước như lượt thường, chỉ khác cửa sổ (spec 7b §4.6-I)."

- [ ] **Step 7: 5 `fetch_all`** — `fred_fetch.fetch_all(series, get, sleep, backfill, intraday=False)`, `fx_fetch.fetch_all(series, get, sleep, backfill, intraday=False)`, `lbma_fetch.fetch_all(series, get, sleep, backfill, intraday=False)` (thân không đổi). `yahoo_fetch.py`:

```python
DAILY_WINDOW_DAYS = 400          # 40 ngày trả 1 nến ở ^SET.BK/PSEI.PS (measure-yahoo2)
INTRADAY_WINDOW_DAYS = 5         # lượt --intraday: nến đang chạy + vài ngày bù (spec 7b §5.3); ^SET.BK/PSEI.PS trả 1 nến — đủ
BACKFILL_PERIOD1 = -2208988800   # 1900-01-01: period1=0 cắt câm lịch sử ở 1970 (yahoo.md Bẫy 1)
...
def fetch_all(series, get, sleep, backfill, intraday=False):
    period2 = int(time.time())
    window = INTRADAY_WINDOW_DAYS if intraday else DAILY_WINDOW_DAYS
    period1 = BACKFILL_PERIOD1 if backfill else period2 - window * 86400
```

`binance_fetch.py`: `DAILY_LIMIT = 40` giữ, thêm `INTRADAY_LIMIT = 3               # hôm nay đang chạy + 2 ngày bù (measure-binance-limit3)`; `_fetch_with(series, get, sleep, backfill, intraday)` với nhánh thường `f.fetch_one(url(sym, INTRADAY_LIMIT if intraday else DAILY_LIMIT), sym)`; `fetch_all(series, get, sleep, backfill, intraday=False)` truyền `intraday` xuống cả hai nhánh.

- [ ] **Step 8: Job và CLI** — `yahoo_job.py`/`binance_job.py`: `SPEC` thêm `supports_intraday=True`; `def run(keys=None, dry_run=False, backfill=False, intraday=False, get=None, sleep=time.sleep, now=None) -> int: return series_job.run(SPEC, keys=keys, dry_run=dry_run, backfill=backfill, intraday=intraday, get=get, sleep=sleep, now=now)`. `__main__.py` khối `("fred", "fx", "lbma", "yahoo", "binance")`:

```python
        if args[0] in ("yahoo", "binance"):
            parser.add_argument("--backfill", action="store_true")
            parser.add_argument("--intraday", action="store_true")        # cửa sổ ngắn, chạy trong phiên (lát 7b)
        parsed = parser.parse_args(args[1:])
        if getattr(parsed, "intraday", False) and getattr(parsed, "backfill", False):
            parser.error("--intraday và --backfill loại trừ nhau")
        extra = {"intraday": parsed.intraday} if args[0] in ("yahoo", "binance") else {}
        return mod.run(keys=parsed.keys, dry_run=parsed.dry_run, backfill=getattr(parsed, "backfill", False), **extra)
```

- [ ] **Step 9: Chạy xanh** — lệnh Step 5 + `tests/etl/test_e44_fred.py tests/etl/test_e45_fx.py tests/etl/test_e46_lbma.py tests/etl/test_e01_cli.py` ⇒ PASS.

- [ ] **Step 10: Commit (controller)** `feat(etl): --intraday for yahoo (5-day window) and binance (limit=3) through the shared series runner`.

---

### Task 4: Nến đang chạy vào kho — bỏ hai luật cắt, pin bằng fixture thật

**Files:**
- Modify: `backend/etl/yahoo_normalize.py:1,51-52,55` · `backend/etl/binance_normalize.py:1,15-16,19-23`
- Test: `backend/tests/etl/test_e47_yahoo.py:63-69` (thay), +2 test · `test_e48_binance.py:40-46` (thay), `:123-136` (số đếm)
- Fixture (Task 0): `yahoo-EURX-5d.json`, `yahoo-CADX-5d.json`, `binance-BTCUSDT-3.json`

**Interfaces:** `yahoo_normalize.bars(s, doc, now)` và `binance_normalize.bars(s, doc, now)` chữ ký không đổi; nến cuối (đang chạy) **có** trong kết quả.

- [ ] **Step 1: Test đỏ — e47.** Thay `test_open_candle_is_dropped_while_the_regular_session_is_still_running` bằng ba test (số literal lấy từ Task 0 — nếu fixture chụp ra số khác, dùng số thật và ghi ledger):

```python
def test_open_candle_is_kept_while_the_regular_session_is_still_running():
    during = datetime(2026, 9, 4, 15, 0, tzinfo=timezone.utc)                          # trong phiên NY (13:30–20:00)
    bars = yn.bars(REG["^GSPC"], _doc("GSPC-10d"), during)
    assert len(bars) == 8 and bars[-1].obs_date == date(2026, 9, 4) and bars[-1].close == Decimal("7718.60009765625")
    early = datetime(2026, 9, 5, 2, 0, tzinfo=timezone.utc)                            # DXY regular.end = 03:59 UTC 09-05 — không còn cắt
    assert yn.bars(REG["DX-Y.NYB"], _doc("DXY-10d"), early)[-1].obs_date == date(2026, 9, 4)


def test_fx_two_candles_on_the_same_london_date_keep_the_live_one():
    # EUR=X 2026-09-05: nến 2026-09-03T23:00Z (London 09-04, close≈open "rỗng") và nến live 2026-09-04T21:29Z (London 09-04)
    s = REG["EUR=X"]
    bars = yn.bars(s, _doc("EURX-5d"), NOW)
    by = {b.obs_date: b for b in bars}
    assert sorted(by) == [date(2026, 8, 31), date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 3), date(2026, 9, 4)]
    b = by[date(2026, 9, 4)]
    assert (b.close, b.high, b.low) == (Decimal("0.8604999780654907"), Decimal("0.8626999855041504"), Decimal("0.8593999743461609"))
    assert b.close != Decimal("0.859969973564148")                                        # nến rỗng 23:00 bị nến live đè


def test_fx_weekend_candle_lands_on_its_london_date():
    bars = yn.bars(REG["CAD=X"], _doc("CADX-5d"), NOW)                                    # nến cuối 2026-09-05T04:21Z = thứ 7 London
    assert bars[-1].obs_date == date(2026, 9, 5) and bars[-1].close == Decimal("1.3837000131607056")
    assert bars[-2].obs_date == date(2026, 9, 4) and bars[-2].close == Decimal("1.3789499998092651")
```

`REG["EUR=X"]`/`REG["CAD=X"]` chỉ tồn tại sau Task 5 — trong task này dùng series tạm: thêm ở đầu phần test

```python
import dataclasses
FX_EUR = dataclasses.replace(REG["^GSPC"], external_key="EUR=X", code="fx.usd_eur.market", quote_currency="EUR",
                             band=(Decimal("0.08"), Decimal("9")), max_lag_days=6)
FX_CAD = dataclasses.replace(FX_EUR, external_key="CAD=X", code="fx.usd_cad.market", quote_currency="CAD",
                             band=(Decimal("0.13"), Decimal("14")))
```

và dùng `FX_EUR`/`FX_CAD` thay `REG[...]` trong hai test FX (Task 5 đổi lại thành `REG`).

- [ ] **Step 2: Test đỏ — e48.** Thay `test_open_time_utc_date_string_prices_and_open_candle_dropped` bằng:

```python
def test_open_time_utc_date_string_prices_and_the_running_candle_is_kept():
    bars = bn.bars(REG["PAXGUSDT"], PAXG, NOW)
    assert [b.obs_date for b in bars] == [date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 3), date(2026, 9, 4), date(2026, 9, 5)]
    b = bars[-2]
    assert (b.open, b.high, b.low, b.close, b.volume, b.close_adj, b.code) == (
        Decimal("4481.95"), Decimal("4489.97"), Decimal("4375.00"), Decimal("4431.81"), Decimal("5744.5282"), None, "paxg")
    assert bars[-1].close == Decimal("4433.13")                                       # nến 09-05 đang chạy (fixture chụp 05/09)
    assert len(bn.bars(REG["PAXGUSDT"], PAXG, datetime(2026, 9, 6, 0, 30, tzinfo=timezone.utc))) == 5


def test_limit_3_fixture_has_two_closed_and_one_running_candle_for_today():
    btc3 = json.loads((FIX / "binance-BTCUSDT-3.json").read_text(encoding="utf-8"))
    bars = bn.bars(REG["BTCUSDT"], btc3, NOW)
    assert [b.obs_date for b in bars] == [date(2026, 9, 3), date(2026, 9, 4), date(2026, 9, 5)] and btc3[-1][6] > NOW.timestamp() * 1000
```

Trong `test_job_writes_44_closed_bars` (đổi tên thành `test_job_writes_55_bars_including_the_running_one`): `stats["bars"] == 55 and stats["inserted"] == 55`; câu `count(*) ... obs_date='2026-09-05'` ⇒ `== 1`.

- [ ] **Step 3: Chạy, xác nhận đỏ** — `uv run pytest tests/etl/test_e47_yahoo.py tests/etl/test_e48_binance.py -q` ⇒ các test mới/đổi FAIL (7 ≠ 8 bars; PAXG 4 ≠ 5; 44 ≠ 55).

- [ ] **Step 4: `yahoo_normalize.py`** — docstring: `"""Nến ngày Yahoo → Bar (spec lát 7 §5.3, lát 7b §5.4). Ba cổng bắt buộc + ngày theo múi giờ SÀN. Nến đang chạy ĐƯỢC GIỮ (D1 lát 7b): hai nến cùng ngày sàn thì nến sau ghi đè — với FX chính là nến live tại regularMarketTime đè nến "rỗng" 23:00 UTC (measure-yahoo-fx 2026-09-05)."""`. Xoá hai dòng `reg = ...` và `cut = ...`; vòng lặp thành `if q["close"][i] is None: continue`.

- [ ] **Step 5: `binance_normalize.py`** — docstring: `"""Nến ngày Binance → Bar: obs_date = ngày UTC của thời điểm MỞ (seam 4 bước 5). Nến đang chạy (closeTime > now) ĐƯỢC GIỮ từ lát 7b — dòng hôm nay bị ghi đè tới 00:00 UTC."""`. Xoá hai dòng `if k[6] / 1000 > now.timestamp(): continue`; hai thông điệp `stale` đổi "nến đã đóng"/"nến đóng cuối" thành "nến"/"nến cuối".

- [ ] **Step 6: Chạy xanh** — lệnh Step 3 ⇒ PASS, kể cả `test_job_writes_296_bars_and_is_idempotent` (NOW thứ 7 ⇒ số nến GSPC-10d không đổi).

- [ ] **Step 7: Commit (controller)** `feat(etl): keep the running candle in ohlc_daily for yahoo and binance (D1)`.

---

### Task 5: Registry — Yahoo +17 FX `.market`, ECB +CNY, FRED −DEXCHUS

**Files:**
- Modify: `backend/etl/yahoo_registry.py` (thêm `_FX_ROWS`, `build`), `fx_registry.py:9-15`, `fx_fetch.py:10`, `fred_registry.py:42`
- Test: `test_e47_yahoo.py:29-35` (+FX), `test_e45_fx.py:23-31,82-91` (+CNY, +1 test), `test_e44_fred.py:30-38,153-160,175-182`, `test_e49_registry_codes_unique.py:13`

**Interfaces:**
- Produces: `yahoo_registry.build()` 54 series; mã `fx.usd_<ccy>.market`; `fx_registry.build()` 7 series (`CNY` cuối); `fx_fetch.PAIRS = "EUR,JPY,GBP,CAD,SEK,CHF,CNY"`; `fred_registry.build()` 14 series.

- [ ] **Step 1: Test đỏ — e47.** Sửa `test_registry_37_indices_all_ohlc` thành:

```python
def test_registry_54_series_37_indices_plus_17_fx_all_ohlc():
    s = yr.build()
    idx = [x for x in s if x.asset_class == "index"]
    fx = [x for x in s if x.asset_class == "fx"]
    assert len(s) == 54 and len(idx) == 37 and len(fx) == 17
    assert all(x.shape == "ohlc" and x.price_type is None and x.source == "yahoo" and x.calendar == "trading_days" for x in s)
    assert all(x.unit == "điểm" and x.max_lag_days == 14 for x in idx)
    assert all(x.unit == f"{x.quote_currency}/1 USD" and x.max_lag_days == 6 and x.code == f"fx.usd_{x.quote_currency.lower()}.market" for x in fx)
    assert REG["^GSPC"].code == "idx.sp500" and REG["DX-Y.NYB"].code == "dxy.ice" and REG["^KS11"].code == "idx.kospi"
    assert REG["^N225"].quote_currency == "JPY" and REG["^MERV"].quote_currency == "ARS" and REG["^GSPC"].band == (Decimal(700), Decimal(80000))
    assert REG["EUR=X"].band == (Decimal("0.08"), Decimal("9")) and REG["VND=X"].code == "fx.usd_vnd.market" and REG["VND=X"].region == "vn"
    assert REG["EUR=X"].band[0] <= Decimal("0.8605") <= REG["EUR=X"].band[1] and not (REG["EUR=X"].band[0] <= Decimal("86.05") <= REG["EUR=X"].band[1])
    assert len({x.code for x in s}) == 54
```

Đổi hai test FX của Task 4 sang `REG["EUR=X"]`/`REG["CAD=X"]`, xoá `FX_EUR`/`FX_CAD`. Trong `test_job_writes_296_bars_and_is_idempotent`: `len(calls) == 54`, `stats["tally"]["ok"] == 54`, `stats["bars"] == 296 + 17 * 8` (= 432 — `_synthetic` dựng từ GSPC-10d 8 nến cho mọi mã không có fixture; `_synthetic` phải set `res["meta"]["currency"] = s.quote_currency` — đã có). Trong `test_ratio_guard_refuses_three_dead_symbols_but_tolerates_one`: 3/54 = 5,6 % > 5 % vẫn từ chối ⇒ giữ; `refused == 54`; `stats["bars"] == 432 - 8` cho ca 1 mã chết.

- [ ] **Step 2: Test đỏ — e45.** `test_registry_six_fx_assets_fixing` ⇒ `[..., "CHF", "CNY"]`, thêm `assert REG["CNY"].code == "fx.usd_cny" and REG["CNY"].band == (Decimal(3), Decimal(15)) and REG["CNY"].region == "eu"`; `test_url_is_the_new_host_with_six_quotes` ⇒ `...&to=EUR,JPY,GBP,CAD,SEK,CHF,CNY`; `test_job_one_call_writes_132_fixing_rows` ⇒ `154` (22 ngày × 7), `registry == {"macro": 0, "asset": 7, "removed": 0}`, thêm assert `fx.usd_cny` ngày `2026-08-14` = **literal CNY từ fixture Task 0**. Thêm test:

```python
def test_ecb_cny_reuses_the_asset_fred_created_and_fred_mapping_goes_away(clean):
    # Kho có sẵn asset fx.usd_cny do FRED tạo (ánh xạ (fred, DEXCHUS)) — lượt ECB phải dùng CÙNG asset_id, không tạo mới
    from etl.registry import Series, load_registry
    fred_cny = Series(source="fred", external_key="DEXCHUS", domain="asset", code="fx.usd_cny", name_vi="cũ", unit="CNY/1 USD",
                      freq="d", asset_class="fx", quote_currency="CNY", price_type="fixing", calendar="trading_days",
                      band=(Decimal(3), Decimal(15)), max_lag_days=12)
    with clean.begin() as c:
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='fred' AND external_code='DEXCHUS'"))
        resolved, _ = load_registry(c, [fred_cny], "fred")
        aid = resolved["fx.usd_cny"].id
    assert xj.run(get=lambda u, t: (200, json.dumps(DOC), {}), sleep=lambda s: None, now=NOW) == 0
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT asset_id FROM asset.asset WHERE code='fx.usd_cny'")).scalar() == aid
        assert c.execute(sa.text("SELECT count(*) FROM asset.asset_external_id WHERE asset_id=:a"), {"a": aid}).scalar() == 2
    with clean.begin() as c:                                   # registry FRED 14 series ⇒ ánh xạ (fred, DEXCHUS) bị xoá, asset và dữ liệu giữ
        from etl import fred_registry
        _, st = load_registry(c, fred_registry.build(), "fred")
    assert st["removed"] == 1
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM asset.asset WHERE code='fx.usd_cny'")).scalar() == 1
    with clean.begin() as c:
        c.execute(sa.text("DELETE FROM macro.indicator_source WHERE source='fred'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='fred'"))
        c.execute(sa.text("DELETE FROM macro.indicator WHERE code LIKE 'us.%'"))
        c.execute(sa.text("DELETE FROM asset.asset WHERE code IN ('dxy.broad','vix') OR (code='wti' AND NOT EXISTS (SELECT 1 FROM asset.asset_external_id x WHERE x.asset_id = asset.asset_id))"))
```

(`Resolved` có trường id — kiểm tên trường thật trong `series_store.Resolved` trước khi viết: `grep -n "class Resolved" -A 4 etl/series_store.py`; nếu tên là `ref_id`/`row_id` thì dùng tên đó.) `_cleanup` của e45 xoá `asset.asset WHERE code = ANY(CODES)` — `CODES` nay có `fx.usd_cny`; thêm điều kiện không xoá khi còn ánh xạ: `DELETE FROM asset.asset a WHERE a.code = ANY(:c) AND NOT EXISTS (SELECT 1 FROM asset.asset_external_id x WHERE x.asset_id = a.asset_id)`.

- [ ] **Step 3: Test đỏ — e44 và e49.** e44: `test_registry_has_15_series...` ⇒ tên `..._14_series_split_11_macro_3_asset...`, `len(s) == 14`, xoá dòng assert `DEXCHUS`, `len({x.code}) == 14`; `test_job_writes_both_domains...`: `len(calls) == 14`, `registry == {"macro": 11, "asset": 3, "removed": 0}`, `tally.ok == 15` ⇒ `14`; giữ `inserted >= 97 + 12 + 20 + 12` nếu còn đúng, nếu đỏ thì hạ về tổng thật của 4 fixture còn lại và ghi report; `test_job_refuses_when_one_series_fails`: `refused == 13`. e49: `15 + 6 + 2 + 37 + 11 + 105` ⇒ `14 + 7 + 2 + 54 + 11 + 105`, docstring "trừ `wti`" giữ.

- [ ] **Step 4: Chạy, xác nhận đỏ** — `uv run pytest tests/etl/test_e44_fred.py tests/etl/test_e45_fx.py tests/etl/test_e47_yahoo.py tests/etl/test_e49_registry_codes_unique.py -q`.

- [ ] **Step 5: `yahoo_registry.py`** — sau `_ROWS` thêm:

```python
# FX (lát 7b, spec Phụ lục F): <CCY>=X = số <CCY> trên 1 USD (đo 2026-09-05: EUR=X 0,8605 vs ECB 0,86044). Asset RIÊNG
# so với fixing ECB `fx.usd_<ccy>` (khác mốc chốt = asset khác); ECB vẫn là mốc chuẩn (fx.md). VND=X là tỷ giá thị
# trường, KHÔNG thay dhtg (yahoo.md §6.1). band = (đo ÷ 10, × 10) trên regularMarketPrice 2026-09-05.
# (symbol, ccy, region, band_lo, band_hi)
_FX_ROWS = [
    ("EUR=X", "EUR", "eu", "0.08", "9"), ("GBP=X", "GBP", "gb", "0.07", "7.5"), ("JPY=X", "JPY", "jp", "15", "1600"),
    ("CAD=X", "CAD", "ca", "0.13", "14"), ("SEK=X", "SEK", "se", "0.9", "96"), ("CHF=X", "CHF", "ch", "0.08", "8.1"),
    ("CNY=X", "CNY", "cn", "0.67", "67"), ("KRW=X", "KRW", "kr", "135", "13500"), ("THB=X", "THB", "th", "3.2", "330"),
    ("SGD=X", "SGD", "sg", "0.12", "13"), ("TWD=X", "TWD", "tw", "3.1", "320"), ("INR=X", "INR", "in", "9.4", "950"),
    ("IDR=X", "IDR", "id", "1760", "176000"), ("MYR=X", "MYR", "my", "0.4", "41"), ("PHP=X", "PHP", "ph", "6.2", "630"),
    ("HKD=X", "HKD", "hk", "0.78", "79"), ("VND=X", "VND", "vn", "2600", "261000"),
]


def build() -> list[Series]:
    idx = [Series(source=SOURCE, external_key=sym, domain="asset", code=code, name_vi=name, unit="điểm", freq="d",
                  region=region, asset_class="index", quote_currency=ccy, price_type=None, calendar="trading_days",
                  band=(Decimal(lo), Decimal(hi)), max_lag_days=14, shape="ohlc")
           for sym, code, name, ccy, region, lo, hi in _ROWS]
    fx = [Series(source=SOURCE, external_key=sym, domain="asset", code=f"fx.usd_{ccy.lower()}.market",
                 name_vi=(f"Tỷ giá {ccy}/USD (thị trường, Yahoo)" if ccy != "VND"
                          else "Tỷ giá USD/VND thị trường (Yahoo, đối chứng — không thay dhtg)"),
                 unit=f"{ccy}/1 USD", freq="d", region=region, asset_class="fx", quote_currency=ccy, price_type=None,
                 calendar="trading_days", band=(Decimal(lo), Decimal(hi)), max_lag_days=6, shape="ohlc")
          for sym, ccy, region, lo, hi in _FX_ROWS]
    return idx + fx
```

Docstring đầu file: thêm "+ 17 cặp FX `.market` (lát 7b)".

- [ ] **Step 6: `fx_registry.py`, `fx_fetch.py`, `fred_registry.py`** — `_ROWS` thêm `("CNY", "fx.usd_cny", "Tỷ giá CNY/USD (fixing ECB)", "3", "15")` cuối danh sách, docstring thêm "CNY từ lát 7b — thay FRED DEXCHUS, chuỗi thuần ECB (spec 7b §4.2)"; `fx_fetch.PAIRS = "EUR,JPY,GBP,CAD,SEK,CHF,CNY"`, docstring "7 cặp"; `fred_registry.py` xoá dòng `_a("DEXCHUS", ...)` và thêm comment ngay chỗ đó: `# DEXCHUS (CNY noon NY) bỏ ở lát 7b — CNY về ECB, một mốc fixing (spec 7b §4.2)`.

- [ ] **Step 7: Chạy xanh** — lệnh Step 4 ⇒ PASS; thêm `uv run pytest tests/etl/test_e43_series_core.py -q` (không đổi).

- [ ] **Step 8: Commit (controller)** `feat(etl): yahoo +17 FX .market series, ECB +CNY, drop FRED DEXCHUS`.

---

### Task 6: WiChart `--intraday` = lượt trên mọi key tần suất ngày

**Files:**
- Modify: `backend/etl/wichart_job.py:71-128`, `backend/etl/__main__.py:71-77`
- Test: `backend/tests/etl/test_e41_wichart_job.py` (+3 test), `test_e51_cli_intraday.py` (+1)

**Interfaces:**
- Produces: `wichart_job.run(keys=None, dry_run=False, intraday=False, get=None, sleep=time.sleep)`; `wichart_job.intraday_series(registry) -> list[Series]` (`freq == 'd'`); `stats["intraday"] = True`; CLI `etl wichart --intraday`.
- Consumes: Task 2 (`wichart_fetch` chung).

- [ ] **Step 1: Test đỏ — e41** (thêm cuối file)

```python
INTRADAY_KEYS = sorted({s.key for s in wr.build() if s.freq == "d"})


def test_intraday_run_hits_only_the_47_daily_keys_guards_and_leaves_domain_state_alone(clean, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert wj.run(intraday=True, get=_fake_get(calls), sleep=lambda s: None) == 0
    assert sorted(set(calls)) == INTRADAY_KEYS and len(INTRADAY_KEYS) == 47 and "cpi" not in calls and "dhtg" in calls and "lslnh" in calls
    status, stats, _ = _last_run(clean)
    assert status == "success" and stats["intraday"] is True and "watermark" not in stats and "subset" not in stats
    assert stats["tally"]["keys_total"] == 47 and stats["tally"]["series_ok"] == 61 and stats["payloads_stored"] == 0
    assert _scalar(clean, "SELECT count(*) FROM ops.data_domain_state WHERE source='wichart'") == 0
    assert _scalar(clean, "SELECT count(*) FROM staging.raw_payload WHERE source='wichart'") == 0
    assert _scalar(clean, "SELECT value FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                          " WHERE a.code='gold.sjc_buy' AND obs_date='2026-09-04'") == Decimal("145600000")
    assert _scalar(clean, "SELECT count(*) FROM macro.observation o JOIN macro.indicator i USING (indicator_id) WHERE i.code='vn.cpi'") == 0


def test_intraday_run_is_guarded_like_a_full_run(clean, monkeypatch):
    _wire(monkeypatch)
    bad = {"dau_wti", "bac", "dong", "kem"}                                             # 4 series đơn / 61 = 6,6 % > 5 %

    def get(u, timeout):
        key = u.rsplit("name=", 1)[1]
        if key in bad:
            return 200, json.dumps({"title": key, "chart": {}})                       # không có chart.series ⇒ bad_shape
        return _fake_get()(u, timeout)
    assert wj.run(intraday=True, get=get, sleep=lambda s: None) == 1
    status, stats, err = _last_run(clean)
    assert status == "failed" and "sai hình dạng" in err and stats["tally"]["keys_bad_shape"] == 4
    assert _scalar(clean, "SELECT count(*) FROM asset.price_daily") == 0


def test_intraday_with_keys_is_an_error_before_any_call(clean, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert wj.run(keys=["vang"], intraday=True, get=_fake_get(calls), sleep=lambda s: None) == 2
    assert calls == [] and _last_run(clean)[0] == "failed"
```

(`_fake_get()` trả 2-tuple `(200, text)` — đúng chữ ký WiChart; `_synthetic` cho key không có fixture sinh đúng 1 điểm ngày 04/09.) Thêm vào `test_e51_cli_intraday.py`:

```python
def test_wichart_intraday_flag_reaches_the_job(monkeypatch):
    import etl.wichart_job
    seen = {}
    monkeypatch.setattr(etl.wichart_job, "run", lambda **kw: seen.update(kw) or 0)
    assert m.main(["wichart", "--intraday"]) == 0
    assert seen == {"keys": None, "dry_run": False, "intraday": True}
```

- [ ] **Step 2: Chạy, xác nhận đỏ** — `uv run pytest tests/etl/test_e41_wichart_job.py tests/etl/test_e51_cli_intraday.py -q` ⇒ 4 FAIL (`TypeError intraday`).

- [ ] **Step 3: `wichart_job.py`** — thêm sau `MAX_ERRORS_IN_STATS`:

```python
def intraday_series(registry):
    """Lượt --intraday = mọi series tần suất NGÀY (47 key: 43 hang_hoa + dhtg, lsdh, lslnh, lshd) — spec 7b §4.4:
    tiêu chí là `freq`, không phải danh sách tay; nhóm tháng/quý/năm chỉ chạy ở lượt trọn hằng ngày."""
    return [s for s in registry if s.freq == "d"]
```

`run(keys=None, dry_run=False, intraday=False, get=None, sleep=time.sleep)`; sau khi có `registry`:

```python
        if subset and intraday:
            raise RuntimeError("--keys và --intraday loại trừ nhau")
        series = registry
        if subset:
            ...
        elif intraday:
            series = intraday_series(registry)
```

`verdict = wichart_guard.check(tally) if not subset else ...` giữ (intraday **có** guard). Trong `stats`: sau `if subset: stats["subset"] = True` thêm `if intraday: stats["intraday"] = True`. Khối ghi:

```python
        with engine.begin() as conn:
            resolved, reg_stats = wichart_store.load_registry(conn, registry)   # registry TRỌN, kể cả lượt con/intraday
            written = wichart_store.apply(conn, points, resolved)
            wichart_store.seed_series_break(conn)
            # Lượt intraday KHÔNG lưu body khi hash đổi: 47 key × 288 lượt/ngày × ~30 KB — đúng lý do lát 7 bỏ lưu body (ruling 7b)
            stored = 0 if intraday else sum(1 for key, text in texts.items() if wichart_store.store_payload_if_changed(conn, key, text, run_id))
```

`if not subset:` (watermark, domain state) ⇒ `if not subset and not intraday:` ở cả hai chỗ. Docstring đầu file thêm câu: "`--intraday` = lượt trên tập tần suất ngày: guard như lượt trọn, KHÔNG đẩy mốc nước (lượt trọn hằng ngày giữ), không lưu body."

`__main__.py` khối `wichart`: thêm `parser.add_argument("--intraday", action="store_true")`; nếu `parsed.keys is not None and parsed.intraday` ⇒ `parser.error("--keys và --intraday loại trừ nhau")`; gọi `etl.wichart_job.run(keys=parsed.keys, dry_run=parsed.dry_run, intraday=parsed.intraday)`.

- [ ] **Step 4: Chạy xanh** — lệnh Step 2 ⇒ PASS; rồi `uv run pytest tests/etl -q` toàn thư mục ⇒ 0 fail.

- [ ] **Step 5: Commit (controller)** `feat(etl): wichart --intraday over every daily-frequency key (47), guarded, no watermark, no payload`.

---

### Task 7: Chạy thật trên kho production, đối chiếu, ledger *(controller tự làm)*

**Files:** `ledger.md` (cùng thư mục), `spec.md` §2/§7 (số thật).

Mọi lệnh từ `backend/`, prefix `set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8`; log stderr ghi file ở scratchpad để grep khoá.

- [ ] **Step 1: AC1** — `uv run pytest -q` ⇒ dán số (kỳ vọng ≥ 709 + ~20 test mới, 2 skipped).
- [ ] **Step 2: AC2** — `uv run python -m etl yahoo --intraday --dry-run` (54/54 ok, ≤ 6 nến/mã, `intraday: true`); `... binance --intraday --dry-run` (11/11, 3 nến/mã); `... wichart --intraday --dry-run` (47 key, 61 series ok). Dán `stats`.
- [ ] **Step 3: CNY thuần ECB** — xoá dòng FRED của `fx.usd_cny` rồi chạy ECB và FRED thật:

```bash
uv run python - <<'EOF'
import os, sqlalchemy as sa
e = sa.create_engine(os.environ["ETL_DATABASE_URL"])
with e.begin() as c:
    n = c.execute(sa.text("DELETE FROM asset.price_daily WHERE asset_id = (SELECT asset_id FROM asset.asset WHERE code='fx.usd_cny')")).rowcount
    print("đã xoá", n, "dòng FRED của fx.usd_cny")   # kỳ vọng 11397
EOF
uv run python -m etl fx      # 7 cặp; kỳ vọng inserted ≈ 6.7xx dòng CNY từ 2000-01-13
uv run python -m etl fred    # 14 series; stats.registry.removed == 1 (ánh xạ DEXCHUS)
```

Nếu `DELETE` bị từ chối quyền dưới `ETL_DATABASE_URL` ⇒ chạy bằng `DATABASE_URL` (owner) và ghi ledger. Truy vấn sau: `min(obs_date)` của `fx.usd_cny` = `2000-01-13`; `asset_external_id` không còn `(fred, DEXCHUS)`; `data_domain_state ('asset','ecb')` mốc hôm nay.

- [ ] **Step 4: AC3 nửa Binance + AC5** — `uv run python -m etl binance --intraday` hai lần cách ≥ 5 phút ⇒ truy vấn `close, ingested_at` của `btc` ngày UTC hôm nay ở hai thời điểm: khác nhau. `uv run python -m etl yahoo --intraday` một lần ⇒ 17 mã `fx.usd_*.market` có dòng; bảng đối chiếu 7 cặp với ECB fixing 09-04 (< 1 %). Chạy `uv run python -m etl wichart --intraday` một lần (thứ 7: ghi số, không kết luận đổi).
- [ ] **Step 5: AC6** — từ log stderr của `etl fred` (Step 3, format `%(asctime)s`) không đủ vì log không ghi từng lời gọi: đo bằng `python -c` gọi `fred_fetch.fetch_all` với `get` thật bọc ghi `time.monotonic()` — hoặc đơn giản hơn: đọc `stats`? Không có. Dùng script scratchpad: bọc `httpx.Client.get` ghi timestamp, chạy `etl lbma` (2 lời gọi) và `etl yahoo --intraday --keys ^GSPC,^N225,^HSI,^FTSE` (4 lời gọi) ⇒ 4 khoảng ∈ [1, 5] s + thời gian phản hồi, không hai khoảng bằng nhau tới 0,01 s. Dán bảng.
- [ ] **Step 6: AC7** — số A2/A4 đã có ở spec §2.1 (Task 0); ghi thành câu "mức này an toàn" vào yahoo.md §7 / wichart.md §2.5 (Task 8).
- [ ] **Step 7: AC8** — `grep -c "$FRED_API"` trên log stderr của lượt `fred` và trên `SELECT stats::text || coalesce(error,'') FROM ops.etl_run WHERE job='global.fred'` ⇒ 0.
- [ ] **Step 8: Ledger** — `ledger.md`: rà tiền kiểm, tiến trình từng task (commit, số test), rulings, AC1–AC8 với bằng chứng, **nợ đầu tuần**: AC3 nửa Yahoo (`^N225` thứ 2 07:00–13:00 VN) + WiChart (`vang_the_gioi,dhtg` giờ làm việc), AC4 ba nguồn.
- [ ] **Step 9: Commit** `docs(plan): slice 7b ledger — AC evidence, CNY pure ECB cut-over, Monday debts`.

---

### Task 8: Tài liệu sống cùng lượt (spec §8) *(controller, hoặc Sonnet với brief từng file)*

**Files:** `docs/90-records/plans/2026-09-05-global-etl/spec.md` (§4.4, §5.2, §5.3, §5.6, Phụ lục A/B/D) · `docs/20-design/market-data-store.md` · `docs/10-sources/global/yahoo.md` (§5.5, §7, §8) · `docs/10-sources/global/fx.md` (§7) · `docs/10-sources/global/fred.md` · `docs/10-sources/macro/wichart.md` (§2.5) · `docs/10-sources/README.md` · `backend/README.md` · `docs/00-overview/roadmap.md` · `database/README.md` · `docs/90-records/README.md`.

- [ ] **Step 1:** Mỗi file một mục theo spec §8, mỗi sửa ở tầng `10-sources/` kèm *(đo 2026-09-05)* và chỉ ghi số đã đo (A1, A1b, A2, A4, Frankfurter CNY); WiChart ghi "chủ dự án kiểm 2026-09-05" cho việc hàng hoá cập nhật trong ngày. Không viết lại quá khứ ở spec lát 7 — thêm chú "đổi ở lát 7b, 2026-09-0x" cạnh câu cũ.
- [ ] **Step 2:** `git grep -n "min_interval\|MIN_INTERVAL\|nến chưa đóng\|closeTime > now\|DEXCHUS\|regular.end"` toàn repo ⇒ mọi hit còn lại hoặc đã đúng, hoặc thuộc `90-records/`/`decisions/` (lịch sử) — dán kết quả vào ledger (§1.7 CLAUDE.md).
- [ ] **Step 3: Commit** `docs: slice 7b — intraday semantics, Yahoo FX direction and two-candle trap, load levels, roadmap`.

---

### Task 9: Review hai trục, verify, merge *(controller)*

- [ ] Review độc lập (Sonnet, hai trục **Chuẩn** và **Spec**, báo riêng) trên `git diff main...feat/intraday-refresh`; sửa Important trước, ghi ruling cho Minor.
- [ ] `uv run pytest -q` lần cuối, dán số; `git status` sạch.
- [ ] `git checkout main && git merge --no-ff feat/intraday-refresh -m "Merge: slice 7b — intraday refresh (running candles, --intraday windows, random gaps, Yahoo FX, CNY via ECB)"`.

---

## Tự rà plan (đã chạy 2026-09-05 tối)

- **Phủ spec:** §5.1 → T1 · §5.2 → T2 · §5.3 → T3 + T6 · §5.4 → T4 · §5.5 → T5 · §4.2 xoá dòng FRED → T7.3 · §4.6-I/II → T3/T6 test · §6 seam: mọi dòng có test ở T1–T6 trừ "quyền `apply_ohlc` UPDATE dưới `dlck_etl`" — **bổ sung ở T4 Step 2**: trong `test_e43` hàm `test_core_works_under_etl_role_including_ohlc_daily` đã đi qua `apply_ohlc` với dòng có sẵn? Executor T4 kiểm: nếu test đó chỉ INSERT, thêm một `apply_ohlc` lần hai với `close` khác dưới cùng `SET LOCAL ROLE` và assert `changed == 1`.
- **Placeholder:** không có TBD; số CNY ngày 08-14 và timestamp fixture ghi "từ Task 0" — đó là literal chụp được, Task 0 ghi vào ledger trước khi Task 4/5 chạy.
- **Nhất quán kiểu:** `fetch_all(series, get, sleep, backfill, intraday)` dùng ở T3/T5/T6 và e43/e44/e47/e48 cùng thứ tự; `stats["intraday"]` ở `series_job` và `wichart_job`; `supports_intraday` chỉ có ở `SourceSpec`.
- **Chốt thêm khi viết plan (ghi ledger, spec §5.3 sửa một dòng):** lượt WiChart `--intraday` **không** gọi `store_payload_if_changed` — spec bản duyệt ghi "vẫn chạy"; đổi vì 47 × 288/ngày × ~30 KB là đúng cái lát 7 đã bỏ. Đảo ngược: nếu lát 12 cần body intraday làm bằng chứng ⇒ lưu mẫu 1/12 lượt.
