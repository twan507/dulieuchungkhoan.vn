# Lộ trình hợp nhất

**Ngày:** 2026-08-14 · **Cập nhật 2026-08-15** theo đợt khảo sát nguồn *(9 nguồn, ~400 lời gọi thật)* · Gộp danh sách "việc tiếp theo" của ba khối tài liệu, xếp lại theo **phụ thuộc thật** thay vì theo thứ tự từng khối được viết ra.

Ba khối vốn có ba danh sách việc riêng, mỗi danh sách tự cho mình là gốc. Xếp chung mới lộ ra: **một số việc chặn nhiều thứ hơn vẻ ngoài của nó, và một số việc tưởng chặn thì thực ra đã có đáp án.**

---

## 0. Trạng thái hiện tại

| Khối | Trạng thái | Bằng chứng |
|---|---|---|
| Tài liệu nguồn thị trường | ✅ Hoàn chỉnh, kiểm chứng bằng lời gọi thật · **phái sinh và ETF/quỹ bổ sung 2026-08-15** | 131 endpoint, mẫu 51 mã · 14 hợp đồng phái sinh · 31 mã ETF |
| Tài liệu nguồn vĩ mô WiChart | ✅ Hoàn chỉnh + bộ tự kiểm chạy được | 87 key, 509 khẳng định |
| **Tài liệu OMO (SBV)** | ✅ **Mới 2026-08-15** — tải và parse thật 1 phiên | [`macro/sbv-omo.md`](../10-sources/macro/sbv-omo.md) |
| **Tài liệu 5 nguồn quốc tế** | ✅ **Mới 2026-08-15** — FRED · Frankfurter · Yahoo · LBMA · Binance | [`10-sources/global/`](../10-sources/global/) |
| Tài liệu nguồn tin | ✅ Đo thật trên 307 URL, 1.408 tiêu đề | ~570 tin/ngày chưa dedupe |
| Thiết kế kho dữ liệu thị trường | ✅ Đã duyệt · **phần realtime đã có code chạy** (2026-08-26) | schema `rt` + ingester đã dựng; phần REST: lát 1–5 đã chạy thật vào kho (screener · events · price · snapshot · fundamentals, 2026-09-03/04) |
| Thiết kế pipeline tin | ✅ Đã duyệt | chưa viết dòng code nào |
| Hai skill chứng khoán | ✅ Xong, test 6 vòng, **dự án đã đóng 2026-08-14** | 3.046 dòng · [bảo trì skill](../30-skills/maintenance.md) |
| Tầng ngữ nghĩa nối dữ liệu ↔ skill | 🟡 Mới đề xuất, chưa duyệt | [chatbot-semantic-layer.md](../20-design/chatbot-semantic-layer.md) |
| **Từ điển mã trường FiinGroup** | ✅ 729 mã · tên VI/EN 98,5% · đơn vị 99,7% | [field-dictionary.json](../10-sources/market/field-dictionary.json) |
| **Chọn nguồn chuẩn cho từng chỉ tiêu** | ✅ Đã chốt | [chọn trường cho ETL thị trường](../20-design/market-field-selection.md) |
| **Giấy phép WiFeed với WiGroup** | ✅ **Đã chốt 2026-08-15** — mở khoá 87 endpoint vĩ mô/hàng hoá | chủ dự án xác nhận |
| **Rate limit FiinGroup** | ✅ **Đã kiểm bằng đúng tải ETL kế hoạch 2026-08-15** — 64 lời gọi tuần tự, không tín hiệu chặn | [quy ước chung §10](../10-sources/market/00-conventions.md) |
| **Độ rộng nguồn** | ✅ **Khép 2026-08-15** — 9 nguồn, ~400 lời gọi thật. Danh sách *"Ngoài phạm vi"* đã phân rã hết, **không còn mục nào chưa có câu trả lời** | [`10-sources/README.md` §2](../10-sources/README.md) |
| **Repo vào git** | ✅ `git init` + commit đầu 2026-08-14 | toàn bộ docs + hai skill |
| **Stack sản phẩm + cây monorepo** | ✅ **Chốt 2026-08-24** — Next.js · Python/FastAPI · Postgres + ClickHouse (lưu tick thô) · skill dời về `backend/agent/skills/` | [ADR 0007](decisions/0007-monorepo-layout-and-stack.md) |
| **Hạ tầng + schema hai kho** | ✅ **Xong 2026-08-26** — compose (PG+Redis+CH, profile `realtime`) · schema `postgres-data` **17 migration** · schema `rt` ClickHouse 2 migration · **596 test** *(số cập nhật 2026-09-05 sáng sau hai fix `status 0`/ngày VN; 593 tối 04/09 sau lát 5 và fix mốc nước lát 4; sau lát 4 là 533 + 2 skipped — spec lát 4 ghi 523 vì thiếu 10 test của `4d193f5`; sau lát 3 là 456; sau lát 2 là 399, mốc 2026-08-28 là 321, lúc dựng xong 26/08 là 10 migration / 71 test)* · một lượt dev trọn (dev-start → migrate → test → dev-stop) chạy sạch | [database/README.md](../../database/README.md) |
| **Code sản phẩm (ingester · ETL thật · api)** | 🟡 **Lát cắt dọc đầu đã dựng 2026-08-26** — `ingester` (socket EIO3 → chuẩn hoá → Redis + ClickHouse, leader lock, đối chứng cuối phiên) và job `etl omo`; đã qua review toàn nhánh và **merge `main` 2026-08-26** *(194 test lúc đó)*. **Cập nhật 2026-08-28: 321 test xanh** — thêm lát tràn-ra-đĩa (AC3 đóng, dư = 0), job `etl refdata`, cây ngành hai lớp, và 7 task chuyển `LogonType=S4U`. Job OMO đã chạy thật từ 26/08 (4 mốc/ngày) — nhưng ⏸️ **cả 4 task OMO đã `Disabled` lúc 2026-08-28 15:04**. Trạng thái, điều kiện bật lại do **mục [4d] ở §2** sở hữu — không chép lại ở đây. **Ghi tick bật 2026-08-26 tối** — phiên ghi thật đầu tiên là 27/08, chạy song song một phiên `--measure` làm lưới an toàn. ⏸️ **TOÀN BỘ 7 task ghi dữ liệu đã `Disabled` lúc 2026-09-03 ~08:55** *(quyết định chủ dự án: giai đoạn này ưu tiên dev, đã có đủ phiên 27/08 · 28/08 + sáng 03/09 làm bằng chứng)*. Hai tiến trình đang chạy (`dlck-ingester`, `dlck-ingester-measure`) bị dừng giữa phiên. Ba đồng hồ mất dữ liệu (tick · frame thô · OMO) vì thế **cùng chạy**; điều kiện bật lại do **mục [4d] ở §2** sở hữu. ⚠️ `scripts/register-tasks.ps1` tự `Enable` `dlck-ingester` khi chạy lại — đừng chạy script đó trong lúc tạm dừng. `api` chưa bắt đầu. **[7] ETL hằng ngày tách thành chuỗi lát; lát 1 `etl screener` ✅ XONG 2026-09-03** — đã merge `main`, chạy thật sau phiên **1.541 dòng/ngày**, 351 test xanh ([spec](../90-records/plans/2026-09-03-screener-daily-etl/spec.md) · [ledger](../90-records/plans/2026-09-03-screener-daily-etl/ledger.md)). **Lát 2 `etl events` ✅ XONG 2026-09-03** — sáu họ `Calendar/GetCorporate*` → `market.corporate_event`, chạy thật vào kho production: **110.695 dòng**, **517 issuer tối thiểu** tạo mới (bảng `issuer` 1.552 → 2.069), 42 bản ghi gộp vì đụng khoá tự nhiên, 9 lời gọi ~2 phút 39 giây, lượt hai idempotent (0 issuer mới, 0 dòng mới), **399 test xanh** ([spec](../90-records/plans/2026-09-03-events-daily-etl/spec.md) · [ledger](../90-records/plans/2026-09-03-events-daily-etl/ledger.md)). **Lát 3 `etl price` ✅ XONG 2026-09-04** — `getPriceData` trang 1 của **1.523** cổ phiếu niêm yết → `market.price_daily`, chạy thật: **91.165 dòng** (60 phiên/mã), **38 phút tuần tự, 0 retry, 0 tín hiệu chặn**; `close_raw` điền từ `closePrice` cho cả lịch sử (phát hiện mới, đã kiểm 3 cách); backfill 12,5 năm có con trỏ, chạy bằng task `dlck-price-backfill` (thứ 7, hoặc kích hoạt tay buổi tối, tự dừng trước phiên); **456 test xanh** ([spec](../90-records/plans/2026-09-03-price-daily-etl/spec.md) · [ledger](../90-records/plans/2026-09-03-price-daily-etl/ledger.md)). **Lát 4 `etl snapshot` ✅ XONG 2026-09-04** — 234 lời gọi/ngày, ghi khi đổi ([spec](../90-records/plans/2026-09-04-snapshot-family-etl/spec.md) · [ledger](../90-records/plans/2026-09-04-snapshot-family-etl/ledger.md)). **Lát 5 `etl fundamentals` ✅ XONG 2026-09-04** — ba báo cáo tài chính + danh sách PDF + từ điển 729 mã, migration `0017`, **591 test xanh** lúc đóng lát, 593 sau fix mốc nước lát 4 ([spec](../90-records/plans/2026-09-04-fundamentals-etl/spec.md) · [ledger](../90-records/plans/2026-09-04-fundamentals-etl/ledger.md)) | [plans/2026-08-26-ingester-omo-first-slice/](../90-records/plans/2026-08-26-ingester-omo-first-slice/) |
| **Realtime phái sinh** | ✅ **Đã đo 2026-08-26 trong phiên** — phái sinh đi chung topic `i`/`o10`/`t` với cổ phiếu (`EX="XHNF"`), không có kênh riêng, không có `openInterest` | [§5.1](#51--realtime-phái-sinh--đã-đo-2026-08-26-phiên-chiều) · [hồ sơ đo](../90-records/surveys/2026-08-26-bvsc-realtime-session/README.md) |

## 1. Việc chặn nhiều thứ nhất — làm trước

| # | Việc | Chặn cái gì | Nguồn |
|---|---|---|---|
| ~~1~~ | ~~Dựng hạ tầng Postgres + ClickHouse (+ Redis)~~ | ✅ **Xong 2026-08-26** — compose profile `realtime`, schema cả hai kho đã migrate, một lượt dev trọn chạy sạch ([database/README.md](../../database/README.md)). Việc chặn đã hết — [4] và [6] đều làm được ngay | kho dữ liệu §8 GĐ 0 · [ADR 0007](decisions/0007-monorepo-layout-and-stack.md) |
| ~~1b~~ | ~~Xác nhận rate limit với FiinGroup~~ | ✅ **Đã kiểm bằng tải kế hoạch 2026-08-15** — burst Screener 52 trang chạy tuần tự (~29 request/phút, 1,8 phút) không gặp tín hiệu chặn nào, và không có header hạn mức nào. Xác nhận chính thức từ FiinGroup **không còn là điều kiện chặn**. Chủ đích không dò ngưỡng trần; nhịp 8 luồng thì chưa kiểm — xem [§10 quy ước chung](../10-sources/market/00-conventions.md). *(Danh sách 11 mã chỉ tiêu chưa giải mã vẫn gửi kèm khi có dịp trao đổi — xem [Phụ lục A §A.5](../10-sources/market/appendix-A-field-codes.md), không chặn việc gì)* | |
| ~~2~~ | ~~Chốt giấy phép WiFeed với WiGroup~~ | ✅ **Đã chốt 2026-08-15** — chủ dự án xác nhận. Mở khoá toàn bộ nhánh vĩ mô/hàng hoá, 87 endpoint | |
| ~~3~~ | ~~Yêu cầu FiinGroup bảng ánh xạ mã chỉ tiêu BCTC~~ | ✅ **Đã tự giải quyết 2026-08-14** — 729 mã, độ phủ 100% trên response thật, lấy từ bundle JS ứng dụng FiinTrade. Kèm tên Việt/Anh (98,5%) và **đơn vị dữ liệu** (99,7%). Xem [Phụ lục A §A.5](../10-sources/market/appendix-A-field-codes.md). Còn 11 mã chưa giải mã — không chặn việc gì | |

Ba việc 1b–3 đều **phụ thuộc bên ngoài**, không tự làm được, và thời gian chờ không kiểm soát được. **Cả ba nay đã xong.** Việc chặn duy nhất còn lại là dựng hạ tầng — việc tự làm được, không phải chờ ai.

## 2. Việc gấp vì mất dữ liệu theo thời gian

> Xếp riêng vì chúng không chặn thứ gì, nhưng **mỗi ngày trì hoãn là một ngày mất vĩnh viễn.**

| # | Việc | Vì sao không hoãn được |
|---|---|---|
| **4** | **Ingester realtime + tích luỹ `bar_1m`** — 🟡 *code đã dựng xong 2026-08-26 ([hồ sơ lát cắt](../90-records/plans/2026-08-26-ingester-omo-first-slice/)); đã bắt được **một phiên chiều** bằng chế độ `--measure` (2,3 triệu frame). Phiên đo trọn trong giờ giao dịch (SM + phái sinh §5.1 + giờ đẩy idx — spec ClickHouse §4.1/§10) **vẫn cần**, nhưng không còn chặn: ✅ **GATE MỞ 2026-08-26 tối (quyết định chủ dự án).** Hai minor M-new-1 (phân loại lỗi ghi theo mã số) và M-new-3 (ngân sách xả cuối phiên) đã sửa; điều kiện thứ ba — phiên đo trọn ngày — chuyển thành **chạy song song** thay vì chạy trước: `dlck-ingester` ghi thật, `dlck-ingester-measure` bắt frame thô cùng lúc làm lưới an toàn và đồng thời trả lời câu hỏi `SM` mà [spec ClickHouse §4.1](../90-records/plans/2026-08-25-clickhouse-realtime-store/spec.md) đòi. Phiên ghi đầu tiên: **27/08**. Chạy thử đường ghi dưới quyền production trước khi bật đã lộ một bug chặn hẳn (`assert_migrated` đòi DDL) — xem [ledger](../90-records/plans/2026-08-26-ingester-omo-first-slice/ledger.md). ⚠️ **Sự cố 2026-09-03 08:30:** reboot 08:00:45, Docker Desktop không tự lên, ingester chết ở hợp đồng khởi động, dựng lại tay 08:37, không mất tick — chủ sở hữu: [service-topology §5](../20-design/service-topology.md)* | Nến intraday **không tồn tại ở bất kỳ nguồn nào**. Mọi dữ liệu khác crawl lại lúc nào cũng được, riêng cái này không |
| ~~**4b**~~ | ~~Cho `--measure` chạy thường trực song song phiên ghi~~ ✅ **Xong 2026-08-27** — `dlck-ingester-measure` đổi thành hằng ngày (kiểm trigger thật: Weekly Thứ 2–6, 08:30, mốc kế 28/08); chính sách giữ 30 ngày nằm trong chính job đo (`prune_old`, 2 test seam); ngân sách RAM/đĩa ghi vào [service-topology §7b](../20-design/service-topology.md). *Không thay được [lát tràn-ra-đĩa](../90-records/plans/2026-08-28-ingester-spill-to-disk/brief.md) — chỉ là lưới an toàn trong lúc chờ* | Mỗi phiên chạy không có bản thô là một phiên **không thể dựng lại và không thể nghiệm thu**. Chi tiết ở §2.1 dưới |
| **4c** | **Lát tràn-ra-đĩa** ([spec](../90-records/plans/2026-08-28-ingester-spill-to-disk/spec.md)) — đóng chỗ hở §2.1 dưới (`pending` không trần). ✅ **XONG 2026-08-28** — hai vòng quản/ghi tách biệt, hai cửa vào chế độ đĩa, hai loại file `-r`/`-n`, bộ đếm `d[]` (`--count`); N/K/trần đĩa điền theo số đo gate cùng ngày (spec §2.5). **AC2 (chaos, `docker stop` thật) PASS có số**: 200.000 fed / 200.000 stored / 0 dup / RSS đỉnh 78,7 MB / 253 block spill+replay. **AC3 ĐÓNG 2026-08-28: dư = 0 cả 5 bảng** trên phiên đầu tiên chạy code spill (4.722.406 dòng; `spill_bytes = 0` — chưa lần nào phải vào chế độ đĩa) — hồ sơ: [ledger](../90-records/plans/2026-08-28-ingester-spill-to-disk/ledger.md) | Đóng đúng chỗ hở mà [4b] chỉ che tạm bằng lưới an toàn — không có nó thì ATO mạnh trùng lúc CH trục trặc vẫn OOM mất dữ liệu im lặng |
| **4d** | **Bật lại toàn bộ task ghi dữ liệu** — ⏸️ 4 task OMO `Disabled` từ **2026-08-28 15:04**; **cả 7 task `Disabled` từ 2026-09-03 ~08:55** *(quyết định chủ dự án: giai đoạn này ưu tiên dev, đã đủ dữ liệu bằng chứng — 27/08 · 28/08 trọn phiên, 03/09 tới 08:55)*. 🔴 **Điều kiện bật lại — chốt lại 2026-09-04 (quyết định chủ dự án): khi đã đi HẾT roadmap và DB hoàn thiện toàn bộ, lúc đó bật TẤT CẢ task cùng một lúc làm một lượt chạy thử toàn hệ.** Trong suốt giai đoạn dev, mọi task giữ nguyên `Disabled`; job nào cần chạy thì chạy tay từng lượt, không bật task. ⚠️ Điều kiện cũ *"khi [7] ETL hằng ngày chạy ổn định"* và **mốc rà cứng 2026-09-15** (cả hai chốt 2026-08-28) nay **hết hiệu lực** — bị thay, không phải bị quên. Đánh đổi là có chủ ý: ba đồng hồ mất dữ liệu ở cột phải chạy suốt giai đoạn dev, chủ dự án đã cân và chọn ưu tiên dev. **Ngoại lệ duy nhất, chốt cùng ngày: `dlck-price-backfill` bật từ thứ 7 2026-09-05** — hôm nay 04/09 chưa bật; nó chỉ đọc lịch sử, không phụ thuộc phiên, và mỗi cuối tuần không chạy là một tuần backfill đứng yên. *(Ghi chú cũ 2026-09-03 08:33, nay đã bị điều kiện trên thay: vẫn tắt; ngân hàng nghỉ 31/08–02/09 nên phiên OMO mất thật tới lúc đó chỉ là phần sau 11:30 của 28/08.)* Bật lại: `Get-ScheduledTask -TaskName "dlck-*" | Enable-ScheduledTask` *(rồi kiểm `State` từng task — Enable không khởi động lượt đã lỡ)*. ✅ Từ 2026-09-03 script đăng ký **9 task** và **cả 9 đã đăng ký thật trên máy** (`dlck-screener` 15:20 · `dlck-events` **18:10**), `LogonType=S4U`, **tất cả `Disabled`** cùng cả đội; **từ 2026-09-04 script lên 11 task, cả 11 đã đăng ký thật trên máy** (`dlck-price` 15:40 · `dlck-price-backfill` thứ 7 00:05, giới hạn chạy 72 giờ — AC8 lát 3, chủ dự án chạy trong cửa sổ admin ~07:30); **cùng ngày đảo `LogonType` về `Interactive`** (cửa sổ cmd có tiêu đề tên task, đăng ký không cần admin — [service-topology §5](../20-design/service-topology.md)), **tất cả `Disabled`** | **Tick và frame thô mất từ 2026-09-03 08:55** — nến 1 phút không tồn tại ở nguồn nào, mỗi phiên tắt là mất hẳn. SBV **không cho backfill** — chỉ hiển thị phiên mới nhất, không có kho lưu *(`sbv-omo.md` Giới hạn 1)* ⇒ mỗi ngày làm việc kể từ **29/08** là một phiên mất hẳn. Và cột **đáo hạn/bơm ròng phải tự dựng** từ kỳ hạn, cần **~140 ngày tích luỹ** mới có số ròng đầy đủ ⇒ mỗi ngày tắt còn đẩy lùi luôn mốc đó |
| **5** | **Backfill lịch sử tin** từ sitemap TinnhanhCK / BNews / NguoiQuanSat | Dữ liệu chỉ còn chừng nào họ còn giữ sitemap |

**Ingester chờ hạ tầng DB — quyết định chủ dự án 2026-08-15.** Nó không còn chạy song song ngay từ đầu nữa mà xếp sau [1]. Lý do gấp thì **không mất đi**: mỗi ngày chưa có Ingester vẫn là một ngày nến 1 phút mất vĩnh viễn, không nguồn nào backfill lại được. Đó chính là **lý do dựng hạ tầng DB là việc kế tiếp** — làm xong hạ tầng là đồng hồ mất dữ liệu dừng lại. *(Cập nhật 2026-08-26: hạ tầng đã xong — điều kiện chờ đã hết.)*

### 2.1 Vì sao `--measure` nên chạy thường trực

*(Ghi 2026-08-27 sau phiên ghi thật đầu tiên — hôm đó nó chạy song song đúng một lần, và tự chứng minh giá trị.)*

Nó làm **hai việc** mà không cơ chế nào khác đang làm:

**1 · Lưới an toàn dựng lại được.** Đường ghi từng có một chỗ hở đã biết: hàng đợi `pending` không trần, nên ATO mạnh trùng lúc ClickHouse trục trặc có thể làm tiến trình OOM và **mất sạch dữ liệu trong bộ nhớ, im lặng** *(phân tích đầy đủ ở [brief tràn-ra-đĩa](../90-records/plans/2026-08-28-ingester-spill-to-disk/brief.md) §2)*. Có bản thô thì mất là **dựng lại được**; không có thì mất vĩnh viễn. ✅ **Chỗ hở đã vá 2026-08-27 tối** — [lát tràn-ra-đĩa](../90-records/plans/2026-08-28-ingester-spill-to-disk/spec.md) [4c] ở §2 trên đặt trần RAM + hàng đợi đĩa, code xong, AC2 (chaos) pass có số, và **AC3 chốt 2026-08-28 — hằng đẳng thức sổ sách dư = 0 cả 5 bảng** trên phiên thật đầu tiên chạy code đó. `--measure` vẫn giữ nguyên vai trò lưới an toàn độc lập + đường nghiệm thu bằng số (điểm 2 dưới), không phải chỉ là giải pháp tạm.

**2 · Đường nghiệm thu *"không mất dòng nào"* bằng SỐ.** Bản thô là **đếm độc lập** với kho, cùng một phiên, hai tiến trình không dùng chung gì ngoài socket. Đó là cách duy nhất chứng minh tính toàn vẹn bằng con số thay vì bằng lập luận — và là tiêu chí nghiệm thu mà lát tràn-ra-đĩa sẽ cần.

Phiên 2026-08-27 chạy cả hai: `t` khớp **205.130 = 205.130** và `ptm` khớp **2.298 = 2.298** tuyệt đối. *(Các topic khác chênh ~0,09%, phần lớn do `dup_dropped = 1.953` và 5 phút đuôi. ⚠️ Chưa phải bằng chứng: measure đếm **frame**, kho đếm **dòng** — một frame mang nhiều bản ghi trong mảng `d[]`. Muốn thành phép nghiệm thu thật thì phải đếm bản ghi trong `d[]`, không đếm frame.)*

**Chi phí:** **93 MB gzip một ngày** *(đo 2026-08-27, trọn phiên)* ≈ 23 GB/năm nếu giữ hết — nên **phải kèm chính sách xoá**, không giữ vô hạn. Đĩa VPS 60 GB không gánh nổi bản thô vô thời hạn. ✅ **Đã cài giữ 30 ngày** (≈ 2,8 GB thường trực; hằng số `KEEP_DAYS` trong `backend/ingester/measure.py`).

🔴 **Đính chính** *(dòng cũ ở đây từng viết "khi lát tràn-ra-đĩa xong có thể rút xuống vài ngày" — sai)*: lát tràn-ra-đĩa xong **không** làm bản đo bớt cần thiết. AC3 của chính lát đó ([spec §12](../90-records/plans/2026-08-28-ingester-spill-to-disk/spec.md)) — hằng đẳng thức sổ sách đối chứng `expected` (từ bản đo, qua bộ đếm `d[]`) với `actual` (kho thật) — **dùng bản đo làm số độc lập để nghiệm thu**, không phải nạng chống tạm. Bản đo vì vậy là **hạ tầng nghiệm thu thường trực**, không phải lưới an toàn sẽ hết cần khi lát này xong; chính sách giữ **30 ngày đứng nguyên**.

**Việc phải làm** *(nhỏ, rời nhau)* — ✅ **cả ba xong 2026-08-27**:

1. ~~`scripts/register-tasks.ps1`: `dlck-ingester-measure` từ `-Once` chuyển thành hằng ngày~~ ✅ — bỏ chốt chặn "đã tồn tại thì giữ nguyên" lẫn nhánh `-Once` (không còn ai dùng); đăng ký lại thật và soi trigger: Weekly Thứ 2–6 08:30.
2. ~~Thêm chính sách xoá file đo cũ~~ ✅ — một dòng trong chính job đo: `prune_old` chạy đầu mỗi phiên `--measure`, xoá thư mục `YYYYMMDD` quá 30 ngày (2 test seam, có case biên đúng ngày cắt).
3. ~~Kiểm ngân sách RAM~~ ✅ — **97 + 13 MB** *(đo 2026-08-27)* nằm trong trần 200 MB, đã ghi thành dòng riêng trong bảng [service-topology §7b](../20-design/service-topology.md) để không quên khi lên VPS 6 GiB.

⚠️ **Một điều chưa đo:** hai tiến trình mở **hai socket riêng** tới BVSC. Hôm nay chạy song song trọn phiên không gặp vấn đề gì, nhưng chưa ai kiểm nguồn có giới hạn số kết nối không. Không chặn việc này, nhưng đừng suy ra là "chắc chắn an toàn với N kết nối".

## 3. Việc theo thứ tự phụ thuộc

*Cây dưới đây là bức tranh phụ thuộc vẽ 2026-08-14 (nhãn trong ngoặc vuông). Nó vẽ nhánh tin song song vì lúc đó chưa chốt làm lần lượt — **thứ tự làm là khối "lát 1–14" và luật thứ tự phía dưới, không phải hình dạng cây.***

```
[1] hạ tầng
     │
     ├─→ [6] Bảng tham chiếu + ETL danh bạ  ✅ XONG 2026-08-26 đêm (job `etl refdata` chạy thật, 2.015 mã; NGÀNH chưa gán — xem ghi chú dưới cây)
     │        │
     │        ├─→ [7]  ETL hằng ngày: giá, snapshot, screener, lịch sự kiện
     │        │         └─→ [8] Bộ giám sát hợp đồng (dựng cùng, dùng chung script)
     │        │              └─→ [9] Backfill lịch sử giá ✅ task dlck-price-backfill, chạy cuối tuần
     │        │                   └─→ [9b] Scheduler trong container etl (lát 13) ─→ [9c] Lên VPS (lát 14, sau cùng)
     │        │
     │        └─→ [10] Khung thu thập tin + chuẩn hoá, chạy KHÔNG có AI 1 tuần
     │                  └─→ [11] Đo tỷ lệ dedupe thật
     │                       └─→ [12] Chốt ngân sách token → bật lưới phân loại
     │
     └─→ [4] Ingester realtime (ưu tiên cao, ngay sau khi hạ tầng DB xong)

[7] + [12] ─→ [13] Tầng ngữ nghĩa + function calling
                    └─→ [14] Test lại vòng 6 CÓ function calling
```

**[6] là nút thắt thật của cả hệ** — và **đã thông 2026-08-26 đêm**: job `python -m etl refdata` chạy thật 2 lượt (idempotent), 2.015 security · 1.550 issuer · 176 mã ICB vào kho, task `dlck-refdata` 08:00/ngày; hồ sơ: [plans/2026-08-26-reference-data-etl/](../90-records/plans/2026-08-26-reference-data-etl/). ✅ **Phần NGÀNH: đã nạp DB 2026-08-28** — migration `0011` (đổi 6 code + 7 tên ngành) · `0012` (bảng `market.issuer_industry_override` + view `market.v_issuer_industry`) · `0013` (seed **55 dòng** lớp 1 + **161 dòng** lớp 2), chủ sở hữu nội dung [industry-mapping.md](../20-design/industry-mapping.md) + bản máy đọc `.json`. Nghiệm thu trên DB thật dưới role `dlck_etl` *(hồ sơ: [ledger](../90-records/plans/2026-08-27-industry-two-layer-mapping/ledger.md))*: job `etl refdata` hai lượt idempotent, **1.526/1.550 issuer có ngành, 24 quỹ/ETF không có ngành theo đúng thiết kế** (`com_type_code='QU'`, `icb_code='8985'` — dòng ICB `8980` cố ý không nạp); năm bất biến của spec đều đạt trên DB thật (`A=0 · B=0 · C=161 · D=55 · E=none`). Hệ quả: tầng lọc tin theo ngành của [10] và khung ngành cho skill **hết bị chặn**.

**[7] tách thành chuỗi lát — quyết định chủ dự án 2026-08-28.** [7] thực ra là bốn họ (Screener 52 · giá 1.974 · snapshot ~4.000 · lịch sự kiện ~10 lời gọi/ngày) cộng một lớp HTTP chưa có *(con số snapshot ~4.000 đã sai — sửa 2026-09-03, xem dưới)*; gói một spec thì một tiêu chí hỏng chặn cả bốn. **Lát 1 = `etl screener`**, vì đó là họ duy nhất đã đo an toàn đúng tải kế hoạch. Spec [2026-09-03](../90-records/plans/2026-09-03-screener-daily-etl/spec.md) — ✅ **duyệt 2026-09-03**; code + review xong cùng ngày, **đã chạy thật ghi 1.541 dòng** (AC3 chính thức chờ sau 15:05). Task `dlck-screener` sẽ đăng ký nhưng **để `Disabled`** cùng cả đội cho tới khi [4d] bật lại.

🔴 **Thứ tự lát ĐÃ ĐẢO — chốt 2026-09-03 sau khi soi họ Snapshot và đo độ phủ lịch sự kiện.** Thứ tự cũ (giá → snapshot → lịch sự kiện) sai theo phụ thuộc thật:

```
lát 1   screener                 ✅ XONG 2026-09-03
lát 2   lịch sự kiện             ✅ XONG 2026-09-03 — mở khoá snapshot, BCTC, re-crawl giá theo sự kiện quyền
lát 3   giá theo ngày            ✅ XONG 2026-09-04 — 1.523 lời gọi tuần tự 38 phút; close_raw điền được cả lịch sử;
                                   backfill = task dlck-price-backfill, tự chạy cuối tuần tới khi hết vòng
lát 4   họ Snapshot              ✅ XONG 2026-09-04 — 234 lời gọi/ngày (quota cuốn chiếu), ghi KHI ĐỔI,
                                   sổ kiểm ops.snapshot_check vừa cấp danh sách tới hạn vừa đếm lỗ của lịch
lát 5   BCTC                     ✅ XONG 2026-09-04 — trigger Earning + quét sàn 90 ngày (quota 20/kind), ghi KHI ĐỔI với hash
                                   TRỌN payload (không danh sách trắng), bỏ null, điền đầu bằng --backfill; sổ kiểm ops.fundamentals_check
lát 6   giám sát hợp đồng        contract_snapshot (market-data-store §7.1) — bắt nguồn đổi schema/độ tươi trước khi guard
                                   phải từ chối cả lượt; dùng chung script với 5 lát trên. TIẾP THEO.
lát 7   vĩ mô WiChart            87 key vĩ mô + hàng hoá → macro.observation (10-sources/macro/wichart.md; 6 bẫy: epoch giờ VN,
                                   15 series sai nhãn đơn vị 1000 lần ⇒ bảng hệ số hardcode)
lát 8   quốc tế                  FRED · Frankfurter · Yahoo · LBMA · Binance → macro.observation + asset.price_daily/ohlc_daily
                                   (10-sources/global/; FRED vá hồi tố ⇒ UPSERT; giá dầu có cột phân biệt giao ngay/tương lai)
lát 9   tin tức — thu thập       khung thu thập + chuẩn hoá + lưu toàn văn (news-pipeline §9.1), chạy KHÔNG có AI 1 tuần
lát 10  tin tức — lưới AI        đo tỷ lệ dedupe thật → chốt ngân sách token → bật lưới phân loại 20 sub + gắn mã
lát 11  tầng ngữ nghĩa           nối kho ↔ hai skill chứng khoán, function calling (chatbot-semantic-layer.md)
lát 12  test vòng 6              có function calling
lát 13  scheduler trong etl      thay 11 task Windows bằng một bảng lịch trong code, chạy bù, bật lại [4d] — xem "Lát 13" dưới;
                                   rồi CẢ HỆ chạy thử trên máy dev vài ngày liền bằng chính bảng lịch này
lát 14  lên VPS                  chỉ khi lát 13 đã ổn vài ngày — hồ sơ docker-compose.vps.yml (service-topology §7b), chuyển hai kho,
                                   ingester active/standby
```

**Bảng ánh xạ tên cũ → lát chuẩn** *(tên trong ngoặc vuông là nhãn của cây phụ thuộc phía trên, viết 2026-08-14; "lát 7/8" cũ là cách gọi từ 2026-09-03 tới 2026-09-04 chiều — tài liệu lịch sử trong `90-records/` vẫn dùng tên cũ, đúng luật không viết lại quá khứ)*:

| Tên cũ | Nay là | Trạng thái |
|---|---|---|
| [1] hạ tầng · [4] ingester realtime · [6] bảng tham chiếu + ETL danh bạ · [9] backfill lịch sử giá | ngoài chuỗi lát | ✅ xong (backfill giá chạy bằng task `dlck-price-backfill`) |
| [7] ETL hằng ngày | lát 1–5 | ✅ xong |
| [8] bộ giám sát hợp đồng | **lát 6** | tiếp theo |
| *(chưa có tên)* ETL vĩ mô / quốc tế | **lát 7, lát 8** | mới thêm 2026-09-04 tối — chủ dự án gọi tên |
| [10] khung thu thập tin không AI | **lát 9** | |
| [11] đo dedupe · [12] ngân sách token + lưới phân loại | **lát 10** | |
| [13] tầng ngữ nghĩa · [14] test vòng 6 | **lát 11, lát 12** | |
| *(lưu ý tra cứu)* "lát 7" và "lát 8" | hai nghĩa theo thời gian viết: trước 2026-09-04 tối = scheduler/VPS (nay 13/14), sau = WiChart/quốc tế | hồ sơ trong `90-records/` giữ nghĩa cũ |
| [9b] "lát 7" scheduler trong etl | **lát 13** — chuẩn hoá cách chạy sau cùng, kèm vài ngày chạy thử trên dev | |
| [9c] "lát 8" lên VPS | **lát 14** — sau cùng | |


🔴 **Luật thứ tự (chốt 2026-09-04):** đi từ trên xuống, **không nhảy lát**; mỗi lát một session mới, bắt đầu từ mục *"Điểm vào cho lát N"* của lát trước và khép bằng cách viết *"Điểm vào cho lát N+1"*. **Làm lần lượt, không song song** *(chủ dự án chốt 2026-09-04 tối, thay cho ý "nhánh tin chạy song song" của bản chiều)*: gom hết nguồn (lát 7–8) và tin (lát 9–10) về kho, nối tầng ngữ nghĩa và test vòng 6 (lát 11–12), **rồi mới chuẩn hoá cách chạy** (lát 13, scheduler) và **cả hệ chạy thử trên máy dev vài ngày**, cuối cùng mới lên VPS (lát 14). Việc cắt ngang (bật lại [4d], spec tự ngắt ngày lễ, mở rộng danh mục phái sinh) chỉ làm khi chủ dự án gọi tên, không tự chen; ETL vĩ mô/quốc tế đã được gọi tên và thành lát 7–8.

**Lát 13 — scheduler trong `etl` (thêm 2026-09-04 với tên "lát 7", đổi số 2026-09-04 tối; sinh ra sau khi đăng ký task admin lộ ra là mệt và khó quản).** Container `etl` của `deploy/app` hiện chỉ có heartbeat walking-skeleton; [service-topology §1–2](../20-design/service-topology.md) đã định nghĩa `etl` là *"job theo lịch, scheduler kích hoạt"*. Lát này thay 11 task Windows bằng **một bảng lịch trong code** (refdata 08:00 · screener 15:20 · price 15:40 · events 18:10 · OMO 4 mốc · price-backfill thứ 7 · quét sàn của lát 4, giờ VN), một vòng lặp spawn `python -m etl <job>` làm tiến trình con (lỗi job này không kéo đổ job kia, log tách riêng), chặn chạy chồng, và **tự chạy bù** mốc đã qua trong ngày mà `ops.etl_run` chưa có lượt success (mọi job đều idempotent). Cùng một code chạy **native trên dev** (`uv run python -m etl`, một cửa sổ thay 11 — không admin, không Docker Desktop trong session) và **trong container trên VPS** (`restart: unless-stopped`, sống qua reboot). `ingester` là daemon, không đi qua bảng này — service riêng có `restart`. Xong lát này thì `scripts/register-tasks.ps1` về hưu. Đứng **sau** lát 6–12 (chưa đau: 11 task đang `Disabled` theo [4d]; chủ dự án muốn xong hết nguồn, tin và tầng ngữ nghĩa rồi mới chuẩn hoá cách chạy một lần) và **ngay trước** lát 14 vì VPS không có Task Scheduler — chính bảng lịch này là thứ chạy thử vài ngày trên dev trước khi lên VPS. Bảng lịch lúc đó gồm cả job vĩ mô/quốc tế/tin của lát 7–10.

**Hai quyết định kèm theo, cùng ngày:** (a) bỏ hai kind chấm điểm `company_score` và `rate_indicator` khỏi `snapshot_daily` — migration `0015`, vì nội dung thật là điểm chữ (`C`/`B`/`D`) và cờ `0.00`/`1.00`, đúng nhóm *không dùng điểm bên thứ ba* đã loại; (b) họ Snapshot **không chạy hằng ngày** mà kích hoạt theo sự kiện kèm quét sàn, vì **không trường nào trong 18 trường ta lưu đổi theo ngày**. Ngân sách ngày vì thế xuống **≈ 2.300 lời gọi** thay vì ~6.000 *(đo thật ở lát 4 ngày 2026-09-04: **1.822** — họ Snapshot chốt ở 234 chứ không 200–260, và tập niêm yết là 1.523 chứ không 1.974)* — bài toán nhịp 8 luồng của lát giá dễ thở hơn nhiều so với ước lượng cũ.

⚠️ **Lịch sự kiện KHÔNG đầy đủ tuyệt đối** — đo 2026-09-03 bằng nguồn độc lập ([`08-fiin-event-calendar.md`](../10-sources/market/08-fiin-event-calendar.md)): `ShareIssuance` 100 % · `Earning` 96,4 % *(sót chỉ ở ≤ 2022)* · `CashDividend` 98,6 % **có sót ở vùng gần đây**. Nên trigger phải đi kèm quét sàn; quét sàn đồng thời là **thước đo** lỗ của lịch.

### Lát 3 — giá theo ngày ✅ XONG 2026-09-04

**`python -m etl price`** — hai chế độ một đường code: hằng ngày (trang 1 = 60 phiên của **1.523** cổ phiếu niêm yết, một giao dịch, guard trước commit) và `--backfill` (mọi trang ~12,5 năm, mỗi mã một giao dịch, con trỏ trong `ops.etl_run.stats`, ngân sách `--max-minutes`), cộng `--codes` cho lượt thử/re-crawl. Hồ sơ: [spec](../90-records/plans/2026-09-03-price-daily-etl/spec.md) · [plan](../90-records/plans/2026-09-03-price-daily-etl/plan.md) · [ledger](../90-records/plans/2026-09-03-price-daily-etl/ledger.md) · [số đo](../90-records/plans/2026-09-03-price-daily-etl/measurements.md).

**Ba điều lượt đo 18 lời gọi lật lại tài liệu** *(đã sửa ở tầng reference cùng ngày)*: `closePrice` là **giá thô lịch sử** (tỷ số với `closeValue` khớp cổ tức lát 2 tới 4 chữ số, 10/10 khớp tick BVSC trong ClickHouse) ⇒ `close_raw` điền được cho **toàn bộ lịch sử**, writer EOD của BVSC không còn là nguồn duy nhất; `status` trả lẫn `0`/`"Success"` trên cùng endpoint; `FromDate`/`ToDate` bị bỏ qua. Con số **1.974 lời gọi/ngày** của bản bàn giao cũ là số **trước** lượt dọn 442 mã huỷ niêm yết — thật là 1.523.

**Ba quyết định §4.8, mỗi cái kèm điều kiện đảo ngược trong spec §4:** tuần tự, không `core/http` + 8 luồng *(nhu cầu biến mất khi ngân sách ngày còn ~40 phút tuần tự; đảo khi `api` gọi FiinTrade hoặc backfill > 60 giờ)* · `close_raw = coalesce(cũ, closePrice)` điền một lần *(đảo khi `raw_close_mismatch` > 0 liên tiếp)* · 5 cột + `raw` giữ 99 trường, **không migration** *(đảo khi có tiêu thụ thật cần cột — điền từ `raw` bằng UPDATE, không crawl lại)*.

**Chạy thật vào kho production 2026-09-04:** AC2 3 mã 5 s · **AC3 1.523/1.523 mã, 91.165 dòng, 38 phút tuần tự (~40 request/phút), 0 retry, 0 tín hiệu chặn** — đồng thời là phép đo nhịp mà [quy ước §10.7](../10-sources/market/00-conventions.md) còn thiếu · AC4 lượt hai **`rows_changed = 0`** trên 91.165 dòng gửi lại · AC5 đột biến 3/100 mã `Code not valid` ⇒ guard từ chối đúng lý do, 0 dòng ghi, 1 bằng chứng · AC6 `price_factor` của DMX = 0,9548 trước ngày ex và 1 từ ngày ex, BID 3.142 dòng lùi tới 2014-01-24 · AC7 hai lượt `--max-minutes 3` nối nhau đúng con trỏ (`AAM` → *"còn 1519 mã"* → `ABC`, 4 + 6 mã không chồng). Review hai trục bắt **8 lỗi thật** (nặng nhất: cận ngày toàn cục của `raw_close_mismatches` sẽ quét cả bảng sau backfill) — sửa hết, kiểm bằng test. **456 test xanh.** Task `dlck-price` 15:40 (`-MustNotContain "--backfill"`) và `dlck-price-backfill` thứ 7 00:05 (`--stop-before-open`, giới hạn 72 giờ) **đã đăng ký thật (AC8)**, để `Disabled` cùng cả đội theo [4d].

🔴 **Sự cố lộ lỗi thật trong AC7:** máy **ngủ** 02:00 → 05:56, lời gọi treo qua giấc ngủ thành `httpx.ReadTimeout` và **lọt qua vòng retry**, giết cả lượt ở mã đầu — sửa `e7f80f6` (exception vận chuyển đi cùng đường với response xấu; `events_fetch`/`screener_fetch` cùng khuôn nhưng chỉ 9–52 lời gọi nên chưa gặp). Máy ngủ là **theo lịch** (chủ dự án đặt 02:00), app không chặn được ⇒ job được làm cho **sống qua giấc ngủ**: `pool_pre_ping` + ngân sách theo đồng hồ tường, cộng retry vận chuyển ([backend/README](../../backend/README.md)).

### Lát 4 — họ Snapshot ✅ XONG 2026-09-04

**`python -m etl snapshot`** — bốn kind `snapshot` · `valuation` · `ownership` · `dividend` vào `market.snapshot_daily`, kiến trúc hai lớp của [market-data-store §4.1b](../20-design/market-data-store.md): trigger từ lịch sự kiện + **quét sàn cuốn chiếu theo quota ngày** (24 · 70 · 70 · 70 = **234 lời gọi/ngày**, phủ trọn sàn sau 22 ngày với ba kind nhịp tháng và 64 ngày với `snapshot`). Hồ sơ: [spec](../90-records/plans/2026-09-04-snapshot-family-etl/spec.md) · [plan](../90-records/plans/2026-09-04-snapshot-family-etl/plan.md) · [ledger](../90-records/plans/2026-09-04-snapshot-family-etl/ledger.md) · [số đo](../90-records/plans/2026-09-04-snapshot-family-etl/measurements.md).

**Điểm khác mọi lát trước: kho chỉ nhận dòng KHI NỘI DUNG ĐỔI.** Không trường nào của họ này đổi theo ngày, nên ghi mỗi ngày một dòng là chép lại cùng một thứ 250 lần/năm. Phép so "có đổi không" tính hash trên **danh sách trắng theo kind** — bắt buộc, vì đo được rằng `rtd11` `rtd21` `rtd25` (snapshot) và `priceEarningRatio` `dividendYield` (dividend) **tính từ giá, đổi mỗi ngày**: hash trọn payload thì 100% mã "đổi" mỗi lượt và cả kiến trúc trigger mất nghĩa. Mọi lượt kiểm — đổi hay không — đều cập nhật `ops.snapshot_check`, và **`checked_at` chính là con trỏ** nên job không cần con trỏ riêng, lượt bị giết giữa chừng không mất chỗ.

**Chạy thật vào kho production 2026-09-04:** AC3 **234 target, 234 lời gọi, 0 retry, 0 hỏng, 0 tín hiệu chặn**, phần snapshot ~123 giây · AC4 lượt hai cùng ngày `unchanged 12`, `rows_written 0` · AC6 re-crawl giá **18.429/18.909 dòng đổi** ở lượt đầu và **0** ở lượt hai (hệ số RYG 0,8547 · TCH 0,9091 trước ngày ex, 1,0 từ ngày ex; DCF chỉ có `AGM` nên giữ 1,0 suốt) · AC7 ép hỏng ⇒ `failed`, 0 dòng ghi, sổ kiểm không nhúc nhích. **523 test xanh.** ⏳ **AC5 còn nợ.** Nửa *trôi trong ngày* đã đạt (243/246 mã đứng yên qua 2,5 giờ; 3 mã đổi là công bố sở hữu thật, lượt sau về 0 — và đó là **số đo lỗ của lịch đầu tiên**, vì `ownership` không có loại sự kiện nào bắn trigger). Nửa còn lại cần **một giá đóng cửa mới**, mà tính tới **16:42 ngày 04/09 nguồn vẫn chưa nạp** phiên hôm đó — đóng bằng một lệnh, xem [ledger §1d](../90-records/plans/2026-09-04-snapshot-family-etl/ledger.md). Merge trước là an toàn vì danh sách trắng sai sẽ làm chốt chặn (i) **từ chối cả lượt**, không ghi dòng nào.

🔴 **Bài học đắt nhất, và 523 test không bắt được:** lượt chạy thật đầu tiên ghi `watermark = 2026-09-22` — một ngày **ở tương lai** — vì spec định nghĩa mốc nước là `max(greatest(public_date, exright_date))` mà kho có 20 sự kiện `exright_date` tương lai. Trigger sẽ chết ba tuần, im lặng. Gốc rễ: **trộn hai đồng hồ khác nhau**. *"Sự kiện nào mới được công bố"* đo bằng `public_date`; *"ngày không hưởng quyền nào vừa đi qua"* đo bằng `exright_date` so với **hôm nay**. Tách xong thì re-crawl thành **không trạng thái** (cửa sổ 3 ngày), và phải kèm hai chốt nữa cũng chỉ lộ ra khi chạy thật: trần thời gian `RECRAWL_MAX_MINUTES = 20` *(mùa cổ tức có tuần 48 mã có ngày ex, mỗi mã là một lượt backfill trọn 12,5 năm)* và bộ lọc `event_type IN ('CashDividend','StockDividend','ShareIssuance')` *(6/10 sự kiện được chọn là `AGM` — chốt quyền dự đại hội, không đụng hệ số điều chỉnh)*.

⚠️ **`ingested_at` không dùng được làm mốc "sự kiện mới"** — `events_store` upsert kèm `DO UPDATE SET ingested_at = clock_timestamp()`, mà job events tải trọn 110.695 dòng mỗi lượt nên cả bảng được làm mới dấu thời gian mỗi ngày. Đã cân nhắc và loại; đừng đề xuất lại.

### Lát 5 — BCTC ✅ XONG 2026-09-04

**`python -m etl fundamentals`** — ba endpoint `GetBalanceSheet` · `GetIncomeStatement` · `GetCashFlow` vào `market.financial_statement` dạng dài **bỏ null** (ô null không thành dòng; "không áp dụng cho loại hình" suy lúc đọc từ hậu tố mã + `com_type_code`), `GetFinancialReports` vào `financial_report_file` khoá theo `source_id`, từ điển 729 mã vào `metric_dictionary` mỗi lượt. Trigger `Earning` (`public_date` > mốc nước, **loại cặp đã kiểm sau ngày công bố**, trần 300 issuer/lượt, mốc chỉ tiến tới ngày cắt − 1) + quét sàn nhịp 90 ngày quota 20/kind ≈ 80 lời gọi/ngày; **ghi khi đổi** với hash **trọn payload** — không cần danh sách trắng vì ba endpoint không có trường tính từ giá. Khi đổi: xoá trọn `(issuer, statement_type)` rồi chèn lại, mỗi lần đổi một dòng `staging.raw_payload` làm lịch sử điều chỉnh. Lượt điền đầu `--backfill --stop-before-open` như backfill giá, con trỏ là `checked_at`. Hồ sơ: [spec](../90-records/plans/2026-09-04-fundamentals-etl/spec.md) · [plan](../90-records/plans/2026-09-04-fundamentals-etl/plan.md) · [ledger](../90-records/plans/2026-09-04-fundamentals-etl/ledger.md) · [khảo sát BCTC](../90-records/surveys/2026-09-04-bctc-endpoints/README.md).

**Migration `0017`:** `financial_report_file.source_id` UNIQUE thay cho UNIQUE `source_url` (BID/BAB: hai `id` cùng một PDF — bản quý 3 và bản 9 tháng), `length_report IN (1,2,3,4,5,6,9)` cho `financial_report_file` **và** `corporate_event`; `financial_statement` **giữ** 1–5 (6/9 ở đây là `bad_shape`, job báo chứ không nạp); bảng `ops.fundamentals_check`.

**Chạy thật vào kho production 2026-09-04:** AC2 `--codes A32,BAB,AAS` 12 lời gọi, **41.123 dòng**, khớp từng dòng với bộ đếm độc lập `count_rows.py` (A32 3.645 · BAB 16.471 · AAS 20.845; PDF 8 / 106 / 48) · AC4 lượt hai `unchanged 12`, `rows_written 0` · AC6 ép 503 hàng loạt ⇒ guard từ chối 20/20, `failed`, 0 dòng · AC1 **591 passed, 2 skipped** *(warning duy nhất là `ResourceWarning` của test ingester, có từ trước)*. AC3 lượt điền trọn sàn **xong cùng tối, 3 lô 40 phút (20:09 → 21:55): 6.082 lời gọi, 0 retry, 0 tín hiệu chặn, nhịp 0,8–1,2 s/lời gọi** ⇒ **27.281.962 dòng** báo cáo (BS 14,0 · IS 6,8 · CF 6,4 triệu) cho đủ **1.523 mã**, 3,4 GB; **114.629** dòng PDF; 6.092 cặp trong sổ kiểm; payload thô 198 MB. Ước 21 triệu dòng của khảo sát thấp hơn thật ~30 % vì mẫu 3 mã không đủ kỳ quý sâu. AC7 lượt thường sau đó: 34 `Earning` ngày 04/09 đều bị loại đúng vì vừa kiểm sau ngày công bố ⇒ 0 target, `success`, mốc tiến `2026-09-04`. Chi tiết [ledger §3, §7](../90-records/plans/2026-09-04-fundamentals-etl/ledger.md). Review toàn nhánh bắt **1 Important + 9 Minor**, hai vòng sửa, re-review sạch.

🔴 **Hai bẫy chỉ lộ khi chạy thật, 591 test không bắt được:** (1) **`"quarterly": null`** — cùng mã A32, sáng nguồn trả `[]`, chiều trả `null`; `classify` ban đầu xếp `bad_shape` và lượt AC4 bỏ qua A32 3/3 báo cáo mà guard không nổ (12 target < `MIN_SAMPLE`). Cùng họ với `status` 0/"Success": **hai cách tuần tự hoá của cùng một nghĩa trên cùng endpoint** — đã ghi ở [05](../10-sources/market/05-fiin-financial-statements.md). (2) **Mốc nước nhảy qua issuer bị cắt trần trigger** (reviewer bắt): mốc = `max(public_date)` toàn cục trong khi trigger chỉ phục vụ 300 issuer ⇒ phần dư mất trigger vĩnh viễn. Cách sửa "mốc = ngày cắt − 1" **bị loại** vì ngày hạn nộp có hàng trăm mã cùng `public_date` ⇒ kẹt vĩnh viễn; sửa đúng là loại cặp đã kiểm sau ngày công bố bằng sổ kiểm, rồi mới cắt.

### Điểm vào cho lát 6 — giám sát hợp đồng, đọc trước khi bắt đầu

**Trạng thái bàn giao 2026-09-04 ~23:00:** `main` = lát 5 + fix mốc nước lát 4 + roadmap 14 lát · **593 test xanh, 2 skipped** (`pytest tests -q`) *(sáng 05/09 sau hai fix dưới: **596**)* · migration head `0017` · `financial_statement` **27,3 triệu dòng / 1.523 mã / 3,4 GB**, `financial_report_file` 114.629 dòng, mốc nước `2026-09-04` · `metric_dictionary` 729 dòng · **không đăng ký task Scheduler** (lịch thuộc lát 13: `fundamentals` chạy **sau `events` 18:10 và sau `snapshot`**).

| Cần biết trước | Ở đâu |
|---|---|
| Lỗi mốc nước nhảy qua issuer bị cắt trần trigger (A1 của review lát 5) **đã sửa cho cả lát 4** tối 2026-09-04 (`snapshot_store.plan_due` / `trigger_cut`, cùng công thức lát 5) — không còn nợ trước khi bật lịch | [ledger lát 5 §2](../90-records/plans/2026-09-04-fundamentals-etl/ledger.md) · [backend/README](../../backend/README.md) |
| Bảy phép kiểm đơn vị của từ điển (đẳng thức kế toán, nhất quán thang) là đầu vào cho bộ giám sát — nhưng **mới ở dạng văn xuôi**, phải viết lại thành code (xem bảng dưới); `metric_dictionary` nay có 729 dòng trong kho | [market-data-store §7.1](../20-design/market-data-store.md) · [field-dictionary.json](../10-sources/market/field-dictionary.json) |
| Lịch sử điều chỉnh hồi tố nằm ở `staging.raw_payload` (`source = 'fundamentals'`, một dòng mỗi lần đổi, `meta.hash`) — thước đo tần suất restatement, giả định §2.2.1 của spec lát 5 chưa kiểm | [spec lát 5 §4.1](../90-records/plans/2026-09-04-fundamentals-etl/spec.md) |
| Khuôn `Fetcher`/`_UNIVERSE` đã nhân bản hai lần (`snapshot_*`, `fundamentals_*`) — lát 6 dùng chung script cho 5 lát nên là lúc cân nhắc trích chung, không phải trước | ledger lát 5 §1 (Task 2) |
| Chốt guard (i) tính trên cả lượt: mùa báo cáo, quét sàn rơi vào mã vừa có kỳ mới mà lịch sót sẽ chạm 20 % — vận hành bình thường, chạy tay `--kinds` để đi tiếp, ghi số | [backend/README](../../backend/README.md) |

**Trạng thái kho, lịch và nợ — đo 2026-09-04 ~23:00, hai audit độc lập + tự kiểm:**

| Mục | Sự thật |
|---|---|
| 🔴 **Ba bảng của bộ giám sát ĐÃ TỒN TẠI** — `ops.contract_snapshot`, `ops.series_health`, `ops.source_build` từ migration `0008` (2026-08-25), **0 dòng**, có `test_s08_staging_ops.py`. Lát 6 viết script ghi vào chúng, **không** thiết kế lại migration; đối chiếu cột thật trong `0008` với §7.1 trước khi tin văn bản | [`0008_staging_ops.py`](../../database/migrations/versions/0008_staging_ops.py) dòng 52 · 64 · 80 |
| **Bảy phép kiểm đơn vị của từ điển là VĂN XUÔI** ghi lại một lượt chạy tay 2026-08-14 (6 đẳng thức kế toán + 1 kiểm nhất quán thang), chưa có hàm nào — lát 6 phải viết lại thành code, dùng `metric_dictionary` (729 dòng trong kho) làm đầu vào | [Phụ lục A](../10-sources/market/appendix-A-field-codes.md) mục "Xác thực đơn vị" |
| ✅ **Nợ `status == "Success"` ở `screener_fetch`/`events_fetch` ĐÃ TRẢ sáng 2026-09-05** (`7c3b481`, TDD, hai test `status_zero`): hai `_valid` nay nhận `status ∈ {0, "Success"}` đúng quy ước §6.1. Cùng buổi vá thêm **lỗi đồng hồ**: `recrawl_codes` lấy `current_date` theo session Postgres (UTC) trong khi test và nghiệp vụ tính ngày VN — hai test `test_e29` đỏ mỗi ngày từ 00:00 đến 07:00 giờ VN (đo 05:38). Nay mốc là ngày VN tính ở Python, bơm được (`today=`) — `3a57c51`. **Bài học thứ tư:** `now()`/`current_date` phía DB là giờ UTC của session, KHÔNG phải ngày VN; mọi phép so "hôm nay" trong SQL phải qua `AT TIME ZONE 'Asia/Ho_Chi_Minh'` hoặc nhận ngày từ Python | [quy ước §6.1](../10-sources/market/00-conventions.md) · `backend/etl/snapshot_store.py` `recrawl_codes` |
| Trạng thái kho: `ops.etl_run` 74 lượt · `staging.raw_payload` 6.109 (6.092 của `fundamentals`) · `ops.snapshot_check` 292 (tối đa 6.092) · `ops.fundamentals_check` 6.092 · `metric_dictionary` 729 · `financial_statement` 27.281.962 · `data_domain_state`: `market.fundamentals` = 2026-09-04, `market.snapshot` = 2026-09-03, `market.events` = 2026-09-04 | truy vấn dưới `ETL_DATABASE_URL` |
| Lịch: **11 task `Disabled`** theo [4d], trừ `dlck-price-backfill` `Ready` (bật từ thứ 7 05/09). `snapshot` và `fundamentals` chưa có task — lịch thuộc lát 13 | `Get-ScheduledTask dlck-*` |
| Hợp đồng từng job mà bộ giám sát phải bắt: `screener` — `status == "Success"` (nợ trên), guard `MIN_PRICED_RATIO 0.2 · DROP 0.02 · UNMAPPED 0.02` · `events` — cùng nợ status, guard `DROP 0.02 · DUP 0.005 · MAX_NEW_ISSUERS 20` + "sáu họ cùng rỗng" · `price` — `status ∈ {0,"Success"}`, guard `MISSING 0.02 · DROP 0.02 · ngày tương lai · ngày lùi mốc` · `snapshot` — `status ∈ {0,"Success"}` + khoá gốc theo kind, guard `MIN_SAMPLE 20 · đổi sàn 20 % · hỏng 20 % · sai hình dạng 5 %` · `fundamentals` — như snapshot + `null` = rỗng + `empty 5 %`. Bằng chứng từ chối luôn ở `staging.raw_payload`, số đếm ở `ops.etl_run.stats` | `backend/etl/*_fetch.py` (`classify`/`_valid`), `backend/etl/*_guard.py` |
| Mẫu 51 mã của Phụ lục B (đo 2026-08-10) **chưa được rà** với 438 mã bị đánh dấu huỷ niêm yết 2026-09-03 — nếu dùng làm mẫu giám sát độ phủ, lọc trước, không thì "độ phủ tụt" trên mã đã rời sàn là báo động giả | [Phụ lục B](../10-sources/market/appendix-B-coverage.md) · luật huỷ niêm yết 2026-08-28 |
| Nợ nhỏ còn treo: AC5 lát 4 chạy sáng 05/09 (`etl snapshot --codes AAA,ABB,AAM,AAT`, nguồn làm mới qua đêm) · bảy Minor hoãn của lát 5 (ledger §2) · câu hỏi "nguồn nạp sau lúc fetch cùng ngày công bố" (ledger §7) | [ledger lát 4 §1d](../90-records/plans/2026-09-04-snapshot-family-etl/ledger.md) · [ledger lát 5](../90-records/plans/2026-09-04-fundamentals-etl/ledger.md) |

**Ba bài học lát 5, áp thẳng được:**

1. **Cùng một endpoint có thể tuần tự hoá cùng một nghĩa hai cách** (`status` 0/"Success", `quarterly` `[]`/`null`). Mọi kiểm hình dạng phải viết theo *nghĩa* ("không có kỳ quý"), không theo *kiểu* của một mẫu đã lưu; và lượt `--codes` nhỏ hơn `MIN_SAMPLE` không được guard bảo vệ — đọc `stats.tally` của nó bằng mắt.
2. **Mốc nước theo ngày + trần theo số lượng = kẹt hoặc nhảy cóc.** Muốn "đã phục vụ" thì ghi theo từng đơn vị (sổ kiểm), đừng suy từ một mốc toàn cục.
3. **Test dùng ngày hardcode cạnh `now()` là bom hẹn giờ** — reviewer bắt được ba test sẽ đỏ sau 7–29 ngày. Mọi ngày trong test lấy từ `date.today()` (§4.4.4).

### ~~Điểm vào cho lát 5~~ — ĐÃ DÙNG XONG 2026-09-04, giữ làm ngữ cảnh

*(Mục này viết ở cuối lát 4. Lát 5 đã xong — trạng thái hiện tại nằm ở hai mục trên, không phải ở đây.)*


**Trạng thái bàn giao 2026-09-04:** nhánh `feat/snapshot-family-etl` **đã merge `main`** (`27b3171`) · **523 test xanh** · migration head `0016` · `snapshot_daily` 246 dòng ngày 2026-09-04 · `ops.snapshot_check` 246 dòng · **không đăng ký task Scheduler** (lịch thuộc lát 13 — tên lúc viết mục này là "lát 7") · AC5 còn nợ tới 05/09 *(kiểm lại 17:10 ngày 04/09: nguồn vẫn mang giá đóng cửa 03/09 — AAA `rtd11 ÷ outstandingShare` = 7.090, chưa phải 7.130 — nên vẫn chưa đóng được)*.

| Cần biết trước | Ở đâu |
|---|---|
| Tín hiệu kích hoạt đã có sẵn: `corporate_event` loại `Earning` kèm `year_report`/`length_report` — lát 4 đã dùng đúng đường này cho kind `snapshot` | [`snapshot_store.due_list`](../../backend/etl/snapshot_store.py) |
| **Khuôn job đã ổn định qua 3 lát**: `fetch` (classify 3 nhánh, retry, giãn cách) → `normalize` (thuần) → `guard` (ngưỡng + **mẫu tối thiểu**) → `store` → `job`. Nhân bản từ `snapshot_*`, đừng chép từ lát 1 | `backend/etl/snapshot_*.py` |
| **Ghi khi đổi + sổ kiểm** là mẫu dùng lại được cho BCTC (BCTC cũng chỉ đổi khi có kỳ báo cáo mới) — cân nhắc trước khi mặc định ghi mọi lượt | [spec lát 4 §4.1](../90-records/plans/2026-09-04-snapshot-family-etl/spec.md) |
| **556** mã chỉ tiêu BCTC trong từ điển, kèm đơn vị. ⚠️ Con số **557** ghi trong khảo sát 2026-09-04 là số **khoá phân biệt** trên ba endpoint — gồm **8 khoá không phải mã chỉ tiêu** (`organCode` · `ebit` · `ebitDa` · `operating` · `otherAssetBank` · `otherAssetNonBank` · `otherLiabilties` · `rtq29`) và **549** mã từ điển; 7 mã từ điển chưa gặp trên mẫu 3 mã. **Không phải đính chính của 556** — hai số đếm hai thứ khác nhau *(đối chiếu lại 2026-09-04 chiều, [khảo sát §6](../90-records/surveys/2026-09-04-bctc-endpoints/README.md))* | [Phụ lục A](../10-sources/market/appendix-A-field-codes.md) · [field-dictionary.json](../10-sources/market/field-dictionary.json) |
| `snapshot.quarterly[]` / `yearly[]` **đã nằm sẵn trong payload** `snapshot_daily` (mã `bsa*` `isa*` `cfa*`) — cố ý không bóc ở lát 4. **Đã đóng 2026-09-04:** khối đó chỉ 25 mã / 9 kỳ so với 549 mã / 43 kỳ ở endpoint riêng ⇒ lát 5 **bắt buộc** gọi ba endpoint BCTC | [khảo sát BCTC câu 1](../90-records/surveys/2026-09-04-bctc-endpoints/README.md) |
| **`financial_statement` KHÔNG cần nới CHECK `length_report`** — ba endpoint số liệu chỉ phát `quarterReport` 1–4 (quý) và 5 (năm) trên 5 mã đo (BAB · AAS · VNM · HPG · A32, 0 dòng ngoài dải). Giá trị `6`/`9` chỉ có ở `getFinancialReports` ⇒ nới CHECK trên `financial_report_file` và `corporate_event` là đủ | [khảo sát §6](../90-records/surveys/2026-09-04-bctc-endpoints/README.md) · [market-data-store §5.4](../20-design/market-data-store.md) |
| **Khoá viết hoa lẫn trong response:** `GetBalanceSheet` trả `bsI141` và `bsS134` (4/4 mã, 2026-09-04) trong khi từ điển và cột `metric_code` là chữ thường ⇒ **hạ chữ thường khi nạp**, nếu không hai mã này rơi khỏi từ điển | [05-fiin-financial-statements](../10-sources/market/05-fiin-financial-statements.md) |

**Bốn bài học lát 4, áp thẳng được:**

1. **Chạy thật một lượt trước khi tin bất cứ điều gì.** Ba lỗi nặng nhất của lát này — mốc nước tương lai, re-crawl không trần, re-crawl lấy nhầm `AGM` — **không lỗi nào bị 523 test bắt được**. Chúng lộ ra ở lượt `--codes` đầu tiên và ở việc đọc `stats` của lượt đó.
2. **Tài liệu thiết kế có thể lệch migration.** SQL viết theo `market-data-store.md` §5.6 tham chiếu cột `organ_code` không tồn tại. Lược đồ thật nằm ở migration; §5.6 đã đồng bộ 2026-09-04.
3. **Test đụng CSDL dùng chung phải tự dập nền.** 9 test xanh khi chạy riêng, đỏ khi chạy cả bộ, vì chúng assert trên truy vấn **toàn cục** trong khi bộ test khác commit dữ liệu thật nằm lại. Helper dập nền + lọc theo mã của chính test.
4. **Ngưỡng phần trăm phải có mẫu tối thiểu.** Chốt chặn "tỷ lệ đổi > 20%" tự vi phạm ở lượt `--codes` 3 mã và ở lượt cold start nếu không có `MIN_SAMPLE`.

### ~~Điểm vào cho lát 4~~ — ĐÃ DÙNG XONG 2026-09-04, giữ làm ngữ cảnh

*(Mục này viết ở cuối lát 3. Lát 4 đã xong — trạng thái hiện tại nằm ở hai mục trên, không phải ở đây.)*

**Trạng thái bàn giao 2026-09-04:** nhánh `feat/price-daily-etl` merge `main` · **456 test xanh** · migration head `0015` · **11 task** đã đăng ký thật, đều `Disabled` · `price_daily` 113.427 dòng: 60 phiên/mã cho cả 1.523 mã + backfill đã đi tới con trỏ `ABC` (kiểm `ops.etl_run` job `market.price_backfill`, `stats.cursor`).

| Cần biết trước | Ở đâu |
|---|---|
| Thiết kế hai lớp trigger + quét sàn, nhịp quét theo kind, vì sao Snapshot không chạy hằng ngày | [market-data-store §4.1b](../20-design/market-data-store.md) |
| Tín hiệu đã có sẵn trong kho: `corporate_event` (Earning · ShareIssuance · Cash/StockDividend, `exright_date`), `screener_daily` (máy dò sở hữu) | lát 2 · lát 1 |
| **Re-crawl giá theo sự kiện quyền đã có đường sẵn:** `python -m etl price --backfill --codes A,B` tải lại trọn lịch sử mã đó (chuỗi `close_adj` đổi toàn bộ sau mỗi sự kiện quyền; `close_raw` giữ nguyên) — lát 4 chỉ cần chọn mã từ `exright_date` và gọi | [spec lát 3 §5.5e](../90-records/plans/2026-09-03-price-daily-etl/spec.md) |
| Backfill lịch sử giá **còn dở** (con trỏ ở `ACC`, 17/1.523 mã + BID + DMX xong): chạy bằng task **`dlck-price-backfill`** (thứ 7 00:05, hoặc `Start-ScheduledTask` tay buổi tối; `--stop-before-open` tự dừng trước 08:45 ngày giao dịch kế; ~20 giờ đủ trọn vòng) — task **đã đăng ký thật** 2026-09-04 (AC8); trạng thái bật/tắt do **[4d] ở §2** sở hữu — chốt 2026-09-04: task này bật từ thứ 7 05/09, ngoại lệ duy nhất của cả đội. Lệnh: `Enable-ScheduledTask dlck-price-backfill; Start-ScheduledTask dlck-price-backfill`; máy ngủ giữa chừng cũng không hỏng | [backend/README](../../backend/README.md) |
| ETF (6/31 mã có dữ liệu, gọi theo ticker, `iNav`) cố ý ngoài lát 3 — thêm khi thiết kế chỉ báo dòng tiền ETF | [spec lát 3 §3.2](../90-records/plans/2026-09-03-price-daily-etl/spec.md) |

**Bài học lát 3, áp thẳng được:**

1. **Đo nguồn trước khi tin thiết kế — kể cả thiết kế đã qua 4 vòng review.** Step-03 chốt *"backfill để `close_raw` NULL vì quá khứ không có giá thô ở nguồn nào"*; một lượt đo 18 lời gọi cộng hai nguồn đối chứng **đã có sẵn trong kho** (cổ tức lát 2, tick ClickHouse) lật ngược điều đó. Tài sản của các lát trước là **thước đo** cho lát sau.
2. **`status` không được so với một giá trị.** Cùng endpoint trả `0` và `"Success"` tuỳ máy chủ/cache sau cân bằng tải; lát 1–2 kiểm `== "Success"` chỉ may mà chưa gặp. Công thức đúng nằm sẵn ở [quy ước §6.1](../10-sources/market/00-conventions.md) từ 2026-08-15 — đọc lại quy ước, đừng chép code lát trước.
3. **Exception vận chuyển phải đi cùng đường với response xấu.** Ba fetcher cùng khuôn đều để `httpx` ném thẳng ra ngoài; chỉ lát có 1.523 lời gọi mới trả giá. `events_fetch`/`screener_fetch` **đã vá cùng ngày** (`356cdc9`, mỗi cái hai test đỏ→xanh) — lát sau nhân bản từ bản đã vá.
4. **Hạ tầng dev chết giữa chừng không phải lỗi code, và có ba dạng:** reboot không lên Docker (03/09 sáng, 03/09 đêm), và **máy ngủ** (04/09 02:00). Trước khi đặt giả thuyết về code: `docker ps`, cổng, và System event 42/107. Hai việc *"Start Docker Desktop when you sign in"* và *"tắt sleep khi chạy job đêm"* nay đã đắt ba lần.

## 4. Việc đã có đáp án, chỉ cần áp dụng

Bốn mục đang nằm trong danh sách **"Còn để ngỏ"** của pipeline tin nhưng thực ra đã được trả lời ở khối tài liệu khác:

| Đang ghi là để ngỏ | Đáp án đã có |
|---|---|
| Danh sách ~1.600 mã niêm yết | `getListOrganization` cho danh bạ doanh nghiệp (**gồm cả mã đã huỷ niêm yết**); con số **1.974 cổ phiếu** là đếm `StockType=2` từ **`getAllQuotes` của BVSC**, đo 2026-08-15 — không phải số của `getListOrganization`. Số ~1.600 là ước lượng sai. Lọc mã huỷ niêm yết bằng `getAllQuotes` — *và 1.974 vẫn gồm 442 mã đã rời sàn: sau lượt dọn theo luật huỷ niêm yết (2026-09-03) tập `listed` thật là **1.523**, đó là số lời gọi/ngày của lát giá* |
| Bảng tên thương mại → mã | `organName` + `organShortName` trong cùng endpoint |
| Khung ngành để lọc tin | `getAllIcbIndustry` — cây ICB 4 cấp |
| Khung ngành cho skill | Cùng nguồn trên, nối theo hợp đồng ở [§3.2](architecture.md) |
| Bảng ánh xạ mã chỉ tiêu BCTC | **729 mã đã giải mã** từ bundle JS FiinTrade — xem [Phụ lục A §A.5](../10-sources/market/appendix-A-field-codes.md) |
| Đơn vị của các mã chỉ tiêu | **727/729 mã có `don_vi_du_lieu`**, 392 xác thực bằng đẳng thức kế toán |
| Lấy trường nào từ nguồn nào | [chọn trường cho ETL thị trường](../20-design/market-field-selection.md) — Screener 80/193 (ước lượng 2026-08-14; đếm 2026-09-03: **75/193** — 66 khoá đặt tên từ response thật, trừ 4 nhãn xếp hạng và 2 dòng KQKD trùng BCTC), Snapshot **18/54** ở ngân hàng và **15/54** ở phi ngân hàng *(`rtq44` `rtq137` `rqq41` chỉ ngân hàng mới có — đo 9/9 mã 2026-09-04)*, giá từ BVSC |

## 5. Việc còn thật sự để ngỏ

| Việc | Ghi chú | Chốt bằng cách nào |
|---|---|---|
| ~~**Luật bỏ boilerplate cho từng nguồn**~~ | ✅ **Đã khảo sát 2026-08-15** — luật riêng cho cả 8 nguồn báo nằm ở [cấu trúc trang bài](../10-sources/news/article-structure.md) (33 bài, chạy thật trên trang đã tải). Còn ngỏ: dạng bài longform/video/bài cũ chưa phủ | Đã làm — đúng bằng một vòng soi tương tự vòng soi feed |
| 🔴 **Nguồn Screener trả gì sau 15:00 của một NGÀY LỄ?** | Guard *"có phiên"* của `etl screener` dựa vào `closePrice > 0`. Đã đo 2026-09-03 ba mức trong cùng ngày: **0 %** trước mở cửa · **53,8 %** giữa phiên · **100 %** sau phiên ⇒ ngưỡng 20 % có biên rộng. **Nhưng chưa ai đo ngày lễ.** Nếu hôm đó nguồn trả **giá phiên trước** thay vì 0 thì guard **cho qua** và ghi ~1.545 dòng ma cho một ngày không giao dịch — và Screener không có backfill để sửa *(spec §2.2.1, [ledger AC5](../90-records/plans/2026-09-03-screener-daily-etl/ledger.md))* | **Lượt chạy ngày lễ đầu tiên phải có người soi.** Task đang `Disabled` nên chưa tự chạy — khi bật lại theo [4d], ngày lễ đầu tiên chạy tay và đọc `stats.counts.priced`. Nếu > 0 ⇒ **đổi tín hiệu** (dùng lịch nghỉ, hoặc đối chiếu `tradingDate` với ngày giao dịch gần nhất trong kho), **không phải nâng ngưỡng** |
| **Chọn mô hình embedding** | 🟡 **Kích thước + kiểu lưu chốt 2026-08-26: `halfvec(768)`** — ràng buộc từ VPS 50 GB, chênh 4× dung lượng so với 1536 chiều float32 ([news-pipeline §9.5](../20-design/news-pipeline.md)). Còn ngỏ: mô hình cụ thể | Chọn bằng cách **đo khả năng tách tin trùng** trên tin đã crawl, không theo tiếng tăm. Đổi số chiều = embed lại toàn kho |
| **Ngưỡng `confidence`** phân loại | Dưới bao nhiêu thì vào hàng chờ rà tay | Sau vài tuần chạy thật |
| **Trần 3.000 hay 4.000 ký tự** | | Đối chiếu `content_chars` với các ca phân loại sai |
| **Tách từ tiếng Việt** | Chỉ làm nếu có bằng chứng `simple` + `unaccent` không đủ | |
| ~~**Câu treo cuối của dự án skill**~~ | ✅ **Đã quyết 2026-08-14: giữ nguyên tên "ngân hàng"** trong luận điểm *ngành báo hiệu* — là cơ chế, không phải danh sách ngành cứng. Bảng rà `CAN-SUA.md` hết việc và đã xoá | |
| **Đoạn giới hạn phạm vi vào system prompt** | Skill không tự gác cổng được — xem [§4](architecture.md) | Làm khi dựng backend |
| ~~**Đăng ký lại 7 task với `-LogonType S4U`**~~ | ✅ **XONG 2026-08-28** — cả 7 task nay `LogonType=S4U`, `RunLevel=Limited`; nghiệm thu bằng soi `Principal` từng task. Cửa sổ `cmd` (rủi ro bấm nhầm X giết phiên ghi tick) **đã hết**. ⚠️ *"Chạy cả khi không đăng nhập"* chỉ đúng một nửa — Docker Desktop sống trong session người dùng nên log off là hai kho tắt theo: [service-topology §5](../20-design/service-topology.md) | `scripts/register-tasks.ps1` nay nhận `-LogonType` + tự kiểm `Assert-TaskLogonType`. Hai bẫy đã trả giá và ghi lại: script cần **`pwsh`** (UTF-8 không BOM, 5.1 parse hỏng) và `-UserId` phải **qualified `DOMAIN\user`** (tên trần fail cả S4U lẫn Interactive) |
| ~~**Luật huỷ niêm yết cho mã vắng danh bạ**~~ | ✅ **CÀI XONG 2026-08-28, nghiệm thu trên DB thật** — migration `0014` (cột dấu `security.directory_absent_since`), `apply` đóng/gỡ dấu, `plan_delist` đọc dấu của lượt trước, ngưỡng `DIRECTORY_ABSENT_DAYS = 3`. Hai lượt job liên tiếp exit 0: đóng dấu **438** rồi **0**; **A=438 · B=0 · C=0 · D=4**. Cơ chế: [market-data-store §4.4](../20-design/market-data-store.md) | ✅ **Lượt dọn đã chạy 2026-09-03.** Ngưỡng thoả lúc 31/08 19:41 nên job báo đỏ đúng thiết kế ba lượt liên tiếp (01/09, 02/09, 03/09 — chốt chặn 1% từ chối đúng 22,3%, `failed`, không ghi gì). Dọn bằng một lượt chạy tay có người nhìn: `uv run python -m etl refdata --accept-drop` — `ops.etl_run` **run_id 62**, `accept_drop: true`, lật **439** mã sang `delisted` *(438 đo lúc 31/08 19:41; chênh 1 mã, chưa rà nguyên nhân)*. `directory_absent_since` nay bằng **0** trên toàn kho — danh bạ hết đứng ở trạng thái 31/08 |

### 5.1 ✅ Realtime phái sinh — ĐÃ ĐO 2026-08-26 (phiên chiều)

> **Kết quả** *([hồ sơ phiên đo](../90-records/surveys/2026-08-26-bvsc-realtime-session/README.md))*: **phái sinh KHÔNG có kênh riêng** — tick phái sinh đi chung ba topic `i`/`o10`/`t` với cổ phiếu, phân biệt bằng `EX = "XHNF"`, cấu trúc trường **giống hệt** cổ phiếu, **không có `openInterest`** trong luồng realtime (muốn OI phải lấy từ `/datafeed/instruments`). 15 topic còn lại của bảng hằng số **không đẩy frame nào** — kể cả `pth`. Mã `41I1G9000` (VN30F1M) đẩy 24.162 lệnh khớp trong một phiên chiều, nhiều hơn mọi mã cổ phiếu.
>
> **Việc còn lại (không chặn lát cắt hiện tại):** mã phái sinh **không có trong `/quotes`** nên danh mục runtime chưa đăng ký chúng — mở rộng danh mục là một quyết định phạm vi riêng, cần cùng lúc chốt lược đồ (dùng chung bảng `trade`/`quote`/`snapshot_delta` hay tách).
>
> *(Nguyên văn phần chưa đo, giữ làm ngữ cảnh:)*

**Việc gấp nhất còn lại của khối nguồn.** Đợt khảo sát chạy ngày **thứ Bảy 2026-08-15**, thị trường đóng (`tradingSessionID: "CLOSED"`), nên **không phép kiểm nào ngoài giờ có giá trị**: server BVSC trả ack `statusCode: 200` cho **mọi** chuỗi topic rồi im lặng — đăng ký thành công không chứng minh topic hợp lệ *(đã ghi ở [`11-bvsc-realtime.md` §1.4](../10-sources/market/11-bvsc-realtime.md))*.

**Đã biết chắc, rút từ mã nguồn bảng giá BVSC** *(đọc 2026-08-15)*:

| Mục | Giá trị |
|---|---|
| Máy chủ | `https://wss.bvsc.com.vn`, đường dẫn `/market/socket.io`, thư viện **sails.io**, `transports: ["websocket"]` |
| Bảng hằng số topic | 20 topic dùng chung toàn bảng giá — `i` · `i_ol` · `o10` · `o_ol10` · `o` · `o_ol` · `t` · `t_ol` · `tm` · `e` · `e_ol` · `im` · `e_im` · `om` · `idx` · `pth` · `ptm` · `p` · `u` · `d` |
| Hạ tầng | Bảng phái sinh render từ `psStocks` và **ăn cùng module socket** với bảng cổ phiếu ⇒ **dùng chung hạ tầng realtime, không phải kênh riêng** |

**Chưa biết:** topic nào mang tick phái sinh · định dạng frame · tần suất · có `openInterest` realtime không.

**Quy trình đo — khung 08:45–15:00** *(⚠️ phái sinh mở sớm hơn cổ phiếu 15 phút; sớm nhất là phiên kế tiếp sau 2026-08-15)*:

1. Nối `wss.bvsc.com.vn/market/socket.io`.
2. Đăng ký **toàn bộ 20 topic** với 2–3 mã phái sinh — `41I1G8000` là **mã duy nhất có thanh khoản thật** *(đo 2026-08-15)*.
3. Ghi frame trong ~5 phút, xem **topic nào thật sự đẩy dữ liệu** — đây là phép kiểm duy nhất có giá trị.
4. Đối chiếu giá trong frame với `/datafeed/instruments` gọi cùng lúc.

**Ảnh hưởng thiết kế:** cho tới khi đo xong, lược đồ và Ingester **không được giả định** là có tick phái sinh realtime.

### 5.2 Việc treo khác phát sinh từ khảo sát 2026-08-15

| Việc | Vì sao ảnh hưởng thiết kế | Chốt bằng cách nào |
|---|---|---|
| ✅ **ĐÃ XONG 2026-08-25 — Phiên thiết kế + THỰC THI schema Postgres**: spec 7 bước qua 4 vòng review + 10 migration Alembic + 37 test seam trên Postgres thật, merge `main` — hồ sơ: [plans/2026-08-25-postgres-data-schema/](../90-records/plans/2026-08-25-postgres-data-schema/), cách chạy: [database/README.md](../../database/README.md). Việc kế tiếp chuyển sang: cập nhật `market-data-store` theo ClickHouse (dòng dưới) + plan lát ETL đầu *(nguyên văn cũ, giữ làm ngữ cảnh:)* | Đứng **trước** `first-rest-slice`: "hứng dữ liệu về lưu lung tung thì chết". Gộp bốn việc: (1) **consolidation** schema REST từ [kho dữ liệu §5](../20-design/market-data-store.md) *(bỏ phần tick/`bar_1m`/Timescale — chuyển ClickHouse)*; (2) **quyết định chống khoá-nhà-cung-cấp** — tách `security_id` khỏi `organ_code`, thêm `source`+`canonical_code`, bảng `data_domain_state` ([§9.3/§9.6](../20-design/market-data-store.md), *rẻ nếu làm ngay, đắt nếu retrofit*); (3) đối soát **ClickHouse split**; (4) **tách instance data/user — ĐÃ CHỐT D** *([service-topology §4](../20-design/service-topology.md))*, chỉ cần đưa vào DDL/migration + hai connection string. Cùng chốt Alembic vs SQL thuần | Một phiên thiết kế riêng ở **session mới** (làm mới context), brainstorm→spec vào `docs/90-records/plans/` |
| ✅ **ĐÃ XONG 2026-08-26 — Cập nhật `market-data-store.md` theo ClickHouse**: spec một file (qua 4 vòng review + 15 phép kiểm trên ClickHouse 26.3.22.7 thật, §12 spec) + plan 8 task + 2 migration SQL thuần + 29 test seam trên ClickHouse thật + `market-data-store.md`/`service-topology.md`/`database/README.md` đã cập nhật theo checklist §13 của spec — hồ sơ: [plans/2026-08-25-clickhouse-realtime-store/](../90-records/plans/2026-08-25-clickhouse-realtime-store/), cách chạy: [database/README.md](../../database/README.md) *(nguyên văn cũ, giữ làm ngữ cảnh:)* | Chốt 2026-08-24 ([ADR 0007](decisions/0007-monorepo-layout-and-stack.md)): kho realtime đổi TimescaleDB → ClickHouse để lưu tick thô + sổ lệnh. Thiết kế đã duyệt chưa phản ánh: DDL ClickHouse, materialized view sinh nến, buffer ghi batch cho Ingester; Redis giữ nguyên vai trò pub/sub + leader lock | Một phiên thiết kế riêng, làm **trước khi dựng hạ tầng [1]** |
| 🔴 **Lược đồ giá dầu phải có cột phân biệt loại giá** | Quyết định chủ dự án 2026-08-15: **lưu cả hai** — giao ngay *(FRED `DCOILWTICO`, trễ 4 ngày)* và tương lai *(WiChart `dau_wti`, T−1)*. Chênh cơ sở đo được **~+2,0% ổn định**. Trộn chung một cột "giá dầu" thì lịch sử có **bậc nhảy 2% tại điểm đổi nguồn** | Thêm cột loại giá vào lược đồ trước khi nạp dòng đầu tiên |
| ~~**Crawl OMO phải chạy từ ngày đầu**~~ | ✅ **Đã cài và chạy thật từ 2026-08-26** (4 mốc/ngày) — [`macro/sbv-omo.md`](../10-sources/macro/sbv-omo.md). ⏸️ Nhưng **đang tắt từ 2026-08-28**: trạng thái và điều kiện bật lại do **[4d] ở §2** sở hữu, không chép lại ở đây | — |
| **Kho FRED phải UPSERT, không append-only** | FRED **vá hồi tố**: `PAYEMS` tháng 5/2026 có **3 giá trị** khác nhau. Append-only sẽ giữ số đã bị thay thế | Làm mới cửa sổ 24 tháng mỗi lần chạy — [`global/fred.md` §4](../10-sources/global/fred.md) |
| ~~**Khoá EIA miễn phí**~~ — ⚪ **đã cân nhắc và BỎ QUA** *(chủ dự án quyết 2026-08-15)* | EIA chỉ chuyên năng lượng: trong 15 series FRED đang dùng, **đúng 1 series là của EIA** (`DCOILWTICO`); 14 series còn lại của FRB · BLS · BEA · Fed NY · CBOE. Nên EIA **không thay được FRED**, chỉ bớt một mắt xích cho dầu khí. Đăng ký lại khi nào thật sự cần tồn kho/sản lượng dầu khí Mỹ — mất 5 phút | — |
| ~~**`.gitignore` chưa bao giờ được commit**~~ | ✅ **Đã xong từ 2026-08-15** — commit `d74bbc9` (16:05 cùng ngày, tức mục này đã sai ngay lúc được viết ra và mang cái sai đó 11 ngày). Kiểm lại 2026-08-26: `git check-ignore -v .env` → `.gitignore:2`, `git ls-files .env` → rỗng ⇒ `.env` được che và **không** nằm trong lịch sử git | — |
| **Rà lại các cờ `lệch x%` khác trong `wichart.md`** | Cờ `dau_wti` sai vì chấm một điểm và so nhầm chuẩn. Cờ `vang_the_gioi` đã kiểm trên 712 ngày và **đúng** ⇒ **không được suy đoán đồng loạt cả bộ cờ sai** | So chuỗi, không chấm điểm; nhớ parse `Asia/Ho_Chi_Minh` |
| **Đồng, thép, than, bạc** | Chưa tìm được nguồn ngày miễn phí có mốc chuẩn để đối chiếu | Chưa chặn việc gì |
| **TPCP phái sinh "chưa từng giao dịch"** | Kết luận mới dựa trên **1 phiên** | Đo thêm vài phiên trước khi đưa vào lược đồ |

## 6. Sáu bẫy sẽ cắn ngay ngày đầu cài đặt

Ghi lại ở đây vì chúng nằm rải trong ba file khác nhau và đều đã gặp thật:

1. **`organCode ≠ ticker` ở 41% doanh nghiệp** — gọi bằng ticker trả `HTTP 200` với dữ liệu rỗng, không báo lỗi gì.
2. **Timestamp WiChart phải parse bằng `Asia/Ho_Chi_Minh`**, không phải UTC — parse sai tạo ảo giác lệch nhãn 1 tháng trên toàn bộ chuỗi tháng.
3. **Nhãn `unit` của WiChart sai ở 15 series**, lệch 1000 lần, **rải rác ngẫu nhiên không theo quy luật** — phải dùng bảng hệ số đã hardcode.
4. **Nhãn `unit` của FiinTrade cũng không phải đơn vị dữ liệu** — `Percentage` thực ra là thập phân (`0.1821` = 18,21%), `BillionVND` thực ra là VND đầy đủ. Dùng `don_vi_du_lieu` trong [từ điển mã trường](../10-sources/market/field-dictionary.json), không dùng nhãn của API.
5. **`getScreenerItems` timeout khi gửi nhiều tiêu chí** — 79 tiêu chí thì server FiinTrade trả lỗi Redis timeout, 1 tiêu chí thì chạy ngay. Vẫn đủ 223 trường bất kể số tiêu chí.
6. **`isa20ttm` không bằng tổng 4 quý `isa20`** — lệch tới 9,4%. Screener dùng lợi nhuận cổ đông công ty mẹ, BCTC dùng lợi nhuận thuần. Đừng tự tính lại.

> Bẫy 3 và 4 là **cùng một loại lỗi trên hai nhà cung cấp khác nhau** — nhãn đơn vị do nguồn tự khai không khớp dữ liệu nguồn tự trả. Nếu thêm nguồn thứ tư, kiểm đơn vị bằng dải giá trị thật trước khi tin nhãn.

Danh sách đầy đủ: [13 bẫy triển khai](../10-sources/market/00-conventions.md) · [6 bẫy WiChart](../10-sources/macro/wichart.md) · [7 cạm bẫy nguồn tin](../10-sources/news/README.md) · [3 bẫy cấu trúc Yahoo](../10-sources/global/yahoo.md) · [8 bẫy FRED](../10-sources/global/fred.md) · [5 bẫy tỷ giá](../10-sources/global/fx.md) · [4 bẫy Binance](../10-sources/global/crypto.md).

**Điểm chung của cả ba nhóm bẫy:** mọi thứ nguồn tự khai về chính nó đều phải kiểm lại bằng dữ liệu.

> **Và một bài học ngược lại, cũng đắt ngang:** không phải bất thường nào cũng là lỗi của nguồn. Khi bộ phân loại đơn vị tụt từ 19/19 xuống 16/19 sau khi thêm dữ liệu Screener, kết luận đầu tiên là *"Screener dùng thang khác"* — sai. Kiểm lại bằng `valueRange` của chính API thì thấy Screener dùng đúng thang, còn nguyên nhân là **luật phân loại của mình gãy trên giá trị cực trị toàn thị trường**. Đổ lỗi cho nguồn thì dễ, và nó chặn mất việc tìm ra lỗi thật.

