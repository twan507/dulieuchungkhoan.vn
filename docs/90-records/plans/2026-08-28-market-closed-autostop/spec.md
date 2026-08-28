# Spec — Tự ngắt khi phát hiện ngày thị trường không mở

> 🟡 **CHƯA DUYỆT.** Viết 2026-08-28 để đó, chưa thực thi. §4.1 đòi spec được người dùng duyệt trước khi có dòng code nào. Hai lựa chọn ở §5 là **đề xuất**, chưa chốt.

## 1. Vấn đề

`dlck-ingester` trigger **Weekly Thứ 2–6**. Cuối tuần không khởi động — đúng và đủ, **giữ nguyên**. Nhưng **ngày nghỉ lễ VN rơi vào Thứ 2–6 thì task vẫn nổ**: nối socket, đăng ký 6.364 topic, ngồi im **6,5 tiếng**, rồi thoát lúc 15:05 với đối chứng rỗng.

Vòng chạy hiện tại không có phép phát hiện nào — `backend/ingester/main.py:598` là thuần `while datetime.now(TZ) < deadline`.

Hại trực tiếp thì nhỏ (một tiến trình ngồi không, một bản đo rỗng). Cái đáng sửa là **nó làm hỏng mọi phép cảnh báo sau này**: khi có chuông *"hôm nay không có dữ liệu = sự cố"*, ngày lễ sẽ kêu oan — và chuông kêu oan vài lần là chuông bị tắt.

**Vì sao không dùng lịch nghỉ công bố trước:** phải bảo trì tay mỗi năm, và lịch hoán đổi được công bố sát ngày. Quên cập nhật một lần là quay về đúng hành vi hiện tại. Cơ chế tự phát hiện **không cần biết trước**, và bắt được cả ca không ai công bố (sàn dừng đột xuất).

## 2. Dữ kiện đã đo vs giả định *(§4.8 bước 0 — bắt buộc)*

### Đã đo — 2026-08-28 19:16, socket thật, ngoài giờ giao dịch

| | `Ack` | `Control` | Frame dữ liệu |
|---|---|---|---|
| Phiên giao dịch 28/08 | 64 | 959 / ~390 phút ≈ **2,46/phút** | **4.722.406** |
| **Ngoài giờ, cùng ngày** | **64** | **2/phút** *(phút 1: 2 · phút 2: 4)* | **0** |

Đã ghi vào tầng reference: [`11-bvsc-realtime.md §1.6`](../../../10-sources/market/11-bvsc-realtime.md).

### Giả định — CHƯA kiểm, phải biết mình đang đứng trên gì

1. 🔴 **Nhịp `Control` giữ nguyên trong ngày nghỉ lễ thật.** Phép đo trên chạy ngoài giờ của một *ngày giao dịch*. Lập luận: `Control` là nhịp tim của tầng vận chuyển, không phải của phiên. Hợp lý, **chưa kiểm** — và AC3 biến nó thành cổng chặn.
2. 🔴 **Hàng "socket hỏng ⇒ `Control` = 0" là SUY RA, không phải đo.** Hiển nhiên với socket chết hẳn, nhưng các ca lưng chừng **chưa kiểm**: proxy giữ kết nối mở mà không chuyển tiếp gì · server còn TCP nhưng ngừng phát · route hỏng giữa phiên. Nếu tồn tại ca *"kết nối chết mà `Control` vẫn về"* thì vế 2 của điều kiện ngắt **thủng**.
3. Thị trường mở thì frame dữ liệu chắc chắn xuất hiện trước mốc `T`. Đúng với ATO bình thường; **chưa xét** phiên mở muộn do sự cố sàn.

## 3. Phạm vi

**Trong:** thêm phép phát hiện + lối thoát sớm cho chế độ `run` của `python -m ingester`.

**Ngoài** *(phân loại theo §1.4)*:

| Mục | Loại | Lý do |
|---|---|---|
| Bảng lịch nghỉ công bố trước | Loại có chủ đích | Chính thứ spec này thay thế — xem §1 |
| Cho `etl refdata` / OMO biết ngày nghỉ | Loại có chủ đích | Chúng chạy **08:00**, trước khi có tín hiệu nào để đọc. Ngày nghỉ chúng vẫn chạy và vô hại về dữ liệu — nhưng **vẫn tick bộ đếm vắng danh bạ**, nên [luật huỷ niêm yết](../2026-08-28-catalog-delisting-rule/plan.md) phải tự giải bài toán ngày nghỉ của nó; spec này không gánh hộ |
| Ngày giao dịch **nhìn lại** (`DISTINCT trading_date`) | Đã có đường khác | Nguồn đã chốt ở [step-04-macro §F8](../2026-08-25-postgres-data-schema/step-04-macro.md). Nó trả lời *"D có phải ngày giao dịch"* sau khi D qua — **không** trả lời được *"sáng nay có nên chạy"* |
| Ngắt giữa phiên khi sàn tạm dừng | Loại có chủ đích | Tạm dừng giữa phiên thì phải **giữ kết nối**, không phải thoát |

## 4. Thiết kế — điều kiện ngắt

Ba vế, **thiếu một vế là chạy tiếp**:

```
1. đã nhận đủ Ack cho mọi lô đăng ký            → server CÓ tiếp nhận mình
2. Control frame gần nhất cách đây < 5 phút     → đường truyền còn sống NGAY LÚC NÀY
3. 0 frame dữ liệu kể từ lúc nối, VÀ đã qua T   → thị trường không đẩy gì
```

🔴 **Hướng an toàn lệch hẳn một phía.** Ngắt nhầm một phiên mở cửa = **mất tick vĩnh viễn**, thứ duy nhất trong hệ thống không backfill được. Chạy thừa một ngày nghỉ = một tiến trình ngồi không. Hai hậu quả lệch nhau hàng nghìn lần ⇒ **vế 1 và 2 tồn tại chỉ để NGĂN ngắt**, không phải để ngắt. Nghi ngờ thì chạy tiếp.

Thoát bằng **exit 0** kèm dòng log cấu trúc riêng và counter riêng (`market_closed_detected`) — phải phân biệt được với crash trong mọi phép đọc log về sau.

## 5. Hai lựa chọn cần chốt *(đề xuất, chưa duyệt)*

### ① Mốc `T`

**Đề xuất: 09:15 giờ tường.** Ingester khởi động 08:30 · phái sinh mở 08:45 · cơ sở ATO 09:00 ⇒ trễ 30 phút sau mốc dữ liệu sớm nhất. Dùng **giờ tường** chứ không phải *"T phút sau khi nối"*, để job khởi động trễ không kéo mốc theo.

### ② `--measure` có ngắt theo không?

**Đề xuất: KHÔNG — chỉ `run` ngắt, `measure` chạy tiếp tới 15:10 như hiện nay.**

Bản đo tồn tại đúng để làm **nhân chứng độc lập**. Nếu cơ chế phán đoán sai và hôm đó thị trường **có** mở, `run` đã thoát nhưng `measure` vẫn bắt trọn frame thô ⇒ phiên **dựng lại được**. Cho cả hai cùng ngắt là bỏ đúng cái lưới đỡ vào đúng lúc cần nó nhất. Giá phải trả: một tiến trình **13 MB** ngồi không mỗi ngày nghỉ.

## 6. Seam test *(chốt cùng plan)*

1. Đủ ba vế ⇒ thoát, exit 0, counter `market_closed_detected == 1`.
2. **Ranh giới ngược quan trọng nhất:** `Control` im (vế 2 hỏng) + 0 dữ liệu + đã qua `T` ⇒ **KHÔNG thoát**, chạy tiếp tới 15:05. Đây là ca *"mất mạng sáng sớm"* — test này là thứ ngăn cơ chế nuốt mất một phiên.
3. Chưa đủ `Ack` (vế 1 hỏng) + 0 dữ liệu + đã qua `T` ⇒ không thoát.
4. Có **đúng một** frame dữ liệu trước `T` ⇒ không thoát *(vế 3 là "không frame nào", không phải "ít frame")*.
5. Chưa tới `T`, mọi thứ im ⇒ không thoát.
6. Frame dữ liệu về **sau** khi đã qua `T` nhưng **trước** khi kịp thoát ⇒ không thoát.
7. `measure` với đúng đầu vào của ca 1 ⇒ **vẫn chạy tiếp** *(quyết định ②)*.

Đồng hồ phải tiêm được (fake clock) — không test nào được đốt thời gian thật.

## 7. Tiêu chí nghiệm thu

| AC | Nội dung |
|---|---|
| **AC1** | 7 seam test §6 xanh, mỗi test assert giá trị cụ thể *(§4.5.4)* |
| **AC2** | Chạy `--minutes 3` ngoài giờ trên socket THẬT ⇒ ba vế đủ, thoát exit 0. Dán log nguyên văn |
| **AC3** | 🔴 **Cổng chặn: giả định §2.1 phải được kiểm trong một ngày nghỉ lễ THẬT trước khi bật cơ chế trên `dlck-ingester`.** Chạy `--measure` ngày lễ, xác nhận `Control` vẫn về. Chưa có phép đo này thì **không bật** |

## 8. Rủi ro đã biết

- **Ca xấu nhất là im lặng.** Cơ chế hỏng theo kiểu ngắt nhầm sẽ không kêu — chỉ mất một phiên, và chỉ lộ ra khi có người đi tìm dữ liệu ngày đó. Đối trọng duy nhất là quyết định ②: giữ `measure` chạy nên vẫn còn frame thô để dựng lại.
- **Giả định §2.2 chưa kiểm.** Nếu tồn tại ca *"kết nối chết mà `Control` vẫn về"*, vế 2 vô dụng. Phải nghĩ ra phép thử cho nó khi viết plan.
