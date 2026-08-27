"""Config ingester — env qua core.env; thiếu biến bắt buộc là thoát lỗi rõ (spec §2.1)."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from core.env import REPO_ROOT, load_dotenv


@dataclass(frozen=True)
class Config:
    clickhouse_url: str
    redis_url: str
    log_dir: Path
    measure_dir: Path
    spill_dir: Path


def load(need_db: bool) -> Config:
    load_dotenv()
    ch = os.environ.get("CLICKHOUSE_INGESTER_URL", "")
    rd = os.environ.get("REDIS_URL", "")
    if need_db:
        missing = [k for k, v in (("CLICKHOUSE_INGESTER_URL", ch), ("REDIS_URL", rd)) if not v]
        if missing:
            print(f"ingester: thiếu env bắt buộc: {', '.join(missing)}", file=sys.stderr)
            raise SystemExit(2)
    runtime = REPO_ROOT.parent / "dlck-runtime"
    log_dir = Path(os.environ.get("INGESTER_LOG_DIR") or runtime / "logs")
    measure_dir = Path(os.environ.get("INGESTER_MEASURE_DIR") or runtime / "measure")
    spill_dir = Path(os.environ.get("INGESTER_SPILL_DIR") or runtime / "spill")
    # Ba `mkdir` này ném `OSError` được (ổ chỉ đọc, quyền sai, biến env trỏ vào chỗ không
    # tạo được) và chạy TRƯỚC mọi thứ khác — để nó thoát ra thì thành traceback trần exit
    # 1, đi vòng đúng hợp đồng "thiếu điều kiện khởi động ⇒ exit 2" mà chính hàm này dựng
    # ra ở nhánh thiếu env bên trên.
    for d in (log_dir, measure_dir, spill_dir):
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"ingester: không tạo được thư mục {d}: {e}", file=sys.stderr)
            raise SystemExit(2) from e
    return Config(ch, rd, log_dir, measure_dir, spill_dir)
