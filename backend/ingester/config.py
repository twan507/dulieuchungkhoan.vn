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
    log_dir.mkdir(parents=True, exist_ok=True)
    measure_dir.mkdir(parents=True, exist_ok=True)
    spill_dir.mkdir(parents=True, exist_ok=True)
    return Config(ch, rd, log_dir, measure_dir, spill_dir)
