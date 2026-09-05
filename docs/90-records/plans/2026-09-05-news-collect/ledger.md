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

- Task 7: implementer (Sonnet) DONE — 8 file + `git grep` sweep 15 hit phân loại; tự đổi header "chưa cài đặt" ở news-pipeline/article-structure. Review (Sonnet) ✅ 7/7 mục (đối chiếu 9 số ký tự với e53), Chuẩn: Important — header đổi làm lệch `docs/20-design/README.md:12`. Fix (Sonnet): sửa dòng index, grep "chưa cài đặt" = 0. complete (commit `821e7d5`)
Mọi lượt dưới `ETL_DATABASE_URL` (user thuộc role `dlck_etl`, không superuser — reviewer kiểm `rolsuper=false`), kho production, 2026-09-06 01:21–03:11 VN (đêm thứ 7 rạng chủ nhật). Lượt dài chạy tách tiến trình qua `cmd` (log file trống vì stderr không vào file — stats ở `ops.etl_run`).

| AC | Bằng chứng | Kết quả |
|---|---|---|
| AC1 | `uv run pytest -q`: **782 passed, 2 skipped** (trước lát 729) | ✅ (số sau đợt sửa review ghi §3) |
| AC2 | `etl news --dry-run` 01:21 (`run_id 266`): 53/53 danh sách, **1.769 item, 1.757 mới** (kho trống), 12 gộp theo tiêu đề ngay trong lượt, `warnings` chỉ có feed `vietstock/741/chung-khoan/niem-yet` im > 7 ngày | ✅ |
| AC3 | lượt đầu 01:27–03:06 (`run_id 268`; `267` là lượt bị controller giết vì trần 10 phút của tác vụ nền, đóng sổ `failed`): `new 1.757 · articles_ok 1.736 · refused 21 · articles_failed 0 · calls 1.811 · retries 1`; kho: `article` 1.736 = `article_revision` 1.736, `article_source` 1.748, `article_ticker` 436; theo báo vneconomy 392 · vietstock 359 · tinnhanhck 347 · cafef 167 · nguoiquansat 156 · vietnambiz 137 · baochinhphu 99 · bnews 79; `published_at_src` feed 1.711 · url 4 · unknown 21 (CBTT); 3 bài đọc tay (Vietstock "Nhịp đập Thị trường 26/08…" 9.681 ký tự; BNews "Lịch chốt quyền trả cổ tức…" 561; TinnhanhCK "Quốc hội sẽ xem xét công tác nhân sự…" 4.228) tiêu đề và mở đầu khớp trang gốc — riêng TNCK mở đầu bằng chú thích ảnh (⇒ I4 review) | ✅ (kèm I4) |
| AC4 | lượt hai 03:07–03:11 (`run_id 269`): `items 1.769 · seen 1.748 · new 21 · articles_ok 0 · refused 21`, `revision version>1` = 0, không dòng mới — 21 "mới" chính là 21 URL từ chối lượt 1 bị tải lại (⇒ lỗ §4.6-VII, sửa ở §3) | ✅ (kèm lỗ) |
| AC5 | `article_ticker`: `url` 21 (mọi bài CBTT trừ sàn có mã: 0 thiếu) · `lookup` 415; nhóm 3 chưa chạy tag = 0, nhóm 1–2 mà ran = 0; 3 bài đọc tay đúng: TCB ("…tâm điểm là cổ phiếu TCB"), MBS, SDT (CBTT) | ✅ |
| AC6 | 12 tin có ≥ 2 báo (gộp theo tiêu đề), 0 tin ≥ 2 URL cùng báo; 5 cặp đọc tay đúng cùng tin (CafeF+NguoiQuanSat ×3, BNews+VietnamBiz, VietnamBiz+Vietstock); reviewer đọc độc lập cả 12 cặp: 12/12 đúng, khoá ngắn nhất 32 ký tự | ✅ |
| AC7 | `--loop` ≥ 24 giờ — **chưa**, bật sau khi vá lỗ §4.6-VII; số ghi bổ sung | ⏳ |
| AC8 | `etl news --backfill-sitemap --from 2026-08 --to 2026-08 --max-minutes 60` khởi động 03:11 (`run_id 270`) — số ghi khi xong | ⏳ |
| AC9 | `raw_payload` 8 báo: 117 dòng danh sách (text/html, khi hash đổi) + 42 dòng `refused` (too_short 14, no_container 28 — VnEconomy tạp chí/interactive 9 bài, CafeF video/infographic 4, Vietstock 1, VietnamBiz 1); **0** HTML bài thành công; 42 = 21 × 2 lượt (lỗ §4.6-VII) | ✅ (kèm lỗ) |
| AC10 | không có khoá; log không có token | ✅ |

**Ruling (AC3):** `published_at` của TinnhanhCK lấy ở `meta.cms-date` trên trang, sitemap `lastmod` chỉ dự phòng — vì đo 2026-09-05 `lastmod` là giờ SỬA (20:39 vs 09:18). Spec §5.7 và AC8 viết "`published_at` = `lastmod`" là câu trước khi đo; **không sửa spec** (§1.7), ghi đính chính ở đây; AC8 đối chiếu 3 bài theo `cms-date`, `lastmod` chỉ khi trang không có. Nếu sai: lệch giờ đăng vài giờ cho bài bị sửa — không mất dữ liệu.

## 3. Review toàn nhánh (Opus, hai trục, 2026-09-06 ~03:15) và đợt sửa

**Trục Chuẩn ❌ / Trục Spec ❌ trước đợt sửa.** Critical: **C1** registry xếp `tnck_sitemap` trước 3 trang chuyên mục, `items.setdefault` giữ bản đầu ⇒ 392/453 bài TNCK vào kho với `feed='sitemap'`, `group_from_feed` NULL, không chạy tầng 2 — ngược §4.6-III (test e56 còn chốt hành vi sai); **C2** `insert_article` không `ON CONFLICT (canonical_url)` ⇒ hai tiến trình song song (`--loop` + backfill) trùng URL là chết cả vòng và thoát `--loop`. Important: I1 `meta.cms-date` thiếu `content` ⇒ `TypeError` giết vòng; I2 backfill: sitemap tháng hỏng làm mất `stats`/`cursor`; I3 dedupe tiêu đề không sàn độ dài (khoá ngắn nhất kho 14 ký tự — gộp nhầm là mất nội dung); I4 TNCK caption `p.imgdesc` lọt (26/453 bài); I5 `--minutes` vượt tối đa một vòng + một nhịp; I6 README "dừng ở tầng đầu tiên" sai; I7 ledger thiếu §2 (đã bổ sung trên). Minor M1–M10 (Seen.load quét toàn bảng — đo 13 ms/1.863 URL, ngưỡng sửa ~100k dòng; dải test rộng; thiếu `startswith` 4 nguồn; CLI chưa loại trừ cờ chéo; URL sitemap literal năm cứng; ngày dry-run sai ở README §13.4; run 270 đang chạy; `feeds.json _meta` trạng thái cũ; roadmap "đang nạp"; test role chỉ phủ đường ghi).
**Lỗ §4.6-VII** (controller phát hiện ở AC4, reviewer đo hệ quả): bằng chứng từ chối 269 KB/dòng × 21 URL × 288 vòng ≈ **1,6 GB/ngày** nếu bật loop; guard tự vô hiệu; số AC7 bị đầu độc (`new` +21/vòng); tải A2 +6.000 lời gọi/ngày. **Ruling:** nhớ URL từ chối 7 ngày trong `Seen` (`refused_recent`, đếm `skipped_refused`), bằng chứng một dòng/URL/7 ngày — nhịp thử lại đổi 5 phút → 7 ngày, tinh thần §4.6-VII giữ.
**Ruling (C1 dữ liệu đã ghi):** 392 bài TNCK `feed='sitemap'` NULL nhóm là **gợi ý** (`group_from_feed`), lát 9 gán `group_no` bằng AI nên không mất gì; sau đợt sửa, controller chạy một UPDATE điền `group_from_feed`/`feed` cho bài TNCK có URL đang xuất hiện ở 3 trang chuyên mục (bằng chứng ghi dưới); phần còn lại để NULL.
**Triage Minor đã hoãn:** Task 1 `url = canonical` ở CBTT — giữ (load-bearing: href thật kèm `?utm_source`), thêm comment; Task 3 hai comment — gộp đợt sửa.

**Đợt sửa (một implementer Sonnet, TDD từng mục, commit `b9e57b8`):** C1 registry `tnck_sitemap` cuối + `merge_items` giữ bản có nhóm (test đơn vị + e56 sửa assert) · C2 `insert_article -> (aid, inserted)` với `ON CONFLICT (canonical_url) DO NOTHING`, mọi item bọc `except Exception` ⇒ `articles_failed` (Ctrl+C không bị bắt) · I1 `meta` thiếu `content` · I2 sitemap tháng hỏng ⇒ `months_failed`, exception mang `stats` · I3 `TITLE_MIN_CHARS = 30` · I4 `p.imgdesc` (TNCK text sạch 4.371 → 4.287; article-structure §2.9 cập nhật) · I5 `--minutes` không vượt hạn · I6 README "cả hai tầng" · lỗ §4.6-VII: `Seen.refused` 7 ngày, `refused_recent`/`skipped_refused`, `store_refused` một dòng/URL/7 ngày, áp cả backfill · M2 số đếm chính xác (CBTT 21, TNCK 98) · M3 `startswith` 4 nguồn · M4 CLI loại trừ chéo · M5 URL sitemap = mẫu `SITEMAP` · M6/M8/M9 tài liệu · M10 test role phủ đường đọc · 3 comment. Re-review có phạm vi (Sonnet): 18/18 ADDRESSED, 62 test e52–e58, toàn bộ **791 passed, 2 skipped** (+9); một lệch số test ở README (782) — controller sửa 4 file bằng sed cùng commit.
**Sửa dữ liệu C1 trên kho (controller, 04:03, 3 lời gọi + UPDATE):** 1.227 bài TNCK `feed='sitemap'` NULL nhóm (phần lớn là bài tháng 8 do backfill đang chạy — hợp lệ) ⇒ **98** bài có ở 3 trang chuyên mục được điền `feed`/`group_from_feed`/`ticker_step_ran`; 42 bài nhóm 3 chạy tầng 2 ⇒ **+11** mã. TNCK sau sửa: sitemap 1.129 · ck-quoc-te 104 · dau-tu 55 · chung-khoan 42.
Minor để lại (ruling): M1 `Seen.load` quét toàn bảng mỗi vòng (13 ms/1.863 URL; sửa khi ~100k dòng — nạp một lần khi mở `--loop`, nạp lại mỗi N vòng) · M7 run 270 đang chạy đúng (không phải rác).

## 4. Trạng thái bàn giao

- Nhánh `feat/news-collect` gộp `main` bằng `--no-ff` (**`8be6494`**, 2026-09-06 ~04:08); **791 passed, 2 skipped**; không migration (`0017` head).
- Kho production 04:05 VN: `news.article` ≈ 1.736 + backfill tháng 8 đang chạy (988 bài sitemap tới 04:03); `article_ticker` 447; `data_domain_state ('news', <báo>)` 8 dòng mốc 2026-09-06; `raw_payload` 117 danh sách + 42 từ chối (từ đợt sửa: một dòng/URL/7 ngày).
- **Nợ:** AC7 (tổng hợp `stats` sau ≥ 24 giờ `--loop`, có ngày làm việc — thứ 2 07/09); tải lại bài để bắt bản sửa (lát 12); sitemap BNews/NguoiQuanSat (lát 8b); `Seen.load` tối ưu khi ~100k dòng (M1); VnEconomy dạng tạp chí/interactive và CafeF video/infographic bị từ chối có chủ đích (article-structure §4).

## 5. Rulings (toàn bộ, theo thứ tự)

1. Rà tiền kiểm: `articles_failed == 0` trong test e56 là đúng với fake get; kiểm `grep -c <loc>` trước khi tin 244/245.
2. Task 1: `decode` chuẩn NFC; `time_from_url` VietnamBiz thử cả độ rộng ngày; test BCP `== 5` (fixture thật) — nếu sai: literal test.
3. Task 2: Vietstock giờ từ `p.pPublishTimeSource`; CafeF `%H` với nhãn PM; BNews NFC ở `_text`; khoảng độ dài siết ±5 %; hai chuỗi vắng thay bằng boilerplate thật.
4. Task 3: `decide` chỉ `seen` khi URL thô trùng; tiêu đề lưu = feed (CBTT = trang); cửa sổ `< WINDOW`.
5. Task 4: fake page ×9; seed 21 mã CBTT; HPG trong tiêu đề; chặn `_throttle` thay lọc dải; thêm test Ctrl+C giữa hai vòng.
6. Task 5: `cursor < to_month`; hạn giờ kiểm sau mọi URL; `SourceDown` mang stats.
7. Task 7: header "đã cài đặt" + đồng bộ `docs/20-design/README.md`.
8. AC3: `published_at` TNCK theo `cms-date`, `lastmod` dự phòng — spec §5.7/AC8 không sửa (lịch sử), đính chính ở ledger — nếu sai: lệch giờ đăng bài bị sửa.
9. Lỗ §4.6-VII: nhớ URL từ chối 7 ngày, bằng chứng một dòng/URL — nhịp thử lại 5 phút → 7 ngày — nếu sai: bài bóc hụt vì lỗi tạm thời chờ 7 ngày mới thử lại.
10. C1 dữ liệu: điền nhóm cho 98 bài đang thấy ở trang chuyên mục, phần còn lại NULL (gợi ý, lát 9 gán bằng AI) — nếu sai: thiếu tín hiệu `group_overridden` cho ~1.100 bài tháng 8–9.
11. Minor để lại: M1 `Seen.load`; Task 1 `url = canonical` ở CBTT (load-bearing, đã comment).
12. Controller tự sửa số test 782→791 ở 4 file tài liệu bằng sed (đợt sửa quên) — nếu sai: một số.
