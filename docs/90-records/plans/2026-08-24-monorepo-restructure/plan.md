# Plan — Chuẩn hoá cây monorepo và chốt stack

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dời 2 skill sản phẩm về `backend/agent/skills/`, dựng khung monorepo `frontend/ · backend/ · database/`, đổi `docs/superpowers/` → `docs/90-records/`, phản ánh stack đã chốt (Next.js · FastAPI · Postgres + ClickHouse) vào tài liệu sống, và ghi ADR 0007.

**Architecture:** Toàn bộ là thao tác `git mv` + sửa tài liệu markdown — không có code chạy. "Test" của mỗi task là lệnh kiểm chứng (grep/ls) với kết quả kỳ vọng ghi sẵn. Nguyên tắc xuyên suốt: tài liệu sống sửa cả nhãn lẫn href; hồ sơ lịch sử (`decisions/`, `90-records/`) chỉ sửa **href của link trỏ tới file đã dời** (tiền lệ ADR 0004/0005), không sửa nội dung.

**Tech Stack:** git (mv/grep), perl one-liner cho thay thế hàng loạt, Edit tool cho sửa điểm.

**Spec:** `docs/superpowers/plans/2026-08-24-monorepo-restructure/spec.md` *(sau Task 4 nằm ở `docs/90-records/plans/2026-08-24-monorepo-restructure/spec.md`)*

## Global Constraints

- **Commit message tiếng Anh, ngắn gọn** — quy ước chốt 2026-08-24. Kết mỗi message bằng dòng `Co-Authored-By` theo chuẩn phiên *(các lệnh commit trong task viết gọn `-m "..."`, người thực thi tự thêm trailer)*.
- **Không sửa nội dung** file trong `docs/00-overview/decisions/` và `docs/superpowers/` (sau đổi tên: `docs/90-records/`) — ngoại lệ duy nhất: sửa **href** của link markdown trỏ tới đường dẫn đã dời, giữ nguyên nhãn hiển thị.
- **Không đụng** `docs/10-sources/` trừ đúng 2 href được chỉ định (README.md:188 và docs/README.md:54 — file thứ hai nằm ngoài 10-sources).
- **Không đổi một chữ nào** bên trong 14 file skill khi dời.
- Chạy lệnh từ gốc repo `d:/twan_projects/dulieuchungkhoan.vn`, dùng Bash (Git Bash).
- Sơ đồ ASCII khi sửa phải **giữ thẳng cột `│` đóng khung** — đường dẫn mới dài hơn cũ 6 ký tự thì bớt đúng 6 dấu cách đệm.

---

### Task 1: Dời skill sản phẩm về backend/agent/skills/

**Files:**
- Move: `.claude/skills/vn-stock-advisor/` → `backend/agent/skills/vn-stock-advisor/` (5 file)
- Move: `.claude/skills/vn-stock-knowledge/` → `backend/agent/skills/vn-stock-knowledge/` (9 file)
- Delete: thư mục `.claude/` (sau khi rỗng)

**Interfaces:**
- Produces: đường dẫn `backend/agent/skills/` mà Task 3 sẽ trỏ tài liệu vào.

- [ ] **Step 1: Dời bằng git mv (giữ lịch sử rename)**

```bash
mkdir -p backend/agent
git mv .claude/skills backend/agent/skills
```

- [ ] **Step 2: Kiểm thư mục .claude còn gì không, rồi xoá**

```bash
ls -a .claude
```
Kỳ vọng: chỉ còn `.` và `..` (nếu có file untracked như `settings.local.json` thì **dừng lại hỏi chủ dự án**, không tự xoá).

```bash
rmdir .claude
```

- [ ] **Step 3: Kiểm chứng**

```bash
git status --short | head -20
ls backend/agent/skills
```
Kỳ vọng: các dòng `R  .claude/skills/... -> backend/agent/skills/...` (14 file, git nhận diện rename); `ls` in ra `vn-stock-advisor  vn-stock-knowledge`.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "Move product skills to backend/agent/skills"
```

---

### Task 2: Tạo khung frontend/ · backend/ · database/ với README mồi

**Files:**
- Create: `frontend/README.md`
- Create: `backend/README.md`
- Create: `database/README.md`

**Interfaces:**
- Consumes: `backend/agent/skills/` từ Task 1 (README backend nhắc tới nó).
- Produces: ba thư mục gốc mà Task 5 vẽ vào cây repo.

- [ ] **Step 1: Viết `frontend/README.md`** (nội dung nguyên văn):

```markdown
# frontend — giao diện web dulieuchungkhoan.vn

**Stack đã chốt:** Next.js *(2026-08-24, [ADR 0007](../docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))* — chọn vì cần SSR/SEO cho trang dữ liệu công khai.

**Trạng thái:** chưa bắt đầu. Khởi tạo project khi vào giai đoạn cài đặt FE — xem [lộ trình](../docs/00-overview/roadmap.md).
```

- [ ] **Step 2: Viết `backend/README.md`** (nội dung nguyên văn):

```markdown
# backend — API · ETL · Ingester

**Stack đã chốt:** Python + FastAPI *(2026-08-24, [ADR 0007](../docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))*. Ba khối chạy như process riêng nhưng dùng chung models/clients trong package này:

| Khối | Vai trò |
|---|---|
| `api` | REST + SSE + chatbot function calling |
| `etl` | Thu thập theo lịch từ 9 nguồn — xem [`docs/10-sources/`](../docs/10-sources/README.md) |
| `ingester` | Realtime BVSC, tick thô + sổ lệnh + nến 1', ghi batch vào ClickHouse |

**Đang có:** [`agent/skills/`](agent/skills/) — hai skill sản phẩm `vn-stock-advisor` · `vn-stock-knowledge` (3.046 dòng, đã test 6 vòng). ⚠️ **Trước khi sửa bất cứ gì trong đó, bắt buộc đọc [`docs/30-skills/maintenance.md`](../docs/30-skills/maintenance.md).** `agent/` sau này chứa luôn system prompt và glue function-calling.

**Trạng thái phần code:** chưa bắt đầu.
```

- [ ] **Step 3: Viết `database/README.md`** (nội dung nguyên văn):

```markdown
# database — DDL · migrations · compose

**Stack đã chốt** *(2026-08-24, [ADR 0007](../docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))*:

| Engine | Chứa gì |
|---|---|
| **PostgreSQL** | Dữ liệu REST: giá EOD, BCTC, sự kiện, vĩ mô, tin (tsvector + pgvector) |
| **ClickHouse** | Realtime: tick thô + sổ lệnh từ 5 topic BVSC; nến sinh bằng materialized view |

Redis đi kèm cho pub/sub SSE và leader lock của Ingester — nó là kênh phân phối, không phải kho.

⚠️ Thiết kế chi tiết ở [`docs/20-design/market-data-store.md`](../docs/20-design/market-data-store.md) viết cho TimescaleDB, **chưa cập nhật theo ClickHouse** — xem việc treo ở [lộ trình §5.2](../docs/00-overview/roadmap.md). Công cụ migrations chốt khi bắt đầu code.

**Trạng thái:** chưa bắt đầu.
```

- [ ] **Step 4: Kiểm chứng + commit**

```bash
ls frontend backend database
git add frontend/README.md backend/README.md database/README.md
git commit -m "Seed frontend, backend, database directories"
```
Kỳ vọng `ls`: mỗi thư mục có `README.md` (backend có thêm `agent/`).

---

### Task 3: Trỏ tài liệu sống sang backend/agent/skills/

**Files:**
- Modify: `docs/README.md:71` · `docs/30-skills/README.md` (dòng 3, 7, 19, 20) · `docs/30-skills/maintenance.md` (dòng 5, 62) · `docs/20-design/chatbot-semantic-layer.md:10` — thay hàng loạt
- Modify: `docs/00-overview/architecture.md` (dòng 38, 71, 108, 114) — sửa tay vì có sơ đồ ASCII
- Modify: `docs/00-overview/decisions/0003-close-skill-project.md:29` — **chỉ href**
- KHÔNG sửa: `README.md` gốc (Task 5 viết lại nguyên khối cây) · `decisions/0001`, `0005` (nhắc `.claude` trong văn xuôi/code block lịch sử, không phải link) · mọi file trong `docs/superpowers/`

**Interfaces:**
- Consumes: đường dẫn mới từ Task 1. (Cả 6 file đều trỏ từ độ sâu 2 nên tiền tố `../../` giữ nguyên — chỉ thay `\.claude/skills` → `backend/agent/skills` là link vẫn đúng; riêng `docs/README.md` dùng `../` và `0003` dùng `../../../`, cũng bất biến với phép thay này.)

- [ ] **Step 1: Thay hàng loạt 4 file không có sơ đồ**

```bash
perl -pi -e 's{\.claude/skills}{backend/agent/skills}g' \
  docs/README.md docs/30-skills/README.md docs/30-skills/maintenance.md \
  docs/20-design/chatbot-semantic-layer.md
```

- [ ] **Step 2: Sửa tay `architecture.md`** — 4 chỗ, dùng Edit tool:

Dòng 38 (khung L4 — tên mới dài hơn 6 ký tự, bớt 6 dấu cách đệm cho `│` thẳng cột):
```
cũ:  │  L4 · TRI THỨC — .claude/skills/                                     │
mới: │  L4 · TRI THỨC — backend/agent/skills/                               │
```
Dòng 71 (bảng ranh giới): thay `[`.claude/skills/`](../../.claude/skills/)` → `[`backend/agent/skills/`](../../backend/agent/skills/)`.
Dòng 108: thay href `../../.claude/skills/vn-stock-knowledge/references/portfolio-and-rotation.md` → `../../backend/agent/skills/vn-stock-knowledge/references/portfolio-and-rotation.md`.
Dòng 114: thay href `../../.claude/skills/vn-stock-knowledge/SKILL.md` → `../../backend/agent/skills/vn-stock-knowledge/SKILL.md`.

- [ ] **Step 3: Sửa href-only trong ADR 0003** (dòng 29 — giữ nguyên nhãn `danh-muc-va-luan-chuyen.md`):

```
cũ href: ../../../.claude/skills/vn-stock-knowledge/references/portfolio-and-rotation.md
mới href: ../../../backend/agent/skills/vn-stock-knowledge/references/portfolio-and-rotation.md
```

- [ ] **Step 4: Kiểm chứng**

```bash
grep -rn "\.claude" --include="*.md" . | grep -v "docs/superpowers/" | grep -v "decisions/0001" | grep -v "decisions/0005"
```
Kỳ vọng: chỉ còn `README.md:60` (khối cây — Task 5 xử lý). Kiểm khung sơ đồ:
```bash
sed -n '36,42p' docs/00-overview/architecture.md
```
Kỳ vọng: cột `│` phải thẳng hàng trên cả 7 dòng.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Update skill path references in living docs"
```

---

### Task 4: Đổi docs/superpowers/ → docs/90-records/

**Files:**
- Move: `docs/superpowers/` → `docs/90-records/` (toàn bộ cây, gồm cả plan này)
- Modify: `CLAUDE.md` (dòng 124, 125, 164) — đường dẫn quy trình
- Modify: `docs/10-sources/README.md:188` — **chỉ href** trong changelog
- Modify: nếu bước dò tìm thấy link trong `decisions/` trỏ vào `superpowers/` — **chỉ href**

**Interfaces:**
- Produces: đường dẫn `docs/90-records/` mà Task 5 vẽ vào cây repo và CLAUDE.md dùng làm quy trình từ nay về sau.

- [ ] **Step 1: Đổi tên bằng git mv**

```bash
git mv docs/superpowers docs/90-records
```

- [ ] **Step 2: Sửa CLAUDE.md** — 3 chỗ, thay `docs/superpowers/` → `docs/90-records/`:

```bash
perl -pi -e 's{docs/superpowers/}{docs/90-records/}g' CLAUDE.md
```

- [ ] **Step 3: Sửa href changelog `docs/10-sources/README.md:188`** (giữ nhãn `surveys/2026-08-15-nguon-du-lieu/`):

```
cũ href: ../superpowers/surveys/2026-08-15-nguon-du-lieu/README.md
mới href: ../90-records/surveys/2026-08-15-nguon-du-lieu/README.md
```

- [ ] **Step 4: Dò link sót trỏ superpowers, sửa href-only nếu là link trong decisions/**

```bash
grep -rn "superpowers/" --include="*.md" . | grep -v "docs/90-records/"
```
Kỳ vọng: **rỗng**. Nếu ra hit trong `decisions/`: là link markdown thì sửa href giữ nhãn; là văn xuôi thì để nguyên và ghi lại vào báo cáo task.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Rename docs/superpowers to docs/90-records"
```

---

### Task 5: Cập nhật cây repo và stack trong README · architecture · roadmap

**Files:**
- Modify: `README.md` (đoạn trạng thái dòng 5, khối cây dòng 51–62, dòng L2 69, dòng 76)
- Modify: `docs/00-overview/architecture.md:27` (khung L2)
- Modify: `docs/00-overview/roadmap.md` (bảng §0, dòng 35, bảng §5.2)

**Interfaces:**
- Consumes: đường dẫn từ Task 1–4. Nhắc `ADR 0007` — file sinh ở Task 7 (chấp nhận link tồn tại trước file trong phạm vi một đợt; Task 8 kiểm lại).

- [ ] **Step 1: `README.md` — thêm câu chốt stack vào cuối đoạn trạng thái (dòng 5)**, nối thêm:

```
**Stack chốt 2026-08-24:** Next.js · Python/FastAPI · Postgres + ClickHouse *(lưu tick thô — [ADR 0007](docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))*.
```

- [ ] **Step 2: `README.md` — thay nguyên khối "Cấu trúc repo"** (từ ```` ``` ```` mở đến ```` ``` ```` đóng) bằng:

```
dulieuchungkhoan.vn/
├── docs/                Toàn bộ tài liệu — bản đồ ở docs/README.md
│   ├── 00-overview/     kiến trúc · lộ trình · sổ quyết định (chỉ lịch sử)
│   ├── 10-sources/      reference: market · macro · global · news
│   ├── 20-design/       lựa chọn kiến trúc của dulieuchungkhoan.vn
│   ├── 30-skills/       tài liệu bảo trì + corpus của hai skill
│   └── 90-records/      hồ sơ làm việc: plans · surveys
├── frontend/            Next.js — chưa bắt đầu
├── backend/             Python (FastAPI) — api · etl · ingester
│   └── agent/skills/    vn-stock-advisor · vn-stock-knowledge — sản phẩm chạy được
└── database/            DDL Postgres + ClickHouse · migrations — chưa bắt đầu
```

- [ ] **Step 3: `README.md` — hai dòng stack:**

Dòng 69: `L2  Kho            PostgreSQL + TimescaleDB + Redis` → `L2  Kho            PostgreSQL + ClickHouse + Redis`
Dòng 76: `dựng hạ tầng DB (Postgres + Redis)` → `dựng hạ tầng DB (Postgres + ClickHouse)`

- [ ] **Step 4: `architecture.md:27` — khung L2** (ClickHouse ngắn hơn TimescaleDB 1 ký tự, thêm 1 dấu cách đệm):

```
cũ:  │  PostgreSQL + TimescaleDB + Redis                                   │
mới: │  PostgreSQL + ClickHouse + Redis                                    │
```

- [ ] **Step 5: `roadmap.md` — ba chỗ:**

(a) Bảng §0, chèn ngay trên dòng `| **Toàn bộ phần cài đặt** |`:
```
| **Stack sản phẩm + cây monorepo** | ✅ **Chốt 2026-08-24** — Next.js · Python/FastAPI · Postgres + ClickHouse (lưu tick thô) · skill dời về `backend/agent/skills/` | [ADR 0007](decisions/0007-monorepo-layout-and-stack.md) |
```
(b) Dòng 35: `| **1** | **Dựng hạ tầng Postgres + Redis** | Mọi ETL | kho dữ liệu §8 GĐ 0 |` → `| **1** | **Dựng hạ tầng Postgres + ClickHouse (+ Redis)** | Mọi ETL | kho dữ liệu §8 GĐ 0 · [ADR 0007](decisions/0007-monorepo-layout-and-stack.md) |`
(c) Bảng §5.2, thêm dòng đầu bảng (ngay dưới header):
```
| 🔴 **Cập nhật `market-data-store.md` theo ClickHouse** | Chốt 2026-08-24 ([ADR 0007](decisions/0007-monorepo-layout-and-stack.md)): kho realtime đổi TimescaleDB → ClickHouse để lưu tick thô + sổ lệnh. Thiết kế đã duyệt chưa phản ánh: DDL ClickHouse, materialized view sinh nến, buffer ghi batch cho Ingester; Redis giữ nguyên vai trò pub/sub + leader lock | Một phiên thiết kế riêng, làm **trước khi dựng hạ tầng [1]** |
```

- [ ] **Step 6: Kiểm chứng + commit**

```bash
grep -n "TimescaleDB" README.md docs/00-overview/architecture.md docs/00-overview/roadmap.md
grep -rn "\.claude" README.md
```
Kỳ vọng: lệnh 1 rỗng; lệnh 2 rỗng.

```bash
git add -A && git commit -m "Update repo tree and stack in living docs"
```

---

### Task 6: Cắm cờ chờ-thiết-kế-lại vào tài liệu thiết kế kho

**Files:**
- Modify: `docs/20-design/market-data-store.md` (chèn cảnh báo sau dòng 5 — dòng "Bối cảnh")
- Modify: `docs/20-design/README.md:9` (ô trạng thái)
- Modify: `docs/README.md:54` (ô mô tả)

**Interfaces:**
- Consumes: quyết định ClickHouse (spec §2.1), việc treo ở roadmap §5.2 (Task 5).

- [ ] **Step 1: Chèn blockquote vào `market-data-store.md`**, ngay sau đoạn "Bối cảnh" (dòng 5), nguyên văn:

```markdown
> ⚠️ **2026-08-24 — [ADR 0007](../00-overview/decisions/0007-monorepo-layout-and-stack.md):** kho realtime đã chốt đổi sang **ClickHouse** (lưu tick thô + sổ lệnh; Postgres giữ dữ liệu REST/BCTC/tin; Redis giữ pub/sub + leader lock). Tài liệu này **chưa cập nhật theo** — các phần lược đồ TimescaleDB, continuous aggregate, nén/retention sẽ thiết kế lại trong một phiên riêng, xem [lộ trình §5.2](../00-overview/roadmap.md).
```

- [ ] **Step 2: `docs/20-design/README.md:9`** — ô trạng thái: `✅ đã duyệt, chưa cài đặt` → `✅ đã duyệt, chưa cài đặt · ⚠️ kho realtime sẽ đổi sang ClickHouse (ADR 0007)`

- [ ] **Step 3: `docs/README.md:54`** — cuối ô mô tả, `| ✅ đã duyệt |` → `| ✅ đã duyệt · ⚠️ chờ cập nhật ClickHouse (ADR 0007) |`

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "Flag market-data-store for ClickHouse redesign"
```

---

### Task 7: Viết ADR 0007

**Files:**
- Create: `docs/00-overview/decisions/0007-monorepo-layout-and-stack.md`

**Interfaces:**
- Produces: đích cho mọi link `ADR 0007` đã đặt ở Task 2, 5, 6.

- [ ] **Step 1: Viết file với nội dung nguyên văn:**

```markdown
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
```

- [ ] **Step 2: Kiểm chứng + commit**

```bash
ls docs/00-overview/decisions/
git add docs/00-overview/decisions/0007-monorepo-layout-and-stack.md
git commit -m "ADR 0007: monorepo layout and stack"
```
Kỳ vọng `ls`: 7 file, `0007-monorepo-layout-and-stack.md` có mặt.

---

### Task 8: Tổng kiểm và push

**Files:** không sửa gì — chỉ kiểm.

- [ ] **Step 1: Chạy 5 phép kiểm của spec §5**

```bash
ls
# Kỳ vọng: CLAUDE.md README.md backend database docs frontend (+ file untracked cục bộ nếu có)

grep -rln "\.claude" --include="*.md" . 
# Kỳ vọng: chỉ file trong docs/00-overview/decisions/ và docs/90-records/

grep -rln "superpowers" --include="*.md" .
# Kỳ vọng: chỉ file trong docs/00-overview/decisions/ và docs/90-records/

grep -rn "TimescaleDB" README.md CLAUDE.md docs/README.md docs/00-overview/architecture.md docs/00-overview/roadmap.md
# Kỳ vọng: rỗng

ls backend/agent/skills/vn-stock-advisor backend/agent/skills/vn-stock-knowledge | head -5
# Kỳ vọng: SKILL.md có mặt ở cả hai
```

- [ ] **Step 2: Kiểm link sống không treo** — với mỗi đường dẫn đích xuất hiện trong các file đã sửa (Task 3–7), xác nhận file đích tồn tại:

```bash
for p in backend/agent/skills/vn-stock-advisor/SKILL.md \
         backend/agent/skills/vn-stock-knowledge/SKILL.md \
         backend/agent/skills/vn-stock-knowledge/references/portfolio-and-rotation.md \
         docs/90-records/surveys/2026-08-15-nguon-du-lieu/README.md \
         docs/00-overview/decisions/0007-monorepo-layout-and-stack.md; do
  [ -f "$p" ] && echo "OK  $p" || echo "TREO $p"; done
# Kỳ vọng: 5 dòng OK
```

- [ ] **Step 3: Push**

```bash
git log --oneline origin/main..HEAD
git push origin main
```
Kỳ vọng: 8 commit của đợt này (spec+plan · Task 1–7, mỗi task một commit) lên `origin/main` thành công.
