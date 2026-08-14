# Ghi chú xây dựng skill

Ba file, ba lát cắt thời gian của cùng một dự án. Cố ý **không hợp nhất** — mạch *quyết định nào có trước, đè lên cái gì* chính là giá trị của chúng.

| File | Là gì | Còn hiệu lực |
|---|---|---|
| [HANDOFF.md](HANDOFF.md) | Nhật ký bàn giao giữa các phiên. Đọc file này là đủ để tiếp tục | ✅ **Đầy đủ.** Đọc trước tiên |
| [BAN-DO-KHAI-NIEM.md](BAN-DO-KHAI-NIEM.md) | Kết quả kiểm kê Giai đoạn 1 — 355 section ánh xạ sang 8 file, ngân sách dòng đo thật | ✅ Tham chiếu lịch sử. Việc đã làm xong theo bản đồ này |
| [CAN-SUA.md](CAN-SUA.md) | Bảng các chỗ cần sửa, rà trước Giai đoạn 4 | ⚠️ **Gần hết hiệu lực** — xem bảng dưới |

---

## Trạng thái `CAN-SUA.md` — đã kiểm tận file ngày 2026-08-14

| Phần | Trạng thái |
|---|---|
| **A1–A8** gỡ danh sách ngành cứng | ✅ Đã áp dụng |
| **A9** giữ hay bỏ tên "ngân hàng" trong luận điểm *ngành báo hiệu* | 🔴 **CÒN TREO — cần bạn quyết** |
| **B2** bỏ cột số 1/2/3 ở bảng ba nhóm nhà đầu tư | ✅ Đã áp dụng |
| **B8** đổi ví dụ "quán trà đá" → "quán nước" | ✅ Đã áp dụng |
| **B3, B4, B9, B10** | ✅ Đã quyết giữ nguyên, có lý do |
| **B5, B6, B7, B11** | Theo `HANDOFF` là đã xử lý ở vòng rà soát |

**Về A9:** hiện skill vẫn giữ nguyên tên ngân hàng — *"Ngân hàng đứng đầu bảng xếp hạng an toàn nhưng lại hút tiền đầu tiên… nên nó là ngành báo hiệu"* ([`danh-muc-va-luan-chuyen.md`](../../../.claude/skills/kien-thuc-chung-khoan-vn/references/danh-muc-va-luan-chuyen.md) dòng 97). Đây là *cơ chế*, không phải danh sách ngành cứng, nên nó không vi phạm quyết định ở phần A — nhưng vẫn chưa có quyết định chính thức. Ba lựa chọn: giữ nguyên · đổi thành "nhóm tài chính" · bỏ hẳn.

## Đọc `HANDOFF.md` theo mục đích

| Muốn biết | Mục |
|---|---|
| Vì sao skill viết như hiện tại | §3 quyết định thiết kế đã chốt · §4.3 rủi ro và cách chặn |
| Lỗi nào của nguồn đã được sửa, **đừng sửa ngược** | *Lỗi nguồn đã sửa* — FCFE tính trùng khấu hao, «nội giải», quy đổi 50 ngày, bảng gap |
| Kiến trúc phân tầng L1/L2 | *Kiến trúc phân tầng* + ba luật phân định |
| Kết quả test và tiêu chí dừng | *Giai đoạn 4* — 6 vòng, vòng 6 tính toán trên số liệu thật 10/10 đúng |
| Lỗ hổng gác cổng phạm vi | *Luật phạm vi KHÔNG chặn được câu ngoài hẳn* — chứa nguyên văn đoạn phải dán vào system prompt |
| Nguyên tắc làm việc | §5 — cô đọng, không thêm luật vô tội vạ, không rào đón |

## Bộ test dùng lại được

Vòng 6 là **phép thử hồi quy tốt nhất** cho lỗi FCFE: đưa số liệu, bắt tính ra kết quả. FCFF phải ra **260 tỷ, không phải 380**. Nếu ai đó "sửa ngược" công thức về bản gốc của nguồn, con số sẽ lệch hẳn và bài test bắt được ngay.

Chạy lại bộ này khi: sửa nội dung `dinh-gia.md` · nối function calling vào skill · thêm skill mới vào hệ.
