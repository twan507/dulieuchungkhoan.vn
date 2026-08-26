"""Ghi frame thô chế độ đo — JSONL xoay theo giờ VN, gzip khi đóng (spec §3.5)."""
from __future__ import annotations

import gzip
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Ho_Chi_Minh")


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
