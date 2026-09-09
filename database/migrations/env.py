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
