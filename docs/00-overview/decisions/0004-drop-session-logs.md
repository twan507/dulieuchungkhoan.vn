# 0004 · Bỏ nhật ký phiên, giữ tài liệu trạng thái

**Ngày:** 2026-08-14 · **Trạng thái:** đã áp dụng · **Thay thế** [ADR 0001](0001-docs-structure.md) §6

## Bối cảnh

Kho có hai loại tài liệu bị trộn lẫn từ đầu:

| Loại | Trả lời câu hỏi | Hết hạn khi |
|---|---|---|
| **Nhật ký phiên** | *Phiên trước làm tới đâu, phiên sau làm gì tiếp* | Dự án đóng |
| **Tài liệu trạng thái** | *Hệ thống hiện đang thế nào, sửa gì thì hỏng* | Không hết hạn |

`HANDOFF.md` sinh ra để chuyển giao giữa các phiên lúc mới bắt đầu dự án skill, khi kiến thức còn nằm rải ở nhiều nguồn. `BAN-DO-KHAI-NIEM.md` là kết quả kiểm kê Giai đoạn 1, chờ duyệt trước khi chạy Giai đoạn 2. Cả hai đã hoàn thành nhiệm vụ.

Vấn đề là chúng **không tự biết mình đã hết hạn**. Đo được, không phải cảm tính:

- `HANDOFF.md` dòng đầu khai *"Skill 1 test 5 vòng · Skill 2 Giai đoạn 2 đang chạy"* trong khi chính phần cuối file ghi 6 vòng và *"kết luận: dừng tối ưu"*
- §4.4 còn nguyên *"👉 CÂU HỎI DUY NHẤT CẦN NGƯỜI DÙNG TRẢ LỜI TRƯỚC KHI VIẾT"* — đã trả lời từ lâu
- §4.5 mô tả **kiến trúc đề xuất** khác với kiến trúc đã dựng thật
- §6 *"Giai đoạn 4 — CÒN LẠI"* — đã xong
- `BAN-DO-KHAI-NIEM.md` dòng 3: *"Chờ duyệt trước khi chạy Giai đoạn 2"*

Và chúng **trùng với tài liệu trạng thái đang có**: luật phân tầng L1/L2 cùng ba luật phân định nằm nguyên ở cả `HANDOFF.md` lẫn `30-tri-thuc/README.md`, hai bản không đồng bộ với nhau.

ADR 0001 §6 chốt *không hợp nhất* các file này, lý do: gộp lại sẽ mất mạch **quyết định nào có trước, đè lên cái gì**. Lý do đó đúng **khi dự án đang chạy** — lúc ấy thứ tự quyết định là thông tin sống, vì quyết định sau có thể bị đảo. Dự án đóng rồi thì cái còn giá trị là **kết quả cuối và các bẫy**, còn thứ tự thì git giữ.

## Quyết định

**1 · Bỏ hẳn loại tài liệu "nhật ký phiên" khỏi kho.**

Kho không giữ tài liệu mô tả *phiên làm việc*. Thứ tự và lịch sử là việc của git. Tài liệu chỉ mô tả **hệ thống đang thế nào**.

**2 · Xoá `30-tri-thuc/ghi-chu-xay-dung/` — cả ba file.**

Thay bằng [`30-tri-thuc/bao-tri-skill.md`](../../30-skills/maintenance.md): **140 dòng thay cho 529 dòng**. Chỉ giữ thứ mà sửa nhầm sẽ làm hỏng skill:

| Giữ lại | Vì sao |
|---|---|
| Quyết định thiết kế không được đảo | Đảo là quay lại vấn đề đã tốn một vòng audit |
| 4 chỗ nêu tên ngành **không được gỡ nhầm** | Audit sau sẽ gỡ nhầm nếu không ghi |
| 5 lỗi nguồn đã sửa | Đối chiếu corpus sẽ tưởng skill sai mà "sửa ngược" |
| 5 thứ trông như lỗi nhưng cố ý | Cùng lý do trên |
| Bộ test hồi quy — FCFF **260 chứ không phải 380** | Phép thử duy nhất bắt được lỗi "sửa ngược" |
| Nguyên văn đoạn phải dán vào system prompt | Skill không tự gác cổng phạm vi được |
| Ngân sách dòng + cắt đâu nếu vượt | Chống phình và chống cắt nhầm |
| Ba thao tác đã trả giá | `grep` không đọc được `«` · `sed` hàng loạt sinh lỗi · phải diff không tin báo cáo |

Bỏ đi: kế hoạch từng giai đoạn, mẫu prompt cho subagent, kiến trúc đề xuất (khác bản đã dựng), danh sách "việc tiếp theo" đã xong, số liệu kiểm kê trung gian.

**3 · Bỏ mục "Bàn giao phiên 2026-08-14" khỏi `lo-trinh.md`.**

Cùng loại tài liệu, nằm nhầm chỗ: một bản bàn giao phiên đặt trong tài liệu lộ trình, và **54 dòng của nó trùng gần hết với §0–§6 của chính file** — ba việc đã làm đều đã có trong bảng trạng thái và trong ADR 0001/0002, hai bài học phương pháp đã có nguyên văn ở §6.

**4 · Ranh giới mới, áp cho mọi tài liệu về sau.**

| Thư mục | Chứa | Luật sửa |
|---|---|---|
| `10-nguon-du-lieu/` | Sự thật đo được về hệ thống người khác | Chỉ sửa khi **đo lại** |
| `20-thiet-ke/` | Lựa chọn của Finext | Sửa được, ghi lý do vào `quyet-dinh/` |
| `30-tri-thuc/` | Nguyên liệu + **tài liệu bảo trì** skill | Corpus bất biến; tài liệu bảo trì cập nhật theo trạng thái thật |
| `00-tong-quan/` | Hợp nhất, lộ trình, sổ quyết định | Lộ trình chỉ chứa **việc còn phải làm**, không chứa nhật ký |

Điều khoản *"nhật ký chỉ thêm, không xoá"* của `30-tri-thuc/` **bãi bỏ** — nó tạo ra đúng vấn đề ADR này đang sửa: tài liệu hết hạn không xoá được, phải chồng lớp cải chính lên nhau.

## Hệ quả

**Tốt:**

- Không còn tài liệu nào trong kho tự mô tả sai trạng thái của mình. Đây là điều kiện để tin được tài liệu.
- Trùng lặp luật phân tầng L1/L2 giữa hai file đã hết — nay chỉ nằm ở [`30-tri-thuc/README.md`](../../30-skills/README.md).
- `30-tri-thuc/` còn 3 mục thay vì 4, mỗi mục một vai rõ: bảo trì · thuật ngữ · corpus.
- `lo-trinh.md` thành lộ trình thuần, đọc từ trên xuống là ra việc phải làm.

**Phải chấp nhận:**

- Mất mạch thời gian của dự án skill dưới dạng đọc được. Phải `git log` / `git show a14eb54` mới dựng lại được. Đánh đổi có ý thức: dự án đã đóng, xác suất cần lại thấp.
- Mất chi tiết quy trình dựng skill — mẫu prompt cho 8 subagent, phân bổ 355 section, quy trình 4 giai đoạn. Dựng skill 3 sẽ phải thiết kế lại quy trình thay vì chép. Chấp nhận được vì quy trình đó gắn chặt với corpus cụ thể, và **bài học phương pháp** rút ra từ nó thì đã giữ.

## Đã cân nhắc và loại

| Phương án | Vì sao loại |
|---|---|
| **Giữ nguyên, thêm khối "đã đóng" ở đầu mỗi file** | Đã làm thử với `HANDOFF.md` trong chính phiên này. Kết quả: một file 347 dòng mà người đọc phải tự phân biệt đoạn nào còn đúng — đúng cái mà tài liệu phải làm thay cho người đọc. Chồng lớp cải chính làm tài liệu khó đọc hơn, không dễ hơn |
| **Giữ `HANDOFF.md` làm tài liệu lịch sử, đánh dấu rõ** | Nếu nó là bản ghi trung thực của một thời điểm thì được. Nhưng nó là bản ghi **giữa chừng** — mô tả kiến trúc chưa dựng và câu hỏi chưa trả lời. Tài liệu lịch sử phải đúng ở thời điểm nó mô tả; cái này thì không |
| **Gộp cả vào `30-tri-thuc/README.md`** | README là chỉ mục, phải ngắn để còn dùng làm cửa vào. 140 dòng bảo trì nhét vào đó thì hỏng cả hai vai |
| **Giữ `BAN-DO-KHAI-NIEM.md` vì có ngân sách dòng đo thật** | Ngân sách dòng đúng là còn giá trị — nhưng nó là **8 dòng trong 138**. Đã chuyển sang `bao-tri-skill.md` §8 kèm luật "vượt thì nén đâu, không cắt đâu" |
