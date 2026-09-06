# Ledger — lát 8b: backfill sitemap BNews + NguoiQuanSat

Nhánh `feat/news-backfill-sitemaps`, tách từ `main` `13d7a38` (lát 8 + docs). Spec duyệt 2026-09-06 sáng (`bf4feda`). Kiểm chứng: `PYTHONIOENCODING=utf-8 uv run pytest -q` từ `backend/`.

## 0. Trước khi chạy plan

- Đo 2026-09-06 07:00–08:00: [measure-sitemap-bnews-nqs-2026-09-06.md](measure-sitemap-bnews-nqs-2026-09-06.md).
- Task 0 (controller): 4 fixture + `CAPTURE-2026-09-05.txt` mục 2026-09-06; literal ghi trong plan.
- Mốc trước plan: **791 passed, 2 skipped** (bàn giao lát 8).

## 1. Tiến trình

| Task | Ai | Kết quả | Commit |
|---|---|---|---|
| 0 fixture | controller | xong | `6ac8ffe` |
| 1 registry | Sonnet impl + Sonnet review | Spec ✅ / Quality ✅, 0 vòng sửa; minor để lại: `collect` ngầm coi sitemap không-backfill là theo tháng (đúng vì NQS là backfill_only) | `6e0e0f1` |
| 2 parse_sitemap | Sonnet impl + Sonnet review; fix 1 vòng (Haiku) + re-review (Haiku) | Spec ✅; 1 Important plan-mandated (dòng test 154 ký tự, chép từ plan) đã sửa; minor để lại: `lastmod` naive sẽ bị `astimezone` coi là giờ hệ thống (code lát 8, chưa gặp) | `a89122e`, `f28958a` |
| 3 rule NQS template cũ | Sonnet impl + Sonnet review | Spec ✅ / Quality ✅, 0 vòng sửa; reviewer chạy `extract` trên hai fixture, khớp literal | `1b89196` |
| 4 backfill theo nguồn | Sonnet impl + Sonnet review (lần 1 đứt vì 401 OAuth, dispatch lại) | Spec ✅ / Quality ✅, 0 vòng sửa; impl sửa 2 lỗi trong test helper của plan (`rsplit` ngày NQS, thiếu `feed='sitemap'` ở INSERT mồi) — reviewer xác nhận không làm yếu assertion; minor để lại: `run_backfill` return sớm khi hết kỳ không `dispose` engine (khuôn lát 8), chưa test tháng 2 nhuận | `fe39ed3` |
| 5 CLI `--source` | Sonnet impl + Sonnet review | Spec ✅ / Quality ✅, 0 vòng sửa; toàn bộ **805 passed, 2 skipped** (+14 so với lát 8), 1 warning có sẵn của starlette testclient | `7292bd8` |

## 2. Nghiệm thu (Task 6)

Mọi lượt dưới credential production (`ETL_DATABASE_URL`, role `dlck_etl`), chạy tách tiến trình (`Start-Process cmd`), `--loop` lát 8 vẫn chạy song song suốt thời gian này. Giờ VN.

- **AC2** ✅ `etl news --dry-run` 07:48 (`run_id 318`): `lists_ok 53`, `lists_failed 0`, `sources_total 55`, `items 1.771`; log 0 lời gọi tới `bnews.vn/sitemap` hay `sitemap-article-` (hai nguồn `backfill_only` bị `collect` bỏ qua).
- **AC3 lượt 1** (07:52–08:53, `--from 2026-08 --to 2026-08 --max-minutes 60`, code trước đợt sửa `1e3845f`):
  - BNews `run_id 319`: `articles_ok 1.150`, `articles_failed 0`, `refused 7` (`too_short`), `periods_failed []`, `budget_hit true`, `cursor null` (tháng chưa trọn), lùi từ 31/08 tới ~24/08 — **≈ 19 bài/phút**, đúng ước 3,2 s/bài.
  - NguoiQuanSat `run_id 320`: `articles_ok 1.145`, `articles_failed 0`, `refused 4` (`too_short`), `periods_failed []`, `budget_hit true`, `cursor 2026-08-26` (6 ngày trọn 31→26/08). **0 lỗi 403 sau retry** trong 1.145 bài + 6 file ngày ⇒ A1 đứng vững ở tải này. 0 bài `no_title` ⇒ tháng 8/2026 toàn template mới.
  - Đối chiếu 3 bài mỗi nguồn (chọn ngẫu nhiên, seed 6): BNews `434743`/`434987`/`434786` — `published_at` DB (UTC) = `lastmod` sitemap 2026-8 (`18:01:30`, `10:01:49`, `21:39:36 +07`) 3/3, tiêu đề và 60 ký tự đầu đúng bài; NQS `313246`/`313499`/`313614` — `published_at` = ld+json `datePublished` trên trang tải lại 3/3 (`21:04:01`, `22:06:01`, `21:23:01 +07`). `feed='sitemap'`, `group_from_feed NULL`, `published_at_src='feed'` ✅
- **AC3 lượt 2+** (code đã sửa, nối con trỏ): `run_id 333` (BNews) · `334` (NQS) mở 08:55 — số ghi khi đóng sổ (dưới).
- **AC5** ✅ `load_cursor` trên kho thật sau lượt 1: `tinnhanhck → '2026-08'` (đọc từ tên job cũ `news.backfill_sitemap` của lát 8 — fallback đúng), `bnews → None`, `nguoiquansat → '2026-08-26'` — ba con trỏ độc lập. Lượt 2 NQS mở với `--from 2026-08` nối từ 25/08 (kiểm ở log lượt 334).
- **AC6** ✅ 08:55: mọi bài `feed='sitemap'` có `article_source.source_name` = `primary_source` (lệch 0/1.157 BNews, 0/1.152 NQS, 0/1.699 TNCK).
- **AC1** ✅ toàn bộ **806 passed, 2 skipped** (1 warning starlette có sẵn) sau đợt sửa.
- **AC4** — **bỏ theo ruling 6** (chủ dự án: backfill chỉ để test). Bằng chứng template cũ: test `test_nguoiquansat_old_template_2024_title_time_and_body` trên fixture thật + 3 bài 2021/2022/2024 bóc được lúc đo (file đo §NQS).
- **AC7** (tài liệu, `git grep`): ghi ở §5.

## 3. Review hai trục

**Review toàn nhánh (Opus, `13d7a38..01b5b0c`, hai trục báo riêng).** Trục Chuẩn: 3 Important — (1) `backfill_sitemap` để con trỏ vượt qua kỳ hỏng ⇒ với `--from/--to` chỉ nhận `YYYY-MM` không có cách nào chạy lại kỳ đó, test e57 đang khoá hành vi sai; (2) ca quyền M10 ở e55 chạy câu SQL cũ `job = :j` trong khi production là `ANY(:j)`; (3) news-pipeline §14.6 viết "mỗi nguồn đã chạy tháng 2026-08" trước khi AC chạy (§3.2). Minor: `Source(..., True)` nói sai với tinnhanhck; import `date` thừa; `fail=()` chết; `MONTH_KEY` lỏng hơn `MONTH`; `periods_desc` không cắt `today` cho nguồn tháng; feeds.json hai dòng gọn. Trục Spec: 7/8 chốt §4.2 đạt, §4.2-V nửa "lượt sau tự vá" chưa đạt (= Important 1); thiếu assert `sources_total == 55`; roadmap + `90-records/README` + `market-data-store.md:764` chưa cập nhật (Task 7 đang dở); không scope creep. Triage minor để lại (a)–(e) của các task: để lại cả, không chặn merge.

**Đợt sửa:** một dispatch Sonnet theo `final-fix-brief.md` (ruling 4 dưới), rồi một re-review có phạm vi.

**Kết quả đợt sửa** (`1e3845f` code+test, `d616122` docs): 8/8 ADDRESSED — cờ `frozen` trong `backfill_sitemap` (con trỏ dừng ở kỳ trọn cuối trước kỳ hỏng đầu tiên; test NQS: lượt 1 `cursor 2026-08-31`, lượt 2 đi lại từ 30/08, `skipped_seen 58`; test BNews kỳ đầu hỏng ⇒ `cursor None`); e55 chạy đúng câu `ANY(:j)`; §14.6 news-pipeline hạ về "đang nghiệm thu"; dọn 3 rác; `sources_total == 55`; feeds.json pretty-print; thêm ca 2024-02 = 29 ngày. Test cũ `test_month_fetch_failure…` đổi `cursor == "2026-08"` → `None` — hệ quả trực tiếp của ruling A (kỳ hỏng là kỳ đầu). Toàn bộ **806 passed, 2 skipped**.

## 4. Rulings

6. **Chủ dự án ~09:25:** "backfill chỉ để test… chỉ cần tất cả chạy ngon từ hôm nay" ⇒ dừng sau lượt 2 (run 333/334), không mở lượt mới, **bỏ AC4 chạy thật** (template cũ NQS đã chứng bằng fixture 2024 trong test e53 và 3 bài 2021/2022/2024 lúc đo), **không mở lát cho CafeF/VnEconomy/Vietstock** dù đo cùng ngày thấy có sitemap (ghi news/README §5.6 làm tra cứu, roadmap việc gấp [5] đóng). Nếu sai: chỉ mất thời gian chạy lại, con trỏ nối tiếp.
5. Cổng cắt con trỏ sau fix: `cursor <= periods[0]` ⇒ lọc `p < cursor`, TRỪ khi `--from/--to` xin đúng một kỳ và kỳ đó == con trỏ (chạy lại kỳ đó — giữ hành vi lát 8, AC5 có `skipped_seen`). Nếu sai: một lượt thừa trên kỳ đã xong, `Seen` lo.
4. Important 1 của review toàn nhánh → **phương án A**: sau kỳ hỏng đầu tiên, `cursor` đóng băng (các kỳ sau vẫn xử lý và ghi `periods_done`); lượt sau đi lại từ kỳ hỏng, `Seen` bỏ bài đã có. Đúng chữ spec §4.2-V, không thêm cờ CLI. Nếu sai: mỗi lượt vá tốn thêm ≤ 30 lời gọi sitemap. Minor `MONTH_KEY` lỏng và `periods_desc` không cắt `today` cho nguồn tháng: để lại (khoá luôn sinh từ `periods_desc`).
3. Chủ dự án (giữa Task 4): sàn model subagent là **Sonnet**, cấm Haiku — ghi CLAUDE.md §4.1 (`4b2f232`); Task 2 đã lỡ dùng Haiku cho fix một dòng + re-review (controller đã kiểm lại bằng awk + pytest).
2. Global Constraints "dòng ≤ 150 ký tự" là giới hạn mềm: e52/news_parse lát 8 đã có 10 dòng 152–170 (awk 2026-09-06). Dòng mới cố gắng ≤ 150, không sửa dòng có sẵn — nếu sai: chỉ style.
1. Plan lệch spec §3.1 một điểm: `backfill_sitemap` nhận `periods` đã cắt theo con trỏ (run_backfill tính), không nhận `from/to` — giữ cấu trúc lát 8, test qua `run_backfill`.

## 5. Trạng thái bàn giao
