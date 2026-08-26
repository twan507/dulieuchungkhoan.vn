# Mượn fixture Postgres thật của bộ test schema (cần TEST_DATABASE_URL như README database)
from tests.schema.conftest import db, migrated_engine  # noqa: F401
