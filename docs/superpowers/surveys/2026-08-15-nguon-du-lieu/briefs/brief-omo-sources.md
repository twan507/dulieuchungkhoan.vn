# Brief — Tìm nguồn OMO / tín phiếu NHNN có thể ETL được

## Bối cảnh

Repo `D:\twan-projects\finext-v2` — nền tảng dữ liệu & phân tích chứng khoán Việt Nam.

**Chỗ trống đã xác định (đọc trước):** `scratchpad/report-omo-gap.md` — controller đã đo và kết luận **không nguồn nào trong dự án có dữ liệu OMO**:
- WiChart: 26 key vĩ mô + tiền tệ, không có OMO. Đã thử dò 11 tên key (`omo`, `tin_phieu`, `repo`…) → 500 cả 11.
- FiinTrade: `GET https://wlgw-core.fiintrade.vn/Master/GetAllChartEconomy` (header `Origin: https://fiinapp.bvsc.com.vn`) → 36 chỉ tiêu, không có OMO.
- BVSC: nguồn thuần giao dịch.

**Vì sao cần:** `.claude/skills/vn-stock-knowledge/references/macro-money-creation.md:320` liệt 5 nhân tố quyết định thanh khoản hằng ngày, **OMO đứng đầu**. Dự án có 4/5, thiếu đúng cái đầu tiên.

**Chỉ thị chủ dự án:** *"sbv có nhưng khó mà thành ETL nổi, thử kiếm cách khác."* → Tức là **đừng dừng ở kết luận "vào sbv.gov.vn mà lấy"**. Phải tìm nguồn có **cấu trúc máy đọc được** (API, JSON, CSV, hoặc HTML bảng ổn định).

## Nhiệm vụ

### Bước 1 — Xác định chính xác cần lấy cái gì
Dữ liệu OMO Việt Nam thường gồm: khối lượng chào thầu / trúng thầu, kỳ hạn, lãi suất trúng thầu, khối lượng đáo hạn, **bơm ròng / hút ròng** (net injection), và phát hành **tín phiếu NHNN** (kỳ hạn, lãi suất, khối lượng). Xác định trường tối thiểu đủ dùng cho phân tích "hôm nay tiền nhiều hay ít".

⚠️ Lưu ý nghiệp vụ từ chính skill (`macro-money-creation.md:178`): *"OMO phần lớn thời gian là điều hoà… Chỉ khi tạo thành xu hướng kéo dài mới nói tới chuyện đổi cung tiền."* → Thứ cần là **chuỗi ròng theo ngày để cộng dồn**, không phải con số giật gân từng phiên.

### Bước 2 — Khảo sát các hướng (dùng WebSearch/WebFetch)

Kiểm ít nhất các hướng sau, **mỗi hướng phải kết luận có/không kèm bằng chứng**:

| Hướng | Cần trả lời |
|---|---|
| **SBV** (`sbv.gov.vn`) | Có trang kết quả đấu thầu OMO không? Dạng gì (HTML table / PDF / Excel)? Có URL ổn định theo ngày không? Chủ dự án nói khó ETL — **xác nhận khó ở điểm nào cụ thể**, đừng chỉ đồng ý |
| **HNX** (`hnx.vn`) | HNX tổ chức đấu thầu TPCP; có công bố dữ liệu thị trường tiền tệ / tín phiếu dạng máy đọc không? |
| **VBMA** (Hiệp hội Thị trường Trái phiếu VN) | Bản tin thị trường tiền tệ có số OMO không? Dạng gì? |
| **Vietstock / CafeF / VnEconomy / Người Đồng Hành** | Có trang dữ liệu OMO dạng bảng lịch sử không (không phải bài báo)? |
| **WiFeed/WiChart gói khác** | Ngoài `vietnambiz/vi-mo` còn namespace nào? Thử dò cấu trúc URL khác |
| **Nguồn tổng hợp quốc tế** | CEIC · Trading Economics · investing.com · DBnomics · IMF IFS · BIS — có series OMO/tín phiếu VN không, có API miễn phí không |
| **Công ty chứng khoán** | SSI/VCBS/BSC/MBS ra báo cáo thị trường tiền tệ hằng ngày có số OMO — dạng PDF? Có trang dữ liệu không? |

### Bước 3 — GỌI THẬT nguồn hứa hẹn nhất
**Trần 50 lời gọi mạng.** Tuần tự, nghỉ ≥1s giữa các lời gọi cùng host. Không dò ngưỡng chặn.

Với 2–3 ứng viên tốt nhất, phải **lấy được dữ liệu thật** và ghi: URL chính xác, định dạng, các trường, khoảng lịch sử, tần suất cập nhật, độ trễ, có cần đăng nhập/khoá không, độ ổn định của cấu trúc (có phải scrape HTML dễ vỡ không).

### Bước 4 — Kết luận xếp hạng
Bảng xếp hạng ứng viên theo: **ETL được không** (trọng số cao nhất) · độ trễ · độ sâu lịch sử · rủi ro vỡ · rủi ro pháp lý quan sát được.
Nếu **không nguồn nào ETL được**, nói thẳng, và đề xuất phương án thoái lui rẻ nhất (ví dụ: parse bản tin PDF định kỳ, hay chấp nhận tần suất tuần thay vì ngày).

## Luật viết
- **Chỉ ghi cái đo được.** Chưa gọi thật → gắn nhãn "chưa kiểm". Suy đoán → gắn nhãn suy đoán.
- Ghi ngày đo (2026-08-15) cạnh mọi con số. Tiếng Việt.
- Không tô hồng. Nguồn nào không dùng được thì nói thẳng lý do.
- Pháp lý: chỉ **ghi điều khoản quan sát được**, không phân tích, không đề xuất việc pháp lý (chủ dự án tự xử lý).

## Đầu ra
1. Báo cáo: `C:\Users\tuanb\AppData\Local\Temp\claude\D--twan-projects-finext-v2\8bdadd16-750b-49f9-979c-7dea29fe37ac\scratchpad\report-omo-sources.md`
2. Mẫu dữ liệu thô: thư mục `...\scratchpad\omo-raw\`

⚠️ **Nếu harness chặn việc ghi file `.md`**, hãy ghi bằng đuôi `.txt` HOẶC trả toàn văn báo cáo trong tin nhắn cuối — đừng bỏ mất nội dung.

**CẤM:** mọi lệnh git; sửa bất kỳ file nào trong `D:\twan-projects\finext-v2`. Chỉ đọc repo, ghi ra scratchpad. **KHÔNG dispatch subagent.**

Trả về ngắn gọn: trạng thái, số lời gọi, xếp hạng ứng viên, khuyến nghị một dòng.
