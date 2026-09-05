# LBMA — Giá vàng và bạc fixing chính thức

**Ngày đo:** 2026-08-15 · **Trạng thái:** 2 endpoint đã gọi thật, số liệu đã được controller kiểm chứng độc lập từng con số

> Mọi con số trong file này đến từ lời gọi thật ngày **2026-08-15**. Cái gì chưa gọi thì ghi **"chưa kiểm"**, không suy đoán từ tên endpoint.

---

## 1. Vai trò trong dự án — đọc trước khi dùng

🔴 **LBMA KHÔNG thay WiChart cho giá vàng.** Đây là điểm hay bị hiểu ngược.

| | |
|---|---|
| **Vai 1 — Mốc chuẩn** | Giá fixing chính thức của thị trường vàng London, dùng để đối chiếu mọi nguồn vàng khác *(đã dùng đúng vai này: đo premium của PAXG, xem [`crypto.md`](crypto.md))* |
| **Vai 2 — Backfill lịch sử dài** | **Từ 1968**, một lời gọi lấy hết. Không nguồn nào khác trong bộ của dự án có chiều sâu này |
| **KHÔNG phải vai** | Nguồn giá vàng thế giới hằng ngày — chỗ đó **WiChart `vang_the_gioi` đã khớp chuẩn Investing XAU/USD 0,00% trên 10/10 ngày** *(đo 2026-08-15, chi tiết ở [`../macro/wichart.md`](../macro/wichart.md))*. LBMA lệch **0,56%** so với cùng chuẩn đó |

⚠️ **0,56% không phải sai số của LBMA** — là **đặc tính**: LBMA là giá **fixing tại một thời điểm trong ngày**, không phải giá đóng cửa. Xem §5.

**Bài học phương pháp:** đợt khảo sát ban đầu khuyến nghị *"thay vàng bằng LBMA"*. Khuyến nghị đó đã bị rút lại ngày **2026-08-15** sau khi đối chiếu với chuẩn Investing — nguồn đang có không sai, nên không có gì để thay. **Trước khi thay một nguồn, phải đo nguồn đang có so với chuẩn, không chỉ đo ứng viên mới.**

---

## 2. Đặc tả API

### 2.1 Endpoint

```
GET https://prices.lbma.org.uk/json/gold_pm.json      # vàng, fixing PM
GET https://prices.lbma.org.uk/json/silver.json       # bạc
```

| | |
|---|---|
| Xác thực | **Không** — không khoá, không token, không cookie |
| Tham số | **Không có.** Mỗi lời gọi trả **toàn bộ lịch sử**, không phân trang, không lọc theo ngày |
| Định dạng | JSON |

### 2.2 Độ phủ *(đo 2026-08-15)*

| | Vàng (`gold_pm.json`) | Bạc (`silver.json`) |
|---|---|---|
| Điểm đầu | **1968-04-01** | **1968-01-02** |
| Điểm cuối | 2026-08-14 | 2026-08-14 |
| Số điểm | **14.662** | **14.806** |
| Dung lượng một lời gọi | **913.134 byte** (~913 KB) | chưa đo riêng |
| Giá trị điểm cuối | **4.390,7** USD/oz | chưa ghi |
| Độ trễ | **0 ngày làm việc** | 0 ngày làm việc |

### 2.3 Lược đồ response

✅ **Đã kiểm 2026-09-05** (mở response thật, cả hai file):

```json
[{"is_cms_locked": 0, "d": "1968-04-01", "v": [37.7, 15.68, null]},
 …,
 {"is_cms_locked": 0, "d": "2026-09-04", "v": [4415.4, 3269.16, 3803.43]}]
```

| Trường | Ý nghĩa đo được |
|---|---|
| gốc | **mảng** các dòng, **tăng dần theo ngày**, không phân trang |
| `d` | ngày fixing `YYYY-MM-DD` |
| `v` | mảng **đúng 3 phần tử theo vị trí**: `[USD, GBP, EUR]` /oz; `null` = tiền tệ chưa có (EUR trước 1999) — vàng 7.737 / 14.676 dòng có null, bạc 7.847 / 14.839 |
| `is_cms_locked` | cờ CMS nội bộ, luôn `0` trong mẫu — không mang nghĩa dữ liệu |

Ngày nghỉ **bỏ hẳn dòng** (không chèn điểm rỗng): 14.676 điểm / 58 năm ≈ 253 điểm/năm. Điểm cuối 2026-09-04: vàng **4.415,40** · bạc **66,835** USD/oz; `silver.json` **897 KB**, 14.839 điểm. ETL lát 7 lấy `v[0]` (USD) theo vị trí `external_sub='0'`.

*(Đợt 2026-08-15 chỉ đếm số điểm, khoảng lịch sử, dung lượng và giá trị điểm cuối — phần "chưa kiểm" cũ đã đóng ở đây.)*

### 2.4 Hiệu năng *(đo 2026-08-15, n=2)*

| | |
|---|---|
| Trung vị | ~1.170 ms |
| Chậm nhất | 1.331 ms |
| Header hạn mức | **Không có** `X-RateLimit-*`, không có `Retry-After` |
| ETag / `If-None-Match` | **Có ETag nhưng KHÔNG sinh `304`** *(đo 2026-09-05: gửi `If-None-Match` đúng ETag vẫn nhận `200` trọn 914 KB; `cache-control: no-cache, no-store`; `last-modified` 05:20 GMT thứ 7)* |

⚠️ Không host nào trong nhóm nguồn quốc tế trả header hạn mức — **ETL phải tự giữ nhịp**, không trông chờ server báo.

**Ngân sách:** 2 lời gọi/ngày là đủ cho cả vàng và bạc. Backfill toàn bộ lịch sử cũng chính là 2 lời gọi đó.

---

## 3. Vì sao lấy — so với các nguồn vàng khác

Bảng đối chiếu 10 ngày với chuẩn **Investing XAU/USD giao ngay** *(đo 2026-08-15)*:

| Nguồn | \|Lệch\| TB | Bản chất |
|---|---:|---|
| **WiChart `vang_the_gioi`** | **0,00%** | Bằng nhau tuyệt đối 10/10 ngày — nhiều khả năng cùng nguồn giá *(suy luận, chưa xác nhận nguồn gốc)* |
| **PAXG** (Binance) | 0,15% | Chạy 24/7 — xem [`crypto.md`](crypto.md) |
| **LBMA Gold PM** | **0,56%** | Fixing 15:00 London, không phải giá đóng cửa |

Đối chiếu chéo với Yahoo *(đo 2026-08-15)*:

| Cặp | \|Lệch\| TB | Ngày lệch >2% |
|---|---:|---:|
| `GC=F` (tương lai COMEX) vs LBMA vàng | **0,49%** | **1%** |
| `SI=F` (tương lai COMEX) vs LBMA bạc | **1,81%** | **31%** |

🔴 **Bạc lệch gấp gần 4 lần vàng, và điều đó có lý do cơ học:** fixing bạc chốt **trưa London**, còn COMEX chốt **chiều New York** — hai mốc cách nhau nhiều giờ giao dịch. **Đừng đọc con số 1,81% như bằng chứng nguồn bạc kém.**

---

## 4. Vị trí trong bộ nguồn hàng hoá

| Mặt hàng | Nguồn chính | Vai của file này |
|---|---|---|
| Vàng thế giới hằng ngày | WiChart `vang_the_gioi` | Mốc chuẩn + backfill 1968 |
| Vàng 24/7 (kể cả cuối tuần) | PAXG qua Binance — [`crypto.md`](crypto.md) | Mốc chuẩn để đo premium |
| Bạc | WiChart `bac` *(Tier B, cờ "lệch <1%" — đo 2026-08-12, **chưa đo lại trong đợt 2026-08-15**)* | Mốc chuẩn + backfill 1968 |
| Dầu WTI giao ngay | FRED `DCOILWTICO` — [`fred.md`](fred.md) | — |
| Dầu WTI tương lai | WiChart `dau_wti` · Yahoo `CL=F` — [`yahoo.md`](yahoo.md) | — |
| Đồng · thép · than | 🔴 **Chưa có nguồn ngày miễn phí không khoá nào có mốc chuẩn để đối chiếu** *(đã tìm 2026-08-15, không ra)* | — |

**Đã thử và loại trong cùng đợt đo:**

| Nguồn | Kết quả *(đo 2026-08-15)* |
|---|---|
| **EIA API v2** | `403 API_KEY_MISSING` — cần đăng ký. *(Không cần: `DCOILWTICO`/`DHHNGSP` của FRED **chính là dữ liệu EIA**, lấy được không khoá)* |
| **World Bank Pink Sheet** | Tải được, **86 mặt hàng** — nhưng tần suất **THÁNG**, và đường dẫn gọi được chỉ tới `2024M12` |
| **DBnomics `EIA/PET`** | 180.591 series — **chưa gọi series cụ thể** |

---

## 5. Bẫy và đặc tính

### 🔴 Bẫy 1 — Fixing không phải giá đóng cửa

**LBMA Gold PM chốt 15:00 giờ London** = **14:00 UTC** (mùa hè). Bạc chốt **trưa London**.

Hệ quả bắt buộc nhớ:

- So LBMA với bất kỳ nguồn giá đóng cửa nào sẽ luôn ra một khoảng lệch **có hệ thống, không triệt tiêu được bằng thêm mẫu**.
- Muốn so công bằng, phải **lấy giá của nguồn kia đúng tại 14:00 UTC**. Đã làm đúng cách này khi đo premium PAXG: lệch rơi từ **0,618%** (dùng giá đóng 23:59 UTC) xuống **0,130%** (dùng nến 1 giờ mở lúc 14:00 UTC) *(đo 2026-08-15, 88 ngày)*.
- 0,618% đó **không phải premium** — là **10 tiếng biến động thật** của thị trường vàng.

### ⚠️ Bẫy 2 — Một lời gọi trả toàn bộ lịch sử

Không có tham số lọc ngày. Mỗi lần gọi là **~913 KB cho vàng**. ETL hằng ngày mà gọi lại toàn bộ thì tốn băng thông vô ích cho 14.661 điểm không đổi.

→ ~~Cách chặn: dùng `If-None-Match`/`ETag` nếu có~~ — **đo 2026-09-05: ETag có nhưng không sinh `304`**, nên ETL lát 7 tải trọn 2 file mỗi ngày (~1,8 MB) và UPSERT chỉ-khi-đổi; không lưu body thô (chỉ khi guard từ chối).

### ⚠️ Bẫy 3 — Lịch fixing không phải lịch phiên của thị trường khác

LBMA nghỉ theo **ngày nghỉ ngân hàng Anh**. Ngày nghỉ đó COMEX và các sàn châu Á vẫn có thể chạy. **Join theo ngày thật, đừng join theo vị trí dòng.**

---

## 6. Chưa kiểm — phải đo trước khi triển khai

| Mục | Vì sao cần |
|---|---|
| ~~**Lược đồ JSON đầy đủ**~~ | ✅ đo 2026-09-05 — §2.3 |
| ~~**ETag / `If-None-Match`**~~ | ✅ đo 2026-09-05 — có ETag, không `304` (§2.4) |
| **Ngưỡng rate limit thật** | Chủ đích không dò trong đợt đo; 2 lời gọi/ngày (lát 7) chạy sạch |
| **Điều khoản sử dụng** | Việc của chủ dự án, tài liệu này chỉ ghi là chưa đọc |
| ~~**Dung lượng và giá trị điểm cuối của `silver.json`**~~ | ✅ đo 2026-09-05 — 897 KB, 14.839 điểm, 66,835 USD/oz ngày 2026-09-04 |
| ~~**Cách LBMA xử lý ngày nghỉ trong chuỗi**~~ | ✅ đo 2026-09-05 — bỏ hẳn dòng, không chèn điểm rỗng (§2.3) |

---

## 7. Quy tắc ETL

1. **Lưu giá ở đơn vị gốc:** USD/ounce. Không quy đổi, không làm tròn ở tầng lưu.
2. **UPSERT theo ngày**, không append — chưa kiểm LBMA có vá hồi tố hay không.
3. **Ghi rõ loại giá vào lược đồ:** cột phân biệt `fixing` với `close`. Trộn chung sẽ tạo bậc nhảy ~0,5% tại điểm đổi nguồn — cùng loại lỗi mà bộ nguồn dầu đã phải xử lý bằng cách lưu tách giao ngay và tương lai.
4. **Đối chiếu định kỳ với WiChart `vang_the_gioi`.** Khoảng lệch bình thường là ~0,5%; lệch bật lên nhiều hơn nghĩa là một trong hai nguồn đổi hành vi, không phải giá vàng đổi.
5. **Không dùng LBMA làm giá hiển thị hằng ngày** — người đọc quen với giá đóng cửa sẽ thấy số của bạn lệch so với mọi bảng giá khác.
