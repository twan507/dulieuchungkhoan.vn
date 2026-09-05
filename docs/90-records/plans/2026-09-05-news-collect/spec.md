# Spec — lát 8: thu thập tin tức không AI (47 feed + 6 crawl → `news.*`, dedupe không-AI, gắn mã tầng 1–2, backfill sitemap TinnhanhCK)

**Ngày:** 2026-09-05 tối · **Nhánh:** `feat/news-collect` · **Trạng thái:** chủ dự án duyệt thiết kế tóm tắt 2026-09-05 tối ("ok triển khai đi"); spec này là bản ghi đầy đủ
**Tiền đề:** [roadmap — Điểm vào cho lát 8](../../../00-overview/roadmap.md) · [news-pipeline.md](../../../20-design/news-pipeline.md) (thiết kế đã duyệt, không thiết kế lại) · [news/README.md](../../../10-sources/news/README.md) · [article-structure.md](../../../10-sources/news/article-structure.md) · [feeds.json](../../../10-sources/news/feeds.json) · migration [`0007_news.py`](../../../../database/migrations/versions/0007_news.py)
**Brainstorm:** 5 câu, chủ dự án chốt 2026-09-05 tối — ghi ở §4. Số đo trước spec: [`measure-news-2026-09-05.txt`](measure-news-2026-09-05.txt).

Tiêu chí xuyên suốt: **kho là bản ghi nội dung tại thời điểm nhận, bất biến** (news-pipeline §9.1, §9.4); **mọi thứ nguồn tự khai về chính nó đều phải kiểm bằng dữ liệu** (7 cạm bẫy nguồn tin); và **tối ưu tốc độ dev** — lát này chỉ làm phần không có AI, chạy thử 1–2 ngày lấy số dedupe rồi merge.

---

## 1. Vì sao lát này, và lát này là gì

Miền `news` trống hoàn toàn: 5 bảng của `0007` đều 0 dòng, chưa có dòng code nào. Lát 8 dựng **khung thu thập + chuẩn hoá + lưu toàn văn + dedupe không-AI + gắn mã tầng 1–2**, đúng bước 4 trong "Việc tiếp theo" của news-pipeline §14; lưới AI, tầng 3, `summary_ai`, embedding là lát 9.

| Thành phần | Nội dung |
|---|---|
| Job `python -m etl news` | một lượt thu thập: 47 feed RSS + 4 trang danh sách (CafeF CBTT, 3 chuyên mục TinnhanhCK, BaoChinhPhu chỉ đạo điều hành) + sitemap tháng hiện tại của TinnhanhCK → chuẩn hoá → dedupe → tải bài mới → bóc → ghi 5 bảng |
| `--loop [--minutes N]` | vòng lặp chạy tay (D-2 §4.2): nhịp **5 phút**, mỗi vòng là một `etl_run`; sitemap mỗi 3 vòng; Ctrl+C dừng sạch |
| `--backfill-sitemap --from YYYY-MM [--to YYYY-MM] [--max-minutes] [--stop-before-open]` | kéo lịch sử TinnhanhCK từ sitemap tháng (đo: lùi được tới **2015-06**), con trỏ theo tháng, mỗi bài một giao dịch |
| `--dry-run` | tải feed/danh sách, chuẩn hoá, dedupe theo kho, **không** tải bài, không ghi |
| `--sources a,b` | lượt con theo tên báo (không guard, không đụng `data_domain_state`) |

Không migration: 5 bảng `0007` đủ. Không AI. Không đăng ký task (D-2).

## 2. Dữ kiện đã đo vs giả định *(§4.8 bước 0)*

### 2.1 Đã đo — 2026-09-05 20:15–20:30 (thứ 7), ~120 lời gọi

| Dữ kiện | Bằng chứng |
|---|---|
| **47/47 feed `200` có item**; encoding đúng tài liệu 13/08: BNews UTF-16LE thật (đếm null byte), VietnamBiz UTF-8 dù prolog khai `utf-16`; BaoChinhPhu `pubDate` dạng `9/5/2026 1:30:00 PM` (không RFC 822, không múi giờ); VietnamBiz `pubDate` rỗng cả 30 item, giờ từ URL parse được (`2026-09-05 20:15`, đúng lúc đo) | measure-news §1 |
| Feed im lâu: Vietstock `741/niem-yet` bài đầu **18 ngày** (2026-08-18), `742/kim-loai` 5 ngày; còn lại ≤ 2 ngày (thứ 7) | measure-news §1 |
| **6 nguồn crawl còn đúng cấu trúc:** CafeF CBTT 21 link `/du-lieu/{MÃ}-{id}/…chn?utm_source=du-lieu` (mã trong URL, có `utm_source` phải bỏ); 3 chuyên mục TinnhanhCK ~180 link bài `…-post{id}.html`; BaoChinhPhu 102 link bài | measure-news §2 |
| **Bộ bóc theo selector article-structure còn đúng 8/8 nguồn** (container + tiêu đề có; text sạch 1.953–7.806 ký tự); CafeF CBTT `#newscontent` 367 ký tự, tiêu đề `SGP: Báo cáo tài chính bán niên năm 2026 (công ty mẹ)` | measure-news §3 |
| **Link rot trong vòng một giờ:** bài CafeF `…18826090514012.chn` trả `200`/100 KB lúc 20:20 (container chỉ có "TIN MỚI"), `404`/3 KB lúc 20:28 — đúng lý do news-pipeline §9.1 | measure-news §5 |
| **Sitemap TinnhanhCK:** `news-{YYYY}-{M}.xml` lùi tới **2015-06** (1.414 URL), 2020-09 (2.167), 2024-01 (1.750), 2026-09 (243 tới 05/09); `lastmod` = giờ đăng thật `+07:00`, phân bố đều theo ngày; xếp **tăng dần** theo giờ đăng; 🔴 **phần tử đầu tiên của mọi file tháng có `lastmod` = giờ sinh file** (20:18 tối nay, ở cả 4 tháng) — phải bỏ; file tháng lẫn vài bài đầu tháng kế (2024-01 có bài 2024-02-02) | measure-news §4 |
| Lược đồ thật `0007` (đọc migration, không tin văn bản §9.3): `article(article_id, canonical_url UNIQUE, primary_source, feed, published_at NULL được, published_at_src CHECK ('feed','url','unknown'), fetched_at, group_no, group_from_feed, sub CHECK 20 mã, group_overridden, confidence, classified_from, content_chars, ticker_step_ran, labels)` · `article_revision(article_id, version, title, sapo, summary_ai, content, content_fetched_at, tsv GENERATED)` PK `(article_id, version)` · `article_source(article_id, source_name, url UNIQUE toàn cục)` · `article_ticker(article_id, security_id, via CHECK ('url','lookup','ai'))` PK có `via` · `trade_name` | migration |
| Role `dlck_etl` có `SELECT, INSERT, UPDATE, DELETE` trên `news.*` (`0009`) | migration |
| `market.security(security_id, ticker, exchange, status IN ('listed','delisted'))` — danh sách mã cho tầng 2 = `status = 'listed'` | `0002` |
| Khuôn tái dùng: `http_fetch.open_fetcher(classify, get=, sleep=, headers=, rng=)` (giãn cách ngẫu nhiên 1–5 s, lát 7b) · `omo_store.open_run/close_run` · `series_store.hash_text` · `price_job._next_open` (08:45 ngày giao dịch kế) · `staging.raw_payload` `content_type='html'` | code |

### 2.2 Giả định — CHƯA kiểm

| # | Giả định | Kiểm ở đâu | Nếu sai |
|---|---|---|---|
| A1 | Tỷ lệ dedupe thật ~3,5× (news-pipeline §9.2) | **AC7** — chính là mục đích chạy thử 1–2 ngày | không ảnh hưởng lát này; là số cho ngân sách lát 9 |
| A2 | Tải bài ở nhịp 5 phút không bị chặn: ~570 bài/ngày + 51 lời gọi danh sách/vòng × 288 vòng ≈ 15.000 lời gọi/ngày rải 8 host, giãn cách 1–5 s | AC7 (đếm HTTP ≠ 200 theo host) | hạ nhịp danh sách 10 phút; CafeF CBTT giữ ≤ 15 phút |
| A3 | Sitemap các tháng 2015–2026 đều cùng cấu trúc và bài cũ còn trả `200` với selector hiện tại | AC8 trên một tháng 2026-08; tháng xa hơn lộ khi chạy backfill thật | bài `404`/bóc từ chối được đếm, không dừng lượt |
| A4 | Hai template BNews (đoạn văn là text node trần) và HTML comment BaoChinhPhu — luật đã ghi ở article-structure §2.6, §3.1 — vẫn đúng | test bóc trên fixture chụp 2026-09-05 | sửa luật bóc từng nguồn, không đổi kiến trúc |

## 3. Phạm vi

### 3.1 Trong phạm vi

- Registry nguồn `news_registry.py`: đọc 47 feed từ `feeds.json` (chủ duy nhất của danh sách feed — như `wichart_registry` đọc khối Python trong wichart.md) + 6 nguồn crawl; "của mình": tên báo chuẩn (`cafef`, `vietstock`, `vneconomy`, `vietnambiz`, `bnews`, `nguoiquansat`, `baochinhphu`, `tinnhanhck`), `group_from_feed` theo nhóm feed, `kind` (`rss` | `cafef_cbtt` | `tnck_category` | `tnck_sitemap` | `bcp_list`).
- `news_fetch.py`: `classify` theo `kind` (feed: `200` + XML có `<item>`; danh sách HTML: `200` + ≥ 1 link bài; bài: `200` + độ dài ≥ 5 KB — dưới đó là trang lỗi/soft-404 như ca CafeF 20:28); tải qua `http_fetch`, một `Fetcher` cho trọn lượt; decode theo đếm null byte.
- `news_parse.py` (thuần): item từ RSS/sitemap/danh sách; **URL canonical** (bỏ `utm_*`, `gidzl`, fragment, chuẩn scheme `https`, bỏ `www.`? — **không**, giữ host nguyên văn; `http://vietstock.vn` → `https://`); **giờ đăng 4 luật** (RFC 822 · BaoChinhPhu `M/D/YYYY h:mm:ss AM/PM` +07 · VietnamBiz từ URL `YYYY M DD HHMMSS` · sitemap ISO `+07:00`) với `published_at_src` `'feed'` (giờ do nguồn khai ở feed/sitemap/danh sách) · `'url'` (VietnamBiz, BaoChinhPhu khi thiếu) · `'unknown'`; **tiêu đề chuẩn hoá** cho dedupe: NFD bỏ dấu + `đ→d`, chữ thường, chỉ giữ `[a-z0-9]`, bỏ tiền tố `(chinhphu.vn)`/`(đtck)`/`bnews`.
- `news_extract.py` (thuần): tầng 0 chọn container theo selector từng nguồn; tầng 1 **xoá node `Comment` trước** (article-structure §3.1), decode entity rồi strip tag; tầng 2 bỏ boilerplate theo bảng selector từng nguồn (§2.1–2.9) + luật văn bản (`\.\.>>\s*` TinnhanhCK, tiền tố `(Chinhphu.vn) - `, nhãn `BNEWS`); duyệt **text node** (không `find_all('p')` — bẫy BNews); chuẩn `\s+` → một dấu cách; trả `Extracted(title, sapo, content, published_at?)` với giờ từ trang cho CafeF (`span.pdate`), BaoChinhPhu (`div.detail-time`), TinnhanhCK (`meta.cms-date`), Vietstock (`div.meta span.date`), VnEconomy (`time.article-meta__time`), VietnamBiz (`span.vnbcba-time`), NguoiQuanSat (`span.sc-longform-header-date`); BNews không có giờ trên trang (lấy từ feed). **Từ chối** (`ExtractError`) khi không thấy container, hoặc text < 100 ký tự — trừ `cafef_cbtt` (được phép ngắn, `classified_from` để lát 9 đặt).
- `news_tag.py` (thuần): tầng 1 `url` — mã từ `/du-lieu/{MÃ}-{id}/` của CafeF CBTT, loại `HNX|HOSE|UPCOM`; tầng 2 `lookup` — `\b[A-Z][A-Z0-9]{2}\b` trên **tiêu đề + sapo**, đối chiếu tập `ticker` của `market.security` `status='listed'` (nạp một lần mỗi lượt). Chỉ chạy khi `group_from_feed == 3`; `ticker_step_ran = true` khi đã chạy (kể cả 0 mã).
- `news_store.py`: dedupe + ghi. Thứ tự cho mỗi item: (1) `article_source.url` đã có ⇒ bỏ qua (idempotent); (2) `article.canonical_url` đã có ⇒ thêm `article_source`; (3) tiêu đề chuẩn hoá trùng với một `article` có `published_at` (hoặc `fetched_at`) trong **±48 giờ** ⇒ gộp: thêm `article_source`, không tải bài; (4) còn lại là **bài mới** ⇒ tải, bóc, `INSERT article` + `article_revision v1` + `article_source` (URL feed) + `article_ticker`. Bằng chứng: XML/HTML danh sách vào `raw_payload` **khi hash đổi** (endpoint_key = URL danh sách); HTML bài **chỉ khi bóc từ chối** (`meta.refused`). `add_revision(article_id, extracted)` có sẵn và được test (so hash `content`, tăng `version`) nhưng lát này **không** tải lại URL đã có (§3.2).
- `news_job.py`: khuôn `open_run` ngay trước `try` (như `series_job`), `KeyboardInterrupt` ⇒ `failed: dừng tay (Ctrl+C)` exit 130; stats §5.5; `data_domain_state ('news', <báo>)` mốc = ngày VN lượt, đẩy sau `close_run` cho các báo có lượt danh sách thành công (không đẩy khi `--sources`/`--dry-run`/backfill).
- `--loop`, `--backfill-sitemap`, `--dry-run`, `--sources`; CLI trong `__main__`.
- Chạy thử `--loop` 1–2 ngày (D-2), đo A1/A2, ghi ledger + news-pipeline §12.
- Tài liệu §8.

### 3.2 Ngoài phạm vi — ba loại *(§1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| Lưới AI phân loại, `summary_ai`, tầng 3 gắn mã, embedding, `trade_name` seed | **Đã có đường khác** | lát 9 (news-pipeline §7, §8 tầng 3, §9.5) |
| Sitemap BNews, NguoiQuanSat | **Đã có đường khác** | lát 8b — chưa đo (§4.1 câu 1c) |
| Tải lại bài đã có để bắt bản sửa (`version` > 1) | **Loại có chủ đích** | chưa có tín hiệu nào cho biết bài nào bị sửa; tải lại toàn kho định kỳ là 570 lời gọi/ngày thêm; lát 12 xét lấy mẫu. Đường ghi `add_revision` vẫn có và test |
| Lưu HTML bài thô / HTML container | **Loại có chủ đích** | §4.4 (chủ dự án chốt (a)); news-pipeline §9.2 |
| Dedupe theo nội dung (simhash) | **Loại có chủ đích** | §4.3 (b); lát 9 đo bằng embedding |
| Lịch chạy, task Scheduler | **Đã có đường khác** | lát 13; [4d] |
| Tách từ tiếng Việt, trần 3.000/4.000, ngưỡng `confidence` | **Đã có đường khác** | lát 9; lát này lưu toàn văn không cắt, `content_chars` NULL |
| Bản quyền | — | news-pipeline §9.7 một dòng; không mở lại |

## 4. Quyết định *(§4.8 — chủ dự án chốt 2026-09-05 tối)*

### 4.1 Phạm vi: thu thập hiện tại + backfill sitemap TinnhanhCK *(câu 1 → (c))*
Loại (a) chỉ hiện tại: bỏ lỡ dữ liệu chỉ còn khi họ giữ sitemap. Loại (b) gộp cả BNews/NguoiQuanSat: chưa đo, phình lát. **Đảo ngược:** BNews/NguoiQuanSat đo xong ⇒ lát 8b thêm bộ đọc sitemap, cùng đường ghi.

### 4.2 Cách chạy thử: tiến trình `--loop` chạy tay, 1–2 ngày *(câu 2 → (a); chủ dự án rút "1 tuần" xuống 1–2 ngày để tối ưu tốc độ dev)*
Loại (b) bật task: thêm ngoại lệ [4d]. Loại (c) chạy lẻ: không có số dedupe. Vòng lặp **không** là scheduler của lát 13; job một lượt bên trong mới là thứ lát 13 xếp lịch. **Đảo ngược:** lát 13 thay `--loop` bằng bảng lịch.

### 4.3 Dedupe: URL canonical + tiêu đề chuẩn hoá trong 48 giờ *(câu 3 → (b))*
Loại (a) chỉ URL: không bắt tin 8 báo cùng đăng. Loại (c) simhash: thuật toán mới cần dò ngưỡng, lát 9 có embedding. Gộp nhầm không mất URL nào (`article_source` giữ hết). **Đảo ngược:** lát 9 đo tỷ lệ gộp nhầm bằng embedding > 5 % ⇒ thu hẹp cửa sổ hoặc thêm điều kiện cùng nhóm.

### 4.4 Bằng chứng thô: không lưu HTML bài; XML/HTML danh sách khi hash đổi; HTML bài khi bóc từ chối *(câu 4 → (a), chủ dự án uỷ quyền)*
Đo: HTML bài 97–446 KB × ~570/ngày ≈ 40–55 GB/năm — không hợp VPS 60 GB. Text bóc được lưu bất biến ở `article_revision` là thứ cần bảo vệ. **Đảo ngược:** lát 12 cần bóc lại toàn kho khi luật đổi ⇒ lưu HTML container (b) từ lúc đó.

### 4.5 Guard: không từ chối cả lượt; tally theo feed và bài; cảnh báo theo ngưỡng lát 6–7 *(câu 5, trợ lý đề xuất, chủ dự án đồng ý)*
Khác series: tin bỏ lỡ là mất thật (feed giữ 20–50 bài). Ngưỡng cảnh báo: feed lỗi > 20 %, bóc từ chối > 5 %, feed im > 7 ngày theo `pubDate` bài đầu (VietnamBiz theo URL) — ghi `stats.warnings`, không chặn.

### 4.6 Điểm trợ lý tự chốt khi viết spec (ghi §9 để rà)

| # | Chốt | Vì sao | Đảo ngược khi |
|---|---|---|---|
| I | Tầng 2 chỉ quét **tiêu đề + sapo**, không quét toàn văn | toàn văn nhắc mã "tiện thể" rất nhiều (bài tổng hợp 24h kể 20 mã); tiêu đề + sapo là nơi mã thật sự là chủ đề; tầng 3 (AI) đọc toàn văn ở lát 9 | lát 9 đo thấy tầng 2 sót > 20 % mã mà tầng 3 tìm ra ⇒ mở rộng sang 1.000 ký tự đầu |
| II | `published_at_src = 'feed'` cho cả giờ từ sitemap `lastmod` và giờ đọc trên trang bài; `'url'` cho VietnamBiz và BaoChinhPhu-từ-URL; `'unknown'` khi không có | CHECK của `0007` chỉ có 3 giá trị; thêm giá trị = migration; "feed" = "metadata nguồn khai" | lát 12 cần phân biệt nguồn giờ ⇒ migration thêm `'page'`, `'sitemap'` |
| III | Bài mới của TinnhanhCK lấy qua 3 trang chuyên mục **trước**, sitemap tháng hiện tại **sau** (mỗi 3 vòng) — trang chuyên mục cho `group_from_feed`, sitemap chỉ vá lỗ (`group_from_feed` NULL) | sitemap không có chuyên mục (README §5.2) | — |
| IV | Mỗi vòng `--loop` là một `etl_run` riêng (288 dòng/ngày), job `news.collect`; backfill là `news.backfill_sitemap` | lát 12 đọc từng lượt; khuôn intraday lát 7b | — |
| V | Cửa sổ dedupe tiêu đề so theo `coalesce(published_at, fetched_at)` của bài đã có và của item mới | `published_at` NULL được (VietnamBiz khi URL không parse) | — |
| VI | CafeF CBTT: khoá dedupe thêm `(mã, tiêu đề chuẩn hoá)` trong 48 giờ (README §5.1: hai ID cùng tiêu đề) — chính là luật (3) §3.1 áp cho cùng nguồn | — | — |
| VII | Bài tải về < 5 KB hoặc bóc từ chối ⇒ đếm `refused`, lưu bằng chứng, **không tạo `article`** (không có dòng "rỗng") | bài không có nội dung không có giá trị tra cứu; URL sẽ được thử lại ở lượt sau chừng nào còn trong feed (không có ở `article_source` nên không bị coi là đã thấy) | lát 12 muốn ghi nhận "bài đã gỡ" ⇒ thêm trạng thái |
| VIII | Backfill sitemap: `group_from_feed` NULL, `feed` = `'sitemap'`, `fetched_at` = lúc tải; **mỗi bài một giao dịch**, con trỏ = tháng đã xong ở `stats.cursor` của lượt `success`/`failed` gần nhất; trong tháng URL đã có ở `article_source` bị bỏ qua nên chạy lại rẻ | khuôn backfill giá | — |
| IX | Ước tải backfill: ~1.700 URL/tháng × ~3,2 s ≈ **1,5 giờ/tháng**, 2015-06 → 2026-08 ≈ 135 tháng ≈ **200 giờ** — chủ dự án chọn `--from` lúc chạy; lát này chỉ nghiệm thu **một tháng** (2026-08) | §4.3 CLAUDE.md: chạy đúng tải kế hoạch, không ép | — |

## 5. Thiết kế

### 5.1 File và ranh giới

| File | Trách nhiệm | Phụ thuộc |
|---|---|---|
| `backend/etl/news_registry.py` | `Source(name, kind, url, group_from_feed, feed_slug)`; `build()` đọc `docs/10-sources/news/feeds.json` (đường dẫn như `wichart_registry.WICHART_MD`) — 47 feed + 6 crawl = **53 nguồn**, kiểm số đếm khớp `_meta` | feeds.json |
| `backend/etl/news_fetch.py` | `classify_feed/list/article`, `open_news_fetcher(get, sleep, rng)`, `fetch_text(f, url, kind) -> (text, status, bytes)` decode theo null byte; URL chuẩn hoá `http→https` trước khi gọi | `http_fetch` |
| `backend/etl/news_parse.py` | `Item(source, feed_slug, url, canonical_url, title, sapo_raw, published_at, published_at_src, group_from_feed, ticker_from_url)`; `parse_rss(text, source) -> list[Item]`, `parse_sitemap(text)`, `parse_cafef_cbtt(html)`, `parse_tnck_category(html, group)`, `parse_bcp_list(html)`; `canonical_url(u)`; `parse_pubdate(s, source)`; `vnbiz_time_from_url`, `bcp_time_from_url`; `norm_title(t)` | stdlib `xml.etree`, `bs4` |
| `backend/etl/news_extract.py` | `RULES[source] = Rule(container, drop_selectors, title, sapo, time, time_format)`; `extract(html, source) -> Extracted(title, sapo, content, published_at)`; `ExtractError(reason)` với `reason ∈ {no_container, too_short, no_title}` | `bs4` |
| `backend/etl/news_tag.py` | `tickers_from_url(url) -> list[str]`; `tickers_lookup(title, sapo, listed: set[str]) -> list[str]`; `load_listed(conn) -> dict[ticker, security_id]` | — |
| `backend/etl/news_store.py` | `Seen` (tập URL đã có, tập `(norm_title, ts)` 48 giờ — nạp một lần đầu lượt bằng 2 SELECT); `decide(item, seen) -> 'seen' | 'merge_url' | 'merge_title' | 'new'`; `insert_article(conn, item, extracted, tickers) -> article_id`; `add_source(conn, article_id, source_name, url)`; `add_revision(conn, article_id, extracted) -> bool`; `store_list_if_changed(conn, source, url, text, run_id)`; `store_refused(conn, source, url, html, reason, run_id)`; `upsert_domain_state(engine, sources, watermark)` | `series_store.hash_text` |
| `backend/etl/news_job.py` | `collect(engine, sources, dry_run, get, sleep, now, rng) -> (stats, rc)`; `run(sources=None, dry_run=False, loop=False, minutes=None, get=None, sleep=time.sleep, now=None)`; `backfill_sitemap(engine, from_month, to_month, max_minutes, stop_before_open, get, sleep)`; `run_backfill(...)` | trên + `omo_store`, `price_job._next_open` |
| `backend/etl/__main__.py` | `news` với `--dry-run`, `--sources`, `--loop`, `--minutes`, `--backfill-sitemap`, `--from`, `--to`, `--max-minutes`, `--stop-before-open` | |
| `backend/tests/etl/test_e52_news_parse.py` · `e53_news_extract.py` · `e54_news_tag.py` · `e55_news_store.py` · `e56_news_job.py` · `e57_news_backfill.py` · `e58_news_cli.py` | seam §6 | fixture `tests/etl/fixtures/news/` |

### 5.2 Một vòng `collect`

```
registry 53 nguồn
 └─ với mỗi nguồn danh sách (47 feed · cafef_cbtt · 3 tnck_category · bcp_list · [tnck_sitemap mỗi 3 vòng]):
      fetch_text → classify → parse_* → list[Item]        (lỗi ⇒ tally.feed_failed, tiếp)
      store_list_if_changed(raw XML/HTML)
 └─ items = gộp theo canonical_url trong lượt (5 slug VnEconomy về một kênh)
 └─ seen = Seen.load(conn)                                 (2 SELECT: url của article_source; (norm_title, ts) 48 giờ)
 └─ với mỗi item: decide →
      'seen'        : tally.seen
      'merge_url'   : add_source                            (tally.merged_url)
      'merge_title' : add_source                            (tally.merged_title)
      'new'         : fetch_text(article) → extract → tag → insert_article + revision + source + tickers
                      (fetch lỗi ⇒ tally.article_failed; extract từ chối ⇒ tally.refused + store_refused)
      mỗi item 'new' là MỘT giao dịch (bài hỏng không kéo lùi bài khác; Ctrl+C không mất bài đã ghi)
 └─ close_run(stats) → upsert_domain_state cho báo có ≥ 1 danh sách thành công
```

`--dry-run` dừng sau `decide`, in tally (`new` = số bài sẽ tải). `--sources` lọc registry theo tên báo.

### 5.3 Luật thời gian và URL (§2.1 README, đo lại 05/09)

| Nguồn | `published_at` | `src` |
|---|---|---|
| RSS RFC 822 (CafeF, Vietstock, VnEconomy, BNews, NguoiQuanSat) | `email.utils.parsedate_to_datetime`; thiếu tz ⇒ +07 | `feed` |
| BaoChinhPhu RSS | `M/D/YYYY h:mm:ss AM/PM` +07; hỏng ⇒ URL `102YYMMDDHHMMSS…` | `feed` / `url` |
| VietnamBiz RSS | `pubDate` rỗng ⇒ URL `YYYY M DD HHMMSS` (M 1–2 chữ số, thử cả hai); hỏng ⇒ NULL | `url` / `unknown` |
| TinnhanhCK sitemap | `lastmod` ISO `+07:00`; **bỏ phần tử đầu tiên** của file | `feed` |
| TinnhanhCK chuyên mục · CafeF CBTT · BaoChinhPhu danh sách | không có giờ ở danh sách ⇒ lấy từ trang bài (`meta.cms-date` / — / `div.detail-time`); CBTT không có ⇒ NULL | `feed` / `unknown` |

`canonical_url`: lowercase scheme+host, `http→https`, bỏ query `utm_*`/`gidzl`/`fbclid`/`utm_source`, bỏ fragment, bỏ `/` cuối; giữ mọi query khác nguyên văn. Đây là khoá của `article.canonical_url` và `article_source.url`.

### 5.4 Bóc — bảng luật (chép từ article-structure §2, chủ ở đó)

| Nguồn | Container | Bỏ (tầng 2) | Sapo | Giờ trên trang |
|---|---|---|---|---|
| cafef | `div.detail-content.afcbc-body` | `div.chisochungkhoan, div.tindnd, #listNewsInContent, div.c-banner, div.h-show-pc, div.h-show-mobile, figure, figcaption, #reactRelate, div.VCSortableInPreviewMode` | `p.sapo` (ngoài container) | `span.pdate` `%d-%m-%Y - %I:%M %p` |
| cafef_cbtt | `div#newscontent` | `div.FileWrapper` | — | — |
| vietstock | `div#vst_detail` | `p.pTitle, p.pHead, p.pAuthor, p.pSource, p.pPublishTimeSource, table.img-content, div.article-sharing` | `p.pHead` | `div.meta span.date` `%d/%m/%Y %H:%M` |
| vneconomy | `main#article-editor` | `h4.article-content__lead, figure, figcaption, div.container-adv, section, div.article-tags, table` | `h4.article-content__lead` | `time.article-meta__time` `%H:%M, %d/%m/%Y` |
| vietnambiz | `div.vnbcbc-body` | `div.VnBizPreviewMode, figure, figcaption, table` | `div.vnbcbc-sapo, div.sapo` | `span.vnbcba-time` `%H:%M \| %d/%m/%Y` |
| bnews | `div.lr-ct` | `div.lr-summary-post, div.insertImage, div.editor_inpage, #divAdmicro_inpage, div.lr-author, figure, figcaption, table` | `div.lr-summary-post` (bỏ nhãn `BNEWS`) | không (feed) |
| nguoiquansat | `article.entry` | `div.sc-longform-header, div.sc-hightlight-box, div.c-box, figure, figcaption, div.sc-empty-layer, table` | `p.sc-longform-header-sapo` | `span.sc-longform-header-date` `%d/%m/%Y - %H:%M` hoặc `%d/%m/%Y %H:%M` |
| baochinhphu | `div.detail-content.afcbc-body` | `div.VCSortableInPreviewMode, figure, figcaption, div.detail-relate, div.c-banner, div.admzone, table` | `h2.detail-sapo` (bỏ `(Chinhphu.vn) - `) | `div.detail-time` `%d/%m/%Y %H:%M` |
| tinnhanhck | `div.article__body` | `div.ads_middle, div[id^=adsWeb_], figure.article__avatar, a.cms-relate, div.article__tag, figcaption, table` + text `\.\.>>\s*` | `div.article__sapo` (bỏ `(ĐTCK) `) | `meta.cms-date[itemprop=datePublished]` (ISO) |

Text: xoá `Comment` → decode entity (bs4 làm) → bỏ selector → `get_text(" ")` trên container (duyệt text node) → `\s+` → một dấu cách → strip. Tiêu đề: selector §2; nếu rỗng ⇒ `ExtractError('no_title')`.

### 5.5 `stats` của một lượt

`{"sources_total", "lists_ok", "lists_failed", "lists_stored", "items", "seen", "merged_url", "merged_title", "new", "articles_ok", "articles_failed", "refused", "tickers_url", "tickers_lookup", "stale_feeds": [...], "warnings": [...], "calls", "retries", "run_date", "dry_run"?, "subset"?, "cycle"?}` — `warnings` theo §4.5. Backfill thêm `{"month", "cursor", "urls_in_sitemap", "skipped_seen", "stop_at", "budget_hit", "months_done"}`.

### 5.6 `--loop`

`while True: rc = collect(...); ngủ tới mốc 300 s kể từ lúc bắt đầu vòng (không ngủ nếu vòng > 300 s); cycle += 1; sitemap khi cycle % 3 == 0; dừng khi hết --minutes hoặc Ctrl+C` — mỗi vòng mở/đóng `etl_run` riêng; Ctrl+C giữa vòng ⇒ vòng đó `failed: dừng tay (Ctrl+C)`, exit 130. Log một dòng mỗi vòng: `cycle n · items · new · merged · refused · warnings`.

### 5.7 Backfill sitemap

Tháng đi **lùi** từ `--to` (mặc định tháng hiện tại) về `--from`; mỗi tháng: tải sitemap → bỏ phần tử đầu → `Seen` lọc URL đã có → với từng URL còn lại: fetch bài, extract, `insert_article` (giao dịch riêng; `feed='sitemap'`, `group_from_feed` NULL, `published_at` = `lastmod`, `src='feed'`); hạn giờ theo `--max-minutes` và/hoặc `--stop-before-open` (08:45 ngày giao dịch kế, tái dùng `price_job._next_open`) kiểm sau mỗi bài; `stats.cursor` = tháng đã xong gần nhất; lượt sau đọc cursor từ `etl_run` gần nhất của `news.backfill_sitemap` và bắt đầu từ tháng kế (lùi). Không guard; `refused`/`failed` đếm và lưu bằng chứng từ chối; **10 bài liên tiếp hỏng ⇒ dừng lượt** (khuôn `SourceDown` của backfill giá).

## 6. Seam test *(chốt cùng plan)*

Fixture chụp 2026-09-05 ở `tests/etl/fixtures/news/`: 9 trang bài (8 nguồn + CafeF CBTT) HTML nguyên trang · 8 feed RSS (một mỗi báo, gồm BNews UTF-16LE bytes, VietnamBiz, BaoChinhPhu) · sitemap `news-2026-9.xml` · 3 danh sách HTML (CafeF CBTT, TNCK `chung-khoan`, BCP). Expected là literal đọc tay từ fixture.

| Seam | Ca phải có |
|---|---|
| `news_registry.build` | 53 nguồn; 47 `rss` với `group_from_feed` 14/12/21; tên báo ∈ 8; mọi URL khớp feeds.json; `_meta` số đếm khớp |
| `news_parse.parse_rss` | BNews bytes UTF-16LE ⇒ 20 item tiêu đề đúng literal; VietnamBiz prolog utf-16 ⇒ decode UTF-8 (không có `�`), `pubDate` rỗng ⇒ giờ từ URL literal `2026-09-05 20:15 +07`, `src='url'`; BaoChinhPhu `9/5/2026 1:30:00 PM` ⇒ `2026-09-05 13:30 +07`, `src='feed'`; Vietstock sapo entity `&lt;img` ⇒ sapo_raw giữ nguyên (làm sạch ở extract/store) |
| `news_parse.canonical_url` | `…chn?utm_source=du-lieu` ⇒ bỏ query; `http://vietstock.vn/…` ⇒ `https://`; fragment bỏ; query khác giữ; `/` cuối bỏ |
| `news_parse.norm_title` | `"(Chinhphu.vn) - Cơ chế, chính sách…"` ⇒ `cochechinhsach…`; `"Đầu tư"` ⇒ `dautu`; hai tiêu đề khác dấu/hoa thường ⇒ bằng nhau |
| `news_parse.parse_sitemap` | fixture 243 URL ⇒ **242** item (bỏ phần tử đầu có `lastmod` 20:18); item cuối literal URL + `lastmod 2026-09-05T19:48:38+07:00` |
| `parse_cafef_cbtt` / `parse_tnck_category` / `parse_bcp_list` | số link literal (21 / ≥ 100 / ≥ 90), `ticker_from_url` `SGP`, loại `HNX`/`HOSE`/`UPCOM`; TNCK `group_from_feed=3` |
| `news_extract.extract` × 9 | mỗi nguồn: `len(content)` = literal đếm tay ±0 (fixture cố định), `content[:40]` literal, không chứa chuỗi boilerplate đã biết (`"TIN MỚI"`, `"Tham khảo thêm"`, tên tác giả Vietstock, `"BNEWS"`, `..>>`), tiêu đề literal, giờ trang literal; BNews text node trần ⇒ content > 1.000 ký tự; BaoChinhPhu không chứa `GMT+0700`; container thiếu ⇒ `ExtractError('no_container')`; text 50 ký tự ⇒ `too_short` trừ `cafef_cbtt` |
| `news_tag` | `/du-lieu/SGP-2969587/…` ⇒ `['SGP']`; `HNX-…` ⇒ `[]`; `"HPG tăng trần, USD và GDP…"` với listed `{HPG, SME}` ⇒ `['HPG']`; `"SME công bố…"` ⇒ `['SME']`; chữ thường `hpg` ⇒ `[]` |
| `news_store.decide` | URL đã có ⇒ `seen`; canonical trùng khác URL ⇒ `merge_url`; tiêu đề trùng trong 47 giờ ⇒ `merge_title`, 49 giờ ⇒ `new`; `published_at` NULL dùng `fetched_at` |
| `news_store.insert_article` + `add_revision` (DB) | 1 article + revision v1 + 1 source + n ticker; chạy lại cùng URL ⇒ `seen`, 0 dòng mới; `add_revision` với content khác ⇒ v2, cũ giữ nguyên; content giống ⇒ False; `tsv` có `unaccent` (tìm `chung khoan` ra bài `chứng khoán`) |
| `news_store` bằng chứng (DB) | danh sách hash đổi ⇒ 1 dòng `raw_payload` `content_type='html'`/`'text'`; không đổi ⇒ 0; từ chối ⇒ dòng `meta.refused=true`, `endpoint_key` = URL bài |
| `news_job.collect` (DB, `get` giả từ fixture) | lượt trọn: `lists_ok == 53` (sitemap có khi `cycle % 3 == 0`), `new` = số literal, `articles_ok`, `article` count, `data_domain_state` 8 dòng `('news', báo)`; lượt hai cùng fixture ⇒ `new == 0`, `seen` = tổng; `--dry-run` ⇒ 0 dòng; `--sources cafef` ⇒ không đụng domain state; feed 503 ⇒ `lists_failed`, lượt vẫn `success`, `warnings` khi > 20 %; bài 404 ⇒ `articles_failed`, không `article`; Ctrl+C ⇒ 130 |
| `news_job.backfill_sitemap` (DB) | fixture sitemap 3 URL (2 mới 1 đã có) ⇒ 2 article `feed='sitemap'`, `published_at` = lastmod, `skipped_seen == 1`, `cursor == '2026-09'`; `--max-minutes` hết sau bài 1 ⇒ `budget_hit`, bài 1 vẫn commit; 10 bài liên tiếp 503 ⇒ `failed`, `SourceDown` |
| quyền (DB) | `SET LOCAL ROLE dlck_etl`: insert article/revision/source/ticker + raw_payload + `SELECT market.security` |
| CLI | `etl news --loop --minutes 1` gọi `run(loop=True, minutes=1.0)`; `--backfill-sitemap --from 2026-08` gọi `run_backfill(from_month='2026-08', …)`; `--backfill-sitemap` + `--loop` ⇒ exit 2; `--from` sai định dạng ⇒ exit 2 |

## 7. Tiêu chí nghiệm thu

| | Nội dung | Bằng chứng |
|---|---|---|
| AC1 | Toàn bộ test xanh | trước **729 passed, 2 skipped** / sau |
| AC2 | `etl news --dry-run` trên nguồn sống: `lists_ok` 52–53, `items` ≈ 1.600 (feed) + ~300, `new` > 0, `warnings` chỉ có feed im (Vietstock `niem-yet`) | `stats` |
| AC3 | Lượt đầu `etl news` vào kho production (`ETL_DATABASE_URL`, `dlck_etl`): `article` > 0, `article_revision` = `article`, `article_source` ≥ `article`; **3 bài của 3 báo đối chiếu tay** với trang gốc: tiêu đề khớp, 60 ký tự đầu `content` khớp, không có boilerplate | 3 bảng đối chiếu |
| AC4 | Lượt hai ≤ 5 phút sau: `new` ≤ số bài mới thật trong 5 phút, `seen` ≈ `items`, không `article_revision` v2 | `stats` + đếm |
| AC5 | Gắn mã: mọi `article` từ `cafef_cbtt` có `article_ticker via='url'` (trừ HNX/HOSE/UPCOM); ≥ 1 bài nhóm 3 có `via='lookup'` với mã đúng khi đọc tiêu đề; `ticker_step_ran = true` cho mọi bài nhóm 3, `false` cho nhóm 1–2 | truy vấn |
| AC6 | Dedupe: ≥ 1 `article` có ≥ 2 dòng `article_source` từ 2 báo khác nhau (gộp theo tiêu đề) và ≥ 1 gộp cùng báo khác URL; đọc tay 5 cặp gộp theo tiêu đề: 0 cặp gộp nhầm | truy vấn + đọc tay |
| AC7 | `--loop` chạy thử ≥ 24 giờ có ngày làm việc: tổng `items` / `new` / `merged_url` / `merged_title` / `refused` / `articles_failed`; **tỷ lệ dedupe** = items ÷ article mới; HTTP ≠ 200 theo host; kết luận "nhịp 5 phút × 51 danh sách an toàn" | tổng hợp từ `etl_run` |
| AC8 | `etl news --backfill-sitemap --from 2026-08 --to 2026-08 --max-minutes 60`: bài tháng 8 vào kho `feed='sitemap'`, `published_at` = `lastmod` (đối chiếu 3 bài), URL đã có từ collect bị `skipped_seen`; lượt hai cùng tham số ⇒ `new 0` | `stats` + truy vấn |
| AC9 | Bằng chứng: `raw_payload` chỉ có danh sách (khi hash đổi) và bài từ chối; **0** HTML bài thành công | `SELECT source, count(*) … GROUP BY meta->>'refused'` |
| AC10 | Mọi lượt dưới credential production; không khoá nào (không có) — kiểm log không có URL kèm token | grep |

## 8. Checklist tài liệu sống — cùng lượt

- [ ] [news-pipeline.md](../../../20-design/news-pipeline.md): §12 "Đo tỷ lệ dedupe thật" ✅ số AC7 kèm ngày; §14 "Việc tiếp theo" mục 4 ✅, 6 ✅ (TinnhanhCK; BNews/NguoiQuanSat còn); ghi chú đầu §9.3 "bản ghi thật = migration `0007`; trường AI để NULL tới lát 9".
- [ ] [news/README.md](../../../10-sources/news/README.md) *(đo 2026-09-05)*: §5.2 bẫy phần tử đầu sitemap `lastmod` = giờ sinh file, sitemap lùi tới 2015-06, file lẫn bài đầu tháng kế; §6.3 `utm_source=du-lieu` ở CafeF CBTT; §10 feed im 18 ngày `741/niem-yet`; §13 "đo lại 05/09: 47/47 sống"; "Trạng thái" ⇒ "đã cài đặt lát 8".
- [ ] [article-structure.md](../../../10-sources/news/article-structure.md) *(đo 2026-09-05)*: §2 mỗi nguồn thêm dòng "Kiểm lại 05/09: container + tiêu đề còn đúng, text N ký tự"; §5 giám sát: ngưỡng từ chối 5 % và bằng chứng khi từ chối.
- [ ] [market-data-store.md](../../../20-design/market-data-store.md) hoặc chỗ ghi chú miền: "miền `news` có job từ 2026-09-0x".
- [ ] [backend/README.md](../../../../backend/README.md): mục "Chạy job news" (cờ, `--loop`, backfill, stats, cách đọc `warnings`).
- [ ] [roadmap.md](../../../00-overview/roadmap.md): lát 8 ✅, số test, "Điểm vào cho lát 9" (lưới AI) và lát 8b (sitemap BNews/NguoiQuanSat), việc gấp [5] cập nhật.
- [ ] [database/README.md](../../../../database/README.md): số test. `90-records/README.md`: dòng plan này; `ledger.md`.

## 9. Điểm cần chủ dự án duyệt tường minh

1. Tầng 2 chỉ quét tiêu đề + sapo (§4.6-I).
2. `published_at_src='feed'` dùng chung cho giờ từ sitemap và từ trang bài (§4.6-II) — tránh migration.
3. Bài bóc từ chối **không** tạo `article` (§4.6-VII).
4. Tên báo 8 giá trị và `feed_slug` = phần đường dẫn của URL feed (ví dụ `739/chung-khoan/giao-dich-noi-bo`), `'sitemap'`, `'cbtt'`, `'chi-dao-dieu-hanh'`.
5. Backfill sitemap ước ~200 giờ cho 2015–2026 — lát này chỉ nghiệm thu một tháng; `--from` do chủ dự án chọn khi chạy.
6. Cửa sổ dedupe tiêu đề 48 giờ (câu 3).
7. `--loop` 1–2 ngày rồi merge (câu 2).
