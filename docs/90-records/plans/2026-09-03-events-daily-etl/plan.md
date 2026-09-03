# Kế hoạch thực thi — `etl events` (lát 2 của [7] ETL REST hằng ngày)

> **Cho người/agent thực thi:** dùng skill `superpowers:subagent-driven-development` (khuyến nghị) hoặc `executing-plans`, chạy **từng task một**. Bước đánh dấu `- [ ]` để theo dõi.

**Mục tiêu:** job `python -m etl events` tải trọn sáu họ `Calendar/GetCorporate*` mỗi lượt và ghi vào `market.corporate_event`, kèm chính sách tạo issuer tối thiểu cho mã vắng danh bạ.

**Kiến trúc:** năm module thuần/IO tách bạch y khuôn lát 1 (`screener_*`) — `fetch` (I/O thuần) → `normalize` (thuần) → `ensure_issuers` + `guard` (thuần) → `apply`, tất cả trong **một giao dịch**, guard đánh giá **trước commit**. Không migration: lược đồ `corporate_event` giữ nguyên, hai chỗ vá nằm ở **công thức `stage_key`** mà ETL điền.

**Stack:** Python 3.12 · `httpx` · SQLAlchemy 2 (`sa.text`, không ORM) · Postgres · pytest.

**Spec:** [`spec.md`](spec.md) — đọc trước, plan này chỉ nói *chính xác thế nào*. Số đo nền: [`measurements.md`](measurements.md).

> ✅ **Code và test trong plan này đã được CHẠY THẬT trước khi giao** *(2026-09-03, ở scratchpad ngoài repo)*: **34/34 xanh** — 21 test thuần, 13 test trên Postgres thật. Câu `ON CONFLICT` cũng đã chạy trên chính `postgres-data` dưới role `dlck_etl`. Nghĩa là expected trong plan không phải phỏng đoán.
>
> Lượt chạy đó **bắt được một lỗi thật** và plan đã vá: ngưỡng vế (iv) đúng cho lượt thật (0,037%) thì sai cho fixture dày ca biên (14,3%) — job bị chính guard của nó từ chối. Xem dòng `DUP_RATIO` trong `_wire` ở Task 5. **Đừng "sửa" bằng cách nới ngưỡng trong `events_guard.py`.**

## Ràng buộc toàn cục

- **`PYTHONIOENCODING=utf-8`** trên mọi lệnh chạy Python — không đặt thì crash cp1252 khi in tiếng Việt.
- Mọi lệnh chạy từ thư mục `backend/`, bằng `uv run`.
- Test cần `TEST_DATABASE_URL`; job cần `ETL_DATABASE_URL` (lấy từ `.env` gốc repo qua `core.env.load_dotenv`).
- **Không `--no-verify`, không force push.** Nhánh `feat/events-daily-etl`, commit nhỏ một mục đích, message tiếng Anh.
- Mỗi test **assert giá trị cụ thể**, expected lấy từ fixture thật — **cấm tính lại theo đúng cách code tính** (§4.5.3).
- Vòng TDD: **một seam → một test đỏ → code tối thiểu cho xanh**. Không viết hết test rồi code hết.
- Test đụng database chạy **dưới role `dlck_etl`** (`SET LOCAL ROLE dlck_etl`) — §3.5.
- Header `Origin: https://fiinapp.bvsc.com.vn` bắt buộc cho mọi lời gọi `*.fiintrade.vn`.

## Cây file

| File | Trách nhiệm | Trạng thái |
|---|---|---|
| `backend/etl/events_fetch.py` | I/O thuần — tải 6 họ, phân trang, retry | tạo mới |
| `backend/etl/events_normalize.py` | Thuần — ánh xạ trường, `stage_key`, gộp trùng | tạo mới |
| `backend/etl/events_guard.py` | Thuần — 4 vế chốt chặn | tạo mới |
| `backend/etl/events_store.py` | Ghi kho — issuer tối thiểu, UPSERT, bằng chứng, công tắc miền | tạo mới |
| `backend/etl/events_job.py` | Điều phối một lượt chạy | tạo mới |
| `backend/etl/__main__.py` | Thêm nhánh `events` + cờ `--accept-new` | sửa |
| `backend/tests/etl/test_e16..e20_*.py` | 5 file test theo module | tạo mới |
| `backend/tests/etl/fixtures/events/` | 6 fixture + README | ✅ **đã có sẵn** (commit cùng plan này) |
| `scripts/register-tasks.ps1` | Task thứ 9 | sửa |

**Fixture đã dựng sẵn** từ bản tải thật 2026-09-03, chứa đúng các ca biên đã đo. Ba số dưới đây là **expected của cả bộ test**, tính bằng cách áp luật spec lên chính sáu file đó:

> **28 bản ghi vào → 24 dòng ra · `dup_conflicts = 4` · 17 `organCode` duy nhất**

---

## Task 1 — `events_fetch`

**Files:** Create `backend/etl/events_fetch.py` · Test `backend/tests/etl/test_e16_events_fetch.py`

**Interfaces — Produces:**
- `FAMILIES: dict[str, str]` — `event_type` → tên endpoint
- `fetch(get=None, sleep=time.sleep) -> tuple[dict[str, list[str]], int]` — `{event_type: [text từng trang]}` và tổng số lần retry
- `class FetchError(Exception)`

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/etl/test_e16_events_fetch.py
import json
import pytest
from etl import events_fetch as ef


def _envelope(total, n, start=0):
    return json.dumps({"totalCount": total,
                       "items": [{"organCode": f"C{start + i}"} for i in range(n)],
                       "status": "Success"})


def test_url_carries_pagesize_20000_and_language():
    seen = []

    def get(url):
        seen.append(url)
        return 200, _envelope(3, 3)

    ef.fetch(get=get, sleep=lambda s: None)
    assert seen[0] == ("https://wlgw-market.fiintrade.vn/Calendar/GetCorporateAGM"
                       "?Page=1&PageSize=20000&language=vi")
    assert len(seen) == 6                      # đúng sáu họ, mỗi họ một trang


def test_pages_until_collected_reaches_total_count():
    calls = {"n": 0}

    def get(url):
        calls["n"] += 1
        # họ đầu cần 2 trang (25.000/20.000), năm họ sau 1 trang
        if "GetCorporateAGM" in url:
            return (200, _envelope(25000, 20000)) if "Page=1" in url else (200, _envelope(25000, 5000, 20000))
        return 200, _envelope(1, 1)

    pages, retries = ef.fetch(get=get, sleep=lambda s: None)
    assert len(pages["AGM"]) == 2 and retries == 0
    assert calls["n"] == 7                     # 2 + 5


def test_retries_then_succeeds_and_counts():
    state = {"fail": 2}

    def get(url):
        if "GetCorporateAGM" in url and state["fail"]:
            state["fail"] -= 1
            return 500, "boom"
        return 200, _envelope(1, 1)

    slept = []
    pages, retries = ef.fetch(get=get, sleep=slept.append)
    assert retries == 2 and slept == [2, 4]


def test_raises_after_all_retries_exhausted():
    def get(url):
        return 500, "boom"

    with pytest.raises(ef.FetchError, match="GetCorporateAGM"):
        ef.fetch(get=get, sleep=lambda s: None)


def test_raises_on_empty_page_before_total_reached():
    def get(url):
        if "Page=1" in url:
            return 200, _envelope(25000, 20000)
        return 200, _envelope(25000, 0, 20000)

    with pytest.raises(ef.FetchError, match="rỗng"):
        ef.fetch(get=get, sleep=lambda s: None)
```

- [ ] **Bước 2: Chạy để chắc chắn nó ĐỎ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e16_events_fetch.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'etl.events_fetch'`

- [ ] **Bước 3: Viết code tối thiểu cho xanh**

```python
# backend/etl/events_fetch.py
"""Tải TRỌN sáu họ Calendar/GetCorporate* mỗi lượt (spec §5.2).

Không dùng FromDate: đo 2026-09-03 cho thấy mỗi họ lọc theo một trục ngày khác nhau,
và Earning lọc theo trường KHÔNG có trong response — cửa sổ 5 ngày trả 24 bản ghi
trong khi có 217 bản ghi mang publicDate trong đúng cửa sổ đó (measurements.md §2.1).
Tải trọn hết 9 lời gọi, dưới ngân sách ~10 mà market-data-store §4.1 cấp cho họ này.
"""
from __future__ import annotations

import json
import time

import httpx

BASE = "https://wlgw-market.fiintrade.vn/Calendar"
FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"      # bắt buộc cho *.fiintrade.vn (00-conventions §2)
PAGE_SIZE = 20000                                 # đo: nhóm này KHÔNG có whitelist PageSize
TIMEOUT = 300.0                                   # Earning ~36 s/trang ở 20.000 — 60 s của lát 1 sẽ đứt
RETRIES = 3
BACKOFF = (2, 4, 8)

FAMILIES = {
    "AGM": "GetCorporateAGM",
    "CashDividend": "GetCorporateCashDividend",
    "StockDividend": "GetCorporateStockDividend",
    "Earning": "GetCorporateEarning",
    "IPO": "GetCorporateIPO",
    "ShareIssuance": "GetCorporateShareIssuance",
}


class FetchError(Exception):
    """Một trang hỏng sau mọi lần thử — lượt chạy phải thất bại, không ghi gì."""


def _url(endpoint: str, page: int) -> str:
    return f"{BASE}/{endpoint}?Page={page}&PageSize={PAGE_SIZE}&language=vi"


def _valid(status: int, text: str) -> bool:
    if status != 200:
        return False
    try:
        d = json.loads(text)
    except ValueError:
        return False
    return d.get("status") == "Success" and isinstance(d.get("items"), list)


def _page(get, sleep, endpoint: str, page: int) -> tuple[str, int]:
    retries = 0
    status, text = 0, ""
    for attempt in range(RETRIES + 1):
        status, text = get(_url(endpoint, page))
        if _valid(status, text):
            return text, retries
        if attempt == RETRIES:
            break
        sleep(BACKOFF[attempt])
        retries += 1
    raise FetchError(f"{endpoint} trang {page} hỏng sau {RETRIES + 1} lần (HTTP {status}): {text[:200]}")


def _family(get, sleep, endpoint: str) -> tuple[list[str], int]:
    first, retries = _page(get, sleep, endpoint, 1)
    d = json.loads(first)
    total, got, texts, page = int(d["totalCount"]), len(d["items"]), [first], 1
    while got < total:
        page += 1
        text, r = _page(get, sleep, endpoint, page)
        retries += r
        items = json.loads(text)["items"]
        if not items:
            # 00-conventions §10.5: trang trắng vào kho mà không ai biết
            raise FetchError(f"{endpoint} trang {page} rỗng trong khi mới gom {got}/{total}")
        texts.append(text)
        got += len(items)
    return texts, retries


def _all(get, sleep) -> tuple[dict[str, list[str]], int]:
    pages: dict[str, list[str]] = {}
    retries = 0
    for event_type, endpoint in FAMILIES.items():
        texts, r = _family(get, sleep, endpoint)
        pages[event_type] = texts
        retries += r
    return pages, retries


def fetch(get=None, sleep=time.sleep) -> tuple[dict[str, list[str]], int]:
    if get is not None:                                   # test tiêm get giả, không mở kết nối
        return _all(get, sleep)
    # MỘT client cho trọn lượt (khuôn screener_fetch) — mở lại mỗi trang là bắt tay TLS thừa
    with httpx.Client(timeout=TIMEOUT, headers={"Origin": FIIN_ORIGIN}) as client:
        def get_one(url: str) -> tuple[int, str]:
            r = client.get(url)
            return r.status_code, r.text
        return _all(get_one, sleep)
```

- [ ] **Bước 4: Chạy lại — phải XANH**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e16_events_fetch.py -v`
Expected: 5 passed

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/events_fetch.py backend/tests/etl/test_e16_events_fetch.py
git commit -m "feat(etl): fetch all six calendar families whole, never a partial page"
```

---

## Task 2 — `events_normalize`

**Files:** Create `backend/etl/events_normalize.py` · Test `backend/tests/etl/test_e17_events_normalize.py`

**Interfaces — Consumes:** `events_fetch.FAMILIES` (tên `event_type`).
**Produces:**
- `@dataclass(frozen=True) EventRow` — trường: `event_type, organ_code, name_hint, public_date, exright_date, record_date, payout_date, year_report, length_report, stage_key, source_url, payload`; thuộc tính `natural_key -> tuple`
- `@dataclass(frozen=True) Normalized` — `rows: list[EventRow]`, `counts: dict[str,int]`, `collected: dict[str,int]`, `dup_conflicts: int`, `dup_keys: list[str]`
- `normalize(pages: dict[str, list[str]]) -> Normalized`

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/etl/test_e17_events_normalize.py
import json
import pathlib
from datetime import date

from etl import events_normalize as en

FIX = pathlib.Path(__file__).parent / "fixtures" / "events"


def pages(*families):
    """Dựng đúng hình dạng events_fetch trả về: {event_type: [text từng trang]}."""
    name = {"AGM": "agm", "CashDividend": "cashdividend", "StockDividend": "stockdividend",
            "Earning": "earning", "IPO": "ipo", "ShareIssuance": "shareissuance"}
    return {f: [(FIX / f"{name[f]}-sample-20260903.json").read_text(encoding="utf-8")]
            for f in families}


ALL = ("AGM", "CashDividend", "StockDividend", "Earning", "IPO", "ShareIssuance")


def test_public_date_with_a_time_part_truncates_to_the_date():
    n = en.normalize(pages("AGM"))
    sasteco = [r for r in n.rows if r.organ_code == "SASTECO"]
    # Nguồn trả '2018-03-27T11:03:28.023' VÀ '2018-03-27T00:00:00' — cùng một ngày công bố
    assert len(sasteco) == 1 and sasteco[0].public_date == date(2018, 3, 27)
    assert n.dup_conflicts == 1


def test_agm_stage_key_is_the_meeting_date_so_two_convocations_stay_apart():
    n = en.normalize(pages("AGM"))
    shx = sorted(r.stage_key for r in n.rows if r.organ_code == "SHX")
    assert shx == ["2022-10-18", "2022-12-23"]        # hai lần triệu tập, giữ cả hai


def test_cash_dividend_stage_key_carries_dividend_year():
    n = en.normalize(pages("CashDividend"))
    sd9 = sorted(r.stage_key for r in n.rows if r.organ_code == "SD9")
    assert sd9 == ["2019|Cả năm", "2021|Cả năm"]      # trả bù hai kỳ cùng ngày ⇒ 2 dòng
    assert len(n.rows) == 6 and n.dup_conflicts == 0


def test_share_issuance_keeps_the_record_that_has_a_listing_date():
    n = en.normalize(pages("ShareIssuance"))
    abi = [r for r in n.rows if r.organ_code == "ABI"]
    assert len(abi) == 2                              # hai issueMethodName, mỗi cái một dòng
    assert all(r.payload["listingDate"] == "2025-10-17T00:00:00" for r in abi)
    vic = [r for r in n.rows if r.organ_code == "VIC"]
    assert sorted(r.payload["planVolumn"] for r in vic) == [-27460872.0, 56155405.0]


def test_identical_duplicate_records_collapse_to_one():
    n = en.normalize(pages("StockDividend"))
    assert len(n.rows) == 3 and n.dup_conflicts == 1


def test_name_hint_falls_back_to_ticker_when_no_name_field_exists():
    n = en.normalize(pages("ShareIssuance"))
    ryg = next(r for r in n.rows if r.organ_code == "12681")
    assert ryg.name_hint == "RYG"                     # họ này không trả trường tên nào
    agm = next(r for r in en.normalize(pages("AGM")).rows if r.organ_code == "QNC")
    assert agm.name_hint == "Xi măng Quảng Ninh"


def test_earning_maps_report_period_and_has_no_stage_key():
    n = en.normalize(pages("Earning"))
    dic = next(r for r in n.rows if r.organ_code == "DIC")
    assert (dic.year_report, dic.length_report, dic.stage_key) == (2026, 2, None)
    assert dic.exright_date is None and dic.public_date == date(2026, 8, 19)


def test_source_url_only_present_on_agm():
    assert all(r.source_url for r in en.normalize(pages("AGM")).rows)
    assert all(r.source_url is None for r in en.normalize(pages("CashDividend")).rows)


def test_whole_fixture_set_yields_the_measured_totals():
    n = en.normalize(pages(*ALL))
    assert len(n.rows) == 24 and n.dup_conflicts == 4
    assert n.counts == {"AGM": 6, "CashDividend": 6, "StockDividend": 4,
                        "Earning": 3, "IPO": 2, "ShareIssuance": 7}
    assert n.collected == n.counts
    assert len({r.organ_code for r in n.rows}) == 17
```

- [ ] **Bước 2: Chạy để chắc chắn nó ĐỎ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e17_events_normalize.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'etl.events_normalize'`

- [ ] **Bước 3: Viết code tối thiểu cho xanh**

```python
# backend/etl/events_normalize.py
"""Chuẩn hoá lịch sự kiện — thuần, không I/O (spec §5.3).

Hai bẫy của nguồn, cả hai đã đo:
  1. publicDate ĐÔI KHI kèm giờ ('2018-03-27T11:03:28.023' cạnh '2018-03-27T00:00:00').
     Không cắt ngày thì cùng một sự kiện thành hai khoá.
  2. planVolumn viết SAI CHÍNH TẢ ở nguồn — đọc đúng tên nguồn, đừng "sửa".
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

DUP_SAMPLE = 20            # nêu tên tối đa 20 khoá — đủ chẩn đoán, không phình ops.etl_run.stats


@dataclass(frozen=True)
class EventRow:
    event_type: str
    organ_code: str
    name_hint: str | None
    public_date: date | None
    exright_date: date | None
    record_date: date | None
    payout_date: date | None
    year_report: int | None
    length_report: int | None
    stage_key: str | None
    source_url: str | None
    payload: dict

    @property
    def natural_key(self) -> tuple:
        """Đúng 7 thành phần của `corporate_event_natural_key` (migration 0004),
        với issuer thay bằng organ_code vì lúc này chưa ghép issuer_id."""
        return (self.event_type, self.organ_code, self.public_date, self.exright_date,
                self.year_report, self.length_report, self.stage_key or "")


@dataclass(frozen=True)
class Normalized:
    rows: list[EventRow]
    counts: dict[str, int]
    collected: dict[str, int]
    dup_conflicts: int
    dup_keys: list[str]


def _date(v: str | None) -> date | None:
    return date.fromisoformat(v[:10]) if v else None


def _stage_key(event_type: str, it: dict) -> str | None:
    # CashDividend/StockDividend và ShareIssuance: công thức của thiết kế (step-03 §4, F6).
    if event_type in ("CashDividend", "StockDividend"):
        return f"{it.get('dividendYear')}|{it.get('stageName') or ''}"
    # 🔴 planVolumn thêm ngoài thiết kế: issueYear gỡ đúng 2/129 khoá đụng, planVolumn gỡ 103.
    if event_type == "ShareIssuance":
        return f"{it.get('issueMethodName') or ''}|{it.get('issueYear')}|{it.get('planVolumn')}"
    # 🔴 AGM thiết kế bỏ trống: 16 khoá đụng vì DN triệu tập đại hội nhiều lần cùng ngày
    # công bố. eventTitle KHÔNG dùng được — null 23.467/23.467.
    if event_type == "AGM":
        d = _date(it.get("issueDate"))
        return d.isoformat() if d else ""
    return None                                     # Earning, IPO: 0 khoá đụng trên toàn kho


def _row(event_type: str, it: dict) -> EventRow:
    return EventRow(
        event_type=event_type,
        organ_code=it["organCode"],
        name_hint=it.get("organShortName") or it.get("organName") or it.get("ticker"),
        public_date=_date(it.get("publicDate")),
        exright_date=_date(it.get("exrightDate")),
        record_date=_date(it.get("recordDate")),
        payout_date=_date(it.get("payoutDate")),
        year_report=it.get("yearReport"),
        length_report=it.get("lengthReport"),
        stage_key=_stage_key(event_type, it),
        source_url=it.get("sourceUrl"),             # chỉ AGM có
        payload=it,
    )


def _completeness(it: dict) -> int:
    return sum(1 for v in it.values() if v is not None)


def _dedupe(rows: list[EventRow]) -> tuple[list[EventRow], int, list[str]]:
    """Nguồn tự đẻ trùng, và giữ hai phiên bản của cùng sự kiện sau khi dời ngày.

    Giữ bản ĐẦY ĐỦ NHẤT; hoà thì lấy bản xuất hiện sau (nguồn trả byte-identical
    giữa hai lượt gọi nên thứ tự là deterministic).
    """
    groups: dict[tuple, list[tuple[int, EventRow]]] = defaultdict(list)
    for i, r in enumerate(rows):
        groups[r.natural_key].append((i, r))
    kept: list[tuple[int, EventRow]] = []
    dup, dup_keys = 0, []
    for key, members in groups.items():
        if len(members) > 1:
            dup += len(members) - 1
            dup_keys.append("|".join("" if p is None else str(p) for p in key))
        kept.append(max(members, key=lambda im: (_completeness(im[1].payload), im[0])))
    kept.sort(key=lambda im: im[0])
    return [r for _, r in kept], dup, sorted(dup_keys)[:DUP_SAMPLE]


def normalize(pages: dict[str, list[str]]) -> Normalized:
    rows: list[EventRow] = []
    counts: dict[str, int] = {}
    collected: dict[str, int] = {}
    for event_type, texts in pages.items():
        total, got = 0, 0
        for i, text in enumerate(texts):
            d = json.loads(text)
            if i == 0:
                total = int(d["totalCount"])
            for it in d["items"]:
                rows.append(_row(event_type, it))
                got += 1
        counts[event_type] = total
        collected[event_type] = got
    kept, dup, dup_keys = _dedupe(rows)
    return Normalized(rows=kept, counts=counts, collected=collected,
                      dup_conflicts=dup, dup_keys=dup_keys)
```

- [ ] **Bước 4: Chạy lại — phải XANH**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e17_events_normalize.py -v`
Expected: 9 passed

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/events_normalize.py backend/tests/etl/test_e17_events_normalize.py
git commit -m "feat(etl): normalize calendar events; stage_key closes the key collisions"
```

---

## Task 3 — `events_guard`

**Files:** Create `backend/etl/events_guard.py` · Test `backend/tests/etl/test_e18_events_guard.py`

**Interfaces — Produces:**
- `@dataclass(frozen=True) GuardVerdict` — `ok: bool`, `reasons: tuple[str, ...]`, `families: tuple[str, ...]`
- `check(counts, collected, baseline, issuers_new, dup_conflicts, rows_kept, *, accept_new=False) -> GuardVerdict`
- Hằng số `DROP_RATIO = 0.02`, `DUP_RATIO = 0.005`, `MAX_NEW_ISSUERS = 20`

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/etl/test_e18_events_guard.py
from etl import events_guard as eg

OK_COUNTS = {"AGM": 100, "Earning": 200}


def _check(**kw):
    args = dict(counts=OK_COUNTS, collected=dict(OK_COUNTS), baseline=None,
                issuers_new=0, dup_conflicts=0, rows_kept=300)
    args.update(kw)
    return eg.check(**args)


def test_clean_run_passes():
    assert _check().ok is True


def test_short_page_set_is_refused_and_names_the_family():
    v = _check(collected={"AGM": 99, "Earning": 200})
    assert v.ok is False and v.families == ("AGM",)
    assert "99" in v.reasons[0] and "100" in v.reasons[0]


def test_a_drop_smaller_than_two_percent_passes():
    # Earning MẤT 150 bản ghi trong 24 ngày (57.176 → 57.026) — biến động thật lớn nhất đo được
    v = eg.check(counts={"Earning": 57026}, collected={"Earning": 57026},
                 baseline={"Earning": 57176}, issuers_new=0, dup_conflicts=0, rows_kept=57026)
    assert v.ok is True                            # −0,26% < 2%


def test_a_drop_past_two_percent_is_refused():
    v = eg.check(counts={"Earning": 56000}, collected={"Earning": 56000},
                 baseline={"Earning": 57176}, issuers_new=0, dup_conflicts=0, rows_kept=56000)
    assert v.ok is False and v.families == ("Earning",)


def test_minting_too_many_issuers_is_refused_unless_accepted():
    assert _check(issuers_new=21).ok is False
    assert _check(issuers_new=20).ok is True                       # đúng mép
    assert _check(issuers_new=517, accept_new=True).ok is True     # lượt backfill có người nhìn


def test_duplicate_ratio_threshold():
    # Vùng thật đo được: 42/110.737 = 0,037%
    assert eg.check(counts=OK_COUNTS, collected=dict(OK_COUNTS), baseline=None, issuers_new=0,
                    dup_conflicts=42, rows_kept=110695).ok is True
    assert eg.check(counts=OK_COUNTS, collected=dict(OK_COUNTS), baseline=None, issuers_new=0,
                    dup_conflicts=600, rows_kept=109400).ok is False


def test_every_broken_rule_is_reported_not_just_the_first():
    v = _check(collected={"AGM": 99, "Earning": 199}, issuers_new=21)
    assert len(v.reasons) == 3 and v.families == ("AGM", "Earning")
```

- [ ] **Bước 2: Chạy để chắc chắn nó ĐỎ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e18_events_guard.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'etl.events_guard'`

- [ ] **Bước 3: Viết code tối thiểu cho xanh**

```python
# backend/etl/events_guard.py
"""Chốt chặn cho job events — bốn vế, vế nào hỏng cũng từ chối (spec §5.4).

Module thuần: đầu vào là số trần để test không cần database.

KHÁC lát 1 ở một điểm lớn: KHÔNG có vế "ngày giao dịch". Lịch sự kiện không phụ
thuộc phiên — ngày lễ nguồn vẫn trả đủ kho, không có dòng ma nào để đẻ ra.
"""
from dataclasses import dataclass

DROP_RATIO = 0.02
DUP_RATIO = 0.005
MAX_NEW_ISSUERS = 20
# Vùng dữ liệu thật (đo 2026-09-03): lượt backfill đầu tạo 517 issuer tối thiểu, còn lượt
# hằng ngày phải gần 0. Ngưỡng 20 nằm giữa hai vùng đó. Đây là chốt chặn của chính sách F7:
# nó biến "âm thầm đẻ issuer" thành "đẻ quá tay thì dừng và gọi người".


@dataclass(frozen=True)
class GuardVerdict:
    ok: bool
    reasons: tuple[str, ...]
    families: tuple[str, ...]        # họ bị nghi — quyết định lưu mẫu nào làm bằng chứng


def check(counts: dict[str, int], collected: dict[str, int], baseline: dict[str, int] | None,
          issuers_new: int, dup_conflicts: int, rows_kept: int,
          *, accept_new: bool = False) -> GuardVerdict:
    reasons: list[str] = []
    families: list[str] = []
    for fam in sorted(counts):
        total, got = counts[fam], collected.get(fam, 0)
        if got != total:                                                        # (i)
            reasons.append(f"{fam}: gom được {got} bản ghi, totalCount báo {total} — thiếu trang")
            families.append(fam)
        base = (baseline or {}).get(fam)
        if base is not None and total < base * (1 - DROP_RATIO):                # (ii)
            reasons.append(f"{fam}: totalCount {total} sụt quá {DROP_RATIO:.0%} so mốc {base}")
            families.append(fam)
    if issuers_new > MAX_NEW_ISSUERS and not accept_new:                        # (iii)
        reasons.append(f"tạo mới {issuers_new} issuer tối thiểu — quá {MAX_NEW_ISSUERS};"
                       " chạy lại với --accept-new nếu con số này đúng")
    fetched = rows_kept + dup_conflicts
    if fetched > 0 and dup_conflicts > fetched * DUP_RATIO:                     # (iv)
        reasons.append(f"{dup_conflicts}/{fetched} bản ghi đụng khoá tự nhiên"
                       f" — quá {DUP_RATIO:.1%}")
    return GuardVerdict(ok=not reasons, reasons=tuple(reasons),
                        families=tuple(dict.fromkeys(families)))
```

- [ ] **Bước 4: Chạy lại — phải XANH**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e18_events_guard.py -v`
Expected: 7 passed

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/events_guard.py backend/tests/etl/test_e18_events_guard.py
git commit -m "feat(etl): events guard - short pages, count drop, issuer minting, key collisions"
```

---

## Task 4 — `events_store`

**Files:** Create `backend/etl/events_store.py` · Test `backend/tests/etl/test_e19_events_store.py`

**Interfaces — Consumes:** `events_normalize.EventRow`, `events_guard.GuardVerdict`.
**Produces:**
- `JOB = "market.events"`
- `load_baseline(engine) -> dict[str, int] | None`
- `ensure_issuers(conn, rows) -> tuple[dict[str, int], int]`
- `apply(conn, rows, issuer_by_organ) -> dict`
- `store_refusal_evidence(engine, pages, run_id, verdict, counts, collected) -> None`
- `upsert_domain_state(engine, watermark) -> None`

⚠️ Câu `ON CONFLICT` dưới đây **đã chạy thật** trên `postgres-data` dưới role `dlck_etl` (2026-09-03, trong giao dịch rollback): arbiter suy được, ghi lại cùng khoá cho **1 dòng**, khác `stage_key` cho **2 dòng**, và cả năm cột `coalesce` cùng NULL vẫn dedupe đúng. **Chép nguyên văn, đừng viết lại** — sai một ký tự trong biểu thức `coalesce` là Postgres không suy ra arbiter và ném lỗi.

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/etl/test_e19_events_store.py
import json
import pathlib

import sqlalchemy as sa

from etl import events_normalize as en
from etl import events_store as es

FIX = pathlib.Path(__file__).parent / "fixtures" / "events"
NAME = {"AGM": "agm", "CashDividend": "cashdividend", "StockDividend": "stockdividend",
        "Earning": "earning", "IPO": "ipo", "ShareIssuance": "shareissuance"}


def pages(*families):
    return {f: [(FIX / f"{NAME[f]}-sample-20260903.json").read_text(encoding="utf-8")]
            for f in families}


ALL = ("AGM", "CashDividend", "StockDividend", "Earning", "IPO", "ShareIssuance")


def test_ensure_issuers_mints_one_per_organ_code_and_is_idempotent(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    rows = en.normalize(pages(*ALL)).rows
    by_organ, created = es.ensure_issuers(db, rows)
    assert created == 17 and len(by_organ) == 17
    again_by_organ, again_created = es.ensure_issuers(db, rows)
    assert again_created == 0 and again_by_organ == by_organ


def test_minimal_issuer_name_prefers_a_real_name_and_falls_back_to_the_code(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    rows = en.normalize(pages(*ALL)).rows
    by_organ, _ = es.ensure_issuers(db, rows)
    got = dict(db.execute(sa.text(
        "SELECT external_code, i.name FROM market.issuer i"
        " JOIN market.issuer_external_id x USING (issuer_id)"
        " WHERE x.external_code IN ('QNC','12681','0304941312')")).all())
    assert got == {"QNC": "Xi măng Quảng Ninh",       # organShortName
                   "0304941312": "Xây dựng Công trình Tân Cảng",   # organName
                   "12681": "RYG"}                    # không trường tên nào ⇒ lùi về ticker


def test_ensure_issuers_never_updates_an_existing_issuer(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    iid = db.execute(sa.text(
        "INSERT INTO market.issuer (name) VALUES ('TÊN CŨ CỦA REFDATA') RETURNING issuer_id")).scalar_one()
    db.execute(sa.text("INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
                       " VALUES (:i, 'fiintrade', 'QNC')"), {"i": iid})
    es.ensure_issuers(db, en.normalize(pages("AGM")).rows)
    assert db.execute(sa.text("SELECT name FROM market.issuer WHERE issuer_id = :i"),
                      {"i": iid}).scalar_one() == "TÊN CŨ CỦA REFDATA"


def test_apply_writes_every_row_then_upserts_in_place(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    n = en.normalize(pages(*ALL))
    by_organ, _ = es.ensure_issuers(db, n.rows)
    assert es.apply(db, n.rows, by_organ) == {"rows_written": 24}
    assert db.execute(sa.text("SELECT count(*) FROM market.corporate_event")).scalar_one() == 24
    ids = set(db.execute(sa.text("SELECT event_id FROM market.corporate_event")).scalars())
    es.apply(db, n.rows, by_organ)                       # chạy lại: đè, không thêm
    assert db.execute(sa.text("SELECT count(*) FROM market.corporate_event")).scalar_one() == 24
    assert set(db.execute(sa.text("SELECT event_id FROM market.corporate_event")).scalars()) == ids


def test_apply_keeps_two_rows_for_two_dividend_years_on_the_same_day(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    n = en.normalize(pages("CashDividend"))
    by_organ, _ = es.ensure_issuers(db, n.rows)
    es.apply(db, n.rows, by_organ)
    got = db.execute(sa.text(
        "SELECT stage_key FROM market.corporate_event ce"
        " JOIN market.issuer_external_id x USING (issuer_id)"
        " WHERE x.external_code = 'SD9' ORDER BY stage_key")).scalars().all()
    assert got == ["2019|Cả năm", "2021|Cả năm"]


def test_apply_stores_source_url_for_agm_and_null_elsewhere(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    n = en.normalize(pages("AGM", "CashDividend"))
    by_organ, _ = es.ensure_issuers(db, n.rows)
    es.apply(db, n.rows, by_organ)
    with_url, without = db.execute(sa.text(
        "SELECT count(*) FILTER (WHERE source_url IS NOT NULL),"
        "       count(*) FILTER (WHERE source_url IS NULL) FROM market.corporate_event")).one()
    assert (with_url, without) == (5, 6)


def test_refusal_evidence_stores_only_the_implicated_family(db, migrated_engine):
    from etl import events_guard as eg
    verdict = eg.GuardVerdict(ok=False, reasons=("AGM: thiếu trang",), families=("AGM",))
    es.store_refusal_evidence(migrated_engine, pages("AGM", "Earning"), 99, verdict,
                              {"AGM": 6, "Earning": 3}, {"AGM": 5, "Earning": 3})
    with migrated_engine.begin() as c:
        payload, meta = c.execute(sa.text(
            "SELECT payload, meta FROM staging.raw_payload"
            " WHERE endpoint_key = 'events:refusal' ORDER BY payload_id DESC LIMIT 1")).one()
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE endpoint_key = 'events:refusal'"))
    assert list(payload["sample"]) == ["AGM"] and len(payload["sample"]["AGM"]) == 6
    assert meta["run_id"] == 99 and meta["reasons"] == ["AGM: thiếu trang"]


def test_domain_state_and_baseline_round_trip(migrated_engine):
    es.upsert_domain_state(migrated_engine, "2026-09-03")
    with migrated_engine.begin() as c:
        got = c.execute(sa.text(
            "SELECT status, watermark FROM ops.data_domain_state"
            " WHERE domain = 'market.events' AND source = 'fiintrade'")).one()
        assert got == ("active", "2026-09-03")
        rid = c.execute(sa.text(
            "INSERT INTO ops.etl_run (job, finished_at, status, stats) VALUES"
            " (:j, now(), 'success', cast(:s AS jsonb)) RETURNING run_id"),
            {"j": es.JOB, "s": json.dumps({"counts": {"AGM": 23467}})}).scalar_one()
    assert es.load_baseline(migrated_engine) == {"AGM": 23467}
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE run_id = :r"), {"r": rid})
```

- [ ] **Bước 2: Chạy để chắc chắn nó ĐỎ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e19_events_store.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'etl.events_store'`

- [ ] **Bước 3: Viết code tối thiểu cho xanh**

```python
# backend/etl/events_store.py
"""Ghi kho cho job events (spec §5.5).

Chính sách F7 (step-03 §4, review vòng 4): mã vắng danh bạ ⇒ TẠO issuer tối thiểu rồi ghi
sự kiện, không bỏ dòng, không để FK chặn job.

🔴 LUẬT CHỐNG HAI-CHỦ-MỘT-BẢNG (§1.7): `etl refdata` là chủ duy nhất của NỘI DUNG
`market.issuer`. Job này chỉ được INSERT khi organ_code chưa tồn tại, TUYỆT ĐỐI KHÔNG
UPDATE. Khi doanh nghiệp vào danh bạ, refdata nhận diện đúng dòng đó qua organ_code và
cập nhật — issuer tối thiểu tự lành, không đẻ dòng thứ hai.
"""
from __future__ import annotations

import json

import sqlalchemy as sa

from etl.events_normalize import EventRow

JOB = "market.events"
EVIDENCE_ITEMS = 50
BATCH = 5000

# Biểu thức coalesce phải LẶP NGUYÊN VĂN toàn bộ index `corporate_event_natural_key`
# thì Postgres mới suy ra arbiter (step-03 §4, vòng 4 F9). Đã chạy thật 2026-09-03.
SQL_UPSERT = (
    "INSERT INTO market.corporate_event"
    " (event_type, issuer_id, public_date, exright_date, record_date, payout_date,"
    "  year_report, length_report, stage_key, payload, source_url)"
    " VALUES (:t, :i, :pd, :ed, :rd, :yd, :yr, :lr, :sk, cast(:p AS jsonb), :su)"
    " ON CONFLICT (event_type, issuer_id,"
    "   coalesce(public_date,   '1900-01-01'),"
    "   coalesce(exright_date,  '1900-01-01'),"
    "   coalesce(year_report,   0),"
    "   coalesce(length_report, 0),"
    "   coalesce(stage_key,     ''))"
    " DO UPDATE SET payload = EXCLUDED.payload, source_url = EXCLUDED.source_url,"
    "   ingested_at = clock_timestamp()"
)


def load_baseline(engine) -> dict[str, int] | None:
    """Mốc cho vế (ii) — counts của lượt success gần nhất (khuôn screener_store)."""
    with engine.connect() as c:
        row = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = :j AND status = 'success'"
            " ORDER BY finished_at DESC LIMIT 1"), {"j": JOB}).first()
    if row is None or not row[0]:
        return None
    return row[0].get("counts")


def ensure_issuers(conn, rows: list[EventRow]) -> tuple[dict[str, int], int]:
    names: dict[str, str | None] = {}
    for r in rows:
        if names.get(r.organ_code) is None:          # tên đầu tiên khác None thắng
            names[r.organ_code] = r.name_hint
    by_organ = {code: iid for code, iid in conn.execute(sa.text(
        "SELECT external_code, issuer_id FROM market.issuer_external_id"
        " WHERE source = 'fiintrade'")).all()}
    created = 0
    for code in sorted(names):
        if code in by_organ:
            continue                                  # KHÔNG update — refdata sở hữu nội dung
        issuer_id = conn.execute(sa.text(
            "INSERT INTO market.issuer (name) VALUES (:n) RETURNING issuer_id"),
            {"n": names[code] or code}).scalar_one()
        conn.execute(sa.text(
            "INSERT INTO market.issuer_external_id (issuer_id, source, external_code)"
            " VALUES (:i, 'fiintrade', :c)"), {"i": issuer_id, "c": code})
        by_organ[code] = issuer_id
        created += 1
    return by_organ, created


def apply(conn, rows: list[EventRow], issuer_by_organ: dict[str, int]) -> dict:
    params = [{"t": r.event_type, "i": issuer_by_organ[r.organ_code],
               "pd": r.public_date, "ed": r.exright_date, "rd": r.record_date,
               "yd": r.payout_date, "yr": r.year_report, "lr": r.length_report,
               "sk": r.stage_key, "p": json.dumps(r.payload, ensure_ascii=False),
               "su": r.source_url} for r in rows]
    stmt = sa.text(SQL_UPSERT)
    for i in range(0, len(params), BATCH):            # executemany theo lô — 110k dòng một lượt
        conn.execute(stmt, params[i:i + BATCH])
    return {"rows_written": len(rows)}


def store_refusal_evidence(engine, pages: dict[str, list[str]], run_id: int,
                           verdict, counts: dict, collected: dict) -> None:
    """Bằng chứng vào `staging.raw_payload` — KHÔNG lưu trang thô.

    Một lượt là 36 MB, và review vòng 4 F1 đã chốt sự kiện không vào staging vì đã có
    thô inline per-row. Lưu counts + 50 bản ghi đầu của họ bị nghi là đủ chẩn đoán.
    """
    sample = {}
    for fam in (verdict.families or tuple(pages)):
        texts = pages.get(fam) or []
        sample[fam] = json.loads(texts[0])["items"][:EVIDENCE_ITEMS] if texts else []
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
            " VALUES ('fiintrade', 'events:refusal', 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
            {"p": json.dumps({"counts": counts, "collected": collected, "sample": sample},
                             ensure_ascii=False),
             "m": json.dumps({"run_id": run_id, "reasons": list(verdict.reasons)},
                             ensure_ascii=False)})


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
            " VALUES ('market.events', 'fiintrade', 'active', now(), :w)"
            " ON CONFLICT (domain, source) DO UPDATE"
            " SET last_success_at = now(), watermark = :w, status = 'active'"), {"w": watermark})
```

- [ ] **Bước 4: Chạy lại — phải XANH**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e19_events_store.py -v`
Expected: 8 passed

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/events_store.py backend/tests/etl/test_e19_events_store.py
git commit -m "feat(etl): events store - mint minimal issuers, upsert by natural key, never update issuers"
```

---

## Task 5 — `events_job` và CLI

**Files:** Create `backend/etl/events_job.py` · Modify `backend/etl/__main__.py` · Test `backend/tests/etl/test_e20_events_job.py`

**Interfaces — Consumes:** cả bốn module trên, `omo_store.open_run/close_run`, `core.env.load_dotenv`.
**Produces:** `run(accept_new: bool = False) -> int` — `0` xong, `1` guard từ chối, `2` lỗi khác.

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/etl/test_e20_events_job.py
import json
import pathlib

import sqlalchemy as sa

from etl import events_job

FIX = pathlib.Path(__file__).parent / "fixtures" / "events"
NAME = {"AGM": "agm", "CashDividend": "cashdividend", "StockDividend": "stockdividend",
        "Earning": "earning", "IPO": "ipo", "ShareIssuance": "shareissuance"}


def _pages(broken=None):
    out = {}
    for fam, stem in NAME.items():
        text = (FIX / f"{stem}-sample-20260903.json").read_text(encoding="utf-8")
        if fam == broken:                                  # bỏ 1 bản ghi ⇒ vế (i) đỏ
            d = json.loads(text)
            d["items"] = d["items"][:-1]
            text = json.dumps(d, ensure_ascii=False)
        out[fam] = [text]
    return out


def _wire(monkeypatch, engine, pages):
    monkeypatch.setenv("ETL_DATABASE_URL", str(engine.url.render_as_string(hide_password=False)))
    monkeypatch.setattr("etl.events_fetch.fetch", lambda: (pages, 0))
    monkeypatch.setattr("etl.events_job.load_dotenv", lambda *a, **k: None)
    # 🔴 Fixture CỐ Ý dày đặc ca biên: 4 trùng / 28 bản ghi = 14,3%, trong khi lượt thật là
    # 42/110.737 = 0,037%. Ngưỡng 0,5% của vế (iv) đúng cho lượt thật và SAI cho fixture —
    # không có dòng này thì job bị chính guard của nó từ chối và 3 test dưới đỏ.
    # File này kiểm ĐẤU NỐI của job; ngưỡng do test_e18 sở hữu — nới ở đây, KHÔNG nới ở đó.
    monkeypatch.setattr("etl.events_guard.DUP_RATIO", 0.5)


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM market.corporate_event"))
        c.execute(sa.text("DELETE FROM market.issuer_external_id WHERE source = 'fiintrade'"))
        c.execute(sa.text("DELETE FROM market.issuer WHERE issuer_id NOT IN"
                          " (SELECT issuer_id FROM market.security WHERE issuer_id IS NOT NULL)"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = 'market.events'"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE endpoint_key = 'events:refusal'"))


def test_missing_env_exits_two(monkeypatch):
    monkeypatch.delenv("ETL_DATABASE_URL", raising=False)
    monkeypatch.setattr("etl.events_job.load_dotenv", lambda *a, **k: None)
    assert events_job.run() == 2


def test_full_run_writes_rows_and_records_stats(migrated_engine, monkeypatch):
    _cleanup(migrated_engine)
    _wire(monkeypatch, migrated_engine, _pages())
    assert events_job.run(accept_new=True) == 0            # 17 issuer > ngưỡng 20? không, nhưng
    with migrated_engine.begin() as c:                     # cờ vẫn hợp lệ và không đổi kết quả
        n = c.execute(sa.text("SELECT count(*) FROM market.corporate_event")).scalar_one()
        stats = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = 'market.events'"
            " ORDER BY run_id DESC LIMIT 1")).scalar_one()
        wm = c.execute(sa.text(
            "SELECT watermark FROM ops.data_domain_state"
            " WHERE domain = 'market.events'")).scalar_one()
    assert n == 24
    assert stats["rows_written"] == 24 and stats["issuers_created"] == 17
    assert stats["dup_conflicts"] == 4 and len(stats["dup_keys"]) == 4
    assert wm == "2026-09-03"                              # publicDate lớn nhất trong fixture
    _cleanup(migrated_engine)


def test_second_run_is_idempotent(migrated_engine, monkeypatch):
    _cleanup(migrated_engine)
    _wire(monkeypatch, migrated_engine, _pages())
    assert events_job.run(accept_new=True) == 0
    assert events_job.run() == 0
    with migrated_engine.begin() as c:
        n = c.execute(sa.text("SELECT count(*) FROM market.corporate_event")).scalar_one()
        stats = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = 'market.events'"
            " ORDER BY run_id DESC LIMIT 1")).scalar_one()
    assert n == 24 and stats["issuers_created"] == 0
    _cleanup(migrated_engine)


def test_guard_refusal_writes_nothing_and_leaves_evidence(migrated_engine, monkeypatch):
    _cleanup(migrated_engine)
    _wire(monkeypatch, migrated_engine, _pages(broken="AGM"))
    assert events_job.run() == 1
    with migrated_engine.begin() as c:
        assert c.execute(sa.text("SELECT count(*) FROM market.corporate_event")).scalar_one() == 0
        # 🔴 issuer cũng phải bị rollback — chúng được tạo TRONG cùng giao dịch
        assert c.execute(sa.text(
            "SELECT count(*) FROM market.issuer_external_id"
            " WHERE external_code = '12681'")).scalar_one() == 0
        status, err = c.execute(sa.text(
            "SELECT status, error FROM ops.etl_run WHERE job = 'market.events'"
            " ORDER BY run_id DESC LIMIT 1")).one()
        ev = c.execute(sa.text(
            "SELECT count(*) FROM staging.raw_payload"
            " WHERE endpoint_key = 'events:refusal'")).scalar_one()
    assert status == "failed" and "thiếu trang" in err and ev == 1
    _cleanup(migrated_engine)


def test_job_runs_under_the_etl_role(migrated_engine, monkeypatch):
    """§3.5: mọi đường đọc/ghi của job phải chạy dưới đúng quyền production."""
    _cleanup(migrated_engine)
    _wire(monkeypatch, migrated_engine, _pages())
    real_create = events_job.sa.create_engine

    def create_engine_with_role(url, **kw):
        eng = real_create(url, **kw)

        @sa.event.listens_for(eng, "connect")
        def _set_role(dbapi_conn, _rec):
            cur = dbapi_conn.cursor(); cur.execute("SET ROLE dlck_etl"); cur.close()

        return eng

    monkeypatch.setattr(events_job.sa, "create_engine", create_engine_with_role)
    assert events_job.run(accept_new=True) == 0
    _cleanup(migrated_engine)
```

- [ ] **Bước 2: Chạy để chắc chắn nó ĐỎ**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e20_events_job.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'etl.events_job'`

- [ ] **Bước 3: Viết code tối thiểu cho xanh**

```python
# backend/etl/events_job.py
"""Một lần chạy events: fetch → normalize → ensure_issuers → guard → apply → close_run.

Y khuôn `screener_job.py`: một giao dịch cho dữ liệu; guard đánh giá TRƯỚC commit —
từ chối thì raise bên trong `with engine.begin()` để tự rollback (kể cả issuer vừa tạo);
bằng chứng ghi ở giao dịch riêng.
"""
from __future__ import annotations

import logging
import os
import sys

import sqlalchemy as sa

from core.env import load_dotenv
from etl import events_fetch, events_guard, events_normalize, events_store, omo_store

log = logging.getLogger("etl.events")
JOB = events_store.JOB


class GuardRefused(Exception):
    def __init__(self, verdict):
        self.verdict = verdict
        super().__init__("; ".join(verdict.reasons))


def run(accept_new: bool = False) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    load_dotenv()
    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        log.error("thiếu ETL_DATABASE_URL")
        return 2
    engine = sa.create_engine(url)
    run_id = omo_store.open_run(engine, JOB)
    try:
        pages, retries = events_fetch.fetch()
        n = events_normalize.normalize(pages)
        baseline = events_store.load_baseline(engine)
        try:
            with engine.begin() as conn:
                issuer_by_organ, issuers_new = events_store.ensure_issuers(conn, n.rows)
                verdict = events_guard.check(n.counts, n.collected, baseline, issuers_new,
                                             n.dup_conflicts, len(n.rows), accept_new=accept_new)
                if not verdict.ok:
                    raise GuardRefused(verdict)
                apply_stats = events_store.apply(conn, n.rows, issuer_by_organ)
        except GuardRefused as e:
            events_store.store_refusal_evidence(engine, pages, run_id, e.verdict,
                                                n.counts, n.collected)
            omo_store.close_run(engine, run_id, "failed",
                                error="guard refused: " + "; ".join(e.verdict.reasons))
            log.error("events từ chối: %s", e.verdict.reasons)
            return 1
        watermark = max(r.public_date for r in n.rows if r.public_date).isoformat()
        stats = {"counts": n.counts, "collected": n.collected, **apply_stats,
                 "issuers_created": issuers_new, "dup_conflicts": n.dup_conflicts,
                 "dup_keys": n.dup_keys, "retries": retries, "watermark": watermark}
        omo_store.close_run(engine, run_id, "success", stats)
        events_store.upsert_domain_state(engine, watermark)
        log.info("events xong: %s", {k: v for k, v in stats.items() if k != "dup_keys"})
        return 0
    except Exception as e:  # noqa: BLE001 — job biên ngoài: mọi lỗi đều phải vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("events thất bại")
        return 2
    finally:
        engine.dispose()
```

- [ ] **Bước 4: Nối CLI**

Sửa `backend/etl/__main__.py` — thêm nhánh sau nhánh `screener`, và **sửa cả dòng thông báo lỗi** (nếu quên thì `etl xyz` vẫn báo "hỗ trợ: omo, refdata, screener"):

```python
    if args[0] == "events":
        import etl.events_job
        parser = argparse.ArgumentParser(prog="etl events")
        parser.add_argument("--accept-new", action="store_true")
        parsed = parser.parse_args(args[1:])
        return etl.events_job.run(accept_new=parsed.accept_new)
    print(f"etl: subcommand không hợp lệ: {args[0]!r} (hỗ trợ: omo, refdata, screener, events)",
          file=sys.stderr)
```

Thêm test vào `backend/tests/etl/test_e01_cli.py`:

```python
def test_events_subcommand_passes_accept_new_through(monkeypatch, capsys):
    import etl.events_job
    from etl.__main__ import main
    seen = {}

    def fake_run(accept_new=False):
        seen["accept_new"] = accept_new
        return 0

    monkeypatch.setattr(etl.events_job, "run", fake_run)
    assert main(["events", "--accept-new"]) == 0 and seen["accept_new"] is True
    assert main(["events"]) == 0 and seen["accept_new"] is False
    assert main(["nope"]) == 2 and "events" in capsys.readouterr().err
```

⚠️ `fake_run` phải là **hàm thật, không lambda**: `lambda: seen.setdefault(...) or 0` trả về `True` chứ không trả `0`, và `main()` sẽ trả `True` — phép so `== 0` hỏng.

- [ ] **Bước 5: Chạy lại — phải XANH**

Run: `PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e20_events_job.py tests/etl/test_e01_cli.py -v`
Expected: 5 passed (e20) + toàn bộ e01 passed

- [ ] **Bước 6: Chạy TRỌN bộ test — không được vỡ cái gì**

Run: `PYTHONIOENCODING=utf-8 uv run pytest -q`
Expected: **0 failed**. Số test = 351 *(mốc sau lát 1)* + 35 mới của lát này (5 + 9 + 7 + 8 + 5 + 1). Nếu tổng không phải 386 thì có test bị bỏ quên hoặc trùng tên — soi trước khi đi tiếp. **Dán output thật vào ledger.**

- [ ] **Bước 7: Commit**

```bash
git add backend/etl/events_job.py backend/etl/__main__.py backend/tests/etl/test_e20_events_job.py backend/tests/etl/test_e01_cli.py
git commit -m "feat(etl): events job and 'etl events' subcommand with --accept-new"
```

---

## Task 6 — Chạy thật: backfill và nghiệm thu AC2–AC5

⚠️ **Task này ghi vào kho production.** Chạy tay, có người nhìn. Không giao subagent chạy một mạch.

**Files:** không sửa code (trừ khi lộ bug) · Create `docs/90-records/plans/2026-09-03-events-daily-etl/ledger.md`

- [ ] **Bước 1: Dọn danh bạ trước — nếu chưa dọn**

`etl refdata` báo đỏ từ 01/09 (438 mã chờ gỡ). Lượt dọn **không thêm issuer nào** nên không đổi con số 517, nhưng nên dọn trước để kho nhất quán:

```bash
cd backend && set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl refdata --accept-drop
```

Expected: exit 0. Ghi `stats` vào ledger.

- [ ] **Bước 2: Đếm trạng thái TRƯỚC khi chạy**

```bash
psql "$ETL_DATABASE_URL" -c "SELECT (SELECT count(*) FROM market.corporate_event) AS events, (SELECT count(*) FROM market.issuer) AS issuers"
```

Expected: `events = 0`, `issuers = 1552` *(đo 2026-09-03)*. Ghi số thật vào ledger.

- [ ] **Bước 3: Lượt backfill đầu tiên — AC2**

```bash
cd backend && set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl events --accept-new
```

Expected: exit 0, ~140 giây. Kiểm **bất biến**, không kiểm con số cứng:

```sql
SELECT stats->>'rows_written' = (SELECT count(*)::text FROM market.corporate_event) AS khop_so_dong,
       stats->'counts', stats->>'issuers_created', stats->>'dup_conflicts', stats->>'watermark'
  FROM ops.etl_run WHERE job = 'market.events' ORDER BY run_id DESC LIMIT 1;
```

Expected: `khop_so_dong = t`. Ghi mọi số thật vào ledger.

🔴 **Nếu `issuers_created` lệch xa 517** thì DỪNG và soi trước khi chạy tiếp — nguồn có thể đã đổi hệ mã `organCode`.

- [ ] **Bước 4: Lượt hai — AC3 idempotent**

```bash
cd backend && set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -m etl events
```

Expected: exit 0 **không cần cờ** (lượt này tạo ~0 issuer), `count(*)` không đổi, `issuers_created = 0`.

- [ ] **Bước 5: AC4 — guard từ chối thật, bằng đột biến**

Chạy một lượt có đột biến, dùng `python -c` để tiêm trang thiếu bản ghi, và **đếm trước/sau phải bằng nhau**:

```bash
cd backend && set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run python -c "
import json, sqlalchemy as sa, os
from etl import events_fetch, events_job
real = events_fetch.fetch
def broken():
    pages, r = real()
    d = json.loads(pages['IPO'][0]); d['items'] = d['items'][:-1]
    pages['IPO'] = [json.dumps(d, ensure_ascii=False)]
    return pages, r
events_fetch.fetch = broken
e = sa.create_engine(os.environ['ETL_DATABASE_URL'])
before = e.connect().execute(sa.text('SELECT count(*) FROM market.corporate_event')).scalar_one()
code = events_job.run()
after = e.connect().execute(sa.text('SELECT count(*) FROM market.corporate_event')).scalar_one()
print('exit', code, '| truoc', before, '| sau', after, '| KHONG GHI GI:', before == after)
"
```

Expected: `exit 1`, `KHONG GHI GI: True`. Kiểm thêm `staging.raw_payload` có đúng 1 dòng `events:refusal` mới.

- [ ] **Bước 6: AC5 — dữ liệu dùng được cho lát sau**

```sql
SELECT count(*) FROM market.corporate_event WHERE exright_date >= current_date;
```

Expected: **> 0** — đây là tín hiệu mà lát 3/4 sẽ đọc để kích hoạt re-crawl giá.

- [ ] **Bước 7: Ghi ledger và commit**

```bash
git add docs/90-records/plans/2026-09-03-events-daily-etl/ledger.md
git commit -m "docs(ledger): events backfill acceptance runs against the real database"
```

---

## Task 7 — Đăng ký task và đồng bộ tài liệu sống

**Files:** Modify `scripts/register-tasks.ps1` · `backend/README.md` · `docs/10-sources/market/08-fiin-event-calendar.md` · `docs/20-design/market-data-store.md` · `docs/00-overview/roadmap.md` · `docs/90-records/README.md`

- [ ] **Bước 1: Thêm task thứ 9**

Chèn vào `scripts/register-tasks.ps1` ngay sau khối `dlck-screener`:

```powershell
Write-Host "Đăng ký events (18:00 ngày làm việc — sau phiên và sau screener 15:20, dùng danh bạ tươi từ 08:00):"
Register-DlckTask -TaskName "dlck-events" -AtTime "18:00" -ModuleArgs "etl events" -LogFile "events.log"
Assert-TaskCommand -TaskName "dlck-events" -MustContain "python -m etl events" -MustNotContain "--accept-new"
```

⚠️ `-MustNotContain "--accept-new"` là chốt chặn thật: task chạy tự động **không bao giờ** được mang cờ cho phép đẻ issuer hàng loạt.

Sửa hai dòng đếm trong cùng file: `"Đã kiểm lệnh của cả 8 task"` → **9**, và `"Cả 8 task đăng ký S4U"` → **9**.

- [ ] **Bước 2: Chạy script trong cửa sổ Run as Administrator**

```powershell
pwsh -File scripts/register-tasks.ps1
Get-ScheduledTask -TaskName "dlck-events" | Select-Object TaskName, State
Disable-ScheduledTask -TaskName "dlck-events"
```

Expected: `Assert-TaskCommand` không ném lỗi; task cuối cùng ở trạng thái **`Disabled`** cùng cả đội.

⚠️ Script tự `Enable` `dlck-ingester` — chạy nó trong lúc tạm dừng thì phải `Disable` lại ngay.

- [ ] **Bước 3: Sửa tầng reference — có quyền vì ĐÃ ĐO LẠI (§1.2)**

Trong `docs/10-sources/market/08-fiin-event-calendar.md`:
1. Thêm mục **"Trục lọc `FromDate` — đo 2026-09-03"** với bảng sáu họ và ca Earning.
2. Thêm **"`PageSize` không có trần"** *(đo 2026-09-03)*.
3. 🔴 Sửa câu ở đầu file — *"Trường `sourceUrl` trỏ thẳng về bản công bố gốc"* → nói rõ **chỉ `getCorporateAGM` trả trường này**; năm họ `GetCorporate*` kia không có.
4. Cập nhật `totalCount` sáu họ, **kèm ngày đo 2026-09-03**, giữ nguyên số cũ kèm ngày cũ để thấy độ trôi.

- [ ] **Bước 4: Sửa tầng design**

`docs/20-design/market-data-store.md`:
- §4.1 dòng lịch sự kiện: bỏ *"(dùng `FromDate` lấy phần mới)"*, ghi **tải trọn, 9 lời gọi**.
- §4.2 dòng *"Lịch sự kiện toàn bộ | ~500 | vài phút"* → **9 lời gọi, ~140 giây**.

- [ ] **Bước 5: Sửa roadmap và index**

- `roadmap.md` dòng trạng thái code: lát 2 xong, số test mới.
- `roadmap.md` mục **"Điểm vào cho lát 2"** → viết lại thành điểm vào **lát 3 (giá theo ngày)**, kèm bài học của lát 2.
- `roadmap.md` [4d] và dòng bàn giao: **8 task → 9 task**.
- `backend/README.md`: dòng 13 thêm `etl events`; dòng 99 **8 task → 9 task** kèm mô tả `dlck-events` 18:00; thêm khối lệnh chạy tay giống `etl screener`.
- `docs/90-records/README.md`: cập nhật dòng của plan này sang ✅.

- [ ] **Bước 6: Phép kiểm §1.7 — không được tuyên "đã đồng bộ" nếu chưa chạy**

```bash
git grep -n "FromDate" -- docs/ | grep -v "90-records\|decisions/"
git grep -n "~500 " -- docs/20-design/
git grep -rn "8 task\|cả 8 task" -- docs/ backend/ scripts/
```

Expected: mọi hit còn lại **hoặc đã đúng, hoặc thuộc vùng lịch sử** (`90-records/`, `decisions/` — không viết lại quá khứ). Dán kết quả vào ledger.

- [ ] **Bước 7: Commit**

```bash
git add scripts/register-tasks.ps1 backend/README.md docs/
git commit -m "docs(events): sync the living docs to what the calendar source actually does"
```

---

## Tự rà plan

**Phủ spec:** §5.2 → Task 1 · §5.3 → Task 2 · §5.4 → Task 3 · §5.5 → Task 4 · §5.1 + CLI → Task 5 · §5.6 → Task 7 · §6 (11 seam) → rải trong Task 1–5, **đủ cả 11** · §7 (AC1–AC6) → AC1 Task 5 bước 6, AC2–AC5 Task 6, AC6 Task 7 · §8 → Task 7.

**Nhất quán kiểu:** `EventRow` dùng nguyên tên trường ở cả Task 2/4/5 · `GuardVerdict.families` sinh ở Task 3, tiêu thụ ở Task 4 (`store_refusal_evidence`) và Task 5 · `counts`/`collected` là `dict[str, int]` khoá bằng `event_type` xuyên suốt, khớp `FAMILIES` của Task 1.

**Ba con số chốt toàn bộ bộ test** — 24 dòng · `dup_conflicts = 4` · 17 issuer — tính bằng cách áp luật spec lên fixture, không phải đếm tay, và lặp lại y nguyên ở Task 2, 4, 5.
