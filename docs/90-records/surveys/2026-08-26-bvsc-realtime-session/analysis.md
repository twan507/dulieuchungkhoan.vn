# Phân tích frame thô socket realtime BVSC — phiên chiều 26/08/2026

**Dữ liệu:** `D:\twan_projects\dlck-runtime\measure\20260826\frames-20260826-{12,13,14,15}.jsonl.gz`
**Tổng dòng đọc:** 2.316.957 dòng (0 dòng lỗi JSON).
**Cửa sổ capture đo được:** `r` nhỏ nhất = 1787723797478 ms → 2026-08-26 12:56:37 giờ VN; `r` lớn nhất = 1787731799810 ms → 2026-08-26 15:09:59 giờ VN. Tổng span = **8.002,3 giây** (~133,4 phút).
**Script dùng:**
- `analyze_measure.py` — pass chính, một lượt streaming qua cả 4 file, ghi `result.json`.
- `analyze_sm_floor.py` — pass bổ sung, gom SM theo sàn (`EX` lấy từ event `i`) để trả lời A4 dứt khoát, ghi `result_sm_floor.json`.

Cả hai đều chạy bằng `ingester.eio.parse_packet` thật của repo (`backend/ingester/eio.py`), `gzip.open(..., "rt")` + duyệt từng dòng, không nạp cả file vào RAM.

Đăng ký gói tin đã parse được đúng **5 tên event**: `idx` (17.770) · `i` (519.133) · `o` (1.647.375) · `t` (130.869) · `ptm` (1.426) — tổng 2.316.573, khớp `n_lines - other_control(384 Ack/Control)`. **Mọi `Event` đều có đúng 1 phần tử trong `d`** (`len_d_dist` toàn bộ = `{"1": <count>}`) — không có batch nhiều item/frame trong dữ liệu đo này.

---

## A. Tính chất trường `SM` của event `t`

### A1 — SM duy nhất trong (mã, giây)?

Đếm theo khoá `(SB, TD, FT, SM)` trên toàn bộ 130.869 bản ghi `t`:

```
A1_total_sb_td_ft_groups_with_sm = 130869   (mỗi bản ghi t một khoá)
A1_dup_sb_td_ft_sm_count = 0
```

**Kết luận: SM duy nhất tuyệt đối trong phạm vi (mã, giây) — 0 cặp trùng.**

### A2 — SM duy nhất trong (mã, cả phiên)?

813 mã có ít nhất 1 bản ghi `t`. Với mỗi mã, so `len(set(SM))` với tổng số bản ghi:

```
A2_symbols_total = 813
A2_symbols_with_repeated_sm = 0
```

**Kết luận: không mã nào có SM lặp lại trong cả phiên — SM duy nhất tuyệt đối theo (mã, cả phiên).**

### A3 — SM đơn điệu tăng theo thời gian trong một mã?

So từng bản ghi `t` với bản ghi `t` liền trước **của cùng mã** (theo thứ tự xuất hiện trong file — thứ tự nhận thật từ socket):

```
A3_total_transitions = 130056   (= 130869 - 813, một mã trừ 1 lần chuyển tiếp đầu)
A3_sm_decrease_count_per_symbol = 0
```

**Kết luận: SM đơn điệu tăng chặt (strictly increasing) trong phạm vi một mã — 0 lần giảm trên 130.056 lần chuyển tiếp.**

### A4 — SM là bộ đếm TOÀN SỞ hay theo mã?

Toàn cục: `SM_min = 53.516`, `SM_max = 1.994.673` (script `analyze_measure.py`).

Top 3 mã thanh khoản cao nhất (theo số bản ghi `t`): `41I1G9000` (phái sinh VN30F1M) · `SHB` · `TCB`.

| Mã | SM min | SM max | Số bản ghi |
|---|---|---|---|
| `41I1G9000` | 549.578 | 1.029.298 | 24.162 |
| `SHB` | 984.371 | 1.985.891 | 4.693 |
| `TCB` | 985.758 | 1.987.398 | 4.460 |

→ `SHB` và `TCB` phủ gần như **trùng khít cùng một dải ~1.000.000 giá trị** dù mỗi mã chỉ có ~4.500–4.700 bản ghi — nếu SM là bộ đếm riêng từng mã thì mỗi mã phải bắt đầu gần 1 và không thể trải rộng tới ~2 triệu. Đây là **bằng chứng SM không phải bộ đếm theo mã**.

Chạy pass bổ sung `analyze_sm_floor.py` (gán sàn `EX` cho từng SB từ event `i`, gom SM của event `t` theo sàn):

```json
"HOSE":  {"min": 983574,  "max": 1994673,  "count": 92991, "n_symbols": 370}
"HNX":   {"min": 61759,   "max": 139524,   "count": 8566,  "n_symbols": 176}
"UPCOM": {"min": 53578,   "max": 90588,    "count": 4707,  "n_symbols": 234}
"XHNF":  {"min": 549578,  "max": 1029317,  "count": 24413, "n_symbols": 6}   (phái sinh)
"UNKNOWN": {"min": 53516, "max": 1710221,  "count": 192,   "n_symbols": 192}  (nhiễu: trade tới trước khi biết EX của mã đó, xem chú thích)
```

`SHB` khớp dải `HOSE` (983.574–1.994.673) — đúng vì SHB đã chuyển niêm yết sang HOSE; `TCB` (HOSE gốc) cũng nằm trong đúng dải này. `41I1G9000` (phái sinh, sàn `XHNF`) nằm khít trong dải `XHNF` (549.578–1.029.317). **4 dải này tách biệt gần như hoàn toàn theo SÀN**, không theo mã.

Việc `A4_sm_global_decrease_count = 55.216 / 130.868` (~42%) khi so SM liên tiếp KHÔNG phân biệt sàn (trong `analyze_measure.py`) được giải thích trọn vẹn bởi phát hiện trên: dòng frame trong file xen kẽ bản ghi từ 4 sàn có dải số khác nhau (HNX ~61k–139k, UPCOM ~53k–90k, XHNF ~549k–1.029k, HOSE ~983k–1.995k) nên khi luồng chuyển từ một bản ghi HOSE (SM lớn) sang một bản ghi HNX/UPCOM (SM nhỏ) thì "giảm" — không phải lỗi thứ tự.

*Chú thích "UNKNOWN":* 192/130.869 bản ghi `t` (0,15%) xảy ra trước khi symbol đó có event `i` để suy ra `EX` trong đúng pass này (do `i` và `t` đến gần như đồng thời khi mở kết nối) — không ảnh hưởng tới kết luận theo sàn ở trên vì đây chỉ là hạn chế thứ tự xử lý của script, không phải bản chất SM.

**Kết luận A4: SM là bộ đếm theo TỪNG SÀN (HOSE / HNX / UPCOM / phái sinh XHNF), không phải một bộ đếm toàn thị trường duy nhất, và cũng không phải bộ đếm riêng theo từng mã.** Hệ quả cho khoá chống trùng: `(sàn, SM)` mới là khoá duy nhất đáng tin, `(mã, SM)` cũng duy nhất (theo A1/A2) nhưng dư thừa hơn cần thiết; `SM` một mình (không kèm sàn) KHÔNG duy nhất toàn hệ thống.

### A5 — Bao nhiêu giây có ≥2 lệnh khớp cùng mã?

```
A5_total_sb_second_groups = 94869   (số nhóm (SB,TD,FT) có ≥1 lệnh khớp)
A5_secs_with_ge2_trades = 17200
A5_pct = 18,13%
```

**Kết luận: 17.200 / 94.869 giây-mã (18,13%) có từ 2 lệnh khớp trở lên — đây là các điểm mà thứ tự SM (chứ không phải thứ tự nhận gói) mới thật sự quyết định giá open/close của nến giây.**

---

## B. Phái sinh — 20 topic × 14 mã (FloorCode=03)

14 mã đăng ký (lấy sống từ `cat.fetch_derivative_symbols()`, FloorCode=03, cùng ngày đo):
`41B5G9000 41B5GC000 41B5H3000 41BAG9000 41BAGC000 41BAH3000 41I1G9000 41I1GA000 41I1GC000 41I1H3000 41I2G9000 41I2GA000 41I2GC000 41I2H3000`

### B6 — Topic/event nào thực sự đẩy dữ liệu?

Trên **toàn bộ 2.316.957 dòng, chỉ 5 tên event từng xuất hiện: `idx`, `i`, `o`, `t`, `ptm`.** Không một topic nào trong 20 topic đăng ký (`i_ol o10 o_ol10 o_ol tm e e_ol im e_im om pth p u d` — 15 topic ngoài `i/o10→o/t/idx/ptm`) từng đẩy dù chỉ 1 frame, kể cả cho mã phái sinh.

Số frame theo mã phái sinh × event (script `analyze_measure.py`, khoá `B_deriv_event_counts`):

| Mã | `i` | `o` | `t` |
|---|---|---|---|
| `41I1G9000` (VN30F tháng gần) | 44.140 | 127.677 | **24.162** |
| `41I1GA000` | 32.571 | 106.983 | 147 |
| `41I1H3000` | 14.713 | 46.497 | 63 |
| `41I1GC000` | 11.015 | 35.997 | 24 |
| `41I2G9000` | 5.480 | 17.022 | 15 |
| `41I2GA000` | 2.656 | 8.598 | 2 |
| `41I2H3000` | 2.240 | 7.413 | 0 (không có `t`) |
| `41I2GC000` | 2.127 | 7.146 | 0 (không có `t`) |
| 6 mã còn lại (`41B5*`, `41BA*`) | 2 mỗi mã | 3 mỗi mã | 0 |

**Kết luận: chỉ 3 event `i`/`o`/`t` đẩy dữ liệu phái sinh — giống hệt cơ chế cổ phiếu, không có event/topic riêng nào cho phái sinh.** Thanh khoản dồn gần như tuyệt đối vào `41I1G9000` (VN30F1M), khớp mô tả REST đã đo trước đó (99,3% KL phái sinh dồn vào hợp đồng tháng gần).

### B7 — Cấu trúc trường, tần suất, openInterest

Mẫu ẩn danh (script, khoá `B_deriv_samples`):

```json
"t|41I1G9000": {"TD":"26/08/2026","FV":"10","LC":"B","FMP":"1942.0","FCV":"2.1",
                 "SM":"549578","AVO":"130496","AVA":"25337965780000.0",
                 "FT":"13:00:00","SB":"41I1G9000"}
"o|41I1H3000": {"ACT":"U","TOP":"1","t":1787724000658,"CBV":"1","CSV":"1",
                 "id":"41I1H3000:1","SP":"1949.9","BP":"1932.0","SQ":"1",
                 "SB":"41I1H3000","BQ":"1"}
"i|41B5GC000": {"EX":"XHNF","t":1787724000634,"TSI":"OPEN","SB":"41B5GC000"}
```

Bộ khoá của `t` và `o` cho phái sinh **trùng khít** danh sách 10/11 trường đã tài liệu hoá cho cổ phiếu (xem E11 — 0 khoá lạ). Không có trường nào tên `openInterest`/`OI` xuất hiện ở bất kỳ frame phái sinh nào trong toàn bộ dữ liệu.

Tần suất `41I1G9000` (mã có dữ liệu đủ dày để tính): 127.677 frame `o` trên ~8.000s capture ≈ **~16 frame/giây** riêng sổ lệnh của một hợp đồng — đông hơn hẳn cổ phiếu thanh khoản cao nhất trong tài liệu cũ (`o:SHS` 1,41/giây, đo phiên khác/khoảng thời gian ngắn hơn nên không so trực tiếp 1:1, chỉ nêu độ lớn).

---

## C. Topic `pth`

### C8 — Có frame `pth` nào không?

```
C_pth_frame_count = 0
C_pth_samples = []
```

Kiểm bằng cách đếm mọi `Event` có `pkt.name == "pth"` trên toàn bộ 2.316.957 dòng (bao gồm cả 3 sàn đăng ký `pth:HOSE`, `pth:HNX`, `pth:UPCOM` theo `cat.FLOORS`) — và bằng bảng `all_event_names` (chỉ có 5 tên event, không có `pth`).

**Kết luận: 0 frame `pth` trong toàn bộ phiên đo — khớp kết luận trước đó ở `docs/10-sources/market/11-bvsc-realtime.md` §9 (đo phiên 10/08/2026 cũng 0 frame). Đo lại lần này (26/08/2026, phủ trọn chiều, ~8.000s) tiếp tục không thấy frame nào — củng cố khả năng kênh đã ngừng phát hơn là do khoảng đo trước quá ngắn.**

---

## D. Giờ đẩy dữ liệu

### D9 — Phút sớm nhất / muộn nhất mỗi event (giờ VN)

```
idx: 12:56 → 15:05
i:   12:59 → 15:04
o:   12:59 → 15:04
t:   12:59 → 14:59
ptm: 12:59 → 14:56
```

⚠️ **"Sớm nhất" bị chặn bởi giờ bắt đầu capture (12:56:37)** — không phải giờ thật topic bắt đầu đẩy. Riêng `idx` sớm nhất trùng đúng phút bắt đầu capture (12:56) — tức `idx` gần như chắc chắn đã đẩy dữ liệu **trước** cả lúc bắt đầu ghi, không suy ra được giờ thật sự bắt đầu từ dữ liệu này. `i/o/t/ptm` sớm nhất 12:59 — cũng có thể do độ trễ subscribe/ack sau khi mở socket (vài giây), không phải bằng chứng các topic này khởi động muộn hơn `idx`.

Muộn nhất: `idx` (15:05) đẩy muộn nhất, sau đó là `i`/`o` (15:04). `t` dừng ở 14:59 và `ptm` dừng ở 14:56 — khớp việc khớp lệnh liên tục kết thúc quanh ATC (14:45) rồi có vài lệnh khớp lẻ tẻ tới 14:59, và thoả thuận (`ptm`) ngừng sớm hơn.

### D10 — Phân bố frame `idx` theo phút quanh 14:30–15:00 (ATC/PLO)

Trích `D10_idx_minute_counts_sorted` (script, per-minute, toàn bộ session ổn định ở **162 frame/phút** — tức 15 mã chỉ số × ~10,8 frame/mã/phút):

| Phút | Frame `idx` |
|---|---|
| 14:28 | 162 |
| 14:29 | 164 |
| **14:30** | **174** |
| 14:31–14:43 | 162 (ổn định) |
| **14:44** | **176** |
| **14:45** | **32** ← sụt mạnh |
| 14:46–14:58 | **6/phút** (gần như im lặng) |
| 14:59 | 22 |
| 15:00 | 14 |
| 15:01–15:03 | 0 (không có frame) |
| 15:04 | 16 |
| 15:05 | 15 |

**Kết luận: có đột biến nhẹ (tăng ~7–8%) đúng lúc mở ATC (14:30, 174 so với nền 162) và lúc gần đóng cửa (14:44, 176), sau đó sụt gần như về 0 (6 frame/phút, tức <1 mã chỉ số/phút) suốt 14:46–14:58 — khớp việc khớp lệnh liên tục đã dừng lúc 14:45 nên chỉ số gần như không đổi. Có nhịp đẩy nhỏ trở lại lúc 14:59–15:00 (đóng cửa chính thức chốt) và 15:04–15:05 (rời rạc, có thể là cập nhật muộn/beat cuối trước khi ngắt kết nối đo).** Không có bằng chứng đột biến tăng ("bùng nổ") quanh ATC — ngược lại, đây là vùng **giảm tần suất** mạnh nhất trong cả phiên.

---

## E. Tính đóng của bộ trường + chất lượng

### E11 — Khoá của `t` và `o`

```
E11_t_extra_keys = []   E11_t_missing_keys = []
E11_o_extra_keys = []   E11_o_missing_keys = []
```

**Kết luận: cả `t` (10 khoá) và `o` (11 khoá) khớp tuyệt đối danh sách tài liệu — 0 khoá lạ, 0 khoá thiếu, trên toàn bộ 130.869 + 1.647.375 bản ghi.**

### E12 — Khoá của `i` (tài liệu ghi 34)

```
E12_i_total_distinct_keys = 37
E12_i_extra_keys = ["LO", "OP", "TSI"]
E12_i_missing_keys = []
```

3 khoá lạ, ví dụ thật (script `analyze_sm_floor.py`, khoá `i_extra_samples`):

```json
{"SB":"WCS","EX":"HNX","t":1787724001934,
 "OP":290600,"LO":290600,"HI":290600,"CP":290600,"AP":290600,
 "CH":-3400,"CHP":-1.1564625850340136,"CV":100,"TT":100,"TV":29060000,
 "P1":"100","P2":"290600.0"}
```
```json
{"SB":"41B5GC000","EX":"XHNF","t":1787724000634,"TSI":"OPEN"}
```

**Kết luận: `OP` (giá mở cửa phiên) và `LO` (giá thấp nhất phiên) THỰC SỰ có được đẩy** — trái với ghi chú cũ trong `11-bvsc-realtime.md` §4 rằng `open`/`low` không được đẩy. Đây là quan sát mới, đo được lần đầu ở phiên này (chưa đối chiếu ngược lại tài liệu cũ trong phạm vi nhiệm vụ này — cần người review cập nhật doc riêng, không tự sửa ở đây theo đúng phạm vi "chỉ đọc-phân tích"). `TSI` (Trading Status Indicator, giá trị quan sát được: `"OPEN"`) là khoá lạ thứ ba, chỉ thấy ở mã phái sinh trong mẫu bắt được.

### E13 — Khoá của `idx` (tài liệu ghi 18)

```
E13_idx_extra_keys = ["IC", "MS", "NOF"]
E13_idx_missing_keys = []
```

Ví dụ thật:

```json
{"MC":"XALL","IC":"up","MI":"2870.48","ICH":"0.85","IPC":"0.03","NOF":"1", ...}
{"MC":"UPCOM","MS":"5","TD":"26/08/2026","IT":"13:00:00"}
```

**Kết luận: 3 khoá lạ — `IC` (giá trị `"up"`, có vẻ là chiều biến động, khớp dấu `ICH` dương), `MS` (giá trị quan sát `"5"`, ý nghĩa chưa xác định — không đủ căn cứ suy đoán), `NOF` (giá trị quan sát `"1"`, đi kèm `ADV`/`DE`/`NC`/`NOC` nên có thể liên quan số mã ở một mức giá — chưa xác định rõ, không suy đoán thêm).** Không kết luận ý nghĩa chính xác của `MS`/`NOF` vì không có tài liệu đối chiếu — chỉ ghi nhận sự tồn tại và giá trị quan sát được.

### E14 — `i` có cả `CV` lẫn `P1`: có bao giờ khác nhau không?

```
E14_cv_p1_both_present = 111493
E14_cv_p1_diff = 0
```

**Kết luận: trong 111.493 frame có cả hai trường, `CV` và `P1` LUÔN bằng nhau (so sánh dạng chuỗi) — 0 lần khác nhau. Xác nhận đúng ghi chú tài liệu cũ: `CV` và `P1` là hai tên khác nhau cho cùng một số liệu (khối lượng lệnh khớp gần nhất).**

### E15 — Giá trị số không parse được thành Decimal

```
E15_numeric_fail = {"i.B1": 305, "i.S1": 310}
```
Mẫu: cả hai đều là chuỗi rỗng `''` (5 mẫu đầu, script `numeric_fail_samples`).

**Kết luận: chỉ 2 trong số ~50 trường số được kiểm (10 của `t`, 8 của `o`, 32 của `i`, 15 của `idx`) từng gặp giá trị không parse được — `B1` (giá mua bậc 1) và `S1` (giá bán bậc 1) của event `i`, đều là chuỗi rỗng `''`, tổng 615/519.133 frame `i` (0,12%). Tất cả các trường số khác (kể cả toàn bộ `t`, `o`, `idx`) parse Decimal thành công 100%.** Đây là điểm cần xử lý phòng thủ khi normalize: `B1`/`S1` rỗng nhiều khả năng là trạng thái "không có giá mua/bán bậc 1 tại thời điểm đó" (ví dụ mã hết dư mua/bán tạm thời), không phải lỗi dữ liệu.

---

## F. Tải thực tế

### F16 — Tổng frame theo event, tốc độ, ước lượng dòng/ngày

Tổng frame (= tổng dòng ghi CH nếu 1 frame = 1 dòng, đã xác nhận `len(d)==1` mọi nơi — xem đầu báo cáo):

| Event | Frame | Loại dòng CH tương ứng |
|---|---|---|
| `o` | 1.647.375 | quote (sổ lệnh) |
| `i` | 519.133 | snapshot_delta |
| `t` | 130.869 | trade |
| `idx` | 17.770 | index |
| `ptm` | 1.426 | thoả thuận |
| **Tổng** | **2.316.573** | |

Tốc độ trên **8.002,3 giây** capture (12:56:37–15:09:59, 26/08/2026, catalog đầy đủ ~2.001 mã CP/ETF + 14 phái sinh):

- **Trung bình: 2.316.573 / 8.002,3 ≈ 289,5 frame/giây.**
- **Đỉnh theo phút: 13:00 với 42.287 dòng/60s ≈ 704,8 frame/giây** (`F_minute_total_top10`, script) — ngay sau giờ nghỉ trưa mở lại 13:00, dồn dập cập nhật lại toàn bộ sổ lệnh/snapshot.
- Trung bình mỗi phút (127 phút có dữ liệu): 18.240,7 dòng/phút ≈ 304 frame/giây trung bình theo phút.

**Ước lượng dòng/ngày:** dữ liệu đo **chỉ phủ phiên chiều** (12:56–15:10, ~2h13'), **KHÔNG phủ phiên sáng** (9:00–11:30, ~2h30'). Không đo trực tiếp phiên sáng nên không có số đo thật cho khoảng đó — dùng phép ước lượng nhân đôi thô (giả định mật độ frame/giây phiên sáng cùng bậc độ lớn với phiên chiều đã đo, một giả định **CHƯA kiểm chứng**):

```
Ước lượng thô = 2.316.573 × 2 ≈ 4.633.146 dòng/ngày
```

**So với dải ước lượng 5–35 triệu dòng/ngày của spec ClickHouse §10: con số ước lượng thô (~4,6 triệu) nằm NGAY DƯỚI cận dưới 5 triệu.** Đây là ước lượng nhân đôi thô, có thể lệch theo cả hai chiều: phiên sáng thường có đợt mở cửa (ATO + đợt khớp dồn dập đầu phiên) nên khả năng cao mật độ frame/giây phiên sáng **cao hơn** phiên chiều đo được (phiên chiều không có ATO, chỉ có phần đuôi liên tục + ATC), nên số dòng/ngày thật nhiều khả năng **cao hơn** 4,6 triệu — nhưng **chưa đo trực tiếp phiên sáng nên không khẳng định con số cụ thể**, chỉ nêu hướng lệch có căn cứ (đợt mở cửa dồn sổ lệnh, quan sát tương tự ở đỉnh 13:00 706,8 frame/s ngay sau giờ nghỉ trưa mở lại — ATO buổi sáng nhiều khả năng có hiệu ứng tương tự hoặc mạnh hơn).

---

## Phụ lục — lệnh chạy

```bash
cd D:\twan_projects\dulieuchungkhoan.vn\backend
PYTHONIOENCODING=utf-8 uv run python "<scratchpad>\analyze_measure.py"     # pass chính, ghi result.json
PYTHONIOENCODING=utf-8 uv run python "<scratchpad>\analyze_sm_floor.py"    # pass bổ sung SM-theo-sàn, ghi result_sm_floor.json
```

Cả hai chạy trong ~13–23 giây cho toàn bộ 2.316.957 dòng (streaming, không nạp cả file vào RAM).
