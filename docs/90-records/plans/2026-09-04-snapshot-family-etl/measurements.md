# Số đo họ Snapshot — 2026-09-04

Lượt đo trước khi viết spec, theo bài học số 1 của lát 3 *(đo nguồn trước khi tin thiết kế)*.
**37 lời gọi** trên 9 mã × 4 endpoint, cộng **1 lời gọi** kiểm chứng riêng trên BID.
Tuần tự, giãn cách 0,5 s, ngoài giờ giao dịch. Bản thô: [`measurements-raw.json`](measurements-raw.json) · mẫu payload: [`samples/`](samples/).

## 1. Mẫu

| Ticker | organCode | comType | Ghi chú |
|---|---|---|---|
| BAB | `NASB` | NH | organCode ≠ ticker |
| BVB | `GDB` | NH | organCode ≠ ticker · lượt `valuation` hỏng |
| A32 | `ASECO32` | CT | mã dùng làm mẫu chuẩn trong spec |
| AAH | `2400379403` | CT | organCode là mã số thuế |
| AAN | `0109510866` | CT | organCode là mã số thuế |
| ABC | `VMGC` | CT | |
| AAS | `HAMIS` | CK | |
| ABW | `ABSC` | CK | |
| AIC | `VNAI` | BH | |

Truy vấn lấy mẫu ưu tiên `organ_code <> ticker` để bắt đúng nhóm 41% mà [bẫy 1](../../../10-sources/market/00-conventions.md) cảnh báo — **7/9 mã trong mẫu có organCode khác ticker**, gồm 2 mã là mã số thuế.
`com_type_code = 'QU'` (quỹ) không trả mã nào có `security_type='stock'` niêm yết ⇒ quỹ/ETF tự rơi khỏi phạm vi, không cần luật loại riêng.

## 2. Kết quả từng lời gọi

| Kind | HTTP | `status` | Kích thước | Thời gian |
|---|---|---|---|---|
| `snapshot` (`GetSnapshot`, NH) | 200, 2/2 | **`0`** | 8,8 KB | 416–695 ms |
| `snapshot` (`GetSnapshotNoneBank`, CT/CK/BH) | 200, 7/7 | `"Success"` | 4,2–12,4 KB | 25–371 ms |
| `ownership` | 200, 9/9 | `"Success"` | 4,5–19,6 KB | 23–722 ms |
| `dividend` | 200, 9/9 | `"Success"` | 0,7–4,6 KB | 19–231 ms |
| `valuation` | 200, 9/9 | `"Success"` 8/9 · **`"Failed"` 1/9** | 0,6–15,2 KB | 102 ms – 4,6 s · **12,3 s** cho lượt hỏng |

Tổng payload một mã trọn 4 kind: **≈ 25–40 KB**.

## 3. Ba điều lật lại giả định

### 3.1 `status` trong CÙNG một họ có ba giá trị

`GetSnapshot` trả `0`, `GetSnapshotNoneBank` trả `"Success"`, `GetValuation` của BVB trả `"Failed"`.
Kiểm `status == "Success"` — cách lát 1 và lát 2 đang viết — **từ chối sạch nhánh ngân hàng**.
Công thức đúng đã nằm ở [quy ước §6.1](../../../10-sources/market/00-conventions.md) từ 2026-08-15.

### 3.2 `"Failed"` là lỗi Redis phía nguồn, không phải "mã không có dữ liệu"

Nguyên văn `errors` của BVB *(mẫu: [`samples/BVB-valuation-failed.json`](samples/BVB-valuation-failed.json))*:

```
Timeout performing GET (5000ms), next: GET AllOrganizations, … serverEndpoint: …:6379,
mgr: 10 of 10 available, clientName: FIINTRADE-MICRO
```

Đúng chuỗi mà [quy ước §10.5](../../../10-sources/market/00-conventions.md) đã phân loại là **lỗi tạm thời** từ đợt đo 2026-08-15. Số mới: lượt hỏng tốn **12,3 giây**.

### 3.3 Trường phái sinh từ giá có mặt ở CẢ `snapshot` LẪN `dividend`

Đối chứng bằng nguồn độc lập — `market.price_daily` của lát 3, phiên **2026-09-03**, A32 `close_raw = 28.800`:

| Trường nguồn | Giá trị nguồn | Tính lại | Khớp |
|---|---|---|---|
| `snapshot.rtd11` (vốn hoá) ÷ `outstandingShare` | 195.840.000.000 ÷ 6.800.000 | **28.800** | = giá đóng cửa |
| `snapshot.rtd21` (P/E) | 3,84963858 | 28.800 ÷ `rtd14` 7.481,22 = **3,84964** | ✅ |
| `snapshot.rtd25` (P/B) | 0,84862988 | 28.800 ÷ `valuation.rtd7` 33.937,06 = **0,84863** | ✅ |
| `dividend.priceEarningRatio` năm 2025 | 11,0488925 | 28.800 ÷ `eps` 2.606,596 = **11,04889** | ✅ |

Bốn phép khớp tới 5–6 chữ số. Hệ quả: **phép so "nội dung có đổi không" không được trùm các trường này** — nếu trùm thì mọi lượt quét đều báo đổi và kiến trúc trigger mất nghĩa.

## 4. Hình dạng thật của bốn kind

Cả bốn cùng vỏ `{page, pageSize, totalCount, items, packageId, status, errors}`, bản ghi nằm ở `items[0]`.

| Kind | Khoá gốc trong `items[0]` |
|---|---|
| `snapshot` | `summary` (28 khoá) · `quarterly[]` · `yearly[]` — hai mảng sau mang mã BCTC (`bsa*` `isa*` `cfa*`); `quarterly` **rỗng ở A32** |
| `ownership` | `overviewChartData[]` `{item1, item2}` · `majorOwnershipsChartData[]` · `majorShareHolders[]` `{shareHolderName, shareHolderCode, shareHolderType, isFounder, quantity, percentage, …}` · `boardOfDirectors[]` `{personId, fullName, positionName, quantity, percentage, publicDate, …}` |
| `dividend` | `organCode` · 5 chỉ tiêu dạng `{ratioYears: [{yearReport, ratioValue}]}` **9 năm** · `cashDividendPayouts[]` `{valuePerShare, dividendYear, exrightYear, exrightMonth}` · `cashDividendPlans[]` `{dividendYear, valuePerShare}` |
| `valuation` | `valuationStock` (13 khoá) · `valuationSector` `{icbCode, valuationStocks[]}` — 46 mã cùng ngành ở A32 |

🔴 **Tài liệu nguồn [`04-fiin-company-profile.md`](../../../10-sources/market/04-fiin-company-profile.md) chép SAI hình dạng `dividend`** — bản cũ ghi 5 chỉ tiêu là số vô hướng (`"priceEarningRatio": 8.585`). Kiểm trên chính mã ví dụ của tài liệu (BID) và trên A32: cả hai đều là object `ratioYears`. **Đã sửa tầng reference cùng ngày** (commit `fad9b6b`), cùng loại lỗi §3.4 — mẫu trong tài liệu là bản đã bóc vỏ.

## 5. Số dùng cho spec

| Đại lượng | Giá trị | Từ đâu |
|---|---|---|
| Vũ trụ mã | **1.523** issuer niêm yết dạng stock | `security.status='listed' AND security_type='stock'`, lát 3 |
| Ngân sách quét sàn/ngày | ≈ **231** lời gọi | 1.523×3 kind ÷ 22 ngày + 1.523 ÷ 65 ngày |
| Thời gian ước tính một lượt | **4–8 phút** | 231 lời gọi × (0,5 s giãn + latency trung vị ~0,2 s), `valuation` là đuôi dài |
| Dung lượng lượt quét trọn đầu tiên | ≈ **61 MB** | 1.523 × 4 kind × ~10 KB |
| Timeout client `valuation` | **≥ 30 s** | lượt hỏng đo được 12,3 s |
