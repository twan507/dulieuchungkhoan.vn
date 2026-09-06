"""Seam S3 và S5 — thứ tự tri thức và cửa đọc L2.

Lỗ hổng phạm vi đo được ở vòng 5 test skill: 3/4 câu ngoài lĩnh vực vẫn được trả lời đầy đủ,
vì luật "chỉ trả lời chứng khoán" nằm TRONG thân SKILL.md, chỉ đọc được SAU khi skill tải.
Bản vá là đoạn văn nguyên văn ở docs/30-skills/maintenance.md §7, phải nằm ở system prompt.
"""
import pytest

from agent.skills import L2_TOPICS, load_l1, load_l2
from agent.system_prompt import SCOPE_GUARD, build_system_blocks


def test_scope_guard_chep_nguyen_van_tu_maintenance():
    assert "chỉ trả lời trong lĩnh vực chứng khoán, tài chính và kinh tế" in SCOPE_GUARD
    assert "nửa trong nửa ngoài" in SCOPE_GUARD


def test_block_dau_tien_la_scope_guard():
    blocks = build_system_blocks()
    assert len(blocks) == 2
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
