# Spec — Lược đồ PostgreSQL `postgres-data`

**Ngày:** 2026-08-25 · **Trạng thái:** 🟡 chờ chủ dự án duyệt · **Bước tiếp theo sau duyệt:** plan (skill `writing-plans`) cùng thư mục

**Nguồn gốc:** phiên thiết kế schema theo [lộ trình §5.2](../../../00-overview/roadmap.md), gộp 4 đầu việc: consolidation schema REST từ [kho dữ liệu thị trường §5](../../../20-design/market-data-store.md) · 3 quyết định chống khoá nhà cung cấp (§9.3/§9.6) · đối soát ranh giới ClickHouse ([ADR 0007](../../../00-overview/decisions/0007-monorepo-layout-and-stack.md)) · tách instance data/user đã chốt D ([service-topology §4](../../../20-design/service-topology.md)).

---

## 0. Phạm vi

**Trong phạm vi:** toàn bộ `postgres-data` — mọi miền dữ liệu chạy qua `etl`: chứng khoán VN, vĩ mô VN + quốc tế (WiChart, OMO, FRED), giá tài sản (hàng hoá, FX, chỉ số quốc tế, crypto), tin tức; cộng tầng staging và ops. Chốt công cụ migration.

**Ngoài phạm vi:**
- **DDL ClickHouse** (tick, sổ lệnh, `bar_1m`, nến intraday) — phiên thiết kế riêng theo lộ trình §5.2 dòng 2. Spec này chỉ đối soát *ranh giới* (§8).
- **`postgres-app`** (tài khoản, watchlist, danh mục) — dựng khi làm `api` auth. Spec này chỉ ghi nhận hai connection string và luật cấm JOIN chéo (§1).
- **View ngữ nghĩa + function calling chi tiết** — thuộc tầng L3, thiết kế khi làm chatbot ([mắt xích 3.3](../../../00-overview/architecture.md)). Schema này chỉ bảo đảm nền đủ cho chúng.

## 1. Quyết định nền (chốt trong brainstorm 2026-08-25)

| # | Quyết định | Lý do |
|---|---|---|
| 1 | **Migration bằng Alembic**, một env cho `postgres-data`; `postgres-app` sau này là env riêng | Chuẩn hệ Python — khớp stack FastAPI/uv (ADR 0007); migration viết SQL thô bên trong được; hai instance = hai cấu hình. ClickHouse không dùng Alembic — đằng nào cũng đi đường riêng |
| 2 | **Schema tổ chức theo miền tiêu thụ, không theo nguồn** — chủ dự án chốt: "mục tiêu là tối ưu lưu trữ và tra cứu cùng kết nối API sau này, không quan tâm nguồn thế nào; nguồn chạy qua ETL sẽ biến đổi lại" | Khớp nguyên tắc đã duyệt ở kho dữ liệu §7.1/§9.3: bảng canonical giữ nguyên, mọi thay đổi nguồn hấp thụ ở tầng ánh xạ của ETL |
| 3 | **Pattern định danh thống nhất:** khoá nội bộ (`*_id`) + bảng ánh xạ external (`source`, `external_code`) — áp cho cả ba loại thực thể: chứng khoán, chỉ tiêu, tài sản | Tổng quát hoá `security_external_id` + `metric_mapping` đã chốt "làm ngay" ở §9.6. Thêm nguồn = thêm dòng, không viết lại khoá ngoại |
| 4 | **ETL chuẩn hoá tại cổng:** ngày → `date` giờ VN; giá trị → `numeric` **đơn vị gốc** (hệ số WiChart áp ở ETL); tiền tệ ghi tường minh (USDT ≠ USD, GBp ≠ GBP, USX = cent) | Các bẫy đơn vị/múi giờ đã trả giá — [6 bẫy ngày đầu](../../../00-overview/roadmap.md), [bẫy WiChart](../../../10-sources/macro/wichart.md) |
| 5 | **Ba cột meta** ở các bảng giá/chuỗi: `price_type` · `is_derived` · `source` | Cả ba sinh từ lỗi thật: bậc nhảy 2% dầu spot/futures, DXY tự dựng, bơm ròng OMO tự dựng, chọn nguồn chuẩn |
| 6 | **Kho chứa được nhiều nguồn cho cùng một thứ; tầng đọc chỉ phơi nguồn chuẩn** qua view | Luật "mỗi chỉ tiêu một nguồn chuẩn" (architecture §3.4) thi hành ở tầng đọc — đổi nguồn chuẩn là sửa view, không đụng dữ liệu |
| 7 | **Hai instance Postgres** (`postgres-data` / `postgres-app`), hai connection string `DATA_DATABASE_URL` / `APP_DATABASE_URL`, **cấm JOIN chéo hai miền** | Đã chốt D 2026-08-25 — service-topology §4, không mở lại |

**Quy ước DDL chung:** tên bảng/cột tiếng Anh `snake_case` · khoá nhân tạo `bigint generated always as identity` · mọi bảng dữ liệu có `ingested_at timestamptz not null default now()` · `numeric` không ép precision · ngày quan sát là `date` (đã quy về giờ VN với nguồn VN, quy ước riêng từng nguồn ghi ở bảng ánh xạ) · enum nghiệp vụ dùng `check` constraint, không dùng kiểu `enum` của Postgres (đổi giá trị đỡ đau).

## 2. Sáu schema

```
postgres-data
├── market    chứng khoán VN          (etl ghi)
├── macro     chỉ tiêu vĩ mô VN+quốc tế, OMO
├── asset     giá tài sản: hàng hoá · FX · chỉ số quốc tế · crypto · quỹ
├── news      tin tức toàn văn + tìm kiếm
├── staging   landing zone payload thô theo nguồn
└── ops       data_domain_state · contract_snapshot · nhật ký ETL
```

Người ghi duy nhất cho toàn instance là `etl` (service-topology §4). `api` read-only.

## 3. Schema `market` — chứng khoán VN

Kế thừa cấu trúc đã duyệt ở kho dữ liệu §5 với **hai thay đổi**: (a) bỏ `bar_1m`/tick/TimescaleDB — sang ClickHouse; (b) khoá ngoại đổi từ `organ_code` (mã FiinGroup) sang khoá nội bộ.

### 3.1 Định danh — hai thực thể, không phải một

`organization` của FiinTrade trộn hai khái niệm: **doanh nghiệp phát hành** (issuer — chủ của BCTC, sự kiện, hồ sơ) và **mã giao dịch** (security — chủ của giá, đã gồm cả ETF, chỉ số). Tách:

```sql
market.issuer (
  issuer_id      bigint generated always as identity PRIMARY KEY,
  name           text,            -- organName
  short_name     text,
  com_type_code  text,            -- NH | CT | CK | BH | QU (quyết định endpoint snapshot)
  icb_code       text REFERENCES market.icb_industry,
  updated_at     timestamptz NOT NULL DEFAULT now()
);

market.issuer_external_id (
  issuer_id      bigint NOT NULL REFERENCES market.issuer,
  source         text   NOT NULL,          -- 'fiintrade'
  external_code  text   NOT NULL,          -- organ_code (NHN, 3801140300…)
  PRIMARY KEY (source, external_code),
  UNIQUE (issuer_id, source)
);

market.security (
  security_id    bigint generated always as identity PRIMARY KEY,
  ticker         text NOT NULL,
  exchange       text,                     -- HOSE | HNX | UPCOM
  security_type  text NOT NULL,            -- stock | etf | index | fund_cert
  issuer_id      bigint REFERENCES market.issuer,   -- NULL với index
  status         text NOT NULL DEFAULT 'listed',    -- listed | delisted
  tradelot       int,
  full_name      text,
  updated_at     timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ON market.security (ticker, exchange) WHERE status = 'listed';

market.security_external_id (
  security_id    bigint NOT NULL REFERENCES market.security,
  source         text   NOT NULL,          -- 'fiintrade' | 'bvsc' | 'yahoo'…
  external_code  text   NOT NULL,
  PRIMARY KEY (source, external_code),
  UNIQUE (security_id, source)
);
```

- 🔴 `ticker` chỉ là thuộc tính hiển thị — 41% doanh nghiệp có `organ_code ≠ ticker`. ETL tra `security_external_id`/`issuer_external_id`, **không bao giờ** truyền ticker vào tầng gọi nguồn.
- Chứng quyền, lô lẻ, trái phiếu: **loại có chủ đích** (CLAUDE.md §2.2) — `security_type` không có giá trị cho chúng, ETL không nạp.
- `market.icb_industry`: giữ nguyên draft (`icb_code` PK, `parent_icb_code`, `icb_level`, `icb_code_path`, `icb_name_path`). Đây là mã chuẩn ngành công khai (ICB), không phải mã riêng của vendor — không cần tách khoá nội bộ.
- Bảng `organization` là phụ thuộc cứng của pipeline tin (architecture §3.1) — nay hợp đồng đó trỏ vào `market.issuer` + `market.security` (lọc `status='listed'`).

### 3.2 Giá EOD

```sql
market.price_daily (
  security_id   bigint NOT NULL REFERENCES market.security,
  trading_date  date   NOT NULL,
  close_adj     numeric,        -- getPriceData.closeValue → ĐÃ điều chỉnh
  close_raw     numeric,        -- /datafeed/instruments EOD → giá THÔ
  open_value    numeric, highest_value numeric, lowest_value numeric,
  -- ~90 trường còn lại theo market-field-selection.json (nguồn chuẩn BVSC/MoneyFlow)
  source        text NOT NULL,
  raw           jsonb NOT NULL, -- landing zone inline, bắt buộc (kho dữ liệu §7.1)
  ingested_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (security_id, trading_date)
);

CREATE VIEW market.price_factor AS
SELECT security_id, trading_date,
       close_adj / NULLIF(close_raw, 0) AS factor
FROM market.price_daily;
```

Nguyên tắc **giá lưu thô, điều chỉnh lúc đọc** giữ nguyên — re-crawl làm `close_adj` đổi, hệ số tự đổi, không viết lại quá khứ. Danh sách cột chốt trong plan theo [market-field-selection.json](../../../20-design/market-field-selection.json), không chép tay.

### 3.3 BCTC dạng dài + từ điển chỉ tiêu

```sql
market.financial_statement (
  issuer_id      bigint  NOT NULL REFERENCES market.issuer,
  year_report    smallint NOT NULL,
  quarter_report smallint NOT NULL,      -- 1..4 quý, 5 cả năm
  statement_type text    NOT NULL,       -- BS | IS | CF | NO
  metric_code    text    NOT NULL,       -- mã GỐC của nguồn: bsa1, isa22… (chữ thường)
  source         text    NOT NULL,       -- 'fiintrade'
  canonical_code text,                   -- mã chuẩn của mình — điền dần, NULL không chặn
  value          numeric,
  ingested_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (issuer_id, year_report, quarter_report, statement_type, metric_code, source)
);

market.metric_dictionary (
  source    text NOT NULL,               -- 'screener_params' | 'field_dictionary'
  code      text NOT NULL,               -- chuẩn hoá chữ thường
  name_vi   text, name_en text,
  unit      text,                        -- don_vi_du_lieu, KHÔNG phải nhãn unit của API
  value_min numeric, value_max numeric,
  PRIMARY KEY (source, code)
);

market.metric_mapping (                  -- taxonomy chuẩn, điền dần (§9.6 "làm khi cần")
  source         text NOT NULL,
  vendor_code    text NOT NULL,
  canonical_code text NOT NULL,
  name_vi        text, unit text,
  PRIMARY KEY (source, vendor_code)
);
```

Nạp `metric_dictionary` từ **hai nguồn** (83 mã `GetScreenerParameters` + 729 mã [field-dictionary.json](../../../10-sources/market/field-dictionary.json)); `unit` lấy `don_vi_du_lieu`, không lấy nhãn API (bẫy 4 lộ trình §6). Không tự tính lại TTM (`isa20ttm ≠ Σ4 quý isa20` — bẫy 6).

### 3.4 Snapshot · screener · sự kiện · file BCTC

```sql
market.snapshot_daily (
  issuer_id    bigint NOT NULL REFERENCES market.issuer,
  trading_date date   NOT NULL,
  kind         text   NOT NULL,   -- snapshot | company_score | valuation
                                  -- | rate_indicator | ownership | dividend
  source       text   NOT NULL,
  payload      jsonb  NOT NULL,
  ingested_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (issuer_id, trading_date, kind)
);

market.screener_daily (
  security_id  bigint NOT NULL REFERENCES market.security,
  trading_date date   NOT NULL,
  source       text   NOT NULL,
  payload      jsonb  NOT NULL,   -- 80/193 trường đã chọn
  ingested_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (security_id, trading_date)
);

market.corporate_event (
  event_id     bigint generated always as identity PRIMARY KEY,
  event_type   text   NOT NULL,   -- AGM | CashDividend | StockDividend | Earning | IPO | ShareIssuance
  issuer_id    bigint NOT NULL REFERENCES market.issuer,
  public_date  date, exright_date date, record_date date, payout_date date,
  source       text  NOT NULL,
  payload      jsonb NOT NULL,
  source_url   text,
  ingested_at  timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ON market.corporate_event
  (event_type, issuer_id, public_date, coalesce(exright_date, '1900-01-01'));
CREATE INDEX ON market.corporate_event (issuer_id, exright_date);
```

*(Sửa so với draft cũ: PRIMARY KEY không chứa được biểu thức `coalesce` — chuyển thành khoá nhân tạo + unique index biểu thức.)* `market.financial_report_file` giữ nguyên draft, thêm `issuer_id`.

Hai bảng payload jsonb là chỗ **tự tạo lịch sử** cho dữ liệu nguồn chỉ trả hiện tại (điểm VGM, định giá, sở hữu) — tài sản tầng C không nguồn nào khác có, mất là mất.

## 4. Schema `macro` — chỉ tiêu vĩ mô + OMO

### 4.1 Registry chỉ tiêu + ánh xạ nguồn

```sql
macro.indicator (
  indicator_id bigint generated always as identity PRIMARY KEY,
  code         text NOT NULL UNIQUE,   -- mã của MÌNH: 'vn.cpi', 'vn.gdp.real', 'us.cpi', 'us.fedfunds'…
  name_vi      text NOT NULL,
  name_en      text,
  unit         text NOT NULL,          -- đơn vị GỐC sau chuẩn hoá: 'VND', 'USD', '%', 'index_1982_84=100', 'nghin_nguoi'…
  freq         text NOT NULL CHECK (freq IN ('d','w','m','q','y')),
  region       text NOT NULL,          -- 'vn' | 'us' | 'global'
  notes        text
);

macro.indicator_source (
  indicator_id  bigint NOT NULL REFERENCES macro.indicator,
  source        text   NOT NULL,       -- 'wichart' | 'fred' | 'sbv'
  external_key  text   NOT NULL,       -- WiChart key / FRED series_id
  external_sub  text   NOT NULL DEFAULT '',  -- series_idx WiChart (theo VỊ TRÍ, không theo tên)
  scale         numeric NOT NULL DEFAULT 1,  -- hệ số đơn vị hardcode (bẫy nhãn sai 15 series)
  active        boolean NOT NULL DEFAULT true,
  meta          jsonb,                 -- freq_declared vs freq_inferred, tier, flags, lag…
  PRIMARY KEY (source, external_key, external_sub),
  UNIQUE (indicator_id, source)
);
```

- Bảng hệ số đơn vị WiChart (đã hardcode trong [wichart.md §9](../../../10-sources/macro/wichart.md)) **sống ở `indicator_source.scale`** — ETL nhân trước khi ghi, kho chỉ có đơn vị gốc.
- Series `growth_ref` của WiChart (13 series suy được) **không nạp vào observation** — loại ở tầng ánh xạ (`active=false`, ghi lý do vào `meta`).

### 4.2 Quan sát — UPSERT, không append-only

```sql
macro.observation (
  indicator_id  bigint NOT NULL REFERENCES macro.indicator,
  obs_date      date   NOT NULL,       -- neo kỳ: tháng→ngày 1; quý→ngày 1 tháng cuối quý (quy ước WiChart)
  value         numeric,               -- đã splice nếu có đứt gãy
  value_unspliced numeric,             -- nguyên gốc nền cũ, chỉ khác NULL quanh điểm đứt gãy
  source        text NOT NULL,
  is_derived    boolean NOT NULL DEFAULT false,
  ingested_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (indicator_id, obs_date)
);

macro.series_break (                    -- đứt gãy cấu trúc (đổi năm gốc GDP…)
  indicator_id bigint NOT NULL REFERENCES macro.indicator,
  break_date   date   NOT NULL,        -- điểm ĐẦU TIÊN thuộc nền mới
  factor       numeric NOT NULL,       -- nhân đoạn CŨ với hệ số này
  reason       text, verified_by text, verified_at timestamptz,
  PRIMARY KEY (indicator_id, break_date)
);
```

- 🔴 **Mọi đường ghi là UPSERT theo `(indicator_id, obs_date)`** — FRED vá hồi tố (`PAYEMS` 5/2026 có 3 giá trị). Làm mới cửa sổ 24 tháng là logic ETL; schema chỉ cần `ingested_at`.
- PK **không chứa `source`** — cố ý: mỗi chỉ tiêu vĩ mô có đúng một nguồn chuẩn, `source` chỉ ghi xuất xứ dòng. Khác với `asset.price_daily` (PK chứa `source`) vì giá tài sản chủ đích giữ nhiều nguồn song song để đối chiếu.
- Múi giờ: epoch WiChart parse bằng `Asia/Ho_Chi_Minh` **trước khi** thành `obs_date` (bẫy §3.1 CLAUDE.md). FRED `value="."` → NULL.
- **Deferred có chủ đích:** bảng vintage FRED (`observation_vintage`, `output_type=4`) — làm khi cần backtest (§9.6 "làm khi cần"); lịch công bố `fred_release_calendar` — cùng nhóm.

### 4.3 Cụm OMO — crawl từ ngày đầu, không backfill được

```sql
macro.omo_session (                     -- phiên ĐÃ CRAWL: vắng nhóm là dữ kiện, không phải thiếu
  session_date  date PRIMARY KEY,       -- lấy từ TIÊU ĐỀ bài, không lấy ngày hệ thống
  crawled_at    timestamptz NOT NULL,
  has_reverse_repo   boolean NOT NULL,  -- nhóm "Mua kỳ hạn" xuất hiện
  has_outright_sale  boolean NOT NULL,  -- nhóm "Bán hẳn" xuất hiện
  note          text
);

macro.omo_auction (
  session_date  date NOT NULL REFERENCES macro.omo_session,
  op_type       text NOT NULL CHECK (op_type IN ('reverse_repo','outright_sale')),
  tenor_days    smallint NOT NULL,      -- 7|14|21|28|35|56|63|91|140
  participants  smallint, winners smallint,
  volume_bn_vnd numeric NOT NULL,       -- parse số kiểu VN: 6.307,47 → 6307.47
  rate_pct      numeric,
  ingested_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (session_date, op_type, tenor_days)
);

macro.omo_flow (                        -- TỰ DỰNG toàn phần từ omo_auction, rebuild idempotent
  flow_date        date PRIMARY KEY,
  injection_bn_vnd numeric NOT NULL,
  maturing_bn_vnd  numeric NOT NULL,    -- phiên (D−k, kỳ hạn k) đáo hạn tại D
  net_bn_vnd       numeric NOT NULL,    -- dương = bơm ròng
  outstanding_bn_vnd numeric,
  is_derived       boolean NOT NULL DEFAULT true,
  complete         boolean NOT NULL DEFAULT false  -- chỉ true sau ~140 ngày tích luỹ
);
```

- Ngày trùng `session_date` đã có → phiên cũ chưa cập nhật, **bỏ qua không ghi đè**.
- Chiều dấu nhóm `Bán hẳn` (phát hành = hút) **chưa kiểm trên dữ liệu thật** — ghi trong ETL, không khoá cứng vào schema.
- HTML gốc mỗi phiên lưu ở `staging` (bắt buộc — không tải lại được).

## 5. Schema `asset` — giá tài sản ngoài chứng khoán VN

### 5.1 Registry

```sql
asset.asset (
  asset_id       bigint generated always as identity PRIMARY KEY,
  code           text NOT NULL UNIQUE,  -- 'wti', 'gold.intl', 'gold.sjc', 'gold.lbma', 'paxg', 'btc', 'sp500', 'dxy.ice', 'dxy.ecb_recon'…
  name_vi        text NOT NULL,
  asset_class    text NOT NULL CHECK (asset_class IN ('commodity','crypto','index','fund','rate')),
  quote_currency text NOT NULL,         -- 'USD' | 'USDT' | 'VND' | 'GBp'… KHÔNG suy đoán
  unit           text,                  -- 'USD/thùng', 'VND/lượng', 'USD/oz'…
  region         text,
  notes          text
);

asset.asset_external_id (
  asset_id      bigint NOT NULL REFERENCES asset.asset,
  source        text   NOT NULL,        -- 'wichart' | 'fred' | 'yahoo' | 'lbma' | 'binance'
  external_code text   NOT NULL,        -- 'dau_wti' | 'DCOILWTICO' | 'CL=F' | '^GSPC' | 'PAXGUSDT'…
  meta          jsonb,                  -- timezone sàn, firstTradeDate, quoteType, fixing_time…
  PRIMARY KEY (source, external_code),
  UNIQUE (asset_id, source)
);
```

### 5.2 Ba bảng quan sát

```sql
asset.price_daily (                     -- giá trị đơn theo ngày: hàng hoá, fixing, quỹ NAV
  asset_id    bigint NOT NULL REFERENCES asset.asset,
  obs_date    date   NOT NULL,
  price_type  text   NOT NULL CHECK (price_type IN ('spot','futures','fixing','close')),
  value       numeric NOT NULL,
  quote_currency text NOT NULL,
  source      text   NOT NULL,
  is_derived  boolean NOT NULL DEFAULT false,
  ingested_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (asset_id, obs_date, price_type, source)
);

asset.ohlc_daily (                      -- nến ngày: chỉ số quốc tế (Yahoo), crypto (Binance)
  asset_id    bigint NOT NULL REFERENCES asset.asset,
  obs_date    date   NOT NULL,          -- Binance: từ open_time UTC; Yahoo: ngày phiên sàn
  open numeric, high numeric, low numeric, close numeric,
  close_adj   numeric,                  -- Yahoo adjclose — đổi hồi tố, UPSERT
  volume      numeric,
  quote_currency text NOT NULL,
  source      text NOT NULL,
  ingested_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (asset_id, obs_date, source)
);

asset.fx_rate (
  base_ccy    text NOT NULL,            -- 'USD'
  quote_ccy   text NOT NULL,            -- 'EUR', 'JPY'… giá trị = số quote trên 1 base (chiều TƯỜNG MINH)
  obs_date    date NOT NULL,
  rate        numeric NOT NULL,
  price_type  text NOT NULL CHECK (price_type IN ('fixing','close')),  -- ECB 14:15 CET ≠ close 23:00 UTC
  source      text NOT NULL,
  is_derived  boolean NOT NULL DEFAULT false,
  ingested_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (base_ccy, quote_ccy, obs_date, source)
);

asset.dxy_weight (                      -- tham số dựng DXY (chuẩn ICE), cho ETL derive
  currency  text PRIMARY KEY,
  weight    numeric NOT NULL            -- EUR .576 · JPY .136 · GBP .119 · CAD .091 · SEK .042 · CHF .036
);                                      -- hằng số chuẩn hoá 50.14348112 ghi trong ETL config
```

**Ràng buộc nghiệp vụ nạp liệu (thi hành ở ETL + seed registry, kiểm ở test):**

- **Dầu WTI:** `spot` chỉ từ FRED (`DCOILWTICO`, trễ 4 ngày) · `futures` từ WiChart `dau_wti` (T−1). Chênh ~2% là backwardation — **không bao giờ cùng một chuỗi** (CLAUDE.md §2.3).
- **Vàng — bốn chuỗi tách bạch:** `gold.intl` spot WiChart · `gold.lbma` fixing (15:00 London) · `paxg` 24/7 USDT · `gold.sjc` VND/lượng (scale 1e3 — nhãn nguồn sai).
- **DXY — hai chuỗi:** `dxy.ice` (Yahoo `DX-Y.NYB`, close) và `dxy.ecb_recon` (`is_derived=true`, fixing 14:15 CET, sai số đo p90 0,377%) — không trộn, không hiển thị cạnh nhau như một.
- Yahoo: bỏ nến cuối chưa đóng; validate `dataGranularity` khớp interval xin (bẫy hạ ngầm về `1mo`); `currency` đọc từ response (USX, GBp có thật).
- Binance: giá là **string** → `numeric` qua `Decimal`; nhãn tiền `USDT`, cấm viết tắt USD; nến định danh bằng **thời điểm mở**.
- Cờ cuối tuần cho chuỗi 24/7: **không lưu cột** — view đọc tính `extract(isodow …)` khi ghép với chuỗi phiên.

## 6. Schema `news` — tin tức

Chuyển spec bản ghi JSON của [news-pipeline §9](../../../20-design/news-pipeline.md) thành DDL. Bất biến: **không ghi đè** — bài sửa thì thêm revision.

```sql
news.article (                          -- phần BẤT BIẾN của một tin canonical (sau dedupe)
  article_id    bigint generated always as identity PRIMARY KEY,
  canonical_url text NOT NULL UNIQUE,
  primary_source text NOT NULL,         -- báo của bản canonical
  published_at  timestamptz NOT NULL,
  fetched_at    timestamptz NOT NULL,
  group_no      smallint,               -- nhóm taxonomy, do AI quyết (tránh tên cột "group" phải quote)
  sub           text,
  group_overridden boolean NOT NULL DEFAULT false,
  confidence    numeric,
  classified_from text CHECK (classified_from IN ('content','title_only')),
  ticker_step_ran boolean NOT NULL DEFAULT false,  -- phân biệt "không mã" vs "chưa chạy"
  labels        text[] NOT NULL DEFAULT '{}'       -- 'x_pr', 'x_social'…
);

news.article_revision (                 -- nội dung theo version, KHÔNG ghi đè
  article_id    bigint NOT NULL REFERENCES news.article,
  version       smallint NOT NULL DEFAULT 1,
  title         text NOT NULL,
  sapo          text,
  summary_ai    text,                   -- sinh bởi AI, lưu song song sapo gốc
  content       text NOT NULL,          -- toàn văn đã làm sạch boilerplate
  content_chars int,                    -- số ký tự nạp vào classifier sau cắt trần
  content_fetched_at timestamptz NOT NULL,
  tsv tsvector GENERATED ALWAYS AS
      (to_tsvector('simple', news.immutable_unaccent(title || ' ' || content))) STORED,
  PRIMARY KEY (article_id, version)
);
-- ⚠️ unaccent() gốc là STABLE nên không đứng được trong generated column;
-- migration phải tạo wrapper IMMUTABLE (news.immutable_unaccent) — kỹ thuật chuẩn, chốt trong plan.
CREATE INDEX ON news.article_revision USING gin (tsv);

news.article_source (                   -- dedupe giữ độ phủ: mọi báo cùng đăng
  article_id  bigint NOT NULL REFERENCES news.article,
  source_name text NOT NULL,
  url         text NOT NULL,
  PRIMARY KEY (article_id, url)
);

news.article_ticker (
  article_id  bigint NOT NULL REFERENCES news.article,
  security_id bigint NOT NULL REFERENCES market.security,
  via         text NOT NULL CHECK (via IN ('lookup','ai')),
  PRIMARY KEY (article_id, security_id)
);

news.trade_name (                       -- tên thương mại → mã, tầng 3 gắn mã; khớp gần đúng pg_trgm
  name        text NOT NULL,
  security_id bigint NOT NULL REFERENCES market.security,
  PRIMARY KEY (name, security_id)
);
CREATE INDEX ON news.trade_name USING gin (name gin_trgm_ops);
```

- `news.article_ticker → market.security` là JOIN **trong cùng instance** `postgres-data` — hợp lệ; luật cấm JOIN chéo chỉ áp giữa hai instance data/app.
- Gắn mã chỉ nhận `market.security` có `status='listed'` (lọc mã huỷ niêm yết — architecture §3.1); danh sách lọc động, không hardcode con số.
- Index cấu trúc: btree `(published_at)`, `(group_no, sub)`, và index trên `article_ticker (security_id)`.
- **`news.article_embedding` — cố ý HOÃN:** mô hình embedding chưa chốt (lộ trình §5 "còn để ngỏ") nên **chiều vector chưa biết** → bảng này thuộc một migration riêng khi chốt model. Extension `vector` vẫn bật sẵn từ migration đầu. Thiết kế định trước: `(article_id, version, kind CHECK IN ('content','summary','summary_ai'), model text, embedding vector(N))` — embed cả `summary` lẫn `summary_ai`, giữ riêng.

## 7. Schema `staging` — landing zone

```sql
staging.raw_payload (
  payload_id   bigint generated always as identity PRIMARY KEY,
  source       text NOT NULL,           -- 'wichart' | 'sbv' | 'fred' | 'lbma'…
  endpoint_key text NOT NULL,           -- key/series/URL định danh lời gọi
  fetched_at   timestamptz NOT NULL DEFAULT now(),
  content_type text NOT NULL CHECK (content_type IN ('json','html','text')),
  payload      jsonb,                   -- một trong hai
  body         text,
  meta         jsonb
);
CREATE INDEX ON staging.raw_payload (source, endpoint_key, fetched_at);
```

- **Bắt buộc** với hai nguồn không backfill được: OMO (HTML ~414 KB/phiên — markup viết tay có thể đổi, không tải lại được) và WiChart (cửa sổ trượt 2 năm với chuỗi ngày).
- Các bảng market đã có `raw jsonb` inline thì không ghi trùng vào staging (một sự thật một chủ).
- Không retention drop — kho là tài sản. Theo dõi dung lượng qua ops.

## 8. Schema `ops` — vận hành

```sql
ops.data_domain_state (                 -- "phần thiếu kệ nó, phần đủ cứ chạy" (§9.4)
  domain          text NOT NULL,        -- 'reference' | 'price_daily' | 'fundamentals' | 'events'
                                        -- | 'scores' | 'macro' | 'asset' | 'news'
  source          text NOT NULL,
  status          text NOT NULL CHECK (status IN ('active','frozen','migrating')),
  last_success_at timestamptz,
  watermark       text,
  PRIMARY KEY (domain, source)
);

ops.contract_snapshot (                 -- giám sát hợp đồng dữ liệu (kho dữ liệu §7.1)
  endpoint       text NOT NULL,
  checked_at     timestamptz NOT NULL,
  field_set_hash text,
  field_types    jsonb,
  record_count   int,
  coverage_pct   numeric,
  p95_latency_ms int,
  sample_payload jsonb,
  PRIMARY KEY (endpoint, checked_at)
);

ops.etl_run (
  run_id      bigint generated always as identity PRIMARY KEY,
  job         text NOT NULL,
  started_at  timestamptz NOT NULL,
  finished_at timestamptz,
  status      text NOT NULL CHECK (status IN ('running','success','failed')),
  stats       jsonb,
  error       text
);
```

Miền mất nguồn → `frozen`, các miền khác không ảnh hưởng; view đọc phải chịu `NULL` không lỗi. ETL WiChart tách được khỏi hệ thống mà không kéo đổ gì (architecture §5) — thi hành bằng miền `macro`/`asset` × source `wichart` riêng dòng.

## 9. Đối soát ranh giới ClickHouse

| Ở ClickHouse (phiên thiết kế riêng) | Ở Postgres (`postgres-data`, spec này) |
|---|---|
| Tick thô 5 topic BVSC · sổ lệnh · `bar_1m` + nến intraday dẫn xuất | Mọi thứ EOD/REST: giá ngày, BCTC, snapshot, sự kiện, vĩ mô, asset, tin |
| Ingester ghi (batch) | `etl` ghi |

Điểm nối duy nhất: điều chỉnh giá cho nến intraday cần `market.price_factor` từ Postgres — cơ chế join cross-store thuộc phiên ClickHouse, spec này chỉ bảo đảm view đó tồn tại và có `security_id` + `trading_date` làm khoá.

Chưa được giả định tick phái sinh realtime (lộ trình §5.1) — không ảnh hưởng Postgres.

## 10. Migration — Alembic

- `database/` chứa: `alembic.ini` + env `postgres-data` + thư mục `versions/`. Cấu trúc chính xác chốt trong plan.
- Migration viết **SQL thô** trong file Alembic (`op.execute`) — DDL kiểm soát từng dòng, không autogenerate từ ORM.
- Migration `0001`: tạo 6 schema + extensions `unaccent`, `pg_trgm`, `vector`. Các migration sau theo cụm bảng.
- `postgres-app`: env Alembic **riêng**, dựng khi làm `api` auth — ngoài phạm vi.
- Connection string: `DATA_DATABASE_URL` (Alembic env này) / `APP_DATABASE_URL` (sau này). Cấm JOIN chéo hai instance.

## 11. Điểm đánh dấu "chưa kiểm" — chặn migration cục bộ, không chặn spec

| Mục | Trạng thái | Hệ quả |
|---|---|---|
| Cấu trúc JSON của LBMA | **chưa kiểm** (tài liệu ghi rõ, §1.3 cấm bịa) | Registry `gold.lbma` tạo được; ETL mapping + quyết định multi-currency (thêm currency vào PK hay chỉ USD) chốt sau **một lời gọi thật** |
| Cột file zip `data.binance.vision` | chưa kiểm | Chặn backfill crypto, không chặn ETL API klines |
| Chiều dấu nhóm OMO "Bán hẳn" | chưa quan sát được phiên nào có | Logic `omo_flow` ghi chú, kiểm khi gặp phiên thật |
| Mô hình embedding | chưa chốt | `news.article_embedding` ở migration riêng |
| Vintage FRED (`output_type=4`) | làm khi cần backtest | Không có trong đợt đầu |

## 12. Seam test (chốt cùng spec — §4.5.2 CLAUDE.md)

Seam của schema là **migration + ràng buộc + view** — caller thật là ETL và `api`. Expected đến từ nguồn độc lập (literal/giải tay), không tính lại theo cách code tính:

1. `alembic upgrade head` trên DB test rỗng → đủ 6 schema, 3 extension; `downgrade base` → sạch.
2. UPSERT `macro.observation`: ghi (indicator, date) đã tồn tại với giá trị mới → 1 dòng, giá trị mới (mô phỏng FRED vá `PAYEMS`: 159001 → 158927).
3. `market.price_factor`: `close_adj=50, close_raw=100` → `factor=0.5` (giải tay); `close_raw=0` → NULL, không chia-cho-0.
4. Check constraint `asset.price_daily.price_type`: chèn `'spot_futures'` → lỗi; hai dòng WTI cùng ngày `spot`/`futures` → cùng tồn tại (case biên: cùng asset, khác price_type).
5. Derive `omo_flow`: 2 phiên giả định (D bơm 6307.47 tỷ kỳ hạn 7 ngày; D+7 bơm 5000) → `maturing(D+7)=6307.47`, `net(D+7)=-1307.47` (giải tay).
6. `news.article_revision.tsv`: bài chứa "chứng khoán" → query `unaccent` "chung khoan" bắt được; bài không chứa → không bắt (case sai).
7. Unique `market.security_external_id (source, external_code)`: chèn trùng → lỗi; cùng `external_code` khác `source` → hợp lệ (case biên `organ_code` trùng ticker nguồn khác).
8. Unique partial `market.security (ticker, exchange) WHERE status='listed'`: hai mã trùng ticker cùng sàn đều `listed` → lỗi; một `delisted` → hợp lệ.

DB test thật theo [test-strategy.md](../../../20-design/test-strategy.md); danh sách case chi tiết hoá trong plan, không thêm seam mới ngoài spec.

## 13. Tiêu chí nghiệm thu spec → plan

1. Chủ dự án duyệt spec này (gate cứng §4.1).
2. Plan bẻ thành task: khung Alembic → migration theo cụm schema (thứ tự: ops+staging → market → macro → asset → news) → seed registry (indicator/asset/ánh xạ + scale WiChart + dxy_weight) → test seam §12.
3. Nghiệm thu cuối: `alembic upgrade head` + toàn bộ test seam xanh trên DB test thật, output dán vào ledger.
