# Khảo sát 2026-09-06 — MiniMax M3 và module LLM dùng chung (chuẩn bị lát 9, tái dùng ở lát 10)

**Vì sao:** chủ dự án đặt khoá `LLM_API` (MiniMax Token Plan) và yêu cầu dựng sẵn điểm vào đầy đủ cho lát 9, kèm thiết kế module LLM mà chatbot web dùng lại được. Trước khảo sát này repo **không có** SDK, module hay khoá LLM nào.

| File | Nội dung |
|---|---|
| [brainstorm.md](brainstorm.md) | §4.8: dữ kiện đã kiểm vs giả định · 3 phương án độc lập (A SDK anthropic trỏ MiniMax · B httpx thô giao diện OpenAI · C cổng trung lập) · chấm theo tiêu chí viết trước · **chọn A** · thiết kế `backend/core/llm/` (vị trí, hợp đồng, cấu hình, chi phí/quota, bộ đánh giá, dùng lại ở lát 10, embedding tách 9b, seam test) · 6 điểm chủ dự án chốt ở phiên sau |
| [measure-minimax-2026-09-06.md](measure-minimax-2026-09-06.md) | Nhật ký ≈45 lời gọi thật: endpoint, thinking, đầu ra có cấu trúc, tokenizer 1,62 ký tự/token, cache, SDK, embedding, quota |

Tri thức vận hành đã chuyển vào tài liệu sống: [`docs/10-sources/llm/minimax.md`](../../../10-sources/llm/minimax.md) (tầng reference) và [roadmap — Điểm vào cho lát 9](../../../00-overview/roadmap.md).
