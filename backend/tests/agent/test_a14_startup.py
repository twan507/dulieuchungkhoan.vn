"""Seam đường khởi động `python -m agent` — CLAUDE.md §3.5.

Vì sao có file này: `main()` là đường DUY NHẤT dựng client thật, và mảnh đắt nhất của nó —
`replace(LLMSettings.from_env(), timeout_s=CHAT_TIMEOUT_S)` — **không test nào chạm tới**
(review-chuan-v4 §G5). Lát 10 kiểm tay một lần rồi thôi; đổi tên trường `LLMSettings` sau
này là hỏng im lặng.

§3.5 đòi test chạy dưới **đúng quyền production**, và đòi kiểm **lệnh** chứ không kiểm trạng
thái hiển thị — nên test này gọi thẳng `main()` với `repl` thay bằng hàm ghi lại, thay vì
dựng settings giả rồi tự khẳng định với chính mình.
"""
from __future__ import annotations

import os

import pytest

import agent.__main__ as m


@pytest.mark.skipif(not os.getenv("AGENT_DATABASE_URL"),
                    reason="cần credential production (AGENT_DATABASE_URL) — §3.5")
def test_main_dung_timeout_dai_va_mo_duoc_duong_doc_that(monkeypatch):
    """Ba thứ cùng chết nếu wiring hỏng: timeout, engine đọc, và `assert_read_only` bên trong nó."""
    bat: dict = {}

    def repl_gia(llm, read_eng, ops_eng):
        bat["timeout"] = llm.raw.timeout
        bat["timeout_settings"] = llm.settings.timeout_s
        with read_eng.connect() as conn:
            bat["doc_duoc"] = conn.exec_driver_sql("select 1").scalar()

    monkeypatch.setattr(m, "repl", repl_gia)

    assert m.main() == 0
    # 600 s, không phải 120 s mặc định của core.llm: trần 32k token chỉ chạm tới được khi
    # đồng hồ đủ dài (tốc độ sinh đo 2026-09-07 là 84–152 token/s).
    assert m.CHAT_TIMEOUT_S == 600.0
    assert bat["timeout_settings"] == 600.0
    assert bat["timeout"] == 600.0
    assert bat["doc_duoc"] == 1
