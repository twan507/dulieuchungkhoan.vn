"""Migration runner cho ClickHouse — spec docs/90-records/plans/2026-08-25-clickhouse-realtime-store/spec.md §8.

Không có downgrade. Mọi statement trong versions/ phải idempotent
(DDL không transaction — file chết giữa chừng thì lần chạy lại phải đi qua được).
"""
import os
import re
import sys
from pathlib import Path

import clickhouse_connect

REQUIRED_CH_MIGRATION = "0002_rt_schema"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VERSIONS_DIR = REPO_ROOT / "database" / "clickhouse" / "versions"
_VERSION_RE = re.compile(r"^\d{4}_[a-z0-9_]+$")

_BOOTSTRAP = [
    "CREATE DATABASE IF NOT EXISTS rt",
    "CREATE TABLE IF NOT EXISTS rt.schema_migrations ("
    " version String,"
    " applied_at DateTime('Asia/Ho_Chi_Minh')"
    ") ENGINE = ReplacingMergeTree ORDER BY version",
]


def get_client(url: str | None = None):
    return clickhouse_connect.get_client(dsn=url or os.environ["CLICKHOUSE_URL"])


def split_statements(sql: str) -> list[str]:
    """Tách theo ';'. Quy ước migration: không có ';' trong string literal hay comment."""
    out = []
    for chunk in sql.split(";"):
        lines = [ln for ln in chunk.splitlines() if ln.strip() and not ln.strip().startswith("--")]
        if lines:
            out.append(chunk.strip())
    return out


def _bootstrap(client) -> None:
    for stmt in _BOOTSTRAP:
        client.command(stmt)


def applied_versions(client) -> set[str]:
    """CHỈ ĐỌC — không dựng gì. `assert_migrated` đi qua đây và chạy dưới role
    production `dlck_ingester` (chỉ SELECT/INSERT), nên mọi DDL ở đây là ACCESS_DENIED
    ngay lúc ingester khởi động: task Scheduler vẫn "Ready", vẫn chạy đúng giờ, và chết
    câm — mất trọn phiên. Dựng sổ migration là việc của `upgrade`, chạy bằng user owner.
    """
    exists = client.command(
        "SELECT count() FROM system.tables WHERE database = 'rt' AND name = 'schema_migrations'")
    if not int(exists):
        return set()                 # chưa có sổ = chưa áp dụng gì
    rows = client.query("SELECT DISTINCT version FROM rt.schema_migrations").result_rows
    return {r[0] for r in rows}


def upgrade(client=None, versions_dir: Path | None = None) -> list[str]:
    client = client or get_client()
    versions_dir = versions_dir or DEFAULT_VERSIONS_DIR
    _bootstrap(client)               # đường GHI mới được dựng sổ
    done = applied_versions(client)
    ran: list[str] = []
    for path in sorted(versions_dir.glob("*.sql")):
        version = path.stem
        if not _VERSION_RE.fullmatch(version):
            raise ValueError(f"Tên file migration sai quy ước NNNN_ten_thuong: {path.name}")
        if version in done:
            continue
        for stmt in split_statements(path.read_text(encoding="utf-8")):
            client.command(stmt)
        client.command(
            f"INSERT INTO rt.schema_migrations (version, applied_at) VALUES ('{version}', now())"
        )
        ran.append(version)
    return ran


def assert_migrated(client, required: str = REQUIRED_CH_MIGRATION) -> None:
    """Hợp đồng khởi động (spec §8): ingester gọi hàm này TRƯỚC khi nối socket."""
    have = applied_versions(client)
    if required not in have:
        raise RuntimeError(
            f"ClickHouse chưa migrate tới {required} (đã có: {sorted(have) or 'rỗng'}). "
            "Chạy: uv run python -m core.ch_migrate upgrade"
        )


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    client = get_client()
    if cmd == "upgrade":
        ran = upgrade(client)
        print(f"đã chạy: {ran or 'không có gì mới'}")
    elif cmd == "status":
        print(f"đã áp dụng: {sorted(applied_versions(client))}")
    else:
        sys.exit(f"lệnh không biết: {cmd} (upgrade | status)")


if __name__ == "__main__":
    main()
