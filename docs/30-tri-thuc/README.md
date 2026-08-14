# Tri thức chuyên môn

Tầng này chứa **nguyên liệu và nhật ký** đã dùng để dựng hai skill chứng khoán. Bản thân hai skill là sản phẩm chạy được và nằm ở [`.claude/skills/`](../../.claude/skills/), không nằm đây.

| Đường dẫn | Là gì | Đọc khi nào |
|---|---|---|
| [thuat-ngu.md](thuat-ngu.md) | Bảng tra **bắt buộc** khi đụng vào skill | Trước mọi thay đổi nội dung skill |
| [ghi-chu-xay-dung/](ghi-chu-xay-dung/) | Nhật ký ba giai đoạn dựng skill | Khi cần biết *vì sao* skill viết như hiện tại |
| [corpus/](corpus/) | 96 file tóm tắt bài giảng — nguyên liệu | Khi truy nguyên một luận điểm về nguồn |

---

## Hai skill, xếp tầng chứ không song song

| Tầng | Skill | Tải khi | Quy mô |
|---|---|---|---|
| **L1** | [`co-van-chung-khoan-vn`](../../.claude/skills/co-van-chung-khoan-vn/) | Mọi câu về chứng khoán Việt Nam — luôn có mặt | 772 dòng |
| **L2** | [`kien-thuc-chung-khoan-vn`](../../.claude/skills/kien-thuc-chung-khoan-vn/) | Chỉ khi cần một con số, công thức, hay quy trình tính | 2.273 dòng |

**Luật phân định, tự phân xử được:** nội dung chấm được đúng/sai mà không cần biết ai hỏi và thị trường thế nào → L2. Còn lại → L1.

**Luật kiểm được bằng máy:** L1 giữ bản mỏng ở mức *kết luận*, cấm ở mức *cơ chế*. Câu trong L1 chứa công thức, số bước, hoặc ngưỡng số là sai chỗ. ⚠️ Khi quét kiểm, bắt cả cơ chế viết bằng chữ — *"thứ hai"*, *"ba bước"* — quét chữ số thôi sẽ sót.

**Luật thứ ba:** câu cần cả hai tầng thì **L2 cấp nội dung, L1 quyết định hình dạng** câu trả lời.

Skill 3, 4 sau này theo cùng hợp đồng. Tầng L3 trở lên là hệ dữ liệu — xem [tầng ngữ nghĩa cho chatbot](../20-thiet-ke/tang-ngu-nghia-chatbot.md).

## Ba điều dễ làm hỏng skill

Ghi ở đây vì cả ba đều đã suýt xảy ra hoặc đã xảy ra một lần:

**1 · Đừng nhúng danh sách ngành vào skill.** Skill cố ý chỉ nêu *tiêu chí* phân bậc; danh sách ngành do hệ dữ liệu cấp lúc chạy. Quyết định này tốn 9 chỗ sửa và một vòng audit để thực hiện.

**2 · Đừng "sửa ngược" các lỗi nguồn đã được sửa.** Rõ nhất: công thức FCFE của nguồn tính trùng khấu hao. Bản trong skill là bản đã sửa và đã được kiểm bằng một bài tính đầu-cuối — nếu ai đó khôi phục công thức gốc, FCFF sẽ ra 380 thay vì 260. Danh sách đầy đủ ở [`HANDOFF.md`](ghi-chu-xay-dung/HANDOFF.md), mục *Lỗi nguồn đã sửa*.

**3 · Đừng thêm luật để chữa một ca lỗi.** Nguyên tắc đã đặt: tổng quát hoá và cô đọng luật **đang có**, viết hiệu quả hơn — không thêm luật vô tội vạ. Và một bài học đã trả giá để có: **ví dụ mẫu neo hành vi mạnh hơn mệnh lệnh** — thêm rule về độ dài cải thiện 0%, thêm một ví dụ mẫu ngắn cải thiện 15%.

## Cảnh báo phương pháp

Tầng `corpus/` là **bản AI tóm tắt** từ transcript gốc, và nó **có thể khuếch đại nhiễu nhận dạng giọng nói**: một từ nghe nhầm xuất hiện 1 lần trong transcript có thể thành thuật ngữ dùng 10 lần trong bản tóm tắt. Đã xảy ra thật với «nội giải» — thực chất là *biên độ cây nến*.

🔴 Transcript verbatim gốc (`documents/`) **không còn trong repo**. Gặp thuật ngữ nghe lạ mà muốn đối chiếu ngược, phải lấy từ bản lưu trữ ngoài. Xem [ADR 0001](../00-tong-quan/quyet-dinh/0001-cau-truc-kho-tai-lieu.md).
