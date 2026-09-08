"""Giải đường dẫn thư mục backup — hàm THUẦN, không cần container (M13 + T3, review toàn nhánh lát 12).

Trước 2026-09-08 hai ca đầu nằm cuối `tests/clickhouse/test_t06_backup.py`: muốn chạy hai phép kiểm
thuần chuỗi phải dựng một container ClickHouse và chờ nó healthy.
"""
from pathlib import Path

from core.ch_backup import resolve_backup_dir
from core.env import REPO_ROOT


def test_relative_backup_dir_resolves_against_repo_root():
    """Compose ở GỐC repo giải đường dẫn tương đối theo gốc — code phải cùng gốc, không phải deploy/infra."""
    assert resolve_backup_dir("./deploy/infra/clickhouse-backups") == REPO_ROOT / "deploy" / "infra" / "clickhouse-backups"


def test_absolute_backup_dir_is_kept():
    p = Path("/backups") if Path("/backups").is_absolute() else Path("C:/backups")
    assert resolve_backup_dir(str(p)) == p


def test_an_empty_value_counts_as_not_set_and_falls_back_to_the_default(monkeypatch):
    """Ca biên T3. Compose viết `${CLICKHOUSE_BACKUP_DIR:-./deploy/infra/clickhouse-backups}`, và `:-`
    coi RỖNG như chưa đặt; nhưng `ch_backup.main()` đọc `os.environ[...]` nên một dòng
    `CLICKHOUSE_BACKUP_DIR=` bỏ trống trong `.env` vẫn tới đây dưới dạng chuỗi rỗng. Trước 2026-09-08
    rỗng giải ra chính GỐC REPO — backup đổ thẳng vào thư mục làm việc, cạnh `.env` và `docker-compose.yml`."""
    assert resolve_backup_dir("") == REPO_ROOT / "deploy" / "infra" / "clickhouse-backups"


def test_a_lone_dot_means_the_repo_root():
    """`.` KHÁC rỗng: nó là một đường dẫn tương đối hợp lệ, và gốc tương đối là gốc repo."""
    assert resolve_backup_dir(".") == REPO_ROOT
