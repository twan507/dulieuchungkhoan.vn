"""Không còn `date.today()` / `datetime.now()` trần trong code sản phẩm (spec lát 12 §5.6 lớp 3).

Container mặc định UTC; mọi phép "hôm nay" phải đi qua `core.clock` hoặc `ZoneInfo` tường minh.
Kiểm TĨNH trên mã nguồn, `backend/` ngoài `tests/`.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCAN = [REPO / "backend" / d for d in ("core", "etl", "ingester", "agent", "api")]
BARE = re.compile(r"\b(?:date|datetime)\.today\(\)|\bdatetime\.utcnow\(\)|\bdatetime\.now\(\s*\)")


def test_no_bare_today_or_now_in_product_code():
    hits, n_files = [], 0
    for d in SCAN:
        for p in sorted(d.rglob("*.py")):
            n_files += 1
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if BARE.search(line) and not line.lstrip().startswith("#"):
                    hits.append(f"{p.relative_to(REPO).as_posix()}:{i}: {line.strip()}")
    assert n_files >= 60, f"chỉ quét {n_files} file — nghi phạm vi hụt"
    assert not hits, "ngày/giờ trần, sẽ lệch trong container UTC:\n  " + "\n  ".join(hits)
