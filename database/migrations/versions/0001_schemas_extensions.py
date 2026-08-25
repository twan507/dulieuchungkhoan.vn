"""schemas and extensions

Revision ID: 0001
Revises:
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE SCHEMA extensions;
        CREATE SCHEMA market;
        CREATE SCHEMA macro;
        CREATE SCHEMA asset;
        CREATE SCHEMA news;
        CREATE SCHEMA staging;
        CREATE SCHEMA ops;
        CREATE EXTENSION unaccent      SCHEMA extensions;
        CREATE EXTENSION pg_trgm       SCHEMA extensions;
        CREATE EXTENSION vector        SCHEMA extensions;
        CREATE EXTENSION fuzzystrmatch SCHEMA extensions;
        REVOKE CREATE ON SCHEMA public FROM PUBLIC;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP EXTENSION fuzzystrmatch;
        DROP EXTENSION vector;
        DROP EXTENSION pg_trgm;
        DROP EXTENSION unaccent;
        DROP SCHEMA ops CASCADE;
        DROP SCHEMA staging CASCADE;
        DROP SCHEMA news CASCADE;
        DROP SCHEMA asset CASCADE;
        DROP SCHEMA macro CASCADE;
        DROP SCHEMA market CASCADE;
        DROP SCHEMA extensions CASCADE;
        -- không GRANT lại CREATE trên public: PG16 mặc định đã khoá, GRANT làm DB lỏng hơn trạng thái gốc (final review #5).
        """
    )
