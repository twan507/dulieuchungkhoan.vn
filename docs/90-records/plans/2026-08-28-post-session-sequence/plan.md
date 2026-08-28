# Kế hoạch thực thi — Chuỗi việc sau phiên 28/08

> **Cách dùng:** làm **tuần tự từ trên xuống**, mỗi task một checkbox. Đây là bản điều phối cho cửa sổ sau **15:10**; task nào có hồ sơ riêng thì trỏ về đó, không chép lại nội dung.

**Vì sao gom thành một chuỗi:** mấy việc này đụng vào ba thứ đang chạy — tiến trình ingester, bảy task Scheduler, và DB thật. Làm rải rác trong phiên thì mỗi lần lại phải cân nhắc "cái này có an toàn bây giờ không". Chủ dự án chốt 2026-08-28: **đợi hết phiên, làm một lượt cho nhất quán**.

**Cửa sổ an toàn:** sau **15:10** — ingester ghi thật dừng 15:05 *(`SESSION_END_RUN`)*, bản đo dừng 15:10 *(`SESSION_END_MEASURE`)*. Kiểm bằng `Get-ScheduledTask -TaskName "dlck-*"` phải thấy `State=Ready`, không còn `Running`.

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

- [ ] **Bước 1: Kiểm không còn tiến trình ghi**

```bash
powershell -NoProfile -Command "Get-ScheduledTask -TaskName 'dlck-*' | Select-Object TaskName,State"
```
Expected: cả 7 task `Ready`, **không cái nào `Running`**. Còn `Running` thì chưa tới giờ, đợi.

- [ ] **Bước 2: Kiểm phiên đã đóng sổ trong kho**

```bash
docker exec infra-clickhouse-1 clickhouse-client --password "$CLICKHOUSE_PASSWORD" -q "select max(ts) from rt.quote where toDate(ts)=today()"
```
Expected: mốc cuối ≈ **15:05**, giống phiên 27/08 *(đo: `2026-08-27 15:05:01.501`)*.

---

### Task 1: Đóng AC3 — hằng đẳng thức sổ sách của lát tràn-ra-đĩa

**Hồ sơ:** [`2026-08-28-ingester-spill-to-disk/`](../2026-08-28-ingester-spill-to-disk/spec.md) §11. Đây là điều kiện cuối để lát đó thôi 🟡.

🔴 **Hôm nay là phiên ĐẦU TIÊN chạy code tràn-ra-đĩa.** Phiên trọn 27/08 *(3.122.376 dòng quote, 08:45 → 15:05)* chạy bằng code cũ — lát spill mới xong tối 27. Nên số của hôm nay mới dùng được cho AC3.

- [ ] **Bước 1: Chạy bộ đếm `d[]` offline, so thẳng với kho**

```bash
cd backend && uv run python -m ingester --count 20260828 --db
```
In ra bảng `table | expected | actual | diff` cho 5 bảng, kèm dòng metrics offline. **Dán nguyên văn vào ledger.**

- [ ] **Bước 2: Lấy các counter PHIÊN từ log — bộ đếm offline KHÔNG có chúng**

Chính công cụ tự cảnh báo điều này. Lấy dòng `run counters` cuối cùng của phiên:

```bash
grep "run counters" ../dlck-runtime/logs/ingester-20260828.log | tail -1
```
Cần các khoản: `not_leader_dropped.<bảng>` · `replay_blocks` · `replay_rows` · `dup_dropped` · `normalize_error` · `no_symbol_dropped` · `spill_*`.

- [ ] **Bước 3: Cộng sổ**

```
expected − (dup_dropped + normalize_error + no_symbol_dropped + not_leader_dropped.<bảng>
            + nợ_đĩa + chênh_hai_socket) + replay_rows  =  actual
```
Điều kiện đỗ: **dư = 0**. Không có "chênh nhỏ chấp nhận được".

📌 **Số đo giữa phiên 09:22:02 cho thấy `chênh_hai_socket` gần như bằng 0**: `i` 88.417 vs 88.418 *(lệch 1)*, `o`/`idx`/`t`/`ptm` **trùng khít**. Nếu cuối phiên vẫn thế thì số hạng này coi như triệt tiêu — hằng đẳng thức có cơ hội đóng khít tuyệt đối.

- [ ] **Bước 4: Ghi kết quả**

Dư = 0 ⇒ cập nhật [`ledger`](../2026-08-28-ingester-spill-to-disk/ledger.md), đổi trạng thái lát spill từ 🟡 sang ✅ ở [`90-records/README.md`](../../README.md) và [roadmap §2 mục 4c](../../../00-overview/roadmap.md).
Dư ≠ 0 ⇒ **dừng, không sửa gì**, ghi nguyên trạng vào ledger và định vị vùng thủng bằng log §6 trước khi kết luận.

---

### Task 2: Đăng ký lại 7 task với `-LogonType S4U`

**Hồ sơ:** [service-topology §5](../../../20-design/service-topology.md).

🔴 **Việc này KHÔNG chỉ là chạy lại script.** `scripts/register-tasks.ps1` hiện **không có tham số `-LogonType`** — nó gọi `Register-ScheduledTask` không kèm `-Principal`, nên luôn ra Interactive. Phải **sửa script trước**.

- [ ] **Bước 1: Thêm tham số vào script**

Thêm tham số cấp file `[string] $LogonType = "Interactive"`, dựng `$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType $LogonType -RunLevel Limited`, truyền `-Principal $principal` vào `Register-ScheduledTask`. Giữ nguyên mặc định Interactive để chạy không tham số vẫn ra hành vi cũ.

- [ ] **Bước 2: Mở rộng `Assert-TaskCommand` hoặc thêm một phép kiểm mới**

Script đã có thói quen tự kiểm lệnh sau khi đăng ký *(bài học §3.5 — 5 task từng nổ vì lệnh rỗng)*. Thêm phép kiểm `LogonType` khớp cái vừa yêu cầu, để không lặp lại đúng lỗi "trạng thái hiển thị ok mà lệnh sai".

- [ ] **Bước 3: Chạy lại bằng quyền admin**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\register-tasks.ps1 -LogonType S4U
```
⚠️ Phải là cửa sổ **Run as Administrator** — S4U cần quyền đó. Và phải chắc Task 0 đã xác nhận không task nào `Running`: `Register-ScheduledTask -Force` lên task đang chạy sẽ giết tiến trình.

- [ ] **Bước 4: Nghiệm thu**

```bash
powershell -NoProfile -Command "Get-ScheduledTask -TaskName 'dlck-*' | % { $_.TaskName + ' ' + $_.Principal.LogonType }"
```
Expected: đủ **7 dòng `S4U`**. Và sáng hôm sau: `dlck-refdata` 08:00 chạy **không hiện cửa sổ cmd**, log `refdata.log` vẫn có dòng mới.

- [ ] **Bước 5: Đồng bộ tài liệu** — [service-topology §5](../../../20-design/service-topology.md) đổi từ "hiện chạy Interactive" sang trạng thái thật; gỡ mục khỏi [roadmap §5](../../../00-overview/roadmap.md).

---

### Task 3: Luật huỷ niêm yết cho mã vắng danh bạ

**Hồ sơ riêng, đầy đủ code mẫu và nghiệm thu:** [`2026-08-28-catalog-delisting-rule/plan.md`](../2026-08-28-catalog-delisting-rule/plan.md) — 3 task.

- [ ] Task 1 của plan đó — migration `0014` + test schema
- [ ] Task 2 — đóng/gỡ dấu trong `apply()`, chọn ứng viên trong `plan_delist()`, 5 seam test, thí nghiệm đột biến ngưỡng
- [ ] Task 3 — migrate DB thật, chạy job hai lượt, đối chiếu **A=438 · B=0 · C=0 · D=4**, đồng bộ tài liệu

📌 Sau khi cài, đồng hồ 3 ngày bắt đầu chạy ⇒ mốc lật rơi vào khoảng **31/08**, và lượt đó **chốt chặn sẽ từ chối** (438/1.962 = 22,3% ≫ ngưỡng 1%). Lượt dọn phải chạy tay `--accept-drop`, có người nhìn — **không thuộc chuỗi này**, xếp lịch riêng.

---

### Task 4: Chạy nốt hai bộ test nặng

Chưa chạy bao giờ kể từ khi merge; hoãn trong phiên vì chúng dựng container Docker, tranh CPU/IO với việc bắt tick.

- [ ] **Bước 1**

```bash
cd backend && uv run pytest tests -q
```
Expected: **310 test** thu thập, xanh toàn bộ. Đây cũng là lần đầu chạy trọn bộ bằng **một lệnh** sau khi sửa lỗi collection ở `ff4d0ca`.

- [ ] **Bước 2:** đỏ ở đâu thì ghi nguyên trạng vào ledger trước khi sửa — đừng sửa trong lúc chưa biết vì sao đỏ.

---

### Task 5: Ba khoản nợ nhỏ đáng trả

Chỉ ba khoản này. Các khoản park còn lại **cố ý không đụng** — xem cuối file.

- [ ] **Bước 1: `test_icb_map_targets_level_2_only` đang xanh cả khi bảng rỗng**

`backend/tests/schema/test_s11_industry_override.py` — thêm một assert số dòng lớn hơn 0 trước phép kiểm `level <> 2`, để nó thật sự gác được chứ không xanh vô điều kiện.

- [ ] **Bước 2: Nới lưới `xmin` sang `market.security`**

`backend/tests/etl/test_e09_refdata_store.py` — `test_apply_twice_is_idempotent_including_timestamps` hiện chỉ chụp `xmin` của `market.issuer`. Hai assert `updated_at`/`ingested_at` trên `market.security` và `market.security_external_id` **rỗng nghĩa** trong cùng transaction *(`now()` là `transaction_timestamp()`)*. Chụp thêm `xmin` của hai bảng đó, giữ nguyên khuôn savepoint đã dùng.

- [ ] **Bước 3: Phân loại lỗi serialize PHÍA CLIENT thành tất định** *(điều tra 2026-08-28 trong phiên, từ chip của chaos test — kết luận: ĐÁNG SỬA, code vài dòng)*

`backend/ingester/chwriter.py` `_is_deterministic`: lỗi từ tầng serialize của clickhouse_connect (`driver.transform` gói giá trị vào cột native, ném `AttributeError`/`TypeError`/`ValueError` **trần**, không `.code`, TRƯỚC khi byte nào rời tiến trình) hiện bị đọc thành **transient** → retry vô hạn. Đã kiểm `normalize.py`: **đường thật được che** — mọi cột dựng qua constructor có kiểm kiểu, trường bắt buộc ném `NormalizeError` trước `add()`, nên đây là defense-in-depth. Nhưng **blast radius đã tăng sau lát spill**: dòng hỏng vĩnh viễn giờ đi transient 60 s → cửa 2 → file `-r` → phát lại lại lỗi → **kẹt đầu hàng đợi đĩa, disk mode không thoát cả phiên** (trước lát spill chỉ mất 1 block sau 60 s). Sửa: thêm nhánh vào `_is_deterministic` — `isinstance(e, (AttributeError, TypeError, ValueError)) and not isinstance(e, ClickHouseError) and getattr(e, "code", None) is None` → `True` (đặt sau nhánh `_DETERMINISTIC_TYPES`; `ConnectionError` là `OSError` nên không lọt; lỗi server luôn mang `.code`). Test đỏ-trước theo khuôn `test_i08` (`_RejectingClient` ném `AttributeError("'NoneType' object has no attribute 'timestamp'")` cho đúng 1 seq): 2 dòng lành vào kho, `poison_row.trade == 1`; kèm assert trực tiếp `_is_deterministic` cho cả ba loại + ranh giới ngược `ConnectionError → False`.

- [ ] **Bước 4:** chạy `uv run pytest tests -q`, commit một commit.

---

### Task 6: Dọn nhánh và đẩy lên origin

- [ ] **Bước 1: Đẩy** *(việc này chủ dự án tự chạy — thao tác `git push` bị lớp kiểm duyệt của phiên chặn)*

```bash
git push origin main
```
`main` đang **ahead 25+ commit**; `origin/main` còn đứng ở `09200a4`.

- [ ] **Bước 2: Xoá 3 nhánh đã vào `main`**

```bash
git branch -d feat/industry-two-layer-mapping fix/pytest-conftest-collision docs/task-logontype-s4u
```
Dùng `-d` chứ không `-D`: nếu nhánh nào chưa merge thật thì git sẽ từ chối, đó là lưới chặn.

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
