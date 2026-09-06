"""Vòng chat nhiều lượt trong terminal.

BA điều đọc thẳng từ mã SDK `anthropic 1.4.0` (`lib/tools/_beta_runner.py`), đừng đổi nếu
chưa đọc lại:

1. `self._iterator = self.__run__()` tạo MỘT LẦN trong `__init__` và cạn khi lượt kết thúc.
   Runner đã cạn mà gọi lại thì **không ném lỗi, không gửi request, trả lại message cũ** —
   hỏng im lặng. ⇒ mỗi lượt người dùng dựng runner MỚI, lịch sử do mình tự giữ.

2. `generate_tool_call_response()` CÓ CACHE; `append_messages()` XOÁ cache (dòng 150). Gọi
   `generate` rồi `append` ⇒ vòng lặp trong `__run__` gọi `generate` lần nữa với cache rỗng
   ⇒ **mọi function chạy HAI LẦN**, mà lịch sử message vẫn đúng nên không có gì báo. ⇒ sửa
   `response` TẠI CHỖ và KHÔNG gọi `append_messages`; `__run__` sẽ tự lấy đúng object đã sửa
   từ cache rồi tự nối vào lịch sử của nó.

3. Runner nối lượt assistant NGUYÊN VĂN (`{"role", "content"}`, không bóc lại block), nên
   block `thinking` kèm `signature` được echo đúng — thứ MiniMax bắt buộc phải có ở lượt sau.

Vì sao phải chèn lời nhắc vào **cùng** lượt `tool_result`: Messages API không cho hai lượt
`user` liên tiếp, nên cách hợp lệ duy nhất để nói thêm với model sau khi có dữ liệu là thêm
một block `text` vào chính mảng `content` của lượt mang `tool_result`.
"""
from __future__ import annotations

import time

from agent.llm_log import log_llm_call
from agent.system_prompt import build_system_blocks
from agent.tools import build_tools

REMINDER = ("Dữ liệu trên là số thật vừa tra được — dùng đúng số này, đừng lấy số ví dụ trong "
            "tài liệu kiến thức. Trả lời tiếp theo đúng hình dạng đã định: có mạch lập luận, "
            "kết luận có điều kiện, nói rõ số nào tra được và số nào là giả định, không lộ mã "
            "chỉ tiêu thô.")

MAX_ITERATIONS = 8          # trần cứng chống vòng gọi function vô hạn — số chọn, chưa đo
MAX_TOKENS = 8000           # 4000 CẮT THẬT 3/40 request (đo 2026-09-07): sau khi nạp một file
                            # tri thức L2, model tiêu tới 3.999 token chỉ cho thinking rồi hết
                            # chỗ cho câu trả lời ⇒ lượt đó trả về rỗng, im lặng.


def run_turn(llm, read_eng, ops_eng, history: list, cau_hoi: str) -> tuple[str, list]:
    """Chạy một lượt hỏi–đáp. Trả (câu trả lời, lịch sử mới) để lượt sau dùng lại."""
    messages = [*history, {"role": "user", "content": cau_hoi}]
    runner = llm.raw.beta.messages.tool_runner(
        model=llm.settings.model, max_tokens=MAX_TOKENS, system=build_system_blocks(),
        messages=messages, tools=build_tools(read_eng),
        thinking={"type": "adaptive"}, max_iterations=MAX_ITERATIONS,
    )
    tra_loi, t0 = "", time.monotonic()
    for message in runner:
        if ops_eng is not None:
            log_llm_call(ops_eng, message, model=llm.settings.model,
                         latency_ms=int((time.monotonic() - t0) * 1000))
        t0 = time.monotonic()
        messages = [*messages, {"role": message.role, "content": message.content}]
        if message.stop_reason == "tool_use":
            response = runner.generate_tool_call_response()          # có cache — không gọi lại
            if response is not None:
                response["content"] = [*response["content"], {"type": "text", "text": REMINDER}]
                messages = [*messages, response]
            # KHÔNG append_messages ở đây — xem ghi chú (2) đầu file.
        else:
            tra_loi = "".join(b.text for b in message.content if b.type == "text")
            if not tra_loi.strip():
                # Không bao giờ trả rỗng im lặng: nói rõ vì sao lượt này không có chữ nào.
                tra_loi = (f"[lượt này không sinh được câu trả lời — model dừng vì "
                           f"'{message.stop_reason}'. Thử hỏi ngắn gọn hơn hoặc chia nhỏ câu hỏi.]")
    return tra_loi, messages


def repl(llm, read_eng, ops_eng) -> None:
    print("Hỏi về chứng khoán, tài chính, kinh tế. Ctrl+C để thoát.\n")
    history: list = []
    while True:
        try:
            cau = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTạm biệt.")
            return
        if not cau:
            continue
        t0 = time.monotonic()
        try:
            tra_loi, history = run_turn(llm, read_eng, ops_eng, history, cau)
        except Exception as e:                      # noqa: BLE001 — chỉ giữ tên lớp, không lộ nội dung
            print(f"\n[lỗi {type(e).__name__} — lượt này bỏ qua, lịch sử giữ nguyên]\n")
            continue
        print(f"\nTrợ lý: {tra_loi}\n")
        try:
            q = llm.token_plan_remains()
            print(f"[{time.monotonic() - t0:.1f}s · quota 5h còn {q.interval_pct}% · tuần {q.weekly_pct}%]\n")
        except Exception as e:                      # noqa: BLE001
            print(f"[{time.monotonic() - t0:.1f}s · không đọc được quota: {type(e).__name__}]\n")
