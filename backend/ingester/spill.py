"""Hàng đợi block trên đĩa cho ChWriter — spec spill §3/§4/§6.

Thư mục PHẲNG, mỗi block một file pickle `{seq:010d}-{table}-{kind}.blk`
(kind 'r' = từng gửi, phát lại nguyên văn giữ hash; 'n' = chưa từng gửi, được gộp).
Sở hữu = OS exclusive lock trên `owner.lock`, giữ suốt đời tiến trình, OS tự nhả
khi tiến trình chết (kể cả OOM-kill). Xoá file CHỈ SAU insert thành công — caller
gọi delete() khi ClickHouse trả OK. KHÔNG fsync: mô hình đe doạ là tiến trình
chết (page cache OS sống sót), không phải mất điện (spec §3).
"""
from __future__ import annotations

import logging
import os
import pickle
import re
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("ingester.spill")
_NAME = re.compile(r"^(\d{10})-([a-z_0-9]+)-([rn])\.blk$")


@dataclass(frozen=True)
class SpillItem:
    paths: tuple[Path, ...]
    table: str
    kind: str
    block: list
    n_rows: int
    n_bytes: int


class SpillStore:
    def __init__(self, root: Path, cap_bytes: int):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.cap_bytes = cap_bytes
        self.owned = False
        self.seq = 1
        self.bytes_used = 0
        self.counters: dict[str, int] = {"orphan_tmp": 0, "replay_corrupt": 0,
                                         "seq_collision": 0}
        self._lock_fh = None

    def try_acquire(self) -> bool:
        """Giành khoá RỒI QUÉT, `owned` đặt CUỐI CÙNG (nợ Task 6 — M4).

        🔴 Thứ tự này là hợp đồng, không phải sở thích: `owned = True` đặt trước `scan()`
        mở một khe mà store đã nhận là "của mình" nhưng `seq`/`bytes_used` còn nguyên giá
        trị khởi tạo (1 và 0). Một block xuống đĩa trong khe đó (cửa 2 chạy ở thread vòng
        ghi) ghi đè tên `0000000001-…` — đo trên bản lỗi: file thứ hai `0000000001-trade-r`
        ra đời TRÙNG seq mà `seq_collision` không hề tăng (chốt `final.exists()` so cả
        `kind` nên hai kind khác nhau lọt), và block cùng kind kế tiếp thì bị TỪ CHỐI dù
        đĩa hoàn toàn khoẻ. `bytes_used = 0` cũ còn làm trần đĩa nới ra bằng đúng khối nợ
        đang nằm sẵn. Giành được khoá xong là store phải SẴN SÀNG ghi ngay."""
        if self.owned:
            return True
        fh = open(self.root / "owner.lock", "a+b")
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            return False
        self._lock_fh = fh                    # giữ mở suốt đời — nhả = chết
        try:
            self._scan()
        except OSError:
            # 🔴 Quét hỏng (AV/indexer giữ một `.tmp` mồ côi ⇒ `unlink` ném PermissionError)
            # mà cứ ôm khoá thì tiến trình thành ZOMBIE NGẬM KHOÁ: `owned` vẫn False nên
            # `_adopt_spill_if_possible` thử lại mỗi nhịp, nhưng chính nó không giành lại
            # được (khoá xung đột theo HANDLE với `msvcrt.locking`, theo open-file-
            # description với `flock` — kể cả trong cùng tiến trình), và tiến trình khác
            # cũng không nhận nuôi được. Nhả sạch rồi NÉM TIẾP: đường khởi động bắt
            # `OSError` để trả exit 3 đúng hợp đồng, vòng quản giữa phiên đã có `try` riêng.
            self._release()
            raise
        self.owned = True                     # ĐẶT CUỐI — xem docstring
        return True

    def _release(self) -> None:
        """Nhả khoá + đóng handle. Đóng handle là đủ để OS nhả; mở khoá tường minh chỉ để
        không phụ thuộc vào chi tiết đó."""
        fh, self._lock_fh = self._lock_fh, None
        if fh is None:
            return
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh, fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            fh.close()

    def scan(self) -> None:
        """Quét lại thủ công. `try_acquire()` đã quét sẵn nên đường chạy KHÔNG cần gọi;
        giữ public cho test và cho ca muốn đồng bộ lại `seq`/`bytes_used` với đĩa."""
        assert self.owned, "scan() chỉ sau khi try_acquire() thành công"
        self._scan()

    def _scan(self) -> None:
        max_seq = 0
        self.bytes_used = 0
        for p in list(self.root.iterdir()):
            if p.name.endswith(".blk.tmp"):
                p.unlink()
                self.counters["orphan_tmp"] += 1
                continue
            m = _NAME.match(p.name)
            if m:
                max_seq = max(max_seq, int(m.group(1)))
                self.bytes_used += p.stat().st_size
        self.seq = max_seq + 1

    def _files(self) -> list[Path]:
        return sorted(p for p in self.root.iterdir() if _NAME.match(p.name))

    def empty(self) -> bool:
        return not self._files()

    def pending_files(self) -> tuple[int, int]:
        """(số block, số byte) còn nợ trên đĩa — cho log hết ngân sách xả (spec §5.2).

        Đơn vị là BLOCK + BYTE, không phải dòng: đếm dòng buộc phải `pickle.loads` toàn bộ
        hàng đợi đĩa (có thể nhiều GiB) đúng lúc phiên đang đóng. `bytes_used` là biến đếm
        đã duy trì sẵn nên chỉ tốn một lần liệt kê thư mục."""
        return len(self._files()), self.bytes_used

    def write(self, table: str, block: list, kind: str) -> bool:
        if not self.owned:
            return False
        data = pickle.dumps((table, block), protocol=5)
        if self.bytes_used + len(data) > self.cap_bytes:
            return False
        name = f"{self.seq:010d}-{table}-{kind}.blk"
        final, tmp = self.root / name, self.root / (name + ".tmp")
        try:
            fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                         | getattr(os, "O_BINARY", 0))
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            if final.exists():                # không bao giờ đè (spec §3)
                tmp.unlink()
                self.counters["seq_collision"] += 1
                log.error("spill: %s đã tồn tại — seq hỏng, không đè", name)
                return False
            os.replace(tmp, final)
        except OSError:
            tmp.unlink(missing_ok=True)       # đừng để tmp mồ côi nếu ghi giữa chừng lỗi
            log.exception("spill: lỗi I/O khi ghi %s", name)
            return False
        self.seq += 1
        self.bytes_used += len(data)
        return True

    def next_batch(self, max_rows: int, block_cap: int = 5000) -> SpillItem | None:
        files = self._files()
        i = 0
        while i < len(files):
            p = files[i]
            loaded = self._load(p)
            if loaded is None:
                i += 1
                continue
            table, block = loaded
            kind = _NAME.match(p.name).group(3)
            if kind == "r":
                return SpillItem((p,), table, "r", block, len(block), p.stat().st_size)
            paths, rows = [p], list(block)
            limit = min(block_cap, max_rows)
            for q in files[i + 1:]:
                mq = _NAME.match(q.name)
                if mq.group(2) != table or mq.group(3) != "n":
                    break
                nxt = self._load(q)
                if nxt is None or len(rows) + len(nxt[1]) > limit:
                    break
                paths.append(q)
                rows.extend(nxt[1])
            nb = sum(x.stat().st_size for x in paths)
            return SpillItem(tuple(paths), table, "n", rows, len(rows), nb)
        return None

    def _load(self, p: Path):
        try:
            return pickle.loads(p.read_bytes())
        except Exception:  # noqa: BLE001 — file cụt/hỏng: dạt sang bên, có đếm
            self.counters["replay_corrupt"] += 1
            size = p.stat().st_size           # lấy trước khi rename — sau đó tên đã đổi
            p.rename(p.with_suffix(".corrupt"))
            self.bytes_used -= size           # file rời khỏi hàng đợi — không còn tính vào trần
            log.error("spill: file hỏng %s — dạt sang .corrupt", p.name)
            return None

    def delete(self, item: SpillItem) -> None:
        for p in item.paths:
            self.bytes_used -= p.stat().st_size
            p.unlink()
