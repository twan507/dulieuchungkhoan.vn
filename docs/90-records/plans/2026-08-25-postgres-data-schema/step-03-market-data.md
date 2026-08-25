# Bước 3 — Bảng dữ liệu cổ phiếu: giá EOD, BCTC, snapshot, sự kiện

**Trạng thái:** ✅ chốt 2026-08-25 (chủ dự án đồng ý 5 điểm duyệt, sau làm rõ nguồn gốc `close_raw`) · **Phụ thuộc:** bước 1–2 (✅) · **Phạm vi:** các bảng *sự thật* của schema `market`. Nến intraday/tick **không ở đây** (ClickHouse — phiên riêng). Bảng tự tính (chỉ số ngành, chỉ báo) ở bước 8.

Mỗi bảng ghi rõ **ngữ nghĩa ghi** — đây là "mặt bích" mọi adapter ETL phải tôn trọng (hợp đồng tháo lắp nguồn, README).

---

## 1. Giá ngày — `price_daily`

```sql
CREATE TABLE market.price_daily (
  security_id   bigint NOT NULL REFERENCES market.security,
  trading_date  date   NOT NULL,
  close_adj     numeric,        -- giá ĐÃ điều chỉnh (nguồn tự điều chỉnh khi có sự kiện quyền)
  close_raw     numeric,        -- giá THÔ khớp sàn — sự thật lịch sử, KHÔNG BAO GIỜ sửa
  open_value    numeric, highest_value numeric, lowest_value numeric,
                                -- ⚠️ O/H/L theo nền ĐÃ điều chỉnh (cùng nền close_adj) —
                                -- ghép O/H/L với close_raw là trộn hai nền giá (review vòng 2, M10)
  -- ~90 cột còn lại: khối lượng, giá trị, thoả thuận, khối ngoại, dòng tiền
  -- cá nhân/tổ chức/tự doanh, cờ sự kiện — danh sách chốt trong plan, sinh từ
  -- market-field-selection.json (không chép tay)
  raw           jsonb NOT NULL DEFAULT '{}',
                -- payload gốc KHOÁ THEO ADAPTER: {"fiintrade": {"fetched_at":…, "payload":…}, …} —
                -- dòng này do HAI nguồn ghi (close_adj ← getPriceData, close_raw ← datafeed EOD),
                -- mỗi writer chỉ merge khoá của mình, không đè khoá của writer kia
                -- (review vòng 2, C5). Mỗi khoá mang fetched_at riêng — ingested_at của dòng chỉ
                -- là lần chạm gần nhất, không trả lời được "close_adj nạp lúc nào" (vòng 3, M-1)
  ingested_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (security_id, trading_date)
);

CREATE INDEX ON market.price_daily (trading_date);
-- Review 2026-08-25: PK chỉ phục vụ "một mã theo thời gian"; index này phục vụ chiều
-- cắt ngang "toàn thị trường ngày D" — screener, market overview, và rebuild chỉ số
-- ngành (bước 8) đều quét theo ngày.

CREATE VIEW market.price_factor AS
SELECT security_id, trading_date,
       close_adj / NULLIF(close_raw, 0) AS factor
FROM market.price_daily;
```

- **Ngữ nghĩa ghi: UPSERT theo `(security_id, trading_date)`.** Re-crawl một mã sau sự kiện quyền → `close_adj` toàn chuỗi đổi theo điều chỉnh mới của nguồn → hệ số trong view tự đổi → mọi nến quá khứ hiển thị đúng **mà không viết lại dòng nào** (`close_raw` bất biến).
- **Nguồn gốc hai cột giá — và vì sao `close_raw` nullable** *(làm rõ 2026-08-25 theo câu hỏi chủ dự án)*:
  - **Quá khứ (backfill):** `getPriceData` trả chuỗi **đã điều chỉnh về hiện tại** — giá thô lịch sử không tồn tại ở nguồn nào. Backfill chỉ điền `close_adj`; `close_raw` để **NULL**, không bịa.
  - **Từ ngày vận hành:** mỗi ngày ghi giá khớp thật của chính ngày đó (EOD `/datafeed/instruments` — chưa điều chỉnh) vào `close_raw` một lần rồi bất biến; `close_adj` tiếp tục UPSERT theo nguồn.
  - **Khớp nhu cầu:** hệ số chỉ dùng để điều chỉnh **nến intraday** (ClickHouse) — nến intraday cũng chỉ tồn tại từ ngày Ingester chạy. Giai đoạn cần hệ số = giai đoạn có raw. Ngày không có raw, view trả NULL là hành vi đúng; chart dài hạn dùng thẳng `close_adj` (chuỗi tự nhất quán).
- View `price_factor` cũng là điểm nối duy nhất sang ClickHouse (điều chỉnh nến intraday — cơ chế thuộc phiên ClickHouse).
- Kích hoạt re-crawl: từ `corporate_event.exright_date` (§4).
- **Chỉ số (VNINDEX…) cũng ghi vào bảng này** (`security_type='index'`), dòng chỉ số dùng tập cột con. Nguồn EOD chỉ số **đã đo**: TVC `/history` phủ `VNINDEX`/`VN30`/`HNXIndex` + `getIndexSnapshots` 20 chỉ số — nhưng ⚠️ **TVC chặn cứng 239 nến, `from` bị bỏ qua** ([00-conventions.md](../../../10-sources/market/00-conventions.md) bẫy 7) ⇒ **lịch sử chỉ số không backfill sâu được, phải tự tích luỹ từ ngày vận hành** — cùng họ với snapshot/screener. *(Review vòng 2, I11 — bản trước ghi "chưa kiểm" là sai: nguồn đã kiểm, ràng buộc thật là độ sâu.)*

## 2. BCTC dạng dài — `financial_statement` + từ điển chỉ tiêu

```sql
CREATE TABLE market.financial_statement (
  issuer_id      bigint   NOT NULL REFERENCES market.issuer,
  year_report    smallint NOT NULL,
  quarter_report smallint NOT NULL CHECK (quarter_report BETWEEN 1 AND 5), -- 1..4 quý, 5 = cả năm
  statement_type text     NOT NULL CHECK (statement_type IN ('BS','IS','CF','NO')),
  metric_code    text     NOT NULL,   -- mã chỉ tiêu (chữ thường): bsa1, isa22, cfa18…
  canonical_code text,                -- mã chuẩn của mình — điền dần, NULL không chặn
  value          numeric,
  ingested_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (issuer_id, year_report, quarter_report, statement_type, metric_code)
);
CREATE INDEX ON market.financial_statement (metric_code, year_report, quarter_report);
-- Review vòng 2, C4: bảng lớn nhất kho (~chục triệu dòng); mọi truy vấn ngữ nghĩa đã thiết kế
-- (v_financial_ratios, compare_peers, screen_stocks — market-data-store §6) đều cắt ngang
-- theo (metric_code, kỳ) — thiếu index này là seq-scan.

CREATE TABLE market.metric_dictionary (   -- registry giải mã chỉ tiêu (2 từ điển)
  dictionary text NOT NULL CHECK (dictionary IN ('screener_params','field_dictionary')),
  code       text NOT NULL,               -- chuẩn hoá chữ thường khi nạp
  name_vi    text, name_en text,
  unit       text,                        -- don_vi_du_lieu — KHÔNG phải nhãn unit của API
  value_min  numeric, value_max numeric,  -- valueRange toàn thị trường (screener_params)
  PRIMARY KEY (dictionary, code)
);

CREATE TABLE market.metric_mapping (      -- registry: mã vendor → mã chuẩn (điền dần)
  source         text NOT NULL,           -- registry ĐƯỢC PHÉP có source (ổ cắm — quyết định #4)
  vendor_code    text NOT NULL,
  canonical_code text NOT NULL,
  name_vi        text, unit text,
  PRIMARY KEY (source, vendor_code)
);
-- Review vòng 2, I9: khôi phục đúng thiết kế đã duyệt ở market-data-store §9.3
-- (source, vendor_code) — PK chỉ vendor_code sẽ VỠ khi có nguồn BCTC thứ hai trùng chuỗi mã.
```

- **Vì sao dạng dài:** bộ chỉ tiêu khác nhau theo loại doanh nghiệp (`bsa*` phi ngân hàng, `bsb*` ngân hàng) — dạng cột rộng sẽ thưa hàng trăm cột NULL. 556 mã BCTC + 173 tỷ số nằm gọn một khuôn.
- **Ngữ nghĩa ghi: UPSERT** — BCTC bị **điều chỉnh hồi tố** (restate); re-crawl mỗi quý sau mùa báo cáo, giá trị mới đè giá trị cũ, `ingested_at` cho biết bản nào mới.
- Từ điển nạp từ **hai nguồn**: 83 chỉ tiêu `GetScreenerParameters` (kèm `valueRange`) + 729 mã [field-dictionary.json](../../../10-sources/market/field-dictionary.json) (kèm `don_vi_du_lieu`, 392 mã đã xác thực bằng đẳng thức kế toán — bảy phép kiểm đó vào bộ giám sát hợp đồng, bước 7). **Luật ưu tiên khi trùng `code`** *(review 2026-08-25)*: `unit` lấy theo `field_dictionary` (phủ 99,7%, đã xác thực); `screener_params` chỉ là nguồn của `valueRange` và tên hiển thị.
- ⚪ **Rủi ro chấp nhận** *(review 2026-08-25; thu hẹp ở vòng 2)*: `financial_statement.metric_code` không có namespace nguồn — nếu có nguồn BCTC thứ hai trùng chuỗi mã, xử bằng prefix khi nạp (bảng **dữ liệu** không có cột source theo quyết định #4). Riêng registry `metric_mapping` đã mang `source` trong PK nên không còn rủi ro vỡ khoá.
- 🔴 **Không tự tính lại chỉ tiêu nguồn đã cấp** — `isa20ttm ≠ Σ4 quý isa20` (lệch tới 9,4%, khác định nghĩa lợi nhuận). Lưu số nguồn đưa.

## 3. Snapshot và screener theo ngày — tự tạo lịch sử

```sql
CREATE TABLE market.snapshot_daily (
  issuer_id    bigint NOT NULL REFERENCES market.issuer,
  trading_date date   NOT NULL,
  kind         text   NOT NULL CHECK (kind IN
               ('snapshot','company_score','valuation','rate_indicator','ownership','dividend')),
  payload      jsonb  NOT NULL,
  ingested_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (issuer_id, trading_date, kind)
);
CREATE INDEX ON market.snapshot_daily (trading_date);  -- cắt ngang theo ngày (review vòng 2, M3)

CREATE TABLE market.screener_daily (
  security_id  bigint NOT NULL REFERENCES market.security,
  trading_date date   NOT NULL,
  payload      jsonb  NOT NULL,   -- 80/193 trường đã chọn (market-field-selection)
  ingested_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (security_id, trading_date)
);
CREATE INDEX ON market.screener_daily (trading_date);  -- cắt ngang theo ngày (review 2026-08-25)
```

- **Ngữ nghĩa ghi: UPSERT theo PK** — chạy lại trong ngày đè bản của chính ngày đó; ngày khác nhau là dòng khác nhau.
- Đây là chỗ **tự tạo lịch sử** cho dữ liệu nguồn chỉ trả giá trị hiện tại (điểm VGM, định giá, cơ cấu sở hữu): sau một năm có chuỗi biến động mà chính nguồn cũng không có API nào cung cấp. Mất là mất — vì vậy hai bảng này thuộc nhóm chạy sớm.
- Chọn `jsonb` thay vì cột hoá 80–223 trường: khối tri thức này chưa cần lọc SQL từng trường (đọc theo mã + ngày); trường nào về sau cần lọc/xếp hạng thì thăng cấp thành cột hoặc bảng tự tính (luật bước 8), không phải sửa dữ liệu cũ.

## 3b. Dữ liệu cấp chỉ số/thị trường — MoneyFlow và thống kê phiên *(bổ sung review vòng 3, C-1)*

Kiến trúc §3.4 chốt **MoneyFlow là nguồn chuẩn** cho ba họ dữ liệu **cấp thị trường** mà BVSC không có (tự doanh · đóng góp chỉ số · chuỗi mua/bán chủ động toàn thị trường — nhận `ComGroupCode`, không nhận mã); và `getIndexSnapshots` cấp 33 trường thống kê phiên theo chỉ số (advances/declines…). Bản spec trước không có bảng nào chứa chúng — hai bảng bổ sung, khoá vào dòng chỉ số của `security`:

```sql
CREATE TABLE market.index_stat_daily (    -- thống kê + dòng tiền CẤP CHỈ SỐ theo ngày
  security_id  bigint NOT NULL REFERENCES market.security,  -- dòng security_type='index'
  trading_date date   NOT NULL,
  payload      jsonb  NOT NULL DEFAULT '{}',
               -- khoá theo adapter (như raw của price_daily): {"moneyflow": …, "index_snapshot": …}
               -- trường cần lọc/vẽ chart thăng cấp cột hoặc bảng tự tính sau (luật bước 8)
  ingested_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (security_id, trading_date)
);
CREATE INDEX ON market.index_stat_daily (trading_date);

CREATE TABLE market.index_contribution_daily (  -- đóng góp của TỪNG MÃ vào chỉ số — khoá 3 chiều
  index_security_id bigint NOT NULL REFERENCES market.security,
  security_id       bigint NOT NULL REFERENCES market.security,
  trading_date      date   NOT NULL,
  payload           jsonb  NOT NULL,
  ingested_at       timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (index_security_id, security_id, trading_date)
);
```

Ngữ nghĩa ghi: UPSERT theo PK, cùng họ "tự tạo lịch sử" §3 — nhóm chạy sớm.

## 4. Sự kiện quyền và file BCTC

```sql
CREATE TABLE market.corporate_event (
  event_id     bigint generated always as identity PRIMARY KEY,
  event_type   text NOT NULL CHECK (event_type IN
               ('AGM','CashDividend','StockDividend','Earning','IPO','ShareIssuance')),
  issuer_id    bigint NOT NULL REFERENCES market.issuer,
  public_date  date,
  exright_date date,               -- kích hoạt re-crawl giá của mã thuộc issuer này
  record_date  date, payout_date date,
  year_report   smallint,          -- CHỈ Earning: kỳ báo cáo — phần khoá tự nhiên (vòng 3, C-3)
  length_report smallint,          -- 1..4 quý · 5 cả năm
  payload      jsonb NOT NULL,
  source_url   text,
  ingested_at  timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX corporate_event_natural_key ON market.corporate_event
  (event_type, issuer_id,
   coalesce(public_date,   '1900-01-01'),
   coalesce(exright_date,  '1900-01-01'),
   coalesce(year_report,   0),
   coalesce(length_report, 0));
-- Review 2026-08-25: public_date cũng phải coalesce — Postgres mặc định NULLS DISTINCT,
-- để public_date trần thì hai dòng trùng nhau với public_date NULL đều chèn được (dedupe thủng).
-- Review vòng 3, C-3: Earning (57.176 bản ghi — endpoint lớn nhất nhóm) định danh bằng
-- yearReport+lengthReport và KHÔNG có exright_date — doanh nghiệp công bố hai kỳ cùng ngày
-- (nộp bù, riêng lẻ + hợp nhất) sẽ sập vào một dòng nếu khoá thiếu hai cột này.
CREATE INDEX ON market.corporate_event (issuer_id, exright_date);

CREATE TABLE market.financial_report_file (
  file_id       bigint generated always as identity PRIMARY KEY,
  issuer_id     bigint NOT NULL REFERENCES market.issuer,
  year_report   smallint,
  length_report smallint,          -- 1..4 quý, 5 cả năm
  title         text,
  source_url    text NOT NULL UNIQUE,
  ingested_at   timestamptz NOT NULL DEFAULT now()
);
```

- **Ngữ nghĩa ghi `corporate_event`: UPSERT theo khoá tự nhiên** (unique index biểu thức — PK không chứa được `coalesce` nên dùng khoá nhân tạo + unique index). ETL lấy phần mới bằng `FromDate`. *Lưu ý triển khai (review vòng 2):* `INSERT … ON CONFLICT` phải lặp lại **nguyên văn cả hai biểu thức `coalesce`** thì Postgres mới suy ra được unique index này.
- **Override tường minh so với thiết kế TimescaleDB cũ** *(review vòng 2, M2)*: các lệnh `create_hypertable` + lịch nén §5.2/§5.5/§5.7 của market-data-store **hết hiệu lực theo TimescaleDB** (ADR 0007 đổi kho realtime sang ClickHouse). Postgres thuần, **chưa partition** — khối lượng EOD/BCTC ở mức triệu-chục triệu dòng chưa cần; xét partition khi có bằng chứng chậm thật. "Không xoá gì" vẫn giữ nguyên.
- `exright_date` là tín hiệu vận hành quan trọng nhất bảng này: có dòng mới với ngày này → re-crawl giá mã liên quan (§1).
- **Chỉ nạp từ 6 endpoint `GetCorporate*` chuyên biệt** — không dùng endpoint gộp `getCalendarWatchList` (190k bản ghi, bộ `eventListCode` rộng hơn CHECK 6 giá trị; dùng nó sẽ bị CHECK chặn ~79k dòng — review vòng 3, M-5).

## 5. Điểm cần duyệt ở bước này

- [ ] Giá: `close_raw` bất biến + `close_adj` UPSERT + hệ số là view — đồng ý?
- [ ] BCTC **dạng dài** (một dòng một chỉ tiêu) thay vì bảng cột rộng — đồng ý?
- [ ] Snapshot/screener lưu `jsonb` theo ngày để tự tạo lịch sử; trường cần lọc thì thăng cấp sau theo luật bước 8 — đồng ý?
- [ ] `raw jsonb` inline trên `price_daily` (dựng lại không crawl lại) — đồng ý?
- [ ] Sự kiện: khoá nhân tạo + unique index biểu thức, `exright_date` kích hoạt re-crawl — đồng ý?

## 6. Kiểm chứng của bước này (seam)

1. `price_factor`: `close_adj=50, close_raw=100` → `factor=0.5` (giải tay); `close_raw=0` → NULL, không lỗi chia 0.
2. UPSERT giá: ghi lại `(security_id, trading_date)` đã có với `close_adj` mới → 1 dòng, giá trị mới, `close_raw` giữ nguyên.
3. UPSERT BCTC restate: ghi lại cùng khoá với `value` mới → 1 dòng, giá trị mới (mô phỏng restate quý).
4. `corporate_event`: hai dòng trùng khoá tự nhiên với `exright_date NULL` → dòng hai bị chặn; **cả hai ngày cùng NULL** → vẫn bị chặn (case biên NULLS DISTINCT — đúng lỗi review 2026-08-25 đã vá).
5. `quarter_report=6` → lỗi CHECK; `kind` lạ ở snapshot → lỗi CHECK.
6. `metric_dictionary`: cùng `code` ở hai `dictionary` khác nhau → hợp lệ (hai từ điển tách khoá).

Chốt xong → bước 4 (macro: registry chỉ tiêu + observation + OMO).
