# Đo sitemap BNews + NguoiQuanSat — 2026-09-06 ~07:00–07:40 VN (≈35 lời gọi, curl --compressed)

## BNews (bnews.vn)
- robots.txt → Sitemap: https://bnews.vn/sitemap.xml (index). gzip, text/xml; charset=utf-8.
- Index liệt kê /sitemap/categories.xml + /sitemap/news-{YYYY}-{M}.xml (M KHÔNG đệm 0), 141 tháng 2015-1 → 2026-9.
- Tháng 2015-1/6/7: chỉ 3 phần tử đầu (rỗng). Tháng đầu có bài: 2015-8 (644 bài). 2015-12: 1.784 · 2020-9: 3.036 · 2026-8: 4.085 · 2026-9 (tới 05/09 23h): 602.
- 3 phần tử đầu mỗi file: https://bnews.vn · /photo/trang-1.html · /video/trang-1.html, lastmod = giờ sinh file (UTC, hậu tố Z). Bài: <loc>https://bnews.vn/<slug>/<id>.html</loc> + lastmod ISO +07:00 + changefreq daily + priority 0.7.
- Thứ tự: GIẢM DẦN theo lastmod ở mọi file đo (2026-9 hiện tại, 2026-8, 2020-9, 2015-12), 0 cặp lệch; file tháng chỉ chứa bài đúng tháng (không lẫn tháng kế).
- lastmod = giờ đăng: khớp pubDate feed RSS 20/20 bài (kinh-te-viet-nam-1.rss, cùng giây); khớp ld+json datePublished 3/3 trang (2015-8, 2020-9, 2026-8), dateModified == datePublished.
- Trang bài cũ: 200 với UA ETL; rule "bnews" hiện tại bóc được 3/3 (2015: 1.195 ký tự · 2020: 1.844 · 2026-8: 6.603). Trang có ld+json datePublished (chưa dùng trong rule).
- Không có 403 nào trong 13 lời gọi với UA ETL.

## NguoiQuanSat (nguoiquansat.vn)
- robots.txt → sitemap.xml (index) + sitemap-news.xml (403 mọi UA thử).
- Index (200 với UA ETL, 278 KB): sitemap-article-daily.xml · sitemap-news.xml · sitemap-category.xml · sitemap-event.xml · sitemap-article-{YYYY-MM-DD}.xml theo NGÀY, 1.879 file 2021-07-16 → 2026-09-06, không thiếu ngày. lastmod trong index = giờ sinh (vô nghĩa).
- 🔴 File ngày trả 403 "Access Denied.. blocked by our security system" với UA ETL (4/4), UA "dulieuchungkhoan.vn-bot", dạng "(compatible; …)" và "curl/8.4.0"; trả 200 với UA Chrome (5/5: 2026-09-05, 09-04, 2024-01-15, 2022-01-10, 2021-07-17). sitemap-category.xml 403 cả với UA Chrome. 2021-07-16 (ngày đầu) 403 với UA Chrome.
- File ngày: urlset có image:image; <loc>https://nguoiquansat.vn/<slug>-<id>.html</loc>, lastmod +07:00, giảm dần, đúng một ngày/file, không có phần tử trang chủ. Giây của lastmod luôn :01 (2022+) — lastmod = published rounded + 1 s.
- Số bài/ngày: 2021-07-17: 25 · 2022-01-10: 96 · 2024-01-15: 180 · 2026-09-04: 206 · 2026-09-05 (T7): 120.
- lastmod vs giờ trang: 2026-09-04 bài 314192: trang 13:12:00, lastmod 13:12:01; ld+json datePublished == lastmod ở 3/3 trang.
- Trang bài: 200 với UA ETL 3/4 lần đầu; bài 2021 (41160) 403 lần đầu với UA ETL, lần sau 200 (chập chờn). 
- 🔴 Template cũ (2021, 2022, 2024): KHÔNG có sc-longform-header. Tiêu đề h1.c-detail-head__title, giờ span.c-detail-head__time "15-01-2024 13:04" (%d-%m-%Y %H:%M), container article.entry vẫn đúng, rác div.c-box (ads_after_sapo_*), credit div.c-author-page ngoài container. Rule "nguoiquansat" hiện tại FAIL no_title trên cả 3 bài cũ; bài 2026-09-04 OK (2.941 ký tự).

## File thô đã giữ trong scratchpad
bnews.vn_sitemap*.xml, bnews_2015-*.xml, nqs_*.xml, nqs_art*.html, bnews_2015art.html, bnews.vn_*html

## Bổ sung 07:40–08:00 — bản chất 403 của NguoiQuanSat
- Giả thuyết "chặn theo UA" BỊ BÁC: ngày chưa cache 2022-08-23 với UA ETL → 200 (MISS), UA Chrome → 200, UA ETL lần 3 → 403. UA Chrome+định danh: 403 rồi 200.
- Cùng URL 2026-09-02 với UA ETL 3 lần cách 5 s (cookie jar): 200/200/200 (X-Cached HIT).
- Đo đúng tải kế hoạch: 12 file ngày chưa cache, UA ETL, giãn 3–5 s → 7/12 = 200, 5/12 = 403. Thử lại 5 file lỗi sau 15 s → 4/5 = 200. ⇒ WAF chặn CHẬP CHỜN, không theo UA; Fetcher hiện có (classify 403 → retry, 3 lần, backoff 2/4/8 s) hấp thụ được phần lớn; phần còn lại đếm vào periods_failed và chạy lại lượt sau.
- Kết luận: giữ UA tự định danh của ETL, không đổi.
