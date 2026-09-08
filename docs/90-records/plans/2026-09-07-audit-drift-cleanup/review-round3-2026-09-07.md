# Vòng review 3 — chuẩn hoá code, bộ test và tầng agent

**Ngày:** 2026-09-07 tối → 2026-09-08 · **Nhánh:** `fix/standardise-jobs` · **Yêu cầu chủ dự án:** *"mở rộng phạm vi audit toàn dự án, kĩ càng vào"* — và **chưa vào lát 12**, chuẩn hoá trước.

Hai vòng trước cày tài liệu. Vòng này nhắm **ba vùng chưa ai soi**: chính code 15 họ job, chính bộ 1.039 test, và tầng agent + an toàn khoá.

| | Trục | Kết quả |
|---|---|---|
| **R4** | Chuẩn hoá 15 họ job — 9 trục | 3 🔴 · 6 🟡 |
| **R5** | Chất lượng 1.039 test theo §4.5 | 0 🔴 · 4 🟡 + **6 phép đột biến đề xuất** |
| **R6** | Tầng agent, injection, quét khoá | **0 🔴** · 5 🟡 |

Ràng buộc như hai vòng trước, thêm hai: **R5 không được tự chạy đột biến** (chạy đột biến là sửa file), **R6 không được in giá trị khoá**.

---

## Điều đáng giá nhất: đột biến biến suy đoán thành số đo

R5 **đoán** bộ test không bắt được 6 phép đột biến. Tôi chạy thật cả 6 — nó đúng **4/4** ca nghi ngờ, và **2/2** ca đối chứng cũng đúng:

| Đột biến | R5 đoán | Trước khi sửa | Sau khi sửa |
|---|---|---|---|
| `spill.py` đặt `owned=True` **trước** `_scan()` | không đỏ | 13 passed | **2 failed** |
| `spill.py` bỏ `except OSError: _release(); raise` | không đỏ | 13 passed | **1 failed** |
| `DIRECTORY_ABSENT_DAYS` 3 → 4 | không đỏ | 18 passed | **1 failed** |
| `DIRECTORY_ABSENT_DAYS` 3 → 2 | — | — | **1 failed** |
| `QUOTA_MIN_INTERVAL_PCT` 20 → 19 | không đỏ | 14 passed | **1 failed** |
| `QUOTA_MIN_WEEKLY_PCT` 10 → 9 | — | 14 passed | **2 failed** |
| *(đối chứng)* `DROP_RATIO` 0.02 → 0.03 | **có** đỏ | 1 failed ✓ | — |

Hai nhánh `spill.py` là ca đắt nhất: chúng có **docstring 🔴 tám dòng** mô tả đúng bug đã đo được (*"tiến trình thành ZOMBIE NGẬM KHOÁ"*) và ghi rõ `owned = True` **"ĐẶT CUỐI"** — đã trả giá, đã hiểu, đã viết ra, mà **không test nào giữ**. Refactor sau này đảo hai dòng đó thì cả bộ vẫn xanh.

---

## Đã sửa

### Nhóm A — ba thứ sẽ cắn khi vào container/scheduler *(R4)*

| | Vấn đề | Sửa | Test canh |
|---|---|---|---|
| **G1** | `refdata_fetch` **0 retry** (`grep -c` = 0; các họ khác 7–8) — job duy nhất chết vì một hiccup mạng, mà nó lại chặn cả ETL giá lẫn pipeline tin | Dùng `http_fetch.Fetcher` chung, `gap=(0.5, 0.5)` giữ nhịp FiinTrade — **không** đẻ bản retry thứ tư | `test_e62_refdata_fetch.py` (5 test) — trước đó `refdata_fetch` **không có test trực tiếp nào** |
| **G2** | `omo_job` và `refdata_job` trả **1** cho lỗi thật; README chốt `1` = chốt chặn, `2` = lỗi thật. `refdata` dùng **một mã cho hai nghĩa ngược nhau** | Cả hai → `2`; giữ `1` cho `GuardRefused` | `test_e63_exit_code_contract.py` — **8 họ**, đỏ đúng 2 trước khi sửa |
| **G3** | `pool_pre_ping` vắng ở `omo` `refdata` `screener` `events`, không ai ghi lý do | Bật cả 4, kèm lý do tại chỗ | `test_e64_job_engine_contract.py` — quét mọi `create_engine` trong `*_job.py` |

Hai test G2/G3 là **hợp đồng xuyên họ**: họ job thứ 16 thêm vào mà lệch là đỏ ngay.

### Nhóm B — bốn lỗ hổng test, mỗi cái chứng minh bằng đột biến

- **T1 · T2** hai nhánh `SpillStore.try_acquire()`: nhả khoá khi `_scan()` hỏng (chống zombie), và `owned` chỉ bật **sau** `_scan()`.
- **T3** biên `DIRECTORY_ABSENT_DAYS`: cặp *đúng-3-ngày* / *thiếu-1-giờ* kẹp đúng điểm chuyển. Hai test cũ dùng 2 và 4 ngày — cách ngưỡng mỗi bên một ngày nên không khoá được gì.
- **T4** biên quota LLM: cặp *đúng-ngưỡng* / *dưới-một-điểm*.
- **T5** `tests/ingester/conftest.py` import lại fixture của `tests/clickhouse/conftest.py` — R5 **suy luận** là dựng container kép, tôi **đo được đúng 2**; dời ba fixture về conftest gốc (khuôn `ff4d0ca` đã làm cho Postgres) ⇒ đo lại còn **1**.

### Nhóm C — hợp đồng tầng agent *(R6)*

- **A1** 🔴 `compare_peers` cắt câm `metric_codes` (`codes[:TRAN_CHI_TIEU]`, không cờ) — trong khi cùng file có cơ chế `da_cat` công phu cho **mã**, và §2b ghi 🔴 *"Không bao giờ cắt câm"* kèm ca đã trả giá (`get_corporate_events` trả 20/177). Thêm `da_cat_chi_tieu`/`so_chi_tieu_nhan`/`tran_chi_tieu`, gắn vào **cả 4 điểm trả về**, kèm test cặp *có cắt* / *không cắt*.
- **A2** §2b tự nhận bao trùm *"cả 9 function"* — sai: `load_knowledge_reference` không tra kho nên không có 6 hình dạng. Sửa tiêu đề thành **8 function tra dữ liệu** và ghi rõ ngoại lệ.
- **A3** `maintenance.md:86` mô tả bộ tham số MA `5·20·50–60·200`; skill thật ghi `MA9·MA20·MA50·MA200`.
- **A4** lý do tồn tại của `TOOL_RULES` (ca đo 2026-09-07: hỏi CPI 8/2026, model **không gọi công cụ** mà trả lời *"mốc cập nhật của tôi là 1/2026"* — sai trong khi kho có số) chỉ nằm trong docstring code. Đưa lên tài liệu sống theo §1.1.

---

## 🔴 Ba lần tôi tự sai trong lúc sửa — ghi lại vì đó mới là phần dùng được

1. **Nhét `retries` vào `counts` của refdata.** `counts` được truyền **thẳng vào `refdata_guard.check()`** — tôi suýt bơm dữ liệu lạ vào chốt chặn. Hai test job đỏ mới lộ ra. Chuyển sang `stats`, đúng khuôn 9 họ khác đang dùng.
2. **Viết test T4 tautological.** Tôi lấy `nc.QUOTA_MIN_INTERVAL_PCT` làm **đầu vào** test — đổi hằng số thì đầu vào đổi theo, đột biến 20 → 19 vẫn **16 passed**. Đúng thứ §4.5.3 cấm, và tôi chỉ phát hiện vì **chạy lại đột biến** thay vì tin test xanh. Đổi sang literal `20`/`10`.
3. **Dời fixture làm hỏng đường dẫn.** Khối dời sang conftest gốc mang theo `REPO_ROOT = Path(__file__).parents[3]` — đúng ở `tests/clickhouse/`, **sai một cấp** ở `tests/`, và còn **đè** `REPO_ROOT` sẵn có mà alembic dùng. Hậu quả: volume mount lặng lẽ rỗng, container mất `backups.xml`, **6 test backup đỏ**.

Bài học chung của cả ba: **test xanh không phải bằng chứng test có tác dụng.** Cả ba lần đều chỉ lộ ra khi chạy đột biến hoặc chạy rộng hơn phạm vi vừa sửa.

---

## Chưa sửa — nhóm D, cần chủ dự án quyết

R4 tìm 6 nợ chuẩn hoá là **gộp code dùng chung**, tức thay đổi thiết kế chứ không phải vá lỗi:

| Nợ | Quy mô |
|---|---|
| `class GuardRefused` định nghĩa **6 lần**, 2 hình dạng (`.reasons` vs `.verdict`) | gộp = đụng 6 job |
| `class Fetcher` lặp gần nguyên văn ở `price`/`snapshot`/`fundamentals` (cùng `MIN_INTERVAL=0.5`, `RETRIES=3`, `BACKOFF=(2,4,8)`) | gộp = đụng 3 họ + test |
| `MAX_BAD_SHAPE` vs `MAX_SHAPE` — cùng giá trị 0.05, khác tên | đổi tên = đụng 4 guard |
| Cầu chì `MAX_CONSECUTIVE_FAILED` 10 (price/news) vs **5** (classify), không ghi lý do | có thể chỉ cần một dòng comment |
| `snapshot_store` không ghi `raw_payload` khi thành công — lý do chính đáng (payload đã ở domain table) nhưng **không viết ra**, trong khi `fundamentals` cùng khuôn thì có ghi | một dòng comment |
| `omo_store` dùng SELECT-rồi-INSERT, cơ chế idempotency **yếu nhất** trong 6 loại — không có ràng buộc DB chặn ghi trùng | rủi ro thật nếu lát 13 retry chồng lấn |

Hai mục cuối rẻ và đáng làm sớm. Bốn mục đầu là refactor thật — nên đi qua §4.8 (nhiều phương án) chứ không tiện tay gộp.

## Nghiệm thu

```
pytest tests -q          1.062 passed, 2 skipped   (1.039 -> +23 test mới)
pytest tests/docs -q     8 passed
ruff check --select F    All checks passed!
container ClickHouse một lượt chạy: 2 -> 1
6/6 phép đột biến cho kết quả đúng như dự đoán, cả trước lẫn sau khi sửa
```

---

## Đóng nhóm D — 2026-09-08

*Ghi thêm, không sửa bảng trên: bảng trên là ảnh chụp lúc vòng 3 kết thúc.*

Sáu nợ đi qua §4.8, hồ sơ ở [`decision-unify-jobs-2026-09-08.md`](decision-unify-jobs-2026-09-08.md).
Kết cục:

| Nợ vòng 3 | Kết cục |
|---|---|
| `GuardRefused` 6 bản | ✅ **gộp** — `etl/guard_common.py`, canh bằng `tests/etl/test_e65_guard_refused_contract.py` |
| `Fetcher` "lặp ba bản" | ⚪ **không gộp** — đo lại: `price` 91 dòng, chỉ trùng 16/91; trùng thật chỉ `snapshot`↔`fundamentals` (31/36), cả hai đã có test riêng |
| `MAX_BAD_SHAPE` vs `MAX_SHAPE` | ⚪ **giữ nguyên** — cả bốn file đang đặt tên đúng theo trường nó canh; giá trị 0,05 bằng nhau là trùng hợp, không phải một sự thật chung |
| `MAX_CONSECUTIVE_FAILED` 5 vs 10 | ✅ **đã ghi lý do** tại `news_classify.py` |
| `snapshot_store` không ghi `raw_payload` | ✅ **đã ghi lý do** tại `snapshot_store.py` |
| `omo_store` SELECT-rồi-INSERT | 🟡 **hoãn có chủ đích** — chọn O1 (UNIQUE + `ON CONFLICT`), nhưng phải đếm dòng trùng trên kho thật trước. Việc mở đầu lát 13 |
