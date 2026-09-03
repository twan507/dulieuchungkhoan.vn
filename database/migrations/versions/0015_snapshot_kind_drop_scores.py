"""snapshot_daily: bỏ hai kind chấm điểm bên thứ ba

Quyết định chủ dự án 2026-09-03, sau khi soi nội dung thật của cả 6 endpoint họ
Snapshot (bằng chứng: docs/10-sources/market/04-fiin-company-profile.md và
06-fiin-scoring-valuation.md, số đo cùng ngày):

  company_score   → điểm CHỮ: growth='C' · momentum='B' · value='D' · vgm='B',
                    kèm icbRank/indexRank. Đúng bốn trường mà bảng chọn Screener
                    đã bỏ từ 2026-08-14.
  rate_indicator  → 33 dòng {rateIndicatorName, rateValue, scoreType}, và
                    rateValue chỉ nhận 0.00 / 1.00 / 3.00 — là CỜ chấm điểm,
                    không phải giá trị chỉ tiêu. "Chỉ số EV/EBITDA" mang giá trị
                    0.00, tức đạt/không đạt, không phải tỷ số EV/EBITDA.

Cả hai thuộc nhóm chấm điểm mà chủ dự án đã loại có chủ đích: "không dùng điểm
do bên thứ ba chấm". Bỏ khỏi CHECK để lược đồ không mời gọi nạp thứ đã quyết
không nạp — bảng đang RỖNG (kiểm 2026-09-03) nên không có dòng nào phải dọn.

`valuation` GIỮ LẠI: nó không phải điểm mà là SỐ dự phóng — estimatedEPS
4.913,56 · forecastEPS 1.709,80 · riskFreeRate 0,04337 (đo trên FPT), thứ
market-data-store xếp vào tầng C "Độc quyền FiinGroup — mất là mất".

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-03

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE market.snapshot_daily DROP CONSTRAINT snapshot_daily_kind_check;
        ALTER TABLE market.snapshot_daily ADD CONSTRAINT snapshot_daily_kind_check
          CHECK (kind IN ('snapshot','valuation','ownership','dividend'));
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE market.snapshot_daily DROP CONSTRAINT snapshot_daily_kind_check;
        ALTER TABLE market.snapshot_daily ADD CONSTRAINT snapshot_daily_kind_check
          CHECK (kind IN ('snapshot','company_score','valuation','rate_indicator','ownership','dividend'));
        """
    )
