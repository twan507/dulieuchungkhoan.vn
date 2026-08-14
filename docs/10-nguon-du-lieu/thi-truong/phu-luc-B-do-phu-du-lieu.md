# Phụ lục B — Kết quả kiểm thử độ phủ dữ liệu

**Ngày kiểm thử:** 2026-08-10 · **Khối lượng:** ~1.600 lời gọi · **Mẫu:** 51 mã cổ phiếu

---

## B.1 Phương pháp

### Bộ mã mẫu

51 mã cổ phiếu đang niêm yết, chọn để phủ đủ các chiều rủi ro:

| Chiều | Phân bố |
|---|---|
| Sàn | HOSE 22 · HNX 10 · UPCOM 19 |
| Loại hình (`comTypeCode`) | CT 41 · CK 5 · NH 3 · BH 2 |
| `organCode ≠ ticker` | 22 mã |
| `organCode` là mã số thuế | 3 mã (`TAH`, `TAB`, `BVL`) |

Bao gồm bắt buộc các mã blue-chip: `BID` `FPT` `VNM` `HPG` `SSI` `SHS` `VGI` `ACV`.

### Tiêu chí đánh giá

Một endpoint được coi là **có dữ liệu** cho một mã khi: `HTTP 200`, `status ∈ {0, "Success"}`, và `items` không rỗng, không `null`, không phải mảng chứa object toàn `null`.

---

## B.2 Kết quả tổng hợp

**Không endpoint nào trong phạm vi bị chết.** 100% trả `HTTP 200`, không timeout, không lỗi mạng.

### Nhóm phủ 100% (33 endpoint)

Toàn bộ REST BVSC *(trừ `translogsnaps`)* · toàn bộ tvcharts · 11/12 endpoint Fundamental · `GetPriceData` · `MoneyFlow` ×3 · `Calendar` ×8 · `Master` ×2 · `Screener` · `MarketInDepth` ×2.

### Nhóm hụt độ phủ

| Endpoint | Có dữ liệu | Tỷ lệ | Nhóm thiếu |
|---|---|---|---|
| `Rankings/GetRateIndicator` | 42/51 | **82%** | 8 mã UPCOM + `VMD` |
| `BVSC /datafeed/translogsnaps` | 34/51 | **67%** | 12/17 rỗng là UPCOM |
| `Rankings/GetAllScore` | 50/51 | 98% | 1 mã |
| `FinancialStatement/GetFinancialReports` | 50/51 | 98% | `TAH` |

### Nhóm trả 200 nhưng trường bên trong rỗng

| Endpoint / Trường | Có giá trị | Tỷ lệ |
|---|---|---|
| `Valuation` — `riskFreeRate`, `recommendMethod` | 51/51 | 100% |
| `Valuation` — `estimatedEPS`, `estimatedBookValue` | 41/51 | 80% |
| `Valuation` — `forecastEPS` | 35/51 | 69% |
| `Valuation` — **`forcastBookValue`** | **34/51** | **67%** |
| `GetPriceData` — nhóm dòng tiền theo NĐT | chỉ HOSE | — |

---

## B.3 Quy luật thiếu dữ liệu

Toàn bộ trường hợp thiếu dữ liệu tập trung ở **cổ phiếu nhỏ sàn UPCOM, `comTypeCode = CT`**. Không có tương quan nào với ngân hàng, chứng khoán hay bảo hiểm; không có tương quan với `icbCode`.

### Các mã có vấn đề trong bộ mẫu

| Mã | organCode | Sàn | Vấn đề |
|---|---|---|---|
| **TAH** | `3801140300` | UPCOM | Nặng nhất: `Snapshot.quarterly` và `.yearly` đều `null` · 0 file PDF · `GetPriceData` chỉ 14 phiên · không có `GetRateIndicator` |
| **THU** | — | UPCOM | 0 kỳ quý ở cả ba báo cáo tài chính (vẫn có 12 kỳ năm) · 9 PDF · không có `GetRateIndicator` |
| **RAT** | — | UPCOM | 0 kỳ quý (có 16 kỳ năm) · 19 PDF · không có `GetRateIndicator` |
| **VCT** | — | UPCOM | Chỉ 1–2 kỳ quý (có 18 kỳ năm) · 23 PDF · không có `GetRateIndicator` · 0 sự kiện chart |
| **TAB** | `0107005554` | UPCOM | Chỉ 3 PDF · không có `GetRateIndicator` |
| **BVL** | `10708` | UPCOM | Không có `GetRateIndicator` |
| NAC, HD8 | — | UPCOM | Không có `GetRateIndicator` |
| VMD | — | HOSE | Không có `GetRateIndicator` |

### Hệ quả thiết kế

Giao diện **phải** xử lý được các tình huống:
1. Điểm tổng VGM có, nhưng bung chi tiết 32 chỉ tiêu thì trống
2. Tab "Theo năm" có dữ liệu, tab "Theo quý" hoàn toàn trống
3. Có P/E và P/B, nhưng không có giá mục tiêu vì thiếu EPS/BV dự phóng
4. Bảng "Lệnh khớp" trống vì mã không phát sinh giao dịch trong phiên
5. Dòng tiền theo nhóm nhà đầu tư chỉ có với mã HOSE

Không được giả định dữ liệu luôn tồn tại.

---

## B.4 Độ phủ theo sàn — chi tiết endpoint quan trọng

### `Rankings/GetRateIndicator`

| Sàn | Có dữ liệu | Thiếu |
|---|---|---|
| HOSE | 21/22 (95%) | `VMD` |
| HNX | 10/10 (100%) | — |
| **UPCOM** | **11/19 (58%)** | `THU` `VCT` `RAT` `NAC` `HD8` `TAH` `BVL` `TAB` |

### `GetPriceData` — nhóm trường dòng tiền theo nhà đầu tư

Kiểm 12 trường đại diện (`localIndividual*`, `localInstitutional*`, `proprietary*`, `foreignIndividual*`, `foreignInstitutional*`, `netProprietary*`, `netInstitution*`, `totalDeal*`, `averageValue`):

| Mã | Sàn | Số trường có giá trị |
|---|---|---|
| BID | HOSE | 9/12 |
| FPT | HOSE | 9/12 |
| PVS | HNX | 3/12 |
| SHS | HNX | 1/12 |
| VGI (`VTGI`) | UPCOM | 2/12 |
| ACV (`ACVN`) | UPCOM | 1/12 |

**Kết luận: chỉ HOSE có dữ liệu phân rã theo nhóm nhà đầu tư.**

### `BVSC /datafeed/translogsnaps`

| Sàn | Có dữ liệu | Tỷ lệ |
|---|---|---|
| HOSE | 20/22 | 90,9% |
| HNX | 7/10 | 70,0% |
| UPCOM | 7/19 | 36,8% |

Mã rỗng: `VMD` `TPC` (HOSE) · `ATS` `ARM` `MED` (HNX) · `DM7` `VHF` `THU` `VCT` `RAT` `DWS` `NOS` `AIC` `NAC` `HD8` `BVL` `TAB` (UPCOM).

Nguyên nhân nhiều khả năng là mã không phát sinh lệnh khớp trong phiên, không phải giới hạn API.

---

## B.5 Xác minh bẫy `organCode`

Kiểm tra 22 mã có `organCode ≠ ticker`, gọi `PriceData/GetPriceData` và `TradingView/GetStockChartData` hai lần — một lần bằng `ticker`, một lần bằng `organCode`.

**Kết quả: 22/22 mã, không ngoại lệ.**

| | Dùng `ticker` | Dùng `organCode` |
|---|---|---|
| HTTP | 200 | 200 |
| `items` | rỗng / `null` | đầy đủ |
| Thông báo lỗi | **không có** | — |

Ví dụ cụ thể:

| Ticker | organCode | `GetPriceData` bằng ticker | bằng organCode |
|---|---|---|---|
| `VHM` | `NHN` | 119 byte, 0 phiên | 204.195 byte, 60 phiên |
| `STK` | `CENTURY` | 0 phiên | 60 phiên · 254 nến |
| `TAH` | `3801140300` | 0 phiên | 14 phiên |

---

## B.6 Ổn định dữ liệu

Nhóm `Calendar/GetCorporate*` gọi lặp hai lần liên tiếp cho kết quả **byte-identical**. Dữ liệu ổn định, cache được an toàn.

Các endpoint có dữ liệu trong phiên (`translogsnaps`, `chartinday`, `GetLiquiditySeries`, `GetComGroupBuSdChart`, `MoneyFlow/*`) thay đổi liên tục trong giờ giao dịch — chỉ cache ngắn hạn.

---

## B.7 Ghi chú về thời điểm kiểm thử

Một phần kiểm thử chạy **ngoài giờ giao dịch**, khiến các endpoint phụ thuộc phiên trả rỗng. Đã kiểm lại toàn bộ **trong phiên** (09:00–11:30 ngày 10/08/2026) và xác nhận:

| Endpoint | Ngoài phiên | Trong phiên |
|---|---|---|
| `/datafeed/translogsnaps/BID` | rỗng | 47 KB · 100 bản ghi |
| `/datafeed/chartinday/HOSE` | mảng rỗng | 19 KB · 126 điểm/phút |
| `/datafeed/indexs/getTime` | rỗng | **vẫn rỗng** → xác nhận endpoint chết |

Chỉ `/datafeed/indexs/getTime` là chết thật; các endpoint khác chỉ rỗng do ngoài giờ.
