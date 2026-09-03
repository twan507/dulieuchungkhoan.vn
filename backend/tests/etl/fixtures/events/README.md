# Fixture lịch sự kiện — cắt từ bản tải thật 2026-09-03

Sáu file `*-sample-20260903.json` giữ **nguyên vỏ response** (`{totalCount, items, status}`) và **nguyên văn bản ghi** của nguồn, chỉ chọn lọc bản ghi. Bản tải đầy đủ (35 MB) không vào repo — bằng chứng rút gọn ở [`docs/90-records/plans/2026-09-03-events-daily-etl/samples/`](../../../../../docs/90-records/plans/2026-09-03-events-daily-etl/samples/).

⚠️ `totalCount` trong file đã sửa thành số bản ghi của chính file, để fixture qua được vế guard *"đủ trang"*. Đây là **thay đổi duy nhất** so với nguồn.

Mỗi file chứa đúng những ca biên đã đo được, không phải bản ghi lấy ngẫu nhiên:

| File | Ca biên trong đó |
|---|---|
| `agm-sample` | **SASTECO** — hai bản ghi giống hệt nhau trừ `publicDate` có phần giờ (`T11:03:28.023` vs `T00:00:00`) ⇒ cắt ngày xong phải gộp làm **1**. **SHX** — cùng ngày công bố, khác ngày tổ chức (`2022-12-23` vs `2022-10-18`) ⇒ `stage_key` phải giữ thành **2** |
| `cashdividend-sample` | **SD9** `dividendYear` 2019 vs 2021 và **SGS** 2023 vs 2024 — cùng ngày, cùng `stageName='Cả năm'` ⇒ mỗi cặp phải ra **2 dòng** |
| `stockdividend-sample` | **ABI** hai bản ghi **trùng nguyên văn** — nguồn tự đẻ ⇒ gộp làm **1** |
| `shareissuance-sample` | **ABI** bốn bản ghi: hai `issueMethodName` × (chưa có `listingDate` / đã có) ⇒ ra **2**, giữ bản có `listingDate`. **VIC** khác `planVolumn` (một giá trị **âm**) ⇒ giữ **2**. **RYG** `organCode='12681'` không có trường tên nào ⇒ tên issuer lùi về ticker |
| `earning-sample` | Ba bản ghi thường, `lengthReport=2` |
| `ipo-sample` | `organCode` là **mã số thuế** (`0304941312`) và **id số** (`11009`), có `organName` |

**Tổng cộng 28 bản ghi vào → 24 dòng ra, `dup_conflicts = 4`, 17 `organCode` duy nhất.** Ba số này là expected của bộ test và được tính bằng cách áp luật spec lên chính sáu file này, không phải đếm tay.
