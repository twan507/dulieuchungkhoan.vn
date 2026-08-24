# database — DDL · migrations · compose

**Stack đã chốt** *(2026-08-24, [ADR 0007](../docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))*:

| Engine | Chứa gì |
|---|---|
| **PostgreSQL** | Dữ liệu REST: giá EOD, BCTC, sự kiện, vĩ mô, tin (tsvector + pgvector) |
| **ClickHouse** | Realtime: tick thô + sổ lệnh từ 5 topic BVSC; nến sinh bằng materialized view |

Redis đi kèm cho pub/sub SSE và leader lock của Ingester — nó là kênh phân phối, không phải kho.

⚠️ Thiết kế chi tiết ở [`docs/20-design/market-data-store.md`](../docs/20-design/market-data-store.md) viết cho TimescaleDB, **chưa cập nhật theo ClickHouse** — xem việc treo ở [lộ trình §5.2](../docs/00-overview/roadmap.md). Công cụ migrations chốt khi bắt đầu code.

**Trạng thái:** chưa bắt đầu.
