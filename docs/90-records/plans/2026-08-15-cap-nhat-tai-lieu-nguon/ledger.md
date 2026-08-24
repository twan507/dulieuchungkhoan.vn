# SDD ledger — plan: docs/superpowers/plans/2026-08-15-cap-nhat-tai-lieu-nguon/plan.md

## Quét xung đột trước khi chạy

| Cặp task | Chia sẻ file gì | Kết quả |
|---|---|---|
| T1 ↔ T2 | `01-bvsc-rest.md` vs `00-conventions.md` | Không đụng. T2 ghi bẫy chung, T1 ghi chi tiết endpoint — T1 có thể trỏ link sang T2 nhưng không cần |
| T1 ↔ T3 | T1 mô tả 14 hợp đồng; T3 trỏ link sang | Không đụng file. Plan đã dặn T3 **trỏ link, không chép bảng** |
| T2 ↔ T4 | Bẫy múi giờ ghi ở cả hai | Không đụng file. T2 ghi luật chung, T4 ghi cụ thể cho WiChart + trỏ link |
| T3 ↔ T10 | T3 sửa `09-fiin-market-price.md`, T10 sửa README | Không đụng |
| T5–T8 ↔ nhau | Đều tạo file mới, khác tên | Không đụng |
| T9 ↔ mọi task | ADR chỉ ghi quyết định | Không đụng |
| **T10 ↔ tất cả** | T10 trỏ link tới file do T1–T9 tạo | **Phụ thuộc thật — T10 chạy CUỐI** |

**Mâu thuẫn nội tại của plan:** không có. Mỗi task tự nhất quán.

**Ruling khởi động:** plan viết mỗi task tự `git commit`. **Đổi: agent KHÔNG chạy lệnh git, chỉ ghi file; controller commit.** Lý do: sự cố đầu phiên 2026-08-15 — hai agent trong cùng checkout giẫm commit nhau, một amend rơi nhầm nhánh. Cách này loại hẳn rủi ro và cho phép chạy song song T1–T9 vốn không đụng file nhau. Nếu sai: mất tính "mỗi task một commit" — nhưng controller vẫn commit riêng từng task nên hệ quả bằng 0.

## Tiến độ

EOF_MARKER
- 2026-08-15: CỨU DỮ LIỆU TRƯỚC. Commit d74bbc9 — 22 file báo cáo khảo sát vào docs/superpowers/surveys/2026-08-15-nguon-du-lieu/ + .gitignore lần đầu vào git. Đã push. Rủi ro mất scratchpad khi đóng phiên = 0.
- Commit e7b851b — spec.md + plan.md (10 task chia theo quyền sở hữu file).
- BASE trước khi thực thi: e7b851b.
- Dispatch SONG SONG 8 agent Opus cho Task 1–8. Cơ sở: quét xung đột cho thấy T1–T8 sở hữu file rời nhau hoàn toàn. T9 (ADR) và T10 (đồng bộ README) giữ lại — T10 phụ thuộc kết quả T1–T9.
- Mọi agent bị cấm chạy git (ruling khởi động). Cấm sửa file ngoài phần sở hữu. Cấm tự gọi API đo lại.
- Cảnh báo riêng đã gắn cho T4: file wichart.md có HAI dòng "lệch 1,3%" (dau_wti dòng 357, ure_trung_dong dòng 368). Chỉ được sửa dau_wti. Sửa nhầm ure_trung_dong là lỗi nghiêm trọng vì chưa đo lại.
- Cảnh báo riêng đã gắn cho T3: trỏ link sang bảng 14 hợp đồng của T1, không chép lại.
- Cảnh báo riêng đã gắn cho T6: giấy phép FRED chỉ ghi MỘT DÒNG, không phân tích pháp lý (quy tắc cứng của dự án).
- Cảnh báo riêng đã gắn cho T8: LBMA không thay WiChart cho vàng (WiChart khớp Investing 0,00%); vai là mốc chuẩn + backfill từ 1968. PAXG lấy vì chạy 24/7.
- CHỦ DỰ ÁN yêu cầu giữa chừng: chuyển memory từ thư mục người dùng vào repo. Đã tạo CLAUDE.md ở gốc repo (commit ac81ea6), xoá 2 file memory nội dung, để lại MEMORY.md một dòng trỏ về repo. Lý do giống hệt vụ spec/plan hôm trước: tri thức dự án phải đi theo dự án.
- Task 1 complete → commit d6ffba0. Kiểm: 0 lần "không cung cấp dữ liệu phái sinh", 08:45 xuất hiện 2 lần, 41I1G8000 6 lần, 0 tham chiếu decisions/.
- Task 2 complete → commit eb7f8f3. 4 bẫy 10-13. PHÁT HIỆN LAN TOẢ: đổi tiêu đề "Chín bẫy"→"Mười ba bẫy" làm SAI 4 chỗ khác: docs/README.md:21, 10-sources/README.md:59, roadmap.md:111 (ba chỗ này thuộc T10) và 20-design/market-data-store.md:548 (KHÔNG thuộc task nào — PHẢI THÊM VÀO T10).
- Task 3 complete → commit c169cf8. Trỏ link sang 01-bvsc-rest.md không kèm anchor (cố ý, tránh phụ thuộc tiêu đề T1). Ghi nhận mâu thuẫn sẵn có trong file: dòng 15 ghi "97 trường", mục mới ghi "99 trường" — agent KHÔNG sửa vì không có phép đo mới. Cần rà riêng.
- Task 5 complete (file sbv-omo.md, 248 dòng) — chờ commit cùng đợt file mới.
- Task 4 complete → commit c1bd5d9. HAI PHÂN XỬ:
  (a) Agent ghi 125 ngày thay vì 115 như plan. AGENT ĐÚNG, PLAN CỦA TÔI SAI — báo cáo ghi rõ UTC(sai) n=115→3,35%, giờ VN(đúng) n=125→2,85%. Tôi trộn hai con số khi viết spec. Giữ 125.
  (b) Agent ghi "backwardation chưa xác nhận trực tiếp" vì đọc report §7 — nhưng §7 ĐÃ CŨ, tôi xác nhận backwardation sau đó ở ra-soat-viec-chua-kiem.md §A1 mà quên cập nhật lại báo cáo gốc. Controller sửa cả wichart.md lẫn báo cáo gốc. LỖI CỦA CONTROLLER: đóng một mục "chưa kiểm" mà không cập nhật ngược lại nguồn đã trích.
- Task 6 complete → commit f50ccc9 (fred.md 355 dòng + fx.md 217). Agent TỰ TÍNH LẠI công thức DXY từ 6 tỷ giá đo được → ra đúng 99,6113 và −0,059%, tức ví dụ nghiệm trong file là số tự kiểm chứ không chép suông. Đây là hành vi đáng khen, ghi lại làm chuẩn cho task sau.
- Task 7 complete → commit 5332761 (yahoo.md 447 dòng, 26 bảng). Đặt 3 bẫy cấu trúc TRƯỚC bảng phủ 36 chỉ số vì chúng làm hỏng dữ liệu âm thầm — quyết định trình bày tốt, giữ. Agent ghi "host chính xác của endpoint: chưa kiểm" vì sổ đo chỉ ghi đường dẫn — đúng tinh thần không đoán.
- Task 8 complete → commit 7d03d8f (commodities.md 155 + crypto.md 290). Agent viết ĐÚNG vai trò như đã dặn: LBMA là mốc chuẩn + backfill chứ không thay WiChart; PAXG lấy vì độ phủ thời gian chứ không phải vì WiChart lệch. Còn tự thêm cảnh báo "Đừng ghi lý do lấy PAXG là WiChart lệch".
- Task 5 complete → commit 7c6461f (sbv-omo.md 248 dòng).
- CONTROLLER KIỂM CHỨNG cụm 6 file mới (1.712 dòng): 0 file trỏ về decisions/ (luật vàng OK) · 0 liên kết chết sau khi yahoo.md xuất hiện · mọi file đều có nhãn "đo 2026-08-15" (1-17 lần) và đều có mục "chưa kiểm" (3-8 mục) — dấu hiệu trung thực, không file nào tô hồng · 4/4 từ khoá nghiệm thu của yahoo.md đạt.
- CÒN LẠI: T9 (ADR) đang chạy · T10 (đồng bộ README) chờ T9.
- PHẠM VI THÊM CHO T10 (phát sinh từ T2): 4 chỗ ghi "9 bẫy"/"Chín bẫy" nay sai — docs/README.md:21, 10-sources/README.md:59, roadmap.md:111, và 20-design/market-data-store.md:548 (chỗ cuối KHÔNG có trong plan gốc, phải thêm).
- Task 9 complete → commit 19b90fd (ADR 0006, 119 dòng). Agent TỰ CHẠY phép thử luật vàng đúng cách: quét cơ học tìm URL/endpoint/tên trường/số đo → 0 kết quả; rồi kiểm mất mát bằng cách đối chiếu từng tri thức xem tầng sống còn giữ không. Controller kiểm lại độc lập: 0 URL, 0 tên trường, đúng 8 quyết định, 0 liên kết chết. ĐẠT.
- Agent 9 báo: grep "decisions/" báo vi phạm nhưng là các tham chiếu CÓ SẴN TỪ TRƯỚC (changelog 10-sources/README:134,137 — ngoại lệ ADR 0005 §4 cho phép; docs/README:11,33 mô tả chính thư mục; 10-fiin-dictionary:291 ghi chú lịch sử). Ruling: KHÔNG sửa — changelog trích ADR là trích lịch sử, đúng bản chất; và nội dung vẫn tự chứa nên phép thử xoá decisions/ vẫn đạt.
- Task 10 dispatched (task cuối). Phạm vi mở rộng so với plan: thêm quyền sửa ĐÚNG MỘT DÒNG ở 20-design/market-data-store.md:548 ("Chín bẫy đầy đủ") vì không task nào sở hữu file đó. Cộng việc thêm ADR 0006 vào danh sách ở docs/README.md:33.
- Trạng thái: 9/10 task xong, 10 commit từ BASE e7b851b, cây sạch sau mỗi commit.
