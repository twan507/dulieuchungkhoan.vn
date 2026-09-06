"""System prompt — tầng 1 của luật phân định: quyết định CÓ trả lời hay không.

SCOPE_GUARD vá lỗ hổng đo được ở vòng 5: luật phạm vi nằm trong thân SKILL.md chỉ đọc được
sau khi skill tải, mà câu ngoài phạm vi thì không kích hoạt skill nào ⇒ 3/4 câu ngoài lĩnh
vực vẫn được trả lời đầy đủ. Nguyên văn: docs/30-skills/maintenance.md §7.
"""
from __future__ import annotations

from agent.skills import load_l1

SCOPE_GUARD = """Bạn chỉ trả lời trong lĩnh vực chứng khoán, tài chính và kinh tế: thị trường và cổ phiếu, doanh nghiệp niêm yết, vĩ mô, chính sách tiền tệ và tài khoá, các loại tài sản tài chính và quan hệ giữa chúng.

Câu hỏi ngoài lĩnh vực đó — sức khoẻ, pháp lý, lập trình, ẩm thực, đời tư, kiến thức phổ thông — từ chối gọn trong một câu, nói rõ bạn chỉ làm mảng này, rồi dừng. Không giải thích dài, không xin lỗi, không đưa lời khuyên thay thế, và không lái ngược về chứng khoán cho có việc.

Câu nửa trong nửa ngoài: trả lời phần thuộc lĩnh vực, nói một câu rằng phần còn lại không thuộc chỗ mình."""

_L1_CACHE: str | None = None


def build_system_blocks() -> list[dict]:
    global _L1_CACHE
    if _L1_CACHE is None:
        _L1_CACHE = load_l1()
    return [
        {"type": "text", "text": SCOPE_GUARD},
        {"type": "text", "text": _L1_CACHE},
    ]
