"""Chỉ mục trigram cho tiêu đề bài — gộp tin "cùng chuyện, khác tít" (lát 9b-2, phương án A).

Đo 2026-09-06 trên 7.444 bài/30 ngày: khoá tiêu đề Y HỆT chỉ bắt ≈ 0,5 % bài; `pg_trgm` ngưỡng 0,6 bắt
**2,0 %** (176 cặp khác báo trong 48 giờ), 0,45 bắt 5,9 % — gấp 4–12 lần, kể cả cặp diễn đạt khác hẳn
("MSB chốt quyền chia cổ phiếu thưởng" ↔ "Một ngân hàng chốt quyền phát hành cổ phiếu thưởng", 0,52).
Vì thế embedding cho việc DEDUPE là thừa ở giai đoạn này (hồ sơ: 90-records/plans/2026-09-06-news-classify-llm/embedding-decision.md).

Chỉ mục trên BIỂU THỨC `immutable_unaccent(lower(title))` — đúng biểu thức mà `news_store.find_near_duplicate`
so sánh; index trên cột thô sẽ không được dùng (bài học `trade_name`, migration 0007). Opclass qualify
`extensions.gin_trgm_ops` theo luật extension-schema.

Revision ID: 0020
Revises: 0019
Create Date: 2026-09-06
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX article_revision_title_trgm
          ON news.article_revision
          USING gin (news.immutable_unaccent(lower(title)) extensions.gin_trgm_ops);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX news.article_revision_title_trgm;")
