from pathlib import Path

import pytest

from core import ch_migrate


def _reset(ch):
    ch.command("DROP DATABASE IF EXISTS rt")


def _write(d: Path, name: str, sql: str) -> None:
    (d / name).write_text(sql, encoding="utf-8")


@pytest.fixture(autouse=True, scope="module")
def _don_sach_sau_module(ch):
    """t02 nghịch database rt bằng migration giả — dọn sạch sau khi CẢ module chạy xong,
    để t03+ nhận rt nguyên sơ từ fixture migrated (kẻ gây ô nhiễm tự dọn)."""
    yield
    ch.command("DROP DATABASE IF EXISTS rt")


def test_split_statements_bo_comment_va_rong():
    sql = "-- chi comment\nCREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;\n\n-- nua\n;\nGRANT SELECT ON rt.* TO r1;"
    stmts = ch_migrate.split_statements(sql)
    assert len(stmts) == 2
    assert stmts[0].startswith("-- chi comment")  # comment dính statement sau vô hại
    assert "GRANT SELECT" in stmts[1]


def test_upgrade_bootstrap_va_ap_dung_tuan_tu(ch, tmp_path):
    _reset(ch)
    _write(tmp_path, "0001_a.sql", "CREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;")
    _write(tmp_path, "0002_b.sql", "CREATE TABLE IF NOT EXISTS rt.b (x UInt8) ENGINE = MergeTree ORDER BY x;")
    ran = ch_migrate.upgrade(ch, versions_dir=tmp_path)
    assert ran == ["0001_a", "0002_b"]
    assert ch_migrate.applied_versions(ch) == {"0001_a", "0002_b"}
    # sổ migration dùng ReplacingMergeTree, đọc DISTINCT
    assert ch.command("SELECT engine FROM system.tables WHERE database='rt' AND name='schema_migrations'") == "ReplacingMergeTree"


def test_upgrade_lan_hai_khong_lam_gi(ch, tmp_path):
    _reset(ch)
    _write(tmp_path, "0001_a.sql", "CREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;")
    ch_migrate.upgrade(ch, versions_dir=tmp_path)
    assert ch_migrate.upgrade(ch, versions_dir=tmp_path) == []


def test_file_moi_them_duoc_chay_tiep(ch, tmp_path):
    _reset(ch)
    _write(tmp_path, "0001_a.sql", "CREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;")
    ch_migrate.upgrade(ch, versions_dir=tmp_path)
    _write(tmp_path, "0002_b.sql", "CREATE TABLE IF NOT EXISTS rt.b (x UInt8) ENGINE = MergeTree ORDER BY x;")
    assert ch_migrate.upgrade(ch, versions_dir=tmp_path) == ["0002_b"]


def test_chet_giua_chung_chay_lai_di_qua_duoc(ch, tmp_path):
    """DDL không transaction: statement 1 chạy xong, statement 2 lỗi, sổ chưa ghi.
    Sửa file rồi chạy lại: statement 1 (IF NOT EXISTS) đi qua, version được ghi."""
    _reset(ch)
    _write(tmp_path, "0001_a.sql",
           "CREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;\nSAI CU PHAP;")
    with pytest.raises(Exception):
        ch_migrate.upgrade(ch, versions_dir=tmp_path)
    assert ch_migrate.applied_versions(ch) == set()          # sổ chưa ghi
    assert ch.command("SELECT count() FROM system.tables WHERE database='rt' AND name='a'") == 1
    _write(tmp_path, "0001_a.sql",
           "CREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;")
    assert ch_migrate.upgrade(ch, versions_dir=tmp_path) == ["0001_a"]


def test_assert_migrated(ch, tmp_path):
    _reset(ch)
    _write(tmp_path, "0002_zz_fake.sql", "CREATE TABLE IF NOT EXISTS rt.a (x UInt8) ENGINE = MergeTree ORDER BY x;")
    with pytest.raises(RuntimeError):
        ch_migrate.assert_migrated(ch, required="0002_zz_fake")  # rt chưa tồn tại / sổ trống
    ch_migrate.upgrade(ch, versions_dir=tmp_path)
    ch_migrate.assert_migrated(ch, required="0002_zz_fake")      # không raise
