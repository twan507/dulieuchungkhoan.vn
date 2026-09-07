"""Bảng nhãn ĐÓNG cho tập chỉ tiêu tầng ngữ nghĩa phơi ra model.

Vì sao không tra thẳng metric_dictionary.name_vi: tên KHÔNG duy nhất (đo 2026-09-07) —
isa20 và isa22 cùng tên "LỢI NHUẬN THUẦN" nhưng khác giá trị, BVPS có 3 mã, "Giá trị hao
mòn lũy kế" có 4 mã. Đơn vị vẫn đọc từ metric_dictionary.unit (nguồn sự thật về đơn vị);
bảng này chỉ quyết TÊN HIỂN THỊ. Mã ngoài bảng bị từ chối, kèm danh sách mã hợp lệ.
"""
from __future__ import annotations

LABELS: dict[str, str] = {
    # Kết quả kinh doanh
    "isa3": "Doanh thu thuần",
    "isa9": "Chi phí bán hàng",
    "isa10": "Chi phí quản lý doanh nghiệp",
    "isa16": "Lợi nhuận trước thuế",
    "isa20": "Lợi nhuận sau thuế (toàn bộ)",
    "isa22": "Lợi nhuận sau thuế của cổ đông công ty mẹ",
    "isa23": "Lãi cơ bản trên cổ phiếu (EPS)",
    # Cân đối kế toán
    "bsa1": "Tài sản ngắn hạn",
    "bsa2": "Tiền và tương đương tiền",
    "bsa53": "Tổng tài sản",
    "bsa54": "Nợ phải trả",
    "bsa78": "Vốn chủ sở hữu",
    "bsa96": "Tổng nguồn vốn",
    # Lưu chuyển tiền tệ
    "cfa18": "Lưu chuyển tiền thuần từ hoạt động kinh doanh",
    # Tỷ số thị trường
    "rtd11": "Vốn hoá thị trường",
    "rtd14": "EPS (TTM)",
    "rtd21": "P/E (TTM)",
    "rtd25": "P/B (TTM)",
    "rtd7": "Giá trị sổ sách mỗi cổ phiếu (BVPS, TTM)",
    "rtq12": "ROE (TTM)",
    "rtq14": "ROA (TTM)",
}

DEFAULT_BY_STATEMENT = {
    "IS": ["isa3", "isa9", "isa10", "isa16", "isa20", "isa22", "isa23"],
    "BS": ["bsa1", "bsa2", "bsa53", "bsa54", "bsa78", "bsa96"],
    "CF": ["cfa18"],
}
DEFAULT_RATIOS = ["rtd11", "rtd14", "rtd21", "rtd25", "rtd7", "rtq12", "rtq14"]


def label_for(code: str) -> str | None:
    return LABELS.get(code)
