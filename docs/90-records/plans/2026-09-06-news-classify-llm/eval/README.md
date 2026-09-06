# Bộ đánh giá gán tay (gold set) — lưới phân loại tin

**Mục đích:** đáp án chuẩn do người chốt để chấm lưới MiniMax M3 (độ đúng nhóm/sub/mã/ngành), từ đó chốt ngưỡng `confidence`, thinking, trần cắt, và điều kiện bật chạy tự động (lát 9b). Không phải dữ liệu vận hành.

**Cách làm (2026-09-06 chiều):** 150 bài lấy ngẫu nhiên (seed 20260906) từ kho, `published_at ≥ 2026-08-20`, thân ≥ 300 ký tự, phân tầng 38/38/38/36 theo nhóm gợi ý feed (1 · 2 · 3 · không), rải đều 8 nguồn. Ba subagent **Opus** (không phải model bị chấm) gán nháp độc lập theo đúng tiêu chí của prompt production (chủ thể · 20 sub · ≤ 5 mã niêm yết · ≤ 3 ngành), đánh dấu bài khó. Chủ dự án rà và sửa trên file Excel, chỉ 5 cột "CHỐT".

| File | Nội dung |
|---|---|
| `gold-draft-2026-09-06.xlsx` | 150 bài: ngữ cảnh (tiêu đề, sapo, 700 ký tự đầu, url) · cột NHÁP (Opus) · cột CHỐT (chủ dự án sửa) · sheet `ma_sub`, `ma_nganh`, `huong_dan` |
| `gold.jsonl` *(sau khi chủ dự án chốt)* | `{article_id, group, sub, tickers, industries}` — nguồn duy nhất để chấm |

Luật: gold chỉ được sửa bởi người; model không bao giờ ghi vào cột CHỐT. Chấm lưới = so `news.article`/`article_ticker`/`article_industry` (hoặc dry-run JSONL) với `gold.jsonl` theo `article_id`.
