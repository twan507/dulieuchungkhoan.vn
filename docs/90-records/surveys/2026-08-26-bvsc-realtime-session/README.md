# Phiên đo realtime BVSC — 2026-08-26 (phiên chiều)

**Ngày đo:** 2026-08-26, **12:56:37 → 15:09:59** (8.002 giây, phiên chiều trọn vẹn kể cả ATC/PLO — **không phủ phiên sáng**) · **Công cụ:** chính `ingester --measure` của dự án (không phải script dùng-một-lần) · **Quy mô:** 6.322 topic (2.007 mã cổ phiếu/ETF × 3 + 15 chỉ số + 3 sàn `ptm` + 20 topic × 14 mã phái sinh + `pth` 3 sàn), **2.316.573 frame**, 52 MB gzip.

**Dữ liệu thô:** `D:\twan_projects\dlck-runtime\measure\20260826\frames-*.jsonl.gz` (ngoài repo — quá lớn để commit). **Báo cáo đầy đủ:** [`analysis.md`](analysis.md) · **Script:** [`analyze_measure.py`](analyze_measure.py) · [`analyze_sm_floor.py`](analyze_sm_floor.py).

---

## 1. Phát hiện quan trọng nhất — frame thật có VỎ BỌC

```
42["t",{"a":"i","d":[ {…bản ghi thật…} ]}]
```

Tài liệu nguồn [`11-bvsc-realtime.md`](../../../10-sources/market/11-bvsc-realtime.md) §4–§8 **chỉ chép bản ghi bên trong**. Bản ghi thật nằm trong **mảng `d`**, kèm cờ `a` của lớp vận chuyển (`u` = update · `i` = insert).

🔴 **Hệ quả:** code chuẩn hoá viết theo tài liệu sẽ **từ chối mọi frame thật** (không thấy `SB`). Bắt được đúng nhờ nguyên tắc "đo trước, ghi sau" — nếu bật ghi thật ngay thì cả phiên đầu tiên mất trắng mà log chỉ báo `normalize_error`. Đã sửa: `records_of()` bóc vỏ, mỗi phần tử `d` là một dòng (commit `c88cda2`).

*Đo được: `len(d) == 1` ở toàn bộ 2,3 triệu frame — nhưng code vẫn duyệt mảng để một packet nhiều bản ghi không rơi im lặng.*

## 2. Tính chất `SM` — điều kiện tiên quyết của gate, ĐÃ TRẢ LỜI

| Câu hỏi | Kết quả đo |
|---|---|
| Duy nhất trong (mã, giây)? | ✅ **0 trùng** trên 130.869 bản ghi `t` |
| Duy nhất trong (mã, cả phiên)? | ✅ **0/813 mã** có SM lặp |
| Đơn điệu tăng theo mã? | ✅ **0 lần giảm** trên 130.056 lần chuyển tiếp |
| Bộ đếm toàn sở hay theo mã? | **Theo SÀN** — HOSE 983.574–1.994.673 · HNX 61.759–139.524 · UPCOM 53.578–90.588 · phái sinh (XHNF) 549.578–1.029.317 |
| Bao nhiêu chỗ thứ tự SM thật sự quyết định `o`/`c` của nến? | **18,13%** số cặp (mã, giây) có ≥2 lệnh khớp (17.200/94.869) |

**Hệ quả thiết kế:** giả định "chưa đo" của [spec ClickHouse §4.1](../../plans/2026-08-25-clickhouse-realtime-store/spec.md) nay **đã đo và đứng vững** — khoá `argMin/argMax (ts, seq, received_at)` hợp lệ, và dedup theo SM *về nguyên tắc* dùng được. Lưới dedup hiện tại (hash nội dung) **giữ nguyên**: nó không cần giả định nào về SM và đúng cho cả 5 topic, trong khi SM chỉ có ở `t`.

## 3. Phái sinh — KHÔNG có kênh riêng

Trong 2,3 triệu frame, **đúng 5 tên sự kiện** xuất hiện: `i` · `o` · `t` · `idx` · `ptm`. 15 topic còn lại của bảng hằng số (kể cả toàn bộ tổ hợp 20 topic × 14 mã phái sinh) **không đẩy frame nào**.

**Phái sinh đi chung `i`/`o`/`t` với cổ phiếu**, phân biệt bằng `EX = "XHNF"`; cấu trúc trường **giống hệt** (0 trường thừa/thiếu); **không có trường `openInterest`** ở luồng realtime. Thanh khoản dồn vào `41I1G9000` (VN30F1M): 24.162 bản ghi `t` — nhiều hơn mọi mã cổ phiếu.

⚠️ Mã phái sinh **không có trong `/quotes`** nên danh mục runtime hiện tại (lọc `StockType` của `/quotes`) **không đăng ký chúng** — muốn thu phái sinh phải mở rộng danh mục, là quyết định riêng.

## 4. `pth` — lần đo thứ hai, vẫn 0 frame

Đăng ký cả 3 sàn suốt 2 giờ 13 phút: **0 frame**. Cộng với ~6 phút của đợt đo 2026-08-15 ⇒ hai lần đo độc lập đều trống. Vẫn **chưa đủ để tuyên "không có"** (có thể kênh chỉ sống khi có lệnh chào), nhưng đủ để **không đưa vào phạm vi**.

## 5. Trường lạ — bộ trường của nguồn KHÔNG đóng

| Sự kiện | Khoá ngoài tài liệu | Ghi chú |
|---|---|---|
| `i` | **`OP`** · **`LO`** · `TSI` | `OP`/`LO` là giá mở cửa/thấp nhất phiên — **trái với ghi chú cũ** rằng `open`/`low` không được đẩy. `TSI` quan sát giá trị `"OPEN"`, chỉ thấy ở mã phái sinh |
| `idx` | `IC` · `MS` · `NOF` | `IC` = `"up"` (khớp dấu `ICH`); `MS`, `NOF` **chưa xác định ý nghĩa** — không suy đoán |
| `t`, `o` | **không có** | Bộ trường khớp tài liệu tuyệt đối — tính đóng của `t`/`o` được củng cố (chấp nhận có ý thức ở spec §5.6 nay có bằng chứng) |

Ba khoá lạ của `i` và ba của `idx` hiện **rơi vào cột `extra`** (JSON) — không mất dữ liệu. Nâng `OP`/`LO` thành cột là một migration riêng, **chưa làm** trong lát này.

## 6. Chất lượng dữ liệu

- `CV` và `P1` **luôn bằng nhau** trên 111.493 frame có cả hai — xác nhận ghi chú cũ.
- **Chuỗi rỗng** ở `B1`/`S1` của `i`: 615/519.133 frame (**0,12%**) — nghĩa là "tạm không có dư mua/bán bậc 1", **không phải lỗi**. Đã sửa cổng chuẩn hoá: rỗng → `NULL`, không đầu độc block.
- Mọi trường số khác parse `Decimal` thành công 100%.

## 7. Tải thật

| Đại lượng | Đo được |
|---|---|
| Tổng frame phiên chiều | **2.316.573** (`o` 1.647.375 · `i` 519.133 · `t` 130.869 · `idx` 17.770 · `ptm` 1.426) |
| Trung bình | **289,5 frame/giây** |
| Đỉnh theo phút | **704,8 frame/giây** lúc 13:00 (mở lại sau nghỉ trưa) |
| Ước lượng thô cả ngày (×2, **chưa đo phiên sáng**) | **~4,6 triệu dòng/ngày** |

So với dải ước lượng **5–35 triệu dòng/ngày** của [spec ClickHouse §10](../../plans/2026-08-25-clickhouse-realtime-store/spec.md): con số thật nằm **ngay dưới cận dưới** — tức thiết kế TTL/dung lượng **thoải mái hơn dự kiến**. Chưa đo phiên sáng (có ATO) nên số thật nhiều khả năng cao hơn 4,6 triệu; vẫn cùng bậc độ lớn.

## 8. Giờ đẩy dữ liệu

`idx` 12:56 → **15:05** · `i`/`o` 12:59 → 15:04 · `t` 12:59 → 14:59 · `ptm` 12:59 → 14:56. ⚠️ Mốc "sớm nhất" bị chặn bởi giờ bắt đầu capture — **không phải** giờ topic bắt đầu đẩy. Mốc muộn nhất (15:05) xác nhận cửa sổ dừng 15:05 của ingester là hợp lý.

## 9. Còn để ngỏ sau phiên đo này

| Câu hỏi | Vì sao chưa trả lời được |
|---|---|
| Phiên sáng + ATO | Capture bắt đầu 12:56 — cần một phiên đo **trọn ngày** (08:40–15:05) |
| Giờ sớm nhất `idx`/`t` thật sự đẩy | Cùng lý do trên |
| Ý nghĩa `MS`, `NOF` (idx) · `TSI` (i) | Không có tài liệu đối chiếu; chỉ ghi nhận giá trị quan sát |
| Có nên thu phái sinh không | Đã biết **thu được**; quyết định phạm vi + lược đồ là việc riêng |
| Có nên nâng `OP`/`LO` thành cột | Cần một migration ClickHouse mới |

---

## 10. Dung lượng ClickHouse — đo thật *(2026-08-26 tối, phục vụ quyết định TTL)*

Nạp **toàn bộ 2.316.573 record** của phiên chiều qua **đúng đường ghi production** (`parse_packet` → `records_of` → `symbol_of` + `Stamper` → `normalize`) vào database tạm `measure_tmp` dựng từ chính DDL `0002_rt_schema.sql`, `OPTIMIZE FINAL`, đo `system.parts`, rồi `DROP DATABASE`. Script: [`measure_size.py`](measure_size.py) · số liệu thô: [`size-measurement-raw.json`](size-measurement-raw.json).

> ✅ **Kết quả phụ quan trọng: 2.316.573 record chuẩn hoá, `normalize_error = 0`, `no_symbol = 0`.** Đường ghi production chạy đúng đầu-cuối trên dữ liệu thật — bằng chứng bản sửa vỏ bọc sails.io (§1) là đủ. Số dòng insert khớp `system.parts` từng bảng ⇒ không mất dòng.

| Bảng | Số dòng | Nén | B nén/dòng | Tỷ lệ nén |
|---|---:|---:|---:|---:|
| `quote` | 1.647.375 | 23,3 MiB | 14,8 | 4,6× |
| `snapshot_delta` | 519.133 | 17,9 MiB | 36,1 | 8,2× |
| `trade` | 130.869 | 3,7 MiB | 29,3 | 2,1× |
| `index_delta` | 17.770 | 0,8 MiB | 48,5 | 2,5× |
| `pt_match` | 1.426 | 0,03 MiB | 23,5 | 6,2× |
| **Tổng frame thô / phiên chiều** | **2.316.573** | **45,7 MiB** | | |
| `bar_1m` | 18.648 | 0,95 MiB | 53,7 | 2,3× |
| `index_bar_1m` | 1.594 | 0,07 MiB | 45,6 | 2,1× |

**Quy đổi** *(hệ số ×2 cho cả ngày — phiên sáng CHƯA ĐO; 21 phiên/tháng)*: frame thô **~91 MiB/ngày** ⇒ 1,9 GiB/tháng ⇒ **TTL 3 tháng ≈ 5,6–7,5 GiB** (cửa sổ thật 3–4 tháng) · TTL 6 tháng ≈ 11,2 GiB · TTL 12 tháng ≈ 22,5 GiB. Nến vĩnh viễn **~0,5 GiB/năm**.

**Đối chiếu ước lượng cũ ([spec ClickHouse §10](../../plans/2026-08-25-clickhouse-realtime-store/spec.md))** — thực tế nằm ở **đáy mọi dải**:

| Đại lượng | Ước lượng cũ | Đo thật | |
|---|---|---|---|
| Dòng/ngày | 5–35 triệu | ~4,6 triệu | dưới cận dưới |
| MB/ngày | 50–500 MB | ~91 MiB | đáy dải |
| Cửa sổ 3–4 tháng | 5–60 GB | ~6–8 GiB | nhỏ hơn kịch bản xấu 8× |
| Nến/ngày | 200–540k | **~37k** | nhỏ hơn 5–14× |
| Nến/năm | ~4 GB | ~0,5 GiB | nhỏ hơn 8× |

Nến ít hơn nhiều vì chỉ ~800 mã thật sự có khớp lệnh, và mỗi mã chỉ sinh nến ở phút có giao dịch — không phải 2.000 mã × 250 phút.

**Hệ quả cho quyết định TTL:** dung lượng **không còn là ràng buộc** (cả năm frame thô ~25 GB; ổ D còn 116 GB trống). Ràng buộc thật của cửa sổ là *thời gian tối đa để phát hiện và vá lỗi gom nến* — vá được chỉ khi `trade` còn trong cửa sổ. Chờ chủ dự án chốt giữ 3 tháng hay nới 6 tháng.
