# Yahoo Finance — Chỉ số quốc tế, lợi suất, biến động

**Phiên bản:** 1.0 · **Ngày khảo sát:** 2026-08-15, đo lại 2026-09-05 (lát 7, 7b) · **Trạng thái:** 58 lời gọi thật, Yahoo trả `200` trên 44/44, trung vị **163 ms**, không bị chặn từ Việt Nam

> **Vai của nguồn này — đúng một vai.** Yahoo là **nguồn CHÍNH cho chỉ số chứng khoán quốc tế**: 36 chỉ số / 21 nước, lịch sử tới 1927, trễ 0 ngày *(đo 2026-08-15)*. Kèm theo là lợi suất TPCP Mỹ, họ biến động, ETF quốc gia, và **vai dự phòng cho tỷ giá** *(nguồn chính là Frankfurter — xem [`fx.md`](fx.md))*.
>
> 🔴 **Không dùng Yahoo làm nguồn chính cho dữ liệu Việt Nam.** Ranh giới ở [mục 6](#6-ranh-giới--yahoo-không-được-dùng-làm-gì).

> ⚠️ **Ba bẫy ở [mục 2](#2--ba-bẫy-cấu-trúc--đều-làm-hỏng-dữ-liệu-mà-không-báo-lỗi) làm hỏng dữ liệu ÂM THẦM** — HTTP vẫn `200`, không cờ, không cảnh báo. Đọc mục 2 trước khi viết dòng code đầu tiên.

Mọi con số trong file này đến từ đợt khảo sát **2026-08-15**. Chỗ nào chưa đo thì ghi **"chưa kiểm"**.

Quy ước chung của bộ tài liệu nguồn *(đánh dấu bẫy, đơn vị, múi giờ)*: [`../market/00-conventions.md`](../market/00-conventions.md).

---

## 1. Đặc tả API

### 1.1 Endpoint

| Đường dẫn | Dùng cho | Chi phí |
|---|---|---|
| `v8/finance/chart/{symbol}` | Nến lịch sử + `meta` — **endpoint chính, dùng cho gần như mọi việc** | 1 request / mã |
| `v7/quote` | Ảnh chụp nhiều mã **theo lô** | 1 request / **180 mã** |
| `v1/test/getcrumb` | Lấy `crumb` cho luồng xác thực | — |

**Host** *(đo 2026-09-05, khi dựng ETL lát 7)*: `https://query1.finance.yahoo.com` và `https://query2.finance.yahoo.com` đều trả `200` cho `v8/finance/chart`, cùng body; ETL dùng `query1`. Không có ETag. *(Sổ đo 2026-08-15 chỉ ghi đường dẫn, không ghi host.)*

🔴 **Hợp đồng đổi so với 2026-08-15** *(đo 2026-09-05, 39 mã)*: `meta` **không còn `quoteType`**; cờ chết nay ở **`meta.instrumentType`** (`TIO=F` → `ALTSYMBOL`, chỉ số → `INDEX`). Cổng 3 ở [mục 8](#8-bộ-giám-sát-hợp-đồng--ba-cổng-bắt-buộc) kiểm cả hai khoá. Cùng đợt đo: **cửa sổ `period1 = now − 40 ngày` trả đúng 1 nến** (nến hiện tại) ở `^SET.BK` và `PSEI.PS`, trong khi 400 ngày trả 272/286 nến và 3.000 ngày trả 1.999/2.144 — cùng họ Bẫy 3, ETL dùng cửa sổ **400 ngày**; `^MERV` trả **`currency: ""`**. Cùng họ: cửa sổ **5 ngày** của lượt `--intraday` (lát 7b) cũng trả **1 nến** ở `^SET.BK`/`PSEI.PS` *(đo 2026-09-05)* — xem §5.5.

🔴 **Đây là API nội bộ của Yahoo: không tài liệu, không cam kết, không phiên bản.** Khác hẳn Frankfurter *(mã nguồn mở, tự dựng lại được)*. Mọi thiết kế phải giả định endpoint có thể đổi hình mà không báo trước — xem bộ giám sát ở [mục 8](#8-bộ-giám-sát-hợp-đồng--ba-cổng-bắt-buộc).

### 1.2 Tham số của `v8/finance/chart`

| Tham số | Giá trị dùng | Ghi chú |
|---|---|---|
| `period1` / `period2` | epoch **giây** | ✅ **Cách gọi duy nhất được phép cho lịch sử.** `period1` phải **ÂM** — xem Bẫy 1 |
| `interval` | `1d` | Luôn phải đối chiếu lại với `meta.dataGranularity` — xem Bẫy 2 |
| `range` | ❌ **không dùng** | `range=max` bị hạ ngầm về nến tháng — xem Bẫy 2 |

### 1.3 Cấu trúc response — các trường phải đọc

| Trường | Vai trò |
|---|---|
| `meta.dataGranularity` | 🔴 **Cổng kiểm bắt buộc.** Phải khớp `interval` đã xin; lệch là **lỗi cứng**, không phải cảnh báo |
| `meta.instrumentType` *(2026-08-15 là `meta.quoteType`; đổi tên đo 2026-09-05)* | 🔴 **Cờ chết im lặng.** `ALTSYMBOL` ⇒ mã đã ngừng — xem [mục 3](#3--chết-im-lặng--mã-đã-ngừng-vẫn-trả-200-kèm-giá-hợp-lệ) |
| `meta.regularMarketTime` | 🔴 Cổng kiểm độ tươi. So với **lịch phiên của sàn đó, theo múi giờ sàn đó** |
| `meta.firstTradeDate` | Độ sâu lịch sử. **Nói thật — nghiệm 6/6** *(đo 2026-08-15, xem §4.3)* |
| `meta.currency` | ⚠️ Có mã trả `USX` = **cent Mỹ**, không phải USD — xem §5.7 |
| `meta.exchange` / `fullExchangeName` | Sàn niêm yết |

**Giá trị thiếu = `null` trong mảng, không bỏ dòng.** Mảng thời gian và mảng giá luôn cùng độ dài — parser giữ nguyên vị trí, không nén.

### 1.4 Xác thực

| Endpoint | Đo được 2026-08-15 |
|---|---|
| `v8/finance/chart` | ✅ **Không cần xác thực.** 58 lời gọi bằng `requests` **thuần**, không cookie, không crumb → 44/44 `200` |
| `v7/finance/quote` | 🔴 Trả **`401`** khi không có cookie + crumb *(gặp khi hỏi trường NAV của `VOF.L`)* |

Luồng xác thực khi cần: lấy cookie `A3` từ `fc.yahoo.com` *(host này **trả `404` nhưng vẫn set cookie**)* → gọi `v1/test/getcrumb`.

⚠️ **Chưa kiểm:** lô 180 mã qua `v7/quote` có qua được **không** xác thực hay không. Ngân sách ở [mục 7](#7-ngân-sách-lời-gọi-và-hiệu-năng) giả định lô chạy được — phải xác nhận trước khi vào sản xuất.

⚠️ **Tín hiệu chống bot đang leo thang, nhưng đọc cho đủ ba vế** *(đo 2026-08-15)*:

1. `curl_cffi` *(thư viện giả vân tay TLS)* đã thành **bắt buộc** trong `requires_dist` của `yfinance` 1.6.0 ⇒ Yahoo có chặn theo vân tay TLS.
2. **Nhưng** toàn bộ 58 lời gọi khảo sát dùng `requests` thuần và đạt 44/44 `200` ⇒ hôm nay, từ IP này, **chưa bị chặn**.
3. **Và** bản `yfinance` 0.2.54 *(phát hành 2025-02, cũ 18 tháng)* vẫn chạy tốt ⇒ **giao thức Yahoo ổn định hơn nhiều** so với ấn tượng "đang bị chặn gắt".

Nhịp đã dùng khi khảo sát: **tuần tự, một luồng, nghỉ ≥ 1,10 s giữa hai lời gọi**. Không dò ngưỡng chặn — đây là chủ đích.

---

## 2. 🔴 Ba bẫy cấu trúc — đều làm hỏng dữ liệu mà KHÔNG báo lỗi

Ba bẫy này quan trọng hơn mọi mục còn lại của file. Cả ba đều trả `HTTP 200`, không cờ, không cảnh báo — **dữ liệu sai lặng lẽ đi thẳng vào kho**. Controller đã kiểm chứng lại độc lập: **đúng cả ba** *(11 lời gọi, 2026-08-15)*.

### Bẫy 1 — `period1=0` cắt câm lịch sử ở 1970

| Cách gọi `^GSPC` | Số nến | Bắt đầu |
|---|---:|---|
| `period1=0` | 14.276 | 1970-01-02 |
| `period1=-2208988800` | **24.772** | **1927-12-30** |

**Mất 10.496 nến = 42 năm.** Không có cờ nào báo. `dataGranularity` vẫn `1d`, HTTP vẫn `200`.

Nguyên nhân: `0` là epoch 1970-01-01, không phải "từ đầu". Ai coi `0` là "lấy hết" sẽ mất toàn bộ lịch sử trước 1970 mà không hề biết.

> ### ➜ Luật 1
> **Mọi lời gọi lịch sử phải dùng `period1` ÂM.** Không bao giờ dùng `period1=0`.

### Bẫy 2 — `range=max&interval=1d` bị hạ ngầm về nến THÁNG

| Cách gọi `VNM.VN` | `dataGranularity` trả về | Số nến |
|---|---|---:|
| `range=max&interval=1d` | 🔴 **`1mo`** | 173 |
| `period1`/`period2` + `interval=1d` | ✅ `1d` | **3.730** |

Yahoo **nhận** `interval=1d` rồi **trả** nến tháng, và chỉ khai điều đó trong `meta.dataGranularity`. Không lỗi, không cảnh báo.

**Bẫy này đã suýt tạo ra một kết luận sai công bố được:** trong đợt đo, agent định công bố *"Yahoo lệch BVSC 3,4%"* — thực chất đang **so nến tháng với nến ngày**. Gọi lại đúng cách: lệch **0,0000%**.

> ### ➜ Luật 2
> **Không dùng `range=`.** Luôn dùng `period1`/`period2`.
> **Luôn kiểm `meta.dataGranularity` khớp cái mình xin — lệch là lỗi cứng, dừng ghi kho.**

### Bẫy 3 — `404` KHÔNG có nghĩa là mã không tồn tại

| Lời gọi `0P0000HY8X.VN` *(VN-Index)* | Kết quả |
|---|---|
| `range=5d` | 🔴 **`404`** |
| `period1`/`period2` | ✅ `200`, **1.698 nến** |
| `range=1mo` | ✅ `200` |

Cùng một mã, cùng một ngày. `404` ở đây nói về **tổ hợp tham số**, không nói về mã.

> ### ➜ Luật 3
> Gặp `404` **phải thử lại bằng `period1`/`period2`** trước khi kết luận mã chết. Kết luận "mã không tồn tại" chỉ được rút ra sau khi cách gọi đúng cũng hỏng.

---

## 3. 🔴 Chết im lặng — mã đã ngừng vẫn trả `200` kèm giá hợp lệ

Yahoo có **đúng kiểu hỏng của akshare**: mã ngừng cập nhật từ nhiều năm trước vẫn trả `HTTP 200` với giá trông hoàn toàn hợp lệ.

| Mã | Tên | Mốc cuối THẬT | Đã chết | `quoteType` |
|---|---|---|---:|---|
| **`^BCOM`** | Bloomberg Commodity | 2020-05-28 | **2.269 ngày** | `INDEX` |
| `TIO=F` | Quặng sắt 62% Fe | 2021-08-10 | ~1.830 ngày | `ALTSYMBOL` |
| `MTF=F` | Than API2 CIF ARA | 2025-02-06 | ~554 ngày | `ALTSYMBOL` |
| `RU=F` | **Rúp Nga** *(không phải cao su)* | 2020-08-21 | ~2.184 ngày | `ALTSYMBOL` |
| `LBS=F` | Lumber *(hợp đồng cũ)* | 2023-04-10 | ~1.222 ngày | `ALTSYMBOL` |

*(đo 2026-08-15 — số ngày chết tính tới ngày đo; cột `quoteType` nay là `instrumentType`, đo lại 2026-09-05: `TIO=F` vẫn `ALTSYMBOL`, `^BCOM` vẫn `INDEX` với `regularMarketTime` 2020-05-28 và 0 nến trong cửa sổ 40 ngày)*

### Hai quy tắc nhận biết — nghiệm đúng 5/5

1. **`instrumentType == "ALTSYMBOL"` ⇒ mã đã ngừng.** Chặn cứng. *(Trước 2026-09-05 khoá tên `quoteType`; ETL kiểm cả hai.)*
2. **Luôn so `regularMarketTime` với lịch phiên** của sàn đó, theo múi giờ sàn đó.

⚠️ **Quy tắc 2 là quy tắc không thể bỏ.** `^BCOM` khai `quoteType: "INDEX"` — "sạch" về kiểu, quy tắc 1 không bắt được. **Chỉ mốc thời gian tố cáo nó.**

### So với akshare — khác biệt quyết định

| | akshare | **Yahoo** |
|---|---|---|
| Kiểu hỏng | 🔴 im lặng, `200` | 🔴 im lặng, `200` |
| **Có cờ nhận biết từ response?** | ❌ **không** | ✅ **có:** `ALTSYMBOL` + `regularMarketTime` + `dataGranularity` |
| Commit `fix` trong 50 commit gần nhất | 58% | **26%** |
| Ổn định giao thức | 1 interface gãy / 2–3 ngày | ✅ bản cũ 18 tháng vẫn chạy |

🔵 **akshare hỏng im lặng KHÔNG phát hiện được từ response; Yahoo thì CÓ THỂ.** Rủi ro thấp hơn akshare một bậc — **với điều kiện dựng cổng kiểm** ở [mục 8](#8-bộ-giám-sát-hợp-đồng--ba-cổng-bắt-buộc).

---

## 4. Bản đồ phủ — 36 chỉ số / 21 nước

Đây là **sản phẩm chính** của nguồn này: khối "bối cảnh toàn cầu" trước nay bỏ trống.

**36/37 mã thử được, 21 nước, 100% trễ 0 ngày** *(đo 2026-08-15)*. Cột "trễ" so với phiên 2026-08-14, tính theo **múi giờ chính sàn đó**, không phải UTC.

### 4.1 Châu Á — Thái Bình Dương — 16/17

| Mã | Chỉ số | Thị trường | Lịch sử từ |
|---|---|---|---|
| `^N225` | Nikkei 225 | Nhật | **1965** |
| `^HSI` | Hang Seng | Hồng Kông | 1986 |
| `^STI` | Straits Times | Singapore | 1987 |
| `PSEI.PS` | PSEi | Philippines | 1987 |
| `^JKSE` | Jakarta Composite | Indonesia | 1990 |
| `^AXJO` | S&P/ASX 200 | Úc | 1992 |
| `^HSCE` | Hang Seng China Ent | Hồng Kông | 1993 |
| `^KLSE` | KLCI | Malaysia | 1993 |
| `^KS11` | KOSPI | Hàn Quốc | 1996 |
| `^SET.BK` | SET | Thái Lan | 1996 |
| `^BSESN` | SENSEX | Ấn Độ | 1997 |
| `^TWII` | TAIEX | Đài Loan | 1997 |
| `000001.SS` | Thượng Hải Composite | Trung Quốc | 1997 |
| `399001.SZ` | Thâm Quyến Component | Trung Quốc | 1997 |
| `^NZ50` | S&P/NZX 50 | New Zealand | 2003 |
| `^NSEI` | NIFTY 50 | Ấn Độ | 2007 |

🔴 **`^KOSPI` KHÔNG tồn tại trên Yahoo — phải dùng `^KS11`.** Đây là mã 1/17 bị hụt của nhóm châu Á. Ai gõ theo tên chỉ số sẽ nhận `404` và tưởng Yahoo không có Hàn Quốc.

### 4.2 Âu — Mỹ — 20/20

| Mã | Chỉ số | Thị trường | Lịch sử từ |
|---|---|---|---|
| `^GSPC` | S&P 500 | Mỹ | **1927-12-30** |
| `^IXIC` | NASDAQ Composite | Mỹ | 1971 |
| `^GSPTSE` | S&P/TSX | Canada | 1979 |
| `^FTSE` | FTSE 100 | Anh | 1984 |
| `^GDAXI` | DAX | Đức | 1987 |
| `^RUT` | Russell 2000 | Mỹ | 1987 |
| `^FCHI` | CAC 40 | Pháp | 1990 |
| `^SSMI` | SMI | Thuỵ Sĩ | 1990 |
| `^BFX` | BEL 20 | Bỉ | 1991 |
| `^MXX` | IPC | Mexico | 1991 |
| `^DJI` | Dow Jones | Mỹ | **1992** ⚠️ |
| `^AEX` | AEX | Hà Lan | 1992 |
| `^TA125.TA` | TA-125 | Israel | 1992 |
| `^IBEX` | IBEX 35 | Tây Ban Nha | 1993 |
| `^BVSP` | Bovespa | Brazil | 1993 |
| `^MERV` | MERVAL | Argentina | 1996 |
| `FTSEMIB.MI` | FTSE MIB | Ý | 1997 |
| `^N100` | Euronext 100 | Châu Âu | 1999 |
| `^STOXX50E` | EURO STOXX 50 | Khu vực đồng euro | 2007 |
| `^OMX` | OMX Stockholm 30 | Thuỵ Điển | 2008 |

⚠️ **`^DJI` chỉ từ 1992 — nông hơn `^GSPC` 65 năm.** Cần chuỗi Mỹ dài thì dùng `^GSPC`, không dùng `^DJI`.

🔵 **Vai so với FiinTrade:** chỉ số quốc tế ở FiinTrade chỉ có **3 mã** *(`DJI`/`NASDAQ`/`N225`)*. Yahoo cho **36 mã, sâu hơn nhiều** ⇒ Yahoo là nguồn chính, FiinTrade làm đối chứng.

### 4.3 `firstTradeDate` có nói thật không — nghiệm 6/6 ✅

`^GSPC` khai `firstTradeDate` = 1927-12-30 → tải thật về đúng **1927-12-30**, **24.772 nến**, **0,00% nến rỗng**. `^N225`, `^GSPTSE`, `^HSI`, `^KS11`, `^SET.BK` đều khớp *(đo 2026-08-15)*.

➜ **Dùng `firstTradeDate` làm chỉ dẫn độ sâu mà không phải tải toàn bộ chuỗi.** Tiết kiệm được một vòng tải thăm dò cho mỗi mã.

---

## 5. Các khối khác lấy được

### 5.1 Lợi suất TPCP Mỹ — chất lượng ngang FRED, tươi hơn một ngày

| Mã | Kỳ hạn |
|---|---|
| `^TNX` | 10 năm — **14.174 nến từ 1962-01-02** |
| `^TYX` | 30 năm |
| `^FVX` | 5 năm |
| `^IRX` | 13 tuần |

Múi giờ khai báo: `America/Chicago`.

**Đối chiếu `^TNX` với FRED `DGS10`** *(đo 2026-08-15)*:

| Chỉ tiêu | Kết quả |
|---|---:|
| Số ngày trùng | 54 |
| **Lệch tuyệt đối trung bình** | **0,0091 điểm %** *(~0,9 điểm cơ bản)* |
| Lệch lớn nhất | 0,048 điểm % |
| Số ngày lệch > 0,01 điểm % | 16/54 |
| Độ tươi | 🔵 **Yahoo tươi hơn** — 2026-08-14 vs FRED 2026-08-13 |

➜ `^TNX` **dùng được làm nguồn chính hoặc dự phòng** cho lợi suất TPCP Mỹ. Chi tiết phía FRED: [`fred.md`](fred.md).

⚠️ Ghi nhận: `^VIX` và `^TNX` mang `exchange: "CGI"` — **vẫn là dữ liệu CBOE**. Đổi cửa vào không đổi chủ sở hữu dữ liệu. *(Quan sát, không phải phân tích pháp lý.)*

### 5.2 Biến động và hàng hoá tổng hợp — khối dự án chưa có

| Mã | Đo lường | Lịch sử từ |
|---|---|---|
| 🔵 `^MOVE` | Biến động trái phiếu *(ICE BofA)* — stress thị trường TPCP | 2002-11 |
| 🔵 `^SPGSCI` | Hàng hoá tổng hợp *(S&P GSCI)* | **1984-01** |
| `^SOX` | Bán dẫn Philadelphia | 1994 |
| `^VXN` | Biến động NASDAQ | *chưa ghi* |
| `^OVX` | Biến động giá dầu | *chưa ghi* |
| `^GVZ` | Biến động giá vàng | *chưa ghi* |
| `^SKEW` | Rủi ro đuôi S&P 500 | *chưa ghi* |
| `^VVIX` | Biến động của VIX | *chưa ghi* |

🔵 **`^SOX` lấy ở Yahoo, bỏ akshare** — cùng chỉ số, Yahoo không có kiểu hỏng im lặng không phát hiện được của akshare.

### 5.3 ETF quốc gia và ETF Việt Nam

**ETF quốc gia** *(có đủ, đo 2026-08-15)*:
`EWJ` `EWY` `EWT` `EWH` `EWS` `EWM` `THD` `EIDO` `INDA` `EWZ` `EWW` `EWU` `EWG` `EWQ` `EWA` `EWC` `FXI` `MCHI`

🔵 **`VNM` — VanEck Vietnam ETF, từ 2009-08.** Proxy **dòng tiền ngoại vào Việt Nam** — khối dự án chưa có nguồn nào khác.

### 5.4 Quỹ Việt Nam niêm yết nước ngoài — lịch sử rất sâu

| Mã | Quỹ | Sàn | Số phiên | Từ | Giá *(đo 2026-08-15)* |
|---|---|---|---:|---|---|
| **`VOF.L`** | **VinaCapital Vietnam Opportunity Fund** | London | **5.799** | **2003-09-30** | 442,5 GBp |
| `1VV.F` | *(cùng quỹ, niêm yết Frankfurt)* | Frankfurt | 2.642 | 2016-03-23 | 5,12 EUR |
| `KPHO` | KraneShares Dragon Capital Vietnam Growth ETF | Mỹ | 174 | 2025-12-04 | 22,39 USD |

Thêm: `1VV.MU` *(Munich)* · `VCVOF` *(OTC Mỹ)* · `FUEVN100.VN`.

**`VOF.L` là mục đáng giá nhất: 23 năm lịch sử liên tục** — quỹ đóng lớn ở London chuyên đầu tư Việt Nam.

⚠️ **Chưa kiểm: Yahoo có trả NAV của `VOF.L` không, hay chỉ có giá.** Rào cản đã xác định chính xác — `v7/finance/quote` trả **`401`** khi không có cookie + crumb; đây **không phải** "không có NAV" mà là **chưa qua cửa xác thực**. Không có NAV thì không tính được mức chiết khấu, mà chính mức chiết khấu mới là chỉ báo khẩu vị nhà đầu tư ngoại. **Phải kiểm trước khi tính vào kế hoạch.**

### 5.5 Tỷ giá — vai DỰ PHÒNG cho Frankfurter

**22/23 cặp có dữ liệu**, đủ 6 cặp để dựng DXY *(đo 2026-08-15)*.

Châu Á rộng hơn Frankfurter: `CNY=X` `CNH=X` `KRW=X` `THB=X` `SGD=X` `TWD=X` `INR=X` `IDR=X` `MYR=X` `PHP=X` `HKD=X`.

🔵 **`DX-Y.NYB` — chỉ số DXY của ICE, dữ liệu thật, từ 1971** *(`fullExchangeName: "ICE Futures"`, đo 2026-08-15)*. Đây là thứ **không nguồn miễn phí nào khác trong bộ nguồn có** — dùng làm chuẩn đối chứng cho chuỗi DXY tự dựng từ Frankfurter.

#### Cách đồng bộ mốc thời gian

Vấn đề lệch mốc **chỉ nằm ở nến của phiên ĐANG chạy**. Nến ngày **đã đóng** khớp tuyệt đối: `EURUSD=X`, `JPY=X`, `CHF=X` đều đóng **23:00:00 UTC** và chia sẻ **5.925 ngày trùng nhãn** *(đo 2026-08-15)*.

> ➜ **Luật: bỏ nến cuối chưa đóng, chỉ dùng nến chốt 23:00 UTC** → 6 cặp đồng bộ tuyệt đối. *(đổi ở lát 7b, 2026-09-05: nến đang chạy vào kho, ghi đè tới khi đóng — xem khối đo bên dưới.)*

🔴 **Nhưng 23:00 UTC là nửa đêm London, KHÁC fixing 14:15 CET của ECB.** ⇒ **Không trộn Yahoo và Frankfurter trong cùng một chuỗi DXY.** Chọn một nguồn cho cả chuỗi, không vá chỗ trống bằng nguồn kia.

#### 2026-09-05 (lát 7b) — 17 cặp FX Yahoo thành asset riêng, cập nhật trong phiên

*(đo 2026-09-05 ~17:00 VN, 22 lời gọi)* `<CCY>=X` của Yahoo = số `<CCY>` trên 1 USD; `EUR=X` 0,8605 vs ECB fixing 04/09 0,86044 (+0,007 %); GBP +0,10 %; JPY −0,02 %; CHF −0,03 %; SEK +0,15 %; 17/17 cặp (EUR, GBP, JPY, CAD, SEK, CHF, CNY, KRW, THB, SGD, TWD, INR, IDR, MYR, PHP, HKD, VND) trả `200`, `instrumentType=CURRENCY`, `meta.currency` = mã quote, `exchangeTimezoneName=Europe/London`, phiên `currentTradingPeriod.regular` = `[23:00 UTC hôm trước → 22:59 UTC]`. `EURUSD=X`/`GBPUSD=X` là chiều ngược (`currency=USD`), không dùng.

**Hai nến cùng ngày London:** `EUR=X` cửa sổ 5 ngày có nến `2026-09-03T23:00Z` (London 09-04, o=0,85995 h=0,86301 l=0,85963 c=0,85997 — close≈open, "rỗng") và nến live `2026-09-04T21:29Z` (London 09-04, o=0,85990 h=0,86270 l=0,85940 c=0,8605; h/l khớp `regularMarketDayHigh/Low` của `meta`). Nến live của các cặp **không đồng bộ**: `EUR=X` 21:29Z thứ 6, `JPY=X`/`SEK=X`/`CHF=X` 20:59Z, `CAD=X`/`SGD=X`/`HKD=X` 04:21Z thứ 7, `CNY=X`/`KRW=X`/`INR=X`/`IDR=X`/`MYR=X`/`PHP=X` 03:30Z thứ 7, `THB=X`/`TWD=X` 00:26Z thứ 7, `VND=X` 00:25Z thứ 7 — các nến thứ 7 rất hẹp (CAD h=1,3837 l=1,3835).

**Cửa sổ 5 ngày** *(đo 2026-09-05)*: 50/54 mã trả 5–6 nến, 2 mã 4 nến, `^SET.BK`/`PSEI.PS` trả **1 nến** (chỉ nến hiện tại — cùng họ Bẫy 3).

➜ **Luật ETL: dedupe theo ngày London, nến sau thắng ⇒ lấy nến live.** 17 cặp lưu vào asset riêng `fx.usd_<ccy>.market` (tách khỏi 6 cặp fixing ECB ở Phụ lục B của spec lát 7); `fx.usd_cny` của ECB không đổi vai — Yahoo chỉ là chuỗi thị trường song song.

#### Vì sao Frankfurter là chính, Yahoo là dự phòng

| | **Frankfurter (ECB)** | **Yahoo** |
|---|---|---|
| Bản chất | Mã nguồn mở, **tự dựng lại được bằng Docker** | **API nội bộ, không cam kết, không tài liệu** |
| Xác thực | Không | Cookie `A3` + crumb *(với `v7`)* |
| Chống bot | Không | `curl_cffi` giả vân tay TLS |
| Mốc chốt | 14:15 CET, **có định nghĩa** | Nửa đêm London, **suy ra từ dữ liệu** |
| Sai số DXY dựng lại | **0,180%** | 0,260% |
| Phủ châu Á | Hạn chế | **Rộng hơn, có `VND=X`** |

➜ **ECB ngừng thì Frankfurter vẫn dựng lại được; Yahoo thì không ai dựng lại được.** Vai đúng: **Frankfurter chính · Yahoo dự phòng nóng + bổ sung cặp châu Á**. Chi tiết công thức DXY: [`fx.md`](fx.md).

### 5.6 Hàng hoá đơn lẻ — được 3, mất 3, và **chưa chứng minh được ĐÚNG**

| Mặt hàng | Mã | Trạng thái *(đo 2026-08-15)* |
|---|---|---|
| Đồng | `HG=F` | ✅ tươi 2026-08-14 |
| Thép | `HRC=F` | ✅ tươi |
| Nhôm | `ALI=F` | ✅ tươi |
| Quặng sắt | `TIO=F` | 🔴 chết từ 2021 |
| Than | `MTF=F` | 🔴 chết từ 2025-02 |
| Cao su | — | 🔴 **không có mã nào** |

🔴 **Ba mã sống mới chứng minh được TƯƠI, chưa chứng minh ĐÚNG.** Đợt đo định đối chiếu FRED nhưng `fred.stlouisfed.org` timeout 4/4. **Phải đối chiếu độ đúng trước khi đưa vào sản xuất.**

⚠️ **Đơn vị:** `ZC` `ZS` `ZW` `KC` `SB` `CT` trả `currency: "USX"` = **cent Mỹ**, không phải USD. Đọc nhầm sai **100 lần**. Luôn đọc `meta.currency`, đừng giả định USD.

*(Vàng, dầu, nông sản **không lấy ở Yahoo** — đã có WiChart, LBMA và FRED phủ.)*

---

## 6. Ranh giới — Yahoo KHÔNG được dùng làm gì

### 6.1 `VND=X` là tỷ giá THỊ TRƯỜNG, không thay được `dhtg` của WiChart

| Nguồn | Ngày | Giá |
|---|---|---:|
| Yahoo `VND=X` | **2026-08-15** | **26.147** |
| WiChart — tỷ giá trung tâm | 2026-08-14 | 25.561 |
| WiChart — NHTM bán ra | 2026-08-14 | 26.330 |
| WiChart — tự do bán ra | 2026-08-14 | 25.990 |

Yahoo nằm **giữa giá tự do và giá NHTM bán ra**, **cao hơn tỷ giá trung tâm +2,29%**.

➜ `VND=X` *(có lịch sử từ 2003-12)* là **tỷ giá thị trường liên ngân hàng**. Nó **không thay được** `dhtg` của WiChart — series đó cho đủ 5 loại giá, gồm cả **tỷ giá điều hành**, thứ Yahoo không có. Dùng `VND=X` làm **đối chứng**, không làm nguồn chính. Yahoo tươi hơn một ngày vì chạy cả cuối tuần. Xem [`../macro/wichart.md`](../macro/wichart.md).

### 6.2 Cổ phiếu Việt Nam — chỉ HOSE, mù 72% danh mục

Hậu tố `.VN`, sàn khai `VSE`/`HOSE`, tiền `VND`, múi giờ `Asia/Bangkok`.

| Sàn | BVSC có | Yahoo có | Tỉ lệ |
|---|---:|---:|---:|
| **HOSE** | 399 | **399** | **100%** |
| HNX | 267 | **0** | **0%** |
| UPCOM | 748 | 19 | **2,5%** |

*(19 mã "UPCOM" thực ra là các mã **đã rời HOSE** — `HBC`, `POM`, `ITA`, `HNG`, `VNE` — Yahoo giữ bản ghi cũ.)*

**Độ chính xác trên phần có: rất cao.** Đối chiếu giá phiên 2026-08-14 trên 400 mã: **trùng khớp tuyệt đối 398/400 = 99,5%**, |lệch| trung vị **0,0000%**. Hai ngoại lệ: `VNE` *(đã rời HOSE)*, `BTT` *(BVSC `closePrice=0`, không khớp lệnh)*.

**`VNM.VN`: 3.730 nến ngày, 2012-04 → 2026-08-14 = 14,4 năm** — sâu hơn FiinTrade *(~12,5 năm)*. 30 phiên gần nhất lệch **0,0000%**. Có **37 lần cổ tức + 6 lần chia tách**; `adjclose` so với giá đã điều chỉnh của BVSC lệch trung bình **0,32%** *(hệ số điều chỉnh khác nhau — cùng loại bẫy đã ghi ở [`../market/00-conventions.md`](../market/00-conventions.md))*.

➜ **Vai đúng: cổng kiểm chứng chéo độc lập cho HOSE.** Mù HNX + UPCOM nên chỉ phủ **399/1.414 = 28% danh mục** ⇒ không thể làm nguồn chính.

### 6.3 VN-Index — không dùng làm nguồn chính

Mã đúng là **`0P0000HY8X.VN`** *(`^VNINDEX` → `404`)*. 1.698 nến, 2020-02 → 2026-08-14, so với BVSC lệch trung bình **0,0019%**.

🔴 **Không có khối lượng**, và qua `v7/quote` **trễ 1 ngày**. ⇒ Nguồn chính vẫn là BVSC — xem [`../market/01-bvsc-rest.md`](../market/01-bvsc-rest.md).

*(Mã này cũng chính là ví dụ của Bẫy 3 — `range=5d` trả `404`, `period1`/`period2` trả `200`.)*

### 6.4 Báo cáo tài chính Việt Nam — thua FiinTrade ~90 lần

FiinTrade: **729 chỉ tiêu**. Yahoo: **34 điểm dữ liệu / 8 chỉ tiêu** *(đo 2026-08-15)*. Không có lý do nào để lấy BCTC Việt Nam ở Yahoo — xem [`../market/05-fiin-financial-statements.md`](../market/05-fiin-financial-statements.md).

### 6.5 🔴 Không dùng thư viện `yfinance` trong đường chạy sản xuất

**Khuếch đại request — đo được, không phải suy đoán** *(2026-08-15)*:

| Lệnh `yfinance` | Request HTTP THẬT |
|---|---:|
| `Ticker(...).history()` lần đầu | **4** |
| — lần sau *(đã có auth)* | **2** *(luôn kèm 1 lời gọi `range=1d` thừa)* |
| `yf.download([2 mã])` | **4** = 2 / mã |

Và các request đó **chạy song song** — bộ đếm của thư viện báo 55 trong khi sổ ghi ở tầng `HTTPAdapter.send` ghi **58**. ⇒ **Mọi khoảng nghỉ đặt ở tầng gọi hàm đều bị phá.** Với một nguồn không cam kết và có chống bot, mất kiểm soát nhịp là rủi ro thật.

**Chênh lệch quy mô, cùng một việc — lấy 399 mã HOSE:**

| Cách làm | Số request |
|---|---:|
| `v7/quote` theo lô 180 mã | **3** |
| `yf.download()` | **798** — gấp **266 lần** |

➜ **Bỏ hẳn thư viện, gọi thẳng `v8/finance/chart` và `v7/quote`.** 1 request/mã cho lịch sử, bằng **một nửa** thư viện, và nhịp nghỉ nằm đúng chỗ mình đặt.

*(Hồ sơ thư viện, để tham chiếu: bản mới nhất **1.6.0** phát hành 2026-08-13 · nhịp ~1 bản/tháng trong 12 tháng · giấy phép **Apache-2.0** · commit `fix` **13/50 = 26%**.)*

---

## 7. Ngân sách lời gọi và hiệu năng

**Hiệu năng đo được 2026-08-15:** 44/44 lời gọi Yahoo trả `200`, **trung vị 163 ms**. Không bị chặn từ Việt Nam. Chạy tuần tự, nghỉ ≥ 1,10 s — **không dò ngưỡng chặn, đây là chủ đích**.

Ngân sách nếu triển khai, gọi thẳng `v8/finance/chart`, 1 request/mã/ngày:

| Khối | Số mã | Req/ngày |
|---|---:|---:|
| Chỉ số quốc tế | 36 | 36 |
| Vĩ mô / biến động / lợi suất | 12 | 12 |
| Tỷ giá *(chỉ khi Frankfurter hỏng)* | 23 | 0–23 |
| Kiểm chéo HOSE — **`v7/quote` theo lô 180 mã** | 399 | **3** |
| **Tổng thường nhật** | | **≈ 53** |

🔵 **Lô `v7/quote` là đòn bẩy lớn nhất: 399 mã HOSE chỉ tốn 3 request.**

**Mức tải `--intraday` (lát 7b, đo 2026-09-05 17:20–17:36 VN):** 216 lời gọi (4 lượt × 54 mã) trong 16 phút, giãn cách ngẫu nhiên 1–5 s, **216/216 `200`, 0 lỗi, không header rate-limit**, phản hồi TB 81 ms, max 393 ms. Kết luận: **mức 216 lời gọi/16 phút an toàn** ⇒ nhịp 10 phút × 54 mã nằm dưới mức đó. Chưa đo tổng ngày (≈ 7.800 lời gọi/ngày).

---

## 8. Bộ giám sát hợp đồng — ba cổng bắt buộc

Yahoo là API nội bộ không cam kết, và hỏng theo kiểu **im lặng**. Ba cổng dưới đây là **điều kiện để dùng nguồn này**, không phải tuỳ chọn.

| # | Cổng | Chặn khi | Chống bẫy nào |
|---|---|---|---|
| **1** | **Độ tươi** — so `regularMarketTime` với lịch phiên **của sàn đó, theo múi giờ sàn đó** | Mốc cuối cũ hơn phiên gần nhất | Chết im lặng *(bắt được cả `^BCOM`)* |
| **2** | **Lược đồ** — `meta.dataGranularity` phải khớp `interval` đã xin | Lệch ⇒ **lỗi cứng, dừng ghi kho** | Bẫy 2 |
| **3** | **Lược đồ** — `meta.instrumentType != "ALTSYMBOL"` *(và `quoteType` nếu còn — khoá đổi tên 2026-09-05)* | `ALTSYMBOL` ⇒ mã đã ngừng | Chết im lặng |

Cổng 1 trong code (`etl/yahoo_normalize.py`, 2026-09-05): `regularMarketTime ≥ now − 14 ngày` (phủ Tết Trung Quốc) **và** ≥ 1 nến trong cửa sổ; kèm luật **bỏ nến cuối chưa đóng** khi `now < currentTradingPeriod.regular.end` — lưu ý `DX-Y.NYB` có `regular.end` = 03:59 UTC ngày kế (ICE gần 24 giờ), nên so với `now`, không so với `regularMarketTime`. *(bỏ hẳn ở lát 7b, 2026-09-05 — cả lượt trọn lẫn `--intraday`: `currentTradingPeriod` không còn dùng để loại nến, nến đang chạy vào kho; thay bằng dedupe theo ngày sàn, nến sau ghi đè nến trước.)*

Kèm ba luật gọi ở [mục 2](#2--ba-bẫy-cấu-trúc--đều-làm-hỏng-dữ-liệu-mà-không-báo-lỗi): `period1` âm · không dùng `range=` · `404` phải thử lại bằng `period1`/`period2`.

Và **gọi thẳng REST, không dùng thư viện** *(§6.5)* — nếu không, cổng 1 và 2 vẫn chạy nhưng nhịp nghỉ không còn kiểm soát được.

---

## 9. Chưa kiểm

| Mục | Vì sao còn treo |
|---|---|
| ~~**Host chính xác** của `v8/finance/chart`~~ | ✅ đo 2026-09-05: `query1`/`query2.finance.yahoo.com` (§1.1). `v7/quote` vẫn chưa kiểm host |
| **`v7/quote` theo lô có cần xác thực không** | Chỉ gặp `401` ở lời gọi hỏi NAV `VOF.L`; lô 180 mã chưa thử riêng |
| **Độ đúng `HG=F` / `HRC=F` / `ALI=F`** | Mới chứng minh **tươi**, chưa chứng minh **đúng** — `fred.stlouisfed.org` timeout 4/4 khi đối chiếu |
| **`VOF.L` có NAV không** | `v7/finance/quote` trả `401` — phải dựng luồng cookie `A3` → `getcrumb` |
| **`yfinance` 1.6.0** | Máy đo cài 0.2.54; số ở §6.5 là của 0.2.54. Số liệu endpoint thì độc lập với thư viện |
| ~~**ETag / `If-None-Match`**~~ | ✅ đo 2026-09-05: `v8/finance/chart` **không trả ETag** — ETL lấy cửa sổ 400 ngày mỗi lượt (~50 KB/mã) |
| **Điều khoản dữ liệu Yahoo** | Không đọc được trong đợt khảo sát 2026-08-15 |
| Quyền chọn · tin tức · bộ sàng lọc · dữ liệu giữ cổ phần | Không gọi — loại khỏi phạm vi từ đầu |
