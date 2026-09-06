"""Nạp tri thức skill từ đĩa.

L1 (vn-stock-advisor) nạp TRỌN lúc khởi động và đi vào system prompt — nó quyết định HÌNH DẠNG
câu trả lời nên phải có mặt trước mọi tool_result. L2 (vn-stock-knowledge) nạp THEO NHU CẦU qua
function, vì trọn bộ là 243.545 ký tự ≈ 150k token.

Bảng L2_TOPICS là dict HẰNG: topic tra thẳng ra Path, không nối chuỗi từ đầu vào ⇒ path
traversal không khả dĩ về mặt cấu trúc.
"""
from __future__ import annotations

from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent / "skills"
L1_DIR = SKILLS_DIR / "vn-stock-advisor"
L2_DIR = SKILLS_DIR / "vn-stock-knowledge"

L1_FILES = [
    L1_DIR / "SKILL.md",
    L1_DIR / "references" / "analysis-framework.md",
    L1_DIR / "references" / "market-behavior.md",
    L1_DIR / "references" / "reasoning.md",
    L1_DIR / "references" / "writing-style.md",
]

L2_TOPICS: dict[str, Path] = {
    "tong-quan": L2_DIR / "SKILL.md",
    "advanced": L2_DIR / "references" / "advanced.md",
    "financial-statements": L2_DIR / "references" / "financial-statements.md",
    "macro-money-creation": L2_DIR / "references" / "macro-money-creation.md",
    "portfolio-and-rotation": L2_DIR / "references" / "portfolio-and-rotation.md",
    "psychology-information": L2_DIR / "references" / "psychology-information.md",
    "technical-indicators": L2_DIR / "references" / "technical-indicators.md",
    "technical-supply-demand": L2_DIR / "references" / "technical-supply-demand.md",
    "valuation": L2_DIR / "references" / "valuation.md",
}


def load_l1() -> str:
    """Thiếu file thì chết ngay — thà không chạy còn hơn chạy với skill khuyết."""
    parts = []
    for p in L1_FILES:
        if not p.is_file():
            raise RuntimeError(f"thieu file skill L1: {p.name}")
        parts.append(f"\n\n===== {p.stem} =====\n\n" + p.read_text(encoding="utf-8"))
    return "".join(parts).strip()


def load_l2(topic: str) -> str:
    path = L2_TOPICS[topic]          # KeyError cho mọi thứ ngoài 9 khoá — đúng ý
    return path.read_text(encoding="utf-8")
