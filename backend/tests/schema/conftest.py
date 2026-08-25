import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

TEST_URL = os.environ["TEST_DATABASE_URL"]          # ...:5432/dulieu_test
ADMIN_URL = TEST_URL.rsplit("/", 1)[0] + "/dulieu"  # DB có sẵn để CREATE DATABASE
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


@pytest.fixture(scope="session")
def migrated_engine():
    admin = sa.create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(sa.text("DROP DATABASE IF EXISTS dulieu_test WITH (FORCE)"))
        c.execute(sa.text("CREATE DATABASE dulieu_test"))
    admin.dispose()
    cfg = Config(os.path.join(REPO_ROOT, "database", "alembic.ini"))
    os.environ["DATA_DATABASE_URL"] = TEST_URL      # migrations/env.py đọc biến này
    os.chdir(REPO_ROOT)                             # script_location trong ini là đường dẫn tương đối gốc repo
    command.upgrade(cfg, "head")
    engine = sa.create_engine(TEST_URL)
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
