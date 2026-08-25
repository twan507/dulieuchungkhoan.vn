# Bước 1 — Nền móng: nguyên tắc, bố cục schema, quy ước DDL, migration

**Trạng thái:** ✅ chốt 2026-08-25 (chủ dự án duyệt sau đối chiếu chuẩn ngành) · **Phạm vi bước này:** chỉ khung — chưa có bảng dữ liệu nào. Bảng cụ thể nằm ở bước 2–7.

---

## 1. Nguyên tắc xương sống

1. **Mô hình canonical do mình sở hữu.** Bảng dữ liệu dùng khoá nội bộ và khái niệm của mình. Mã của nguồn (organ_code, WiChart key, FRED series_id, symbol Yahoo…) chỉ xuất hiện trong **bảng ánh xạ registry** — ETL tra ánh xạ để biết gọi đâu, ghi vào đâu. Đổi nguồn = sửa ánh xạ, bảng dữ liệu không đổi.
2. **Không cột `source` ở bảng dữ liệu** *(quyết định chủ dự án 2026-08-25)*. Xuất xứ khi cần truy vết nằm ở: bảng ánh xạ registry (chuỗi nào lấy từ đâu), `staging.raw_payload` (payload thô từng đợt nạp), `ops` (nhật ký chạy). Hai chuỗi cùng bản chất nhưng khác nguồn/khác mốc chốt (vàng LBMA fixing vs vàng spot) là **hai mã series riêng** trong registry — không cần cột source để phân biệt. Ngoại lệ duy nhất: `news` ghi báo nào đăng, vì đó là dữ kiện nghiệp vụ chứ không phải xuất xứ kỹ thuật.
3. **ETL chuẩn hoá tại cổng.** Vào tới bảng dữ liệu thì: ngày là `date` đã quy về giờ Việt Nam (bẫy epoch WiChart), giá trị là `numeric` ở **đơn vị gốc** (hệ số nhân sai-nhãn của nguồn áp ở ETL, kho không có "nghìn/tỷ"), tiền tệ ghi tường minh ở registry (USDT ≠ USD, GBp ≠ GBP).
4. **Cột meta nghiệp vụ** ở bảng giá/chuỗi khi áp dụng: `price_type` (spot/futures/fixing/close — chống bậc nhảy 2% khi trộn loại giá). ~~`is_derived`~~ *(gạch theo review vòng 2, 2026-08-25 — M1: luật tầng tự tính ra đời sau đã thay nó bằng cách mạnh hơn — số tự tính nằm ở **bảng/view tách riêng** (`omo_flow`, `observation_spliced`, DXY dựng lại ở bước 8), nên không còn bảng sự thật nào cần cờ này).*
5. **Không ghi đè sự thật lịch sử.** Giá thô bất biến, điều chỉnh lúc đọc (view hệ số); tin sửa thì thêm version; riêng chuỗi bị nguồn **vá hồi tố** (FRED) thì UPSERT có chủ đích — từng bảng ghi rõ ngữ nghĩa ghi của nó.
6. **Phân ngành theo bộ riêng của chủ dự án** — không lấy cây ICB làm chuẩn. Cấu trúc bộ ngành + cách gán mã chốt ở bước 2.

## 2. Bố cục: sáu schema trong `postgres-data`

```
postgres-data                     (người ghi duy nhất: etl · api chỉ đọc)
├── market    chứng khoán Việt Nam
├── macro     chỉ tiêu vĩ mô VN + quốc tế, OMO
├── asset     giá tài sản: hàng hoá · FX · chỉ số quốc tế · crypto
├── news      tin tức toàn văn + tìm kiếm
├── staging   payload thô theo đợt nạp (landing zone)
├── ops       trạng thái miền · giám sát hợp đồng · nhật ký ETL
└── extensions  chỗ cài 4 extension — không phải miền dữ liệu, không có bảng
```

*(Tổng cộng migration 0001 tạo **7 schema**: 6 schema miền + `extensions` — vòng 4, F2: bản trước chốt "cài extension vào schema riêng" nhưng quên tạo và quên đếm nó.)*

- Ranh giới theo **miền tiêu thụ** (người dùng/API hỏi gì), không theo nguồn.
- Mối nối chéo schema tối thiểu — chỉ theo **một chiều** `news` → `market.security` (hai FK: gắn mã bài viết và bảng tên thương mại — *đếm lại theo review vòng 2*; cùng instance nên FK hợp lệ; luật cấm JOIN chỉ áp **giữa hai instance** data/app).
- **Ranh giới ClickHouse:** tick, sổ lệnh, nến intraday ở ClickHouse (phiên thiết kế riêng). Postgres giữ mọi thứ EOD/REST/BCTC/vĩ mô/tài sản/tin. Điểm nối duy nhất: ClickHouse cần view hệ số điều chỉnh giá từ `market` (cơ chế thuộc phiên ClickHouse).
- `postgres-app` (tài khoản, watchlist…): instance riêng, env migration riêng, dựng khi làm `api` auth — ngoài phạm vi spec này.
- **Khoá schema `public`** (thu quyền CREATE, không đặt object nào vào đó) — khuyến nghị chuẩn Postgres, tránh object lạc trôi ngoài 6 schema.
- **Phân quyền theo schema**: role của `etl` có quyền ghi; role của `api` chỉ `SELECT` trên **4 schema miền** (`market`/`macro`/`asset`/`news`), **không thấy `staging` và `ops`** — thi hành luật "một người ghi" bằng chính DB, không chỉ bằng kỷ luật code. *(Review 2026-08-25: câu cũ ghi "5 schema" đá nhau với bước 7 — thống nhất về 4.)*

*Đối chiếu chuẩn ngành (tra cứu 2026-08-25):* bố cục này khớp 4 pattern chuẩn — schema-per-domain của Postgres; staging thô → canonical (medallion Bronze/Silver, gốc Kimball); security master + bảng symbology cross-reference (Intrinio/GS Marquee/OpenFIGI); và cách FRED/ALFRED tách giá trị hiện hành khỏi kho vintage.

## 3. Quy ước DDL

| Quy ước | Chốt |
|---|---|
| Tên bảng/cột | tiếng Anh, `snake_case`, tránh từ khoá SQL phải quote |
| Khoá nhân tạo | `bigint generated always as identity` |
| Thời điểm nạp | mọi bảng do ETL ghi có ít nhất một timestamp nạp — tên chuẩn `ingested_at timestamptz not null default now()`; bảng có timestamp nghiệp vụ đặc thù thay thế (`crawled_at` phiên OMO, `content_fetched_at` bản text tin) thì ghi rõ tại chỗ; bảng registry duyệt tay (`series_break`) dùng `verified_at` *(luật miễn trừ — review vòng 2, M4)*. Registry do ETL nạp (`icb_industry`, `*_external_id`, `metric_dictionary`, `indicator_source`…) **cũng mang `ingested_at`** — DDL nháp trong các bước lược cột này cho gọn, plan bổ sung đồng loạt *(review vòng 3, M-2)* |
| Số | `numeric` không ép precision |
| Ngày quan sát | `date` (quy ước neo kỳ của chuỗi tháng/quý ghi ở bước 4) |
| Enum nghiệp vụ | `check` constraint, không dùng kiểu `ENUM` của Postgres (sửa giá trị đỡ đau) |
| Qualify schema | **Mọi SQL của backend luôn ghi đủ `schema.bảng`** — hai bảng trùng tên khác schema tồn tại có chủ đích (`market.price_daily` vs `asset.price_daily`), query không qualify sẽ trúng bảng khác theo search_path mà không báo *(vòng 4, F13)* |
| Extension | `unaccent` · `pg_trgm` · `vector` · `fuzzystrmatch` — bật từ migration đầu, **cài vào schema riêng `extensions`** (khoá `public` mà không chốt chỗ cài extension là tự đá nhau — review vòng 3, I-7). Hệ quả plan phải giữ: hàm bọc `news.immutable_unaccent` cố định `search_path`/qualify đầy đủ, opclass ghi `extensions.gin_trgm_ops`. *(`fuzzystrmatch` bổ sung 2026-08-25 khi duyệt bước 6 — luật "bước sau phát hiện thiếu")* |

## 4. Migration — Alembic

- Thư mục `database/`: `alembic.ini` + env cho `postgres-data` + `versions/`. Cấu trúc chính xác chốt trong plan thực thi.
- Migration viết **SQL thô** (`op.execute`) — kiểm soát từng dòng, không autogenerate từ ORM.
- Migration `0001`: tạo **7 schema** (6 miền + `extensions`, tạo `extensions` TRƯỚC khi `CREATE EXTENSION … SCHEMA extensions`) + **4 extension**. Các migration sau đi theo từng bước đã duyệt. *(Vòng 2 I7 sửa số extension; vòng 4 F2 sửa số schema.)*
- Connection string: `DATA_DATABASE_URL` (env này) · `APP_DATABASE_URL` (để dành cho `postgres-app`).

## 5. Kiểm chứng của bước này (seam)

1. `alembic upgrade head` trên DB test rỗng → đủ 7 schema, 4 extension (nằm trong `extensions`).
2. `alembic downgrade base` → DB sạch, không sót object.

## 6. Điểm cần duyệt ở bước này

- [ ] Sáu schema và ranh giới như §2 — đồng ý?
- [ ] Nguyên tắc "không cột source ở bảng dữ liệu, xuất xứ nằm ở registry/staging/ops" như §1.2 — đúng ý anh?
- [ ] ~~Hai cột meta `price_type`/`is_derived` được giữ~~ → còn **một cột `price_type`** (nghiệp vụ, không phải nguồn) — `is_derived` đã gạch ở §1.4 *(ô duyệt sửa theo review vòng 3 — bản cũ đá nhau với thân file)* — đồng ý?
- [ ] Quy ước DDL §3 và cách chạy migration §4 — đồng ý?

Chốt bước này xong → viết bước 2 (định danh + bộ ngành riêng).
