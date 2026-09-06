# Ledger — lát 9a: lưới AI phân loại tin + gắn ngành trên MiniMax M3

Nhánh `feat/news-classify-llm`, tách từ `main` `6b55d77` (docs lát 8b + brainstorm LLM). Chủ dự án chốt hướng trong chat 2026-09-06 chiều (spec §4.1); spec/plan viết cùng phiên, thực thi liền theo yêu cầu "thực thi luôn theo quy trình cho tới xong". Kiểm chứng: `PYTHONIOENCODING=utf-8 uv run pytest tests -q` từ `backend/`.

## 0. Trước khi chạy plan

- Đo bổ sung 2026-09-06 15:10–15:15 (spec §2.1): SDK `anthropic` 1.4.0 dùng `httpx2`, mock được bằng `httpx2.MockTransport`; `GET /v1/token_plan/remains` trả JSON hai dòng `general`/`video` (fixture `backend/tests/core/fixtures/token_plan_remains.json`); kho 7.998 bài, bucket 544/509/627/6.318.
- Task 0 (controller): `uv add anthropic` (+`httpx2`, `httpcore2`, `jiter`), fixture quota, `.env.example` thêm `LLM_API=`.
- Mốc trước plan: **809 passed, 2 skipped** (bàn giao lát 8b + trả nợ nhỏ).

## 1. Tiến trình

| Task | Ai | Kết quả | Commit |
|---|---|---|---|
| 0 fixture + SDK | controller | xong | `2a8da3a` |
| 1+2 core/llm (ghép) | Sonnet impl + Sonnet review; fix 1 vòng (Sonnet) + re-review (Sonnet) | Spec ❌→✅: 1 Important — `OverloadedError` 529 rơi vào `bad_request` (sửa: `status >= 500` trên `APIStatusError`, +2 case 529/503); minor để lại: `r.json()` trong `token_plan_remains` chưa bọc, echo `content` rỗng ở đường sửa, `LLMClient` không có `close()`; 32 test `tests/core` | `42cd63b`, `a87a216`, `5d0a7e8` |
| 3 migration 0018 + s15 | Sonnet impl + Sonnet review | Spec ✅ / Quality ✅, 0 vòng sửa; reviewer tự chạy s15 4/4 và đọc 0009 xác nhận default privileges phủ; minor để lại: `_cleanup` riêng của e55 chưa xoá hai bảng mới (chưa cần vì e55 không ghi vào đó). Ruling: dòng > 150 ký tự trong test chép nguyên từ plan — chấp nhận (repo không lint, file cũ đã có dòng dài) — nếu sai: chỉ tốn một lượt format | `e9ce4d9` |
| 4+5 news_classify thuần + DB (ghép) | Sonnet impl + Sonnet review | Spec ✅ / Quality ✅, 0 vòng sửa; reviewer tự chạy e59 10/10 + e60 4/4 và soi tay regex/view. Hai lệch so với plan, đều đúng: (a) plan tự mâu thuẫn — prompt tĩnh có 3 dấu " — " làm test đếm dòng ngành sai ⇒ đổi chữ, nghĩa giữ nguyên; (b) `confidence numeric` trả `Decimal` ⇒ test ép `float()` (fallback plan cho phép). Minor để lại: biến `c` trong comprehension che biến kết nối ở e60 | `6965d96`, `8a12822` |
| 6 classify_run + CLI | Sonnet impl + Sonnet review; fix 1 vòng (Sonnet) + re-review (Sonnet) | Spec ❌→✅: 1 Important **plan-mandated** — `run()` không `dispose` engine ở nhánh thoát sớm (code chép từ plan) ⇒ Ruling: sửa theo khuôn `run_backfill` (+1 test spy dispose) — nếu sai: không mất gì. Implementer sửa literal `content_chars` 350→355 (`len(LONG)` thật, plan ghi sai). Minor để lại: dry-run không có `except Exception` bao ngoài; `stats.quota` thiếu khoá khi guard hỏng; streak không reset khi lỗi `schema`. **Sự cố:** implementer báo 2 test e05 đỏ là "có sẵn" — sai: FK `ops.llm_call.run_id → etl_run` của 0018 chặn `TRUNCATE ops.etl_run` trong e05 (Task 3 chỉ chạy schema+e56/e57 nên không thấy) ⇒ fix test-only `be5a25d` | `0acad20`, `be5a25d`, `f1ef13a` |

## 2. Nghiệm thu (Task 7)

## 3. Tài liệu (Task 8)

## 4. Tiền kiểm plan (SDD, trước Task 1)

| Cặp/Task | Kiểm | Kết quả |
|---|---|---|
| T1 ↔ T2 | `core/llm/__init__.py` cả hai sửa; T2 export thêm `LLMClient/Structured/QuotaRemains` | tuần tự, ghép một dispatch — không xung đột |
| T2 ↔ T5/T6 | `Structured(value, usage, repaired, stop_reason)`, `QuotaRemains(interval_pct, weekly_pct, raw)`, `LLMError(reason, retryable=)` | tên/chữ ký khớp ở FakeClient và `classify_run` |
| T3 ↔ T5 | `_cleanup` e56 thêm hai bảng mới; e60 có `_cleanup` riêng lọc theo `zz.test` | không giẫm nhau |
| T4 ↔ T5 ↔ T6 | `Row` 9 trường = `_SELECT` 9 cột; `apply` 7 khoá = 7 khoá trong `_empty_stats` | khớp |
| T6 ↔ CLI test | `run(limit, per_group, thinking, dry_run, out, max_minutes, cap)` = dict `seen` ở e61 | khớp |
| Rubric | không có test không assert; không có khối logic chép nguyên | sạch |

Ruling: ghép Task 1+2 và Task 4+5 mỗi cặp một dispatch (cùng file, một mặt review) — giảm overhead — nếu sai: review dài hơn, không mất gì khác. Artifact SDD (brief/report/diff) đặt ở scratchpad ngoài repo theo CLAUDE.md §4.1 (cấm `.superpowers/`).

### 2.1 AC1–AC3 (2026-09-06 chiều)

- **AC1** ✅ toàn bộ **861 passed, 2 skipped** (71 s; +52 so với 809: 13 `tests/core/test_llm_*`, 4 `test_s15`, 10 `e59`, 18 `e60`, 6 `e61`, +1 test dispose) — lệnh `uv run pytest tests -q` từ `backend/`, Docker đang chạy (CH/ingester ephemeral).
- **AC2** ✅ `alembic upgrade head` trên kho thật (`DATA_DATABASE_URL`, owner) ⇒ `current` = **`0018 (head)`**. Downgrade/upgrade sạch trên `dulieu_test` do fixture pytest chứng (dựng từ đầu tới `0018`).
- **AC3** ✅ (có phát hiện) `etl classify --dry-run --per-group 3` dưới `ETL_DATABASE_URL` (`etl_worker`) + khoá thật, 14:55–14:57: `selected 12 · classified 11 · failed 1 (failed_schema 1) · repaired 0`; nhóm `1: 2 · 2: 1 · 3: 3 · x: 5`; token `input 33.321 · cache_read 9.088 · output 7.931 · thinking 4.965` (≈ 3,0k vào / 720 ra / 450 thinking mỗi bài); độ trễ `p50 10,3 s · p90 20,1 s · max 27,4 s`; `usd_estimate 0,0201` (≈ $0,0018/bài, đúng ước); quota `97 % / 86 %` trước và sau (12 lời gọi không nhúc nhích %). `grep` 8 ký tự đầu khoá trong log + JSONL ⇒ **0**.
  - 🔴 **Phát hiện A1 sai một phần:** bài `8000` lỗi schema hai lần: `tickers: Field required; industries: Field required` — model **bỏ hẳn hai trường mảng rỗng** thay vì trả `[]`. Đo 232 lời gọi trước không gặp vì `tickers` khi rỗng vẫn được trả (không có trường thứ hai). ⇒ **Ruling:** `tickers`/`industries` thành tuỳ chọn mặc định `[]` trong `_ClassificationBase`/`build_schema` (schema `required` còn 4 khoá) — đưa vào đợt sửa sau review cuối; nếu sai: model có thể bỏ cả mảng không rỗng — không, model chỉ bỏ khi rỗng (bài 8000 là tin `x`).
  - Cache tự động **không đều**: 4/11 lời gọi đọc cache 2.048 token, 7/11 chỉ 128 (khuôn mặc định) dù system+tools ≈ 1,5k token giống hệt ⇒ ước "1,3k cache mỗi bài" của brainstorm là lạc quan; ghi vào minimax.md.
  - Dry-run không tính `overridden`/`tickers_*`/`industries_*` (chỉ `apply` mới đếm) — đọc JSONL để biết; ghi README.
  - Định tính 11 bài: `x` 5/11 đúng (giáo dục, Einstein, sách "Cha giàu", Vietnam Airlines hạ cánh cấp cứu, học bổng Vietcombank — tin PR/xã hội); PAP nâng vốn ⇒ `3c` + `VANTAI` + mã `PAP` đúng; quốc lộ ⇒ `1d` + `XAYDUNG/VATLIEU` hợp lý; tàu sân bay ⇒ `2d` không ngành hợp lý; khoáng sản về Bộ Công Thương ⇒ `1a` + `KHOANGSAN` hợp lý, `KHUCONGNGHIEP` gượng.

## 5. Review toàn nhánh (Opus, 6b55d77 → f1ef13a) — "With fixes"

Báo cáo đầy đủ ở scratchpad (`review-final-report.md`); tóm tắt: 0 Critical · 3 Important · 15 Minor. Reviewer tự chạy `tests/core` 32/32.

| # | Finding | Xử lý |
|---|---|---|
| I1 | `token_plan_remains` không bọc `r.json()` ⇒ body không phải JSON làm exception lọt qua guard (spec §4.2-VIII: guard hỏng không chặn) | **sửa** |
| I2 | Đường sửa schema echo lượt assistant có `tool_use` rồi nối user text thuần — API kiểu Anthropic đòi `tool_result` ⇒ máy chủ chặt trả 400 `bad_request` thay vì sửa được. **Lỗi của spec/plan §5.2**, implementer chép đúng | **Ruling: sửa theo phương án (b)** — không echo assistant; lượt 2 gửi lại user gốc + câu sửa (một lượt, không cần `tool_result`, dọn luôn minor "echo content rỗng") — nếu sai: mất ngữ cảnh lượt 1 ở đường sửa (đường lạnh, 0/232) |
| I3 | `_cleanup` e55 `DELETE FROM news.article` không phạm vi, chưa dọn `article_industry`/`llm_call` ⇒ vỡ khi đổi thứ tự test | **sửa** (2 dòng) |
| AC3 | Model bỏ hẳn `tickers`/`industries` khi rỗng ⇒ `failed_schema` (ledger §2.1) | **sửa**: hai trường tuỳ chọn mặc định `[]`, `required` còn 4 khoá; test e59 cập nhật + ca thiếu hai khoá vẫn hợp lệ |
| M1 M2 M3 M4 M5 M6 M7 M8 M9 M15 | `model_down` thiếu trong stats; stats mất khi Ctrl+C/exception; `quota` rỗng khi guard hỏng; `industries_ai` đếm lần thử thay vì `rowcount`; token của lời gọi thất bại không vào sổ; comment 350/355; ternary vô nghĩa; assert `< 4` yếu; vòng bóc `base_url` thiếu `break`; `OperationalError` lúc khởi động không dispose | **sửa cùng đợt** (rẻ, cùng chỗ) |
| M10 M11 M12 M13 M14 | `close()` cho `LLMClient` (lát 10); quota check sau `open_run` (giữ — lần chặn nhìn thấy trong sổ, ghi README); streak không reset khi lỗi `schema` (an toàn); mã AI ở bài ngoài nhóm 3 không có counter; FK không `ON DELETE` (ghi README) | **hoãn có ghi**; M11/M14 ⇒ tài liệu |

**Đợt sửa sau review cuối** (một implementer Sonnet, một re-review Sonnet): `c4f2f33` — I1, I2 (phương án b), I3, phát hiện AC3 (mảng tuỳ chọn), M1–M9, M15 đều ADDRESSED, không breakage mới; **865 passed, 2 skipped**. Minor còn treo sau re-review: docstring `errors.py` nói "hai thuộc tính" (nay có `usage`); test M9 chưa có ca đuôi kép. Hoãn có ghi: M10 `close()` (lát 10) · M11 quota sau `open_run` (giữ, ghi README) · M12 streak · M13 `tickers_ai_offgroup` · M14 FK không `ON DELETE` (ghi README).

### 2.2 AC5 — dry-run thinking `disabled`, 25 bài/nhóm gợi ý (15:15–15:22, code `c4f2f33`)

JSONL: [`measure/ac5-dry-disabled-2026-09-06.jsonl`](measure/ac5-dry-disabled-2026-09-06.jsonl). `selected 100 · classified 100 · failed 0 · failed_schema 0 · repaired 1` (mảng đã tuỳ chọn ⇒ hết lỗi "Field required" của AC3).

| Chỉ số | Giá trị |
|---|---|
| Độ trễ p50 / p90 / max / tổng | **3,6 s / 7,1 s / 33,2 s / 438 s** (100 bài ≈ 7,3 phút tuần tự) |
| Token vào (p50 / tổng) | **2.877 / 274.819** — cache đọc lại 95.241 (**47/100** lời gọi trúng cache; không đều, xem minimax.md §6) |
| Token ra (p50 / tổng) | **294 / 31.371**; thinking 0 |
| Chi phí quy giá pay-go | **$0,1258 / 100 bài ≈ $0,0013/bài** |
| Quota Token Plan | cửa sổ 5 giờ **97 % → 95 %** cho 100 lời gọi (≈ 0,02 %/lời gọi ⇒ cửa sổ ≈ 5.000 lời gọi cỡ này); tuần 86 % không đổi |
| Phân bố nhóm | 1: 28 · 2: 27 · 3: 26 · **x: 19** |
| Nhóm so gợi ý feed | giữ nhóm 53/75 bài có gợi ý; đổi sang `x` 16/75; nhảy nhóm 6/75 (3→1: 2, 3→2: 2, 1→2: 1, 1→3: 1); 25 bài không gợi ý ⇒ 3: 8 · 1: 8 · 2: 6 · x: 3 |
| Ngành mỗi bài | 0: 34 · 1: 23 · 2: 32 · 3: 11 (trần 3 chạm 11 %) |
| Mã AI | 14/100 bài có mã (chưa lọc niêm yết — dry-run) |
| `summary_ai` | p50 **349** ký tự (yêu cầu 200–300 — model vẫn vượt như đã đo) |
