import os
import uuid
from decimal import Decimal

import clickhouse_connect
import pytest

from tests.clickhouse.conftest import dt_ago, part_of

COLS = ["symbol", "ts", "seq", "price", "volume", "side", "change", "cum_volume", "cum_value", "received_at"]


@pytest.fixture()
def ing_client(migrated):
    """Client nối bằng user gắn role dlck_ingester — dedup dựa PROFILE, KHÔNG truyền setting phía client."""
    name = f"t_ing_{uuid.uuid4().hex[:6]}"
    migrated.command(f"CREATE USER {name} IDENTIFIED WITH plaintext_password BY 'x' DEFAULT ROLE dlck_ingester")
    base = os.environ["CLICKHOUSE_URL"].rsplit("@", 1)[1]
    c = clickhouse_connect.get_client(dsn=f"http://{name}:x@{base}")
    yield c
    migrated.command(f"DROP USER IF EXISTS {name}")


def test_retry_nguyen_block_bi_nuot_ca_trade_lan_nen(migrated, ing_client):
    """Spec §5.4 + §12 T4/T9: retry block y nguyên → trade không thêm dòng, nến không đếm đôi."""
    row = [["TDDP", dt_ago(6, 10, 0, 1), 1, Decimal("100.00"), 100, "B",
            Decimal("0.00"), 100, Decimal("10000.00"), dt_ago(6, 10, 30, 0)]]
    ing_client.insert("rt.trade", row, column_names=COLS)
    ing_client.insert("rt.trade", row, column_names=COLS)          # retry giả lập
    assert migrated.query("SELECT count() FROM rt.trade WHERE symbol='TDDP'").result_rows[0][0] == 1
    assert migrated.query("SELECT v FROM rt.bar_1m_v WHERE symbol='TDDP'").result_rows == [(100,)]


def test_block_khac_noi_dung_trung_khoa_van_ghi(migrated, ing_client):
    """Dedup theo hash block, không theo khoá."""
    r1 = [["TDD2", dt_ago(6, 10, 1, 1), 1, Decimal("100.00"), 100, "B",
           Decimal("0.00"), 100, Decimal("10000.00"), dt_ago(6, 10, 30, 0)]]
    r2 = [["TDD2", dt_ago(6, 10, 1, 1), 1, Decimal("100.00"), 999, "B",
           Decimal("0.00"), 100, Decimal("10000.00"), dt_ago(6, 10, 30, 0)]]
    ing_client.insert("rt.trade", r1, column_names=COLS)
    ing_client.insert("rt.trade", r2, column_names=COLS)
    assert migrated.query("SELECT count() FROM rt.trade WHERE symbol='TDD2'").result_rows[0][0] == 2


# Ngữ nghĩa part-level (hai dòng cùng part, một hết hạn → cả hai còn) đã đo ở spec §12/M1-lượt-3;
# không test tự động được với mốc ngày động vì hai dòng cùng partition tháng luôn cùng phía ngưỡng
# TTL trừ partition biên — chấp nhận có ý thức, xem ledger.
def test_ttl_part_level(migrated):
    """Spec §2 + §12 T5/T13: dòng ~5 tháng tuổi bị TTL loại (tại INSERT hoặc MATERIALIZE);
    dòng ~1 tháng còn; nến sinh từ tick cũ (không TTL) vẫn còn sau OPTIMIZE FINAL."""
    migrated.insert("rt.trade",
        [["TOLD", dt_ago(150, 10, 0, 0), 1, Decimal("10.00"), 10, "B", Decimal("0.00"), 10, Decimal("100.00"), dt_ago(150, 10, 0, 0)],
         ["TOLD", dt_ago(30, 10, 0, 0), 2, Decimal("11.00"), 20, "S", Decimal("0.00"), 30, Decimal("320.00"), dt_ago(30, 10, 0, 0)]],
        column_names=COLS, settings={"insert_deduplicate": 0})
    migrated.command("ALTER TABLE rt.trade MATERIALIZE TTL SETTINGS mutations_sync = 2")
    rows = migrated.query("SELECT ts, price FROM rt.trade WHERE symbol='TOLD' ORDER BY ts").result_rows
    assert len(rows) == 1 and rows[0][1] == Decimal("11.00")
    # bảng nến không TTL: dòng bar sinh từ tick cũ (MV chạy trước khi part bị loại) phải còn
    migrated.command("OPTIMIZE TABLE rt.bar_1m FINAL")
    assert migrated.query("SELECT count() FROM rt.bar_1m_v WHERE symbol='TOLD'").result_rows[0][0] == 2


def test_sua_nen_voi_token(migrated):
    """Thủ tục §4.1 + §12 T13: DROP PARTITION → backfill có token → retry cùng token bị nuốt."""
    d = dt_ago(6, 9, 30, 1)
    part = part_of(d)
    migrated.insert("rt.trade",
        [["TREP", d, 1, Decimal("100.00"), 10, "B",
          Decimal("0.00"), 10, Decimal("1000.00"), d]],
        column_names=COLS, settings={"insert_deduplicate": 0})
    migrated.command(f"ALTER TABLE rt.bar_1m DROP PARTITION {part}")
    backfill = f"""
      INSERT INTO rt.bar_1m
      SELECT symbol, toStartOfMinute(event_ts) AS ts,
             argMinState(price, (event_ts, seq, received_at)) AS o,
             maxState(price) AS h, minState(price) AS l,
             argMaxState(price, (event_ts, seq, received_at)) AS c,
             sumState(volume) AS v, sumState(toDecimal128(price, 2) * volume) AS val,
             sumState(if(side = 'B', volume, toUInt64(0))) AS v_bu,
             sumState(if(side = 'S', volume, toUInt64(0))) AS v_sd
      FROM (SELECT symbol, ts AS event_ts, seq, price, volume, side, received_at
            FROM rt.trade WHERE toYYYYMM(toDate(ts)) = {part})
      GROUP BY symbol, ts
    """
    tok = {"insert_deduplication_token": f"repair-{part}-test1"}
    migrated.command(backfill, settings=tok)
    migrated.command(backfill, settings=tok)               # retry cùng token → bị nuốt
    assert migrated.query("SELECT v FROM rt.bar_1m_v WHERE symbol='TREP'").result_rows == [(10,)]


def test_sua_nen_khong_token_thi_nhan_doi_va_partition_khac_khong_dung(migrated):
    """Spec §12/T13: retry backfill KHÔNG token → nhân đôi; partition khác không bị đụng."""
    d = dt_ago(6, 9, 40, 1)
    part = part_of(d)
    migrated.insert("rt.trade",
        [["TRP2", d, 1, Decimal("50.00"), 10, "B", Decimal("0.00"), 10, Decimal("500.00"), d]],
        column_names=COLS, settings={"insert_deduplicate": 0})
    old = dt_ago(45, 9, 40, 1)
    migrated.insert("rt.trade",
        [["TRP3", old, 1, Decimal("70.00"), 7, "B", Decimal("0.00"), 7, Decimal("490.00"), old]],
        column_names=COLS, settings={"insert_deduplicate": 0})
    migrated.command(f"ALTER TABLE rt.bar_1m DROP PARTITION {part}")
    backfill = f"""
      INSERT INTO rt.bar_1m
      SELECT symbol, toStartOfMinute(event_ts) AS ts,
             argMinState(price, (event_ts, seq, received_at)) AS o,
             maxState(price) AS h, minState(price) AS l,
             argMaxState(price, (event_ts, seq, received_at)) AS c,
             sumState(volume) AS v, sumState(toDecimal128(price, 2) * volume) AS val,
             sumState(if(side = 'B', volume, toUInt64(0))) AS v_bu,
             sumState(if(side = 'S', volume, toUInt64(0))) AS v_sd
      FROM (SELECT symbol, ts AS event_ts, seq, price, volume, side, received_at
            FROM rt.trade WHERE toYYYYMM(toDate(ts)) = {part})
      GROUP BY symbol, ts
    """
    migrated.command(backfill)
    migrated.command(backfill)                               # không token → đếm đôi
    assert migrated.query("SELECT v FROM rt.bar_1m_v WHERE symbol='TRP2'").result_rows == [(20,)]
    assert migrated.query("SELECT v FROM rt.bar_1m_v WHERE symbol='TRP3'").result_rows == [(7,)]
