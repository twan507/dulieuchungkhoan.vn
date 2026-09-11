"""Hợp đồng lint: toàn repo phải sạch ruff (E4/E7/E9/F/I).

Vì: mục 7 bảng câu hỏi trước lát 12, chốt 2026-09-11 — thêm ruff làm lint tối
thiểu, gác bằng test hợp đồng thay vì chỉ chạy tay. Bộ luật hẹp có chủ đích:
E4/E7/E9 (lỗi rõ ràng), F (pyflakes — unused import/var, undefined name...),
I (isort — thứ tự import). Không bật E501 (chiều dài dòng) hay các rule style
khác.

Bẫy đã trả giá (ledger 2026-09-07 audit): NEVER chạy `ruff --unsafe-fixes`.
Riêng F841 (biến gán mà không dùng) phải tự đọc code rồi sửa tay — biến đó có
thể load-bearing (side effect, hoặc dùng để giữ tham chiếu). Không đoán, không
để `--unsafe-fixes` xoá hộ.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ruff_clean_across_repo():
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
    assert result.returncode == 0
