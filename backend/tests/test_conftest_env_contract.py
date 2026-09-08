"""`tests/conftest.py` phải TỰ nạp `.env`, không ăn ké tác dụng phụ của module khác.

🔴 Vì sao file này ra đời (rà chuẩn hoá 2026-09-08). `migrated_engine` đọc
`os.environ["TEST_DATABASE_URL"]`, mà tới lúc đó **không gì trong `tests/` nạp `.env`**. Cả bộ
vẫn xanh — nhờ `tests/agent/test_a14_startup.py` `import agent.__main__`, và file đó gọi
`load_dotenv()` **lúc import**; `tests/agent` đứng đầu bảng chữ cái nên mọi test sau được ăn ké.

Hai hậu quả đo được cùng ngày:

* `uv run pytest tests -q` → 1.070 passed, nhưng `uv run pytest tests/etl -q` → **KeyError**.
  Chạy một phần bộ test — thứ làm suốt lúc phát triển — đỏ vì lý do không liên quan gì tới test.
* Dòng roadmap *"thiếu `--env-file` là 425 error"* thành **sai** mà không ai đổi gì có chủ đích:
  test canh đường khởi động của lát 11 vô tình vá nó.

Sợi dây này mảnh đúng kiểu nguy hiểm: đổi tên `test_a14_startup.py`, bỏ dòng `import
agent.__main__`, hay chỉ cần thêm một thư mục test sắp trước `agent` **và** chạy `-k` lọc bỏ nó
— là ~400 test đỏ bằng `KeyError`, một triệu chứng không gợi chút nào về nguyên nhân.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
CONFTEST = TESTS / "conftest.py"
BACKEND = TESTS.parent


def test_conftest_tu_nap_dotenv_truoc_khi_doc_bien():
    src = CONFTEST.read_text(encoding="utf-8")
    assert "load_dotenv()" in src, (
        "tests/conftest.py không tự nạp .env — nó đang phụ thuộc vào việc một module test khác "
        "tình cờ nạp hộ, và thứ tự thu thập của pytest quyết định điều đó")
    assert src.index("load_dotenv()") < src.index('os.environ["TEST_DATABASE_URL"]'), (
        "load_dotenv() phải chạy TRƯỚC lần đọc TEST_DATABASE_URL đầu tiên")


def test_dotenv_that_su_cung_cap_bien_khi_shell_khong_co():
    """Vế hành vi: trong tiến trình SẠCH (đã xoá biến khỏi môi trường), `load_dotenv()` một
    mình phải đủ. Kiểm bằng tiến trình con chứ không phải trong phiên này — phiên này đã có
    biến rồi nên không quan sát được gì.

    Tiến trình con **không in giá trị** (CLAUDE.md §5), chỉ in có/không.
    """
    moi_truong = {k: v for k, v in os.environ.items() if k != "TEST_DATABASE_URL"}
    r = subprocess.run(
        [sys.executable, "-c",
         "import os;"
         "from core.env import load_dotenv;"
         "load_dotenv();"
         "print('CO' if os.environ.get('TEST_DATABASE_URL') else 'KHONG')"],
        cwd=BACKEND, env=moi_truong, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "CO", (
        f"load_dotenv() một mình không dựng được TEST_DATABASE_URL (nhận {r.stdout.strip()!r}) "
        "— hoặc .env gốc repo thiếu biến, hoặc REPO_ROOT của core.env trỏ sai")
