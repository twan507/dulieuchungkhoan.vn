# dulieuchungkhoan.vn

Nền tảng dữ liệu và phân tích chứng khoán Việt Nam: thu thập dữ liệu thị trường và tin tức từ nhiều nguồn, lưu vào kho riêng, phân phối lại qua REST và SSE, và một chatbot AI trả lời bằng phương pháp phân tích đã được hệ thống hoá thành skill.

**Trạng thái — 2026-09-07:** thiết kế hoàn chỉnh, và **phần thu thập dữ liệu đã chạy thật trong production** (**15 họ job ETL** — 6 REST FiinTrade + OMO + WiChart + 5 nguồn quốc tế + tin + lưới AI phân loại — cộng ingester realtime; roadmap chuẩn hoá thành 15 lát, **lát 1–11 xong**) — nhưng ⏸️ **mọi job ghi đang tạm tắt để ưu tiên dev** ([lộ trình §2 mục 4d](docs/00-overview/roadmap.md)). Mới nhất: **lát 11 đóng hợp đồng tầng ngữ nghĩa, xong 2026-09-07** — chatbot gọi 9 function đọc kho dưới role chỉ-đọc, khối luật `ANSWER_RULES`, bộ hồi quy 15 câu đạt ngưỡng hình dạng 14/15; **lát 12 xong 2026-09-08, lát 13 — scheduler — xong 2026-09-11 (merge `main` `5e3c72a`)**. Trước đó: lát 10 tầng ngữ nghĩa, lát 9a/9b lưới AI phân loại tin (MiniMax M3), lát 8/8b thu thập tin, lát 7/7b ETL quốc tế, lát 6 vĩ mô WiChart. Và trước nữa `etl fundamentals` 2026-09-04 (27,3 triệu dòng BCTC cho 1.523 mã), `etl price` (91.165 dòng, 38 phút tuần tự; `closePrice` là giá thô nên `close_raw` điền được cả 12,5 năm) và `etl snapshot` (234 lời gọi/ngày, ghi khi đổi); trước nữa `etl events` 2026-09-03 (sáu họ lịch sự kiện, **110.695 dòng**, 9 lời gọi) và `etl screener` (1.541 dòng/ngày, 52 trang). Ingester bắt tick realtime mỗi phiên *(phiên 28/08: **4.722.406 dòng** vào kho, đối chứng sổ sách **dư = 0** trên cả 5 bảng)*; hai kho đã có schema và dữ liệu thật; bộ test chạy trên Postgres/ClickHouse/Redis thật — **số test và cách chạy do [`database/README.md`](database/README.md) sở hữu**, không chép lại ở đây. `api` và `frontend` **chưa bắt đầu**. Hai skill chứng khoán đã xong; bộ hồi quy hiện hành là **vòng 7** dựng lại ở lát 10 *(bộ 10 câu vòng 6 đã mất khỏi repo — [bảo trì skill §6](docs/30-skills/maintenance.md))*. **Không còn việc chặn nào phụ thuộc bên ngoài** — giấy phép WiFeed đã chốt và rate limit FiinGroup đã kiểm, cùng ngày 2026-08-15. Cùng ngày, một **đợt khảo sát nguồn 9 nguồn / ~400 lời gọi thật** đã khép độ rộng dữ liệu: thêm **6 nguồn mới** và mở **5 khối dữ liệu** trước nay bỏ trống.

**Stack chốt 2026-08-24:** Next.js · Python/FastAPI · Postgres + ClickHouse *(lưu tick thô — [ADR 0007](docs/00-overview/decisions/0007-monorepo-layout-and-stack.md))*.

| Khối | Trạng thái | Bằng chứng |
|---|---|---|
| Tài liệu **9 nguồn** — thị trường · vĩ mô VN · quốc tế · tin | ✅ đo thật bằng lời gọi sống | 131 endpoint VN · 87 key · 307 URL · 6 nguồn mới đo 2026-08-15 |
| Độ rộng nguồn dữ liệu | ✅ **khép 2026-08-15** — danh sách *"Ngoài phạm vi"* phân rã hết, không còn mục nào chưa có câu trả lời | [phạm vi nguồn](docs/10-sources/README.md) |
| Từ điển 729 mã trường FiinGroup | ✅ phủ 100% response thật | [field-dictionary.json](backend/etl/data/field-dictionary.json) |
| Chọn nguồn chuẩn cho từng chỉ tiêu | ✅ đã chốt | [chọn trường cho ETL thị trường](docs/20-design/market-field-selection.md) |
| Dự án skill | ✅ **đã đóng**, không còn việc treo | [bảo trì skill](docs/30-skills/maintenance.md) |
| Thiết kế kho dữ liệu · pipeline tin | ✅ đã duyệt, **cả hai đã cài** | kho dữ liệu từ lát 1–7b; pipeline tin lát 8/8b (thu thập) + 9a/9b (lưới AI) |
| Tầng ngữ nghĩa nối dữ liệu ↔ skill | ✅ **dựng lát 10, đóng hợp đồng lát 11** (2026-09-07) | 9 function + vòng chat `python -m agent` — [chatbot-semantic-layer.md](docs/20-design/chatbot-semantic-layer.md) |
| Hai skill chứng khoán | ✅ xong, đã dừng tối ưu; bộ hồi quy hiện hành là **vòng 7** (bộ vòng 6 đã mất khỏi repo) | 3.046 dòng |
| Repo vào git | ✅ khởi tạo 2026-08-14 | commit đầu tiên |
| **Hạ tầng + schema hai kho** | ✅ **2026-08-26** | Postgres **21 migration** (alembic) · ClickHouse **2** · compose PG+CH+Redis |
| **Ingester realtime** | ✅ **ghi thật từ 2026-08-27** — hàng đợi có trần, tràn ra đĩa khi kho trục trặc | 4,72 triệu dòng phiên 28/08 · chưa lần nào phải dùng tới đĩa |
| **ETL theo lịch** | **15/15 họ job chạy được trong container** (lát 12, 2026-09-08) — `docker compose run --rm etl python -m etl <job>`; lịch chung (giờ chạy, chạy bù, chặn chạy chồng) thuộc **lát 13**. 11 task Windows về hưu — gỡ bằng một lệnh PowerShell ở Task 12 (chủ dự án) | 11 task Scheduler, `LogonType=Interactive` (cửa sổ cmd hiện tên task đang chạy; đảo từ S4U 2026-09-04 để khỏi cần admin); **10 `Disabled`, riêng `dlck-price-backfill` `Ready`** *(đọc trạng thái thật 2026-09-07)* |
| **`api` · `frontend`** | ❌ chưa bắt đầu | |

Bảng đầy đủ kèm bằng chứng: [lộ trình §0](docs/00-overview/roadmap.md).

**Khối dữ liệu đã phủ — sau khảo sát 2026-08-15**

| Khối | Nguồn chuẩn | Quy mô đo được *(2026-08-15)* |
|---|---|---|
| Cổ phiếu · chỉ số · sổ lệnh · khối ngoại | BVSC | 1.974 cổ phiếu *(bảng giá gồm cả mã đã rời sàn; tập niêm yết thật sau lượt dọn 2026-09-03: **1.523**)* · 20 chỉ số |
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
| Tin tức | 8 báo điện tử | 47 RSS + 8 nguồn crawl *(6 lượt thường + 2 sitemap chỉ backfill)* |

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
├── backend/             Python — ingester (chạy thật) · etl 15 họ job · agent (tầng ngữ nghĩa) · api (chưa bắt đầu)
│   ├── etl/             omo · refdata · screener · events · price · snapshot · fundamentals
│   │                    wichart · fred · fx · lbma · yahoo · binance · news · classify
│   ├── agent/           9 function + vòng chat terminal; agent/skills/ = hai skill chứng khoán
│   └── tests/           chạy trên Postgres/ClickHouse/Redis THẬT — số test ở database/README.md
├── database/            migrations: Postgres 21 (alembic) · ClickHouse 2
└── deploy/              backend.Dockerfile · infra/clickhouse/*.xml — compose nằm ở gốc: docker-compose.yml + docker-compose.vps.yml
```

## Dựng trên máy mới — dev hay VPS cùng một đường (lát 12, 2026-09-08)

1. `git clone -c core.longpaths=true <url>` *(cờ vô hại trên Linux; cần trên Windows vì đường dẫn dài trong `docs/30-skills/corpus/`)*, rồi `cp .env.example .env` và điền — **chỉ nguyên tố** (host · port · db · user · password), bảy URL được `backend/core/env.py` ráp lúc chạy. Rồi kiểm tên biến — lệnh chỉ in TÊN, không bao giờ in giá trị.

   Cách **chính**, trong container (VPS không cần cài uv/Python):

   ```bash
   docker compose run --rm --no-deps migrate python -m core.env check
   ```

   Biến thể **dev native**, chạy được cả trước lẫn sau `up`:

   ```bash
   cd backend && uv run python -m core.env check
   ```

2. **Một lệnh lên cả hệ** — kho (Postgres · Redis · ClickHouse), `migrate` one-shot (alembic head · `ch_migrate` · cấp 4 user login · tự seed ngành lớp 2), `api`, `etl` (**scheduler**: bảng lịch trong code, chạy bù mốc lỡ, log mỗi job một file — lát 13), `ingester` (daemon, tự ngủ ngoài phiên):

   ```bash
   docker compose up -d --build
   ```

   VPS: `.env` đặt thêm `COMPOSE_FILE=docker-compose.yml:docker-compose.vps.yml` (trần RAM đã đo — [service-topology §7b](docs/20-design/service-topology.md)) rồi **cùng lệnh trên**, không cài gì khác.

3. **Kho mới — hai lệnh sau `up`:** nạp danh bạ rồi chạy lại `migrate` để nó tự seed 161 dòng ngành lớp 2 (migration `0013` cần `market.security` có dòng; `migrate` phát hiện và làm hộ bước tay cũ):

   ```bash
   docker compose run --rm etl python -m etl refdata
   docker compose run --rm migrate
   ```

4. Job bất kỳ: `docker compose run --rm etl python -m etl <job> [cờ]` — cờ từng họ ở [`backend/README.md`](backend/README.md). REPL: `docker compose run --rm agent`. Backup ClickHouse: `docker compose run --rm etl python -m core.ch_backup`.

5. Dev native **không đổi cách gọi**, cùng `.env`: `cd backend && uv run pytest tests -q` (số test ở [`database/README.md`](database/README.md)), `uv run python -m etl <job>`.

🔴 **Dữ liệu KHÔNG đi theo repo.** Hai kho và Redis nằm trong volume `dlck_*` của máy; log/bản đo/spill của ingester ở ba volume `dlck_ingester_*`. Máy mới bắt đầu với kho rỗng — dựng lại được bằng chuỗi trên, **trừ ba thứ không backfill được: tick realtime, phiên OMO, frame thô.** `docker compose down` giữ volume; chỉ `down -v` mới xoá.

⚠️ Docker Desktop trên máy dev vẫn sống trong session người dùng và không tự khởi động sau reboot ([service-topology §5](docs/20-design/service-topology.md)): sau reboot mở Docker Desktop là cả stack tự lên nhờ `restart: unless-stopped`; `migrate` chạy lại (idempotent).

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

1. ⏸️ **Ingester tích luỹ nến 1 phút — chạy 27/08 · 28/08 · sáng 03/09, TẠM TẮT từ 2026-09-03 08:55** *(quyết định chủ dự án: ưu tiên dev, đã đủ dữ liệu bằng chứng; điều kiện bật lại ở [lộ trình §2 mục 4d](docs/00-overview/roadmap.md))*. Nến intraday không tồn tại ở bất kỳ nguồn nào, không backfill lại được. Mỗi phiên nay chạy kèm một phiên `--measure` bắt frame thô làm lưới an toàn **và** làm đường nghiệm thu bằng số.
2. ⏸️ **Crawl OMO của Ngân hàng Nhà nước — ĐÃ CHẠY 26/08, tạm tắt 2026-08-28 15:04** *(quyết định chủ dự án: giai đoạn này ưu tiên dev)*. 🔴 **Đồng hồ mất dữ liệu vì thế chạy lại**: nguồn chỉ hiển thị đúng phiên mới nhất, không có kho lưu, ngày nào không crawl là mất hẳn. Điều kiện bật lại, mốc rà và lệnh bật: [lộ trình §2 mục 4d](docs/00-overview/roadmap.md). Xem [`sbv-omo.md`](docs/10-sources/macro/sbv-omo.md).

> ✅ **Việc đo realtime phái sinh — XONG 2026-08-26 (phiên chiều).** Phái sinh **không có kênh riêng**: tick đi chung ba topic `i`/`o10`/`t` với cổ phiếu, phân biệt bằng `EX="XHNF"`, và **không có `openInterest`** trong luồng realtime. Chi tiết: [lộ trình §5.1](docs/00-overview/roadmap.md).

## Nguyên tắc chung

- **Mọi thứ nguồn tự khai về chính nó đều phải kiểm lại bằng dữ liệu.** Nguyên tắc này đã bắt được **53 cạm bẫy và giới hạn thật** *(đếm 2026-08-15: 26 ở ba nguồn ban đầu — 13 quy ước chung, 6 WiChart, 7 nguồn tin; 27 ở sáu nguồn mới — 8 FRED, 5 tỷ giá, 4 Binance, 4 SBV, 3 Yahoo, 3 LBMA)*, không phải giả định.
- 🔴 **Gọi thật vẫn chưa đủ — phải đối chiếu độ tươi với lịch công bố.** Bài học đắt nhất của đợt 2026-08-15: một nguồn trả `HTTP 200`, đủ 294 dòng, không lỗi nào, mà **dữ liệu đã chết gần một năm**.
- **Tài liệu trong `10-sources/` chỉ sửa khi đo lại.** Sửa số mà không đo là nói dối.
- **Số liệu trong skill là tham số ví dụ, không phải dữ kiện.** Toàn bộ là 2022–2024 và đã chết. Công thức thì còn nguyên giá trị.
