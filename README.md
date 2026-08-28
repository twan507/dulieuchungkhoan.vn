# dulieuchungkhoan.vn

Nền tảng dữ liệu và phân tích chứng khoán Việt Nam: thu thập dữ liệu thị trường và tin tức từ nhiều nguồn, lưu vào kho riêng, phân phối lại qua REST và SSE, và một chatbot AI trả lời bằng phương pháp phân tích đã được hệ thống hoá thành skill.

**Trạng thái — 2026-08-28:** thiết kế hoàn chỉnh, và **phần lõi thu thập dữ liệu đã chạy thật trong production**. Ingester bắt tick realtime mỗi phiên *(phiên 28/08: **4.722.406 dòng** vào kho, đối chứng sổ sách **dư = 0** trên cả 5 bảng)*; hai kho đã có schema và dữ liệu thật; **321 test** xanh chạy trên Postgres/ClickHouse/Redis thật; 7 task chạy theo lịch Windows Scheduler. `api` và `frontend` **chưa bắt đầu**. Hai skill chứng khoán đã xong và đã test 6 vòng. **Không còn việc chặn nào phụ thuộc bên ngoài** — giấy phép WiFeed đã chốt và rate limit FiinGroup đã kiểm, cùng ngày 2026-08-15. Cùng ngày, một **đợt khảo sát nguồn 9 nguồn / ~400 lời gọi thật** đã khép độ rộng dữ liệu: thêm **6 nguồn mới** và mở **5 khối dữ liệu** trước nay bỏ trống.

**Stack chốt 2026-08-24:** Next.js · Python/FastAPI · Postgres + ClickHouse *(lưu tick thô — [ADR 0007](docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))*.

| Khối | Trạng thái | Bằng chứng |
|---|---|---|
| Tài liệu **9 nguồn** — thị trường · vĩ mô VN · quốc tế · tin | ✅ đo thật bằng lời gọi sống | 131 endpoint VN · 87 key · 307 URL · 6 nguồn mới đo 2026-08-15 |
| Độ rộng nguồn dữ liệu | ✅ **khép 2026-08-15** — danh sách *"Ngoài phạm vi"* phân rã hết, không còn mục nào chưa có câu trả lời | [phạm vi nguồn](docs/10-sources/README.md) |
| Từ điển 729 mã trường FiinGroup | ✅ phủ 100% response thật | [field-dictionary.json](docs/10-sources/market/field-dictionary.json) |
| Chọn nguồn chuẩn cho từng chỉ tiêu | ✅ đã chốt | [chọn trường cho ETL thị trường](docs/20-design/market-field-selection.md) |
| Dự án skill | ✅ **đã đóng**, không còn việc treo | [bảo trì skill](docs/30-skills/maintenance.md) |
| Thiết kế kho dữ liệu · pipeline tin | ✅ đã duyệt | kho dữ liệu **đã cài**; pipeline tin chưa |
| Tầng ngữ nghĩa nối dữ liệu ↔ skill | 🟡 đề xuất, **chưa duyệt** | [chatbot-semantic-layer.md](docs/20-design/chatbot-semantic-layer.md) |
| Hai skill chứng khoán | ✅ xong, test 6 vòng, đã dừng tối ưu | 3.046 dòng |
| Repo vào git | ✅ khởi tạo 2026-08-14 | commit đầu tiên |
| **Hạ tầng + schema hai kho** | ✅ **2026-08-26** | Postgres **14 migration** (alembic) · ClickHouse **2** · compose PG+CH+Redis |
| **Ingester realtime** | ✅ **ghi thật từ 2026-08-27** — hàng đợi có trần, tràn ra đĩa khi kho trục trặc | 4,72 triệu dòng phiên 28/08 · chưa lần nào phải dùng tới đĩa |
| **ETL theo lịch** | ✅ `etl omo` (⏸️ tạm tắt) · `etl refdata` 08:00 | 7 task Scheduler, `LogonType=S4U` |
| **`api` · `frontend`** | ❌ chưa bắt đầu | |

Bảng đầy đủ kèm bằng chứng: [lộ trình §0](docs/00-overview/roadmap.md).

**Khối dữ liệu đã phủ — sau khảo sát 2026-08-15**

| Khối | Nguồn chuẩn | Quy mô đo được *(2026-08-15)* |
|---|---|---|
| Cổ phiếu · chỉ số · sổ lệnh · khối ngoại | BVSC | 1.974 cổ phiếu · 20 chỉ số |
| BCTC · tỷ số · dòng tiền · lịch sự kiện | FiinTrade | 729 mã chỉ tiêu |
| **Phái sinh** *(mới)* | BVSC + FiinTrade | 14 hợp đồng · 62 trường · backfill 2.233 phiên từ 31/08/2017 |
| **ETF/quỹ niêm yết** *(mới)* | BVSC + FiinTrade | 31 mã · `iNav` phủ **6/31**, chỉ **2 mã** có thanh khoản thật |
| Vĩ mô · tiền tệ · hàng hoá Việt Nam | WiChart | 87 key |
| **OMO** *(mới)* | SBV | crawl HTML · 🔴 **không backfill được** |
| **Vĩ mô Mỹ** *(mới)* | FRED | 15 series |
| **Tỷ giá + chỉ số đô** *(mới)* | Frankfurter (ECB) | 6 cặp · DXY dựng lại, lệch trung bình **0,180%** trên 248 phiên |
| **Chỉ số quốc tế** *(mới)* | Yahoo Finance | **36 chỉ số / 21 nước** · lợi suất TPCP Mỹ · họ biến động |
| **Vàng/bạc mốc chuẩn** *(mới)* | LBMA | từ **1968**, 14.662 điểm một lời gọi |
| **Crypto + vàng 24/7** *(mới)* | Binance | 10 đồng · PAXG |
| Tin tức | 8 báo điện tử | 47 RSS + 6 crawler |

⛔ **Loại có chủ đích, đừng mở lại:** chứng quyền (342 mã) · lô lẻ (1.890 mã) · trái phiếu (187 mã) — **cả ba đều có dữ liệu**, loại vì không phục vụ phân tích · realtime FiinTrade *(dùng của BVSC)* · luồng cần đăng nhập. **Đã kiểm, không nguồn nào có:** NAV quỹ mở. Lý do từng mục: [phạm vi nguồn §2](docs/10-sources/README.md).

---

## Bắt đầu từ đâu

| Bạn muốn | Đọc |
|---|---|
| Hiểu toàn cảnh hệ thống | [Kiến trúc tổng thể](docs/00-overview/architecture.md) |
| Biết làm gì tiếp theo | [Lộ trình hợp nhất](docs/00-overview/roadmap.md) |
| Tra một endpoint cụ thể | [Bản đồ tài liệu](docs/README.md) |

## Cấu trúc repo

```
dulieuchungkhoan.vn/
├── docs/                Toàn bộ tài liệu — bản đồ ở docs/README.md
│   ├── 00-overview/     kiến trúc · lộ trình · sổ quyết định (chỉ lịch sử)
│   ├── 10-sources/      reference: market · macro · global · news
│   ├── 20-design/       lựa chọn kiến trúc của dulieuchungkhoan.vn
│   ├── 30-skills/       tài liệu bảo trì + corpus của hai skill
│   └── 90-records/      hồ sơ làm việc: plans · surveys
├── frontend/            Next.js — chưa bắt đầu (mới có README)
├── backend/             Python — ingester (chạy thật) · etl (omo, refdata) · api (chưa bắt đầu)
│   ├── agent/skills/    vn-stock-advisor · vn-stock-knowledge — sản phẩm chạy được
│   └── tests/           321 test, chạy trên Postgres/ClickHouse/Redis THẬT
├── database/            migrations: Postgres 14 (alembic) · ClickHouse 2
├── deploy/infra/        docker compose — Postgres · ClickHouse · Redis
└── scripts/             register-tasks.ps1 — đăng ký 7 task Windows Scheduler
```

## Dựng trên máy mới

Kiến thức dựng lại nằm rải ở nhiều file — đây là chuỗi nối chúng. Chi tiết từng bước ở file được trỏ tới, **không chép lại ở đây**.

1. `git clone`, rồi tạo `.env` từ [`.env.example`](.env.example).
2. **Bật hạ tầng.** ClickHouse nằm sau `profiles: ["realtime"]` nên `docker compose up` trần sẽ **không** bật nó:

   ```bash
   npm run dev-start          # scripts/stack.mjs — đã kèm --profile realtime
   ```

3. **Bootstrap hai kho, đúng ba bước** — [`database/README.md`](database/README.md) mục *Bootstrap DB mới*: `alembic upgrade head` + `core.ch_migrate upgrade` → một lượt `etl refdata` (nạp danh bạ, danh mục mã, cây ICB từ API thật) → `alembic downgrade 0012` rồi `upgrade head`.

   🔴 **Bước ba không được bỏ.** Migration `0013` seed 161 dòng gán ngành tay bằng cách phân giải ticker → `issuer_id` qua `market.security`; bảng đó còn **rỗng** lúc `0013` chạy ở bước một ⇒ nạp **0 dòng, không exception, không cảnh báo nào**, và job `etl refdata` sau đó vẫn báo y hệt trạng thái khoẻ mạnh.

4. `cd backend && uv run pytest tests` — kỳ vọng **321 passed, 2 skipped** *(hai skip là probe thủ công có cổng env: `RUN_PROBE`, `RUN_CHAOS`)*.
5. **Chỉ khi muốn máy đó ghi thật**, trong cửa sổ **Run as Administrator** — đường dẫn phải **tuyệt đối** vì cửa sổ admin mở ở `C:\Windows\System32`, và phải là `pwsh` chứ không phải `powershell` *(file UTF-8 không BOM, 5.1 parse hỏng)*:

   ```bash
   pwsh -NoProfile -ExecutionPolicy Bypass -File D:\twan_projects\dulieuchungkhoan.vn\scripts\register-tasks.ps1 -LogonType S4U
egister-tasks.ps1 -LogonType S4U
   ```

   Máy dev thuần thì bỏ qua bước này.

🔴 **Dữ liệu KHÔNG đi theo repo.** Hai kho và Redis nằm trong Docker named volume của máy cũ; log, bản đo và vùng spill nằm ở `dlck-runtime/` **ngoài repo**. Máy mới bắt đầu với kho rỗng và **đó là bình thường cho dev** — mọi thứ dựng lại được bằng chuỗi trên, **trừ ba thứ không backfill được: tick realtime, phiên OMO, và frame thô.** Ba thứ đó mất là mất hẳn.

⚠️ **Hai bộ volume, đừng nhầm — kiểm 2026-08-28 trên máy dev hiện tại.** `scripts/stack.mjs` chạy compose với project `-p dlck-infra` ⇒ volume `dlck-infra_pgdata` · `dlck-infra_chdata` · `dlck-infra_redisdata`. Nhưng stack **đang chạy** trên máy này là project `infra` (dựng bằng `docker compose -f deploy/infra/docker-compose.yml` trần, project lấy theo tên thư mục) ⇒ volume `infra_*`. **Dữ liệu thật nằm ở bộ `infra_`**: `infra_chdata` **1,6 GB** so với `dlck-infra_chdata` **11,5 MB**. Hai bộ là **hai kho khác nhau**; chạy nhầm project thì hoặc đụng cổng (nếu bộ kia đang chạy), hoặc lặng lẽ ghi vào kho rỗng. Trên máy mới thì dùng bộ nào cũng được **miễn là nhất quán**; trên máy này phải biết mình đang nói tới bộ nào.

## Bốn tầng hệ thống

```
L0  Nguồn ngoài    BVSC+FiinTrade · WiChart · SBV · FRED · ECB · Yahoo · LBMA · Binance · 8 báo
L1  Thu thập       ETL + Ingester realtime  │  Gom tin + lưới AI
L2  Kho            PostgreSQL + ClickHouse + Redis
L3  Ngữ nghĩa      view người-đọc-được · function calling
L4  Tri thức       hai skill: tư duy (luôn có mặt) + kiến thức (tải khi cần)
```

## Không còn việc chặn bên ngoài — 2026-08-15

Cả ba việc phải chờ bên thứ ba đều đã xong. *(Câu cũ ở đây — "việc kế tiếp là dựng hạ tầng DB" — **đã xong 2026-08-26**.)*

> *Xác nhận ngưỡng rate limit với FiinGroup* — **đã kiểm bằng đúng tải ETL kế hoạch ngày 2026-08-15**: burst Screener 52 trang chạy tuần tự (~29 request/phút, 1,8 phút) không gặp tín hiệu chặn nào, và nguồn không trả header hạn mức nào. Xác nhận chính thức từ FiinGroup không còn là điều kiện chặn. Chủ đích **không dò ngưỡng trần**, và nhịp 8 luồng của ETL hằng ngày thì **chưa kiểm** — xem [quy ước chung §10](docs/10-sources/market/00-conventions.md).

> *Chốt giấy phép WiFeed với WiGroup* — **đã chốt ngày 2026-08-15** (chủ dự án xác nhận). Toàn bộ nhánh vĩ mô và hàng hoá, 87 endpoint, không còn bị chặn về pháp lý. Xem [tình trạng pháp lý WiChart](docs/10-sources/macro/wichart.md).

> Việc thứ ba trước đây — *xin bảng ánh xạ mã chỉ tiêu báo cáo tài chính từ FiinGroup* — **đã tự giải quyết ngày 2026-08-14**, không cần chờ họ nữa: 729 mã lấy từ bundle JS của ứng dụng FiinTrade, phủ 100% response thật, kèm tên Việt/Anh (98,5%) và đơn vị dữ liệu (99,7%). Xem [Phụ lục A §A.5](docs/10-sources/market/appendix-A-field-codes.md).

Hai việc gấp vì **mỗi ngày trì hoãn là một ngày mất vĩnh viễn** — trạng thái 2026-08-28:

1. ✅ **Ingester tích luỹ nến 1 phút — ĐANG CHẠY từ 2026-08-27.** Nến intraday không tồn tại ở bất kỳ nguồn nào, không backfill lại được. Mỗi phiên nay chạy kèm một phiên `--measure` bắt frame thô làm lưới an toàn **và** làm đường nghiệm thu bằng số.
2. ⏸️ **Crawl OMO của Ngân hàng Nhà nước — ĐÃ CHẠY 26/08, tạm tắt 2026-08-28 15:04** *(quyết định chủ dự án: giai đoạn này ưu tiên dev)*. 🔴 **Đồng hồ mất dữ liệu vì thế chạy lại**: nguồn chỉ hiển thị đúng phiên mới nhất, không có kho lưu, ngày nào không crawl là mất hẳn. Điều kiện bật lại, mốc rà và lệnh bật: [lộ trình §2 mục 4d](docs/00-overview/roadmap.md). Xem [`sbv-omo.md`](docs/10-sources/macro/sbv-omo.md).

> ✅ **Việc đo realtime phái sinh — XONG 2026-08-26 (phiên chiều).** Phái sinh **không có kênh riêng**: tick đi chung ba topic `i`/`o10`/`t` với cổ phiếu, phân biệt bằng `EX="XHNF"`, và **không có `openInterest`** trong luồng realtime. Chi tiết: [lộ trình §5.1](docs/00-overview/roadmap.md).

## Nguyên tắc chung

- **Mọi thứ nguồn tự khai về chính nó đều phải kiểm lại bằng dữ liệu.** Nguyên tắc này đã bắt được **53 cạm bẫy và giới hạn thật** *(đếm 2026-08-15: 26 ở ba nguồn ban đầu — 13 quy ước chung, 6 WiChart, 7 nguồn tin; 27 ở sáu nguồn mới — 8 FRED, 5 tỷ giá, 4 Binance, 4 SBV, 3 Yahoo, 3 LBMA)*, không phải giả định.
- 🔴 **Gọi thật vẫn chưa đủ — phải đối chiếu độ tươi với lịch công bố.** Bài học đắt nhất của đợt 2026-08-15: một nguồn trả `HTTP 200`, đủ 294 dòng, không lỗi nào, mà **dữ liệu đã chết gần một năm**.
- **Tài liệu trong `10-sources/` chỉ sửa khi đo lại.** Sửa số mà không đo là nói dối.
- **Số liệu trong skill là tham số ví dụ, không phải dữ kiện.** Toàn bộ là 2022–2024 và đã chết. Công thức thì còn nguyên giá trị.
