"""`python -m agent` — vòng chat terminal của tầng ngữ nghĩa.

Thứ tự khởi động có chủ đích: nạp `.env` TRƯỚC mọi import chạm biến môi trường, rồi dựng
engine đọc (bên trong nó `assert_read_only` chạy — sai quyền là chết ngay tại đây chứ không
phải giữa cuộc trò chuyện, CLAUDE.md §3.5).
"""
from __future__ import annotations

import sys

from core.env import load_dotenv

load_dotenv()

from agent.chat import repl                      # noqa: E402 — phải nạp .env trước
from agent.db import ops_engine, read_engine     # noqa: E402
from core.llm.client import LLMClient            # noqa: E402
from core.llm.settings import LLMSettings        # noqa: E402


def main() -> int:
    read_eng = read_engine()
    ops_eng = ops_engine()
    try:
        with LLMClient(LLMSettings.from_env()) as llm:
            repl(llm, read_eng, ops_eng)
    finally:
        read_eng.dispose()
        ops_eng.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
