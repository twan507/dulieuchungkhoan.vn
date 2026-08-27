# Spec — Hàng đợi ghi có trần, tràn ra đĩa, không mất dòng nào

**Ngày:** 2026-08-27 · **Trạng thái:** 🟡 chờ duyệt (bản v2) · **Brief nền:** [brief.md](brief.md) *(số đo phiên 2026-08-27 + phân tích chế độ hỏng — đọc trước)* · **Hướng:** A (tràn ra đĩa), chủ dự án chốt 2026-08-27.

*Thư mục đặt tên theo ngày dự kiến thực thi (2026-08-28); spec viết 2026-08-27 — không phải gõ nhầm.*

**Bản v2 sau hai review Opus độc lập 2026-08-27** (trục kỹ thuật đối kháng + trục chuẩn repo — disposition: [review-2026-08-27.md](review-2026-08-27.md)). Các thay đổi lớn so với v1: tách vòng quản-hàng-đợi khỏi vòng ghi CH; hai cửa vào chế độ đĩa (bỏ hẳn drop-theo-hạn-chót); trần theo DÒNG không theo block; hai loại file spill (giữ-hash / được-gộp); cửa sổ dedup viết đúng đơn vị BLOCK; định nghĩa kết thúc phiên có nợ đĩa; AC3 thành hằng đẳng thức sổ sách.

**Quyết định chính sách đã chốt trong brainstorm 2026-08-27** *(không mở lại)*:

| # | Quyết định | Lựa chọn |
|---|---|---|
| 1 | Tiêu chí nghiệm thu | Bộ đếm bản ghi `d[]` từ bản đo thô, đối chứng với kho — **trong phạm vi lát này** |
| 2 | Thời điểm phát lại | **Trong phiên, có tiết lưu** — không chờ hết phiên |
| 3 | Khi trần đĩa cũng chạm | **Bỏ block MỚI đến, có đếm** — hàng đợi đĩa đã ghi giữ nguyên |
| 4 | Ack thất lạc | **Thà trùng hơn mất** — trùng phát hiện được qua đối chứng, mất thì không. ⚠️ Đây là **đảo** luật 3 của [market-data-store §3.7](../../../20-design/market-data-store.md) ("đếm đôi tệ hơn mất dòng") trong điều kiện có spill + có bộ đếm `d[]` — xem §15 |

---

## 1. Mục tiêu và phạm vi

**Mục tiêu:** đóng chế độ hỏng brief §2 — ATO mạnh trùng lúc ClickHouse trục trặc làm `pending` không trần phình tới OOM, mất sạch dữ liệu trong RAM không dấu vết. Sau lát này: RAM có trần cứng, phần vượt trần nằm trên đĩa, tiến trình chết kiểu gì thì phần đã xuống đĩa cũng tự hồi, và *"không mất dòng nào"* chứng minh bằng **số đếm độc lập**, không bằng lập luận.

**Trong phạm vi:** `ChWriter` + vòng flush của `main.py` (tách vòng, chế độ đĩa, phát lại, trần) · `drain_writer` cuối phiên · metric độ sâu và tốc độ xả · bộ đếm `d[]` offline · các phép kiểm trên ClickHouse thật · counter mới cho các đường bỏ dòng chưa đếm (`not_leader_dropped`).

**Ngoài phạm vi:** xem §14.

## 2. Máy trạng thái hai chế độ

### 2.1 Bất biến nền: tách vòng quản-hàng-đợi khỏi vòng ghi CH

Kiến trúc hiện hành có một điểm chết đã được review chỉ ra: `flush_once` giữ `_flush_lock` suốt lúc insert, nhịp gọi 1 s trả về ngay khi lock bận, và một server treo (không chết hẳn) giam thread flush tới hàng chục giây **mỗi block** — trong suốt thời gian đó không dòng code nào kiểm trần hay chuyển chế độ, RAM phình đúng như chế độ hỏng brief §2 (~200 MB cho 63 s treo ở đỉnh ATO).

Vì vậy lát này **tách hai vòng**, và đây là bất biến số một của spec:

> **Vòng QUẢN (mỗi nhịp 1 s, luôn chạy, KHÔNG bao giờ làm I/O ClickHouse):** cắt buffer → `pending`, ghi gauge độ sâu, kiểm hai cửa vào chế độ đĩa, ghi block xuống đĩa khi ở chế độ đĩa, chuyển chế độ. Chạy được ngay cả khi vòng ghi đang kẹt trong một insert.
>
> **Vòng GHI (tách riêng):** lấy block theo FIFO, insert với **ngân sách thời gian cho cả lời gọi** (không phải cho từng block), trả về còn/hết. Hợp đồng `_write_block` đổi: trả `DONE | RETRY_LATER | POISONED` — vòng retry + backoff nằm ở tầng gọi; nhánh chia đôi dòng độc giữ **trần số lần thử**, không phải trần thời gian (tránh tái diễn ca 778 s đã trả giá).

Lỗi đường đĩa (ENOSPC, PermissionError, file cụt, pickle hỏng) **không bao giờ thoát ra khỏi hai vòng** — mỗi loại có counter (`spill_io_error`, `replay_corrupt`) + log, nhịp sau chạy tiếp. Vòng flush hiện tại không có `try` nên một exception I/O sẽ giết task im lặng cả phiên — seam test riêng cho bất biến này (§13.11).

`add()` trên event-loop **không bao giờ đụng đĩa** — như v1, đã kiểm khả thi (chỉ chạm `buffers`/`pending` dưới `_lock` hiện có, không cần khoá mới).

### 2.2 Chế độ RAM (bình thường)

Như hiện hành, thêm:

- `pending` có **trần N tính theo DÒNG toàn cục** (đếm chung mọi bảng). ⚠️ Không đếm theo block: `flush_once` cắt block theo nhịp chứ không theo độ đầy — 99,99 % block trong phiên thường là block vài chục dòng (brief §3.3 cả phiên chỉ một lần `block_cap`), trần theo block vừa bật nhầm sau vài giây hiccup vừa không chặn được RAM lúc ATO. Gauge byte = dòng × 497 B (hằng số đo brief §3.2) — **không** `getsizeof` đệ quy trên đường chạy.
- Gauge `pending_depth` ghi metric mỗi nhịp vòng quản, kể cả khi mọi thứ khoẻ; vượt 50 % N → log WARNING (brief §5.1 đòi metric **+ ngưỡng cảnh báo**).
- Luật chia đôi cô lập dòng độc giữ nguyên (theo mã lỗi tất định).

### 2.3 Chế độ ĐĨA — hai cửa vào, bất biến "dính"

**Cửa vào (một trong hai):**

1. **Trần RAM:** tổng dòng trong `pending` vượt N.
2. **Hạn chót transient:** một block cạn ngân sách retry 60 s ở chế độ RAM → block đó **ghi xuống đĩa**, không bỏ. Đường `dropped_block` (bỏ theo hạn chót) **xoá khỏi mode run** — nếu giữ, kịch bản dễ nhất của AC2 (`docker stop` vài phút ở tải nhẹ, ~4 MB/60 s không bao giờ chạm N) chắc chắn mất dòng, mâu thuẫn "0 dòng mất". Đường thoát cuối duy nhất còn lại là trần đĩa (§6).

**Trong chế độ đĩa:**

3. Phần `pending` hiện có thành **đầu hàng đợi** trong RAM; mọi block cắt mới xuống đĩa ở nhịp vòng quản kế tiếp (giữa hai nhịp nằm RAM ≤ ~1 s tải đến — nay đúng thật vì vòng quản không bị insert chặn).
4. Xả theo **FIFO toàn cục**: đầu RAM (cũ nhất) trước → rồi đĩa theo thứ tự tên file. Tiết lưu: **K là trần TỔNG số dòng insert mỗi nhịp của vòng ghi, tính cả block lấy từ đầu RAM** — không có nhịp "xả dồn N block" nào khi CH vừa gượng dậy.
5. **Không drop theo thời gian.** Block chỉ rời hàng đợi khi (a) insert thành công, hoặc (b) dòng độc đã cô lập. Transient kéo dài → file nằm đó, vòng ghi backoff, nhịp sau thử tiếp.
6. **Ra:** chỉ khi đĩa rỗng (và đầu RAM rỗng). *Ghi chú tỉnh táo từ review: FIFO toàn cục là ràng buộc **tự đặt** cho dễ suy luận — không bất biến đọc nào đòi nó (MV nến khoá theo giá trị cột `(event_ts, seq, received_at)`, không theo thứ tự insert). Giá của nó là kéo dài chế độ đĩa. Nếu số đo cho thấy chế độ đĩa dai quá mức, lối thoát đã biết là hạ xuống FIFO theo bảng — nhưng đó là quyết định đổi spec, không phải quyết định của plan.*

### 2.4 Phát lại: hai loại file, gộp có điều kiện

Nhịp đến thật ở chế độ đĩa là **~5–6 block/s** (mỗi bảng một block mỗi nhịp + cap-cut lúc ATO), phần lớn là block nhỏ — phát lại từng file nhỏ một insert sẽ không bao giờ rút kịp. Đòn bẩy duy nhất là **gộp**, nhưng gộp đổi hash block ⇒ mất lưới dedup cho block đã từng gửi. Giải: phân hai loại file từ lúc ghi, bằng hậu tố tên:

| Loại | Sinh từ | Phát lại |
|---|---|---|
| **`-r.blk`** (retry) | Block cạn hạn chót transient (§2.3 cửa 2) — **có thể đã gửi, ack có thể đã mất** | **Nguyên văn, không gộp** — giữ đúng hash để lưới dedup còn cơ hội bắt |
| **`-n.blk`** (new) | Block cắt mới trong chế độ đĩa — **chưa từng gửi**, không có ack nào để mất | **Được gộp** các file cùng bảng liền kề tới ≤ `BLOCK_CAP` dòng một insert — hash mới vô hại |

**Điều kiện khả thi của K** (ghi tường minh, không phải lời hứa): `nhịp_dòng_đến_đỉnh × p95_insert_per_dòng < 1`. Nếu phép đo §10 cho thấy điều kiện vỡ (ClickHouse không nuốt kịp ngay cả khi đã gộp) thì **không K nào cứu được** — plan phải dừng ở điểm đo và báo chủ dự án, không được chọn đại một K rồi đi tiếp.

### 2.5 Hằng số — công thức trước, số sau

🔴 Không số nào được bốc thuốc; task đo (§10) chạy trước, hằng số điền theo công thức, căn cứ đo ghi ngay tại định nghĩa trong code:

| Hằng số | Công thức | Ràng buộc |
|---|---|---|
| **N** (trần `pending`, đơn vị DÒNG) | Ngân sách RAM hàng đợi ÷ 497 B/dòng. Ngân sách RAM hàng đợi = 200 − 97 (writer thường) − 13 (tiến trình đo) − ~12 (`buffers` 5 bảng × 5.000 dòng) ⇒ **≤ ~50 MB ≈ 100.000 dòng** | N chỉ cần **đủ để chế độ đĩa không kích ở vận hành bình thường**: ≥ 10× `pending_depth` p99 đo được (§10.1) và ≥ vài giây ATO đỉnh. Khả năng "chịu 1 phút đỉnh × 3" **thuộc trần đĩa, không thuộc N** — RAM không phải vùng chịu sự cố trong hướng A |
| **K** (trần dòng insert/nhịp khi phát lại) | > nhịp dòng đến đỉnh (~6.500 dòng/s) × hệ số an toàn ≥ 3, và K × p95_insert_per_dòng < 1 nhịp | Kèm điều kiện khả thi §2.4; hệ quả phụ: cửa sổ dedup co còn ~100/(block-per-nhịp) — xem §7 |
| **Trần đĩa** | ✅ **10 GiB** *(đo 2026-08-27: pickle 65 B/dòng — §9.2)*. Đích: chịu được **≥ 2 giờ sự cố ở tải đỉnh × hệ số 3** — kiểm: 6.496 dòng/s × 7.200 s × 65 B × 3 ≈ 9,1 GB ≤ 10 GiB | Cộng kho CH ~5 GB + bản đo 30 ngày ~2,8 GB + Postgres/OS/Docker vẫn nằm trong 60 GB |

**Kết quả gate điền hằng số** *(2026-08-27 tối — nguồn: probe §9 + số phiên thật 27/08 trong brief §3)*:

- `N_CAP_ROWS = 100_000` — 49,7 MB @ 497 B/dòng ≤ ngân sách ~50 MB; ≈ 15 s ATO đỉnh ≈ 5 s × hệ số 3.
- `K_REPLAY_ROWS = 20_000` — > 6.496 × 3 = 19.488; chi phí xả 4 insert gộp × p95 88 ms ≈ 0,35 s < 1 nhịp.
- **Điều kiện khả thi §2.4: ĐẠT, dư ~8,7×** — 6.496 dòng/s × (88 ms ÷ 5.000 dòng) ≈ 0,114 < 1. p95 hồ sơ VPS hẹp ≈ hồ sơ dev (88,2 vs 87,5 ms) nên K không cần hiệu chỉnh theo môi trường.

## 3. Vòng đời file trên đĩa

```
serialize (pickle protocol 5) → spill/<seq>-<table>-<loại>.blk.tmp (O_EXCL)
→ rename thành .blk (đích PHẢI chưa tồn tại — va chạm = counter + ERROR, không đè)
→ (tới lượt) đọc → insert → THÀNH CÔNG → xoá file
```

- **Một thư mục phẳng, `seq` toàn cục** — không chia thư mục ngày (v1 chia theo ngày nhưng cấm xoá theo tuổi nên phân vùng không phục vụ gì, lại đẻ bài toán FIFO xuyên thư mục). FIFO = thứ tự `seq` zero-pad (10 chữ số — tràn là ~10¹⁰ block, không xảy ra trong đời VPS).
- 🔴 **`seq` bền qua restart:** khởi tạo = max(`seq` quét được trên đĩa) + 1, trong cùng lần quét khởi động. Không có luật này thì tiến trình mới đè đúng file mà nó vừa hứa phát lại (`rename` thay thế đích im lặng trên cả POSIX lẫn Windows) — mất 5.000 dòng không dấu vết. `.tmp` mở bằng `O_EXCL`; đích `.blk` kiểm chưa-tồn-tại trước rename.
- **Mỗi block một file pickle.** Pickle giữ Decimal/datetime từng byte — phát lại loại `-r` là đúng block cũ, đúng hash cũ (đã kiểm: `received_at` do writer cấp, nằm trong `COLUMNS`, không dựa DEFAULT của DDL — nội dung block tất định).
- **Xoá file CHỈ SAU insert thành công** — hợp đồng "không mất dòng nào" thu về một câu.
- **Chia đôi dòng độc ở chế độ đĩa:** ghi **hai file con rồi xoá file cha TRƯỚC khi insert** — biến một block không-nguyên-tử thành hai block nguyên tử, đóng ca "insert nửa block rồi chết → phát lại trùng nửa đầu" mà v1 bỏ sót.
- **Không `fsync`** — quyết định tường minh: mô hình đe doạ của lát này là **tiến trình chết** (OOM/crash), với ca đó dữ liệu đã nằm trong page cache của OS và sống sót; `fsync` chỉ cứu ca **mất điện cả máy**, mà ca đó bản đo thô cùng máy cũng mất — chi phí không mua được gì.
- **Dọn:** đĩa rỗng khi thoát → không còn gì để dọn (thư mục phẳng giữ nguyên). File sót không bao giờ bị xoá theo tuổi — chỉ đường insert-thành-công được xoá.
- `spill_bytes` (phục vụ trần đĩa) khởi tạo từ lần quét khởi động, không từ 0.

## 4. Sở hữu thư mục spill — lock file, không suy đoán leadership

Thư mục spill là **tài sản của đúng một tiến trình tại một thời điểm**, chứng minh bằng **OS exclusive lock** trên một file khoá trong thư mục (giữ suốt đời tiến trình, OS tự nhả khi tiến trình chết — kể cả OOM-kill):

- **Khởi động (mode `run`):** acquire lock → quét: `.tmp` mồ côi bỏ + đếm; `.blk` sót → khởi tạo `seq`, vào thẳng chế độ đĩa, phát lại theo FIFO (chờ tới khi giành leadership mới insert).
- **Nhận leadership giữa phiên (standby tiếp quản):** chỉ được nhận nuôi thư mục spill **nếu acquire được lock** — lấy được nghĩa là chủ cũ đã chết thật; không lấy được nghĩa là chủ cũ còn sống (dù đã mất Redis lease, thread insert của nó có thể còn đang cầm file) → **không đụng thư mục**, chỉ ghi log + counter. Không bao giờ có hai tiến trình cùng đọc/xoá một file.
- **Mất leadership giữa phiên:** ngừng insert CH (như hiện hành qua `is_leader`), nhưng **tiếp tục spill xuống đĩa** — spill là I/O cục bộ, không cần leadership; dữ liệu nằm đĩa chờ lấy lại leadership hoặc chờ tiến trình sau nhận nuôi. Đầu RAM không bị vứt.
- **Standby khác máy:** thư mục spill là đĩa cục bộ — file của máy chết chỉ phát lại được khi máy đó sống lại. Topology hiện tại (một máy, Task Scheduler) chưa có ca này — ghi ở §14.

**Ack thất lạc** (insert thành công nhưng chết trước khi xoá file): lần sau insert lại. Lưới dedup của ClickHouse bắt được **chỉ khi** block còn trong cửa sổ — mà cửa sổ đếm bằng block, không bằng giây (§7), nên sau một lần restart (khởi động lại hàng chục giây, leader khác vẫn bơm block mới cùng bảng) **trùng là kết quả mong đợi, không phải ngoại lệ**. Chấp nhận theo quyết định #4; số trùng lộ ở đối chứng `d[]` dưới dạng dương và tách được nhờ `replay_blocks`.

## 5. Kết thúc phiên khi đĩa chưa rỗng — định nghĩa tường minh

Chế độ đĩa xoá hạn chót thời gian, nên `DRAIN_BUDGET_S = RETRY_BUDGET_S + 15` hiện hành **mất căn cứ** ([market-data-store §3.7](../../../20-design/market-data-store.md) luật 4 — phải viết lại, §15):

1. `drain_writer` đổi điều kiện "sạch": buffers rỗng **và** pending rỗng **và** đĩa rỗng. Ngân sách xả cuối phiên = min(độ sâu còn lại ÷ K, trần cứng **10 phút**) — số 10 phút chốt trong plan theo K đo được.
2. Hết ngân sách mà đĩa còn file → **để lại** (không vứt), log rõ `"còn X block / Y dòng trên đĩa"`, `drained = False` → cảnh báo *"PHÁN QUYẾT KHÔNG ĐÁNG TIN"* hiện hành **giữ nguyên ngữ nghĩa** — nó đang nói đúng sự thật; exit code khác 0 như hiện tại.
3. **Sáng hôm sau lúc khởi động:** phát lại nợ trước khi vào phiên (dòng hôm qua mang `ts`/`received_at` hôm qua — vào đúng partition cũ, không ảnh hưởng reconcile hôm nay). Sau khi nợ xả sạch, chạy `reconcile --date <ngày nợ>` cho ngày đó để có phán quyết thật thay cho phán quyết "không đáng tin" tối qua — tự động trong đường khởi động, không chờ tay.

## 6. Trần đĩa — bỏ block mới, đủ sổ sách để dựng lại

Chạm trần → bỏ block **mới đến** (quyết định #3): hàng đợi đã ghi nguyên vẹn. Sổ sách phải đủ dựng lại từ bản đo — một counter tổng không đủ vì drop **chớp tắt** quanh mức trần (hàng đợi rút xuống rồi lại chạm), không phải "một mốc duy nhất":

- Counter `spill_drop_newest.<table>` theo dòng, **tách theo bảng**.
- Mỗi block bị bỏ một dòng log có cấu trúc: `(table, n_rows, received_at_min, received_at_max)` — người dựng lại thủ công từ bản đo biết chính xác bảng nào thủng khoảng nào.

## 7. Cửa sổ dedup ClickHouse — đơn vị là BLOCK, và thiết kế này làm nó co lại

🔴 Sửa một hằng số giả đã lan vào tài liệu sống: `non_replicated_deduplication_window = 100` (DDL `0002_rt_schema.sql`) đếm **100 block gần nhất mỗi bảng**, không phải ~100 giây — "~100 s" chỉ đúng ở nhịp 1 block/giây. Hệ quả xuyên spec:

- Ở chế độ phát lại, vòng ghi bắn nhiều block/nhịp ⇒ cửa sổ thời gian co còn ~100 ÷ (block/nhịp) giây — **mỏng nhất đúng lúc cần nhất**. Đó là lý do §4 coi trùng-khi-replay là kết quả mong đợi.
- `RETRY_BUDGET_S = 60 < "cửa sổ ~100 s"` trong comment `chwriter.py:16` và luật 3 [market-data-store §3.7](../../../20-design/market-data-store.md) mang cùng hằng số giả — sửa cùng lượt (§15, kèm `git grep` "~100 giây" / "tệ hơn mất dòng").
- Hai phép kiểm §9 đo theo **số block chen giữa**, không theo thời gian — "chờ quá cửa sổ" theo đồng hồ sẽ xanh mà trả lời sai câu hỏi (đúng họ lỗi §1.3 CLAUDE.md).

## 8. Quan trắc

**Gauge:** `pending_depth` (dòng + byte = dòng × 497) mỗi nhịp vòng quản; WARNING khi > 50 % N.
**Counter mới:** `spill_blocks` · `spill_bytes` · `replay_blocks` · `spill_drop_newest.<table>` · `orphan_tmp` · `spill_io_error` · `replay_corrupt` · `seq_collision` · **`not_leader_dropped`** (đường `if is_leader: writer.add(n)` hiện bỏ dòng im lặng khi chưa/mất leader — chưa từng có counter, mà AC3 cần mọi khoản trừ đếm được) · **đếm frame theo topic trong mode `run`** (để đối chứng được với bộ đếm frame của `--measure` — tách phần chênh do hai socket rớt lệch nhau).
**Đồng hồ:** p50/p95/p99 thời gian insert (bọc `_write_block`).
**Log:** một dòng rõ khi vào/ra chế độ đĩa (kèm cửa vào nào, thời lượng, tổng block qua đĩa); log cấu trúc cho block bị bỏ (§6).

## 9. Phép kiểm một-lần trên ClickHouse thật *(kết quả ghi vào NGAY MỤC NÀY sau khi đo)*

> ✅ **ĐÃ ĐO 2026-08-27** (probe `tests/clickhouse/test_c99_dedup_probe.py`, ClickHouse container thật, schema `rt` — output nguyên văn trong ledger):
>
> - **1a (trong cửa sổ, qua đường đĩa):** block 100 dòng insert 2 lần, lần hai là bản pickle-roundtrip → `count = 100` — **server nuốt, hash GIỮ NGUYÊN qua pickle**. Giả định §3 đứng vững.
> - **1b (ngoài cửa sổ theo block):** block 50 dòng, chen 105 block khác cùng bảng, insert lại → `count = 100` — **NHÂN ĐÔI**, đúng dự đoán: cửa sổ bị đẩy theo block.
> - **1c (chiều thời gian):** block 10 dòng, chờ 130 s KHÔNG chen block, insert lại → `count = 10` — **cửa sổ thuần block, không co theo giây**; biến thể `_window_seconds` không có tác dụng quan sát được.
> - **§9.2 kích thước pickle:** block 5.000 dòng `rt.trade` = **323.657 B ≈ 316 KiB ≈ 65 B/dòng** (gọn hơn 497 B/dòng trong RAM ~7,7×).
> - **Thưởng thêm (Ruling PF-1):** p95 insert — block 5.000 dòng: 87,5 ms (dev) / 88,2 ms (VPS hẹp); block 50 dòng: ~72 ms cả hai. Insert bị chi phối bởi latency, không phải số dòng ⇒ gộp block khi phát lại (§2.4) là đòn bẩy đúng.
> - ⚠️ **Phát hiện ngoài dự kiến:** `deploy/infra/clickhouse/memory-vps.xml` bản cũ làm ClickHouse **crash-loop lúc boot** (BAD_ARGUMENTS — 3 setting `merge_tree` mặc định lớn hơn pool 8). Đã sửa (pin cả ba = 4) + kiểm bằng boot container thật (commit `7d65d44`). Overlay VPS trước đó **chưa từng được boot thử** — nếu deploy như cũ là chết từ dòng đầu.

1. **Dedup qua đường đĩa, đơn vị block:**
   - *(1a — trong cửa sổ)* insert block X → pickle → file → load → insert lại ngay: kỳ vọng bị nuốt ⇒ chứng minh vòng qua đĩa **không đổi hash** (điều seam test so-object-Python không chứng minh được).
   - *(1b — ngoài cửa sổ)* insert X → chen ≥ 100 block khác vào **cùng bảng** → insert lại X: đo nhân đôi hay nuốt. Đo thêm chiều thời gian (biến thể `_window_seconds` có tồn tại không — chưa kiểm, đo luôn, không suy). Kết quả ghi bằng đơn vị **block**.
2. **Kích thước pickle của một block 5.000 dòng `rt.quote` thật** → số cho công thức trần đĩa §2.5.

## 10. Việc phải ĐO trước khi điền hằng số *(task đầu của plan — điểm dừng cứng)*

1. Gauge `pending_depth` + đồng hồ `_write_block` chạy ít nhất **một phiên thật** → độ sâu p99 nền + tốc độ xả.
2. Nhịp block/dòng đến đỉnh — đo bằng gauge, **không suy từ 1,3 block/s** (con số đó chỉ đếm cap-cut; nhịp thật ≈ 5–6 block/s vì mỗi bảng cắt một block mỗi nhịp).
3. **Đo p95 insert dưới hồ sơ VPS hẹp** (overlay `docker-compose.vps.yml`, cache 256 MiB — brief §4 đòi, v1 làm rơi): K điền theo số đo hồ sơ hẹp, không theo dev thả cửa.
4. Điền N, K, trần đĩa theo công thức §2.5, hệ số ≥ 3; **kiểm điều kiện khả thi §2.4** — vỡ thì dừng plan, báo chủ dự án.

Plan có **điểm dừng giữa chừng**: task đo merge và chạy phiên thật trước, rồi mới tới task cơ chế tràn. Không gộp một đợt.

## 11. Bộ đếm `d[]` — đường nghiệm thu bằng số

Công cụ offline (lệnh trong họ `python -m ingester`, tên chốt ở plan), **dùng lại chính pipeline của ingester ở chế độ khô**: đọc bản đo của một ngày → parse frame → lọc topic → dedup frame → normalize → đếm dòng kỳ vọng theo bảng, không ghi DB. Không viết bộ đếm luật riêng (bẫy hai-nguồn-sự-thật). Bốn điều kiện để "chạy khô" đúng nghĩa:

1. **Đồng hồ bơm từ dữ liệu:** `FrameDedup.seen(key, now)` và `Stamper` nhận `now = r/1000` từ chính file đo — truyền đồng hồ tường khi đọc cả ngày trong một phút sẽ coi mọi frame trùng nội dung cả ngày là dup, `expected` hụt giả. Kéo theo: `make_on_packet` bẻ thành hàm nhận `now` từ ngoài (nếu không thì "dùng lại pipeline" bất khả thi).
2. Đọc cả `frames-*.jsonl` **trần chưa gzip** (tiến trình đo bị giết để lại file chưa xoay).
3. Cửa sổ chung cắt theo **`received_at`** (cùng họ đồng hồ với `r`), không theo `ts` sự kiện sàn; công cụ nhận `--from/--to`.
4. Khoản trừ đầy đủ: `dup_dropped` · `normalize_error` · `no_symbol_dropped` · `not_leader_dropped` · nợ đĩa còn lại (nếu có) · trùng do replay (dấu `replay_blocks`).

Đầu ra: bảng per-table `expected / actual / từng khoản trừ / dư`.

## 12. Tiêu chí nghiệm thu

| AC | Nội dung |
|---|---|
| **AC1** | Toàn bộ seam test (§13, chốt cuối trong plan) xanh trên ClickHouse thật |
| **AC2** | Kịch bản sự cố dàn dựng, chạy được thành lệnh: nguồn tải = phát frame từ một file đo thật qua `on_packet` (harness test, số dòng nạp biết trước) → `docker stop` ClickHouse ≥ 2 phút giữa chừng → `docker start` → chờ xả hết. Đối chứng: `count()` trong kho + trùng-đếm-được = số nạp (đẳng thức, cho phép vế trùng > 0 có sổ). RAM: RSS lấy mẫu 1 s suốt kịch bản, **đỉnh ≤ 200 MB** (ngân sách [service-topology §7b](../../../20-design/service-topology.md); chưa có cgroup nào ép nên phải đo bằng tay) |
| **AC3** | Một phiên thật với `--measure` song song: **hằng đẳng thức sổ sách** `expected − (dup_dropped + normalize_error + no_symbol_dropped + not_leader_dropped + nợ_đĩa + chênh_hai_socket) + trùng_replay_đếm_được = actual`, **dư = 0**; trong đó `chênh_hai_socket` đo tách bằng bộ đếm frame theo topic của mode `run` (§8) đối chiếu bộ đếm của `--measure` theo khoảng rớt trong log. Mọi số hạng là counter/log có thật — không có "chênh nhỏ chấp nhận được", và cũng không đòi "khớp tuyệt đối" kiểu phủ nhận quyết định #4 (trùng hợp lệ nằm ở vế `trùng_replay`) |
| **AC4** | N, K, trần đĩa nằm trong code kèm căn cứ đo; điều kiện khả thi §2.4 đã kiểm; hai phép kiểm §9 có kết quả ghi tại §9 |

## 13. Phác seam test cho plan *(chốt cùng plan; client CH inject sẵn — giả lập sự cố không cần vá code)*

1. Block → file → load → bằng tuyệt đối (Decimal/datetime).
2. `.tmp` mồ côi: bỏ + đếm, không phát lại nửa block.
3. Vượt N (theo DÒNG) khi client hỏng → file xuất hiện; client hồi mà đĩa chưa rỗng → block mới vẫn xuống đĩa.
4. Cửa vào 2: block cạn hạn chót transient → thành file `-r`, không thành `dropped_block`.
5. FIFO xuyên RAM–đĩa: thứ tự insert cuối = thứ tự sinh.
6. K là trần TỔNG: đầu RAM có M > K dòng → nhịp đó insert đúng K.
7. Gộp chỉ áp cho `-n`, không bao giờ cho `-r`.
8. Insert fail → file còn nguyên; chỉ thành công mới xoá.
9. Dòng độc chế độ đĩa: hai file con thay file cha **trước** insert; phần lành vào kho.
10. Khởi động có `.blk` sót: `seq` = max + 1 (không đè — `O_EXCL`/kiểm đích), phát lại hết, `spill_bytes` khởi tạo từ quét.
11. Lỗi I/O đĩa (inject) → vòng quản/ghi vẫn sống, counter tăng, nhịp sau chạy.
12. Chạm trần đĩa → bỏ mới: counter theo bảng + log cấu trúc `(table, n_rows, received_at_min/max)`, file cũ nguyên.
13. Lock thư mục: tiến trình hai không acquire được → không đụng file (kể cả đọc).
14. Mất leadership giữa chừng → ngừng insert, spill vẫn chạy, không mất đầu RAM.
15. Gauge `pending_depth` đúng số dòng thật (literal độc lập).
16. `add()` không đụng đĩa: inject lớp ghi đĩa ném exception → `add()` vẫn sạch.
17. `drain_writer` với đĩa còn file → `False` + log "còn X/Y".
18. Cắt cửa sổ `--from/--to` của bộ đếm `d[]` (frame ngoài cửa sổ không vào expected).
19. Golden test `d[]`: file đo cố định nhỏ → số kỳ vọng **giải tay** (literal độc lập — chống tautological §4.5.3), gồm ca dup cần đồng hồ `r` mới bắt đúng.

## 14. Ngoài phạm vi *(phân loại theo CLAUDE.md §1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| Nén biểu diễn hàng đợi RAM (brief §5-C) | Loại có chủ đích | Nhân thêm biên chứ không đặt trần — chỉ cân nhắc nếu số đo N cho thấy ngân sách quá chật |
| Nén file spill (gzip như `MeasureWriter`) | Loại có chủ đích | CPU trên đường nóng đổi lấy đĩa — mà đĩa có trần riêng đã tính đủ; xét lại nếu §9.2 đo ra block pickle lớn bất ngờ |
| WAL toàn phần | Loại có chủ đích | Hàng chục nghìn file nhỏ/ngày + I/O hot path suốt phiên cho sự cố hiếm — brainstorm 2026-08-27 |
| Trần cứng + bỏ dòng cũ (brief §5-B) | Loại có chủ đích | Chủ dự án loại: không đạt "không mất dòng nào" |
| **Công cụ nạp lại bản đo `--measure` vào kho** | Loại có chủ đích — **công cụ chưa tồn tại** (kiểm 2026-08-27: `backend/` không có đường replay; spec 2026-08-26 quyết định #10 để "tuỳ chọn", chưa làm) | "Dựng lại từ bản đo" trong spec này nghĩa là **thủ công**, với bộ đếm `d[]` + log §6 định vị vùng thủng. Tự động hoá là lát riêng nếu ca mất thật sự xảy ra |
| Chuông báo động (email/telegram) khi vào chế độ đĩa/chạm trần | Loại có chủ đích | Cùng lý do tiền lệ spec 2026-08-26 §8 — log + counter trước, kênh báo là lát vận hành riêng |
| Backpressure lên nguồn BVSC | Loại có chủ đích | EIO3/sails.io không có kênh điều khiển luồng phía client trong các loại packet đã đo ([11-bvsc-realtime](../../../10-sources/market/11-bvsc-realtime.md)); chưa dò bundle JS để kết luận toàn nguồn — không cần cho lát này *(v1 ghi "đã kiểm — không có" là quá tay: chưa có phép đo chống lưng)* |
| Giới hạn số kết nối BVSC (2 socket song song) | Chưa đo được | Roadmap §2.1 đã ghi — không thuộc lát này |
| Standby khác máy nhận nuôi spill | Loại có chủ đích | Topology hiện tại một máy; file spill là đĩa cục bộ — khi nào tách máy thì thiết kế lại §4 |
| Sửa đường đọc/API trên `rt.*` | Loại có chủ đích | Không liên quan chế độ hỏng đang vá |

## 15. Checklist tài liệu khi lát xong

- [x] [`docs/90-records/README.md`](../../README.md) — thêm dòng plan này vào index (§1.6 luật cứng — đúng ra phải làm ngay khi thư mục có spec, cùng lượt commit spec). *(Task 11, 2026-08-27: trạng thái cập nhật Phase A+B code xong + AC2 pass, chờ AC3.)*
- [x] [market-data-store §3.7](../../../20-design/market-data-store.md) — **viết lại luật 3 và luật 4**, không chỉ bổ sung: (luật 3) sửa hằng số giả "~100 giây" thành 100 block/bảng, và nêu điều kiện đảo của quyết định #4 — khi có spill + bộ đếm `d[]`, trùng-có-đếm ưu tiên hơn mất; luật cũ giữ cho chế độ RAM; (luật 4) ngân sách xả cuối phiên không còn suy từ `RETRY_BUDGET_S`, thay bằng công thức §5. Chạy `git grep` "~100 giây" và "tệ hơn mất dòng" toàn repo (gồm comment `chwriter.py:16`) — phép kiểm §1.7. *(Task 11, 2026-08-27: viết lại xong, kèm tóm tắt hợp đồng chế độ đĩa; comment `chwriter.py` và test `test_i08_chwriter.py` sửa theo cùng lượt.)*
- [x] [service-topology §7b](../../../20-design/service-topology.md) — **cả hai dòng**: đĩa (vùng spill: trần + số đo) và RAM (ngân sách hàng đợi tách khỏi 97 MB nền, kẻo người sau đọc "97/200" tưởng còn dư nguyên). *(Task 11, 2026-08-27.)*
- [x] [`backend/README.md`](../../../../backend/README.md) — chế độ chạy mới của `python -m ingester` (bộ đếm `d[]`) + câu "ba chế độ" sửa thành bốn. *(Task 11, 2026-08-27.)*
- [x] [`.env.example`](../../../../.env.example) + `ingester/config.py` — biến `INGESTER_SPILL_DIR` (mặc định `dlck-runtime/spill`, cùng họ `INGESTER_MEASURE_DIR`). *(Đã làm ở task cơ chế trước Task 11 — kiểm 2026-08-27: cả hai file đã có biến; Task 11 chỉ thêm dòng nhắc trong `backend/README.md`.)*
- [x] [roadmap](../../../00-overview/roadmap.md) — mục lát này ở §2; gỡ ⚠️ "chưa làm xong ngày nào thì ngày đó vẫn hở" ở §2.1; **đính chính** câu "khi lát tràn-ra-đĩa xong có thể rút bản đo xuống vài ngày" — AC3 biến bản đo thành hạ tầng nghiệm thu thường trực, chính sách giữ 30 ngày đứng nguyên. *(Task 11, 2026-08-27: thêm dòng trạng thái [4c], gỡ cảnh báo hở, đính chính câu rút ngày.)*
- [x] Ghi kết quả hai phép kiểm một-lần vào ngay §9 spec này *(ranh giới sửa spec sau khi duyệt: chỉ thêm kết quả đo, không đổi thiết kế)*. *(Đã ghi tại gate đo 2026-08-27 tối — xem khối "✅ ĐÃ ĐO 2026-08-27" đầu §9.)*
