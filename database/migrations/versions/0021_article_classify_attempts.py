"""Đếm số lần lưới phân loại thất bại trên một bài (lát 13 §5.4, chủ dự án 2026-09-09).

Trước: bài lỗi giữ `classified_from NULL` nên được chọn lại mãi, và không phân biệt được với bài chưa thử —
lỗi chỉ nằm ở `ops.llm_call`. Nay job tăng `classify_attempts` mỗi lần model trả lỗi và bỏ qua bài đã thử
đủ `MAX_ATTEMPTS = 3` (hằng trong `etl/news_classify.py`, không CHECK ở DB để đổi ngưỡng không cần migration).

Revision ID: 0021
Revises: 0020
Create Date: 2026-09-09
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE news.article ADD COLUMN classify_attempts smallint NOT NULL DEFAULT 0;")


def downgrade() -> None:
    op.execute("ALTER TABLE news.article DROP COLUMN classify_attempts;")
