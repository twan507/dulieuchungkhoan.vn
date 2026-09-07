"""Hai đường DB của tầng ngữ nghĩa.

Đường ĐỌC chạy dưới role `dlck_api` (chỉ SELECT trên market/macro/asset/news), qua user login
`agent_reader` và biến `AGENT_DATABASE_URL`. Đường GHI SỔ dùng lại `ETL_DATABASE_URL` vì
`dlck_api` không có quyền gì trên schema `ops` — cố ý, để `dlck_api` giữ đúng hợp đồng "chỉ
đọc" thay vì nới quyền cho một bảng sổ (spec §4.7).

`assert_read_only` chạy ngay lúc khởi động, theo khuôn `assert_migrated` của ingester: dự án
đã trả giá ba lần vì nghiệm thu bằng trạng thái hiển thị thay vì bằng thứ tiến trình thật sự
chạy, và ca đắt nhất nằm ở ĐƯỜNG KHỞI ĐỘNG (CLAUDE.md §3.5).
"""
from __future__ import annotations

import os

import sqlalchemy as sa


def assert_read_only(conn: sa.Connection) -> None:
    """Kết nối này phải thuộc role dlck_api và phải KHÔNG ghi được.

    Không hỏi current_user: current_role là đồng nghĩa của current_user và tư cách thành viên
    role không đổi nó, nên kết nối bằng agent_reader luôn trả 'agent_reader'. Hỏi pg_has_role
    để biết tư cách, rồi hỏi thẳng quyền INSERT để biết hệ quả thật.
    """
    is_member, can_insert = conn.execute(sa.text(
        "SELECT pg_has_role(current_user, 'dlck_api', 'member'),"
        "       has_table_privilege('market.security', 'INSERT')"
    )).one()
    if not is_member:
        raise RuntimeError("ket noi doc khong thuoc role dlck_api")
    if can_insert:
        raise RuntimeError("ket noi doc con quyen INSERT — sai role, khong phai dlck_api thuan doc")


def _engine(var: str) -> sa.Engine:
    url = os.environ.get(var)
    if not url:
        raise RuntimeError(f"thieu {var}")
    return sa.create_engine(url, pool_pre_ping=True)


def read_engine() -> sa.Engine:
    """Engine đọc dữ liệu. Kiểm quyền ngay lúc dựng — sai quyền là chết ở đây, không chạy tiếp."""
    eng = _engine("AGENT_DATABASE_URL")
    with eng.connect() as conn:
        assert_read_only(conn)
    return eng


def ops_engine() -> sa.Engine:
    """Engine ghi sổ ops.llm_call. Chỉ dùng cho đúng việc đó."""
    return _engine("ETL_DATABASE_URL")
