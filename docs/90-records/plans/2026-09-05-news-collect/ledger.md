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
