# Corpus — nguyên liệu dựng skill

**96 file · 1,85 MB · bất biến.** Đây là **nguyên liệu**, không phải tài liệu dự án. Đừng sửa; đừng trích thẳng cho người dùng cuối.

> Kích thước đo ngày 2026-08-14: HP0–HP6 **1.331 KB** (67 file) + Trà Chiều **564 KB** (29 file). Tài liệu cũ từng ghi *"~2,1 MB"* — đó là ước lượng, không phải số đo.

Nội dung: bản AI tóm tắt và hệ thống hoá từ các buổi giảng của một chuyên gia chứng khoán Việt Nam.

| Thư mục | Nội dung | Số file | Đã dùng cho |
|---|---|---|---|
| `HP0` – `HP6` | Sáu học phần: nhập môn · trò chơi dòng tiền · phân tích kinh tế · phân tích cơ bản · phân tích kỹ thuật · xây dựng danh mục · chủ đề nâng cao | 67 | **Skill L2** `vn-stock-knowledge` |
| `Tra Chieu` | Nhận định thị trường theo tuần, 2026 | 29 | **Skill L1** `vn-stock-advisor` |

---

## Ba điều phải biết trước khi đọc

**1 · Đây là bản tóm tắt, không phải bản gốc.** Transcript verbatim (`documents/`) đã được đưa ra khỏi repo — xem [ADR 0001](../../00-overview/decisions/0001-docs-structure.md).

**2 · Tầng tóm tắt có thể khuếch đại nhiễu nhận dạng giọng nói.** Một từ nghe nhầm xuất hiện **1 lần** trong transcript gốc có thể thành thuật ngữ dùng **10 lần** ở đây. Đã xảy ra thật với «nội giải» — thực chất là *biên độ cây nến*. Gặp thuật ngữ nghe lạ, đối chiếu [bảng thuật ngữ](../terminology.md) trước khi tin.

**3 · Corpus là nhiều thế hệ giáo trình, không phải một khoá học.** Nhãn `V1 2022` · `V2 2023` · `V3` · `V4` · `Ứng dụng 2024` · `Version đặc biệt` là **phiên bản giáo trình, không phải ngày ghi hình**. Khi hai bản mâu thuẫn:

1. Dùng **ngày quay được chú thích** trong file (12 file có) — ưu tiên cao nhất
2. Rồi mới tới nhãn *"Ứng dụng 2024"* / *"Version đặc biệt"* — thế hệ muộn
3. Nhãn V1–V4 chỉ dùng khi không có thông tin nào khác

**Không bao giờ dùng ngày upload.**

## Ba cơ chế kiểm soát chất lượng có sẵn trong file

Đây là điểm mạnh của corpus — khai thác thay vì tự dựng:

| Section | Số file có | Dùng thế nào |
|---|---|---|
| *"Bối cảnh thị trường lúc giảng"* | 28 | **Bỏ nguyên khối** — nội dung gắn thời điểm đã bị cách ly sẵn |
| *"Điểm thầy nhấn mạnh"* | 27 | **Đọc trước tiên** — phần đúc kết sẵn, dùng làm xương sống |
| Marker `[?...]` | 111 | Chỗ nghe không chắc đã lộ diện sẵn — bỏ luận điểm, hoặc ghi rõ là không chắc |

## Mọi số liệu trong corpus đã chết

Toàn bộ là **2022–2024**. Công thức và định nghĩa còn nguyên giá trị; con số quan sát thì không.

- ✅ Giữ: *"số nhân tiền = 1 / tỷ lệ dự trữ bắt buộc"*
- ❌ Bỏ: *"số nhân tiền khoảng 33 lần"*, *"P/E ngân hàng 8,06"*

Ngân sách dòng đo thật và luật *"vượt thì nén đâu, không được cắt đâu"*: [maintenance.md §8](../maintenance.md). Bản đồ chi tiết 355 section → 8 file skill là tài liệu trung gian của Giai đoạn 1, đã bỏ theo [ADR 0004](../../00-overview/decisions/0004-drop-session-logs.md) — còn ở commit `a14eb54`.
