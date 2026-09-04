# 04 — Hồ sơ doanh nghiệp FiinTrade

Base URL: `https://wlgw-fundamental.fiintrade.vn` — ký hiệu `FIIN_FUND`
Header bắt buộc: `Origin: https://fiinapp.bvsc.com.vn`

5 endpoint. Tất cả nhận **`organCode`**, không nhận ticker (trừ `getCashDividendAnalysis` nhận cả hai).

---

## `getSnapshot` / `getSnapshotNoneBank`

**Tóm tắt:** Ảnh chụp tổng hợp doanh nghiệp — chỉ số thị trường, cơ cấu sở hữu, và chuỗi tài chính theo quý/năm.

**Mô tả:** Hai endpoint **cấu trúc giống hệt nhau**, khác nhau ở bộ chỉ tiêu tài chính phù hợp với loại hình doanh nghiệp. Đây là nguồn dữ liệu cho toàn bộ phần "Tình hình chung" của màn hình phân tích cơ bản.

```
GET FIIN_FUND/Snapshot/GetSnapshot?OrganCode={organCode}&language=vi
GET FIIN_FUND/Snapshot/GetSnapshotNoneBank?OrganCode={organCode}&language=vi
```

### 🔴 Hai endpoint trả `status` KHÁC NHAU

*(đo 2026-09-04, 9 mã)* `GetSnapshot` trả `"status": 0`, `GetSnapshotNoneBank` trả `"status": "Success"` — **cùng một họ, cùng một lượt gọi**. Kiểm `status == "Success"` sẽ từ chối sạch nhánh ngân hàng. Dùng công thức ở [quy ước §6.1](00-conventions.md).

### 🔴 Chọn endpoint nào

Cả hai đều trả `HTTP 200` cho mọi mã. Chọn sai **không báo lỗi** mà làm gần một nửa số trường thành `null`.

| `comTypeCode` | Dùng | Tỷ lệ null nếu chọn đúng | Tỷ lệ null nếu chọn sai |
|---|---|---|---|
| `NH` — Ngân hàng | **`GetSnapshot`** | 25,9% | 46,4% |
| `CT` — Công ty thường | **`GetSnapshotNoneBank`** | 12,1% | 36,3% |
| `CK` — Chứng khoán | **`GetSnapshotNoneBank`** | 24,3% | 29,6% |
| `BH` — Bảo hiểm | **`GetSnapshotNoneBank`** | 14,3% | 29,6% |

Lấy `comTypeCode` từ [`getListOrganization`](03-fiin-reference.md).

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `OrganCode` | query | string | **bắt buộc** | Mã nội bộ FiinTrade, **không phải ticker** |
| `language` | query | string | *tuỳ chọn* | `vi` \| `en` |

### Response 200

```json
{
  "totalCount": 1,
  "items": [{
    "summary": { ... 28 trường ... },
    "quarterly": [ ... ],
    "yearly": [ ... ]
  }],
  "status": 0
}
```

#### `summary` — 28 trường

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `organCode` | string | — | Mã doanh nghiệp |
| `comTypeCode` | string | — | Loại hình |
| `rtd11` | number | VND | Vốn hoá thị trường |
| `rtd14` | number | VND | EPS |
| `rtd21` | number | lần | P/E |
| `rtd25` | number | lần | P/B |
| `rtd53` | number | — | *(chưa xác định)* |
| `rtq10` `rtq12` `rtq14` `rtq29` | number | — | Nhóm chỉ số TTM — `rtq12` = ROE, `rtq14` = ROA. Xem [Phụ lục A](appendix-A-field-codes.md) |
| `averageMatchVolume1Month` | number | cổ phiếu | KLGD bình quân 1 tháng |
| `valuePerShare` | number | VND | Mệnh giá |
| `outstandingShare` | number | cổ phiếu | Số CP đang lưu hành |
| `freeFloat` | number | cổ phiếu | Khối lượng tự do chuyển nhượng |
| `freeFloatRate` | number | thập phân | Tỷ lệ free float |
| `statePercentage` | number | thập phân | Tỷ lệ sở hữu nhà nước |
| `stateVolumn` | number | cổ phiếu | Khối lượng nhà nước nắm |
| `foreignerPercentage` | number | thập phân | Tỷ lệ sở hữu nước ngoài |
| `foreignerVolumn` | number | cổ phiếu | Khối lượng nước ngoài nắm |
| `foreignerRoom` | number | cổ phiếu | Room còn lại |
| `totalForeignRoom` | number | cổ phiếu | Tổng room |
| `maximumForeignPercentage` | number | thập phân | Trần sở hữu nước ngoài |
| `lowestPrice1Year` / `highestPrice1Year` | number | VND | Thấp nhất / cao nhất 52 tuần |
| `ceo` | string | — | Tên tổng giám đốc |
| `competitors` | array | — | Danh sách mã cùng ngành để so sánh |
| `majorHoldings` | array | — | Các khoản đầu tư lớn |

#### `quarterly[]` / `yearly[]`

Chuỗi chỉ tiêu tài chính theo kỳ. Trường định danh kỳ: `year`, `quarter`.

Các trường còn lại là **mã chỉ tiêu FiinGroup**, ví dụ trong bản ngân hàng:

```
rtq44  rtq137  rtq25  rtq1  rtq2  rtq3  rtq29  rqq41
isa1   isa22   isb27  isi103
bsa53  bsb104  bsa1   bsa23  bsa54  bsa78  bsa80  bsb98  bsb113
nob44  cfa18
```

Tiền tố quyết định nhóm chỉ tiêu — xem [Phụ lục A](appendix-A-field-codes.md):

| Tiền tố | Nhóm |
|---|---|
| `rtd` | Chỉ số thị trường theo ngày (P/E, P/B, vốn hoá) |
| `rtq` | Chỉ số TTM (4 quý gần nhất) |
| `rqq` | Chỉ số theo quý |
| `ryq` | Chỉ số theo năm |
| `isa` `isb` `isi` | Báo cáo kết quả kinh doanh |
| `bsa` `bsb` | Bảng cân đối kế toán |
| `cfa` | Lưu chuyển tiền tệ |
| `nob` | Chỉ tiêu ngoài bảng |

Số kỳ trả về: quý trung bình 9–13 kỳ, năm 6 kỳ.

### Ghi chú
- Bộ chỉ tiêu trong `quarterly`/`yearly` **khác nhau giữa hai endpoint** — bản ngân hàng có chỉ tiêu NIM, nợ xấu, tín dụng, huy động; bản phi ngân hàng có doanh thu, biên lợi nhuận, hàng tồn kho. Giao diện phải render khác nhau theo loại hình.
- Toàn bộ 5 biểu đồ ở màn hình "Tình hình chung" (thu nhập lãi thuần, lãi thuần, tổng tài sản, tín dụng, huy động vốn) đều dựng từ **duy nhất** endpoint này — không có API riêng cho từng biểu đồ.

### Độ phủ & hiệu năng
51/51 mã mẫu · `GetSnapshot` 8,1 KB TB · `GetSnapshotNoneBank` 10,7 KB TB · ~640 ms.
Ngoại lệ: mã `TAH` có `summary` nhưng `quarterly` và `yearly` đều `null`.

---

## `getCompanyScore`

**Tóm tắt:** Xếp hạng và điểm tổng hợp VGM của doanh nghiệp.

**Mô tả:** Cung cấp thứ hạng trong ngành, thứ hạng trong rổ chỉ số, và bốn điểm đánh giá dạng chữ cái. Đây là dữ liệu cho khối "FiinTrade Xếp Hạng" ở đầu màn hình phân tích cơ bản.

```
GET FIIN_FUND/Snapshot/GetCompanyScore?OrganCode={organCode}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `OrganCode` | query | string | **bắt buộc** | |
| `language` | query | string | *tuỳ chọn* | `vi` \| `en` |

### Response 200

```json
{
  "items": [{
    "organCode": "BID",
    "icbRank": 4,
    "icbTotalRanked": 28,
    "indexRank": 6,
    "indexTotalRanked": 32,
    "icbCode": "8350",
    "comGroupCode": "VNINDEX",
    "growth": "C",
    "value": "F",
    "momentum": "C",
    "vgm": "C",
    "controlStatusCode": null,
    "controlStatusName": null
  }],
  "status": 0
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `icbRank` / `icbTotalRanked` | integer | Thứ hạng trong ngành / tổng số mã được xếp hạng. Hiển thị dạng `4/28 Ngân hàng` |
| `indexRank` / `indexTotalRanked` | integer | Thứ hạng trong rổ chỉ số. `6/32 VN30` |
| `icbCode` | string | Mã ngành |
| `comGroupCode` | string | Sàn |
| `value` | string | Điểm định giá — thang `A`..`F` |
| `growth` | string | Điểm tăng trưởng |
| `momentum` | string | Điểm động lực |
| `vgm` | string | Điểm tổng hợp Value + Growth + Momentum |
| `controlStatusCode` / `controlStatusName` | string \| null | Trạng thái kiểm soát (cảnh báo, kiểm soát…). `null` khi bình thường |

### Ghi chú
Bốn điểm chữ cái chỉ là kết quả tổng hợp. Muốn biết **vì sao** một mã bị điểm `F`, phải gọi [`getRateIndicator`](06-fiin-scoring-valuation.md) để bung ra 32 chỉ tiêu thành phần.

### Độ phủ & hiệu năng
51/51 mã mẫu · ~343 byte · ~436 ms.

---

## `getOwnership`

**Tóm tắt:** Cơ cấu sở hữu, cổ đông lớn và ban lãnh đạo.

```
GET FIIN_FUND/Ownership/GetOwnership?OrganCode={organCode}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc |
|---|---|---|---|
| `OrganCode` | query | string | **bắt buộc** |
| `language` | query | string | *tuỳ chọn* |

### Response 200

```json
{
  "items": [{
    "overviewChartData": [...],
    "majorOwnershipsChartData": [...],
    "majorShareHolders": [...],
    "boardOfDirectors": [...]
  }],
  "status": 0
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `overviewChartData` | array | Cơ cấu sở hữu tổng quan — dữ liệu biểu đồ tròn (nhà nước / nước ngoài / khác) |
| `majorOwnershipsChartData` | array | Tỷ trọng các cổ đông lớn — dữ liệu biểu đồ |
| `majorShareHolders` | array | Danh sách cổ đông lớn |
| `boardOfDirectors` | array | Danh sách thành viên HĐQT và ban điều hành |

### Ghi chú
Hai endpoint bổ trợ `Ownership/GetBoDTooltip` và `Ownership/GetShareHolderTooltip` **luôn trả rỗng** (99 byte, `items: []`) trên toàn bộ 51 mã kiểm thử — đã loại khỏi phạm vi. Thông tin chi tiết HĐQT và cổ đông đã nằm sẵn trong `boardOfDirectors` và `majorShareHolders` của endpoint này.

### Độ phủ & hiệu năng
51/51 mã mẫu · 4,8–34 KB *(phụ thuộc số cổ đông)* · TB 10,9 KB · ~500 ms.

---

## `getCashDividendAnalysis`

**Tóm tắt:** Lịch sử và kế hoạch cổ tức tiền mặt, kèm chỉ số liên quan.

```
GET FIIN_FUND/CashDividendAnalysis/GetAnalysis?OrganCode={organCode}&Code={ticker}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `OrganCode` | query | string | **bắt buộc** | Mã nội bộ FiinTrade |
| `Code` | query | string | **bắt buộc** | ⚠️ **Ticker**, không phải organCode. Endpoint duy nhất nhận cả hai |
| `language` | query | string | *tuỳ chọn* | |

### Response 200

```json
{
  "items": [{
    "organCode": "ASECO32",
    "priceEarningRatio":   { "ratioYears": [ {"yearReport": 2025, "ratioValue": 11.0488925}, … ] },
    "dividendYield":       { "ratioYears": [ … ] },
    "eps":                 { "ratioYears": [ … ] },
    "dps":                 { "ratioYears": [ … ] },
    "dividendPayoutRatio": { "ratioYears": [ … ] },
    "cashDividendPayouts": [ {"valuePerShare": 2200.0, "dividendYear": 2014,
                              "exrightYear": 2014, "exrightMonth": 12}, … ],
    "cashDividendPlans":   [ {"dividendYear": 2026, "valuePerShare": 2200.0}, … ]
  }],
  "status": "Success"
}
```

🔴 **Bản mẫu cũ ở đây SAI hình dạng** *(sửa 2026-09-04 sau khi gọi lại thật)*: năm chỉ tiêu đầu **không phải số**, mà là object `{"ratioYears": [{"yearReport", "ratioValue"}]}` — chuỗi **9 năm**. Kiểm trên chính mã ví dụ cũ (BID) và trên A32, cả hai cùng hình dạng. Cùng loại lỗi §3.4 của [CLAUDE.md](../../../CLAUDE.md): mẫu chép trong tài liệu là bản đã bóc vỏ, không phải frame thật.

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `priceEarningRatio` | object | lần | P/E theo năm — 🔴 **mục của NĂM HIỆN HÀNH tính theo GIÁ hôm nay, đổi mỗi ngày** |
| `dividendYield` | object | thập phân | Tỷ suất cổ tức theo năm — 🔴 **cũng theo giá, đổi mỗi ngày** |
| `eps` | object | VND | Lợi nhuận trên cổ phiếu theo năm |
| `dps` | object | VND | Cổ tức trên cổ phiếu theo năm |
| `dividendPayoutRatio` | object | thập phân | Tỷ lệ chi trả cổ tức theo năm |
| `cashDividendPayouts` | array | — | Lịch sử các đợt đã chi trả — `valuePerShare` · `dividendYear` · `exrightYear` · `exrightMonth` |
| `cashDividendPlans` | array | — | Kế hoạch cổ tức đã công bố — `dividendYear` · `valuePerShare` |

**Bằng chứng hai trường theo giá** *(đo 2026-09-04)*: A32 có `priceEarningRatio` năm 2025 = **11,0489**, `eps` = 2.606,60; giá đóng cửa 03/09 trong kho của dự án là **28.800** ⇒ 28.800 ÷ 2.606,60 = **11,0489**. Hệ quả cho ETL: hai trường này **không được vào phép so "nội dung có đổi không"**, nếu không thì ngày nào cũng báo đổi.

### Độ phủ & hiệu năng
51/51 mã mẫu · 598 byte – 8,1 KB · TB 4,3 KB · ~130 ms. *(Đo lại 2026-09-04 trên 9 mã khác: 748 byte – 4,6 KB, 19–231 ms — cùng bậc.)*
