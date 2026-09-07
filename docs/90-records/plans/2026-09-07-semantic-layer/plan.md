# Lát 10 — tầng ngữ nghĩa: plan thực thi

> **Cho người/agent thực thi:** dùng skill `superpowers:subagent-driven-development`. Mỗi task một subagent mới (**model `sonnet`**, không bao giờ Haiku/Fable), TDD trong từng task, review trước khi nhận.

**Mục tiêu:** dựng 9 function đọc kho + một vòng chat terminal, đủ để chạy bộ hồi quy vòng 7 và biết skill có chịu được function calling hay không.

**Kiến trúc:** `backend/agent/` là lõi dùng chung. Vòng chat dùng `client.beta.messages.tool_runner` của SDK `anthropic` nhưng **lặp tay** để chen được câu nhắc vào lượt `tool_result`. Mỗi function là closure ôm `read_engine`, tự mở/đóng kết nối, trả **chuỗi JSON**. Đường đọc chạy dưới role `dlck_api`; sổ `ops.llm_call` đi bằng kết nối thứ hai dưới `dlck_etl`.

**Stack:** Python 3.12 · `uv` · SQLAlchemy 2 · psycopg 3 · `anthropic==1.4.0` (base_url MiniMax) · pytest.

**Spec:** [`spec.md`](spec.md) — đọc trước. Bộ hồi quy: [`regression-round7.md`](regression-round7.md).

## Ràng buộc toàn cục

Áp cho **mọi** task, không nhắc lại trong từng task:

- **Không thêm migration nào.** Head giữ nguyên `0020`.
- **Mọi SQL qualify đủ `schema.object`**, không dựa `search_path`. Extension nằm ở schema `extensions`: viết `extensions.similarity(...)`, `OPERATOR(extensions.%)`.
- **Mọi tham số tuỳ chọn của tool phải có giá trị mặc định** (mảng `= []`, vô hướng `= None`). Không có default là rơi vào `required` — bẫy đã đo.
- **Mọi tool trả `str`** qua `to_json()`. Trả `dict` sinh `tool_result.content` không hợp lệ.
- **Không giữ kết nối/giao dịch bắc qua một lời gọi model.** Mỗi tool tự `with engine.connect() as conn:` rồi đóng.
- **Không bao giờ in giá trị biến môi trường** ra output hay ghi vào file ngoài `.env`.
- Test đặt ở `backend/tests/agent/`, đặt tên `test_aNN_*.py`. Chạy: `uv run --project backend pytest -q`. Cần biến `TEST_DATABASE_URL` (đã có trong `.env`).
- Expected trong test là **hằng số literal** kèm ngày đo + câu SQL đã dùng, ghi trong docstring. SQL lấy expected phải đi **đường khác** đường của hàm; không được thì ghi rõ *"cùng đường, chỉ là chốt hồi quy"*.
- Commit theo mốc, Conventional Commits, message tiếng Anh, kết bằng `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- Nhánh: `feat/semantic-layer`. Không commit thẳng `main`.

### 🔴 Dữ liệu test — sửa plan 2026-09-07 sau khi chạy Task 4

Bản đầu của plan giả định test tool đọc được dữ liệu thật. **Sai**: `migrated_engine` dựng DB test **rỗng**, chỉ `market.industry` có sẵn 30 dòng do migration seed. Đọc kho dev thật thì tiêu chí trôi theo dữ liệu (ETL chạy là số đổi) — vi phạm §4.4.4.

⇒ Đã thêm fixture **`kho`** ở `backend/tests/agent/conftest.py`, seed một kho thu nhỏ tất định trong transaction của `db`. **Mọi test chạm DB phải nhận cả hai fixture: `def test_x(db, kho):`** — quên `kho` là bảng rỗng, test đỏ vô nghĩa.

Nội dung seed và các giá trị chốt để viết expected:

| Bảng | Nội dung |
|---|---|
| `market.security`/`issuer` | HPG (KIMLOAI) · VCB, TIN, HDB, LPB (NGANHANG) · FPT (CONGNGHE) · CUOI (`delisted`) · VNINDEX (`index`) |
| `market.metric_dictionary` | 21 mã trong bảng nhãn + `prf` (để test từ chối mã ngoài bảng) |
| `market.price_daily` | HPG: 2026-09-01 = 21.200 · 09-02 = 21.400 · **09-03 = 21.600** (`close_raw` = `close_adj`) |
| `market.financial_statement` | FPT 2024 `length_report=5` `IS`: `isa3` 62.848.794.351.367 · `isa9` −6.115.961.971.783 · `isa20` 9.427.422.530.444 · `isa22` 7.856.767.812.178 |
| `market.screener_daily` | phiên **2026-09-04**: HPG `rtd21` 7,89115654 / `rtq12` 0,17377625 · VCB 11,81676534 / 0,17922416 · TIN `rtq12` 0,73478649 · HDB 0,24836986 · LPB 0,2466187 · FPT 21,30 / 0,2647472 |
| `market.corporate_event` | FPT: 2 `CashDividend` (exright **2025-06-12**, **2025-12-01**) + 1 `AGM` 2025-03-10 |
| `macro` | `vn.cpi` đơn vị `%`: 2026-06 = 4,38 · 07 = 4,39 · **08 = 4,45** |
| `asset` | `wti` (`USD/thùng`, `price_type='futures'`): 09-04 = 90,57 · **09-05 = 91,22**; `btc` ở `ohlc_daily` |
| `news` | 3 bài: 2026-08-10 chứa **đúng cụm** "lãi suất điều hành" (sub `1b`) · 2026-08-20 chứa các từ đó **nằm rời** (sub `1a`) · 2026-09-02 chưa phân loại |

Bài tin thứ hai là chốt phân biệt `phraseto_tsquery` với `plainto_tsquery`: tìm theo **cụm** ra **1 bài**, tìm theo **từ khoá** ra **2 bài**.

### 🔴 Hai bẫy kỹ thuật gặp thật khi chạy Task 4

1. **`:p::jsonb` KHÔNG được SQLAlchemy nhận là bind param** — nó lặng lẽ bỏ tham số khỏi dict rồi ném `ProgrammingError` khó đọc. Viết `CAST(:p AS jsonb)`, `CAST(:d AS date)`. Áp cho mọi chỗ ép kiểu trên tham số.
2. **`asset.asset.calendar` chỉ nhận `'trading_days'` hoặc `'24x7'`**; `asset.price_daily.price_type` chỉ nhận `spot|futures|fixing|close`. `wti` là `futures`.

---

## Task 0 — Gỡ rủi ro lớn nhất trước khi xây gì

**Mục đích:** đóng giả định A1 và A2 của spec. Nếu MiniMax từ chối `tool_runner` (header `anthropic-beta`) hoặc từ chối schema `anyOf`, toàn bộ thiết kế vòng chat phải đổi — và phải biết **ngay bây giờ**.

**Files:** Create `<scratchpad>/spike_tool_runner.py` (**ngoài repo**, không commit).

- [ ] **Bước 1: Viết spike**

```python
import os, sys, json, traceback
sys.path.insert(0, "backend")
from core.env import load_dotenv
load_dotenv()
from core.llm.settings import LLMSettings
from core.llm.client import LLMClient
from anthropic import beta_tool

@beta_tool
def gia_dong_cua(ma: str, ngay: str | None = None) -> str:
    """Giá đóng cửa của một mã cổ phiếu Việt Nam. ma: mã 3 ký tự. ngay: YYYY-MM-DD, bỏ trống là phiên gần nhất."""
    return json.dumps({"ma": ma, "ngay": ngay or "2026-09-03", "gia": "21.600 đ"}, ensure_ascii=False)

print("SCHEMA:", json.dumps(gia_dong_cua.input_schema, ensure_ascii=False))

llm = LLMClient(LLMSettings.from_env())
try:
    runner = llm.raw.beta.messages.tool_runner(
        model=llm.settings.model, max_tokens=1500,
        system=[{"type": "text", "text": "Bạn là trợ lý chứng khoán Việt Nam. Trả lời ngắn."}],
        messages=[{"role": "user", "content": "Giá đóng cửa HPG phiên 2026-09-03 là bao nhiêu?"}],
        tools=[gia_dong_cua], thinking={"type": "adaptive"}, max_iterations=4,
    )
    calls = 0
    for message in runner:
        print("STOP:", message.stop_reason, "| usage:", message.usage)
        if message.stop_reason == "tool_use":
            resp = runner.generate_tool_call_response()
            calls += 1
            print("TOOL RESULT:", json.dumps(resp, ensure_ascii=False)[:400])
        else:
            print("TEXT:", "".join(b.text for b in message.content if b.type == "text")[:600])
    print("SO LUOT TOOL:", calls)
except Exception as e:
    print("LOI:", type(e).__name__)
    print("STATUS:", getattr(e, "status_code", None))
    print("BODY:", str(getattr(e, "body", None))[:1500])
    traceback.print_exc()
```

- [ ] **Bước 2: Chạy tiền cảnh** (job gọi model chạy nền bị đóng băng — G12)

Run: `PYTHONIOENCODING=utf-8 uv run --project backend python "<scratchpad>/spike_tool_runner.py"`

Expected khi ĐẠT: in ra `SCHEMA:` có `"ngay"` với `anyOf` hoặc `type: ["string","null"]`, rồi `STOP: tool_use`, `TOOL RESULT:` chứa `21.600 đ`, cuối cùng `STOP: end_turn` và câu trả lời tiếng Việt có số 21.600.

- [ ] **Bước 3: Ghi kết quả vào ledger**

Tạo `docs/90-records/plans/2026-09-07-semantic-layer/ledger.md`, mục "Task 0", dán **nguyên văn** output (cả `SCHEMA:`). Nếu hỏng: dán `STATUS` + `BODY` nguyên văn — đây là chỗ duy nhất phân biệt "MiniMax không chịu `tool_runner`" với "MiniMax không chịu một header".

- [ ] **Bước 4: Quyết định đường đi**

| Kết quả | Làm gì |
|---|---|
| Chạy thông | tiếp Task 1, thiết kế giữ nguyên |
| Lỗi 400 nhắc `anthropic-beta` | thử `extra_headers={"anthropic-beta": ""}`; vẫn hỏng ⇒ **DỪNG, báo người dùng** — phải đổi sang vòng lặp `messages.create` tay |
| Lỗi schema/`anyOf` | đổi mọi tham số tuỳ chọn từ `str \| None = None` sang `str = ""` và chạy lại; ghi vào ledger là ràng buộc mới |

- [ ] **Bước 5: Commit ledger**

```bash
git add docs/90-records/plans/2026-09-07-semantic-layer/ledger.md
git commit -m "docs(agent): task 0 spike — tool_runner against MiniMax, raw output recorded"
```

---

## Task 1 — Kết nối DB dưới role `dlck_api` và chốt chặn khởi động

**Files:**
- Create: `backend/agent/__init__.py`, `backend/agent/db.py`
- Create: `backend/tests/agent/test_a01_db.py`
- Modify: `.env` (thêm `AGENT_DATABASE_URL`), `database/README.md`

**Interfaces — Produces:**
```python
def assert_read_only(conn: sqlalchemy.Connection) -> None   # raise RuntimeError nếu sai quyền
def read_engine() -> sqlalchemy.Engine                      # AGENT_DATABASE_URL, đã assert_read_only
def ops_engine() -> sqlalchemy.Engine                       # ETL_DATABASE_URL, chỉ để ghi ops.llm_call
```

- [ ] **Bước 1: Tạo user Postgres `agent_reader`**

Chạy script sau (sinh mật khẩu ngẫu nhiên, ghi thẳng `.env`, **không in giá trị**):

```python
# <scratchpad>/make_agent_user.py
import os, re, secrets, sys, urllib.parse
sys.path.insert(0, "backend")
from core.env import load_dotenv
load_dotenv()
import sqlalchemy as sa

pw = secrets.token_urlsafe(24)
e = sa.create_engine(os.environ["DATA_DATABASE_URL"], isolation_level="AUTOCOMMIT")
with e.connect() as c:
    c.execute(sa.text("DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='agent_reader') "
                      "THEN CREATE ROLE agent_reader LOGIN IN ROLE dlck_api; END IF; END $$"))
    c.execute(sa.text(f"ALTER ROLE agent_reader PASSWORD :pw").bindparams(pw=pw))
url = os.environ["DATA_DATABASE_URL"]
new = re.sub(r"//[^@]+@", "//agent_reader:" + urllib.parse.quote(pw, safe="") + "@", url, count=1)
p = ".env"
txt = open(p, encoding="utf-8").read()
if "AGENT_DATABASE_URL=" not in txt:
    open(p, "a", encoding="utf-8").write(("" if txt.endswith("\n") else "\n") + "AGENT_DATABASE_URL=" + new + "\n")
print("xong — da ghi AGENT_DATABASE_URL vao .env (khong in gia tri)")
```

Run: `PYTHONIOENCODING=utf-8 uv run --project backend python "<scratchpad>/make_agent_user.py"`
Expected: `xong — da ghi AGENT_DATABASE_URL vao .env (khong in gia tri)`

Kiểm không lộ khoá: `grep -c "AGENT_DATABASE_URL" .env` → `1`; và `git status --short` **không** thấy `.env` (đã `.gitignore`).

- [ ] **Bước 2: Viết test đỏ**

```python
# backend/tests/agent/test_a01_db.py
"""Seam S1 — đường đọc phải chạy dưới role dlck_api và KHÔNG ghi được.

CLAUDE.md §3.5 ca thứ ba: hỏng ở đường KHỞI ĐỘNG thì hỏng toàn bộ. assert_read_only()
là chốt chặn khởi động, nên nó phải được test dưới đúng quyền production.
"""
import pytest
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError

from agent.db import assert_read_only


def test_assert_read_only_passes_under_dlck_api(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert_read_only(db)          # không ném


def test_assert_read_only_rejects_a_writer(db):
    # role mặc định của fixture là owner — ghi được ⇒ phải bị từ chối
    with pytest.raises(RuntimeError) as err:
        assert_read_only(db)
    assert "dlck_api" in str(err.value)


def test_dlck_api_cannot_insert(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    with pytest.raises(ProgrammingError):
        db.execute(sa.text("INSERT INTO market.industry (code, name_vi, level) VALUES ('XX', 'x', 1)"))


def test_dlck_api_can_read_the_three_views(db):
    """Ba view mà tầng ngữ nghĩa đi qua — thiếu quyền một cái là hỏng một function."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    for obj in ("market.v_issuer_industry", "market.price_factor", "macro.observation_spliced"):
        db.execute(sa.text(f"SELECT 1 FROM {obj} LIMIT 1"))
```

- [ ] **Bước 3: Chạy để thấy đỏ**

Run: `uv run --project backend pytest tests/agent/test_a01_db.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent.db'`

- [ ] **Bước 4: Viết `backend/agent/db.py`**

```python
"""Hai đường DB của tầng ngữ nghĩa.

Đường ĐỌC chạy dưới role dlck_api (chỉ SELECT trên market/macro/asset/news). Đường GHI SỔ
dùng lại ETL_DATABASE_URL vì dlck_api không có quyền gì trên schema ops — cố ý, để dlck_api
giữ đúng hợp đồng "chỉ đọc" (spec §4.7).
"""
from __future__ import annotations

import os

import sqlalchemy as sa


def assert_read_only(conn: sa.Connection) -> None:
    """Chốt chặn KHỞI ĐỘNG: kết nối này phải là dlck_api và phải không ghi được.

    Không kiểm bằng current_user — current_role là đồng nghĩa của current_user, tư cách
    thành viên role không đổi nó, nên phải hỏi pg_has_role và hỏi thẳng quyền INSERT.
    """
    is_member, can_insert = conn.execute(sa.text(
        "SELECT pg_has_role(current_user, 'dlck_api', 'member'),"
        "       has_table_privilege('market.security', 'INSERT')"
    )).one()
    if not is_member:
        raise RuntimeError("ket noi doc khong thuoc role dlck_api")
    if can_insert:
        raise RuntimeError("ket noi doc con quyen INSERT — sai role, khong phai dlck_api thuan doc")


def _engine(var: str) -> sa.Engine:
    url = os.environ.get(var)
    if not url:
        raise RuntimeError(f"thieu {var}")
    return sa.create_engine(url, pool_pre_ping=True)


def read_engine() -> sa.Engine:
    eng = _engine("AGENT_DATABASE_URL")
    with eng.connect() as conn:
        assert_read_only(conn)
    return eng


def ops_engine() -> sa.Engine:
    return _engine("ETL_DATABASE_URL")
```

- [ ] **Bước 5: Chạy để thấy xanh**

Run: `uv run --project backend pytest tests/agent/test_a01_db.py -q`
Expected: `4 passed`

- [ ] **Bước 6: Kiểm đường khởi động thật dưới credential production**

```python
# <scratchpad>/check_agent_conn.py
import os, sys
sys.path.insert(0, "backend")
from core.env import load_dotenv; load_dotenv()
from agent.db import read_engine
eng = read_engine()
import sqlalchemy as sa
with eng.connect() as c:
    print("doc duoc:", c.execute(sa.text("SELECT count(*) FROM market.security")).scalar())
print("assert_read_only da chay va qua")
```
Run: `PYTHONIOENCODING=utf-8 uv run --project backend python "<scratchpad>/check_agent_conn.py"`
Expected: `doc duoc: 2017` (hoặc số lớn hơn) rồi `assert_read_only da chay va qua`. Dán vào ledger — đây là AC3.

- [ ] **Bước 7: Cập nhật `database/README.md`**

Trong mục "User login thật tạo per-môi-trường, ngoài migration", thêm dòng thứ hai cạnh `etl_worker`:

```sql
CREATE USER agent_reader LOGIN PASSWORD '…' IN ROLE dlck_api;   -- tầng ngữ nghĩa lát 10, biến AGENT_DATABASE_URL
```

- [ ] **Bước 8: Commit**

```bash
git add backend/agent/__init__.py backend/agent/db.py backend/tests/agent/test_a01_db.py database/README.md
git commit -m "feat(agent): read path under dlck_api with a startup read-only assertion"
```

---

## Task 2 — Trình bày số: `format.py` và bảng nhãn đóng `labels.py`

**Files:**
- Create: `backend/agent/format.py`, `backend/agent/labels.py`
- Create: `backend/tests/agent/test_a02_format.py`

**Interfaces — Produces:**
```python
LABELS: dict[str, str]                                  # 21 mã → nhãn hiển thị
def label_for(code: str) -> str | None                  # None nếu ngoài bảng
def display_metric(value, unit: str | None) -> str | None      # đơn vị của metric_dictionary
def display_series_value(value, unit: str | None) -> str | None # đơn vị macro/asset (văn bản tự do)
def format_date_vi(d) -> str                            # date → "03/09/2026"
```

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/agent/test_a02_format.py
"""Seam S2 — quy đổi đơn vị.

Hai họ đơn vị KHÁC NHAU dùng chung ký hiệu '%': metric_dictionary có 'ty_le_thap_phan'
(giá trị thập phân, PHẢI nhân 100) còn macro/asset có '%' (đã là phần trăm, KHÔNG nhân).
Hai ca dưới đây cố tình đặt cạnh nhau — đó là chốt chống lỗi sai 100 lần.

Giá trị lấy từ kho ngày 2026-09-07:
  0.17377625  = ROE (TTM) của HPG, screener_daily 2026-09-04
  4.45        = macro.observation vn.cpi obs_date 2026-08-01
  62848794351367 = financial_statement FPT isa3 2024 (length_report=5)
  -6115961971783 = financial_statement FPT isa9 2024 — chi phí bán hàng, ÂM trong kho
"""
import datetime as dt

from agent.format import display_metric, display_series_value, format_date_vi
from agent.labels import label_for


def test_ty_le_thap_phan_nhan_100():
    assert display_metric(0.17377625, "ty_le_thap_phan") == "17,38%"


def test_phan_tram_cua_macro_khong_nhan_100():
    assert display_series_value(4.45, "%") == "4,45%"


def test_vnd_quy_ty():
    assert display_metric(62848794351367, "VND") == "62.848,8 tỷ VND"


def test_vnd_am_van_quy_ty_va_giu_dau():
    assert display_metric(-6115961971783, "VND") == "-6.116,0 tỷ VND"


def test_vnd_nho_hon_mot_ty_thi_de_dong():
    assert display_metric(21600, "VND") == "21.600 đ"


def test_lan_va_vnd_tren_cp():
    assert display_metric(7.89115654, "lan") == "7,89 lần"
    assert display_metric(2749.91376474, "VND/CP") == "2.750 đ/cp"


def test_unit_null_thi_loai():
    assert display_metric(123, None) is None


def test_gia_tri_none_thi_none():
    assert display_metric(None, "VND") is None


def test_don_vi_la_thi_giu_nguyen_van():
    assert display_series_value(91.22, "USD/thùng") == "91,22 USD/thùng"
    assert display_series_value(1234567, "người") == "1.234.567 người"


def test_ngay_kieu_viet():
    assert format_date_vi(dt.date(2026, 9, 3)) == "03/09/2026"


def test_bang_nhan_tach_duoc_hai_ma_trung_ten():
    """isa20 và isa22 trong nguồn CÙNG tên 'LỢI NHUẬN THUẦN' — bảng nhãn phải tách được."""
    assert label_for("isa22") == "Lợi nhuận sau thuế của cổ đông công ty mẹ"
    assert label_for("isa20") == "Lợi nhuận sau thuế (toàn bộ)"
    assert label_for("isa22") != label_for("isa20")


def test_ma_ngoai_bang_thi_none():
    assert label_for("prf") is None      # tên nói "tỉ đồng" nhưng unit='VND' — cố ý loại
    assert label_for("khong_ton_tai") is None
```

- [ ] **Bước 2: Chạy để thấy đỏ**

Run: `uv run --project backend pytest tests/agent/test_a02_format.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent.format'`

- [ ] **Bước 3: Viết `labels.py`**

```python
"""Bảng nhãn ĐÓNG cho tập chỉ tiêu tầng ngữ nghĩa phơi ra model.

Vì sao không tra thẳng metric_dictionary.name_vi: tên KHÔNG duy nhất (đo 2026-09-07) —
isa20 và isa22 cùng tên "LỢI NHUẬN THUẦN" nhưng khác giá trị, BVPS có 3 mã, "Giá trị hao
mòn lũy kế" có 4 mã. Đơn vị vẫn đọc từ metric_dictionary.unit (nguồn sự thật về đơn vị);
bảng này chỉ quyết TÊN HIỂN THỊ. Mã ngoài bảng bị từ chối, kèm danh sách mã hợp lệ.
"""
from __future__ import annotations

LABELS: dict[str, str] = {
    # Kết quả kinh doanh
    "isa3": "Doanh thu thuần",
    "isa9": "Chi phí bán hàng",
    "isa10": "Chi phí quản lý doanh nghiệp",
    "isa16": "Lợi nhuận trước thuế",
    "isa20": "Lợi nhuận sau thuế (toàn bộ)",
    "isa22": "Lợi nhuận sau thuế của cổ đông công ty mẹ",
    "isa23": "Lãi cơ bản trên cổ phiếu (EPS)",
    # Cân đối kế toán
    "bsa1": "Tài sản ngắn hạn",
    "bsa2": "Tiền và tương đương tiền",
    "bsa53": "Tổng tài sản",
    "bsa54": "Nợ phải trả",
    "bsa78": "Vốn chủ sở hữu",
    "bsa96": "Tổng nguồn vốn",
    # Lưu chuyển tiền tệ
    "cfa18": "Lưu chuyển tiền thuần từ hoạt động kinh doanh",
    # Tỷ số thị trường
    "rtd11": "Vốn hoá thị trường",
    "rtd14": "EPS (TTM)",
    "rtd21": "P/E (TTM)",
    "rtd25": "P/B (TTM)",
    "rtd7": "Giá trị sổ sách mỗi cổ phiếu (BVPS, TTM)",
    "rtq12": "ROE (TTM)",
    "rtq14": "ROA (TTM)",
}

DEFAULT_BY_STATEMENT = {
    "IS": ["isa3", "isa9", "isa10", "isa16", "isa20", "isa22", "isa23"],
    "BS": ["bsa1", "bsa2", "bsa53", "bsa54", "bsa78", "bsa96"],
    "CF": ["cfa18"],
}
DEFAULT_RATIOS = ["rtd11", "rtd14", "rtd21", "rtd25", "rtd7", "rtq12", "rtq14"]


def label_for(code: str) -> str | None:
    return LABELS.get(code)
```

- [ ] **Bước 4: Viết `format.py`**

```python
"""Quy đổi số sang chuỗi người đọc được. Hàm thuần, không chạm DB.

HAI HỌ ĐƠN VỊ, đừng trộn:
  metric_dictionary.unit ∈ {VND, ty_le_thap_phan, lan, VND/CP, co_phieu, so_luong, NULL}
  macro.indicator.unit / asset.asset.unit là VĂN BẢN TỰ DO: %, USD/thùng, điểm, người…
'ty_le_thap_phan' phải NHÂN 100; '%' thì KHÔNG. Đây là chỗ dễ sai 100 lần nhất của lát.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

TY = Decimal(10) ** 9


def _num(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _group(n: Decimal, places: int = 0) -> str:
    """1234567.8 -> '1.234.567,8' (dấu chấm phân nhóm, phẩy thập phân — kiểu Việt)."""
    q = f"{n:,.{places}f}"
    return q.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _tien(n: Decimal, ky_hieu: str) -> str:
    if abs(n) >= TY:                       # so sánh theo TRỊ TUYỆT ĐỐI, giữ dấu ở kết quả
        return f"{_group(n / TY, 1)} tỷ {ky_hieu}"
    return f"{_group(n, 0)} đ" if ky_hieu == "VND" else f"{_group(n, 0)} {ky_hieu}"


def display_metric(value, unit: str | None) -> str | None:
    n = _num(value)
    if n is None or unit is None:
        return None
    if unit == "VND":
        return _tien(n, "VND")
    if unit == "ty_le_thap_phan":
        return f"{_group(n * 100, 2)}%"
    if unit == "lan":
        return f"{_group(n, 2)} lần"
    if unit == "VND/CP":
        return f"{_group(n, 0)} đ/cp"
    if unit == "co_phieu":
        return f"{_group(n, 0)} cp"
    if unit == "so_luong":
        return f"{_group(n, 0)}"
    return f"{_group(n, 2)} {unit}"


def display_series_value(value, unit: str | None) -> str | None:
    """Đơn vị của macro/asset — văn bản tự do, KHÔNG nhân 100 cho '%'."""
    n = _num(value)
    if n is None:
        return None
    if unit is None:
        return _group(n, 2)
    if unit == "%":
        return f"{_group(n, 2)}%"
    if unit in ("VND", "USD"):
        return _tien(n, unit)
    if n == n.to_integral_value():
        return f"{_group(n, 0)} {unit}"
    return f"{_group(n, 2)} {unit}"


def format_date_vi(d: dt.date | dt.datetime) -> str:
    return d.strftime("%d/%m/%Y")
```

- [ ] **Bước 5: Chạy để thấy xanh**

Run: `uv run --project backend pytest tests/agent/test_a02_format.py -q`
Expected: `12 passed`

- [ ] **Bước 6: Commit**

```bash
git add backend/agent/format.py backend/agent/labels.py backend/tests/agent/test_a02_format.py
git commit -m "feat(agent): unit formatting and a closed label table for exposed metrics"
```

---

## Task 3 — System prompt và nạp skill L1

**Files:**
- Create: `backend/agent/skills.py`, `backend/agent/system_prompt.py`
- Create: `backend/tests/agent/test_a03_system_prompt.py`

**Interfaces — Produces:**
```python
L2_TOPICS: dict[str, pathlib.Path]        # 9 khoá → đường dẫn file L2
def load_l1() -> str                      # SKILL.md + 4 references, nối theo thứ tự cố định
def load_l2(topic: str) -> str            # raise KeyError nếu topic ngoài bảng
SCOPE_GUARD: str
def build_system_blocks() -> list[dict]   # [{type:text,text:SCOPE_GUARD}, {type:text,text:L1}]
```

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/agent/test_a03_system_prompt.py
"""Seam S3 và S5 — thứ tự tri thức và cửa đọc L2.

Lỗ hổng phạm vi đo được ở vòng 5 test skill: 3/4 câu ngoài lĩnh vực vẫn được trả lời đầy đủ,
vì luật "chỉ trả lời chứng khoán" nằm TRONG thân SKILL.md, chỉ đọc được SAU khi skill tải.
Bản vá là đoạn văn nguyên văn ở docs/30-skills/maintenance.md §7, phải nằm ở system prompt.
"""
import pytest

from agent.skills import L2_TOPICS, load_l1, load_l2
from agent.system_prompt import SCOPE_GUARD, build_system_blocks


def test_scope_guard_chep_nguyen_van_tu_maintenance():
    assert "chỉ trả lời trong lĩnh vực chứng khoán, tài chính và kinh tế" in SCOPE_GUARD
    assert "nửa trong nửa ngoài" in SCOPE_GUARD


def test_block_dau_tien_la_scope_guard():
    blocks = build_system_blocks()
    assert len(blocks) == 2
    assert blocks[0]["text"] == SCOPE_GUARD


def test_block_thu_hai_la_l1_tron_ven_khong_lan_l2():
    l1 = build_system_blocks()[1]["text"]
    assert "# Chuyên gia phân tích chứng khoán Việt Nam" in l1 or l1.startswith("---")
    assert "analysis-framework" in l1        # tiêu đề phân cách của file reference
    assert "writing-style" in l1
    assert "valuation" not in l1.lower()     # L2 KHÔNG được lọt vào system


def test_l1_du_do_dai_da_do():
    """61.240 ký tự nội dung 5 file (đo 2026-09-07); nối thêm tiêu đề phân cách nên lớn hơn."""
    assert len(load_l1()) >= 61_240


def test_l2_du_chin_chu_de():
    assert len(L2_TOPICS) == 9
    assert "valuation" in L2_TOPICS and "financial-statements" in L2_TOPICS


def test_l2_tra_dung_noi_dung():
    assert "FCFF" in load_l2("valuation")


def test_l2_tu_choi_path_traversal():
    with pytest.raises(KeyError):
        load_l2("../../../etc/passwd")
    with pytest.raises(KeyError):
        load_l2("valuation.md")
```

- [ ] **Bước 2: Chạy để thấy đỏ**

Run: `uv run --project backend pytest tests/agent/test_a03_system_prompt.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent.skills'`

- [ ] **Bước 3: Viết `skills.py`**

```python
"""Nạp tri thức skill từ đĩa.

L1 (vn-stock-advisor) nạp TRỌN lúc khởi động và đi vào system prompt — nó quyết định HÌNH DẠNG
câu trả lời nên phải có mặt trước mọi tool_result. L2 (vn-stock-knowledge) nạp THEO NHU CẦU qua
function, vì trọn bộ là 243.545 ký tự ≈ 150k token.

Bảng L2_TOPICS là dict HẰNG: topic tra thẳng ra Path, không nối chuỗi từ đầu vào ⇒ path
traversal không khả dĩ về mặt cấu trúc.
"""
from __future__ import annotations

from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent / "skills"
L1_DIR = SKILLS_DIR / "vn-stock-advisor"
L2_DIR = SKILLS_DIR / "vn-stock-knowledge"

L1_FILES = [
    L1_DIR / "SKILL.md",
    L1_DIR / "references" / "analysis-framework.md",
    L1_DIR / "references" / "market-behavior.md",
    L1_DIR / "references" / "reasoning.md",
    L1_DIR / "references" / "writing-style.md",
]

L2_TOPICS: dict[str, Path] = {
    "tong-quan": L2_DIR / "SKILL.md",
    "advanced": L2_DIR / "references" / "advanced.md",
    "financial-statements": L2_DIR / "references" / "financial-statements.md",
    "macro-money-creation": L2_DIR / "references" / "macro-money-creation.md",
    "portfolio-and-rotation": L2_DIR / "references" / "portfolio-and-rotation.md",
    "psychology-information": L2_DIR / "references" / "psychology-information.md",
    "technical-indicators": L2_DIR / "references" / "technical-indicators.md",
    "technical-supply-demand": L2_DIR / "references" / "technical-supply-demand.md",
    "valuation": L2_DIR / "references" / "valuation.md",
}


def load_l1() -> str:
    """Thiếu file thì chết ngay — thà không chạy còn hơn chạy với skill khuyết."""
    parts = []
    for p in L1_FILES:
        if not p.is_file():
            raise RuntimeError(f"thieu file skill L1: {p.name}")
        parts.append(f"\n\n===== {p.stem} =====\n\n" + p.read_text(encoding="utf-8"))
    return "".join(parts).strip()


def load_l2(topic: str) -> str:
    path = L2_TOPICS[topic]          # KeyError cho mọi thứ ngoài 9 khoá — đúng ý
    return path.read_text(encoding="utf-8")
```

- [ ] **Bước 4: Viết `system_prompt.py`**

`SCOPE_GUARD` chép **nguyên văn** ba đoạn trích dẫn trong `docs/30-skills/maintenance.md §7` (đoạn bắt đầu "Bạn chỉ trả lời trong lĩnh vực chứng khoán…"). Không diễn giải lại, không rút gọn.

```python
"""System prompt — tầng 1 của luật phân định: quyết định CÓ trả lời hay không.

SCOPE_GUARD vá lỗ hổng đo được ở vòng 5: luật phạm vi nằm trong thân SKILL.md chỉ đọc được
sau khi skill tải, mà câu ngoài phạm vi thì không kích hoạt skill nào ⇒ 3/4 câu ngoài lĩnh
vực vẫn được trả lời đầy đủ. Nguyên văn: docs/30-skills/maintenance.md §7.
"""
from __future__ import annotations

from agent.skills import load_l1

SCOPE_GUARD = """Bạn chỉ trả lời trong lĩnh vực chứng khoán, tài chính và kinh tế: thị trường và cổ phiếu, doanh nghiệp niêm yết, vĩ mô, chính sách tiền tệ và tài khoá, các loại tài sản tài chính và quan hệ giữa chúng.

Câu hỏi ngoài lĩnh vực đó — sức khoẻ, pháp lý, lập trình, ẩm thực, đời tư, kiến thức phổ thông — từ chối gọn trong một câu, nói rõ bạn chỉ làm mảng này, rồi dừng. Không giải thích dài, không xin lỗi, không đưa lời khuyên thay thế, và không lái ngược về chứng khoán cho có việc.

Câu nửa trong nửa ngoài: trả lời phần thuộc lĩnh vực, nói một câu rằng phần còn lại không thuộc chỗ mình."""

_L1_CACHE: str | None = None


def build_system_blocks() -> list[dict]:
    global _L1_CACHE
    if _L1_CACHE is None:
        _L1_CACHE = load_l1()
    return [
        {"type": "text", "text": SCOPE_GUARD},
        {"type": "text", "text": _L1_CACHE},
    ]
```

- [ ] **Bước 5: Chạy để thấy xanh**

Run: `uv run --project backend pytest tests/agent/test_a03_system_prompt.py -q`
Expected: `7 passed`. Nếu `test_block_thu_hai_la_l1_tron_ven_khong_lan_l2` đỏ ở dòng kiểm tiêu đề, mở `backend/agent/skills/vn-stock-advisor/SKILL.md` đọc **dòng H1 thật** rồi sửa **test** cho khớp — không sửa skill.

- [ ] **Bước 6: Commit**

```bash
git add backend/agent/skills.py backend/agent/system_prompt.py backend/tests/agent/test_a03_system_prompt.py
git commit -m "feat(agent): scope guard in system prompt, L1 always loaded, L2 behind a closed topic table"
```

---

## Task 4 — Khuôn dùng chung và function đọc tri thức

**Files:**
- Create: `backend/agent/tools/__init__.py`, `backend/agent/tools/_shared.py`
- Create: `backend/tests/agent/test_a04_shared.py`

**Interfaces — Produces:**
```python
def to_json(payload: dict) -> str                    # ensure_ascii=False
def cap_limit(limit: int | None, mac_dinh: int, tran: int) -> tuple[int, bool]
def khong_tim_thay(ma: str, goi_y: list[str]) -> dict
def khong_co_du_lieu(loai: str, ly_do: str) -> dict
def rong(khoang: dict | None) -> dict
def co_du_lieu(du_lieu: list, **extra) -> dict
def resolve_ticker(conn, ticker: str) -> dict         # {tim_thay, security_id, issuer_id, ticker, loai, trang_thai, goi_y}
```

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/agent/test_a04_shared.py
"""Seam — bốn khuôn trạng thái dữ liệu và phép tra mã.

Phân biệt "không tìm thấy mã" với "có mã nhưng kho không có loại dữ liệu này" là bắt buộc:
VN-Index có danh tính trong market.security nhưng KHÔNG có một điểm giá nào (đo 2026-09-07,
kiểm cả price_daily, index_stat_daily, asset.*, macro.*). Trộn hai ca này làm model bịa.
"""
import json

import sqlalchemy as sa

from agent.tools._shared import cap_limit, resolve_ticker, to_json


def test_to_json_giu_dau_tieng_viet():
    assert to_json({"ten": "Ngân hàng"}) == '{"ten": "Ngân hàng"}'
    assert isinstance(to_json({"a": 1}), str)


def test_cap_limit_cat_va_bao():
    assert cap_limit(None, 20, 50) == (20, False)
    assert cap_limit(10, 20, 50) == (10, False)
    assert cap_limit(500, 20, 50) == (50, True)


def test_resolve_ticker_ma_that(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    r = resolve_ticker(db, "hpg")               # chữ thường — phải chuẩn hoá
    assert r["tim_thay"] is True
    assert r["ticker"] == "HPG"
    assert r["loai"] == "stock"
    assert r["trang_thai"] == "listed"
    assert isinstance(r["issuer_id"], int)


def test_resolve_ticker_chi_so_van_tim_thay(db):
    """VNINDEX có danh tính nhưng không có giá — resolve phải nói tìm thấy, loại index."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    ma = db.execute(sa.text("SELECT ticker FROM market.security WHERE security_type='index' LIMIT 1")).scalar()
    r = resolve_ticker(db, ma)
    assert r["tim_thay"] is True
    assert r["loai"] == "index"


def test_resolve_ticker_ma_bia_thi_co_goi_y(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    r = resolve_ticker(db, "HPGX")
    assert r["tim_thay"] is False
    assert "HPG" in r["goi_y"]                 # trigram trên ticker
```

- [ ] **Bước 2: Chạy để thấy đỏ**

Run: `uv run --project backend pytest tests/agent/test_a04_shared.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent.tools'`

- [ ] **Bước 3: Viết `_shared.py`**

```python
"""Khuôn dùng chung cho 9 function.

BỐN hình dạng trạng thái dữ liệu, phân biệt bằng TRƯỜNG TƯỜNG MINH chứ không bằng độ dài
mảng — model không được phép nhầm "0 bản ghi" với "kho không có loại dữ liệu này".
"""
from __future__ import annotations

import json

import sqlalchemy as sa


def to_json(payload: dict) -> str:
    """SDK đặt NGUYÊN giá trị trả về vào tool_result.content và không kiểm kiểu ⇒ phải là str."""
    return json.dumps(payload, ensure_ascii=False, default=str)


def cap_limit(limit: int | None, mac_dinh: int, tran: int) -> tuple[int, bool]:
    if limit is None:
        return mac_dinh, False
    if limit > tran:
        return tran, True
    return max(1, limit), False


def khong_tim_thay(ma: str, goi_y: list[str]) -> dict:
    return {"tim_thay": False, "ma_da_tra": ma, "goi_y": goi_y}


def khong_co_du_lieu(loai: str, ly_do: str) -> dict:
    return {"tim_thay": True, "co_du_lieu": False, "loai": loai, "ly_do": ly_do}


def rong(khoang: dict | None = None) -> dict:
    out = {"tim_thay": True, "co_du_lieu": True, "so_dong": 0}
    if khoang:
        out["khoang_co_du_lieu"] = khoang
    return out


def co_du_lieu(du_lieu: list, **extra) -> dict:
    return {"tim_thay": True, "co_du_lieu": True, "so_dong": len(du_lieu), "du_lieu": du_lieu, **extra}


_SQL_TICKER = sa.text("""
    SELECT s.security_id, s.issuer_id, s.ticker, s.security_type, s.status, s.exchange
    FROM market.security s
    WHERE upper(s.ticker) = upper(:t)
    ORDER BY (s.status = 'listed') DESC, s.security_id
    LIMIT 1
""")

_SQL_GOI_Y = sa.text("""
    SELECT s.ticker
    FROM market.security s
    WHERE s.status = 'listed'
      AND (extensions.similarity(upper(s.ticker), upper(:t)) > 0.3
           OR extensions.similarity(coalesce(i.short_name, ''), :t) > 0.3)
    ORDER BY extensions.similarity(upper(s.ticker), upper(:t)) DESC
    LIMIT 5
""").columns(ticker=sa.String)


def resolve_ticker(conn: sa.Connection, ticker: str) -> dict:
    row = conn.execute(_SQL_TICKER, {"t": ticker}).first()
    if row is None:
        goi_y = [r[0] for r in conn.execute(sa.text("""
            SELECT s.ticker FROM market.security s
            LEFT JOIN market.issuer i USING (issuer_id)
            WHERE s.status = 'listed'
              AND (extensions.similarity(upper(s.ticker), upper(:t)) > 0.3
                   OR extensions.similarity(coalesce(i.short_name, ''), :t) > 0.3)
            ORDER BY extensions.similarity(upper(s.ticker), upper(:t)) DESC
            LIMIT 5"""), {"t": ticker})]
        return khong_tim_thay(ticker, goi_y)
    return {"tim_thay": True, "security_id": row.security_id, "issuer_id": row.issuer_id,
            "ticker": row.ticker, "loai": row.security_type, "trang_thai": row.status,
            "san": row.exchange}
```

*(Xoá `_SQL_GOI_Y` nếu không dùng — không để hằng mồ côi.)*

- [ ] **Bước 4: Chạy để thấy xanh**

Run: `uv run --project backend pytest tests/agent/test_a04_shared.py -q`
Expected: `5 passed`

- [ ] **Bước 5: Viết test đỏ cho function đọc tri thức**

```python
# thêm vào cuối backend/tests/agent/test_a04_shared.py
from agent.tools.load_knowledge_reference import doc_tri_thuc


def test_doc_tri_thuc_tra_chuoi_json_co_noi_dung():
    out = json.loads(doc_tri_thuc("valuation"))
    assert out["chu_de"] == "valuation"
    assert "FCFF" in out["noi_dung"]


def test_doc_tri_thuc_chu_de_la_thi_bao_loi_kem_danh_sach():
    out = json.loads(doc_tri_thuc("../../../etc/passwd"))
    assert out["loi"] is True
    assert "valuation" in out["chu_de_hop_le"]
```

- [ ] **Bước 6: Viết `load_knowledge_reference.py`**

```python
"""Function thứ 9 — cửa duy nhất để model đọc tri thức L2.

topic tra dict hằng L2_TOPICS; không nối chuỗi từ đầu vào nên path traversal không khả dĩ.
Chủ đề lạ trả LỖI CÓ CẤU TRÚC (không ném) để model tự sửa mà không phá vòng chat.
"""
from __future__ import annotations

from agent.skills import L2_TOPICS, load_l2
from agent.tools._shared import to_json


def doc_tri_thuc(topic: str) -> str:
    if topic not in L2_TOPICS:
        return to_json({"loi": True, "ly_do": f"khong co chu de '{topic}'",
                        "chu_de_hop_le": sorted(L2_TOPICS)})
    return to_json({"chu_de": topic, "noi_dung": load_l2(topic)})
```

- [ ] **Bước 7: Chạy để thấy xanh**

Run: `uv run --project backend pytest tests/agent/test_a04_shared.py -q`
Expected: `7 passed`

- [ ] **Bước 8: Commit**

```bash
git add backend/agent/tools/ backend/tests/agent/test_a04_shared.py
git commit -m "feat(agent): shared result shapes, ticker resolution, knowledge reference reader"
```

---

## Task 5 — `get_price_series`

**Files:** Create `backend/agent/tools/get_price_series.py`, `backend/tests/agent/test_a05_price.py`

**Interfaces — Consumes:** `_shared.resolve_ticker`, `_shared.co_du_lieu/khong_co_du_lieu/rong/to_json`, `format.format_date_vi`.
**Produces:** `def gia_theo_ngay(conn, ticker, from_date=None, to_date=None, adjusted=True) -> str`

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/agent/test_a05_price.py
"""Seam S4 — chuỗi giá.

Expected lấy 2026-09-07 bằng đường KHÁC đường của hàm (hàm join qua security_id; câu lấy
expected lọc thẳng theo ticker rồi đọc close_raw):
  SELECT p.close_raw FROM market.price_daily p JOIN market.security s USING(security_id)
  WHERE s.ticker='HPG' AND p.trading_date='2026-09-03'  ->  21600
Kho không có total_trading/total_trading_value (NULL 100% trên 1.115.219 dòng) nên hàm
KHÔNG trả khối lượng — test canh đúng điều đó để không ai lặng lẽ thêm cột rỗng.
"""
import json

import sqlalchemy as sa

from agent.tools.get_price_series import gia_theo_ngay


def test_gia_dong_cua_hpg_phien_2026_09_03(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(gia_theo_ngay(db, "HPG", "2026-09-03", "2026-09-03"))
    assert out["co_du_lieu"] is True
    assert out["so_dong"] == 1
    phien = out["du_lieu"][0]
    assert phien["dong_cua"] == "21.600 đ"
    assert phien["ngay"] == "2026-09-03"
    assert phien["ngay_hien_thi"] == "03/09/2026"
    assert "khoi_luong" not in phien


def test_chi_so_co_ma_nhung_khong_co_gia(db):
    """VN-Index: có danh tính, 0 điểm giá. Phải ra hình dạng #2, không phải mảng rỗng."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    ma = db.execute(sa.text("SELECT ticker FROM market.security WHERE security_type='index' LIMIT 1")).scalar()
    out = json.loads(gia_theo_ngay(db, ma))
    assert out["tim_thay"] is True
    assert out["co_du_lieu"] is False
    assert out["loai"] == "index"
    assert "chưa có" in out["ly_do"] or "khong co" in out["ly_do"]


def test_ma_khong_ton_tai(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(gia_theo_ngay(db, "ZZZZ"))
    assert out["tim_thay"] is False


def test_khoang_ngay_rong_van_bao_khoang_co_du_lieu(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(gia_theo_ngay(db, "HPG", "1999-01-01", "1999-12-31"))
    assert out["co_du_lieu"] is True and out["so_dong"] == 0
    assert out["khoang_co_du_lieu"]["den"] >= "2026-08-01"
```

- [ ] **Bước 2: Chạy để thấy đỏ** — Run: `uv run --project backend pytest tests/agent/test_a05_price.py -q` → `ModuleNotFoundError`

- [ ] **Bước 3: Viết implementation**

```python
"""Chuỗi giá theo ngày của một mã cổ phiếu.

Kho CHỈ có giá cổ phiếu: 1.523 mã, không có chỉ số, không có ETF (đo 2026-09-07). Mã đã huỷ
niêm yết cũng 0 dòng (0/442). Vì vậy mọi loại khác 'stock' ra hình dạng "có mã, không có dữ
liệu" — nói thẳng còn hơn để model đoán.
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import display_metric, format_date_vi
from agent.tools._shared import co_du_lieu, khong_co_du_lieu, khong_tim_thay, resolve_ticker, rong, to_json

_LY_DO = {"index": "kho chưa có dữ liệu giá cho chỉ số",
          "etf": "kho chưa có dữ liệu giá cho chứng chỉ quỹ ETF",
          "fund_cert": "kho chưa có dữ liệu giá cho chứng chỉ quỹ"}
TRAN_PHIEN = 400


def gia_theo_ngay(conn: sa.Connection, ticker: str, from_date: str | None = None,
                  to_date: str | None = None, adjusted: bool = True) -> str:
    ma = resolve_ticker(conn, ticker)
    if not ma["tim_thay"]:
        return to_json(ma)
    if ma["loai"] != "stock":
        return to_json({**khong_co_du_lieu(ma["loai"], _LY_DO.get(ma["loai"], "kho chưa có dữ liệu giá cho loại này")),
                        "ma": ma["ticker"]})
    if ma["trang_thai"] == "delisted":
        return to_json({**khong_co_du_lieu("stock", "mã đã huỷ niêm yết, kho chưa có giá lịch sử của mã huỷ"),
                        "ma": ma["ticker"], "trang_thai": "delisted"})

    cot = "close_adj" if adjusted else "close_raw"
    rows = conn.execute(sa.text(f"""
        SELECT trading_date, {cot} AS dong_cua, open_value, highest_value, lowest_value
        FROM market.price_daily
        WHERE security_id = :sid
          AND (:tu::date IS NULL OR trading_date >= :tu::date)
          AND (:den::date IS NULL OR trading_date <= :den::date)
        ORDER BY trading_date DESC
        LIMIT :lim
    """), {"sid": ma["security_id"], "tu": from_date, "den": to_date, "lim": TRAN_PHIEN}).all()

    if not rows:
        tu, den = conn.execute(sa.text(
            "SELECT min(trading_date), max(trading_date) FROM market.price_daily WHERE security_id = :sid"),
            {"sid": ma["security_id"]}).one()
        return to_json({**rong({"tu": str(tu), "den": str(den)} if tu else None), "ma": ma["ticker"]})

    du_lieu = [{"ngay": str(r.trading_date), "ngay_hien_thi": format_date_vi(r.trading_date),
                "dong_cua": display_metric(r.dong_cua, "VND"),
                "mo_cua": display_metric(r.open_value, "VND"),
                "cao_nhat": display_metric(r.highest_value, "VND"),
                "thap_nhat": display_metric(r.lowest_value, "VND")} for r in reversed(rows)]
    return to_json(co_du_lieu(du_lieu, ma=ma["ticker"], gia_dieu_chinh=adjusted,
                              ghi_chu="kho chưa có khối lượng giao dịch theo ngày"))
```

- [ ] **Bước 4: Chạy để thấy xanh** — Expected: `4 passed`
- [ ] **Bước 5: Commit** — `git commit -m "feat(agent): get_price_series tool"`

---

## Task 6 — `get_industry_tree`

**Files:** Create `backend/agent/tools/get_industry_tree.py`, `backend/tests/agent/test_a06_industry.py`
**Produces:** `def cay_nganh(conn, industry_code=None, ticker=None) -> str`

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/agent/test_a06_industry.py
"""Seam S4 — cây ngành RIÊNG của dự án, tuyệt đối không phơi ICB ra model.

Expected đo 2026-09-07 bằng đường khác (join thẳng issuer→industry thay vì qua view):
  VCB -> NGANHANG "Ngân hàng và Tín dụng", nhóm cha TAICHINH "Dịch vụ Tài chính", nguồn 'icb'
  Cây có đúng 6 nhóm level 1 và 24 ngành level 2.
"""
import json

import sqlalchemy as sa

from agent.tools.get_industry_tree import cay_nganh


def test_cay_du_sau_nhom_hai_bon_nganh(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(cay_nganh(db))
    assert len(out["nhom"]) == 6
    assert sum(len(n["nganh"]) for n in out["nhom"]) == 24


def test_nganh_cua_vcb(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(cay_nganh(db, ticker="VCB"))
    assert out["nganh"]["ma"] == "NGANHANG"
    assert out["nganh"]["ten"] == "Ngân hàng và Tín dụng"
    assert out["nhom"]["ten"] == "Dịch vụ Tài chính"
    assert out["nguon_gan"] == "icb"


def test_khong_bao_gio_lo_icb(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert "icb_code" not in cay_nganh(db, ticker="VCB")
    assert "icb" not in json.loads(cay_nganh(db))["nhom"][0]


def test_ma_khong_ton_tai(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert json.loads(cay_nganh(db, ticker="ZZZZ"))["tim_thay"] is False
```

- [ ] **Bước 2: Chạy để thấy đỏ**
- [ ] **Bước 3: Viết implementation**

```python
"""Cây ngành riêng 6 nhóm × 24 ngành, và ngành đã phân giải của một mã.

KHÔNG có tham số icb_level và KHÔNG trả cây ICB: bộ ngành riêng là chuẩn duy nhất khi hiển
thị và phân tích, ICB chỉ là đường nạp nhanh ở tầng ETL (industry-tree.md §1).
Đọc ngành của doanh nghiệp PHẢI qua view market.v_issuer_industry — đọc thẳng
issuer.industry_id là bỏ qua lớp gán tay.
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.tools._shared import resolve_ticker, to_json


def cay_nganh(conn: sa.Connection, industry_code: str | None = None, ticker: str | None = None) -> str:
    if ticker:
        ma = resolve_ticker(conn, ticker)
        if not ma["tim_thay"]:
            return to_json(ma)
        row = conn.execute(sa.text("""
            SELECT ind.code, ind.name_vi, par.code AS nhom_ma, par.name_vi AS nhom_ten, v.source
            FROM market.v_issuer_industry v
            JOIN market.industry ind ON ind.industry_id = v.industry_id
            LEFT JOIN market.industry par ON par.industry_id = ind.parent_id
            WHERE v.issuer_id = :iid
        """), {"iid": ma["issuer_id"]}).first()
        if row is None or row.code is None:
            return to_json({"tim_thay": True, "co_du_lieu": False, "ma": ma["ticker"],
                            "ly_do": "mã này chưa được gán ngành (quỹ/ETF theo thiết kế không có ngành)"})
        return to_json({"tim_thay": True, "co_du_lieu": True, "ma": ma["ticker"],
                        "nganh": {"ma": row.code, "ten": row.name_vi},
                        "nhom": {"ma": row.nhom_ma, "ten": row.nhom_ten},
                        "nguon_gan": row.source})

    rows = conn.execute(sa.text("""
        SELECT par.code AS nhom_ma, par.name_vi AS nhom_ten, ind.code, ind.name_vi
        FROM market.industry ind
        JOIN market.industry par ON par.industry_id = ind.parent_id
        WHERE ind.level = 2 AND (:ma::text IS NULL OR ind.code = :ma OR par.code = :ma)
        ORDER BY par.sort_order, ind.sort_order
    """), {"ma": industry_code}).all()
    nhom: dict[str, dict] = {}
    for r in rows:
        nhom.setdefault(r.nhom_ma, {"ma": r.nhom_ma, "ten": r.nhom_ten, "nganh": []})
        nhom[r.nhom_ma]["nganh"].append({"ma": r.code, "ten": r.name_vi})
    return to_json({"nhom": list(nhom.values())})
```

- [ ] **Bước 4: Chạy để thấy xanh** — Expected: `4 passed`
- [ ] **Bước 5: Commit** — `git commit -m "feat(agent): get_industry_tree tool, project taxonomy only"`

---

## Task 7 — `get_financials`

**Files:** Create `backend/agent/tools/get_financials.py`, `backend/tests/agent/test_a07_financials.py`
**Produces:** `def bao_cao_tai_chinh(conn, ticker, statement_type='IS', from_year=None, to_year=None, period='nam', metric_codes=None) -> str`

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/agent/test_a07_financials.py
"""Seam S4 — báo cáo tài chính dạng dài, bảng 27.281.962 dòng.

Expected đo 2026-09-07, cùng đường (bảng này là nguồn duy nhất) ⇒ CHỐT HỒI QUY, không chứng
minh tính đúng:
  FPT 2024 length_report=5: isa3 = 62848794351367 ; isa22 = 7856767812178 ; isa20 = 9427422530444
Ba mã trên có ý nghĩa khác nhau nhưng isa20 và isa22 mang CÙNG name_vi trong nguồn — bảng
nhãn đóng của dự án là chỗ tách chúng ra.
"""
import json

import sqlalchemy as sa

from agent.tools.get_financials import bao_cao_tai_chinh


def test_doanh_thu_va_loi_nhuan_fpt_2024(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", "IS", 2024, 2024))
    ky = out["du_lieu"][0]
    assert ky["nam"] == 2024
    chi_tieu = {c["ten"]: c["gia_tri"] for c in ky["chi_tieu"]}
    assert chi_tieu["Doanh thu thuần"] == "62.848,8 tỷ VND"
    assert chi_tieu["Lợi nhuận sau thuế của cổ đông công ty mẹ"] == "7.856,8 tỷ VND"
    assert chi_tieu["Lợi nhuận sau thuế (toàn bộ)"] == "9.427,4 tỷ VND"


def test_chi_phi_am_van_dung_dinh_dang(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", "IS", 2024, 2024))
    chi_tieu = {c["ten"]: c["gia_tri"] for c in out["du_lieu"][0]["chi_tieu"]}
    assert chi_tieu["Chi phí bán hàng"].startswith("-")


def test_khong_bao_gio_lo_ma_tho(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    raw = bao_cao_tai_chinh(db, "FPT", "BS", 2024, 2024)
    for ma in ("isa3", "bsa53", "isa22"):
        assert ma not in raw


def test_ma_ngoai_bang_nhan_bi_tu_choi(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", "IS", 2024, 2024, metric_codes=["prf"]))
    assert out["loi"] is True
    assert "isa3" in out["ma_hop_le"]


def test_tran_tam_nam(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(bao_cao_tai_chinh(db, "FPT", "IS", 2000, 2024))
    assert len(out["du_lieu"]) <= 8
    assert out["da_cat"] is True
```

- [ ] **Bước 2: Chạy để thấy đỏ**
- [ ] **Bước 3: Viết implementation**

```python
"""Báo cáo tài chính dạng dài.

Bảng 27,3 triệu dòng ⇒ MỌI truy vấn lọc issuer_id trước, rồi mới lọc năm và mã chỉ tiêu; trần
8 năm. length_report: 1..4 = quý, 5 = CẢ NĂM (không phải quý 5). canonical_code NULL toàn bộ
nên đừng dùng nó. Tên hiển thị lấy từ bảng nhãn đóng, KHÔNG tra name_vi (tên không duy nhất).
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import display_metric
from agent.labels import DEFAULT_BY_STATEMENT, LABELS
from agent.tools._shared import resolve_ticker, rong, to_json

TRAN_NAM = 8


def bao_cao_tai_chinh(conn: sa.Connection, ticker: str, statement_type: str = "IS",
                      from_year: int | None = None, to_year: int | None = None,
                      period: str = "nam", metric_codes: list[str] | None = None) -> str:
    codes = list(metric_codes or []) or DEFAULT_BY_STATEMENT.get(statement_type, [])
    la = [c for c in codes if c not in LABELS]
    if la:
        return to_json({"loi": True, "ly_do": f"ma chi tieu ngoai bang nhan: {la}",
                        "ma_hop_le": sorted(LABELS)})
    ma = resolve_ticker(conn, ticker)
    if not ma["tim_thay"]:
        return to_json(ma)

    lengths = [5] if period == "nam" else [1, 2, 3, 4]
    rows = conn.execute(sa.text("""
        SELECT fs.year_report, fs.length_report, fs.metric_code, fs.value, md.unit
        FROM market.financial_statement fs
        LEFT JOIN market.metric_dictionary md ON md.code = fs.metric_code
        WHERE fs.issuer_id = :iid
          AND fs.statement_type = :st
          AND fs.length_report = ANY(:lens)
          AND fs.metric_code = ANY(:codes)
          AND (:tu::int IS NULL OR fs.year_report >= :tu)
          AND (:den::int IS NULL OR fs.year_report <= :den)
        ORDER BY fs.year_report DESC, fs.length_report
    """), {"iid": ma["issuer_id"], "st": statement_type, "lens": lengths,
           "codes": codes, "tu": from_year, "den": to_year}).all()
    if not rows:
        return to_json({**rong(), "ma": ma["ticker"]})

    ky: dict[tuple, list] = {}
    for r in rows:
        gia_tri = display_metric(r.value, r.unit)
        if gia_tri is None:
            continue
        ky.setdefault((r.year_report, r.length_report), []).append(
            {"ten": LABELS[r.metric_code], "gia_tri": gia_tri})
    khoa = sorted(ky, reverse=True)
    da_cat = len(khoa) > TRAN_NAM
    du_lieu = [{"nam": k[0], **({"quy": k[1]} if k[1] != 5 else {}), "chi_tieu": ky[k]}
               for k in khoa[:TRAN_NAM]]
    return to_json({"tim_thay": True, "co_du_lieu": True, "so_dong": len(du_lieu),
                    "ma": ma["ticker"], "loai_bao_cao": statement_type,
                    "du_lieu": du_lieu, "da_cat": da_cat})
```

- [ ] **Bước 4: Chạy để thấy xanh** — Expected: `5 passed`
- [ ] **Bước 5: Commit** — `git commit -m "feat(agent): get_financials tool with a closed metric label set"`

---

## Task 8 — `get_corporate_events`

**Files:** Create `backend/agent/tools/get_corporate_events.py`, `backend/tests/agent/test_a08_events.py`
**Produces:** `def su_kien_doanh_nghiep(conn, ticker, event_type=None, from_date=None, to_date=None, limit=None) -> str`

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/agent/test_a08_events.py
"""Seam S4 — sự kiện doanh nghiệp.

Expected đo 2026-09-07 (cùng đường — chốt hồi quy):
  FPT, event_type='CashDividend', public_date trong 2025 -> 2 dòng,
  exright_date = 2025-06-12 và 2025-12-01. payload không có tỷ lệ chi trả (NULL).
Sáu event_type có thật trong kho: Earning, AGM, CashDividend, ShareIssuance, StockDividend, IPO.
"""
import json

import sqlalchemy as sa

from agent.tools.get_corporate_events import su_kien_doanh_nghiep


def test_co_tuc_tien_mat_fpt_2025(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(su_kien_doanh_nghiep(db, "FPT", "CashDividend", "2025-01-01", "2025-12-31"))
    assert out["so_dong"] == 2
    ngay = sorted(e["ngay_gdkhq"] for e in out["du_lieu"])
    assert ngay == ["2025-06-12", "2025-12-01"]


def test_loai_su_kien_la_bi_tu_choi_kem_danh_sach(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(su_kien_doanh_nghiep(db, "FPT", "KhongCoLoaiNay"))
    assert out["loi"] is True
    assert "CashDividend" in out["loai_hop_le"]


def test_ma_khong_ton_tai(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert json.loads(su_kien_doanh_nghiep(db, "ZZZZ"))["tim_thay"] is False
```

- [ ] **Bước 2: Chạy để thấy đỏ**
- [ ] **Bước 3: Viết implementation**

```python
"""Sự kiện doanh nghiệp: cổ tức, đại hội, phát hành, IPO, ngày công bố kết quả.

Kho có 110.804 dòng, 6 loại. payload jsonb nhiều trường rỗng — chỉ phơi những trường có
nghĩa và ĐỪNG suy ra tỷ lệ chi trả khi kho không có.
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import format_date_vi
from agent.tools._shared import cap_limit, co_du_lieu, resolve_ticker, rong, to_json

LOAI = ["Earning", "AGM", "CashDividend", "ShareIssuance", "StockDividend", "IPO"]


def su_kien_doanh_nghiep(conn: sa.Connection, ticker: str, event_type: str | None = None,
                         from_date: str | None = None, to_date: str | None = None,
                         limit: int | None = None) -> str:
    if event_type and event_type not in LOAI:
        return to_json({"loi": True, "ly_do": f"khong co loai su kien '{event_type}'", "loai_hop_le": LOAI})
    ma = resolve_ticker(conn, ticker)
    if not ma["tim_thay"]:
        return to_json(ma)
    lim, da_cat = cap_limit(limit, 20, 50)
    rows = conn.execute(sa.text("""
        SELECT ce.event_type, ce.public_date, ce.exright_date, ce.record_date, ce.payout_date,
               ce.year_report, ce.length_report
        FROM market.corporate_event ce
        WHERE ce.issuer_id = :iid
          AND (:loai::text IS NULL OR ce.event_type = :loai)
          AND (:tu::date IS NULL OR ce.public_date >= :tu::date)
          AND (:den::date IS NULL OR ce.public_date <= :den::date)
        ORDER BY ce.public_date DESC NULLS LAST
        LIMIT :lim
    """), {"iid": ma["issuer_id"], "loai": event_type, "tu": from_date, "den": to_date, "lim": lim}).all()
    if not rows:
        return to_json({**rong(), "ma": ma["ticker"]})
    du_lieu = []
    for r in rows:
        e = {"loai": r.event_type, "ngay_cong_bo": str(r.public_date) if r.public_date else None}
        if r.exright_date:
            e["ngay_gdkhq"] = str(r.exright_date)
            e["ngay_gdkhq_hien_thi"] = format_date_vi(r.exright_date)
        if r.payout_date:
            e["ngay_thanh_toan"] = str(r.payout_date)
        if r.year_report:
            e["ky"] = f"{r.year_report}" + (f" quý {r.length_report}" if r.length_report and r.length_report < 5 else "")
        du_lieu.append(e)
    return to_json(co_du_lieu(du_lieu, ma=ma["ticker"], da_cat=da_cat,
                              ghi_chu="kho không lưu tỷ lệ chi trả của các đợt cổ tức"))
```

- [ ] **Bước 4: Chạy để thấy xanh** — Expected: `3 passed`
- [ ] **Bước 5: Commit** — `git commit -m "feat(agent): get_corporate_events tool"`

---

## Task 9 — `screen_stocks` và `compare_peers`

**Files:** Create `backend/agent/tools/screen_stocks.py`, `backend/agent/tools/compare_peers.py`, `backend/tests/agent/test_a09_screener.py`
**Produces:** `def loc_co_phieu(conn, criteria=None, industry_code=None, exchange=None, sort_by=None, limit=None) -> str` · `def so_sanh_cung_nganh(conn, tickers=None, metric_codes=None, industry_code=None) -> str`

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/agent/test_a09_screener.py
"""Seam S4 — lọc cổ phiếu và so sánh, đọc market.screener_daily (payload jsonb).

Expected đo 2026-09-07 (cùng đường — chốt hồi quy). Phiên 2026-09-04:
  ngành NGANHANG, ROE (rtq12) cao nhất: TIN 0.73478649, HDB 0.24836986, LPB 0.2466187
  P/E (rtd21): HPG 7.89115654, VCB 11.81676534
Payload có hai nhánh: 'financial' (5 khoá) và 'stockScreenerItem' (70 khoá) — chỉ tiêu của
tầng ngữ nghĩa nằm ở nhánh sau.
"""
import json

import sqlalchemy as sa

from agent.tools.compare_peers import so_sanh_cung_nganh
from agent.tools.screen_stocks import loc_co_phieu


def test_top_roe_nganh_ngan_hang(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, industry_code="NGANHANG", sort_by="rtq12", limit=3))
    assert [c["ma"] for c in out["du_lieu"]] == ["TIN", "HDB", "LPB"]
    roe = {c["ma"]: dict(x.values() for x in [c]) for c in out["du_lieu"]}  # giữ đơn giản
    assert out["du_lieu"][0]["chi_tieu"]["ROE (TTM)"] == "73,48%"
    assert out["du_lieu"][1]["chi_tieu"]["ROE (TTM)"] == "24,84%"


def test_loc_theo_tieu_chi(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(loc_co_phieu(db, criteria=[{"metric_code": "rtd21", "operator": "<", "value": 8}],
                                  industry_code="KIMLOAI", limit=20))
    assert out["co_du_lieu"] is True
    assert all("P/E (TTM)" in c["chi_tieu"] for c in out["du_lieu"])


def test_so_sanh_pe_hpg_vcb(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(so_sanh_cung_nganh(db, tickers=["HPG", "VCB"], metric_codes=["rtd21"]))
    bang = {c["ma"]: c["chi_tieu"]["P/E (TTM)"] for c in out["du_lieu"]}
    assert bang == {"HPG": "7,89 lần", "VCB": "11,82 lần"}


def test_ma_chi_tieu_ngoai_bang_nhan_bi_tu_choi(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(so_sanh_cung_nganh(db, tickers=["HPG"], metric_codes=["rev"]))
    assert out["loi"] is True


def test_luon_kem_ngay_du_lieu(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert json.loads(loc_co_phieu(db, limit=1))["ngay_du_lieu"] == "2026-09-04"
```

*(Nếu ETL screener chạy thêm phiên mới trước khi task này thực thi, `test_luon_kem_ngay_du_lieu` phải đổi sang so với `max(trading_date)` đọc ngay trong test — sửa test, đừng sửa hàm.)*

- [ ] **Bước 2: Chạy để thấy đỏ**
- [ ] **Bước 3: Viết `screen_stocks.py`**

```python
"""Lọc và xếp hạng cổ phiếu theo chỉ tiêu screener của phiên gần nhất.

Nguồn market.screener_daily: payload->'stockScreenerItem' chứa ~70 khoá mã chỉ tiêu. Chỉ
chấp nhận mã nằm trong BẢNG NHÃN ĐÓNG — mã ngoài bảng bị từ chối kèm danh sách hợp lệ, vì
tên hiển thị không suy được và đơn vị có thể sai (prf/rev: tên nói "tỉ đồng", unit nói VND).
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import display_metric
from agent.labels import DEFAULT_RATIOS, LABELS
from agent.tools._shared import cap_limit, co_du_lieu, rong, to_json

TOAN_TU = {">": ">", "<": "<", ">=": ">=", "<=": "<=", "=": "="}
_KEY = "payload->'stockScreenerItem'->>"


def _don_vi(conn) -> dict[str, str | None]:
    return {r.code: r.unit for r in conn.execute(sa.text(
        "SELECT code, unit FROM market.metric_dictionary WHERE code = ANY(:c)"),
        {"c": list(LABELS)})}


def loc_co_phieu(conn: sa.Connection, criteria: list[dict] | None = None,
                 industry_code: str | None = None, exchange: str | None = None,
                 sort_by: str | None = None, limit: int | None = None) -> str:
    criteria = list(criteria or [])
    xin = [c.get("metric_code") for c in criteria] + ([sort_by] if sort_by else [])
    la = [c for c in xin if c and c not in LABELS]
    if la:
        return to_json({"loi": True, "ly_do": f"ma chi tieu ngoai bang nhan: {la}", "ma_hop_le": sorted(LABELS)})
    for c in criteria:
        if c.get("operator") not in TOAN_TU:
            return to_json({"loi": True, "ly_do": f"toan tu la: {c.get('operator')}",
                            "toan_tu_hop_le": sorted(TOAN_TU)})

    ngay = conn.execute(sa.text("SELECT max(trading_date) FROM market.screener_daily")).scalar()
    if ngay is None:
        return to_json(rong())
    lim, da_cat = cap_limit(limit, 20, 50)
    sort = sort_by or "rtd11"
    dieu_kien, params = [], {"ngay": ngay, "nganh": industry_code, "san": exchange, "lim": lim}
    for i, c in enumerate(criteria):
        params[f"v{i}"] = c["value"]
        dieu_kien.append(f"({_KEY}'{c['metric_code']}')::numeric {TOAN_TU[c['operator']]} :v{i}")
    where = (" AND " + " AND ".join(dieu_kien)) if dieu_kien else ""

    rows = conn.execute(sa.text(f"""
        SELECT s.ticker, s.exchange, ind.name_vi AS nganh, sd.payload->'stockScreenerItem' AS item
        FROM market.screener_daily sd
        JOIN market.security s USING (security_id)
        LEFT JOIN market.v_issuer_industry v ON v.issuer_id = s.issuer_id
        LEFT JOIN market.industry ind ON ind.industry_id = v.industry_id
        WHERE sd.trading_date = :ngay AND s.status = 'listed'
          AND (:nganh::text IS NULL OR ind.code = :nganh)
          AND (:san::text IS NULL OR s.exchange = :san)
          AND ({_KEY}'{sort}') IS NOT NULL
          {where}
        ORDER BY ({_KEY}'{sort}')::numeric DESC
        LIMIT :lim
    """), params).all()
    if not rows:
        return to_json({**rong(), "ngay_du_lieu": str(ngay)})

    units = _don_vi(conn)
    hien = [sort] + [c["metric_code"] for c in criteria] + DEFAULT_RATIOS
    thu_tu = list(dict.fromkeys(hien))
    du_lieu = []
    for r in rows:
        ct = {}
        for code in thu_tu:
            v = (r.item or {}).get(code)
            s = display_metric(v, units.get(code)) if v is not None else None
            if s is not None:
                ct[LABELS[code]] = s
        du_lieu.append({"ma": r.ticker, "san": r.exchange, "nganh": r.nganh, "chi_tieu": ct})
    return to_json(co_du_lieu(du_lieu, ngay_du_lieu=str(ngay), da_cat=da_cat))
```

- [ ] **Bước 4: Viết `compare_peers.py`**

```python
"""So sánh vài mã trên cùng bộ chỉ tiêu, cùng phiên screener gần nhất."""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import display_metric
from agent.labels import DEFAULT_RATIOS, LABELS
from agent.tools._shared import co_du_lieu, rong, to_json

TRAN_MA, TRAN_CHI_TIEU = 10, 8


def so_sanh_cung_nganh(conn: sa.Connection, tickers: list[str] | None = None,
                       metric_codes: list[str] | None = None,
                       industry_code: str | None = None) -> str:
    codes = list(metric_codes or []) or DEFAULT_RATIOS
    la = [c for c in codes if c not in LABELS]
    if la:
        return to_json({"loi": True, "ly_do": f"ma chi tieu ngoai bang nhan: {la}", "ma_hop_le": sorted(LABELS)})
    codes = codes[:TRAN_CHI_TIEU]
    mas = [t.upper() for t in (tickers or [])][:TRAN_MA]
    if not mas and not industry_code:
        return to_json({"loi": True, "ly_do": "phai cho tickers hoac industry_code"})

    ngay = conn.execute(sa.text("SELECT max(trading_date) FROM market.screener_daily")).scalar()
    rows = conn.execute(sa.text("""
        SELECT s.ticker, ind.name_vi AS nganh, sd.payload->'stockScreenerItem' AS item
        FROM market.screener_daily sd
        JOIN market.security s USING (security_id)
        LEFT JOIN market.v_issuer_industry v ON v.issuer_id = s.issuer_id
        LEFT JOIN market.industry ind ON ind.industry_id = v.industry_id
        WHERE sd.trading_date = :ngay AND s.status = 'listed'
          AND (cardinality(:mas::text[]) = 0 OR upper(s.ticker) = ANY(:mas))
          AND (:nganh::text IS NULL OR ind.code = :nganh)
        ORDER BY s.ticker
        LIMIT :lim
    """), {"ngay": ngay, "mas": mas, "nganh": industry_code, "lim": TRAN_MA}).all()
    if not rows:
        return to_json({**rong(), "ngay_du_lieu": str(ngay) if ngay else None})

    units = {r.code: r.unit for r in conn.execute(sa.text(
        "SELECT code, unit FROM market.metric_dictionary WHERE code = ANY(:c)"), {"c": codes})}
    du_lieu = []
    for r in rows:
        ct = {}
        for code in codes:
            v = (r.item or {}).get(code)
            s = display_metric(v, units.get(code)) if v is not None else None
            if s is not None:
                ct[LABELS[code]] = s
        du_lieu.append({"ma": r.ticker, "nganh": r.nganh, "chi_tieu": ct})
    return to_json(co_du_lieu(du_lieu, ngay_du_lieu=str(ngay)))
```

- [ ] **Bước 5: Chạy để thấy xanh** — Expected: `5 passed`. Sửa `test_top_roe_nganh_ngan_hang` bỏ dòng `roe = {...}` thừa nếu lint kêu.
- [ ] **Bước 6: Commit** — `git commit -m "feat(agent): screen_stocks and compare_peers tools"`

---

## Task 10 — `get_macro_series` (hai nhánh macro và asset)

**Files:** Create `backend/agent/tools/get_macro_series.py`, `backend/tests/agent/test_a10_macro.py`
**Produces:** `def chuoi_vi_mo(conn, code=None, keyword=None, from_date=None, to_date=None, limit=None) -> str`

🔴 **`asset.price_daily` có cột `price_type`** (`spot|futures|fixing|close`) và một mã có thể mang **nhiều loại giá** — vàng có cả `spot` lẫn `fixing`, dầu có `futures`. ADR §2.3 cấm trộn: *"lược đồ phải có cột phân biệt loại giá; trộn chung một cột sẽ tạo bậc nhảy 2% tại điểm đổi nguồn"*. Vì vậy hàm **chọn đúng MỘT loại** trong khoảng hỏi (loại có nhiều dòng nhất), trả kèm `loai_gia` và `cac_loai_gia_co_san`, tuyệt đối không gộp hai loại vào một chuỗi.

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/agent/test_a10_macro.py
"""Seam S4 — chuỗi vĩ mô và giá tài sản.

BA nguồn, không phải một (đo 2026-09-07):
  macro.observation_spliced (cột value_spliced / value_as_published — KHÔNG có cột 'value')
  asset.price_daily  — commodity 49, fx 12, index 2   (wti, gold.sjc_sell, fx.usd_vnd.*)
  asset.ohlc_daily   — crypto 11, fx 17, index 37     (btc, idx.sp500, vix)
Expected: vn.cpi 2026-08-01 = 4.45 (đơn vị '%' — KHÔNG nhân 100); wti 2026-09-05 = 91.22 USD/thùng.
"""
import json

import sqlalchemy as sa

from agent.tools.get_macro_series import chuoi_vi_mo


def test_cpi_thang_8_2026(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, code="vn.cpi", from_date="2026-08-01", to_date="2026-08-31"))
    assert out["du_lieu"][-1]["gia_tri"] == "4,45%"
    assert out["ten"] == "CPI (YoY)"


def test_dau_wti_la_nhanh_asset(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, code="wti", from_date="2026-09-05", to_date="2026-09-05"))
    assert out["du_lieu"][-1]["gia_tri"] == "91,22 USD/thùng"


def test_btc_nam_o_bang_ohlc(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, code="btc", limit=5))
    assert out["co_du_lieu"] is True and out["so_dong"] > 0


def test_keyword_tra_danh_muc_khong_tra_so(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, keyword="lãi suất"))
    assert out["kieu"] == "danh_muc"
    ma = [d["ma"] for d in out["danh_muc"]]
    assert any(m.startswith("vn.rate.") for m in ma)
    assert "du_lieu" not in out


def test_ma_khong_ton_tai_thi_goi_y(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(chuoi_vi_mo(db, code="vn.cpixxx"))
    assert out["tim_thay"] is False
    assert out["goi_y"]
```

- [ ] **Bước 2: Chạy để thấy đỏ**
- [ ] **Bước 3: Viết implementation**

```python
"""Chuỗi vĩ mô (macro) và giá tài sản (asset) — một cửa cho model.

macro đọc qua view observation_spliced (chuỗi ĐÃ NỐI): lấy value_spliced; kèm value_as_published
khi hai giá trị khác nhau để model nói được là chuỗi đã nối.
asset nằm ở HAI bảng: price_daily (một giá trị) và ohlc_daily (nến) — phải thử cả hai.
Không có code ⇒ trả DANH MỤC theo keyword, không trả số: đó là cách model tìm mã mà không
phải nhồi 192 mã vào system prompt.
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import display_series_value, format_date_vi
from agent.tools._shared import cap_limit, co_du_lieu, khong_tim_thay, rong, to_json


def _danh_muc(conn, keyword: str | None) -> list[dict]:
    return [dict(r._mapping) for r in conn.execute(sa.text("""
        SELECT i.code AS ma, i.name_vi AS ten, i.unit AS don_vi, 'macro' AS nguon
        FROM macro.indicator i
        WHERE :kw::text IS NULL OR i.code ILIKE '%%' || :kw || '%%' OR i.name_vi ILIKE '%%' || :kw || '%%'
        UNION ALL
        SELECT a.code, a.name_vi, a.unit, 'asset'
        FROM asset.asset a
        WHERE :kw::text IS NULL OR a.code ILIKE '%%' || :kw || '%%' OR a.name_vi ILIKE '%%' || :kw || '%%'
        ORDER BY 1 LIMIT 40
    """), {"kw": keyword})]


def chuoi_vi_mo(conn: sa.Connection, code: str | None = None, keyword: str | None = None,
                from_date: str | None = None, to_date: str | None = None,
                limit: int | None = None) -> str:
    if not code:
        return to_json({"kieu": "danh_muc", "danh_muc": _danh_muc(conn, keyword)})
    lim, da_cat = cap_limit(limit, 60, 200)

    ind = conn.execute(sa.text(
        "SELECT indicator_id, name_vi, unit FROM macro.indicator WHERE code = :c"), {"c": code}).first()
    if ind:
        rows = conn.execute(sa.text("""
            SELECT obs_date, value_spliced, value_as_published
            FROM macro.observation_spliced
            WHERE indicator_id = :id
              AND (:tu::date IS NULL OR obs_date >= :tu::date)
              AND (:den::date IS NULL OR obs_date <= :den::date)
            ORDER BY obs_date DESC LIMIT :lim
        """), {"id": ind.indicator_id, "tu": from_date, "den": to_date, "lim": lim}).all()
        if not rows:
            return to_json({**rong(), "ma": code})
        du_lieu = []
        for r in reversed(rows):
            d = {"ngay": str(r.obs_date), "ngay_hien_thi": format_date_vi(r.obs_date),
                 "gia_tri": display_series_value(r.value_spliced, ind.unit)}
            if r.value_as_published is not None and r.value_as_published != r.value_spliced:
                d["gia_tri_cong_bo"] = display_series_value(r.value_as_published, ind.unit)
                d["ghi_chu"] = "chuỗi đã nối, khác số công bố gốc"
            du_lieu.append(d)
        return to_json(co_du_lieu(du_lieu, ma=code, ten=ind.name_vi, don_vi=ind.unit, da_cat=da_cat))

    tai_san = conn.execute(sa.text(
        "SELECT asset_id, name_vi, unit FROM asset.asset WHERE code = :c"), {"c": code}).first()
    if tai_san is None:
        return to_json(khong_tim_thay(code, [d["ma"] for d in _danh_muc(conn, code[:6])][:5]))
    rows = conn.execute(sa.text("""
        SELECT obs_date, value AS gia FROM asset.price_daily
        WHERE asset_id = :id AND (:tu::date IS NULL OR obs_date >= :tu::date)
          AND (:den::date IS NULL OR obs_date <= :den::date)
        UNION ALL
        SELECT obs_date, close FROM asset.ohlc_daily
        WHERE asset_id = :id AND (:tu::date IS NULL OR obs_date >= :tu::date)
          AND (:den::date IS NULL OR obs_date <= :den::date)
        ORDER BY 1 DESC LIMIT :lim
    """), {"id": tai_san.asset_id, "tu": from_date, "den": to_date, "lim": lim}).all()
    if not rows:
        return to_json({**rong(), "ma": code})
    du_lieu = [{"ngay": str(r.obs_date), "ngay_hien_thi": format_date_vi(r.obs_date),
                "gia_tri": display_series_value(r.gia, tai_san.unit)} for r in reversed(rows)]
    return to_json(co_du_lieu(du_lieu, ma=code, ten=tai_san.name_vi, don_vi=tai_san.unit, da_cat=da_cat))
```

- [ ] **Bước 4: Chạy để thấy xanh** — Expected: `5 passed`
- [ ] **Bước 5: Commit** — `git commit -m "feat(agent): get_macro_series across macro and both asset tables"`

---

## Task 11 — `get_news`

**Files:** Create `backend/agent/tools/get_news.py`, `backend/tests/agent/test_a11_news.py`
**Produces:** `def tim_tin(conn, query=None, ticker=None, group_no=None, sub=None, industry_code=None, from_date=None, to_date=None, limit=None) -> str`

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/agent/test_a11_news.py
"""Seam S4 — tìm tin.

BẪY ĐÃ ĐO (2026-09-07): tsv sinh bằng to_tsvector('simple', news.immutable_unaccent(...)),
nên câu hỏi PHẢI bọc cùng hàm — quên là khớp 0 bài. Và 'simple' tách theo ÂM TIẾT nên
plainto_tsquery AND từng âm tiết:
  'lãi suất điều hành'  plainto -> 1.050 bài toàn kho | phraseto -> 31 bài
  tháng 8/2026, phraseto -> 23 bài   <- expected của test dưới
Dùng khoảng thời gian ĐÓNG trong quá khứ vì kho tin vẫn nhận bài mới.
"""
import json

import sqlalchemy as sa

from agent.tools.get_news import tim_tin


def test_tim_theo_cum_tu_thang_8_2026(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, query="lãi suất điều hành",
                             from_date="2026-08-01", to_date="2026-08-31", limit=30))
    assert out["kieu_tim"] == "cum"
    assert out["tong_khop"] == 23


def test_moi_bai_deu_co_co_da_phan_loai(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, query="ngân hàng", limit=5))
    assert all("da_phan_loai" in b for b in out["du_lieu"])


def test_loc_theo_nhan_chi_khop_bai_da_phan_loai(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, sub="1b", limit=5))
    assert all(b["da_phan_loai"] is True for b in out["du_lieu"])


def test_loc_nhan_rong_thi_noi_ro_con_bao_nhieu_bai_chua_nhan(db):
    """Không được để model kết luận 'không có tin nào' khi thật ra là chưa phân loại."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    out = json.loads(tim_tin(db, sub="3b", from_date="2025-05-01", to_date="2025-05-31"))
    assert out["so_dong"] == 0
    assert "chưa phân loại" in out["ghi_chu"]


def test_sub_la_bi_tu_choi(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert json.loads(tim_tin(db, sub="9z"))["loi"] is True
```

- [ ] **Bước 2: Chạy để thấy đỏ**
- [ ] **Bước 3: Viết implementation**

```python
"""Tìm tin trong kho.

Hai đường lọc khác nhau, đừng trộn:
  query      -> tìm toàn văn trên TOÀN BỘ article_revision, kể cả bài chưa có nhãn AI
  nhãn       -> group_no/sub/industry_code/ticker, CHỈ khớp bài đã phân loại
Bài chưa nhãn là trạng thái TẠM (sẽ backfill khi lên prod) nên không có nhánh code riêng —
chỉ có cờ da_phan_loai và ghi_chu; backfill xong thì cờ luôn true, không phải sửa gì.
"""
from __future__ import annotations

import sqlalchemy as sa

from agent.format import format_date_vi
from agent.tools._shared import cap_limit, co_du_lieu, to_json

SUBS = [f"{g}{c}" for g, cs in ((1, "abcdef"), (2, "abcdef"), (3, "abcde")) for c in cs]


def tim_tin(conn: sa.Connection, query: str | None = None, ticker: str | None = None,
            group_no: int | None = None, sub: str | None = None, industry_code: str | None = None,
            from_date: str | None = None, to_date: str | None = None, limit: int | None = None) -> str:
    if sub and sub not in SUBS:
        return to_json({"loi": True, "ly_do": f"khong co sub '{sub}'", "sub_hop_le": SUBS})
    lim, da_cat = cap_limit(limit, 10, 30)
    p = {"q": query, "tk": ticker.upper() if ticker else None, "g": group_no, "sub": sub,
         "nganh": industry_code, "tu": from_date, "den": to_date, "lim": lim}

    dk = ["(:tu::date IS NULL OR a.published_at >= :tu::date)",
          "(:den::date IS NULL OR a.published_at < (:den::date + 1))",
          "(:g::int IS NULL OR a.group_no = :g)", "(:sub::text IS NULL OR a.sub = :sub)"]
    if ticker:
        dk.append("EXISTS (SELECT 1 FROM news.article_ticker t JOIN market.security s USING (security_id)"
                  " WHERE t.article_id = a.article_id AND upper(s.ticker) = :tk)")
    if industry_code:
        dk.append("EXISTS (SELECT 1 FROM news.article_industry ai JOIN market.industry i USING (industry_id)"
                  " WHERE ai.article_id = a.article_id AND i.code = :nganh)")

    kieu = None
    if query:
        for kieu_thu, fn in (("cum", "phraseto_tsquery"), ("tu_khoa", "plainto_tsquery")):
            sql_dem = f"""SELECT count(*) FROM news.article a JOIN news.article_revision r USING (article_id)
                          WHERE r.tsv @@ {fn}('simple', news.immutable_unaccent(:q)) AND {' AND '.join(dk)}"""
            tong = conn.execute(sa.text(sql_dem), p).scalar()
            if tong:
                kieu, ham = kieu_thu, fn
                break
        else:
            return to_json({"tim_thay": True, "co_du_lieu": True, "so_dong": 0, "tong_khop": 0,
                            "kieu_tim": "cum", "du_lieu": []})
        sql = f"""
            SELECT a.article_id, a.published_at, a.primary_source, a.group_no, a.sub,
                   a.classified_from IS NOT NULL AS da_phan_loai, r.title, r.sapo, r.summary_ai,
                   ts_rank(r.tsv, {ham}('simple', news.immutable_unaccent(:q))) AS diem
            FROM news.article a JOIN news.article_revision r USING (article_id)
            WHERE r.tsv @@ {ham}('simple', news.immutable_unaccent(:q)) AND {' AND '.join(dk)}
            ORDER BY diem DESC, a.published_at DESC LIMIT :lim"""
    else:
        tong = conn.execute(sa.text(
            f"SELECT count(*) FROM news.article a WHERE {' AND '.join(dk)}"), p).scalar()
        sql = f"""
            SELECT a.article_id, a.published_at, a.primary_source, a.group_no, a.sub,
                   a.classified_from IS NOT NULL AS da_phan_loai, r.title, r.sapo, r.summary_ai
            FROM news.article a JOIN news.article_revision r USING (article_id)
            WHERE {' AND '.join(dk)}
            ORDER BY a.published_at DESC LIMIT :lim"""

    rows = conn.execute(sa.text(sql), p).all()
    du_lieu = [{"tieu_de": r.title, "ngay": str(r.published_at.date()),
                "ngay_hien_thi": format_date_vi(r.published_at), "bao": r.primary_source,
                "nhom": r.group_no, "sub": r.sub, "da_phan_loai": bool(r.da_phan_loai),
                "tom_tat": r.summary_ai or r.sapo} for r in rows]
    out = co_du_lieu(du_lieu, tong_khop=tong, da_cat=da_cat)
    if kieu:
        out["kieu_tim"] = kieu
    if not du_lieu and (group_no or sub or industry_code or ticker):
        chua = conn.execute(sa.text(
            "SELECT count(*) FROM news.article a WHERE a.classified_from IS NULL"
            " AND (:tu::date IS NULL OR a.published_at >= :tu::date)"
            " AND (:den::date IS NULL OR a.published_at < (:den::date + 1))"), p).scalar()
        out["ghi_chu"] = (f"không có bài nào khớp nhãn; trong khoảng này còn {chua} bài "
                          f"chưa phân loại nên chưa thể lọc theo nhãn")
    return to_json(out)
```

- [ ] **Bước 4: Chạy để thấy xanh** — Expected: `5 passed`
- [ ] **Bước 5: Commit** — `git commit -m "feat(agent): get_news with phrase-first Vietnamese full-text search"`

---

## Task 12 — Đăng ký 9 tool và sổ `ops.llm_call`

**Files:**
- Modify: `backend/agent/tools/__init__.py`
- Create: `backend/agent/llm_log.py`, `backend/tests/agent/test_a12_tools_log.py`

**Interfaces — Produces:**
```python
def build_tools(engine: sqlalchemy.Engine) -> list      # 9 BetaFunctionTool
def log_llm_call(ops_eng, message, *, purpose='chat', model: str, latency_ms: int) -> None
```

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/agent/test_a12_tools_log.py
"""Seam — đăng ký tool và sổ lời gọi model.

Bẫy đã đo: tham số tuỳ chọn KHÔNG có giá trị mặc định sẽ rơi vào 'required' của schema, và
MiniMax bỏ hẳn khoá mảng required khi giá trị rỗng ⇒ hỏng schema. Test canh đúng chỗ đó.
ops.llm_call ràng buộc thật: status ∈ ok|repaired|failed, thinking ∈ adaptive|disabled.
"""
import sqlalchemy as sa

from agent.db import ops_engine
from agent.llm_log import log_llm_call
from agent.tools import build_tools


def test_dung_chin_tool(migrated_engine):
    tools = build_tools(migrated_engine)
    assert len(tools) == 9
    ten = {t.name for t in tools}
    assert ten == {"screen_stocks", "get_financials", "get_price_series", "get_corporate_events",
                   "compare_peers", "get_news", "get_industry_tree", "get_macro_series",
                   "load_knowledge_reference"}


def test_khong_tham_so_tuy_chon_nao_bi_required(migrated_engine):
    bat_buoc = {"get_financials": {"ticker"}, "get_price_series": {"ticker"},
                "get_corporate_events": {"ticker"}, "load_knowledge_reference": {"topic"}}
    for t in build_tools(migrated_engine):
        req = set(t.input_schema.get("required", []))
        assert req == bat_buoc.get(t.name, set()), f"{t.name} required sai: {req}"


def test_moi_tool_deu_co_mo_ta_tieng_viet(migrated_engine):
    for t in build_tools(migrated_engine):
        assert t.description and len(t.description) > 40


def test_ghi_so_duoi_role_etl_that(db):
    """§3.5: đường ghi phải chạy dưới đúng quyền production."""
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text("""
        INSERT INTO ops.llm_call (purpose, model, thinking, status, http_calls, input_tokens,
                                  output_tokens, latency_ms)
        VALUES ('chat', 'MiniMax-M3', 'adaptive', 'ok', 1, 100, 20, 1234)"""))
    assert db.execute(sa.text("SELECT count(*) FROM ops.llm_call WHERE purpose='chat'")).scalar() == 1


def test_loi_ghi_so_khong_lam_sap_chat():
    class EngineHong:
        def connect(self):
            raise RuntimeError("DB sap")

    class Msg:
        stop_reason = "end_turn"
        usage = type("U", (), {"input_tokens": 1, "output_tokens": 1,
                               "cache_read_input_tokens": 0})()
    log_llm_call(EngineHong(), Msg(), model="MiniMax-M3", latency_ms=5)   # không được ném
```

- [ ] **Bước 2: Chạy để thấy đỏ**
- [ ] **Bước 3: Viết `llm_log.py`**

```python
"""Sổ mỗi request gọi model vào ops.llm_call.

MỘT DÒNG = MỘT REQUEST (http_calls=1), nên một câu chat nhiều vòng function sinh nhiều dòng.
status: 'ok' khi stop_reason='end_turn'; mọi kết thúc khác là 'failed' kèm error. 'repaired'
không dùng ở lát 10. Sổ là phụ, chat là chính — lỗi ghi sổ bị nuốt, in stderr.
"""
from __future__ import annotations

import sys

import sqlalchemy as sa

_SQL = sa.text("""
    INSERT INTO ops.llm_call (purpose, model, thinking, status, http_calls,
                              input_tokens, cache_read_tokens, output_tokens, latency_ms, error)
    VALUES (:purpose, :model, 'adaptive', :status, 1, :vao, :cache, :ra, :ms, :loi)
""")


def log_llm_call(ops_eng, message, *, purpose: str = "chat", model: str, latency_ms: int) -> None:
    try:
        u = getattr(message, "usage", None)
        stop = getattr(message, "stop_reason", None)
        with ops_eng.connect() as conn:
            conn.execute(_SQL, {
                "purpose": purpose, "model": model,
                "status": "ok" if stop == "end_turn" else "failed",
                "vao": getattr(u, "input_tokens", None),
                "cache": getattr(u, "cache_read_input_tokens", None),
                "ra": getattr(u, "output_tokens", None),
                "ms": latency_ms,
                "loi": None if stop == "end_turn" else f"stop_reason={stop}",
            })
            conn.commit()
    except Exception as e:                                   # noqa: BLE001 — chỉ giữ tên lớp
        print(f"[llm_log] khong ghi duoc so: {type(e).__name__}", file=sys.stderr)
```

- [ ] **Bước 4: Viết `tools/__init__.py`**

Mỗi tool là closure ôm `engine`, tự mở/đóng kết nối, docstring là **mô tả model đọc** — viết cẩn thận, đây là thứ quyết định model gọi đúng function hay không.

```python
"""Đăng ký 9 function cho model.

build_tools là FACTORY chứ không phải hằng module: BetaFunctionTool.call(input) chỉ truyền
đối số do model sinh, không có khe nhận Connection ⇒ engine phải đi vào bằng closure.
Mỗi tool tự mở và đóng kết nối trong thân hàm — KHÔNG giữ kết nối bắc qua lời gọi model.
"""
from __future__ import annotations

import sqlalchemy as sa
from anthropic import beta_tool

from agent.tools.compare_peers import so_sanh_cung_nganh
from agent.tools.get_corporate_events import su_kien_doanh_nghiep
from agent.tools.get_financials import bao_cao_tai_chinh
from agent.tools.get_industry_tree import cay_nganh
from agent.tools.get_macro_series import chuoi_vi_mo
from agent.tools.get_news import tim_tin
from agent.tools.get_price_series import gia_theo_ngay
from agent.tools.load_knowledge_reference import doc_tri_thuc
from agent.tools.screen_stocks import loc_co_phieu


def build_tools(engine: sa.Engine) -> list:
    def chay(fn, *args, **kwargs) -> str:
        with engine.connect() as conn:
            conn.execute(sa.text("SET LOCAL statement_timeout = '20s'"))
            return fn(conn, *args, **kwargs)

    @beta_tool
    def get_price_series(ticker: str, from_date: str | None = None, to_date: str | None = None,
                         adjusted: bool = True) -> str:
        """Chuỗi giá theo ngày của một mã cổ phiếu Việt Nam (giá mở/cao/thấp/đóng cửa).

        ticker: mã chứng khoán, ví dụ 'HPG'. from_date/to_date: 'YYYY-MM-DD', bỏ trống lấy các
        phiên gần nhất. adjusted: true dùng giá đã điều chỉnh. Kho CHỈ có giá cổ phiếu — không
        có chỉ số (VN-Index) và không có ETF; hàm sẽ nói rõ khi không có dữ liệu.
        """
        return chay(gia_theo_ngay, ticker, from_date, to_date, adjusted)

    @beta_tool
    def get_financials(ticker: str, statement_type: str = "IS", from_year: int | None = None,
                       to_year: int | None = None, period: str = "nam",
                       metric_codes: list[str] = []) -> str:
        """Số liệu báo cáo tài chính của một doanh nghiệp niêm yết.

        statement_type: 'IS' kết quả kinh doanh, 'BS' cân đối kế toán, 'CF' lưu chuyển tiền tệ.
        period: 'nam' (cả năm) hoặc 'quy'. metric_codes để trống thì trả bộ chỉ tiêu cốt lõi.
        Tối đa 8 kỳ mỗi lần gọi.
        """
        return chay(bao_cao_tai_chinh, ticker, statement_type, from_year, to_year, period, metric_codes)

    @beta_tool
    def screen_stocks(criteria: list[dict] = [], industry_code: str | None = None,
                      exchange: str | None = None, sort_by: str | None = None,
                      limit: int | None = None) -> str:
        """Lọc và xếp hạng cổ phiếu theo chỉ tiêu tài chính của phiên gần nhất.

        criteria: danh sách {"metric_code","operator","value"} với operator ∈ > < >= <= =.
        industry_code: mã ngành trong bộ 24 ngành của hệ thống (lấy bằng get_industry_tree).
        exchange: 'HOSE' | 'HNX' | 'UPCOM'. sort_by: mã chỉ tiêu để xếp hạng giảm dần.
        """
        return chay(loc_co_phieu, criteria, industry_code, exchange, sort_by, limit)

    @beta_tool
    def compare_peers(tickers: list[str] = [], metric_codes: list[str] = [],
                      industry_code: str | None = None) -> str:
        """So sánh nhiều mã trên cùng bộ chỉ tiêu, cùng một phiên dữ liệu. Tối đa 10 mã."""
        return chay(so_sanh_cung_nganh, tickers, metric_codes, industry_code)

    @beta_tool
    def get_corporate_events(ticker: str, event_type: str | None = None,
                             from_date: str | None = None, to_date: str | None = None,
                             limit: int | None = None) -> str:
        """Sự kiện doanh nghiệp: cổ tức tiền mặt, cổ tức cổ phiếu, phát hành thêm, đại hội, IPO.

        event_type ∈ 'CashDividend' | 'StockDividend' | 'ShareIssuance' | 'AGM' | 'Earning' | 'IPO'.
        """
        return chay(su_kien_doanh_nghiep, ticker, event_type, from_date, to_date, limit)

    @beta_tool
    def get_industry_tree(industry_code: str | None = None, ticker: str | None = None) -> str:
        """Khung ngành của hệ thống: 6 nhóm × 24 ngành, hoặc ngành của một mã cụ thể.

        Đây là khung ngành DUY NHẤT dùng để phân tích và hiển thị. Bỏ trống cả hai tham số để
        lấy toàn bộ cây.
        """
        return chay(cay_nganh, industry_code, ticker)

    @beta_tool
    def get_macro_series(code: str | None = None, keyword: str | None = None,
                         from_date: str | None = None, to_date: str | None = None,
                         limit: int | None = None) -> str:
        """Chuỗi vĩ mô Việt Nam/Mỹ và giá tài sản (hàng hoá, tiền tệ, chỉ số quốc tế, crypto).

        Không biết mã thì để trống code và truyền keyword để lấy DANH MỤC chuỗi khớp, rồi gọi
        lại với code. Ví dụ mã: 'vn.cpi', 'vn.m2', 'us.yield.10y', 'wti', 'gold.sjc_sell',
        'fx.usd_vnd.central', 'idx.sp500', 'btc'.
        """
        return chay(chuoi_vi_mo, code, keyword, from_date, to_date, limit)

    @beta_tool
    def get_news(query: str | None = None, ticker: str | None = None, group_no: int | None = None,
                 sub: str | None = None, industry_code: str | None = None,
                 from_date: str | None = None, to_date: str | None = None,
                 limit: int | None = None) -> str:
        """Tìm tin tức tài chính trong kho.

        query: tìm toàn văn (ưu tiên khớp đúng cụm). ticker/group_no/sub/industry_code: lọc theo
        nhãn — chỉ khớp những bài đã được phân loại. Mỗi bài trả kèm cờ da_phan_loai.
        """
        return chay(tim_tin, query, ticker, group_no, sub, industry_code, from_date, to_date, limit)

    @beta_tool
    def load_knowledge_reference(topic: str) -> str:
        """Đọc một tài liệu kiến thức chuyên sâu khi cần công thức, quy trình hoặc định nghĩa.

        topic ∈ 'valuation' (định giá, DCF, FCFF/FCFE, WACC, P/E, P/B) | 'financial-statements'
        (đọc BCTC, các chỉ số) | 'macro-money-creation' (vĩ mô, tiền tệ, tín dụng) |
        'technical-indicators' (chỉ báo kỹ thuật) | 'technical-supply-demand' (cung cầu, dòng
        tiền) | 'portfolio-and-rotation' (danh mục, luân chuyển ngành) | 'psychology-information'
        (tâm lý, thông tin) | 'advanced' (CAPM, Fama-French, APT, phòng hộ) | 'tong-quan'.
        """
        return doc_tri_thuc(topic)

    return [get_price_series, get_financials, screen_stocks, compare_peers, get_corporate_events,
            get_industry_tree, get_macro_series, get_news, load_knowledge_reference]
```

- [ ] **Bước 5: Chạy để thấy xanh**

Run: `uv run --project backend pytest tests/agent/test_a12_tools_log.py -q`
Expected: `5 passed`. Nếu `test_khong_tham_so_tuy_chon_nao_bi_required` đỏ, **không** nới test — sửa chữ ký hàm cho có default.

- [ ] **Bước 6: Commit** — `git commit -m "feat(agent): register nine tools as closures; log each model request"`

---

## Task 13 — Vòng chat

**Files:** Create `backend/agent/chat.py`, `backend/agent/__main__.py`, `backend/tests/agent/test_a13_chat.py`

**Interfaces — Produces:**
```python
REMINDER: str
def run_turn(llm, read_eng, ops_eng, history: list[dict], cau_hoi: str) -> tuple[str, list[dict]]
def repl(llm, read_eng, ops_eng) -> None
```

- [ ] **Bước 1: Viết test đỏ**

```python
# backend/tests/agent/test_a13_chat.py
"""Seam S6 — vòng chat, chạy với model GIẢ (không gọi API thật).

🔴 Test quan trọng nhất của lát: generate_tool_call_response() CÓ CACHE, còn append_messages()
XOÁ cache. Nếu gọi generate rồi append thì vòng lặp bên trong SDK gọi generate lần nữa với
cache rỗng ⇒ MỌI function chạy HAI LẦN, mà lịch sử message vẫn đúng nên không có gì báo.
test_tool_chay_dung_mot_lan là chốt canh đúng lỗi đó.

Model giả dựng bằng httpx2.MockTransport — cùng khuôn đã dùng ở tests/core/test_llm_client.py.
"""
import json

import httpx2
import pytest

from agent.chat import REMINDER, run_turn


def _msg(blocks, stop, **usage):
    return {"id": "msg_1", "type": "message", "role": "assistant", "model": "MiniMax-M3",
            "content": blocks, "stop_reason": stop, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5, **usage}}


@pytest.fixture()
def llm_gia(monkeypatch):
    """Lượt 1 gọi tool, lượt 2 trả lời."""
    lan = {"n": 0}

    def handler(request: httpx2.Request) -> httpx2.Response:
        lan["n"] += 1
        if lan["n"] == 1:
            body = _msg([{"type": "thinking", "thinking": "nghi", "signature": "SIG-1"},
                         {"type": "tool_use", "id": "tu_1", "name": "get_price_series",
                          "input": {"ticker": "HPG"}}], "tool_use")
        else:
            body = _msg([{"type": "text", "text": "Giá đóng cửa HPG là 21.600 đồng."}], "end_turn")
        handler.requests.append(json.loads(request.content))
        return httpx2.Response(200, json=body)

    handler.requests = []
    from core.llm.client import LLMClient
    from core.llm.settings import LLMSettings
    s = LLMSettings(api_key="x", base_url="https://api.minimax.io/anthropic", model="MiniMax-M3", timeout_s=30)
    yield LLMClient(s, http_client=httpx2.Client(transport=httpx2.MockTransport(handler))), handler


def test_tool_chay_dung_mot_lan(llm_gia, migrated_engine):
    llm, handler = llm_gia
    dem = {"n": 0}

    from agent import chat as chat_mod

    def build_gia(engine):
        from anthropic import beta_tool

        @beta_tool
        def get_price_series(ticker: str, from_date: str | None = None,
                             to_date: str | None = None, adjusted: bool = True) -> str:
            """Giá cổ phiếu."""
            dem["n"] += 1
            return json.dumps({"ma": ticker, "dong_cua": "21.600 đ"}, ensure_ascii=False)

        return [get_price_series]

    chat_mod.build_tools = build_gia
    tra_loi, lich_su = run_turn(llm, migrated_engine, None, [], "Giá HPG?")
    assert dem["n"] == 1, "tool bị gọi lại — xem lại chỗ cache của generate_tool_call_response"
    assert "21.600" in tra_loi


def test_loi_nhac_di_kem_tool_result(llm_gia, migrated_engine):
    llm, handler = llm_gia
    from agent import chat as chat_mod
    from anthropic import beta_tool

    @beta_tool
    def get_price_series(ticker: str, from_date: str | None = None,
                         to_date: str | None = None, adjusted: bool = True) -> str:
        """Giá cổ phiếu."""
        return "{}"

    chat_mod.build_tools = lambda e: [get_price_series]
    run_turn(llm, migrated_engine, None, [], "Giá HPG?")
    lượt_hai = handler.requests[1]["messages"]
    khoi = lượt_hai[-1]["content"]
    assert any(b.get("type") == "tool_result" for b in khoi)
    assert any(b.get("type") == "text" and REMINDER[:30] in b["text"] for b in khoi)


def test_thinking_signature_duoc_echo(llm_gia, migrated_engine):
    llm, handler = llm_gia
    from agent import chat as chat_mod
    from anthropic import beta_tool

    @beta_tool
    def get_price_series(ticker: str, from_date: str | None = None,
                         to_date: str | None = None, adjusted: bool = True) -> str:
        """Giá cổ phiếu."""
        return "{}"

    chat_mod.build_tools = lambda e: [get_price_series]
    run_turn(llm, migrated_engine, None, [], "Giá HPG?")
    assistant = handler.requests[1]["messages"][-2]
    assert any(b.get("signature") == "SIG-1" for b in assistant["content"])


def test_lich_su_song_qua_hai_luot(llm_gia, migrated_engine):
    llm, handler = llm_gia
    from agent import chat as chat_mod
    from anthropic import beta_tool

    @beta_tool
    def get_price_series(ticker: str, from_date: str | None = None,
                         to_date: str | None = None, adjusted: bool = True) -> str:
        """Giá cổ phiếu."""
        return "{}"

    chat_mod.build_tools = lambda e: [get_price_series]
    _, lich_su = run_turn(llm, migrated_engine, None, [], "Giá HPG?")
    assert lich_su[0]["role"] == "user" and lich_su[0]["content"] == "Giá HPG?"
    assert lich_su[-1]["role"] == "assistant"
```

- [ ] **Bước 2: Chạy để thấy đỏ**
- [ ] **Bước 3: Viết `chat.py`**

```python
"""Vòng chat nhiều lượt trong terminal.

BA điều đã đọc thẳng mã SDK anthropic 1.4.0, đừng đổi nếu chưa đọc lại:
1. runner.__run__() được tạo MỘT LẦN trong __init__ và cạn khi stop_reason='end_turn'. Runner
   đã cạn gọi lại thì KHÔNG ném lỗi, KHÔNG gửi request, trả lại message cũ — hỏng im lặng.
   ⇒ mỗi lượt người dùng dựng runner MỚI, lịch sử do mình tự giữ.
2. generate_tool_call_response() có cache; append_messages() XOÁ cache. Gọi generate rồi
   append ⇒ vòng lặp trong SDK gọi generate lần nữa ⇒ mọi function chạy HAI LẦN, im lặng.
   ⇒ sửa response TẠI CHỖ và KHÔNG gọi append_messages.
3. Runner tự nối lượt assistant nguyên văn, nên block thinking kèm signature được echo đúng.
"""
from __future__ import annotations

import time

from agent.llm_log import log_llm_call
from agent.system_prompt import build_system_blocks
from agent.tools import build_tools

REMINDER = ("Dữ liệu trên là số thật vừa tra được — dùng đúng số này, đừng lấy số ví dụ trong "
            "tài liệu kiến thức. Trả lời tiếp theo đúng hình dạng đã định: có mạch lập luận, "
            "kết luận có điều kiện, nói rõ số nào tra được và số nào là giả định, không lộ mã "
            "chỉ tiêu thô.")

MAX_ITERATIONS = 8


def run_turn(llm, read_eng, ops_eng, history: list[dict], cau_hoi: str) -> tuple[str, list[dict]]:
    messages = [*history, {"role": "user", "content": cau_hoi}]
    runner = llm.raw.beta.messages.tool_runner(
        model=llm.settings.model, max_tokens=4000, system=build_system_blocks(),
        messages=messages, tools=build_tools(read_eng),
        thinking={"type": "adaptive"}, max_iterations=MAX_ITERATIONS,
    )
    tra_loi, t0 = "", time.monotonic()
    for message in runner:
        if ops_eng is not None:
            log_llm_call(ops_eng, message, model=llm.settings.model,
                         latency_ms=int((time.monotonic() - t0) * 1000))
        t0 = time.monotonic()
        if message.stop_reason == "tool_use":
            response = runner.generate_tool_call_response()
            if response is not None:
                response["content"] = [*response["content"], {"type": "text", "text": REMINDER}]
                # KHÔNG append_messages ở đây — xem ghi chú (2) đầu file.
            messages = [*messages, {"role": message.role, "content": message.content}]
            if response is not None:
                messages = [*messages, response]
        else:
            tra_loi = "".join(b.text for b in message.content if b.type == "text")
            messages = [*messages, {"role": message.role, "content": message.content}]
    return tra_loi, messages


def repl(llm, read_eng, ops_eng) -> None:
    print("Hỏi về chứng khoán, tài chính, kinh tế. Ctrl+C để thoát.\n")
    history: list[dict] = []
    while True:
        try:
            cau = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTạm biệt.")
            return
        if not cau:
            continue
        t0 = time.monotonic()
        tra_loi, history = run_turn(llm, read_eng, ops_eng, history, cau)
        print(f"\nTrợ lý: {tra_loi}\n")
        q = llm.token_plan_remains()
        print(f"[{time.monotonic() - t0:.1f}s · quota 5h còn {q.interval_pct}% · tuần {q.weekly_pct}%]\n")
```

- [ ] **Bước 4: Viết `__main__.py`**

```python
"""`python -m agent` — vòng chat terminal của tầng ngữ nghĩa."""
from __future__ import annotations

import sys

from core.env import load_dotenv

load_dotenv()

from agent.chat import repl                      # noqa: E402 — phải nạp .env trước
from agent.db import ops_engine, read_engine     # noqa: E402
from core.llm.client import LLMClient            # noqa: E402
from core.llm.settings import LLMSettings        # noqa: E402


def main() -> int:
    read_eng = read_engine()          # assert_read_only chạy ở đây — sai quyền là chết ngay
    ops_eng = ops_engine()
    with LLMClient(LLMSettings.from_env()) as llm:
        repl(llm, read_eng, ops_eng)
    read_eng.dispose()
    ops_eng.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Bước 5: Chạy để thấy xanh**

Run: `uv run --project backend pytest tests/agent/ -q`
Expected: tất cả xanh. Nếu `LLMSettings(...)` trong fixture sai chữ ký, mở `backend/core/llm/settings.py` đọc chữ ký thật rồi sửa **fixture** cho khớp.

- [ ] **Bước 6: Chạy toàn bộ bộ test**

Run: `uv run --project backend pytest -q`
Expected: không test cũ nào đỏ. Dán dòng tóm tắt vào ledger.

- [ ] **Bước 7: Commit** — `git commit -m "feat(agent): multi-turn terminal chat loop over tool_runner"`

---

## Task 14 — Chạy thật: nghiệm thu và bộ hồi quy vòng 7

**Files:** Create `docs/90-records/plans/2026-09-07-semantic-layer/round7-results-2026-09-XX.md`; Modify `ledger.md`

- [ ] **Bước 1: AC1 + AC5 + AC6 — chạy tay `python -m agent`**

Run: `PYTHONIOENCODING=utf-8 uv run --project backend python -m agent` (**tiền cảnh**)

Hỏi lần lượt, dán nguyên văn transcript vào ledger:

1. `Giá đóng cửa HPG phiên 2026-09-03 là bao nhiêu?` → phải gọi function, trả **21.600 đ**.
2. `VN-Index hôm nay bao nhiêu điểm?` → phải **nói thẳng kho chưa có dữ liệu chỉ số**, không bịa, không thay bằng chỉ số khác (AC6).
3. `Cho tôi công thức nấu phở bò.` → từ chối gọn một câu (AC5).
4. `Viết giúp tôi hàm Python đảo ngược chuỗi.` → từ chối gọn một câu (AC5).
5. `Tôi bị đau lưng, uống thuốc gì?` → từ chối (AC5).
6. `Luật đất đai 2024 quy định gì về sổ đỏ?` → từ chối (AC5).

- [ ] **Bước 2: AC9 — kiểm không rò kết nối**

Sau khi thoát chat, chạy:
```sql
SELECT count(*) FROM pg_stat_activity
WHERE usename = 'agent_reader' AND state = 'idle in transaction';
```
Expected: `0`. Dán vào ledger.

- [ ] **Bước 3: AC7 — chạy bộ hồi quy vòng 7**

Hỏi lần lượt **15 câu** trong [`regression-round7.md`](regression-round7.md), **tiền cảnh, chia khối 5 câu** (job gọi model chạy nền bị đóng băng — nguyên nhân chưa xác định). Lưu trọn transcript từng câu.

- [ ] **Bước 4: Chấm bằng subagent Sonnet độc lập**

Giao một subagent (**model `sonnet`**) đề bài tự đủ: 15 câu hỏi + đáp án + rubric hai lớp ở `regression-round7.md` §Chấm + 15 transcript. Yêu cầu trả bảng: mỗi câu — số đúng/sai, hình dạng x/5, mục nào trượt. **Không** cho subagent biết câu trả lời do model nào sinh.

- [ ] **Bước 5: AC8 — đo chi phí thật**

```sql
SELECT count(*) AS so_request,
       percentile_disc(0.5) WITHIN GROUP (ORDER BY input_tokens)  AS vao_p50,
       percentile_disc(0.5) WITHIN GROUP (ORDER BY output_tokens) AS ra_p50,
       percentile_disc(0.5) WITHIN GROUP (ORDER BY latency_ms)    AS tre_p50,
       percentile_disc(0.9) WITHIN GROUP (ORDER BY latency_ms)    AS tre_p90,
       sum(input_tokens) * 0.30 / 1e6 + sum(output_tokens) * 1.20 / 1e6 AS usd
FROM ops.llm_call WHERE purpose = 'chat';
```
Dán kết quả; chia cho 15 để ra $/câu và so với ước lượng $0,022–0,048 của spec §4.3.

- [ ] **Bước 6: Viết hồ sơ kết quả**

Tạo `round7-results-2026-09-XX.md`: 15 transcript, bảng chấm hai lớp, số lần model gọi mỗi function, số đo chi phí. Nếu **không** đạt 15/15 hoặc ≥ 2 câu hỏng hình dạng: **ghi nguyên trạng**, không sửa cho đẹp — đó là phát hiện của lát.

- [ ] **Bước 7: Commit**

```bash
git add docs/90-records/plans/2026-09-07-semantic-layer/
git commit -m "docs(agent): round-7 regression results and measured cost per question"
```

---

## Task 15 — Đồng bộ tài liệu và đóng lát

**Files:** Modify `docs/20-design/chatbot-semantic-layer.md`, `docs/20-design/market-data-store.md`, `docs/30-skills/maintenance.md`, `docs/00-overview/roadmap.md`, `docs/90-records/README.md`, `backend/README.md`

- [ ] **Bước 1: `chatbot-semantic-layer.md`**

Bỏ nhãn "🟡 đề xuất, chưa duyệt" ở đầu; đổi §2 từ 8 → **9 function** với chữ ký thật đã dựng; **xoá `icb_level`** khỏi `get_industry_tree`; §4 "Điều chưa biết" — đóng ba dòng đầu bằng số đo thật từ Task 14, giữ nguyên dòng đã đóng.

- [ ] **Bước 2: `market-data-store.md` §6.3**

Đồng bộ danh sách function (5 → 9, tên thật). Thêm một câu ở §6.2: ví dụ view dùng tên bảng `organization` là **lược đồ cũ trước spec 2026-08-25**, tên thật là `market.issuer`/`market.security`.

- [ ] **Bước 3: `maintenance.md` §6**

Thêm ghi chú: bộ vòng 6 **không còn trong repo** nên không tái lập được; con số "FCFF 260 tỷ" không đối chiếu được với bất cứ thứ gì còn lại (ví dụ DCF trong `valuation.md` cho 270 với số liệu khác) — **giữ nguyên, không sửa**; bộ thay thế là `regression-round7.md`, 15 câu, có lưu trong repo.

- [ ] **Bước 4: `roadmap.md`**

- Đổi dòng lát 10 thành ✅ XONG với số đo thật (số test, $/câu, kết quả vòng 7).
- Dòng 150 (`lát 11 test vòng 6`): ghi rõ **đã gộp vào lát 10** vì bộ vòng 6 mất và lát 10 phải tự dựng để nghiệm thu; số các lát sau **giữ nguyên**.
- Bảng ánh xạ `[13] · [14]`: sửa cho khớp.
- Dòng 145: **gỡ** "Chọn mô hình embedding DỜI sang lát 10" — chủ dự án đã chốt để sau lát 10.
- Viết mục **"Điểm vào cho lát 12"** (giám sát hợp đồng) theo khuôn các điểm vào cũ.

- [ ] **Bước 5: `docs/90-records/README.md`** — thêm hồ sơ `2026-09-07-semantic-layer/` vào index.

- [ ] **Bước 6: `backend/README.md`** — thêm một dòng về `python -m agent` và biến `AGENT_DATABASE_URL`.

- [ ] **Bước 7: AC10 — phép kiểm không còn tài liệu đá nhau**

```bash
git grep -n "icb_level" -- docs backend
git grep -n "lát 11" -- docs
git grep -n "DỜI sang lát 10" -- docs
git grep -n "8 function\|năm function" -- docs
```
Expected: mọi hit còn lại **hoặc đã đúng, hoặc nằm trong vùng lịch sử** (`decisions/`, `90-records/`). Dán kết quả vào ledger.

- [ ] **Bước 8: Commit và báo cáo**

```bash
git add docs backend/README.md
git commit -m "docs: close slice 10 — semantic layer live, docs synced, entry point for slice 12"
```

---

## Tự soát plan

**Phủ spec:** §4.1 → Task 1–13 · §4.2 → Task 13 · §4.3 → Task 3 · §4.4 (9 function) → Task 4–12 · §4.5 → Task 2, 7, 9, 10, 11 · §4.6 → Task 4, 5 · §4.7 → Task 1, 12 · §5 → Task 14 · §6 (S1–S7) → Task 1, 2, 3, 4, 5–11, 12, 13 · §7 (AC1–AC10) → Task 0, 13, 14, 15 · §9 → Task 15.

**Chỗ plan cố ý để mở** (không phải placeholder — là điểm quyết định lúc chạy):
- Task 0 bước 4: ba nhánh đường đi tuỳ kết quả spike, mỗi nhánh nói rõ làm gì.
- Task 3 bước 5 và Task 9 bước 5: nếu expected trong test lệch với file/kho thật thì **sửa test, không sửa nguồn** — nói rõ chiều sửa.
- Task 14 bước 6: kết quả xấu thì ghi nguyên trạng.

**Nhất quán tên:** `to_json`, `resolve_ticker`, `cap_limit`, `co_du_lieu`, `khong_co_du_lieu`, `khong_tim_thay`, `rong` định nghĩa ở Task 4 và dùng đúng tên đó ở Task 5–11. `display_metric`/`display_series_value`/`format_date_vi`/`LABELS`/`DEFAULT_BY_STATEMENT`/`DEFAULT_RATIOS` định nghĩa ở Task 2, dùng đúng tên ở Task 5, 7, 9, 10. `build_tools` (Task 12) được `chat.py` (Task 13) gọi đúng tên. `log_llm_call(ops_eng, message, *, purpose, model, latency_ms)` khớp giữa Task 12 và 13.
