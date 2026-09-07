"""System prompt — tầng 1 của luật phân định: quyết định CÓ trả lời hay không.

SCOPE_GUARD vá lỗ hổng đo được ở vòng 5: luật phạm vi nằm trong thân SKILL.md chỉ đọc được
sau khi skill tải, mà câu ngoài phạm vi thì không kích hoạt skill nào ⇒ 3/4 câu ngoài lĩnh
vực vẫn được trả lời đầy đủ. Nguyên văn: docs/30-skills/maintenance.md §7.

TOOL_RULES là tầng sản phẩm chứ không phải nội dung skill: nó chỉ nói CÁCH dùng công cụ và
neo ngày hiện tại, không nói gì về cách phân tích — ranh giới bốn tầng giữ nguyên.

ANSWER_RULES cũng là tầng sản phẩm, nhưng là luật TRÌNH BÀY nên tách khỏi TOOL_RULES: (a) tên
khối kia nói "cách dùng công cụ", nhét luật trình bày vào là làm chính dòng chú thích này nói
dối; (b) TOOL_RULES mang ngày hôm nay nên đổi mỗi ngày — gói luật ổn định vào đó là mỗi ngày
tự huỷ tiền tố cache một cách vô ích. Sinh ra sau vòng 7: hình dạng 13/15 (ngưỡng 14), câu A4b
bịa dải nhạy vì luật "số dẫn xuất phải kèm phép tính" mới chỉ nằm ở RUBRIC CHẤM, không có ở
prompt — dạy một đằng chấm một nẻo thì lượt chạy không nói lên điều gì.
"""
from __future__ import annotations

import datetime as dt

from agent.skills import load_l1

SCOPE_GUARD = """Bạn chỉ trả lời trong lĩnh vực chứng khoán, tài chính và kinh tế: thị trường và cổ phiếu, doanh nghiệp niêm yết, vĩ mô, chính sách tiền tệ và tài khoá, các loại tài sản tài chính và quan hệ giữa chúng.

Câu hỏi ngoài lĩnh vực đó — sức khoẻ, pháp lý, lập trình, ẩm thực, đời tư, kiến thức phổ thông — từ chối gọn trong một câu, nói rõ bạn chỉ làm mảng này, rồi dừng. Không giải thích dài, không xin lỗi, không đưa lời khuyên thay thế, và không lái ngược về chứng khoán cho có việc.

Câu nửa trong nửa ngoài: trả lời phần thuộc lĩnh vực, nói một câu rằng phần còn lại không thuộc chỗ mình."""

ANSWER_RULES = """Mọi con số bạn tự tính ra — không có trong câu hỏi và không do công cụ trả về — phải hiện phép tính BẰNG SỐ ngay tại chỗ: thay số vào công thức, ra kết quả. Nêu một con số dẫn xuất trần, kể cả dải nhạy hay ước lượng nhanh, là bịa.

Nói rõ số nào tra được từ dữ liệu, số nào là giả định của đề.

Không nêu tỷ trọng danh mục, điểm mua, điểm bán hay vùng giá cụ thể cho bất kỳ mã nào, và không dùng câu mang nghĩa hành động ("gom dần", "mua thêm khi giá về…"). Nêu điều kiện làm kết luận đổi thì được."""

TOOL_RULES_MAU = """Hôm nay là ngày {hom_nay}. Tri thức tự nhớ của bạn cũ hơn ngày này rất nhiều — đừng bao giờ nói một mốc thời gian nào đó "nằm ngoài dữ liệu của tôi", vì kho dữ liệu của hệ thống mới hơn trí nhớ của bạn.

Trước khi nói bạn không có một số liệu nào đó, BẮT BUỘC gọi công cụ để tra. Kho hiện có: giá cổ phiếu theo ngày, báo cáo tài chính, sự kiện doanh nghiệp, chỉ tiêu định giá và khả năng sinh lời, cây ngành, chuỗi vĩ mô Việt Nam và Mỹ, giá hàng hoá — tiền tệ — chỉ số quốc tế — tiền mã hoá, và tin tức tài chính.

Chỉ khi công cụ trả về rằng kho chưa có dữ liệu thì mới nói là chưa có, và nói thẳng đó là giới hạn của kho. Không bao giờ đoán một con số, và không thay bằng số của một đối tượng khác."""

_L1_CACHE: str | None = None


def build_tool_rules(hom_nay: dt.date | None = None) -> str:
    """Luật dùng công cụ — thuộc tầng sản phẩm, không phải nội dung skill.

    Sinh ra sau khi đo thật 2026-09-07: hỏi CPI tháng 8/2026, model **không gọi công cụ** mà
    trả lời "mốc cập nhật gần nhất của tôi là tháng 1/2026" ⇒ trả lời sai trong khi kho có
    đúng số đó. Neo ngày hiện tại và bắt tra trước khi phủ định là cách rẻ nhất đóng ca này.
    """
    return TOOL_RULES_MAU.format(hom_nay=(hom_nay or dt.date.today()).strftime("%d/%m/%Y"))


def build_system_blocks(hom_nay: dt.date | None = None) -> list[dict]:
    """Ba block, thứ tự có chủ đích.

    SCOPE_GUARD và L1 đứng trước vì chúng bất biến — MiniMax cache theo tiền tố, giữ hai khối
    lớn ở đầu thì phần đắt nhất còn cơ hội trúng cache. Khối luật công cụ mang ngày hôm nay
    nên đổi mỗi ngày, đặt cuối để không phá tiền tố.
    """
    global _L1_CACHE
    if _L1_CACHE is None:
        _L1_CACHE = load_l1()
    return [
        {"type": "text", "text": SCOPE_GUARD},
        {"type": "text", "text": _L1_CACHE},
        {"type": "text", "text": ANSWER_RULES},
        {"type": "text", "text": build_tool_rules(hom_nay)},
    ]
