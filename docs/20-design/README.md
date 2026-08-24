# Thiết kế hệ thống

Tầng này ghi **lựa chọn của dulieuchungkhoan.vn** — cái gì xây thế nào và vì sao chọn thế. Khác với [`10-sources/`](../10-sources/) vốn chỉ ghi sự thật đo được về hệ thống của người khác.

**Luật sửa:** sửa được, nhưng lý do phải viết thẳng vào chính tài liệu. Một thiết kế không có lý do là một thiết kế sẽ bị đảo ngược bởi người tiếp theo.

| File | Nội dung | Trạng thái |
|---|---|---|
| [service-topology.md](service-topology.md) | Ranh giới **process** của backend · ba tiến trình `ingester`/`etl`/`api` tách theo vòng đời · ai ghi miền nào · rate limiter lên Redis · lát cắt writer trước · bố cục `backend/` | ✅ chốt trước khi viết code |
| [test-strategy.md](test-strategy.md) | Công cụ test theo stack (pytest · Vitest · Playwright) · **cấm gọi thật nguồn ngoài trong CI** (tách với giám sát hợp đồng) · DB test thật không SQLite · bẫy đơn vị · chống test giả | ✅ chốt định hướng |
| [market-data-store.md](market-data-store.md) | Cách ly hoàn toàn khỏi nguồn · Ingester active+standby · SSE · lược đồ TimescaleDB · lịch ETL · giám sát hợp đồng dữ liệu · thứ tự triển khai | ✅ đã duyệt, chưa cài đặt · ⚠️ kho realtime sẽ đổi sang ClickHouse (ADR 0007) |
| [news-pipeline.md](news-pipeline.md) | Mọi tin qua lưới AI không đường tắt · taxonomy 3 nhóm 20 sub · gắn mã cổ phiếu 3 tầng · kho toàn văn bất biến · tìm kiếm Postgres | ✅ đã duyệt, chưa cài đặt |
| [chatbot-semantic-layer.md](chatbot-semantic-layer.md) | Luật phân định bốn tầng · 8 function · ba quy tắc nối dữ liệu vào skill · điều chưa biết | 🟡 **đề xuất, chưa duyệt** |
| [market-field-selection.md](market-field-selection.md) | Luật chọn nguồn · bảng lấy/bỏ từng mã trường của BVSC, Screener, Snapshot · bảng đối soát số đếm · danh sách cần kiểm API. Bản máy đọc: [market-field-selection.json](market-field-selection.json) | ✅ đã chốt (trải từ quyết định 2026-08-14) |

⚠️ Hai file `market-field-selection.md` và `market-field-selection.json` **sinh tự động** từ [`gen_field_selection.py`](gen_field_selection.py) — sửa nội dung thì sửa trong script rồi chạy lại, **cấm sửa tay**.

---

## Ba nguyên tắc xuyên suốt ba tài liệu kiến trúc — kho dữ liệu, pipeline tin, tầng ngữ nghĩa

**1 · Cách ly hoàn toàn khỏi nguồn.** dulieuchungkhoan.vn không bao giờ gọi thẳng API nhà cung cấp khi phục vụ người dùng. Ba lý do đều đo được: độ trễ chênh ~1.000 lần so với đọc từ Postgres · API không có versioning và không thông báo thay đổi · chatbot hỏi hàng chục câu mỗi phút.

**2 · Không có đường tắt trong xử lý.** Mọi tin đều đi qua lưới AI kể cả tin từ feed thuần nhất. Phương án lai tiết kiệm ~40% lượt gọi đã bị loại: hai đường xử lý song song tạo ra **lỗi im lặng** khi feed đổi nội dung mà config không đổi theo.

**3 · Lưu thô, biến đổi lúc đọc.** Giá lưu thô và điều chỉnh khi đọc; tin lưu toàn văn ngay khi nhận, bất biến, không ghi đè. Không bao giờ sửa quá khứ.

## Nơi hai nhánh gặp nhau

Nhánh dữ liệu thị trường và nhánh tin tức độc lập tới tận tầng kho, gặp nhau lần đầu ở tầng ngữ nghĩa qua **mã cổ phiếu** — khoá nối duy nhất. Hệ quả quan trọng nhất: bảng `organization` là **nguồn sự thật duy nhất** cho danh sách mã, pipeline tin không được tự nạp bản riêng.

Chi tiết ba mắt xích nối: [kiến trúc tổng thể §3](../00-overview/architecture.md).
