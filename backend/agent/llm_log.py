"""Sổ mỗi request gọi model vào ops.llm_call.

MỘT DÒNG = MỘT REQUEST (http_calls=1) — một câu chat nhiều vòng function sinh nhiều dòng.
status: 'ok' khi stop_reason là 'end_turn' HOẶC 'tool_use' — lượt gọi công cụ là một bước
bình thường giữa chừng, không phải hỏng (đo 2026-09-07: bản đầu ghi nhầm mọi lượt tool thành
'failed', làm sổ nói dối). 'failed' dành cho 'max_tokens', chạm max_iterations, và exception. 'repaired' không dùng ở lát 10 (đó là ánh xạ của
core.llm.client cho vòng structured output, không phải vòng chat). thinking='adaptive' vì
vòng chat lát 10 chỉ dùng adaptive.

Bốn loại token đọc qua core.llm.usage.Usage.from_sdk — cùng đường core/llm/client.py đã dùng
để đọc usage của SDK (getattr an toàn, kể cả khi output_tokens_details vắng mặt), tránh viết
lại một bản riêng ở đây.

Sổ là phụ, chat là chính: lỗi ghi sổ (mất kết nối, vi phạm ràng buộc CHECK) bị NUỐT — chỉ in
stderr, không bao giờ ném ra ngoài làm sập vòng chat.
"""
from __future__ import annotations

import sys

import sqlalchemy as sa

from core.llm.usage import Usage

_SQL = sa.text("""
    INSERT INTO ops.llm_call (purpose, model, thinking, status, http_calls,
                              input_tokens, cache_read_tokens, output_tokens, thinking_tokens,
                              latency_ms, error)
    VALUES (:purpose, :model, 'adaptive', :status, 1, :vao, :cache, :ra, :nghi, :ms, :loi)
""")


def log_llm_call(ops_eng, message, *, purpose: str = "chat", model: str, latency_ms: int) -> None:
    """Ghi một dòng vào ops.llm_call cho một lượt gọi model thật. Không bao giờ ném ra ngoài."""
    try:
        stop = getattr(message, "stop_reason", None)
        u = Usage.from_sdk(message.usage, latency_ms / 1000)
        with ops_eng.connect() as conn:
            conn.execute(_SQL, {
                "purpose": purpose,
                "model": model,
                "status": "ok" if stop in ("end_turn", "tool_use") else "failed",
                "vao": u.input_tokens,
                "cache": u.cache_read_tokens,
                "ra": u.output_tokens,
                "nghi": u.thinking_tokens,
                "ms": latency_ms,
                "loi": None if stop in ("end_turn", "tool_use") else f"stop_reason={stop}",
            })
            conn.commit()
    except Exception as e:                                   # noqa: BLE001 — chỉ giữ tên lớp, không lộ nội dung lỗi
        print(f"[llm_log] khong ghi duoc so: {type(e).__name__}", file=sys.stderr)
