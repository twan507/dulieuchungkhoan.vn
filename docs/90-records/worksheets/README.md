# Worksheet — bảng điền tay của chủ dự án

Nơi để những bảng **cần người quyết nội dung**, xuất từ dữ liệu thật để điền rồi nạp lại. Không phải tài liệu sống, không phải bản ghi lịch sử — là **đầu vào công việc**.

## `industry-map-worksheet.csv` — điền để lấp `market.industry_icb_map`

**37 dòng.** Mỗi dòng là một nhánh ICB cấp 3; điền cột cuối `nganh_cua_toi` bằng **mã ngành** trong bảng dưới. 37 dòng này phủ **100% của 1.550 doanh nghiệp** — không doanh nghiệp nào thiếu `icb_code` *(đo 2026-08-26)*.

| Cột | Nghĩa |
|---|---|
| `icb_l3` | mã ICB cấp 3 — khoá để nạp vào `industry_icb_map` |
| `ten_icb_l3` · `nhom_icb_l2` | tên ngành ICB cấp 3 và nhóm cha cấp 2, để nhận diện |
| `so_dn` | số doanh nghiệp rơi vào nhánh này — xếp giảm dần, dòng đầu nặng nhất |
| `mot_so_ma` | tối đa 12 mã đang niêm yết làm mẫu nhận diện *(không phải danh sách đầy đủ — xem `all-securities.csv`)* |
| **`nganh_cua_toi`** | **cột để điền** — một mã trong 24 mã dưới |

### 24 mã ngành hợp lệ

| Mã | Tên | Mã | Tên |
|---|---|---|---|
| `NGANHANG` | Ngân hàng và Tín dụng | `CHUNGKHOAN` | Công ty Chứng khoán |
| `BAOHIEM` | Kinh doanh Bảo hiểm | `BDS` | Bất động sản Dân dụng |
| `KCN` | Bất động sản Khu công nghiệp | `XAYDUNG` | Thi công Xây dựng |
| `VLXD` | Vật liệu Xây dựng | `THIETBI` | Thiết bị Điện và Máy móc |
| `KIMLOAI` | Kim loại Công nghiệp | `HOACHAT` | Hóa chất và Phân bón |
| `NHUA` | Nhựa và Bao bì | `CAOSU` | Cao su và Săm lốp |
| `DAUKHI` | Dầu khí và Nhiên liệu | `DIENNUOC` | Điện, Nước và Khí đốt |
| `TAINGUYEN` | Tài nguyên Cơ bản | `NONGNGHIEP` | Nông nghiệp và Chăn nuôi |
| `THUYSAN` | Chế biến Thủy sản | `THUCPHAM` | Thực phẩm và Đồ uống |
| `DETMAY` | Dệt may và Gia dụng | `BANLE` | Bán buôn và Bán lẻ |
| `VANTAI` | Vận tải, Cảng biển và Kho bãi | `DULICH` | Hàng không, Du lịch và Giải trí |
| `CONGNGHE` | Công nghệ Thông tin và Viễn thông | `YTEGD` | Dược phẩm, Y tế và Giáo dục |

### Bốn ca đã biết là gán lệch — xử luôn lúc điền

Ghi sẵn ở [industry-tree §5](../../20-design/industry-tree.md). Chúng **không sửa được bằng bảng ICB này** (một nhánh ICB chỉ map về một ngành), phải gán tay từng doanh nghiệp sau khi nạp — nhưng biết trước lúc điền thì đỡ phải nghĩ lại:

| Mã | Đang ở | Vấn đề |
|---|---|---|
| `TRC` · `DRI` | CAOSU | Cao su thiên nhiên **ngược chiều giá cao su** với nhóm săm lốp cùng ngành — chỉ số dòng tiền ngành tự triệt tiêu |
| `TTF` · `ACG` · `GDT` · `SAV` | BANLE | Gỗ nội thất **xuất khẩu** — hồ sơ rủi ro giống hàng xuất khẩu (đơn hàng Mỹ, tỷ giá) hơn bán lẻ nội địa |
| `IPA` | DIENNUOC | Thực chất holding tài chính (công ty mẹ của VND) |
| `VEF` | DULICH | Thực chất bất động sản dự án |

### Nạp lại thế nào

Điền xong đưa lại file — sẽ nạp qua **migration seed**, giống `0003_seed_industry`. `market.industry_icb_map` **không có đường ghi runtime**, nên seed ở migration là đúng chỗ *(khác `market.security`, nơi ETL ghi hằng ngày)*.

Sau khi nạp, `issuer.industry_id` gán theo map, rồi **gán tay đè lên** cho bốn ca trên — ETL hằng ngày **không bao giờ ghi đè** cột đó *(luật tay-thắng-máy, đã khoá bằng test)*.

---

## `all-securities.csv` — toàn bộ 2.015 mã đang có trong kho

Tra cứu, không phải để điền. Xuất 2026-08-26 sau lượt refdata đầu tiên.

| Cột | Ghi chú |
|---|---|
| `ticker` · `exchange` · `security_type` · `status` | `security_type`: `stock` 1.963 · `etf` 31 · `index` 18 · `fund_cert` 3 |
| `ten_doanh_nghiep` · `loai_hinh` | rỗng khi mã **không có issuer** — 437 cổ phiếu (chủ yếu UPCOM) không có bản ghi ở danh bạ FiinTrade, cùng toàn bộ ETF và chỉ số |
| `icb_l4` · `ten_icb_l4` · `icb_l3` | rỗng cùng lý do trên |

⚠️ **437 cổ phiếu không có `icb_code`** nên bảng map không với tới được. Chúng sẽ có `industry_id` rỗng cho tới khi gán tay hoặc tìm được nguồn ngành khác — không phải lỗi, là độ phủ thật của nguồn.
