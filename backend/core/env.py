"""Nạp .env gốc repo — cho tiến trình chạy từ Task Scheduler không kế thừa shell env.

Không đè biến đã có; không bao giờ in giá trị (CLAUDE.md §5).
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_dotenv(path: Path | None = None) -> None:
    p = path or (REPO_ROOT / ".env")
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())
