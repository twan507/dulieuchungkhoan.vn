# Chiến lược test

**Ngày:** 2026-08-24 · **Trạng thái:** chốt định hướng · Quy tắc chống test giả nằm ở [CLAUDE.md §4.5](../../CLAUDE.md); file này chốt **công cụ và luật riêng theo stack** của dulieuchungkhoan.vn.

## Công cụ

| Lớp | Bộ công cụ |
|---|---|
| Backend (FastAPI: api · etl · ingester) | **pytest** + pytest-asyncio · mock HTTP bằng `httpx.MockTransport`/`respx` |
| Frontend (Next.js) | **Vitest** + React Testing Library · MSW cho tầng gọi API |
| E2E (khi có FE/SSE) | **Playwright**, chỉ Chromium — 10–20 smoke critical path |

## Luật riêng theo stack

1. 🔴 **Cấm gọi thật nguồn ngoài trong CI.** Mọi BVSC/FiinTrade/WiChart/FRED/ECB/Yahoo/LBMA/Binance mock bằng `httpx.MockTransport` hoặc `respx`. Test CI phải **deterministic và offline** — nguồn sống thay đổi/timeout sẽ làm CI đỏ giả.
   > **Tách hoàn toàn với "giám sát hợp đồng".** Việc gọi **live** để bắt nguồn đổi schema/độ tươi là [giám sát hợp đồng](market-data-store.md#71-giám-sát-hợp-đồng-dữ-liệu) — chạy theo lịch, **không phải** test CI. Trộn hai thứ này làm CI phụ thuộc nguồn ngoài.

2. 🔴 **DB test là Postgres + ClickHouse THẬT** (service container trong CI), **không SQLite/in-memory.** pgvector, JSONB, materialized view sinh nến của ClickHouse sẽ cho **test xanh giả** trên engine giả lập. Tăng tốc bằng reuse-db / bỏ migration nơi an toàn, không bằng đổi engine.

3. **Ingester/realtime:** test hàm **ghép delta** và **batch writer** với frame giả lập lưu sẵn (replay); **không** cố mock websocket sống trong CI. 1–2 E2E smoke xác nhận luồng khi dựng thật.

4. 🔴 **Đơn vị dữ liệu là bẫy — test phải bắt được.** Nhãn `unit` do nguồn tự khai **không khớp** dữ liệu nguồn tự trả (WiChart lệch 1000× ở 15 series; FiinTrade `Percentage` thực ra là thập phân — [roadmap §6 bẫy 3/4](../00-overview/roadmap.md)). Test tầng chuẩn hoá đơn vị phải assert bằng **dải giá trị thật đã biết đúng**, không tin nhãn nguồn.

5. **Module deterministic quan trọng giữ coverage cao** + để dành mutation testing: điều chỉnh giá (thô→hiển thị), sinh nến, rate limiter phân tán, ghép delta. **Coverage không có ngưỡng % cứng** — chỉ là tín hiệu.

6. **Dev-time nuôi CI, không thay CI.** Agent tự verify bằng lệnh thật (`curl /api/healthz`, chạy `etl` một nhịp, so frame) ngay sau khi sửa, rồi **cập nhật smoke test tương ứng** — công cụ agent bổ sung bộ test, không thay nó.

## Nhắc lại ranh giới (chi tiết ở CLAUDE.md §4.5)

Test tại **seam đã chốt trong plan** · **cấm tautological** (expected đến từ nguồn độc lập, không tính lại theo cách code tính) · mỗi test assert giá trị cụ thể + một case biên/sai · **đỏ trước xanh, lát dọc**.
