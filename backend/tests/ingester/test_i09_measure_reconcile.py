import gzip
import json
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from ingester.measure import MeasureWriter
from ingester.reconcile import _classify, reconcile


def test_measure_roundtrip_exact_bytes(tmp_path):
    w = MeasureWriter(tmp_path)
    pkt = '42["t",{"SB":"ACV","FMP":"42100.0"}]'
    w.write(1786342136000, pkt)
    w.close()
    f = next(tmp_path.glob("frames-*.jsonl*"))
    opener = gzip.open if f.suffix == ".gz" else open
    with opener(f, "rt", encoding="utf-8") as fh:
        row = json.loads(fh.readline())
    assert row == {"r": 1786342136000, "p": pkt}  # nguyên văn từng byte


def test_measure_rotates_by_hour(tmp_path):
    clock = {"t": 1_786_330_800.0}  # trong giờ 13h VN ngày 10/08/2026

    def fake_clock():
        return clock["t"]

    w = MeasureWriter(tmp_path, clock=fake_clock)
    w.write(1, "a")
    clock["t"] += 3600  # sang giờ mới → file cũ phải được gzip
    w.write(2, "b")
    w.close()
    names = sorted(p.name for p in tmp_path.iterdir())
    assert len(names) == 2
    assert all(n.endswith(".jsonl.gz") for n in names)


def test_reconcile_classifies(migrated):
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    ts = datetime(2026, 8, 20, 9, 15, 1, tzinfo=tz)
    rows = [
        # mã OK: 2 tick, cum khớp tổng
        ["OKA", ts, 1, Decimal("10.00"), 100, "B", Decimal("0.00"), 100, Decimal("1000.00"), ts],
        ["OKA", ts, 2, Decimal("10.00"), 50, "S", Decimal("0.00"), 150, Decimal("1500.00"), ts],
        # mã hụt >0.1%: bar có 100 nhưng AVO nói 200
        ["MISS", ts, 1, Decimal("10.00"), 100, "B", Decimal("0.00"), 200, Decimal("2000.00"), ts],
    ]
    migrated.insert("rt.trade", rows, column_names=[
        "symbol", "ts", "seq", "price", "volume", "side", "change",
        "cum_volume", "cum_value", "received_at"])
    r = reconcile(migrated, date(2026, 8, 20))
    assert r.ok >= 1
    assert any(s == "MISS" for s, *_ in r.p2)
    assert not any(s == "OKA" for s, *_ in r.p1 + r.p2)
    migrated.command("ALTER TABLE rt.trade DELETE WHERE symbol IN ('OKA','MISS')")
    migrated.command("ALTER TABLE rt.bar_1m DROP PARTITION '202608'")


def test_classify_branches():
    assert _classify(150, 100) == "p1"
    assert _classify(100, 200) == "p2"
    assert _classify(999, 1000) == "minor"
    assert _classify(100, 100) == "ok"


def test_reconcile_names_symbol_missing_from_bars(migrated):
    """MINOR 1 review cuối — `coalesce(b.symbol, t.symbol)` giả định FULL JOIN đệm NULL,
    nhưng ClickHouse mặc định `join_use_nulls = 0` đệm CHUỖI RỖNG cho phía không khớp.
    Mã chỉ có trong `rt.trade` (không có nến) vì thế bị báo với tên RỖNG — đúng ca P2 mà
    người trực cần biết mã nào.
    """
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    ts = datetime(2026, 7, 20, 9, 15, 1, tzinfo=tz)
    migrated.insert("rt.trade", [
        ["NOBAR", ts, 1, Decimal("10.00"), 100, "B", Decimal("0.00"), 200,
         Decimal("2000.00"), ts]], column_names=[
        "symbol", "ts", "seq", "price", "volume", "side", "change",
        "cum_volume", "cum_value", "received_at"])
    # xoá nến do MV sinh ra → mã này chỉ còn ở một phía của FULL JOIN
    migrated.command("ALTER TABLE rt.bar_1m DROP PARTITION '202607'")
    r = reconcile(migrated, date(2026, 7, 20))
    assert [s for s, *_ in r.p2] == ["NOBAR"]      # có tên thật, không phải chuỗi rỗng
    assert r.p1 == []
    migrated.command("ALTER TABLE rt.trade DELETE WHERE symbol='NOBAR'")
