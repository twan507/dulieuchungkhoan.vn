"""rename industry codes and names (industry-tree.md §2, rà 2026-08-27)

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-27

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (code cũ, code mới, tên mới) — nội dung do docs/20-design/industry-tree.md §2 sở hữu.
RENAMES = [
    ("BDS", "DANDUNG", "Bất động sản Dân dụng"),
    ("KCN", "KHUCONGNGHIEP", "Bất động sản Khu công nghiệp"),
    ("VLXD", "VATLIEU", "Vật liệu Xây dựng"),
    ("TAINGUYEN", "KHOANGSAN", "Than và Khoáng sản"),
    ("YTEGD", "YTE", "Y tế, Giáo dục và Xuất bản"),
    ("DIENNUOC", "TIENICH", "Điện, Nước và Môi trường"),
]
# Đổi tên mà giữ nguyên code.
RETITLES = [
    ("NHUA", "Nhựa, Bao bì và Giấy"),
    ("DETMAY", "Dệt may, Gỗ và Gia dụng"),
    ("DULICH", "Hàng không, Du lịch và Truyền thông"),
    ("DAUKHI", "Dầu mỏ và Khí đốt"),
]
OLD = {
    "DANDUNG": ("BDS", "Bất động sản Dân dụng"),
    "KHUCONGNGHIEP": ("KCN", "Bất động sản Khu công nghiệp"),
    "VATLIEU": ("VLXD", "Vật liệu Xây dựng"),
    "KHOANGSAN": ("TAINGUYEN", "Tài nguyên Cơ bản"),
    "YTE": ("YTEGD", "Dược phẩm, Y tế và Giáo dục"),
    "TIENICH": ("DIENNUOC", "Điện, Nước và Khí đốt"),
    "NHUA": ("NHUA", "Nhựa và Bao bì"),
    "DETMAY": ("DETMAY", "Dệt may và Gia dụng"),
    "DULICH": ("DULICH", "Hàng không, Du lịch và Giải trí"),
    "DAUKHI": ("DAUKHI", "Dầu khí và Nhiên liệu"),
}


def upgrade() -> None:
    conn = op.get_bind()
    for old, new, name in RENAMES:
        conn.exec_driver_sql(
            "UPDATE market.industry SET code = %s, name_vi = %s WHERE code = %s",
            (new, name, old),
        )
    for code, name in RETITLES:
        conn.exec_driver_sql(
            "UPDATE market.industry SET name_vi = %s WHERE code = %s", (name, code)
        )


def downgrade() -> None:
    conn = op.get_bind()
    for new, (old, name) in OLD.items():
        conn.exec_driver_sql(
            "UPDATE market.industry SET code = %s, name_vi = %s WHERE code = %s",
            (old, name, new),
        )
