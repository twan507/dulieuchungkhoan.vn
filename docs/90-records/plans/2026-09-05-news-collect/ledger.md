# SDD ledger — plan: docs/90-records/plans/2026-09-05-news-collect/plan.md

Sổ thực thi lát 8. Artifact subagent ở scratchpad ngoài repo (`…/scratchpad/sdd8/`). Nhánh `feat/news-collect`, gốc `main` = `3a47e9e` (sau lát 7b). Test trước lát: 729 passed, 2 skipped.

## 0. Rà tiền kiểm plan (2026-09-05 đêm)

| Cặp / task | Bên sản xuất → tiêu thụ | Kết quả |
|---|---|---|
| T1 → T3/T4/T5 | `Item(source, feed_slug, url, canonical_url, title, sapo_raw, published_at, published_at_src, group_from_feed, ticker_from_url, rule)` 11 trường | T3 `published_for`/`Seen` dùng `rule`, `published_at`, `title`, `url`, `canonical_url`; T4/T5 dựng `Item` qua `PARSERS` — khớp |
| T1 → T3 | `news_tag` import `CBTT_HREF`, `EXCHANGES` từ `news_parse` | T1 định nghĩa cả hai ở module-level — khớp |
| T2 → T4/T5 | `extract(html, rule) -> Extracted(title, sapo, content, published_at)`; `ExtractError.reason` | T4/T5 dùng đúng — khớp |
| T2 → T4 test | e56 dựng trang từ `RULES[rule].container/.title` bằng `_tag()` — selector có dấu phẩy (`vietnambiz` sapo) chỉ ở `sapo`, container/title đều đơn | khớp; `_tag` lấy phần trước dấu phẩy để phòng |
| T3 → T4/T5 | `insert_article(conn, item, ext, *, fetched_at, tickers)`, `Seen.decide -> (str, int|None)`, `Seen.remember`, `add_source -> bool`, `store_list_if_changed(..., content_type)`, `store_refused`, `upsert_domain_state(engine, set, wm)`, `load_listed` | T4/T5 gọi đúng tên/thứ tự — khớp |
| T4 → T5 | `_cleanup`, `_page`, `NAMES` import từ e56 vào e57 | e56 định nghĩa cả ba ở module-level — khớp |
| T4 → T5 | `SourceDown` mang `stats` (ruling plan) | T5 `raise SourceDown(msg, st)`; `run_backfill` đóng sổ với `e.stats` |
| T4 | test loop: dãy `clock` giả trong plan là dự kiến — implementer chỉnh theo số lần gọi thật, kỳ vọng 3 vòng + ngủ `[290, 0]` | ghi trong dispatch |
| T4 | e56 `test_feed_failures…`: 47 feed 503 ⇒ `lists_failed 47`, `lists_ok 6` (5 crawl + sitemap ở cycle 0) — nhưng cycle 0 sitemap có; 6 = cbtt + 3 tnck + bcp + sitemap ✓ | khớp |
| Toàn plan | subagent không commit; `.superpowers/` cấm; không migration | dispatch ghi rõ |

**Ruling (rà tiền kiểm):** (1) e56 `test_full_cycle…` kỳ vọng `articles_failed == 0` nhưng `_fake_get` trả 404 cho URL trong `dead=()` rỗng và trang tổng hợp cho mọi URL khác — kể cả bài BaoChinhPhu/VietnamBiz mà rule dựng từ `RULES` ⇒ đúng 0. (2) Fixture sitemap 245 URL nhưng test e52 kỳ vọng 244 sau khi bỏ trang chủ — kiểm `grep -c "<loc>"` trước khi tin. Không xung đột chặn. Bắt đầu Task 1.

## 1. Tiến trình

- Task 0: fixture chụp 2026-09-05 ~20:45 (19 file, `CAPTURE-2026-09-05.txt`), commit cùng plan.
- Task 1: implementer (Sonnet) DONE_WITH_CONCERNS — e52 12/12, `tests/etl` 463. **Ruling:** ba chỗ khác brief chấp nhận: `decode` chuẩn hoá NFC (BNews trả chuỗi không NFC/NFD — reviewer đo lại), `time_from_url` VietnamBiz thử cả độ rộng ngày 1–2 chữ số, test BCP `== 5` (fixture chỉ có 5 link bài — số "102 link bài" ở measure là regex lỏng; nếu sai: chỉ literal test). Review (Sonnet, tự chạy lại 463 xanh + đo byte fixture) ✅ Spec, Approved; Minor (deferred): `parse_cafef_cbtt` gán `url = canonical_url` (không nhất quán với hai parser kia, vô hại). complete (commit `5b77e4e`)
- Task 2: implementer (Sonnet) DONE — e53 11/11, `tests/etl` 474. Ba phát hiện trên fixture (đo 2026-09-05, ghi Task 7 sang article-structure): Vietstock `div.meta span.date` chỉ có giờ tương đối ("2 giờ trước") ⇒ giờ lấy từ `p.pPublishTimeSource` (`- %H:%M %d/%m/%Y`); CafeF `span.pdate` = `05-09-2026 - 17:09 PM` (24 giờ dán nhãn PM) ⇒ `%H:%M %p`; BNews tiêu đề dạng tổ hợp rời ⇒ NFC trong `_text`. Hai literal brief lấy nhầm cột text thô (vneconomy, nguoiquansat) sửa theo DOM. Review (Sonnet, tự chạy 474 + đo fixture) ✅ Spec; Chuẩn: Important — 6/9 khoảng độ dài rộng hơn ±5 % (số plan là dự kiến), Minor — 2 assert "vắng chuỗi" vô hiệu. **Ruling:** siết ±5 % quanh số đo thật; thay bằng chuỗi thật bị bỏ (`(Theo số liệu từ Tổng điều tra`, `Từ Khoá`). Fix round 1/5 (Sonnet): 11/11; controller đối chiếu từng dòng thay cho re-review. complete (commit `81c28be`)
- Task 3: implementer (Sonnet) DONE — e54+e55+s07 19 xanh, toàn bộ 764 passed / 2 skipped. **Ruling:** ba chỗ khác code mẫu plan chấp nhận — `decide` chỉ `seen` khi URL thô trùng (canonical trùng ⇒ `merge_url`, đúng seam §6), tiêu đề lưu = `item.title or ext.title` (khớp khoá dedupe; CBTT rỗng ⇒ fallback trang), cửa sổ `< WINDOW` (biên 48h00 là `new`); nếu sai: một luật dedupe, sửa một dòng. Review (Sonnet, chạy lại 764) ✅ Spec, Chuẩn: 2 Minor (deferred) — thiếu comment tại `<` WINDOW và `item.title` ưu tiên. complete (commit `5f245f7`)
- Task 4: implementer (Sonnet) DONE — e56 7 + e58 2 + e01 4 xanh, `tests/etl` 495, toàn bộ 773 passed / 2 skipped; 6 sửa phía test (helper `_tag` lồng thẻ + chữ số, hệ số ×9 cho 5 KB, seed 21 mã CBTT thật vào `market.security`, HPG vào tiêu đề trang vì tầng 2 chỉ quét tiêu đề+sapo, ngưỡng raw_payload 8 báo, dãy `clock` 9 giá trị) — code job nguyên văn plan. Review (Sonnet, chạy lại 495) ✅ Spec; Chuẩn: Important — thiếu test Ctrl+C giữa hai vòng; Minor — lọc `sleep` theo dải. Fix round 1/5 (Sonnet): thêm `test_ctrl_c_between_cycles_returns_130_without_a_dangling_run`, chặn `Fetcher._throttle` bằng monkeypatch ⇒ `slept == [290.0, 0.0]` nguyên văn; 8/8; controller đọc diff thay re-review. complete (commit `7a84f8b`)
- Task 5: implementer (Sonnet) DONE_WITH_CONCERNS — e57 5 + e58 3 + e56 7, `tests/etl` 502. **Ruling:** `cursor < to_month` (tháng đúng con trỏ chạy lại được, rẻ nhờ bỏ URL đã thấy) — plan viết `<=` mâu thuẫn test; ×9; `[-13:]`. Review (Sonnet, chạy lại 502) ❌ Spec: **Critical** — hạn giờ chỉ kiểm sau bài thành công (lỗi trong code mẫu plan, lệch khuôn `price_job`); Minor `calls/retries` = 0 khi `SourceDown`; Minor report đếm 6 ≠ 5 test. Fix round 1/5 (Sonnet): `_over_budget()` kiểm sau MỌI URL, gán calls/retries trước `raise`, +2 test (`refused` vẫn kiểm hạn; `--stop-before-open` dừng sau bài đang làm). Re-review có phạm vi (Sonnet): 3/3 ADDRESSED, 7 passed. complete (commit `13db81c`)

## 2. Nghiệm thu (Task 6)

