# Quyết định §4.8 — gộp bao nhiêu của 15 họ job trước lát 12

**Ngày:** 2026-09-08 · **Bối cảnh:** vòng review 3 để lại 6 nợ chuẩn hoá; chủ dự án chốt *"bốn mục refactor đi qua §4.8, đừng tiện tay gộp"*. Đây là hồ sơ đó.

**Vì sao là quyết định khó đảo:** đụng **ranh giới module** của 15 họ job — §4.8 liệt kê đúng loại này. Gộp sai thì mỗi lát sau phải chịu một khuôn không ai thiết kế.

---

## Bước 0 — dữ kiện đã kiểm vs giả định *(bắt buộc, §4.8)*

### Đã kiểm bằng lệnh (2026-09-08)

| Sự thật | Cách đo |
|---|---|
| `GuardRefused` định nghĩa **6 lần**, đúng **2 hình dạng** | `grep -A3 "class GuardRefused" *_job.py` |
| Hình dạng `verdict` có **4 bản, thân giống hệt nhau** (`events` `fundamentals` `price` `snapshot`) | so từng dòng |
| Hình dạng `reasons` có **2 bản** (`refdata` `screener`), cũng giống hệt nhau | nt |
| 🔴 **`Fetcher` KHÔNG trùng ba bản** — `price` **91 dòng**, `snapshot`/`fundamentals` **36 dòng** | `ast` lấy đúng span lớp |
| `snapshot` ↔ `fundamentals`: **31/36 dòng giống hệt** | `difflib.ndiff` |
| `price` ↔ `snapshot`: chỉ **16/91 dòng** giống | nt |
| `MAX_BAD_SHAPE` (2 file) và `MAX_SHAPE` (2 file) cùng giá trị `0.05` | `grep` |
| `omo_store.store()` kiểm tồn tại bằng `SELECT` rồi mới `INSERT`; `macro.omo_session` **không có UNIQUE** trên `session_date` | đọc `omo_store.py` + migration `0005` |

🔴 **Một mục của báo cáo R4 sai khi đo lại:** R4 viết *"`class Fetcher` lặp lại gần như nguyên văn ở `price`/`snapshot`/`fundamentals`"*. Thật ra `price_fetch.Fetcher` có cầu chì `SourceDown`, `CodeInvalid`, nghỉ-rồi-thử-lại — **gần gấp ba số dòng và khác hẳn**. Trùng lặp thật là **hai** bản, không phải ba. Con số này đổi hẳn phép tính lợi/hại bên dưới.

### Giả định — chưa kiểm

- Rằng bốn bản `GuardRefused` hình dạng `verdict` sẽ **mãi** giống nhau. Chưa có gì bảo đảm; mỗi họ có thể cần trường riêng về sau.
- Rằng gộp `Fetcher` của `snapshot`+`fundamentals` không làm hỏng ca biên nào — **hai họ này có `Tally` khác nhau**, chưa đọc hết đường dùng.
- Rằng chưa có dòng `omo_session` trùng trong kho production. **Không kiểm được ở đây** (không đụng kho thật); lát 13 phải kiểm trước khi thêm ràng buộc.

---

## Ba phương án

Mỗi phương án tối ưu **một trục khác nhau** và tự khai rủi ro của chính nó.

### P1 — Chỉ ghi lý do, không gộp dòng nào *(tối ưu: bán kính hỏng = 0)*

Thêm comment đối chiếu chéo ở mọi chỗ lệch; giữ nguyên mã.

- **Được:** không rủi ro hồi quy. Làm xong trong một lượt. Lát 12 (container) không phụ thuộc gì vào việc này.
- **Mất:** 6 bản `GuardRefused` vẫn trôi độc lập; lát sau thêm họ thứ 16 là bản thứ 7.
- **Tự khai rủi ro:** comment không thi hành được. Đúng bệnh mà cả ba vòng audit vừa rồi chứng minh: **luật không có phép kiểm thì không ai theo**.

### P2 — Gộp đúng chỗ đã đo là trùng, kèm phép kiểm *(tối ưu: giá trị/rủi ro)*

1. Một `GuardRefused` duy nhất ở `etl/guard_common.py`, mang **cả** `verdict` lẫn `reasons` (`reasons` suy từ `verdict` khi có) — 6 job import, xoá 6 định nghĩa.
2. Đổi `MAX_BAD_SHAPE` → `MAX_SHAPE` cho khớp 4/4 file.
3. **Không** đụng `Fetcher`: chỉ 2 bản trùng thật, và cả hai đang được test riêng phủ kín.
4. Thêm test hợp đồng: *"không `*_job.py` nào được tự định nghĩa `GuardRefused`"* — khuôn đúng bằng `test_e64_job_engine_contract.py` vừa dựng.

- **Được:** xoá 5/6 bản sao có hại nhất; họ thứ 16 không thể lệch vì có test chặn.
- **Mất:** vẫn còn 2 bản `Fetcher` trùng 31/36 dòng.
- **Tự khai rủi ro:** `GuardRefused` hợp nhất phải phục vụ hai hình dạng ⇒ hơi rộng hơn cần thiết cho mỗi phía. Đụng 6 file job — đây là các file **đang chạy production**, tuy thay đổi cơ học.

### P3 — Trích khuôn chung cho cả 15 họ *(tối ưu: nhất quán dài hạn)*

P2 cộng: gộp `Fetcher` `snapshot`+`fundamentals`, gom `MIN_SAMPLE`/`MAX_FAILED`/`MAX_SHAPE` vào `guard_constants.py`, thống nhất chiến lược `raw_payload`.

- **Được:** một khuôn duy nhất cho lát 12/13 container hoá.
- **Mất:** đụng ~12 file gồm cả đường ghi kho.
- **Tự khai rủi ro:** 🔴 **YAGNI ngược.** Gom hằng số của 4 guard vào một file làm việc đọc một guard phải nhảy hai file — đổi một thứ dễ đọc lấy một thứ "gọn". Và chưa có bằng chứng nào cho thấy 4 giá trị đó **phải** bằng nhau mãi; ép chung là quyết định thay cho tương lai.

---

## Chấm theo tiêu chí viết trước

Tiêu chí chốt **trước** khi chấm: *(a)* không tăng rủi ro cho lát 12; *(b)* chặn được lệch mới bằng máy, không bằng trí nhớ; *(c)* số file production phải đụng; *(d)* không quyết thay cho tương lai khi chưa có dữ kiện.

| | (a) rủi ro lát 12 | (b) chặn lệch mới | (c) file đụng | (d) không quyết hộ tương lai |
|---|---|---|---|---|
| **P1** | 0 | ✗ không có gì thi hành | 6 (chỉ comment) | ✓ |
| **P2** | thấp — thay đổi cơ học, có test | ✓ test hợp đồng | 6 job + 1 mới | ✓ |
| **P3** | trung bình — đụng đường ghi kho | ✓ | ~12 | ✗ ép 4 hằng số bằng nhau mãi |

**Chọn P2, nguyên vẹn, không trộn.**

**Vì sao loại P1:** ba vòng audit vừa rồi là bằng chứng trực tiếp rằng comment không đủ — chính §1.7 đã ghi thành luật mà vẫn bị vi phạm ba lần liên tiếp, kể cả trong lượt đi sửa nó. Một bản sao không có phép kiểm là một bản sao sẽ trôi.

**Vì sao loại P3:** hai lý do độc lập. Một, phần thêm của nó (`Fetcher`) chỉ có **2 bản trùng** chứ không phải 3 như báo cáo nói — giá trị bằng một phần ba dự tính, trong khi rủi ro đụng đường ghi kho thì không giảm. Hai, gom hằng số guard là **quyết định thay cho tương lai** khi chưa có dữ kiện nào nói bốn ngưỡng đó phải khớp nhau vĩnh viễn.

## Điều kiện đảo ngược

- Nếu họ job thứ 16 cần một trường thứ ba trong `GuardRefused` (không phải `verdict` cũng không phải `reasons`) ⇒ lớp hợp nhất đã sai hình dạng, tách lại theo miền.
- Nếu `snapshot_fetch` và `fundamentals_fetch` **phân kỳ** thêm (xuống dưới 25/36 dòng giống nhau) ⇒ bỏ hẳn ý gộp `Fetcher`, ghi là hai họ khác nhau thật.
- Nếu lát 12 lộ ra một khuôn container cần cấu hình tập trung ⇒ xét lại P3 **với dữ kiện mới**, không phải với dự đoán hôm nay.

---

## Quyết định riêng — idempotency của `omo_store`

Tách khỏi phần trên vì đây là **thay đổi lược đồ**, trục rủi ro khác hẳn.

**Vấn đề đã đo:** `omo_store.store()` làm `SELECT` kiểm `session_date` rồi mới `INSERT`; `macro.omo_session` không có ràng buộc UNIQUE. An toàn khi một tiến trình chạy tuần tự — nhưng lát 13 đưa job vào container với retry/restart là mặc định, hai lượt chồng lấn sẽ ghi trùng một phiên OMO. Đây là cơ chế **yếu nhất trong 6 loại idempotency** của 15 họ; năm loại kia đều tựa vào ràng buộc DB.

| | Cách | Rủi ro tự khai |
|---|---|---|
| **O1** | Migration thêm `UNIQUE (session_date)` + đổi `INSERT` sang `ON CONFLICT DO NOTHING` | 🔴 **Migration sẽ ĐỔ nếu kho production đã có dòng trùng.** Phải đếm trước khi chạy |
| **O2** | Giữ lược đồ, bọc `SELECT`+`INSERT` trong một giao dịch `SERIALIZABLE` | Không sửa dữ liệu cũ, nhưng vẫn là khoá ở tầng ứng dụng — yếu hơn ràng buộc DB, và phải xử lý retry khi serialize lỗi |
| **O3** | Không làm gì tới lát 13, lúc đó chốt cùng bảng lịch | Đồng hồ mất dữ liệu OMO đang chạy; nhưng job đang `Disabled` nên rủi ro hiện tại bằng 0 |

**Chọn O1, nhưng KHÔNG chạy trong lượt này.** Lý do: migration đúng hướng (đưa omo về cùng lớp bảo vệ với 5 họ kia), nhưng **điều kiện tiên quyết là đếm dòng trùng trong kho production** — mà lượt này không đụng kho thật. Ghi thành việc mở đầu của lát 13, kèm lệnh kiểm:

```sql
SELECT session_date, count(*) FROM macro.omo_session GROUP BY 1 HAVING count(*) > 1;
```

Rỗng thì thêm ràng buộc thẳng; không rỗng thì phải chốt cách gộp trước — và **đó mới là quyết định thật**, không phải việc cơ học.
