# Fixture giá theo ngày — cắt từ bản tải thật 2026-09-03

Ba file giữ **nguyên vỏ response** (`page · pageSize · totalCount · items · packageId · status · errors`) và **nguyên văn bản ghi 99 trường** của `PriceData/GetPriceData`; chỉ cắt bớt số bản ghi. Bản thô đầy đủ không vào repo — bằng chứng rút gọn ở [`docs/90-records/plans/2026-09-03-price-daily-etl/samples/`](../../../../../docs/90-records/plans/2026-09-03-price-daily-etl/samples/).

| File | Nội dung | Ca biên nó mang |
|---|---|---|
| `bid-page1-20260903.json` | BID trang 1, **5 phiên đầu** (03/09 → 25/08), `totalCount` giữ nguyên 3.142 | Phiên vừa đóng: `closeValue == closePrice` (chưa có điều chỉnh nào sau đó); nhóm dòng tiền theo NĐT **null** ở phiên 03/09 (T+1) nhưng đã điền ở 28/08 |
| `bid-page52-20260903.json` | BID trang 52, **1 phiên** (03/06/2014) | `closeValue = 5747.8202873773` (đã điều chỉnh, thập phân) **≠** `closePrice = 14500` (thô, nguyên) — hai cột khác nhau của lược đồ |
| `dmx-page1-20260903.json` | DMX **trọn trang 1 = 18 phiên** (mã mới niêm yết, `totalCount = 18`) | Ngày không hưởng quyền **18/08/2026**, cổ tức 4.000 đ (lát 2 đã ghi): 17/08 `closePrice 88500` · `closeValue 84499.8` ⇒ hệ số 0,9548 = (88.500 − 4.000)/88.500; từ 18/08 hai cột bằng nhau. Trang này **< 60 bản ghi** nên cũng là ca "trang cuối" |

**Số dùng làm expected:** 5 + 1 + 18 = **24 phiên** khi cả ba file đi qua job; các literal giá trong test chép từ chính file, không tính lại theo code.
