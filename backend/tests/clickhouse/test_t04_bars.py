from decimal import Decimal

from tests.clickhouse.conftest import dt_ago

IDX_COLS = ["symbol", "ts", "index_value", "total_vol", "total_value", "received_at"]


def _ins_trade(ch, rows):
    ch.insert(
        "rt.trade", rows,
        column_names=["symbol", "ts", "seq", "price", "volume", "side",
                      "change", "cum_volume", "cum_value", "received_at"],
        settings={"insert_deduplicate": 0},   # test hành vi MV, không test dedup ở đây
    )


def test_bar_1m_giai_tay(migrated):
    """3 tick một phút: (s+1,seq5,100.00,100,B) (s+2,seq7,101.00,200,S) (s+59,seq9,99.00,50,B)
    → o=100 h=101 l=99 c=99 v=350 val=10000+20200+4950=35150 v_bu=150 v_sd=200 (spec §12 T1)."""
    rows = [
        ["TBID", dt_ago(6, 9, 15, 1), 5, Decimal("100.00"), 100, "B", Decimal("0.00"), 100, Decimal("10000.00"), dt_ago(6, 9, 15, 1, 100000)],
        ["TBID", dt_ago(6, 9, 15, 2), 7, Decimal("101.00"), 200, "S", Decimal("1.00"), 300, Decimal("30200.00"), dt_ago(6, 9, 15, 2, 100000)],
        ["TBID", dt_ago(6, 9, 15, 59), 9, Decimal("99.00"), 50, "B", Decimal("-1.00"), 350, Decimal("35150.00"), dt_ago(6, 9, 15, 59, 100000)],
    ]
    _ins_trade(migrated, rows[:1])
    _ins_trade(migrated, rows[1:])            # rải 2 block cùng phút — state phải gộp đúng
    r = migrated.query("SELECT o, h, l, c, v, val, v_bu, v_sd FROM rt.bar_1m_v WHERE symbol='TBID'").result_rows
    assert r == [(Decimal("100.00"), Decimal("101.00"), Decimal("99.00"), Decimal("99.00"),
                  350, Decimal("35150.00"), 150, 200)]


def test_side_la_vao_v_khong_vao_bu_sd(migrated):
    _ins_trade(migrated, [["TVNM", dt_ago(6, 9, 16, 10), 11, Decimal("50.00"), 30, "X",
                           Decimal("0.00"), 30, Decimal("1500.00"), dt_ago(6, 9, 16, 10)]])
    r = migrated.query("SELECT v, v_bu, v_sd FROM rt.bar_1m_v WHERE symbol='TVNM'").result_rows
    assert r == [(30, 0, 0)]


def test_o_c_on_dinh_qua_merge_khi_hoa_ts_seq(migrated):
    """Khoá total (ts, seq, received_at) — spec §4.1, đo T12: hai tick hoà (ts,seq) khác received_at."""
    _ins_trade(migrated, [["TTIE", dt_ago(6, 9, 17, 10), 7, Decimal("100.00"), 10, "B",
                           Decimal("0.00"), 10, Decimal("1000.00"), dt_ago(6, 9, 17, 10, 100000)]])
    _ins_trade(migrated, [["TTIE", dt_ago(6, 9, 17, 10), 7, Decimal("200.00"), 20, "B",
                           Decimal("0.00"), 30, Decimal("5000.00"), dt_ago(6, 9, 17, 10, 250000)]])
    before = migrated.query("SELECT o, c FROM rt.bar_1m_v WHERE symbol='TTIE'").result_rows
    migrated.command("OPTIMIZE TABLE rt.bar_1m FINAL")
    after = migrated.query("SELECT o, c FROM rt.bar_1m_v WHERE symbol='TTIE'").result_rows
    assert before == after == [(Decimal("100.00"), Decimal("200.00"))]


def test_index_bar_null_khong_thanh_0(migrated):
    """Phút không frame nào mang TV → cum_vol NULL (spec §4.2, đo T3)."""
    migrated.insert("rt.index_delta",
        [["THOSE", dt_ago(6, 9, 20, 5), Decimal("1300.50"), None, None, dt_ago(6, 9, 20, 5)],
         ["THOSE", dt_ago(6, 9, 20, 35), Decimal("1301.20"), None, None, dt_ago(6, 9, 20, 35)]],
        column_names=IDX_COLS)
    migrated.insert("rt.index_delta",
        [["THOSE", dt_ago(6, 9, 21, 5), Decimal("1302.00"), 500000, Decimal("12000000.00"), dt_ago(6, 9, 21, 5)]],
        column_names=IDX_COLS)
    r = migrated.query(
        "SELECT ts, o, c, cum_vol, cum_value FROM rt.index_bar_1m_v WHERE symbol='THOSE' ORDER BY ts").result_rows
    assert r[0][3] is None and r[0][4] is None          # phút đầu — NULL, không phải 0
    assert r[1][3] == 500000 and r[1][4] == Decimal("12000000.00")


def test_index_guard_mi_bang_0_khong_sinh_nen(migrated):
    migrated.insert("rt.index_delta",
        [["TGRD", dt_ago(6, 8, 50, 0), Decimal("0.00"), None, None, dt_ago(6, 8, 50, 0)]],
        column_names=IDX_COLS)
    assert migrated.query("SELECT count() FROM rt.index_bar_1m_v WHERE symbol='TGRD'").result_rows[0][0] == 0


def test_index_o_c_on_dinh_qua_merge_khi_hoa_ms(migrated):
    """Khoá total (event_ts, received_at) — spec §4.2, đo T14: hai frame hoà mili-giây."""
    migrated.insert("rt.index_delta",
        [["THNX", dt_ago(6, 13, 9, 0, 500000), Decimal("700.00"), None, None, dt_ago(6, 13, 9, 0, 600000)]],
        column_names=IDX_COLS)
    migrated.insert("rt.index_delta",
        [["THNX", dt_ago(6, 13, 9, 0, 500000), Decimal("800.00"), None, None, dt_ago(6, 13, 9, 0, 700000)]],
        column_names=IDX_COLS)
    before = migrated.query("SELECT o, c FROM rt.index_bar_1m_v WHERE symbol='THNX'").result_rows
    migrated.command("OPTIMIZE TABLE rt.index_bar_1m FINAL")
    after = migrated.query("SELECT o, c FROM rt.index_bar_1m_v WHERE symbol='THNX'").result_rows
    assert before == after == [(Decimal("700.00"), Decimal("800.00"))]
