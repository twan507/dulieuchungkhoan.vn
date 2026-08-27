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
        -- LỚP 2 — gán tay, người ghi. Bảng này là của NGƯỜI: ETL KHÔNG đọc, KHÔNG ghi
        -- (spec §2) — luật do DB gác, không do comment gác. ETL và API đọc ngành qua
        -- view market.v_issuer_industry; view chạy bằng quyền chủ view (security_invoker
        -- mặc định false) nên không cần quyền trên bảng nền để đọc qua view.
        CREATE TABLE market.issuer_industry_override (
          issuer_id   bigint PRIMARY KEY REFERENCES market.issuer,
          industry_id bigint NOT NULL REFERENCES market.industry,  -- luôn level 2
          note        text NOT NULL,                               -- vì sao đè — bắt buộc
          updated_at  timestamptz NOT NULL DEFAULT now(),
          CONSTRAINT note_not_blank CHECK (btrim(note) <> '')
        );

        -- Đường đọc NGÀNH ĐÃ PHÂN GIẢI của doanh nghiệp. Đọc thẳng issuer.industry_id
        -- là bỏ qua lớp tay; đọc thẳng issuer_industry_override là chỉ thấy lớp tay.
        -- DB ép được luật này với dlck_etl (bị REVOKE trên bảng nền); với dlck_api thì
        -- đây là KỶ LUẬT CODE, không phải ràng buộc DB — API vẫn giữ quyền đọc bảng nền
        -- để lấy cột `note` (lý do đè tay) mà view không phơi ra.
        CREATE VIEW market.v_issuer_industry AS
        SELECT i.issuer_id,
               COALESCE(o.industry_id, i.industry_id) AS industry_id,
               CASE WHEN o.industry_id IS NOT NULL THEN 'manual'
                    WHEN i.industry_id IS NOT NULL THEN 'icb'
               END AS source
        FROM market.issuer i
        LEFT JOIN market.issuer_industry_override o USING (issuer_id);

        -- 0009 cấp SELECT, INSERT, UPDATE, DELETE cho dlck_etl trên MỌI bảng market
        -- (kèm default privileges) — thu hồi cả đọc lẫn ghi để khớp spec §2.
        REVOKE SELECT, INSERT, UPDATE, DELETE ON market.issuer_industry_override FROM dlck_etl;
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
