# 05 — Báo cáo tài chính FiinTrade

Base URL: `https://wlgw-fundamental.fiintrade.vn` — ký hiệu `FIIN_FUND`
Header bắt buộc: `Origin: https://fiinapp.bvsc.com.vn`

4 endpoint. Tất cả nhận **`organCode`**.

> ⚠️ **Ba endpoint đầu trả payload rất lớn (191–374 KB mỗi lời gọi)** và mất 1,9–2,5 giây. Chúng trả **toàn bộ lịch sử** trong một lần, không phân trang. Không có tham số nào giới hạn số kỳ.

---

## `getBalanceSheet` · `getIncomeStatement` · `getCashFlow`

**Tóm tắt:** Bảng cân đối kế toán / Kết quả kinh doanh / Lưu chuyển tiền tệ — toàn bộ lịch sử theo quý và năm.

**Mô tả:** Ba endpoint có **cấu trúc response giống hệt nhau**, chỉ khác bộ mã chỉ tiêu bên trong. Mỗi lời gọi trả về toàn bộ lịch sử sẵn có: tới **86 kỳ quý** và **21 kỳ năm** với doanh nghiệp lâu đời.

```
GET FIIN_FUND/FinancialStatement/GetBalanceSheet?OrganCode={organCode}&language=vi
GET FIIN_FUND/FinancialStatement/GetIncomeStatement?OrganCode={organCode}&language=vi
GET FIIN_FUND/FinancialStatement/GetCashFlow?OrganCode={organCode}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `OrganCode` | query | string | **bắt buộc** | Mã nội bộ FiinTrade |
| `language` | query | string | *tuỳ chọn* | `vi` \| `en` |

Không có tham số giới hạn kỳ, phân trang, hay lọc theo năm.

### Response 200

```json
{
  "page": 1, "pageSize": 0, "totalCount": 1,
  "items": [{
    "quarterly": [
      { "yearReport": 2026, "quarterReport": 2, "bsa1": 1516685712000000, "bsa23": ..., "bsb98": ... }
    ],
    "yearly": [
      { "yearReport": 2025, "quarterReport": 5, "bsa1": ..., "bsa23": ... }
    ]
  }],
  "status": 0
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `items[0].quarterly[]` | array | Chuỗi kỳ quý, mới nhất trước |
| `items[0].yearly[]` | array | Chuỗi kỳ năm |
| `yearReport` | integer | Năm báo cáo |
| `quarterReport` | integer | `1`..`4` = quý I–IV · `5` = cả năm |
| *(các trường khác)* | number \| null | Mã chỉ tiêu FiinGroup — xem dưới |

### Mã chỉ tiêu theo endpoint

| Endpoint | Tiền tố | Ví dụ |
|---|---|---|
| `GetBalanceSheet` | `bsa*` `bsb*` | `bsa1` = Tổng tài sản · `bsa23` · `bsa53` · `bsa78` · `bsb98` · `bsb103` · `bsb104` · `bsb106` · `bsb113` |
| `GetIncomeStatement` | `isa*` `isb*` `isi*` | `isa1` · `isa22` · `isb27` · `isi103` |
| `GetCashFlow` | `cfa*` | `cfa18` |

Hậu tố `a` / `b` phân biệt bộ chỉ tiêu **phi ngân hàng** (`a`) và **ngân hàng** (`b`). Doanh nghiệp ngân hàng có các trường `bsb*` được điền, `bsa*` phần lớn `null` và ngược lại.

Tra nghĩa từng mã: [Phụ lục A §A.5](appendix-A-field-codes.md) — **729 mã đã giải mã, độ phủ 100% trên response thật**, kèm bảng [field-dictionary.json](field-dictionary.json).

### Ghi chú & bẫy

- ⚠️ **Không lọc được kỳ.** Muốn hiển thị 5 năm gần nhất vẫn phải tải toàn bộ 21 kỳ năm và 86 kỳ quý.
- Số kỳ khác nhau rõ rệt giữa các mã. Ví dụ đo được:

| Mã | Sàn | quarterly (BS/IS/CF) | yearly |
|---|---|---|---|
| TDH | HOSE | 78 / 86 / 62 | 21 |
| STC | HNX | 78 / 86 / 64 | 20–21 |
| VND | HOSE (CK) | 67 / 67 / 65 | 18–19 |
| ABS | HOSE | 30 / 30 / 29 | 10 |
| DM7 | UPCOM | 36 / 37 / 35 | 9 |
| **THU** | UPCOM | **0 / 0 / 0** | 12 |
| **RAT** | UPCOM | **0 / 0 / 0** | 16 |
| **VCT** | UPCOM | **2 / 1 / 1** | 18 |

- ⚠️ Ba mã UPCOM nhỏ (`THU`, `RAT`, `VCT`) **không có dữ liệu quý** nhưng vẫn có dữ liệu năm. Giao diện phải xử lý trường hợp tab "Theo quý" trống trong khi tab "Theo năm" có dữ liệu.
- Số kỳ giữa ba báo cáo **không bằng nhau** trên cùng một mã (TDH: 78 / 86 / 62). Không thể giả định ghép được theo chỉ số vị trí — phải ghép theo cặp `yearReport` + `quarterReport`.

### Độ phủ & hiệu năng

| Endpoint | Độ phủ (20 mã) | Size min / TB / max | Thời gian |
|---|---|---|---|
| `GetBalanceSheet` | 20/20 | 42 KB / 227 KB / 374 KB | ~2,45 s |
| `GetIncomeStatement` | 20/20 | 30 KB / 165 KB / 278 KB | ~2,41 s |
| `GetCashFlow` | 20/20 | 25 KB / 126 KB / 194 KB | ~1,90 s |

⚡ **Đo lại 2026-09-04 trên 3 mã (BAB · A32 · AAS): độ trễ chỉ 27–499 ms**, thấp hơn một bậc so với ~1,9–2,45 s đo ngày 2026-08-10. Giữ cả hai số kèm ngày — nguồn đã nhanh lên, không phải số cũ sai. Hệ quả: chi phí một lượt trọn sàn do **giãn cách 0,5 s** quyết định chứ không do độ trễ. Chi tiết: [khảo sát BCTC](../../90-records/surveys/2026-09-04-bctc-endpoints/README.md).

---

## `getFinancialReports`

**Tóm tắt:** Danh sách file PDF báo cáo tài chính gốc, kèm link tải trực tiếp.

**Mô tả:** Trả về đường dẫn tới bản PDF do doanh nghiệp công bố, lưu trên CDN của FiinGroup. Đây là bản gốc có dấu, khác với dữ liệu số đã chuẩn hoá ở ba endpoint trên.

```
GET FIIN_FUND/FinancialStatement/GetFinancialReports?OrganCode={organCode}&language=vi
```

### Tham số

| Tên | Vị trí | Kiểu | Bắt buộc |
|---|---|---|---|
| `OrganCode` | query | string | **bắt buộc** |
| `language` | query | string | *tuỳ chọn* |

### Response 200

```json
{
  "page": 1, "pageSize": 0, "totalCount": 139,
  "items": [{
    "id": 9431745,
    "organCode": "BID",
    "yearReport": 2026,
    "lengthReport": 2,
    "title": "BCTC chưa kiểm toán quý 2 năm 2026",
    "sourceUrl": "https://cmsv6.fiingroup.vn/medialib/FG/2026/2026-07/2026-07-31/BID/BID_BCTC_Q2_2026_HN.pdf"
  }],
  "status": 0
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | integer | Định danh báo cáo |
| `organCode` | string | Mã doanh nghiệp |
| `yearReport` | integer | Năm báo cáo |
| `lengthReport` | integer | `1`..`4` = quý · `5` = cả năm |
| `title` | string | Tiêu đề, ví dụ *"BCTC riêng lẻ chưa kiểm toán quý 2 năm 2026"* |
| `sourceUrl` | string | **URL PDF trực tiếp** trên `cmsv5/cmsv6.fiingroup.vn` |

### Ghi chú & bẫy

- ⚠️ `sourceUrl` trỏ tới CDN ngoài (`cmsv5/cmsv6.fiingroup.vn`). Nên **proxy qua backend** thay vì cho trình duyệt tải thẳng: tránh phụ thuộc uptime của CDN bên thứ ba, kiểm soát được timeout, và ghi nhận được lượt tải.
- Một mã có nhiều bản cho cùng một kỳ (hợp nhất `_HN` và riêng lẻ `_RL`) — phân biệt qua `title`, không có trường riêng.
- `totalCount` chính xác ở endpoint này.

### Độ phủ & hiệu năng

50/51 mã mẫu (98%) — chỉ `TAH` trả 0 báo cáo.

| | Số PDF |
|---|---|
| Trung bình | ~94 |
| Cao nhất | VNM 233 · FPT 213 · VC3 213 · HPG 212 · SSI 206 |
| Thấp nhất | TAB 3 · THU 9 · NAC 9 · HD8 18 · RAT 19 · VCT 23 |

99 byte – 51,7 KB · TB 21 KB · ~590 ms.
