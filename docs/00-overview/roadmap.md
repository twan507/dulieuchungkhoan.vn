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
| Thiết kế kho dữ liệu thị trường | ✅ Đã duyệt · **phần realtime đã có code chạy** (2026-08-26) | schema `rt` + ingester đã dựng; phần REST chưa viết |
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
| **Hạ tầng + schema hai kho** | ✅ **Xong 2026-08-26** — compose (PG+Redis+CH, profile `realtime`) · schema `postgres-data` **14 migration** · schema `rt` ClickHouse 2 migration · **321 test** *(số cập nhật 2026-08-28; lúc dựng xong 26/08 là 10 migration / 71 test)* · một lượt dev trọn (dev-start → migrate → test → dev-stop) chạy sạch | [database/README.md](../../database/README.md) |
| **Code sản phẩm (ingester · ETL thật · api)** | 🟡 **Lát cắt dọc đầu đã dựng 2026-08-26** — `ingester` (socket EIO3 → chuẩn hoá → Redis + ClickHouse, leader lock, đối chứng cuối phiên) và job `etl omo`; đã qua review toàn nhánh và **merge `main` 2026-08-26** *(194 test lúc đó)*. **Cập nhật 2026-08-28: 321 test xanh** — thêm lát tràn-ra-đĩa (AC3 đóng, dư = 0), job `etl refdata`, cây ngành hai lớp, và 7 task chuyển `LogonType=S4U`. Job OMO đã chạy thật từ 26/08 (4 mốc/ngày) — nhưng ⏸️ **cả 4 task OMO đã `Disabled` lúc 2026-08-28 15:04**. Trạng thái, điều kiện bật lại và mốc rà do **mục [4d] ở §2** sở hữu — không chép lại ở đây. **Ghi tick bật 2026-08-26 tối** — phiên ghi thật đầu tiên là 27/08, chạy song song một phiên `--measure` làm lưới an toàn. ⏸️ **TOÀN BỘ 7 task ghi dữ liệu đã `Disabled` lúc 2026-09-03 ~08:55** *(quyết định chủ dự án: giai đoạn này ưu tiên dev, đã có đủ phiên 27/08 · 28/08 + sáng 03/09 làm bằng chứng)*. Hai tiến trình đang chạy (`dlck-ingester`, `dlck-ingester-measure`) bị dừng giữa phiên. Ba đồng hồ mất dữ liệu (tick · frame thô · OMO) vì thế **cùng chạy**; điều kiện bật lại và mốc rà do **mục [4d] ở §2** sở hữu. ⚠️ `scripts/register-tasks.ps1` tự `Enable` `dlck-ingester` khi chạy lại — đừng chạy script đó trong lúc tạm dừng. `api` chưa bắt đầu. **[7] ETL hằng ngày tách thành chuỗi lát; lát 1 `etl screener` ✅ XONG 2026-09-03** — đã merge `main`, chạy thật sau phiên **1.541 dòng/ngày**, 351 test xanh ([spec](../90-records/plans/2026-09-03-screener-daily-etl/spec.md) · [ledger](../90-records/plans/2026-09-03-screener-daily-etl/ledger.md)). **Lát 2 = lịch sự kiện, chưa bắt đầu** | [plans/2026-08-26-ingester-omo-first-slice/](../90-records/plans/2026-08-26-ingester-omo-first-slice/) |
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
| **4d** | **Bật lại toàn bộ task ghi dữ liệu** — ⏸️ 4 task OMO `Disabled` từ **2026-08-28 15:04**; **cả 7 task `Disabled` từ 2026-09-03 ~08:55** *(quyết định chủ dự án: giai đoạn này ưu tiên dev, đã đủ dữ liệu bằng chứng — 27/08 · 28/08 trọn phiên, 03/09 tới 08:55)*. 🔴 **Điều kiện bật lại, chốt 2026-08-28: khi [7] ETL hằng ngày chạy ổn định.** Đó là một *điều kiện*, không phải một ngày — nên kèm **mốc rà cứng 2026-09-15**: tới đó chưa bật thì phải quyết lại, đừng để trôi tiếp. *Kiểm 2026-09-03 08:33: vẫn tắt; ngân hàng nghỉ 31/08–02/09 nên phiên OMO mất thật tới giờ chỉ là phần sau 11:30 của 28/08 — bật trước 11:30 hôm nay là chưa mất thêm phiên nào.* Bật lại: `Get-ScheduledTask -TaskName "dlck-*" | Enable-ScheduledTask` *(rồi kiểm `State` từng task — Enable không khởi động lượt đã lỡ)*. ⚠️ Từ 2026-09-03 script đăng ký **8 task** — `dlck-screener` 15:20 chưa đăng ký trên máy (cần cửa sổ admin); đăng ký xong cũng **để `Disabled`** cùng cả đội | **Tick và frame thô mất từ 2026-09-03 08:55** — nến 1 phút không tồn tại ở nguồn nào, mỗi phiên tắt là mất hẳn. SBV **không cho backfill** — chỉ hiển thị phiên mới nhất, không có kho lưu *(`sbv-omo.md` Giới hạn 1)* ⇒ mỗi ngày làm việc kể từ **29/08** là một phiên mất hẳn. Và cột **đáo hạn/bơm ròng phải tự dựng** từ kỳ hạn, cần **~140 ngày tích luỹ** mới có số ròng đầy đủ ⇒ mỗi ngày tắt còn đẩy lùi luôn mốc đó |
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

```
[1] hạ tầng
     │
     ├─→ [6] Bảng tham chiếu + ETL danh bạ  ✅ XONG 2026-08-26 đêm (job `etl refdata` chạy thật, 2.015 mã; NGÀNH chưa gán — xem ghi chú dưới cây)
     │        │
     │        ├─→ [7]  ETL hằng ngày: giá, snapshot, screener, lịch sự kiện
     │        │         └─→ [8] Bộ giám sát hợp đồng (dựng cùng, dùng chung script)
     │        │              └─→ [9] Backfill lịch sử giá, rải 1–2 tuần
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
lát 1  screener       ✅ XONG 2026-09-03, đã merge main
lát 2  lịch sự kiện   ← ĐẨY LÊN. ~10 lời gọi/ngày, rẻ nhất cả nhóm, mà MỞ KHOÁ
                        cho snapshot, BCTC và re-crawl giá theo sự kiện quyền
lát 3  giá theo ngày  1.974 lời gọi; cần lớp core/http + đo nhịp 8 luồng
lát 4  họ snapshot    kích hoạt theo lát 2 + quét sàn — xem market-data-store §4.1b
sau đó BCTC           kích hoạt theo `getCorporateEarning` của lát 2
```

**Hai quyết định kèm theo, cùng ngày:** (a) bỏ hai kind chấm điểm `company_score` và `rate_indicator` khỏi `snapshot_daily` — migration `0015`, vì nội dung thật là điểm chữ (`C`/`B`/`D`) và cờ `0.00`/`1.00`, đúng nhóm *không dùng điểm bên thứ ba* đã loại; (b) họ Snapshot **không chạy hằng ngày** mà kích hoạt theo sự kiện kèm quét sàn, vì **không trường nào trong 18 trường ta lưu đổi theo ngày**. Ngân sách ngày vì thế xuống **≈ 2.300 lời gọi** thay vì ~6.000 — bài toán nhịp 8 luồng của lát giá dễ thở hơn nhiều so với ước lượng cũ.

⚠️ **Lịch sự kiện KHÔNG đầy đủ tuyệt đối** — đo 2026-09-03 bằng nguồn độc lập ([`08-fiin-event-calendar.md`](../10-sources/market/08-fiin-event-calendar.md)): `ShareIssuance` 100 % · `Earning` 96,4 % *(sót chỉ ở ≤ 2022)* · `CashDividend` 98,6 % **có sót ở vùng gần đây**. Nên trigger phải đi kèm quét sàn; quét sàn đồng thời là **thước đo** lỗ của lịch.

### Điểm vào cho lát 2 — đọc trước khi bắt đầu

**Trạng thái bàn giao 2026-09-03:** `main` sạch sau merge lát 1 · **351 test xanh** · 8 task Scheduler đều `Disabled` (xem [4d]) · migration head `0015`.

**Lát 2 = `etl events`** — bốn endpoint `Calendar/GetCorporate*` (`Earning` · `CashDividend` · `StockDividend` · `ShareIssuance`) → `market.corporate_event`. Bảng đã có từ migration `0004` với khoá tự nhiên 7 cột, **không cần migration mới**.

| Cần biết trước | Ở đâu |
|---|---|
| Tài liệu endpoint + bẫy `Ticker=` trả **toàn bộ** 23.434 bản ghi (phải dùng `OrganCode=`) | [`08-fiin-event-calendar.md`](../10-sources/market/08-fiin-event-calendar.md) |
| **Độ đầy đủ đã đo 2026-09-03** — `ShareIssuance` 100 % · `Earning` 96,4 % *(sót chỉ ở ≤ 2022)* · `CashDividend` 98,6 % **có sót gần đây** | cùng file, mục *Độ ĐẦY ĐỦ của lịch* |
| Khuôn job để nhân bản: fetch → normalize → merge → **guard trước commit** → apply → `close_run` | `backend/etl/screener_*.py` — lát 1, mới nhất, đã qua review toàn nhánh |
| Vì sao lát 2 đứng trước lát giá và lát snapshot | [`market-data-store.md` §4.1b](../20-design/market-data-store.md) |

**Ba bài học của lát 1, áp thẳng được:**

1. **Đừng suy nghĩa từ TÊN khoá — đọc GIÁ TRỊ.** Lát 1 mắc hai lần trong một ngày: `roe` tưởng là tỷ số, hoá ra là nhãn `'Tốt'`/`'Trung bình'`; `isa3`/`isa5` tưởng là tỷ số, hoá ra là dòng kết quả kinh doanh trùng BCTC.
2. **Guard đặt ngưỡng cách xa vùng dữ liệu thật, đừng sát mép.** Ngưỡng *"có phiên"* ban đầu đặt 50 % từ mẫu **trang 1**; lượt chạy thật cho thấy giữa phiên toàn thị trường chỉ **53,8 %** — hơn ngưỡng 3,8 điểm. Hạ về 20 % sau khi đo đủ ba mức **0 / 53,8 / 100 %** trong cùng một ngày.
3. **Bộ đếm lỗi phải nêu tên, không chỉ đếm.** `unmapped: 4` để suốt buổi không biết mã nào, đoán sai hai lần; thêm `unmapped_tickers` xong là truy ra nguyên nhân trong đúng một truy vấn.

**Việc còn treo của lát 1** *(không chặn lát 2)*: **AC5** — chạy `etl screener` **trước 09:00** một ngày bất kỳ, phải bị guard từ chối với lý do *"không phải ngày giao dịch"*; **AC6** — đăng ký `dlck-screener` (đã thêm vào `scripts/register-tasks.ps1`, cần cửa sổ **Run as Administrator**, đăng ký xong **để `Disabled`** cùng cả đội). Lát 2 (giá) mới cần lớp `core/http` + token bucket và phép đo nhịp 8 luồng mà [§10.6 quy ước chung](../10-sources/market/00-conventions.md) đòi.

## 4. Việc đã có đáp án, chỉ cần áp dụng

Bốn mục đang nằm trong danh sách **"Còn để ngỏ"** của pipeline tin nhưng thực ra đã được trả lời ở khối tài liệu khác:

| Đang ghi là để ngỏ | Đáp án đã có |
|---|---|
| Danh sách ~1.600 mã niêm yết | `getListOrganization` cho danh bạ doanh nghiệp (**gồm cả mã đã huỷ niêm yết**); con số **1.974 cổ phiếu** là đếm `StockType=2` từ **`getAllQuotes` của BVSC**, đo 2026-08-15 — không phải số của `getListOrganization`. Số ~1.600 là ước lượng sai. Lọc mã huỷ niêm yết bằng `getAllQuotes` |
| Bảng tên thương mại → mã | `organName` + `organShortName` trong cùng endpoint |
| Khung ngành để lọc tin | `getAllIcbIndustry` — cây ICB 4 cấp |
| Khung ngành cho skill | Cùng nguồn trên, nối theo hợp đồng ở [§3.2](architecture.md) |
| Bảng ánh xạ mã chỉ tiêu BCTC | **729 mã đã giải mã** từ bundle JS FiinTrade — xem [Phụ lục A §A.5](../10-sources/market/appendix-A-field-codes.md) |
| Đơn vị của các mã chỉ tiêu | **727/729 mã có `don_vi_du_lieu`**, 392 xác thực bằng đẳng thức kế toán |
| Lấy trường nào từ nguồn nào | [chọn trường cho ETL thị trường](../20-design/market-field-selection.md) — Screener 80/193 (ước lượng 2026-08-14; đếm 2026-09-03: **75/193** — 66 khoá đặt tên từ response thật, trừ 4 nhãn xếp hạng và 2 dòng KQKD trùng BCTC), Snapshot 16/54, giá từ BVSC |

## 5. Việc còn thật sự để ngỏ

| Việc | Ghi chú | Chốt bằng cách nào |
|---|---|---|
| ~~**Luật bỏ boilerplate cho từng nguồn**~~ | ✅ **Đã khảo sát 2026-08-15** — luật riêng cho cả 8 nguồn báo nằm ở [cấu trúc trang bài](../10-sources/news/article-structure.md) (33 bài, chạy thật trên trang đã tải). Còn ngỏ: dạng bài longform/video/bài cũ chưa phủ | Đã làm — đúng bằng một vòng soi tương tự vòng soi feed |
| **Chọn mô hình embedding** | 🟡 **Kích thước + kiểu lưu chốt 2026-08-26: `halfvec(768)`** — ràng buộc từ VPS 50 GB, chênh 4× dung lượng so với 1536 chiều float32 ([news-pipeline §9.5](../20-design/news-pipeline.md)). Còn ngỏ: mô hình cụ thể | Chọn bằng cách **đo khả năng tách tin trùng** trên tin đã crawl, không theo tiếng tăm. Đổi số chiều = embed lại toàn kho |
| **Ngưỡng `confidence`** phân loại | Dưới bao nhiêu thì vào hàng chờ rà tay | Sau vài tuần chạy thật |
| **Trần 3.000 hay 4.000 ký tự** | | Đối chiếu `content_chars` với các ca phân loại sai |
| **Tách từ tiếng Việt** | Chỉ làm nếu có bằng chứng `simple` + `unaccent` không đủ | |
| ~~**Câu treo cuối của dự án skill**~~ | ✅ **Đã quyết 2026-08-14: giữ nguyên tên "ngân hàng"** trong luận điểm *ngành báo hiệu* — là cơ chế, không phải danh sách ngành cứng. Bảng rà `CAN-SUA.md` hết việc và đã xoá | |
| **Đoạn giới hạn phạm vi vào system prompt** | Skill không tự gác cổng được — xem [§4](architecture.md) | Làm khi dựng backend |
| ~~**Đăng ký lại 7 task với `-LogonType S4U`**~~ | ✅ **XONG 2026-08-28** — cả 7 task nay `LogonType=S4U`, `RunLevel=Limited`; nghiệm thu bằng soi `Principal` từng task. Cửa sổ `cmd` (rủi ro bấm nhầm X giết phiên ghi tick) **đã hết**. ⚠️ *"Chạy cả khi không đăng nhập"* chỉ đúng một nửa — Docker Desktop sống trong session người dùng nên log off là hai kho tắt theo: [service-topology §5](../20-design/service-topology.md) | `scripts/register-tasks.ps1` nay nhận `-LogonType` + tự kiểm `Assert-TaskLogonType`. Hai bẫy đã trả giá và ghi lại: script cần **`pwsh`** (UTF-8 không BOM, 5.1 parse hỏng) và `-UserId` phải **qualified `DOMAIN\user`** (tên trần fail cả S4U lẫn Interactive) |
| ~~**Luật huỷ niêm yết cho mã vắng danh bạ**~~ | ✅ **CÀI XONG 2026-08-28, nghiệm thu trên DB thật** — migration `0014` (cột dấu `security.directory_absent_since`), `apply` đóng/gỡ dấu, `plan_delist` đọc dấu của lượt trước, ngưỡng `DIRECTORY_ABSENT_DAYS = 3`. Hai lượt job liên tiếp exit 0: đóng dấu **438** rồi **0**; **A=438 · B=0 · C=0 · D=4**. Cơ chế: [market-data-store §4.4](../20-design/market-data-store.md) | 🔴 **Còn đúng MỘT việc, và nó sẽ làm job báo đỏ trước:** ngưỡng thoả lúc 31/08 19:41, nên **lượt job đầu tiên nhìn thấy 438 ứng viên là thứ 3 01/09 08:00** — lượt đó chốt chặn 1% sẽ **từ chối** (22,3%), job báo `failed` và không ghi gì. **Đó là hành vi đúng.** Dọn bằng một lượt chạy tay có người nhìn: `uv run python -m etl refdata --accept-drop`. **Kiểm 2026-09-03: đã báo đỏ đúng thiết kế 01/09, 02/09, 03/09 — lượt dọn chưa chạy**, danh bạ đứng ở trạng thái 31/08 cho tới khi chạy |

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

