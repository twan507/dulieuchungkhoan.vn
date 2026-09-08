"""Không còn `date.today()` / `datetime.now()` trần trong code sản phẩm (spec lát 12 §5.6 lớp 3).

Container mặc định UTC; mọi phép "hôm nay" phải đi qua `core.clock` hoặc `ZoneInfo` tường minh.
Kiểm TĨNH trên mã nguồn, `backend/` ngoài `tests/`.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCAN = [REPO / "backend" / d for d in ("core", "etl", "ingester", "agent", "api")]
OWNERS = {"date", "datetime"}        # `date.today()`, và cả `dt.date` / `datetime.datetime`
METHODS = {"today", "now", "utcnow"}


def _is_bare(call: ast.Call) -> bool:
    """Lời gọi "bây giờ" KHÔNG nêu múi giờ. `now(VN)` / `now(tz=VN)` không tính: nêu múi giờ tường
    minh là đúng cách, bắt luôn cả nó thì phép kiểm thành báo động giả. `today`/`utcnow` không nhận
    tham số tz nên luôn tính."""
    f = call.func
    if not isinstance(f, ast.Attribute) or f.attr not in METHODS:
        return False
    owner = f.value
    name = owner.id if isinstance(owner, ast.Name) else getattr(owner, "attr", None)
    if name not in OWNERS:
        return False
    if f.attr == "now":
        return not call.args and not any(k.arg == "tz" for k in call.keywords)
    return True


def _bare_calls(tree: ast.AST) -> list[ast.Call]:
    """Mọi lời gọi trần trong một cây đã parse (Chuẩn M4 — trước 2026-09-08 là regex trên từng dòng).

    Duyệt AST bắt theo CẤU TRÚC: `dt.date.today()` và `datetime.datetime.now()` không còn phụ thuộc
    việc mẫu regex có tình cờ khớp phần đuôi hay không, lời gọi vắt qua nhiều dòng vẫn thấy, và
    chuỗi/docstring/comment nói VỀ `date.today()` không bao giờ tính là hit."""
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call) and _is_bare(n)]


def scan_bare_calls(root: Path) -> list[str]:
    """Quét mọi `*.py` dưới `root`, trả các dòng có lời gọi trần, dạng
    `<đường dẫn tương đối root>:<số dòng>: <nội dung>`. Seam test âm — không có DB, không mock."""
    hits: list[str] = []
    for p in sorted(root.rglob("*.py")):
        lines = p.read_text(encoding="utf-8").splitlines()
        for call in _bare_calls(ast.parse("\n".join(lines), filename=str(p))):
            hits.append(f"{p.relative_to(root).as_posix()}:{call.lineno}: {lines[call.lineno - 1].strip()}")
    return hits


def test_bare_call_detector_catches_the_known_bad_shapes():
    """Đối chứng dương (Chuẩn I4/T2a) — một bộ quét hỏng cũng cho `hits == []`; phải tự bắt được
    các hình dạng tái diễn thật trước khi tin `assert not hits` ở dưới. Mẫu là chuỗi parse thành
    module, không phải file trên đĩa: giữ đối chứng độc lập với cây repo."""
    for src in ("x = date.today()", "datetime.now()", "dt.date.today()",
                "datetime.datetime.now()", "datetime.utcnow()"):
        assert len(_bare_calls(ast.parse(src))) == 1, src


def test_a_call_that_names_its_timezone_is_not_a_hit():
    """`datetime.now(VN)` là ĐÚNG cách. Bắt luôn cả nó thì phép kiểm thành báo động giả — thứ dạy
    người sau tắt phép kiểm. Regex cũ né được ca này chỉ vì ghim cặp ngoặc RỖNG."""
    for src in ("datetime.now(VN)", "datetime.now(tz=VN)",
                "dt.datetime.now(ZoneInfo('Asia/Ho_Chi_Minh'))"):
        assert _bare_calls(ast.parse(src)) == [], src


def test_prose_naming_date_today_is_not_a_hit():
    """Chuỗi/docstring NÓI VỀ `date.today()` không phải lời gọi. Regex cũ chỉ né được dòng mở đầu
    bằng `#`; một docstring cảnh báo đúng chuyện này lại tự làm phép kiểm đỏ."""
    assert _bare_calls(ast.parse('S = "đừng gọi date.today() trong container UTC"')) == []


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
