import gzip
import json

from ingester.measure import MeasureWriter


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
