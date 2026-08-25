# Bước 5 — Giá tài sản: hàng hoá, tỷ giá, chỉ số quốc tế, crypto

**Trạng thái:** ✅ chốt 2026-08-25 (chủ dự án đồng ý 5 điểm duyệt) · **Phụ thuộc:** bước 1–4 (✅) · **Phạm vi:** schema `asset` — mọi "thứ có giá" ngoài chứng khoán Việt Nam: hàng hoá trong nước + thế giới (WiChart ~61 key, FRED dầu, LBMA vàng bạc), tỷ giá (ECB), 36 chỉ số quốc tế + phụ trợ (Yahoo), crypto (Binance).

---

## 1. Registry tài sản — pattern quen thuộc lần thứ ba

```sql
CREATE TABLE asset.asset (
  asset_id       bigint generated always as identity PRIMARY KEY,
  code           text NOT NULL UNIQUE,   -- mã của MÌNH: 'wti', 'gold.intl', 'gold.lbma',
                                         -- 'gold.sjc', 'paxg', 'btc', 'sp500', 'dxy.ice', 'thep_hrc'…
  name_vi        text NOT NULL,
  asset_class    text NOT NULL CHECK (asset_class IN ('commodity','crypto','index','fund','rate')),
  quote_currency text NOT NULL,          -- 'USD' | 'USDT' | 'VND' | 'GBp'… — KHÔNG suy đoán,
                                         -- đọc từ nguồn (bẫy đã đo: USX = cent Mỹ, GBp = pence)
  unit           text,                   -- 'USD/thùng', 'USD/oz', 'VND/lượng', 'điểm'…
  region         text,
  notes          text
);

CREATE TABLE asset.asset_external_id (   -- Ổ CẮM nguồn
  asset_id      bigint NOT NULL REFERENCES asset.asset,
  source        text NOT NULL,           -- 'wichart' | 'fred' | 'yahoo' | 'lbma' | 'binance'
  external_code text NOT NULL,           -- 'dau_wti' | 'DCOILWTICO' | '^GSPC' | 'PAXGUSDT'…
  meta          jsonb,                   -- múi giờ sàn, firstTradeDate, quoteType, mốc chốt fixing…
  PRIMARY KEY (source, external_code),
  UNIQUE (asset_id, source)
);
```

## 2. Ba bảng quan sát — theo hình dạng giá trị, không theo nguồn

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

CREATE TABLE asset.fx_rate (             -- tỷ giá: chuẩn = fixing ECB 14:15 CET
  base_ccy    text NOT NULL,             -- 'USD'
  quote_ccy   text NOT NULL,             -- 'EUR','JPY','GBP','CAD','SEK','CHF'
  obs_date    date NOT NULL,
  rate        numeric NOT NULL,          -- SỐ QUOTE TRÊN 1 BASE — chiều tường minh, hết nhầm
                                         -- (Frankfurter trả EUR:0.86453 = 1 USD đổi 0,86453 EUR;
                                         --  EURUSD hiển thị = 1/rate, tính ở tầng đọc)
  ingested_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (base_ccy, quote_ccy, obs_date)
);
```

**Ngữ nghĩa ghi:** cả ba bảng **UPSERT theo PK** — idempotent (chạy lại không nhân đôi); `close_adj` Yahoo đổi hồi tố là ca UPSERT thật; LBMA chưa rõ có vá quá khứ không nên UPSERT là mặc định an toàn.

## 3. Luật nghiệp vụ — chống trộn chuỗi (các bẫy đã đo tiền thật)

1. **Dầu WTI — một mã, hai `price_type`, cấm trộn:** `('wti', ngày, 'spot')` từ FRED (trễ 4 ngày) và `('wti', ngày, 'futures')` từ WiChart (T−1). Chênh ~2% giữa hai loại là **backwardation** (cấu trúc kỳ hạn thật), không phải sai số — trộn chung một chuỗi tạo bậc nhảy 2% tại điểm đổi nguồn. `price_type` nằm trong khoá chính nên hai chuỗi **không thể** đè nhau.
2. **Vàng — bốn mã tách hẳn** (khác bản chất, không phải khác nguồn): `gold.intl` (giao ngay thế giới) · `gold.lbma` (fixing London 15:00 — lệch spot ~0,5% có hệ thống) · `paxg` (token 24/7, quote **USDT**) · `gold.sjc` (vàng miếng trong nước, VND/lượng). Bốn chuỗi phục vụ bốn câu hỏi khác nhau; hiển thị cạnh nhau được, nối thành một thì không.
3. **Crypto giữ nhãn USDT** — không viết tắt thành USD ở bất kỳ tầng nào (chênh neo nhỏ nhưng có thật); chuỗi 24/7 khi ghép với chuỗi phiên phải xử lý ngày cuối tuần ở tầng đọc (không lưu cờ — tính được từ ngày).
4. **DXY tự dựng KHÔNG ở bước này.** Bước này chỉ lưu sự thật: `dxy.ice` (chỉ số DXY thật từ Yahoo `DX-Y.NYB`, lịch sử từ 1971) và 6 cặp tỷ giá ECB. Chuỗi "DXY dựng lại từ ECB" là **số tự tính** → thuộc tầng tự tính bước 8 (đúng luật "không trộn dẫn xuất vào bảng sự thật"), kèm bảng trọng số khi đó.
5. **Bẫy tầng ETL** (ghi để plan kiểm): Yahoo — bỏ nến cuối chưa đóng, validate `dataGranularity` khớp interval xin (bẫy hạ ngầm về nến tháng), `period1` phải âm mới lấy được lịch sử trước 1970; Binance — giá là **chuỗi ký tự**, ép `Decimal`, đọc mảng theo vị trí; LBMA — **cấu trúc JSON chưa kiểm** (tài liệu ghi rõ), phải mở một response thật trước khi viết adapter; nếu trả nhiều tiền tệ thì mỗi tiền tệ cân nhắc thành asset riêng, quyết khi thấy dữ liệu thật.

## 4. Điểm cần duyệt ở bước này

- [ ] **Registry + ánh xạ nguồn** cho tài sản — cùng pattern đã duyệt ở cổ phiếu (bước 2) và chỉ tiêu vĩ mô (bước 4) — đồng ý?
- [ ] **Ba bảng theo hình dạng giá trị** (giá đơn / nến OHLC / tỷ giá) thay vì bảng theo nguồn — đồng ý?
- [ ] **`price_type` nằm trong khoá chính** của bảng giá đơn — dầu spot và futures vĩnh viễn là hai chuỗi — đồng ý?
- [ ] **Vàng 4 mã tách** + crypto giữ nhãn USDT — đồng ý?
- [ ] **DXY dựng lại dời sang bước 8** (tầng tự tính); bước này chỉ lưu DXY thật của ICE — đồng ý?

## 5. Kiểm chứng của bước này (seam)

1. Hai dòng `('wti', cùng ngày, 'spot')` và `('wti', cùng ngày, 'futures')` → cùng tồn tại; chèn lại `'spot'` cùng ngày → UPSERT đè, vẫn 1 dòng.
2. `price_type='perp'` → lỗi CHECK (Binance perp đã đo và loại — không cho lọt cửa).
3. UPSERT `close_adj`: ghi lại nến Yahoo đã có với `close_adj` mới → 1 dòng, `close` gốc giữ nguyên.
4. Binance epoch mở nến `1786726800000` → `obs_date` theo **UTC** (giải tay); không được dùng quy tắc múi giờ VN của WiChart (hai nguồn hai luật — test giữ ranh giới).
5. `fx_rate`: nghịch đảo hiển thị `EURUSD = 1/0.86453 = 1.156698` (literal từ tài liệu fx.md) tính ở tầng đọc — bảng lưu đúng chiều gốc.
6. `asset.code` trùng → lỗi UNIQUE; external_id trùng `(source, external_code)` → lỗi.

Chốt xong → bước 6 (news: bài viết, version, gắn mã, tìm kiếm).
