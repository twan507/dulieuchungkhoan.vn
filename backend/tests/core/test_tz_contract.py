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


def scan_bare_calls(root: Path) -> list[str]:
    """Quét mọi `*.py` dưới `root`, trả các dòng khớp `BARE` (bỏ dòng comment), dạng
    `<đường dẫn tương đối root>:<số dòng>: <nội dung>`. Seam test âm — không có DB, không mock."""
    hits: list[str] = []
    for p in sorted(root.rglob("*.py")):
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if BARE.search(line) and not line.lstrip().startswith("#"):
                hits.append(f"{p.relative_to(root).as_posix()}:{i}: {line.strip()}")
    return hits


def test_bare_regex_catches_the_known_bad_shapes():
    """Đối chứng dương (Chuẩn I4/T2a) — một bộ quét hỏng cũng cho `hits == []`; phải tự bắt được
    ít nhất hai hình dạng tái diễn thật trước khi tin `assert not hits` ở dưới."""
    assert BARE.search("x = date.today()")
    assert BARE.search("datetime.now()")


def test_scan_bare_calls_catches_a_seeded_violation(tmp_path):
    """Seam spec §6: chèn `date.today()` vào một file tạm trong phạm vi ⇒ phải đỏ, nêu tên file."""
    f = tmp_path / "somefile.py"
    f.write_text("d = date.today()\n", encoding="utf-8")
    hits = scan_bare_calls(tmp_path)
    assert len(hits) == 1
    assert "somefile.py" in hits[0]


def test_no_bare_today_or_now_in_product_code():
    hits: list[str] = []
    n_files = 0
    for d in SCAN:
        n_files += sum(1 for _ in d.rglob("*.py"))
        prefix = d.relative_to(REPO).as_posix()
        hits.extend(f"{prefix}/{h}" for h in scan_bare_calls(d))
    assert n_files >= 60, f"chỉ quét {n_files} file — nghi phạm vi hụt"
    assert not hits, "ngày/giờ trần, sẽ lệch trong container UTC:\n  " + "\n  ".join(hits)
