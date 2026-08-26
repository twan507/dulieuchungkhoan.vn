# Plan thực thi — lát cắt dọc đầu tiên: ingester + job OMO

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dựng `backend/ingester/` (socket BVSC → Redis → ClickHouse `rt`, có chế độ đo) và job `python -m etl omo` (SBV → Postgres `macro` + `staging`), kèm bộ test seam, để dừng đồng hồ mất dữ liệu nến 1' + OMO.

**Architecture:** Ingester là một tiến trình asyncio theo phiên: socket client EIO3 tự viết → chuẩn hoá tại cổng (một từ điển dùng chung Redis/ClickHouse) → dedup hash nội dung → leader mới ghi (Redis HASH/PUB + buffer ClickHouse flush 1 s). Job OMO chạy-rồi-thoát: fetch qua cổng WAF → parser phòng thủ → transaction Postgres → rebuild `omo_flow`. Chi tiết và lý do: [spec.md](spec.md) cùng thư mục.

**Tech Stack:** Python 3.12 (`uv`) · `websockets` · `redis` · `clickhouse-connect` · `httpx` · `beautifulsoup4` · SQLAlchemy/psycopg (Postgres) · pytest + container Docker thật (CH `26.3.22.7`, `redis:7-alpine`, Postgres test DB có sẵn).

**Spec:** [spec.md](spec.md) — đọc trước khi làm bất kỳ task nào. Hợp đồng writer/khởi động gốc: [spec ClickHouse §5/§8](../2026-08-25-clickhouse-realtime-store/spec.md).

## Global Constraints

- Nhánh làm việc: **`feat/ingester-omo-first-slice`** — không commit `main`. Conventional Commits, message tiếng Anh.
- Python chạy qua `uv run` từ `backend/`; env `PYTHONIOENCODING=utf-8`.
- Múi giờ: mọi thời gian nguồn parse theo `Asia/Ho_Chi_Minh` (`zoneinfo`); cấm `utcfromtimestamp`.
- Số tiền/giá đi bằng `Decimal`, **không qua float** (spec ClickHouse §9 seam ép kiểu).
- Test: nguồn ngoài (socket BVSC, HTTP SBV) mock bằng literal; ClickHouse/Redis/Postgres dùng **container/DB thật** (fixture sẵn có ở `tests/clickhouse/conftest.py`, `tests/schema/conftest.py`).
- **KHÔNG ghi thật vào ClickHouse trong giờ giao dịch trước khi gate AC3 (phiên đo) chốt** — mọi lần chạy sớm chỉ dùng `--measure`.
- Task gắn nhãn **[controller]** do phiên chính tự làm (cần mạng thật/nhìn dữ liệu rồi quyết); còn lại giao subagent **Sonnet** (cấm Fable — CLAUDE.md §4.1).
- Artifact tạm để ở scratchpad ngoài repo; cấm tạo `.superpowers/` trong repo.
- Sổ thực thi: `ledger.md` cùng thư mục, ghi theo từng task.

## Bản đồ file

```
backend/
├── core/env.py                 nạp .env gốc repo (cho job chạy từ Task Scheduler)
├── ingester/
│   ├── __init__.py  __main__.py (CLI)  config.py
│   ├── eio.py        parse/build packet EIO3 + sails.io
│   ├── normalize.py  từ điển trường nguồn → cột rt.* + ép kiểu (+ Metrics)
│   ├── dedup.py      FrameDedup (hash nội dung) + Stamper (received_at đơn điệu)
│   ├── catalog.py    hợp nhất /quotes + /datafeed/instruments → topics + state nền
│   ├── state.py      RedisSink — HASH state + PUBLISH delta
│   ├── leader.py     LeaderLock (SET NX PX + Lua renew)
│   ├── chwriter.py   buffer/block/flush/retry/poison-bisect
│   ├── measure.py    MeasureWriter — JSONL xoay giờ, gzip
│   ├── reconcile.py  đối chứng cuối phiên §5.7
│   └── main.py       orchestration (socket_loop, wiring, giờ phiên)
├── etl/
│   ├── __main__.py   subcommand: (rỗng→heartbeat) | omo
│   ├── omo_fetch.py  fetch + cổng WAF
│   ├── omo_parse.py  parser HTML SBV
│   ├── omo_store.py  ghi omo_session/omo_auction/staging + etl_run
│   ├── omo_flow.py   rebuild macro.omo_flow
│   └── omo_job.py    orchestration một lần chạy
└── tests/
    ├── etl/          conftest.py (mượn fixture schema) + test_e01..e04
    └── ingester/     conftest.py (redis container) + test_i01..i09
scripts/register-tasks.ps1      đăng ký Task Scheduler (ingester + omo×4)
```

---

### Task 1: `core/env.py` + phụ thuộc mới

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/core/env.py`
- Test: `backend/tests/core/__init__.py` (rỗng), `backend/tests/core/test_env.py`

**Interfaces:**
- Produces: `core.env.load_dotenv(path: Path | None = None) -> None` — nạp `KEY=VALUE` từ `.env` gốc repo vào `os.environ`, **không đè** biến đã có; bỏ qua dòng trống/`#`; không in giá trị.

- [ ] **Step 1: Thêm dependency** — trong `backend/pyproject.toml`, mảng `dependencies` thêm:

```toml
    "websockets>=13",
    "redis>=5",
    "httpx>=0.27",
    "beautifulsoup4>=4.12",
```

(`httpx` đang ở nhóm dev — giữ nguyên dòng dev cũng được, thêm bản chính.) Chạy: `cd backend && uv sync` — Expected: lock cập nhật, không lỗi.

- [ ] **Step 2: Test đỏ** — `backend/tests/core/test_env.py`:

```python
import os
from core.env import load_dotenv


def test_load_dotenv_reads_and_does_not_override(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("# comment\nFOO_X=abc\nBAR_Y=1\n\n", encoding="utf-8")
    monkeypatch.delenv("FOO_X", raising=False)
    monkeypatch.setenv("BAR_Y", "keep")
    load_dotenv(f)
    assert os.environ["FOO_X"] == "abc"
    assert os.environ["BAR_Y"] == "keep"


def test_load_dotenv_missing_file_is_noop(tmp_path):
    load_dotenv(tmp_path / "khong-ton-tai.env")  # không raise
```

Chạy: `cd backend && uv run pytest tests/core -v` — Expected: FAIL `No module named 'core.env'`.

- [ ] **Step 3: Cài đặt** — `backend/core/env.py`:

```python
"""Nạp .env gốc repo — cho tiến trình chạy từ Task Scheduler không kế thừa shell env.

Không đè biến đã có; không bao giờ in giá trị (CLAUDE.md §5).
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_dotenv(path: Path | None = None) -> None:
    p = path or (REPO_ROOT / ".env")
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())
```

- [ ] **Step 4: Chạy xanh** — `uv run pytest tests/core -v` → PASS.
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat(core): dotenv loader + deps for ingester/etl slice"`

---

### Task 2: CLI `etl` thành subcommand (giữ heartbeat mặc định)

**Files:**
- Modify: `backend/etl/__main__.py`
- Test: `backend/tests/etl/__init__.py` (rỗng), `backend/tests/etl/test_e01_cli.py`

**Interfaces:**
- Produces: `etl.__main__.main(argv: list[str] | None = None) -> int` — `[]` → heartbeat loop như cũ; `["omo"]` → gọi `etl.omo_job.run()` (Task 8) và trả exit code của nó.

- [ ] **Step 1: Test đỏ** — `backend/tests/etl/test_e01_cli.py`:

```python
from unittest.mock import patch

from etl.__main__ import main


def test_omo_subcommand_dispatches_to_job():
    with patch("etl.omo_job.run", return_value=0) as run:
        assert main(["omo"]) == 0
    run.assert_called_once()


def test_unknown_subcommand_exits_2():
    assert main(["gibberish"]) == 2
```

Chạy: `uv run pytest tests/etl/test_e01_cli.py -v` — Expected: FAIL (main không nhận argv / chưa có nhánh omo).

- [ ] **Step 2: Cài đặt** — `backend/etl/__main__.py` thay bằng:

```python
import sys
import time
from datetime import datetime, timezone

from etl.heartbeat import heartbeat


def _heartbeat_loop() -> int:
    while True:
        print(heartbeat(datetime.now(timezone.utc)), flush=True)
        time.sleep(15)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        return _heartbeat_loop()          # giữ tương thích compose deploy/app
    if args[0] == "omo":
        import etl.omo_job
        return etl.omo_job.run()
    print(f"etl: subcommand không hợp lệ: {args[0]!r} (hỗ trợ: omo)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

*(Test patch `etl.omo_job.run` — tạo file rỗng `backend/etl/omo_job.py` với `def run() -> int: raise NotImplementedError` để import được; Task 8 thay thật.)*

- [ ] **Step 3: Chạy xanh** → PASS. **Step 4: Commit** — `git commit -m "feat(etl): subcommand CLI, heartbeat stays default"`

---

### Task 3: `omo_fetch.py` — cổng WAF

**Files:**
- Create: `backend/etl/omo_fetch.py`
- Test: `backend/tests/etl/test_e02_fetch.py`

**Interfaces:**
- Produces: `URL`, `MARKER = "KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ"`, `MIN_BYTES = 100_000`, `class WafBlocked(RuntimeError)`, `check_gate(body: str) -> None`, `fetch(client: httpx.Client | None = None, retry_delay_s: float = 60.0) -> str`.

- [ ] **Step 1: Test đỏ** — `backend/tests/etl/test_e02_fetch.py`:

```python
import httpx
import pytest

from etl.omo_fetch import MARKER, WafBlocked, check_gate, fetch


def test_gate_rejects_waf_stub():
    with pytest.raises(WafBlocked):
        check_gate("<html><title>Request Rejected</title>Your support ID is: 1</html>")


def test_gate_rejects_big_body_without_marker():
    with pytest.raises(WafBlocked):
        check_gate("x" * 500_000)


def test_gate_accepts_real_shape():
    check_gate(("x" * 400_000) + MARKER)  # không raise


def test_fetch_retries_transport_error_once():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("boom")
        return httpx.Response(200, text=("x" * 400_000) + MARKER)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    body = fetch(client=client, retry_delay_s=0)
    assert MARKER in body and calls["n"] == 2
```

Chạy: `uv run pytest tests/etl/test_e02_fetch.py -v` — Expected: FAIL import.

- [ ] **Step 2: Cài đặt** — `backend/etl/omo_fetch.py`:

```python
"""Tải trang OMO của SBV qua cổng WAF — sbv-omo.md §3/§6.

Bẫy chính: WAF chặn bằng HTTP 200 + body 246 byte "Request Rejected".
Cổng: body ≥ MIN_BYTES VÀ chứa MARKER; hụt một trong hai → WafBlocked, không ghi gì.
"""
from __future__ import annotations

import time

import httpx

URL = "https://sbv.gov.vn/vi/nghi%E1%BB%87p-v%E1%BB%A5-th%E1%BB%8B-tr%C6%B0%E1%BB%9Dng-m%E1%BB%9F"
MARKER = "KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ"
MIN_BYTES = 100_000  # trang thật ~414 KB; <10 KB chắc chắn bị chặn — biên an toàn
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                  " (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "vi,en;q=0.9",
}


class WafBlocked(RuntimeError):
    """Nghi WAF chặn hoặc trang đổi cấu trúc — cấm ghi kho lẫn staging."""


def check_gate(body: str) -> None:
    n = len(body.encode("utf-8"))
    if n < MIN_BYTES:
        raise WafBlocked(f"body {n} byte < {MIN_BYTES} — nghi WAF chặn")
    if MARKER not in body:
        raise WafBlocked("body đủ dài nhưng thiếu chuỗi mốc — trang đổi cấu trúc?")


def fetch(client: httpx.Client | None = None, retry_delay_s: float = 60.0) -> str:
    own = client is None
    client = client or httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True)
    try:
        for attempt in (1, 2):  # một lần retry cho lỗi mạng; WAF chặn thì KHÔNG retry
            try:
                resp = client.get(URL, headers=HEADERS)
                resp.raise_for_status()
                body = resp.text
                break
            except httpx.TransportError:
                if attempt == 2:
                    raise
                time.sleep(retry_delay_s)
        check_gate(body)
        return body
    finally:
        if own:
            client.close()
```

- [ ] **Step 3: Chạy xanh** → PASS. **Step 4: Commit** — `git commit -m "feat(etl): OMO fetcher with WAF gate"`

---

### Task 4 **[controller]**: bắt fixture OMO thật + giải tay expected

Cần mạng thật + mắt người đọc bảng — phiên chính tự làm (CLAUDE.md §4.1 bảng giao việc).

- [ ] Chạy một lời gọi thật qua `etl.omo_fetch.fetch()` (1–2 lời gọi, đúng tải kế hoạch §4.3 CLAUDE.md — không dò thêm).
- [ ] Lưu **nguyên trang** vào scratchpad; cắt phần `<head>` rác, giữ tiêu đề bài + toàn bộ bảng (mục tiêu < ~80 KB) → `backend/tests/etl/fixtures/omo_page.html`. Ghi chú đầu file (comment HTML): ngày bắt, đã cắt gì. ⚠️ Cổng `check_gate` dùng ngưỡng 100 KB — test parser dùng fixture gọi thẳng `parse()`, không đi qua gate.
- [ ] Đọc bảng bằng mắt, giải tay expected (ngày, nhóm, từng dòng kỳ hạn: tv tham gia/trúng, KL tỷ đồng → VND, lãi suất) → ghi vào `backend/tests/etl/fixtures/omo_page.expected.md` để Task 5 chép vào test.
- [ ] Nếu markup lệch mô tả `sbv-omo.md §4` (class khác, cột khác) → cập nhật `sbv-omo.md` kèm ngày đo (luật §1.2) và điều chỉnh selector Task 5 theo thực tế.
- [ ] Commit: `git commit -m "test(etl): real SBV OMO page fixture with hand-solved expected"`

---

### Task 5: `omo_parse.py`

**Files:**
- Create: `backend/etl/omo_parse.py`
- Test: `backend/tests/etl/test_e03_parse.py`

**Interfaces:**
- Produces:

```python
class ParseError(ValueError): ...
@dataclass(frozen=True)
class OmoRow:
    op_type: str          # 'reverse_repo' | 'repo' | 'outright_sale'
    tenor_days: int
    participants: int | None
    winners: int | None
    volume_vnd: Decimal   # VND gốc (nguồn tỷ đồng × 1e9)
    rate_pct: Decimal | None
@dataclass(frozen=True)
class OmoResult:
    session_date: date
    rows: list[OmoRow]
    groups_present: frozenset[str]   # op_type có mặt
parse_vn_number(s: str) -> Decimal   # '6.307,47' → Decimal('6307.47')
parse(html: str) -> OmoResult
```

- [ ] **Step 1: Test đỏ** — `backend/tests/etl/test_e03_parse.py`. Expected chép từ `omo_page.expected.md` (Task 4); khung dưới dùng số phiên 14/08/2026 của [sbv-omo.md §5](../../../10-sources/macro/sbv-omo.md) làm ví dụ — **thay bằng số fixture thật**:

```python
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from etl.omo_parse import OmoRow, ParseError, parse, parse_vn_number

FIXTURE = (Path(__file__).parent / "fixtures" / "omo_page.html").read_text(encoding="utf-8")


def test_parse_vn_number():
    assert parse_vn_number("6.307,47") == Decimal("6307.47")
    assert parse_vn_number("4,5") == Decimal("4.5")
    with pytest.raises(Exception):
        parse_vn_number("abc")


def test_float_style_parse_would_be_wrong():
    # '6.307,47' đọc kiểu float() phải KHÁC kết quả đúng — bắt bẫy định dạng Việt
    assert float("6.307") != float(parse_vn_number("6.307,47"))


def test_parse_fixture_hand_solved():
    r = parse(FIXTURE)
    assert r.session_date == date(2026, 8, 26)            # ← ngày của fixture thật
    assert "reverse_repo" in r.groups_present
    row0 = r.rows[0]
    assert row0 == OmoRow("reverse_repo", 7, 4, 4, Decimal("6307.47") * 10**9, Decimal("4.5"))
    # ... assert đủ MỌI dòng của fixture, giải tay từ omo_page.expected.md


def test_parse_rejects_unknown_group():
    bad = FIXTURE.replace("Mua kỳ hạn", "Mua đứt bán đoạn", 1)
    with pytest.raises(ParseError):
        parse(bad)


def test_parse_rejects_missing_title():
    with pytest.raises(ParseError):
        parse("<html><body><p>trang khác</p></body></html>")
```

Chạy: `uv run pytest tests/etl/test_e03_parse.py -v` — Expected: FAIL import.

- [ ] **Step 2: Cài đặt** — `backend/etl/omo_parse.py` (selector điều chỉnh theo fixture thật, giữ đủ các luật phòng thủ):

```python
"""Parser bảng OMO SBV — sbv-omo.md §4/§5, luật phòng thủ Giới hạn 3.

- Ngày lấy từ TIÊU ĐỀ bài `(dd.mm.yy)` — cấm ngày hệ thống.
- Bảng dò theo tiêu đề cột, class ls01-* chỉ là gợi ý; header ≠ 4 cột → fail.
- Nhóm ngoài ba loại đã biết → fail to, không đoán (markup 'Bán kỳ hạn'/'Bán hẳn'
  chưa từng quan sát — sbv-omo.md §10).
- Đối chiếu dòng Tổng của nhóm với tổng các dòng — lệch là parse sai đâu đó.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup

GROUPS = {"Mua kỳ hạn": "reverse_repo", "Bán kỳ hạn": "repo", "Bán hẳn": "outright_sale"}
TITLE_RE = re.compile(r"KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ\s*\((\d{2})\.(\d{2})\.(\d{2})\)")
TENOR_RE = re.compile(r"(\d+)\s*ngày")
BILLION = Decimal(10) ** 9


class ParseError(ValueError): ...


@dataclass(frozen=True)
class OmoRow:
    op_type: str
    tenor_days: int
    participants: int | None
    winners: int | None
    volume_vnd: Decimal
    rate_pct: Decimal | None


@dataclass(frozen=True)
class OmoResult:
    session_date: date
    rows: list[OmoRow]
    groups_present: frozenset[str]


def parse_vn_number(s: str) -> Decimal:
    try:
        return Decimal(s.strip().replace(".", "").replace(",", "."))
    except InvalidOperation as e:
        raise ParseError(f"số Việt hỏng: {s!r}") from e


def _cells(tr) -> list[str]:
    return [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]


def parse(html: str) -> OmoResult:
    soup = BeautifulSoup(html, "html.parser")
    m = TITLE_RE.search(soup.get_text(" ", strip=True))
    if not m:
        raise ParseError("không tìm thấy tiêu đề 'KẾT QUẢ ĐẤU THẦU…(dd.mm.yy)'")
    dd, mm, yy = (int(g) for g in m.groups())
    session_date = date(2000 + yy, mm, dd)

    table = None
    for t in soup.find_all("table"):
        if "Loại hình giao dịch" in t.get_text():
            table = t
            break
    if table is None:
        raise ParseError("không tìm thấy bảng có cột 'Loại hình giao dịch'")

    rows: list[OmoRow] = []
    current: str | None = None
    group_sum: dict[str, Decimal] = {}
    group_total: dict[str, Decimal] = {}
    for tr in table.find_all("tr"):
        cells = _cells(tr)
        if not cells or not any(cells):
            continue
        text0 = cells[0]
        if "Loại hình giao dịch" in " ".join(cells):      # header
            if len(cells) != 4:
                raise ParseError(f"header {len(cells)} cột, kỳ vọng 4 — markup đổi?")
            continue
        joined = " ".join(cells)
        matched_group = next((g for g in GROUPS if g in joined and TENOR_RE.search(joined) is None), None)
        if matched_group and len([c for c in cells if c]) <= 2:
            current = GROUPS[matched_group]
            continue
        if text0.startswith("Tổng") or "ls01-total" in (tr.get("class") or []):
            if current and len(cells) >= 3 and cells[2]:
                group_total[current] = parse_vn_number(cells[2]) * BILLION
            continue
        tm = TENOR_RE.search(text0)
        if tm:
            if current is None:
                raise ParseError(f"dòng kỳ hạn trước khi có nhóm: {cells!r}")
            tenor = int(tm.group(1))
            part = win = None
            if len(cells) > 1 and "/" in cells[1]:
                p, _, w = cells[1].partition("/")
                part, win = int(p), int(w)
            vol = parse_vn_number(cells[2]) * BILLION
            rate = parse_vn_number(cells[3]) if len(cells) > 3 and cells[3] else None
            rows.append(OmoRow(current, tenor, part, win, vol, rate))
            group_sum[current] = group_sum.get(current, Decimal(0)) + vol
            continue
        # dòng nhóm không nhận diện được mà cũng không phải kỳ hạn/tổng → nghi nhóm lạ
        if len([c for c in cells if c]) <= 2 and text0 and not text0[0].isdigit():
            raise ParseError(f"nhóm không nhận diện được: {text0!r}")

    if not rows:
        raise ParseError("không parse được dòng kỳ hạn nào")
    for g, total in group_total.items():
        if g in group_sum and group_sum[g] != total:
            raise ParseError(f"tổng nhóm {g} lệch: Σdòng={group_sum[g]} vs Tổng={total}")
    return OmoResult(session_date, rows, frozenset(group_sum))
```

⚠️ Selector/điều kiện dòng chỉnh theo fixture thật của Task 4 — **các luật fail-to (nhóm lạ, header ≠ 4 cột, tổng lệch, thiếu tiêu đề) là bất biến, không được nới**.

- [ ] **Step 3: Chạy xanh** → PASS. **Step 4: Commit** — `git commit -m "feat(etl): defensive OMO table parser"`

---

### Task 6: `omo_store.py` — ghi Postgres

**Files:**
- Create: `backend/etl/omo_store.py`
- Create: `backend/tests/etl/conftest.py`
- Test: `backend/tests/etl/test_e04_store_flow.py` (phần store)

**Interfaces:**
- Consumes: `OmoResult`/`OmoRow` (Task 5).
- Produces: `store(result: OmoResult, html: str, conn) -> dict` (conn = SQLAlchemy Connection, caller giữ transaction) — trả `{"skipped": True}` nếu `session_date` đã có, ngược lại `{"sessions": 1, "auctions": n}`; `open_run(engine, job: str) -> int` / `close_run(engine, run_id: int, status: str, stats: dict | None, error: str | None)` ghi `ops.etl_run` (autocommit riêng, sống sót khi transaction chính rollback); `upsert_domain_state(engine, watermark: str)`.

- [ ] **Step 1: conftest mượn fixture schema** — `backend/tests/etl/conftest.py`:

```python
# Mượn fixture Postgres thật của bộ test schema (cần TEST_DATABASE_URL như README database)
from tests.schema.conftest import db, migrated_engine  # noqa: F401
```

- [ ] **Step 2: Test đỏ** — thêm vào `backend/tests/etl/test_e04_store_flow.py`:

```python
import json
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from etl.omo_parse import OmoResult, OmoRow
from etl.omo_store import store

R1 = OmoResult(
    session_date=date(2026, 8, 14),
    rows=[
        OmoRow("reverse_repo", 7, 4, 4, Decimal("6307.47") * 10**9, Decimal("4.5")),
        OmoRow("reverse_repo", 35, 4, 4, Decimal("3466.54") * 10**9, Decimal("4.5")),
    ],
    groups_present=frozenset({"reverse_repo"}),
)


def test_store_writes_session_auction_staging(db):
    stats = store(R1, "<html>raw</html>", db)
    assert stats == {"sessions": 1, "auctions": 2}
    s = db.execute(sa.text(
        "SELECT has_reverse_repo, has_repo, has_outright_sale FROM macro.omo_session"
        " WHERE session_date = '2026-08-14'")).one()
    assert tuple(s) == (True, False, False)
    vol = db.execute(sa.text(
        "SELECT volume_vnd FROM macro.omo_auction WHERE session_date='2026-08-14'"
        " AND op_type='reverse_repo' AND tenor_days=7")).scalar_one()
    assert vol == Decimal("6307470000000")
    raw = db.execute(sa.text(
        "SELECT content_type, body, meta FROM staging.raw_payload"
        " WHERE source='sbv' AND endpoint_key='omo'")).one()
    assert raw.content_type == "html" and raw.body == "<html>raw</html>"
    assert raw.meta["bytes"] == len("<html>raw</html>".encode())


def test_store_skips_duplicate_date(db):
    store(R1, "x" , db)
    assert store(R1, "x", db) == {"skipped": True}
    n = db.execute(sa.text("SELECT count(*) FROM macro.omo_auction")).scalar_one()
    assert n == 2
```

Chạy: `uv run pytest tests/etl/test_e04_store_flow.py -v` — Expected: FAIL import.

- [ ] **Step 3: Cài đặt** — `backend/etl/omo_store.py`:

```python
"""Ghi kết quả OMO — append-only, ngày trùng bỏ qua (sbv-omo.md §9.2, step-04 §3)."""
from __future__ import annotations

import hashlib
import json

import sqlalchemy as sa

from etl.omo_parse import OmoResult


def store(result: OmoResult, html: str, conn) -> dict:
    exists = conn.execute(
        sa.text("SELECT 1 FROM macro.omo_session WHERE session_date = :d"),
        {"d": result.session_date},
    ).first()
    if exists:
        return {"skipped": True}
    conn.execute(
        sa.text(
            "INSERT INTO macro.omo_session"
            " (session_date, crawled_at, has_reverse_repo, has_repo, has_outright_sale)"
            " VALUES (:d, now(), :r, :p, :o)"
        ),
        {"d": result.session_date,
         "r": "reverse_repo" in result.groups_present,
         "p": "repo" in result.groups_present,
         "o": "outright_sale" in result.groups_present},
    )
    for row in result.rows:
        conn.execute(
            sa.text(
                "INSERT INTO macro.omo_auction (session_date, op_type, tenor_days,"
                " participants, winners, volume_vnd, rate_pct)"
                " VALUES (:d, :op, :t, :p, :w, :v, :r)"
            ),
            {"d": result.session_date, "op": row.op_type, "t": row.tenor_days,
             "p": row.participants, "w": row.winners,
             "v": row.volume_vnd, "r": row.rate_pct},
        )
    body_bytes = html.encode("utf-8")
    conn.execute(
        sa.text(
            "INSERT INTO staging.raw_payload (source, endpoint_key, content_type, body, meta)"
            " VALUES ('sbv', 'omo', 'html', :b, cast(:m AS jsonb))"
        ),
        {"b": html, "m": json.dumps({"bytes": len(body_bytes),
                                     "hash": hashlib.sha256(body_bytes).hexdigest()})},
    )
    return {"sessions": 1, "auctions": len(result.rows)}


def open_run(engine, job: str) -> int:
    with engine.connect() as c:
        rid = c.execute(
            sa.text("INSERT INTO ops.etl_run (job) VALUES (:j) RETURNING run_id"), {"j": job}
        ).scalar_one()
        c.commit()
        return rid


def close_run(engine, run_id: int, status: str, stats: dict | None = None,
              error: str | None = None) -> None:
    with engine.connect() as c:
        c.execute(
            sa.text("UPDATE ops.etl_run SET finished_at = now(), status = :s,"
                    " stats = cast(:st AS jsonb), error = :e WHERE run_id = :r"),
            {"s": status, "st": json.dumps(stats) if stats is not None else None,
             "e": error, "r": run_id},
        )
        c.commit()


def upsert_domain_state(engine, watermark: str) -> None:
    with engine.connect() as c:
        c.execute(
            sa.text(
                "INSERT INTO ops.data_domain_state (domain, source, status, last_success_at, watermark)"
                " VALUES ('macro.omo', 'sbv', 'active', now(), :w)"
                " ON CONFLICT (domain, source) DO UPDATE"
                " SET last_success_at = now(), watermark = :w, status = 'active'"
            ),
            {"w": watermark},
        )
        c.commit()
```

- [ ] **Step 4: Chạy xanh** (cần Postgres dev + `TEST_DATABASE_URL` như [database/README.md](../../../../database/README.md)) → PASS. **Step 5: Commit** — `git commit -m "feat(etl): OMO postgres writer + etl_run bookkeeping"`

---

### Task 7: `omo_flow.py` — rebuild toàn phần

**Files:**
- Create: `backend/etl/omo_flow.py`
- Test: thêm vào `backend/tests/etl/test_e04_store_flow.py`

**Interfaces:**
- Consumes: dữ liệu `macro.omo_auction` (Task 6 ghi).
- Produces: `rebuild(conn) -> int` (số dòng flow). Quy ước dấu (chốt tại plan này, theo step-04 để ngỏ): `injection_vnd`/`maturing_vnd` **có dấu theo chiều bơm** — `reverse_repo` = `+volume`, `repo`/`outright_sale` = `−volume`; `net = injection − maturing`; `outstanding = Σ net` theo ngày. Kiểm chiều: outright_sale phát hành ⇒ net âm (hút) ✓, đáo hạn ⇒ net dương (bơm trả lại) ✓.

- [ ] **Step 1: Test đỏ** (giải tay step-04 §5.4, đơn vị VND gốc):

```python
from etl.omo_flow import rebuild


def _seed(db, d, tenor, vol_billion, op="reverse_repo"):
    db.execute(sa.text(
        "INSERT INTO macro.omo_session (session_date, crawled_at, has_reverse_repo,"
        " has_repo, has_outright_sale) VALUES (:d, now(), true, false, false)"
        " ON CONFLICT DO NOTHING"), {"d": d})
    db.execute(sa.text(
        "INSERT INTO macro.omo_auction (session_date, op_type, tenor_days, volume_vnd)"
        " VALUES (:d, :op, :t, :v)"),
        {"d": d, "op": op, "t": tenor, "v": Decimal(str(vol_billion)) * 10**9})


def test_flow_hand_solved(db):
    _seed(db, date(2026, 8, 14), 7, "6307.47")
    _seed(db, date(2026, 8, 21), 7, "5000")
    rebuild(db)
    r = db.execute(sa.text(
        "SELECT injection_vnd, maturing_vnd, net_vnd, complete FROM macro.omo_flow"
        " WHERE flow_date = '2026-08-21'")).one()
    assert r.injection_vnd == Decimal("5000") * 10**9
    assert r.maturing_vnd == Decimal("6307.47") * 10**9
    assert r.net_vnd == Decimal("-1307.47") * 10**9
    assert r.complete is False        # price_daily rỗng → không đánh giá được cửa sổ


def test_flow_outright_sale_reversed_sign(db):
    _seed(db, date(2026, 8, 14), 7, "1000", op="outright_sale")
    rebuild(db)
    r = db.execute(sa.text(
        "SELECT injection_vnd, net_vnd FROM macro.omo_flow WHERE flow_date='2026-08-14'")).one()
    assert r.injection_vnd == Decimal("-1000") * 10**9    # phát hành tín phiếu = hút
    m = db.execute(sa.text(
        "SELECT net_vnd FROM macro.omo_flow WHERE flow_date='2026-08-21'")).one()
    assert m.net_vnd == Decimal("1000") * 10**9           # đáo hạn tín phiếu = bơm trả lại


def test_flow_rebuild_idempotent(db):
    _seed(db, date(2026, 8, 14), 7, "6307.47")
    rebuild(db)
    first = db.execute(sa.text("SELECT * FROM macro.omo_flow ORDER BY flow_date")).all()
    rebuild(db)
    assert db.execute(sa.text("SELECT * FROM macro.omo_flow ORDER BY flow_date")).all() == first
```

Chạy — Expected: FAIL import.

- [ ] **Step 2: Cài đặt** — `backend/etl/omo_flow.py`:

```python
"""Rebuild macro.omo_flow — tầng tự tính, xoá-dựng-lại toàn phần idempotent (step-04 §3).

complete(D) cần CẢ BA: (1) đủ ≥140 ngày lịch sử; (2) lịch ngày làm việc từ
market.price_daily PHỦ cửa sổ [D−140, D] (rỗng/không phủ ⇒ false — cấm vacuous-true);
(3) mọi ngày làm việc trong cửa sổ đều có dòng omo_session. Chiều dấu repo/outright_sale
CHƯA KIỂM trên phiên thật — gặp phiên đầu có nhóm đó phải đối chiếu tay (spec §4.4).
"""
from __future__ import annotations

import sqlalchemy as sa

_REBUILD = """
TRUNCATE macro.omo_flow;
WITH signed AS (
  SELECT session_date, tenor_days,
         CASE WHEN op_type = 'reverse_repo' THEN volume_vnd ELSE -volume_vnd END AS sv
  FROM macro.omo_auction
),
inj AS (SELECT session_date AS d, sum(sv) AS v FROM signed GROUP BY 1),
mat AS (SELECT (session_date + tenor_days) AS d, sum(sv) AS v FROM signed GROUP BY 1),
days AS (SELECT d FROM inj UNION SELECT d FROM mat)
INSERT INTO macro.omo_flow (flow_date, injection_vnd, maturing_vnd, net_vnd, outstanding_vnd, complete)
SELECT days.d,
       coalesce(inj.v, 0),
       coalesce(mat.v, 0),
       coalesce(inj.v, 0) - coalesce(mat.v, 0),
       sum(coalesce(inj.v, 0) - coalesce(mat.v, 0)) OVER (ORDER BY days.d),
       false
FROM days LEFT JOIN inj ON inj.d = days.d LEFT JOIN mat ON mat.d = days.d;

UPDATE macro.omo_flow f SET complete = true
WHERE (SELECT min(session_date) FROM macro.omo_session) <= f.flow_date - 140
  AND EXISTS (SELECT 1 FROM market.price_daily p WHERE p.trading_date <= f.flow_date - 140)
  AND EXISTS (SELECT 1 FROM market.price_daily p WHERE p.trading_date >= f.flow_date)
  AND NOT EXISTS (
    SELECT 1
    FROM (SELECT DISTINCT trading_date AS wd FROM market.price_daily
          WHERE trading_date BETWEEN f.flow_date - 140 AND f.flow_date) w
    LEFT JOIN macro.omo_session s ON s.session_date = w.wd
    WHERE s.session_date IS NULL
  );
"""


def rebuild(conn) -> int:
    for stmt in _REBUILD.split(";"):
        if stmt.strip():
            conn.execute(sa.text(stmt))
    return conn.execute(sa.text("SELECT count(*) FROM macro.omo_flow")).scalar_one()
```

⚠️ Kiểm tên cột `market.price_daily.trading_date` bằng `\d market.price_daily` (hoặc đọc migration `0004`) trước khi chạy — nếu tên khác, sửa SQL **và** ghi chú ledger.

- [ ] **Step 3: Chạy xanh** → PASS. **Step 4: Commit** — `git commit -m "feat(etl): omo_flow full rebuild with signed injection semantics"`

---

### Task 8: `omo_job.py` — orchestration một lần chạy

**Files:**
- Modify: `backend/etl/omo_job.py` (thay stub Task 2)
- Test: `backend/tests/etl/test_e05_job.py`

**Interfaces:**
- Consumes: Task 3/5/6/7. Produces: `run() -> int` — 0 = thành công (kể cả skip), ≠0 = lỗi; đọc env `ETL_DATABASE_URL` (qua `core.env.load_dotenv()`).

- [ ] **Step 1: Test đỏ** — `backend/tests/etl/test_e05_job.py` (mock fetch, DB thật qua engine test):

```python
from pathlib import Path
from unittest.mock import patch

import sqlalchemy as sa

from etl import omo_job

FIXTURE = (Path(__file__).parent / "fixtures" / "omo_page.html").read_text(encoding="utf-8")


def test_run_happy_path(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", str(migrated_engine.url.render_as_string(hide_password=False)))
    with patch("etl.omo_job.omo_fetch.fetch", return_value=FIXTURE):
        assert omo_job.run() == 0
    with migrated_engine.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM macro.omo_session")).scalar_one() == 1
        run_row = c.execute(sa.text(
            "SELECT status FROM ops.etl_run WHERE job='macro.omo_crawl'"
            " ORDER BY run_id DESC LIMIT 1")).scalar_one()
        assert run_row == "success"
        c.execute(sa.text("TRUNCATE macro.omo_flow, macro.omo_auction, macro.omo_session,"
                          " staging.raw_payload, ops.etl_run, ops.data_domain_state"))
        c.commit()


def test_run_waf_blocked_records_failed(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", str(migrated_engine.url.render_as_string(hide_password=False)))
    from etl.omo_fetch import WafBlocked
    with patch("etl.omo_job.omo_fetch.fetch", side_effect=WafBlocked("nghi chặn")):
        assert omo_job.run() != 0
    with migrated_engine.connect() as c:
        assert c.execute(sa.text(
            "SELECT status FROM ops.etl_run ORDER BY run_id DESC LIMIT 1")).scalar_one() == "failed"
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload")).scalar_one() == 0
        c.execute(sa.text("TRUNCATE ops.etl_run")); c.commit()
```

Chạy — Expected: FAIL (`run` là stub `NotImplementedError`).

- [ ] **Step 2: Cài đặt** — `backend/etl/omo_job.py`:

```python
"""Một lần chạy crawl OMO: fetch → parse → store → flow. Chạy-rồi-thoát (Task Scheduler)."""
from __future__ import annotations

import logging
import os
import sys

import sqlalchemy as sa

from core.env import load_dotenv
from etl import omo_fetch, omo_flow, omo_parse, omo_store

log = logging.getLogger("etl.omo")
JOB = "macro.omo_crawl"


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
        html = omo_fetch.fetch()
        result = omo_parse.parse(html)
        with engine.begin() as conn:
            stats = omo_store.store(result, html, conn)
            if not stats.get("skipped"):
                stats["flow_rows"] = omo_flow.rebuild(conn)
        omo_store.close_run(engine, run_id, "success", stats)
        omo_store.upsert_domain_state(engine, watermark=result.session_date.isoformat())
        log.info("omo xong: %s", stats)
        return 0
    except Exception as e:  # noqa: BLE001 — job biên ngoài: mọi lỗi đều phải vào etl_run
        omo_store.close_run(engine, run_id, "failed", error=f"{type(e).__name__}: {e}")
        log.exception("omo thất bại")
        return 1
    finally:
        engine.dispose()
```

- [ ] **Step 3: Chạy xanh** → PASS toàn bộ `tests/etl`. **Step 4: Commit** — `git commit -m "feat(etl): omo job orchestration run-and-exit"`

---

### Task 9: gói `ingester` + `config.py` + `eio.py`

**Files:**
- Create: `backend/ingester/__init__.py` (rỗng), `backend/ingester/config.py`, `backend/ingester/eio.py`
- Test: `backend/tests/ingester/__init__.py` (rỗng), `backend/tests/ingester/test_i01_eio.py`, `backend/tests/ingester/test_i02_config.py`

**Interfaces:**
- Produces `eio`: `WSS_URL` (URL đầy đủ §3.1 spec); dataclass `Open(ping_interval_ms, ping_timeout_ms)`, `Event(name: str, payload: dict)`, `Ack(ack_id: int, body: list)`, `Control(kind: str)`; `parse_packet(raw: str) -> Open | Event | Ack | Control | None`; `build_subscribe(ack_id: int, args: list[str], op: str = "subscribe") -> str`; `chunk(seq, n=100)`; `PING = "2"`.
- Produces `config`: `@dataclass Config(clickhouse_url, redis_url, log_dir: Path, measure_dir: Path)`; `load(need_db: bool) -> Config` — gọi `core.env.load_dotenv()`, `need_db=True` đòi `CLICKHOUSE_INGESTER_URL` + `REDIS_URL` (thiếu → `SystemExit(2)` message rõ, không in giá trị); `INGESTER_LOG_DIR`/`INGESTER_MEASURE_DIR` default `<repo>/../dlck-runtime/{logs,measure}` (ngoài repo).

- [ ] **Step 1: Test đỏ** — `backend/tests/ingester/test_i01_eio.py` (literal từ [11-bvsc-realtime](../../../10-sources/market/11-bvsc-realtime.md)):

```python
import json

from ingester.eio import Ack, Control, Event, Open, build_subscribe, chunk, parse_packet


def test_parse_open():
    p = parse_packet('0{"sid":"abc","upgrades":[],"pingInterval":25000,"pingTimeout":60000}')
    assert p == Open(25000, 60000)


def test_parse_controls():
    assert parse_packet("40") == Control("40")
    assert parse_packet("3") == Control("3")


def test_parse_event_t():
    raw = '42["t",{"TD":"10/08/2026","FT":"13:08:56","SB":"ACV","FV":"100","LC":"S","FMP":"42100.0","FCV":"1000.0","SM":"74027","AVO":"590000","AVA":"24983210000.0"}]'
    p = parse_packet(raw)
    assert isinstance(p, Event) and p.name == "t" and p.payload["SB"] == "ACV"


def test_parse_ack():
    p = parse_packet('431[{"body":{"result":[]},"statusCode":200}]')
    assert isinstance(p, Ack) and p.ack_id == 1


def test_parse_garbage_returns_none():
    assert parse_packet("42tào lao") is None
    assert parse_packet("9xyz") is None


def test_build_subscribe_matches_sails_envelope():
    s = build_subscribe(1, ["i:BID", "o10:BID"])
    assert s.startswith("421[")
    body = json.loads(s[3:])
    assert body[0] == "get"
    assert body[1]["url"] == "/client/subscribe"
    assert body[1]["data"] == {"op": "subscribe", "args": ["i:BID", "o10:BID"]}


def test_chunk():
    assert list(chunk(list(range(5)), 2)) == [[0, 1], [2, 3], [4]]
```

Chạy — Expected: FAIL import.

- [ ] **Step 2: Cài đặt `eio.py`**:

```python
"""Packet Engine.IO v3 + envelope sails.io — 11-bvsc-realtime.md §1.

Ack statusCode:200 KHÔNG chứng minh topic hợp lệ (§1.4) — caller không dùng ack
làm bằng chứng; bằng chứng duy nhất là frame dữ liệu về.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

WSS_URL = ("wss://wss.bvsc.com.vn/market/socket.io/?EIO=3&transport=websocket"
           "&__sails_io_sdk_version=1.2.1&__sails_io_sdk_platform=browser"
           "&__sails_io_sdk_language=javascript")
PING = "2"


@dataclass(frozen=True)
class Open:
    ping_interval_ms: int
    ping_timeout_ms: int


@dataclass(frozen=True)
class Event:
    name: str
    payload: dict


@dataclass(frozen=True)
class Ack:
    ack_id: int
    body: list


@dataclass(frozen=True)
class Control:
    kind: str


def _split_id(rest: str) -> tuple[int | None, str]:
    i = 0
    while i < len(rest) and rest[i].isdigit():
        i += 1
    return (int(rest[:i]) if i else None, rest[i:])


def parse_packet(raw: str):
    try:
        if raw.startswith("0"):
            d = json.loads(raw[1:])
            return Open(int(d["pingInterval"]), int(d["pingTimeout"]))
        if raw in ("1", "2", "3", "6", "40", "41"):
            return Control(raw)
        if raw.startswith("42"):
            _, rest = _split_id(raw[2:])
            arr = json.loads(rest)
            if isinstance(arr, list) and arr and isinstance(arr[0], str):
                payload = arr[1] if len(arr) > 1 and isinstance(arr[1], dict) else {}
                return Event(arr[0], payload)
            return None
        if raw.startswith("43"):
            ack_id, rest = _split_id(raw[2:])
            return Ack(ack_id or 0, json.loads(rest))
    except (ValueError, KeyError, TypeError):
        return None
    return None


def build_subscribe(ack_id: int, args: list[str], op: str = "subscribe") -> str:
    body = ["get", {"url": "/client/subscribe", "method": "get", "headers": {},
                    "data": {"op": op, "args": args}}]
    return f"42{ack_id}" + json.dumps(body, separators=(",", ":"))


def chunk(seq, n: int = 100):
    for i in range(0, len(seq), n):
        yield list(seq[i:i + n])
```

- [ ] **Step 3: Test đỏ config** — `backend/tests/ingester/test_i02_config.py`:

```python
import pytest

from ingester.config import load


def test_load_measure_mode_needs_no_db(monkeypatch):
    monkeypatch.delenv("CLICKHOUSE_INGESTER_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    cfg = load(need_db=False)
    assert cfg.measure_dir.name == "measure"


def test_load_run_mode_requires_db(monkeypatch):
    monkeypatch.delenv("CLICKHOUSE_INGESTER_URL", raising=False)
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    with pytest.raises(SystemExit):
        load(need_db=True)
```

- [ ] **Step 4: Cài đặt `config.py`**:

```python
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from core.env import REPO_ROOT, load_dotenv


@dataclass(frozen=True)
class Config:
    clickhouse_url: str
    redis_url: str
    log_dir: Path
    measure_dir: Path


def load(need_db: bool) -> Config:
    load_dotenv()
    ch = os.environ.get("CLICKHOUSE_INGESTER_URL", "")
    rd = os.environ.get("REDIS_URL", "")
    if need_db:
        missing = [k for k, v in (("CLICKHOUSE_INGESTER_URL", ch), ("REDIS_URL", rd)) if not v]
        if missing:
            print(f"ingester: thiếu env bắt buộc: {', '.join(missing)}", file=sys.stderr)
            raise SystemExit(2)
    runtime = REPO_ROOT.parent / "dlck-runtime"
    log_dir = Path(os.environ.get("INGESTER_LOG_DIR") or runtime / "logs")
    measure_dir = Path(os.environ.get("INGESTER_MEASURE_DIR") or runtime / "measure")
    log_dir.mkdir(parents=True, exist_ok=True)
    measure_dir.mkdir(parents=True, exist_ok=True)
    return Config(ch, rd, log_dir, measure_dir)
```

- [ ] **Step 5: Chạy xanh cả hai file test** → PASS. **Step 6: Commit** — `git commit -m "feat(ingester): package scaffold, EIO3 codec, config"`

---

### Task 10: `normalize.py` — từ điển + ép kiểu

**Files:**
- Create: `backend/ingester/normalize.py`
- Test: `backend/tests/ingester/test_i03_normalize.py`

**Interfaces:**
- Produces: `TZ`; `class NormalizeError(ValueError)`; `class Metrics` (`inc(key, n=1)`, `counters: dict`); `@dataclass Normalized(table: str, row: dict, delta: dict, symbol: str)`; `normalize(event: str, payload: dict, received_at_ms: int, metrics: Metrics) -> Normalized` (raise `NormalizeError` cho frame hỏng tất định); `symbol_of(event: str, payload: dict) -> str | None`; `COLUMNS: dict[str, list[str]]` — thứ tự cột INSERT từng bảng, **chép đúng DDL** [spec ClickHouse §3](../2026-08-25-clickhouse-realtime-store/spec.md).

`COLUMNS` (chép nguyên văn vào code):

```python
COLUMNS = {
    "trade": ["symbol", "ts", "seq", "price", "volume", "side", "change",
              "cum_volume", "cum_value", "received_at"],
    "quote": ["symbol", "ts", "top", "action", "bid_price", "bid_qty", "ask_price",
              "ask_qty", "cum_bid", "cum_ask", "received_at"],
    "snapshot_delta": ["symbol", "exchange", "ts",
                       "b1", "b2", "b3", "v1", "v2", "v3", "s1", "s2", "s3",
                       "u1", "u2", "u3", "total_bid", "total_offer",
                       "close_price", "change", "change_pct", "avg_price", "high",
                       "last_vol", "last_vol2", "last_price", "total_vol", "total_value",
                       "foreign_buy", "foreign_sell", "foreign_remain",
                       "pt_price", "pt_qty", "pt_total_qty", "pt_total_val",
                       "extra", "received_at"],
    "index_delta": ["symbol", "ts", "index_value", "change", "change_pct",
                    "total_vol", "total_value", "advances", "declines", "unchanged",
                    "ceiling_cnt", "adv_vol", "dec_vol", "unch_vol",
                    "pt_total", "pt_value", "extra", "received_at"],
    "pt_match": ["symbol", "market", "ts", "price", "volume", "ref_price",
                 "ceil_price", "floor_price", "order_id", "extra", "received_at"],
}
```

Ánh xạ trường (chép vào code, nguồn: [11-bvsc-realtime](../../../10-sources/market/11-bvsc-realtime.md) §4–§8 × DDL spec CH §3):

- `t` → `trade`: `SB→symbol · TD+FT→ts (giây, TZ VN) · SM→seq · FMP→price · FV→volume · LC→side · FCV→change · AVO→cum_volume · AVA→cum_value`. Khoá lạ: đếm `unknown_key.t.<K>`, không lưu.
- `o` → `quote`: `SB→symbol · t→ts(ms) · TOP→top · ACT→action · BP/BQ/SP/SQ→bid_price/bid_qty/ask_price/ask_qty · CBV/CSV→cum_bid/cum_ask`; `id` bỏ (trùng thông tin). Khoá lạ: đếm, không lưu.
- `i` → `snapshot_delta`: `SB/EX/t` + `B1..3→b1..3 · V1..3→v1..3 · S1..3→s1..3 · U1..3→u1..3 · TB→total_bid · TO→total_offer · CP→close_price · CH→change · CHP→change_pct · AP→avg_price · HI→high · CV→last_vol · P1→last_vol2 · P2→last_price · TT→total_vol · TV→total_value · FB→foreign_buy · FS→foreign_sell · FR→foreign_remain · PMP→pt_price · PMQ→pt_qty · PTQ→pt_total_qty · PTV→pt_total_val`; trường ngoài danh sách → `extra` JSON. Cả hai `CV`/`P1` cùng có mà lệch → `metrics.inc("cv_ne_p1")`.
- `idx` → `index_delta`: `MC→symbol · t→ts(ms) · MI→index_value · ICH→change · IPC→change_pct · TV→total_vol · TVA→total_value · ADV→advances · DE→declines · NC→unchanged · NOC→ceiling_cnt · AV→adv_vol · DV→dec_vol · NCV→unch_vol · PTT→pt_total · PTV→pt_value`; `IT`/`TD` **bỏ có chủ đích** (spec CH §3.4 — không vào extra); còn lại lạ → `extra`.
- `ptm` → `pt_match`: `SB→symbol · MC→market · LS→ts (epoch GIÂY) · PR→price · MVL→volume · RE/CE/FL→ref_price/ceil_price/floor_price · CNO→order_id`; `MKI`/`IAC` → `extra` (có chủ đích); `TD`/`TI` bỏ; còn lại lạ → `extra`.

`delta` (cho Redis): các cột frame vừa mang (không `extra`/`received_at`), giá trị chuỗi; thêm `ts` = epoch ms dạng chuỗi.

- [ ] **Step 1: Test đỏ** — `backend/tests/ingester/test_i03_normalize.py` (literal từ tài liệu nguồn; expected giải tay):

```python
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from ingester.normalize import Metrics, NormalizeError, TZ, normalize, symbol_of

RECV = 1786342136000  # 2026-08-10 13:08:56.000 +07 (epoch ms bất kỳ trong phiên)

T_FRAME = {"TD": "10/08/2026", "FT": "13:08:56", "SB": "ACV", "FV": "100", "LC": "S",
           "FMP": "42100.0", "FCV": "1000.0", "SM": "74027",
           "AVO": "590000", "AVA": "24983210000.0"}


def test_normalize_t_hand_solved():
    m = Metrics()
    n = normalize("t", T_FRAME, RECV, m)
    assert n.table == "trade" and n.symbol == "ACV"
    assert n.row["ts"] == datetime(2026, 8, 10, 13, 8, 56, tzinfo=TZ)
    assert n.row["price"] == Decimal("42100.00")
    assert n.row["volume"] == 100 and n.row["seq"] == 74027
    assert n.row["cum_value"] == Decimal("24983210000.00")
    assert n.row["received_at"].timestamp() * 1000 == RECV


def test_normalize_t_unknown_key_counted_not_stored():
    m = Metrics()
    n = normalize("t", {**T_FRAME, "ZZ": "1"}, RECV, m)
    assert "ZZ" not in n.row and m.counters.get("unknown_key.t.ZZ") == 1


def test_normalize_excess_decimals_rounded_with_metric():
    m = Metrics()
    n = normalize("t", {**T_FRAME, "FMP": "100.005"}, RECV, m)
    assert n.row["price"] == Decimal("100.00")           # half-even về scale 2
    assert m.counters.get("decimal_normalized") == 1


def test_normalize_t_bad_volume_raises():
    with pytest.raises(NormalizeError):
        normalize("t", {**T_FRAME, "FV": "abc"}, RECV, Metrics())


def test_normalize_i_extra_and_cv_p1():
    m = Metrics()
    p = {"EX": "HOSE", "t": 1786330492737, "U2": "43500", "SB": "BID",
         "CV": "1100", "P1": "1100", "LAZ": {"x": 1}}
    n = normalize("i", p, RECV, m)
    assert n.table == "snapshot_delta"
    assert n.row["u2"] == 43500 and n.row["b1"] is None
    assert '"LAZ"' in n.row["extra"] and m.counters.get("cv_ne_p1") is None
    n2 = normalize("i", {**p, "P1": "9"}, RECV, m)
    assert m.counters.get("cv_ne_p1") == 1
    assert n2.row["extra"] != ""


def test_normalize_i_no_extra_is_empty_string():
    n = normalize("i", {"EX": "HOSE", "t": 1786330492737, "SB": "BID"}, RECV, Metrics())
    assert n.row["extra"] == ""


def test_normalize_idx_ms_epoch_tz():
    p = {"MC": "X50", "MI": "3230.86", "t": 1786342140044, "IT": "13:09:00", "TD": "10/08/2026"}
    n = normalize("idx", p, RECV, Metrics())
    ts = n.row["ts"]
    assert ts.tzinfo is not None and ts.astimezone(TZ).hour == 13 and ts.minute == 9
    assert n.row["index_value"] == Decimal("3230.86")
    assert n.row["extra"] == ""      # IT/TD bỏ có chủ đích, không phải trường lạ


def test_normalize_ptm_epoch_seconds_and_extra():
    p = {"SB": "DBC", "MC": "HOSE", "TD": "10/08/2026", "TI": "13:09:17", "PR": "16650.0",
         "MVL": 590000, "RE": 16650, "CE": 17800, "FL": 15500,
         "CNO": "VN000000DBC2-mdds:0:682530462/GSTO000009:1211905",
         "LS": 1786342157, "MKI": "10", "IAC": True}
    n = normalize("ptm", p, RECV, Metrics())
    assert n.row["ts"] == datetime.fromtimestamp(1786342157, tz=TZ)
    assert n.row["volume"] == 590000
    assert '"MKI"' in n.row["extra"] and '"IAC"' in n.row["extra"]


def test_symbol_of():
    assert symbol_of("t", T_FRAME) == "ACV"
    assert symbol_of("idx", {"MC": "HOSE"}) == "HOSE"
    assert symbol_of("t", {}) is None
```

Chạy — Expected: FAIL import.

- [ ] **Step 2: Cài đặt `normalize.py`** — khung dưới là bản đầy đủ về cấu trúc; điền đủ các bảng ánh xạ như mô tả Interfaces:

```python
"""Chuẩn hoá frame BVSC → dòng ClickHouse rt.* + delta Redis — spec §3.3.

MỘT từ điển ánh xạ dùng chung cho cả hai đường ghi (quyết định #9 spec lát cắt).
Nguồn sự thật tên cột: DDL spec ClickHouse §3. Frame hỏng tất định → NormalizeError
(đường block độc §5.8 — log + metric, không ghi sai).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Ho_Chi_Minh")

COLUMNS = {...}  # chép nguyên văn từ Interfaces ở trên


class NormalizeError(ValueError): ...


@dataclass
class Metrics:
    counters: dict[str, int] = field(default_factory=dict)

    def inc(self, key: str, n: int = 1) -> None:
        self.counters[key] = self.counters.get(key, 0) + n


@dataclass(frozen=True)
class Normalized:
    table: str
    row: dict
    delta: dict
    symbol: str


def _dec2(v, metrics: Metrics) -> Decimal:
    try:
        d = Decimal(str(v))
    except InvalidOperation as e:
        raise NormalizeError(f"không phải số: {v!r}") from e
    q = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    if q != d:
        metrics.inc("decimal_normalized")
    return q


def _uint(v):
    try:
        d = Decimal(str(v))
    except InvalidOperation as e:
        raise NormalizeError(f"không phải số: {v!r}") from e
    i = int(d)
    if i != d or i < 0:
        raise NormalizeError(f"không phải số nguyên không âm: {v!r}")
    return i


def _ts_ms(v) -> datetime:
    return datetime.fromtimestamp(_uint(v) / 1000, tz=TZ)


def symbol_of(event: str, payload: dict):
    return payload.get("MC" if event == "idx" else "SB")


# --- mỗi topic một hàm normalize_<topic>, dispatch qua: ---
_NORMALIZERS = {"t": _normalize_t, "o": _normalize_o, "i": _normalize_i,
                "idx": _normalize_idx, "ptm": _normalize_ptm}


def normalize(event, payload, received_at_ms, metrics):
    fn = _NORMALIZERS.get(event)
    if fn is None:
        raise NormalizeError(f"event không hỗ trợ: {event}")
    return fn(payload, received_at_ms, metrics)
```

Điểm bắt buộc trong từng hàm:

- `_normalize_t`: dựng `ts` từ `TD`+`FT` theo TZ (KeyError/ValueError → `NormalizeError`); các trường bắt buộc `SB/FMP/FV/SM`; `received_at = datetime.fromtimestamp(received_at_ms/1000, tz=TZ)`.
- `_normalize_i`/`_normalize_idx`: hai tập cột — Decimal (`_dec2`) và UInt (`_uint`) — mọi cột không có trong frame để `None`; unmapped → dict `extra`, cuối cùng `row["extra"] = json.dumps(extra, ensure_ascii=False, sort_keys=True) if extra else ""`.
- `_normalize_ptm`: `LS` là epoch **giây** (`datetime.fromtimestamp(_uint(LS), tz=TZ)`); `MKI`/`IAC` luôn vào `extra`; `TD`/`TI` drop.
- `delta`: dict cột→`str(giá trị)` của các cột frame mang (khác None), bỏ `extra`/`received_at`, thêm `"ts": str(epoch_ms)`.

- [ ] **Step 3: Chạy xanh** → PASS. **Step 4: Commit** — `git commit -m "feat(ingester): source->column dictionary and typing gate"`

---

### Task 11: `dedup.py` — FrameDedup + Stamper

**Files:**
- Create: `backend/ingester/dedup.py`
- Test: `backend/tests/ingester/test_i04_dedup.py`

**Interfaces:**
- Produces: `frame_key(event: str, payload: dict) -> bytes`; `class FrameDedup(window_s=600.0)` với `seen(key: bytes, now: float) -> bool`; `class Stamper` với `stamp(symbol: str, now_ms: int) -> int` (đơn điệu tăng theo mã — spec CH §4.1).

- [ ] **Step 1: Test đỏ**:

```python
from ingester.dedup import FrameDedup, Stamper, frame_key


def test_same_content_same_key_diff_content_diff_key():
    a = frame_key("t", {"SB": "ACV", "SM": "1"})
    assert a == frame_key("t", {"SM": "1", "SB": "ACV"})     # thứ tự khoá không đổi hash
    assert a != frame_key("t", {"SB": "ACV", "SM": "2"})
    assert a != frame_key("o", {"SB": "ACV", "SM": "1"})     # cùng payload khác event


def test_dedup_window():
    d = FrameDedup(window_s=10)
    k = frame_key("t", {"SM": "1"})
    assert d.seen(k, 100.0) is False
    assert d.seen(k, 105.0) is True          # trong cửa sổ → trùng
    assert d.seen(k, 200.0) is False         # ra ngoài cửa sổ → ghi lại (lưới block CH đỡ dưới)


def test_stamper_monotonic_per_symbol():
    s = Stamper()
    a = s.stamp("ACV", 1000)
    b = s.stamp("ACV", 1000)                 # cùng ms → +1
    c = s.stamp("ACV", 900)                  # đồng hồ lùi → vẫn tăng
    assert (a, b, c) == (1000, 1001, 1002)
    assert s.stamp("BID", 1000) == 1000      # mã khác độc lập
```

Chạy — Expected: FAIL import.

- [ ] **Step 2: Cài đặt**:

```python
"""Lưới dedup mức frame (hash nội dung, cửa sổ trượt) + received_at đơn điệu.

KHÔNG dùng luật thứ tự SM trước phiên đo (spec §1 quyết định #8; spec CH §5.4).
Frame lọt lại sau khi ra khỏi cửa sổ: chấp nhận — lưới block CH và tính idempotent
của MV chỉ số đỡ tầng dưới.
"""
from __future__ import annotations

import hashlib
import json


def frame_key(event: str, payload: dict) -> bytes:
    blob = event + "\x00" + json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                       ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).digest()


class FrameDedup:
    def __init__(self, window_s: float = 600.0):
        self.window_s = window_s
        self._seen: dict[bytes, float] = {}
        self._last_purge = 0.0

    def seen(self, key: bytes, now: float) -> bool:
        if now - self._last_purge > 60.0:
            cutoff = now - self.window_s
            self._seen = {k: t for k, t in self._seen.items() if t >= cutoff}
            self._last_purge = now
        prev = self._seen.get(key)
        self._seen[key] = now
        return prev is not None and now - prev < self.window_s


class Stamper:
    def __init__(self):
        self._last: dict[str, int] = {}

    def stamp(self, symbol: str, now_ms: int) -> int:
        v = max(now_ms, self._last.get(symbol, -1) + 1)
        self._last[symbol] = v
        return v
```

- [ ] **Step 3: Chạy xanh** → PASS. **Step 4: Commit** — `git commit -m "feat(ingester): content-hash frame dedup and monotonic stamper"`

---

### Task 12: `catalog.py` — danh mục runtime

**Files:**
- Create: `backend/ingester/catalog.py`
- Test: `backend/tests/ingester/test_i05_catalog.py`

**Interfaces:**
- Produces: `INDEX_CODES` (15 mã — `HOSE 30 100 MID SML XALL X50 SI ALL DIAMOND FINLEAD FINSELECT HNX HNX30 UPCOM`), `FLOORS = ["HOSE","HNX","UPCOM"]`, `BASE = "https://online.bvsc.com.vn"`; `@dataclass Catalog(symbols: list[str], base_state: dict[str, dict[str, str]])`; `build_catalog(client: httpx.Client | None = None) -> Catalog`; `topics(cat: Catalog) -> list[str]`; `fetch_instруments := fetch_base_state(client=None) -> dict[str, dict[str, str]]` *(đặt tên `fetch_base_state` — dùng lại khi reconnect)*.

- [ ] **Step 1: Test đỏ** (MockTransport, fixture literal thu nhỏ):

```python
import httpx

from ingester.catalog import BASE, Catalog, INDEX_CODES, build_catalog, topics

QUOTES = {"s": "ok", "d": [
    {"symbol": "ACB", "StockType": "2", "ceiling": 23950, "floor": 20850, "reference": 22400, "exchange": "HOSE"},
    {"symbol": "FUEVFVND", "StockType": "3", "ceiling": 30000, "floor": 26000, "reference": 28000, "exchange": "HOSE"},
    {"symbol": "CACB2602", "StockType": "4", "ceiling": 1000, "floor": 800, "reference": 900, "exchange": "HOSE"},
    {"symbol": "HDC425001", "StockType": "12", "ceiling": 0, "floor": 0, "reference": 0, "exchange": "HNX"},
    {"symbol": "VFMVF1", "StockType": "3", "ceiling": 0, "floor": 0, "reference": 12000, "exchange": "UPCOM"},
]}
INSTR = {"s": "ok", "d": [
    {"symbol": "ACB", "open": 22500, "low": 22300, "ceiling": 23950, "floor": 20850, "reference": 22400, "FloorCode": "10"},
    {"symbol": "41I1G8000", "open": 1300, "low": 1290, "ceiling": 1400, "floor": 1200, "reference": 1310, "FloorCode": "03"},
]}


def _client():
    def handler(request):
        if request.url.path == "/quotes":
            return httpx.Response(200, json=QUOTES)
        if request.url.path == "/datafeed/instruments":
            return httpx.Response(200, json=INSTR)
        return httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(handler), base_url=BASE)


def test_catalog_merges_and_filters():
    cat = build_catalog(client=_client())
    assert cat.symbols == ["ACB", "FUEVFVND", "VFMVF1"]        # CP+ETF; không CW/TP/phái sinh
    assert cat.base_state["ACB"]["open"] == "22500"            # nền từ instruments
    assert cat.base_state["VFMVF1"] == {"ceiling": "0", "floor": "0", "reference": "12000"}


def test_topics_shape():
    cat = Catalog(["ACB"], {})
    t = topics(cat)
    assert set(t[:3]) == {"i:ACB", "o10:ACB", "t:ACB"}         # o10, KHÔNG PHẢI o (bẫy §3)
    assert "idx:HOSE" in t and "idx:FINLEAD" in t and len([x for x in t if x.startswith("idx:")]) == len(INDEX_CODES)
    assert "ptm:UPCOM" in t
```

Chạy — Expected: FAIL import.

- [ ] **Step 2: Cài đặt**:

```python
"""Danh mục runtime — hợp nhất /quotes + /datafeed/instruments (spec CH #8/#9).

- Phân loại CHỈ bằng StockType của /quotes (bẫy 10 — bảng mã theo endpoint).
- Không endpoint nào một mình đủ (bẫy 11) — hợp nhất, khử trùng theo symbol.
- Không đọc Postgres. Reconnect chỉ gọi lại fetch_base_state, không đổi danh mục.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

BASE = "https://online.bvsc.com.vn"
INDEX_CODES = ["HOSE", "30", "100", "MID", "SML", "XALL", "X50", "SI", "ALL",
               "DIAMOND", "FINLEAD", "FINSELECT", "HNX", "HNX30", "UPCOM"]
FLOORS = ["HOSE", "HNX", "UPCOM"]
_BASE_FIELDS = ("open", "low", "ceiling", "floor", "reference")


@dataclass(frozen=True)
class Catalog:
    symbols: list[str]
    base_state: dict[str, dict[str, str]]


def _get(client: httpx.Client, path: str, **params) -> list[dict]:
    r = client.get(path, params=params or None, timeout=30.0)
    r.raise_for_status()
    body = r.json()
    d = body.get("d")
    if body.get("s") != "ok" or not isinstance(d, list) or not d:
        raise RuntimeError(f"BVSC {path}: response bất thường (s={body.get('s')!r}, n={len(d or [])})")
    return d


def fetch_base_state(client: httpx.Client | None = None) -> dict[str, dict[str, str]]:
    own = client is None
    client = client or httpx.Client(base_url=BASE)
    try:
        rows = _get(client, "/datafeed/instruments")
        return {r["symbol"]: {k: str(r[k]) for k in _BASE_FIELDS if r.get(k) not in (None, "")}
                for r in rows}
    finally:
        if own:
            client.close()


def build_catalog(client: httpx.Client | None = None) -> Catalog:
    own = client is None
    client = client or httpx.Client(base_url=BASE)
    try:
        quotes = _get(client, "/quotes", symbols="ALL")
        inst = fetch_base_state(client)
        symbols, base_state = [], {}
        for q in quotes:
            if q.get("StockType") not in ("2", "3"):
                continue
            sym = q["symbol"]
            symbols.append(sym)
            base_state[sym] = inst.get(sym) or {
                k: str(q[k]) for k in ("ceiling", "floor", "reference") if q.get(k) is not None
            }
        return Catalog(sorted(set(symbols)), base_state)
    finally:
        if own:
            client.close()


def topics(cat: Catalog) -> list[str]:
    out = []
    for s in cat.symbols:
        out += [f"i:{s}", f"o10:{s}", f"t:{s}"]     # o10 — bẫy 11-bvsc-realtime §3
    out += [f"idx:{c}" for c in INDEX_CODES]
    out += [f"ptm:{f}" for f in FLOORS]
    return out
```

- [ ] **Step 3: Chạy xanh** → PASS. **Step 4: Commit** — `git commit -m "feat(ingester): runtime catalog from merged BVSC endpoints"`

---

### Task 13: fixture Redis + `state.py` + `leader.py`

**Files:**
- Create: `backend/tests/ingester/conftest.py`, `backend/ingester/state.py`, `backend/ingester/leader.py`
- Test: `backend/tests/ingester/test_i06_state.py`, `backend/tests/ingester/test_i07_leader.py`

**Interfaces:**
- Produces conftest: fixture session `redis_url` (container `redis:7-alpine` ephemeral, port tự do, xoá cuối session — cùng pattern `tests/clickhouse/conftest.py`).
- Produces `state`: `class RedisSink(redis)` (client `redis.asyncio.Redis`) — `async init_state(base: dict[str, dict[str, str]])`; `async apply(n: Normalized)`. Khoá/kênh đúng spec §3.4: HASH `rt:state:{symbol}` / `rt:state:idx:{code}` (EXPIRE 86400), PUBLISH `rt:pub:{event}:{key}` với event ∈ `i t o idx ptm`, key = symbol/mã chỉ số/sàn; payload JSON `{"symbol":…, **delta}`.
- Produces `leader`: `class LeaderLock(redis, ttl_ms=5000, renew_s=2.0, retry_s=0.5)` — thuộc tính `id`; `async try_acquire() -> bool`; `async renew() -> bool` (Lua so-id — không đè khoá người khác); `async run(is_leader: asyncio.Event)` (renew trả 0 → clear ngay; lỗi mạng 2 lần liên tiếp → clear); `KEY = "rt:ingester:leader"`.

- [ ] **Step 1: conftest** (viết trước — cả hai test cần):

```python
import socket
import subprocess
import time
import uuid

import pytest


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def redis_url():
    name = f"redis-test-{uuid.uuid4().hex[:8]}"
    port = _free_port()
    subprocess.run(["docker", "run", "-d", "--name", name,
                    "-p", f"127.0.0.1:{port}:6379", "redis:7-alpine"],
                   check=True, capture_output=True)
    url = f"redis://127.0.0.1:{port}/0"
    import redis as redis_sync
    try:
        r = redis_sync.Redis.from_url(url)
        for _ in range(30):
            try:
                if r.ping():
                    break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("redis test container không lên")
        yield url
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
```

- [ ] **Step 2: Test đỏ state** — `test_i06_state.py`:

```python
import asyncio
import json

import pytest
import redis.asyncio as aioredis

from ingester.normalize import Metrics, normalize
from ingester.state import RedisSink

RECV = 1786342136000


@pytest.fixture()
def run(redis_url):
    def _run(coro):
        return asyncio.run(coro)
    return _run


def test_init_and_apply_i(redis_url, run):
    async def scenario():
        r = aioredis.Redis.from_url(redis_url, decode_responses=True)
        sink = RedisSink(r)
        await sink.init_state({"BID": {"open": "39550", "reference": "39050"}})
        assert await r.hget("rt:state:BID", "open") == "39550"

        pubsub = r.pubsub()
        await pubsub.subscribe("rt:pub:i:BID")
        await pubsub.get_message(timeout=2)          # subscribe ack
        n = normalize("i", {"EX": "HOSE", "t": 1786330492737, "U2": "43500", "SB": "BID"}, RECV, Metrics())
        await sink.apply(n)
        assert await r.hget("rt:state:BID", "u2") == "43500"
        assert await r.hget("rt:state:BID", "open") == "39550"   # trường cũ giữ nguyên
        assert await r.ttl("rt:state:BID") > 0
        msg = await pubsub.get_message(timeout=2)
        body = json.loads(msg["data"])
        assert body["symbol"] == "BID" and body["u2"] == "43500"
        await r.aclose()
    run(scenario())


def test_apply_trade_publishes_no_hash(redis_url, run):
    async def scenario():
        r = aioredis.Redis.from_url(redis_url, decode_responses=True)
        sink = RedisSink(r)
        n = normalize("t", {"TD": "10/08/2026", "FT": "13:08:56", "SB": "ACV", "FV": "100",
                            "LC": "S", "FMP": "42100.0", "FCV": "1000.0", "SM": "74027",
                            "AVO": "590000", "AVA": "24983210000.0"}, RECV, Metrics())
        pubsub = r.pubsub()
        await pubsub.subscribe("rt:pub:t:ACV")
        await pubsub.get_message(timeout=2)
        await sink.apply(n)
        msg = await pubsub.get_message(timeout=2)
        assert json.loads(msg["data"])["price"] == "42100.00"
        assert await r.exists("rt:state:ACV") == 0    # t không đụng HASH
        await r.aclose()
    run(scenario())
```

- [ ] **Step 3: Cài đặt `state.py`**:

```python
"""Hot path Redis — HASH state + PUBLISH delta (spec §3.4). Chỉ leader gọi apply."""
from __future__ import annotations

import json

from ingester.normalize import Normalized

_TTL_S = 86400
_EVENT_OF_TABLE = {"snapshot_delta": "i", "trade": "t", "quote": "o",
                   "index_delta": "idx", "pt_match": "ptm"}


class RedisSink:
    def __init__(self, redis):
        self.redis = redis

    async def init_state(self, base: dict[str, dict[str, str]]) -> None:
        pipe = self.redis.pipeline(transaction=False)
        for sym, fields in base.items():
            if fields:
                pipe.hset(f"rt:state:{sym}", mapping=fields)
                pipe.expire(f"rt:state:{sym}", _TTL_S)
        await pipe.execute()

    async def apply(self, n: Normalized) -> None:
        event = _EVENT_OF_TABLE[n.table]
        if n.table == "pt_match":
            key = n.row["market"]
        elif n.table == "index_delta":
            key = n.symbol
        else:
            key = n.symbol
        pipe = self.redis.pipeline(transaction=False)
        if n.table == "snapshot_delta":
            pipe.hset(f"rt:state:{n.symbol}", mapping=n.delta)
            pipe.expire(f"rt:state:{n.symbol}", _TTL_S)
        elif n.table == "index_delta":
            pipe.hset(f"rt:state:idx:{n.symbol}", mapping=n.delta)
            pipe.expire(f"rt:state:idx:{n.symbol}", _TTL_S)
        pipe.publish(f"rt:pub:{event}:{key}", json.dumps({"symbol": n.symbol, **n.delta},
                                                         ensure_ascii=False))
        await pipe.execute()
```

- [ ] **Step 4: Test đỏ leader** — `test_i07_leader.py`:

```python
import asyncio

import redis.asyncio as aioredis

from ingester.leader import LeaderLock


def test_lock_exclusive_and_renew(redis_url):
    async def scenario():
        r1 = aioredis.Redis.from_url(redis_url, decode_responses=True)
        r2 = aioredis.Redis.from_url(redis_url, decode_responses=True)
        a = LeaderLock(r1, ttl_ms=800)
        b = LeaderLock(r2, ttl_ms=800)
        assert await a.try_acquire() is True
        assert await b.try_acquire() is False
        assert await a.renew() is True
        assert await b.renew() is False          # không đè/đụng khoá của a
        await asyncio.sleep(1.0)                 # TTL hết, a không renew nữa
        assert await b.try_acquire() is True     # tiếp quản
        await r1.aclose(); await r2.aclose()
    asyncio.run(scenario())
```

- [ ] **Step 5: Cài đặt `leader.py`**:

```python
"""Leader lock Redis — SET NX PX + Lua renew so id (spec §3.6, market-data-store §3.1)."""
from __future__ import annotations

import asyncio
import os
import secrets
import socket

_RENEW_LUA = ("if redis.call('get', KEYS[1]) == ARGV[1] then"
              " return redis.call('pexpire', KEYS[1], ARGV[2]) else return 0 end")


class LeaderLock:
    KEY = "rt:ingester:leader"

    def __init__(self, redis, ttl_ms: int = 5000, renew_s: float = 2.0, retry_s: float = 0.5):
        self.redis = redis
        self.ttl_ms = ttl_ms
        self.renew_s = renew_s
        self.retry_s = retry_s
        self.id = f"{socket.gethostname()}:{os.getpid()}:{secrets.token_hex(4)}"

    async def try_acquire(self) -> bool:
        return bool(await self.redis.set(self.KEY, self.id, nx=True, px=self.ttl_ms))

    async def renew(self) -> bool:
        return bool(await self.redis.eval(_RENEW_LUA, 1, self.KEY, self.id, str(self.ttl_ms)))

    async def run(self, is_leader: asyncio.Event) -> None:
        net_fail = 0
        while True:
            try:
                if is_leader.is_set():
                    if not await self.renew():
                        is_leader.clear()        # khoá mất về tay khác → hạ cấp NGAY
                    net_fail = 0
                    await asyncio.sleep(self.renew_s)
                else:
                    if await self.try_acquire():
                        is_leader.set()
                        continue
                    await asyncio.sleep(self.retry_s)
            except (ConnectionError, OSError):
                net_fail += 1
                if net_fail >= 2 and is_leader.is_set():
                    is_leader.clear()            # mất Redis 2 nhịp → ngừng ghi
                await asyncio.sleep(self.retry_s)
```

- [ ] **Step 6: Chạy xanh cả hai** → PASS. **Step 7: Commit** — `git commit -m "feat(ingester): redis hot path sink and leader lock"`

---

### Task 14: `chwriter.py` — buffer/flush/retry/poison

**Files:**
- Create: `backend/ingester/chwriter.py`
- Create: `backend/tests/ingester/test_i08_chwriter.py` + `backend/tests/ingester/conftest.py` thêm dòng mượn fixture CH: `from tests.clickhouse.conftest import ch, ch_backup_dir, migrated  # noqa: F401`

**Interfaces:**
- Consumes: `COLUMNS`, `Normalized` (Task 10).
- Produces: `BLOCK_CAP = 5000`, `RETRY_BUDGET_S = 60`, `class ChWriter(client, sleep_fn=time.sleep)` — `add(n: Normalized)`, `flush_once()` (sync — gọi từ `asyncio.to_thread` hoặc test), `metrics: Metrics`; hành vi: transient → retry **nguyên block** backoff 1→16 s tổng ≤ 60 s rồi bỏ block (`dropped_block.<table>`); tất định → chia đôi đệ quy, dòng hỏng `poison_row.<table>` + log; chạm `BLOCK_CAP` → cắt block chờ nhịp sau + `block_cap.<table>` (không flush sớm — trần 1 part/giây spec CH §10).

- [ ] **Step 1: Test đỏ** (CH thật + stub cho retry):

```python
import time
from decimal import Decimal

from ingester.chwriter import ChWriter
from ingester.normalize import Metrics, normalize

RECV = 1786342136000
T = {"TD": "10/08/2026", "FT": "13:08:56", "SB": "ACV", "FV": "100", "LC": "S",
     "FMP": "42100.0", "FCV": "1000.0", "SM": "74027", "AVO": "590000", "AVA": "24983210000.0"}


def _n(**kw):
    return normalize("t", {**T, **kw}, RECV, Metrics())


def test_flush_writes_rows(migrated):
    w = ChWriter(migrated)
    w.add(_n())
    w.add(_n(SM="74028", FMP="42200.0"))
    w.flush_once()
    rows = migrated.query(
        "SELECT price, volume FROM rt.trade WHERE symbol='ACV' AND seq IN (74027,74028)"
        " ORDER BY seq").result_rows
    assert rows == [(Decimal("42100.00"), 100), (Decimal("42200.00"), 100)]
    migrated.command("ALTER TABLE rt.trade DELETE WHERE symbol='ACV'")


def test_poison_row_isolated(migrated):
    w = ChWriter(migrated)
    w.add(_n(SM="80001"))
    w.add(_n(SM="80002", FMP="99999999999999999.0"))   # tràn Decimal64(2) → lỗi tất định
    w.add(_n(SM="80003"))
    w.flush_once()
    n = migrated.query(
        "SELECT count() FROM rt.trade WHERE symbol='ACV' AND seq BETWEEN 80001 AND 80003"
    ).result_rows[0][0]
    assert n == 2
    assert w.metrics.counters.get("poison_row.trade") == 1
    migrated.command("ALTER TABLE rt.trade DELETE WHERE symbol='ACV'")


class FlakyClient:
    def __init__(self, real, fail_times):
        self.real, self.left = real, fail_times
        self.blocks = []

    def insert(self, table, data, column_names):
        if self.left > 0:
            self.left -= 1
            raise ConnectionError("mạng chập chờn")
        self.blocks.append(list(data))
        return self.real.insert(table, data, column_names=column_names)


def test_transient_retries_same_block(migrated):
    flaky = FlakyClient(migrated, fail_times=2)
    w = ChWriter(flaky, sleep_fn=lambda s: None)
    w.add(_n(SM="90001"))
    w.flush_once()
    assert len(flaky.blocks) == 1 and len(flaky.blocks[0]) == 1   # block nguyên vẹn, không gộp thêm
    migrated.command("ALTER TABLE rt.trade DELETE WHERE symbol='ACV'")


def test_block_cap_cuts_without_flush():
    class NullClient:
        def insert(self, *a, **k):
            raise AssertionError("không được insert khi chưa flush")
    w = ChWriter(NullClient())
    import ingester.chwriter as m
    for i in range(m.BLOCK_CAP + 3):
        w.add(_n(SM=str(100000 + i)))
    assert w.metrics.counters.get("block_cap.trade") == 1
```

Chạy — Expected: FAIL import.

- [ ] **Step 2: Cài đặt**:

```python
"""Batch writer ClickHouse — hợp đồng spec CH §5: flush 1 s cố định (vòng lặp ở main),
retry NGUYÊN block, chia đôi block độc, trần BLOCK_CAP không flush sớm."""
from __future__ import annotations

import logging
import time
from collections import deque

from ingester.normalize import COLUMNS, Metrics, Normalized

log = logging.getLogger("ingester.chwriter")
BLOCK_CAP = 5000
RETRY_BUDGET_S = 60          # < tuổi thọ cửa sổ dedup ~100 s (spec CH §5.5)
_TRANSIENT = (ConnectionError, TimeoutError, OSError)


def _is_transient(e: Exception) -> bool:
    if isinstance(e, _TRANSIENT):
        return True
    text = str(e).lower()
    return "timeout" in text or "connection" in text or "temporarily" in text


class ChWriter:
    def __init__(self, client, sleep_fn=time.sleep):
        self.client = client
        self.sleep = sleep_fn
        self.metrics = Metrics()
        self.buffers: dict[str, list[list]] = {t: [] for t in COLUMNS}
        self.pending: dict[str, deque] = {t: deque() for t in COLUMNS}

    def add(self, n: Normalized) -> None:
        buf = self.buffers[n.table]
        buf.append([n.row.get(c) for c in COLUMNS[n.table]])
        if len(buf) >= BLOCK_CAP:
            self.pending[n.table].append(buf[:])
            buf.clear()
            self.metrics.inc(f"block_cap.{n.table}")
            log.warning("bảng %s chạm trần block %d — tải cao bất thường", n.table, BLOCK_CAP)

    def flush_once(self) -> None:
        for table, buf in self.buffers.items():
            if buf:
                self.pending[table].append(buf[:])
                buf.clear()
        for table, q in self.pending.items():
            while q:
                self._write_block(table, q[0])
                q.popleft()

    def _write_block(self, table: str, block: list, budget: float | None = None) -> None:
        budget = RETRY_BUDGET_S if budget is None else budget
        delay, spent = 1.0, 0.0
        while True:
            try:
                self.client.insert(f"rt.{table}", block, column_names=COLUMNS[table])
                self.metrics.inc(f"rows.{table}", len(block))
                return
            except Exception as e:  # noqa: BLE001 — phân loại rồi xử lý theo hợp đồng
                if _is_transient(e):
                    if spent >= budget:
                        self.metrics.inc(f"dropped_block.{table}", len(block))
                        log.error("bỏ block %s (%d dòng) sau %ss retry: %r", table, len(block), spent, e)
                        return
                    self.sleep(delay)
                    spent += delay
                    delay = min(delay * 2, 16.0)
                    continue                      # retry NGUYÊN block — không gộp dòng mới
                if len(block) == 1:
                    self.metrics.inc(f"poison_row.{table}")
                    log.error("dòng độc %s: %r — %r", table, block[0], e)
                    return
                mid = len(block) // 2             # lỗi tất định → cô lập dòng hỏng (§5.8)
                self._write_block(table, block[:mid], budget)
                self._write_block(table, block[mid:], budget)
                return
```

- [ ] **Step 3: Chạy xanh** (cần Docker) → PASS. **Step 4: Commit** — `git commit -m "feat(ingester): clickhouse batch writer with retry and poison isolation"`

---

### Task 15: `measure.py` + `reconcile.py`

**Files:**
- Create: `backend/ingester/measure.py`, `backend/ingester/reconcile.py`
- Test: `backend/tests/ingester/test_i09_measure_reconcile.py`

**Interfaces:**
- Produces `measure`: `class MeasureWriter(out_dir: Path, clock=time.time)` — `write(received_at_ms: int, packet: str)` ghi dòng JSONL `{"r":…,"p":"<packet nguyên văn>"}` vào `frames-YYYYMMDD-HH.jsonl` (giờ VN); sang giờ mới → đóng file cũ và nén thành `.jsonl.gz` (xoá bản thô); `close()`.
- Produces `reconcile`: `@dataclass ReconcileResult(p1: list[tuple], p2: list[tuple], ok: int)`; `reconcile(client, d: date) -> ReconcileResult` — so `Σ bar_1m_v.v` với `max(trade.cum_volume)` từng mã (spec §3.7): `Σv > max(AVO)` → P1; hụt > 0,1% → P2.

- [ ] **Step 1: Test đỏ**:

```python
import gzip
import json
from datetime import date, datetime
from pathlib import Path

from ingester.measure import MeasureWriter
from ingester.reconcile import reconcile


def test_measure_roundtrip_exact_bytes(tmp_path):
    w = MeasureWriter(tmp_path)
    pkt = '42["t",{"SB":"ACV","FMP":"42100.0"}]'
    w.write(1786342136000, pkt)
    w.close()
    f = next(tmp_path.glob("frames-*.jsonl*"))
    opener = gzip.open if f.suffix == ".gz" else open
    with opener(f, "rt", encoding="utf-8") as fh:
        row = json.loads(fh.readline())
    assert row == {"r": 1786342136000, "p": pkt}      # nguyên văn từng byte


def test_reconcile_classifies(migrated):
    from decimal import Decimal
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    ts = datetime(2026, 8, 20, 9, 15, 1, tzinfo=tz)
    rows = [
        # mã OK: 2 tick, cum khớp tổng
        ["OKA", ts, 1, Decimal("10.00"), 100, "B", Decimal("0.00"), 100, Decimal("1000.00"), ts],
        ["OKA", ts, 2, Decimal("10.00"), 50, "S", Decimal("0.00"), 150, Decimal("1500.00"), ts],
        # mã hụt >0.1%: bar có 100 nhưng AVO nói 200
        ["MISS", ts, 1, Decimal("10.00"), 100, "B", Decimal("0.00"), 200, Decimal("2000.00"), ts],
    ]
    migrated.insert("rt.trade", rows, column_names=[
        "symbol", "ts", "seq", "price", "volume", "side", "change",
        "cum_volume", "cum_value", "received_at"])
    r = reconcile(migrated, date(2026, 8, 20))
    assert r.ok >= 1
    assert any(s == "MISS" for s, *_ in r.p2)
    assert not any(s == "OKA" for s, *_ in r.p1 + r.p2)
    migrated.command("ALTER TABLE rt.trade DELETE WHERE symbol IN ('OKA','MISS')")
    migrated.command("ALTER TABLE rt.bar_1m DROP PARTITION '202608'")
```

*(P1 khó dựng sạch qua MV — đếm đôi cần block trùng lách dedup; case P1 kiểm bằng logic thuần: thêm test đơn vị cho hàm phân loại `_classify(bar_vol, avo)` nếu tách được — tách `_classify(bar_vol: int, avo: int) -> str` trả `"ok"|"p1"|"p2"|"minor"` và test 4 nhánh literal.)*

- [ ] **Step 2: Cài đặt `measure.py`**:

```python
"""Ghi frame thô chế độ đo — JSONL xoay theo giờ VN, gzip khi đóng (spec §3.5)."""
from __future__ import annotations

import gzip
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class MeasureWriter:
    def __init__(self, out_dir: Path, clock=time.time):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self._fh = None
        self._hour = None

    def _rotate(self, now: float) -> None:
        hour = datetime.fromtimestamp(now, tz=TZ).strftime("%Y%m%d-%H")
        if hour == self._hour:
            return
        self._gzip_current()
        self._hour = hour
        self._path = self.out_dir / f"frames-{hour}.jsonl"
        self._fh = self._path.open("a", encoding="utf-8")

    def _gzip_current(self) -> None:
        if self._fh is None:
            return
        self._fh.close()
        with self._path.open("rb") as src, gzip.open(f"{self._path}.gz", "wb") as dst:
            shutil.copyfileobj(src, dst)
        self._path.unlink()
        self._fh = None

    def write(self, received_at_ms: int, packet: str) -> None:
        self._rotate(self.clock())
        self._fh.write(json.dumps({"r": received_at_ms, "p": packet}, ensure_ascii=False) + "\n")

    def close(self) -> None:
        self._gzip_current()
```

- [ ] **Step 3: Cài đặt `reconcile.py`**:

```python
"""Đối chứng cuối phiên §5.7 spec ClickHouse — hai chiều lệch hai nghĩa, hai ngưỡng."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

THRESHOLD = 0.001  # 0,1% — hiệu chỉnh sau tuần đầu (spec CH §10)

_SQL = """
SELECT coalesce(b.symbol, t.symbol) AS symbol,
       coalesce(b.sv, 0)  AS bar_vol,  coalesce(t.mv, 0)  AS avo
FROM (SELECT symbol, sum(v) AS sv FROM rt.bar_1m_v WHERE toDate(ts) = {d:Date} GROUP BY symbol) b
FULL OUTER JOIN
     (SELECT symbol, max(cum_volume) AS mv FROM rt.trade WHERE toDate(ts) = {d:Date} GROUP BY symbol) t
ON b.symbol = t.symbol
"""


@dataclass
class ReconcileResult:
    p1: list
    p2: list
    ok: int


def _classify(bar_vol: int, avo: int) -> str:
    if bar_vol > avo:
        return "p1"                       # đếm đôi — luôn là lỗi
    if avo == 0:
        return "ok"
    miss = (avo - bar_vol) / avo
    if miss > THRESHOLD:
        return "p2"                       # mất quá ngưỡng chấp nhận
    return "minor" if miss > 0 else "ok"


def reconcile(client, d: date) -> ReconcileResult:
    rows = client.query(_SQL, parameters={"d": d}).result_rows
    p1, p2, ok = [], [], 0
    for symbol, bar_vol, avo in rows:
        kind = _classify(int(bar_vol), int(avo))
        if kind == "p1":
            p1.append((symbol, int(bar_vol), int(avo)))
        elif kind == "p2":
            p2.append((symbol, int(bar_vol), int(avo)))
        else:
            ok += 1
    return ReconcileResult(p1, p2, ok)
```

*(thêm test `_classify` 4 nhánh: `(150,100)→p1 · (100,200)→p2 · (999,1000)→minor · (100,100)→ok`)*

- [ ] **Step 4: Chạy xanh** → PASS. **Step 5: Commit** — `git commit -m "feat(ingester): measure JSONL writer and end-of-session reconcile"`

---

### Task 16: `main.py` + `__main__.py` — orchestration + test tích hợp server giả

**Files:**
- Create: `backend/ingester/main.py`, `backend/ingester/__main__.py`
- Test: `backend/tests/ingester/test_i10_main.py`

**Interfaces:**
- Produces `main`: `async socket_loop(url, topics, on_packet, stop: asyncio.Event, on_reconnect=None, reconnect_delay_s=5.0)` — bắt tay (đợi `Open` + `Control("40")`), subscribe theo lô 100 (Task 9 `chunk`), tự gửi PING theo `pingInterval` server khai, `recv` timeout = `pingTimeout` → coi như rớt; rớt → gọi `on_reconnect()` (đồng bộ lại state) → nối lại sau `reconnect_delay_s`, đăng ký lại toàn bộ; `run(mode: str, minutes: float | None) -> int` — mode `run|measure|reconcile`, trình tự khởi động đúng spec §2.1 (thứ tự cứng: config → `assert_migrated` → Redis ping → catalog → init_state → lock → socket); vòng đời phiên: quá `15:05` giờ VN (hoặc hết `minutes`) → stop → final flush → (mode run) reconcile → thoát.
- Produces `__main__`: argparse `--measure`, `--out DIR`, `--minutes N`, `--reconcile`, `--date YYYY-MM-DD`.
- Đường xử lý một packet (mode run — chép làm docstring):

```
raw → (measure? ghi file, xong) → parse_packet → Event? → name ∈ 5 topic?
    → frame_key + dedup.seen? bỏ → symbol_of → stamper.stamp → normalize
    → NormalizeError? log+metric, bỏ → chwriter.add (luôn — buffer chỉ leader flush)
    → is_leader? queue → RedisSink.apply
```

⚠️ **Chỉ leader flush ClickHouse**: `flush_loop` mỗi 1,0 s gọi `asyncio.to_thread(w.flush_once)` **chỉ khi `is_leader.is_set()`**; standby giữ buffer, và để buffer standby không phình vô hạn, khi **không** là leader thì mỗi nhịp flush **xả bỏ** block quá 120 s tuổi (đếm metric `standby_dropped`) — standby chỉ cần state + seen-set ấm, dữ liệu đã có leader ghi.

- [ ] **Step 1: Test đỏ** — `test_i10_main.py` (server EIO3 giả bằng `websockets.serve`):

```python
import asyncio
import json

import pytest
import websockets

from ingester.eio import parse_packet
from ingester.main import socket_loop

HANDSHAKE = '0{"sid":"x","upgrades":[],"pingInterval":25000,"pingTimeout":60000}'
T_PACKET = '42["t",{"TD":"10/08/2026","FT":"13:08:56","SB":"ACV","FV":"100","LC":"S","FMP":"42100.0","FCV":"1000.0","SM":"74027","AVO":"590000","AVA":"24983210000.0"}]'


def test_socket_loop_subscribes_receives_reconnects():
    async def scenario():
        state = {"connects": 0, "subs": []}
        got, resubbed = asyncio.Event(), asyncio.Event()

        async def handler(ws):
            state["connects"] += 1
            await ws.send(HANDSHAKE)
            await ws.send("40")
            msg = await ws.recv()                      # frame subscribe đầu
            state["subs"].append(msg)
            if state["connects"] == 1:
                await ws.send(T_PACKET)
                await asyncio.sleep(0.2)
                await ws.close()                       # ép rớt → client phải nối lại
            else:
                resubbed.set()
                await asyncio.sleep(5)

        packets = []

        def on_packet(raw):
            packets.append(raw)
            if raw == T_PACKET:
                got.set()

        async with websockets.serve(handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            stop = asyncio.Event()
            task = asyncio.create_task(socket_loop(
                f"ws://127.0.0.1:{port}/", ["t:ACV", "i:ACV"], on_packet, stop,
                reconnect_delay_s=0.1))
            await asyncio.wait_for(got.wait(), 5)
            await asyncio.wait_for(resubbed.wait(), 5)
            stop.set()
            await asyncio.wait_for(task, 5)

        assert state["connects"] == 2                       # đã tự nối lại
        sub0 = json.loads(state["subs"][0][3:])             # bỏ "42<ack>"
        assert sub0[1]["data"]["op"] == "subscribe"
        assert sub0[1]["data"]["args"][0] == "t:ACV"
        assert state["subs"][1] == state["subs"][0].replace("421", "421") or state["subs"][1]  # đăng ký lại TOÀN BỘ
        assert T_PACKET in packets
    asyncio.run(scenario())
```

*(assert cuối cùng viết gọn: so `args` của lần 2 bằng `args` lần 1 — đăng ký lại toàn bộ.)*

- [ ] **Step 2: Cài đặt `main.py`** (khung — giữ đúng thứ tự khởi động spec §2.1 và đường xử lý packet ở Interfaces):

```python
from __future__ import annotations

import asyncio
import logging
import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

import websockets

from ingester import catalog as cat
from ingester import eio
from ingester.chwriter import ChWriter
from ingester.dedup import FrameDedup, Stamper, frame_key
from ingester.measure import MeasureWriter
from ingester.normalize import Metrics, NormalizeError, normalize, symbol_of

log = logging.getLogger("ingester")
TZ = ZoneInfo("Asia/Ho_Chi_Minh")
SESSION_END = (15, 5)          # 15:05 — sau đó dừng, flush, đối chứng, thoát
EVENTS = {"i", "t", "o", "idx", "ptm"}


async def socket_loop(url, topics, on_packet, stop, on_reconnect=None, reconnect_delay_s=5.0):
    first = True
    while not stop.is_set():
        if not first:
            await asyncio.sleep(reconnect_delay_s)     # client gốc BVSC: 5 s
            if on_reconnect:
                await asyncio.to_thread(on_reconnect)  # đồng bộ state từ REST
        first = False
        try:
            async with websockets.connect(url, max_size=2 ** 22) as ws:
                ping_ms, timeout_ms = 25000, 60000
                ready = opened = False
                while not (ready and opened):          # đợi Open + "40"
                    pkt = eio.parse_packet(await asyncio.wait_for(ws.recv(), 10))
                    if isinstance(pkt, eio.Open):
                        ping_ms, timeout_ms = pkt.ping_interval_ms, pkt.ping_timeout_ms
                        opened = True
                    elif isinstance(pkt, eio.Control) and pkt.kind == "40":
                        ready = True
                ack = 0
                for batch in eio.chunk(topics, 100):
                    ack += 1
                    await ws.send(eio.build_subscribe(ack, batch))

                async def pinger():
                    while True:
                        await asyncio.sleep(ping_ms / 1000)
                        await ws.send(eio.PING)

                ping_task = asyncio.create_task(pinger())
                try:
                    while not stop.is_set():
                        raw = await asyncio.wait_for(ws.recv(), timeout_ms / 1000)
                        on_packet(raw)
                finally:
                    ping_task.cancel()
        except Exception as e:  # noqa: BLE001 — rớt là bình thường (2 lần/4 phút), log rồi vòng lại
            if stop.is_set():
                break
            log.warning("socket rớt: %r — nối lại sau %ss", e, reconnect_delay_s)
    return None
```

*(`asyncio.CancelledError` là BaseException nên không bị `except Exception` nuốt — đúng chủ đích.)*

`run(mode, minutes)` — các bước, mỗi bước một hàm nhỏ:

1. `cfg = config.load(need_db=(mode != "measure"))`; logging ra `cfg.log_dir/ingester-YYYYMMDD.log` + stderr.
2. mode `reconcile`: client CH từ `cfg.clickhouse_url` → `reconcile(client, d)` → in P1/P2/ok, exit 1 nếu có P1 hoặc P2, else 0.
3. mode `run`: `from core import ch_migrate; ch_migrate.assert_migrated(clickhouse_connect.get_client(dsn=cfg.clickhouse_url))` — lỗi → in rõ, exit 3 (spec CH §8: **trước khi nối socket**). Redis ping.
4. `catalog = cat.build_catalog()`; topics = `cat.topics(catalog)`; mode `measure` thêm: mã phái sinh từ `fetch instruments FloorCode=="03"` (lấy `41I1G8000` + 2 mã đầu khác) × 20 prefix `["i","i_ol","o10","o_ol10","o","o_ol","t","t_ol","tm","e","e_ol","im","e_im","om","idx","pth","ptm","p","u","d"]` + `pth:HOSE/HNX/UPCOM`.
5. mode `run`: `sink.init_state(catalog.base_state)` (chỉ khi leader — standby bỏ qua, tiếp quản mới init).
6. Tasks: `leader.run(is_leader)` (mode run) · `socket_loop(...)` · `flush_loop` (mode run) · `log_loop` 60 s in counters · `session_timer` — `datetime.now(TZ)` quá `SESSION_END` hoặc quá `minutes` → `stop.set()`.
7. Kết thúc: final `flush_once()` (mode run, nếu leader) · `measure_writer.close()` (mode measure) · mode run: `reconcile` hôm nay, in kết quả; exit 0.

`on_packet` (mode run) và `on_packet_measure` như khối Interfaces. Redis apply qua `asyncio.Queue` + task tiêu thụ (giữ thứ tự); `on_packet` chạy trong event loop (callback từ socket_loop) — chỉ làm việc sync nhanh + `queue.put_nowait`.

`__main__.py`:

```python
import argparse
import asyncio
from datetime import date

from ingester.main import run


def main() -> int:
    ap = argparse.ArgumentParser("ingester")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--out", default=None, help="thư mục frame đo (default INGESTER_MEASURE_DIR)")
    ap.add_argument("--minutes", type=float, default=None)
    ap.add_argument("--reconcile", action="store_true")
    ap.add_argument("--date", type=date.fromisoformat, default=None)
    a = ap.parse_args()
    mode = "measure" if a.measure else ("reconcile" if a.reconcile else "run")
    return asyncio.run(run(mode, minutes=a.minutes, out=a.out, d=a.date))


if __name__ == "__main__":
    raise SystemExit(main())
```

*(chữ ký `run(mode, minutes=None, out=None, d=None)` — thống nhất với Interfaces.)*

- [ ] **Step 3: Chạy xanh** `tests/ingester` toàn bộ → PASS. Chạy cả `uv run pytest tests -v` — bộ cũ không vỡ.
- [ ] **Step 4: Commit** — `git commit -m "feat(ingester): session orchestration, CLI, fake-server integration test"`

---

### Task 17 **[controller]**: vận hành — env, user DB, README, Task Scheduler, chạy thật OMO + smoke ingester

- [ ] `.env.example`: thêm khối (không giá trị thật):

```
# Lát cắt ingester + OMO (spec 2026-08-26)
CLICKHOUSE_INGESTER_URL=http://ingester_worker:change-me-in-production@127.0.0.1:8123
REDIS_URL=redis://127.0.0.1:6379/0
ETL_DATABASE_URL=postgresql+psycopg://etl_worker:change-me-in-production@127.0.0.1:5432/dulieu
# INGESTER_LOG_DIR=D:\dlck-runtime\logs
# INGESTER_MEASURE_DIR=D:\dlck-runtime\measure
```

- [ ] Tạo user thật per-môi-trường (không commit mật khẩu): ClickHouse `ingester_worker` theo `database/clickhouse/create_users.sql.example`; Postgres `CREATE USER etl_worker LOGIN PASSWORD '…' IN ROLE dlck_etl;` (README database). Cập nhật `.env` thật.
- [ ] `scripts/register-tasks.ps1` (idempotent — `schtasks /Create /F`):

```powershell
# Đăng ký Task Scheduler cho lát cắt ingester + OMO. Chạy: pwsh scripts/register-tasks.ps1
$repo = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $repo "backend"
$uv = (Get-Command uv).Source
$omoCmd = "cd /d `"$backend`" && set PYTHONIOENCODING=utf-8 && `"$uv`" run python -m etl omo"
foreach ($t in @(@("dlck-omo-1130", "11:30"), @("dlck-omo-1530", "15:30"),
                 @("dlck-omo-1800", "18:00"), @("dlck-omo-2130", "21:30"))) {
    schtasks /Create /F /TN $t[0] /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST $t[1] `
        /TR "cmd /c $omoCmd >> `"$repo\..\dlck-runtime\logs\omo.log`" 2>&1"
}
$ingCmd = "cd /d `"$backend`" && set PYTHONIOENCODING=utf-8 && `"$uv`" run python -m ingester"
schtasks /Create /F /TN "dlck-ingester" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 08:30 `
    /TR "cmd /c $ingCmd >> `"$repo\..\dlck-runtime\logs\ingester-task.log`" 2>&1"
Write-Host "Đã đăng ký 5 task. GHI CHÚ: task dlck-ingester chỉ được bật SAU gate phiên đo (spec §3.5)."
```

⚠️ Đăng ký 4 task OMO ngay; task `dlck-ingester` tạo nhưng **Disable** (`schtasks /Change /TN dlck-ingester /DISABLE`) cho tới khi gate AC3 chốt.

- [ ] `backend/README.md`: mục "Chạy ingester" (3 chế độ + gate đo) và "Job OMO" (lệnh, lịch, env cần) — ngắn, trỏ spec.
- [ ] **Chạy thật OMO một lần** (`uv run python -m etl omo`), kiểm bằng SQL 4 nơi (session/auction/staging/etl_run) → AC5. Chạy lại lần hai → skip. Dán output vào `ledger.md`.
- [ ] **Smoke AC2** (ngoài giờ giao dịch): `uv run python -m ingester --measure --minutes 2` → nối thật, ack về, file JSONL sinh ra (0 frame dữ liệu ngoài giờ là hợp lệ). Dán output vào ledger.
- [ ] Bật compose profile realtime nếu CH dev chưa chạy; `python -m core.ch_migrate status` xác nhận `0002_rt_schema`.
- [ ] Commit: `git commit -m "chore: env, task scheduler registration, backend README for slice"`

---

### Task 18: quét tài liệu sống (checklist spec §9) + tự rà

- [ ] `docs/90-records/README.md`: thêm dòng plan này; thêm dòng còn thiếu cho `2026-08-25-clickhouse-realtime-store` (✅ xong); sửa dòng `postgres-data-schema` → ✅ xong (đối chiếu roadmap §5.2).
- [ ] `roadmap.md`: §0 dòng "Code sản phẩm" → 🟡 đang chạy lát cắt (trỏ hồ sơ này); §2 việc [4] ghi chú trạng thái (code xong, chờ phiên đo); KHÔNG đánh ✅ khi AC3/AC4 chưa qua.
- [ ] Tự rà chéo: `git grep -n "rt:state:\|rt:pub:\|CLICKHOUSE_INGESTER_URL\|ETL_DATABASE_URL"` — mọi hit nhất quán với spec §3.4/§5; `git grep -n "python -m etl"` — compose `deploy/app` vẫn chạy heartbeat mặc định.
- [ ] `uv run pytest tests -v` toàn backend lần cuối, dán tổng vào ledger (AC1).
- [ ] Commit: `git commit -m "docs: living-docs sweep for ingester+omo slice"`

---

### Task 19 **[gate — chủ dự án + controller]**: phiên đo → chốt luật → bật ghi thật

Không giao subagent; phụ thuộc giờ giao dịch (08:45–15:00, phái sinh từ 08:45).

- [ ] Phiên giao dịch kế tiếp: chạy `uv run python -m ingester --measure` trọn 08:40–15:05 (AC3 bước 1).
- [ ] Phân tích offline file frame (script phân tích để ở scratchpad; kết quả vào báo cáo): trả lời đủ 5 câu spec §3.5.2 (SM · topic phái sinh · phút idx/t · khoá lạ + CV==P1 · tải; và `pth`).
- [ ] Viết `docs/90-records/surveys/<ngày>-bvsc-realtime-session/README.md`; cập nhật `11-bvsc-realtime.md` + `roadmap.md` §5.1 (kèm ngày đo).
- [ ] Chủ dự án duyệt luật SM/dedup → ghi quyết định vào `ledger.md`. Nếu luật mới ≠ hash-nội-dung thì sửa `dedup.py` bằng vòng TDD mới trước khi bật.
- [ ] Bật task `dlck-ingester` (`schtasks /Change /TN dlck-ingester /ENABLE`). Phiên kế tiếp chạy thật; cuối phiên kiểm AC4 (5 bảng + nến + đối chứng + log); bắt đầu điền "danh sách đo tuần đầu" vào spec ClickHouse §10.
- [ ] *(Tuỳ chọn, quyết định #10 spec)*: nạp lại frame phiên đo qua đường writer trước phiên ghi thật đầu tiên.
- [ ] Cập nhật `roadmap.md` §0/§2 khi AC4 qua; commit từng mốc.

---

## Self-review (đã chạy khi viết plan)

- **Phủ spec:** §2.1→T16 · §3.1→T9/T16 · §3.2→T12 · §3.3→T10 · §3.4→T13 · §3.5→T15/T19 · §3.6→T13 · §3.7→T15 · §3.8→T17 · §4.1→T3 · §4.2→T4/T5 · §4.3→T6 · §4.4→T7 · §4.5→T17 · §5→T1/T9/T17 · §6 (bảng seam)→T3–T16 · §7 AC→T17/T18/T19 · §9→T18.
- **Nhất quán kiểu:** `Normalized`/`Metrics`/`COLUMNS` định nghĩa một lần ở T10, T14/T13/T16 tiêu thụ đúng tên; `run(mode, minutes, out, d)` thống nhất giữa `main.py` và `__main__.py`.
- **Điểm ngỏ có chủ đích:** selector parser OMO chỉnh theo fixture thật (T4 đứng trước T5); phân loại transient/tất định của clickhouse-connect tinh chỉnh khi chạy T14 trên lỗi thật — luật xử lý thì cố định.
