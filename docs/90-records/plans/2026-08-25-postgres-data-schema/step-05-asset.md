# Bước 5 — Giá tài sản: hàng hoá, tỷ giá, chỉ số quốc tế, crypto

**Trạng thái:** ✅ chốt 2026-08-25 (chủ dự án đồng ý 5 điểm duyệt; sửa theo review vòng 2 I1/I3/M6/M9/M11 — nặng nhất là **gộp FX vào pattern asset, bỏ bảng `fx_rate`** — xem [review](review-2026-08-25.md)) · **Phụ thuộc:** bước 1–4 (✅) · **Phạm vi:** schema `asset` — mọi "thứ có giá" ngoài chứng khoán Việt Nam: hàng hoá trong nước + thế giới (WiChart ~61 key, FRED dầu, LBMA vàng bạc), tỷ giá (ECB), 36 chỉ số quốc tế + phụ trợ (Yahoo), crypto (Binance).

---

## 1. Registry tài sản — pattern quen thuộc lần thứ ba

```sql
CREATE TABLE asset.asset (
  asset_id       bigint generated always as identity PRIMARY KEY,
  code           text NOT NULL UNIQUE,   -- mã của MÌNH: 'wti', 'gold.intl', 'gold.lbma',
                                         -- 'gold.sjc_buy'/'gold.sjc_sell', 'paxg', 'btc', 'sp500',
                                         -- 'dxy.ice', 'fx.usd_eur', 'thep_hrc'…
  name_vi        text NOT NULL,
  asset_class    text NOT NULL CHECK (asset_class IN ('commodity','crypto','index','fund','fx')),
                                         -- 'fx' thêm, 'rate' bỏ (lãi suất/lợi suất thuộc macro —
                                         --  luật phân miền bước 4 §0; review vòng 2, I2/I3)
  quote_currency text NOT NULL,          -- 'USD' | 'USDT' | 'VND' | 'GBp'… — KHÔNG suy đoán,
                                         -- đọc từ nguồn (bẫy đã đo: USX = cent Mỹ, GBp = pence)
  unit           text,                   -- 'USD/thùng', 'USD/oz', 'VND/lượng', 'điểm', 'EUR/1 USD'…
  calendar       text NOT NULL DEFAULT 'trading_days'
                 CHECK (calendar IN ('trading_days','24x7')),
                                         -- lịch của CHUỖI — không suy được từ obs_date: một số
                                         -- chuỗi phiên có điểm cuối tuần carry-forward (vàng
                                         -- WiChart 36,8% ngày đứng giá) — review vòng 2, M11
  region         text,
  notes          text
);

CREATE TABLE asset.asset_external_id (   -- Ổ CẮM nguồn
  asset_id      bigint NOT NULL REFERENCES asset.asset,
  source        text NOT NULL,           -- 'wichart' | 'fred' | 'yahoo' | 'lbma' | 'binance'
  external_code text NOT NULL,           -- 'dau_wti' | 'DCOILWTICO' | '^GSPC' | 'PAXGUSDT'…
  external_sub  text NOT NULL DEFAULT '',-- series trong document đa chuỗi — WiChart một key chứa
                                         -- nhiều series ('xang_dau' 4 loại xăng, 'vang' giá mua/bán),
                                         -- trỏ theo VỊ TRÍ như macro.indicator_source
                                         -- (review 2026-08-25 — trước đó thiếu, ổ cắm không đủ chân)
  scale         numeric NOT NULL DEFAULT 1,   -- hệ số đơn vị hardcode — lỗi nhãn 1000× của WiChart
                                              -- nằm CHỦ YẾU ở nhóm hàng hoá (vang ×1e3, xang_dau
                                              -- ×1e3, U1000…) — review vòng 2, I1
  active        boolean NOT NULL DEFAULT true,-- series chết/đóng băng ở nguồn (thiec DEAD,
                                              -- ca_tra FROZEN, RON 95 SUBDEAD…)
  price_type    text,                         -- chuỗi này đổ vào price_type nào (spot/futures/
                                              -- fixing/close) — neo ở registry để hai nguồn cùng
                                              -- price_type không đè nhau lặng lẽ khi migrating
  meta          jsonb,                        -- múi giờ sàn, firstTradeDate, quoteType, mốc chốt…
  PRIMARY KEY (source, external_code, external_sub),
  UNIQUE (asset_id, source)
);
```

## 2. Hai bảng quan sát — theo hình dạng giá trị, không theo nguồn

*(Bản đã duyệt có bảng thứ ba `fx_rate`. Review vòng 2, I3: bảng đó không có registry — đổi nguồn FX không có dòng ánh xạ nào để sửa, trái quyết định #3 — và không phân biệt được mốc chốt trong khi chính bước 1 §1.2 định luật "khác mốc chốt = mã series riêng"; FX có ba mốc chốt đã đo lệch nhau không hiệu chỉnh được (ECB 14:15 CET · FRED noon ET · Yahoo 23:00 UTC). Sửa: **mỗi cặp tiền × mốc chốt = một asset** (`fx.usd_eur` class `'fx'`, quote_currency `'EUR'`, unit `'EUR/1 USD'`), quan sát vào `price_daily` với `price_type='fixing'`/`'close'` — một pattern duy nhất cho cả miền, bớt một bảng.)*

```sql
CREATE TABLE asset.price_daily (         -- giá trị ĐƠN theo ngày: hàng hoá, fixing, NAV quỹ
  asset_id    bigint NOT NULL REFERENCES asset.asset,
  obs_date    date   NOT NULL,
  price_type  text   NOT NULL CHECK (price_type IN ('spot','futures','fixing','close')),
  value       numeric NOT NULL,
  ingested_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (asset_id, obs_date, price_type)
);

CREATE TABLE asset.ohlc_daily (          -- nến ngày: chỉ số quốc tế (Yahoo), crypto (Binance)
  asset_id    bigint NOT NULL REFERENCES asset.asset,
  obs_date    date   NOT NULL,           -- Binance: từ thời điểm MỞ nến, epoch ms UTC → date UTC
  open numeric, high numeric, low numeric, close numeric,
  close_adj   numeric,                   -- Yahoo adjclose — nguồn đổi hồi tố, UPSERT
  volume      numeric,
  ingested_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (asset_id, obs_date)
);

```

**Tỷ giá — nay là các asset class `'fx'`:** sáu cặp ECB = sáu asset `fx.usd_eur` · `fx.usd_jpy` · `fx.usd_gbp` · `fx.usd_cad` · `fx.usd_sek` · `fx.usd_chf` (fixing 14:15 CET, `price_type='fixing'`); `fx.usd_cny` từ FRED `DEXCHUS` (noon ET); **5 chuỗi USD/VND** từ WiChart `dhtg` = `fx.usd_vnd.central/.ceiling/.floor/.bank_sell/.free_sell` (chuyển từ macro theo luật phân miền — bước 4 §0, vòng 3 I-4). `price_type` cho 5 chuỗi này *(vòng 4, F11 — chốt trước vì nằm trong PK)*: `central`/`ceiling`/`floor` = `'fixing'` (mức công bố/suy từ công bố của NHNN); `bank_sell`/`free_sell` = `'spot'` (giá giao dịch khảo sát). Giá trị = **số quote trên 1 USD**, chiều tường minh ghi ở `unit` ('EUR/1 USD'); Frankfurter trả `EUR: 0.86453` = 1 USD đổi 0,86453 EUR — chiều hiển thị EURUSD = 1/giá trị, tính ở tầng đọc. Thêm nguồn khác mốc chốt (Yahoo close 23:00 UTC) = **asset mới** (`fx.usd_eur.close`), không đè chuỗi fixing.

**Ngữ nghĩa ghi:** cả hai bảng **UPSERT theo PK** — idempotent (chạy lại không nhân đôi); `close_adj` Yahoo đổi hồi tố là ca UPSERT thật; LBMA chưa rõ có vá quá khứ không nên UPSERT là mặc định an toàn.

**Hai nguồn không bao giờ ghi chung một chuỗi** *(vòng 4, F5 — xử bằng luật, KHÁC đề xuất thêm `price_type` vào PK OHLC)*: đổi nguồn = cutover, adapter mới UPSERT tiếp đúng chuỗi cũ; muốn chạy song song để đối chiếu (`migrating`) thì mở **asset tạm** theo luật "một chuỗi nguồn = một asset" (§3.2b), so xong thì tắt. Lý do không thêm `price_type` vào PK `ohlc_daily`: chưa có ca nào một asset cần hai loại nến (khác mốc chốt đã là asset khác theo §1.2 bước 1), thêm cột khoá cho ca chưa tồn tại là abstraction sớm; `asset_external_id.price_type` vì vậy chỉ có nghĩa với chuỗi đổ vào `price_daily`, chuỗi OHLC để NULL.

## 3. Luật nghiệp vụ — chống trộn chuỗi (các bẫy đã đo tiền thật)

1. **Dầu WTI — một mã, hai `price_type`, cấm trộn:** `('wti', ngày, 'spot')` từ FRED (trễ 4 ngày) và `('wti', ngày, 'futures')` từ WiChart (T−1). Chênh ~2% giữa hai loại là **backwardation** (cấu trúc kỳ hạn thật), không phải sai số — trộn chung một chuỗi tạo bậc nhảy 2% tại điểm đổi nguồn. `price_type` nằm trong khoá chính nên hai chuỗi **không thể** đè nhau.
2. **Vàng — các mã tách hẳn** (khác bản chất, không phải khác nguồn): `gold.intl` (giao ngay thế giới) · `gold.lbma` (fixing London 15:00 — lệch spot ~0,5% có hệ thống) · `paxg` (token 24/7, quote **USDT**) · vàng miếng trong nước **hai mã** `gold.sjc_buy` / `gold.sjc_sell` (WiChart trả hai series mua/bán trong cùng key `vang`, VND/lượng). Các chuỗi phục vụ các câu hỏi khác nhau; hiển thị cạnh nhau được, nối thành một thì không.
2b. **Một chuỗi giá trị của nguồn = một asset** *(luật tổng quát, review 2026-08-25)*: key đa series của nguồn (xăng dầu 4 loại, vàng mua/bán…) tách thành từng asset, mỗi asset trỏ về `(source, external_code, external_sub)` riêng — không nhét nhiều chuỗi vào một asset.
3. **Crypto giữ nhãn USDT** — không viết tắt thành USD ở bất kỳ tầng nào (chênh neo nhỏ nhưng có thật). Ghép chuỗi 24/7 với chuỗi phiên: tra `asset.calendar` (`'24x7'` vs `'trading_days'`) — **không suy từ obs_date**, vì một số chuỗi phiên có điểm cuối tuần carry-forward (vàng WiChart đứng giá 36,8% ngày — review vòng 2, M11; ETL bỏ điểm carry-forward cuối tuần, chi tiết trong plan).
4. **DXY tự dựng KHÔNG ở bước này.** Bước này chỉ lưu sự thật: `dxy.ice` (chỉ số DXY thật từ Yahoo `DX-Y.NYB`, lịch sử từ 1971) và 6 cặp tỷ giá ECB. Chuỗi "DXY dựng lại từ ECB" là **số tự tính** → thuộc tầng tự tính bước 8 (đúng luật "không trộn dẫn xuất vào bảng sự thật"), kèm bảng trọng số khi đó.
4b. **Chưa xác minh đơn vị thì chưa nạp** *(vòng 3, M-4)*: `quote_currency`/`unit` NOT NULL + luật "không suy đoán" nghĩa là chuỗi nguồn khai đơn vị đáng ngờ (`vai_cotton_my` nhãn USD/tấn nhưng giá trị khớp US cents/lb — cờ UNVERIFIED của wichart.md) **đứng ngoài kho** tới khi xác minh bằng dải giá trị thật — không đoán để lấp cột.
5. **Bẫy tầng ETL** (ghi để plan kiểm): Yahoo — **ba cổng bắt buộc, "điều kiện để dùng nguồn, không phải tuỳ chọn"** *(vòng 4, F15 — bản trước chỉ ghi 1/3)*: (a) `dataGranularity` khớp interval xin (bẫy hạ ngầm về nến tháng); (b) `quoteType != 'ALTSYMBOL'` — mã chết vẫn trả 200 kèm giá hợp lệ (`^BCOM` chết 2.269 ngày); (c) độ tươi: so `regularMarketTime` với lịch phiên **của sàn đó, múi giờ sàn đó**; cộng `period1` phải âm mới lấy được lịch sử trước 1970, bỏ nến cuối chưa đóng; Binance — giá là **chuỗi ký tự**, ép `Decimal`, đọc mảng theo vị trí; LBMA — **cấu trúc JSON chưa kiểm** (tài liệu ghi rõ), phải mở một response thật trước khi viết adapter; nếu trả nhiều tiền tệ thì mỗi tiền tệ cân nhắc thành asset riêng, quyết khi thấy dữ liệu thật.

## 4. Điểm cần duyệt ở bước này

- [ ] **Registry + ánh xạ nguồn** cho tài sản — cùng pattern đã duyệt ở cổ phiếu (bước 2) và chỉ tiêu vĩ mô (bước 4) — đồng ý?
- [ ] **Hai bảng theo hình dạng giá trị** (giá đơn / nến OHLC) thay vì bảng theo nguồn; **FX là asset class `'fx'`** đi qua bảng giá đơn *(sửa từ "ba bảng" theo review vòng 2, I3 — bảng `fx_rate` cũ không có registry và không phân biệt mốc chốt)* — đồng ý?
- [ ] **`price_type` nằm trong khoá chính** của bảng giá đơn — dầu spot và futures vĩnh viễn là hai chuỗi — đồng ý?
- [ ] **Vàng tách mã theo bản chất** (intl / lbma / paxg / sjc mua / sjc bán) + luật "một chuỗi nguồn = một asset" + crypto giữ nhãn USDT — đồng ý?
- [ ] **DXY dựng lại dời sang bước 8** (tầng tự tính); bước này chỉ lưu DXY thật của ICE — đồng ý?

## 5. Kiểm chứng của bước này (seam)

1. Hai dòng `('wti', cùng ngày, 'spot')` và `('wti', cùng ngày, 'futures')` → cùng tồn tại; chèn lại `'spot'` cùng ngày → UPSERT đè, vẫn 1 dòng.
2. `price_type='perp'` → lỗi CHECK (Binance perp đã đo và loại — không cho lọt cửa).
3. UPSERT `close_adj`: ghi lại nến Yahoo đã có với `close_adj` mới → 1 dòng, `close` gốc giữ nguyên.
4. Binance epoch mở nến ngày `1786752000000` = **2026-08-15 00:00 UTC** (giải tay) → `obs_date='2026-08-15'` theo UTC; không được dùng quy tắc múi giờ VN của WiChart (hai nguồn hai luật — test giữ ranh giới). *(Review vòng 2, M6: literal cũ `1786726800000` là 17:00 UTC — mốc nửa đêm giờ VN của WiChart, không thể là open-time nến ngày Binance.)*
5. FX qua asset: seed `fx.usd_eur` giá trị `0.86453` (`price_type='fixing'`) → chiều hiển thị `EURUSD = 1/0.86453 = 1.156698` (literal từ fx.md) tính ở tầng đọc — bảng lưu đúng chiều gốc; chèn thêm `('fx.usd_eur', cùng ngày, 'close')` → cùng tồn tại (khác mốc chốt không đè nhau).
6. `asset.code` trùng → lỗi UNIQUE; external_id trùng `(source, external_code)` → lỗi.

Chốt xong → bước 6 (news: bài viết, version, gắn mã, tìm kiếm).
