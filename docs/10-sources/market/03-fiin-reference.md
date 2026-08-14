# 03 — Dữ liệu tham chiếu FiinTrade

Base URL: `https://wlgw-core.fiintrade.vn` — ký hiệu `FIIN_CORE`
Header bắt buộc: `Origin: https://fiinapp.bvsc.com.vn`

2 endpoint. **Đây là nền tảng bắt buộc** — mọi lời gọi FiinTrade khác đều phụ thuộc vào bảng ánh xạ lấy từ đây.

---

## `getListOrganization`

**Tóm tắt:** Danh bạ toàn bộ doanh nghiệp niêm yết, kèm ánh xạ `ticker → organCode`.

**Mô tả:** Endpoint quan trọng nhất trong toàn bộ hệ thống FiinTrade. Nó cung cấp ba thứ mà không endpoint nào khác có:

1. **Ánh xạ `ticker → organCode`** — bắt buộc để gọi mọi API FiinTrade khác (xem [Bẫy 1](00-conventions.md))
2. **`comTypeCode`** — quyết định chọn `GetSnapshot` hay `GetSnapshotNoneBank` (xem [Bẫy 3](00-conventions.md))
3. **`icbCode`** — ngành của doanh nghiệp, ghép với [`getAllIcbIndustry`](#getallicbindustry)

Phải nạp một lần lúc khởi động ứng dụng và cache.

```
GET FIIN_CORE/Master/GetListOrganization?language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `language` | query | string | *tuỳ chọn* | `vi` \| `en`. Ảnh hưởng `organName`, `organShortName` |

### Response 200

```json
{
  "page": 1, "pageSize": 0, "totalCount": 1553,
  "items": [
    {
      "organCode": "0101264009",
      "ticker": "DDB",
      "comGroupCode": "UpcomIndex",
      "icbCode": "2353",
      "organTypeCode": "DN",
      "comTypeCode": "CT",
      "organName": "Công ty Cổ Phần Thương Mại Và Xây Dựng Đông Dương",
      "organShortName": "TM & XD Đông Dương"
    }
  ],
  "status": 0, "errors": null
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `organCode` | string | **Khoá định danh FiinTrade.** Dùng cho mọi endpoint khác |
| `ticker` | string | Mã chứng khoán trên sàn |
| `comGroupCode` | string | Sàn — xem bảng dưới. ⚠️ Khác quy ước `exchange` của BVSC |
| `icbCode` | string | Mã ngành ICB, 4 chữ số. 100% bản ghi đều có |
| `organTypeCode` | string | `DN` (1.522) \| `OTHER` (31) |
| `comTypeCode` | string | Loại hình — xem bảng dưới. **Quyết định chọn endpoint Snapshot** |
| `organName` | string | Tên đầy đủ |
| `organShortName` | string | Tên rút gọn, dùng hiển thị trong bảng |

**Bảng `comGroupCode`** — lưu ý khác với `exchange` của BVSC:

| FiinTrade | BVSC tương đương | Số DN |
|---|---|---|
| `VNINDEX` | `HOSE` | 429 |
| `HNXIndex` | `HNX` | 299 |
| `UpcomIndex` | `UPCOM` | 825 |

**Bảng `comTypeCode`:**

| Giá trị | Nghĩa | Số DN | Endpoint Snapshot |
|---|---|---|---|
| `CT` | Công ty thường | 1.444 | `GetSnapshotNoneBank` |
| `CK` | Công ty chứng khoán | 42 | `GetSnapshotNoneBank` |
| `NH` | Ngân hàng | 30 | **`GetSnapshot`** |
| `QU` | Quỹ đầu tư | 24 | `GetSnapshotNoneBank` |
| `BH` | Bảo hiểm | 13 | `GetSnapshotNoneBank` |

### Ghi chú & bẫy

⚠️ **647/1.553 bản ghi (41,7%) có `organCode ≠ ticker`.** Phân bố: UPCOM 449 · HOSE 135 · HNX 63. Trong đó **72 mã dùng mã số thuế** làm `organCode`.

Ví dụ cần lưu ý:

| Ticker | organCode | Ghi chú |
|---|---|---|
| `VHM` | `NHN` | Mã lớn VN30 |
| `ACV` | `ACVN` | |
| `VGI` | `VTGI` | |
| `MCH` | `MSCC` | |
| `BSR` | `BSRC` | |
| `STK` | `CENTURY` | |
| `TAH` | `3801140300` | Mã số thuế |
| `TAB` | `0107005554` | Mã số thuế |
| `BVL` | `10708` | Mã số thuế |

Không có quy luật nào để suy ra `organCode` từ `ticker` — bắt buộc tra bảng.

⚠️ Danh sách này gồm **cả mã đã huỷ niêm yết**. Muốn chỉ lấy mã đang giao dịch, lọc chéo với [`getAllQuotes`](01-bvsc-rest.md) của BVSC (**2.534** mã đang niêm yết, trong đó **1.974** cổ phiếu — đếm lại 2026-08-15; ngày 2026-08-10 là 2.530 / 1.972, tức con số này **đổi theo tuần**, phải lọc động chứ đừng hardcode).

### Độ phủ & hiệu năng
1.553 bản ghi · 51/51 mã mẫu có mặt · 355 KB · **~4,4 s** — endpoint chậm nhất nhóm tham chiếu. Nạp một lần lúc khởi động, cache dài hạn.

---

## `getAllIcbIndustry`

**Tóm tắt:** Cây phân ngành ICB bốn cấp.

**Mô tả:** Bảng phân ngành theo chuẩn ICB (Industry Classification Benchmark) mà FiinGroup áp dụng cho thị trường Việt Nam. BVSC không có nguồn phân ngành nào tương đương — `getAllQuotes` chỉ có `StockType`, không có ngành.

```
GET FIIN_CORE/Master/GetAllIcbIndustry?language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `language` | query | string | *tuỳ chọn* | `vi` \| `en`. Ảnh hưởng `icbName`, `friendlyName`, `icbNamePath` |

### Response 200

```json
{
  "totalCount": 176,
  "items": [
    {
      "icbCode": "8350",
      "icbName": "Ngân hàng",
      "parentIcbCode": "8300",
      "friendlyName": "Ngân hàng",
      "icbLevel": 3,
      "icbOrder": 12,
      "sectorProfile": "...",
      "status": 1,
      "createDate": "...",
      "updateDate": "...",
      "icbCodePath": "8000/8300/8350",
      "icbNamePath": "Tài chính/Ngân hàng/Ngân hàng",
      "industryID": 45,
      "parentIndustryID": 12,
      "icbShortName": "NH"
    }
  ],
  "status": 0
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `icbCode` | string | Mã ngành, 4 chữ số. Khớp với `icbCode` trong `getListOrganization` |
| `icbName` | string | Tên ngành |
| `icbShortName` | string | Tên viết tắt |
| `friendlyName` | string | Tên hiển thị thân thiện |
| `parentIcbCode` | string | Mã ngành cha — dùng dựng cây |
| `icbLevel` | integer | Cấp: `1`..`4` |
| `icbOrder` | integer | Thứ tự sắp xếp trong cùng cấp |
| `icbCodePath` | string | Đường dẫn mã từ gốc, ngăn bởi `/` |
| `icbNamePath` | string | Đường dẫn tên từ gốc, ngăn bởi `/` |
| `sectorProfile` | string | Mô tả ngành |
| `industryID` / `parentIndustryID` | integer | ID nội bộ |
| `status` | integer | `1` = đang dùng |
| `createDate` / `updateDate` | string | Metadata |

**Phân bố theo cấp:**

| Cấp | Số ngành | Ví dụ |
|---|---|---|
| L1 | 11 | Tài chính, Công nghiệp, Hàng tiêu dùng… |
| L2 | 19 | Ngân hàng L2, Dầu khí L2… |
| L3 | 40 | |
| L4 | 106 | Ngành chi tiết nhất |

`icbCode` trong `getListOrganization` trỏ tới **cấp lá** (thường L4). Dùng `icbCodePath` để lấy ngành cha ở cấp mong muốn mà không phải duyệt cây.

### Độ phủ & hiệu năng
176 bản ghi · 73 KB · ~578 ms. Cache dài hạn — cây ngành gần như không đổi.
