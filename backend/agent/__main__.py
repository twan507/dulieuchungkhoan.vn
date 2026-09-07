"""`python -m agent` — vòng chat terminal của tầng ngữ nghĩa.

Thứ tự khởi động có chủ đích: nạp `.env` TRƯỚC mọi import chạm biến môi trường, rồi dựng
engine đọc (bên trong nó `assert_read_only` chạy — sai quyền là chết ngay tại đây chứ không
phải giữa cuộc trò chuyện, CLAUDE.md §3.5).
"""
from __future__ import annotations

import sys
from dataclasses import replace

from core.env import load_dotenv

load_dotenv()

from agent.chat import repl                      # noqa: E402 — phải nạp .env trước
from agent.db import ops_engine, read_engine     # noqa: E402
from core.llm.client import LLMClient            # noqa: E402
from core.llm.settings import LLMSettings        # noqa: E402


CHAT_TIMEOUT_S = 600.0
"""Thời gian chờ một request của vòng chat, dài hơn hẳn mặc định 120 s của `core.llm`.

Vì sao không dùng mặc định: `chat.MAX_TOKENS` là 32.000, mà tốc độ sinh đo được 2026-09-07 là
84–152 token/s ⇒ một câu trả lời dài thật sự cần tới ~380 s. Với timeout 120 s thì trần token
kia không bao giờ chạm tới được, và lượt nào chạm sẽ hết giờ rồi thử lại 3 lần — mất 4 request
thay vì một câu trả lời bị cắt. Job lô (`etl classify`) vẫn giữ 120 s vì bài của nó ngắn.
"""


def main() -> int:
    read_eng = read_engine()
    ops_eng = ops_engine()
    settings = replace(LLMSettings.from_env(), timeout_s=CHAT_TIMEOUT_S)
    try:
        with LLMClient(settings) as llm:
            repl(llm, read_eng, ops_eng)
    finally:
        read_eng.dispose()
        ops_eng.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
