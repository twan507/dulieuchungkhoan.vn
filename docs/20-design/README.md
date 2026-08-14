# Thiết kế hệ thống

Tầng này ghi **lựa chọn của Finext** — cái gì xây thế nào và vì sao chọn thế. Khác với [`10-sources/`](../10-sources/) vốn chỉ ghi sự thật đo được về hệ thống của người khác.

**Luật sửa:** sửa được, nhưng quyết định lớn phải để lại lý do ở [`00-overview/decisions/`](../00-overview/decisions/). Một thiết kế không có lý do là một thiết kế sẽ bị đảo ngược bởi người tiếp theo.

| File | Nội dung | Trạng thái |
|---|---|---|
| [market-data-store.md](market-data-store.md) | Cách ly hoàn toàn khỏi nguồn · Ingester active+standby · SSE · lược đồ TimescaleDB · lịch ETL · giám sát hợp đồng dữ liệu · thứ tự triển khai | ✅ đã duyệt, chưa cài đặt |
| [news-pipeline.md](news-pipeline.md) | Mọi tin qua lưới AI không đường tắt · taxonomy 3 nhóm 20 sub · gắn mã cổ phiếu 3 tầng · kho toàn văn bất biến · tìm kiếm Postgres | ✅ đã duyệt, chưa cài đặt |
| [chatbot-semantic-layer.md](chatbot-semantic-layer.md) | Luật phân định bốn tầng · 8 function · ba quy tắc nối dữ liệu vào skill · điều chưa biết | 🟡 **đề xuất, chưa duyệt** |

---

## Ba nguyên tắc xuyên suốt cả ba tài liệu

**1 · Cách ly hoàn toàn khỏi nguồn.** Finext không bao giờ gọi thẳng API nhà cung cấp khi phục vụ người dùng. Ba lý do đều đo được: độ trễ chênh ~1.000 lần so với đọc từ Postgres · API không có versioning và không thông báo thay đổi · chatbot hỏi hàng chục câu mỗi phút.

**2 · Không có đường tắt trong xử lý.** Mọi tin đều đi qua lưới AI kể cả tin từ feed thuần nhất. Phương án lai tiết kiệm ~40% lượt gọi đã bị loại: hai đường xử lý song song tạo ra **lỗi im lặng** khi feed đổi nội dung mà config không đổi theo.

**3 · Lưu thô, biến đổi lúc đọc.** Giá lưu thô và điều chỉnh khi đọc; tin lưu toàn văn ngay khi nhận, bất biến, không ghi đè. Không bao giờ sửa quá khứ.

## Nơi hai nhánh gặp nhau

Nhánh dữ liệu thị trường và nhánh tin tức độc lập tới tận tầng kho, gặp nhau lần đầu ở tầng ngữ nghĩa qua **mã cổ phiếu** — khoá nối duy nhất. Hệ quả quan trọng nhất: bảng `organization` là **nguồn sự thật duy nhất** cho danh sách mã, pipeline tin không được tự nạp bản riêng.

Chi tiết ba mắt xích nối: [kiến trúc tổng thể §3](../00-overview/architecture.md).
