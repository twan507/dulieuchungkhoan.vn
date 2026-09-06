# Bộ đánh giá gán tay (gold set) — lưới phân loại tin

**Mục đích:** đáp án chuẩn do người chốt để chấm lưới MiniMax M3 (độ đúng nhóm/sub/mã/ngành), từ đó chốt ngưỡng `confidence`, thinking, trần cắt, và điều kiện bật chạy tự động (lát 9b). Không phải dữ liệu vận hành.

**Cách làm (2026-09-06 chiều):** 150 bài lấy ngẫu nhiên (seed 20260906) từ kho, `published_at ≥ 2026-08-20`, thân ≥ 300 ký tự, phân tầng 38/38/38/36 theo nhóm gợi ý feed (1 · 2 · 3 · không), rải đều 8 nguồn. Ba subagent **Opus** (không phải model bị chấm) gán nháp độc lập theo đúng tiêu chí của prompt production (chủ thể · 20 sub · ≤ 5 mã niêm yết · ≤ 3 ngành), đánh dấu bài khó. Chủ dự án rà và sửa trên file Excel, chỉ 5 cột "CHỐT".

| File | Nội dung |
|---|---|
| `gold-draft-2026-09-06.xlsx` | 150 bài: ngữ cảnh (tiêu đề, sapo, 700 ký tự đầu, url) · cột NHÁP (Opus) · cột CHỐT (chủ dự án sửa) · sheet `ma_sub`, `ma_nganh`, `huong_dan` |
| `gold.jsonl` *(sau khi chủ dự án chốt)* | `{article_id, group, sub, tickers, industries}` — nguồn duy nhất để chấm |

Luật: gold chỉ được sửa bởi người; model không bao giờ ghi vào cột CHỐT. Chấm lưới = so `news.article`/`article_ticker`/`article_industry` (hoặc dry-run JSONL) với `gold.jsonl` theo `article_id`.

## Bản 2 (2026-09-06 chiều tối) — 400 bài, ba lượt Opus, đây là bộ gold dùng để chấm

Chủ dự án: "đọc không hết 150 bài — dùng agent Opus gán, hai lượt độc lập rồi chốt; mở rộng mẫu, đủ cả ba nhóm". Làm: taxonomy mở rộng trước (`2f`, `3e` thị trường tài sản, nhóm 3 gồm DN chưa niêm yết, luật chủ thể — news-pipeline §3), rồi 400 bài (150 cũ + 250 mới, 100 mỗi nhóm gợi ý, seed 20260906) chia 8 lô × 50; **lượt 1 và lượt 2** mỗi lượt 8 subagent Opus gán độc lập theo `brief-annotator.md`; **lượt 3** ba subagent Opus phân xử 43 bài lệch theo `brief-adjudicator.md`; `build_final.py` gộp + áp luật nhất quán `NGANHANG` cho `1c`/`2b` (4 bài).

| File | Nội dung |
|---|---|
| `gold.jsonl` | **đáp án chuẩn** 400 dòng `{article_id, group, sub, tickers, industries}` — nhóm 1: 126 · 2: 93 · 3: 127 · x: 54 |
| `gold-2026-09-06.xlsx` | bảng soát: ngữ cảnh + nhãn lượt 1, lượt 2, cách chốt, lý do phân xử (dòng vàng = có lệch) + 4 cột CHỐT; sheet `thong_ke` |
| `pred-adaptive-2026-09-06.jsonl` · `pred-disabled-2026-09-06.jsonl` | dự đoán MiniMax M3 trên đúng 400 bài (`etl classify --dry-run --ids-file`), hai chế độ thinking |
| `score.py` | chấm dự đoán với gold: đúng nhóm, nhóm+sub, mã P/R, ngành P/R, ma trận nhầm, độ đúng theo dải `confidence` |
| `compare.py` · `build_final.py` · `build_xlsx.py` | so khớp hai lượt · dựng gold cuối · dựng bản nháp 150 (bản 1, đã thay) |

**Đồng thuận hai lượt Opus** (đo độ tự nhất quán của một model, không phải hai người): nhóm 396/400 (99 %), sub 391 (98 %), mã 388 (97 %), ngành 374 (94 %), cả bốn 357 (89 %). Phân xử: 19 theo lượt 1, 23 theo lượt 2, 1 nhãn mới. Chỉnh sửa của chủ dự án (nếu có) làm trên cột CHỐT của xlsx rồi dựng lại `gold.jsonl`.
