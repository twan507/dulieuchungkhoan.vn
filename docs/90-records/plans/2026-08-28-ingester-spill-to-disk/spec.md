# Spec — Hàng đợi ghi có trần, tràn ra đĩa, không mất dòng nào

**Ngày:** 2026-08-27 · **Trạng thái:** 🟡 chờ duyệt · **Brief nền:** [brief.md](brief.md) *(số đo phiên 2026-08-27 + phân tích chế độ hỏng — đọc trước)* · **Hướng:** A (tràn ra đĩa), chủ dự án chốt 2026-08-27.

**Quyết định chính sách đã chốt trong brainstorm 2026-08-27** *(không mở lại)*:

| # | Quyết định | Lựa chọn |
|---|---|---|
| 1 | Tiêu chí nghiệm thu | Bộ đếm bản ghi `d[]` từ bản đo thô, đối chứng với kho — **trong phạm vi lát này** |
| 2 | Thời điểm phát lại | **Trong phiên, có tiết lưu** — không chờ hết phiên |
| 3 | Khi trần đĩa cũng chạm | **Bỏ block MỚI đến, có đếm** — hàng đợi đĩa đã ghi giữ nguyên |
| 4 | Ack thất lạc | **Thà trùng hơn mất** — trùng phát hiện được qua đối chứng, mất thì không |

---

## 1. Mục tiêu và phạm vi

**Mục tiêu:** đóng chế độ hỏng brief §2 — ATO mạnh trùng lúc ClickHouse trục trặc làm `pending` không trần phình tới OOM, mất sạch dữ liệu trong RAM không dấu vết. Sau lát này: RAM có trần cứng, phần vượt trần nằm trên đĩa, tiến trình chết kiểu gì thì phần đã xuống đĩa cũng tự hồi, và *"không mất dòng nào"* chứng minh bằng **số đếm độc lập**, không bằng lập luận.

**Trong phạm vi:** `ChWriter` (chế độ đĩa + phát lại + trần) · metric độ sâu và tốc độ xả · bộ đếm `d[]` offline · các phép kiểm trên ClickHouse thật.

**Ngoài phạm vi:** xem §8.

## 2. Thiết kế — máy trạng thái hai chế độ

Bổ sung vào `ChWriter` ([chwriter.py](../../../../backend/ingester/chwriter.py)); đường `add()` trên event-loop **không bao giờ đụng đĩa**.

### 2.1 Chế độ RAM (bình thường)

Như hiện hành, thêm:

- `pending` có **trần N block toàn cục** (đếm chung mọi bảng — thứ phải bảo vệ là RAM tổng, không phải từng bảng).
- Gauge `pending_depth` (block + byte ước lượng) ghi metric **mỗi nhịp flush**, kể cả khi mọi thứ khoẻ.
- Hạn chót retry 60 s (`RETRY_BUDGET_S`) và luật chia đôi cô lập dòng độc **giữ nguyên**.

### 2.2 Chế độ ĐĨA (sự cố) — bất biến "dính"

**Vào:** tổng block trong `pending` vượt N (chỉ xảy ra khi ClickHouse trục trặc — brief §2: khi khoẻ, `flush_once` xả sạch trong một nhịp).

Từ thời điểm vào:

1. Phần `pending` hiện có trở thành **đầu hàng đợi** đông cứng trong RAM.
2. **Mọi block cắt mới** (từ `flush_once` lẫn từ `add()` chạm `BLOCK_CAP`) được chuyển xuống đĩa ở nhịp flush kế tiếp — giữa hai nhịp chúng nằm RAM tối đa ~1 s (đỉnh ATO đo được ~6.500 dòng/s ≈ 3,2 MB — tính vào hệ số an toàn của N, không cần cơ chế riêng).
3. Xả theo **FIFO toàn cục**: đầu RAM (cũ nhất) trước → rồi hàng đợi đĩa theo thứ tự tên file. Mỗi nhịp flush insert tối đa **K block** từ đĩa — tiết lưu để ClickHouse vừa gượng dậy không bị dồn cục.
4. **Ra:** chỉ khi đĩa rỗng. Chừng nào đĩa còn file, block mới vẫn xuống đĩa kể cả khi ClickHouse đã hồi — thứ tự tuyệt đối không bao giờ đảo. Hàng đợi rút với tốc độ (K − nhịp đến); K chọn > nhịp đến đỉnh × hệ số an toàn nên luôn rút được.
5. **Không drop theo thời gian** trong chế độ đĩa: vùng đệm là đĩa, không phải thời gian. Block chỉ rời hàng đợi khi (a) insert thành công, hoặc (b) là dòng độc đã cô lập. Transient kéo dài → file nằm đó, backoff, nhịp sau thử tiếp. `dropped_block` (drop theo hạn chót 60 s) chỉ còn tồn tại ở chế độ RAM.

### 2.3 Hằng số N, K, trần đĩa — công thức trước, số sau

🔴 **Không số nào được bốc thuốc.** Task đầu của plan là đo (§7); hằng số điền theo công thức, ghi kèm căn cứ đo ngay tại định nghĩa trong code:

| Hằng số | Công thức | Ràng buộc |
|---|---|---|
| **N** (trần pending) | RAM ngân sách cho hàng đợi ÷ 497 byte/dòng ÷ `BLOCK_CAP`, với RAM ngân sách ≤ ~50 MB (ingester tổng 200 MB — [service-topology §7b](../../../20-design/service-topology.md), đã dùng 97 MB lúc thường) | Chịu được ≥ 1 phút ATO đỉnh × hệ số an toàn ≥ 3 trước khi tràn |
| **K** (block/nhịp phát lại) | > nhịp block đến đỉnh × hệ số an toàn, và × p95 thời gian insert phải < 1 nhịp flush | Hàng đợi đĩa phải rút được ngay cả trong ATO |
| **Trần đĩa** | ~10 GB (chốt sau khi đo kích thước file block thật) | Ghi kèm phép tính "chịu được bao nhiêu giờ sự cố ở tải đỉnh"; cộng với kho CH + bản đo 30 ngày vẫn nằm trong 60 GB |

## 3. Vòng đời file trên đĩa

```
serialize (pickle protocol 5) → spill/YYYYMMDD/<seq>-<table>.blk.tmp → fsync
→ rename thành <seq>-<table>.blk → (tới lượt) đọc → insert → THÀNH CÔNG → xoá file
```

- **Mỗi block một file pickle.** Pickle giữ nguyên Decimal/datetime từng byte — phát lại là đúng block cũ, không đi qua tầng chuyển kiểu JSON. File do chính tiến trình ghi và đọc, rủi ro pickle-từ-nguồn-lạ không áp dụng. `<seq>` đơn điệu tăng, zero-pad, để FIFO = thứ tự tên file, không cần index.
- **Temp + atomic rename:** chỉ file `.blk` mới tồn tại với hàng đợi. Crash giữa lúc ghi để lại `.tmp` → quét thấy thì bỏ + counter `orphan_tmp`, không bao giờ phát lại nửa block.
- **Xoá file CHỈ SAU insert thành công** — hợp đồng "không mất dòng nào" thu về một câu. Insert thất bại transient → file còn nguyên.
- **Dòng độc trong chế độ đĩa:** giữ luật chia đôi theo mã lỗi tất định hiện có; cô lập xong (counter `poison_row`), phần lành vào kho rồi file mới được xoá.
- **Dọn:** phiên kết thúc với đĩa rỗng → xoá thư mục ngày rỗng. File sót **không bao giờ** bị xoá theo tuổi — chúng là dữ liệu chưa vào kho, chỉ đường insert-thành-công được xoá.

## 4. Hồi phục sau crash và chuyển leader

- **Lúc khởi động** (mode `run`): quét thư mục spill. Còn `.blk` sót → vào thẳng chế độ đĩa, phát lại theo FIFO trước khi nhận trạng thái bình thường. OOM/crash giờ chỉ mất phần chưa kịp xuống đĩa.
- **Lúc TRỞ THÀNH leader giữa phiên** (standby tiếp quản không qua restart): quét lại thư mục spill ngay tại thời điểm nhận leadership — file của leader cũ để lại phải được phát lại, không chờ restart. Đường spill (ghi lẫn phát lại) chỉ hoạt động trên leader, cùng ranh giới với đường ghi CH hiện hành.
- **Ack thất lạc** (insert thành công nhưng chết trước khi xoá file): lần sau insert lại. Trong cửa sổ dedup ~100 s ([spec CH §5.5](../2026-08-25-clickhouse-realtime-store/spec.md)) server tự nuốt; ngoài cửa sổ **có thể trùng** — chấp nhận theo quyết định #4 (thà trùng hơn mất; trùng lộ ra ở đối chứng `d[]` dưới dạng số dương). ⚠️ Hành vi block trùng ngoài cửa sổ trên bảng `rt.*` thật phải **kiểm, không suy** — phép kiểm §6.

## 5. Trần đĩa

Vùng spill có trần dung lượng (§2.3). Chạm trần → **bỏ block mới đến**: counter `spill_drop_newest` (đếm theo dòng), log ERROR mỗi lần, hàng đợi đĩa đã ghi nguyên vẹn. Ranh giới mất là một mốc thời gian duy nhất, thuật lại được từ log + counter. Bản đo thô của tiến trình `--measure` (chạy hằng ngày từ 2026-08-27) vẫn là đường dựng lại thủ công cho phần bị bỏ.

## 6. Quan trắc và các phép kiểm đo

**Metric mới:** `pending_depth` (gauge) · `spill_blocks` · `spill_bytes` · `replay_blocks` · `spill_drop_newest` · `orphan_tmp` · thời gian insert p50/p95/p99. **Log:** một dòng rõ khi vào/ra chế độ đĩa kèm thời lượng và số block đã qua đĩa.

**Phép kiểm một-lần trên ClickHouse thật** (kết quả ghi vào spec này, mục §9):

1. **Trùng ngoài cửa sổ dedup:** insert một block vào `rt.quote`/`rt.trade` thật, chờ quá cửa sổ, insert lại đúng block → đo xem dòng nhân đôi hay bị nuốt (theo engine từng bảng). Quyết định #4 đứng trên kết quả đo này, không trên suy luận.
2. **Kích thước file block thật:** pickle một block 5.000 dòng `rt.quote` thật → số cho công thức trần đĩa.

## 7. Việc phải ĐO trước khi điền hằng số *(task đầu của plan)*

Đúng danh sách brief §4, nay thành yêu cầu spec:

1. Gauge `pending_depth` + đồng hồ `_write_block` (p50/p95/p99) chạy ít nhất **một phiên thật** → tốc độ xả nền.
2. Nhịp block đến đỉnh (suy từ số đo ATO đã có: 6.496 dòng/s ⇒ ~1,3 block/s ở `BLOCK_CAP` 5.000 — kiểm lại bằng gauge).
3. Điền N, K, trần đĩa theo công thức §2.3, hệ số an toàn ≥ 3 trên số đo (nguyên tắc chủ dự án: phiên đo được là phiên nhẹ — brief §6).

Trình tự này nghĩa là plan có một **điểm dừng giữa chừng**: task đo merge và chạy một phiên trước, rồi mới tới task cơ chế tràn. Không gộp làm một đợt.

## 8. Bộ đếm `d[]` — đường nghiệm thu bằng số

Công cụ offline (lệnh trong họ `python -m ingester`, tên chốt ở plan), **dùng lại chính pipeline của ingester ở chế độ khô**: đọc bản đo JSONL gzip của một ngày → parse frame → lọc topic → dedup frame (`frame_key`) → normalize → **đếm dòng kỳ vọng theo bảng**, không ghi DB. Không viết bộ đếm luật riêng — hai bộ luật sẽ lệch nhau lúc nào không biết (bẫy hai-nguồn-sự-thật).

Đối chứng: so số kỳ vọng với `count()` trong `rt.*` cùng phiên, **cắt hai phía về cửa sổ thời gian chung** (measure chạy tới 15:10, writer dừng 15:05 — so ngoài cửa sổ chung là so lệch giả; công cụ nhận mốc cắt, quy trình AC3 ghi cách lấy mốc từ log writer). Đầu ra: bảng per-table `expected / actual / chênh`, kèm các khoản trừ đếm được (`dup_dropped`, `normalize_error`).

## 9. Tiêu chí nghiệm thu

| AC | Nội dung |
|---|---|
| **AC1** | Toàn bộ seam test (danh sách chốt trong plan, phác ở dưới) xanh trên ClickHouse thật |
| **AC2** | Kịch bản sự cố dàn dựng: nạp tải tổng hợp, `docker stop` ClickHouse giữa chừng, bật lại → **0 dòng mất** (số nạp = số trong kho), RAM tiến trình không vượt ngân sách trong suốt sự cố |
| **AC3** | Một phiên thật với `--measure` song song: đối chứng `d[]` khớp **tuyệt đối** mọi bảng trong cửa sổ chung; mọi khoản trừ là số đếm được, không có "chênh nhỏ chấp nhận được" |
| **AC4** | N, K, trần đĩa nằm trong code kèm căn cứ đo; hai phép kiểm §6 có kết quả ghi lại |

**Phác seam test cho plan** *(chốt cùng plan theo §4.5 CLAUDE.md; client CH là tham số inject sẵn — giả lập sự cố không cần vá code)*: (1) block → file → load → bằng tuyệt đối, Decimal/datetime giữ nguyên · (2) `.tmp` mồ côi bỏ + đếm · (3) vượt N khi client hỏng → file xuất hiện; client hồi mà đĩa chưa rỗng → block mới vẫn xuống đĩa · (4) thứ tự insert cuối = thứ tự sinh (FIFO xuyên RAM–đĩa) · (5) ≤ K block đĩa/nhịp · (6) insert fail → file còn nguyên · (7) dòng độc chế độ đĩa: cô lập, phần lành vào kho, file mới biến mất · (8) khởi động có `.blk` sót → tự phát lại, thư mục sạch · (9) chạm trần đĩa → bỏ mới có đếm, file cũ nguyên · (10) golden test `d[]`: file đo cố định nhỏ → số kỳ vọng **giải tay** (literal độc lập, không tính lại bằng code — luật chống tautological §4.5).

## 10. Ngoài phạm vi *(phân loại theo CLAUDE.md §1.4)*

| Mục | Loại | Lý do |
|---|---|---|
| Nén biểu diễn hàng đợi RAM (brief §5-C) | Loại có chủ đích | Nhân thêm biên chứ không đặt trần — chỉ cân nhắc nếu số đo N cho thấy ngân sách RAM quá chật |
| WAL toàn phần (mọi block qua đĩa trước) | Loại có chủ đích | Nhịp flush 1 s × 5 bảng sinh hàng chục nghìn file nhỏ/ngày, thêm I/O hot path suốt phiên cho một sự cố hiếm — brainstorm 2026-08-27 |
| Trần cứng + bỏ dòng cũ (brief §5-B) | Loại có chủ đích | Chủ dự án loại: không đạt "không mất dòng nào" |
| Backpressure lên nguồn BVSC | Đã kiểm — không có | Socket đẩy một chiều, nguồn không chậm lại vì ta |
| Giới hạn số kết nối BVSC (2 socket song song) | Chưa đo, không chặn | Roadmap §2.1 đã ghi — không thuộc lát này |
| Sửa đường đọc/API trên `rt.*` | Loại có chủ đích | Không liên quan chế độ hỏng đang vá |

## 11. Checklist tài liệu khi lát xong

- [ ] [market-data-store §3.7](../../../20-design/market-data-store.md) — hợp đồng ghi: bổ sung chế độ đĩa (retry không hạn chót thời gian khi có spill, FIFO, tiết lưu K).
- [ ] [service-topology §7b](../../../20-design/service-topology.md) — ngân sách đĩa: dòng vùng spill (trần + con số đo).
- [ ] [roadmap](../../../00-overview/roadmap.md) — mục lát này + gỡ ⚠️ "chưa làm xong ngày nào thì ngày đó vẫn hở" ở §2.1.
- [ ] Ghi kết quả hai phép kiểm một-lần vào ngay §6 spec này (ranh giới sửa spec sau khi duyệt: chỉ thêm kết quả đo, không đổi thiết kế).
