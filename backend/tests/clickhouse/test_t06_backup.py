from datetime import timedelta
from decimal import Decimal

from core import ch_backup
from tests.clickhouse.conftest import TODAY, dt_ago, part_of

COLS = ["symbol", "ts", "seq", "price", "volume", "side", "change", "cum_volume", "cum_value", "received_at"]

PM = part_of(dt_ago(45))                  # partition tháng ĐÃ ĐÓNG (45 ngày trước luôn khác tháng hiện tại)
CUR = TODAY.strftime("%Y%m")
STAMP = TODAY.strftime("%Y%m%d")
STAMP2 = (TODAY + timedelta(days=1)).strftime("%Y%m%d")


def _seed(ch):
    ch.insert("rt.trade",
        [["TBK", dt_ago(45, 9, 15, 1), 1, Decimal("50.00"), 10, "B", Decimal("0.00"), 10, Decimal("500.00"), dt_ago(45, 9, 15, 1)],
         ["TBK", dt_ago(0, 9, 15, 1), 2, Decimal("60.00"), 20, "S", Decimal("0.00"), 30, Decimal("1700.00"), dt_ago(0, 9, 15, 1)]],
        column_names=COLS, settings={"insert_deduplicate": 0})


def test_backup_lan_dau_thang_dong_mot_lan_thang_mo_theo_ngay(migrated, ch_backup_dir):
    _seed(migrated)
    ch_backup.run_backup(migrated, ch_backup_dir, today=TODAY)
    names = {p.name for p in ch_backup_dir.iterdir()}
    assert f"trade-{PM}.zip" in names                      # tháng đóng — tên không ngày
    assert f"trade-{CUR}-{STAMP}.zip" in names             # tháng mở — tên theo ngày
    assert f"bar_1m-{STAMP}.zip" in names                  # bảng nến full
    assert f"index_bar_1m-{STAMP}.zip" in names


def test_chay_lai_cung_ngay_khong_lam_gi(migrated, ch_backup_dir):
    ch_backup.run_backup(migrated, ch_backup_dir, today=TODAY)
    a2 = ch_backup.run_backup(migrated, ch_backup_dir, today=TODAY)
    assert a2 == []                                        # idempotent trong ngày


def test_ngay_moi_de_ban_thang_mo_xoa_ban_cu(migrated, ch_backup_dir):
    ch_backup.run_backup(migrated, ch_backup_dir, today=TODAY)
    ch_backup.run_backup(migrated, ch_backup_dir, today=TODAY + timedelta(days=1))
    names = {p.name for p in ch_backup_dir.iterdir()}
    assert f"trade-{CUR}-{STAMP2}.zip" in names or (TODAY + timedelta(days=1)).strftime("%Y%m") != CUR
    assert f"trade-{CUR}-{STAMP}.zip" not in names         # bản cũ của tháng mở đã xoá (hoặc tháng vừa đóng — cũng xoá daily)
    assert f"trade-{PM}.zip" in names                      # tháng đóng không chép lại


def test_restore_partition_du_dong_khong_kich_mv(migrated, ch_backup_dir):
    """Spec §12 T15: RESTORE cần allow_non_empty_tables, gắn part trực tiếp — nến không đổi."""
    ch_backup.run_backup(migrated, ch_backup_dir, today=TODAY)
    bars_before = migrated.query("SELECT count() FROM rt.bar_1m_v").result_rows[0][0]
    migrated.command(f"ALTER TABLE rt.trade DROP PARTITION {PM}")
    migrated.command(f"RESTORE TABLE rt.trade PARTITION '{PM}' FROM Disk('backups', 'trade-{PM}.zip')"
                     " SETTINGS allow_non_empty_tables = true")
    assert migrated.query("SELECT count() FROM rt.trade WHERE symbol='TBK'").result_rows[0][0] == 2
    assert migrated.query("SELECT count() FROM rt.bar_1m_v").result_rows[0][0] == bars_before
