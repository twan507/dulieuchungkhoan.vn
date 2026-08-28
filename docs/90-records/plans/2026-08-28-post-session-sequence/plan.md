# Kế hoạch thực thi — Chuỗi việc sau phiên 28/08

> **Cách dùng:** làm **tuần tự từ trên xuống**, mỗi task một checkbox. Đây là bản điều phối cho cửa sổ sau **15:10**; task nào có hồ sơ riêng thì trỏ về đó, không chép lại nội dung.

**Vì sao gom thành một chuỗi:** mấy việc này đụng vào ba thứ đang chạy — tiến trình ingester, bảy task Scheduler, và DB thật. Làm rải rác trong phiên thì mỗi lần lại phải cân nhắc "cái này có an toàn bây giờ không". Chủ dự án chốt 2026-08-28: **đợi hết phiên, làm một lượt cho nhất quán**.

**Cửa sổ an toàn:** sau **15:10** — ingester ghi thật dừng 15:05 *(`SESSION_END_RUN`)*, bản đo dừng 15:10 *(`SESSION_END_MEASURE`)*. Kiểm bằng `Get-ScheduledTask -TaskName "dlck-*"` phải thấy `State=Ready`, không còn `Running`.

---

## Trạng thái — cập nhật 2026-08-28 15:12

**Đã xong: CẢ 8 TASK** — 0 ✅ · 1 ✅ *(AC3 đóng, dư = 0)* · 2 ✅ *(7/7 S4U)* · 3 ✅ *(A=438·B=0·C=0·D=4)* · 4 ✅ *(313 passed)* · 5 ✅ · 6 ✅ · 7 ✅.

**Hai mốc còn treo, đều cần thời gian trôi qua chứ không phải việc để làm:**
1. **Thứ 2 31/08 08:00** — mốc hành vi S4U: `dlck-refdata` phải chạy không hiện cửa sổ cmd, `refdata.log` có dòng mới.
2. **Thứ 3 01/09 08:00** — lượt job đầu tiên thấy 438 ứng viên huỷ niêm yết; chốt chặn 1% sẽ **từ chối**, job báo `failed`. **Đó là hành vi đúng**, dọn bằng `--accept-drop` chạy tay.

Việc ngoài runbook đã làm trong ngày, phiên sau cần biết:

- ⏸️ **4 task OMO đã `Disabled` lúc 15:04** *(quyết định chủ dự án — giai đoạn này ưu tiên dev)*. Đồng hồ mất dữ liệu OMO vì thế chạy lại; xem bẫy ở Task 2.
- ✅ **`main` đã đẩy lên origin** — `origin/main` = `9a8c040`, ahead **0** *(kiểm 2026-08-28 15:18 bằng `git ls-remote`, hỏi thẳng remote chứ không tin ref tracking cục bộ)*. Task 7 Bước 1 vì thế **đã xong**.
- `main` đã gom mọi việc của ngày; **7 nhánh** đã merge đang chờ xoá ở Task 7 — không phải 3 như bản đầu.
- **Không có gì đang chạy** — `dlck-ingester` và `dlck-ingester-measure` đều `Ready` từ 15:10:18, `dlck-refdata` `Ready` (mốc kế 08:00 hôm sau).

---

## Global Constraints

- `PYTHONIOENCODING=utf-8` cho mọi lệnh Python; nạp biến bằng `set -a; . ./.env; set +a` và **không in giá trị ra output**.
- Lệnh alembic đúng dạng, chạy tại **gốc repo**: `uv run --project backend alembic -c database/alembic.ini <lệnh>`.
- Chạy pytest **riêng từng thư mục** hoặc cả `tests` một lần — lỗi collection đã sửa ở `ff4d0ca`, giờ `uv run pytest tests` chạy được cả bộ.
- Không sửa migration đã chạy trên DB thật (`0001`–`0013`).
- Conventional Commits, message tiếng Anh. Không `--no-verify`, không force push.
- **Thứ tự không đảo được:** T1 phải xong trước T2 *(T2 đăng ký lại task, kéo theo dừng/khởi động lại — đừng để lẫn vào lúc còn đang đọc số của phiên)*.

---

### Task 0: Xác nhận phiên đã đóng

- [x] **Bước 1: Kiểm không còn tiến trình ghi**

```bash
powershell -NoProfile -Command "Get-ScheduledTask -TaskName 'dlck-*' | Select-Object TaskName,State"
```
Expected: cả 7 task `Ready`, **không cái nào `Running`**. Còn `Running` thì chưa tới giờ, đợi.

- [x] **Bước 2: Kiểm phiên đã đóng sổ trong kho**

```bash
docker exec infra-clickhouse-1 clickhouse-client --password "$CLICKHOUSE_PASSWORD" -q "select max(ts) from rt.quote where toDate(ts)=today()"
```
Expected: mốc cuối ≈ **15:05**, giống phiên 27/08 *(đo: `2026-08-27 15:05:01.501`)*.

✅ **Đã chạy 15:11** — cả 7 task hết `Running` lúc **15:10:18**; `max(ts)` = **2026-08-28 15:05:01.338**. Đối chứng cuối phiên trong log: **`p1=0 p2=0 ok=971`**. Hàng đợi lúc đóng `pending_depth_rows = 0`. Cả phiên `spill_bytes = 0` · `orphan_tmp`/`replay_corrupt`/`seq_collision`/`spill_io_error` đều **0**.

---

### Task 1: Đóng AC3 — hằng đẳng thức sổ sách của lát tràn-ra-đĩa  ✅ XONG 2026-08-28 15:24

**Hồ sơ:** [`2026-08-28-ingester-spill-to-disk/`](../2026-08-28-ingester-spill-to-disk/spec.md) §11. Đây là điều kiện cuối để lát đó thôi 🟡.

🔴 **Hôm nay là phiên ĐẦU TIÊN chạy code tràn-ra-đĩa.** Phiên trọn 27/08 *(3.122.376 dòng quote, 08:45 → 15:05)* chạy bằng code cũ — lát spill mới xong tối 27. Nên số của hôm nay mới dùng được cho AC3.

- [x] **Bước 1: Chạy bộ đếm `d[]` offline, so thẳng với kho**

```bash
cd backend && uv run python -m ingester --count 20260828 --db
```
In ra bảng `table | expected | actual | diff` cho 5 bảng, kèm dòng metrics offline. **Dán nguyên văn vào ledger.**

- [x] **Bước 2: Lấy các counter PHIÊN từ log — bộ đếm offline KHÔNG có chúng**

Chính công cụ tự cảnh báo điều này. Lấy dòng `run counters` cuối cùng của phiên:

```bash
grep "run counters" ../dlck-runtime/logs/ingester-20260828.log | tail -1
```
Cần các khoản: `not_leader_dropped.<bảng>` · `replay_blocks` · `replay_rows` · `dup_dropped` · `normalize_error` · `no_symbol_dropped` · `spill_*`.

🔴 **Đừng hoảng khi grep ra rỗng — vắng mặt nghĩa là BẰNG 0, không phải log hỏng.** Kiểm 2026-08-28: năm khoản `not_leader_dropped.*` · `replay_blocks` · `replay_rows` · `normalize_error` · `no_symbol_dropped` có **0 lần xuất hiện** trong log ngày 28/08. Căn cứ ở code chứ không phải suy đoán: [`ingester/normalize.py:46`](../../../../backend/ingester/normalize.py) — `Metrics.inc` làm `counters.get(key, 0) + n` trên `dict` trần, **không pre-init**, nên một key chỉ hiện ra sau lần tăng đầu tiên. Chưa từng tăng ⇒ không có dòng ⇒ **bằng 0**. *(Mấy counter spill `orphan_tmp`/`replay_corrupt`/`seq_collision`/`spill_io_error`/`spill_bytes` **có** in `0` là vì được khởi tạo tường minh từ lượt quét đĩa lúc khởi động — seam test 10. Đừng lấy chúng làm mẫu để kết luận về năm khoản kia.)*

Hệ quả tốt: vế trừ của hằng đẳng thức co lại còn đúng một số hạng — **`dup_dropped = 1.974`** *(số của phiên 28/08)*.

- [x] **Bước 3: Cộng sổ**

```
expected − (dup_dropped + normalize_error + no_symbol_dropped + not_leader_dropped.<bảng>
            + nợ_đĩa + chênh_hai_socket) + replay_rows  =  actual
```
Điều kiện đỗ: **dư = 0**. Không có "chênh nhỏ chấp nhận được".

📌 **Số đo giữa phiên 09:22:02 cho thấy `chênh_hai_socket` gần như bằng 0**: `i` 88.417 vs 88.418 *(lệch 1)*, `o`/`idx`/`t`/`ptm` **trùng khít**. Mẫu này dùng được vì hai bên được lấy **cùng một thời điểm**.

🔴 **Bẫy: KHÔNG lấy `chênh_hai_socket` bằng cách trừ hai dòng cuối của hai log.** Hai bản ghi không cùng mốc thời gian — run-side in `run counters` lần cuối lúc **15:04:05**, còn measure-side chạy tới 15:10 và đã đứng số từ 15:07. Trừ thẳng ra `i` 288 · `o` 873 · `idx` 32 · `t` 0 · `ptm` 0, nhưng phần lớn chỗ đó chỉ là **56 giây run-side còn nhận sau lần in cuối của nó**, không phải chênh socket. Ai làm theo lối trừ này sẽ dựng ra một lỗ thủng ma **~1.193 frame** rồi đi tìm nguyên nhân không tồn tại. Số hạng này phải suy từ chính lượt chạy bộ đếm ở Bước 1 *(kiểm 2026-08-28 15:18)*.

- [x] **Bước 4: Ghi kết quả**

Dư = 0 ⇒ cập nhật [`ledger`](../2026-08-28-ingester-spill-to-disk/ledger.md), đổi trạng thái lát spill từ 🟡 sang ✅ ở [`90-records/README.md`](../../README.md) và [roadmap §2 mục 4c](../../../00-overview/roadmap.md).
Dư ≠ 0 ⇒ **dừng, không sửa gì**, ghi nguyên trạng vào ledger và định vị vùng thủng bằng log §6 trước khi kết luận.

---

### Task 2: Đăng ký lại 7 task với `-LogonType S4U`  ✅ XONG 2026-08-28 15:52 *(còn một mốc kiểm sáng mai)*

**Hồ sơ:** [service-topology §5](../../../20-design/service-topology.md).

🔴 **Việc này KHÔNG chỉ là chạy lại script.** `scripts/register-tasks.ps1` hiện **không có tham số `-LogonType`** — nó gọi `Register-ScheduledTask` không kèm `-Principal`, nên luôn ra Interactive. Phải **sửa script trước**.

- [x] **Bước 1: Thêm tham số vào script**

Thêm tham số cấp file `[string] $LogonType = "Interactive"`, dựng `$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType $LogonType -RunLevel Limited`, truyền `-Principal $principal` vào `Register-ScheduledTask`. Giữ nguyên mặc định Interactive để chạy không tham số vẫn ra hành vi cũ.

🔴 **Đính chính bước này: `-UserId $env:USERNAME` SAI — phải qualified `"$env:USERDOMAIN\$env:USERNAME"`.** `Get-ScheduledTask` **hiển thị** UserId là `tuanb`, nhưng dạng hiển thị **khác dạng nhận vào**: `Register-ScheduledTask` với tên trần ném `The parameter is incorrect. (15,8):UserId:`. Đo thật 2026-08-28 bằng probe trên task rác *(không đụng 7 task thật)*:

| UserId | S4U |
|---|---|
| `tuanb` | ❌ FAIL |
| **`TUANB\tuanb`** | ✅ **OK** |
| `S-1-5-21-…-1001` (SID) | ❌ FAIL |

Và bẫy **không chỉ dính S4U** — đối chứng cho thấy `Interactive` + tên trần cũng FAIL y hệt, tức bản sửa đầu làm hỏng luôn đường mặc định. Script cũ thoát được vì **không truyền `-Principal`** nên chẳng phải phân giải UserId nào. Giả thuyết "tài khoản Microsoft không làm được S4U" đã bị probe **bác bỏ** — `PrincipalSource = MicrosoftAccount` nhưng S4U đăng ký được bình thường khi UserId đúng dạng.

- [x] **Bước 2: Mở rộng `Assert-TaskCommand` hoặc thêm một phép kiểm mới**

Script đã có thói quen tự kiểm lệnh sau khi đăng ký *(bài học §3.5 — 5 task từng nổ vì lệnh rỗng)*. Thêm phép kiểm `LogonType` khớp cái vừa yêu cầu, để không lặp lại đúng lỗi "trạng thái hiển thị ok mà lệnh sai".

✅ **Đã làm 2026-08-28 15:35.** Tham số `-LogonType` (ValidateSet, mặc định `Interactive` giữ nguyên hành vi cũ); `$principal` dựng một lần với `RunLevel` **đúng cái 7 task đang mang** (`Limited` — lượt này chỉ đổi LogonType, không nhân tiện đổi quyền chạy). *(Bản 15:35 dùng `-UserId $env:USERNAME` — **SAI**, đã đính chính sang qualified ở Bước 1 lúc 15:52.)* Phép kiểm mới `Assert-TaskLogonType` gọi **bên trong `Register-DlckTask`** nên không task nào lọt. Guard đã chứng minh **đỏ trước xanh** trên chính 7 task thật *(hàm trích khỏi file bằng AST, không gõ lại bản sao — tránh test tautological §4.5.3)*: đòi `S4U` khi thực tế `Interactive` ⇒ ném đúng, thông báo nêu **cả hai** giá trị, **7/7 task đều bị bắt**; đòi `Interactive` ⇒ im lặng. Dòng tổng kết cuối script cũng rẽ theo `$LogonType` — không sửa thì chạy S4U xong nó vẫn in "đang chạy Interactive".

- [x] **Bước 3: Chạy lại bằng quyền admin**

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\twan_projects\dulieuchungkhoan.vn\scripts\register-tasks.ps1 -LogonType S4U
```

🔴 **Đường dẫn TUYỆT ĐỐI, không phải tương đối** *(vấp thật 2026-08-28)*. Cửa sổ **Run as Administrator** mở ở `C:\Windows\System32`, không ở gốc repo — `-File scripts\register-tasks.ps1` ra thẳng *is not recognized as the name of a script file*. Script tự định vị repo bằng `$PSScriptRoot` nên gọi từ thư mục nào cũng chạy đúng; chỉ **đường dẫn TỚI script** là phải tuyệt đối.

🔴 **`pwsh`, KHÔNG phải `powershell`** *(bản đầu ghi `powershell` — lệnh đó chạy sẽ hỏng)*. Script là UTF-8 **không BOM** và đầy chú thích tiếng Việt; Windows PowerShell 5.1 đọc file không BOM theo ANSI nên **parse hỏng ngay**, không phải lỗi tham số. Kiểm 2026-08-28: bản `HEAD` chưa ai sửa cũng đã hỏng dưới 5.1 (1 lỗi cú pháp) và sạch dưới `pwsh` 7 — ràng buộc sẵn có của file, [`backend/README.md`](../../../../backend/README.md) vốn đã ghi đúng `pwsh`.
⚠️ Phải là cửa sổ **Run as Administrator** — S4U cần quyền đó. Và phải chắc Task 0 đã xác nhận không task nào `Running`: `Register-ScheduledTask -Force` lên task đang chạy sẽ giết tiến trình.

🔴 **Bẫy:** 4 task OMO đang ở trạng thái `Disabled` *(tắt 2026-08-28 15:04 theo quyết định chủ dự án)*. `register-tasks.ps1` đăng ký lại **cả bảy** bằng `-Force` ⇒ chúng sẽ **sống lại ở trạng thái BẬT** mà không ai nói gì. Sau khi chạy script, nếu vẫn muốn giữ OMO tắt thì tắt lại ngay:

```powershell
Get-ScheduledTask -TaskName "dlck-omo-*" | Disable-ScheduledTask
```

Và kiểm lại bằng `Get-ScheduledTask -TaskName "dlck-*" | Select TaskName,State` — trạng thái mong đợi: `dlck-ingester*` và `dlck-refdata` **Ready**, 4 task OMO **Disabled**.

- [x] **Bước 4: Nghiệm thu** *(phần đăng ký — phần hành vi chờ sáng mai)*

```bash
powershell -NoProfile -Command "Get-ScheduledTask -TaskName 'dlck-*' | % { $_.TaskName + ' ' + $_.Principal.LogonType }"
```
Expected: đủ **7 dòng `S4U`**. Và sáng hôm sau: `dlck-refdata` 08:00 chạy **không hiện cửa sổ cmd**, log `refdata.log` vẫn có dòng mới.

✅ **Phần đăng ký ĐẠT 2026-08-28 15:52** — soi độc lập, không tin output của script: cả 7 task `LogonType=S4U`, `RunLevel=Limited` giữ nguyên. Bẫy OMO **đã bắn đúng như dự đoán** — cả 4 task sống lại `Ready`, đã tắt lại ngay; trạng thái chốt: `dlck-ingester*` + `dlck-refdata` `Ready`, 4 OMO `Disabled`.

🕗 **CHƯA ĐẠT TRỌN — mốc hành vi là sáng THỨ HAI 2026-08-31, KHÔNG phải sáng mai.** Đăng ký đúng ≠ chạy đúng: phải thấy `dlck-refdata` chạy **không hiện cửa sổ cmd** và `refdata.log` có dòng mới. Hôm nay là **thứ 6 2026-08-28**; cả 7 task trigger **Weekly Thứ 2–6** nên thứ 7 và chủ nhật **không có lượt nào chạy**. Mốc kế thật, đọc từ Scheduler: `dlck-refdata` **31/08 08:00**, `dlck-ingester` + `dlck-ingester-measure` **31/08 08:30**. *(4 task OMO vẫn hiện `NextRunTime` tối nay nhưng đang `Disabled` nên không nổ.)*

Đây là lần đầu 3 job chạy dưới S4U, mà S4U đổi cả token lẫn môi trường tiến trình — chưa xem log thứ 2 thì chưa được tuyên Task 2 xong hẳn.

🔴 **Lịch nghỉ lễ VN thì trigger Thứ 2–6 KHÔNG biết.** Task vẫn nổ vào ngày thị trường đóng cửa (Tết, 30/4, 1/5, 2/9, Giỗ tổ). Với ingester/refdata thì phần lớn vô hại (phiên rỗng), nhưng nó **cắn thật vào ngưỡng ân hạn của Task 3** — xem ghi chú trong plan huỷ niêm yết.

- [x] **Bước 5: Đồng bộ tài liệu** — [service-topology §5](../../../20-design/service-topology.md) đổi từ "hiện chạy Interactive" sang trạng thái thật; gỡ mục khỏi [roadmap §5](../../../00-overview/roadmap.md).

---

### Task 3: Luật huỷ niêm yết cho mã vắng danh bạ  ✅ XONG 2026-08-28 19:41

**Hồ sơ riêng, đầy đủ code mẫu và nghiệm thu:** [`2026-08-28-catalog-delisting-rule/plan.md`](../2026-08-28-catalog-delisting-rule/plan.md) — 3 task.

- [x] Task 1 của plan đó — migration `0014` + test schema
- [x] Task 2 — đóng/gỡ dấu trong `apply()`, chọn ứng viên trong `plan_delist()`, 5 seam test, thí nghiệm đột biến ngưỡng
- [x] Task 3 — migrate DB thật, chạy job hai lượt, đối chiếu **A=438 · B=0 · C=0 · D=4**, đồng bộ tài liệu

📌 Sau khi cài, đồng hồ 3 ngày bắt đầu chạy ⇒ mốc lật rơi vào khoảng **31/08**, và lượt đó **chốt chặn sẽ từ chối** (438/1.962 = 22,3% ≫ ngưỡng 1%). Lượt dọn phải chạy tay `--accept-drop`, có người nhìn — **không thuộc chuỗi này**, xếp lịch riêng.

---

### Task 4: Chạy nốt hai bộ test nặng  ✅ XONG 2026-08-28 15:41

Chưa chạy bao giờ kể từ khi merge; hoãn trong phiên vì chúng dựng container Docker, tranh CPU/IO với việc bắt tick.

- [x] **Bước 1**

```bash
cd backend && uv run pytest tests -q
```
Expected: **310 test** thu thập, xanh toàn bộ. Đây cũng là lần đầu chạy trọn bộ bằng **một lệnh** sau khi sửa lỗi collection ở `ff4d0ca`.

✅ **XANH 2026-08-28 15:41 — `310 passed, 2 skipped` trong 28,95 s, exit 0.** Chạy trọn bộ bằng một lệnh, đúng như `ff4d0ca` hứa. Hai skip **không phải test bị bỏ quên**, cả hai là probe thủ công có cổng môi trường, đã soi bằng `-rs`: `tests/clickhouse/test_c99_dedup_probe.py` (`RUN_PROBE=1`) và `tests/ingester/test_i17_chaos_ch_restart.py` (`RUN_CHAOS=1` — chính chaos test đã chạy thật ở AC2). Tổng thu thập là 312; con số 310 trong Expected ở trên là **số test PASS**, không phải số thu thập.

- [ ] **Bước 2:** đỏ ở đâu thì ghi nguyên trạng vào ledger trước khi sửa — đừng sửa trong lúc chưa biết vì sao đỏ.

---

### Task 5: Ba khoản nợ nhỏ đáng trả  ✅ XONG 2026-08-28 16:05

Chỉ ba khoản này. Các khoản park còn lại **cố ý không đụng** — xem cuối file.

- [x] **Bước 1: `test_icb_map_targets_level_2_only` đang xanh cả khi bảng rỗng**

`backend/tests/schema/test_s11_industry_override.py` — thêm một assert số dòng lớn hơn 0 trước phép kiểm `level <> 2`, để nó thật sự gác được chứ không xanh vô điều kiện.

- [x] **Bước 2: Nới lưới `xmin` sang `market.security`**

`backend/tests/etl/test_e09_refdata_store.py` — `test_apply_twice_is_idempotent_including_timestamps` hiện chỉ chụp `xmin` của `market.issuer`. Hai assert `updated_at`/`ingested_at` trên `market.security` và `market.security_external_id` **rỗng nghĩa** trong cùng transaction *(`now()` là `transaction_timestamp()`)*. Chụp thêm `xmin` của hai bảng đó, giữ nguyên khuôn savepoint đã dùng.

- [x] **Bước 3: Phân loại lỗi serialize PHÍA CLIENT thành tất định** *(điều tra 2026-08-28 trong phiên, từ chip của chaos test — kết luận: ĐÁNG SỬA, code vài dòng)*

`backend/ingester/chwriter.py` `_is_deterministic`: lỗi từ tầng serialize của clickhouse_connect (`driver.transform` gói giá trị vào cột native, ném `AttributeError`/`TypeError`/`ValueError` **trần**, không `.code`, TRƯỚC khi byte nào rời tiến trình) hiện bị đọc thành **transient** → retry vô hạn. Đã kiểm `normalize.py`: **đường thật được che** — mọi cột dựng qua constructor có kiểm kiểu, trường bắt buộc ném `NormalizeError` trước `add()`, nên đây là defense-in-depth. Nhưng **blast radius đã tăng sau lát spill**: dòng hỏng vĩnh viễn giờ đi transient 60 s → cửa 2 → file `-r` → phát lại lại lỗi → **kẹt đầu hàng đợi đĩa, disk mode không thoát cả phiên** (trước lát spill chỉ mất 1 block sau 60 s). Sửa: thêm nhánh vào `_is_deterministic` — `isinstance(e, (AttributeError, TypeError, ValueError)) and not isinstance(e, ClickHouseError) and getattr(e, "code", None) is None` → `True` (đặt sau nhánh `_DETERMINISTIC_TYPES`; `ConnectionError` là `OSError` nên không lọt; lỗi server luôn mang `.code`). Test đỏ-trước theo khuôn `test_i08` (`_RejectingClient` ném `AttributeError("'NoneType' object has no attribute 'timestamp'")` cho đúng 1 seq): 2 dòng lành vào kho, `poison_row.trade == 1`; kèm assert trực tiếp `_is_deterministic` cho cả ba loại + ranh giới ngược `ConnectionError → False`.

- [x] **Bước 4:** chạy `uv run pytest tests -q`, commit một commit.

✅ **XONG 2026-08-28 16:05 — `313 passed, 2 skipped`** *(+3 đúng bằng số test mới của Bước 3)*.

Cả ba khoản đều là **assert xanh vô điều kiện** hoặc **lỗi phân loại sai** — nên xanh sau khi sửa chưa chứng minh được gì. Đã kiểm bằng **đột biến, gọi chính hàm test thật** *(probe tạm, chạy xong xoá)*:

- Bước 1 — làm rỗng `industry_icb_map` trong savepoint rồi gọi `test_icb_map_targets_level_2_only` ⇒ **ném `AssertionError`**. Trước khi sửa nó xanh.
- Bước 2 — ghi lại thật `market.security` và `market.security_external_id` trong subxact ⇒ `xmin` **cả hai bảng đều đổi**, tức lưới bắt được lượt ghi lại. Trước đó hai assert `updated_at`/`ingested_at` rỗng nghĩa trong cùng transaction.
- Bước 3 — **đỏ trước xanh** đúng khuôn `test_i08`: `AttributeError` trần từng bị log là `insert trade lỗi transient: code=None`, cả 3 dòng kẹt hàng đợi (`pending_depth_rows: 3`); sau khi sửa `poison_row.trade == 1`, hai dòng lành vào kho. Kèm **ranh giới ngược** (`ConnectionError`/`OSError`/`TimeoutError` vẫn transient) — test này xanh SẴN trước khi sửa, nên nó chứng minh bản vá không nuốt nhầm lỗi mạng.

---

### Task 6: Kiến thức đi theo repo — cửa vào và đường dựng máy mới  ✅ XONG 2026-08-28 16:30

*(Chủ dự án nêu 2026-08-28: dữ liệu mất không tiếc, nhưng **kiến thức phải nằm trong repo** để đổi máy dev vẫn còn.)*

Rà lại thì phần lớn đã ổn: phiên 27/08 nằm đủ trong [service-topology §7b](../../../20-design/service-topology.md) *(4,27 triệu dòng / 82,2 MB một phiên · 93 MB gzip/ngày · cảnh báo đỉnh RAM đo trên cache rộng)*, thứ tự bootstrap DB nằm trong [database/README](../../../../database/README.md). Còn thủng ba chỗ.

- [x] **Bước 1: Viết lại `README.md` gốc — chỗ trôi lệch nặng nhất repo**

Hiện đang nói: *"**Trạng thái — 2026-08-15:** thiết kế hoàn chỉnh, **chưa viết dòng code sản phẩm nào**"* và bảng cuối ghi *"Toàn bộ phần cài đặt ❌ chưa bắt đầu"*.

Thực tế 2026-08-28: ingester bắt tick thật hằng phiên · hai kho có schema và dữ liệu · 310 test · 7 task chạy theo lịch · ba job ETL đã chạy production. **Người clone repo trên máy mới đọc dòng đầu tiên sẽ kết luận dự án chưa có gì** — đúng chỗ tệ nhất để nói sai. Viết lại phần trạng thái và bảng khối cho khớp, giữ nguyên phần mô tả sản phẩm và stack.

- [x] **Bước 2: Thêm mục "Dựng trên máy mới" vào `README.md`**

Kiến thức này đang nằm rải ở `database/README` (bootstrap DB) · `deploy/infra/docker-compose.yml` · `backend/README` (ba job) · `scripts/register-tasks.ps1` (task theo lịch) · `.env.example` — **không chỗ nào nối chúng thành một chuỗi**, mà đổi máy dev cần đúng chuỗi đó. Viết dạng các bước, **trỏ** về từng file cho chi tiết, không chép lại nội dung của chúng:

```
clone → tạo .env từ .env.example → docker compose up (deploy/infra)
      → alembic upgrade head → core.ch_migrate
      → một lượt `etl refdata` (nạp danh bạ + danh mục mã + cây ICB từ API thật)
      → alembic downgrade 0012 && upgrade head   (seed lại lớp 2 gán tay — database/README §Luật)
      → uv run pytest tests
```
Đăng ký task theo lịch **chỉ khi** muốn máy đó ghi thật — máy dev thuần thì bỏ qua.

🔴 Ghi thẳng một câu: **dữ liệu không đi theo repo.** Postgres, ClickHouse, Redis nằm trong Docker named volume của máy cũ (`infra_pgdata` · `infra_chdata` · `infra_redisdata`), `dlck-runtime/` (log, bản đo, spill) nằm ngoài repo. Máy mới bắt đầu với kho rỗng và **đó là bình thường cho dev** — mọi thứ trừ tick, OMO và frame thô đều dựng lại được bằng chuỗi trên.

- [x] **Bước 3: Ghi phiên 28/08 vào `service-topology §7b`** ⚠️ *cần số của Task 1, làm sau Task 1*

§7b đã có mục *"Đỉnh ATO đã đo — 2026-08-27"*; thiếu đúng **phiên đầu tiên chạy code tràn-ra-đĩa**. Thêm một mục cho 28/08 với số đã đo **trọn phiên** *(sẵn ở đây để khỏi phải lục lại log)*:

| | 28/08 (code spill) | 27/08 (code cũ, để so) |
|---|---|---|
| Dòng vào kho | quote **3.417.375** · snapshot 1.009.350 · trade 237.450 · index 56.168 · pt_match 2.063 | quote 3.122.376 |
| Đỉnh hàng đợi | 🔴 **SỐ NÀY SAI — đã đính chính khi làm Bước 3.** Đỉnh thật là **3.090 dòng / 1.535.730 B lúc 13:00:04** (3,09%), không phải 2.948 lúc 09:00:02 — 2.948 chỉ là mẫu ATO, mà đỉnh phiên này **không** rơi vào ATO. Phải quét cả phiên thay vì đọc mẫu giờ cao điểm | — |
| Chế độ đĩa | `spill_bytes = 0` — **chưa lần nào vào** | chưa có cơ chế |
| Sổ sách spill | `orphan_tmp`/`replay_corrupt`/`seq_collision`/`spill_io_error` = **0** | — |
| Đối chứng cuối phiên | `p1=0 p2=0 ok=971`, `pending_depth_rows = 0` lúc đóng | `p1=0 p2=0 ok=868` |
| Độ trễ insert | giữa phiên p50 63 / p95 73 / p99 82 ms · cuối phiên p50 **14,7** / p95 73,6 / p99 77,4 ms | — |
| RSS tiến trình ghi | 🔴 **KHÔNG có nguồn** — `ingester-20260828.log` không ghi RSS lần nào (0 hit). Đã bỏ khỏi §7b thay vì chép lại số không truy được | đỉnh CH 1,18 GiB (cache rộng) |
| Chênh hai socket | **1 frame / 464.127** (đo 09:22:02) | — |

Bổ sung kết quả AC3 từ Task 1 rồi mới viết.

Viết **một lần** sau khi có đủ số — đừng viết trước rồi sửa lại.

- [x] **Bước 4: Quét chéo và commit**

```bash
git grep -n "chưa viết dòng code\|chưa bắt đầu" -- README.md docs
```
Mọi hit còn lại phải **đúng** hoặc **thuộc vùng lịch sử**. Commit một commit `docs: ...`.

---

### Task 7: Dọn nhánh và đẩy lên origin  ✅ XONG 2026-08-28 15:20 *(8 nhánh, gồm cả nhánh sửa runbook)*

- [x] **Bước 1: Đẩy** *(việc này chủ dự án tự chạy — thao tác `git push` bị lớp kiểm duyệt của phiên chặn)*

```bash
git push origin main
```
✅ **Đã xong** — chủ dự án đẩy sau khi phiên đóng. Kiểm 2026-08-28 15:18: `git ls-remote origin main` trả `9a8c040`, bằng `main` cục bộ, ahead **0**. *(Bản đầu của bước này ghi "ahead 25+ commit, `origin/main` đứng ở `09200a4`" — số đó đã cũ.)*

- [x] **Bước 2: Xoá các nhánh đã vào `main`**

```bash
git branch -d feat/industry-two-layer-mapping fix/pytest-conftest-collision docs/task-logontype-s4u                chore/pause-omo-tasks docs/post-session-sequence docs/runbook-knowledge-task                docs/runbook-state-after-session
```
Dùng `-d` chứ không `-D`: nếu nhánh nào chưa merge thật thì git sẽ từ chối, đó là lưới chặn.

📌 **Bảy nhánh, không phải ba.** Bản đầu liệt 3; bốn nhánh còn lại sinh ra *sau* khi bước này được viết. Kiểm 2026-08-28 15:18: `git branch --merged main` ra đủ 7, `git branch --no-merged main` **rỗng** ⇒ cả 7 xoá `-d` được. Nhánh của chính lượt sửa này (`docs/runbook-drift-fixes`) cũng xoá cùng lượt sau khi merge.

---

## Cố ý KHÔNG làm trong chuỗi này

| Mục | Lý do |
|---|---|
| `string_to_array` tính hai lần trong subquery | Sửa mỹ phẩm vào câu SQL production vừa nghiệm thu trên DB thật — được zero hành vi, phạm "sửa như phẫu thuật" |
| Thêm `AND s.status='listed'` vào `0013` | Migration **đã chạy trên DB thật**, cấm sửa. Cần thì migration mới. Đo hôm nay: 0 ticker trùng nên kết quả y hệt |
| Lưới đối chiếu file↔file cho seed lớp 2 | `0013` không được phép sửa nữa ⇒ rủi ro trôi lệch ≈ 0 |
| `test_industry_names_match_tree` thiếu ca âm | Đã phủ gián tiếp bằng set-equality của test cạnh nó |
| Dựng worktree dev | Chưa cần: việc dev sắp tới đụng `etl/refdata_*` và `tests/`, không đụng `ingester/**`. Và nó **không miễn phí** — worktree không có `.venv` (bị gitignore), `uv` phải dựng lại môi trường riêng |
| 8 mã độ tin cậy thấp + `PVT` | Cần chỉ số ngành chạy thật mới có căn cứ |
| Lượt dọn `--accept-drop` cho 438 mã | Đợi đồng hồ 3 ngày của Task 3, và phải có người nhìn |
