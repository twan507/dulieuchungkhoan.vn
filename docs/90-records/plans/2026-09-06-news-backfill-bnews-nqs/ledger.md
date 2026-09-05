# Ledger — lát 8b: backfill sitemap BNews + NguoiQuanSat

Nhánh `feat/news-backfill-sitemaps`, tách từ `main` `13d7a38` (lát 8 + docs). Spec duyệt 2026-09-06 sáng (`bf4feda`). Kiểm chứng: `PYTHONIOENCODING=utf-8 uv run pytest -q` từ `backend/`.

## 0. Trước khi chạy plan

- Đo 2026-09-06 07:00–08:00: [measure-sitemap-bnews-nqs-2026-09-06.md](measure-sitemap-bnews-nqs-2026-09-06.md).
- Task 0 (controller): 4 fixture + `CAPTURE-2026-09-05.txt` mục 2026-09-06; literal ghi trong plan.
- Mốc trước plan: **791 passed, 2 skipped** (bàn giao lát 8).

## 1. Tiến trình

| Task | Ai | Kết quả | Commit |
|---|---|---|---|
| 0 fixture | controller | xong | (cùng commit plan) |

## 2. Nghiệm thu (Task 6)

## 3. Review hai trục

## 4. Rulings

1. Plan lệch spec §3.1 một điểm: `backfill_sitemap` nhận `periods` đã cắt theo con trỏ (run_backfill tính), không nhận `from/to` — giữ cấu trúc lát 8, test qua `run_backfill`.

## 5. Trạng thái bàn giao
