"""issuer_industry_override + v_issuer_industry (spec §2)

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-27

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- LỚP 2 — gán tay, người ghi, ETL KHÔNG đọc KHÔNG ghi (spec §2).
        CREATE TABLE market.issuer_industry_override (
          issuer_id   bigint PRIMARY KEY REFERENCES market.issuer,
          industry_id bigint NOT NULL REFERENCES market.industry,  -- luôn level 2
          note        text NOT NULL,                               -- vì sao đè — bắt buộc
          updated_at  timestamptz NOT NULL DEFAULT now(),
          CONSTRAINT note_not_blank CHECK (btrim(note) <> '')
        );

        -- ĐƯỜNG ĐỌC DUY NHẤT của ngành doanh nghiệp. Đọc thẳng issuer.industry_id là
        -- bỏ qua lớp tay — mọi truy vấn hiển thị/phân tích phải qua view này.
        CREATE VIEW market.v_issuer_industry AS
        SELECT i.issuer_id,
               COALESCE(o.industry_id, i.industry_id) AS industry_id,
               CASE WHEN o.industry_id IS NOT NULL THEN 'manual'
                    WHEN i.industry_id IS NOT NULL THEN 'icb'
               END AS source
        FROM market.issuer i
        LEFT JOIN market.issuer_industry_override o USING (issuer_id);

        -- 0009 cấp quyền ghi cho dlck_etl trên MỌI bảng market (kèm default privileges).
        -- Bảng này là của NGƯỜI: thu hồi để luật "ETL không ghi" do DB gác, không do comment gác.
        REVOKE INSERT, UPDATE, DELETE ON market.issuer_industry_override FROM dlck_etl;
        GRANT SELECT ON market.v_issuer_industry TO dlck_etl, dlck_api;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP VIEW IF EXISTS market.v_issuer_industry;
        DROP TABLE IF EXISTS market.issuer_industry_override;
        """
    )
