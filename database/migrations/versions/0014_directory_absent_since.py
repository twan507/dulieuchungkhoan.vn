"""directory_absent_since on market.security (market-data-store §4.4)

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-28

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- Dấu thời điểm LẦN ĐẦU thấy mã vắng khỏi danh bạ doanh nghiệp FiinTrade
        -- (mã còn trong bảng giá BVSC nhưng không có issuer). NULL = đang có mặt.
        -- Job đóng dấu một lần rồi thôi, gỡ dấu khi mã quay lại; chỉ mã mang dấu đủ
        -- ngưỡng mới bị lật 'delisted' (market-data-store §4.4). Nhờ đó mã MỚI niêm
        -- yết — vào bảng giá trước khi vào danh bạ — chỉ mang dấu tạm rồi được gỡ.
        ALTER TABLE market.security ADD COLUMN directory_absent_since timestamptz;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE market.security DROP COLUMN directory_absent_since;")
