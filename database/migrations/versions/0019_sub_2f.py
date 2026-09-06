"""Taxonomy tin: thêm sub `2f` "Doanh nghiệp và kinh tế các nước" (news-pipeline §3, chốt 2026-09-06 khi gán bộ gold —
ba annotator độc lập cùng vấp: tin doanh nghiệp nước ngoài / chính sách kinh tế nội bộ nước ngoài không sub nào của nhóm 2 nhận).
`3e` chỉ đổi tên/mở rộng nghĩa (thị trường tài sản trong nước), mã giữ nguyên nên không đụng DB.

Revision ID: 0019
Revises: 0018
Create Date: 2026-09-06
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SUBS_OLD = "'1a','1b','1c','1d','1e','1f','2a','2b','2c','2d','2e','3a','3b','3c','3d','3e','3f','3g','3h','3i'"
SUBS_NEW = SUBS_OLD.replace("'2e',", "'2e','2f',")


def upgrade() -> None:
    op.execute(f"ALTER TABLE news.article DROP CONSTRAINT article_sub_check, ADD CONSTRAINT article_sub_check CHECK (sub IN ({SUBS_NEW}));")


def downgrade() -> None:
    # Vỡ nếu đã có dòng sub='2f' — đúng ý: không lặng lẽ mất nhãn. Xoá/đổi nhãn 2f trước khi downgrade.
    op.execute(f"ALTER TABLE news.article DROP CONSTRAINT article_sub_check, ADD CONSTRAINT article_sub_check CHECK (sub IN ({SUBS_OLD}));")
