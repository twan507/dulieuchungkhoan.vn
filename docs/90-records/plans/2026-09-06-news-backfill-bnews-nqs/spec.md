# Spec — lát 8b: backfill sitemap BNews + NguoiQuanSat (một job `--backfill-sitemap --source`, con trỏ riêng từng nguồn)

**Ngày:** 2026-09-06 sáng · **Nhánh:** `feat/news-backfill-sitemaps` · **Trạng thái:** chủ dự án duyệt thiết kế 10 điểm rồi duyệt spec 2026-09-06 sáng ("độ sâu chốt luôn lấy tạm 1 tháng… còn lại ok")
**Tiền đề:** [roadmap — Điểm vào cho lát 8b](../../../00-overview/roadmap.md) · [spec lát 8](../2026-09-05-news-collect/spec.md) (§4.6-VIII, IX: khuôn backfill; §5.7) · [news-pipeline §9.6](../../../20-design/news-pipeline.md) · [news/README §5.2](../../../10-sources/news/README.md) · [article-structure §2.6, §2.7](../../../10-sources/news/article-structure.md)
**Số đo trước spec:** [`measure-sitemap-bnews-nqs-2026-09-06.md`](measure-sitemap-bnews-nqs-2026-09-06.md) (≈50 lời gọi, hai host).

Tiêu chí xuyên suốt: **cùng đường ghi của lát 8, không thiết kế lại** — lát này chỉ tham số hoá bộ đọc sitemap theo nguồn và vá luật bóc cho template cũ; **mọi thứ nguồn tự khai về chính nó đều đã kiểm bằng dữ liệu** (§2.1).

---

## 1. Vì sao lát này, và lát này là gì

news-pipeline §9.6: backfill lịch sử làm sớm, dữ liệu chỉ còn chừng nào họ còn giữ sitemap. Lát 8 chỉ làm TinnhanhCK; `backfill_sitemap` hiện **cứng** `tinnhanhck` ở 6 chỗ (registry tạo tay, `PARSERS["tnck_sitemap"]`, regex `-post\d+\.html$`, nhãn fetch, `store_refused`, một job/con trỏ `news.backfill_sitemap`).

| Thành phần | Nội dung |
|---|---|
| `etl news --backfill-sitemap --source {tinnhanhck\|bnews\|nguoiquansat} --from YYYY-MM [--to] [--max-minutes] [--stop-before-open]` | một job cho ba nguồn; `--source` mặc định `tinnhanhck` để lệnh và tài liệu lát 8 vẫn đúng |
| Registry | chủ mẫu URL sitemap + **đơn vị kỳ** (tháng / ngày) + regex URL bài theo nguồn |
| Con trỏ | riêng từng nguồn: job `news.backfill_sitemap:<source>`; TinnhanhCK đọc thêm tên cũ để không mất con trỏ |
| Luật bóc NguoiQuanSat | nhận cả template cũ (trước ~2025): `h1.c-detail-head__title`, `span.c-detail-head__time` |

Không migration. Không AI. Không đăng ký task.

## 2. Dữ kiện đã đo vs giả định *(§4.8 bước 0)*

### 2.1 Đã đo — 2026-09-06 07:00–08:00 VN, ≈50 lời gọi (chi tiết: file đo)

| Dữ kiện | Bằng chứng |
|---|---|
| **BNews:** index `sitemap.xml` → `sitemap/news-{Y}-{M}.xml` (M không đệm 0), 141 tháng 2015-1 → 2026-9; tháng đầu có bài **2015-08** (644 bài); 2015-1/6/7 chỉ có 3 phần tử đầu | file đo §BNews |
| BNews mỗi file: **3 phần tử đầu** (`https://bnews.vn`, `/photo/trang-1.html`, `/video/trang-1.html`, `lastmod` = giờ sinh file, UTC `Z`); bài `/<slug>/<id>.html`; **giảm dần** theo `lastmod` ở mọi file kể cả tháng hiện tại (0 cặp lệch); file tháng không lẫn tháng kế | 5 file: 2015-8, 2015-12, 2020-9, 2026-8, 2026-9 |
| **BNews `lastmod` = giờ đăng**: khớp `pubDate` feed 20/20 (đến giây); khớp ld+json `datePublished` 3/3 trang (2015, 2020, 2026-08), `dateModified` = `datePublished` | so feed `kinh-te-viet-nam-1.rss` với sitemap 2026-9 |
| BNews khối lượng: 2026-08 **4.085** bài · 2020-09 3.036 · 2015-12 1.784 · 2015-08 644 ⇒ lùi hết ≈ 480k URL | đếm `<loc>` |
| BNews trang bài cũ `200` với UA ETL; rule `bnews` hiện tại bóc được 3/3 (2015: 1.195 · 2020: 1.844 · 2026-08: 6.603 ký tự); 0 lỗi 403 trong 13 lời gọi | `news_extract.extract` trên trang tải về |
| **NguoiQuanSat:** index `sitemap.xml` (200 với UA ETL) → `sitemap-article-{YYYY-MM-DD}.xml` theo **ngày**, 1.879 file 2021-07-16 → 2026-09-06, không thiếu ngày; `sitemap-news.xml`, `sitemap-category.xml` 403 mọi UA (không cần) | file đo §NQS |
| NQS file ngày: urlset có `image:image`; bài `/<slug>-<id>.html`; `lastmod +07:00` **giảm dần**, đúng một ngày/file, **không có phần tử trang chủ**; `lastmod` = giờ đăng (giây `:01`; khớp giờ trang `13:12:00` vs `13:12:01`; khớp ld+json 3/3) | 5 file: 2021-07-17, 2022-01-10, 2024-01-15, 2026-09-04, 2026-09-05 |
| NQS khối lượng: 25 bài/ngày (2021-07) → 96 (2022-01) → 180 (2024-01) → 206 (2026-09-04, thứ 6), 120 (thứ 7) ⇒ lùi hết ≈ 250k URL | đếm `<loc>` |
| 🔴 **NQS WAF chặn chập chờn, KHÔNG theo UA:** 12 file ngày chưa cache, UA ETL, giãn 3–5 s → 7 đạt / 5 bị 403 (`Access Denied.. blocked by our security system`); thử lại sau 15 s → 4/5 đạt. Giả thuyết chặn theo UA bị bác (UA ETL có lúc 200 MISS, UA Chrome+định danh có lúc 403). Trang bài: UA ETL 5/6 lần `200`, lần 403 thử lại `200` | file đo §Bổ sung |
| 🔴 **NQS template cũ** (bài 2021, 2022, 2024): không có `sc-longform-header`; tiêu đề `h1.c-detail-head__title`, giờ `span.c-detail-head__time` dạng `15-01-2024 13:04`; container `article.entry` và rác `div.c-box` vẫn đúng; không có sapo trong head (`c-detail-head__cat/row/time/title`); credit `div.c-author-page` ngoài container. Rule hiện tại **fail `no_title`** 3/3; bài 2026-09-04 (template mới) OK 2.941 ký tự | `news_extract.extract` |
| Fetcher hiện có: `news_fetch.classify` trả `retry` cho mọi HTTP ≠ 200/404; `http_fetch.Fetcher` retry 3 lần, backoff 2/4/8 s, giãn ngẫu nhiên 1–5 s | code |

### 2.2 Giả định — CHƯA kiểm

| # | Giả định | Kiểm ở đâu | Nếu sai |
|---|---|---|---|
| A1 | Retry 3 lần của Fetcher đủ hấp thụ 403 chập chờn của NQS ở tải thật (1 lời gọi / 1–5 s liên tục hàng giờ) | AC3: tỷ lệ `articles_failed` + `periods_failed` của lượt NQS 30 phút | nâng backoff riêng cho NQS (ví dụ 5/15/45 s) — đổi một hằng, không đổi kiến trúc; tệ nhất: giảm nhịp |
| A2 | NQS chỉ có hai template (mới `sc-longform-*`, cũ `c-detail-head__*`) trong 2021–2026 | AC4 lượt 2024-01 + đếm `refused` theo `reason` ở AC3 | thêm selector vào danh sách, không đổi kiến trúc |
| A3 | BNews template B (text node trần, article-structure §2.6) không đổi ở bài cũ | AC3: đối chiếu 3 bài BNews 2026-08 + 1 bài 2020 đã đo | luật bóc từng nguồn |
| A4 | Tải thêm ≈ 1 lời gọi / 3 s lên mỗi host khi chạy song song với `--loop` không bị chặn thêm (đo A2 lát 8 chưa gồm backfill) | AC3 chạy khi `--loop` đang bật | chạy backfill ngoài giờ loop |

## 3. Phạm vi

### 3.1 Trong phạm vi

- **`news_registry.py`:** bảng `SITEMAPS = {name: SitemapSpec(period, url_tmpl, article_url)}`: `tinnhanhck` (`month`, `…/sitemaps/news-{y}-{m}.xml`, `-post\d+\.html$`) · `bnews` (`month`, `https://bnews.vn/sitemap/news-{y}-{m}.xml`, `/\d+\.html$`) · `nguoiquansat` (`day`, `https://nguoiquansat.vn/sitemap-article-{y:04d}-{m:02d}-{d:02d}.xml`, `-\d+\.html$`). `Source` thêm `backfill_only: bool = False`. Kind `tnck_sitemap` **đổi tên** thành `sitemap` (một kind cho ba nguồn — §4.2). `build()` đọc hai dòng `crawl_html` mới của feeds.json (cờ `chi_backfill: true`) ⇒ `Source(kind="sitemap", backfill_only=True)`; sitemap TinnhanhCK giữ `backfill_only=False` (vẫn vá lỗ mỗi 3 vòng). Kiểm `_meta.crawl_html` = 8. `sitemap_url(source, period_key)` thay `sitemap_url(now_vn)`.
- **`news_parse.py`:** `parse_sitemap(text, src)` lọc `<loc>` bằng `SITEMAPS[src.name].article_url`; `Item(source=src.name, …, rule=src.name)`; `POST_URL` giữ cho `parse_tnck_category`. Loại trang chủ/photo/video của BNews và mọi entry không phải bài đều rơi vào cùng bộ lọc regex — không cần luật "bỏ phần tử đầu".
- **`news_job.py`:** `periods_desc(source, from_month, to_month) -> list[str]` — nguồn tháng: `["2026-08", …]`; nguồn ngày: mọi ngày của các tháng đó, lùi từ ngày cuối `to_month` (không vượt quá hôm nay VN) về ngày 1 của `from_month`, khoá `"2026-08-31"`. `backfill_sitemap(engine, source, from_month, to_month, …)`: mỗi kỳ tải sitemap theo `sitemap_url(source, key)`, parse, lọc `Seen`, tải bài với `f.fetch_one(url, source)`, `extract(html, source)`, `store_refused(c, source, …)`; `stats` đổi `month/months_done/months_failed` → `period/periods_done/periods_failed` (kèm `source`, `period_unit`); `cursor` = kỳ đã xong gần nhất. `JOB_BACKFILL` → `job_name(source) = f"news.backfill_sitemap:{source}"`; `load_cursor(engine, source)` đọc `job IN (job_name(source), 'news.backfill_sitemap')` khi `source == 'tinnhanhck'` (fallback tên cũ), lấy `run_id` lớn nhất. `run_backfill(source=…, …)`; luật nối con trỏ giữ nguyên (`cursor < to`): với nguồn ngày, `to` = ngày trước con trỏ.
- **`news_extract.py`:** `Rule.title`/`Rule.time` nhận **danh sách selector CSS** (chuỗi `a, b` — `select_one` chọn phần tử đầu khớp trong thứ tự tài liệu; hai template không đồng thời có cả hai selector nên không nhập nhằng). `nguoiquansat`: title `"h1.sc-longform-header-title, h1.c-detail-head__title"`, time `"span.sc-longform-header-date, span.c-detail-head__time"`, `time_fmt` thêm `"%d-%m-%Y %H:%M"`. `bnews` không đổi.
- **`__main__.py`:** `--source` (choices ba tên, mặc định `tinnhanhck`), chỉ hợp lệ cùng `--backfill-sitemap` (khác ⇒ exit 2, khuôn "loại trừ chéo" M4 lát 8).
- **`feeds.json`:** hai dòng `crawl_html` (`nguon` `bnews` / `nguoiquansat`, `url` mẫu, `nhom_mac_dinh` null, `chi_backfill: true`, `ghi_chu` số đo); `_meta.crawl_html` 6 → 8, `cap_nhat` 2026-09-06.
- Fixture chụp 2026-09-06 vào `tests/etl/fixtures/news/`: `bnews-sitemap-2026-9.xml` (cắt còn 3 phần tử đầu + 5 bài), `nqs-sitemap-2026-09-05.xml` (cắt còn 5 bài, giữ `image:image`), `nqs-article-2024-01-15.html` (template cũ, bài 110172), `bnews-article-2020-09-15.html` (bài 169672).
- Nghiệm thu thật §7; tài liệu §8; ledger.

### 3.2 Ngoài phạm vi — ba loại *(§1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| Lọc BNews theo chuyên mục (`article:section`) | **Loại có chủ đích** | chủ dự án chốt "lấy hết, độ sâu chọn lúc chạy" (§4.1); lát 9 phân loại bằng AI |
| Đổi UA / giả UA trình duyệt cho NQS | **Loại có chủ đích** | đo cho thấy 403 không theo UA (§2.1); giữ UA tự định danh |
| `sitemap-news.xml`, `sitemap-category.xml` của NQS | **Đã kiểm — không có** | 403 mọi UA; không cần: file ngày đủ |
| Giờ trang cho BNews (ld+json `datePublished`) | **Đã có đường khác** | `lastmod` = giờ đăng đã đo 23/23; thêm luật là thừa (§4.4.2) |
| Giá trị `published_at_src` mới (`'sitemap'`) | **Đã có đường khác** | spec lát 8 §4.6-II: `'feed'`; migration để lát 12 |
| Chạy backfill tự động / task | **Đã có đường khác** | lát 13; chạy tay tách tiến trình (memory: lượt > 10 phút mở bằng `Start-Process`) |
| `Seen.load` tối ưu khi ~100k dòng (M1 lát 8) | **Đã có đường khác** | nợ lát 8; backfill ~2k bài/lượt 30 phút chưa chạm ngưỡng; theo dõi ở ledger |

## 4. Quyết định *(§4.8 — chủ dự án chốt trong chat 2026-09-06 sáng)*

### 4.1 Phạm vi BNews: lấy hết, không lọc chuyên mục; **độ sâu tạm 1 tháng (2026-08) cho cả hai nguồn** *(câu 1 → (a); chủ dự án chốt thêm độ sâu khi duyệt spec 2026-09-06 sáng: "lấy tạm 1 tháng thôi, không lấy quá nhiều")*
Loại (b) lọc theo `article:section` sau tải: vẫn tốn lời gọi, chỉ tiết kiệm dung lượng, phải chốt danh sách chuyên mục. Loại (c) mốc cứng trong code: quyết định vận hành không nên nằm trong code — độ sâu là tham số `--from` lúc chạy; lát này chạy đúng **một tháng 2026-08** mỗi nguồn (không lùi thêm) và không đăng ký lượt nào tự lùi tiếp. **Đảo ngược:** chủ dự án muốn lùi sâu hơn ⇒ chạy lại với `--from` xa hơn, con trỏ nối tiếp; kho `news.*` vượt dung lượng VPS ⇒ lọc ở lát 9 bằng nhóm đã gán.

### 4.2 Điểm trợ lý tự chốt khi viết spec (ghi §9 để rà)

| # | Chốt | Vì sao | Đảo ngược khi |
|---|---|---|---|
| I | Một job, `--source`, job name `news.backfill_sitemap:<source>` cho cả ba; TinnhanhCK đọc thêm tên cũ | con trỏ không giẫm nhau; lát 12 đọc theo job; tên nhất quán hơn "TNCK giữ tên cũ, hai nguồn kia có hậu tố" | — |
| II | Kind `tnck_sitemap` → `sitemap` + cờ `backfill_only` | một parser cho ba nguồn; hai kind cho cùng parser là hai nguồn sự thật; `collect` bỏ qua `backfill_only` nên lượt thường vẫn 53 danh sách | — |
| III | Đơn vị kỳ nằm ở registry; CLI vẫn `--from/--to YYYY-MM` cho cả ba; con trỏ nguồn ngày ghi tới ngày | người chạy không phải nhớ nguồn nào theo ngày; nguồn ngày có ~30 kỳ/tháng, mỗi kỳ 25–250 bài nên con trỏ theo ngày mất ít khi ngắt | — |
| IV | `published_at` bài backfill BNews/NQS = `lastmod`, `src='feed'`; `published_for` không đổi | đo `lastmod` = giờ đăng ở cả hai (23/23 BNews, 3/3 NQS); NQS có giờ trang nhưng bằng nhau | phát hiện `lastmod` bị cập nhật khi sửa bài ⇒ đưa NQS vào nhánh "giờ trang trước" như TinnhanhCK |
| V | 403 NQS: không đổi UA, dùng retry sẵn có; kỳ hỏng sau retry → `periods_failed`, không đẩy con trỏ qua kỳ đó, chạy lại lượt sau tự vá | đo §2.1; kỳ hỏng không đếm vào cầu chì (I2 lát 8) | A1 sai ⇒ backoff riêng cho NQS |
| VI | Lọc entry bằng regex URL bài theo nguồn thay luật "bỏ phần tử đầu" | BNews có 3 phần tử đầu, NQS có 0, TNCK có 1 — regex phủ cả ba mà không đếm vị trí | — |
| VII | Ước tải: BNews ~4.000 URL/tháng × ~3,2 s ≈ **3,5 giờ/tháng**, 2015-08 → 2026-08 ≈ 480 giờ; NQS ~5.000 URL/tháng ≈ **4,5 giờ/tháng**, 2021-07 → 2026-08 ≈ 250 giờ. Lát này chạy **trọn tháng 2026-08 mỗi nguồn** (BNews ≈ 4.085 URL ≈ 3,5 giờ; NQS ≈ 5.000 URL ≈ 4,5 giờ, chia nhiều lượt `--max-minutes`, con trỏ nối) + 10 phút NQS 2024-01 để chứng template cũ; **không lùi quá 2026-08** (§4.1) | §4.3 CLAUDE.md; chủ dự án chốt độ sâu | — |
| VIII | Chạy song song với `--loop`: được; mỗi nguồn tối đa một tiến trình backfill (không có khoá trong code — `ON CONFLICT` lát 8 C2 đã bảo vệ dữ liệu, chỉ là quy ước vận hành) | tải thêm ≈ 1 lời gọi/3 s mỗi host | A4 sai |

## 5. Thiết kế

### 5.1 File và thay đổi

| File | Thay đổi |
|---|---|
| `backend/etl/news_registry.py` | `SitemapSpec(period: 'month'\|'day', url: str, article_url: re.Pattern)`; `SITEMAPS`; `Source.backfill_only`; `KINDS` đổi `tnck_sitemap` → `sitemap`; `_crawl_kind` nhận `chi_backfill`/`/sitemap` của ba host; `sitemap_url(source, key)`; xếp `sitemap` xuống cuối như C1 lát 8 |
| `backend/etl/news_parse.py` | `parse_sitemap(text, src)` dùng `SITEMAPS[src.name]`; `PARSERS["sitemap"]` |
| `backend/etl/news_job.py` | `periods_desc`, `job_name`, `load_cursor(engine, source)`, `backfill_sitemap(engine, source, …)`, `run_backfill(source, …)`; `collect` bỏ qua `backfill_only`, dùng `sitemap_url("tinnhanhck", key)` cho vá lỗ |
| `backend/etl/news_extract.py` | rule `nguoiquansat` hai selector tiêu đề/giờ + định dạng mới; docstring `Rule.title/time` ghi "danh sách CSS" |
| `backend/etl/news_store.py` | `store_list_if_changed(... "text" if kind in ("rss","sitemap"))` — chỉ đổi tên kind |
| `backend/etl/__main__.py` | `--source` |
| `docs/10-sources/news/feeds.json` | +2 `crawl_html`, `_meta` |
| `backend/tests/etl/test_e52_news_parse.py` · `e53_news_extract.py` · `e56_news_job.py` · `e57_news_backfill.py` · `e58_news_cli.py` | sửa assert kind; thêm ca §6 |

### 5.2 Một lượt backfill

```
run_backfill(source, from, to)
 ├─ periods_desc(source, from, to) ; cursor = load_cursor(source) ⇒ cắt `to` về kỳ trước cursor
 ├─ open_run(job_name(source))
 └─ với mỗi kỳ (lùi):
      tải sitemap_url(source, kỳ) ── hỏng sau retry ⇒ periods_failed, kỳ kế
      parse_sitemap ⇒ lọc regex bài ⇒ Seen (url/canonical/refused)
      với mỗi URL còn lại: fetch(url, source) ⇒ extract(html, source) ⇒ insert_article (giao dịch riêng, feed='sitemap', group NULL, published_at = lastmod)
         hỏng ⇒ articles_failed + streak (10 ⇒ SourceDown) · từ chối ⇒ refused + bằng chứng
         kiểm hạn giờ sau MỖI URL ⇒ budget_hit
      kỳ trọn ⇒ periods_done, cursor = kỳ
 └─ close_run(stats)
```

`stats`: `{"source", "period_unit", "cursor", "periods_done": [...], "periods_failed": [...], "period", "urls_in_sitemap", "skipped_seen", "skipped_refused", "articles_ok", "articles_failed", "refused", "budget_hit", "calls", "retries", "stop_at"}`.

### 5.3 Xử lý lỗi
Giữ nguyên lát 8 (I2, §4.6-VII, cầu chì 10 bài, Ctrl+C ⇒ 130, exception mang `stats`). Thêm: `--source` lạ ⇒ argparse exit 2; `periods_desc` với nguồn ngày và `to_month` là tháng hiện tại không sinh ngày tương lai.

## 6. Seam test *(chốt cùng plan; expected là literal đọc tay từ fixture)*

| Seam | Ca phải có |
|---|---|
| `news_registry.build` | 55 nguồn: 47 `rss` + 8 crawl; kinds có đúng 3 `sitemap`; `bnews`/`nguoiquansat` sitemap `backfill_only=True`, `tinnhanhck` `False`; `_meta.crawl_html=8` (lệch ⇒ `RegistryError`); `SITEMAPS["nguoiquansat"].period == "day"` |
| `news_registry.sitemap_url` | `("bnews","2026-08")` ⇒ `https://bnews.vn/sitemap/news-2026-8.xml` (không đệm 0); `("nguoiquansat","2026-08-05")` ⇒ `…/sitemap-article-2026-08-05.xml`; `("tinnhanhck","2026-08")` ⇒ giá trị hiện tại |
| `news_parse.parse_sitemap` | fixture BNews 8 entry ⇒ **5** item (bỏ trang chủ/photo/video), item đầu literal URL + `lastmod`, `source == rule == "bnews"`, `feed_slug == "sitemap"`; fixture NQS 5 entry ⇒ 5 item, `image:image` không làm hỏng, `published_at` literal `2026-09-05 23:48:01+07:00`; fixture TNCK cũ ⇒ 242 như trước |
| `news_job.periods_desc` | `("bnews","2026-07","2026-09")` ⇒ `["2026-09","2026-08","2026-07"]`; `("nguoiquansat","2026-08","2026-08")` ⇒ 31 khoá từ `"2026-08-31"` xuống `"2026-08-01"`; `("nguoiquansat","2026-02","2026-03")` ⇒ 59 khoá (2026 không nhuận); tháng hiện tại không vượt hôm nay (bơm `today`) |
| `news_extract.extract("nguoiquansat")` | fixture 2024 ⇒ tiêu đề literal `Đây là những tấm hộ chiếu quyền lực nhất thế giới năm 2024`, `published_at == 2024-01-15 13:04 +07`, `len(content)` literal đếm tay, không chứa `Theo Kiến thức Đầu tư`; fixture 2026 (đã có) không đổi kết quả |
| `news_job.backfill_sitemap` (DB) | `source="bnews"`, fixture 5 URL (4 mới, 1 đã có) ⇒ 4 article `feed='sitemap'`, `primary_source='bnews'`, `published_at` = lastmod, `skipped_seen == 1`, `cursor == "2026-09"`, job `news.backfill_sitemap:bnews`; `source="nguoiquansat"` một ngày ⇒ `cursor == "2026-09-05"`, `period_unit == "day"`; hai nguồn chạy nối nhau không đọc nhầm con trỏ của nhau |
| `news_job.load_cursor` (DB) | dòng `news.backfill_sitemap` cũ `cursor 2026-08` + không có dòng `:tinnhanhck` ⇒ `"2026-08"`; có cả hai ⇒ dòng `run_id` lớn hơn; `bnews` không thấy dòng của tinnhanhck |
| `news_job.collect` (DB) | registry 55 ⇒ `lists_ok == 53` (hai `backfill_only` bị bỏ, sitemap TNCK có khi `cycle % 3 == 0`); `sources_total == 55` |
| CLI | `--backfill-sitemap --source bnews --from 2026-08` gọi `run_backfill(source="bnews", …)`; thiếu `--source` ⇒ `"tinnhanhck"`; `--source xyz` ⇒ exit 2; `--source bnews` không có `--backfill-sitemap` ⇒ exit 2 |
| quyền (DB) | ca hiện có của lát 8 phủ đường ghi; không có đường mới |

## 7. Tiêu chí nghiệm thu

| | Nội dung | Bằng chứng |
|---|---|---|
| AC1 | Toàn bộ test xanh | trước **791 passed, 2 skipped** / sau |
| AC2 | `etl news --dry-run` sau đổi registry: `lists_ok` 52–53, không có nguồn `backfill_only` trong lượt | `stats` |
| AC3 | `etl news --backfill-sitemap --source bnews --from 2026-08 --to 2026-08 --max-minutes N` và `--source nguoiquansat …` chạy nhiều lượt tới khi `cursor == "2026-08"` / `"2026-08-01"` (tách tiến trình, `--loop` đang chạy): bài vào kho `feed='sitemap'`, `primary_source` đúng; **3 bài mỗi nguồn đối chiếu tay** (tiêu đề, 60 ký tự đầu, `published_at` = `lastmod` = giờ trên trang/ld+json); `stats.source`, `period_unit`, `periods_failed`, `articles_failed` ghi; NQS: tỷ lệ HTTP ≠ 200 sau retry ≤ 5 % (A1) | `stats` + truy vấn + bảng đối chiếu |
| AC4 | `--source nguoiquansat --from 2024-01 --to 2024-01 --max-minutes 10`: bài template cũ vào kho, `refused` theo `reason` ≈ 0, `published_at` khớp `span.c-detail-head__time` 3 bài | `stats` + truy vấn |
| AC5 | Lượt hai cùng tham số mỗi nguồn ⇒ `articles_ok 0`, `skipped_seen` = số đã có; con trỏ nguồn này không đổi con trỏ nguồn kia; `--source tinnhanhck` đọc được con trỏ cũ `2026-08`… của lát 8 (`load_cursor` fallback) | `ops.etl_run` |
| AC6 | Kho: `article_source` mỗi bài backfill một dòng đúng `source_name`; 0 bài `primary_source` sai nguồn | truy vấn |
| AC7 | Tài liệu §8 xong cùng nhánh; `git grep tnck_sitemap` chỉ còn trong vùng lịch sử (`90-records`) | grep |

## 8. Checklist tài liệu sống — cùng lượt

- [ ] [news/README.md](../../../10-sources/news/README.md) *(đo 2026-09-06)*: §5 "Sáu nguồn crawl" → tám; **§5.4 BNews — sitemap tháng** (mẫu URL, 3 phần tử đầu, giảm dần, `lastmod` = giờ đăng, lùi tới 2015-08, ~4.000 bài/tháng); **§5.5 NguoiQuanSat — sitemap ngày** (mẫu URL, không phần tử trang chủ, giảm dần, `lastmod` = giờ đăng, lùi tới 2021-07-16, 25 → 200 bài/ngày, 🔴 403 chập chờn không theo UA, `sitemap-news/category` 403); "Trạng thái" ⇒ "lát 8b".
- [ ] [article-structure.md](../../../10-sources/news/article-structure.md) *(đo 2026-09-06)*: §2.7 NguoiQuanSat thêm **template cũ** (bài ≤ 2024: `h1.c-detail-head__title`, `span.c-detail-head__time` `%d-%m-%Y %H:%M`, không sapo trong head); §2.6 BNews thêm "Kiểm lại 06/09 trên bài 2015/2020: rule còn đúng; trang có ld+json `datePublished`".
- [ ] [news-pipeline.md](../../../20-design/news-pipeline.md) §9.6: dòng BNews/NguoiQuanSat *(đo 2026-09-06)*: dạng sitemap, `lastmod` = giờ đăng, độ sâu; §14 mục 6 ✅ cả ba.
- [ ] [feeds.json](../../../../backend/etl/data/feeds.json): hai dòng + `_meta`.
- [ ] [backend/README.md](../../../../backend/README.md): mục job news — `--source`, job name theo nguồn, ước tải, quy ước một tiến trình/nguồn.
- [ ] [roadmap.md](../../../00-overview/roadmap.md): lát 8b ✅ trong bảng lát, gạch "Điểm vào cho lát 8b", việc gấp [5] cập nhật, số test.
- [ ] `90-records/README.md`: dòng plan này; `ledger.md`.

## 9. Điểm cần chủ dự án duyệt tường minh

1. Job name `news.backfill_sitemap:<source>` cho cả ba, TinnhanhCK đọc thêm tên cũ (§4.2-I).
2. Đổi tên kind `tnck_sitemap` → `sitemap` + cờ `backfill_only` (§4.2-II) — chạm test e52/e56 của lát 8.
3. `--from/--to` vẫn `YYYY-MM` cho nguồn ngày; con trỏ ghi tới ngày (§4.2-III).
4. `published_at` = `lastmod`, `src='feed'` cho BNews/NQS (§4.2-IV).
5. Không đổi UA cho NQS; chấp nhận kỳ hỏng chạy lại lượt sau (§4.2-V).
6. Độ sâu tạm **1 tháng (2026-08)** mỗi nguồn, không lùi thêm; 10 phút NQS 2024-01 chỉ để chứng template cũ (§4.1, §4.2-VII). ✅ chủ dự án chốt 2026-09-06 sáng.
