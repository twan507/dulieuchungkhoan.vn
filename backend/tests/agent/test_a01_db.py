"""Seam S1 — đường đọc phải chạy dưới role dlck_api và KHÔNG ghi được.

CLAUDE.md §3.5 ca thứ ba: hỏng ở đường KHỞI ĐỘNG thì hỏng toàn bộ, không phải một phần.
assert_read_only() là chốt chặn khởi động nên nó phải được test dưới đúng quyền production.

Không kiểm bằng current_user: trong Postgres current_role là ĐỒNG NGHĨA của current_user và
tư cách thành viên role không đổi nó — kết nối bằng user agent_reader thì current_user luôn là
'agent_reader', không bao giờ là 'dlck_api'. Phải hỏi pg_has_role và hỏi thẳng quyền INSERT.
"""
import pytest
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError

from agent.db import assert_read_only


def test_assert_read_only_passes_under_dlck_api(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert_read_only(db)                       # không ném


def test_assert_read_only_rejects_a_writer(db):
    """Role mặc định của fixture ghi được ⇒ chốt chặn phải từ chối nó."""
    with pytest.raises(RuntimeError) as err:
        assert_read_only(db)
    assert "dlck_api" in str(err.value)


def test_dlck_api_cannot_insert(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    with pytest.raises(ProgrammingError):
        db.execute(sa.text("INSERT INTO market.industry (code, name_vi, level) VALUES ('XX', 'x', 1)"))


def test_dlck_api_can_read_the_three_views(db):
    """Ba view mà tầng ngữ nghĩa đi qua — thiếu quyền một cái là hỏng một function."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    for obj in ("market.v_issuer_industry", "market.price_factor", "macro.observation_spliced"):
        db.execute(sa.text(f"SELECT 1 FROM {obj} LIMIT 1"))


def test_dlck_api_can_call_the_unaccent_wrapper(db):
    """news.immutable_unaccent là hàm sinh cột tsv — get_news bắt buộc gọi được nó."""
    db.execute(sa.text("SET LOCAL ROLE dlck_api"))
    assert db.execute(sa.text("SELECT news.immutable_unaccent('lãi suất')")).scalar() == "lai suat"
