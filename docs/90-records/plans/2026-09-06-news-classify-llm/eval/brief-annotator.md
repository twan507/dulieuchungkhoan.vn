# Brief gán nhãn bộ gold — taxonomy bản 2026-09-06 (đã mở rộng)

Bạn là biên tập viên tài chính giàu kinh nghiệm. Nhãn của bạn là ĐÁP ÁN NHÁP để chấm một model khác (MiniMax M3): gán theo phán đoán của chính bạn khi đọc bài; KHÔNG để "nhóm gợi ý" (hint = nhóm mặc định của feed, sai thường xuyên) chi phối; không đoán model sẽ trả gì. Đọc kỹ toàn bộ đoạn trích (2.500 ký tự) trước khi gán; bài mơ hồ thì đọc lại lần hai.

## Tài liệu chuẩn (đọc trước)
- Taxonomy + luật chung: D:\twan_projects\dulieuchungkhoan.vn\docs\20-design\news-pipeline.md — §3 (20 sub nhóm 1/2/3 + `2f` mới + `x`) và mục "Luật chung khi phân nhóm" ngay dưới §3.
- 24 mã ngành: C:/Users/tuanb/AppData/Local/Temp/claude/D--twan-projects-dulieuchungkhoan-vn/8822569d-752d-4211-8356-f10bb9cedcae/scratchpad/gold/industries.json (cây ngành: D:\twan_projects\dulieuchungkhoan.vn\docs\20-design\industry-tree.md)
- Mã niêm yết hợp lệ: C:/Users/tuanb/AppData/Local/Temp/claude/D--twan-projects-dulieuchungkhoan-vn/8822569d-752d-4211-8356-f10bb9cedcae/scratchpad/gold/listed.json — chỉ dùng mã trong đây; doanh nghiệp chưa niêm yết (Viettel, VinFast, Amy Grupo…) KHÔNG có mã, không gắn công ty mẹ thay thế.

## Tiêu chí (đúng thế này, không thêm luật riêng)
- **group theo CHỦ THỂ của bài:** 1 = Việt Nam (Nhà nước, chính sách, lãnh đạo, số liệu, đối ngoại của Việt Nam) · 2 = nước ngoài / thế giới (kể cả doanh nghiệp nước ngoài và chính sách nội bộ nước ngoài ⇒ `2f`) · 3 = doanh nghiệp Việt Nam (niêm yết hay CHƯA — TKV, VinFast, công ty phát hành trái phiếu… đều nhóm 3, mã để rỗng nếu chưa niêm yết) HOẶC thị trường tài sản trong nước (chứng khoán, vàng, bất động sản dân sinh ⇒ `3e`) · x = không phải tin tài chính - kinh tế (xã hội, thể thao, giải trí, PR, advertorial; xét nội dung, văn bản pháp quy phi kinh tế vẫn là x). group = x ⇒ sub = x.
- **2a** = thị trường tài chính thế giới gồm tiền mã hoá; **2c** = hàng hoá (vàng, dầu, kim loại) — chỉ khi chủ thể là ngân hàng trung ương mới là 2b.
- **sub:** một trong 21 mã (1a–1f, 2a–2f, 3a–3i). Bài tổng hợp nhiều chủ đề: sub của chủ đề dẫn tiêu đề. Luật do Quốc hội bàn ⇒ chủ thể Nhà nước ⇒ 1a.
- **tickers:** chỉ khi group = 3; mã là CHỦ THỂ CHÍNH của bài, tối đa 5, quan trọng nhất trước; bài liệt kê nhiều mã chỉ chọn mã nổi bật nhất; rỗng nếu không có.
- **industries:** tối đa 3 mã ngành chịu tác động TRỰC TIẾP nhất, áp cho mọi nhóm (Fed ⇒ NGANHANG; thuế quan dệt may ⇒ DETMAY; data center ⇒ CONGNGHE, TIENICH); rỗng nếu vĩ mô thuần hoặc x. Không có sub "công nghệ/AI": tin AI = sub theo loại sự kiện + ngành CONGNGHE.
- **hard:** true nếu phân vân giữa hai nhóm/sub hoặc về mã/ngành, kèm `note` một câu nêu phân vân; bài rõ: note "".

## Đầu ra
Một dòng JSON mỗi bài, cùng thứ tự đầu vào, không bỏ sót, không thêm khoá:
{"article_id": <int>, "group": "1"|"2"|"3"|"x", "sub": "<mã>", "tickers": [...], "industries": [...], "hard": true|false, "note": "..."}
Ghi bằng Python, encoding utf-8, ensure_ascii=False. Tự kiểm sau khi ghi: đủ dòng, sub thuộc đúng group, ticker ∈ listed.json, industry ∈ 24 mã, ≤5 mã, ≤3 ngành, ticker rỗng khi group ≠ 3. Không dispatch subagent. Không sửa file trong repo.
Trả lời chỉ: số dòng, số hard, phân bố group, 3 bài phân vân nhất (article_id + một câu).
