# Worksheet — bảng điền tay của chủ dự án

Nơi để những bảng **cần người quyết nội dung**, xuất từ dữ liệu thật để điền rồi nạp lại. Không phải tài liệu sống, không phải bản ghi lịch sử — là **đầu vào công việc**.

Tên file tiếng Anh, nội dung (kể cả tên sheet) tiếng Việt — [CLAUDE.md §1.5](../../../CLAUDE.md).

---

## 🔴 `industry-mapping.xlsx` — file để ĐIỀN

Mở bằng Excel, sheet **`Phân ngành`**, điền cột **`NGÀNH CỦA TÔI`** (ô vàng) — **chọn từ dropdown**, không gõ tay.

| Sheet | Nội dung |
|---|---|
| `Hướng dẫn` | cách dùng · một dòng ví dụ mẫu · 4 ca gán lệch đã biết · giới hạn độ phủ |
| `Phân ngành` | **37 dòng để điền** — cột A–E là dữ liệu, cột F để trống |
| `Mã ngành` | 24 mã ngành + tên đầy đủ, để tra |

**37 dòng phủ 100% của 1.550 doanh nghiệp** — không doanh nghiệp nào thiếu `icb_code` *(đo 2026-08-26)*. Xếp theo số doanh nghiệp giảm dần, nên **10 dòng đầu đã phủ phần lớn thị trường**; không cần làm đủ 37 mới dùng được.

| Cột | Nghĩa |
|---|---|
| `Mã ICB L3` | khoá để nạp vào `market.industry_icb_map` — lưu dạng **văn bản**, giữ số 0 đầu |
| `Tên ngành ICB cấp 3` · `Nhóm ICB cấp 2` | để nhận diện nhánh |
| `Số DN` | số doanh nghiệp rơi vào nhánh |
| `Một số mã` | tối đa 12 mã đang niêm yết làm mẫu — **không phải danh sách đầy đủ** |
| **`NGÀNH CỦA TÔI`** | **cột để điền**, dropdown 24 giá trị |

### Bốn ca đã biết là gán lệch

Ghi sẵn ở [industry-tree §5](../../20-design/industry-tree.md). **Không sửa được bằng bảng ICB này** — một nhánh ICB chỉ map về một ngành, nên phải gán tay từng doanh nghiệp sau khi nạp. Biết trước lúc điền thì đỡ nghĩ lại:

| Mã | Đang ở | Vấn đề |
|---|---|---|
| `TRC` · `DRI` | CAOSU | Cao su thiên nhiên **ngược chiều giá cao su** với nhóm săm lốp cùng ngành — chỉ số dòng tiền ngành tự triệt tiêu |
| `TTF` · `ACG` · `GDT` · `SAV` | BANLE | Gỗ nội thất **xuất khẩu** — rủi ro giống hàng xuất khẩu (đơn hàng Mỹ, tỷ giá) hơn bán lẻ nội địa |
| `IPA` | DIENNUOC | Thực chất holding tài chính (công ty mẹ của VND) |
| `VEF` | DULICH | Thực chất bất động sản dự án |

### Nạp lại thế nào

Điền xong đưa lại file — nạp qua **migration seed**, giống `0003_seed_industry`. `market.industry_icb_map` **không có đường ghi runtime** nên seed ở migration là đúng chỗ *(khác `market.security`, nơi ETL ghi hằng ngày — một bảng một người ghi)*.

Sau khi nạp: `issuer.industry_id` gán theo map, rồi **gán tay đè lên** cho bốn ca trên. ETL hằng ngày **không bao giờ ghi đè** cột đó *(luật tay-thắng-máy, đã khoá bằng test)*.

---

## `all-securities.xlsx` — toàn bộ 2.015 mã trong kho

Tra cứu, không phải để điền. Sheet `Toàn bộ mã`, có auto-filter. Xuất 2026-08-26 sau lượt refdata đầu tiên.

| Cột | Ghi chú |
|---|---|
| `Mã` · `Sàn` · `Loại` · `Trạng thái` | `Loại`: `stock` 1.963 · `etf` 31 · `index` 18 · `fund_cert` 3 |
| `Tên doanh nghiệp` · `Loại hình` | rỗng khi mã **không có issuer** |
| `ICB L4` · `Tên ICB L4` · `ICB L3` | rỗng cùng lý do; lưu dạng văn bản |

⚠️ **437 cổ phiếu (chủ yếu UPCOM) không có `icb_code`** nên bảng map không với tới. Chúng sẽ có `industry_id` rỗng cho tới khi gán tay hoặc tìm được nguồn ngành khác — **là độ phủ thật của nguồn, không phải lỗi**.

---

## Vì sao `.xlsx` chứ không phải `.csv`

*(Ghi 2026-08-27 sau khi bản CSV hỏng trên máy chủ dự án — bản CSV đã xoá hẳn để không ai mở nhầm.)*

| Lỗi của bản CSV | Hậu quả |
|---|---|
| UTF-8 **không BOM** | Excel trên Windows đọc theo codepage hệ thống ⇒ **vỡ hết dấu tiếng Việt** |
| Excel hỏi *"Remove leading zeros"* | Bấm Convert là **ăn mất số 0 đầu** của mã ICB (`0533`) và `organ_code` (`0106839469`) — **hỏng dữ liệu thật**, không chỉ hiển thị |

`.xlsx` chặn cả hai bằng cấu tạo: encoding nằm trong định dạng, và mọi cột mã khai `number_format='@'` (văn bản) nên Excel không đụng vào. Thêm dropdown để mã ngành không thể gõ sai.
