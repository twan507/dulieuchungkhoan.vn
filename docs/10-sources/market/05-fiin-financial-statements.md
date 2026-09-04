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
| `items[0].quarterly[]` | array | Chuỗi kỳ quý, mới nhất trước *(xác nhận lại 2026-09-04 trên 4 mã: phần tử đầu là 2026Q2, phần tử cuối là kỳ cũ nhất — NGƯỢC với khối `quarterly[]` trong `GetSnapshot*`, khối đó xếp cũ → mới)* |
| `items[0].yearly[]` | array | Chuỗi kỳ năm |
| `yearReport` | integer | Năm báo cáo |
| `quarterReport` | integer | `1`..`4` = quý I–IV · `5` = cả năm — **chỉ năm giá trị này** *(đo 2026-09-04: 5 mã BAB · AAS · VNM · HPG · A32, 0 dòng mang giá trị khác; khác với `lengthReport` của `getFinancialReports` bên dưới có thêm `6`/`9`)* |
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
- ⚠️ **`GetBalanceSheet` trả hai khoá viết hoa lẫn: `bsI141` và `bsS134`** *(đo 2026-09-04, 4/4 mã BAB · AAS · VNM · HPG, kèm mẫu A32 trong [khảo sát](../../90-records/surveys/2026-09-04-bctc-endpoints/samples/A32-balance_sheet.json))*. Từ điển ghi `bsi141`/`bss134` chữ thường — **hạ chữ thường trước khi tra hoặc ghi kho**. `GetIncomeStatement` và `GetCashFlow` không có khoá nào như vậy.
- ⚠️ **`quarterly`/`yearly` có thể là `null` thay vì `[]`** — cùng mã A32, sáng 2026-09-04 nguồn trả `"quarterly": []`, chiều cùng ngày (18:5x) trả `"quarterly": null` trên cả ba endpoint, `yearly` bình thường, `status` `"Success"`. Hai cách tuần tự hoá của "không có kỳ quý"; coi `null` là rỗng, chỉ thiếu khoá hay kiểu khác list mới là sai hình dạng. Mẫu thật: `backend/tests/etl/fixtures/fundamentals/A32-cf-quarterly-null.json`.
- `status` trả `0` *(đo 2026-08-10)* **và** `"Success"` *(đo 2026-09-04, 21/21 lời gọi trên 5 mã BAB · A32 · AAS · VNM · HPG)* trên cùng ba endpoint — kiểm bằng `status ∈ {0, "Success"}` theo [quy ước §6.1](00-conventions.md), không so với một giá trị.
- Ngoài mã chỉ tiêu, mỗi response còn **8 khoá không phải mã chỉ tiêu**: `organCode` · `ebit` · `ebitDa` · `operating` · `otherAssetBank` · `otherAssetNonBank` · `otherLiabilties` *(nguyên văn, thiếu chữ `i`)* · `rtq29` *(chỉ `GetIncomeStatement`)*. Đếm trọn ba endpoint được **557 khoá phân biệt** = 549 mã từ điển + 8 khoá này *(đối chiếu 2026-09-04 trên 3 mã)* — đừng đọc 557 thành "số mã chỉ tiêu".
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
- ⚠️ **Một kỳ có thể xuất hiện HAI lần trong cùng mảng** — `GetBalanceSheet` của BSHCO *(đo 2026-09-04 20:12, lượt điền đầu của lát 5)*: `quarterly` 17 phần tử mà kỳ 2024/Q2 có hai bản ghi **giống hệt nhau** (160 ô, 0 khác biệt). Khảo sát buổi chiều đo 0 trùng trên 4 mã nên đây là ca hiếm. Gộp khi giống hệt; hai bản khác nhau mới coi là sai hợp đồng. Mẫu thật: `backend/tests/etl/fixtures/fundamentals/BSHCO-bs-duplicate-period.json`.

### Độ phủ & hiệu năng

| Endpoint | Độ phủ (20 mã) | Size min / TB / max | Thời gian |
|---|---|---|---|
| `GetBalanceSheet` | 20/20 | 42 KB / 227 KB / 374 KB | ~2,45 s |
| `GetIncomeStatement` | 20/20 | 30 KB / 165 KB / 278 KB | ~2,41 s |
| `GetCashFlow` | 20/20 | 25 KB / 126 KB / 194 KB | ~1,90 s |

⚡ **Đo lại 2026-09-04 trên 3 mã (BAB · A32 · AAS): độ trễ chỉ 27–499 ms**, thấp hơn một bậc so với ~1,9–2,45 s đo ngày 2026-08-10. *Chiều cùng ngày, 12 lời gọi trên 4 mã có kỳ quý (BAB · AAS · VNM · HPG): 118–1.069 ms, payload 117–408 KB — lớn nhất là `GetBalanceSheet` của VNM (408 KB, 84 kỳ quý, 1.069 ms).* Giữ cả hai số kèm ngày — nguồn đã nhanh lên, không phải số cũ sai. Hệ quả: chi phí một lượt trọn sàn do **giãn cách 0,5 s** quyết định chứ không do độ trễ. Chi tiết: [khảo sát BCTC](../../90-records/surveys/2026-09-04-bctc-endpoints/README.md).

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
| `lengthReport` | integer | `1`..`4` = quý · `5` = cả năm · **`6` = bán niên · `9` = 9 tháng luỹ kế** *(đo 2026-09-04: 28/307 dòng trên 4 mã BID · BAB · A32 · AAS mang `6`/`9`; giải nghĩa từ `title`, chi tiết [khảo sát §5.1](../../90-records/surveys/2026-09-04-bctc-endpoints/README.md))* |
| `title` | string | Tiêu đề, ví dụ *"BCTC riêng lẻ chưa kiểm toán quý 2 năm 2026"* |
| `sourceUrl` | string | **URL PDF trực tiếp** trên `cmsv5/cmsv6.fiingroup.vn` |

### Ghi chú & bẫy

- ⚠️ `sourceUrl` trỏ tới CDN ngoài (`cmsv5/cmsv6.fiingroup.vn`). Nên **proxy qua backend** thay vì cho trình duyệt tải thẳng: tránh phụ thuộc uptime của CDN bên thứ ba, kiểm soát được timeout, và ghi nhận được lượt tải.
- Một mã có nhiều bản cho cùng một kỳ (hợp nhất `_HN` và riêng lẻ `_RL`) — phân biệt qua `title`, không có trường riêng.
- `totalCount` chính xác ở endpoint này *(4/4 mã `len(items) == totalCount`, đo 2026-09-04)*.
- ⚠️ `sourceUrl` **trùng ngay trong một response** — BID và BAB mỗi mã một cặp: hai `id` khác nhau, cùng năm, cùng `lengthReport`, cùng `title`, cùng URL *(đo 2026-09-04)*. Khử trùng trước khi ghi nếu cột khoá theo URL.
- `status` trả `0` *(đo 2026-08-10)* và `"Success"` *(đo 2026-09-04, 4/4)* — cùng luật `∈ {0, "Success"}` như ba endpoint trên.

### Độ phủ & hiệu năng

50/51 mã mẫu (98%) — chỉ `TAH` trả 0 báo cáo.

| | Số PDF |
|---|---|
| Trung bình | ~94 |
| Cao nhất | VNM 233 · FPT 213 · VC3 213 · HPG 212 · SSI 206 |
| Thấp nhất | TAB 3 · THU 9 · NAC 9 · HD8 18 · RAT 19 · VCT 23 |

99 byte – 51,7 KB · TB 21 KB · ~590 ms.
