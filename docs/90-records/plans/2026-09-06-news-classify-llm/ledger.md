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

### 2.3 AC4 — lượt ghi thật thinking `adaptive` (run 414, 15:22–15:54, **dừng tay theo chủ dự án** ở 182/400 bài) + lượt ngắn `--per-group 12` (run 422, 15:54–16:01, 48 bài)

Chủ dự án 15:53: "khảo sát qua xem như vậy đủ dữ kiện chưa thì chốt luôn… không nhất thiết phải làm đủ" ⇒ **Ruling:** kill run 414 khi nhóm 1 xong 100, nhóm 2 được 82 (đủ số token/thời gian), đóng dòng `etl_run` bằng tay (`failed`, error "dừng tay (kill)…", stats dựng lại từ `ops.llm_call`); chạy thêm một lượt ngắn 12 bài/nhóm để có mẫu nhóm 3 và nhóm không gợi ý (mã, ngành suy từ mã) — cũng là AC6. Nếu sai: thiếu số nhóm 3/NULL ở cỡ 100 — bù được bằng một lệnh.

| Chỉ số (mỗi lời gọi `ok`) | Run 414 (n=179 + 3 `repaired`) | Run 422 (n=48) | AC5 disabled (n=100) |
|---|---|---|---|
| Độ trễ p50 / p90 / max | **8,0 s / 16,5 s / 50 s** (repaired: 54 s, 2 lời gọi HTTP) | 7,4 s / 16,0 s / 23 s | 3,6 s / 7,1 s / 33 s |
| Token vào p50 / cache đọc | **3.009** / trúng cache **97/179** | 2.503 / 25/48 | 2.877 / 47/100 |
| Token ra p50 (thinking tổng) | **745** (58.720 thinking / 179) | 638 (16.069 / 48) | 294 (0) |
| Tổng token vào / cache / ra / thinking | 511.301 / 180.983 / 156.265 / 61.366 | 129.957 / 52.380 / 37.348 / 16.069 | 274.819 / 95.241 / 31.371 / 0 |
| Chi phí quy giá pay-go | **$0,352 ⇒ $0,0019/bài** | $0,087 ⇒ $0,0018/bài | $0,126 ⇒ $0,0013/bài |
| Quota cửa sổ 5 giờ | 97 % → 92 % (sau AC5 + 182 bài) | 92 % → 91 % | 97 % → 95 % |
| Nhịp tuần tự | **≈ 5,8 bài/phút** (182 bài / 31,5 phút) | 6,6 bài/phút | 13,7 bài/phút |

⇒ **Adaptive so với disabled trên cùng loại bài:** độ trễ ≈ 2,2×, token ra ≈ 2,5×, chi phí quy giá ≈ 1,45× (phần vào chiếm đa số nên chênh tổng nhỏ hơn brainstorm ước 8 % — vì thinking thật ≈ 330 token/bài, nhiều hơn 250 đo hôm trưa). 350 bài/ngày adaptive ≈ **1 giờ, ≈ $0,66 quy giá, ≈ 6–7 % cửa sổ 5 giờ**. Toàn kho 7.797 bài còn lại ≈ 22 giờ, ≈ $15, ≈ 3 cửa sổ 5 giờ.

**Đường sửa schema đã chạy thật 3 lần** (run 414, `status='repaired'`, `http_calls 2`): lần 1 model trả sai hình dạng, lần 2 (gửi lại user + câu sửa, phương án b) đúng — I2 của review cuối được kiểm bằng ca thật, không còn là giả định. 0 `failed` trên 230 lời gọi ghi thật sau khi mảng thành tuỳ chọn.

**Kết quả phân loại (run 414, nhóm gợi ý 1 và 2):** nhóm 1 (100): giữ 66 · →2: 16 · →3: 2 · →`x`: 16; nhóm 2 (82): giữ 53 · →1: 1 · →`x`: 28. **`x` = 44/182 = 24 %**. Feed bị ghi đè > 50 %: `bnews/kinh-te-viet-nam-1` 13/19, `vneconomy/tieu-diem` 6/9, `vietnambiz/tai-chinh` 2/3, `cafef/tai-chinh-quoc-te` 4/7 (run 422) — phần lớn sang `x` (feed tổng hợp lẫn tin xã hội/PR), đúng cơ chế §7.3. Sub nhiều nhất: `2d` 35, `1b` 18, `1a` 16, `1d` 13, `2e` 12. Run 422 (12/nhóm): nhóm 3 giữ 8/12, →1: 2, →`x`: 2; không gợi ý (12): 1: 3 · 2: 5 · 3: 2 · `x`: 2.

**Ngành:** 204 dòng `ai` trên 230 bài (≈ 0,9/bài; nhóm 1/2 gần như bài nào cũng có ngành — `CONGNGHE` 20, `XAYDUNG` 18, `NGANHANG` 14, `VANTAI` 14, `DAUKHI` 12); 20 dòng `ticker` trên 8 bài; **AC7:** `ai ∩ ticker` 9, `ticker` không có `ai` 11. Soi tay 5 bài nhóm 1/2: cao tốc ⇒ `VATLIEU/XAYDUNG`, thuốc thú y ⇒ `THUCPHAM/NONGNGHIEP`, lãi suất ⇒ `NGANHANG`, du lịch ⇒ `DULICH` — hợp lý; "Myanmar muốn học tập Việt Nam" ⇒ 3 ngành gượng (bài đối ngoại). ⚠️ Bài rổ FTSE 28 mã ⇒ 8 ngành `ticker` — với bài liệt kê danh mục, ngành suy từ mã thành nhiễu; cân nhắc ở lát 9b: chỉ suy ngành từ mã khi bài ≤ N mã.

**Mã (run 422, nhóm 3 và không gợi ý):** `via='ai'` 41 (1 bị lọc không niêm yết), `lookup` bù 4. ⚠️ Tầng 2 bắt nhầm **`USD`** (là một mã niêm yết thật trong `market.security` — bài FTSE) và `AMC` cho "HD AMC" — false positive của regex 3 chữ, tầng 3 không mắc; ghi vào nợ lát 9b (danh sách loại trừ cho tầng 2, hoặc bỏ tầng 2 khi đã có tầng 3).

**AC6** ✅ run 422 chọn 48 bài **khác** run 414 (tổng `classified_from IS NOT NULL` = 230 = 182 + 48; 7.797 còn NULL; `title_only` 0); PK `article_industry`/`article_ticker` không sinh dòng trùng.

**Tổng chi phí lát này (quy giá):** AC3 $0,02 + AC5 $0,13 + run 414 $0,35 + run 422 $0,09 ≈ **$0,59**; quota cửa sổ 5 giờ 97 % → 91 %, tuần 86 % → 85 %.

### 2.4 Soi chất lượng tóm tắt / mã / nhãn — mẫu 17 bài phân tầng (16:10, chủ dự án hỏi; định tính, không phải số đúng/sai)

- **`summary_ai`:** nội dung đúng bài, giữ số liệu tốt (PAP, Amy Grupo, KLB, Fed). Nhưng **độ dài không tuân**: p50 355, min 223, max 625 ký tự (yêu cầu 200–300); 3 bài mở đầu "Bài viết…"; bài `x` vẫn tóm tắt kèm câu bình luận thừa ("Đây là tin thể thao/lifestyle, không liên quan tài chính"). ⇒ 9b: cắt/kiểm hậu kỳ, bỏ tóm tắt cho `x`.
- **Nhóm/sub:** đúng phần lớn; ranh giới yếu như đã đo — tin đối ngoại (Thủ tướng hội kiến Myanmar, Chủ tịch QH thăm Hàn Quốc) bị xếp `2d` thay vì `1b`; "bảng lương 27 ngân hàng" hint 1 → `3d` chấp nhận được. 5/5 bài `x` đúng (lũ Nepal, máy bay Air India, sao Chelsea…).
- **Mã:** đúng với bài đơn chủ thể (PAP, KLB, NVL/KBC/PDR/AGG); **bài liệt kê** (bảng lương 17 mã, rổ FTSE 27 mã) gắn hết danh sách — đúng luật "một tin nhiều mã" nhưng làm ngành `ticker` thành nhiễu (FTSE ⇒ 8 ngành). Tầng 2 `lookup` có **false positive**: `USD` (mã niêm yết thật), `ACB` trong bài KLB (chỉ nhắc nơi làm cũ). Phân bố nhóm 3: 4 bài 0 mã · 3 bài 1–3 · 3 bài 4–9 · 2 bài ≥ 10.
- **Ngành:** hợp lý ở tin ngành rõ (VANTAI, NGANHANG, DANDUNG/XAYDUNG); lỏng ở vĩ mô quốc tế (Fed ⇒ `NGANHANG`, Iran ⇒ `DAUKHI` chấp nhận được) — cần luật "ngành = ngành VN chịu tác động" trong prompt hoặc chấp nhận.
- ⇒ Việc rẻ nên làm trước bộ gold (9b): (1) hậu kỳ `summary_ai` (cắt 300, bỏ "Bài viết", không tóm tắt `x`); (2) danh sách loại trừ tầng 2 (`USD`, `GDP`… có trong `market.security`) hoặc bỏ tầng 2 khi tầng 3 đã chạy; (3) đánh dấu bài liệt kê (≥ 5 mã) và không suy ngành từ mã cho chúng; (4) prompt: tin đối ngoại của lãnh đạo VN ⇒ nhóm 1.

## 6. Đợt sửa prompt + gắn mã theo chủ dự án (nhánh `fix/news-classify-prompt`, 16:05–16:30)

Chủ dự án chốt: sửa ở prompt, không hậu kỳ; **tổng quát hoá, ít luật, mỗi luật sắc** (model nhỏ không theo được nhiều luật vụn); độ dài tóm tắt theo **câu** (3–5) thay vì ký tự; danh sách mã dễ nhận sai (USD, WTO, WHO…); **trần số mã và số ngành** mỗi bài, chọn đáng chú ý nhất; Fed → `NGANHANG` là đúng (tôi rút nhận xét).

| Thay đổi | Chi tiết |
|---|---|
| Prompt (10 dòng) | Nhóm 1/2/3/x phân theo **chủ thể** của bài (Việt Nam / nước ngoài / doanh nghiệp niêm yết / không phải tin kinh tế) — ca lãnh đạo Việt Nam đi thăm tự rơi vào nhóm 1, không cần luật riêng; `summary_ai` 3–5 câu, giữ số, không mở đầu "Bài viết"; `tickers` = chủ thể chính, tối đa 5, quan trọng nhất trước; `industries` tối đa 3 chịu tác động trực tiếp nhất. Bỏ hẳn "200–300 ký tự" |
| `MAX_TICKERS = 5` | `apply` lọc niêm yết trước rồi cắt trần, đếm `tickers_ai_capped` |
| Tầng 2 | `news_tag.AMBIGUOUS` (đo trên 470 dòng lookup: USD 25 · HCM 20 · CEO 7 · SEA 3 · VND 2 · BOT 2 · PPP 1) + tiền tệ/chỉ số/viết tắt thường gặp; `load_listed` bỏ `security_type='index'` (VN30, HNX30…). Tầng 3 không bị giới hạn — AI đọc ngữ cảnh |
| Dọn kho | xoá **60** dòng `article_ticker via='lookup'` sai (USD/HCM/CEO/SEA/VND/BOT/PPP) + **2** dòng ngành `ticker` mồ côi; `lookup` còn 394 |
| Test | +4 (e54 nhập nhằng, e55 bỏ index, e59 luật prompt, e60 trần mã), 3 expected cũ cập nhật; **869 passed, 2 skipped** |

**Dry-run 12 bài với prompt mới (16:25):** 12/12 xanh; số câu 4·4·7·4·7·4·4·4·4·6·4·5 ⇒ **10/12 trong 3–5 câu**, nhưng câu dài hơn — tóm tắt trung bình ≈ **900 ký tự** (trước 355): model theo số câu bằng cách kéo dài câu. Trần mã chạy đúng (bài ETF 10.000 tỷ: 5 mã VIC/VHM/STB/FPT/HPG). Tổng thống Myanmar nhắc Viettel ⇒ `1/1b` (trước kiểu bài này bị `2d`). Tin Mỹ–Iran ⇒ `NGANHANG` (chấp nhận theo chủ dự án). **Chưa phân loại lại 230 bài đã chạy bằng prompt cũ** — chờ chủ dự án gọi tên (≈ 40 phút, $0,45).

**Vòng 2 luật tóm tắt (16:35, chủ dự án: "900 ký tự là quá dài — 3–5 câu ngắn gọn súc tích, ngôn từ chuyên nghiệp chuẩn nhà báo"):** luật đổi thành "3–5 câu ngắn, súc tích, giọng báo chí chuyên nghiệp; chỉ ý chính và con số quan trọng nhất". Dry-run 12 bài: số câu 5·5·6·4·5·5·4·3·4·4·4·4 (11/12 trong 3–5); **trung vị 620 ký tự ≈ 130 từ, max 760** (vòng 1: ≈ 900; prompt gốc theo ký tự: 355 nhưng cắt ý). Trần 5 mã và nhóm theo chủ thể giữ nguyên kết quả vòng 1. Chấp nhận mức này; muốn ngắn hơn nữa thì hạ "3–5 câu" xuống "3–4 câu".

## 7. Bộ gold — bản nháp (16:40–16:50, mở đầu lát 9b theo chủ dự án)

150 bài mẫu (seed 20260906, `published_at ≥ 2026-08-20`, thân ≥ 300 ký tự, 38/38/38/36 theo nhóm gợi ý, 8 nguồn) chia 3 lô, ba subagent **Opus** gán nháp độc lập theo tiêu chí prompt production. Kết quả: 150/150 hợp lệ (sub đúng nhóm, mã ∈ niêm yết, ngành ∈ 24, trần 5/3); nhóm 1: 58 · 2: 37 · 3: 43 · x: 12; **63 bài Opus đánh "khó"**; 27 bài có mã, 79 bài có ngành. File cho chủ dự án rà: [`eval/gold-draft-2026-09-06.xlsx`](eval/gold-draft-2026-09-06.xlsx) (5 cột CHỐT điền sẵn = nháp, dropdown nhóm/sub, tô vàng bài khó, sheet hướng dẫn); dựng lại bằng `eval/build_xlsx.py`.

**Ba lỗ hổng taxonomy mà cả ba annotator cùng vấp — cần chủ dự án quyết khi rà (ảnh hưởng đáp án hàng loạt):**
1. **Nhóm 2 không có sub cho doanh nghiệp / chính sách kinh tế nội bộ nước ngoài** (Apple–Tim Cook, Amazon–Nvidia, Heineken, visa Nhật, Thái Lan siết data center, kỷ luật lãnh đạo DNNN Trung Quốc) — hiện dồn tạm vào `2a`/`2d`. Phương án: thêm `2f` "Doanh nghiệp và chính sách kinh tế nước ngoài", hoặc quy ước cứng.
2. **Tin thị trường trong nước không phải Nhà nước, không phải DN niêm yết** (môi giới địa ốc, giá chung cư Hà Nội, giá vàng SJC, giá bạc) — không sub nào khớp; tạm `1e`/`1c`. Cần quy ước: vàng/bất động sản dân sinh thuộc `1c`/`1e` hay nhóm 3 (`3e`)?
3. **Bài điểm tin tuần / văn bản pháp quy phi kinh tế** (Quốc ca, Luật Chứng khoán do UBTVQH cho ý kiến — nhóm 1 hay 3?).

## 8. Lát 9b bắt đầu — bộ gold 400 bài và lần chấm đầu (2026-09-06 16:55–18:15)

**Bộ gold v2:** 400 bài (150 cũ + 250 mới; 100 mỗi nhóm gợi ý; seed 20260906), taxonomy mở rộng trước khi gán (`2f`, `3e` thị trường tài sản, nhóm 3 gồm DN chưa niêm yết, luật chủ thể). Hai lượt Opus độc lập (8 agent × 50 bài mỗi lượt) đồng thuận nhóm 99 % · sub 98 % · mã 97 % · ngành 94 % · cả bốn 89 %; 43 bài lệch do ba trọng tài Opus phân xử (19 theo lượt 1, 23 theo lượt 2, 1 nhãn mới); luật nhất quán `NGANHANG` cho `1c`/`2b` áp thêm 4 bài. Kết quả: nhóm 1: 126 · 2: 93 · 3: 127 · x: 54. Hồ sơ: [`eval/`](eval/README.md). Lưu ý: hai lượt cùng một model nên "đồng thuận" đo độ tự nhất quán, không phải hai người.

**Taxonomy sau khi gán** (news-pipeline §3 đã sửa cùng lượt): ngoài `2f`/`3e`, phân tích 800 nhãn + 311 ghi chú khó lộ thêm: DN Việt Nam chưa niêm yết (34 ghi chú, 98/251 nhãn nhóm 3 không mã) ⇒ nhóm 3 gồm DN chưa niêm yết, mã chỉ khi niêm yết; `2a` gồm tiền mã hoá; vàng/dầu/kim loại là `2c`, chỉ NHTW mới `2b`; `1b` phủ Đảng/địa phương với phép thử quy phạm↔quyết định cụ thể; mã ở bản tin thị trường chỉ khi tiêu đề/sapo nêu tên; tin tiền tệ luôn `NGANHANG`. Nợ cây ngành: ô tô/xe điện, holding, dịch vụ dầu khí.

**Chấm MiniMax M3 trên 400 bài gold** (`etl classify --dry-run --ids-file`, prompt TRƯỚC bốn câu làm sắc cuối, 17:14–18:13, 0 lỗi schema, 2 `repaired` mỗi lượt):

| | thinking adaptive | thinking disabled |
|---|---|---|
| Đúng nhóm | **376/400 = 94,0 %** | 366/400 = 91,5 % |
| Đúng nhóm + sub | **338/400 = 84,5 %** | 325/400 = 81,2 % |
| Nhãn `x` (54 bài gold) | precision 91 % · recall 74 % | 88 % · 70 % |
| Mã (127 bài gold nhóm 3) | P 56 % · **R 98 %** (fp 92) | P 51 % · R 97 % (fp 114) |
| Ngành (mọi bài) | P 46 % · **R 90 %** (fp 265); khớp tập 57 % | P 45 % · R 90 %; khớp tập 55 % |
| Đúng nhóm+sub theo `confidence` | < 0,7: 1/7 · 0,7–0,9: 99/126 (79 %) · ≥ 0,9: 238/267 (89 %) | < 0,7: 1/7 · 0,7–0,9: 56/94 (60 %) · ≥ 0,9: 268/299 (90 %) |

Nhầm nhóm nhiều nhất (adaptive): gold `x` → model `1` (9 bài: hướng dẫn dân sinh, thiên tai, PR bị coi là tin trong nước) · `1` → `3` (3) · `x` → `3` (3). Nhầm sub cùng nhóm: `1b`→`1a` (8 — đúng chỗ vừa làm sắc phép thử quy phạm↔quyết định), `3d`→`3a` (4), `3f`→`3e` (4), `2f`→`2c` (3).

**Đọc kết quả:** (1) thinking adaptive hơn disabled ≈ 3 điểm ở cả nhóm lẫn sub, chênh lớn nhất ở dải `confidence` 0,8–0,9 (79 % so 59 %) ⇒ **giữ adaptive**. (2) Model **bắt đủ nhưng gắn thừa**: recall mã 98 %, ngành 90 %; precision thấp vì prompt lúc chấm chưa có luật "mã chỉ khi tiêu đề/sapo nêu tên" và gold gán ngành chặt (chỉ ngành chịu tác động) — lượt chấm lại với prompt mới đang chạy (`pred-adaptive-v2`). (3) **Ngưỡng `confidence` đề xuất 0,8**: dưới 0,8 có 37/400 bài (9 %) đúng 65 %; từ 0,8 trở lên 363 bài đúng 86,5 % — đưa 9 % bài vào hàng rà tay là chi phí chấp nhận được. (4) `x` bị bỏ sót 26 % — model ngại loại tin; đáng xem lại câu định nghĩa `x` sau lượt chấm lại.

### 8.1 Chấm lại sau bốn câu làm sắc prompt (19:36–21:05, 400/400 bài, adaptive)

`pred-adaptive-v2-2026-09-06.jsonl`. Prompt mới = bốn câu chốt sau khi phân xử gold: nhóm 3 gồm DN Việt chưa niêm yết · `1b` phủ Đảng/địa phương (phép thử quy phạm↔quyết định cụ thể) · mã chỉ khi tiêu đề/sapo nêu tên · tin tiền tệ luôn `NGANHANG`; `2a` gồm tiền mã hoá, vàng/dầu là `2c`.

| Chỉ số (400 bài) | Prompt cũ | **Prompt mới** |
|---|---|---|
| Đúng nhóm | 94,0 % | 93,8 % |
| Đúng nhóm + sub | 84,5 % | **84,8 %** |
| Mã (127 bài nhóm 3): precision / recall | 56 % / 98 % | **65 %** / 93 % |
| Ngành: precision / recall | 46 % / 90 % | 43 % / **93 %** |
| `x` (54 bài): precision / recall | 91 % / 74 % | 92 % / **81 %** |

⇒ **Chốt dùng prompt mới:** mã gắn thừa giảm mạnh (fp 92 → 61), `x` bắt thêm 7 điểm, nhóm+sub nhích nhẹ. Đổi lại recall mã giảm 5 điểm (fn 3 → 9) — chấp nhận: gắn sót rẻ hơn gắn sai.

**Hai việc cho lát sau, đã đo, chưa làm** (chủ dự án chốt sổ 2026-09-06 tối):
1. **Ngành gắn thừa** — precision 43 %, khớp tập 51 %: model gắn 2–3 ngành gần như mọi bài, gold nhiều bài 1 ngành hoặc rỗng. Sửa bằng một câu: "mặc định 1 ngành; chỉ thêm ngành thứ 2–3 khi bài nói trực tiếp tới ngành đó".
2. **`1d` → `1b` nhầm 8 lần** (mới xuất hiện sau khi làm sắc `1b`): tin đầu tư công/hạ tầng bị kéo về "điều hành". Cần thêm vế cho phép thử: dự án, vốn đầu tư công, hạ tầng ⇒ `1d` dù văn bản là quyết định điều hành. `1a`→`1b` vẫn 8 lần.

**Chốt vận hành cho lát 9b tiếp theo:** thinking **adaptive**; ngưỡng `confidence` **0,8** (dưới ngưỡng 31/400 = 8 % bài, đúng 61 %; từ 0,8 trở lên 369 bài, đúng 87 %) ⇒ bài dưới 0,8 vào hàng rà tay; trần cắt giữ 3.000 ký tự (chưa có bằng chứng cần 4.000). **Chưa bật chạy tự động**, chưa phân loại lại 230 bài đã chạy bằng prompt cũ.

## 9. Lát 9b — làm hết phần thiết kế, KHÔNG bật live (chủ dự án 2026-09-06 tối: "làm hết từng phần, trừ bật dữ liệu live… thiết kế mọi thứ chạy ổn rồi dừng")

| Việc | Trạng thái | Ghi chú |
|---|---|---|
| (1) Hai chỉnh sửa prompt đã đo | ✅ `9a44009` | ngành **mặc định 1**, chỉ thêm 2–3 khi bài nói trực tiếp (nhắm precision 43 %); `1d` giữ tin đầu tư công/hạ tầng "kể cả khi văn bản là quyết định điều hành" (nhắm 8 ca `1d`→`1b`). Đo lại: §9.1 |
| (2) Móc lưới vào vòng `--loop` | ✅ `7f88008` — **mặc định TẮT** | `etl news --loop --classify N`: sau mỗi vòng thu thập gọi job `news.classify` với trần N (quota guard, `ops.llm_call` riêng); lỗi phân loại **không** giết vòng thu thập. Không truyền cờ ⇒ không gọi lần nào (test `test_loop_calls_classify_only_when_flag_set`). Chưa đăng ký task Scheduler |
| (3) Chạy toàn kho | ⏸️ **để chủ dự án gọi tên** | 7.797 bài chưa phân loại + 230 bài chạy bằng prompt cũ ≈ 22 giờ ≈ $15 quy giá |
| (4) Embedding (9b-2) | ✅ đo xong, **đề xuất dời sang lát 10** | `pg_trgm` (đã cài, chi phí 0) bắt **2,0 %** bài ở ngưỡng 0,6 và **5,9 %** ở 0,45 — gấp 4–12 lần khoá tiêu đề y hệt (0,5 %), kể cả cặp khác hẳn từ ngữ ("MSB chốt quyền chia cổ phiếu thưởng" ↔ "Một ngân hàng chốt quyền phát hành cổ phiếu thưởng", 0,52) ⇒ giá trị biên của embedding cho dedupe nhỏ; giá trị còn lại là tìm kiếm khái niệm cho chatbot. Ba phương án: [embedding-decision.md](embedding-decision.md) |
| (5) Nợ kỹ thuật | ✅ `050a648` | `LLMClient.close()` + context manager (chỉ đóng client tự tạo, không đóng client caller bơm vào) — cần cho chatbot lát 10; `run()` gọi close ở mọi nhánh |
| (5b) Ba ô thiếu trong cây ngành | ⏸️ **cần chủ dự án quyết** | ô tô/xe điện (VinFast phải mượn `THIETBI`), holding/đầu tư phi ngân hàng, dịch vụ dầu khí. Cây 6×24 do chủ dự án chốt từng vòng (industry-tree.md) và đổi cây kéo theo gán lại ngành cho ~1.500 mã ⇒ không tự sửa |

**Test sau toàn bộ:** `875 passed, 2 skipped` (+6 so với 869: close(), móc `--classify`, hai luật prompt, `--ids-file`).

**Sự cố vận hành đáng ghi:** lượt đo lại 400 bài mở lúc 21:03 **treo không ghi dòng nào** trong 13 phút dù tiến trình sống, quota còn 77 %, và một lời gọi thử riêng trả lời trong 0,6 giây ⇒ không phải model, không phải quota. Nhiều khả năng là bẫy **QuickEdit của console Windows** (bấm/chọn chữ trong cửa sổ `cmd` làm đóng băng tiến trình). Từ nay lượt đo dài mở bằng `Start-Process -WindowStyle Minimized` và đặt `PYTHONUNBUFFERED=1`.
