# Ledger — plan: luật huỷ niêm yết cho mã vắng danh bạ

Thực thi 2026-08-28 tối, controller tự làm cả 3 task (mỗi task 1–2 file, thuộc diện "tự làm" §4.1).

## Quyết định trước khi viết code

- **Ngưỡng giữ NGÀY LỊCH, không đổi sang đếm lượt** *(chủ dự án chốt)*. Có nêu lo ngại: job chạy Thứ 2–6 nên "3 ngày" ≠ 3 lần quan sát. Bốn phương án cân nhắc và loại cả bốn (đếm lượt · đếm `DISTINCT trading_date` · nới 3→5 · cột đếm song song) — **không đáng độ phức tạp**. Căn cứ: `etl refdata` là job REST chứ không phải socket, ngày lễ vẫn quan sát bình thường, nên hở duy nhất là cuối tuần. Hệ quả chấp nhận + điều kiện đảo ngược ghi tại plan §Ba ràng buộc mục 3.

## Task 1 — migration 0014

- Test đỏ TRƯỚC, và đỏ **đúng lý do**: `UndefinedColumn: column "directory_absent_since" does not exist` (kiểm bằng grep, không chỉ đọc "2 failed").
- Sau migration: `pytest tests/schema` → **51 passed**. Chuỗi alembic `0013 -> 0014 (head)`.
- Commit `ad95f07`.

## Task 2 — đóng/gỡ dấu + chọn ứng viên

- 5 test mới. **Chỉ 3 test đỏ được trước**; 2 test còn lại (`not_delisted_before_threshold`, `etf_and_index_are_never_marked_or_delisted`) là **assert phủ định** nên XANH SẴN khi chưa có code — chúng không chứng minh gì.
- 🔴 **Thí nghiệm đột biến** (plan yêu cầu) — chạy trên chính hai test đó:

| Đột biến | Test | Kết quả |
|---|---|---|
| `DIRECTORY_ABSENT_DAYS` 3 → 1 | `test_not_delisted_before_threshold` | **FAILED** ✅ |
| Bỏ `AND security_type = 'stock'` khỏi câu đóng dấu | `test_etf_and_index_are_never_marked_or_delisted` | **FAILED** ✅ |

  Khôi phục xong: 18/18 xanh lại. Hai guard có gác thật.
- Toàn bộ: **320 passed, 2 skipped**. Commit `6a53226`.

## Task 3 — nghiệm thu trên DB thật (2026-08-28 19:40–19:41)

**Sao lưu trước:** `pg_dump -n market` → 619.082 B / 8.800 dòng / 36 khối `CREATE TABLE`+`COPY`. Kiểm **có nội dung thật**, không chỉ kiểm khác 0 byte.

**Số nền trước khi động vào:** `listed_stock=1962` · `no_issuer_listed_stock=438` · `D_delisted=4` · `tong_security=2015`.

**Migrate:** `alembic upgrade head` → `current` = **`0014 (head)`**.

**Hai lượt job, cả hai `exit 0`:**

```
lượt 1: {'sec_unchanged': 2015, 'delisted': 0, 'directory_absent_cleared': 0,
         'directory_absent_marked': 438, 'stocks_no_issuer': 438, ...}
lượt 2: {'sec_unchanged': 2015, 'delisted': 0, 'directory_absent_cleared': 0,
         'directory_absent_marked': 0,   'stocks_no_issuer': 438, ...}
```

**Đối chiếu:**

```
A_co_dau=438
B_dau_sai_loai=0
C_khong_issuer_chua_dau=0
D_da_bi_lat=4
```

Kỳ vọng plan **A=438 · B=0 · C=0 · D=4** — khớp cả bốn.

**Kiểm thêm ngoài plan** — `marked=0` mới chỉ là counter tự khai, nên soi thẳng dữ liệu:

```
so_moc_thoi_gian_khac_nhau=1
moc=2026-08-28 12:41:00.214924+00
```

Đúng **một** mốc duy nhất ⇒ lượt hai thật sự không dời dấu.

## Mốc kế tiếp — tính ra, không ước lượng

Dấu đóng **2026-08-28 19:41** (giờ VN) ⇒ ngưỡng 3 ngày thoả lúc **31/08 19:41**. Job chạy **08:00**, nên lượt thứ 2 (31/08) **chưa** thấy. **Lượt đầu tiên nhìn thấy 438 ứng viên là thứ 3 2026-09-01 08:00**, và lượt đó chốt chặn 1% sẽ **từ chối** (438/1.962 = 22,3%) — job `failed`, không ghi gì, **đúng thiết kế**.

*(Plan ước "khoảng 31/08"; tính chính xác theo giờ chạy thật thì là 01/09.)*
