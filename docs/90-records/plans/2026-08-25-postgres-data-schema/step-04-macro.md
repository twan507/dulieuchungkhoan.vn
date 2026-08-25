# Bước 4 — Vĩ mô: registry chỉ tiêu, chuỗi quan sát, cụm OMO

**Trạng thái:** 🟡 chờ duyệt · **Phụ thuộc:** bước 1–3 (✅) · **Phạm vi:** schema `macro` — chỉ tiêu vĩ mô Việt Nam (WiChart ~70 chỉ tiêu sau lọc) + Mỹ (FRED 15 series) + đấu thầu OMO của SBV. *Giá hàng hoá của WiChart không ở đây — nó là giá tài sản, thuộc bước 5.*

---

## 1. Registry chỉ tiêu — khái niệm của mình, nguồn chỉ là ánh xạ

```sql
CREATE TABLE macro.indicator (
  indicator_id bigint generated always as identity PRIMARY KEY,
  code         text NOT NULL UNIQUE,     -- mã của MÌNH: 'vn.cpi', 'vn.gdp', 'us.fedfunds', 'us.cpi'…
  name_vi      text NOT NULL,
  name_en      text,
  unit         text NOT NULL,            -- đơn vị GỐC sau chuẩn hoá: 'VND', 'USD', '%', 'nghin_nguoi'…
  freq         text NOT NULL CHECK (freq IN ('d','w','m','q','y')),
  region       text NOT NULL CHECK (region IN ('vn','us','global')),
  notes        text
);

CREATE TABLE macro.indicator_source (     -- Ổ CẮM: tháo lắp nguồn tại đây
  indicator_id bigint NOT NULL REFERENCES macro.indicator,
  source       text NOT NULL,             -- 'wichart' | 'fred' | 'sbv'
  external_key text NOT NULL,             -- WiChart key ('cpi') / FRED series_id ('CPIAUCSL')
  external_sub text NOT NULL DEFAULT '',  -- series_idx WiChart — theo VỊ TRÍ, không theo tên
                                          -- (bẫy đã đo: tên series trùng nhau giữa 2 key)
  scale        numeric NOT NULL DEFAULT 1,-- hệ số đơn vị hardcode — nhãn nguồn sai 15 series,
                                          -- sai 1000 lần rải ngẫu nhiên, ETL nhân trước khi ghi
  active       boolean NOT NULL DEFAULT true,  -- false = series loại (growth_ref, chết, đóng băng)
  meta         jsonb,                     -- tier, lag, freq khai vs freq thật, cờ đặc thù nguồn
  PRIMARY KEY (source, external_key, external_sub),
  UNIQUE (indicator_id, source)
);
```

Người dùng và API chỉ thấy `vn.cpi`; việc nó đang lấy từ WiChart key `cpi` series 0 là chuyện riêng của bảng ánh xạ — đổi nguồn là sửa dòng ánh xạ, không đụng dữ liệu.

## 2. Chuỗi quan sát — một bảng chung, UPSERT

```sql
CREATE TABLE macro.observation (
  indicator_id    bigint NOT NULL REFERENCES macro.indicator,
  obs_date        date   NOT NULL,        -- NGÀY ĐẦU KỲ (quy ước §2.1)
  value           numeric,                -- giá trị chuẩn đọc (đã nối nếu chuỗi có đứt gãy)
  value_unspliced numeric,                -- nguyên gốc nền cũ — chỉ khác NULL quanh điểm đứt gãy
  ingested_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (indicator_id, obs_date)
);

CREATE TABLE macro.series_break (         -- sổ đăng ký đứt gãy cấu trúc (vd đổi năm gốc GDP)
  indicator_id bigint NOT NULL REFERENCES macro.indicator,
  break_date   date   NOT NULL,           -- điểm ĐẦU TIÊN thuộc nền mới
  factor       numeric NOT NULL,          -- nhân đoạn CŨ với hệ số này để nối
  reason       text NOT NULL,
  verified_by  text, verified_at timestamptz,
  PRIMARY KEY (indicator_id, break_date)
);
```

- 🔴 **Ngữ nghĩa ghi: UPSERT theo `(indicator_id, obs_date)` — bắt buộc, không append-only.** FRED **vá số quá khứ**: cùng một tháng 5/2026 của chuỗi việc làm `PAYEMS` từng mang 3 giá trị khác nhau qua 3 lần công bố. ETL FRED làm mới cửa sổ 24 tháng gần nhất mỗi lần chạy; `ingested_at` cho biết bản hiện tại nạp lúc nào.
- **Đứt gãy chuỗi**: khi nguồn đổi nền tính (đổi năm gốc giá so sánh GDP), chuỗi gãy một bậc không phải do kinh tế. Xử lý: đăng ký điểm gãy + hệ số vào `series_break` (duyệt tay, có `verified_by`), ETL nhân đoạn cũ để ra `value` liền mạch, đồng thời giữ `value_unspliced` nguyên gốc quanh đoạn ảnh hưởng — ai cần số "như nguồn công bố" vẫn có.
- **Bẫy parse ở tầng ETL** (ghi để plan kiểm, không ảnh hưởng DDL): epoch WiChart phải parse múi giờ `Asia/Ho_Chi_Minh` (lệch UTC = lệch cả chuỗi 1 ngày/1 tháng); FRED giá trị thiếu là chuỗi `"."` chứ không phải null.
- **Hoãn có chủ đích:** bảng vintage FRED (lưu mọi phiên bản của một con số, phục vụ backtest "biết gì tại thời điểm nào") — chỉ làm khi thật sự backtest, đã ghi ở bước 11 spec cũ, giữ nguyên quyết định.

### 2.1 Quy ước ngày neo kỳ — một luật duy nhất

Chuỗi tháng/quý/năm cần một ngày đại diện cho kỳ. Chuẩn của mình: **`obs_date` = ngày đầu kỳ** — tháng 7/2026 → `2026-07-01`; quý 2/2026 → `2026-04-01`; năm 2026 → `2026-01-01`. Trùng quy ước FRED; còn WiChart neo kiểu khác (quý neo tháng cuối, năm thì bất nhất giữa các chuỗi) — ETL quy đổi hết về luật này tại cổng. Một luật, không ngoại lệ, để JOIN hai chuỗi bất kỳ theo `obs_date` luôn đúng kỳ.

## 3. Cụm OMO — ba bảng: phiên, kết quả, dòng bơm-hút

Nghiệp vụ: SBV đấu thầu bơm/hút tiền qua kênh thị trường mở; trang kết quả **chỉ hiện phiên mới nhất, không có kho lưu** → crawl từ ngày đầu, mỗi ngày bỏ lỡ là mất vĩnh viễn (việc gấp nhóm [2] của roadmap).

```sql
CREATE TABLE macro.omo_session (          -- mỗi phiên ĐÃ CRAWL một dòng
  session_date      date PRIMARY KEY,     -- lấy từ TIÊU ĐỀ bài của SBV, cấm lấy ngày hệ thống
  crawled_at        timestamptz NOT NULL,
  has_reverse_repo  boolean NOT NULL,     -- có nhóm "Mua kỳ hạn" (bơm tiền)
  has_outright_sale boolean NOT NULL,     -- có nhóm "Bán hẳn" (hút tiền, tín phiếu)
  note              text
);
-- Vắng nhóm là DỮ KIỆN: phiên không có "Bán hẳn" nghĩa là hôm đó SBV không phát hành
-- tín phiếu — cờ false ghi nhận điều đó, khác hẳn "chưa crawl" (không có dòng).

CREATE TABLE macro.omo_auction (          -- kết quả: một dòng = (phiên × loại hình × kỳ hạn)
  session_date  date NOT NULL REFERENCES macro.omo_session,
  op_type       text NOT NULL CHECK (op_type IN ('reverse_repo','outright_sale')),
  tenor_days    smallint NOT NULL,        -- 7|14|21|28|35|56|63|91|140
  participants  smallint,                 -- số thành viên tham gia
  winners       smallint,                 -- số trúng thầu
  volume_bn_vnd numeric NOT NULL,         -- tỷ VND — parse số kiểu VN: '6.307,47' → 6307.47
  rate_pct      numeric,                  -- %/năm
  ingested_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (session_date, op_type, tenor_days)
);

CREATE TABLE macro.omo_flow (             -- TỰ DỰNG toàn phần từ omo_auction (luật bước 8)
  flow_date          date PRIMARY KEY,
  injection_bn_vnd   numeric NOT NULL,    -- bơm trong ngày
  maturing_bn_vnd    numeric NOT NULL,    -- đáo hạn: phiên (D−k, kỳ hạn k) đến hạn tại D
  net_bn_vnd         numeric NOT NULL,    -- ròng = bơm − đáo hạn (dương = bơm ròng)
  outstanding_bn_vnd numeric,             -- đang lưu hành (cộng dồn)
  complete           boolean NOT NULL DEFAULT false  -- true khi kho đã tích đủ ~140 ngày
);                                        -- (kỳ hạn dài nhất) — trước đó số ròng còn thiếu vế
```

- **Ngữ nghĩa ghi:** `omo_session`/`omo_auction` append-only; ngày trong tiêu đề **trùng ngày đã có** → phiên cũ chưa cập nhật, bỏ qua không ghi đè. `omo_flow` rebuild toàn phần idempotent — đúng ba luật tầng tự tính (README).
- SBV không công bố đáo hạn/ròng/đang lưu hành — cả ba **tự dựng** từ kỳ hạn (dòng ngày D kỳ hạn k sinh khoản đáo hạn tại D+k). Chiều dấu nhóm "Bán hẳn" (phát hành = hút) **chưa kiểm trên phiên thật** — ghi ở ETL, kiểm khi gặp.
- HTML gốc mỗi phiên (~414 KB) lưu ở `staging` (bước 7) — markup viết tay của SBV có thể đổi và không tải lại được.

## 4. Điểm cần duyệt ở bước này

- [ ] **Chỉ tiêu mang mã của mình** (`vn.cpi`, `us.fedfunds`…), nguồn chỉ nằm trong bảng ánh xạ kèm hệ số đơn vị — đồng ý?
- [ ] **Một bảng `observation` chung** cho mọi chỉ tiêu (dạng dài như BCTC bước 3), ghi kiểu **UPSERT** vì nguồn vá số quá khứ — đồng ý?
- [ ] **Ngày neo kỳ = ngày đầu kỳ**, một luật cho mọi chuỗi tháng/quý/năm — đồng ý?
- [ ] **Đứt gãy chuỗi**: giữ cả bản đã nối (`value`) lẫn nguyên gốc (`value_unspliced`) + sổ đăng ký hệ số duyệt tay — đồng ý?
- [ ] **OMO ba bảng**: phiên đã crawl (vắng nhóm là dữ kiện) · kết quả thầu · dòng bơm-hút tự dựng có cờ `complete` — đồng ý?

## 5. Kiểm chứng của bước này (seam)

1. UPSERT observation: ghi lại `(indicator, obs_date)` đã có với giá trị mới (literal 159001 → 158927, mô phỏng FRED vá `PAYEMS`) → 1 dòng, giá trị mới.
2. Neo kỳ: epoch WiChart của "Tháng 07/2026" (giải tay ra `2026-07-01` theo múi giờ VN) → `obs_date='2026-07-01'`; parse UTC sẽ ra `2026-06-30` — test bắt đúng bẫy này.
3. Splice: chuỗi 4 điểm với một điểm gãy factor 1,6005 (literal từ ca GDP thật) → `value` đoạn cũ = gốc × 1,6005; `value_unspliced` giữ số gốc.
4. `omo_flow` giải tay: phiên D bơm 6.307,47 tỷ kỳ hạn 7 ngày; phiên D+7 bơm 5.000 → `maturing(D+7)=6307.47`, `net(D+7)=−1307.47`.
5. Parse số VN: `'6.307,47'` → `6307.47` (literal); `float()` thẳng phải fail test này.
6. `freq='x'` → lỗi CHECK; `omo_auction.op_type` lạ → lỗi CHECK; chèn auction cho phiên chưa có trong `omo_session` → lỗi FK.

Chốt xong → bước 5 (asset: giá tài sản — hàng hoá, FX, chỉ số quốc tế, crypto).
