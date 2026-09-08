"""Fixture Postgres thật dùng chung cho `tests/schema` và `tests/etl` (cần `TEST_DATABASE_URL`, xem database/README).

Một file conftest gốc để cả bộ chỉ có MỘT fixture `migrated_engine` session-scope. Trước 2026-09-05 nó nằm ở
`tests/schema/conftest.py` và `tests/etl/conftest.py` import lại — pytest coi đó là HAI fixturedef, nên full suite
dựng + migrate database test hai lần, và lần dựng lại thứ hai từng che một va chạm dữ liệu giữa test job (registry
`asset.code='wti'` để lại) và test schema (review lát 6, I6). Nay va chạm như thế phải lộ ra ngay.

Đọc biến môi trường LÚC fixture chạy, không lúc import: `tests/clickhouse`/`tests/ingester` không cần Postgres.
"""
import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

from core.env import load_dotenv

# 🔴 Nạp `.env` NGAY TẠI ĐÂY, không đợi module khác nạp hộ (rà chuẩn hoá 2026-09-08).
# Trước đó không gì trong `tests/` nạp cả: cả bộ xanh chỉ vì `tests/agent/test_a14_startup.py`
# `import agent.__main__`, và file đó gọi `load_dotenv()` lúc import — `tests/agent` đứng đầu
# bảng chữ cái nên mọi test sau ăn ké. Hậu quả: `pytest tests` xanh mà `pytest tests/etl` ném
# `KeyError: TEST_DATABASE_URL`. `load_dotenv` dùng `setdefault` nên biến đặt sẵn ở shell/CI
# vẫn thắng, và thiếu file `.env` thì nó im lặng bỏ qua. Hợp đồng ở `tests/test_conftest_env_contract.py`.
load_dotenv()

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture(scope="session")
def migrated_engine():
    test_url = os.environ["TEST_DATABASE_URL"]          # ...:5432/dulieu_test
    admin_url = test_url.rsplit("/", 1)[0] + "/dulieu"  # DB có sẵn để CREATE DATABASE
    admin = sa.create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(sa.text("DROP DATABASE IF EXISTS dulieu_test WITH (FORCE)"))
        c.execute(sa.text("CREATE DATABASE dulieu_test"))
    admin.dispose()
    cfg = Config(os.path.join(REPO_ROOT, "database", "alembic.ini"))
    os.environ["DATA_DATABASE_URL"] = test_url      # migrations/env.py đọc biến này
    os.chdir(REPO_ROOT)                             # script_location trong ini là đường dẫn tương đối gốc repo
    command.upgrade(cfg, "head")
    engine = sa.create_engine(test_url)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(migrated_engine):
    with migrated_engine.connect() as conn:
        tx = conn.begin()
        yield conn
        tx.rollback()                               # mỗi test một transaction — sạch tuyệt đối


def expect_violation(conn, sql, params=None):
    """Chạy trong SAVEPOINT; True nếu vi phạm ràng buộc (transaction ngoài còn sống)."""
    nested = conn.begin_nested()
    try:
        conn.execute(sa.text(sql), params or {})
        nested.commit()
        return False
    except IntegrityError:
        nested.rollback()
        return True


# --- ClickHouse ephemeral: MỘT container cho cả tests/clickhouse lẫn tests/ingester ---
# Đặt ở conftest GỐC (tổ tiên chung) chứ không ở conftest con: import lại vào conftest
# anh em tạo hai FixtureDef, đo được 2 container/lượt (rà 2026-09-07). Cùng bài học với
# `migrated_engine` của Postgres — test-strategy.md §6.
import os
import socket
import subprocess
import time
import uuid
from pathlib import Path

import clickhouse_connect

IMAGE = "clickhouse/clickhouse-server:26.3.22.7"
# KHÔNG tái định nghĩa REPO_ROOT (dòng 18 đã có, alembic dùng nó). Ở đây file nằm sâu
# hơn một cấp so với chỗ cũ `tests/clickhouse/` nên parents[3] sẽ trỏ RA NGOÀI repo:
# volume mount lặng lẽ rỗng, container mất backups.xml, 6 test backup đỏ (đã gặp thật).
CH_CONF_DIR = Path(REPO_ROOT) / "deploy" / "infra" / "clickhouse"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def ch_backup_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("ch-backups")


@pytest.fixture(scope="session")
def ch(ch_backup_dir):
    """Container ClickHouse ephemeral — không đụng CH dev. Xoá khi hết session."""
    name = f"ch-test-{uuid.uuid4().hex[:8]}"
    port = _free_port()
    cmd = [
        "docker", "run", "-d", "--name", name,
        "--ulimit", "nofile=262144:262144",
        "-e", "CLICKHOUSE_PASSWORD=testpass",
        "-e", "CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1",
        "-e", "TZ=Asia/Ho_Chi_Minh",
        "-v", f"{CH_CONF_DIR / 'backups.xml'}:/etc/clickhouse-server/config.d/backups.xml:ro",
        "-v", f"{ch_backup_dir}:/backups",
        "-p", f"127.0.0.1:{port}:8123",
        IMAGE,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    url = f"http://default:testpass@127.0.0.1:{port}"
    client = None
    try:
        for _ in range(60):
            try:
                client = clickhouse_connect.get_client(dsn=url)
                client.command("SELECT 1")
                break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("ClickHouse test container không lên sau 60s")
        os.environ["CLICKHOUSE_URL"] = url
        yield client
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)


@pytest.fixture()
def migrated(ch):
    """Đảm bảo đã upgrade (idempotent — chạy lại là no-op). Test dùng symbol riêng để cách ly."""
    from core import ch_migrate
    ch_migrate.upgrade(ch)
    return ch
