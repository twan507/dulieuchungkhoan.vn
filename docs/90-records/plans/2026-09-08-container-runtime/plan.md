# Plan — lát 12: chạy được trong container

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sau lát này, một máy mới chỉ cần `git clone` + điền `.env` + `docker compose up -d --build` là hai kho dựng xong, bốn user login được cấp, và cả 15 họ job lẫn ingester chạy trong container; trên máy dev, native (`uv run …`) vẫn chạy với **cùng một `.env`**.

**Architecture:** `.env` chỉ khai nguyên tố (host · port · db · user · password); `core/env.py` ráp bảy biến `*_URL` mà code đang đọc, nên không consumer nào đổi dòng đọc và compose chỉ đè ba biến `*_HOST`. Một `docker-compose.yml` ở gốc repo (kho + `migrate` one-shot + `api` + `etl` + `ingester`), image tự đủ chứa `backend/` và `database/`, `core.bootstrap` migrate hai kho + cấp user + tự seed ngành lớp 2, ingester tự ngủ ngoài phiên, `SIGTERM` đi cùng đường Ctrl+C.

**Tech Stack:** Python 3.12 · uv 0.9.18 · SQLAlchemy 2 + psycopg 3 · alembic · clickhouse-connect · Docker Engine 29 / Compose v2.40 · pytest (+ `pyyaml` chỉ cho test đọc compose).

**Spec:** [`spec.md`](spec.md) — plan này lập luận từ spec; người thực thi đọc cả hai. Ba phương án hình dạng cấu hình nguyên văn ở [`options/`](options/).

**Ledger:** [`ledger.md`](ledger.md) — output thật của mỗi task (tạo ở Task 0).

## Global Constraints

- **Luật repo** ([CLAUDE.md](../../../../CLAUDE.md)): §4.4 sửa như phẫu thuật · §4.5 test đỏ trước, expected là literal · §3.5 nghiệm thu bằng lệnh thật dưới đúng credential · §5 **không bao giờ in giá trị secret** (kể cả trong ledger, test output, log) · commit Conventional Commits, message tiếng Anh.
- **Không đọc/sửa file `.env` thật.** Chỉ chủ dự án viết `.env`. Agent chỉ đọc `.env.example` và chạy `python -m core.env check` (in tên biến).
- **Luôn `PYTHONIOENCODING=utf-8`** khi chạy Python trên máy dev. Lệnh pytest chạy từ `backend/`: `cd backend && uv run pytest <đường dẫn> -q`. **Không chạy hai phiên pytest song song** (chung `dulieu_test`).
- **Subagent: model `sonnet` tường minh cho mọi task; không Haiku, không Fable** (CLAUDE.md §4.1).
- **Kho dev cũ (`infra_*`) còn chạy cho tới Task 9** — tests Task 1–8 dùng nó (chỉ `dulieu_test` + container ClickHouse tạm). Không `docker rm`/`docker volume rm` gì trước Task 9 và Task 12.
- Tên biến nguyên tố **đúng theo spec §5.1** — không đặt tên khác.
- Mọi ngày tháng trong test lấy từ literal cố định (2026-09-08 là **thứ 3**; 11/09 thứ 6; 12/09 thứ 7; 14/09 thứ 2) hoặc từ `date.today()` **chỉ trong test**.

---

## Bản đồ file

| File | Việc | Task |
|---|---|---|
| `backend/core/env.py` | + `URL_SPECS` · `compose_urls()` · `parse_dotenv()` · `check()` CLI; `load_dotenv()` ráp URL ở cuối | 1 |
| `backend/tests/core/test_env.py` | + 7 test ráp/kiểm | 1 |
| `.env.example` | viết lại theo nguyên tố | 2 |
| `backend/tests/core/test_env_contract.py` *(mới)* | `.env.example` ↔ `core.env` ↔ code | 2 |
| `backend/tests/conftest.py` · `backend/tests/test_conftest_env_contract.py` | admin URL từ `POSTGRES_DB`; tên DB test từ URL | 3 |
| `database/alembic.ini` · `database/migrations/env.py` | `prepend_sys_path`; `load_dotenv()` | 3 |
| `backend/core/ch_migrate.py` · `backend/core/ch_backup.py` · `backend/tests/clickhouse/test_t06_backup.py` | `load_dotenv()` ở `main()`; `resolve_backup_dir()` theo gốc repo | 3 |
| `backend/core/clock.py` *(mới)* · `backend/tests/core/test_clock.py` *(mới)* · `backend/tests/core/test_tz_contract.py` *(mới)* | `today_vn()`; ba chỗ sửa; phép kiểm tĩnh | 4 |
| `backend/etl/refdata_job.py` · `backend/agent/system_prompt.py` · `backend/core/ch_backup.py` | dùng `today_vn()` | 4 |
| `backend/core/shutdown.py` *(mới)* · `backend/tests/core/test_shutdown.py` *(mới)* | `SIGTERM` → `KeyboardInterrupt` | 5 |
| `backend/etl/__main__.py` · `backend/ingester/__main__.py` · `backend/etl/price_job.py` | gỡ console, gắn handler | 5 |
| **xoá** `backend/core/console.py` · `backend/tests/core/test_console.py` · `scripts/register-tasks.ps1` · `scripts/stack.mjs` · `scripts/stack.test.mjs` · `package.json` | về hưu | 5 |
| `backend/ingester/main.py` · `backend/tests/ingester/test_i16_daemon.py` *(mới)* | `SESSION_START` · `next_window()` · `daemon()` · `run()` rẽ nhánh | 6 |
| `deploy/backend.Dockerfile` · `.dockerignore` *(mới, gốc)* · `docker-compose.yml` *(mới, gốc)* · `docker-compose.vps.yml` *(mới, gốc)* | image tự đủ, compose gộp | 7 |
| **xoá** `backend/.dockerignore` · `deploy/infra/docker-compose.yml` · `deploy/infra/docker-compose.vps.yml` · `deploy/app/docker-compose.yml` | thay bằng file gốc | 7 |
| `backend/pyproject.toml` · `backend/tests/docs/test_d03_compose_contract.py` *(mới)* | `pyyaml` dev; hợp đồng compose/Dockerfile | 7 |
| `backend/core/bootstrap.py` *(mới)* · `backend/tests/core/test_bootstrap_postgres.py` *(mới)* · `backend/tests/core/test_bootstrap_clickhouse.py` *(mới)* | migrate + user + seed | 8 |
| **xoá** `database/clickhouse/create_users.sql.example` | bootstrap thay thế | 8 |
| `ledger.md` | output thật AC2, AC4, AC7, AC3, AC5, AC6, AC8, AC9 | 9–12 |
| `README.md` · `backend/README.md` · `database/README.md` · `docs/20-design/service-topology.md` · `docs/00-overview/roadmap.md` · `CLAUDE.md` · `docs/90-records/README.md` | tài liệu sống (spec §8) | 11 |

---

### Task 0: Sổ ledger và tiền kiểm

**Files:**
- Create: `docs/90-records/plans/2026-09-08-container-runtime/ledger.md`

- [ ] **Step 1: Ghi trạng thái xuất phát vào ledger** — tạo file với nội dung:

```markdown
# Ledger — lát 12: chạy được trong container

**Nhánh:** `feat/container-runtime` · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Mỗi task ghi output THẬT của bước kiểm (đỏ trước · xanh sau · lệnh nghiệm thu). Không dán giá trị secret.

## Task 0 — xuất phát 2026-09-08

- `git log --oneline -1`: (dán)
- `docker ps --format '{{.Names}} {{.Status}}' | grep infra`: (dán — kho cũ còn chạy, giữ tới Task 9)
- `docker volume ls --format '{{.Name}}' | grep -E 'infra|dlck'`: (dán — sáu volume sẽ xoá ở Task 12; `tutor-infra_pgdata` KHÔNG đụng)
- `cd backend && uv run pytest tests -q` (kho cũ, `.env` cũ): (dán dòng cuối — số xuất phát)
```

- [ ] **Step 2: Chạy ba lệnh trên, dán output thật vào ledger**

Run (từ gốc repo): `git log --oneline -1 && docker ps --format '{{.Names}} {{.Status}}' | grep infra && docker volume ls --format '{{.Name}}' | grep -E 'infra|dlck'`
Expected: `2e8814d …`; ba container `infra-*` `Up … (healthy)`; sáu volume `infra_*` + `dlck-infra_*` và `tutor-infra_pgdata`.

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests -q 2>&1 | tail -1`
Expected: `… passed, 2 skipped …` (số cụ thể ghi ledger; đây là mốc, không phải tiêu chí).

- [ ] **Step 3: Commit**

```bash
git add docs/90-records/plans/2026-09-08-container-runtime/ledger.md
git commit -m "docs(ledger): open the slice 12 ledger with the starting state"
```

---

### Task 1: `core/env.py` — ráp URL từ nguyên tố, CLI `check`

**Files:**
- Modify: `backend/core/env.py` (toàn bộ file, 22 dòng hiện tại)
- Test: `backend/tests/core/test_env.py` (giữ 2 test cũ, thêm 7)

**Interfaces:**
- Produces: `core.env.REPO_ROOT: Path` · `load_dotenv(path=None) -> None` (như cũ, thêm ráp URL) · `parse_dotenv(text) -> dict[str,str]` · `compose_urls(env: Mapping[str,str]) -> dict[str,str]` (thuần) · `check(path=None, out=sys.stdout) -> int` (0 đủ · 1 thiếu · 2 không có file) · hằng `URL_SPECS`, `DEFAULTS`, `ASSEMBLED_KEYS`, `REQUIRED_KEYS`, `OPTIONAL_KEYS`, `KNOWN_KEYS`, `PASSWORD_KEYS`.
- Task 2 dùng `KNOWN_KEYS`/`REQUIRED_KEYS`/`ASSEMBLED_KEYS`/`parse_dotenv`; Task 8 dùng `load_dotenv`; mọi consumer hiện có không đổi.

- [ ] **Step 1: Viết test đỏ** — thêm vào cuối `backend/tests/core/test_env.py`:

```python
import io

from core.env import ASSEMBLED_KEYS, REQUIRED_KEYS, check, compose_urls

BASE = {
    "POSTGRES_HOST": "127.0.0.1", "POSTGRES_PORT": "5432", "POSTGRES_DB": "dulieu",
    "POSTGRES_USER": "dulieu", "POSTGRES_PASSWORD": "pw-owner",
    "ETL_DB_USER": "etl_worker", "ETL_DB_PASSWORD": "p@ss:w/rd",
    "AGENT_DB_USER": "agent_reader", "AGENT_DB_PASSWORD": "pw-agent",
    "REDIS_HOST": "127.0.0.1", "REDIS_PORT": "6379",
    "CLICKHOUSE_HOST": "127.0.0.1", "CLICKHOUSE_PORT": "8123", "CLICKHOUSE_PASSWORD": "pw-ch",
    "CLICKHOUSE_INGESTER_USER": "ingester_worker", "CLICKHOUSE_INGESTER_PASSWORD": "pw-ing",
}


def test_compose_urls_literal_shapes():
    """Expected là chuỗi literal (§4.5.3) — mật khẩu `p@ss:w/rd` phải thành `p%40ss%3Aw%2Frd`."""
    assert compose_urls(BASE) == {
        "DATA_DATABASE_URL": "postgresql+psycopg://dulieu:pw-owner@127.0.0.1:5432/dulieu",
        "TEST_DATABASE_URL": "postgresql+psycopg://dulieu:pw-owner@127.0.0.1:5432/dulieu_test",
        "ETL_DATABASE_URL": "postgresql+psycopg://etl_worker:p%40ss%3Aw%2Frd@127.0.0.1:5432/dulieu",
        "AGENT_DATABASE_URL": "postgresql+psycopg://agent_reader:pw-agent@127.0.0.1:5432/dulieu",
        "CLICKHOUSE_URL": "http://default:pw-ch@127.0.0.1:8123",
        "CLICKHOUSE_INGESTER_URL": "http://ingester_worker:pw-ing@127.0.0.1:8123",
        "REDIS_URL": "redis://127.0.0.1:6379/0",
    }


def test_compose_urls_skips_a_url_whose_part_is_missing():
    env = dict(BASE)
    del env["ETL_DB_PASSWORD"]
    urls = compose_urls(env)
    assert "ETL_DATABASE_URL" not in urls
    assert urls["DATA_DATABASE_URL"] == "postgresql+psycopg://dulieu:pw-owner@127.0.0.1:5432/dulieu"


def test_compose_urls_optional_parts_override_defaults():
    urls = compose_urls({**BASE, "POSTGRES_TEST_DB": "khac_test", "REDIS_DB": "3"})
    assert urls["TEST_DATABASE_URL"] == "postgresql+psycopg://dulieu:pw-owner@127.0.0.1:5432/khac_test"
    assert urls["REDIS_URL"] == "redis://127.0.0.1:6379/3"


def test_load_dotenv_composes_urls_but_an_existing_url_wins(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("\n".join(f"{k}={v}" for k, v in BASE.items()) + "\n", encoding="utf-8")
    for k in ASSEMBLED_KEYS | set(BASE):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("REDIS_URL", "redis://da-co-san:1/9")
    load_dotenv(f)
    assert os.environ["ETL_DATABASE_URL"] == "postgresql+psycopg://etl_worker:p%40ss%3Aw%2Frd@127.0.0.1:5432/dulieu"
    assert os.environ["REDIS_URL"] == "redis://da-co-san:1/9"


def test_load_dotenv_composes_even_when_the_file_is_absent(tmp_path, monkeypatch):
    """Container: compose đã bơm nguyên tố vào env, không có file .env — vẫn phải ráp."""
    for k in ASSEMBLED_KEYS | set(BASE):
        monkeypatch.delenv(k, raising=False)
    for k, v in BASE.items():
        monkeypatch.setenv(k, v)
    load_dotenv(tmp_path / "khong-co.env")
    assert os.environ["CLICKHOUSE_URL"] == "http://default:pw-ch@127.0.0.1:8123"


def test_check_prints_names_only_and_exits_1_when_missing(tmp_path):
    f = tmp_path / ".env"
    f.write_text("POSTGRES_HOST=127.0.0.1\nBIEN_LA=gia-tri-bi-mat-xyz\n", encoding="utf-8")
    out = io.StringIO()
    rc = check(f, out=out)
    text = out.getvalue()
    assert rc == 1
    assert "THIẾU  POSTGRES_PASSWORD" in text and "LẠ     BIEN_LA" in text
    assert "gia-tri-bi-mat-xyz" not in text and "127.0.0.1" not in text


def test_check_exits_0_when_every_required_key_is_present(tmp_path):
    f = tmp_path / ".env"
    f.write_text("\n".join(f"{k}=x" for k in sorted(REQUIRED_KEYS)) + "\n", encoding="utf-8")
    out = io.StringIO()
    assert check(f, out=out) == 0
    assert "đủ" in out.getvalue()
```

- [ ] **Step 2: Chạy, xác nhận đỏ**

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/core/test_env.py -q`
Expected: `ImportError: cannot import name 'ASSEMBLED_KEYS' from 'core.env'` (thu thập thất bại — đỏ).

- [ ] **Step 3: Viết `backend/core/env.py`** — thay toàn bộ file:

```python
"""Nạp `.env` gốc repo và RÁP chuỗi kết nối từ nguyên tố (lát 12, spec §5.1).

- `.env` chỉ khai NGUYÊN TỐ: host · port · db · user · password. Bảy biến `*_URL` mà code
  đang đọc được ráp ở cuối `load_dotenv()` bằng `setdefault`: biến đã có sẵn trong môi
  trường thắng; thiếu nguyên tố thì bỏ qua URL đó (consumer tự thi hành "thiếu env ⇒ exit 2").
- Không đè biến đã có; không bao giờ in giá trị (CLAUDE.md §5) — `check` chỉ in TÊN biến.
- Tiến trình từ container không có file `.env` (compose đã bơm nguyên tố) ⇒ vẫn ráp.
"""
from __future__ import annotations

import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parents[2]

# Nguyên tố tuỳ chọn và mặc định — dùng cả khi ráp lẫn khi `check`.
DEFAULTS = {"POSTGRES_TEST_DB": "dulieu_test", "REDIS_DB": "0"}

# (biến ráp, khuôn, nguyên tố BẮT BUỘC). Nguyên tố tuỳ chọn trong khuôn lấy từ DEFAULTS.
URL_SPECS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("DATA_DATABASE_URL",
     "postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
     ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB")),
    ("TEST_DATABASE_URL",
     "postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_TEST_DB}",
     ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT")),
    ("ETL_DATABASE_URL",
     "postgresql+psycopg://{ETL_DB_USER}:{ETL_DB_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
     ("ETL_DB_USER", "ETL_DB_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB")),
    ("AGENT_DATABASE_URL",
     "postgresql+psycopg://{AGENT_DB_USER}:{AGENT_DB_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
     ("AGENT_DB_USER", "AGENT_DB_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB")),
    ("CLICKHOUSE_URL",
     "http://default:{CLICKHOUSE_PASSWORD}@{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}",
     ("CLICKHOUSE_PASSWORD", "CLICKHOUSE_HOST", "CLICKHOUSE_PORT")),
    ("CLICKHOUSE_INGESTER_URL",
     "http://{CLICKHOUSE_INGESTER_USER}:{CLICKHOUSE_INGESTER_PASSWORD}@{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}",
     ("CLICKHOUSE_INGESTER_USER", "CLICKHOUSE_INGESTER_PASSWORD", "CLICKHOUSE_HOST", "CLICKHOUSE_PORT")),
    ("REDIS_URL", "redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}", ("REDIS_HOST", "REDIS_PORT")),
)
ASSEMBLED_KEYS = frozenset(name for name, _, _ in URL_SPECS)
PASSWORD_KEYS = frozenset(k for _, _, parts in URL_SPECS for k in parts if k.endswith("_PASSWORD"))
# Bắt buộc = mọi nguyên tố của bảy URL + hai biến chỉ bootstrap dùng (spec §5.1).
REQUIRED_KEYS = frozenset(k for _, _, parts in URL_SPECS for k in parts) | {
    "CLICKHOUSE_API_USER", "CLICKHOUSE_API_PASSWORD"}
OPTIONAL_KEYS = frozenset(DEFAULTS) | {
    "CLICKHOUSE_BACKUP_DIR", "INGESTER_LOG_DIR", "INGESTER_MEASURE_DIR", "INGESTER_SPILL_DIR",
    "LLM_API", "LLM_BASE_URL", "LLM_MODEL", "LLM_TIMEOUT_S", "FRED_API",
    "COMPOSE_FILE", "COMPOSE_PROJECT_NAME"}
KNOWN_KEYS = REQUIRED_KEYS | OPTIONAL_KEYS

_PLACEHOLDER = re.compile(r"{(\w+)}")


def parse_dotenv(text: str) -> dict[str, str]:
    """`KEY=value` mỗi dòng; bỏ dòng trống/`#`. KHÔNG hỗ trợ comment cuối dòng — giá trị lấy trọn."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip()
    return out


def compose_urls(env: Mapping[str, str]) -> dict[str, str]:
    """Ráp những URL ráp được từ `env`. Thuần — không đụng `os.environ`. Mật khẩu được URL-encode."""
    urls: dict[str, str] = {}
    for name, template, required in URL_SPECS:
        if any(not env.get(k) for k in required):
            continue
        parts = {k: env.get(k) or DEFAULTS.get(k, "") for k in _PLACEHOLDER.findall(template)}
        parts = {k: (quote(v, safe="") if k in PASSWORD_KEYS else v) for k, v in parts.items()}
        urls[name] = template.format(**parts)
    return urls


def load_dotenv(path: Path | None = None) -> None:
    p = path or (REPO_ROOT / ".env")
    if p.is_file():
        for key, value in parse_dotenv(p.read_text(encoding="utf-8")).items():
            os.environ.setdefault(key, value)
    for name, url in compose_urls(os.environ).items():
        os.environ.setdefault(name, url)


def check(path: Path | None = None, out=sys.stdout) -> int:
    """In TÊN biến bắt buộc còn thiếu và biến lạ của file `.env` — không bao giờ in giá trị.
    0 = đủ · 1 = thiếu · 2 = không có file."""
    p = path or (REPO_ROOT / ".env")
    if not p.is_file():
        print(f"không thấy {p}", file=out)
        return 2
    keys = set(parse_dotenv(p.read_text(encoding="utf-8")))
    missing = sorted(REQUIRED_KEYS - keys)
    unknown = sorted(keys - KNOWN_KEYS)
    for k in missing:
        print(f"THIẾU  {k}", file=out)
    for k in unknown:
        print(f"LẠ     {k}", file=out)
    if not missing and not unknown:
        print(f"đủ {len(REQUIRED_KEYS)} biến bắt buộc, không biến lạ", file=out)
    return 1 if missing else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd != "check":
        sys.exit(f"lệnh không biết: {cmd} (hỗ trợ: check)")
    raise SystemExit(check())
```

- [ ] **Step 4: Chạy, xác nhận xanh (cả 2 test cũ lẫn 7 mới)**

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/core/test_env.py tests/test_conftest_env_contract.py -q`
Expected: `11 passed` (9 ở `test_env.py` + 2 hợp đồng cũ — `.env` thật hiện vẫn có `TEST_DATABASE_URL` nên hợp đồng vẫn xanh).

- [ ] **Step 5: Commit**

```bash
git add backend/core/env.py backend/tests/core/test_env.py
git commit -m "feat(core): assemble the seven connection URLs from elemental .env values"
```

---

### Task 2: `.env.example` nguyên tố + hợp đồng `.env.example` ↔ code · **chủ dự án viết lại `.env`**

**Files:**
- Modify: `.env.example` (viết lại toàn bộ)
- Create: `backend/tests/core/test_env_contract.py`

**Interfaces:**
- Consumes: `core.env.ASSEMBLED_KEYS`, `KNOWN_KEYS`, `REQUIRED_KEYS`, `parse_dotenv` (Task 1).

- [ ] **Step 1: Viết test đỏ** `backend/tests/core/test_env_contract.py`:

```python
"""`.env.example` ↔ `core.env` ↔ code phải cùng nói một chuyện (spec lát 12 §6, CLAUDE.md §1.7).

Ba vế: (1) mọi khoá trong `.env.example` đều là khoá `core.env` biết; (2) mọi khoá bắt buộc
có mặt và KHÔNG bị comment; (3) không khai khoá nào trong bảy URL RÁP (`ASSEMBLED_KEYS`) — URL kết nối là thứ ráp,
không phải thứ khai; khoá `*_URL` khác (vd `LLM_BASE_URL`) hợp lệ khi thuộc `KNOWN_KEYS`.
Vế 4 soi CODE: mọi tên env đọc bằng literal trong code sản phẩm phải là khoá biết hoặc khoá ráp.
"""
from __future__ import annotations

import re
from pathlib import Path

from core.env import ASSEMBLED_KEYS, KNOWN_KEYS, REQUIRED_KEYS, parse_dotenv

REPO = Path(__file__).resolve().parents[3]
CODE_DIRS = [REPO / "backend" / d for d in ("core", "etl", "ingester", "agent", "api")] + [
    REPO / "database" / "migrations"]
# Tên env code đọc nhưng KHÔNG thuộc `.env` của dự án (do hệ điều hành/compose cấp).
FOREIGN = {"TZ"}
_READ = re.compile(r'(?:os\.environ|\benv)(?:\.get\(|\[)\s*"([A-Z][A-Z0-9_]+)"')


def _example_keys() -> tuple[set[str], set[str]]:
    text = (REPO / ".env.example").read_text(encoding="utf-8")
    active = set(parse_dotenv(text))
    commented = set(re.findall(r"^#\s*([A-Z][A-Z0-9_]+)=", text, re.M))
    return active, commented


def test_example_only_contains_keys_core_env_knows():
    active, commented = _example_keys()
    assert (active | commented) <= KNOWN_KEYS, sorted((active | commented) - KNOWN_KEYS)


def test_example_has_every_required_key_uncommented():
    active, _ = _example_keys()
    assert REQUIRED_KEYS <= active, sorted(REQUIRED_KEYS - active)


def test_example_declares_no_assembled_url():
    """URL kết nối là thứ RÁP, không phải thứ khai. (Ruling khi thực thi 2026-09-08: bản đầu còn cấm mọi
    khoá đuôi `_URL` — sai, vì `LLM_BASE_URL` là endpoint API tuỳ chọn hợp lệ trong `OPTIONAL_KEYS`;
    khoá lạ đuôi `_URL` đã bị vế `test_example_only_contains_keys_core_env_knows` chặn.)"""
    active, commented = _example_keys()
    keys = active | commented
    assert not (keys & ASSEMBLED_KEYS), sorted(keys & ASSEMBLED_KEYS)


def test_every_env_name_read_in_code_is_a_known_or_assembled_key():
    seen: dict[str, str] = {}
    for d in CODE_DIRS:
        for p in d.rglob("*.py"):
            for m in _READ.finditer(p.read_text(encoding="utf-8")):
                seen.setdefault(m.group(1), p.relative_to(REPO).as_posix())
    assert len(seen) >= 10, f"phép kiểm quét được quá ít tên ({len(seen)}) — nghi regex hụt"
    unknown = {k: v for k, v in seen.items() if k not in KNOWN_KEYS | ASSEMBLED_KEYS | FOREIGN}
    assert not unknown, unknown
```

- [ ] **Step 2: Chạy, xác nhận đỏ**

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/core/test_env_contract.py -q`
Expected: 3 đỏ (`.env.example` cũ có `APP_ENV`/`LOG_LEVEL`/`COMPOSE_PROFILES` lạ; thiếu `ETL_DB_USER`…; còn 7 khoá `*_URL`), vế code xanh.

- [ ] **Step 3: Viết lại `.env.example`** (không comment cuối dòng — `parse_dotenv` lấy trọn giá trị):

```
# .env — MỘT file cho một máy, chỉ khai NGUYÊN TỐ (lát 12, 2026-09-08).
# Bảy biến *_URL được backend/core/env.py RÁP lúc chạy — KHÔNG khai URL ở đây.
# Native trên dev nối 127.0.0.1; trong container, compose đè POSTGRES_HOST/REDIS_HOST/
# CLICKHOUSE_HOST bằng tên service. Kiểm tên biến (không in giá trị):
#     cd backend && uv run python -m core.env check
# Không comment cuối dòng: giá trị được lấy trọn tới hết dòng.

# --- Postgres, user owner: compose dựng kho · alembic · bootstrap ---
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=dulieu
POSTGRES_USER=dulieu
POSTGRES_PASSWORD=change-me
# DB test do pytest tự dựng lại; mặc định dulieu_test
# POSTGRES_TEST_DB=dulieu_test

# --- User login Postgres — bootstrap tạo và đổi mật khẩu theo đây mỗi lần `docker compose up` ---
# etl_worker thuộc role dlck_etl: 15 họ job + sổ ops.llm_call của agent
ETL_DB_USER=etl_worker
ETL_DB_PASSWORD=change-me
# agent_reader thuộc role dlck_api: python -m agent, chỉ đọc 4 schema miền
AGENT_DB_USER=agent_reader
AGENT_DB_PASSWORD=change-me

# --- Redis ---
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
# REDIS_DB=0

# --- ClickHouse, owner `default`: compose dựng kho · ch_migrate · ch_backup · bootstrap ---
CLICKHOUSE_HOST=127.0.0.1
CLICKHOUSE_PORT=8123
CLICKHOUSE_PASSWORD=change-me
# ingester_worker thuộc role dlck_ingester: ingester
CLICKHOUSE_INGESTER_USER=ingester_worker
CLICKHOUSE_INGESTER_PASSWORD=change-me
# api_reader thuộc role dlck_api: chưa tiến trình nào dùng, bootstrap cấp sẵn
CLICKHOUSE_API_USER=api_reader
CLICKHOUSE_API_PASSWORD=change-me
# Thư mục backup trên HOST; compose mount vào /backups; tương đối = theo gốc repo
CLICKHOUSE_BACKUP_DIR=./deploy/infra/clickhouse-backups

# --- Thư mục runtime ingester: để TRỐNG khi native (= <repo>/../dlck-runtime/{logs,measure,spill});
#     trong container compose đè thành /var/lib/dlck/... ---
# INGESTER_LOG_DIR=
# INGESTER_MEASURE_DIR=
# INGESTER_SPILL_DIR=

# --- Dịch vụ ngoài ---
# MiniMax Token Plan — docs/10-sources/llm/minimax.md; thiếu thì `etl classify` và `agent` exit 2
LLM_API=
# LLM_BASE_URL=https://api.minimax.io/anthropic
# LLM_MODEL=MiniMax-M3
# LLM_TIMEOUT_S=120
# FRED — docs/10-sources/global/fred.md, đăng ký bằng email dự án; thiếu thì `etl fred` lỗi lúc fetch
FRED_API=

# --- Docker Compose (chỉ VPS): overlay trần tài nguyên, để `docker compose up -d --build` là đủ ---
# COMPOSE_FILE=docker-compose.yml:docker-compose.vps.yml
# COMPOSE_PROJECT_NAME=dlck
```

- [ ] **Step 4: Chạy, xác nhận xanh**

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/core/test_env_contract.py tests/core/test_env.py -q`
Expected: `13 passed`.

- [ ] **Step 5: Commit**

```bash
git add .env.example backend/tests/core/test_env_contract.py
git commit -m "feat(env): elemental .env.example with a contract test against core.env and the code"
```

- [ ] **Step 6 — CHỦ DỰ ÁN (không giao subagent): viết lại `.env` thật theo `.env.example`.** Giữ nguyên `POSTGRES_PASSWORD`/`CLICKHOUSE_PASSWORD` của kho cũ (kho cũ còn dùng tới Task 9); bốn mật khẩu user login đặt mới hay giữ cũ đều được (bootstrap Task 9 sẽ đồng bộ). Xoá bảy dòng `*_URL`, `APP_ENV`, `LOG_LEVEL`, `COMPOSE_PROFILES`. Rồi:

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run python -m core.env check`
Expected: `đủ 18 biến bắt buộc, không biến lạ` (exit 0). Dán dòng này vào ledger — **chỉ dòng này**.

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/test_conftest_env_contract.py tests/schema -q`
Expected: xanh — `TEST_DATABASE_URL` nay được ráp, fixture dựng `dulieu_test` như cũ.

---

### Task 3: Consumer chuyển sang nguyên tố — conftest, alembic, `ch_migrate`, `ch_backup`

**Files:**
- Modify: `backend/tests/conftest.py:30-44` (fixture `migrated_engine`)
- Modify: `database/alembic.ini` (thêm 1 dòng) · `database/migrations/env.py`
- Modify: `backend/core/ch_migrate.py` (`main()`), `backend/core/ch_backup.py` (`main()` + hàm mới)
- Test: `backend/tests/clickhouse/test_t06_backup.py` (thêm 2 test cho `resolve_backup_dir`)

**Interfaces:**
- Produces: `core.ch_backup.resolve_backup_dir(value: str) -> Path` — tuyệt đối giữ nguyên; tương đối giải theo `core.env.REPO_ROOT`.

- [ ] **Step 1: Test đỏ cho `resolve_backup_dir`** — thêm vào cuối `backend/tests/clickhouse/test_t06_backup.py`:

```python
from pathlib import Path

from core.ch_backup import resolve_backup_dir
from core.env import REPO_ROOT


def test_relative_backup_dir_resolves_against_repo_root():
    """Compose ở GỐC repo giải đường dẫn tương đối theo gốc — code phải cùng gốc, không phải deploy/infra."""
    assert resolve_backup_dir("./deploy/infra/clickhouse-backups") == REPO_ROOT / "deploy" / "infra" / "clickhouse-backups"


def test_absolute_backup_dir_is_kept():
    p = Path("/backups") if Path("/backups").is_absolute() else Path("C:/backups")
    assert resolve_backup_dir(str(p)) == p
```

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/clickhouse/test_t06_backup.py -q -k resolve`
Expected: `ImportError: cannot import name 'resolve_backup_dir'`.

- [ ] **Step 2: Sửa `backend/core/ch_backup.py`** — thay hàm `main()` (dòng 77–86) bằng:

```python
def resolve_backup_dir(value: str) -> Path:
    """Tương đối = theo GỐC repo (cùng gốc với docker-compose.yml từ lát 12); tuyệt đối giữ nguyên."""
    from core.env import REPO_ROOT
    p = Path(value)
    return p if p.is_absolute() else (REPO_ROOT / p)


def main() -> None:
    from core.ch_migrate import get_client
    from core.env import load_dotenv
    load_dotenv()
    backup_dir = resolve_backup_dir(os.environ["CLICKHOUSE_BACKUP_DIR"])
    acts = run_backup(get_client(), backup_dir)
    print(f"backup: {acts or 'không có gì mới'}")
```

- [ ] **Step 3: Sửa `backend/core/ch_migrate.py` `main()`** — thêm hai dòng đầu hàm:

```python
def main() -> None:
    from core.env import load_dotenv
    load_dotenv()                    # ráp CLICKHOUSE_URL từ nguyên tố (lát 12)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
```

- [ ] **Step 4: Alembic tự nạp `.env`** — `database/alembic.ini` thêm dưới `script_location`:

```ini
script_location = database/migrations
prepend_sys_path = backend
path_separator = os
```

(`path_separator = os` — bổ sung khi thực thi 2026-09-08: thiếu nó alembic 1.19 in `DeprecationWarning` mỗi lượt, vi phạm luật output test sạch.)

và `database/migrations/env.py` thành:

```python
import os

from alembic import context
from sqlalchemy import create_engine, pool

# `prepend_sys_path = backend` trong alembic.ini (giải theo thư mục làm việc = gốc repo) cho import này.
from core.env import load_dotenv

load_dotenv()   # ráp DATA_DATABASE_URL từ nguyên tố; biến đã export (conftest trỏ DB test) THẮNG


def run_migrations_online() -> None:
    url = os.environ["DATA_DATABASE_URL"]
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
```

- [ ] **Step 5: `tests/conftest.py`** — thay thân fixture `migrated_engine` (dòng 31–44):

```python
@pytest.fixture(scope="session")
def migrated_engine():
    test_url = os.environ["TEST_DATABASE_URL"]                 # ráp từ nguyên tố: .../<POSTGRES_TEST_DB>
    test_db = test_url.rsplit("/", 1)[1]
    assert re.fullmatch(r"[a-z_][a-z0-9_]*", test_db), test_db  # ghép vào DDL nên phải là identifier sạch
    admin_url = test_url.rsplit("/", 1)[0] + "/" + os.environ.get("POSTGRES_DB", "dulieu")  # DB owner có sẵn
    admin = sa.create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(sa.text(f"DROP DATABASE IF EXISTS {test_db} WITH (FORCE)"))
        c.execute(sa.text(f"CREATE DATABASE {test_db}"))
    admin.dispose()
    cfg = Config(os.path.join(REPO_ROOT, "database", "alembic.ini"))
    os.environ["DATA_DATABASE_URL"] = test_url      # migrations/env.py đọc biến này — GÁN, không setdefault
    os.chdir(REPO_ROOT)                             # script_location trong ini là đường dẫn tương đối gốc repo
    command.upgrade(cfg, "head")
    engine = sa.create_engine(test_url)
    yield engine
    engine.dispose()
```

(thêm `import re` ở đầu file, cạnh `import os`).

- [ ] **Step 6: Chạy**

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/clickhouse/test_t06_backup.py tests/schema tests/test_conftest_env_contract.py -q`
Expected: xanh (2 test mới + bộ schema + hợp đồng).

Run (native CLI alembic, từ gốc repo, shell KHÔNG export gì): `uv run --project backend alembic -c database/alembic.ini current`
Expected: in `0020 (head)` — chứng minh `env.py` tự ráp `DATA_DATABASE_URL` (giả định 2.2.4 của spec đóng; ghi ledger).

- [ ] **Step 7: Commit**

```bash
git add backend/tests/conftest.py database/alembic.ini database/migrations/env.py backend/core/ch_migrate.py backend/core/ch_backup.py backend/tests/clickhouse/test_t06_backup.py
git commit -m "refactor(env): alembic, ch_migrate and ch_backup read elemental .env; backup dir resolves from the repo root"
```

---

### Task 4: Múi giờ — `core/clock.py`, ba chỗ sửa, phép kiểm tĩnh

**Files:**
- Create: `backend/core/clock.py`, `backend/tests/core/test_clock.py`, `backend/tests/core/test_tz_contract.py`
- Modify: `backend/etl/refdata_job.py:60`, `backend/agent/system_prompt.py:53`, `backend/core/ch_backup.py:39`

**Interfaces:**
- Produces: `core.clock.VN: ZoneInfo` · `now_vn() -> datetime` · `today_vn(now: datetime | None = None) -> date` (naive ⇒ `ValueError`).

- [ ] **Step 1: Test đỏ** `backend/tests/core/test_clock.py`:

```python
from datetime import date, datetime, timezone

import pytest

from core.clock import VN, today_vn


def test_today_vn_is_the_next_day_while_utc_is_still_the_evening_before():
    # 2026-09-07 17:30 UTC = 2026-09-08 00:30 giờ VN — đúng cửa sổ 00:00–07:00 từng làm hai test đỏ
    assert today_vn(datetime(2026, 9, 7, 17, 30, tzinfo=timezone.utc)) == date(2026, 9, 8)


def test_today_vn_keeps_a_vn_datetime():
    assert today_vn(datetime(2026, 9, 8, 0, 30, tzinfo=VN)) == date(2026, 9, 8)


def test_today_vn_rejects_naive_input():
    with pytest.raises(ValueError):
        today_vn(datetime(2026, 9, 8, 0, 30))
```

và `backend/tests/core/test_tz_contract.py`:

```python
"""Không còn `date.today()` / `datetime.now()` trần trong code sản phẩm (spec lát 12 §5.6 lớp 3).

Container mặc định UTC; mọi phép "hôm nay" phải đi qua `core.clock` hoặc `ZoneInfo` tường minh.
Kiểm TĨNH trên mã nguồn, `backend/` ngoài `tests/`.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCAN = [REPO / "backend" / d for d in ("core", "etl", "ingester", "agent", "api")]
BARE = re.compile(r"\b(?:date|datetime)\.today\(\)|\bdatetime\.utcnow\(\)|\bdatetime\.now\(\s*\)")


def test_no_bare_today_or_now_in_product_code():
    hits, n_files = [], 0
    for d in SCAN:
        for p in sorted(d.rglob("*.py")):
            n_files += 1
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if BARE.search(line) and not line.lstrip().startswith("#"):
                    hits.append(f"{p.relative_to(REPO).as_posix()}:{i}: {line.strip()}")
    assert n_files >= 60, f"chỉ quét {n_files} file — nghi phạm vi hụt"
    assert not hits, "ngày/giờ trần, sẽ lệch trong container UTC:\n  " + "\n  ".join(hits)
```

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/core/test_clock.py tests/core/test_tz_contract.py -q`
Expected: `test_clock` đỏ `ModuleNotFoundError: core.clock`; `test_tz_contract` đỏ với **đúng 3 hit**: `etl/refdata_job.py:60`, `core/ch_backup.py:39`, `agent/system_prompt.py:53`. Nhiều hơn 3 ⇒ dừng, báo (không tự sửa chỗ khác).

- [ ] **Step 2: Viết `backend/core/clock.py`**

```python
"""Đồng hồ dự án: mọi phép "hôm nay" tính theo giờ Việt Nam, không dựa vào TZ của tiến trình (spec lát 12 §5.6).

Bài học 2026-09-05: `recrawl_codes` lấy `current_date` phía Postgres (UTC) ⇒ hai test đỏ mỗi ngày
00:00–07:00 giờ VN. Container mặc định UTC nên `date.today` gọi trần rơi đúng bẫy đó mỗi đêm.
(Đổi chữ khi thực thi 2026-09-08: docstring không được viết nguyên `date.today()` vì phép kiểm tĩnh quét cả docstring.)
"""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

VN = ZoneInfo("Asia/Ho_Chi_Minh")


def now_vn() -> datetime:
    return datetime.now(VN)


def today_vn(now: datetime | None = None) -> date:
    """Ngày VN của `now` (mặc định: bây giờ). Từ chối `now` naive — naive là chính cái bẫy đang tránh."""
    if now is None:
        return now_vn().date()
    if now.tzinfo is None:
        raise ValueError("today_vn cần datetime có múi giờ")
    return now.astimezone(VN).date()
```

- [ ] **Step 3: Sửa ba chỗ**

`backend/etl/refdata_job.py`: thêm `from core.clock import today_vn` cạnh các import `core`; dòng 60 thành
`refdata_store.upsert_domain_state(engine, today_vn().isoformat())`. Nếu `from datetime import date` không còn ai dùng trong file thì bỏ import đó (dọn rác do chính mình tạo — §4.4.3).

`backend/agent/system_prompt.py`: thêm `from core.clock import today_vn`; dòng 53 thành
`return TOOL_RULES_MAU.format(hom_nay=(hom_nay or today_vn()).strftime("%d/%m/%Y"))`.

`backend/core/ch_backup.py`: thêm `from core.clock import today_vn`; dòng 39 thành `today = today or today_vn()`.

- [ ] **Step 4: Chạy**

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/core tests/agent tests/etl/test_e10_refdata_job.py tests/clickhouse/test_t06_backup.py -q`
Expected: xanh; `test_tz_contract` 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/core/clock.py backend/tests/core/test_clock.py backend/tests/core/test_tz_contract.py backend/etl/refdata_job.py backend/agent/system_prompt.py backend/core/ch_backup.py
git commit -m "fix(tz): every 'today' goes through core.clock in VN time, with a contract test against bare calls"
```

---

### Task 5: `SIGTERM` đi cùng đường Ctrl+C; về hưu console Windows, `register-tasks.ps1`, `stack.mjs`

**Files:**
- Create: `backend/core/shutdown.py`, `backend/tests/core/test_shutdown.py`
- Modify: `backend/etl/__main__.py:1-20`, `backend/ingester/__main__.py:1-13`, `backend/etl/price_job.py:20,101,209`
- Delete: `backend/core/console.py`, `backend/tests/core/test_console.py`, `scripts/register-tasks.ps1`, `scripts/stack.mjs`, `scripts/stack.test.mjs`, `package.json`

**Interfaces:**
- Produces: `core.shutdown.install_signal_handlers() -> None` · `core.shutdown._raise_interrupt(signum, frame)`.

- [ ] **Step 1: Test đỏ** `backend/tests/core/test_shutdown.py`:

```python
"""`docker stop` gửi SIGTERM; Python mặc định chết ngay, bỏ qua đường đóng sổ mà Ctrl+C đang có
(`test_e42`: `failed: dừng tay (Ctrl+C)`, exit 130). Handler nâng SIGTERM thành KeyboardInterrupt
để hai đường dừng là một. Windows đăng ký được nhưng không giao SIGTERM — ca thật chỉ chạy POSIX.
"""
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from core import shutdown

BACKEND = Path(__file__).resolve().parents[2]


def test_handler_raises_keyboard_interrupt():
    with pytest.raises(KeyboardInterrupt):
        shutdown._raise_interrupt(signal.SIGTERM, None)


def test_install_registers_the_handler_for_sigterm():
    old = signal.getsignal(signal.SIGTERM)
    try:
        shutdown.install_signal_handlers()
        assert signal.getsignal(signal.SIGTERM) is shutdown._raise_interrupt
    finally:
        signal.signal(signal.SIGTERM, old)


@pytest.mark.skipif(sys.platform == "win32", reason="Windows không giao SIGTERM cho handler Python")
def test_sigterm_in_a_real_process_lands_in_the_ctrl_c_path():
    code = ("import os, sys, time\n"
            "from core.shutdown import install_signal_handlers\n"
            "install_signal_handlers(); print('READY', flush=True)\n"
            "try:\n    time.sleep(30)\nexcept KeyboardInterrupt:\n    print('INTERRUPTED'); sys.exit(130)\n")
    p = subprocess.Popen([sys.executable, "-c", code], cwd=BACKEND, stdout=subprocess.PIPE, text=True)
    assert p.stdout.readline().strip() == "READY"
    p.send_signal(signal.SIGTERM)
    out, _ = p.communicate(timeout=10)
    assert p.returncode == 130 and "INTERRUPTED" in out
```

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/core/test_shutdown.py -q`
Expected: đỏ `ModuleNotFoundError: core.shutdown` (2 test; test thứ ba skip trên Windows).

- [ ] **Step 2: Viết `backend/core/shutdown.py`**

```python
"""SIGTERM → cùng đường dừng với Ctrl+C (spec lát 12 §5.5).

`docker compose stop/down` gửi SIGTERM rồi đợi `stop_grace_period`. Không handler thì Python chết
ngay: job không đóng sổ `ops.etl_run`, ingester mất hàng đợi RAM chưa xả. Nâng thành
`KeyboardInterrupt` để mọi `except KeyboardInterrupt` đã có (khuôn `price_job`, `test_e42`) chạy y hệt.
"""
from __future__ import annotations

import signal


def _raise_interrupt(signum, frame):  # noqa: ARG001 — chữ ký handler của `signal`
    raise KeyboardInterrupt


def install_signal_handlers() -> None:
    signal.signal(signal.SIGTERM, _raise_interrupt)
```

- [ ] **Step 3: Gắn vào hai entrypoint, gỡ console**

`backend/etl/__main__.py` — thay `from core.console import lock_if_scheduled` bằng `from core.shutdown import install_signal_handlers`; thay hai dòng đầu thân `main()`:

```python
def main(argv: list[str] | None = None) -> int:
    install_signal_handlers()         # SIGTERM của `docker stop` đi cùng đường Ctrl+C (đóng sổ, exit 130)
    args = sys.argv[1:] if argv is None else argv
```

`backend/ingester/__main__.py` — tương tự: import `install_signal_handlers`, bỏ khối `if lock_if_scheduled(): …`, gọi `install_signal_handlers()` làm dòng đầu `main()`.

`backend/etl/price_job.py` — bỏ `from core.console import banner`; dòng 101 và 209 đổi `banner(` thành `log.info(` (giữ nguyên nội dung chuỗi).

- [ ] **Step 4: Xoá về hưu**

```bash
git rm backend/core/console.py backend/tests/core/test_console.py scripts/register-tasks.ps1 scripts/stack.mjs scripts/stack.test.mjs package.json
```

- [ ] **Step 5: Chạy**

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/core tests/etl/test_e42_interrupt_closes_run.py tests/etl/test_e63_exit_code_contract.py tests/ingester/test_i02_config.py -q && git grep -n "core.console\|lock_if_scheduled\|DLCK_LOCK_CONSOLE" -- backend`
Expected: xanh; grep **0 hit** trong `backend/`.

- [ ] **Step 6: Commit**

```bash
git add -A backend/core backend/etl/__main__.py backend/ingester/__main__.py backend/etl/price_job.py backend/tests/core scripts package.json
git commit -m "feat(shutdown): route SIGTERM through the Ctrl+C path; retire the Windows console lock, the task registrar and the Node stack wrapper"
```

---

### Task 6: Ingester thành daemon — `next_window`, `daemon`, rẽ nhánh trong `run()`

**Files:**
- Modify: `backend/ingester/main.py` (hằng số ~dòng 39; thêm hai hàm; `run()` dòng 682–703)
- Test: `backend/tests/ingester/test_i16_daemon.py` (mới)

**Interfaces:**
- Produces: `ingester.main.SESSION_START = (8, 30)` · `next_window(now, start_hm, end_hm) -> tuple[datetime, datetime]` · `async daemon(mode, run_session, *, clock, sleep, stop, end_hm) -> int`.
- Không đổi: `run(mode, minutes, …)` chữ ký; `--minutes N` vẫn chạy N phút rồi thoát.

- [ ] **Step 1: Test đỏ** `backend/tests/ingester/test_i16_daemon.py`:

```python
"""Daemon: ngoài phiên ngủ, trong phiên chạy, lỗi khởi động (≥ 2) thoát để Docker khởi động lại (spec §5.5)."""
import asyncio
from datetime import datetime, timedelta

from ingester.main import SESSION_END_MEASURE, SESSION_END_RUN, SESSION_START, TZ, daemon, next_window


def vn(y, m, d, h, mi):
    return datetime(y, m, d, h, mi, tzinfo=TZ)


# 2026-09-08 là thứ 3 · 11/09 thứ 6 · 12/09 thứ 7 · 14/09 thứ 2
def test_next_window_friday_evening_rolls_to_monday():
    assert next_window(vn(2026, 9, 11, 16, 0), SESSION_START, SESSION_END_RUN) == (vn(2026, 9, 14, 8, 30), vn(2026, 9, 14, 15, 5))


def test_next_window_saturday_rolls_to_monday():
    assert next_window(vn(2026, 9, 12, 10, 0), SESSION_START, SESSION_END_RUN) == (vn(2026, 9, 14, 8, 30), vn(2026, 9, 14, 15, 5))


def test_next_window_early_morning_is_the_same_day():
    assert next_window(vn(2026, 9, 8, 7, 0), SESSION_START, SESSION_END_RUN) == (vn(2026, 9, 8, 8, 30), vn(2026, 9, 8, 15, 5))


def test_next_window_inside_session_returns_the_open_window():
    assert next_window(vn(2026, 9, 8, 9, 0), SESSION_START, SESSION_END_RUN) == (vn(2026, 9, 8, 8, 30), vn(2026, 9, 8, 15, 5))


def test_next_window_at_15_05_is_already_tomorrow():
    assert next_window(vn(2026, 9, 8, 15, 5), SESSION_START, SESSION_END_RUN)[0] == vn(2026, 9, 9, 8, 30)


def test_measure_window_ends_15_10():
    assert next_window(vn(2026, 9, 8, 9, 0), SESSION_START, SESSION_END_MEASURE)[1] == vn(2026, 9, 8, 15, 10)


class FakeClock:
    def __init__(self, start):
        self.t = start
        self.sleeps = []

    def now(self):
        return self.t

    async def sleep(self, s):
        self.sleeps.append(s)
        self.t += timedelta(seconds=s)


def test_daemon_sleeps_until_08_30_then_runs_one_session():
    fc = FakeClock(vn(2026, 9, 8, 7, 0))
    stop = asyncio.Event()
    calls = []

    async def session():
        calls.append(fc.now())
        fc.t = vn(2026, 9, 8, 15, 5)      # phiên chạy tới deadline như `_run_run`
        stop.set()
        return 0

    rc = asyncio.run(daemon("run", session, clock=fc.now, sleep=fc.sleep, stop=stop, end_hm=SESSION_END_RUN))
    assert rc == 0
    assert calls == [vn(2026, 9, 8, 8, 30)]
    assert max(fc.sleeps) <= 60 and sum(fc.sleeps) == 90 * 60


def test_daemon_runs_immediately_when_inside_the_window_and_exits_on_startup_failure():
    fc = FakeClock(vn(2026, 9, 8, 9, 0))
    calls = []

    async def session():
        calls.append(fc.now())
        return 3                          # hợp đồng khởi động hỏng ⇒ thoát để Docker restart

    rc = asyncio.run(daemon("run", session, clock=fc.now, sleep=fc.sleep, stop=asyncio.Event(), end_hm=SESSION_END_RUN))
    assert rc == 3 and calls == [vn(2026, 9, 8, 9, 0)] and fc.sleeps == []


def test_daemon_after_a_clean_session_waits_for_the_next_window():
    fc = FakeClock(vn(2026, 9, 8, 9, 0))
    stop = asyncio.Event()
    calls = []

    async def session():
        calls.append(fc.now())
        fc.t = vn(2026, 9, 8, 15, 5)
        if len(calls) == 2:
            stop.set()
        return 1                          # đối chứng lệch = phiên vẫn kết thúc bình thường, không thoát

    asyncio.run(daemon("run", session, clock=fc.now, sleep=fc.sleep, stop=stop, end_hm=SESSION_END_RUN))
    assert calls == [vn(2026, 9, 8, 9, 0), vn(2026, 9, 9, 8, 30)]
```

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/ingester/test_i16_daemon.py -q`
Expected: `ImportError: cannot import name 'SESSION_START'`.

- [ ] **Step 2: Sửa `backend/ingester/main.py`**

Cạnh hai hằng `SESSION_END_*` (dòng 39–40) thêm:

```python
SESSION_START = (8, 30)          # mốc task Windows cũ 08:30 — daemon nối socket từ đây (spec lát 12 §5.5)
```

Thêm `from datetime import datetime, time, timedelta` (bổ sung `time`; chú ý module đã `import time` — đặt tên `from datetime import time as dtime` để không đè). Thêm hai hàm ngay sau `_run_deadline`:

```python
def next_window(now: datetime, start_hm: tuple[int, int], end_hm: tuple[int, int]) -> tuple[datetime, datetime]:
    """Cửa sổ phiên đang mở hoặc kế tiếp, thứ 2–6, giờ VN. `start <= now < end` khi đang trong phiên."""
    day = now.date()
    for _ in range(8):
        if day.weekday() < 5:
            start = datetime.combine(day, dtime(*start_hm), tzinfo=now.tzinfo)
            end = datetime.combine(day, dtime(*end_hm), tzinfo=now.tzinfo)
            if now < end:
                return start, end
        day += timedelta(days=1)
    raise AssertionError("không tìm được cửa sổ phiên trong 8 ngày")


async def daemon(mode: str, run_session, *, clock=lambda: datetime.now(TZ), sleep=asyncio.sleep,
                 stop: asyncio.Event | None = None, end_hm: tuple[int, int] = SESSION_END_RUN) -> int:
    """Vòng cửa sổ phiên: ngoài phiên ngủ (lát ≤ 60 s), trong phiên gọi `run_session` một lần.
    Mã ≥ 2 (hợp đồng khởi động hỏng) ⇒ thoát để Docker khởi động lại có giãn cách; 0/1 ⇒ chờ phiên kế."""
    stop = stop or asyncio.Event()
    while not stop.is_set():
        now = clock()
        start, end = next_window(now, SESSION_START, end_hm)
        if now < start:
            log.info("%s: ngoài phiên, chờ tới %s", mode, start.isoformat())
            while (now := clock()) < start and not stop.is_set():
                await sleep(min(60.0, (start - now).total_seconds()))
            continue
        rc = await run_session()
        log.info("%s: phiên đóng lúc %s, mã %d", mode, clock().isoformat(), rc)
        if rc >= 2:
            return rc
        while (now := clock()) < end and not stop.is_set():   # phiên trả sớm thì đợi qua `end`, không chạy lại cùng phiên
            await sleep(min(60.0, (end - now).total_seconds()))
    return 0
```

Thay `run()` (dòng 682–703) bằng:

```python
def _day_log_handler(cfg: config.Config) -> logging.Handler:
    h = logging.FileHandler(cfg.log_dir / f"ingester-{datetime.now(TZ):%Y%m%d}.log", encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    return h


async def run(mode: str, minutes: float | None = None, out: str | None = None, d=None,
              count: str | None = None, t_from: str | None = None, t_to: str | None = None,
              use_db: bool = False) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if mode == "measure":
        if minutes is None:                                   # daemon: cửa sổ đo 08:30–15:10 mỗi ngày làm việc
            return await daemon("measure", lambda: _run_measure(None, out), end_hm=SESSION_END_MEASURE)
        return await _run_measure(minutes, out)
    if mode == "count":
        return await _run_count(count, t_from, t_to, use_db)

    cfg = config.load(need_db=True)
    if mode == "reconcile":
        logging.getLogger().addHandler(_day_log_handler(cfg))
        return await _run_reconcile(cfg, d)
    if mode == "run":
        if minutes is not None:                               # đường nghiệm thu / chạy tay: N phút rồi thoát
            logging.getLogger().addHandler(_day_log_handler(cfg))
            return await _run_run(cfg, minutes)

        async def session() -> int:                           # mỗi phiên một file log theo ngày
            h = _day_log_handler(cfg)
            root = logging.getLogger()
            root.addHandler(h)
            try:
                return await _run_run(cfg, None)
            finally:
                root.removeHandler(h)
                h.close()

        return await daemon("run", session, end_hm=SESSION_END_RUN)
    print(f"ingester: mode không biết: {mode!r}")
    return 4
```

- [ ] **Step 3: Chạy**

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/ingester -q`
Expected: xanh (9 test mới + bộ ingester cũ, có container ClickHouse tạm).

- [ ] **Step 3b — BỔ SUNG theo phán quyết 2026-09-08 (review Task 5): đường dừng tử tế cho vòng asyncio.**

Phát hiện: `ingester/main.py` **không có** `except KeyboardInterrupt`; `KeyboardInterrupt` ném từ handler tín hiệu trong lúc `await stop.wait()` thoát thẳng khỏi `asyncio.run()` — đuôi phiên (xả hàng đợi `_drain_for_verdict`, đối chứng) **không chạy**, cả với Ctrl+C lẫn SIGTERM. Đường đúng cho asyncio là tín hiệu → `stop.set()` trên loop, để phiên đóng y như tới deadline.

Thêm test vào `backend/tests/ingester/test_i16_daemon.py` (đỏ trước):

```python
import signal
import sys

from ingester.main import install_loop_stop


def test_install_loop_stop_declines_on_windows_and_arms_on_posix():
    async def scenario():
        stop = asyncio.Event()
        armed = install_loop_stop(stop)
        if sys.platform == "win32":
            assert armed is False and not stop.is_set()
            return
        assert armed is True
        signal.raise_signal(signal.SIGTERM)
        await asyncio.sleep(0.05)          # handler chạy ở vòng lặp kế
        assert stop.is_set()
    asyncio.run(scenario())


def test_daemon_returns_right_after_a_session_ended_by_signal():
    fc = FakeClock(vn(2026, 9, 8, 10, 0))
    stop = asyncio.Event()

    async def session():
        fc.t = vn(2026, 9, 8, 10, 5)
        stop.set()                          # tín hiệu đến giữa phiên: _run_run đóng phiên rồi trả về
        return 0

    rc = asyncio.run(daemon("run", session, clock=fc.now, sleep=fc.sleep, stop=stop, end_hm=SESSION_END_RUN))
    assert rc == 0 and fc.sleeps == []      # không ngủ tới phiên kế — thoát ngay để container dừng
```

Code trong `backend/ingester/main.py` (thêm `import signal` đầu file):

```python
def install_loop_stop(stop: asyncio.Event) -> bool:
    """SIGTERM/SIGINT → `stop.set()` trên loop đang chạy: phiên đóng đúng đường deadline (xả hàng đợi,
    đối chứng) thay vì `KeyboardInterrupt` cắt ngang `await` (review Task 5 lát 12: `_run_run` không có
    `except KeyboardInterrupt`, đuôi phiên không chạy). Windows (Proactor) không hỗ trợ ⇒ False, giữ
    đường KeyboardInterrupt của `core.shutdown` (mã thoát như Ctrl+C, không xả)."""
    loop = asyncio.get_running_loop()
    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, stop.set)
    except (NotImplementedError, RuntimeError):
        return False
    return True
```

`_run_run(cfg, minutes, stop: asyncio.Event | None = None)`: thay dòng `stop = asyncio.Event()` bên trong bằng `stop = stop or asyncio.Event()`; `_run_measure(minutes, out, stop=None)` tương tự. Trong `run()`: ngay sau `logging.basicConfig(...)` thêm `stop = asyncio.Event()` và `install_loop_stop(stop)`; truyền `stop=stop` vào mọi lời gọi `_run_run`/`_run_measure` (kể cả trong `session()` của daemon) và `daemon(..., stop=stop)`. Trong `daemon()`, ngay sau `rc = await run_session()` và dòng log: `if stop.is_set(): return rc` (tín hiệu ⇒ thoát để container dừng, không chờ phiên kế).

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/ingester/test_i16_daemon.py tests/ingester/test_i10_main.py -q` — Expected: xanh (trên Windows test đầu đi nhánh `False`).

- [ ] **Step 3c — BỔ SUNG theo phán quyết 2026-09-08 (báo cáo implementer Task 6): tách `shutdown` khỏi `stop` của phiên; test cũ gọi phiên có hạn.**

Hai lỗi Step 3b để lại: (a) `session_timer` của `_run_run`/`_run_measure` cũng `stop.set()` lúc tới mốc giờ, mà daemon dùng chính event đó để biết "có tín hiệu" ⇒ phiên bình thường kết thúc là daemon thoát, nhánh "chờ phiên kế" không bao giờ chạy thật; (b) ba test cũ gọi `run("run")` không `minutes` nay đi qua daemon và **ngủ tới 08:30** nếu chạy ngoài giờ.

Sửa trong `backend/ingester/main.py`:

```python
async def _relay(src: asyncio.Event, dst: asyncio.Event) -> None:
    """Chuyển tín hiệu dừng (event `shutdown` của cả tiến trình) vào `stop` của PHIÊN đang chạy."""
    await src.wait()
    dst.set()


async def _session_with_relay(shutdown: asyncio.Event, factory) -> int:
    """Mỗi phiên một `stop` mới (mốc giờ chỉ đóng phiên đó, không đóng daemon); tín hiệu thì đóng cả hai.
    Relay huỷ khi phiên xong để `stop` cũ không bị đụng."""
    stop = asyncio.Event()
    relay = asyncio.create_task(_relay(shutdown, stop))
    try:
        return await factory(stop)
    finally:
        relay.cancel()
```

Trong `run()`: event của tín hiệu đặt tên `shutdown` (`shutdown = asyncio.Event(); install_loop_stop(shutdown)`); đường `--minutes`: `return await _session_with_relay(shutdown, lambda stop: _run_run(cfg, minutes, stop=stop))` (measure tương tự với `_run_measure(minutes, out, stop=stop)`); trong daemon, `session()` gọi `_session_with_relay(shutdown, lambda stop: _run_run(cfg, None, stop=stop))` (measure tương tự); `daemon(..., stop=shutdown, ...)`. `daemon()` giữ `if stop.is_set(): return rc`. Docstring `install_loop_stop` nói rõ nó bật `shutdown`, relay đưa vào phiên.

Test thêm vào `test_i16_daemon.py` (đỏ trước — `ImportError: _relay`):

```python
from ingester.main import _relay, _session_with_relay


def test_relay_sets_the_session_stop_when_shutdown_fires():
    async def scenario():
        shutdown, stop = asyncio.Event(), asyncio.Event()
        task = asyncio.create_task(_relay(shutdown, stop))
        await asyncio.sleep(0)
        assert not stop.is_set()
        shutdown.set()
        await asyncio.sleep(0.01)
        assert stop.is_set()
        await task
    asyncio.run(scenario())


def test_each_session_gets_a_fresh_stop_and_the_relay_is_cancelled_after_it():
    async def scenario():
        shutdown, seen = asyncio.Event(), []

        async def factory(stop):
            seen.append(stop)
            return 7

        assert await _session_with_relay(shutdown, factory) == 7
        assert await _session_with_relay(shutdown, factory) == 7
        assert seen[0] is not seen[1] and not seen[0].is_set() and not seen[1].is_set()
        shutdown.set()                      # relay đã huỷ: bật shutdown sau khi phiên xong không đụng stop cũ
        await asyncio.sleep(0.01)
        assert not seen[1].is_set()
    asyncio.run(scenario())
```

Ba test cũ đổi sang phiên có hạn (thêm chú thích `# minutes=: một phiên có hạn, không qua daemon (lát 12)`): `tests/ingester/test_i10_main.py::test_run_mode_returns_exit_3_when_clickhouse_unreachable` (`asyncio.run(run("run", minutes=1))`) và hai lời gọi trong `tests/ingester/test_i15_recovery_drain.py` (`asyncio.run(run("run", minutes=1)) == 3`).

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/ingester/test_i16_daemon.py tests/ingester/test_i10_main.py tests/ingester/test_i15_recovery_drain.py -q` — Expected: xanh. Commit riêng: `fix(ingester): separate the shutdown signal from the session deadline; bounded runs in tests`.

- [ ] **Step 3d — BỔ SUNG theo phán quyết 2026-09-08 (review Task 6): chỉ cài `install_loop_stop` ở `run`/`measure`.**

Cài trước nhánh chọn chế độ (Step 3b) làm `count` và `reconcile` trên POSIX mất đường ngắt: `add_signal_handler` đè handler `core.shutdown`, mà hai chế độ đó không ai đọc `shutdown`. Sửa `run()`: bỏ `install_loop_stop(shutdown)` ngay sau `logging.basicConfig`; gọi nó **bên trong** nhánh `measure` (trước khi rẽ `--minutes`/daemon) và nhánh `run` (sau `config.load`, trước khi rẽ). `count`/`reconcile` giữ handler `core.shutdown` (KeyboardInterrupt) như cũ.

Test thêm vào `test_i16_daemon.py` (đỏ trước — recorder ghi nhận lời gọi ở `count`):

```python
import ingester.main as main_mod


def test_loop_stop_is_armed_only_for_run_and_measure(monkeypatch):
    armed = []
    monkeypatch.setattr(main_mod, "install_loop_stop", lambda ev: armed.append(ev) or True)

    async def fake_count(*a, **k):
        return 0

    async def fake_run(cfg, minutes, stop=None):
        return 0

    monkeypatch.setattr(main_mod, "_run_count", fake_count)
    monkeypatch.setattr(main_mod, "_run_run", fake_run)
    monkeypatch.setattr(main_mod.config, "load", lambda need_db: object())
    monkeypatch.setattr(main_mod, "_day_log_handler", lambda cfg: logging.NullHandler())
    assert asyncio.run(main_mod.run("count", count="20260908")) == 0
    assert armed == []                                        # count: giữ đường KeyboardInterrupt
    assert asyncio.run(main_mod.run("run", minutes=1)) == 0
    assert len(armed) == 1                                    # run: một lần, trước khi rẽ
```

(`import logging` đầu file test.) Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/ingester/test_i16_daemon.py tests/ingester/test_i10_main.py -q` — xanh. Commit riêng: `fix(ingester): arm the loop stop only for run and measure so count/reconcile stay interruptible`.

- [ ] **Step 4: Commit**

```bash
git add backend/ingester/main.py backend/tests/ingester/test_i16_daemon.py
git commit -m "feat(ingester): sleep outside the trading window instead of exiting, so restart: unless-stopped is safe"
```

---

### Task 7: Image tự đủ + một compose gốc + overlay VPS + hợp đồng tĩnh

**Files:**
- Modify: `deploy/backend.Dockerfile`, `backend/pyproject.toml` (dev dep `pyyaml`)
- Create: `.dockerignore` (gốc), `docker-compose.yml` (gốc), `docker-compose.vps.yml` (gốc), `backend/tests/docs/test_d03_compose_contract.py`
- Delete: `backend/.dockerignore`, `deploy/infra/docker-compose.yml`, `deploy/infra/docker-compose.vps.yml`, `deploy/app/docker-compose.yml`
- Modify (comment): `backend/tests/clickhouse/test_c99_dedup_probe.py:27,90` — đổi chữ `deploy/infra/docker-compose.vps.yml` thành `docker-compose.vps.yml`

**Interfaces:**
- Produces: project compose `dlck` với service `postgres` `redis` `clickhouse` `migrate` `api` `etl` `ingester` `ingester-measure`(profile `measure`) `agent`(profile `tools`); image `dlck-backend`; đường dẫn trong container `/app/backend` (WORKDIR), `/app/database`, `/var/lib/dlck/{logs,measure,spill}`, `/backups`.
- Consumes: `core.bootstrap` (Task 8) là `command` của `migrate` — file chưa có nên **Task này chỉ `build`, không `up`**.

- [ ] **Step 1: Thêm `pyyaml` vào dev** — `backend/pyproject.toml`:

```toml
[dependency-groups]
dev = [
    "psutil>=7.2.2",
    "pytest>=8",
    "pyyaml>=6",
]
```

Run: `cd backend && uv sync` → `uv.lock` cập nhật (commit cùng).

- [ ] **Step 2: Test đỏ** `backend/tests/docs/test_d03_compose_contract.py`:

```python
"""Hợp đồng compose/Dockerfile ↔ spec lát 12 §5.2–5.3 — kiểm tĩnh, không dựng container.

Danh sách biến compose được đè là TOÀN BỘ danh sách §5.2: thêm/bớt một biến là đỏ, để lệch giữa
`.env.example`, `core.env` và YAML không thể xảy ra âm thầm.
"""
from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
COMPOSE = REPO / "docker-compose.yml"
OVERRIDES = {
    "POSTGRES_HOST": "postgres", "REDIS_HOST": "redis", "CLICKHOUSE_HOST": "clickhouse",
    "TZ": "Asia/Ho_Chi_Minh",
    "INGESTER_LOG_DIR": "/var/lib/dlck/logs", "INGESTER_MEASURE_DIR": "/var/lib/dlck/measure",
    "INGESTER_SPILL_DIR": "/var/lib/dlck/spill", "CLICKHOUSE_BACKUP_DIR": "/backups",
}
APP = {"migrate", "api", "etl", "ingester", "ingester-measure", "agent"}


def _services():
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))["services"]


def test_root_compose_exists_and_the_split_files_are_gone():
    assert COMPOSE.is_file()
    for old in ("deploy/infra/docker-compose.yml", "deploy/infra/docker-compose.vps.yml", "deploy/app/docker-compose.yml"):
        assert not (REPO / old).exists(), old


def test_app_services_override_exactly_the_documented_variables():
    for name in APP:
        env = _services()[name].get("environment") or {}
        assert env == OVERRIDES, f"{name}: {sorted(set(env) ^ set(OVERRIDES))}"


def test_no_service_declares_a_url_variable():
    for name, svc in _services().items():
        for key in (svc.get("environment") or {}):
            assert not key.endswith("_URL"), f"{name}.{key}"


def test_every_app_service_waits_for_migrate():
    for name in APP - {"migrate"}:
        dep = _services()[name]["depends_on"]["migrate"]
        assert dep == {"condition": "service_completed_successfully"}, name


def test_migrate_is_a_one_shot_running_bootstrap():
    m = _services()["migrate"]
    assert m["restart"] == "no" and m["command"] == ["python", "-m", "core.bootstrap"]


def test_ingester_runtime_dirs_are_named_volumes_and_stop_grace_is_generous():
    ing = _services()["ingester"]
    targets = {v.split(":")[1] for v in ing["volumes"]}
    assert targets == {"/var/lib/dlck/logs", "/var/lib/dlck/measure", "/var/lib/dlck/spill"}
    assert ing["stop_grace_period"] == "90s" and _services()["etl"]["stop_grace_period"] == "60s"


def test_image_never_carries_secrets_or_tests():
    dockerfile = (REPO / "deploy" / "backend.Dockerfile").read_text(encoding="utf-8")
    assert ".env" not in dockerfile
    ignore = (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in ignore and ".env.*" in ignore and "backend/tests" in ignore
    assert not (REPO / "backend" / ".dockerignore").exists()
```

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/docs/test_d03_compose_contract.py -q`
Expected: đỏ (`docker-compose.yml` gốc chưa có).

- [ ] **Step 3: `deploy/backend.Dockerfile`** — thay toàn bộ:

```dockerfile
# Build context = GỐC repo (lát 12): image mang cả backend/ lẫn database/ để migrate chạy trong container.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/ /app/backend/
COPY database/ /app/database/
ENV PATH="/app/backend/.venv/bin:$PATH"
# REPO_ROOT của core/env.py = parents[2] của /app/backend/core/env.py = /app — đúng cấp với native.
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: `.dockerignore` ở gốc** (xoá `backend/.dockerignore`):

```
.git
.env
.env.*
**/.venv
**/__pycache__
**/*.pyc
**/.pytest_cache
backend/tests
docs
node_modules
deploy/infra/clickhouse-backups
```

- [ ] **Step 5: `docker-compose.yml` ở gốc** (`git rm` ba file compose cũ trước):

```yaml
# MỘT compose cho cả kho lẫn app (lát 12, 2026-09-08). Trên VPS: `.env` đặt
#   COMPOSE_FILE=docker-compose.yml:docker-compose.vps.yml
# rồi `docker compose up -d --build` là đủ. Trên dev: cùng lệnh, không overlay.
# Job: docker compose run --rm etl python -m etl <job> [cờ]   ·  REPL: docker compose run --rm agent
name: dlck

x-app: &app
  build:
    context: .
    dockerfile: deploy/backend.Dockerfile
  image: dlck-backend
  env_file: .env
  environment:
    POSTGRES_HOST: postgres
    REDIS_HOST: redis
    CLICKHOUSE_HOST: clickhouse
    TZ: Asia/Ho_Chi_Minh
    INGESTER_LOG_DIR: /var/lib/dlck/logs
    INGESTER_MEASURE_DIR: /var/lib/dlck/measure
    INGESTER_SPILL_DIR: /var/lib/dlck/spill
    CLICKHOUSE_BACKUP_DIR: /backups
  networks:
    - dlck-net

services:
  postgres:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-dulieu}
      POSTGRES_USER: ${POSTGRES_USER:-dulieu}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD phải đặt trong .env}
    ports:
      - "127.0.0.1:${POSTGRES_PORT:-5432}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-dulieu} -d ${POSTGRES_DB:-dulieu}"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - dlck-net

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    ports:
      - "127.0.0.1:${REDIS_PORT:-6379}:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - dlck-net

  clickhouse:
    image: clickhouse/clickhouse-server:26.3.22.7
    restart: unless-stopped
    environment:
      TZ: Asia/Ho_Chi_Minh
      CLICKHOUSE_PASSWORD: ${CLICKHOUSE_PASSWORD:?CLICKHOUSE_PASSWORD phải đặt trong .env}
      CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: "1"
    ulimits:
      nofile:
        soft: 262144
        hard: 262144
    ports:
      - "127.0.0.1:${CLICKHOUSE_PORT:-8123}:8123"
      - "127.0.0.1:9000:9000"
    volumes:
      - chdata:/var/lib/clickhouse
      - ./deploy/infra/clickhouse/backups.xml:/etc/clickhouse-server/config.d/backups.xml:ro
      - ./deploy/infra/clickhouse/system-logs.xml:/etc/clickhouse-server/config.d/system-logs.xml:ro
      - ./deploy/infra/clickhouse/memory.xml:/etc/clickhouse-server/config.d/memory.xml:ro
      - ${CLICKHOUSE_BACKUP_DIR:-./deploy/infra/clickhouse-backups}:/backups
    healthcheck:
      test: ["CMD-SHELL", "clickhouse-client --password \"$$CLICKHOUSE_PASSWORD\" -q 'SELECT 1'"]
      interval: 5s
      timeout: 3s
      retries: 20
    networks:
      - dlck-net

  # One-shot: alembic head · ch_migrate · 4 user login · tự seed ngành lớp 2. Chạy lại mỗi `up` (idempotent).
  migrate:
    <<: *app
    restart: "no"
    command: ["python", "-m", "core.bootstrap"]
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      clickhouse:
        condition: service_healthy

  api:
    <<: *app
    restart: unless-stopped
    ports:
      - "8000:8000"
    depends_on:
      migrate:
        condition: service_completed_successfully

  # Vỏ job: lát 12 giữ heartbeat; lát 13 thay `command` bằng scheduler. Job lẻ chạy qua `docker compose run --rm etl …`.
  etl:
    <<: *app
    restart: unless-stopped
    command: ["python", "-m", "etl"]
    stop_grace_period: 60s
    volumes:
      - ${CLICKHOUSE_BACKUP_DIR:-./deploy/infra/clickhouse-backups}:/backups
    depends_on:
      migrate:
        condition: service_completed_successfully

  # Daemon: ngoài phiên ngủ, 08:30–15:05 giờ VN ghi thật. Exit 3 (hợp đồng khởi động) ⇒ Docker khởi động lại có giãn cách.
  ingester:
    <<: *app
    restart: unless-stopped
    command: ["python", "-m", "ingester"]
    stop_grace_period: 90s
    volumes:
      - ingester_logs:/var/lib/dlck/logs
      - ingester_measure:/var/lib/dlck/measure
      - ingester_spill:/var/lib/dlck/spill
    depends_on:
      migrate:
        condition: service_completed_successfully
      clickhouse:
        condition: service_healthy
      redis:
        condition: service_healthy

  # Lưới an toàn frame thô (tuỳ chọn): docker compose --profile measure up -d ingester-measure
  ingester-measure:
    <<: *app
    profiles: ["measure"]
    restart: unless-stopped
    command: ["python", "-m", "ingester", "--measure"]
    stop_grace_period: 30s
    volumes:
      - ingester_logs:/var/lib/dlck/logs
      - ingester_measure:/var/lib/dlck/measure
    depends_on:
      migrate:
        condition: service_completed_successfully

  # REPL tầng ngữ nghĩa: docker compose run --rm agent
  agent:
    <<: *app
    profiles: ["tools"]
    command: ["python", "-m", "agent"]
    stdin_open: true
    tty: true
    depends_on:
      migrate:
        condition: service_completed_successfully

volumes:
  pgdata:
  redisdata:
  chdata:
  ingester_logs:
  ingester_measure:
  ingester_spill:

networks:
  dlck-net:
```

- [ ] **Step 6: `docker-compose.vps.yml` ở gốc** — chép nguyên `deploy/infra/docker-compose.vps.yml` cũ (kể cả khối comment ngân sách RAM), chỉ đổi dòng mount thành `./deploy/infra/clickhouse/memory-vps.xml:/etc/clickhouse-server/config.d/memory.xml:ro` và dòng lệnh chạy trong comment đầu file thành:

```
#   .env đặt COMPOSE_FILE=docker-compose.yml:docker-compose.vps.yml  rồi:  docker compose up -d --build
```

- [ ] **Step 7: Chạy hợp đồng + kiểm cấu hình + build**

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/docs/test_d03_compose_contract.py -q`
Expected: `7 passed`. (⚠️ `test_d01` vế link chết sẽ **đỏ có chủ đích** từ Task 5 tới Task 11 — tài liệu sống còn link tới file đã xoá; Task 11 sửa. Không chạy cả `tests/docs` ở đây.)

Run (gốc repo): `docker compose config --quiet && echo OK`
Expected: `OK` (YAML hợp lệ, interpolation đủ — cần `.env` mới của Task 2 Step 6).

Run: `docker compose build migrate 2>&1 | tail -3`
Expected: build xong, không lỗi. Rồi: `docker run --rm dlck-backend sh -c 'ls /app && test ! -e /app/.env && test ! -e /app/backend/tests && test -f /app/database/alembic.ini && python -c "from core.env import REPO_ROOT; print(REPO_ROOT)"'`
Expected: in `backend database`, rồi `/app` — dòng cuối là bằng chứng `REPO_ROOT` đã đúng cấp. Dán vào ledger.

- [ ] **Step 8: Commit**

```bash
git add deploy/backend.Dockerfile .dockerignore docker-compose.yml docker-compose.vps.yml backend/pyproject.toml backend/uv.lock backend/tests/docs/test_d03_compose_contract.py backend/tests/clickhouse/test_c99_dedup_probe.py
git rm backend/.dockerignore deploy/infra/docker-compose.yml deploy/infra/docker-compose.vps.yml deploy/app/docker-compose.yml
git commit -m "feat(deploy): one root compose and a self-contained image that carries database/"
```

---

### Task 8: `core.bootstrap` — migrate hai kho, cấp 4 user login, tự seed ngành lớp 2

**Files:**
- Create: `backend/core/bootstrap.py`, `backend/tests/core/test_bootstrap_postgres.py`, `backend/tests/core/test_bootstrap_clickhouse.py`
- Delete: `database/clickhouse/create_users.sql.example`

**Interfaces:**
- Produces: `core.bootstrap.alembic_config(url) -> alembic.config.Config` · `provision_postgres(engine, users: list[tuple[str,str,str]]) -> list[str]` · `provision_clickhouse(client, users) -> list[str]` · `reseed_industry_if_needed(engine, cfg) -> tuple[str, int]` (`"skipped:security-rong"` · `"skipped:da-co"` · `"seeded"`) · `main(argv=None) -> int` (0 · 2).
- Consumes: `core.env.load_dotenv`, `core.ch_migrate.get_client/upgrade`, fixture `migrated_engine` (Postgres test) và `migrated`/`ch` (ClickHouse tạm) từ `tests/conftest.py`.

- [ ] **Step 1: Test đỏ Postgres** `backend/tests/core/test_bootstrap_postgres.py`:

```python
"""Cấp user login từ env: tạo nếu chưa có, LUÔN đổi mật khẩu theo env, thuộc đúng role (spec §5.4).
Chạy trên `dulieu_test` bằng owner; role cấp cluster nên tên bắt đầu `zz_test_` và dọn ở finally."""
import json
import os
import pathlib

import sqlalchemy as sa

from core import bootstrap

MAP_JSON = pathlib.Path(__file__).resolve().parents[3] / "docs" / "20-design" / "industry-mapping.json"


def _can_connect(base_url: sa.URL, user: str, password: str) -> bool:
    url = base_url.set(username=user, password=password)
    eng = sa.create_engine(url)
    try:
        with eng.connect() as c:
            return c.execute(sa.text("SELECT 1")).scalar_one() == 1
    except sa.exc.OperationalError:
        return False
    finally:
        eng.dispose()


def test_provision_creates_login_user_in_role_and_rotates_password(migrated_engine):
    name = "zz_test_etl_login"
    try:
        assert bootstrap.provision_postgres(migrated_engine, [(name, "pw-one", "dlck_etl")]) == [name]
        with migrated_engine.connect() as c:
            assert c.execute(sa.text("SELECT pg_has_role(:n, 'dlck_etl', 'member')"), {"n": name}).scalar_one() is True
            assert c.execute(sa.text("SELECT rolcanlogin FROM pg_roles WHERE rolname = :n"), {"n": name}).scalar_one() is True
        assert _can_connect(migrated_engine.url, name, "pw-one")
        bootstrap.provision_postgres(migrated_engine, [(name, "pw-two", "dlck_etl")])
        assert _can_connect(migrated_engine.url, name, "pw-two")
        assert not _can_connect(migrated_engine.url, name, "pw-one")
    finally:
        with migrated_engine.begin() as c:
            c.execute(sa.text(f"DROP ROLE IF EXISTS {name}"))


def test_provision_rejects_a_name_that_is_not_an_identifier(migrated_engine):
    import pytest
    with pytest.raises(ValueError):
        bootstrap.provision_postgres(migrated_engine, [("bad name; --", "x", "dlck_etl")])


def test_reseed_skips_when_security_is_empty(migrated_engine):
    cfg = bootstrap.alembic_config(os.environ["TEST_DATABASE_URL"])
    assert bootstrap.reseed_industry_if_needed(migrated_engine, cfg) == ("skipped:security-rong", 0)


def test_reseed_seeds_the_matching_ticker_then_skips(migrated_engine):
    ticker = json.loads(MAP_JSON.read_text(encoding="utf-8"))["layer2"][0]["ticker"]   # đọc từ chủ, không hardcode
    with migrated_engine.begin() as c:
        iid = c.execute(sa.text(
            "INSERT INTO market.issuer (name, com_type_code, icb_code) VALUES ('ZZ seed probe', 'NH', '8355') RETURNING issuer_id"
        )).scalar_one()
        c.execute(sa.text(
            "INSERT INTO market.security (ticker, exchange, security_type, issuer_id) VALUES (:t, 'HOSE', 'stock', :i)"),
            {"t": ticker, "i": iid})
    try:
        cfg = bootstrap.alembic_config(os.environ["TEST_DATABASE_URL"])
        assert bootstrap.reseed_industry_if_needed(migrated_engine, cfg) == ("seeded", 1)
        with migrated_engine.connect() as c:
            assert c.execute(sa.text("SELECT count(*) FROM market.issuer_industry_override WHERE issuer_id = :i"),
                             {"i": iid}).scalar_one() == 1
        assert bootstrap.reseed_industry_if_needed(migrated_engine, cfg)[0] == "skipped:da-co"
    finally:
        with migrated_engine.begin() as c:
            c.execute(sa.text("DELETE FROM market.issuer_industry_override"))
            c.execute(sa.text("DELETE FROM market.security WHERE issuer_id = :i"), {"i": iid})
            c.execute(sa.text("DELETE FROM market.issuer WHERE issuer_id = :i"), {"i": iid})
```

và `backend/tests/core/test_bootstrap_clickhouse.py`:

```python
"""User ClickHouse: SELECT được `rt.*`, DDL bị chặn, mật khẩu đổi theo env — trên container CH tạm (fixture gốc)."""
import os

import clickhouse_connect
import pytest
from clickhouse_connect.driver.exceptions import ClickHouseError

from core import bootstrap


def _client(host_port: str, user: str, password: str):
    return clickhouse_connect.get_client(dsn=f"http://{user}:{password}@{host_port}")


def test_provision_clickhouse_user_can_select_not_ddl_and_password_rotates(migrated):
    host_port = os.environ["CLICKHOUSE_URL"].rsplit("@", 1)[1]
    name = "zz_test_ingester_login"
    try:
        assert bootstrap.provision_clickhouse(migrated, [(name, "pw-one", "dlck_ingester")]) == [name]
        c1 = _client(host_port, name, "pw-one")
        assert int(c1.command("SELECT count() FROM rt.schema_migrations")) >= 1
        with pytest.raises(ClickHouseError):
            c1.command("CREATE TABLE rt.zz_probe (x UInt8) ENGINE = Memory")
        bootstrap.provision_clickhouse(migrated, [(name, "pw-two", "dlck_ingester")])
        with pytest.raises(ClickHouseError):
            _client(host_port, name, "pw-one").command("SELECT 1")
        assert int(_client(host_port, name, "pw-two").command("SELECT 1")) == 1
    finally:
        migrated.command(f"DROP USER IF EXISTS {name}")
```

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/core/test_bootstrap_postgres.py tests/core/test_bootstrap_clickhouse.py -q`
Expected: đỏ `ModuleNotFoundError: core.bootstrap`.

- [ ] **Step 2: Viết `backend/core/bootstrap.py`**

```python
"""Bootstrap hai kho — lệnh của service one-shot `migrate` (spec lát 12 §5.4).

Thứ tự cứng, idempotent, chạy bằng OWNER hai kho (URL ráp từ nguyên tố): (1) alembic head ·
(2) ch_migrate · (3) bốn user login — tạo nếu chưa có, LUÔN đổi mật khẩu theo env để `.env` là nguồn
thật · (4) tự seed ngành lớp 2 khi `market.security` có dòng mà bảng override rỗng (bước 3 của
"Bootstrap DB mới" trong database/README.md — trước đây phải nhớ làm tay).

Mọi lỗi ⇒ exit 2 kèm một dòng lý do. Không in giá trị secret.
"""
from __future__ import annotations

import logging
import os
import re
import sys

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from psycopg import sql

from core import ch_migrate
from core.env import REPO_ROOT, load_dotenv

log = logging.getLogger("bootstrap")
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# (biến tên, biến mật khẩu, role) — tên role là của migration 0009 / 0001_roles.sql
PG_USERS = (("ETL_DB_USER", "ETL_DB_PASSWORD", "dlck_etl"), ("AGENT_DB_USER", "AGENT_DB_PASSWORD", "dlck_api"))
CH_USERS = (("CLICKHOUSE_INGESTER_USER", "CLICKHOUSE_INGESTER_PASSWORD", "dlck_ingester"),
            ("CLICKHOUSE_API_USER", "CLICKHOUSE_API_PASSWORD", "dlck_api"))
REQUIRED = ("DATA_DATABASE_URL", "CLICKHOUSE_URL") + tuple(v for u in PG_USERS + CH_USERS for v in u[:2])


def _ident(name: str) -> str:
    if not _IDENT.fullmatch(name):
        raise ValueError(f"tên không phải identifier: {name!r}")
    return name


def alembic_config(url: str) -> Config:
    cfg = Config(str(REPO_ROOT / "database" / "alembic.ini"))
    os.environ["DATA_DATABASE_URL"] = url      # migrations/env.py đọc biến này — GÁN, không setdefault
    os.chdir(REPO_ROOT)                        # script_location tương đối gốc repo
    return cfg


def provision_postgres(engine: sa.Engine, users) -> list[str]:
    done: list[str] = []
    with engine.begin() as conn:
        raw = conn.connection.driver_connection          # psycopg.Connection — để ghép identifier/literal an toàn
        for name, password, role in users:
            _ident(name), _ident(role)
            with raw.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (name,))
                if cur.fetchone() is None:
                    cur.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(name)))
                cur.execute(sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(sql.Identifier(name), sql.Literal(password)))
                cur.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(role), sql.Identifier(name)))
            done.append(name)
    return done


def _ch_literal(s: str) -> str:
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def provision_clickhouse(client, users) -> list[str]:
    done: list[str] = []
    for name, password, role in users:
        _ident(name), _ident(role)
        client.command(f"CREATE USER IF NOT EXISTS {name} IDENTIFIED WITH sha256_password BY {_ch_literal(password)}")
        client.command(f"ALTER USER {name} IDENTIFIED WITH sha256_password BY {_ch_literal(password)}")
        client.command(f"GRANT {role} TO {name}")
        client.command(f"ALTER USER {name} DEFAULT ROLE {role}")
        done.append(name)
    return done


SEED_REVISION = "0013"      # seed industry_icb_map (55) + issuer_industry_override (161)


def _rerun_seed_revision(engine: sa.Engine, cfg: Config) -> None:
    """Chạy lại ĐÚNG MỘT migration `0013` (downgrade = DELETE hai bảng seed, upgrade = nạp lại) trong một
    transaction, KHÔNG đụng `alembic_version`, KHÔNG đụng migration nào khác.

    🔴 Vì sao không `alembic downgrade 0012` → `upgrade head` như README từng ghi: câu đó đúng khi head
    là `0013`. Head nay là `0020`, nên `downgrade 0012` lùi TÁM migration — DROP `news.article_industry`,
    `ops.llm_call`, `ops.snapshot_check`… kèm dữ liệu. Phát hiện lúc viết plan lát 12 (2026-09-08).
    """
    module = ScriptDirectory.from_config(cfg).get_revision(SEED_REVISION).module
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):          # cài proxy `alembic.op` để `op.execute` trong migration chạy
            module.downgrade()
            module.upgrade()


def reseed_industry_if_needed(engine: sa.Engine, cfg: Config) -> tuple[str, int]:
    """Kho mới: `0013` chạy lúc `market.security` rỗng ⇒ lớp 2 0 dòng, không báo. Khi security đã có
    dòng mà override rỗng thì chạy lại riêng `0013` (xem `_rerun_seed_revision`)."""
    q_sec = sa.text("SELECT count(*) FROM market.security WHERE issuer_id IS NOT NULL")
    q_ovr = sa.text("SELECT count(*) FROM market.issuer_industry_override")
    with engine.connect() as c:
        n_sec, n_ovr = c.execute(q_sec).scalar_one(), c.execute(q_ovr).scalar_one()
    if n_sec == 0:
        return "skipped:security-rong", n_ovr
    if n_ovr > 0:
        return "skipped:da-co", n_ovr
    _rerun_seed_revision(engine, cfg)
    with engine.connect() as c:
        n_after = c.execute(q_ovr).scalar_one()
    if n_after == 0:
        raise RuntimeError("seed lớp 2 chạy lại mà vẫn 0 dòng — security có dòng nhưng không ticker nào khớp")
    return "seeded", n_after


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    if missing:
        print("bootstrap: thiếu env: " + ", ".join(missing), file=sys.stderr)
        return 2
    pg_url = os.environ["DATA_DATABASE_URL"]
    try:
        cfg = alembic_config(pg_url)
        command.upgrade(cfg, "head")
        print("bootstrap: postgres migrate xong (head)")
        ch = ch_migrate.get_client(os.environ["CLICKHOUSE_URL"])
        ran = ch_migrate.upgrade(ch)
        print(f"bootstrap: clickhouse migrate: {ran or 'không có gì mới'}")
        engine = sa.create_engine(pg_url, pool_pre_ping=True)
        try:
            pg_users = [(os.environ[u], os.environ[p], role) for u, p, role in PG_USERS]
            print("bootstrap: postgres user: " + ", ".join(provision_postgres(engine, pg_users)))
            ch_users = [(os.environ[u], os.environ[p], role) for u, p, role in CH_USERS]
            print("bootstrap: clickhouse user: " + ", ".join(provision_clickhouse(ch, ch_users)))
            how, n = reseed_industry_if_needed(engine, cfg)
            print(f"bootstrap: seed ngành lớp 2: {how} ({n} dòng override)")
        finally:
            engine.dispose()
    except Exception as e:  # noqa: BLE001 — one-shot: mọi lỗi là exit 2 kèm lý do, không traceback trần
        print(f"bootstrap: LỖI {type(e).__name__}: {e}", file=sys.stderr)
        log.exception("bootstrap thất bại")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Chạy**

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/core/test_bootstrap_postgres.py tests/core/test_bootstrap_clickhouse.py -q`
Expected: `5 passed` (giả định 2.2.3 của spec — `ALTER USER … IDENTIFIED WITH` trên tag `26.3.22.7` — đóng bằng test CH; ghi ledger).

- [ ] **Step 4: Xoá template tay, commit**

```bash
git rm database/clickhouse/create_users.sql.example
git add backend/core/bootstrap.py backend/tests/core/test_bootstrap_postgres.py backend/tests/core/test_bootstrap_clickhouse.py
git commit -m "feat(bootstrap): one-shot that migrates both stores, provisions the four login users from env and re-seeds industry layer 2"
```

---

### Task 9: Dựng kho mới trên project `dlck` — AC2 · giả định 2.2.1 · seed 161 · AC4 · AC7

**Files:** ledger.

**Điều kiện:** `.env` đã theo hình dạng mới (Task 2 Step 6). Chạy **ngoài giờ 08:30–15:10** để ingester ở trạng thái "ngoài phiên"; nếu buộc chạy trong giờ, ghi rõ vào ledger và đọc log tương ứng.

- [ ] **Step 1: Hạ kho cũ, giữ volume** (chỉ container + mạng ngoài):

```bash
docker rm -f infra-postgres-1 infra-redis-1 infra-clickhouse-1
docker network rm dlck-net || true
docker ps -a --format '{{.Names}}' | grep -E '^infra-' ; echo "(rỗng là đúng)"
```

- [ ] **Step 2: Lên** (gốc repo):

```bash
docker compose up -d --build 2>&1 | tail -15
docker compose ps -a
```

Expected: `migrate` `Exited (0)`; `postgres`/`redis`/`clickhouse` `(healthy)`; `api`/`etl`/`ingester` `Up`. Dán `docker compose ps -a` vào ledger.

```bash
docker compose logs migrate
```

Expected 4 dòng `bootstrap: …`: `postgres migrate xong (head)` · `clickhouse migrate: ['0001_roles', '0002_rt_schema']` · `postgres user: etl_worker, agent_reader` · `clickhouse user: ingester_worker, api_reader` · `seed ngành lớp 2: skipped:security-rong (0 dòng override)`.

- [ ] **Step 3: AC2 còn lại**

```bash
curl -s http://127.0.0.1:8000/api/healthz
docker compose logs --tail 3 etl
docker compose logs --tail 3 ingester
```

Expected: `{"status":"ok","service":"api"}` · dòng `[etl] alive at …` · dòng `run: ngoài phiên, chờ tới 2026-…T08:30:00+07:00`.

- [ ] **Step 4: Giả định 2.2.1 — one-shot chạy lại ở lần `up` sau**

```bash
docker compose up -d 2>&1 | grep -i migrate
docker compose ps -a migrate --format '{{.Name}} {{.Status}}'
docker compose logs migrate | grep -c "bootstrap: seed"
```

Expected: `migrate` được `Started`/`Created` lại, `Exited (0)` với thời điểm mới; đếm `2` dòng seed (hai lượt). Nếu **không** chạy lại: ghi ledger, và runbook §5.8 chuyển thành `docker compose run --rm migrate` sau `up` (spec 2.2.1 đảo — cập nhật spec bằng một ghi chú đính chính, không viết lại).

- [ ] **Step 5: Danh bạ + seed 161**

```bash
docker compose run --rm etl python -m etl refdata; echo "exit=$?"
docker compose run --rm migrate
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select (select count(*) from market.security) as security, (select count(*) from market.issuer_industry_override) as override"
```

Expected: `exit=0`; migrate in `seed ngành lớp 2: seeded (161 dòng override)`; psql: `security` > 1.500, `override` = **161**. (`$POSTGRES_USER`/`$POSTGRES_DB` lấy từ shell: `set -a && . ./.env && set +a` trước, hoặc gõ tay tên user/db — không dán mật khẩu.)

- [ ] **Step 6: AC4 — ingester trong container ngoài giờ**

```bash
docker compose run --rm ingester python -m ingester --minutes 2; echo "exit=$?"
docker compose run --rm ingester sh -c 'ls -la /var/lib/dlck/logs /var/lib/dlck/spill && tail -5 /var/lib/dlck/logs/ingester-*.log'
```

Expected: exit `0` hoặc `1` (**không** `2`/`3`), stdout có dòng `reconcile: p1=… p2=… ok=…`; log có `run: N mã, M topic` (hợp đồng khởi động qua dưới `ingester_worker`); thư mục spill tồn tại (thường thấy `owner.lock`). Không có dòng `lỗi I/O trên thư mục spill` và không exit 3 ⇒ giả định 2.2.2 (khoá file trên volume) đóng. Dán vào ledger. (Service `ingester` daemon đang ngủ ngoài phiên nên không giữ leader lock — lượt `--minutes 2` này là leader.)

- [ ] **Step 7: AC7 — backup trong container**

```bash
docker compose run --rm etl python -m core.ch_backup
ls deploy/infra/clickhouse-backups | head
```

Expected: `backup: ['bar_1m-YYYYMMDD.zip', 'index_bar_1m-YYYYMMDD.zip', …]` và file `.zip` xuất hiện trên host.

- [ ] **Step 8: Ghi ledger, commit**

```bash
git add docs/90-records/plans/2026-09-08-container-runtime/ledger.md
git commit -m "docs(ledger): fresh store up on project dlck — AC2, AC4, AC7 and the one-shot re-run assumption"
```

---

### Task 9a — BỔ SUNG theo phán quyết 2026-09-08 (Task 9 chặn ở AC4): volume runtime thuộc root, appuser không ghi được

**Sự thật đo:** `docker compose run --rm ingester python -m ingester --minutes 2` chết `PermissionError: [Errno 13] Permission denied: '/var/lib/dlck/logs/ingester-20260908.log'`, exit **1**. Ba volume có tên gắn vào `/var/lib/dlck/{logs,measure,spill}` được Docker tạo `root:root 755` vì image không có sẵn thư mục đó; container chạy `appuser` (uid 1000). Daemon `dlck-ingester-1` đang ngủ cũng sẽ chết y hệt lúc mở phiên. Lỗ thứ hai: mở file log nằm ngoài hợp đồng khởi động nên thoát 1 (traceback trần) thay vì 2.

**Files:** Modify `deploy/backend.Dockerfile`, `backend/ingester/main.py`, `backend/tests/ingester/test_i16_daemon.py`, `backend/tests/docs/test_d03_compose_contract.py`.

- [ ] **Step 1: Test đỏ.** Thêm vào `backend/tests/docs/test_d03_compose_contract.py` (thêm `import re` đầu file):

```python
def test_image_owns_the_runtime_dirs_for_appuser():
    """Volume có tên lấy quyền từ thư mục điểm gắn trong image; không có sẵn thì Docker tạo root:root và appuser không ghi được (AC4 lát 12)."""
    dockerfile = (REPO / "deploy" / "backend.Dockerfile").read_text(encoding="utf-8")
    for d in ("/var/lib/dlck/logs", "/var/lib/dlck/measure", "/var/lib/dlck/spill", "/backups"):
        assert d in dockerfile, d
    assert re.search(r"chown -R appuser [^
]*/var/lib/dlck", dockerfile)
```

và vào `backend/tests/ingester/test_i16_daemon.py` (thêm `from ingester.config import Config as IngesterConfig`):

```python
def test_run_exits_2_when_the_day_log_cannot_be_opened(tmp_path, monkeypatch, capsys):
    """Mở file log là điều kiện khởi động: volume sai quyền, ổ đầy ⇒ exit 2 có lý do, không traceback exit 1."""
    blocker = tmp_path / "logs"
    blocker.write_text("file, không phải thư mục", encoding="utf-8")
    cfg = IngesterConfig(clickhouse_url="fake://", redis_url="redis://x",
                         log_dir=blocker, measure_dir=tmp_path, spill_dir=tmp_path)
    monkeypatch.setattr(main_mod.config, "load", lambda need_db: cfg)
    assert asyncio.run(main_mod.run("run", minutes=1)) == 2
    assert "không ghi được log" in capsys.readouterr().err
```

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/docs/test_d03_compose_contract.py tests/ingester/test_i16_daemon.py -q` — Expected: hai test mới đỏ (Dockerfile chưa có thư mục; `run` ném `OSError` thay vì trả 2).

- [ ] **Step 2: Dockerfile** — thay dòng `RUN useradd -m appuser && chown -R appuser /app` bằng:

```dockerfile
# Điểm gắn volume phải có sẵn và thuộc appuser: Docker chép quyền của thư mục trong image sang volume mới;
# không có sẵn thì volume ra đời root:root và tiến trình non-root không ghi được (AC4 lát 12, 2026-09-08).
RUN mkdir -p /var/lib/dlck/logs /var/lib/dlck/measure /var/lib/dlck/spill /backups  && useradd -m appuser && chown -R appuser /app /var/lib/dlck /backups
```

- [ ] **Step 3: `ingester/main.py`** — giữ `_day_log_handler(cfg)` (tạo handler, ném `OSError`), thêm ngay dưới nó:

```python
def _attach_day_log(cfg: config.Config) -> logging.Handler | None:
    """Gắn file log theo ngày vào root logger. Không mở được (volume sai quyền, ổ đầy…) ⇒ in lý do, trả None —
    caller trả 2 theo hợp đồng "thiếu điều kiện khởi động ⇒ exit 2" (AC4 lát 12: volume root:root)."""
    try:
        h = _day_log_handler(cfg)
    except OSError as e:
        print(f"ingester: không ghi được log trong {cfg.log_dir}: {e}", file=sys.stderr)
        return None
    logging.getLogger().addHandler(h)
    return h
```

Ba chỗ dùng: `reconcile` — `if _attach_day_log(cfg) is None: return 2`; `run --minutes` — như trên trước khi gọi `_session_with_relay`; daemon `session()` — `h = _attach_day_log(cfg)`, `if h is None: return 2`, `try: … finally: root.removeHandler(h); h.close()`.

- [ ] **Step 4: Xanh + commit**

Run: lệnh Step 1 — Expected: xanh. Commit: `fix(deploy,ingester): runtime dirs owned by appuser in the image; unopenable day log exits 2`.

- [ ] **Step 5 (vận hành, sau review): dựng lại volume runtime rỗng và tiếp Task 9 từ Step 6.** Ba volume `dlck_ingester_*` mới tạo hôm nay, chưa có gì (daemon chưa mở phiên, probe chết trước khi ghi) — xoá để Docker tạo lại với quyền từ image:

```bash
docker compose down
docker volume rm dlck_ingester_logs dlck_ingester_measure dlck_ingester_spill
docker compose up -d --build
docker compose run --rm ingester sh -c 'ls -ld /var/lib/dlck/logs /var/lib/dlck/measure /var/lib/dlck/spill'
```

Expected: ba dòng `drwxr-xr-x … appuser appuser …`. Rồi chạy Task 9 Step 6 (AC4) và Step 7 (AC7) như brief Task 9; ghi ledger. Ghi chú giả định 2.2.1: lượt `up` thứ hai **recreate** container one-shot nên `docker compose logs migrate` chỉ giữ log lượt mới — bằng chứng là mốc `Exited (0)` mới, không phải `grep -c … == 2`.

---

### Task 10: AC3 — 15 họ job trong container · AC-SIGTERM · AC5 · AC6 · AC8

**Files:** ledger.

**Điều kiện:** `LLM_API` và `FRED_API` có trong `.env` (chủ dự án xác nhận — không in). Chạy theo đúng thứ tự (phụ thuộc dữ liệu trên kho mới).

- [ ] **Step 1: AC3 — chạy từng lệnh, ghi `exit` và dòng `ops.etl_run` mới nhất**

```bash
J() { docker compose run --rm etl python -m etl "$@"; echo "exit=$?"; }
J events --accept-new
J price --codes FPT,VNM
J snapshot --codes FPT --kinds snapshot
J fundamentals --codes FPT --kinds bs
J screener
J omo
J wichart --keys vang
J fred --keys DGS10
J fx
J lbma
J yahoo --keys '^GSPC'
J binance --intraday
J news --sources cafef
J classify --limit 1
```

(`refdata` đã chạy ở Task 9 — đếm là họ thứ 15.) Sau đó:

```bash
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select distinct on (job) job, status, left(coalesce(error,''),60) as error, finished_at from ops.etl_run order by job, run_id desc"
```

Expected: mỗi họ **≥ 1 dòng**; `status` ∈ {`success`, `failed`}; `failed` chỉ được là guard từ chối có lý do (`screener` ngoài phiên — đúng hành vi) hoặc `quota_stop`; **không** lệnh nào `exit=2`. Bảng 15 dòng `họ | cờ | exit | status | ghi chú` vào ledger. Bất kỳ `exit=2` ⇒ dừng, báo, không tự lách.

- [ ] **Step 2: AC-SIGTERM — `docker stop` đóng sổ như Ctrl+C**

```bash
docker compose run -d --name sigterm-probe etl python -m etl price --backfill --max-minutes 5
sleep 20 && docker stop -t 60 sigterm-probe
docker inspect sigterm-probe --format '{{.State.ExitCode}}'; docker rm sigterm-probe
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select status, error from ops.etl_run where job='market.price_backfill' order by run_id desc limit 1"
```

Expected: exit code `130`; dòng sổ `failed | dừng tay (Ctrl+C)`.

- [ ] **Step 3: AC5 — `down` rồi `up` không mất gì**

```bash
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "select (select count(*) from ops.etl_run), (select count(*) from market.security)"
docker compose exec clickhouse clickhouse-client --password "$CLICKHOUSE_PASSWORD" -q "select count() from rt.schema_migrations"
docker volume ls --format '{{.Name}}' | grep '^dlck_' | sort > /tmp/vol-before.txt
docker compose down && docker compose up -d
docker compose ps -a migrate --format '{{.Status}}'
# lặp lại ba phép đếm, và:
docker volume ls --format '{{.Name}}' | grep '^dlck_' | sort | diff - /tmp/vol-before.txt && echo "volume: không đổi"
```

Expected: ba số **bằng nhau** trước/sau; `migrate` `Exited (0)`; `volume: không đổi` (6 volume `dlck_*`).

- [ ] **Step 4: AC6 — đổi mật khẩu một user, bootstrap đồng bộ**

Chủ dự án đổi `ETL_DB_PASSWORD` trong `.env` (giá trị mới, không dán). Rồi:

```bash
docker compose run --rm migrate | grep "postgres user"
docker compose run --rm etl python -m etl omo; echo "exit=$?"
```

Expected: `postgres user: etl_worker, agent_reader`; `exit=0` — job đi bằng mật khẩu mới (URL ráp từ `.env` mới). Ghi ledger "AC6 đạt", không ghi giá trị.

- [ ] **Step 5: AC8 nửa native — job native vào cùng kho** (cả bộ pytest chạy ở Task 11 Step 8, sau khi tài liệu hết link chết)

```bash
cd backend && PYTHONIOENCODING=utf-8 uv run python -m etl omo; echo "exit=$?"
```

Expected: `exit=0` — native vào **cùng kho** `dlck` qua `127.0.0.1`, cùng `.env`.

- [ ] **Step 6: Commit ledger**

```bash
git add docs/90-records/plans/2026-09-08-container-runtime/ledger.md
git commit -m "docs(ledger): all 15 job families ran in the container; SIGTERM, down/up, password rotation and native checks"
```

---

### Task 10a — BỔ SUNG theo chỉ đạo chủ dự án 2026-09-08 (Task 10 chặn ở AC3): code không được đọc `docs/` — dữ liệu tra cứu dời vào code

**Sự thật đo (Task 10 Step 1, operator 18:51):** `fundamentals --codes FPT --kinds bs` trong container → `exit=2`, `FileNotFoundError: [Errno 2] No such file or directory: '/app/docs/10-sources/market/field-dictionary.json'`. `.dockerignore` gốc (spec §5.3) loại `docs`, Dockerfile không `COPY docs/` — **đúng thiết kế**; sai ở chỗ code đọc file dưới `docs/` lúc chạy. Grep code ngoài test (2026-09-08): **bốn** chỗ — `backend/etl/fundamentals_store.py:37` → `docs/10-sources/market/field-dictionary.json` · `backend/etl/news_registry.py:13` → `docs/10-sources/news/feeds.json` · `backend/etl/screener_normalize.py:29` → `docs/20-design/market-field-selection.json` · `backend/etl/wichart_registry.py:15` → `docs/10-sources/macro/wichart.md` (khối Python §9, đọc bằng `exec`). Bốn họ `fundamentals` `news` `screener` `wichart` cùng chết trong container. Thêm một script dev cùng lỗi: `database/gen_price_columns.py:17` đọc `docs/20-design/market-field-selection.json` bằng đường dẫn tương đối.

**Chỉ đạo chủ dự án (2026-09-08 ~19:05, nguyên văn):** *"code không được đọc doc, chỉ có bạn mới đọc docs để lấy kiến thức code, còn code cần kiến thức gì bạn phải viết lại vào code — trong backend hoặc db gì đó, không phải docs"* · *"không được đưa vào image [thứ] không sửa đổi và kiểm soát được, để hết ở trong code mới là đúng, các phần tra cứu cần dùng hardcode lại các file json hoặc md chuẩn hoá cần thiết"*. Phương án trợ lý định làm (image mang `docs/10-sources` + `docs/20-design`) **bị bác — không áp dụng**.

**Ruling thực thi:** `.dockerignore` **giữ nguyên** (`docs` vẫn bị loại; spec §5.3 đúng). Ba file JSON **`git mv`** sang `backend/etl/data/` — một chủ sở hữu duy nhất, docs chỉ trỏ tới (không chép thành hai bản, CLAUDE.md §1.7). Khối Python §9 của `wichart.md` thành module **`backend/etl/wichart_source.py`** (nội dung khối nguyên văn), `wichart_registry` import module thay vì `exec` markdown; `wichart.md` §9 giữ tiêu đề + một đoạn trỏ tới module. Luật của chủ dự án mã hoá thành test tĩnh (đỏ trước): **không file `.py` nào trong `backend/` (ngoài `backend/tests/`) và `database/` ráp đường dẫn vào `docs/`**. Không đổi tên/định dạng ba file JSON (đường dẫn đổi, nội dung không).

**Files:**
- Move (`git mv`, giữ lịch sử): `docs/10-sources/market/field-dictionary.json` → `backend/etl/data/field-dictionary.json` · `docs/10-sources/news/feeds.json` → `backend/etl/data/feeds.json` · `docs/20-design/market-field-selection.json` → `backend/etl/data/market-field-selection.json`
- Create: `backend/etl/wichart_source.py`
- Modify (code): `backend/etl/fundamentals_store.py` · `backend/etl/news_registry.py` · `backend/etl/screener_normalize.py` · `backend/etl/wichart_registry.py` · `database/gen_price_columns.py` · `docs/20-design/gen_field_selection.py` · `docs/10-sources/macro/verify_wichart.py` · `.gitattributes`
- Modify (test): `backend/tests/docs/test_d03_compose_contract.py` (+1 test) · `backend/tests/etl/test_e36_wichart_registry.py` · `backend/tests/docs/test_d01_docs_consistency.py` (hai chỗ `_read` feeds.json)
- Modify (tài liệu sống — link + câu chữ): `README.md` · `backend/README.md` · `docs/00-overview/roadmap.md` · `docs/10-sources/README.md` · `docs/10-sources/market/appendix-A-field-codes.md` · `docs/10-sources/news/README.md` · `docs/10-sources/news/article-structure.md` · `docs/10-sources/macro/wichart.md` · `docs/20-design/README.md` · `docs/20-design/market-field-selection.md` · `docs/20-design/news-pipeline.md`
- Modify (tài liệu lịch sử `docs/90-records/`, `docs/00-overview/decisions/` — **CHỈ href, giữ nhãn**): đúng những link mà `test_no_dead_internal_links` báo chết **do lượt dời này** (so với mốc Step 1)

- [ ] **Step 1: Mốc link chết TRƯỚC khi sửa** (tests/docs đang đỏ có chủ đích tới Task 11 vì file xoá ở Task 5/7 — lượt dời này **không được thêm** link chết mới)

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/docs/test_d01_docs_consistency.py::test_no_dead_internal_links -q 2>&1 | grep -E "^E\s+\S+:[0-9]+ -> " | sort > <report-dir>/deadlinks-before.txt; wc -l <report-dir>/deadlinks-before.txt`
Expected: một danh sách `file:dòng -> đích` (toàn bộ đều trỏ tới `register-tasks.ps1` · `core/console.py` · `stack.mjs` · `.dockerignore` · `deploy/app/docker-compose.yml` · `deploy/infra/docker-compose.vps.yml` · `create_users.sql.example` — file đã xoá ở Task 5/7/8). Đây là mốc so sánh ở Step 6.

- [ ] **Step 2: Test đỏ — code không đọc `docs/`** — thêm vào cuối `backend/tests/docs/test_d03_compose_contract.py` (đã có `import re`, `REPO`):

```python
def test_production_code_never_reads_docs():
    """Image không mang `docs/` (spec §5.3, `.dockerignore`) — mọi tri thức code cần lúc chạy phải nằm trong
    backend/ hoặc database/ (chỉ đạo chủ dự án 2026-09-08). Task 10 lát 12: `fundamentals` chết exit 2 trong
    container vì đọc docs/10-sources/…; `news` · `screener` · `wichart` cùng lỗi. Quét tĩnh, không dựng container."""
    pat = re.compile(r"""["']docs["']\s*/|["']docs/""")
    skip = {".venv", "__pycache__", ".pytest_cache", "node_modules"}
    hits = []
    for root in (REPO / "backend", REPO / "database"):
        for py in sorted(root.rglob("*.py")):
            rel = py.relative_to(REPO).as_posix()
            parts = set(rel.split("/"))
            if parts & skip or rel.startswith("backend/tests/"):
                continue
            for n, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                if pat.search(line):
                    hits.append(f"{rel}:{n}: {line.strip()}")
    assert not hits, "code ráp đường dẫn vào docs/ — dời tri thức vào backend/ hoặc database/:\n  " + "\n  ".join(hits)
    ignore = (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert "docs" in ignore                                    # image vẫn không mang docs/
```

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/docs/test_d03_compose_contract.py -q -k never_reads_docs 2>&1 | tail -12`
Expected: **FAIL**, thông báo liệt kê đúng **5** dòng: `backend/etl/fundamentals_store.py:37` · `backend/etl/news_registry.py:13` · `backend/etl/screener_normalize.py:29` · `backend/etl/wichart_registry.py:15` · `database/gen_price_columns.py:17`. (Nếu ra thêm dòng nào khác ⇒ dòng đó cũng phải sửa ở Step 4; nếu ít hơn 5 ⇒ regex sai, sửa test trước.) Lưu ý `rglob` đi qua `backend/.venv` nhưng bộ lọc `skip` loại bằng tên thư mục — nếu chậm > 30 s thì đổi sang `os.walk` cắt `dirs[:]`, giữ nguyên ngữ nghĩa.

- [ ] **Step 3: Dời ba file JSON, sửa `.gitattributes`**

```bash
mkdir -p backend/etl/data
git mv docs/10-sources/market/field-dictionary.json backend/etl/data/field-dictionary.json
git mv docs/10-sources/news/feeds.json               backend/etl/data/feeds.json
git mv docs/20-design/market-field-selection.json    backend/etl/data/market-field-selection.json
```

`.gitattributes` dòng `docs/20-design/market-field-selection.json  text eol=lf` → `backend/etl/data/market-field-selection.json  text eol=lf`. Kiểm: `git status --short | grep -c "^R"` → `3`.

- [ ] **Step 4: Code trỏ vào `etl/data/`; khối §9 thành module**

(a) `backend/etl/fundamentals_store.py:37` → `DICTIONARY_JSON = Path(__file__).resolve().parent / "data" / "field-dictionary.json"`.
(b) `backend/etl/news_registry.py:13` → `FEEDS_JSON = Path(__file__).resolve().parent / "data" / "feeds.json"`; docstring dòng 1–2: vế *"đọc từ docs/10-sources/news/feeds.json (chủ duy nhất của danh sách feed, như wichart_registry đọc khối Python trong wichart.md)"* → *"đọc từ `etl/data/feeds.json` (chủ duy nhất của danh sách feed — dời từ `docs/` vào code 2026-09-08, lát 12 Task 10a)"*.
(c) `backend/etl/screener_normalize.py:29` → `SELECTION_JSON = Path(__file__).resolve().parent / "data" / "market-field-selection.json"`.
(d) **Tạo `backend/etl/wichart_source.py`:** docstring dưới đây + **nguyên văn** nội dung khối Python cuối `docs/10-sources/macro/wichart.md` (mọi dòng nằm giữa fence mở ```` ```python ```` ở dòng 610 và fence đóng ở dòng 799 — tức dòng 611–798; định nghĩa `BASE`, `url()`, `G`/`D`, `WICHART`, `TIER_X`, `SRCNOTE`; **không đổi một ký tự dữ liệu nào**, kể cả hai dòng comment đầu khối):

```python
"""Bảng đo về nguồn WiChart — 87 key: series, đơn vị gốc, hệ số `scale`, role, cờ, tier, `SRCNOTE`.

Từng là khối Python §9 của `docs/10-sources/macro/wichart.md` (audit 2026-08-12, đo lại 2026-08-15 · 2026-09-05 · 2026-09-07).
Dời nguyên văn vào code 2026-09-08 (lát 12, Task 10a): code không đọc `docs/`, image không mang `docs/`.
Chủ sở hữu duy nhất của bảng này là module này; `wichart.md` giữ phần người đọc (bẫy, quy ước, cách đo).
Sửa số ở đây CHỈ khi đo lại (CLAUDE.md §1.2). `etl.wichart_registry.build()` ghép bảng này với MACRO/ASSET;
`docs/10-sources/macro/verify_wichart.py` đọc module này để đối chiếu với API sống.
"""
```

(e) `backend/etl/wichart_registry.py`: bỏ `WICHART_MD` (và `import re`, `Path` nếu mồ côi sau khi bỏ); thêm `from etl import wichart_source` ở khối import; docstring đầu file: gạch đầu dòng thứ nhất thành *"- `etl/wichart_source.py` (từng là §9 `wichart.md`, dời vào code 2026-09-08): sự thật ĐO về nguồn — tên series, đơn vị gốc, `scale`, role, cờ, nhóm, tần suất."* và bỏ vế "Đọc bằng `exec`, đúng cách `verify_wichart.py` làm". Seam mới:

```python
def load_doc() -> tuple[dict, list[str]]:
    """Trả (WICHART, TIER_X) từ bảng đo về nguồn — module `etl.wichart_source` sở hữu (từng là khối §9 wichart.md)."""
    return wichart_source.WICHART, list(wichart_source.TIER_X)


def build(doc: dict | None = None, tier_x: list[str] | None = None) -> list[Series]:
    if doc is None:
        doc, tier_x = load_doc()
    tier_x = list(tier_x or [])
    # … phần thân giữ nguyên từ dòng `out: list[Series] = []` trở xuống …
```

`tests/etl/test_e41_wichart_job.py:19` gọi `wr.load_doc()` không đối số — vẫn chạy. Không còn `RegistryError("không thấy khối Python …")`.
(f) `database/gen_price_columns.py:17` → `pathlib.Path(__file__).resolve().parents[1] / "backend" / "etl" / "data" / "market-field-selection.json"` (`parents[1]` của `database/gen_price_columns.py` = gốc repo).
(g) `docs/20-design/gen_field_selection.py`: `DICT = HERE.parents[1] / "backend" / "etl" / "data" / "field-dictionary.json"`; `OUT_JSON = HERE.parents[1] / "backend" / "etl" / "data" / "market-field-selection.json"`; hai href trong template (dòng 578, 710) `../10-sources/market/field-dictionary.json` → `../../backend/etl/data/field-dictionary.json`. **Không chạy lại generator** — sửa tay file sinh `docs/20-design/market-field-selection.md` (dòng 27, 631) đúng cùng chuỗi.
(h) `docs/10-sources/macro/verify_wichart.py`: bỏ `MD = …` (dòng 37) và bốn dòng đọc/`exec` (84–87); thay bằng:

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))   # gốc repo/backend
from etl import wichart_source                                              # bảng hardcode nay ở code (2026-09-08)
```

(đặt sau các `import` chuẩn; trong `main()` dùng `ns = vars(wichart_source)` thay cho dict `ns` từ `exec`). Docstring dòng 5 *"đọc bảng registry Python NGAY TRONG FILE MD"* → *"đọc bảng registry từ `backend/etl/wichart_source.py` (dời khỏi file MD 2026-09-08)"*. Bỏ `import re` nếu không còn dùng.

- [ ] **Step 5: Tài liệu — index và link theo file (§1.6, §1.7)**

Tài liệu sống (đổi href **và** câu chữ cho đúng sự thật mới):

| File:dòng | Sửa |
|---|---|
| `README.md:13` | href → `backend/etl/data/field-dictionary.json` |
| `backend/README.md:241` | chuỗi `docs/10-sources/market/field-dictionary.json` → `backend/etl/data/field-dictionary.json`; **thêm** ngay dưới dòng 13 ("Trạng thái phần code") một đoạn: *"**`etl/data/`** — dữ liệu tra cứu máy đọc mà job cần lúc chạy: `field-dictionary.json` (729 mã BCTC, `fundamentals`), `feeds.json` (47 feed + 8 crawl + taxonomy, `news`/`classify`), `market-field-selection.json` (chọn trường, `screener`); bảng đo WiChart ở `etl/wichart_source.py`. Dời từ `docs/` vào code 2026-09-08 (lát 12): code không đọc `docs/`, image không mang `docs/`. Tài liệu người đọc vẫn ở `docs/10-sources/`."* |
| `docs/00-overview/roadmap.md:22` | href → `../../backend/etl/data/field-dictionary.json` |
| `docs/00-overview/roadmap.md:467` | *"khối Python `WICHART`/`TIER_X`/`SRCNOTE` trong [wichart.md §9](../../../10-sources/macro/wichart.md)"* → *"khối Python `WICHART`/`TIER_X`/`SRCNOTE` — nay là [`backend/etl/wichart_source.py`](../../../../backend/etl/wichart_source.py) (dời khỏi wichart.md §9 ngày 2026-09-08)"* |
| `docs/10-sources/README.md:117` | href → `../../backend/etl/data/field-dictionary.json`; thêm *"(file nằm trong code từ 2026-09-08)"* |
| `docs/10-sources/README.md:125` | *"đọc registry ngay trong `wichart.md`"* → *"đọc registry từ `backend/etl/wichart_source.py`"* |
| `docs/10-sources/README.md:145` | href → `../../backend/etl/data/feeds.json`; thêm *"(file nằm trong code từ 2026-09-08)"* |
| `docs/10-sources/README.md:189` | *"đã hardcode ở [wichart.md §9](../../../10-sources/macro/wichart.md)"* → *"đã hardcode ở [`backend/etl/wichart_source.py`](../../../../backend/etl/wichart_source.py) (từng là wichart.md §9)"* |
| `docs/10-sources/market/appendix-A-field-codes.md:233` | href → `../../../backend/etl/data/field-dictionary.json` |
| `docs/10-sources/news/README.md:21` | href → `../../../backend/etl/data/feeds.json`; thêm *"(nằm trong code từ 2026-09-08)"* |
| `docs/10-sources/news/article-structure.md:24` | href → `../../../backend/etl/data/feeds.json` |
| `docs/10-sources/macro/wichart.md` §9 (dòng 608–799) | giữ tiêu đề `## 9. Bảng hardcode`; **thay trọn khối fence** bằng: *"Bảng hardcode (87 key · series · đơn vị gốc · `scale` · role · cờ · tier · `SRCNOTE`) **do [`backend/etl/wichart_source.py`](../../../../backend/etl/wichart_source.py) sở hữu từ 2026-09-08** (lát 12, Task 10a: code không đọc `docs/`, image không mang `docs/`). Khối Python từng nằm ở đây được dời nguyên văn, không đổi số nào. Ý nghĩa cột giữ nguyên: `scale` = nhân raw để về đơn vị gốc (đơn vị 1); `role` = `data` · `growth_ref` · `None` (không nạp); cờ cấp series và cấp key theo bộ ký hiệu của tài liệu này. Sửa số trong module chỉ khi đo lại (CLAUDE.md §1.2); [`verify_wichart.py`](../../../10-sources/macro/verify_wichart.py) đọc module đó để đối chiếu với API sống."* |
| `docs/20-design/README.md:14` | href bản máy đọc → `../../backend/etl/data/market-field-selection.json` |
| `docs/20-design/market-field-selection.md:27`, `:631` | href → `../../backend/etl/data/field-dictionary.json` (cùng chuỗi với template ở Step 4g) |
| `docs/20-design/news-pipeline.md:9`, `:456` | href → `../../backend/etl/data/feeds.json` |
| `docs/20-design/news-pipeline.md:433` | ô `docs/10-sources/news/feeds.json` → `backend/etl/data/feeds.json` |
| `backend/tests/docs/test_d01_docs_consistency.py:207`, `:243` | `_read("docs/10-sources/news/feeds.json")` → `_read("backend/etl/data/feeds.json")` |
| `backend/tests/etl/test_e36_wichart_registry.py` | docstring dòng 1: *"(khối §9 của wichart.md · bảng mã trong module)"* → *"(bảng đo `etl/wichart_source.py` · bảng mã trong `wichart_registry`)"*; test `test_build_raises_when_module_maps_a_series_the_doc_does_not_collect` viết lại (không còn đọc md): |

```python
def test_build_raises_when_module_maps_a_series_the_source_table_does_not_collect():
    import copy
    from etl import wichart_source as ws
    broken = copy.deepcopy(ws.WICHART)
    entries = list(broken["xang_dau"]["s"])
    assert entries[1][0] == "Giá xăng E5"
    entries[1] = ("Giá xăng E5", "VND/lít", 1e3, None, ["DEAD"])
    broken["xang_dau"]["s"] = entries
    with pytest.raises(wr.RegistryError, match=r"xang_dau\[1\]"):
        wr.build(doc=broken, tier_x=list(ws.TIER_X))
```

Tài liệu lịch sử (`docs/90-records/`, `docs/00-overview/decisions/`): chạy lại lệnh Step 1 vào `deadlinks-after.txt`; với mỗi dòng **có trong after mà không có trong before** ⇒ đó là link vỡ do lượt dời này ⇒ sửa **chỉ href** sang đích mới (`backend/etl/data/<file>` với số `../` đúng cấp), giữ nguyên nhãn hiển thị. Không sửa dòng nào khác trong hai vùng đó.

- [ ] **Step 6: Xanh + hồi quy + phép kiểm §1.7**

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/docs/test_d03_compose_contract.py -q 2>&1 | tail -3`
Expected: `9 passed` (8 cũ + `test_production_code_never_reads_docs`).

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/etl/test_e11_screener_normalize.py tests/etl/test_e35_fundamentals_job.py tests/etl/test_e36_wichart_registry.py tests/etl/test_e41_wichart_job.py tests/etl/test_e52_news_parse.py -q 2>&1 | tail -3`
Expected: tất cả pass, 0 failed (ghi số).

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/docs/test_d01_docs_consistency.py -q 2>&1 | tail -5` rồi `… ::test_no_dead_internal_links -q 2>&1 | grep -E "^E\s+\S+:[0-9]+ -> " | sort > <report-dir>/deadlinks-after.txt; diff <report-dir>/deadlinks-before.txt <report-dir>/deadlinks-after.txt && echo "deadlinks: không đổi"`
Expected: chỉ `test_no_dead_internal_links` còn đỏ (đúng nợ Task 11), mọi test khác trong file xanh; `diff` rỗng + `deadlinks: không đổi`.

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests/etl -q 2>&1 | tail -2`
Expected: `… passed` (0 failed; ghi số).

Run: `PYTHONIOENCODING=utf-8 uv run --project backend python -m py_compile docs/10-sources/macro/verify_wichart.py docs/20-design/gen_field_selection.py database/gen_price_columns.py && echo "compile: OK"` và `PYTHONIOENCODING=utf-8 uv run --project backend python -c "import sys; sys.path.insert(0,'backend'); from etl import wichart_source as w; print('WICHART', len(w.WICHART), 'keys; TIER_X', len(w.TIER_X))"`
Expected: `compile: OK`; một dòng đếm (ghi số vào report — không có expected cứng, chỉ để chứng minh module import được ngoài pytest).

Run: `git grep -n -E "[\"']docs[\"']\s*/|[\"']docs/" -- backend database ':!backend/tests' | wc -l`
Expected: `0`.

Run: `git grep -n "10-sources/market/field-dictionary.json\|10-sources/news/feeds.json\|20-design/market-field-selection.json" -- . ':!docs/90-records' ':!docs/00-overview/decisions' | grep -v "dời\|từng\|2026-09-08"`
Expected: **0 hit** ngoài vùng lịch sử (mọi câu còn nhắc đường cũ phải là câu kể chuyện dời, có ngày).

- [ ] **Step 7: Commit**

```bash
git add -A backend/etl backend/tests database/gen_price_columns.py docs .gitattributes README.md backend/README.md
git status --short   # kiểm: đúng 3 dòng R (rename) + các dòng M/A liệt kê ở mục Files, không có file lạ
git commit -m "fix(etl): lookup data moves from docs/ into backend/etl — production code never reads docs"
```

- [ ] **Step 8: Vận hành — image mới, chạy lại họ `fundamentals`** (gốc repo; không đọc `.env`, không `docker compose config`)

```bash
docker compose up -d --build 2>&1 | tail -8
docker run --rm dlck-backend sh -c 'test ! -e /app/docs && test -f /app/backend/etl/data/field-dictionary.json && test -f /app/backend/etl/data/feeds.json && test -f /app/backend/etl/data/market-field-selection.json && test -f /app/backend/etl/wichart_source.py && echo "image-data: OK"'
docker compose run --rm etl python -m etl fundamentals --codes FPT --kinds bs; echo "exit=$?"
docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' <<'SQL'
select run_id, job, status, left(coalesce(error,''),60) as error from ops.etl_run where job='market.fundamentals' order by run_id desc limit 2;
SQL
```

Expected: 7 service lên lại (`migrate` `Exited (0)`); `image-data: OK`; `exit=0` kèm dòng `fundamentals xong: {…}`; dòng `ops.etl_run` mới nhất của `market.fundamentals` là `success` (dòng trước đó — run 5 — vẫn `failed | FileNotFoundError…`, giữ làm bằng chứng). `exit=2` hay `exit=1` ⇒ dừng, báo nguyên trạng. Ghi output vào report; controller ghi ledger. Task 10 (tiếp) nối từ họ `screener`.

---

### Task 11: Tài liệu sống (spec §8) — cùng lượt, và "Điểm vào cho lát 13"

**Files:**
- Modify: `README.md`, `backend/README.md`, `database/README.md`, `docs/20-design/service-topology.md`, `docs/00-overview/roadmap.md`, `CLAUDE.md`, `docs/90-records/README.md`

- [ ] **Step 1: `README.md`** — (a) cây repo: dòng `deploy/infra/` thành `deploy/               backend.Dockerfile · infra/clickhouse/*.xml — compose nằm ở gốc: docker-compose.yml + docker-compose.vps.yml`, xoá dòng `scripts/`; (b) thay trọn mục "Dựng trên máy mới" (5 bước + hai đoạn 🔴/⚠️ "Hai bộ volume") bằng:

```markdown
## Dựng trên máy mới — dev hay VPS cùng một đường (lát 12, 2026-09-08)

1. `git clone`, rồi `cp .env.example .env` và điền — **chỉ nguyên tố** (host · port · db · user · password), bảy URL được `backend/core/env.py` ráp lúc chạy. Kiểm tên biến, không in giá trị:

   ```bash
   cd backend && uv run python -m core.env check
   ```

2. **Một lệnh lên cả hệ** — kho (Postgres · Redis · ClickHouse), `migrate` one-shot (alembic head · `ch_migrate` · cấp 4 user login · tự seed ngành lớp 2), `api`, `etl` (vỏ job, heartbeat tới lát 13), `ingester` (daemon, tự ngủ ngoài phiên):

   ```bash
   docker compose up -d --build
   ```

   VPS: `.env` đặt thêm `COMPOSE_FILE=docker-compose.yml:docker-compose.vps.yml` (trần RAM đã đo — [service-topology §7b](docs/20-design/service-topology.md)) rồi **cùng lệnh trên**, không cài gì khác.

3. **Kho mới — hai lệnh sau `up`:** nạp danh bạ rồi chạy lại `migrate` để nó tự seed 161 dòng ngành lớp 2 (migration `0013` cần `market.security` có dòng; `migrate` phát hiện và làm hộ bước tay cũ):

   ```bash
   docker compose run --rm etl python -m etl refdata
   docker compose run --rm migrate
   ```

4. Job bất kỳ: `docker compose run --rm etl python -m etl <job> [cờ]` — cờ từng họ ở [`backend/README.md`](backend/README.md). REPL: `docker compose run --rm agent`. Backup ClickHouse: `docker compose run --rm etl python -m core.ch_backup`.

5. Dev native **không đổi cách gọi**, cùng `.env`: `cd backend && uv run pytest tests -q` (số test ở [`database/README.md`](database/README.md)), `uv run python -m etl <job>`.

🔴 **Dữ liệu KHÔNG đi theo repo.** Hai kho và Redis nằm trong volume `dlck_*` của máy; log/bản đo/spill của ingester ở ba volume `dlck_ingester_*`. Máy mới bắt đầu với kho rỗng — dựng lại được bằng chuỗi trên, **trừ ba thứ không backfill được: tick realtime, phiên OMO, frame thô.** `docker compose down` giữ volume; chỉ `down -v` mới xoá.

⚠️ Docker Desktop trên máy dev vẫn sống trong session người dùng và không tự khởi động sau reboot ([service-topology §5](docs/20-design/service-topology.md)): sau reboot mở Docker Desktop là cả stack tự lên nhờ `restart: unless-stopped`; `migrate` chạy lại (idempotent).
```

(c) bảng trạng thái đầu file: dòng **ETL theo lịch** đổi thành *"15 họ job chạy được trong container (lát 12, 2026-09-08); lịch chung thuộc lát 13; 11 task Windows đã gỡ"*; câu "**tiếp theo lát 12**" thành "**lát 12 xong 2026-09-0x, tiếp theo lát 13 — scheduler**"; xoá cụm "11 task Windows Scheduler đã đăng ký, 10 đang tắt".

- [ ] **Step 2: `backend/README.md`** — (a) mục "Chạy `ingester`": câu "Cần: Redis + ClickHouse đang chạng (`docker compose -f deploy/infra/...`)" thành "Cần: stack `docker compose up -d` ở gốc repo (kho + migrate), `.env` nguyên tố (bootstrap đã cấp `ingester_worker`)"; thêm dòng lệnh `uv run python -m ingester` chú thích **"daemon: ngoài 08:30–15:05 giờ VN thì ngủ, trong phiên ghi thật; `--minutes N` = chạy N phút rồi thoát"**; (b) **xoá trọn mục "Lịch chạy (Windows Task Scheduler)"** (dòng 398–hết) và thay bằng:

```markdown
## Chạy trong container (lát 12 — 2026-09-08)

Cùng image, cùng code: `docker compose run --rm etl python -m etl <job> [cờ]` (mọi cờ ở các mục trên). `ingester` là service daemon riêng (`docker compose up -d ingester`), lưới đo `docker compose --profile measure up -d ingester-measure`. `docker stop`/`compose down` gửi `SIGTERM`, job và ingester đi cùng đường Ctrl+C (`core/shutdown.py`): sổ `ops.etl_run` đóng `failed: dừng tay (Ctrl+C)`, exit 130; `stop_grace_period` 60 s (`etl`) / 90 s (`ingester`). Lịch chạy tự động thuộc **lát 13**; Task Scheduler và `scripts/register-tasks.ps1` đã về hưu.
```

(c) grep trong file: `DLCK_LOCK_CONSOLE`, `nút X`, `cửa sổ cmd`, `register-tasks` — xoá/viết lại mọi câu còn lại.

- [ ] **Step 3: `database/README.md`** — (a) mục "Cách chạy": bỏ khối `set -a … export DATA_DATABASE_URL=…` (alembic tự ráp từ `.env`); lệnh migrate giữ nguyên; thêm *"Trong container: `docker compose run --rm migrate` chạy alembic head + `ch_migrate` + cấp user + seed lớp 2 — `backend/core/bootstrap.py`"*; xoá đoạn **"Ngoài bộ Python còn một bộ nhỏ bằng Node"**; cập nhật **số hiện hành** từ AC8 (Step 8 dưới) kèm ngày; (b) mục "Luật": đoạn *"User login thật tạo per-môi-trường, ngoài migration"* thành *"User login do `core.bootstrap` tạo/đồng bộ từ `.env` (`ETL_DB_*`, `AGENT_DB_*`, `CLICKHOUSE_INGESTER_*`, `CLICKHOUSE_API_*`) mỗi lần `docker compose up`; không còn tạo tay"*; (c) "Bootstrap DB mới": bốn bước thành *"`docker compose up -d` → `run --rm etl python -m etl refdata` → `run --rm migrate` (tự chạy lại riêng `0013`) → kiểm 161"*, giữ nguyên đoạn giải thích vì sao `0013` cần bước này, và **thay** câu hướng dẫn `alembic downgrade 0012` → `upgrade head` bằng cảnh báo 🔴: *"KHÔNG dùng `downgrade 0012` nữa — đúng khi head là `0013`, nay head `0020` nên lệnh đó lùi tám migration và DROP `news.article_industry`, `ops.llm_call`, `ops.snapshot_check`… kèm dữ liệu (phát hiện 2026-09-08 khi viết plan lát 12). Cách đúng là `core.bootstrap` chạy riêng revision `0013` qua `Operations.context`."* Đoạn cảnh báo `alembic downgrade <revision>` phía trên giữ nguyên. Cùng bẫy này ở `README.md` gốc mục "Dựng trên máy mới" bước 3 (Step 1 đã thay trọn mục).

- [ ] **Step 4: `docs/20-design/service-topology.md`** — §5 mục 5: thêm đoạn đầu *"✅ **Lát 12 (2026-09-08): Task Scheduler về hưu.** 11 task đã gỡ, `register-tasks.ps1` và `core/console.py` xoá; mọi tiến trình chạy bằng `docker compose` ở gốc repo, ingester là daemon tự ngủ ngoài phiên, `SIGTERM` đi cùng đường Ctrl+C. Phần dưới giữ làm lịch sử."*; giữ nguyên hai đoạn 🔴 về Docker Desktop/reboot/ngủ (vẫn đúng). §6: thêm bảng *"Trong container: `/app/backend` (WORKDIR) · `/app/database` · `/var/lib/dlck/{logs,measure,spill}` (3 volume) · `/backups` (bind `CLICKHOUSE_BACKUP_DIR`)"* và dòng *"Compose: `docker-compose.yml` gốc + `docker-compose.vps.yml` qua `COMPOSE_FILE`"*. §7b: đoạn "Đĩa — vùng spill": đổi *"mặc định `dlck-runtime/spill`"* thành *"volume `dlck_ingester_spill` (native: `dlck-runtime/spill`)"*; câu lệnh chạy hồ sơ VPS thành `.env: COMPOSE_FILE=docker-compose.yml:docker-compose.vps.yml` + `docker compose up -d --build`; đường dẫn overlay thành `docker-compose.vps.yml` gốc.

- [ ] **Step 5: `docs/00-overview/roadmap.md`** — (a) §0 dòng "Code sản phẩm": nối *"**Lát 12 chạy được trong container ✅ XONG 2026-09-0x** — `.env` nguyên tố + hàm ráp, một compose gốc, `core.bootstrap`, ingester daemon, 15/15 họ job chạy thật trong container (kèm link "hồ sơ" tương đối từ roadmap: `../90-records/plans/2026-09-08-container-runtime/`). **TIẾP: lát 13 — scheduler.**"*; (b) dòng `lát 12` trong cây §3: `🔜 TIẾP THEO` → `✅ XONG 2026-09-0x`, một dòng tóm tắt, `TIẾP: lát 13`; (c) mục [4d] §2: thêm *"11 task đã gỡ 2026-09-0x (lát 12) — bật lại nay = `docker compose up -d` cả hệ, không còn Task Scheduler"*; (d) mục "Điểm vào cho lát 12": tiêu đề gạch `~~…~~ — ĐÃ DÙNG XONG 2026-09-0x, giữ làm ngữ cảnh`; (e) viết mục mới ngay dưới:

```markdown
### Điểm vào cho lát 13 — scheduler trong container `etl`, đọc trước khi bắt đầu

*(viết 2026-09-0x sau khi đóng lát 12)*

**Nền đã có (lát 12):** một `docker-compose.yml` gốc; service `etl` là vỏ job (`command: python -m etl` = heartbeat) — lát này **chỉ thay `command`** bằng scheduler; mọi họ job chạy được trong container bằng `python -m etl <job>`; mã thoát 0/1/2 có test hợp đồng (`test_e63`); `SIGTERM` → Ctrl+C → exit 130 (`core/shutdown.py`); `migrate` one-shot chạy lại mỗi `up`; ingester **tự lo cửa sổ phiên**, không đi qua bảng lịch.

**Việc:** bảng lịch trong code (giờ VN) + chạy bù mốc đã qua trong ngày mà `ops.etl_run` chưa có `success` + chặn chạy chồng + thứ tự phụ thuộc: `fundamentals` sau `events` 18:10 và sau `snapshot`; `snapshot` **không** trước ~15:20 (số đo lát 4/11); `classify` chạy độc lập kiểu quét sàn với trần mỗi đêm (số đo token/thời gian ở điểm vào lát 12 §4); 9 họ chưa từng có lịch: `snapshot` `fundamentals` `wichart` `fred` `fx` `lbma` `yahoo` `binance` (+`--intraday` theo spec lát 7b §5.7) `news --loop` `classify`. Spawn `python -m etl <job>` làm tiến trình con, log tách riêng.

**Nghiệm thu:** cả hệ chạy thử vài ngày trên dev (kho dev đã dựng lại từ đầu ở lát 12); bật lại ingester theo [4d] sau lát 14.

**Trạng thái bàn giao:** `main` = lát 12 · số test do `database/README.md` sở hữu · migration head `0020` · kho `dlck` mới: refdata + 161 override + mỗi họ một lượt hẹp · 11 task Windows đã gỡ, 6 volume cũ đã xoá.
```

(f) đoạn "Lát 13 — scheduler trong `etl`" (§3, sau bảng ánh xạ): câu *"Xong lát này thì `scripts/register-tasks.ps1` về hưu"* thành *"(`register-tasks.ps1` đã về hưu ở lát 12)"*; câu "thay 11 task Windows" giữ (lịch sử), thêm "(đã gỡ 2026-09-0x)".

- [ ] **Step 6: `CLAUDE.md`** — §3.5 dòng *"Cả ba phép kiểm nay đã mã hoá thành code — `Assert-TaskCommand` … trong `scripts/register-tasks.ps1`, …"* thành *"Cả ba phép kiểm nay đã mã hoá thành code — `Assert-TaskCommand` từng nằm trong `scripts/register-tasks.ps1` (script về hưu ở lát 12, 2026-09-08 — bài học giữ), test `test_flow_rebuild_works_under_etl_role`, và `test_assert_migrated_works_under_ingester_role`."*; §5 bảng Môi trường thêm dòng `| Chạy production | Docker: \`docker compose up -d --build\` ở gốc repo (lát 12); native \`uv run …\` chỉ cho dev/test, cùng một \`.env\` nguyên tố |`.

- [ ] **Step 7: `docs/90-records/README.md`** — cột kết quả dòng `2026-09-08-container-runtime/`: `✅ XONG 2026-09-0x — 15/15 họ job chạy trong container, AC1–AC9 đạt (ledger); thêm \`plan.md\` · \`ledger.md\` vào danh sách file`.

- [ ] **Step 7b: Link chết tới file đã xoá** (đo 2026-09-08 bằng `git grep` trước khi xoá) — tài liệu **sống**: đổi link thành mã inline kèm "(đã xoá lát 12)" hoặc trỏ file thay thế; tài liệu **lịch sử** (`90-records/`): **chỉ đổi href**, giữ nguyên nhãn:

| File:dòng | Trỏ tới | Xử lý |
|---|---|---|
| `backend/README.md:404`, `:406` | `scripts/register-tasks.ps1`, `core/console.py` | cả mục bị xoá ở Step 2b |
| `database/README.md:61` | `create_users.sql.example` | câu thành *"user login do `core.bootstrap` cấp"* |
| `docs/00-overview/roadmap.md:574` `:578` `:579` `:592` `:593` `:603` | `backend/.dockerignore` · `core/console.py` · `scripts/stack.mjs` · `deploy/app/docker-compose.yml` · `deploy/infra/docker-compose.vps.yml` | nằm trong "Điểm vào cho lát 12" (gạch ngang ở Step 5d): giữ nhãn, href → `.dockerignore` gốc / bỏ link (file xoá) / `docker-compose.yml` / `docker-compose.vps.yml` |
| `docs/20-design/service-topology.md:106`, `:189` | `core/console.py` · `deploy/infra/docker-compose.vps.yml` | §5 đoạn lịch sử: bỏ link, giữ chữ; §7b: href → `docker-compose.vps.yml` |
| `docs/90-records/plans/2026-08-28-ingester-spill-to-disk/brief.md:149` | `deploy/infra/docker-compose.vps.yml` | **chỉ href** → `../../../../docker-compose.vps.yml` |
| `docs/90-records/plans/2026-08-26-ingester-omo-first-slice/spec.md:212` | `create_users.sql.example` (nếu là link) | **chỉ href** → `../../../../backend/core/bootstrap.py` |

- [ ] **Step 8: Phép kiểm §1.7 — grep quét mọi chỗ, rồi CẢ BỘ test (AC8)**

Run: `git grep -n "register-tasks\|stack.mjs\|npm run\|COMPOSE_PROFILES\|DLCK_LOCK_CONSOLE\|deploy/infra/docker-compose\|deploy/app/\|ETL_DATABASE_URL=\|create_users.sql\|downgrade 0012" -- . ':!docs/90-records' ':!docs/00-overview/decisions'`
Expected: **0 hit** ngoài hai vùng lịch sử (riêng `downgrade 0012`: câu còn lại phải là lời cảnh báo "đừng làm", không phải hướng dẫn). Còn hit ⇒ sửa tiếp (trừ chữ trong khối ``` được trích làm lịch sử có ghi ngày).

Run: `cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests -q 2>&1 | tail -1`
Expected: `… passed, 2 skipped` — **AC8**; ghi số này + ngày vào `database/README.md` (chủ sở hữu duy nhất) trong cùng commit, và vào ledger. `tests/docs` phải xanh trở lại (link chết đã sửa ở 7b).

- [ ] **Step 9: Commit**

```bash
git add README.md backend/README.md database/README.md docs/20-design/service-topology.md docs/00-overview/roadmap.md CLAUDE.md docs/90-records/README.md
git commit -m "docs: the living docs describe the container runtime; roadmap closes slice 12 and opens slice 13"
```

---

### Task 12: Review toàn nhánh · gỡ 11 task · xoá 6 volume cũ · build sạch từ clone · khép

**Files:** ledger; (sửa theo review nếu có).

- [ ] **Step 1: Review độc lập hai trục** (skill `requesting-code-review`, subagent **`sonnet`**, hai lượt riêng — trục *Chuẩn* (đúng repo, code smell) và trục *Spec* (thiếu/sai/scope-creep so với `spec.md`)). Đưa kết quả vào ledger; sửa mục nặng (Critical/Important) rồi chạy lại `pytest tests -q`; Minor ghi "hoãn có lý do".

- [ ] **Step 2 — CHỦ DỰ ÁN: gỡ 11 task Windows** (AC9 phần 1):

```powershell
Get-ScheduledTask -TaskName 'dlck-*' | Unregister-ScheduledTask -Confirm:$false
Get-ScheduledTask -TaskName 'dlck-*' -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
```

Expected: `0`. Dán vào ledger.

- [ ] **Step 3: Xoá sáu volume cũ** (AC9 phần 2 — spec §5.9, chủ dự án uỷ quyền 2026-09-08; **không** đụng `tutor-infra_pgdata`):

```bash
docker volume rm infra_pgdata infra_chdata infra_redisdata dlck-infra_pgdata dlck-infra_chdata dlck-infra_redisdata
docker volume ls --format '{{.Name}}' | grep -E 'infra|dlck' | sort
```

Expected: còn đúng 6 volume `dlck_*` + `tutor-infra_pgdata`. Dán vào ledger.

- [ ] **Step 4: AC1 — build sạch từ clone mới** (Git Bash; `$TMP` = thư mục scratchpad của phiên, không phải trong repo)

```bash
CLONE="$TMP/dlck-clone"; rm -rf "$CLONE"
git clone --quiet . "$CLONE" && cp .env "$CLONE/.env"
docker compose -p dlck-clonecheck -f "$CLONE/docker-compose.yml" config --quiet && echo "config: OK"
docker compose -p dlck-clonecheck -f "$CLONE/docker-compose.yml" build migrate 2>&1 | tail -2 && echo "clone build: OK"
docker run --rm dlck-backend sh -c 'test ! -e /app/.env && test ! -e /app/backend/tests && test ! -e /app/docs && test -f /app/database/alembic.ini && test -f /app/backend/etl/data/feeds.json && echo "image: OK"'
rm -rf "$CLONE"
```

Expected: `config: OK` · `clone build: OK` · `image: OK`. (`-f` với đường dẫn tuyệt đối đặt project dir = thư mục clone nên nó đọc `.env` ở đó; **không** commit `.env`.)

- [ ] **Step 5: Lượt cuối cả bộ + ledger đóng**

```bash
cd backend && PYTHONIOENCODING=utf-8 uv run pytest tests -q 2>&1 | tail -1
git grep -n "\[DEBUG-" -- backend | wc -l
```

Expected: xanh; `0`. Ledger: mục "Đóng lát" với bảng AC1–AC9 → đạt/không, và mọi nợ để lại kèm lý do. `docs/90-records/README.md` và roadmap ghi ngày thật thay `2026-09-0x`.

- [ ] **Step 6: Commit, rồi khép nhánh** (skill `finishing-a-development-branch`: merge `--no-ff` vào `main`, chạy lại cả bộ trên `main`, push, xoá nhánh — theo khuôn ledger lát audit).

```bash
git add -A docs && git commit -m "docs(ledger): close slice 12 — AC1 to AC9, old tasks and volumes gone"
```

---

## Tự rà plan (đã chạy trước khi giao)

- **Đính chính spec khi viết plan (ghi ở cuối `spec.md`):** §5.4 bước 4 nói "chạy đúng nhịp `downgrade 0012` → `upgrade head`" — với head `0020` lệnh đó lùi tám migration và xoá dữ liệu; plan T8 chạy lại **riêng** revision `0013` qua `Operations.context`. Kết quả nghiệm thu (161 dòng) không đổi.
- **Phủ spec:** §5.1 → T1–T3 · §5.2/5.3 → T7 · §5.4 → T8 (+T9 chạy thật) · §5.5 → T5 (SIGTERM), T6 (daemon), T7 (volume, grace) · §5.6 → T4 · §5.7 → T5 · §5.8/§5.9 → T9, T11, T12 · §6 mọi seam có test ở T1–T8 (seam "ba chỗ sửa §5.6" đo qua `today_vn` + phép kiểm tĩnh; seam "tín hiệu dừng" = `test_shutdown` + AC-SIGTERM T10) · §7 AC1 T12 · AC2/AC4/AC7 T9 · AC3/AC5/AC6/AC8 T10 · AC9 T12 · §8 T11.
- **Giả định spec 2.2:** 2.2.1 → T9 Step 4 · 2.2.2 → T9 Step 6 · 2.2.3 → T8 test CH · 2.2.4 → T3 Step 6.
- **Placeholder:** không có TBD/TODO; mã/khoá cụ thể ở AC3 là tham số thật (`FPT,VNM` · `vang` · `DGS10` · `^GSPC` · `cafef`). Chỗ duy nhất để ngỏ có chủ đích: `2026-09-0x` = ngày đóng lát, điền lúc T11/T12.
- **Nhất quán tên:** `install_signal_handlers` (T5, gọi ở T5) · `next_window`/`daemon`/`SESSION_START` (T6) · `resolve_backup_dir` (T3) · `today_vn` (T4) · `compose_urls`/`check`/`KNOWN_KEYS`/`REQUIRED_KEYS`/`ASSEMBLED_KEYS`/`parse_dotenv` (T1 → T2) · `provision_postgres`/`provision_clickhouse`/`reseed_industry_if_needed`/`alembic_config` (T8) · biến `.env` khớp spec §5.1 và `OVERRIDES` của T7 khớp spec §5.2.
