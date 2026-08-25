# Bước 4 — Vĩ mô: registry chỉ tiêu, chuỗi quan sát, cụm OMO

**Trạng thái:** ✅ chốt 2026-08-25 (chủ dự án đồng ý 5 điểm duyệt; sửa theo review cùng ngày F2 + vòng 2 C1/C2/C3/I2/I8 — xem [review](review-2026-08-25.md)) · **Phụ thuộc:** bước 1–3 (✅) · **Phạm vi:** schema `macro` — chỉ tiêu vĩ mô Việt Nam (WiChart **25 key** vĩ mô — 26 key đo từ [wichart.md](../../../10-sources/macro/wichart.md) trừ `dhtg` chuyển sang asset theo luật §0; mỗi key nhiều series, số series chốt khi seed registry) + Mỹ (FRED **11/15 series** — xem §0) + đấu thầu OMO của SBV. *Giá hàng hoá của WiChart không ở đây — nó là giá tài sản, thuộc bước 5.*

## 0. Luật phân miền macro ↔ asset *(review vòng 2, I2 — trước đó DCOILWTICO có hai chủ)*

**Luật** *(viết lại ở vòng 3, I-4 — bản cũ "do cơ quan công bố → macro" không sinh ra được chính phân bổ nó biện minh: fixing ECB cũng do NHTW công bố mà vẫn thuộc asset)*:

> **Chuỗi là MỨC GIÁ của một thứ định giá được trên thị trường — có mốc chốt/loại giá cần phân biệt (spot/futures/fixing/close) → `asset`. Chuỗi là chỉ tiêu thống kê hay lãi suất theo kỳ → `macro`.** Tỷ giá là mức giá ⇒ luôn `asset`, kể cả bản fixing/điều hành do NHTW công bố (fixing chính là một mốc chốt).

Phân bổ dứt điểm 15 series FRED:

| Miền | Series |
|---|---|
| `macro` (11) | `DFF` · `FEDFUNDS` · `SOFR` · `DGS2` · `DGS10` · `T10Y2Y` · `T10YIE` · `CPIAUCSL` · `PCEPILFE` · `UNRATE` · `PAYEMS` |
| `asset` (4) | `DCOILWTICO` (dầu WTI spot) · `DTWEXBGS` (chỉ số đô broad) · `VIXCLS` (chỉ số biến động) · `DEXCHUS` (tỷ giá CNY/USD) |

Cùng luật đó cho WiChart: key `dhtg` — **5 series tỷ giá USD/VND** (trung tâm · trần · sàn · NHTM bán · tự do bán) — **rời `macro` sang `asset`** thành 5 mã `fx.usd_vnd.central/.ceiling/.floor/.bank_sell/.free_sell`; Yahoo `VND=X` khi cần làm đối chứng cắm vào registry asset. Vậy `macro` còn **25 key WiChart**. Lãi suất/lợi suất vẫn `macro` (Yahoo `^TNX` làm dự phòng cho `DGS10` thì cắm vào `indicator_source` với `source='yahoo'` — đúng cơ chế tháo lắp, không mở miền mới).

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
  role         text NOT NULL DEFAULT 'data' CHECK (role IN ('data','growth_ref')),
  notes        text
);
-- role='growth_ref' (review vòng 2, C3): 13 series "Tăng trưởng" của WiChart KHÔNG bị loại —
-- chúng là nguyên liệu DUY NHẤT để tính factor nối đứt gãy (đoạn cũ/mới không chồng lấn,
-- wichart.md §6.2) và để GIÁM SÁT phát hiện break mới. Vẫn nạp vào observation như thường,
-- nhưng tầng đọc/API chỉ phơi role='data'.

CREATE TABLE macro.indicator_source (     -- Ổ CẮM: tháo lắp nguồn tại đây
  indicator_id bigint NOT NULL REFERENCES macro.indicator,
  source       text NOT NULL,             -- 'wichart' | 'fred' | 'sbv'
  external_key text NOT NULL,             -- WiChart key ('cpi') / FRED series_id ('CPIAUCSL')
  external_sub text NOT NULL DEFAULT '',  -- series_idx WiChart — theo VỊ TRÍ, không theo tên
                                          -- (bẫy đã đo: tên series trùng nhau giữa 2 key)
  scale        numeric NOT NULL DEFAULT 1,-- hệ số đơn vị hardcode — nhãn nguồn sai 15 series,
                                          -- sai 1000 lần rải ngẫu nhiên, ETL nhân trước khi ghi
  active       boolean NOT NULL DEFAULT true,  -- false = series chết/đóng băng ở nguồn
                                               -- (growth_ref KHÔNG vào đây — nó là role
                                               --  của indicator, vẫn nạp; review vòng 2, C3)
  meta         jsonb,                     -- tier, lag, freq khai vs freq thật, cờ đặc thù nguồn
  PRIMARY KEY (source, external_key, external_sub),
  UNIQUE (indicator_id, source)
);
```

Người dùng và API chỉ thấy `vn.cpi`; việc nó đang lấy từ WiChart key `cpi` series 0 là chuyện riêng của bảng ánh xạ — đổi nguồn là sửa dòng ánh xạ, không đụng dữ liệu.

## 2. Chuỗi quan sát — một bảng chung, UPSERT

```sql
CREATE TABLE macro.observation (
  indicator_id bigint NOT NULL REFERENCES macro.indicator,
  obs_date     date   NOT NULL,           -- NGÀY ĐẦU KỲ (quy ước §2.1)
  value        numeric NOT NULL,          -- NHƯ NGUỒN CÔNG BỐ (sau chuẩn hoá đơn vị) — KHÔNG splice
  ingested_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (indicator_id, obs_date)
);
-- Giá trị thiếu = KHÔNG CÓ DÒNG (FRED trả "." thì bỏ qua), không chèn NULL —
-- thống nhất policy với asset (review 2026-08-25).

CREATE TABLE macro.series_break (         -- sổ đăng ký đứt gãy cấu trúc (vd đổi năm gốc GDP)
  indicator_id bigint NOT NULL REFERENCES macro.indicator,
  break_date   date   NOT NULL,           -- điểm ĐẦU TIÊN thuộc nền mới
  factor       numeric NOT NULL,          -- nhân đoạn CŨ với hệ số này để nối
  reason       text NOT NULL,
  verified_by  text, verified_at timestamptz,
  PRIMARY KEY (indicator_id, break_date)
);

CREATE VIEW macro.observation_spliced AS  -- chuỗi ĐÃ NỐI — tính lúc đọc, không lưu
SELECT o.indicator_id, o.obs_date,
       o.value * <tích factor của mọi break có break_date > o.obs_date>  AS value_spliced,
       o.value                                                           AS value_as_published
FROM macro.observation o;
-- SQL cụ thể của phép "tích factor" chốt trong plan (Postgres không có aggregate PRODUCT
-- dựng sẵn — dùng exp(sum(ln(factor))) hoặc LATERAL, chọn khi viết migration).
-- 🔴 BẮT BUỘC coalesce(…, 1) quanh tích: chuỗi KHÔNG có break nào (đại đa số) cho tập rỗng
-- → sum() = NULL → exp(NULL) = NULL → cả kho trả NULL. (Review vòng 3, I-6.)
```

- 🔴 **Ngữ nghĩa ghi: UPSERT theo `(indicator_id, obs_date)` — bắt buộc, không append-only.** FRED **vá số quá khứ**: cùng một tháng 5/2026 của chuỗi việc làm `PAYEMS` từng mang 3 giá trị khác nhau qua 3 lần công bố. ETL FRED làm mới cửa sổ 24 tháng gần nhất mỗi lần chạy; `ingested_at` cho biết bản hiện tại nạp lúc nào.
- **Đứt gãy chuỗi — nối bằng VIEW, không nối trong bảng** *(đổi theo review 2026-08-25, F2)*: khi nguồn đổi nền tính (đổi năm gốc giá so sánh GDP), chuỗi gãy một bậc không phải do kinh tế. Bảng chỉ lưu số **như nguồn công bố**; điểm gãy + hệ số đăng ký vào `series_break` (duyệt tay, có `verified_by`); view `observation_spliced` nhân hệ số cho đoạn cũ **lúc đọc**. Ba lý do đổi: (a) số đã nối là **số mình tự tính** — luật tầng tự tính cấm trộn vào bảng sự thật; (b) cùng pattern với `price_factor` đã duyệt — một kiểu tư duy cho cả kho; (c) phát hiện break mới = **thêm một dòng registry, không rewrite dữ liệu** (cách cũ phải UPDATE toàn bộ đoạn cũ). Lưu ý phạm vi: hệ số áp cho **toàn bộ đoạn trước điểm gãy**, không phải "quanh điểm gãy" (mô tả cũ sai).
- **Bẫy parse ở tầng ETL** (ghi để plan kiểm, không ảnh hưởng DDL): epoch WiChart phải parse múi giờ `Asia/Ho_Chi_Minh` (lệch UTC = lệch cả chuỗi 1 ngày/1 tháng); FRED giá trị thiếu là chuỗi `"."` chứ không phải null; 🔴 **cổng chống WAF của SBV** *(vòng 3, B7-7)* — WAF chặn trả **HTTP 200 kèm body 246 byte** "Request Rejected": trước khi parse/ghi bất cứ đâu phải kiểm **độ dài body** (trang thật ~414 KB, dưới 10 KB là bị chặn) **và** chuỗi mốc `KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ`; thiếu một trong hai → báo động, **không ghi kho, không ghi staging**.
- **Hoãn có chủ đích:** bảng vintage FRED (lưu mọi phiên bản của một con số, phục vụ backtest "biết gì tại thời điểm nào") — chỉ làm khi thật sự backtest, đã ghi ở bước 11 spec cũ, giữ nguyên quyết định.

### 2.1 Quy ước ngày neo kỳ — một luật duy nhất

Chuỗi tháng/quý/năm cần một ngày đại diện cho kỳ. Chuẩn của mình: **`obs_date` = ngày đầu kỳ** — tháng 7/2026 → `2026-07-01`; quý 2/2026 → `2026-04-01`; năm 2026 → `2026-01-01`. Trùng quy ước FRED; còn WiChart neo kiểu khác (quý neo tháng cuối, năm thì bất nhất giữa các chuỗi) — ETL quy đổi hết về luật này tại cổng. Một luật, không ngoại lệ, để JOIN hai chuỗi bất kỳ theo `obs_date` luôn đúng kỳ.

*Chuỗi tuần (`freq='w'`): CHECK để sẵn nhưng 15 series FRED và 26 key WiChart hiện tại **không có chuỗi tuần nào** — quy ước neo tuần quyết khi có chuỗi tuần thật đầu tiên, không bịa trước (review 2026-08-25).*

## 3. Cụm OMO — ba bảng: phiên, kết quả, dòng bơm-hút

Nghiệp vụ: SBV đấu thầu bơm/hút tiền qua kênh thị trường mở; trang kết quả **chỉ hiện phiên mới nhất, không có kho lưu** → crawl từ ngày đầu, mỗi ngày bỏ lỡ là mất vĩnh viễn (việc gấp nhóm [2] của roadmap).

```sql
CREATE TABLE macro.omo_session (          -- mỗi phiên ĐÃ CRAWL một dòng
  session_date      date PRIMARY KEY,     -- lấy từ TIÊU ĐỀ bài của SBV, cấm lấy ngày hệ thống
  crawled_at        timestamptz NOT NULL,
  has_reverse_repo  boolean NOT NULL,     -- có nhóm "Mua kỳ hạn"  (bơm có kỳ hạn)
  has_repo          boolean NOT NULL,     -- có nhóm "Bán kỳ hạn"  (hút có kỳ hạn) — review vòng 2, C1
  has_outright_sale boolean NOT NULL,     -- có nhóm "Bán hẳn"     (hút, tín phiếu)
  note              text
);
-- Vắng nhóm là DỮ KIỆN: phiên không có "Bán hẳn" nghĩa là hôm đó SBV không phát hành
-- tín phiếu — cờ false ghi nhận điều đó, khác hẳn "chưa crawl" (không có dòng).
-- Cột "Loại hình giao dịch" của SBV có BA giá trị (sbv-omo.md §4) — bản đầu chỉ mô hình hoá
-- hai nhóm từng quan sát được; thiếu 'Bán kỳ hạn' thì phiên đầu tiên có nó sẽ vỡ CHECK
-- giữa job, đúng nguồn không backfill được (review vòng 2, C1).

CREATE TABLE macro.omo_auction (          -- kết quả: một dòng = (phiên × loại hình × kỳ hạn)
  session_date  date NOT NULL REFERENCES macro.omo_session,
  op_type       text NOT NULL CHECK (op_type IN ('reverse_repo','repo','outright_sale')),
  tenor_days    smallint NOT NULL,        -- 7|14|21|28|35|56|63|91|140
  participants  smallint,                 -- số thành viên tham gia
  winners       smallint,                 -- số trúng thầu
  volume_vnd    numeric NOT NULL,         -- VND ĐƠN VỊ GỐC — nguồn công bố tỷ VND, ETL nhân 1e9
                                          -- tại cổng ('6.307,47' tỷ → 6.30747e12); giữ luật
                                          -- "kho không có nghìn/tỷ" của bước 1 (review vòng 2, C2)
  rate_pct      numeric,                  -- %/năm
  ingested_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (session_date, op_type, tenor_days)
);

CREATE TABLE macro.omo_flow (             -- TỰ DỰNG toàn phần từ omo_auction (luật bước 8)
  flow_date       date PRIMARY KEY,
  injection_vnd   numeric NOT NULL,       -- bơm trong ngày (VND)
  maturing_vnd    numeric NOT NULL,       -- đáo hạn: phiên (D−k, kỳ hạn k) đến hạn tại D
  net_vnd         numeric NOT NULL,       -- ròng = bơm − đáo hạn (dương = bơm ròng)
  outstanding_vnd numeric,                -- đang lưu hành (cộng dồn)
  complete        boolean NOT NULL DEFAULT false
);
-- complete(D) — HAI điều kiện, thiếu một là false (định nghĩa lại ở vòng 3, B7-6):
-- (1) kho đã có ≥140 ngày lịch sử trước D (kỳ hạn dài nhất);
-- (2) KHÔNG THIẾU PHIÊN NÀO trong cửa sổ [D−140, D] — đối chiếu omo_session với lịch ngày
--     làm việc để phân biệt "không crawl" (hỏng cửa sổ) với "SBV không đấu thầu" (bình thường).
-- Bỏ lỡ một phiên là hỏng cả cửa sổ 140 ngày sau đó, không vá được (sbv-omo.md §8) — chỉ mã
-- hoá điều kiện (1) sẽ cho net_vnd thiếu vế đáo hạn mà vẫn complete=true: sai có hệ thống.
-- Chiều dấu theo op_type khi dựng flow: reverse_repo phát hành = BƠM, đáo hạn = hút;
-- repo và outright_sale phát hành = HÚT (đáo hạn của repo = bơm trả lại). Công thức tổng
-- quát chốt trong plan; chiều của repo/outright_sale CHƯA KIỂM trên phiên thật.
```

- **Ngữ nghĩa ghi:** `omo_session`/`omo_auction` append-only; ngày trong tiêu đề **trùng ngày đã có** → phiên cũ chưa cập nhật, bỏ qua không ghi đè. `omo_flow` rebuild toàn phần idempotent — đúng ba luật tầng tự tính (README).
- SBV không công bố đáo hạn/ròng/đang lưu hành — cả ba **tự dựng** từ kỳ hạn (dòng ngày D kỳ hạn k sinh khoản đáo hạn tại D+k). Chiều dấu nhóm "Bán hẳn" (phát hành = hút) **chưa kiểm trên phiên thật** — ghi ở ETL, kiểm khi gặp.
- HTML gốc mỗi phiên (~414 KB) lưu ở `staging` (bước 7) — markup viết tay của SBV có thể đổi và không tải lại được.

## 4. Điểm cần duyệt ở bước này

- [ ] **Chỉ tiêu mang mã của mình** (`vn.cpi`, `us.fedfunds`…), nguồn chỉ nằm trong bảng ánh xạ kèm hệ số đơn vị — đồng ý?
- [ ] **Một bảng `observation` chung** cho mọi chỉ tiêu (dạng dài như BCTC bước 3), ghi kiểu **UPSERT** vì nguồn vá số quá khứ — đồng ý?
- [ ] **Ngày neo kỳ = ngày đầu kỳ**, một luật cho mọi chuỗi tháng/quý/năm — đồng ý?
- [ ] **Đứt gãy chuỗi**: bảng lưu số **như nguồn công bố**; hệ số nối đăng ký duyệt tay vào `series_break`; bản đã nối là **view** `observation_spliced` tính lúc đọc *(viết lại theo F2 — bản cũ của ô này mô tả thiết kế hai-cột đã bị thay; review vòng 2, I8)* — đồng ý?
- [ ] **OMO ba bảng**: phiên đã crawl (vắng nhóm là dữ kiện) · kết quả thầu · dòng bơm-hút tự dựng có cờ `complete` — đồng ý?

## 5. Kiểm chứng của bước này (seam)

1. UPSERT observation: ghi lại `(indicator, obs_date)` đã có với giá trị mới (literal 159001 → 158927, mô phỏng FRED vá `PAYEMS`) → 1 dòng, giá trị mới.
2. Neo kỳ: epoch WiChart của "Tháng 07/2026" (giải tay ra `2026-07-01` theo múi giờ VN) → `obs_date='2026-07-01'`; parse UTC sẽ ra `2026-06-30` — test bắt đúng bẫy này.
3. Splice qua view: chuỗi 4 điểm + một break factor 1,6005 (literal từ ca GDP thật) → `observation_spliced` trả đoạn **trước** break = gốc × 1,6005, đoạn sau giữ nguyên; bảng `observation` không đổi một dòng nào khi thêm break.
3b. **Case biên bắt buộc** *(vòng 3, I-6)*: chỉ tiêu **không có** dòng `series_break` nào → `value_spliced = value_as_published` (không NULL) — đây là đường đi của đại đa số chỉ tiêu.
4. `omo_flow` giải tay *(đơn vị VND gốc — C2)*: phiên D bơm 6.307,47 tỷ kỳ hạn 7 ngày; phiên D+7 bơm 5.000 tỷ → `maturing_vnd(D+7) = 6 307 470 000 000`, `net_vnd(D+7) = −1 307 470 000 000`.
5. Parse số VN + nhân đơn vị: `'6.307,47'` (tỷ) → `6.30747e12` VND (literal); `float()` thẳng trên chuỗi phải fail test này.
5b. `op_type='repo'` hợp lệ (nhóm "Bán kỳ hạn" — C1); `op_type` lạ → lỗi CHECK.
6. `freq='x'` → lỗi CHECK; `omo_auction.op_type` lạ → lỗi CHECK; chèn auction cho phiên chưa có trong `omo_session` → lỗi FK.

Chốt xong → bước 5 (asset: giá tài sản — hàng hoá, FX, chỉ số quốc tế, crypto).
