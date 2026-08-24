# yfinance / Yahoo Finance — khảo sát nguồn cuối · đo 2026-08-15

**58/60 request THẬT** (đếm ở tầng `HTTPAdapter.send`) · Yahoo 44/44 `200`, trung vị **163 ms** · **không bị chặn từ Việt Nam** · tuần tự, nghỉ ≥1,10 s, không dò ngưỡng chặn.

*(Agent không ghi được `.md`; controller ghi lại. Raw: `scratchpad/yfinance-raw/` — 36 file, 14 MB. Kiểm chứng độc lập ở §9.)*

## 0. Khuyến nghị một dòng

**LẤY — đúng một vai: nguồn chỉ số chứng khoán & vĩ mô QUỐC TẾ (36 chỉ số / 21 nước, lịch sử tới 1927, trễ 0 ngày) + dự phòng tỷ giá cho ECB. KHÔNG lấy làm nguồn chính cho dữ liệu Việt Nam.**

## 1. Bản đồ phủ chỉ số quốc tế — **36/37 mã, 21 nước, 100% trễ 0 ngày**

Cột "trễ" so với phiên 2026-08-14, tính theo **múi giờ chính sàn đó**, không phải UTC.

### Châu Á — 16/17

`^N225` Nikkei **1965** · `^HSI` Hang Seng 1986 · `^STI` Singapore 1987 · `PSEI.PS` Philippines 1987 · `^JKSE` Indonesia 1990 · `^AXJO` ASX 200 1992 · `^HSCE` HS China Ent 1993 · `^KLSE` Malaysia 1993 · `^KS11` KOSPI 1996 · `^SET.BK` Thái 1996 · `^BSESN` SENSEX 1997 · `^TWII` Đài Loan 1997 · `000001.SS` Thượng Hải 1997 · `399001.SZ` Thâm Quyến 1997 · `^NZ50` New Zealand 2003 · `^NSEI` NIFTY 50 2007

🔴 `^KOSPI` **không tồn tại** — phải dùng `^KS11`.

### Âu — Mỹ — 20/20

`^GSPC` S&P 500 **1927-12-30** · `^IXIC` NASDAQ 1971 · `^GSPTSE` Canada 1979 · `^FTSE` 1984 · `^GDAXI` DAX 1987 · `^RUT` Russell 2000 1987 · `^FCHI` CAC 40 1990 · `^SSMI` Thuỵ Sĩ 1990 · `^BFX` Bỉ 1991 · `^MXX` Mexico 1991 · `^DJI` Dow **1992** ⚠️ · `^AEX` Hà Lan 1992 · `^TA125.TA` Israel 1992 · `^IBEX` Tây Ban Nha 1993 · `^BVSP` Brazil 1993 · `^MERV` Argentina 1996 · `FTSEMIB.MI` Ý 1997 · `^N100` Euronext 1999 · `^STOXX50E` EURO STOXX 50 2007 · `^OMX` Thuỵ Điển 2008

⚠️ `^DJI` chỉ từ 1992 — **nông hơn `^GSPC` 65 năm**.

### `firstTradeDate` có nói thật không — nghiệm 6/6 ✅

`^GSPC` khai 1927-12-30 → thật **1927-12-30**, 24.772 nến, **0,00% nến rỗng**. `^N225`, `^GSPTSE`, `^HSI`, `^KS11`, `^SET.BK` đều khớp. → Dùng `firstTradeDate` làm chỉ dẫn độ sâu mà không phải tải toàn bộ. Giá trị thiếu = **`null` trong mảng**, không bỏ dòng.

## 2. 🔴 Ba bẫy cấu trúc — controller đã kiểm chứng lại, đúng cả ba

### Bẫy 1 — `period1=0` cắt câm lịch sử ở 1970

| Cách gọi `^GSPC` | Số nến | Bắt đầu |
|---|---:|---|
| `period1=0` | 14.276 | 1970-01-02 |
| `period1=-2208988800` | **24.772** | **1927-12-30** |

**Mất 10.496 nến = 42 năm.** Không cờ, `dataGranularity` vẫn `1d`, HTTP vẫn `200`.
➜ **Luật: mọi lời gọi lịch sử phải dùng `period1` ÂM.**

### Bẫy 2 — `range=max&interval=1d` bị hạ ngầm về nến THÁNG

| Cách gọi `VNM.VN` | `dataGranularity` trả về | Số nến |
|---|---|---:|
| `range=max&interval=1d` | 🔴 **`1mo`** | 173 |
| `period1`/`period2`&`interval=1d` | ✅ `1d` | **3.730** |

Agent suýt công bố *"Yahoo lệch BVSC 3,4%"* — thực chất là **so nến tháng với nến ngày**. Sửa xong: lệch **0,0000%**.
➜ **Luật: không dùng `range=`; luôn kiểm `meta.dataGranularity` khớp cái mình xin, lệch là lỗi cứng.**

### Bẫy 3 — `404` không có nghĩa là mã không tồn tại *(controller phát hiện thêm)*

`0P0000HY8X.VN` với `range=5d` → **`404`**. Cùng mã đó với `period1`/`period2` hoặc `range=1mo` → **`200`, 1.698 nến**.
➜ Gặp `404` phải thử lại bằng `period1`/`period2` trước khi kết luận mã chết.

## 3. 🔴 Chết im lặng — Yahoo có đúng kiểu hỏng của akshare

| Mã | Tên | Mốc cuối THẬT | Chết | `quoteType` |
|---|---|---|---:|---|
| **`^BCOM`** | Bloomberg Commodity | 2020-05-28 | **2.269 ngày** | `INDEX` |
| `TIO=F` | Quặng sắt 62% Fe | 2021-08-10 | ~1.830 ngày | `ALTSYMBOL` |
| `MTF=F` | Than API2 CIF ARA | 2025-02-06 | ~554 ngày | `ALTSYMBOL` |
| `RU=F` | **Rúp Nga** *(không phải cao su)* | 2020-08-21 | ~2.184 ngày | `ALTSYMBOL` |
| `LBS=F` | Lumber (HĐ cũ) | 2023-04-10 | ~1.222 ngày | `ALTSYMBOL` |

Tất cả vẫn trả `200` + giá hợp lệ.

🔵 **Hai quy tắc nhận biết, nghiệm đúng 5/5:**
1. `quoteType == "ALTSYMBOL"` ⇒ mã đã ngừng
2. Luôn so `regularMarketTime` với lịch phiên — `^BCOM` là `INDEX` "sạch" về kiểu, **chỉ mốc thời gian tố cáo nó**

## 4. Vĩ mô / biến động / ETF — 33/34 có

**Đáng lấy, dự án chưa có:**
- 🔵 **`^MOVE`** — biến động trái phiếu (ICE BofA), từ 2002-11
- 🔵 **`^SPGSCI`** — hàng hoá tổng hợp, từ **1984-01**
- 🔵 **`VNM`** (VanEck Vietnam ETF) — proxy dòng tiền ngoại vào VN, từ 2009-08
- `^VXN` `^VVIX` `^OVX` `^GVZ` `^SKEW` — họ biến động
- `^SOX` bán dẫn từ 1994 → **lấy ở Yahoo, bỏ akshare**
- ETF quốc gia: `EWJ EWY EWT EWH EWS EWM THD EIDO INDA EWZ EWW EWU EWG EWQ EWA EWC FXI MCHI`

**Lợi suất TPCP Mỹ:** `^TNX` **14.174 nến từ 1962-01-02**, `^TYX` `^FVX` `^IRX`. tz `America/Chicago`.

⚠️ Ghi nhận: `^VIX` và `^TNX` mang `exchange: "CGI"` — **vẫn là dữ liệu CBOE**. Đổi cửa vào không đổi chủ sở hữu dữ liệu. *(Quan sát, không phân tích pháp lý.)*

## 5. Tỷ giá — vai dự phòng cho ECB

**22/23 cặp.** 6 cặp DXY đủ. Châu Á rộng: `CNY=X` `CNH=X` `KRW=X` `THB=X` `SGD=X` `TWD=X` `INR=X` `IDR=X` `MYR=X` `PHP=X` `HKD=X`.
🔵 **`VND=X` = USD/VND, từ 2003-12, giá 26.147** *(chưa đối chiếu WiChart)*.

### 🔵 Giải được vấn đề lệch mốc thời gian

Vấn đề chỉ ở **nến phiên ĐANG chạy**. Nến ngày **đã đóng** khớp tuyệt đối — `EURUSD=X`, `JPY=X`, `CHF=X` đều đóng **23:00:00 UTC**, chia sẻ **5.925 ngày trùng nhãn**.
➜ **Luật: bỏ nến cuối chưa đóng, chỉ dùng nến chốt 23:00 UTC** → 6 cặp đồng bộ tuyệt đối.
⚠️ Nhưng đó là **nửa đêm London ≠ fixing 14:15 CET của ECB** → **không trộn hai nguồn trong cùng một chuỗi DXY**.

### Bên nào bền hơn — nói thẳng

| | **Frankfurter (ECB)** | **Yahoo** |
|---|---|---|
| Bản chất | Mã nguồn mở, **tự dựng lại được bằng Docker** | **API nội bộ, không cam kết, không tài liệu** |
| Xác thực | Không | Cookie `A3` + crumb |
| Chống bot | Không | `curl_cffi` giả vân tay TLS |
| Mốc chốt | 14:15 CET, **có định nghĩa** | Nửa đêm London, **suy ra từ dữ liệu** |
| Chính xác DXY | **0,180%** | 0,260% |
| Phủ châu Á | Hạn chế | **Rộng hơn, có `VND=X`** |

➜ **Frankfurter bền hơn rõ rệt** — ECB ngừng thì Frankfurter vẫn dựng lại được, Yahoo thì không ai dựng lại được.
➜ **Vai đúng: Frankfurter chính · Yahoo dự phòng nóng + bổ sung cặp châu Á.**

## 6. Dữ liệu Việt Nam — dùng được, nhưng chỉ HOSE

Hậu tố `.VN`, sàn `VSE`/`HOSE`, tiền `VND`, múi giờ `Asia/Bangkok`.

| Sàn | BVSC | Yahoo có | Tỉ lệ |
|---|---:|---:|---:|
| **HOSE** | 399 | **399** | **100%** |
| HNX | 267 | **0** | **0%** |
| UPCOM | 748 | 19 | 2,5% |

*(19 mã "UPCOM" là các mã **đã rời HOSE** — `HBC`, `POM`, `ITA`, `HNG`, `VNE` — Yahoo giữ bản ghi cũ.)*

**Đối chiếu giá phiên 2026-08-14, 400 mã: trùng khớp tuyệt đối 398/400 = 99,5%**, |lệch| trung vị **0,0000%**. Hai ngoại lệ: `VNE` (đã rời HOSE), `BTT` (BVSC `closePrice=0`, không khớp lệnh).

**`VNM.VN`: 3.730 nến ngày, 2012-04 → 2026-08-14 (14,4 năm — sâu hơn FiinTrade ~12,5 năm).** 30 phiên gần nhất lệch **0,0000%**. Có **37 lần cổ tức + 6 lần chia tách**; `adjclose` vs BVSC đã điều chỉnh lệch TB 0,32%.

**VN-Index: `0P0000HY8X.VN`** (`^VNINDEX` → 404). 1.698 nến, 2020-02 → 2026-08-14, vs BVSC lệch TB **0,0019%**. 🔴 **Không có khối lượng**, và qua `v7/quote` trễ **1 ngày**.

➜ **Vai đúng: cổng kiểm chứng chéo độc lập cho HOSE — nhưng mù HNX+UPCOM nên chỉ phủ 399/1.414 = 28% danh mục.**

## 7. Hàng hoá — được 3, mất 3, và **chưa chứng minh được ĐÚNG**

| Mặt hàng | Mã | Trạng thái |
|---|---|---|
| Đồng | `HG=F` | ✅ tươi 2026-08-14 |
| Thép | `HRC=F` | ✅ tươi |
| Nhôm | `ALI=F` | ✅ tươi |
| Quặng sắt | `TIO=F` | 🔴 chết 2021 |
| Than | `MTF=F` | 🔴 chết 2025-02 |
| Cao su | — | 🔴 **không có** |

⚠️ `ZC/ZS/ZW/KC/SB/CT` trả `currency: "USX"` = **cent Mỹ**, không phải USD — đọc nhầm sai 100 lần.

🔴 **Ba mã sống mới chứng minh được TƯƠI, chưa chứng minh ĐÚNG** — agent định đối chiếu FRED nhưng `fred.stlouisfed.org` timeout 4/4. **Phải đối chiếu trước khi vào sản xuất.**

## 8. Thư viện — và ba nhận định ngược chiều nhau

| Hạng mục | Đo được |
|---|---|
| Bản mới nhất | **1.6.0**, phát hành 2026-08-13 |
| Bản đang cài | 0.2.54 (2025-02, ~18 tháng) |
| Nhịp 12 tháng | 12 bản (~1/tháng) |
| Giấy phép mã nguồn | **Apache-2.0** |
| Commit `fix` | **13/50 = 26%** *(akshare: 58%)* |
| Xác thực | Cookie `A3` từ `fc.yahoo.com` (**trả `404` nhưng vẫn set cookie**) → `/v1/test/getcrumb` |
| `curl_cffi` | 🔴 **bắt buộc** trong `requires_dist` của 1.6.0 |

**Ba nhận định phải nói cả ba, đừng chỉ nói một:**
1. `curl_cffi` thành bắt buộc = **tín hiệu Yahoo chặn theo vân tay TLS**, leo thang rõ.
2. **Nhưng** toàn bộ 58 lời gọi khảo sát dùng `requests` **thuần** và đạt 44/44 `200` ⇒ hôm nay, từ IP này, **chưa bị chặn**.
3. **Và** bản 0.2.54 cũ 18 tháng **vẫn chạy tốt** ⇒ giao thức Yahoo **ổn định hơn nhiều** so với ấn tượng "đang bị chặn gắt".

### 🔴 Khuếch đại request — bẫy có thật

| Lệnh yfinance | Request HTTP THẬT |
|---|---:|
| `Ticker(...).history()` lần đầu | **4** |
| — lần sau (đã có auth) | **2** *(luôn có 1 lời gọi `range=1d` thừa)* |
| `yf.download([2 mã])` | **4** = 2/mã |

Và chúng **chạy song song** — bộ đếm báo 55 trong khi ledger ghi 58, **phá vỡ mọi nhịp nghỉ đặt ở tầng gọi hàm**.

➜ **Bỏ hẳn thư viện, gọi thẳng `v8/finance/chart`** — 1 request/mã, bằng **một nửa**, kiểm soát được nhịp.

## 9. Kiểm chứng độc lập của controller *(11 lời gọi)*

| Khẳng định | Kết quả |
|---|---|
| `period1=0` cắt ở 1970 | ✅ **Đúng** — 14.276 nến từ 1970-01-02 vs 24.772 từ 1927-12-30 |
| `range=max&interval=1d` → nến tháng | ✅ **Đúng** — `dataGranularity='1mo'`, 173 nến vs 3.730 |
| VN-Index = `0P0000HY8X.VN` | ✅ **Đúng** — 1.698 nến, "Vietnam VN Index", tz Asia/Bangkok. **Bổ sung:** `range=5d` cho mã này trả `404`, phải dùng `period1`/`period2` |

### 🔵 Controller lấp chỗ agent bị timeout: `^TNX` vs FRED `DGS10`

Agent không đối chiếu được vì `fred.stlouisfed.org` timeout 4/4. Controller dùng **`api.stlouisfed.org`** (host API, có khoá) — chạy tốt.

| | Kết quả |
|---|---|
| Số ngày trùng | **54** |
| **Lệch tuyệt đối TB** | **0,0091 điểm %** *(~0,9 điểm cơ bản)* |
| Lệch lớn nhất | 0,048 điểm % |
| Số ngày lệch > 0,01 | 16/54 |
| Độ tươi | 🔵 **Yahoo tươi hơn** — 2026-08-14 vs FRED 2026-08-13 |

➜ **`^TNX` chất lượng tương đương `DGS10`, sai lệch dưới một điểm cơ bản, và tươi hơn một ngày.** Dùng được làm nguồn chính hoặc dự phòng cho lợi suất TPCP Mỹ.

## 10. LẤY GÌ / BỎ GÌ

### ✅ LẤY

| # | Lấy gì | Cho mục | Số chứng minh |
|---|---|---|---|
| 1 | **36 chỉ số cổ phiếu quốc tế, 21 nước** | Bối cảnh toàn cầu — **khối đang trống** | 36/37, **100% trễ 0 ngày**, `^GSPC` 24.772 nến từ 1927 |
| 2 | `^MOVE` `^SPGSCI` `^SOX` `^VXN` `^OVX` `^GVZ` `^SKEW` | Stress trái phiếu, hàng hoá tổng hợp, bán dẫn, biến động | `^SPGSCI` từ 1984, `^SOX` từ 1994 |
| 3 | `^TNX` `^TYX` `^FVX` `^IRX` | Đường cong lợi suất Mỹ | **lệch FRED 0,009 điểm %, tươi hơn 1 ngày** |
| 4 | **Tỷ giá — vai DỰ PHÒNG** | Dự phòng Frankfurter + cặp châu Á | 22/23 cặp, có `VND=X`, đồng bộ được bằng nến 23:00 UTC |
| 5 | **`VNM`** (VanEck Vietnam ETF) | Dòng tiền ngoại vào VN — **chưa có** | Từ 2009-08 |
| 6 | **`.VN` HOSE — vai KIỂM CHỨNG CHÉO** | Cổng kiểm chéo độc lập cho BVSC | **398/400 khớp tuyệt đối** |
| 7 | *(có điều kiện)* `HG=F` `HRC=F` `ALI=F` | Đồng/thép/nhôm | 🔴 **chưa kiểm độ đúng** |

### ❌ BỎ

**Vì trùng nguồn:** BCTC Việt Nam *(FiinTrade 729 chỉ tiêu vs Yahoo 34 điểm/8 chỉ tiêu — thua ~90 lần)* · giá/KL cổ phiếu VN làm nguồn chính *(mù HNX+UPCOM = 72% danh mục)* · VN-Index làm nguồn chính *(trễ 1 ngày, không có khối lượng)* · nông sản, vàng, dầu *(WiChart + LBMA + FRED)*.

**Vì rủi ro:** `^BCOM` `TIO=F` `MTF=F` `RU=F` `LBS=F` *(chết 554–2.269 ngày mà vẫn trả `200`)* · **thư viện `yfinance` trong đường chạy sản xuất** *(2 request/mã + song song phá nhịp)*.

⚠️ **Cần xét lại:** chỉ số quốc tế hiện định lấy từ FiinTrade (`DJI`/`NASDAQ`/`N225` — 3 mã). Yahoo cho **36 mã, sâu hơn nhiều**. Nên đảo vai: **Yahoo chính, FiinTrade đối chứng**.

## 11. Ngân sách nếu triển khai

Gọi thẳng `v8/finance/chart`, 1 request/mã/ngày:

| Khối | Số mã | Req/ngày |
|---|---:|---:|
| Chỉ số quốc tế | 36 | 36 |
| Vĩ mô/biến động/lợi suất | 12 | 12 |
| Tỷ giá *(chỉ khi ECB hỏng)* | 23 | 0–23 |
| Kiểm chéo HOSE — **`v7/quote` theo lô 180 mã** | 399 | **3** |
| **Tổng thường nhật** | | **~53** |

🔵 **`v7/quote` theo lô là đòn bẩy lớn nhất: 399 mã HOSE chỉ tốn 3 request.** Cùng việc đó qua `yf.download()` tốn **798 request** — gấp **266 lần**.

## 12. Rủi ro vỡ so với akshare

| | akshare | **Yahoo** |
|---|---|---|
| Kiểu hỏng | 🔴 im lặng, `200` | 🔴 im lặng, `200` |
| **Có cờ nhận biết?** | ❌ không | ✅ **có: `ALTSYMBOL` + `regularMarketTime` + `dataGranularity`** |
| Commit `fix` | 58% | **26%** |
| Ổn định giao thức | 1 interface gãy/2–3 ngày | ✅ bản 18 tháng vẫn chạy |

🔵 **Khác biệt quyết định: akshare hỏng im lặng KHÔNG phát hiện được từ response; Yahoo thì CÓ THỂ.** Rủi ro **thấp hơn akshare một bậc** — với điều kiện dựng cổng kiểm.

**Ba điều kiện bắt buộc:** (a) cổng kiểm độ tươi theo lịch phiên **của sàn đó, theo múi giờ sàn đó**; (b) cổng kiểm lược đồ — chặn cứng nếu `dataGranularity` ≠ cái đã xin hoặc `quoteType == "ALTSYMBOL"`; (c) gọi thẳng REST, không dùng thư viện.

## 13. Chưa kiểm

- **Độ đúng `HG=F`/`HRC=F`/`ALI=F`** — chỉ chứng minh tươi
- **`VND=X` vs WiChart `dhtg`**
- **yfinance 1.6.0** — máy cài 0.2.54; số liệu §8 là của 0.2.54, số liệu endpoint độc lập thư viện
- **Điều khoản dữ liệu Yahoo** — không đọc được trong đợt này
- Quyền chọn · tin tức · sàng lọc · giữ cổ phần — không gọi, loại từ đầu

## 14. Mâu thuẫn với tài liệu

1. `10-sources/README.md` §2 *"Ngoài phạm vi"* liệt "Cổ phiếu và chỉ số quốc tế" → **chỉ số quốc tế vào phạm vi**, cổ phiếu quốc tế vẫn ngoài.
2. `report-more-sources.md` §3.1 kết luận *"Yahoo chỉ dùng cho `DX-Y.NYB` và `^GSPC`"* — dựa trên khảo sát **4 chỉ số**. Nay đo được **36 chỉ số/21 nước**. **Cần xét lại.**
