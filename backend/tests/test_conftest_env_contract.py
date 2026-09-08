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

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
CONFTEST = TESTS / "conftest.py"
BACKEND = TESTS.parent


def _root_conftest():
    """Nạp `tests/conftest.py` bằng ĐƯỜNG DẪN tường minh, không qua `import conftest`.

    🔴 `sys.modules['conftest']` không đáng tin khi chạy CẢ BỘ: bốn `conftest.py` (`tests/`,
    `tests/agent/`, `tests/clickhouse/`, `tests/ingester/`) không nằm trong package (không
    `__init__.py`) nên pytest coi mỗi file là module TRẦN cùng tên `conftest` — file nạp SAU CÙNG
    trong thứ tự thu thập đè `sys.modules['conftest']`. Đo được 2026-09-08: `pytest tests/
    test_conftest_env_contract.py` một mình thì `from conftest import assert_test_db_name` chạy
    đúng, nhưng `pytest tests -q` (cả bộ) cho `ImportError: cannot import name 'assert_test_db_name'
    from 'conftest' (.../tests/ingester/conftest.py)` — đúng bẫy mà chính file này đã cảnh báo ở
    docstring đầu file, lần này cắn vào một test MỚI thêm sau.
    """
    spec = importlib.util.spec_from_file_location("_dlck_root_conftest_probe", CONFTEST)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_assert_test_db_name_rejects_test_db_equal_to_prod_db():
    """Tên DB test nay đến từ `.env` (`POSTGRES_TEST_DB`), không còn là hằng số `dulieu_test` trong
    code — regex 'là identifier sạch' không đủ để khoá bán kính `DROP DATABASE ... WITH (FORCE)`."""
    with pytest.raises(AssertionError):
        _root_conftest().assert_test_db_name("dulieu", "dulieu")


def test_assert_test_db_name_rejects_a_name_without_the_test_suffix():
    with pytest.raises(AssertionError):
        _root_conftest().assert_test_db_name("dulieu_prod", "dulieu")


def test_assert_test_db_name_accepts_a_proper_test_db_name():
    """Ca dương phải khẳng định một GIÁ TRỊ, không chỉ "không raise" — một thân hàm rỗng cũng không
    raise, nên phép kiểm cũ vẫn xanh sau khi ai đó xoá sạch ba điều kiện (nit re-review 2026-09-08).
    Hàm trả lại chính tên đã kiểm, và `conftest` dùng GIÁ TRỊ TRẢ VỀ đó để ghép câu DDL."""
    assert _root_conftest().assert_test_db_name("dulieu_test", "dulieu") == "dulieu_test"
