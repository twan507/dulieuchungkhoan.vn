# `etl screener` — kế hoạch thực thi

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Một subcommand `python -m etl screener` gom 52 trang `GetScreenerItems` mỗi ngày giao dịch, ghi các trường đã chọn vào `market.screener_daily`, và **từ chối ghi** khi nguồn không có phiên — kèm vá bảng chọn trường cho đủ 193/193 khoá.

**Architecture:** Y khuôn job `refdata` đã nghiệm thu thật: `open_run` → fetch (I/O thuần) → normalize (thuần) → merge (đọc DB) → **guard trước commit** → `apply` trong một `engine.begin()` → `close_run`; bằng chứng từ chối ghi ở giao dịch riêng. Sáu module nhỏ `etl/screener_*.py`, không lớp HTTP chung, không luồng — 52 lời gọi tuần tự là đúng mức đã đo an toàn.

**Tech Stack:** Python 3.12 · `httpx` · SQLAlchemy 2 + psycopg 3 · Postgres thật cho test (`TEST_DATABASE_URL`) · pytest · Task Scheduler (`scripts/register-tasks.ps1`).

**Spec:** [`spec.md`](spec.md) cùng thư mục — **đã duyệt 2026-09-03**. Plan lập luận từ spec; người thực thi đọc cả hai. Bằng chứng số đo: [`samples/`](samples/).

## Global Constraints

- Mọi lệnh Python chạy tại **`backend/`**, đặt `PYTHONIOENCODING=utf-8`, nạp `.env` bằng `set -a; . ../.env; set +a` — **không in giá trị biến ra output**.
- Test DB: `uv run pytest tests/etl/<file> -v` cần `TEST_DATABASE_URL` (fixture `migrated_engine` dựng lại `dulieu_test` từ đầu mỗi session pytest — chậm vài giây lần đầu, bình thường).
- Cả bộ hiện có **321 passed, 2 skipped** — không được giảm.
- **Không sửa migration đã chạy** (`0001`–`0014`). Lát này **không cần migration mới**: `market.screener_daily`, `ops.etl_run`, `ops.data_domain_state`, `staging.raw_payload` đã có.
- `market-field-selection.md` / `.json` **sinh tự động** — chỉ sửa `gen_field_selection.py` rồi chạy lại; **cấm sửa tay** hai file sinh.
- **Không ép con số 80** (spec §4.3): số `keep` là kết quả đếm, dự kiến **77**. Ép cho ra 80 là lỗi.
- Toàn bộ 7 task `dlck-*` đang **`Disabled`** (roadmap [4d], 2026-09-03). `dlck-screener` đăng ký xong cũng **để `Disabled`**. Chạy `register-tasks.ps1` sẽ tự **bật lại** `dlck-ingester` ⇒ ngay sau khi chạy script phải tắt lại cả đội (Task 8 bước 4).
- Guard **(i) `closePrice > 0`** là lý do tồn tại của lát này — không được "tạm bỏ để test cho tiện".
- Conventional Commits, message tiếng Anh, làm trên nhánh `feat/screener-daily-etl`, không `--no-verify`, không force push. Artifact tạm (report subagent, log) ở scratchpad ngoài repo; **cấm tạo `.superpowers/` trong repo**.
- Nhịp gọi nguồn: **tuần tự, 52 lời gọi/lượt**. Chạy tay thật tối đa **2 lượt/ngày** (AC3 + AC4) — không "chạy thử thêm cho chắc".

---

## Cấu trúc file

| File | Trách nhiệm | Task |
|---|---|---|
| `docs/20-design/gen_field_selection.py` (sửa) | thêm 66 khoá Screener, gỡ số 80 cứng | 1 |
| `docs/20-design/market-field-selection.{md,json}` (sinh lại) | bảng chọn trường 193/193 | 1 |
| `backend/tests/etl/fixtures/screener/` (mới) | 2 response thật + README | 2 |
| `backend/etl/screener_normalize.py` (mới) | item → `ScreenerRow`; nạp keep-set từ JSON | 2 |
| `backend/etl/screener_fetch.py` (mới) | 52 trang tuần tự, retry có kiểm soát | 3 |
| `backend/etl/screener_guard.py` (mới) | ba vế từ chối, thuần | 4 |
| `backend/etl/screener_store.py` (mới) | merge ticker→security_id · baseline · apply UPSERT · bằng chứng · domain_state | 5 |
| `backend/etl/screener_job.py` (mới) + `backend/etl/__main__.py` (sửa) | dàn nhạc + subcommand | 6 |
| `ledger.md` (mới, cùng thư mục) | số thật của AC3–AC6 | 7, 8 |
| `scripts/register-tasks.ps1` + tài liệu sống §8 spec | task `dlck-screener` 15:20 (Disabled) + đồng bộ docs | 8 |

Thứ tự thực thi = thứ tự task. Task 2–4 độc lập nhau về code (chỉ chung fixture) nhưng làm tuần tự để mỗi commit là một seam trọn.

---

### Task 1: Vá bảng chọn trường cho đủ 193/193 (spec §4)

**Files:**
- Modify: `docs/20-design/gen_field_selection.py` — khối `# ───── Screener — BO ─────` (từ dòng 138) thêm 5 lời gọi `add`; khối `# ───── Screener — GIU ─────` (dòng 96–137) thêm 1 lời gọi; dòng 100 và các dòng 611/756–758 gỡ số 80 cứng.
- Regenerate: `docs/20-design/market-field-selection.md`, `docs/20-design/market-field-selection.json`
- Test: script đếm chạy tay (bước 1 và 5) — không có pytest cho tầng docs.

**Interfaces:**
- Produces: `market-field-selection.json` với **193 dòng `source == "Screener"`**, `keep is True` đếm ra **N** (dự kiến 77). Task 2 nạp keep-set từ đúng file này.

- [ ] **Bước 1: Viết phép kiểm "đỏ" — đếm hiện trạng**

Tạo `C:\Users\<user>\...\scratchpad\count_selection.py` (ngoài repo):

```python
import json, sys
rows = json.load(open("docs/20-design/market-field-selection.json", encoding="utf-8"))
scr = [r for r in rows if r["source"] == "Screener"]
live = {k for it in json.load(open("docs/90-records/plans/2026-09-03-screener-daily-etl/samples/page1-20260828-postclose.json", encoding="utf-8"))["items"]
        for b in it.values() if b for k in b}
codes = {r["code"] for r in scr}
print("dòng Screener:", len(scr), "| keep True:", sum(r["keep"] is True for r in scr),
      "| keep False:", sum(r["keep"] is False for r in scr), "| keep None:", sum(r["keep"] is None for r in scr))
print("khoá thật:", len(live), "| thiếu trong bảng:", sorted(live - codes))
sys.exit(0 if live <= codes else 1)
```

Chạy tại gốc repo: `PYTHONIOENCODING=utf-8 python <scratchpad>/count_selection.py`
Expected: `dòng Screener: 127 | keep True: 59 …`, `thiếu trong bảng:` liệt kê **66** khoá, exit 1.

- [ ] **Bước 2: Thêm 66 khoá vào generator**

Trong `gen_field_selection.py`, ngay **sau** lời gọi `add([... "isi103Y", "rev", "prf"], …)` cuối khối GIU (kết thúc ở dòng ~137, trước dòng `# ───── Screener — BO ─────`), chèn:

```python
# ───────────────────────── Screener — 66 khoá lần đầu có tên (đo 2026-08-28) ─────────────────────────
# Không tài liệu nguồn nào liệt kê 66 khoá này (§7.5 bản trước). Tên lấy từ response thật
# GetScreenerItems 2026-08-28 (docs/90-records/plans/2026-09-03-screener-daily-etl/samples/).
# 48 khoá xếp bằng luật đã chốt; 18 mã tỷ số xếp `lấy` theo duyệt 2026-09-03 (spec §4.2, §9).
R_NEW = ("tỷ số tài chính — không rơi vào nhóm bỏ nào, cùng họ với cụm tỷ số không nguồn nào khác có; "
         "duyệt 2026-09-03 (spec etl screener §4.2)")
add(["isa3", "isa5", "ryq2", "ryq3", "ryq6"], "Screener", "Screener", True, R_NEW, block="Tỷ số (đo 2026-08-28)")
add(["fryq30", "grossMargin", "profitGrowth", "revenueGrowth", "roe", "rqd25", "rqd52", "rtd20", "rtd36Avg",
     "rtq160", "rtq166", "rtq176", "ryq4"], "Screener", "Screener", True,
    R_NEW + " — KHÔNG có trong từ điển 729 mã: lưu trước, giải mã sau (bundle JS FiinTrade)",
    status="chưa giải mã", block="Tỷ số (đo 2026-08-28)",
    names={"fryq30": "chưa giải mã", "grossMargin": "Biên lãi gộp (suy từ tên khoá)",
           "profitGrowth": "Tăng trưởng lợi nhuận (suy từ tên khoá)",
           "revenueGrowth": "Tăng trưởng doanh thu (suy từ tên khoá)", "roe": "ROE (suy từ tên khoá)",
           "rqd25": "chưa giải mã", "rqd52": "chưa giải mã", "rtd20": "chưa giải mã",
           "rtd36Avg": "chưa giải mã", "rtq160": "chưa giải mã", "rtq166": "chưa giải mã",
           "rtq176": "chưa giải mã", "ryq4": "chưa giải mã"},
    nsrc="tự đặt")
```

Rồi ngay **sau** lời gọi `add` cuối cùng của khối `# ───── Screener — BO ─────` (trước khối `# ───── Screener — DA CHOT BANG SO DO 2026-08-15 ─────`, dòng ~191), chèn:

```python
add(["comGroupCode", "icbCode", "isForecastTime", "marketStatus", "matchType", "organCode", "rateAdjusted",
     "referenceDate", "ticker", "tradingDate"], "Screener", "—", False,
    "metadata của response, không phải chỉ tiêu — `tradingDate` là timestamp riêng từng mã và ĐÃ mang ngày "
    "hôm nay từ trước mở cửa (đo 2026-09-03), ETL chỉ dùng nó để lấy ngày, không lưu",
    names={c: "metadata" for c in ["comGroupCode", "icbCode", "isForecastTime", "marketStatus", "matchType",
                                    "organCode", "rateAdjusted", "referenceDate", "ticker", "tradingDate"]},
    nsrc="tự đặt", block="Metadata (đo 2026-08-28)")
add(["atoPrice", "atoVolume", "averagePrice", "ceilingPrice", "dealPrice", "dealValue", "dealVolume",
     "expectedTradePrice", "expectedTradeVolume", "floorPrice", "foreignBuyValueTotal", "foreignBuyVolumeTotal",
     "foreignCurrentRoom", "foreignSellValueTotal", "foreignSellVolumeTotal", "foreignTotalRoom", "highestPrice",
     "lowestPrice", "matchPrice", "matchValue", "matchVolume", "openPrice", "percentPriceChange", "priceChange",
     "referencePrice", "totalDealValue", "totalDealVolume", "totalValue", "totalVolume"],
    "Screener", "BVSC", False,
    "trùng BVSC — nhóm giá/khối ngoại/thoả thuận, nguồn chuẩn là BVSC realtime + `datafeed/instruments`",
    names={c: "giá/khối ngoại (khối priceInfo)" for c in
           ["atoPrice", "atoVolume", "averagePrice", "ceilingPrice", "dealPrice", "dealValue", "dealVolume",
            "expectedTradePrice", "expectedTradeVolume", "floorPrice", "foreignBuyValueTotal",
            "foreignBuyVolumeTotal", "foreignCurrentRoom", "foreignSellValueTotal", "foreignSellVolumeTotal",
            "foreignTotalRoom", "highestPrice", "lowestPrice", "matchPrice", "matchValue", "matchVolume",
            "openPrice", "percentPriceChange", "priceChange", "referencePrice", "totalDealValue",
            "totalDealVolume", "totalValue", "totalVolume"]},
    nsrc="tự đặt", block="Trùng BVSC (đo 2026-08-28)")
add(["percentPriceChange1Year", "percentPriceChange2Month", "percentPriceChange2Week", "percentPriceChange9Month"],
    "Screener", "BVSC (tự tính)", False, "biến động giá — tính lại được từ chuỗi giá BVSC",
    names={"percentPriceChange1Year": "Biến động giá 1 năm", "percentPriceChange2Month": "Biến động giá 2 tháng",
           "percentPriceChange2Week": "Biến động giá 2 tuần", "percentPriceChange9Month": "Biến động giá 9 tháng"},
    nsrc="tự đặt", block="Biến động giá (đo 2026-08-28)")
add(["icbTotalRanked", "indexRank", "indexTotalRanked"], "Screener", "— (không lưu)", False,
    "nhóm chấm điểm/xếp hạng riêng của FiinTrade — quyết định của chủ dự án: không dùng điểm do bên thứ ba chấm",
    names={"icbTotalRanked": "Tổng số mã được xếp hạng trong ngành", "indexRank": "Hạng trong rổ chỉ số",
           "indexTotalRanked": "Tổng số mã được xếp hạng trong rổ"},
    nsrc="tự đặt", block="Chấm điểm (đo 2026-08-28)")
add(["cmf", "sma20Past4"], "Screener", "BVSC (tự tính)", False, "chỉ báo kỹ thuật — tính lại được từ chuỗi giá",
    names={"cmf": "Chaikin Money Flow", "sma20Past4": "SMA20 của 4 phiên trước"},
    nsrc="tự đặt", block="Chỉ báo kỹ thuật (đo 2026-08-28)")
```

- [ ] **Bước 3: Gỡ số 80 cứng — ba chỗ**

Dòng ~100: `"nên thuộc 80 trường giữ")` → `"nên thuộc nhóm giữ")`.

Dòng ~611 trong template: `| **Tổng giữ** | **80** | **{scr_keep_n}** | **{scr_keep_lech}** |` → `| **Tổng giữ** | **80** *(ước lượng theo nhóm 2026-08-14)* | **{scr_keep_n}** *(đếm 2026-09-03)* | **{scr_keep_lech}** |`. Giữ nguyên các biến `scr_keep_lech*` ở dòng 756–758 — chúng phải **hiện ra lệch** (đó là điểm của §7: *"Lệch không bị ép cho khớp"*).

Dòng ~483: `| Tỷ số tài chính, Beta, sở hữu tổ chức, TTM | **Screener** | 80/193 |` → `| Tỷ số tài chính, Beta, sở hữu tổ chức, TTM | **Screener** | {scr_keep_n}/193 |`. Dòng này nằm **trong** template `md = """…"""` (bắt đầu dòng 436, `.format(` ở dòng 747, và `scr_keep_n=` đã là kwarg ở dòng 753) — nên `{scr_keep_n}` được thay lúc render. ⚠️ Vì template dùng `.format`, **không** đưa dấu `{`/`}` nào khác vào các đoạn văn mới của bước này.

- [ ] **Bước 4: Sinh lại hai file**

```bash
cd docs/20-design && PYTHONIOENCODING=utf-8 python gen_field_selection.py && cd ../..
git diff --stat docs/20-design/
```
Expected: `market-field-selection.md` và `.json` đổi; **không** file nào khác.

- [ ] **Bước 5: Chạy lại phép kiểm — phải xanh**

`PYTHONIOENCODING=utf-8 python <scratchpad>/count_selection.py`
Expected: `dòng Screener: 193 | keep True: 77 | keep False: 112 | keep None: 4`, `thiếu trong bảng: []`, exit 0.
*(4 `None` = 4 dòng `cần kiểm API` cũ. Nếu `keep True` ra khác 77 thì **ghi số thật**, đừng sửa cho bằng.)*

Mở `market-field-selection.md` §7.3: dòng *"Chưa liệt kê được"* phải là **0**.

- [ ] **Bước 6: Đồng bộ "80/193" ở tài liệu sống (§1.7)**

```bash
git grep -n "80/193" -- README.md docs/00-overview docs/10-sources docs/20-design
```
Mỗi hit ngoài `market-field-selection.md`: thêm *"(ước lượng 2026-08-14; đếm 2026-09-03: 77/193)"* ngay sau. Không sửa `90-records/`, `decisions/`.

- [ ] **Bước 7: Commit**

```bash
git checkout -b feat/screener-daily-etl
git add docs/20-design/gen_field_selection.py docs/20-design/market-field-selection.md docs/20-design/market-field-selection.json README.md docs/00-overview docs/10-sources
git commit -m "docs(field-selection): name the 66 screener keys no vendor doc lists; count keeps instead of assuming 80"
```

---

### Task 2: `screener_normalize` — item → `ScreenerRow` (spec §5.3)

**Files:**
- Create: `backend/tests/etl/fixtures/screener/page1-20260828-postclose.json` (chép từ `docs/90-records/plans/2026-09-03-screener-daily-etl/samples/`), `page1-20260903-preopen.json` (nt), `README.md`
- Create: `backend/etl/screener_normalize.py`
- Test: `backend/tests/etl/test_e11_screener_normalize.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class ScreenerRow:
      ticker: str; exchange: str; organ_code: str | None
      trading_date: datetime.date; close_price: float; payload: dict
  @dataclass(frozen=True)
  class NormResult:
      rows: list[ScreenerRow]; total_count: int
      unknown_com_group: int; null_blocks: int
  KEEP: dict[str, frozenset[str]]              # khối → khoá keep, nạp lúc import
  def normalize(pages: list[str]) -> NormResult
  ```
  `pages` là text thô từng trang (đầu ra Task 3). `total_count` lấy từ trang đầu.

- [ ] **Bước 1: Fixture + README**

```bash
mkdir -p backend/tests/etl/fixtures/screener
cp docs/90-records/plans/2026-09-03-screener-daily-etl/samples/page1-20260828-postclose.json backend/tests/etl/fixtures/screener/
cp docs/90-records/plans/2026-09-03-screener-daily-etl/samples/page1-20260903-preopen.json backend/tests/etl/fixtures/screener/
```

`backend/tests/etl/fixtures/screener/README.md`:

```markdown
# Fixture screener — hai response thật `GetScreenerItems` trang 1, `pageSize=30`

Nguyên văn, không cắt. Bản gốc và số đo: `docs/90-records/plans/2026-09-03-screener-daily-etl/`.

| File | Chụp lúc | Literal cho test |
|---|---|---|
| `page1-20260828-postclose.json` | 2026-08-28 20:51, sau phiên | 30 mã, `closePrice > 0` **30/30**; `DDB` UpcomIndex `tradingDate 2026-08-28T15:00:01.533`, `closePrice 9100.0`, `rtd7 12750.50715092`, `rtd11 107400000000.0`, `rtd14 113.41451175`; `V68` có `technical = null`; `CCC`/`AAN`/`SBG` đóng dấu **14:45**; `FUEIP100` là ETF trên VNINDEX; `totalCount 1545` |
| `page1-20260903-preopen.json` | 2026-09-03 08:38, trước mở cửa sau nghỉ lễ | cùng 30 mã, `closePrice > 0` **0/30**, mọi `tradingDate` = `2026-09-03T08:2x`, `referenceDate 2026-08-28` |
```

- [ ] **Bước 2: Test đỏ**

`backend/tests/etl/test_e11_screener_normalize.py`:

```python
import json, pathlib
from datetime import date

import pytest

from etl import screener_normalize as sn

FIX = pathlib.Path(__file__).parent / "fixtures" / "screener"
POST = (FIX / "page1-20260828-postclose.json").read_text(encoding="utf-8")
PRE = (FIX / "page1-20260903-preopen.json").read_text(encoding="utf-8")


def test_keep_set_loaded_from_selection_json():
    # Nguồn độc lập: đếm thẳng file JSON, không qua code normalize
    rows = json.loads((pathlib.Path(sn.SELECTION_JSON)).read_text(encoding="utf-8"))
    expected = {r["code"] for r in rows if r["source"] == "Screener" and r["keep"] is True}
    got = set().union(*sn.KEEP.values())
    assert got == expected
    assert "rtd26" in got and "closePrice" not in got and "icbRank" not in got


def test_ddb_row_values_from_real_sample():
    res = sn.normalize([POST])
    ddb = next(r for r in res.rows if r.ticker == "DDB")
    assert ddb.exchange == "UPCOM"
    assert ddb.organ_code == "0101264009"
    assert ddb.trading_date == date(2026, 8, 28)
    assert ddb.close_price == 9100.0
    assert ddb.payload["stockScreenerItem"]["rtd7"] == 12750.50715092
    assert ddb.payload["stockScreenerItem"]["rtd11"] == 107400000000.0
    assert ddb.payload["financial"]["rtd14"] == 113.41451175
    assert "closePrice" not in ddb.payload.get("priceInfo", {})      # metadata/BVSC không lưu
    assert "technical" not in ddb.payload                             # khối không còn khoá keep → bỏ khối
    assert res.total_count == 1545 and len(res.rows) == 30


def test_null_block_is_dropped_not_crashed():
    res = sn.normalize([POST])
    v68 = next(r for r in res.rows if r.ticker == "V68")
    assert "technical" not in v68.payload
    assert v68.close_price == 19500.0
    assert res.null_blocks == 1


def test_trading_date_is_cut_from_per_ticker_timestamp_1445():
    res = sn.normalize([POST])
    ccc = next(r for r in res.rows if r.ticker == "CCC")
    assert ccc.exchange == "HOSE"
    assert ccc.trading_date == date(2026, 8, 28)      # dấu 14:45, không phải 15:00


def test_unknown_com_group_is_counted_and_skipped():
    d = json.loads(POST)
    d["items"][0]["priceInfo"]["comGroupCode"] = "XYZ"
    res = sn.normalize([json.dumps(d)])
    assert res.unknown_com_group == 1 and len(res.rows) == 29


def test_preopen_sample_has_zero_priced_rows():
    res = sn.normalize([PRE])
    assert sum(1 for r in res.rows if r.close_price > 0) == 0
    assert all(r.trading_date == date(2026, 9, 3) for r in res.rows)
```

- [ ] **Bước 3: Chạy — phải đỏ**

`cd backend && uv run pytest tests/etl/test_e11_screener_normalize.py -v`
Expected: 6 FAIL/ERROR, `ModuleNotFoundError: No module named 'etl.screener_normalize'`.

- [ ] **Bước 4: Implementation tối thiểu**

`backend/etl/screener_normalize.py`:

```python
"""Chuẩn hoá response GetScreenerItems thành ScreenerRow (spec etl screener §5.3).

Thuần — không I/O ngoài việc nạp bảng chọn trường lúc import. Nhận text thô
từng trang (đã fetch sẵn), trả NormResult cho merge/guard/store dùng tiếp.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

log = logging.getLogger(__name__)

# Bảng chọn trường là nguồn sự thật "trường này lấy hay bỏ" — không hardcode danh sách ở đây.
SELECTION_JSON = Path(__file__).resolve().parents[2] / "docs" / "20-design" / "market-field-selection.json"
BLOCKS = ("priceInfo", "stockScreenerItem", "performance", "financial", "technical")
EXCHANGE = {"VNINDEX": "HOSE", "HNXIndex": "HNX", "UpcomIndex": "UPCOM"}


def _load_keep() -> dict[str, frozenset[str]]:
    rows = json.loads(SELECTION_JSON.read_text(encoding="utf-8"))
    keep = frozenset(r["code"] for r in rows if r["source"] == "Screener" and r["keep"] is True)
    # Cùng một tập keep cho mọi khối: 27 khoá trùng khối được giữ ở MỌI khối có nó — không chọn khối ưu tiên.
    return {b: keep for b in BLOCKS}


KEEP = _load_keep()


@dataclass(frozen=True)
class ScreenerRow:
    ticker: str
    exchange: str
    organ_code: str | None
    trading_date: date
    close_price: float
    payload: dict


@dataclass(frozen=True)
class NormResult:
    rows: list[ScreenerRow]
    total_count: int
    unknown_com_group: int
    null_blocks: int


def _row(item: dict) -> tuple[ScreenerRow | None, int, bool]:
    """Trả (row | None nếu bỏ, số khối null, bỏ vì com_group lạ?)."""
    pi = item.get("priceInfo") or {}
    exchange = EXCHANGE.get(pi.get("comGroupCode"))
    if exchange is None:
        return None, 0, True
    nulls = 0
    payload: dict = {}
    for b in BLOCKS:
        blk = item.get(b)
        if blk is None:
            nulls += 1
            continue
        kept = {k: v for k, v in blk.items() if k in KEEP[b]}
        if kept:
            payload[b] = kept
    ts = datetime.fromisoformat(pi["tradingDate"])
    return ScreenerRow(
        ticker=pi["ticker"], exchange=exchange, organ_code=pi.get("organCode"),
        trading_date=ts.date(), close_price=float(pi.get("closePrice") or 0.0), payload=payload,
    ), nulls, False


def normalize(pages: list[str]) -> NormResult:
    rows: list[ScreenerRow] = []
    unknown = 0
    nulls = 0
    total_count = 0
    for i, text in enumerate(pages):
        d = json.loads(text)
        if i == 0:
            total_count = int(d["totalCount"])
        for item in d["items"]:
            row, n, skipped = _row(item)
            nulls += n
            if skipped:
                unknown += 1
                continue
            rows.append(row)
    return NormResult(rows=rows, total_count=total_count, unknown_com_group=unknown, null_blocks=nulls)
```

- [ ] **Bước 5: Chạy — phải xanh**

`uv run pytest tests/etl/test_e11_screener_normalize.py -v` → **6 passed**.

- [ ] **Bước 6: Commit**

```bash
git add backend/etl/screener_normalize.py backend/tests/etl/test_e11_screener_normalize.py backend/tests/etl/fixtures/screener
git commit -m "feat(etl): normalize screener items against the field-selection keep set"
```

---

### Task 3: `screener_fetch` — 52 trang tuần tự, retry có kiểm soát (spec §5.2)

**Files:**
- Create: `backend/etl/screener_fetch.py`
- Test: `backend/tests/etl/test_e12_screener_fetch.py`

**Interfaces:**
- Produces:
  ```python
  class FetchError(Exception): ...
  def fetch(post=None, sleep=time.sleep) -> tuple[list[str], int]
      # trả (text thô từng trang theo thứ tự, tổng số lần retry). post(body: dict) -> (status_code: int, text: str)
  ```
  Tiêm `post`/`sleep` chỉ để test retry không đốt thời gian thật; mặc định dùng `httpx`.

- [ ] **Bước 1: Test đỏ**

`backend/tests/etl/test_e12_screener_fetch.py`:

```python
import json

import pytest

from etl import screener_fetch as sf


def _ok(page, total=61):      # 61 mã ⇒ 3 trang (30/30/1)
    return 200, json.dumps({"page": page, "pageSize": 30, "totalCount": total,
                            "items": [{"priceInfo": {"ticker": f"T{page}{i}"}} for i in range(min(30, total - 30 * (page - 1)))],
                            "status": "Success", "errors": None})


def test_paginates_by_total_count_and_returns_raw_pages():
    calls = []
    def post(body):
        calls.append(body["page"]); return _ok(body["page"])
    pages, retries = sf.fetch(post=post, sleep=lambda s: None)
    assert calls == [1, 2, 3] and retries == 0
    assert json.loads(pages[2])["items"][0]["priceInfo"]["ticker"] == "T30"
    assert all(b == 30 for b in [30])  # pageSize cố định 30


def test_transient_failed_status_is_retried_once_not_returned_as_empty_page():
    seq = {2: [(200, json.dumps({"status": "Failed", "errors": ["Timeout performing GET (5000ms)"]}))]}
    def post(body):
        p = body["page"]
        if seq.get(p):
            return seq[p].pop(0)
        return _ok(p)
    slept = []
    pages, retries = sf.fetch(post=post, sleep=slept.append)
    assert retries == 1 and slept == [2]
    assert len(pages) == 3 and json.loads(pages[1])["status"] == "Success"


def test_four_consecutive_failures_raise_and_nothing_is_returned():
    def post(body):
        if body["page"] == 2:
            return 500, "boom"
        return _ok(body["page"])
    with pytest.raises(sf.FetchError) as ei:
        sf.fetch(post=post, sleep=lambda s: None)
    assert "trang 2" in str(ei.value)


def test_body_sends_exactly_one_criterion_and_page_size_30():
    seen = {}
    def post(body):
        seen.update(body); return _ok(body["page"], total=5)
    sf.fetch(post=post, sleep=lambda s: None)
    assert seen["pageSize"] == 30 and seen["comGroupCode"] == "ALL" and seen["icbCode"] == "ALL"
    assert len(seen["parameters"]) == 1 and seen["parameters"][0]["code"] == "ClosePrice"
```

- [ ] **Bước 2: Chạy — phải đỏ**

`uv run pytest tests/etl/test_e12_screener_fetch.py -v` → 4 lỗi `ModuleNotFoundError`.

- [ ] **Bước 3: Implementation tối thiểu**

`backend/etl/screener_fetch.py`:

```python
"""Tải 52 trang GetScreenerItems, tuần tự (spec etl screener §5.2).

I/O thuần — không parse ngoài việc đọc totalCount/status để phân trang và retry.
Trang hỏng thử lại tối đa 3 lần (2·4·8 s); hết thì raise — KHÔNG trả trang rỗng
(00-conventions §10.5: trang trắng vào kho mà không ai biết).
"""
from __future__ import annotations

import json
import math
import time

import httpx

URL = "https://wlgw-tools.fiintrade.vn/Screener/GetScreenerItems?language=vi"
FIIN_ORIGIN = "https://fiinapp.bvsc.com.vn"          # bắt buộc cho *.fiintrade.vn (00-conventions §2)
PAGE_SIZE = 30                                        # enum: chỉ nhận 30 (10-fiin-dictionary)
CRITERION = {"code": "ClosePrice", "type": "Range", "unit": "VND",
             "valueRange": [100.0, 614345.0], "selectedValue": [100.0, 614345.0]}
RETRIES = 3
BACKOFF = (2, 4, 8)


class FetchError(Exception):
    """Một trang hỏng sau mọi lần thử — lượt chạy phải thất bại, không ghi gì."""


def _body(page: int) -> dict:
    return {"comGroupCode": "ALL", "icbCode": "ALL", "page": page, "pageSize": PAGE_SIZE,
            "parameters": [CRITERION]}


def _httpx_post(body: dict) -> tuple[int, str]:
    with httpx.Client(timeout=60.0) as client:
        r = client.post(URL, json=body, headers={"Origin": FIIN_ORIGIN})
        return r.status_code, r.text


def _valid(status: int, text: str) -> bool:
    if status != 200:
        return False
    try:
        d = json.loads(text)
    except ValueError:
        return False
    return d.get("status") == "Success" and isinstance(d.get("items"), list)


def _page(post, sleep, page: int) -> tuple[str, int]:
    retries = 0
    for attempt in range(RETRIES + 1):
        status, text = post(_body(page))
        if _valid(status, text):
            return text, retries
        if attempt == RETRIES:
            break
        sleep(BACKOFF[attempt])
        retries += 1
    raise FetchError(f"trang {page} hỏng sau {RETRIES + 1} lần (HTTP {status}): {text[:200]}")


def fetch(post=None, sleep=time.sleep) -> tuple[list[str], int]:
    post = post or _httpx_post
    first, retries = _page(post, sleep, 1)
    total = int(json.loads(first)["totalCount"])
    pages = [first]
    for p in range(2, math.ceil(total / PAGE_SIZE) + 1):
        text, r = _page(post, sleep, p)
        pages.append(text)
        retries += r
    return pages, retries
```

- [ ] **Bước 4: Chạy — phải xanh**

`uv run pytest tests/etl/test_e12_screener_fetch.py -v` → **4 passed**.

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/screener_fetch.py backend/tests/etl/test_e12_screener_fetch.py
git commit -m "feat(etl): fetch screener pages sequentially with bounded retry, never an empty page"
```

---

### Task 4: `screener_guard` — ba vế từ chối (spec §5.4)

**Files:**
- Create: `backend/etl/screener_guard.py`
- Test: `backend/tests/etl/test_e13_screener_guard.py`

**Interfaces:**
- Produces:
  ```python
  DROP_RATIO = 0.02; UNMAPPED_RATIO = 0.02
  @dataclass(frozen=True)
  class GuardVerdict: ok: bool; reasons: tuple[str, ...]
  def check(total_count: int, collected: int, priced: int, unmapped: int, baseline_items: int | None) -> GuardVerdict
  ```

- [ ] **Bước 1: Test đỏ**

`backend/tests/etl/test_e13_screener_guard.py`:

```python
import json, pathlib

from etl import screener_guard as sg
from etl import screener_normalize as sn

FIX = pathlib.Path(__file__).parent / "fixtures" / "screener"


def test_preopen_real_sample_is_refused_as_non_trading_day():
    res = sn.normalize([(FIX / "page1-20260903-preopen.json").read_text(encoding="utf-8")])
    priced = sum(1 for r in res.rows if r.close_price > 0)
    v = sg.check(total_count=30, collected=30, priced=priced, unmapped=0, baseline_items=None)
    assert v.ok is False
    assert v.reasons == ("không có mã nào có closePrice > 0 — không phải ngày giao dịch",)


def test_postclose_real_sample_passes_without_baseline():
    res = sn.normalize([(FIX / "page1-20260828-postclose.json").read_text(encoding="utf-8")])
    priced = sum(1 for r in res.rows if r.close_price > 0)
    assert priced == 30
    assert sg.check(total_count=30, collected=30, priced=priced, unmapped=0, baseline_items=None).ok is True


def test_drop_against_baseline_refuses_beyond_two_percent():
    assert sg.check(1545, 1545, 1500, 0, baseline_items=1600).ok is False      # sụt 3,4%
    assert sg.check(1545, 1545, 1500, 0, baseline_items=1560).ok is True       # sụt 1,0%


def test_incomplete_pages_refused():
    v = sg.check(total_count=1545, collected=1515, priced=1500, unmapped=0, baseline_items=None)
    assert v.ok is False and "1515" in v.reasons[0] and "1545" in v.reasons[0]


def test_unmapped_ratio_refused_beyond_two_percent():
    assert sg.check(1545, 1545, 1500, unmapped=40, baseline_items=None).ok is False   # 2,6%
    assert sg.check(1545, 1545, 1500, unmapped=30, baseline_items=None).ok is True    # 1,9%
```

- [ ] **Bước 2: Chạy — phải đỏ**

`uv run pytest tests/etl/test_e13_screener_guard.py -v` → 5 lỗi import.

- [ ] **Bước 3: Implementation tối thiểu**

`backend/etl/screener_guard.py`:

```python
"""Chốt chặn cho job screener — ba vế, vế nào hỏng cũng từ chối (spec §5.4).

Module thuần: không I/O, đầu vào là số trần để test không cần database.
Vế (i) là lý do tồn tại: nguồn đóng dấu tradingDate = hôm nay ngay từ trước mở cửa
với giá 0 (đo 2026-09-03) — không có vế này, mỗi ngày lễ đẻ ~1.545 dòng ma.
"""
from dataclasses import dataclass

DROP_RATIO = 0.02
UNMAPPED_RATIO = 0.02


@dataclass(frozen=True)
class GuardVerdict:
    ok: bool
    reasons: tuple[str, ...]


def check(total_count: int, collected: int, priced: int, unmapped: int,
          baseline_items: int | None) -> GuardVerdict:
    reasons: list[str] = []
    if priced <= 0:                                                        # (i)
        reasons.append("không có mã nào có closePrice > 0 — không phải ngày giao dịch")
    if collected != total_count:                                           # (ii) đủ trang
        reasons.append(f"gom được {collected} mã, totalCount báo {total_count} — thiếu trang")
    if baseline_items is not None and total_count < baseline_items * (1 - DROP_RATIO):
        reasons.append(f"totalCount {total_count} sụt quá {DROP_RATIO:.0%} so mốc {baseline_items}")
    if collected > 0 and unmapped > collected * UNMAPPED_RATIO:            # (iii)
        reasons.append(f"{unmapped}/{collected} mã không ghép được security_id — quá {UNMAPPED_RATIO:.0%}")
    return GuardVerdict(ok=not reasons, reasons=tuple(reasons))
```

- [ ] **Bước 4: Chạy — phải xanh**

`uv run pytest tests/etl/test_e13_screener_guard.py -v` → **5 passed**.

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/screener_guard.py backend/tests/etl/test_e13_screener_guard.py
git commit -m "feat(etl): screener guard refuses non-trading days, short page sets, and unmapped tickers"
```

---

### Task 5: `screener_store` — merge · baseline · UPSERT · bằng chứng · domain_state (spec §5.5)

**Files:**
- Create: `backend/etl/screener_store.py`
- Test: `backend/tests/etl/test_e14_screener_store.py` (Postgres thật, fixture `db` — mỗi test một transaction rollback)

**Interfaces:**
- Consumes: `ScreenerRow`, `NormResult` (Task 2).
- Produces:
  ```python
  JOB = "market.screener"
  def merge(conn, rows: list[ScreenerRow]) -> tuple[list[tuple[int, ScreenerRow]], int]   # (mapped, unmapped)
  def load_baseline(engine) -> int | None                     # stats.counts.items của lượt success gần nhất
  def apply(conn, mapped: list[tuple[int, ScreenerRow]]) -> dict   # {"rows_written": n}
  def store_refusal_evidence(engine, pages: list[str], run_id: int, reasons: list[str]) -> None
  def upsert_domain_state(engine, watermark: str) -> None      # ('market.scores','fiintrade')
  ```

- [ ] **Bước 1: Test đỏ**

`backend/tests/etl/test_e14_screener_store.py`:

```python
import json, pathlib
from datetime import date

import sqlalchemy as sa

from etl import screener_normalize as sn
from etl import screener_store as st

FIX = pathlib.Path(__file__).parent / "fixtures" / "screener"
POST = (FIX / "page1-20260828-postclose.json").read_text(encoding="utf-8")


def _seed_securities(conn, rows):
    """Cắm đúng 30 mã của mẫu vào market.security — fixture refdata không có các mã UPCOM này."""
    for r in rows:
        conn.execute(sa.text(
            "INSERT INTO market.security (ticker, exchange, security_type) VALUES (:t, :e, :k)"),
            {"t": r.ticker, "e": r.exchange, "k": "etf" if r.ticker.startswith("FUE") else "stock"})


def test_merge_maps_by_ticker_and_exchange_and_counts_unmapped(db):
    rows = sn.normalize([POST]).rows
    _seed_securities(db, rows[:-1])                     # bỏ 1 mã cuối (FUEIP100) → 1 unmapped
    mapped, unmapped = st.merge(db, rows)
    assert len(mapped) == 29 and unmapped == 1
    sid_ddb = db.execute(sa.text("SELECT security_id FROM market.security WHERE ticker='DDB'")).scalar_one()
    assert (sid_ddb, next(r for r in rows if r.ticker == "DDB")) in mapped


def test_merge_ignores_delisted_rows(db):
    rows = sn.normalize([POST]).rows
    _seed_securities(db, rows)
    db.execute(sa.text("UPDATE market.security SET status='delisted' WHERE ticker='DDB'"))
    mapped, unmapped = st.merge(db, rows)
    assert unmapped == 1 and all(r.ticker != "DDB" for _, r in mapped)


def test_apply_twice_same_day_is_idempotent_and_bumps_ingested_at(db):
    rows = sn.normalize([POST]).rows
    _seed_securities(db, rows)
    mapped, _ = st.merge(db, rows)
    assert st.apply(db, mapped) == {"rows_written": 30}
    t1 = db.execute(sa.text("SELECT max(ingested_at) FROM market.screener_daily")).scalar_one()
    db.execute(sa.text("SELECT pg_sleep(0.01)"))
    assert st.apply(db, mapped) == {"rows_written": 30}
    n, t2 = db.execute(sa.text("SELECT count(*), max(ingested_at) FROM market.screener_daily")).one()
    assert n == 30 and t2 > t1
    got = db.execute(sa.text(
        "SELECT payload->'stockScreenerItem'->>'rtd7', trading_date FROM market.screener_daily sd"
        " JOIN market.security s USING (security_id) WHERE s.ticker='DDB'")).one()
    assert float(got[0]) == 12750.50715092 and got[1] == date(2026, 8, 28)


def test_baseline_reads_items_of_last_success(migrated_engine):
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job=:j"), {"j": st.JOB})
        assert st.load_baseline(migrated_engine) is None
        c.execute(sa.text("INSERT INTO ops.etl_run (job, status, finished_at, stats)"
                          " VALUES (:j,'failed',now(),cast(:s AS jsonb))"), {"j": st.JOB, "s": json.dumps({"counts": {"items": 9}})})
        c.execute(sa.text("INSERT INTO ops.etl_run (job, status, finished_at, stats)"
                          " VALUES (:j,'success',now(),cast(:s AS jsonb))"), {"j": st.JOB, "s": json.dumps({"counts": {"items": 1545}})})
    assert st.load_baseline(migrated_engine) == 1545
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job=:j"), {"j": st.JOB})


def test_refusal_evidence_and_domain_state(migrated_engine):
    with migrated_engine.begin() as c:
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='screener'"))
    st.store_refusal_evidence(migrated_engine, [POST, POST], run_id=7, reasons=["x"])
    with migrated_engine.connect() as c:
        keys = c.execute(sa.text("SELECT endpoint_key, meta->>'run_id' FROM staging.raw_payload"
                                 " WHERE source='screener' ORDER BY endpoint_key")).all()
    assert [k for k, _ in keys] == ["screener:page1", "screener:page2"] and keys[0][1] == "7"
    st.upsert_domain_state(migrated_engine, "2026-08-28")
    st.upsert_domain_state(migrated_engine, "2026-08-29")
    with migrated_engine.connect() as c:
        w = c.execute(sa.text("SELECT watermark, status FROM ops.data_domain_state"
                              " WHERE domain='market.scores' AND source='fiintrade'")).one()
    assert w == ("2026-08-29", "active")
```

- [ ] **Bước 2: Chạy — phải đỏ**

`set -a; . ../.env; set +a; uv run pytest tests/etl/test_e14_screener_store.py -v` → 5 lỗi import.

- [ ] **Bước 3: Implementation tối thiểu**

`backend/etl/screener_store.py`:

```python
"""Ghi kho cho job screener (spec etl screener §5.5).

`merge` đọc `market.security` theo (ticker, exchange) đang niêm yết — đúng unique
index sẵn có; không ghép qua organ_code → issuer vì một issuer có thể có nhiều security.
`apply` UPSERT theo PK (security_id, trading_date): chạy lại trong ngày đè bản của
chính ngày đó (step-03 §3). Bằng chứng từ chối vào staging.raw_payload ở giao dịch riêng.
"""
from __future__ import annotations

import json

import sqlalchemy as sa

from etl.screener_normalize import ScreenerRow

JOB = "market.screener"


def merge(conn, rows: list[ScreenerRow]) -> tuple[list[tuple[int, ScreenerRow]], int]:
    listed = conn.execute(sa.text(
        "SELECT ticker, exchange, security_id FROM market.security WHERE status = 'listed'")).all()
    by_key = {(t, e): sid for t, e, sid in listed}
    mapped: list[tuple[int, ScreenerRow]] = []
    unmapped = 0
    for r in rows:
        sid = by_key.get((r.ticker, r.exchange))
        if sid is None:
            unmapped += 1
        else:
            mapped.append((sid, r))
    return mapped, unmapped


def load_baseline(engine) -> int | None:
    """Mốc cho vế (ii) — counts.items của lượt success gần nhất (khuôn refdata_store)."""
    with engine.connect() as c:
        row = c.execute(sa.text(
            "SELECT stats FROM ops.etl_run WHERE job = :j AND status = 'success'"
            " ORDER BY finished_at DESC LIMIT 1"), {"j": JOB}).first()
    if row is None or not row[0]:
        return None
    return (row[0].get("counts") or {}).get("items")


def apply(conn, mapped: list[tuple[int, ScreenerRow]]) -> dict:
    stmt = sa.text(
        "INSERT INTO market.screener_daily (security_id, trading_date, payload)"
        " VALUES (:sid, :d, cast(:p AS jsonb))"
        " ON CONFLICT (security_id, trading_date) DO UPDATE"
        " SET payload = EXCLUDED.payload, ingested_at = now()")
    for sid, r in mapped:
        conn.execute(stmt, {"sid": sid, "d": r.trading_date, "p": json.dumps(r.payload)})
    return {"rows_written": len(mapped)}


def store_refusal_evidence(engine, pages: list[str], run_id: int, reasons: list[str]) -> None:
    meta = json.dumps({"run_id": run_id, "reasons": reasons})
    with engine.begin() as conn:
        for i, text in enumerate(pages, start=1):
            conn.execute(sa.text(
                "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, payload, meta)"
                " VALUES ('screener', :ek, 'json', cast(:p AS jsonb), cast(:m AS jsonb))"),
                {"ek": f"screener:page{i}", "p": text, "m": meta})


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
            " VALUES ('market.scores', 'fiintrade', 'active', now(), :w)"
            " ON CONFLICT (domain, source) DO UPDATE"
            " SET last_success_at = now(), watermark = :w, status = 'active'"), {"w": watermark})
```

- [ ] **Bước 4: Chạy — phải xanh**

`uv run pytest tests/etl/test_e14_screener_store.py -v` → **5 passed**.

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/screener_store.py backend/tests/etl/test_e14_screener_store.py
git commit -m "feat(etl): screener store - merge by (ticker, exchange), upsert by PK, refusal evidence"
```

---

### Task 6: `screener_job` + subcommand (spec §5.1) — chạy dưới role `dlck_etl`

**Files:**
- Create: `backend/etl/screener_job.py`
- Modify: `backend/etl/__main__.py` — thêm nhánh `screener` trước dòng `print(f"etl: subcommand không hợp lệ…`, và sửa chuỗi `(hỗ trợ: omo, refdata)` → `(hỗ trợ: omo, refdata, screener)`
- Test: `backend/tests/etl/test_e15_screener_job.py`

**Interfaces:**
- Consumes: `screener_fetch.fetch`, `screener_normalize.normalize`, `screener_store.*`, `screener_guard.check`, `omo_store.open_run/close_run`, `core.env.load_dotenv`.
- Produces: `screener_job.run() -> int` — `0` success · `1` guard từ chối · `2` thiếu env / lỗi khác.

- [ ] **Bước 1: Test đỏ**

`backend/tests/etl/test_e15_screener_job.py`:

```python
import os, pathlib

import sqlalchemy as sa

import etl.screener_job as job_mod
from etl import screener_normalize as sn
from etl import screener_store as st
from etl.__main__ import main as etl_main

FIX = pathlib.Path(__file__).parent / "fixtures" / "screener"
POST = (FIX / "page1-20260828-postclose.json").read_text(encoding="utf-8")
PRE = (FIX / "page1-20260903-preopen.json").read_text(encoding="utf-8")


def _patch(monkeypatch, pages):
    monkeypatch.setattr(job_mod.screener_fetch, "fetch", lambda: (pages, 0))
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])   # KHÔNG str(engine.url) — mật khẩu bị che
    monkeypatch.setattr(job_mod, "load_dotenv", lambda: None)


def _seed(engine):
    rows = sn.normalize([POST]).rows
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM market.screener_daily"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job=:j"), {"j": st.JOB})
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='screener'"))
        for r in rows:
            c.execute(sa.text("INSERT INTO market.security (ticker, exchange, security_type)"
                              " SELECT :t, :e, :k WHERE NOT EXISTS"
                              " (SELECT 1 FROM market.security WHERE ticker=:t AND exchange=:e AND status='listed')"),
                      {"t": r.ticker, "e": r.exchange, "k": "etf" if r.ticker.startswith("FUE") else "stock"})


def test_success_writes_rows_run_and_domain_state(monkeypatch, migrated_engine):
    _seed(migrated_engine); _patch(monkeypatch, [POST])
    assert job_mod.run() == 0
    with migrated_engine.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM market.screener_daily")).scalar_one() == 30
        run = c.execute(sa.text("SELECT status, stats FROM ops.etl_run WHERE job=:j ORDER BY run_id DESC LIMIT 1"),
                        {"j": st.JOB}).one()
        assert run.status == "success"
        assert run.stats["counts"] == {"items": 30, "pages": 1, "priced": 30}
        assert run.stats["rows_written"] == 30 and run.stats["unmapped"] == 0 and run.stats["trading_date"] == "2026-08-28"
        w = c.execute(sa.text("SELECT watermark FROM ops.data_domain_state WHERE domain='market.scores' AND source='fiintrade'")).scalar_one()
        assert w == "2026-08-28"
    assert st.load_baseline(migrated_engine) == 30
    assert job_mod.run() == 0                                   # idempotent lượt hai
    with migrated_engine.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM market.screener_daily")).scalar_one() == 30


def test_preopen_sample_is_refused_nothing_written_evidence_kept(monkeypatch, migrated_engine):
    _seed(migrated_engine); _patch(monkeypatch, [PRE])
    assert job_mod.run() == 1
    with migrated_engine.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM market.screener_daily")).scalar_one() == 0
        run = c.execute(sa.text("SELECT status, error FROM ops.etl_run WHERE job=:j ORDER BY run_id DESC LIMIT 1"),
                        {"j": st.JOB}).one()
        assert run.status == "failed" and "không phải ngày giao dịch" in run.error
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source='screener'")).scalar_one() == 1


def test_job_works_under_etl_role(monkeypatch, migrated_engine):
    """§3.5: mọi đường đọc/ghi của job phải chạy dưới đúng quyền production (role dlck_etl)."""
    _seed(migrated_engine); _patch(monkeypatch, [POST])
    real_create = job_mod.sa.create_engine
    def create_engine_with_role(url, **kw):
        eng = real_create(url, **kw)
        @sa.event.listens_for(eng, "connect")
        def _set_role(dbapi_conn, _rec):
            cur = dbapi_conn.cursor(); cur.execute("SET ROLE dlck_etl"); cur.close()
        return eng
    monkeypatch.setattr(job_mod.sa, "create_engine", create_engine_with_role)
    assert job_mod.run() == 0


def test_cli_dispatch_and_help_lists_screener(monkeypatch, migrated_engine, capsys):
    _seed(migrated_engine); _patch(monkeypatch, [POST])
    assert etl_main(["screener"]) == 0
    assert etl_main(["nope"]) == 2
    assert "screener" in capsys.readouterr().err
```

- [ ] **Bước 2: Chạy — phải đỏ**

`uv run pytest tests/etl/test_e15_screener_job.py -v` → 4 lỗi import.

- [ ] **Bước 3: Implementation tối thiểu**

`backend/etl/screener_job.py`:

```python
"""Một lần chạy screener: fetch → normalize → merge → guard → apply → close_run (spec §5.1).

Y khuôn `refdata_job.py`: một giao dịch cho dữ liệu; guard đánh giá TRƯỚC commit —
từ chối thì raise bên trong `with engine.begin()` để tự rollback; bằng chứng ở giao dịch riêng.
"""
from __future__ import annotations

import logging
import os
import sys

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_store, screener_fetch, screener_guard, screener_normalize, screener_store

log = logging.getLogger("etl.screener")
JOB = screener_store.JOB


class GuardRefused(Exception):
    def __init__(self, reasons):
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


def run() -> int:
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
        pages, retries = screener_fetch.fetch()
        n = screener_normalize.normalize(pages)
        priced = sum(1 for r in n.rows if r.close_price > 0)
        baseline = screener_store.load_baseline(engine)
        try:
            with engine.begin() as conn:
                mapped, unmapped = screener_store.merge(conn, n.rows)
                verdict = screener_guard.check(n.total_count, len(n.rows) + n.unknown_com_group,
                                               priced, unmapped, baseline)
                if not verdict.ok:
                    raise GuardRefused(verdict.reasons)
                apply_stats = screener_store.apply(conn, mapped)
        except GuardRefused as e:
            screener_store.store_refusal_evidence(engine, pages, run_id, e.reasons)
            omo_store.close_run(engine, run_id, "failed", error=f"guard refused: {'; '.join(e.reasons)}")
            log.error("screener từ chối: %s", e.reasons)
            return 1
        trading_date = max(r.trading_date for r in n.rows).isoformat()
        stats = {"counts": {"items": n.total_count, "pages": len(pages), "priced": priced},
                 **apply_stats, "unmapped": unmapped, "unknown_com_group": n.unknown_com_group,
                 "null_blocks": n.null_blocks, "retries": retries, "trading_date": trading_date}
        omo_store.close_run(engine, run_id, "success", stats)
        screener_store.upsert_domain_state(engine, trading_date)
        log.info("screener xong: %s", stats)
        return 0
    except Exception as e:  # noqa: BLE001 — job biên ngoài: mọi lỗi đều phải vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("screener thất bại")
        return 2
    finally:
        engine.dispose()
```

`backend/etl/__main__.py` — chèn trước dòng `print(f"etl: subcommand không hợp lệ…`:

```python
    if args[0] == "screener":
        import etl.screener_job
        return etl.screener_job.run()
```
và sửa chuỗi thành `(hỗ trợ: omo, refdata, screener)`.

- [ ] **Bước 4: Chạy — phải xanh, rồi cả bộ**

`uv run pytest tests/etl/test_e15_screener_job.py -v` → **4 passed**.
`uv run pytest tests` → **321 + 24 = 345 passed, 2 skipped** *(24 = 6+4+5+5+4; số cũ 321 không được giảm)*.

⚠️ `test_job_works_under_etl_role`: nếu đỏ vì `permission denied`, đó là **bug thật của lát** — role thiếu quyền ở một bảng — sửa bằng migration mới cấp quyền, **không** sửa test.

- [ ] **Bước 5: Commit**

```bash
git add backend/etl/screener_job.py backend/etl/__main__.py backend/tests/etl/test_e15_screener_job.py
git commit -m "feat(etl): screener job - guard before commit, evidence on refusal, 'etl screener' subcommand"
```

---

### Task 7: Chạy tay thật — AC3 · AC4 · AC5 (spec §7)

**Files:**
- Create: `docs/90-records/plans/2026-09-03-screener-daily-etl/ledger.md`

**Interfaces:** không — task nghiệm thu, dán output nguyên văn.

- [ ] **Bước 1: Điều kiện** — một ngày giao dịch, **sau 15:05**; Docker Desktop mở, `infra-postgres-1` healthy (`docker ps`). Không cần ingester chạy.

- [ ] **Bước 2: AC3 — lượt thật đầu tiên dưới credential production**

```bash
cd backend && set -a && . ../.env && set +a && PYTHONIOENCODING=utf-8 uv run python -m etl screener; echo "exit=$?"
```
Expected: exit **0**, dòng log `screener xong: {'counts': {'items': 1545, 'pages': 52, 'priced': ~1500}, 'rows_written': ~1500, 'unmapped': ≤30, …}` trong ~2–3 phút. Nếu `unmapped` > 2% ⇒ guard từ chối đúng — **dừng**, soi các ticker không ghép được (`git grep` không giúp; chạy `SELECT` bên dưới với `NOT EXISTS`) rồi mới quyết.

```bash
docker exec infra-postgres-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT count(*), min(trading_date), max(trading_date) FROM market.screener_daily" -c "SELECT status, stats FROM ops.etl_run WHERE job='market.screener' ORDER BY run_id DESC LIMIT 1"
```

- [ ] **Bước 3: AC4 — lượt hai cùng ngày** (lệnh y hệt) → `count(*)` **không đổi**, `etl_run` có 2 dòng `success`.

- [ ] **Bước 4: AC5 — ngày không giao dịch** — sáng hôm sau **trước 09:00** (hoặc ngày lễ gần nhất, bất kỳ giờ nào): chạy lệnh AC3 → expected exit **1**, log `screener từ chối: ['không có mã nào có closePrice > 0 — không phải ngày giao dịch']`, `count(*)` không đổi, và:

```bash
docker exec infra-postgres-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT count(*), max(fetched_at) FROM staging.raw_payload WHERE source='screener'"
```
→ 52 dòng bằng chứng của lượt từ chối.

- [ ] **Bước 5: Ghi ledger** — `ledger.md`: bảng AC1–AC6, mỗi dòng dán **output nguyên văn** (cắt gọn nhưng giữ số), giờ chạy, và mục *"AC5 trong ngày lễ THẬT sau 15:00"* để **mở** cho tới khi có ngày lễ đầu tiên (spec §2.2.1).

- [ ] **Bước 6: Commit** — `git add docs/90-records/plans/2026-09-03-screener-daily-etl/ledger.md && git commit -m "docs(ledger): screener slice-1 live runs AC3-AC5"`.

---

### Task 8: Task Scheduler (để `Disabled`) + đồng bộ tài liệu sống (spec §5.6, §8, AC6)

**Files:**
- Modify: `scripts/register-tasks.ps1` — sau khối `dlck-refdata` (dòng ~135–136), trước khối ingester
- Modify: `docs/20-design/market-data-store.md` §4.1 · `docs/20-design/service-topology.md` §5 · `docs/00-overview/roadmap.md` §0/§3 · `README.md` bảng dịch vụ + bước 5 · `docs/90-records/README.md` dòng plan này
- Modify: `ledger.md` (AC6)

- [ ] **Bước 1: Thêm task vào script**

Chèn sau `Assert-TaskCommand -TaskName "dlck-refdata" -MustContain "python -m etl refdata"`:

```powershell
Write-Host "Đăng ký screener (15:20 ngày làm việc — sau khi ingester ghi xong 15:05, tránh 15:30 của OMO):"
Register-DlckTask -TaskName "dlck-screener" -AtTime "15:20" -ModuleArgs "etl screener" -LogFile "screener.log"
Assert-TaskCommand -TaskName "dlck-screener" -MustContain "python -m etl screener"
```
Và sửa dòng `Write-Host "`nĐã kiểm lệnh của cả 7 task…"` → `cả 8 task`.

- [ ] **Bước 2: Chủ dự án chạy script trong cửa sổ Run as Administrator** *(shell của agent không elevated — đo 2026-09-03)*:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\twan_projects\dulieuchungkhoan.vn\scripts\register-tasks.ps1 -LogonType S4U
```
Expected: 8 dòng `+ dlck-…`, không `throw`; cuối script **cảnh báo 7 task đang tắt đã bị bật lại** — đó là hành vi đã biết.

- [ ] **Bước 3: Kiểm lệnh và principal của task mới — chứ không tin "đăng ký thành công"**

```powershell
Get-ScheduledTask dlck-screener | % { $_.Actions[0].Arguments; $_.Principal.LogonType; $_.Triggers[0].StartBoundary }
```
Expected: chuỗi chứa `python -m etl screener`, `S4U`, `…T15:20:00`.

- [ ] **Bước 4: 🔴 Tắt lại CẢ ĐỘI ngay** (roadmap [4d] — giai đoạn dev):

```powershell
Get-ScheduledTask -TaskName 'dlck-*' | Disable-ScheduledTask | Out-Null; Get-ScheduledTask -TaskName 'dlck-*' | Select TaskName, State
```
Expected: **8 task, tất cả `Disabled`**. Dán vào ledger (AC6).

- [ ] **Bước 5: Tài liệu sống — checklist §8 của spec, cùng lượt**

| File | Sửa |
|---|---|
| `market-data-store.md` §4.1 | dòng Screener: `[spec…] đã duyệt 2026-09-03` → `✅ chạy được từ 2026-09-xx (AC3 …), task dlck-screener 15:20 — Disabled cùng cả đội` |
| `service-topology.md` §5 | "Cả 7 task" → "Cả 8 task (thêm `dlck-screener` 15:20)" |
| `roadmap.md` §0 hàng code + §3 đoạn "[7] tách thành chuỗi lát" | lát 1 ✅ xong, số AC3; lát 2 (giá) là việc kế |
| `README.md` | bảng dịch vụ: thêm `etl screener`; bước 5: "8 task" |
| `backend/README.md` | danh sách job + mục "Chạy job screener" + "8 task" — **đã làm trong đợt sửa review cuối** |
| `docs/90-records/README.md` | dòng plan: ✅ xong + số |
| `10-fiin-dictionary.md` | **không sửa** — đã cập nhật 2026-09-03; chỉ sửa nếu AC5 đo ra điều mới |

Sau khi sửa: `git grep -n "7 task\|cả 7" -- README.md backend/README.md docs/00-overview docs/20-design` — mỗi hit còn lại phải đúng hoặc thuộc vùng lịch sử. *(`backend/README.md` là index sở hữu danh sách job backend; bản đầu của checklist bỏ sót nó — review cuối 2026-09-03.)*

- [ ] **Bước 6: Commit + review + merge**

```bash
git add scripts/register-tasks.ps1 README.md docs/00-overview docs/20-design docs/90-records
git commit -m "feat(ops): register dlck-screener at 15:20 (kept Disabled with the fleet); sync living docs"
```
Rồi review nhánh theo §4.1.5 (hai trục Chuẩn/Spec), `superpowers:finishing-a-development-branch`, merge `main`, xoá nhánh.

---

## Tự rà (đã làm khi viết)

- **Phủ spec:** §4 → T1 · §5.2 → T3 · §5.3 → T2 · §5.4 → T4 · §5.5 → T5 · §5.1/§5.6 → T6, T8 · §6 seam 1–13 → e11 (1–4), e12 (5–6), e13 (7–9), e14 (10), e15 (11–13) · §7 AC1 → T1 b5, AC2 → T6 b4, AC3–AC5 → T7, AC6 → T8 · §8 → T1 b6 + T8 b5. Không có mục spec thiếu task.
- **Placeholder:** không có TBD/TODO; mọi bước code có code; số kỳ vọng là literal từ mẫu thật hoặc số đếm dự kiến kèm luật "ghi số thật nếu khác".
- **Nhất quán kiểu:** `ScreenerRow(ticker, exchange, organ_code, trading_date, close_price, payload)` dùng y hệt ở T2/T5/T6; `NormResult(rows, total_count, unknown_com_group, null_blocks)`; `fetch() -> (pages, retries)`; `check(total_count, collected, priced, unmapped, baseline_items)`; `merge(conn, rows) -> (mapped, unmapped)`; `apply(conn, mapped) -> {"rows_written"}`; `load_baseline(engine) -> int | None`. Guard gọi với `collected = len(rows) + unknown_com_group` để vế (ii) đếm đúng số item nguồn trả, không lẫn với số dòng bị bỏ vì com_group lạ.
- **Một điểm cố ý để mở:** `SELECTION_JSON` trỏ vào `docs/` — container `deploy/app` không mount `docs/`. Hôm nay app container chỉ chạy heartbeat nên chưa chạm; ghi vào ledger như nợ có chủ, xử lý khi đóng gói ETL vào container.
