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
