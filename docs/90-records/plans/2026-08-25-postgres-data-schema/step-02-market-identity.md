# Bước 2 — Định danh: doanh nghiệp, mã chứng khoán, bộ ngành riêng

**Trạng thái:** ✅ chốt 2026-08-25 (chủ dự án đồng ý cả 4 điểm duyệt) · **Phụ thuộc:** bước 1 (✅) · **Phạm vi:** các bảng "ai là ai" của schema `market` — nền cho mọi bảng dữ liệu ở bước 3 và cho tin gắn mã ở bước 6.

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
CREATE TABLE market.industry (            -- bộ ngành RIÊNG — nội dung: docs/20-design/industry-tree.md
  industry_id  bigint generated always as identity PRIMARY KEY,
  code         text NOT NULL UNIQUE,      -- viết hoa không dấu: 'TAICHINH', 'NGANHANG' (luật đặt tên §3 industry-tree)
  name_vi      text NOT NULL,             -- 'Ngân hàng và Tín dụng'
  parent_id    bigint REFERENCES market.industry,
  level        smallint NOT NULL CHECK (level IN (1,2)),  -- cây đã chốt 2 CẤP: 6 nhóm × 24 ngành
  sort_order   smallint,
  CHECK ((level = 1) = (parent_id IS NULL))  -- nhóm không có cha, ngành bắt buộc có cha
);
-- Level 1 chỉ phục vụ điều hướng web; chỉ số phân tích (dòng tiền, breadth, xếp hạng)
-- đọc ở level 2 — cấp có "sóng ngành" thật (industry-tree §1). Không tính chỉ số tổng hợp level 1.
-- SEED: nạp từ industry-tree.md (chủ sở hữu nội dung duy nhất) trong migration seed;
-- test đối chiếu bảng sau seed với file (6 + 24 code) để hai bản không trôi lệch.

CREATE TABLE market.industry_icb_map (    -- ICB (nguồn) → ngành riêng: gán hàng loạt
  icb_code    text PRIMARY KEY,           -- + tự gán mã mới niêm yết
  industry_id bigint NOT NULL REFERENCES market.industry
);
-- LUẬT PHÂN GIẢI (review vòng 2, I10): map đăng ký ở CẤP NHÁNH ICB, còn issuer mang mã LÁ
-- (cấp 4) — hai cấp không join thẳng được. Thứ tự tra: khớp icb_code chính xác trước;
-- không có thì leo icb_code_path ('8000/8300/8350') lấy TỔ TIÊN GẦN NHẤT có trong map.
-- Mã ICB lạ chưa có trong cây → industry_id để NULL + cảnh báo, không chặn job.

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
  industry_id   bigint REFERENCES market.industry,  -- MỖI DOANH NGHIỆP 1 NGÀNH, luôn là LEVEL 2
                                                    -- (nhóm suy từ cha — không gán nhóm trực tiếp)
  icb_code      text,                               -- tham khảo THUẦN, KHÔNG FK — review vòng 3 C-2:
                                                    -- FK sẽ chặn job danh bạ khi nguồn trả icbCode
                                                    -- chưa có trong cây (2 endpoint khác nhịp),
                                                    -- trái luật "mã ICB lạ không chặn job" ở trên
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
  exchange      text NOT NULL,            -- HOSE|HNX|UPCOM — NOT NULL vì unique một phần
                                          -- (ticker, exchange) sẽ thủng với NULL (NULLS DISTINCT;
                                          --  review 2026-08-25)
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
  external_sub  text NOT NULL DEFAULT '', -- ngữ cảnh mã trong CÙNG nguồn — review vòng 3 I-3:
                                          -- BVSC dùng HAI bộ mã chỉ số song song (TVC 'VNINDEX'
                                          -- vs getIndexSnapshots 'HOSE'); VN-Index cần cả hai
                                          -- dòng, đối xứng với macro/asset registry
  PRIMARY KEY (source, external_code),
  UNIQUE (security_id, source, external_sub)
);
```

## 3. Luật nghiệp vụ

1. **Ngành gán ở doanh nghiệp, mã thừa hưởng** — trùng chuẩn quốc tế (GICS/ICB: một doanh nghiệp một ngành theo hoạt động chính) và trùng thói quen phân tích của chủ dự án. ETF/chỉ số không có ngành.
2. **Bộ ngành riêng là chuẩn duy nhất khi hiển thị/phân tích.** ICB chỉ dùng để: (a) nạp nhanh — anh map mỗi nhánh ICB về ngành của anh một lần trong `industry_icb_map` thay vì gán tay ~2.000 mã; (b) tự gán mã mới niêm yết; (c) đối chiếu khi nghi gán sai. `issuer.industry_id` gán tay được và **tay thắng máy** (ETL không ghi đè giá trị đã gán tay — cơ chế chốt trong plan thực thi). `industry_icb_map.industry_id` và `issuer.industry_id` luôn trỏ ngành **level 2**; holding đa ngành xếp theo mảng đóng góp lợi nhuận chính (industry-tree §4). Bốn ca gán lệch đã ghi nhận (TRC/DRI, nhóm gỗ, IPA, VEF — industry-tree §5) xử lý bằng gán tay khi nạp dữ liệu thật, không đổi cấu trúc.
3. **Chứng quyền, lô lẻ, trái phiếu không nạp** — loại có chủ đích (CLAUDE.md §2.2), `security_type` không có giá trị cho chúng.
3b. **Phái sinh — hoãn có chủ đích** *(review vòng 3, I-5 — trước đó vắng mặt không lý do, trái luật §1.4)*: 14 hợp đồng có dữ liệu tham chiếu/EOD ở nguồn, nhưng giá trị chính nằm ở tick realtime — thứ **chưa đo được trong phiên** (roadmap §5.1 cấm giả định). Nhận phái sinh khi đã đo: thêm `'derivative'` vào CHECK + bảng thuộc tính hợp đồng riêng (underlying, đáo hạn, openInterest). Điều kiện mở lại: đo socket phái sinh BVSC trong phiên.
4. **ETL tra `*_external_id` để gọi nguồn** — không bao giờ truyền ticker (bẫy `organCode ≠ ticker`: HTTP 200 kèm dữ liệu rỗng).
5. **Lọc mã huỷ niêm yết bằng `status`** — danh bạ FiinTrade gồm cả mã đã rời sàn; đối chiếu `getAllQuotes` BVSC để đặt `status`, lọc động không hardcode con số. Tin (bước 6) và mọi phép phân tích mặc định chỉ nhìn `listed`.
5b. **Hai bẫy danh mục phải xử ở ETL nạp danh bạ** *(review vòng 2, I12 — từ [00-conventions.md](../../../10-sources/market/00-conventions.md) bẫy 10–11)*: (a) `StockType` **không dùng làm khoá phân loại chung** — cùng một mã trả 12 ở `/quotes` nhưng 1 ở `/datafeed/instruments`; `security_type` quyết theo **một endpoint chốt trong plan**, ghi rõ. (b) **Không endpoint nào là danh mục chuẩn duy nhất** (`/quotes` 2.534 mã vs `/datafeed/instruments` 2.001) — danh bạ = **hợp nhất hai endpoint**; mã chỉ có ở một bên vẫn nạp, `exchange` lấy từ bên có nó.
6. **Skill không cố định danh sách ngành** (hợp đồng architecture §3.2) — trước ghi "khung ngành = ICB", nay khung ngành do `market.industry` cung cấp. Hợp đồng không đổi bản chất: hệ dữ liệu cấp khung + mã ngành từng doanh nghiệp, skill cấp tiêu chí phân bậc. Cập nhật tài liệu sống khi spec chốt xong.

## 4. Kiểm chứng của bước này (seam)

1. Unique một phần: hai dòng cùng `(ticker, exchange)` cùng `listed` → lỗi; một dòng `delisted` → hợp lệ.
2. `security_external_id`: trùng `(source, external_code)` → lỗi; cùng `external_code` khác `source` → hợp lệ.
2b. *(vòng 4, F4)* VN-Index mang **hai dòng cùng `source='bvsc'`** khác `external_sub` (`('bvsc','VNINDEX','tvc')` + `('bvsc','HOSE','snapshot')`) → cả hai hợp lệ, cùng trỏ một `security_id`.
3. Cây ngành: chèn level 1 có `parent_id` → lỗi CHECK; level 2 không có `parent_id` → lỗi CHECK; level 3 → lỗi CHECK. Ràng buộc "`issuer.industry_id`/`industry_icb_map.industry_id` phải trỏ level 2" thi hành bằng **seam test + guard trong ETL, không dùng trigger** (review 2026-08-25 — ghi tường minh). Tương tự, CHECK hiện có **không** ràng buộc "cha phải là level 1" — hàng rào là seed test đối chiếu literal với industry-tree.md, đủ vì bảng chỉ được ghi bởi migration seed, không có đường ghi runtime *(review vòng 3, M-9)*.
4. Seed đối chiếu `industry-tree.md`: sau seed, bảng có đúng 6 dòng level 1 + 24 dòng level 2; so khớp **danh sách code literal** (TAICHINH…NANGLUONG; NGANHANG…CONGNGHE) lấy thẳng từ file — expected độc lập với code seed.
5. `industry_icb_map`: một `icb_code` chỉ map một ngành (PK); map tới `industry_id` không tồn tại → lỗi FK.

## 5. Điểm cần duyệt ở bước này

- [ ] Tách `issuer` / `security`, chỉ số không có issuer — đồng ý?
- [ ] Ngành: cây tự tham chiếu, nội dung đã chốt ([industry-tree.md](../../../20-design/industry-tree.md)) + gán ở doanh nghiệp (mã thừa hưởng) + tay thắng máy — đồng ý?
- [ ] ICB giữ tham khảo đúng vai trò §3.2 (nạp nhanh, tự gán mã mới, đối chiếu) — đồng ý?
- [ ] `status` listed/delisted + unique một phần theo `(ticker, exchange)` — đồng ý?

Chốt xong → bước 3 (bảng dữ liệu market: giá EOD, BCTC, snapshot, sự kiện).
