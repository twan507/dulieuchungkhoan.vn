"""Seam S3 và S5 — thứ tự tri thức và cửa đọc L2.

Lỗ hổng phạm vi đo được ở vòng 5 test skill: 3/4 câu ngoài lĩnh vực vẫn được trả lời đầy đủ,
vì luật "chỉ trả lời chứng khoán" nằm TRONG thân SKILL.md, chỉ đọc được SAU khi skill tải.
Bản vá là đoạn văn nguyên văn ở docs/30-skills/maintenance.md §7, phải nằm ở system prompt.
"""
import pytest

from agent.skills import L2_TOPICS, load_l1, load_l2
from agent.system_prompt import ANSWER_RULES, SCOPE_GUARD, build_system_blocks


def test_scope_guard_chep_nguyen_van_tu_maintenance():
    assert "chỉ trả lời trong lĩnh vực chứng khoán, tài chính và kinh tế" in SCOPE_GUARD
    assert "nửa trong nửa ngoài" in SCOPE_GUARD


def test_block_dau_tien_la_scope_guard():
    blocks = build_system_blocks()
    assert len(blocks) == 4
    assert blocks[0]["text"] == SCOPE_GUARD


def test_block_thu_hai_la_l1_tron_ven_khong_lan_l2():
    l1 = build_system_blocks()[1]["text"]
    # Tiêu đề H1 thật của SKILL.md (đọc trực tiếp file 2026-09-07): "# Cố vấn chứng khoán Việt Nam".
    assert "# Cố vấn chứng khoán Việt Nam" in l1
    assert "analysis-framework" in l1        # tiêu đề phân cách của file reference
    assert "writing-style" in l1
    assert "valuation" not in l1.lower()     # L2 KHÔNG được lọt vào system


def test_l1_du_do_dai_da_do():
    """61.240 ký tự nội dung 5 file (đo 2026-09-07); nối thêm tiêu đề phân cách nên lớn hơn."""
    assert len(load_l1()) >= 61_240


def test_l2_du_chin_chu_de():
    assert len(L2_TOPICS) == 9
    assert "valuation" in L2_TOPICS and "financial-statements" in L2_TOPICS


def test_l2_tra_dung_noi_dung():
    assert "FCFF" in load_l2("valuation")


def test_l2_tu_choi_path_traversal():
    with pytest.raises(KeyError):
        load_l2("../../../etc/passwd")
    with pytest.raises(KeyError):
        load_l2("valuation.md")


def test_khoi_luat_cong_cu_neo_ngay_va_bat_tra_truoc_khi_phu_dinh():
    """Đo 2026-09-07: hỏi CPI tháng 8/2026, model KHÔNG gọi công cụ mà nói "ngoài dữ liệu của
    tôi (tháng 1/2026)" — sai, vì kho có đúng số đó. Khối luật này neo ngày và bắt tra trước."""
    import datetime as dt

    from agent.system_prompt import build_tool_rules

    luat = build_tool_rules(dt.date(2026, 9, 7))
    assert "07/09/2026" in luat
    assert "BẮT BUỘC gọi công cụ" in luat


def test_khoi_luat_cong_cu_dung_CUOI_de_khong_pha_tien_to_cache():
    """MiniMax cache theo tiền tố: khối mang ngày thay đổi mỗi ngày phải đứng sau hai khối lớn."""
    import datetime as dt

    blocks = build_system_blocks(dt.date(2026, 9, 7))
    assert "07/09/2026" in blocks[3]["text"]
    assert "07/09/2026" not in blocks[0]["text"] + blocks[1]["text"] + blocks[2]["text"]


def test_bon_block_dung_thu_tu_va_answer_rules_dung_thu_ba():
    """Luật trình bày phải là block RIÊNG, không nhét vào khối luật công cụ.

    Vòng 7: hình dạng 13/15, ngưỡng 14. Câu A4b bịa dải nhạy 23.500–32.500 (đúng là
    ~24.643–30.962) vì luật "số dẫn xuất phải kèm phép tính" mới chỉ có ở RUBRIC CHẤM.
    """
    blocks = build_system_blocks()
    assert len(blocks) == 4
    assert blocks[0]["text"] == SCOPE_GUARD
    assert blocks[2]["text"] == ANSWER_RULES
