# Ledger — lát 9a: lưới AI phân loại tin + gắn ngành trên MiniMax M3

Nhánh `feat/news-classify-llm`, tách từ `main` `6b55d77` (docs lát 8b + brainstorm LLM). Chủ dự án chốt hướng trong chat 2026-09-06 chiều (spec §4.1); spec/plan viết cùng phiên, thực thi liền theo yêu cầu "thực thi luôn theo quy trình cho tới xong". Kiểm chứng: `PYTHONIOENCODING=utf-8 uv run pytest tests -q` từ `backend/`.

## 0. Trước khi chạy plan

- Đo bổ sung 2026-09-06 15:10–15:15 (spec §2.1): SDK `anthropic` 1.4.0 dùng `httpx2`, mock được bằng `httpx2.MockTransport`; `GET /v1/token_plan/remains` trả JSON hai dòng `general`/`video` (fixture `backend/tests/core/fixtures/token_plan_remains.json`); kho 7.998 bài, bucket 544/509/627/6.318.
- Task 0 (controller): `uv add anthropic` (+`httpx2`, `httpcore2`, `jiter`), fixture quota, `.env.example` thêm `LLM_API=`.
- Mốc trước plan: **809 passed, 2 skipped** (bàn giao lát 8b + trả nợ nhỏ).

## 1. Tiến trình

| Task | Ai | Kết quả | Commit |
|---|---|---|---|
| 0 fixture + SDK | controller | | |
| 1 core/llm settings·usage·errors | | | |
| 2 core/llm client | | | |
| 3 migration 0018 + s15 | | | |
| 4 news_classify thuần | | | |
| 5 news_classify DB | | | |
| 6 classify_run + CLI | | | |

## 2. Nghiệm thu (Task 7)

## 3. Tài liệu (Task 8)
