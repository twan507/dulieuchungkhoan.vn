"""SpillStore — spec spill §3/§4/§6. Seam 1, 2, 10, 12, 13 của spec §13."""
import os
import pickle
import subprocess
import sys
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from ingester.spill import SpillStore

TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _block(n: int, seq0: int = 1) -> list[list]:
    ts = datetime(2026, 8, 20, 9, 15, 1, tzinfo=TZ)
    return [["ACV", ts, seq0 + i, Decimal("10.00"), 100, "B", Decimal("0.00"),
             100, Decimal("1000.00"), ts] for i in range(n)]


def _store(tmp_path, cap=10**9) -> SpillStore:
    s = SpillStore(tmp_path, cap_bytes=cap)
    assert s.try_acquire()
    s.scan()
    return s


def test_roundtrip_exact_and_fifo_order(tmp_path):
    s = _store(tmp_path)
    b1, b2 = _block(3), _block(2, seq0=100)
    assert s.write("trade", b1, "n") and s.write("quote", b2, "n")
    i1 = s.next_batch(max_rows=10_000)
    assert i1.table == "trade" and i1.block == b1          # FIFO + byte-exact (Decimal/datetime)
    s.delete(i1)
    i2 = s.next_batch(max_rows=10_000)
    assert i2.table == "quote" and i2.block == b2
    s.delete(i2)
    assert s.empty() and s.bytes_used == 0


def test_merge_adjacent_n_same_table_up_to_max_rows(tmp_path):
    s = _store(tmp_path)
    for k in range(3):
        s.write("trade", _block(2, seq0=k * 10), "n")
    s.write("trade", _block(2, seq0=99), "r")              # '-r' chặn gộp
    item = s.next_batch(max_rows=10_000)
    assert item.n_rows == 6 and len(item.paths) == 3       # 3 file -n gộp, dừng trước -r
    s.delete(item)
    r = s.next_batch(max_rows=10_000)
    assert r.kind == "r" and len(r.paths) == 1             # -r nguyên văn một file


def test_merge_respects_max_rows(tmp_path):
    s = _store(tmp_path)
    for k in range(3):
        s.write("trade", _block(2, seq0=k * 10), "n")
    item = s.next_batch(max_rows=4)
    assert item.n_rows == 4 and len(item.paths) == 2       # 2 file = 4 dòng ≤ max


def test_tmp_orphan_skipped_and_counted(tmp_path):
    (tmp_path / "0000000007-trade-n.blk.tmp").write_bytes(b"nua block")
    s = _store(tmp_path)
    assert s.counters["orphan_tmp"] == 1
    assert not (tmp_path / "0000000007-trade-n.blk.tmp").exists()
    assert s.empty()


def test_seq_survives_restart_no_clobber(tmp_path):
    s1 = _store(tmp_path)
    s1.write("trade", _block(1), "n")                      # → seq 1
    del s1
    # tiến trình "mới": KHÔNG giữ lock cũ (mô phỏng chết) — mở store thứ hai
    s2 = SpillStore(tmp_path, cap_bytes=10**9)
    # lock cũ còn giữ bởi file handle s1? s1 đã del → GC đóng. Windows cần chắc chắn:
    import gc; gc.collect()
    assert s2.try_acquire()
    s2.scan()
    assert s2.seq == 2                                     # max quét được + 1, KHÔNG đè
    s2.write("trade", _block(1, seq0=50), "n")
    names = sorted(p.name for p in tmp_path.iterdir() if p.suffix == ".blk")
    assert names == ["0000000001-trade-n.blk", "0000000002-trade-n.blk"]


def test_cap_rejects_write(tmp_path):
    s = _store(tmp_path, cap=200)                          # trần bé tí
    assert s.write("trade", _block(500), "n") is False     # pickle 500 dòng >> 200 B
    assert s.empty()


def test_corrupt_file_moved_aside_and_counted(tmp_path):
    s = _store(tmp_path)
    s.write("trade", _block(1), "n")
    files = [p for p in tmp_path.iterdir() if p.suffix == ".blk"]
    files[0].write_bytes(b"khong phai pickle")
    assert s.next_batch(max_rows=100) is None
    assert s.counters["replay_corrupt"] == 1
    assert any(p.suffix == ".corrupt" for p in tmp_path.iterdir())


def test_lock_excludes_second_process(tmp_path):
    s = _store(tmp_path)
    # lock là CỦA TIẾN TRÌNH — phải kiểm bằng tiến trình con thật, không phải store thứ hai in-process
    code = ("import sys; from pathlib import Path; from ingester.spill import SpillStore; "
            "s = SpillStore(Path(sys.argv[1]), cap_bytes=10**9); "
            "sys.exit(0 if not s.try_acquire() else 1)")
    r = subprocess.run([sys.executable, "-c", code, str(tmp_path)],
                       capture_output=True, cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    assert r.returncode == 0, r.stderr.decode()
