"""Mọi nhánh trả 1 (chốt chặn từ chối / nguồn chết) phải đóng sổ bằng `close_run_refused` để planner lát 13 đọc
`stats.guard_refused` mà không so chuỗi `error` (spec §5.8). Quét tĩnh, cùng tinh thần test_e65 vế 2."""
import re
from pathlib import Path

ETL = Path(__file__).resolve().parents[2] / "etl"
RETURN_1 = re.compile(r"^\s+return 1\s*(#.*)?$")
DRY_RUN_FORM = re.compile(r"return 0 if .* else 1")


def _violations():
    out = []
    for py in sorted(ETL.glob("*.py")):
        lines = py.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if RETURN_1.match(line) and not DRY_RUN_FORM.search(line):
                window = "\n".join(lines[max(0, i - 8):i])
                if "close_run_refused(" not in window:
                    out.append(f"{py.name}:{i + 1}")
    return out


def test_every_exit_1_closes_the_run_as_refused():
    assert _violations() == [], "nhánh trả 1 không đi qua close_run_refused: " + ", ".join(_violations())


def test_scanner_sees_the_known_exit_1_sites():
    names = {v.split(":")[0] for v in _violations()} | {p.name for p in ETL.glob("*_job.py")}
    assert {"refdata_job.py", "price_job.py", "series_job.py"} <= names      # đối chứng dương: quét đúng thư mục
