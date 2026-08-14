# Phụ lục A — Từ điển mã trường FiinGroup

Dữ liệu FiinTrade dùng **mã trường viết tắt** thay cho tên có nghĩa (`rtd11`, `rtq12`, `bsa1`, `isa22`…). Phụ lục này giải mã chúng.

**Tổng cộng 729 mã — 98,5% có tên tiếng Việt, 98,5% có tên tiếng Anh.** Bảng đầy đủ dạng máy đọc: [field-dictionary.json](field-dictionary.json).

Hai nguồn giải mã:

| Họ mã | Nguồn | Số mã | Có `unit`? | Xem |
|---|---|---:|---|---|
| `rtd*` `rtq*` `rqq*` `ryq*` `rsd*` `rsq*` | [`Screener/GetScreenerParameters`](10-fiin-dictionary.md) — API trả `code → name → unit`, **83 mã**. Phần còn lại lấy từ bundle | 173 | ⚠️ chỉ 83 | **A.3** · **A.5** |
| `bs*` `is*` `cf*` `no*` — chỉ tiêu báo cáo tài chính, đủ 4 loại hình | Bundle JS của ứng dụng FiinTrade — **không phải API** | 556 | ❌ | **A.5** |

---

## A.1 Quy tắc tiền tố

| Tiền tố | Nhóm chỉ tiêu | Kỳ tính |
|---|---|---|
| `rtd` | Chỉ số thị trường theo ngày | Thời điểm hiện tại |
| `rtq` | Chỉ số tài chính | **TTM** — 4 quý gần nhất |
| `rqq` | Chỉ số tài chính | Quý gần nhất |
| `ryq` | Chỉ số tài chính | Năm gần nhất |
| `rsd` | Chỉ số cấp ngành | Theo ngày |
| `isa` | Kết quả kinh doanh — phi ngân hàng | Theo kỳ báo cáo |
| `isb` | Kết quả kinh doanh — ngân hàng | Theo kỳ báo cáo |
| `isi` | Kết quả kinh doanh — bảo hiểm | Theo kỳ báo cáo |
| `bsa` | Cân đối kế toán — phi ngân hàng | Theo kỳ báo cáo |
| `bsb` | Cân đối kế toán — ngân hàng | Theo kỳ báo cáo |
| `cfa` | Lưu chuyển tiền tệ | Theo kỳ báo cáo |
| `nob` | Chỉ tiêu ngoài bảng | Theo kỳ báo cáo |

Hậu tố `a` / `b` / `i` phân biệt bộ chỉ tiêu theo loại hình doanh nghiệp. Với một doanh nghiệp cụ thể, chỉ một bộ được điền, bộ còn lại là `null`.

---

## A.2 Mã đã xác minh bằng đối chiếu số học

Xác minh trên mã BID, giá 39.050 đ ngày 10/08/2026, đối chiếu chéo giữa `Valuation/GetValuation`, `Rankings/GetAllScore` và bảng so sánh ngành:

| Mã | Ý nghĩa | Giá trị (BID) | Cách kiểm chứng |
|---|---|---|---|
| `rtd11` | **Vốn hoá thị trường** (VND) | 284.286.546.450.500 | Bằng đúng `marketCap` trong `valuationSector` |
| `rtd14` | **EPS** (VND) | 4.548,52 | 39.050 ÷ 4.548,52 = 8,585 = `rtd21` |
| `rtd7` | **Giá trị sổ sách/CP — BVPS** (VND) | 26.517,60 | 39.050 ÷ 26.517,6 = 1,4726 = `rtd25` |
| `rtd21` | **P/E** (lần) | 8,585 | Bằng đúng `pe` trong `valuationSector` |
| `rtd25` | **P/B** (lần) | 1,4726 | Bằng đúng `pb` trong `valuationSector` |
| `rtq12` | **ROE (TTM)** (thập phân) | 0,1821 = 18,21% | Xác nhận chéo bởi `GetScreenerParameters`: `Rtq12` = "ROE (TTM)" |
| `rtq14` | **ROA (TTM)** (thập phân) | 0,00975 = 0,98% | Xác nhận chéo: `Rtq14` = "ROA (TTM)" |
| `bsa1` | **Tổng tài sản** (VND) | 1.516.685.712.000.000 | Khớp `totalAsset` trong `valuationSector` |

### Mã chưa xác định

| Mã | Giá trị quan sát (BID) | Ghi chú |
|---|---|---|
| `rtd35` | 0,9552 | Nghi là **Beta**. Chưa xác nhận |
| `rtd53` | — | Xuất hiện trong `Snapshot.summary` |
| `rtq10` | — | Xuất hiện trong `Snapshot.summary` |
| `rtq180` | 87.626.300.000.000 | Xuất hiện trong `Valuation.valuationStock` |

> Bốn mã này vẫn chưa xác định sau vòng dò 2026-08-14 — xem [§A.5](#a5-từ-điển-đầy-đủ--729-mã), mục *11 mã còn thiếu tên*. Đã thử ba cách, kể cả đối chiếu số học toàn bộ trường trên bốn loại hình doanh nghiệp.

---

## A.3 Bảng tra 83 tiêu chí từ `GetScreenerParameters`

Bảng này lấy trực tiếp từ API, có thể gọi lại bất cứ lúc nào để cập nhật. Lưu ý mã ở đây viết **hoa chữ đầu** (`Rtq12`) trong khi các endpoint dữ liệu trả về **viết thường** (`rtq12`) — cùng một chỉ tiêu.

### Giá — `Price`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `ClosePrice` | Giá | Range | VND |
| `PercentPriceChange1Day` | Biến động giá 1 ngày | Range | Percentage |
| `PercentPriceChange1Week` | Biến động giá 1 tuần | Range | Percentage |
| `PercentPriceChange1Month` | Biến động giá 1 tháng | Range | Percentage |
| `PercentPriceChange3Month` | Biến động giá 3 tháng | Range | Percentage |
| `PercentPriceChange6Month` | Biến động giá 6 tháng | Range | Percentage |
| `PercentPriceChange52Week` | Biến động giá 52 tuần | Range | Percentage |
| `PercentPriceChangeYTD` | Biến động giá từ đầu năm | Range | Percentage |

### Khối lượng & Biến động — `VolumeNVolatility`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `TotalMatchVolume` | Khối lượng GD | Range | ThousandUnit |
| `AverageVolume1Week` | Kl T.bình 5 phiên | Range | ThousandUnit |
| `AverageVolume2Week` | Kl T.bình 10 phiên | Range | ThousandUnit |
| `AverageVolume1Month` | Kl T.bình 20 phiên | Range | ThousandUnit |
| `AverageVolume3Month` | Kl T.bình 3 tháng | Range | ThousandUnit |
| `Rtd19` | Beta | Range | Unit |
| `FreeFloatRate` | % Free Float | Range | Percentage |

### Giá trị GD — `TradingValue`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `TotalMatchValue` | Giá trị GD | Range | MillionVND |
| `AverageValue1Week` | Giá trị GD T.bình 5D | Range | MillionVND |
| `AverageValue2Week` | Giá trị GD T.bình 10D | Range | MillionVND |
| `AverageValue1Month` | Giá trị GD T.bình 20D | Range | MillionVND |
| `AverageValue3Month` | Giá trị GD T.bình 3M | Range | MillionVND |

### Chỉ tiêu FiinTrade — `FiinTradeIndicators`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `IcbRank` | FiinTrade Rank | Range | Rank |
| `Value` | Value (FiinTrade Score) | Value | Unit |
| `Growth` | Growth (FiinTrade Score) | Value | Unit |
| `Momentum` | Momentum (FiinTrade Score) | Value | Unit |
| `Vgm` | VGM (FiinTrade Score) | Value | Unit |
| `FScore` | F-Score (TTM) | Range | Rank |
| `Canslim` | Canslim (TTM) | Range | Rank |

### Chỉ số định giá thị trường — `MarketRatio`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `Rtd11` | Vốn hóa | Range | BillionVND |
| `Rtd21` | P/E (TTM) | Range | Unit |
| `Rtd26` | P/S (TTM) | Range | Unit |
| `Rtd25` | P/B (TTM) | Range | Unit |
| `Rtd28` | Giá - Dòng Tiền (TTM) | Range | Unit |
| `Rtd40` | Giá - Dòng Tiền Tự Do (TTM) | Range | Unit |
| `Rtd27` | Giá - T.sản hữu hình (TTM) | Range | Unit |
| `Rtd14` | EPS (TTM) | Range | Unit |

### Doanh thu & lợi nhuận — `RevenueProfit`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `RevTTM` | Doanh thu (tỉ đồng) (TTM) | Range | BillionVND |
| `Isa20TTM` | LN ròng (tỉ đồng) (TTM) | Range | BillionVND |
| `RevY` | Doanh thu (tỉ đồng) (năm trước) | Range | BillionVND |
| `Isa20Y` | LN ròng (tỉ đồng) (năm trước) | Range | BillionVND |
| `Rev` | Doanh thu (tỉ đồng) (quý gần nhất) | Range | BillionVND |
| `Prf` | Lợi nhuận ròng (tỉ đồng) (quý gần nhất) | Range | BillionVND |

### Chỉ số tăng trưởng — `GrowthRatio`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `Rtq78` | T.trưởng D.thu (YoY) | Range | Percentage |
| `Rtq79` | T.trưởng LN gộp (YoY) | Range | Percentage |
| `Rtq83` | T.trưởng LN ròng (YoY) | Range | Percentage |
| `Ryq160` | T.trưởng K.doanh 3 năm | Range | Percentage |
| `Ryq166` | T.trưởng LN ròng 3 năm | Range | Percentage |
| `Ryq176` | T.trưởng vốn CSH 3 năm | Range | Percentage |
| `Rtd52` | T.trưởng EPS (TTM) | Range | Percentage |
| `RevGrowth` | Tăng trưởng doanh thu quý gần nhất (YoY) | Range | Percentage |
| `PrfGrowth` | Tăng trưởng lợi nhuận thuần quý gần nhất (YoY) | Range | Percentage |

### Chỉ số khả năng sinh lời — `ProfitabilityRatio`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `Rtq12` | ROE (TTM) | Range | Percentage |
| `Rtq14` | ROA (TTM) | Range | Percentage |
| `Rtq25` | Biên LN gộp (TTM) | Range | Percentage |
| `Rqq25` | Biên LN gộp (quý) | Range | Percentage |
| `Ryq25` | Biên LN gộp (năm gần nhất) | Range | Percentage |
| `Rtq29` | Biên LN ròng (TTM) | Range | Percentage |
| `Rqq29` | Biên LN ròng (quý) | Range | Percentage |
| `Ryq29` | Biên LN ròng (năm gần nhất) | Range | Percentage |
| `Rtq27` | Biên EBIT (TTM) | Range | Percentage |
| `Rqq27` | Biên EBIT (quý) | Range | Percentage |
| `Rqq23` | ROIC (quý) | Range | Percentage |

### Cơ cấu tài chính — `EquityStructure`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `Rtq7` | Nợ phải trả/ Tổng tài sản (TTM) | Range | Unit |
| `Rtq6` | Nợ phải trả/ Vốn chủ sở hữu (TTM) | Range | Unit |
| `Rtq4` | Nợ dài hạn/ Vốn chủ sở hữu (TTM) | Range | Unit |
| `Rqq6` | Nợ phải trả/ Vốn chủ sở hữu (quý) | Range | Unit |

### Chỉ số thanh toán — `LiquidityRatio`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `Rtq3` | Tỉ suất thanh toán hiện hành (TTM) | Range | Unit |
| `Rtq2` | Tỉ suất thanh toán nhanh (TTM) | Range | Unit |
| `Rtq1` | Tỉ suất thanh toán tiền mặt (TTM) | Range | Unit |
| `Rtq77` | Khả năng chi trả lãi vay (TTM) | Range | Unit |

### Sở hữu — `Ownership`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `CorpOwnership` | Tỉ lệ tổ chức sở hữu | Range | Percentage |
| `ForeignerPercentage` | Sở hữu nước ngoài | Range | Percentage |
| `ForeignerRoom` | Room nước ngoài | Range | ThousandUnit |

### Cổ Tức — `Dividends`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `Rtd43` | Cổ Tức | Range | Unit |
| `Rtd36` | Tỉ Suất Cổ Tức | Range | Percentage |
| `Rtd20Avg` | Tỉ Suất Cổ Tức T.Bình 3 Năm | Range | Percentage |
| `Rtd51` | Tỉ Lệ Chi Trả Cổ Tức | Range | Percentage |

### Chỉ Số Kĩ Thuật — `TechnicalIndicators`

| Mã | Tên | Kiểu | Đơn vị |
|---|---|---|---|
| `Rsi` | RSI | Range | Unit |
| `Adx` | ADX | Range | Unit |
| `Cci` | CCI | Range | Unit |
| `Roc` | ROC | Range | Unit |
| `Stochastic` | STOCH | Range | Unit |
| `Williams` | Williams | Range | Unit |
| `Mfi` | MFI | Range | Unit |

---

## A.4 Cách dùng

1. Gọi `Screener/GetScreenerParameters?language=vi` một lần, cache kết quả.
2. Chuẩn hoá mã về chữ thường để tra: `Rtq12` → `rtq12`.
3. Với mã chỉ tiêu báo cáo tài chính (`bsa*`, `bsb*`, `bss*`, `bsi*`, `isa*`, `isb*`, `iss*`, `isi*`, `cfa*`, `cfb*`, `cfs*`, `cfi*`, `nob*`), tra ở **A.5** dưới đây.

Bảng A.3 phủ các mã xuất hiện trong `Snapshot`, `GetAllScore`, `GetValuation`, `GetCorporateEarning`.

---

## A.5 Từ điển đầy đủ — 729 mã

**Đo ngày 2026-08-14.** Bảng đầy đủ ở dạng máy đọc: [field-dictionary.json](field-dictionary.json) — **729 mã, 98,5% có tên tiếng Việt**.

> **Kiểm chứng độ phủ:** quét **21 response thật** trên BID · HPG · SSI · BVH · VNM, tổng **2.852 lần xuất hiện mã** — **không còn mã nào nằm ngoài từ điển**. Đây là điều kiện dừng: mọi mã mà API thực sự trả về đều tra được.

### Hai nguồn, hai họ mã

| Họ mã | Nguồn | Số mã | Có `unit`? |
|---|---|---:|---|
| `bs*` `is*` `cf*` `no*` — chỉ tiêu báo cáo tài chính | **Bundle JS ứng dụng FiinTrade** — không phải API | 556 | ❌ |
| `rt*` `rq*` `ry*` `rs*` — tỷ số và chỉ số thị trường | Bundle + `GetScreenerParameters` (83 mã có unit) | 173 | ⚠️ chỉ 83 |

Bảng dịch **tiếng Việt nằm ngay trong bundle** nhưng ở dạng escape unicode, nên tìm bằng chuỗi tiếng Việt sẽ không thấy — phải giải mã escape trước. Đây là lý do vòng dò đầu tiên tưởng nhầm rằng bundle chỉ có tên tiếng Anh.

```
https://staging-app-bvsc.fiintrade.vn/static/js/main.<hash>.chunk.js
```

⚠️ **Hash đổi theo mỗi lần FiinTrade deploy.** Đọc thuộc tính `src` của thẻ `<script>` trong HTML gốc để lấy tên file hiện hành, đừng hardcode đường dẫn.

### Phân bố chỉ tiêu báo cáo tài chính

| Báo cáo | Phi ngân hàng | Ngân hàng | Chứng khoán | Bảo hiểm |
|---|---:|---:|---:|---:|
| Cân đối kế toán | `bsa` 120 | `bsb` 26 | `bss` 47 | `bsi` 37 |
| Kết quả kinh doanh | `isa` 25 | `isb` 17 | `iss` 62 | `isi` 70 |
| Lưu chuyển tiền tệ | `cfa` 44 | `cfb` 35 | `cfs` 59 | `cfi` 10 |
| Ngoài bảng | `nob` 4 | | | |

Hậu tố xác định loại hình: `a` phi ngân hàng · `b` ngân hàng · `s` công ty chứng khoán · `i` bảo hiểm. Một doanh nghiệp chỉ được điền bộ mã ứng với loại hình của nó; các bộ còn lại là `null`.

### Ba chữ cái đầu quyết định kỳ báo cáo

Bundle chứa bảng `specialTtmKeysSwap` — **44 cặp** ánh xạ mã kỳ năm/quý về mã TTM tương ứng. Từ đó suy ra quy tắc chung:

> **Cùng chữ số + cùng chữ thứ ba (`d` hoặc `q`) = cùng chỉ tiêu, khác kỳ.**
> `rtq12` (TTM) · `rqq12` (quý) · `ryq12` (năm) đều là **ROE**.

Quy tắc này giải thêm được nhiều mã không có tên riêng trong bundle. Mã nào lấy tên theo cách này đều mang trường `suy_tu` trong JSON.

### Độ phủ trên response thật

| Endpoint | Trường | Là mã chỉ tiêu | Tra được |
|---|---:|---:|---:|
| `GetBalanceSheet` | 235 | 230 | **100%** |
| `GetIncomeStatement` | 180 | 175 | **100%** |
| `GetCashFlow` | 150 | 146 | **100%** |

Các trường còn lại không phải mã chỉ tiêu: `yearReport`, `quarterReport`, `organCode`, `ebit`, `ebitDa`, `operating`, `otherAssetBank`, `otherAssetNonBank`, `otherLiabilties` *(nguyên văn, thiếu chữ `i` — không phải lỗi gõ trong tài liệu này)*.

### Ba loại tên tiếng Việt — phân biệt rõ nguồn gốc

Độ phủ **718/729 (98,5%)**, nhưng không phải tên nào cũng cùng độ tin cậy:

| Loại | Số mã | Đánh dấu trong JSON |
|---|---:|---|
| **Tên gốc FiinGroup** — từ bundle hoặc API | 703 | *(mặc định)* |
| **Bản dịch** — tôi dịch từ viết tắt tiếng Anh | 12 | `ten_vi_la_ban_dich: true` |
| **Suy luận** — xác định bằng đối chiếu số học | 3 | `ten_vi_la_suy_luan: true` + `bang_chung` |
| **Chưa có tên** | 11 | `trang_thai: chua-giai-ma` |

🔴 **12 mã có trường `ten_vi_la_ban_dich` không phải tên chính thức của FiinGroup.** Bundle chỉ có viết tắt tiếng Anh (`NIM %`, `ROIC`, `BVPS`), tôi dịch theo thuật ngữ kế toán chuẩn. Nếu FiinGroup về sau cung cấp tên chính thức thì thay thế:

| Mã | Bundle ghi | Bản dịch |
|---|---|---|
| `rqq72` | `EBIT` | Lợi nhuận trước lãi vay và thuế (EBIT) |
| `rsd7` | `BVPS` | Giá trị sổ sách trên mỗi cổ phiếu (BVPS) |
| `rsd14` | — | Lãi cơ bản trên cổ phiếu (EPS) |
| `rsd28` | *(suy từ `rtd28`)* | Giá trên dòng tiền (P/CF) |
| `rsi14` | `Rsi14` | Chỉ báo sức mạnh tương đối 14 phiên (RSI 14) |
| `rsq12` | `ROE %` | Tỷ suất lợi nhuận trên vốn chủ sở hữu (ROE) |
| `rsq14` | `ROA %` | Tỷ suất lợi nhuận trên tổng tài sản (ROA) |
| `rsq44` `rtq44` `ryq44` | `NIM %` | Biên lãi thuần (NIM) |
| `rsq76` `ryq76` | `ROIC` | Tỷ suất lợi nhuận trên vốn đầu tư (ROIC) |

### Viết tắt trong `ten_vi` không phải là thiếu sót

17 mã có `ten_vi` là viết tắt — `P/E (TTM)`, `ROE (TTM)`, `Beta`, `ADX`, `% Free Float`… Đây là **tên chính thức từ API với `language=vi`**: ngành tài chính Việt Nam dùng nguyên viết tắt, không dịch. Chúng được bổ sung trường `ten_vi_day_du` để chatbot hiểu nghĩa, **không thay thế** `ten_vi`.

### 🔴 Nhãn `unit` của API KHÔNG phải đơn vị của dữ liệu

Phát hiện ngày 2026-08-14, đo trên 19 doanh nghiệp thuộc 4 loại hình. Đây là bẫy nghiêm trọng nhất của từ điển:

| Mã | Nhãn `unit` | Giá trị thật quan sát | Đơn vị thật |
|---|---|---|---|
| `rtq12` ROE | `Percentage` | 0,098 – 0,339 | **thập phân** — phải ×100 mới ra % |
| `rtd11` Vốn hoá | `BillionVND` | 2,03e12 – 4,99e14 | **VND đầy đủ**, không phải tỷ đồng |
| `foreignerRoom` | `ThousandUnit` | 8.127 – 2,3e9 | **cổ phiếu**, không phải nghìn cổ phiếu. ⚠️ Là room **CÒN LẠI** (= `foreignRemain` của BVSC), không phải tổng room — đo 2026-08-15, xem [§getScreenerItems](10-fiin-dictionary.md#ghi-chú-1) |
| `rtd14` EPS | `Unit` | 1.308 – 6.666 | **VND/cổ phiếu** |

Hiển thị `0.1821` với nhãn `Percentage` thành *"0,18%"* là **sai 100 lần** — con số thật là 18,21%.

> Nhãn `unit` chỉ đúng trong ngữ cảnh **bộ lọc Screener**, nơi nó mô tả cách hiển thị thanh trượt. Nó không mô tả dữ liệu mà các endpoint khác trả về. Tài liệu đã ghi bẫy tương tự cho `getScreenerItems` (⚠️ *"Thang đơn vị theo dữ liệu thô, không theo `unit`"*) — nay xác nhận nó áp dụng cho **mọi** endpoint.

Vì vậy từ điển có hai trường tách bạch: `don_vi` giữ nguyên nhãn API (chỉ dùng khi làm việc với Screener), và **`don_vi_du_lieu` là đơn vị thật, luôn dùng cái này**.

### Đơn vị dữ liệu — 727/729 mã (99,7%)

| Đơn vị | Số mã | Nghĩa |
|---|---:|---|
| `VND` | 582 | Số tiền đầy đủ, không phải nghìn/triệu/tỷ đồng |
| `ty_le_thap_phan` | 80 | **Nhân 100 mới ra phần trăm.** `0.1821` = 18,21% |
| `lan` | 46 | Số lần, bội số, điểm số — không có đơn vị tiền |
| `VND/CP` | 10 | Đồng trên mỗi cổ phiếu |
| `co_phieu` | 8 | Số lượng cổ phiếu |
| `so_luong` | 1 | Số đếm (số công ty trong ngành) |
| *chưa xác định* | 2 | `rsq148`, `ryd20` |

**Cách xác định, không phải phỏng đoán:** tên chỉ tiêu quyết định trước, dải giá trị thật trên 19 doanh nghiệp dùng để **xác nhận**; họ mã báo cáo tài chính luôn là VND. Bộ phân loại được **kiểm chứng trên 19 mã có đơn vị biết trước — đúng 19/19** trước khi áp cho phần còn lại. Mỗi mã mang `don_vi_ly_do` và `don_vi_do_tin_cay` — **392 mã đã xác thực bằng bằng chứng số học, 308 mức cao, 27 mức trung bình**.

### Xác thực đơn vị bằng đẳng thức kế toán

Suy đơn vị từ dải giá trị vẫn là suy luận. Sáu phép kiểm sau **neo nó vào bằng chứng số học**, chạy ngày 2026-08-14:

| Phép kiểm | Kết quả | Chứng minh điều gì |
|---|---|---|
| `bsa1 + bsa23 = bsa53` *(TSNH + TSDH = tổng tài sản)* | **8/8** — khớp chính xác từng chữ số | Mọi mã trong báo cáo tài chính dùng **chung một đơn vị** |
| `bsa53 = bsa96` *(tổng tài sản = tổng nguồn vốn)* | **8/8** | Đẳng thức kế toán cơ bản đúng → dữ liệu nhất quán |
| `rtd11 ÷ số cổ phiếu` = giá cổ phiếu | **8/8** — ra 21.700 đến 77.900 đ | `rtd11` là **VND đầy đủ**. Nếu là tỷ đồng thì giá ra 0,00002 đ — vô lý |
| `rtd14 (EPS) × số cổ phiếu` = LNST 4 quý | **7/8** | `isa20` là VND, `rtd14` là VND/cổ phiếu |
| `bsa78 ÷ số cổ phiếu` = `rtd7` (BVPS) | **6/8** — hai ca lệch do lợi ích cổ đông thiểu số | `bsa78` là VND, `rtd7` là VND/cổ phiếu |
| `rtd14 ÷ rtd7` (EPS/BVPS) = `rtq12` (ROE) | **10/10** | `rtq12` là **thập phân**. Nếu là phần trăm thì giá trị phải là 17,4 thay vì 0,1738 |

Hai phép đầu chứng minh nhóm báo cáo tài chính **cùng một đơn vị**; bốn phép sau **gắn đơn vị đó vào VND cụ thể**. Vì vậy đơn vị của nhóm báo cáo tài chính không còn là suy luận thuần.

Nhưng sáu phép đó mới phủ 10 mã. Để phủ toàn bộ, thêm một phép kiểm chạy trên **138 bảng dữ liệu của 25 doanh nghiệp**:

### Kiểm nhất quán thang — phủ mọi mã báo cáo tài chính

Với mỗi mã, tính tỷ lệ giá trị so với tổng tài sản của cùng doanh nghiệp. Mã nào dùng thang khác (nghìn/triệu/tỷ đồng) sẽ **lệch bội số 1000 và lộ ra ngay**.

**Kết quả: 390/393 mã cùng thang** — không mã nào lệch bội số 1000.

Và ba mã lộ ra thì **đều đúng, hai trong số đó là lỗi của từ điển này**:

| Mã | Tên | Từ điển ghi | Thực tế |
|---|---|---|---|
| `isa23` | Lãi cơ bản trên cổ phiếu | ~~VND~~ | **VND/CP** — đã sửa |
| `isa24` | Lãi trên cổ phiếu pha loãng | ~~VND~~ | **VND/CP** — đã sửa |
| `rtq29` | Biên Lãi Thuần | `ty_le_thap_phan` | ✅ đúng từ đầu |

Lỗi do luật *"họ mã báo cáo tài chính luôn là VND"* ghi đè lên tên chỉ tiêu. Quét lại theo tên còn tìm thêm `iss167` cùng loại lỗi. **Phép kiểm không chỉ xác nhận mà còn bắt lỗi** — đó là lý do nên đưa nó vào bộ giám sát chạy hằng ngày.

Phân bố cuối: **392 xác thực · 308 cao · 27 trung bình**.

> ⚠️ **Dữ liệu Screener phủ toàn thị trường nên chứa giá trị cực trị.** Suy đơn vị bằng ngưỡng dải giá trị sẽ thất bại trên đó — phải dựa vào tên chỉ tiêu trước. Ví dụ `Rtq29` (Biên LN ròng) có `valueRange = [-524, 756]`, tức tới 75.600% ở doanh nghiệp lỗ nặng; luật *"max ≤ 5 thì là tỷ lệ"* gãy ngay.
>
> **Screener KHÔNG dùng thang đơn vị khác** — điều này đã kiểm bằng chính `valueRange` của API: `ClosePrice = [100, 614345]` là VND đầy đủ, `Rtq12` (ROE) `= [-127.56, 7.86]` là thập phân, giống hệt các endpoint khác.

### Ba mã xác định được bằng đối chiếu số học

Không có tên ở bất kỳ nguồn nào, nhưng **quan hệ số học trên dữ liệu thật xác định được vai trò**. Đánh dấu `ten_vi_la_suy_luan: true`, kèm `bang_chung` và `do_tin_cay`.

**`isi180` = Chi phí kinh doanh bất động sản đầu tư** · *độ tin cậy cao*

Bộ ba `isi178` `isi179` `isi180` thoả `isi178 = isi179 + isi180` đúng **32/32 kỳ** trên BVH, BMI, PVI, PTI. Đã biết `isi179` = *Doanh thu kinh doanh BĐS đầu tư* và `isi178` = *Lợi nhuận từ hoạt động đầu tư BĐS*, nên `isi180` chỉ có thể là chi phí — và nó ghi số âm, khớp.

**`cfb71` = Tiền thu từ phát hành giấy tờ có giá dài hạn và vốn vay dài hạn khác**
**`cfb72` = Tiền chi thanh toán giấy tờ có giá dài hạn và vốn vay dài hạn khác** · *độ tin cậy khá*

Ba bằng chứng cùng chỉ một hướng: **vị trí** — nằm giữa `cfa27` *(thu từ phát hành cổ phiếu)* và `cfa32` *(cổ tức đã trả)*, đúng chỗ hai dòng này trong mẫu B03/TCTD; **dấu** — `cfb71` dương (thu), `cfb72` âm (chi); **tổng** — `cfa27 + cfb71 + cfb72 + cfa32 + cfb73 + cfb74 = cfa34` khớp chính xác trên BID.

Yếu hơn `isi180` ở chỗ phép tổng xác nhận chúng thuộc nhóm tài chính nhưng không tự nó chốt được tên; tên lấy theo mẫu báo cáo chuẩn.

### 11 mã còn thiếu tên — không suy được

`nob44` `nob65` `nob66` · `rqq41` · `rtd35` `rtd53` `rtq81` `rtq137` `rtq180` · `ryd20` `ryd30`

Đã thử **năm cách**, đều không cho kết luận chắc chắn:

1. Tìm tên trong bundle — không có
2. Suy từ mã cùng chỉ tiêu khác kỳ — không mã họ hàng nào có tên
3. Đối chiếu **bằng nhau** với toàn bộ chỉ tiêu đã biết tên trên 4 loại hình (188–395 trường mỗi mã) — không giá trị nào trùng
4. Tìm quan hệ **tỷ lệ ổn định** với mọi chỉ tiêu đã biết, trên **144 hàng dữ liệu** — không tỷ lệ nào có độ lệch chuẩn dưới 2%
5. Đối chiếu với chỉ tiêu ngành tương ứng — ví dụ `rtq137` với `ryq58` *(Tỷ lệ Nợ Xấu)*: lệch ở 3/5 ngân hàng

Mỗi mã nay mang `dai_gia_tri_quan_sat` và phần lớn có `manh_moi` trong JSON, để lần sau khỏi đo lại. Những manh mối đáng chú ý nhất:

| Mã | Quan sát được | Vì sao chưa đủ để ghi |
|---|---|---|
| `rtd53` | Luôn **nhỏ hơn** `rtd14` (EPS) ở mọi doanh nghiệp phi ngân hàng, tỷ lệ 0,40–0,95. Ngân hàng = 0 | Tỷ lệ không ổn định nên không phải EPS pha loãng. Có thể là *lợi nhuận cốt lõi trên cổ phiếu* |
| `rtq137` | Chỉ ngân hàng có. 0,47%–2,23%, luôn nhỏ hơn NIM. Rất sát tỷ lệ nợ xấu thực tế của 5 ngân hàng lớn | Đối chiếu `ryq58` lệch ở 3/5 ngân hàng |
| `rtq180` | Tiền, 8,2e10–2,2e14, **có giá trị âm** (SSI) | Giả thuyết *nợ ròng* đã tính ra và không khớp trên cả 4 doanh nghiệp |
| `rtd35` | 0,0065–1,23, không âm — dải điển hình của **Beta** | `rtd19` đã là Beta; chưa rõ khác nhau ở khung thời gian nào |
| `ryd30` | 5,56–23,65, có âm — dải của một hệ số định giá | Ánh xạ về `rtd30`, mà `rtd30` cũng chưa biết tên |

Không ghi tên cho nhóm này vì đoán sẽ là bịa — và bịa trong từ điển nguy hiểm hơn để trống, vì chatbot sẽ đọc sai dòng báo cáo mà không ai biết. Danh sách ngắn, gửi kèm được khi trao đổi với FiinGroup về rate limit.
