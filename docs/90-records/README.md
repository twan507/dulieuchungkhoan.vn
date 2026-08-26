# Hồ sơ làm việc

Tầng này lưu **bản ghi lịch sử của từng đợt làm việc lớn** — không phải tài liệu sống. Hai loại hồ sơ:

- **`plans/`** — spec + plan của một task lớn, theo quy trình [CLAUDE.md §4.1](../../CLAUDE.md): việc lớn thì viết đặc tả và kế hoạch trước, rồi mới thực thi.
- **`surveys/`** — hồ sơ một đợt khảo sát: số liệu đo thật, báo cáo từng nguồn/chủ đề, brief tóm tắt.

**Luật sửa:** bản ghi lịch sử — **thêm mới, không viết lại quá khứ**. Một hồ sơ đã đóng phản ánh điều đúng *tại thời điểm đó*; tri thức vận hành rút ra từ nó phải đi vào tài liệu sống ở [`10-sources/`](../10-sources/) hoặc [`20-design/`](../20-design/), không nằm lại đây.

> Hồ sơ ở đây là **bằng chứng đo**, không phải nguồn tra cứu vận hành. Muốn biết "hệ thống hiện thế nào" thì đọc tài liệu sống; muốn biết "vì sao con số này ra thế" thì mới lần về đây.

---

## `plans/` — đặc tả và kế hoạch từng task lớn

Mỗi thư mục là một task, đặt tên `YYYY-MM-DD-<tên>`. File bên trong: `spec.md` (đặc tả mục tiêu + nghiệm thu), `plan.md` (kế hoạch từng bước), đôi khi `ledger.md` (sổ theo dõi lúc thực thi).

| Thư mục | Task | Kết quả |
|---|---|---|
| [`2026-08-14-restructure-english-tree/`](plans/2026-08-14-restructure-english-tree/) | Tái cấu trúc kho tài liệu sang cây tiếng Anh — `spec.md` · `plan.md` | Đã áp dụng → [ADR 0005](../00-overview/decisions/0005-english-tree.md) |
| [`2026-08-15-cap-nhat-tai-lieu-nguon/`](plans/2026-08-15-cap-nhat-tai-lieu-nguon/) | Cập nhật tài liệu nguồn theo khảo sát 2026-08-15 — `spec.md` · `plan.md` · `ledger.md` | Đã áp dụng → tài liệu 9 nguồn |
| [`2026-08-24-monorepo-restructure/`](plans/2026-08-24-monorepo-restructure/) | Chuẩn hoá cây monorepo + chốt stack — `spec.md` · `plan.md` | Đã áp dụng → [ADR 0007](../00-overview/decisions/0007-monorepo-layout-and-stack.md) |
| [`2026-08-24-deploy-scaffold/`](plans/2026-08-24-deploy-scaffold/) | Khung đóng gói một-nút (docker compose infra/app · `stack.mjs` · dev native + deploy docker) — học tinh hoa từ tutor-agent — `spec.md` · `plan.md` · `ledger.md` | ✅ thực thi xong trên `feat/deploy-scaffold` (AC1–AC8 nghiệm thu live); chờ merge |
| [`2026-08-25-postgres-data-schema/`](plans/2026-08-25-postgres-data-schema/) | Lược đồ PostgreSQL `postgres-data` — 6 schema theo miền tiêu thụ, canonical id + ánh xạ external, Alembic — spec tách 7 bước duyệt tuần tự, mục lục ở README của plan | ✅ **xong 2026-08-25** — 10 migration + 37 test seam trên Postgres thật, merge `main` |
| [`2026-08-25-clickhouse-realtime-store/`](plans/2026-08-25-clickhouse-realtime-store/) | Kho realtime ClickHouse — 5 bảng frame thô TTL 3 tháng + 2 bảng nến vĩnh viễn + materialized view, runner migration SQL thuần, role/profile, backup theo partition | ✅ **xong 2026-08-26** — 2 migration + 29 test seam trên CH thật (26.3.22.7), 15 phép kiểm §12 của spec |
| [`2026-08-26-ingester-omo-first-slice/`](plans/2026-08-26-ingester-omo-first-slice/) | **Lát cắt dọc đầu tiên** — `ingester` realtime (socket BVSC → Redis → ClickHouse) + job `etl omo` (crawl OMO của SBV → Postgres) — `spec.md` · `plan.md` · `ledger.md` | ✅ **merge `main` 2026-08-26** — 179 test xanh, 2 vòng review + review toàn nhánh; OMO chạy thật 4 mốc/ngày. Ghi tick realtime **chờ gate phiên đo trọn ngày** |

## `surveys/` — hồ sơ khảo sát

Mỗi thư mục là một đợt khảo sát, có README riêng làm mục lục chi tiết. Ở đây chỉ liệt kê đợt.

| Thư mục | Đợt | Quy mô |
|---|---|---|
| [`2026-08-15-nguon-du-lieu/`](surveys/2026-08-15-nguon-du-lieu/README.md) | Khảo sát nguồn dữ liệu — báo cáo từng nguồn, brief, rà soát nguồn cũ và việc chưa kiểm | 9 nguồn · ~400 lời gọi thật · mục lục ở README của đợt |
| [`2026-08-26-bvsc-realtime-session/`](surveys/2026-08-26-bvsc-realtime-session/README.md) | **Phiên đo realtime BVSC** — chạy bằng chính `ingester --measure`: vỏ bọc frame thật, tính chất `SM`, phái sinh đi chung topic, trường lạ, tải toàn thị trường | 2.316.573 frame · 6.322 topic · phiên chiều 26/08 |
