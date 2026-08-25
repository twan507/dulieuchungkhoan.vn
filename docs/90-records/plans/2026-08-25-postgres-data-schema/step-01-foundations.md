# Bước 1 — Nền móng: nguyên tắc, bố cục schema, quy ước DDL, migration

**Trạng thái:** 🟡 chờ duyệt · **Phạm vi bước này:** chỉ khung — chưa có bảng dữ liệu nào. Bảng cụ thể nằm ở bước 2–7.

---

## 1. Nguyên tắc xương sống

1. **Mô hình canonical do mình sở hữu.** Bảng dữ liệu dùng khoá nội bộ và khái niệm của mình. Mã của nguồn (organ_code, WiChart key, FRED series_id, symbol Yahoo…) chỉ xuất hiện trong **bảng ánh xạ registry** — ETL tra ánh xạ để biết gọi đâu, ghi vào đâu. Đổi nguồn = sửa ánh xạ, bảng dữ liệu không đổi.
2. **Không cột `source` ở bảng dữ liệu** *(quyết định chủ dự án 2026-08-25)*. Xuất xứ khi cần truy vết nằm ở: bảng ánh xạ registry (chuỗi nào lấy từ đâu), `staging.raw_payload` (payload thô từng đợt nạp), `ops` (nhật ký chạy). Hai chuỗi cùng bản chất nhưng khác nguồn/khác mốc chốt (vàng LBMA fixing vs vàng spot) là **hai mã series riêng** trong registry — không cần cột source để phân biệt. Ngoại lệ duy nhất: `news` ghi báo nào đăng, vì đó là dữ kiện nghiệp vụ chứ không phải xuất xứ kỹ thuật.
3. **ETL chuẩn hoá tại cổng.** Vào tới bảng dữ liệu thì: ngày là `date` đã quy về giờ Việt Nam (bẫy epoch WiChart), giá trị là `numeric` ở **đơn vị gốc** (hệ số nhân sai-nhãn của nguồn áp ở ETL, kho không có "nghìn/tỷ"), tiền tệ ghi tường minh ở registry (USDT ≠ USD, GBp ≠ GBP).
4. **Hai cột meta nghiệp vụ** ở bảng giá/chuỗi khi áp dụng: `price_type` (spot/futures/fixing/close — chống bậc nhảy 2% khi trộn loại giá) và `is_derived` (số tự dựng: DXY, bơm ròng OMO). Cả hai là dữ kiện nghiệp vụ, không phải xuất xứ.
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
└── ops       trạng thái miền · giám sát hợp đồng · nhật ký ETL
```

- Ranh giới theo **miền tiêu thụ** (người dùng/API hỏi gì), không theo nguồn.
- Mối nối chéo schema tối thiểu — hiện chỉ một: tin gắn mã → `market.security` (cùng instance nên FK hợp lệ; luật cấm JOIN chỉ áp **giữa hai instance** data/app).
- **Ranh giới ClickHouse:** tick, sổ lệnh, nến intraday ở ClickHouse (phiên thiết kế riêng). Postgres giữ mọi thứ EOD/REST/BCTC/vĩ mô/tài sản/tin. Điểm nối duy nhất: ClickHouse cần view hệ số điều chỉnh giá từ `market` (cơ chế thuộc phiên ClickHouse).
- `postgres-app` (tài khoản, watchlist…): instance riêng, env migration riêng, dựng khi làm `api` auth — ngoài phạm vi spec này.
- **Khoá schema `public`** (thu quyền CREATE, không đặt object nào vào đó) — khuyến nghị chuẩn Postgres, tránh object lạc trôi ngoài 6 schema.
- **Phân quyền theo schema**: role của `etl` có quyền ghi; role của `api` chỉ `SELECT` trên 5 schema dữ liệu (không thấy `staging`) — thi hành luật "một người ghi" bằng chính DB, không chỉ bằng kỷ luật code.

*Đối chiếu chuẩn ngành (tra cứu 2026-08-25):* bố cục này khớp 4 pattern chuẩn — schema-per-domain của Postgres; staging thô → canonical (medallion Bronze/Silver, gốc Kimball); security master + bảng symbology cross-reference (Intrinio/GS Marquee/OpenFIGI); và cách FRED/ALFRED tách giá trị hiện hành khỏi kho vintage.

## 3. Quy ước DDL

| Quy ước | Chốt |
|---|---|
| Tên bảng/cột | tiếng Anh, `snake_case`, tránh từ khoá SQL phải quote |
| Khoá nhân tạo | `bigint generated always as identity` |
| Thời điểm nạp | mọi bảng dữ liệu có `ingested_at timestamptz not null default now()` |
| Số | `numeric` không ép precision |
| Ngày quan sát | `date` (quy ước neo kỳ của chuỗi tháng/quý ghi ở bước 4) |
| Enum nghiệp vụ | `check` constraint, không dùng kiểu `ENUM` của Postgres (sửa giá trị đỡ đau) |
| Extension | `unaccent` · `pg_trgm` · `vector` — bật từ migration đầu |

## 4. Migration — Alembic

- Thư mục `database/`: `alembic.ini` + env cho `postgres-data` + `versions/`. Cấu trúc chính xác chốt trong plan thực thi.
- Migration viết **SQL thô** (`op.execute`) — kiểm soát từng dòng, không autogenerate từ ORM.
- Migration `0001`: tạo 6 schema + 3 extension. Các migration sau đi theo từng bước đã duyệt (bước 2 → một cụm migration, v.v.).
- Connection string: `DATA_DATABASE_URL` (env này) · `APP_DATABASE_URL` (để dành cho `postgres-app`).

## 5. Kiểm chứng của bước này (seam)

1. `alembic upgrade head` trên DB test rỗng → đủ 6 schema, 3 extension.
2. `alembic downgrade base` → DB sạch, không sót object.

## 6. Điểm cần duyệt ở bước này

- [ ] Sáu schema và ranh giới như §2 — đồng ý?
- [ ] Nguyên tắc "không cột source ở bảng dữ liệu, xuất xứ nằm ở registry/staging/ops" như §1.2 — đúng ý anh?
- [ ] Hai cột meta `price_type`/`is_derived` được giữ (chúng là nghiệp vụ, không phải nguồn) — đồng ý?
- [ ] Quy ước DDL §3 và cách chạy migration §4 — đồng ý?

Chốt bước này xong → viết bước 2 (định danh + bộ ngành riêng).
