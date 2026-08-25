"""writer/reader roles and schema grants

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='dlck_etl') THEN CREATE ROLE dlck_etl NOLOGIN; END IF;
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='dlck_api') THEN CREATE ROLE dlck_api NOLOGIN; END IF;
        END $$;
        GRANT USAGE ON SCHEMA market, macro, asset, news, staging, ops, extensions TO dlck_etl;
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA market, macro, asset, news, staging, ops TO dlck_etl;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA market, macro, asset, news, staging, ops TO dlck_etl;
        GRANT USAGE ON SCHEMA market, macro, asset, news, extensions TO dlck_api;
        GRANT SELECT ON ALL TABLES IN SCHEMA market, macro, asset, news TO dlck_api;
        ALTER DEFAULT PRIVILEGES IN SCHEMA market, macro, asset, news
          GRANT SELECT ON TABLES TO dlck_api;
        ALTER DEFAULT PRIVILEGES IN SCHEMA market, macro, asset, news, staging, ops
          GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO dlck_etl;
        -- fix round 1: thiếu default priv sequence — bảng mới có identity sẽ chặn etl ghi
        ALTER DEFAULT PRIVILEGES IN SCHEMA market, macro, asset, news, staging, ops
          GRANT USAGE, SELECT ON SEQUENCES TO dlck_etl;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER DEFAULT PRIVILEGES IN SCHEMA market, macro, asset, news, staging, ops
          REVOKE USAGE, SELECT ON SEQUENCES FROM dlck_etl;
        ALTER DEFAULT PRIVILEGES IN SCHEMA market, macro, asset, news, staging, ops
          REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM dlck_etl;
        ALTER DEFAULT PRIVILEGES IN SCHEMA market, macro, asset, news
          REVOKE SELECT ON TABLES FROM dlck_api;

        REVOKE SELECT ON ALL TABLES IN SCHEMA market, macro, asset, news FROM dlck_api;
        REVOKE USAGE ON SCHEMA market, macro, asset, news, extensions FROM dlck_api;

        REVOKE USAGE, SELECT ON ALL SEQUENCES IN SCHEMA market, macro, asset, news, staging, ops FROM dlck_etl;
        REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA market, macro, asset, news, staging, ops FROM dlck_etl;
        REVOKE USAGE ON SCHEMA market, macro, asset, news, staging, ops, extensions FROM dlck_etl;

        -- Role cluster-level (§ ghi chú task): nếu DB khác trong cùng cluster đã upgrade 0009 và còn
        -- giữ grant cho role này, DROP ROLE ở đây sẽ gặp lỗi dependent_objects_still_exist. Đã REVOKE
        -- sạch trong DB hiện tại ở trên; bọc DROP để không chặn downgrade của DB này vì grant ở DB khác.
        DO $$ BEGIN
          DROP ROLE IF EXISTS dlck_api;
        EXCEPTION WHEN dependent_objects_still_exist THEN
          RAISE NOTICE 'dlck_api con grant o DB khac trong cung cluster - giu role';
        END $$;
        DO $$ BEGIN
          DROP ROLE IF EXISTS dlck_etl;
        EXCEPTION WHEN dependent_objects_still_exist THEN
          RAISE NOTICE 'dlck_etl con grant o DB khac trong cung cluster - giu role';
        END $$;
        """
    )
