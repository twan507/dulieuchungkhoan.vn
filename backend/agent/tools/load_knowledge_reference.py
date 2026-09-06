"""Function thứ 9 — cửa duy nhất để model đọc tri thức L2.

topic tra dict hằng L2_TOPICS rồi mới ra Path; không nối chuỗi từ đầu vào nên path traversal
không khả dĩ về mặt cấu trúc, không phải nhờ lọc ký tự. Chủ đề lạ trả LỖI CÓ CẤU TRÚC (không
ném) để model tự sửa mà không phá vòng chat.
"""
from __future__ import annotations

from agent.skills import L2_TOPICS, load_l2
from agent.tools._shared import to_json


def doc_tri_thuc(topic: str) -> str:
    if topic not in L2_TOPICS:
        return to_json({"loi": True, "ly_do": f"khong co chu de '{topic}'",
                        "chu_de_hop_le": sorted(L2_TOPICS)})
    return to_json({"chu_de": topic, "noi_dung": load_l2(topic)})
