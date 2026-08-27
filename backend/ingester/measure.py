"""Ghi frame thô chế độ đo — JSONL xoay theo giờ VN, gzip khi đóng (spec §3.5)."""
from __future__ import annotations

import gzip
import json
import re
import shutil
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Ho_Chi_Minh")

# Chính sách giữ bản đo thô (roadmap §2.1, đo 2026-08-27): ~93 MB gzip/ngày,
# giữ 30 ngày ≈ 2,8 GB — đĩa VPS 60 GB không gánh nổi vô thời hạn.
KEEP_DAYS = 30


def prune_old(root: Path, keep_days: int = KEEP_DAYS, today: date | None = None) -> list[str]:
    """Xoá thư mục đo tên YYYYMMDD quá `keep_days` ngày; trả về tên đã xoá (sorted)."""
    cutoff = (today or datetime.now(TZ).date()) - timedelta(days=keep_days)
    removed: list[str] = []
    for p in sorted(Path(root).iterdir()):
        if not (p.is_dir() and re.fullmatch(r"\d{8}", p.name)):
            continue
        try:
            d = datetime.strptime(p.name, "%Y%m%d").date()
        except ValueError:
            continue
        if d < cutoff:
            shutil.rmtree(p)
            removed.append(p.name)
    return removed


class MeasureWriter:
    def __init__(self, out_dir: Path, clock=time.time):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self._fh = None
        self._path: Path | None = None
        self._hour: str | None = None

    def _rotate(self, now: float) -> None:
        hour = datetime.fromtimestamp(now, tz=TZ).strftime("%Y%m%d-%H")
        if hour == self._hour:
            return
        self._gzip_current()
        self._hour = hour
        self._path = self.out_dir / f"frames-{hour}.jsonl"
        self._fh = self._path.open("a", encoding="utf-8")

    def _gzip_current(self) -> None:
        if self._fh is None:
            return
        self._fh.close()
        with self._path.open("rb") as src, gzip.open(f"{self._path}.gz", "wb") as dst:
            shutil.copyfileobj(src, dst)
        self._path.unlink()
        self._fh = None

    def write(self, received_at_ms: int, packet: str) -> None:
        self._rotate(self.clock())
        self._fh.write(json.dumps({"r": received_at_ms, "p": packet}, ensure_ascii=False) + "\n")

    def close(self) -> None:
        self._gzip_current()
