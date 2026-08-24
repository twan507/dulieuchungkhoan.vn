# 07 — Dòng tiền thị trường

Base URL: `https://wlgw-market.fiintrade.vn` — ký hiệu `FIIN_MARKET`

> **Ba endpoint này giữ nguyên vì BVSC không có nguồn tương đương.** Đã rà ngày 2026-08-14, gọi thật:
>
> | Dữ liệu | BVSC | Ghi chú |
> |---|---|---|
> | Khối ngoại **theo mã** | ✅ `foreignBuy` `foreignSell` `foreignRemain` `foreignRoom` | dulieuchungkhoan.vn lấy từ BVSC vì realtime |
> | Khối ngoại **toàn thị trường theo chuỗi** | ⚠️ Không trực tiếp | Muốn tổng phải cộng 2.534 mã — dùng `getForeign` (227 điểm intraday) |
> | **Tự doanh** | ❌ Không có | Chỉ `getProprietaryV2` |
> | **Đóng góp chỉ số** | ❌ Không có | Chỉ `getContribution` |
> | Thoả thuận | ✅ `PT_*` theo mã, `PT_TOTAL_*` theo chỉ số | dulieuchungkhoan.vn lấy từ BVSC |
>
> Kiểm chứng chéo: `getContribution` trả VN-INDEX **1.729,08** và thay đổi **−36,55** — khớp chính xác bảng giá BVSC cùng thời điểm. Hai nguồn độc lập, cùng một số.
>
> Chi tiết lấy/bỏ từng trường: [chọn trường cho ETL thị trường §6](../../20-design/market-field-selection.md).
Header bắt buộc: `Origin: https://fiinapp.bvsc.com.vn`

3 endpoint, đều ở **cấp thị trường** (nhận `ComGroupCode`, không nhận mã doanh nghiệp).

> **Đây là nhóm dữ liệu BVSC không có nguồn thay thế.** Đặc biệt `getProprietaryV2` — dữ liệu tự doanh không tồn tại ở bất kỳ endpoint BVSC nào.

### `ComGroupCode` được hỗ trợ

Cả ba endpoint đều chạy với **7 nhóm**: `VNINDEX` · `HNXIndex` · `UpcomIndex` · `VN30` · `HNX30` · `VNMID` · `VN100`.

---

## `getForeign`

**Tóm tắt:** Dòng tiền khối ngoại — chuỗi trong phiên và bảng xếp hạng theo 4 khung thời gian.

```
GET FIIN_MARKET/MoneyFlow/GetForeign?ComGroupCode={group}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Giá trị |
|---|---|---|---|---|
| `ComGroupCode` | query | string | **bắt buộc** | `enum`: 7 nhóm ở trên |
| `language` | query | string | *tuỳ chọn* | `vi` \| `en` |

### Response 200

```json
{
  "items": [{
    "comGroupCode": "VNINDEX",
    "series": [
      { "tradingDate": "2026-08-10T09:45:00",
        "foreignBuyValue": 199722954700.0,
        "foreignSellValue": 351041436000.0 }
    ],
    "today":      { ... },
    "oneWeek":    { ... },
    "oneMonth":   { ... },
    "yearToDate": { ... }
  }],
  "status": 0
}
```

#### `series[]` — chuỗi trong phiên

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `tradingDate` | string | ISO 8601 | Mốc thời gian trong phiên |
| `foreignBuyValue` | number | VND | Giá trị mua luỹ kế tại mốc đó |
| `foreignSellValue` | number | VND | Giá trị bán luỹ kế |

31 điểm quan sát được lúc 09:45. Dùng vẽ biểu đồ dòng tiền ngoại theo thời gian thực trong ngày.

#### Bốn khung thời gian — cấu trúc giống nhau

`today` · `oneWeek` · `oneMonth` · `yearToDate`, mỗi khối:

| Trường | Kiểu | Mô tả |
|---|---|---|
| `comGroupCode` | string | Nhóm chỉ số |
| `fromDate` / `toDate` | string | Khoảng thời gian |
| `timeRange` | string | `ToDay` \| `OneWeek` \| `OneMonth` \| `YearToDate` |
| `foreignBuyValue` / `foreignSellValue` | number | Tổng mua / bán toàn nhóm (VND) |
| `foreignNetBuyValue` / `foreignNetSellValue` | number | Ròng mua / ròng bán |
| `buy[]` `sell[]` `netBuy[]` `netSell[]` | array | **Bảng xếp hạng top 50 mã** cho từng tiêu chí |

#### Bản ghi trong `buy` / `sell` / `netBuy` / `netSell` — 16 trường

| Trường | Kiểu | Đơn vị | Mô tả |
|---|---|---|---|
| `organCode` | string | — | Mã FiinTrade |
| `ticker` | string | — | Mã chứng khoán |
| `timeRange` | string | — | Khung thời gian |
| `marketType` | string | — | `Buy` \| `Sell` \| `NetBuy` \| `NetSell` |
| `foreignBuyValue` / `foreignSellValue` | number | VND | Mua / bán |
| `foreignNetBuyValue` / `foreignNetSellValue` | number | VND | Ròng |
| `priceChange` | number | VND | Thay đổi giá |
| `percentPriceChange` | number | thập phân | Thay đổi phần trăm |
| `matchPrice` | number | VND | Giá khớp |
| `ceilingPrice` / `floorPrice` / `referencePrice` | number | VND | Trần / sàn / tham chiếu |
| `fromDate` / `toDate` | string | — | Khoảng thời gian |

Mỗi mảng chứa **50 bản ghi**.

### Ví dụ dữ liệu thật
Phiên 10/08/2026: ngoại mua ròng mạnh nhất `SSI` 17,0 tỷ (+2,25%) · bán ròng mạnh nhất `VHM` 48,0 tỷ (−2,19%).

### Ghi chú
`organCode` và `ticker` có thể khác nhau ngay trong dữ liệu trả về — ví dụ bản ghi `VHM` có `organCode: "NHN"`. Hiển thị phải dùng `ticker`.

### Độ phủ & hiệu năng
7/7 nhóm chỉ số · ~350 KB · ~2,9 s.

---

## `getProprietaryV2`

**Tóm tắt:** Dòng tiền tự doanh của các công ty chứng khoán.

**Mô tả:** Cấu trúc song song với `getForeign` nhưng tách cả **khối lượng lẫn giá trị**, và tách riêng khớp lệnh với thoả thuận. BVSC không có nguồn nào cung cấp dữ liệu này.

```
GET FIIN_MARKET/MoneyFlow/GetProprietaryV2?ComGroupCode={group}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Giá trị |
|---|---|---|---|---|
| `ComGroupCode` | query | string | **bắt buộc** | `enum`: 7 nhóm |
| `language` | query | string | *tuỳ chọn* | |

### Response 200

```json
{
  "items": [{
    "comGroupCode": "VNINDEX",
    "today": {
      "timeRange": "Today",
      "totalBuyTradeVolume": ..., "totalBuyTradeValue": ...,
      "totalSellTradeVolume": ..., "totalSellTradeValue": ...,
      "totalNetBuyTradeVolume": ..., "totalNetBuyTradeValue": ...,
      "totalNetSellTradeVolume": ..., "totalNetSellTradeValue": ...,
      "buy": [...], "sell": [...], "netBuy": [...], "netSell": [...]
    },
    "oneWeek": {...}, "oneMonth": {...}, "yearToDate": {...}
  }],
  "status": 0
}
```

⚠️ Khác `getForeign`: **không có mảng `series`**.

#### Tổng cấp nhóm — 8 chỉ tiêu

`totalBuyTradeVolume` · `totalBuyTradeValue` · `totalSellTradeVolume` · `totalSellTradeValue` · `totalNetBuyTradeVolume` · `totalNetBuyTradeValue` · `totalNetSellTradeVolume` · `totalNetSellTradeValue`

Đơn vị: `*Volume` = cổ phiếu · `*Value` = VND.

#### Bản ghi trong `buy` / `sell` / `netBuy` / `netSell` — 20 trường

| Trường | Kiểu | Đơn vị |
|---|---|---|
| `organCode` / `ticker` | string | — |
| `timeRange` | string | — |
| `marketType` | string \| null | ⚠️ thường `null` ở endpoint này |
| `totalBuyTradeVolume` / `totalBuyTradeValue` | number | cổ phiếu / VND |
| `totalSellTradeVolume` / `totalSellTradeValue` | number | cổ phiếu / VND |
| `totalNetBuyTradeVolume` / `totalNetBuyTradeValue` | number | cổ phiếu / VND |
| `totalNetSellTradeVolume` / `totalNetSellTradeValue` | number | cổ phiếu / VND |
| `priceChange` / `percentPriceChange` | number | VND / thập phân |
| `matchPrice` / `ceilingPrice` / `floorPrice` / `referencePrice` | number | VND |
| `fromDate` / `toDate` | string | — |

Mỗi mảng **50 bản ghi**.

### Ví dụ dữ liệu thật
Phiên 10/08/2026: tự doanh bán ròng mạnh nhất `DMX` (organCode `MWJSC`) 657,7 tỷ / 8,125 triệu CP · mua ròng mạnh nhất `HT1` 40,2 tỷ / 2,94 triệu CP.

### Độ phủ & hiệu năng
7/7 nhóm chỉ số · ~459 KB · **~3,1 s** — endpoint nặng nhất nhóm này.

---

## `getContribution`

**Tóm tắt:** Đóng góp của từng mã vào biến động chỉ số.

```
GET FIIN_MARKET/MoneyFlow/GetContribution?ComGroupCode={group}&Type=Total&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Giá trị |
|---|---|---|---|---|
| `ComGroupCode` | query | string | **bắt buộc** | `enum`: 7 nhóm |
| `Type` | query | string | **bắt buộc** | `enum`: **chỉ `Total`** |
| `language` | query | string | *tuỳ chọn* | |

⚠️ **`Type` chỉ nhận `Total`.** Đã thử `Up` và `Down` trên cả 7 nhóm — tất cả 14 tổ hợp đều trả `HTTP 400`.

### Response 200

```json
{
  "items": [{
    "series": [...],
    "contrib1Day": [...],
    "contrib5Day": [...],
    "contrib10Day": [...],
    "contrib20Day": [...]
  }],
  "status": 0
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `series` | array | Chuỗi đóng góp theo thời gian |
| `contrib1Day` | array | Đóng góp trong 1 phiên |
| `contrib5Day` | array | Luỹ kế 5 phiên |
| `contrib10Day` | array | Luỹ kế 10 phiên |
| `contrib20Day` | array | Luỹ kế 20 phiên |

### Ghi chú
Có thể truyền thêm `time={epoch_ms}` làm tham số chống cache — ứng dụng FiinTrade gốc có gửi, nhưng không bắt buộc và không ảnh hưởng kết quả.

### Độ phủ & hiệu năng
7/7 nhóm chỉ số · ~41 KB · ~800 ms.
