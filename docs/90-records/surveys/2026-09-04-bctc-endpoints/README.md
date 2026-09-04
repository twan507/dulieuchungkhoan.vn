# Khảo sát nguồn BCTC — chuẩn bị lát 5

**Ngày đo:** 2026-09-04 · **Tải:** 13 lời gọi (3 mã × 3 endpoint BCTC + 4 mã × `getFinancialReports`) + truy vấn kho, **không lời gọi nào ngoài kế hoạch**
**Mẫu:** BAB (`NASB`, ngân hàng) · A32 (`ASECO32`, công ty thường) · AAS (`HAMIS`, chứng khoán)
**Bản thô:** [`measurements-raw.json`](measurements-raw.json) + [`samples/`](samples/) — 4 payload `getFinancialReports` (bằng chứng cho hai lỗi lược đồ ở §5) và 3 payload BCTC của A32 làm mẫu hình dạng.
*(Payload BCTC của BAB và AAS cố ý KHÔNG đưa vào repo: 943 KB, và mọi số rút ra từ chúng đã nằm trong `measurements-raw.json`.)*

Tài liệu [`05-fiin-financial-statements.md`](../../../10-sources/market/05-fiin-financial-statements.md) **đã đo 2026-08-10** hình dạng response, số kỳ, độ phủ 20/20, kích thước và độ trễ. Khảo sát này **không đo lại** những thứ đó — chỉ trả lời bốn câu nó để ngỏ, đều là thứ lát 5 phải quyết.

---

## Câu 1 — Khối `quarterly[]`/`yearly[]` trong `snapshot_daily` có thay được ba endpoint BCTC không?

**Không. Cách xa.** Đây là câu spec lát 4 §3.2 cố ý để ngỏ, nay đã đóng:

| | Mã chỉ tiêu | Kỳ quý | Kỳ năm |
|---|---|---|---|
| Khối trong `snapshot_daily` (BAB) | **25** | **9** | 6 |
| Ba endpoint BCTC (BAB) | **557** | **43** | 17 |

Khối trong Snapshot là một **lát mỏng để vẽ biểu đồ tóm tắt**, không phải báo cáo tài chính. Lát 5 **bắt buộc** gọi ba endpoint riêng; không có đường tắt.

## Câu 2 — `status` của họ BCTC

**`"Success"` trên 9/9 lời gọi**, kể cả mã ngân hàng (BAB). **Chưa thấy biến thể `0`** — nhưng mẫu chỉ 3 mã, nên đây là *chưa gặp*, không phải *không có*. Vẫn dùng công thức `status ∈ {0, "Success"}` của [quy ước §6.1](../../../10-sources/market/00-conventions.md), đúng bài học lát 4: cùng một họ mà `GetSnapshot` trả `0` còn `GetSnapshotNoneBank` trả `"Success"`.

## Câu 3 — Chi phí thật một lượt trọn sàn

**Độ trễ thấp hơn hẳn số đo cũ:** 27–499 ms *(đo 2026-09-04)* so với ~1,9–2,45 s *(đo 2026-08-10)*. Nguồn nhanh hơn nhiều so với lần đo trước.

Nhưng chi phí **không do độ trễ quyết định** mà do **giãn cách 0,5 s** của trần 2 request/giây:

| | Số lời gọi | Thời gian tối thiểu chỉ tính giãn cách |
|---|---|---|
| 1.523 mã niêm yết × 3 endpoint | **4.569** | **≥ 38 phút** |
| *(bản thiết kế cũ: 1.974 mã)* | *5.922* | *≥ 49 phút* |

🔴 **`market-data-store.md` §4.2 ghi "5.922 lời gọi, ~25 phút" — con số 25 phút không thể đúng**: chỉ riêng giãn cách đã là 49 phút. Phải sửa khi lát 5 khởi động *(chưa sửa vì nhánh hiện tại thuộc lát 4)*.

## Câu 4 — Dung lượng và số dòng, tức bài toán lược đồ của lát 5

Payload trọn ba báo cáo mỗi mã: BAB **498 KB** · AAS **445 KB** · A32 **80 KB** ⇒ ước ~340 KB × 1.523 mã ≈ **500 MB** mỗi lượt trọn sàn.

Nhưng con số chi phối thiết kế là **số dòng của bảng dạng dài** `financial_statement`:

| Mã | Ô dữ liệu (mã × kỳ) | Không null | Mật độ |
|---|---|---|---|
| BAB *(ngân hàng)* | 33.540 | 16.785 | **50,0%** |
| AAS *(chứng khoán)* | 29.860 | 21.194 | **71,0%** |
| A32 *(không có kỳ quý)* | 5.590 | 3.710 | **66,4%** |

Trung bình ~13.900 dòng không null mỗi mã ⇒ **≈ 21 triệu dòng** cho một lượt nạp trọn lịch sử 1.523 mã.

Mật độ ~50–71% là do **hậu tố `a`/`b`** — bộ chỉ tiêu ngân hàng và phi ngân hàng dùng chung một response. Ví dụ cụ thể: BAB ở kỳ mới nhất, bảng cân đối chỉ **61/233 mã có giá trị (26%)**.

**Hệ quả cho lát 5 — quyết định phải chốt trong spec:** lưu **null hay bỏ null**. Bỏ null cắt được 30–50% số dòng và là hành vi đúng của lược đồ dạng dài, nhưng khi đó *"không có dòng"* mang hai nghĩa lẫn nhau — **chỉ tiêu không áp dụng cho loại hình này** và **kỳ đó nguồn chưa có số**. Đây đúng loại quyết định §4.8 (khó đảo ngược: đã ghi 21 triệu dòng rồi thì đổi rất đắt).

## Câu 5 — `getFinancialReports`: hai lỗi lược đồ sẽ giết ETL lát 5 ngay lượt đầu

*(đo thêm 2026-09-04, 4 lời gọi — BID · BAB · A32 · AAS; bản thô [`samples/*-reports.json`](samples/))*

Tài liệu đã ghi hình dạng, bẫy CDN, chuyện trùng bản `_HN`/`_RL`, độ phủ 50/51. Năm điều nó **chưa** nói:

### 5.1 🔴 `lengthReport` có BẢY giá trị, lược đồ chỉ cho phép NĂM

```
{1: 47, 2: 78, 3: 45, 4: 40, 5: 65, 6: 24, 9: 4}     ← 307 dòng trên 4 mã
```

Đọc `title` để giải nghĩa hai giá trị lạ:

| Giá trị | Nghĩa | Ví dụ `title` |
|---|---|---|
| 1–4 | quý I–IV | *"BCTC chưa kiểm toán quý 2 năm 2026"* |
| 5 | cả năm | *"BCTC đã kiểm toán năm 2025"* |
| **6** | **bán niên** | *"BCTC đã kiểm toán 6 tháng năm 2026"* |
| **9** | **9 tháng luỹ kế** | *"BCTC chưa kiểm toán 9 tháng năm 2021"* |

Migration `0004` đặt `length_report smallint CHECK (length_report BETWEEN 1 AND 5)` trên **cả hai** bảng `financial_report_file` **và** `corporate_event`. Với dữ liệu đo được, **28/307 dòng (9%)** rơi ngoài ràng buộc ⇒ `INSERT` vi phạm CHECK ⇒ **giết cả lượt**, không phải rơi một dòng.

⚠️ **`corporate_event` chưa bị cắn nhưng là mìn chờ.** Kho hiện chỉ có `length_report` 1–5 *(53.669 dòng NULL + 1–5)*, và `events_normalize` truyền thẳng `lengthReport` xuống **không kẹp giá trị** — nghĩa là `getCorporateEarning` chưa từng phát `6`/`9`, chứ không phải code đang chặn. Ngày nguồn phát một sự kiện báo cáo bán niên, `etl events` sẽ chết vì CHECK.

**Việc phải làm ở lát 5:** migration nới CHECK trên **cả hai bảng** theo tập đo được. Nên viết `IN (1,2,3,4,5,6,9)` kèm chú thích nghĩa từng giá trị thay vì `BETWEEN 1 AND 9` — dải liền để lọt `7`, `8` là hai giá trị chưa ai thấy và chưa ai biết nghĩa.

### 5.2 🔴 `sourceUrl` trùng trong CÙNG một response, mà cột lại `UNIQUE`

BID và BAB mỗi mã có **1 cặp trùng**. Ví dụ BID: hai `id` khác nhau (`9172652`, `9268003`), cùng năm 2021, cùng `lengthReport=5`, cùng `title`, **cùng một URL**.

`financial_report_file.source_url` khai `text NOT NULL UNIQUE` ⇒ nạp tuần tự sẽ vi phạm khoá duy nhất **ngay trong một payload**. Phải khử trùng trước khi ghi, hoặc `ON CONFLICT (source_url) DO NOTHING`.

Kèm một câu hỏi thiết kế: bảng **không lưu `id`** của nguồn. Hai bản ghi phân biệt nhau bằng `id` mà ta lại lấy `source_url` làm khoá — cân nhắc lưu thêm `id` để giữ được thông tin nguồn coi chúng là hai.

### 5.3 Không cần phân trang

`len(items) == totalCount` trên **4/4 mã** (141 · 106 · 8 · 48). Một mã một lời gọi, không nhân lên.

### 5.4 `status` trả `"Success"`, không phải `0`

Mẫu trong tài liệu ghi `"status": 0` *(đo 2026-08-10)*; đo lại hôm nay ra `"Success"` trên 4/4. Giữ cả hai số kèm ngày, và cứ dùng công thức `status ∈ {0, "Success"}`.

### 5.5 Quy mô

8–141 báo cáo mỗi mã *(trung bình 77 trên mẫu 4 mã)*, dải năm 2008–2026. Ước cho 1.523 mã: **1.523 lời gọi** *(≥ 13 phút chỉ tính giãn cách 0,5 s)*, **≈ 117.000 dòng**. Kích thước 1,8–30,3 KB mỗi response, độ trễ 64–662 ms.

## Ba con số đính chính cho tầng tài liệu

| Chỗ | Đang ghi | Đo được 2026-09-04 |
|---|---|---|
| `market-data-store.md` §4.2 | BCTC "5.922 lời gọi, ~25 phút" | **4.569** lời gọi *(1.523 mã)*, **≥ 38 phút** chỉ tính giãn cách |
| `market-data-store.md` §5.4 / roadmap | "556 mã chỉ tiêu" | **557** mã phân biệt trên ba endpoint |
| `05-fiin-financial-statements.md` | độ trễ ~1,9–2,45 s | **27–499 ms** *(nguồn nhanh lên; giữ cả hai số kèm ngày đo)* |

## Việc lát 5 nên làm đầu tiên

1. Chốt **lưu null hay bỏ null** (§4.8, ba phương án, điều kiện đảo ngược).
2. Chốt nạp **trọn lịch sử** hay **cửa sổ N kỳ** — nguồn **không lọc được kỳ** *(bẫy đã ghi trong tài liệu)*, nên mỗi lời gọi luôn tải trọn; cắt cửa sổ chỉ tiết kiệm chỗ lưu, không tiết kiệm lời gọi.
3. Nhân bản khuôn `snapshot_*` — nó đã qua 5 vòng sửa và một review toàn nhánh.

---

## 6. Bổ sung chiều 2026-09-04 — 12 lời gọi trước khi mở lát 5

**Tải:** 3 endpoint × 4 mã có kỳ quý (BAB `NASB` · AAS `HAMIS` · VNM · HPG), giãn cách 0,5 s, không lời gọi nào ngoài kế hoạch. Bản thô: [`periods-raw.json`](periods-raw.json). Cộng một phép đối chiếu cục bộ giữa `measurements-raw.json` và [`field-dictionary.json`](../../../10-sources/market/field-dictionary.json).

### 6.1 `quarterReport` của ba endpoint số liệu chỉ có NĂM giá trị

| Mã | Kỳ quý (BS / IS / CF) | Kỳ năm | `quarterReport` quý | `quarterReport` năm | Kỳ trùng |
|---|---|---|---|---|---|
| BAB | 43 / 43 / 43 | 17 / 17 / 17 | `{1,2,3,4}` | `{5}` | 0 |
| AAS | 39 / 38 / 38 | 15 / 15 / 15 | `{1,2,3,4}` | `{5}` | 0 |
| VNM | 84 / 87 / 67 | 24 / 23 / 23 | `{1,2,3,4}` | `{5}` | 0 |
| HPG | 78 / 86 / 72 | 21 / 21 / 19 | `{1,2,3,4}` | `{5}` | 0 |
| A32 *(mẫu sáng)* | 0 / 0 / 0 | 10 | — | `{5}` | 0 |

Giá trị `6`/`9` ở §5.1 là của **`lengthReport` trong `getFinancialReports`** (danh sách PDF), **không** xuất hiện ở ba endpoint số liệu. Hệ quả: `financial_statement` giữ nguyên `CHECK (length_report BETWEEN 1 AND 5)`; chỉ `financial_report_file` và `corporate_event` cần nới.

Cả bốn mã: `quarterly[]` xếp **mới → cũ** (phần tử đầu 2026Q2), `yearly[]` cũng mới → cũ — đúng như tài liệu nguồn ghi, và **ngược** với khối `quarterly[]` trong `GetSnapshot*` (cũ → mới, đính chính ở spec lát 4 §5.3).

### 6.2 Con số 557 ở "Ba con số đính chính" là gì

Đối chiếu tập khoá của 9 lời gọi buổi sáng với từ điển:

| | Số |
|---|---|
| Khoá phân biệt trên ba endpoint (đúng con số 557 của §"Ba con số đính chính") | **557** |
| … trong đó là mã từ điển (so khớp không phân biệt hoa thường) | **549** |
| … trong đó **không phải** mã chỉ tiêu | **8**: `organCode` · `ebit` · `ebitDa` · `operating` · `otherAssetBank` · `otherAssetNonBank` · `otherLiabilties` · `rtq29` |
| Mã từ điển chưa gặp trên mẫu 3 mã | 7: `cfa71` `cfa72` `isi173` `nob44` `nob65` `nob66` `nob151` |
| Mã BCTC trong từ điển | **556** |

Vậy **557 không phải đính chính của 556** — dòng "556 → 557" ở bảng đính chính buổi sáng là so hai số đếm hai thứ khác nhau. Tài liệu sống đã sửa lại theo đó (roadmap, `market-data-store` §5.4, `05-fiin-financial-statements.md`); bảng buổi sáng giữ nguyên làm bản ghi.

### 6.3 Khoá viết hoa lẫn: `bsI141` và `bsS134`

`GetBalanceSheet` trả đúng hai khoá này với chữ hoa ở giữa trên **4/4 mã chiều + A32 sáng**; `GetIncomeStatement` và `GetCashFlow` không có. Từ điển ghi `bsi141`/`bss134`. Không hạ chữ thường thì hai mã rơi khỏi từ điển và không khớp khoá chính `metric_code` (migration `0004` chú thích "chữ thường").

### 6.4 Số kỳ ba báo cáo không bằng nhau, kích thước và độ trễ

| Mã | KB (BS / IS / CF) | ms (BS / IS / CF) | Số khoá (BS / IS / CF) |
|---|---|---|---|
| BAB | 212 / 152 / 135 | 653 / 219 / 118 | 235 / 180 / 150 |
| AAS | 189 / 140 / 117 | 640 / 399 / 527 | 235 / 180 / 150 |
| VNM | 408 / 285 / 204 | 1.069 / 538 / 484 | 235 / 180 / 150 |
| HPG | 377 / 276 / 206 | 817 / 413 / 332 | 235 / 180 / 150 |

Số khoá mỗi endpoint **cố định** bất kể loại hình (ngân hàng, chứng khoán, sản xuất) — bộ mã của mọi loại hình cùng nằm trong một response, loại hình không áp dụng thì `null`. `status` = `"Success"` 12/12.

### 6.5 AC5 của lát 4 — kiểm lại lúc 17:10

`GetSnapshotNoneBank` của AAA: `rtd11` 2.791.635.955.700 ÷ `outstandingShare` 393.742.730 = **7.090** — vẫn là giá đóng cửa **03/09** (giá 04/09 là 7.130 theo `getPriceData`, xem [ledger lát 4 §1d](../../plans/2026-09-04-snapshot-family-etl/ledger.md)). Nguồn chưa nạp phiên 04/09 sau 2 giờ 10 phút kể từ khi đóng cửa. AC5 vẫn chưa đóng được; lệnh đóng không đổi.

### 6.6 Bổ sung tối 2026-09-04 (18:5x, 4 lời gọi) — `quarterly` là `null`, không phải `[]`

Lượt AC4 của lát 5 báo A32 `bad_shape` 3/3 báo cáo trong khi lượt 18:40 nạp sạch. Gọi thẳng `ASECO32` ba endpoint: HTTP 200, `status "Success"`, **`"quarterly": null`**, `yearly` 10 kỳ như cũ. Mẫu buổi sáng (`samples/A32-*.json`) có `"quarterly": []`. Cùng một mã, cùng một ngày, hai cách tuần tự hoá của "không có kỳ quý" — cùng họ với `status` 0/"Success" ở câu 2. Bản thô: `backend/tests/etl/fixtures/fundamentals/A32-cf-quarterly-null.json`. Hệ quả cho code: coi `null` là rỗng; kiểm hình dạng viết theo *nghĩa*, không theo *kiểu* của mẫu đã lưu. Tài liệu sống đã ghi ở [05](../../../10-sources/market/05-fiin-financial-statements.md).
