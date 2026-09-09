"""Mọi nhánh trả 1 (chốt chặn từ chối / nguồn chết) phải đóng sổ bằng `close_run_refused` để planner lát 13 đọc
`stats.guard_refused` mà không so chuỗi `error` (spec §5.8). Quét tĩnh, cùng tinh thần test_e65 vế 2."""
import re
from pathlib import Path

ETL = Path(__file__).resolve().parents[2] / "etl"
RETURN_1 = re.compile(r"^\s+return 1\s*(#.*)?$")
DRY_RUN_FORM = re.compile(r"return 0 if .* else 1")
NO_RUN = re.compile(r"#\s*no-run:")


def _violations_in(lines: list[str], name: str) -> list[str]:
    """Quét thuần một danh sách dòng (không đụng đĩa) — dùng lại cho cả file thật lẫn test đối chứng."""
    out = []
    for i, line in enumerate(lines):
        if not RETURN_1.match(line) or DRY_RUN_FORM.search(line):
            continue
        if NO_RUN.search(line) or (i > 0 and NO_RUN.search(lines[i - 1])):
            continue                                    # nhánh cố ý không mở sổ (vd dry-run) — đánh dấu tường minh
        window_lines = [w for w in lines[max(0, i - 8):i] if not w.strip().startswith("#")]
        window = "\n".join(window_lines)
        if "close_run_refused(" not in window:
            out.append(f"{name}:{i + 1}")
    return out


def _violations():
    out = []
    for py in sorted(ETL.glob("*.py")):
        out.extend(_violations_in(py.read_text(encoding="utf-8").splitlines(), py.name))
    return out


def test_every_exit_1_closes_the_run_as_refused():
    assert _violations() == [], "nhánh trả 1 không đi qua close_run_refused: " + ", ".join(_violations())


def test_flags_return_1_with_no_close_run_refused_nearby():
    lines = ["def f():", "    x = 1", "    return 1"]
    assert _violations_in(lines, "x.py") == ["x.py:3"]


def test_does_not_flag_when_close_run_refused_two_lines_above():
    lines = [
        "def f():",
        '    omo_store.close_run_refused(engine, run_id, "x")',
        "    log.error('x')",
        "    return 1",
    ]
    assert _violations_in(lines, "x.py") == []


def test_close_run_refused_mentioned_only_in_comment_still_flags():
    lines = [
        "def f():",
        "    # close_run_refused( được nhắc trong chú thích",
        "    return 1",
    ]
    assert _violations_in(lines, "x.py") == ["x.py:3"]


def test_no_run_marker_exempts():
    lines = ["def f():", "    return 1  # no-run: dry-run, run_id=None"]
    assert _violations_in(lines, "x.py") == []


def test_dry_run_shape_exempts():
    lines = ["def f():", "    return 0 if verdict.ok else 1"]
    assert _violations_in(lines, "x.py") == []
