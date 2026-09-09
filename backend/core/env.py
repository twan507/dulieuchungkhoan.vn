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
# Giá trị giữ chỗ của .env.example (cả 6 mật khẩu) — copy nguyên rồi `up -d` không được phép báo xanh.
WEAK_VALUES = frozenset({"change-me", "changeme"})

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
    """In TÊN biến bắt buộc còn thiếu, giá trị còn giữ chỗ (YẾU, vd `change-me`) và biến lạ — không
    bao giờ in giá trị. Khoá khai nhưng RỖNG bị coi là thiếu, đồng bộ với `compose_urls` (vốn cũng
    coi rỗng = không có). Không có file `.env` ⇒ rơi về `os.environ` thay vì trả 2 — image trong
    container không mang `.env` (`.dockerignore`), compose bơm nguyên tố qua `env_file`; khi đó bỏ
    qua kiểm "biến lạ" vì tiến trình luôn có sẵn biến hệ điều hành khác không thuộc hợp đồng `.env`.
    0 = đủ · 1 = thiếu hoặc còn giữ chỗ."""
    p = path or (REPO_ROOT / ".env")
    if p.is_file():
        parsed = parse_dotenv(p.read_text(encoding="utf-8"))
        print(f"nguồn: {p}", file=out)
        unknown = sorted(set(parsed) - KNOWN_KEYS)
        checked_unknown = True
    else:
        parsed = dict(os.environ)
        print(f"nguồn: môi trường (không có {p})", file=out)
        unknown = []
        checked_unknown = False
    present = {k for k, v in parsed.items() if v}
    missing = sorted(REQUIRED_KEYS - present)
    weak = sorted(k for k in (REQUIRED_KEYS & present) if parsed[k] in WEAK_VALUES)
    for k in missing:
        print(f"THIẾU  {k}", file=out)
    for k in weak:
        print(f"YẾU    {k}", file=out)
    for k in unknown:
        print(f"LẠ     {k}", file=out)
    if not missing and not weak and not unknown:
        tail = ", không biến lạ" if checked_unknown else " (không kiểm biến lạ trên môi trường)"
        print(f"đủ {len(REQUIRED_KEYS)} biến bắt buộc{tail}", file=out)
    return 1 if (missing or weak) else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd != "check":
        sys.exit(f"lệnh không biết: {cmd} (hỗ trợ: check)")
    raise SystemExit(check())
