# Lượt đo nguồn lịch sự kiện — 2026-09-03

Đo trước khi viết spec lát 2, theo [CLAUDE.md §4.8 bước 0](../../../../CLAUDE.md): tách dữ kiện đã kiểm khỏi giả định, vì năm quyết định thiết kế của lát này đều treo lên hành vi thật của nguồn.

**Cách đo:** 46 lời gọi `GET` tuần tự tới `https://wlgw-market.fiintrade.vn/Calendar`, header `Origin: https://fiinapp.bvsc.com.vn`, không ghi kho. Bản tải đầy đủ sáu họ (35 MB) **không commit** — bằng chứng rút gọn nằm ở [`samples/`](samples/).

| File bằng chứng | Nội dung |
|---|---|
| [`shape-20260903.json`](samples/shape-20260903.json) | Danh sách trường thật + 3 bản ghi đầu mỗi họ |
| [`stage-values-20260903.json`](samples/stage-values-20260903.json) | Toàn bộ giá trị `stageName` / `issueMethodName` kèm tần suất |
| [`key-collisions-20260903.json`](samples/key-collisions-20260903.json) | 211 khoá tự nhiên bị đụng, đủ bản ghi từng nhóm |
| [`m2-fromdate-axis-20260903.json`](samples/m2-fromdate-axis-20260903.json) | Kết quả thô phép đo trục ngày, cửa sổ 2026-08-01..05 |

---

## 1. `PageSize` không có trần thực tế — tải trọn rẻ hơn phân trang

| Họ | `PageSize` | Bản ghi trả về | Giây | Byte |
|---|---|---|---|---|
| StockDividend | 20 · 100 · 500 · 1.000 · 3.000 | 20 · 100 · 500 · 1.000 · **2.100 (hết)** | 0,2–1,1 | |
| Earning | 20 | 20 | 5,7 | 6 KB |
| Earning | 1.000 | 1.000 | 9,0 | 314 KB |
| Earning | 10.000 | 10.000 | 31,4 | 3,1 MB |
| Earning | 20.000 × 3 trang | 57.026 | 109 | 18,5 MB |

Nguồn trả `min(PageSize, số còn lại)`, không cắt, không lỗi. **Tải trọn cả sáu họ = 7 lời gọi, ~140 giây, ~36 MB.**

Phân trang ổn định: 57.026 bản ghi qua 3 trang, **0 bản ghi trùng giữa các trang**.

## 2. 🔴 `FromDate`/`ToDate` lọc theo một trục ngày KHÁC NHAU ở mỗi họ

Phép kiểm: tải trọn họ, rồi so **tập bản ghi** API trả về cho một cửa sổ với tập suy từ từng trường ngày. Trục thật phải cho **tập bằng nhau**, không phải "nằm trong".

| Họ | Trục lọc thật | Bằng chứng |
|---|---|---|
| `CashDividend` | **`payoutDate`** | 3 cửa sổ, 25/25 bản ghi; `publicDate` 0/25 |
| `StockDividend` | **`payoutDate`** | cửa sổ 2026-05-25..29 tách được: chỉ `payoutDate` cho tập bằng nhau (7/7) |
| `ShareIssuance` | **`issueDate`** | 2 cửa sổ, 10/10; `exrightDate` chỉ 6/10 |
| `AGM` | **`publicDate`** | 219/219 trong cửa sổ 2026-03-10..14 |
| `IPO` | `publicDate` | mẫu 1 bản ghi — **chưa đủ để khẳng định** |
| `Earning` | **không phải trường nào có trong response** | xem dưới |

**Trục sắp xếp lại là trục khác nữa.** 100 bản ghi đầu của AGM · CashDividend · StockDividend · ShareIssuance sắp giảm dần theo **`exrightDate`** — không theo trục lọc, không theo `publicDate`. IPO sắp theo `publicDate` giảm dần. Earning không sắp theo trường nào.

### 2.1 🔴 Earning: cửa sổ `FromDate` bỏ sót phần lớn dữ liệu

| Cửa sổ | API trả | Số bản ghi thật có `publicDate` trong cửa sổ | Giao | API trả mà ngoài cửa sổ | **Trong cửa sổ mà API KHÔNG trả** |
|---|---|---|---|---|---|
| 2026-03-10..14 | 24 | 217 | 22 | 2 | **195** |
| 2025-11-03..07 | 83 | 80 | 75 | 8 | 5 |
| 2026-08-01..05 | 135 | 116 | 100 | 35 | 16 |

Hai tập **cắt nhau**, không tập nào chứa tập nào ⇒ trục lọc là một trường không có trong response (nhiều khả năng là ngày dự kiến công bố hoặc dấu thời gian cập nhật bản ghi).

**Hệ quả thiết kế:** job hằng ngày dùng `FromDate` cho họ Earning sẽ **mất im lặng tới 90% bản ghi** của cửa sổ đó. Mà tải trọn Earning chỉ tốn 3 lời gọi.

## 3. `stage_key` — lấy từ đâu

| Họ | Trường | Số giá trị khác nhau | Null | Giá trị nhiều nhất |
|---|---|---|---|---|
| CashDividend | `stageName` | 26 | 0 | `Cả năm` 8.577 · `Đợt 1` 4.899 · `Đợt 2` 3.712 |
| StockDividend | `stageName` | 7 | 0 | `Cả năm` 1.960 · `Đợt 2` 70 · `Đợt 1` 53 |
| ShareIssuance | `issueMethodName` | 10 | 0 | `Phát hành riêng lẻ` 2.575 · `Trả Cổ tức bằng Cổ phiếu` 2.414 |
| AGM | `eventTitle` | — | **23.467/23.467 null** | ⇒ **không dùng được** |

`issueMethodName` là trường có giá trị nhất: thiếu nó, ShareIssuance đụng **1.265** khoá; có nó, còn **129**.

## 4. 🔴 Khoá tự nhiên 7 cột của migration `0004` KHÔNG đủ phân biệt

Khoá: `(event_type, issuer_id, public_date, exright_date, year_report, length_report, stage_key)` — với `stage_key` lấy theo mục 3.

| Họ | Bản ghi | Khoá bị đụng | Trong đó **khác nội dung** (sẽ bị đè mất) |
|---|---|---|---|
| Earning | 57.026 | **0** | 0 |
| IPO | 77 | **0** | 0 |
| AGM | 23.467 | 16 | 16 |
| CashDividend | 17.970 | 47 | 45 |
| StockDividend | 2.100 | 19 | 17 |
| ShareIssuance | 10.097 | 129 | 115 |

**211 khoá đụng, 193 khác nội dung.** Nạp nguyên trạng thì 193 bản ghi biến mất im lặng.

### 4.1 Thêm trường nào thì hết đụng

| Họ | Trường gỡ được nhiều nhất | Còn lại |
|---|---|---|
| CashDividend | **`dividendYear`** | 47 → **4** |
| StockDividend | **`dividendYear`** | 19 → **3** |
| ShareIssuance | **`planVolumn`** | 129 → **27** |
| AGM | **`issueDate`** *(ngày tổ chức đại hội)* | 16 → **4** |

Ví dụ điển hình — SD9 công bố cùng ngày 2026-03-17, cùng `exrightDate`, cùng `stageName = "Cả năm"`, khác **`dividendYear` 2019 vs 2021**: hai kỳ cổ tức trả bù cùng lúc. Không có `dividendYear` trong khoá thì mất một kỳ.

Phần đụng còn lại chủ yếu là **nguồn tự đẻ bản ghi trùng**: ShareIssuance 14 khoá trùng nguyên văn; và cặp NVL/ABI khác nhau đúng ở `listingDate` (`null` vs đã điền) — cùng một đợt phát hành, bản cũ chưa được xoá khi bản mới có ngày niêm yết.

## 5. Bản ghi trùng nguyên văn do chính nguồn đẻ ra

| Họ | Bản ghi | Trùng nguyên văn |
|---|---|---|
| ShareIssuance | 10.097 | **14** |
| CashDividend | 17.970 | 2 |
| StockDividend | 2.100 | 2 |
| AGM · IPO · Earning | | 0 |

## 6. `totalCount` trôi theo thời gian — kể cả trôi XUỐNG

| Họ | Tài liệu *(đo ~2026-08-10)* | Đo 2026-09-03 | Chênh |
|---|---|---|---|
| AGM | 23.434 | 23.467 | +33 |
| CashDividend | 17.884 | 17.970 | +86 |
| StockDividend | 2.086 | 2.100 | +14 |
| ShareIssuance | 10.052 | 10.097 | +45 |
| IPO | 77 | 77 | 0 |
| **Earning** | **57.176** | **57.026** | **−150** |

Earning **mất 150 bản ghi** trong 24 ngày. Chốt chặn kiểu "tổng số sụt quá X% thì từ chối" vẫn dùng được (150/57.176 = 0,26%), nhưng **không được giả định tổng số chỉ tăng**.

---

## Còn chưa đo

| Việc | Vì sao chưa | Chặn cái gì |
|---|---|---|
| Tỷ lệ `organCode` ghép được vào `market.issuer_external_id` | Danh bạ đang đứng ở trạng thái 31/08 — `etl refdata` báo đỏ từ 01/09, lượt dọn tay `--accept-drop` chưa chạy | Ngưỡng guard `unmapped` |
| Trục lọc của `IPO` | Cả kho chỉ 77 bản ghi, cửa sổ thử chỉ trúng 1 | Không chặn — tải trọn 1 lời gọi thì trục lọc thành vô nghĩa |
| `GetCalendarWatchList` (190.143 bản ghi) và `GetEconomy` | Ngoài phạm vi sáu họ `GetCorporate*` đã chốt | Không chặn |
