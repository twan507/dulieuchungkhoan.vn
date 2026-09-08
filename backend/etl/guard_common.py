"""Thứ dùng chung giữa các chốt chặn (guard) của họ job ETL.

Hiện chỉ có một lớp. File này ra đời ngày 2026-09-08 theo quyết định §4.8
(`docs/90-records/plans/2026-09-07-audit-drift-cleanup/decision-unify-jobs-2026-09-08.md`)
để **xoá sáu bản sao** của `GuardRefused`, không phải để gom sẵn chỗ cho hằng số guard —
quyết định đó đã cân nhắc và **loại**: ngưỡng của mỗi họ là một con số ĐO ĐƯỢC của riêng họ
(xem lý do 0.5 → 0.2 ghi tại `screener_guard`), gom chung là quyết thay cho tương lai.
"""
from __future__ import annotations


class GuardRefused(Exception):
    """Chốt chặn từ chối lượt chạy — ném BÊN TRONG `with engine.begin()` để giao dịch dữ
    liệu tự rollback, rồi ghi bằng chứng ở một giao dịch riêng và trả mã thoát **1**
    (`backend/README.md` §"Mã thoát": 1 = từ chối, dữ liệu vẫn lành; 2 = lỗi thật).

    Nhận nguyên `verdict` của guard chứ không nhận riêng `reasons`: cả 8 guard đều trả một
    object có `ok` + `reasons`, và bốn họ cần chính `verdict` để lưu bằng chứng. `reasons`
    là **bản sao dạng list** — verdict là bằng chứng sẽ ghi xuống `staging`, không được để
    một chỗ bắt exception lỡ tay sửa vào nó.
    """

    def __init__(self, verdict):
        self.verdict = verdict
        self.reasons = list(verdict.reasons)
        super().__init__("; ".join(self.reasons))
