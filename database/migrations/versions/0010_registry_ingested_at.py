"""registry tables gain ingested_at

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-25

Quy ước step-01 §3 (review vòng 3, M-2): registry do ETL nạp cũng phải mang
`ingested_at` — các bước 2/4/5/6 lược cột này khi viết DDL nháp cho gọn, migration
này bổ sung đồng loạt.

MIỄN TRỪ có chủ đích (không thêm ingested_at):
- market.industry, market.industry_icb_map, news.trade_name — registry duyệt tay
  (luật miễn trừ step-01 §3, cùng nhóm với macro.series_break đã dùng verified_at)
- macro.omo_flow — bảng rebuild toàn phần từ macro.omo_auction, không phải bảng nạp trực tiếp
- ops.data_domain_state — đã có last_success_at, không cần thêm ingested_at
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE market.icb_industry        ADD COLUMN ingested_at timestamptz NOT NULL DEFAULT now();
        ALTER TABLE market.issuer_external_id   ADD COLUMN ingested_at timestamptz NOT NULL DEFAULT now();
        ALTER TABLE market.security_external_id ADD COLUMN ingested_at timestamptz NOT NULL DEFAULT now();
        ALTER TABLE market.metric_dictionary    ADD COLUMN ingested_at timestamptz NOT NULL DEFAULT now();
        ALTER TABLE market.metric_mapping       ADD COLUMN ingested_at timestamptz NOT NULL DEFAULT now();
        ALTER TABLE macro.indicator             ADD COLUMN ingested_at timestamptz NOT NULL DEFAULT now();
        ALTER TABLE macro.indicator_source      ADD COLUMN ingested_at timestamptz NOT NULL DEFAULT now();
        ALTER TABLE asset.asset                 ADD COLUMN ingested_at timestamptz NOT NULL DEFAULT now();
        ALTER TABLE asset.asset_external_id     ADD COLUMN ingested_at timestamptz NOT NULL DEFAULT now();
        ALTER TABLE news.article_source         ADD COLUMN ingested_at timestamptz NOT NULL DEFAULT now();
        ALTER TABLE news.article_ticker         ADD COLUMN ingested_at timestamptz NOT NULL DEFAULT now();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE news.article_ticker         DROP COLUMN ingested_at;
        ALTER TABLE news.article_source         DROP COLUMN ingested_at;
        ALTER TABLE asset.asset_external_id     DROP COLUMN ingested_at;
        ALTER TABLE asset.asset                 DROP COLUMN ingested_at;
        ALTER TABLE macro.indicator_source      DROP COLUMN ingested_at;
        ALTER TABLE macro.indicator             DROP COLUMN ingested_at;
        ALTER TABLE market.metric_mapping       DROP COLUMN ingested_at;
        ALTER TABLE market.metric_dictionary    DROP COLUMN ingested_at;
        ALTER TABLE market.security_external_id DROP COLUMN ingested_at;
        ALTER TABLE market.issuer_external_id   DROP COLUMN ingested_at;
        ALTER TABLE market.icb_industry         DROP COLUMN ingested_at;
        """
    )
