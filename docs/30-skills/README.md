# Tri thức chuyên môn

Tầng này chứa **nguyên liệu và tài liệu bảo trì** của hai skill chứng khoán. Bản thân hai skill là sản phẩm chạy được và nằm ở [`.claude/skills/`](../../.claude/skills/), không nằm đây.

| Đường dẫn | Là gì | Đọc khi nào |
|---|---|---|
| [maintenance.md](maintenance.md) | Những thứ **sửa nhầm sẽ làm hỏng skill mà không có gì báo lỗi** | **Trước mọi thay đổi** trong `.claude/skills/` |
| [terminology.md](terminology.md) | Bảng tra **bắt buộc** — hai trục phân loại, chuyển đổi thuật ngữ nguồn | Cùng lúc với file trên |
| [corpus/](corpus/) | 96 file tóm tắt bài giảng — nguyên liệu, không phải tài liệu | Khi truy nguyên một luận điểm về nguồn |

**Dự án skill đã đóng ngày 2026-08-14** — hai skill xong, test 6 vòng, không còn việc treo.

---

## Hai skill, xếp tầng chứ không song song

| Tầng | Skill | Tải khi | Quy mô |
|---|---|---|---|
| **L1** | [`vn-stock-advisor`](../../.claude/skills/vn-stock-advisor/) | Mọi câu về chứng khoán Việt Nam — luôn có mặt | 774 dòng |
| **L2** | [`vn-stock-knowledge`](../../.claude/skills/vn-stock-knowledge/) | Chỉ khi cần một con số, công thức, hay quy trình tính | 2.272 dòng |

Ba luật phân định, áp cho cả skill 3, 4 sau này:

**1 · Tự phân xử được.** Nội dung chấm được đúng/sai mà không cần biết ai hỏi và thị trường thế nào → **L2**. Còn lại → **L1**.

**2 · Kiểm được bằng máy.** L1 giữ bản mỏng ở mức *kết luận*, cấm ở mức *cơ chế*. Câu trong L1 chứa công thức, số bước, hoặc ngưỡng số là sai chỗ. ⚠️ Khi quét kiểm, bắt cả cơ chế viết bằng chữ — *"thứ hai"*, *"ba bước"* — quét chữ số thôi sẽ sót.

**3 · Câu cần cả hai tầng** thì **L2 cấp nội dung, L1 quyết định hình dạng** câu trả lời.

Tầng L3 trở lên là hệ dữ liệu — xem [tầng ngữ nghĩa cho chatbot](../20-design/chatbot-semantic-layer.md).

## Trước khi sửa skill

Ba thứ hay bị làm hỏng nhất, chi tiết ở [`maintenance.md`](maintenance.md):

1. **Đừng nhúng danh sách ngành vào skill** — skill cố ý chỉ nêu *tiêu chí* phân bậc; danh sách ngành do hệ dữ liệu cấp lúc chạy. Nhưng cũng **đừng gỡ nhầm** bốn chỗ nêu tên ngành vì lý do kế toán hoặc định giá.
2. **Đừng "sửa ngược" năm lỗi của nguồn đã được sửa** — rõ nhất là công thức FCFE tính trùng khấu hao. Khôi phục bản gốc thì FCFF ra 380 thay vì 260.
3. **Đừng thêm luật để chữa một ca lỗi** — tổng quát hoá luật đang có. Ví dụ mẫu neo hành vi mạnh hơn mệnh lệnh.

Và **năm thứ trông như lỗi nhưng là cố ý** — trùng lặp có chủ đích giữa hai skill, marker `[?…]`, anchor không dấu, hai phép đếm tình cờ dùng chung con số. Đã soi và quyết giữ, có lý do.
