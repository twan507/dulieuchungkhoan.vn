"""SpillStore — spec spill §3/§4/§6. Seam 1, 2, 10, 12, 13 của spec §13."""
import os
import pickle
import subprocess
import sys
import threading
from datetime import datetime
from decimal import Decimal
from pathlib import Path
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


def test_bytes_used_decrements_on_corrupt_rename(tmp_path):
    b1, b2 = _block(1), _block(1, seq0=50)
    size1 = len(pickle.dumps(("trade", b1), protocol=5))
    size2 = len(pickle.dumps(("trade", b2), protocol=5))
    cap = size1 + size2                             # đủ đúng 2 khối, không dư
    s = _store(tmp_path, cap=cap)
    assert s.write("trade", b1, "n") and s.write("trade", b2, "n")
    assert s.write("trade", b1, "n") is False        # hết trần trước khi hỏng file
    files = sorted(p for p in tmp_path.iterdir() if p.suffix == ".blk")
    files[0].write_bytes(b"x" * size1)               # hỏng nội dung, GIỮ NGUYÊN độ dài
    before = s.bytes_used
    item = s.next_batch(max_rows=100)                # corrupt-rename file1, trả về khối 2
    assert item is not None and item.block == b2
    assert s.counters["replay_corrupt"] == 1
    assert s.bytes_used == before - size1            # bytes_used phải trừ đúng size file hỏng
    assert s.write("trade", b1, "n") is True         # không gian đã giải phóng đủ cho khối mới


def test_tmp_cleaned_up_on_write_io_error(tmp_path, monkeypatch):
    s = _store(tmp_path)
    real_fdopen = os.fdopen

    def _boom_fdopen(fd, mode):
        real_fh = real_fdopen(fd, mode)

        class _Boom:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                real_fh.close()
                return False

            def write(self, data):
                raise OSError("giả lập lỗi I/O giữa chừng ghi")

        return _Boom()

    monkeypatch.setattr(os, "fdopen", _boom_fdopen)
    assert s.write("trade", _block(1), "n") is False
    assert list(tmp_path.glob("*.tmp")) == []        # tmp không được để sót lại
    # Spec §8 phân loại: `write` trả False vì HAI lý do khác hẳn nhau — chạm trần đĩa
    # (bình thường, có `spill_drop_newest`) và lỗi I/O (bão ENOSPC, đĩa hỏng). Không có
    # counter riêng thì hai chuyện đó trông y hệt nhau trên bảng đếm.
    assert s.counters["spill_io_error"] == 1


def test_read_io_error_keeps_the_file_and_stops_the_batch(tmp_path, monkeypatch):
    """`except Exception` gộp lỗi ĐỌC (AV/indexer giữ handle — trigger sản xuất đã nêu)
    với pickle hỏng. Hệ quả: một file HOÀN TOÀN LÀNH bị đổi tên `.corrupt` = vứt dòng chưa
    bao giờ hỏng. Lỗi đọc phải: giữ nguyên file, đếm riêng, và DỪNG lô này — không nhảy
    qua file đó (nhảy là phá thứ tự FIFO của hàng đợi đĩa)."""
    s = _store(tmp_path)
    assert s.write("trade", _block(1), "n")
    assert s.write("trade", _block(1, seq0=50), "n")
    before = sorted(p.name for p in tmp_path.iterdir())

    def _boom(self):
        raise PermissionError("AV giữ handle file")

    monkeypatch.setattr(Path, "read_bytes", _boom)
    assert s.next_batch(max_rows=100) is None            # dừng, KHÔNG nhảy qua
    assert sorted(p.name for p in tmp_path.iterdir()) == before   # file còn NGUYÊN
    assert s.counters["spill_io_error"] == 1
    assert s.counters["replay_corrupt"] == 0             # không phải hỏng — đừng đếm nhầm


def test_corrupt_rename_failure_holds_the_file_without_inflating_replay_corrupt(
        tmp_path, monkeypatch):
    """Vế hai: file hỏng THẬT nhưng `rename` cũng hỏng. Bản cũ đã kịp `replay_corrupt += 1`
    trước khi `rename` ném, nên mỗi nhịp `next_batch` bốc lại đúng file đó lại cộng thêm
    một — bộ đếm mất dòng phồng lên vô hạn trong khi KHÔNG dòng nào thật sự bị vứt."""
    s = _store(tmp_path)
    assert s.write("trade", _block(1), "n")
    f = next(p for p in tmp_path.iterdir() if p.suffix == ".blk")
    f.write_bytes(b"khong phai pickle")

    def _boom(self, target):
        raise PermissionError("AV giữ handle file")

    monkeypatch.setattr(Path, "rename", _boom)
    assert s.next_batch(max_rows=100) is None
    assert s.next_batch(max_rows=100) is None            # nhịp thứ hai bốc lại đúng file đó
    assert f.exists()                                    # chưa cách ly được thì file ở lại
    assert s.counters["replay_corrupt"] == 0             # ...nên chưa được đếm là mất dòng
    assert s.counters["spill_io_error"] == 2


# --- Ghi từ HAI thread: vòng quản (`_spill_tail`) và vòng ghi (cửa 2, chia đôi) -------


def test_concurrent_writes_from_two_threads_never_collide(tmp_path):
    """`write()` được gọi từ CẢ HAI thread của ChWriter — vòng quản (`_spill_tail`) và vòng
    ghi (cửa 2 ghi '-r', `_split_disk_item` ghi hai file con) — mà `self.seq`/`bytes_used`
    không có gì bảo vệ. Đua cùng `seq`: kẻ thua thấy `final.exists()` rồi gọi
    `tmp.unlink()` — mà `tmp` là ĐÚNG tên file tạm kẻ THẮNG đang ghi dở, nên xoá mất bản
    của người khác và cả hai block cùng rơi.

    Hạ `switchinterval` theo đúng kỹ thuật của `test_i08` để GIL nhường quyền dày hơn."""
    old_interval = sys.getswitchinterval()
    sys.setswitchinterval(0.00001)
    try:
        _run_concurrent_write_check(tmp_path)
    finally:
        sys.setswitchinterval(old_interval)


def _run_concurrent_write_check(tmp_path):
    n = 80
    s = _store(tmp_path)
    results: list[bool] = []
    lock = threading.Lock()

    def writer(seq0: int):
        oks = [s.write("trade", _block(1, seq0=seq0 + i), "n") for i in range(n)]
        with lock:
            results.extend(oks)

    ts = [threading.Thread(target=writer, args=(base,)) for base in (0, 1000)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()

    assert all(results) and len(results) == 2 * n     # không lời gọi nào bị từ chối
    blks = [p for p in tmp_path.iterdir() if p.suffix == ".blk"]
    assert len(blks) == 2 * n                          # ...và không file nào bốc hơi
    assert sorted(int(p.name[:10]) for p in blks) == list(range(1, 2 * n + 1))
    assert s.counters["seq_collision"] == 0
    assert s.bytes_used == sum(p.stat().st_size for p in blks)   # đo lại độc lập từ đĩa
    assert list(tmp_path.glob("*.tmp")) == []


def test_lock_excludes_second_process(tmp_path):
    s = _store(tmp_path)
    # lock là CỦA TIẾN TRÌNH — phải kiểm bằng tiến trình con thật, không phải store thứ hai in-process
    code = ("import sys; from pathlib import Path; from ingester.spill import SpillStore; "
            "s = SpillStore(Path(sys.argv[1]), cap_bytes=10**9); "
            "sys.exit(0 if not s.try_acquire() else 1)")
    r = subprocess.run([sys.executable, "-c", code, str(tmp_path)],
                       capture_output=True, cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    assert r.returncode == 0, r.stderr.decode()
