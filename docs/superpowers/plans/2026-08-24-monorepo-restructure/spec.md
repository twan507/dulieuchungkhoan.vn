# SPEC — Chuẩn hoá cây monorepo và chốt stack

**Ngày:** 2026-08-24 · **Repo:** `d:\twan_projects\dulieuchungkhoan.vn` · **Trạng thái:** đã duyệt qua thảo luận với chủ dự án trong phiên 2026-08-24.

## 1. Bối cảnh

Repo sắp chứa toàn bộ sản phẩm: frontend, backend, database, tài liệu. Hiện gốc repo chỉ có `README.md` · `docs/` · `.claude/skills/` (2 skill sản phẩm) · `.git/`. Hai vấn đề:

1. **Skill sản phẩm nằm nhầm chỗ.** `.claude/skills/` là đường dẫn công cụ dev (Claude Code tự nạp khi code dự án), nhưng `vn-stock-advisor` và `vn-stock-knowledge` là **sản phẩm cho agent của web**, chỉ backend tiêu thụ lúc runtime.
2. **`docs/superpowers/` lạc loài** giữa các thư mục tri thức đánh số `00–30` — nó là hồ sơ quá trình (plans/surveys), không phải tri thức đọc theo thứ tự.

## 2. Quyết định đã chốt (phiên 2026-08-24, chủ dự án duyệt từng điểm)

### 2.1 Stack

| Tầng | Chốt | Ghi chú |
|---|---|---|
| Frontend | **Next.js** | SEO/SSR cho trang dữ liệu công khai — tên miền nhắm organic traffic |
| Backend | **Python + FastAPI** | Khớp ETL, ingester, SSE async, Anthropic SDK. Django bị loại: ORM không hợp ClickHouse/Timescale, SSE lủng củng, admin chưa cần |
| Database | **Postgres** (REST/BCTC/tin) + **ClickHouse** (realtime) | Chủ dự án chốt **lưu tick thô + sổ lệnh** từ 5 topic BVSC — cùng logic "không backfill được" của nến 1'. ClickHouse: nén cột 10–30×, materialized view tự sinh nến, TTL. Giá phải trả: insert batch, không transaction, hệ quản trị thứ hai |

⚠️ **Hệ quả treo:** `docs/20-design/market-data-store.md` (đã duyệt trước đây với TimescaleDB) **chưa cập nhật theo ClickHouse** — là việc thiết kế riêng, ghi vào roadmap, KHÔNG làm trong đợt này. Vai trò Redis (pub/sub SSE, leader lock) không bị ClickHouse thay thế.

### 2.2 Cây thư mục gốc

```
dulieuchungkhoan.vn/
├── README.md
├── docs/                # giữ nguyên, trừ đổi tên superpowers → 90-records
├── frontend/            # Next.js
├── backend/             # Python — api (FastAPI) · etl · ingester dùng chung code
│   └── agent/
│       └── skills/      # vn-stock-advisor · vn-stock-knowledge (dời từ .claude/skills/)
└── database/            # DDL Postgres + ClickHouse · migrations · compose
```

- **Phẳng theo vai trò deploy** — monorepo đa ngôn ngữ (Python + JS), không dùng khung `apps/packages` kiểu Node.
- **Skill nằm trong `backend/agent/`** — nguyên tắc "ai dùng thì người đó chứa" (chủ dự án chốt sau phản biện; phương án `agent/` gốc bị loại). `backend/agent/` sau này chứa luôn system prompt và glue function-calling.
- **`.claude/` xoá hẳn** — hệ quả có lợi: Claude Code không còn tự nạp skill sản phẩm khi code dự án.
- Thư mục chưa có code tạo kèm **README mồi** (git không giữ thư mục rỗng).

### 2.3 Cây `docs/`

```
docs/
├── 00-overview/     tri thức
├── 10-sources/      tri thức
├── 20-design/       tri thức
├── 30-skills/       tri thức
└── 90-records/      hồ sơ làm việc: plans/ · surveys/ · (specs/ sau này)
```

- Quy ước: **`00–8x` = tri thức, `9x` = hồ sơ quá trình.** Chỗ dành sẵn: `40-operations/` (runbook — khi hệ chạy thật), `50-api/` (tài liệu API công khai — khi có API thật).
- Phương án gộp tri thức vào `docs/knowledge/` bị loại: thêm tầng sâu, vỡ link hàng loạt, chỉ được thẩm mỹ.
- Dời cả cây (kể cả hồ sơ cũ bên trong) là đổi **đường dẫn**, không đổi **nội dung** lịch sử — đúng tiền lệ ADR 0005.

## 3. Luật sửa tham chiếu

1. **Tài liệu sống** (README, CLAUDE.md, docs/00 trừ decisions, 10, 20, 30): sửa cả nhãn lẫn href.
2. **Hồ sơ lịch sử** (`docs/*/decisions/`, `90-records/plans/`, `90-records/surveys/`): **không sửa nội dung**. Ngoại lệ duy nhất — theo tiền lệ ADR 0004/0005: link markdown trong `decisions/` có **href trỏ tới file đã dời thì sửa href cho khỏi treo, giữ nguyên nhãn hiển thị**.
3. `docs/30-skills/` (tri thức bảo trì skill) đứng yên — chỉ skill sản phẩm dời.

## 4. Ngoài phạm vi

| Mục | Loại |
|---|---|
| Cập nhật `market-data-store.md` theo ClickHouse (DDL, buffer batch ingester, vai trò Redis) | Đã có đường khác — việc thiết kế riêng, ghi vào roadmap §5.2 |
| Khởi tạo code Next.js / FastAPI / compose | Có chủ đích — chưa vào giai đoạn cài đặt |
| Chọn công cụ migrations, cấu trúc module trong `backend/` | Có chủ đích — chốt khi bắt đầu code |

## 5. Tiêu chí hoàn thành

1. `ls` gốc repo: đúng `README.md · docs/ · frontend/ · backend/ · database/ · .git/` (cộng file untracked cục bộ như `.env`).
2. `git grep -l "\.claude"` : không còn hit nào ngoài `docs/00-overview/decisions/` và `docs/90-records/`.
3. `git grep -l "docs/superpowers\|superpowers/"` : không còn hit nào ngoài `docs/00-overview/decisions/` và `docs/90-records/`.
4. Hai skill nằm ở `backend/agent/skills/`, lịch sử git giữ nguyên (git nhận diện rename).
5. Không còn link treo trong tài liệu sống trỏ tới đường dẫn cũ.
6. ADR 0007 tồn tại, ghi cả hai quyết định (layout + stack) kèm lý do và phương án bị loại.
7. Mọi commit message tiếng Anh, ngắn gọn.
