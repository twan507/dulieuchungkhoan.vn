# Worksheet — bảng điền tay của chủ dự án

Nơi để những bảng **cần người quyết nội dung**, xuất từ dữ liệu thật để điền rồi nạp lại. Không phải tài liệu sống, không phải bản ghi lịch sử — là **đầu vào công việc**.

Tên file tiếng Anh, nội dung (kể cả tên sheet) tiếng Việt — [CLAUDE.md §1.5](../../../CLAUDE.md).

---

## `industry-mapping.xlsx` — ẢNH CHỤP, không phải nguồn sự thật

🔴 **Nội dung map đã chốt và chuyển sang tài liệu sống: [`20-design/industry-mapping.md`](../../20-design/industry-mapping.md)** *(kèm bản máy đọc `.json`, sinh từ `gen_industry_mapping.py`)*. File Excel này giữ lại để **xem tay cho tiện**, không dùng làm nguồn nạp — nếu hai bên lệch nhau thì tài liệu sống đúng.

Quá trình rà 295 mã và các phương án đã loại: [sổ rà lớp 2](../plans/2026-08-27-industry-two-layer-mapping/layer2-review.md) · [spec](../plans/2026-08-27-industry-two-layer-mapping/spec.md).

*(Dựng 2026-08-27. Bản đầu là 37 dòng ICB cấp 3 để trống chờ điền tay; bản này đã chốt hết.)*

| Sheet | Nội dung |
|---|---|
| `Hướng dẫn` | cơ chế hai lớp · ba ca ICB không với tới · đối chiếu bốn ca cũ ở industry-tree §5 · giới hạn độ phủ |
| `Lớp 1 - ICB` | **56 dòng** — 39 dòng ICB cấp 3 (mặc định) + 16 dòng cấp 4 (ngoại lệ, nền vàng) + 1 dòng không nạp (nền cam) |
| `Lớp 2 - Gán tay` | **161 dòng** gán tay đè lên lớp 1 |
| `Độ phủ` | phân bố doanh nghiệp sau khi áp cả hai lớp |
| `Mã ngành` | 24 mã ngành level 2 — nguồn của dropdown ở cả hai sheet trên |

Cột ngành ở cả hai sheet đều là **dropdown 24 giá trị** — sửa bằng cách chọn, không gõ tay.

### Hai lớp là gì

| Lớp | Chỗ ở trong kho | Ai ghi |
|---|---|---|
| **1 · máy** | `market.industry_icb_map` → `market.issuer.industry_id` | job `etl refdata`, mỗi lượt |
| **2 · tay** | `market.issuer_industry_override` — **đã nạp qua migration `0012` (tạo bảng) + `0013` (seed 161 dòng)**, đo trên DB thật 2026-08-28 | người, qua migration seed |

Đọc ra là `COALESCE(lớp 2, lớp 1)` qua view `market.v_issuer_industry` (migration `0012`, cột `source` ∈ `manual` | `icb` | `NULL`): mã mới niêm yết tự có ngành qua lớp 1; ai đã đè tay thì tay thắng.

🔴 **Vì sao lớp 1 trộn hai cấp ICB:** luật phân giải ở [DDL 0002](../../../database/migrations/versions/0002_market_identity.py) là *khớp `icb_code` chính xác trước, không có thì leo `icb_code_path` lấy tổ tiên gần nhất*. Nên dòng cấp 4 **thắng** dòng cấp 3 cùng nhánh, còn dòng cấp 3 làm **nền** để mã ICB lá mới chưa từng thấy vẫn leo lên được thay vì rơi NULL. Đây là lý do không dùng bảng cấp-4-thuần.

Cấp 4 chỉ thêm ở **10 nhánh cấp 3 chứa từ hai ngành riêng trở lên**. Riêng `2350` (Xây dựng và Vật liệu) và `1350` (Hóa chất) nếu để nguyên cấp 3 sẽ gán sai một nửa của **370 doanh nghiệp**.

Ba dòng cấp 3 **chưa có doanh nghiệp nào** — `0580` Năng lượng thay thế · `2710` Hàng không & Quốc phòng · `8670` Quỹ ủy thác BĐS — vẫn phải có mặt: thiếu chúng thì mã lá mới rơi vào đó sẽ leo lên cấp 2 (không có dòng) rồi rơi NULL. Có đủ 40/40 nhánh cấp 3 thì cây ICB kín, không nút lá nào thủng.

### Ba nhóm ICB không với tới — vì sao lớp 2 là bắt buộc

*(đo 2026-08-27)*

| Nhóm | Vì sao | Số mã |
|---|---|---|
| **KHUCONGNGHIEP** | ICB không tách khu công nghiệp khỏi BĐS dân dụng — không nút nào với tới | 34 |
| **NONGNGHIEP** | Nhánh `3573` gộp nuôi trồng với thủy sản; đã đảo lớp 1 sang THUYSAN (đa số 29/45) nên nông nghiệp phải bóc tay | 29 |
| **CAOSU** | Cao su thiên nhiên nằm ở `1353` cùng nhựa; lớp 1 chỉ với tới `3357` Săm lốp (4 mã) | 11 |

⚠️ Bản trước ghi *"bốn ca đã biết là gán lệch"* — **thiếu**. Thực tế là ba nhóm, ~66 doanh nghiệp. Còn bốn ca cũ ở [industry-tree §5](../../20-design/industry-tree.md) thì đối chiếu lại với ICB thật cho kết quả khác:

| Ca cũ | Đối chiếu 2026-08-27 |
|---|---|
| Gỗ TTF/ACG/SAV/GDT | **Lớp 1 tự giải** — ICB `1733` → DETMAY, GDT ở `3726` → DETMAY |
| VEF | **Lớp 1 tự giải** — ICB xếp `8633` → DANDUNG, không phải DULICH |
| IPA | **Cần lớp 2** — ICB xếp `2791` → XAYDUNG; đè sang DANDUNG *(luật BCTC chặn đường vào CHUNGKHOAN)* |
| TRC/DRI | 🔴 **Tiền đề sai.** §5 giả định CAOSU có 5 mã (2 thiên nhiên, 3 săm lốp). Đo thật **11 thiên nhiên vs 4 săm lốp** — thiên nhiên áp đảo, chỉ số bám giá cao su chứ không tự triệt tiêu. Không dời sang NONGNGHIEP; riêng DPR/GVR/PHR sang KHUCONGNGHIEP |

### Đã chốt hết 2026-08-27

Bốn chỗ từng để ngỏ nay đã quyết: `5557` sách & ấn bản → **YTE** *(không tách ngành thứ 25)* · `3353` ô tô → **BANLE** *(TMT và VMA đè sang THIETBI, DAS sang DAUKHI)* · `VGC` → **KHUCONGNGHIEP** · `ASM` → **THUYSAN** *(nay là mặc định của lớp 1 sau khi đảo `3573`)*.

Hai chỗ chốt sớm hơn trong ngày: `7573` xăng dầu & khí đốt → **DAUKHI** · `2799` môi trường đô thị → **TIENICH**.

Toàn bộ 295 quyết định, kèm lý do từng mã và dấu *độ tin cậy thấp* ở chỗ suy đoán: [sổ rà lớp 2](../plans/2026-08-27-industry-two-layer-mapping/layer2-review.md).

### Độ phủ *(đo 2026-08-27)*

**1.525/1.525 cổ phiếu có issuer đều có ngành**, cả 24 ngành đều có mã. Hai khoản ngoài tầm với — **là độ phủ thật của nguồn, không phải lỗi**:

- **24 chứng chỉ quỹ/ETF** (ICB `8980`) — không nạp, ETF và quỹ không có ngành.
- **437 cổ phiếu không có issuer** *(UPCOM 377 · HNX 39 · HOSE 21 — đo 2026-08-27)* — **để trống ngành theo luật**. Ngành gán ở doanh nghiệp, không có issuer thì không có chỗ gắn, ở cả hai lớp. *(Bản trước ghi "437 mã không có `icb_code`" là **sai** — trong 1.526 mã có issuer, **0 mã** thiếu ICB. Chi tiết: [spec §7b](../plans/2026-08-27-industry-two-layer-mapping/spec.md).)*

### Nạp thế nào

Nạp từ [`20-design/industry-mapping.json`](../../20-design/industry-mapping.json), **không phải từ file Excel này** — qua **migration seed `0013`** (đã chạy trên DB thật 2026-08-28), giống `0003_seed_industry`. Cả `industry_icb_map` lẫn `issuer_industry_override` **không có đường ghi runtime** nên seed ở migration là đúng chỗ *(khác `market.security`, nơi ETL ghi hằng ngày — một bảng một người ghi)*. Nghiệm thu trên DB thật: [ledger](../plans/2026-08-27-industry-two-layer-mapping/ledger.md).

---

## `all-securities.xlsx` — toàn bộ 2.015 mã trong kho

Tra cứu, không phải để điền. Sheet `Toàn bộ mã`, có auto-filter. Xuất 2026-08-26 sau lượt refdata đầu tiên. Đây cũng là **nguồn dựng `industry-mapping.xlsx`**.

| Cột | Ghi chú |
|---|---|
| `Mã` · `Sàn` · `Loại` · `Trạng thái` | `Loại`: `stock` 1.963 · `etf` 31 · `index` 18 · `fund_cert` 3 |
| `Tên doanh nghiệp` · `Loại hình` | rỗng khi mã **không có issuer** |
| `ICB L4` · `Tên ICB L4` · `ICB L3` | rỗng cùng lý do; lưu dạng văn bản |

---

## Vì sao `.xlsx` chứ không phải `.csv`

*(Ghi 2026-08-27 sau khi bản CSV hỏng trên máy chủ dự án — bản CSV đã xoá hẳn để không ai mở nhầm.)*

| Lỗi của bản CSV | Hậu quả |
|---|---|
| UTF-8 **không BOM** | Excel trên Windows đọc theo codepage hệ thống ⇒ **vỡ hết dấu tiếng Việt** |
| Excel hỏi *"Remove leading zeros"* | Bấm Convert là **ăn mất số 0 đầu** của mã ICB (`0533`) và `organ_code` (`0106839469`) — **hỏng dữ liệu thật**, không chỉ hiển thị |

`.xlsx` chặn cả hai bằng cấu tạo: encoding nằm trong định dạng, và mọi cột mã khai `number_format='@'` (văn bản) nên Excel không đụng vào. Thêm dropdown để mã ngành không thể gõ sai.
