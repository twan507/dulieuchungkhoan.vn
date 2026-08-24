# 0007 — Cây monorepo và stack sản phẩm

**Ngày:** 2026-08-24 · **Người quyết:** chủ dự án · **Trạng thái:** đã chốt

## Bối cảnh

Repo sẽ chứa toàn bộ sản phẩm (FE, BE, DB, tài liệu). Trước quyết định này, gốc repo chỉ có `README.md · docs/ · .claude/skills/`, trong đó `.claude/skills/` chứa hai skill **sản phẩm cho agent của web** nằm nhờ đường dẫn công cụ dev; và `docs/superpowers/` (hồ sơ quá trình) nằm lẫn cùng mặt bằng với các thư mục tri thức đánh số `00–30`.

## Quyết định

### 1 · Stack sản phẩm

| Tầng | Chốt | Lý do chính |
|---|---|---|
| Frontend | **Next.js** | Tên miền nhắm organic traffic — trang dữ liệu công khai cần SSR/SEO |
| Backend | **Python + FastAPI** | Khớp ETL + ingester + SSE async + Anthropic SDK. Django bị loại: ORM không hợp ClickHouse, SSE qua Channels lủng củng, admin dựng sẵn chưa có nhu cầu |
| Kho REST | **PostgreSQL** | Giá EOD, BCTC, sự kiện, vĩ mô, tin (tsvector + pgvector) — không đổi |
| Kho realtime | **ClickHouse** — thay TimescaleDB trong thiết kế đã duyệt | Chủ dự án chốt **lưu tick thô + sổ lệnh** từ 5 topic BVSC. Cùng logic với nến 1': không nguồn nào backfill được, ngày không ghi là mất vĩnh viễn. ClickHouse: nén cột 10–30×, materialized view tự sinh nến, TTL/tiering. Giá phải trả có ý thức: insert phải batch, không transaction, thêm một hệ quản trị |
| Pub/sub | **Redis** | Không đổi — ClickHouse là kho, không phải kênh phân phối SSE |

Kịch bản "chỉ lưu nến 1 phút" đã cân nhắc và loại: khối lượng ~540k dòng/ngày thì TimescaleDB đủ, nhưng nó đóng cửa vĩnh viễn với dữ liệu vi cấu trúc — trong khi chi phí lưu tick bằng ClickHouse gần như không đáng kể.

### 2 · Cây thư mục gốc — phẳng theo vai trò deploy

    dulieuchungkhoan.vn/
    ├── docs/
    ├── frontend/            Next.js
    ├── backend/             Python — api · etl · ingester
    │   └── agent/skills/    vn-stock-advisor · vn-stock-knowledge
    └── database/            DDL Postgres + ClickHouse · migrations

- Monorepo **đa ngôn ngữ** (Python + JS) nên khung `apps/ + packages/` kiểu Node bị loại — nó chia theo workspace tooling của một ngôn ngữ.
- Skill nằm **trong `backend/agent/`** theo nguyên tắc *ai dùng thì người đó chứa* — chỉ BE tiêu thụ lúc runtime. Phương án `agent/` ở gốc (tách vòng đời nội dung khỏi code) đã cân nhắc và loại vì là suy đoán tương lai; nếu ngày nào cần tách nhịp phát hành, một `git mv` là xong.
- `.claude/` xoá hẳn. Hệ quả có chủ đích: Claude Code không còn tự nạp skill sản phẩm khi làm việc trên repo.

### 3 · `docs/`: tri thức đánh số 00–8x, hồ sơ quá trình 9x

`docs/superpowers/` → **`docs/90-records/`** (plans · surveys · specs sau này). Quy ước: `00–8x` là tri thức đọc được theo thứ tự; `9x` là hồ sơ làm việc. Chỗ dành sẵn khi cần: `40-operations/` (runbook khi hệ chạy thật), `50-api/` (tài liệu API công khai khi có API). Phương án gộp tri thức vào `docs/knowledge/` bị loại: thêm tầng sâu và vỡ link hàng loạt chỉ để được thẩm mỹ.

## Hệ quả

1. **`docs/20-design/market-data-store.md` lỗi thời một phần** — viết cho TimescaleDB. Việc thiết kế lại kho realtime (DDL ClickHouse, materialized view sinh nến, buffer batch cho Ingester) ghi ở lộ trình §5.2, làm trước khi dựng hạ tầng.
2. Đường dẫn quy trình trong `CLAUDE.md` đổi theo: plans/surveys nằm ở `docs/90-records/`.
3. Hồ sơ lịch sử (`decisions/`, `90-records/`) giữ nguyên nội dung; chỉ href của link trỏ tới file đã dời được sửa cho khỏi treo — tiền lệ ADR 0004/0005.
