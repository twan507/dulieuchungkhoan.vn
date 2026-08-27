# Brief — hàng đợi ghi có trần, tràn ra đĩa, không mất dòng nào

**Ngày ghi:** 2026-08-27 (cuối phiên) · **Trạng thái:** chưa bắt đầu, chờ phiên sau · **Quyết định chủ dự án:** làm thành **lát riêng**, đi đủ chuỗi brainstorm → spec → plan (§4.1).

> Đây **chưa phải spec**. Đây là hồ sơ số đo + phân tích chế độ hỏng, để phiên sau không phải đo lại. Spec viết ở `spec.md` cùng thư mục.

---

## 1. Vì sao có lát này

Chủ dự án nêu, sau phiên ghi thật đầu tiên 2026-08-27:

> *"phiên nay ko thể gọi là trần cứng đc, thanh khoản thấp, trong quá khứ có rất nhiều phiên đỉnh ATO cao hơn nhiều, bạn thiết kế cần có hệ số an toàn, trần có thể ok nhưng cơ chế xếp hàng cần thiết kế cẩn thận để ko mất dòng nào."*

Đọc lại code thì lo ngại đó **có cơ sở, và chỗ hở nghiêm trọng hơn chuyện trần bộ nhớ**.

---

## 2. Chế độ hỏng — chính xác

`ChWriter.pending` là `dict[str, deque]` **không trần, không backpressure, không metric độ sâu** ([chwriter.py](../../../../backend/ingester/chwriter.py)).

Hàng đợi **không nguy hiểm khi ClickHouse khoẻ** — `flush_once` xả sạch trong vòng một nhịp. Nó chỉ phình đúng lúc **ClickHouse trục trặc**: `RETRY_BUDGET_S = 60` là 60 giây writer kiên nhẫn thử lại, và **suốt 60 giây đó không gì chặn hàng đợi lớn lên**.

🔴 **Chế độ hỏng thật là GIAO của hai sự kiện:** ATO thanh khoản cao **cùng lúc** ClickHouse hiccup.

Hậu quả khi trúng: tiến trình vượt ngân sách RAM → OOM → **mất sạch cả `buffers` lẫn `pending`**, **không counter nào ghi lại**, leader lock rơi, standby tiếp quản nhưng dữ liệu trong bộ nhớ đã đi. Đây là đường mất dòng **lớn nhất và im lặng nhất** — lớn hơn `dropped_block` (đường này có trần, có đếm, có log).

**Vì sao hôm nay không thấy:** `block_cap` chỉ đếm lúc *cắt* block, không nói hàng đợi *đang* sâu bao nhiêu. Sẽ không ai thấy nó dâng cho tới lúc tiến trình chết.

---

## 3. Số đo — phiên 2026-08-27 (thanh khoản THẤP)

⚠️ **Đọc bảng này như SÀN, không phải trần.** Chủ dự án xác nhận lịch sử có nhiều phiên ATO cao hơn nhiều. Mọi thiết kế phải nhân hệ số an toàn lên trên các số này.

### 3.1 Lưu lượng

| | Dòng/giây |
|---|---|
| Trung bình cả phiên | **139** |
| **Đỉnh một giây** — 09:00:13, ATO | **6.496** |
| Tỷ lệ đỉnh/trung bình | **47×** |

Năm giây cao nhất đều nằm trong phút 09:00 (ATO): 6.496 · 5.834 · 4.916 · 4.194 · 3.724. Phút cao nhất: 09:00 với 62.062 dòng.

### 3.2 Chi phí bộ nhớ của hàng đợi

**497 byte/dòng** khi nằm trong `pending` *(đo bằng `sys.getsizeof` đệ quy trên 5.000 dòng `rt.quote` thật — 1 block = 2,4 MB)*.

| Kịch bản | Đỉnh | Xếp hàng trọn 60 s |
|---|---|---|
| Hôm nay (thanh khoản thấp) | 6.496/s | **185 MB** |
| Giả định 3× | 19.488/s | **555 MB** |
| Giả định 5× | 32.480/s | **924 MB** |

Ngân sách ingester trên VPS là **200 MB** ([service-topology §7b](../../../20-design/service-topology.md)) ⇒ **kịch bản 3× đã vượt gần 3 lần**.

### 3.3 Bối cảnh phiên

`reconcile: p1=0 p2=0 ok=868` · 4,27 triệu dòng / 82,2 MB · `block_cap.quote` chạm **đúng một lần lúc 09:00:14** · **0** `dropped_block` · **0** `poison_row` · **0** `normalize_error`.

Tức **cơ chế hiện tại chạy đúng trong phiên nhẹ** — vấn đề là biên, không phải lỗi.

---

## 4. Việc phải ĐO trong lát này (chưa có số)

🔴 **Tốc độ xả thật của `flush_once`** — bao nhiêu block/giây, và INSERT 5.000 dòng mất bao lâu.

Không có số này thì **không đặt được ngưỡng tràn**: ngưỡng phải là hàm của (tốc độ nạp − tốc độ xả) × thời gian chịu đựng. Hiện đang thiếu vế thứ hai.

Cách đo đề xuất: bọc `_write_block` bằng đồng hồ, ghi p50/p95/p99 vào `Metrics`, chạy một phiên. Hoặc đo offline: phát lại một block thật vào ClickHouse dev N lần.

Đo thêm, cùng lượt:
- Độ sâu `pending` theo thời gian trong một phiên thật (cần metric ở §5.1).
- Đỉnh có đổi không khi ClickHouse chạy dưới **hồ sơ VPS hẹp** (cache 256 MiB) — số 1,18 GiB đỉnh đo trên dev nơi cache được cấp 5 GiB.

---

## 5. Ba hướng đã cân — chủ dự án chốt A

### A · Tràn ra đĩa ✅ **CHỐT**

Vượt ngưỡng N block thì serialize block ra đĩa cục bộ, phát lại khi ClickHouse hồi. Bộ nhớ có trần cứng, đĩa 60 GB làm vùng đệm.

**Là hướng duy nhất giữ được lời hứa "không mất dòng nào"** — RAM hữu hạn, còn nguồn thì không chậm lại vì ta.

Điểm phải thiết kế cẩn thận (để spec trả lời):
- Định dạng tràn — tái dùng khuôn `MeasureWriter` (JSONL gzip) hay nhị phân gọn hơn?
- Thứ tự phát lại: đĩa trước hay bộ nhớ trước? *(Ảnh hưởng cửa sổ dedup ~100 s của ClickHouse — xem [spec CH §5.5](../2026-08-25-clickhouse-realtime-store/spec.md).)*
- Tràn có phá **dedup theo hash block** không? Nếu block ra đĩa rồi phát lại nguyên vẹn thì hash không đổi ⇒ vẫn dedup được. **Phải kiểm, không suy.**
- Trần đĩa và chính sách khi đĩa cũng đầy — đường thoát cuối cùng là gì.
- Phát lại vào lúc nào: trong phiên khi CH hồi, hay sau phiên? Phát lại giữa phiên có làm ngộp thêm không?
- Crash giữa lúc tràn: file dở dang xử thế nào.

### B · Trần cứng + bỏ dòng cũ nhất, có đếm

Bộ nhớ an toàn, mất dòng nhưng *thấy được*. **Không đạt yêu cầu** chủ dự án đặt ra. Ghi lại để không ai đề xuất lại.

### C · Nén biểu diễn hàng đợi

497 B/dòng phần lớn là overhead list Python; gói theo cột (mảng) cắt được 3–5 lần. **Nhân thêm biên chứ không đặt trần** — đi kèm A, không thay A. Cân nhắc trong spec như tối ưu tuỳ chọn.

### 5.1 Việc rẻ nên làm TRƯỚC, ngay đầu lát

**Metric độ sâu `pending` + ngưỡng cảnh báo.** Không thấy thì không quản được. Rẻ, không đụng đường dữ liệu, và là thứ biến giả định ở §3.2 thành số thật.

Nên là task đầu tiên của plan, để các phiên sau đó tự sinh dữ liệu cho việc chọn ngưỡng.

### 5.2 Lưới an toàn có ngay, chi phí gần bằng không

Chế độ `--measure` **đã ghi mọi frame thô ra JSONL gzip** (~52 MB/nửa phiên). Cho nó chạy **thường trực song song** phiên ghi là có sẵn bản sao thô để dựng lại nếu đường ghi mất dòng.

Không thay được tràn-ra-đĩa (bản thô chưa chuẩn hoá, dựng lại là việc thủ công), nhưng là bảo hiểm **có ngay hôm nay**. Cân nhắc bật trong lúc chờ lát này xong.

---

## 6. Nguyên tắc thiết kế chủ dự án đặt ra

1. **Hệ số an toàn trên số đo, không lấy số đo làm trần.** Phiên đo được là phiên nhẹ.
2. **Không mất dòng nào** — đây là tiêu chí nghiệm thu, không phải mong muốn.
3. Trần bộ nhớ thì "có thể ok"; **cơ chế xếp hàng mới là chỗ phải thiết kế cẩn thận**.

---

## 7. Liên quan

- [service-topology §7b](../../../20-design/service-topology.md) — ngân sách VPS, và đính chính "427 MB là đầu phiên không phải đỉnh"
- [market-data-store §3.7](../../../20-design/market-data-store.md) — hợp đồng ghi ClickHouse hiện hành (phân loại lỗi, ngân sách retry, hạn chót chung)
- [`deploy/infra/docker-compose.vps.yml`](../../../../deploy/infra/docker-compose.vps.yml) — trần cứng/mềm, ngân sách từng service
- [ledger lát ingester](../2026-08-26-ingester-omo-first-slice/ledger.md) — lịch sử các lỗi đường ghi đã sửa
