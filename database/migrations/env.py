import os

from alembic import context
from sqlalchemy import create_engine, pool


def run_migrations_online() -> None:
    # Test đặt DATA_DATABASE_URL trỏ DB test trước khi gọi alembic (conftest lo việc này)
    url = os.environ["DATA_DATABASE_URL"]
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
