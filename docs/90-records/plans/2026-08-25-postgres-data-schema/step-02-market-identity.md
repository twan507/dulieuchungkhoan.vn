# Bước 2 — Định danh: doanh nghiệp, mã chứng khoán, bộ ngành riêng

**Trạng thái:** 🟡 chờ duyệt · **Phụ thuộc:** bước 1 (✅) · **Phạm vi:** các bảng "ai là ai" của schema `market` — nền cho mọi bảng dữ liệu ở bước 3 và cho tin gắn mã ở bước 6.

---

## 1. Hai thực thể, không phải một

Nguồn FiinTrade trộn hai khái niệm trong `organization`. Mình tách:

- **`issuer`** — doanh nghiệp phát hành: chủ của BCTC, sự kiện quyền, hồ sơ, **ngành**.
- **`security`** — mã giao dịch: chủ của giá. Gồm cả ETF và chỉ số (chỉ số không có issuer).

```
icb_industry (tham khảo)      industry (BỘ NGÀNH RIÊNG — chuẩn)
        ▲                            ▲
        │ icb_code                   │ industry_id
        └────────────┐   ┌───────────┘
                   issuer ──────◄ issuer_external_id   (organ_code từng nguồn)
                     ▲ issuer_id (NULL với index)
                  security ─────◄ security_external_id (symbol từng nguồn)
```

## 2. DDL

```sql
CREATE TABLE market.industry (            -- bộ ngành RIÊNG của dự án
  industry_id  bigint generated always as identity PRIMARY KEY,
  code         text NOT NULL UNIQUE,      -- mã ngắn tự đặt, vd 'bank'
  name_vi      text NOT NULL,
  parent_id    bigint REFERENCES market.industry,   -- NULL = cấp gốc
  level        smallint NOT NULL DEFAULT 1,
  sort_order   smallint
);
-- Cây tự tham chiếu: chịu được 1 cấp, 2 cấp hay nhiều cấp.
-- NỘI DUNG bộ ngành là DỮ LIỆU, chủ dự án cung cấp sau — không chặn migration.

CREATE TABLE market.industry_icb_map (    -- ICB (nguồn) → ngành riêng: gán hàng loạt
  icb_code    text PRIMARY KEY,           -- + tự gán mã mới niêm yết
  industry_id bigint NOT NULL REFERENCES market.industry
);

CREATE TABLE market.icb_industry (        -- cây ICB của nguồn — CHỈ THAM KHẢO
  icb_code        text PRIMARY KEY,
  icb_name        text,
  parent_icb_code text,
  icb_level       smallint,               -- 1..4
  icb_code_path   text                    -- '8000/8300/8350'
);

CREATE TABLE market.issuer (
  issuer_id     bigint generated always as identity PRIMARY KEY,
  name          text NOT NULL,
  short_name    text,
  com_type_code text,                     -- NH|CT|CK|BH|QU — quyết định endpoint snapshot
  industry_id   bigint REFERENCES market.industry,  -- MỖI DOANH NGHIỆP 1 NGÀNH (chuẩn GICS/ICB)
  icb_code      text REFERENCES market.icb_industry,-- tham khảo, không phải chuẩn
  updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE market.issuer_external_id (
  issuer_id     bigint NOT NULL REFERENCES market.issuer,
  source        text NOT NULL,            -- 'fiintrade'
  external_code text NOT NULL,            -- organ_code — 41% khác ticker, 72 mã là mã số thuế
  PRIMARY KEY (source, external_code),
  UNIQUE (issuer_id, source)
);

CREATE TABLE market.security (
  security_id   bigint generated always as identity PRIMARY KEY,
  ticker        text NOT NULL,            -- thuộc tính hiển thị, KHÔNG phải khoá
  exchange      text,                     -- HOSE|HNX|UPCOM
  security_type text NOT NULL CHECK (security_type IN ('stock','etf','index','fund_cert')),
  issuer_id     bigint REFERENCES market.issuer,    -- NULL với index
  status        text NOT NULL DEFAULT 'listed' CHECK (status IN ('listed','delisted')),
  tradelot      int,
  full_name     text,
  updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ON market.security (ticker, exchange) WHERE status = 'listed';
CREATE INDEX ON market.security (ticker);

CREATE TABLE market.security_external_id (
  security_id   bigint NOT NULL REFERENCES market.security,
  source        text NOT NULL,            -- 'fiintrade'|'bvsc'|'yahoo'…
  external_code text NOT NULL,
  PRIMARY KEY (source, external_code),
  UNIQUE (security_id, source)
);
```

## 3. Luật nghiệp vụ

1. **Ngành gán ở doanh nghiệp, mã thừa hưởng** — trùng chuẩn quốc tế (GICS/ICB: một doanh nghiệp một ngành theo hoạt động chính) và trùng thói quen phân tích của chủ dự án. ETF/chỉ số không có ngành.
2. **Bộ ngành riêng là chuẩn duy nhất khi hiển thị/phân tích.** ICB chỉ dùng để: (a) nạp nhanh — anh map mỗi nhánh ICB về ngành của anh một lần trong `industry_icb_map` thay vì gán tay ~2.000 mã; (b) tự gán mã mới niêm yết; (c) đối chiếu khi nghi gán sai. `issuer.industry_id` gán tay được và **tay thắng máy** (ETL không ghi đè giá trị đã gán tay — cơ chế chốt trong plan thực thi).
3. **Chứng quyền, lô lẻ, trái phiếu không nạp** — loại có chủ đích (CLAUDE.md §2.2), `security_type` không có giá trị cho chúng.
4. **ETL tra `*_external_id` để gọi nguồn** — không bao giờ truyền ticker (bẫy `organCode ≠ ticker`: HTTP 200 kèm dữ liệu rỗng).
5. **Lọc mã huỷ niêm yết bằng `status`** — danh bạ FiinTrade gồm cả mã đã rời sàn; đối chiếu `getAllQuotes` BVSC để đặt `status`, lọc động không hardcode con số. Tin (bước 6) và mọi phép phân tích mặc định chỉ nhìn `listed`.
6. **Skill không cố định danh sách ngành** (hợp đồng architecture §3.2) — trước ghi "khung ngành = ICB", nay khung ngành do `market.industry` cung cấp. Hợp đồng không đổi bản chất: hệ dữ liệu cấp khung + mã ngành từng doanh nghiệp, skill cấp tiêu chí phân bậc. Cập nhật tài liệu sống khi spec chốt xong.

## 4. Kiểm chứng của bước này (seam)

1. Unique một phần: hai dòng cùng `(ticker, exchange)` cùng `listed` → lỗi; một dòng `delisted` → hợp lệ.
2. `security_external_id`: trùng `(source, external_code)` → lỗi; cùng `external_code` khác `source` → hợp lệ.
3. Cây ngành: chèn ngành con trỏ `parent_id` không tồn tại → lỗi FK; cây 2 cấp mẫu (literal) truy ngược con→cha đúng.
4. `industry_icb_map`: một `icb_code` chỉ map một ngành (PK); map tới `industry_id` không tồn tại → lỗi FK.

## 5. Điểm cần duyệt ở bước này

- [ ] Tách `issuer` / `security`, chỉ số không có issuer — đồng ý?
- [ ] Ngành: cây tự tham chiếu chờ nội dung của anh + gán ở doanh nghiệp (mã thừa hưởng) + tay thắng máy — đồng ý?
- [ ] ICB giữ tham khảo đúng vai trò §3.2 (nạp nhanh, tự gán mã mới, đối chiếu) — đồng ý?
- [ ] `status` listed/delisted + unique một phần theo `(ticker, exchange)` — đồng ý?

Chốt xong → bước 3 (bảng dữ liệu market: giá EOD, BCTC, snapshot, sự kiện).
