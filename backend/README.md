# backend — API · ETL · Ingester

**Stack đã chốt:** Python + FastAPI *(2026-08-24, [ADR 0007](../docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))*. Ba khối chạy như process riêng nhưng dùng chung models/clients trong package này:

| Khối | Vai trò |
|---|---|
| `api` | REST + SSE + chatbot function calling |
| `etl` | Thu thập theo lịch từ 9 nguồn — xem [`docs/10-sources/`](../docs/10-sources/README.md) |
| `ingester` | Realtime BVSC, tick thô + sổ lệnh + nến 1', ghi batch vào ClickHouse |

**Đang có:** [`agent/skills/`](agent/skills/) — hai skill sản phẩm `vn-stock-advisor` · `vn-stock-knowledge` (3.046 dòng, đã test 6 vòng). ⚠️ **Trước khi sửa bất cứ gì trong đó, bắt buộc đọc [`docs/30-skills/maintenance.md`](../docs/30-skills/maintenance.md).** `agent/` sau này chứa luôn system prompt và glue function-calling.

**Trạng thái phần code:** lát cắt dọc đầu tiên đã dựng — `ingester` (socket BVSC → Redis → ClickHouse) và job `etl omo` (crawl OMO của SBV → Postgres). Hồ sơ: [`docs/90-records/plans/2026-08-26-ingester-omo-first-slice/`](../docs/90-records/plans/2026-08-26-ingester-omo-first-slice/). `api` chưa bắt đầu.

---

## Chạy `ingester`

Cần: Redis + ClickHouse đang chạy (`docker compose -f deploy/infra/docker-compose.yml --profile realtime up -d`), schema `rt` đã migrate (`python -m core.ch_migrate upgrade`), và các biến `CLICKHOUSE_INGESTER_URL` / `REDIS_URL` trong `.env` (mẫu ở `.env.example`; user ứng dụng tạo per-môi-trường — xem [`database/README.md`](../database/README.md)).

```bash
cd backend                          # luôn đặt PYTHONIOENCODING=utf-8
uv run python -m ingester --measure --minutes 5   # ĐO: ghi frame thô ra file, KHÔNG đụng DB
uv run python -m ingester                          # GHI THẬT: Redis + ClickHouse, tự thoát ~15:05
uv run python -m ingester --reconcile [--date 2026-08-26]   # chỉ đối chứng cuối phiên
```

🔴 **Gate trước khi bật ghi thật:** phải có **một phiên đo trọn trong giờ giao dịch** (08:40–15:05) và chủ dự án duyệt luật `SM`/dedup — [spec §3.5](../docs/90-records/plans/2026-08-26-ingester-omo-first-slice/spec.md). Trước khi qua gate, chỉ chạy `--measure`.

Ba chế độ đều nối cùng một socket; `--measure` thêm 20 topic × mã phái sinh + `pth` (câu hỏi đo còn treo — [roadmap §5.1](../docs/00-overview/roadmap.md)). File đo là JSONL gzip theo giờ trong `INGESTER_MEASURE_DIR`.

## Chạy job crawl OMO

```bash
cd backend
uv run python -m etl omo            # một lần chạy, ghi rồi thoát
```

Cần `ETL_DATABASE_URL` (user thuộc role `dlck_etl`). Job idempotent theo **ngày trong tiêu đề bài của SBV**: ngày đã có trong `macro.omo_session` thì bỏ qua, không ghi đè. Bị WAF chặn → `ops.etl_run` ghi `failed`, **không** ghi kho lẫn staging.

## Lịch chạy (Windows Task Scheduler)

```bash
pwsh scripts/register-tasks.ps1
```

Đăng ký 4 mốc OMO (11:30 · 15:30 · 18:00 · 21:30, ngày làm việc) và `dlck-ingester` 08:30. **Gate ghi tick mở 2026-08-26** — `dlck-ingester` nay đăng ký ở trạng thái BẬT, kèm `dlck-ingester-measure` chạy **một lần** vào ngày làm việc kế tiếp để bắt frame thô song song. Bật/tắt tay bằng cmdlet `Enable-ScheduledTask` / `Disable-ScheduledTask`, **không dùng `schtasks.exe`** — xem cảnh báo đầu [`scripts/register-tasks.ps1`](../scripts/register-tasks.ps1).
