# SDD ledger — plan: docs/90-records/plans/2026-09-04-fundamentals-etl/plan.md

**Ngày:** 2026-09-04 · **Nhánh:** `feat/fundamentals-etl` · [spec](spec.md) · [plan](plan.md)

Thực thi bằng subagent (Sonnet, chỉ định tường minh), review hai trục sau mỗi task, artifact điều phối (brief, report, gói diff) ở scratchpad ngoài repo.

## 0. Rà plan trước khi giao (pre-flight)

| Cặp / task | Sản xuất → tiêu thụ | Kết quả |
|---|---|---|
| T1 → T5, T6 | bảng `ops.fundamentals_check(issuer_id, kind, checked_at, payload_hash, changed_at, found_by)`, cột `source_id` | T5 `apply`/`due_list` dùng đúng tên cột; T5 `_write_reports` upsert `ON CONFLICT (source_id)` khớp UNIQUE của T1 |
| T2 → T5, T6 | `Target(kind, issuer_id, organ_code, ticker, found_by)`, `classify` trả `{"items": [...]}` cho reports, `{"quarterly","yearly"}` cho báo cáo | T3 `report_rows` đọc `item["items"]`; T5 `_target` không dùng `com_type` (khác lát 4 — đúng, endpoint không rẽ nhánh theo loại hình) |
| T3 → T5, T6 | `rows`, `payload_hash`, `EMPTY_HASH`, `BadRecord`, `STATEMENT` | T5 import đủ; T6 bắt `BadRecord` cùng `BadShape` → `bad_shape` |
| T4 → T5, T6 | `Tally` có `empty` | T5 tăng `tally.empty`; T4 guard đọc `empty` |
| T5 → T6 | `Fetched(target, text, rows)`, `apply(conn, fetched, run_id)`, `remaining(conn, kinds)`, `load_dictionary(conn)` | T6 gọi đúng chữ ký |
| T1 tự thân | test chèn `financial_statement` length 6 phải vi phạm; migration giữ CHECK 1–5 | nhất quán |
| T2 tự thân | test giãn cách: `answers` 3 phần tử cho 3 lời gọi | đã sửa ở self-review plan |
| T5 tự thân | `test_due_list_backfill…` monkeypatch `fs.QUOTA` không tác dụng lên default arg — backfill bỏ LIMIT nên test vẫn đúng | chấp nhận, ghi chú: dòng monkeypatch thừa, không sai |
| T6 tự thân | `_wall_clock` mock: 2 lần 0.0 rồi 10.000 | đã sửa ở self-review plan |
| Toàn plan vs rubric | Task 2 và 5 chép khuôn `Fetcher`/`_UNIVERSE` từ `snapshot_*` (nhân bản có chủ đích theo spec §1, không import chéo để hai lát không kéo nhau đổ) | Ruling: chấp nhận trùng lặp khuôn — spec chọn "nhân bản từ snapshot_*"; chi phí nếu sai: hai bản trôi lệch, sửa một quên một |

## 1. Tiến độ theo task

- Task 1: complete (commits 2fea3ce..0208510, review clean). Schema 60 test xanh (56 → 60). Minor (deferred): downgrade sẽ vỡ nếu kho đã có dòng 6/9 — bản chất của mọi downgrade siết CHECK, spec §4.5 đã ghi.
- Task 2: complete (commits 0208510..64350c0, review clean). 11 test fetch xanh. Minor (deferred): `Fetcher`/`open_fetcher` gần trùng `snapshot_fetch` — trùng lặp khuôn theo ruling pre-flight; cân nhắc trích chung ở lát 6.
- Task 3: complete (commits 64350c0..48146dc, review clean). 7 test normalize xanh; reviewer tự chạy lại `count_rows.py` ra 1.749/980/916. Minor (deferred): `isinstance(year, int)` và `isinstance(sid, int)` nhận cả `bool` — thêm `and not isinstance(x, bool)` khi chạm lại module.
- Task 4: complete (commits 48146dc..b92b009, review clean). 6 test guard xanh. Minor (deferred): chưa có test pin đúng biên `MIN_SAMPLE` = 20 (19 vs 20).
- Task 5: Ruling: từ điển có 4 mã (`growth` `momentum` `value` `vgm`) mang `dai_gia_tri` là thang chữ `["A".."F"]`, code plan bind thẳng vào cột numeric ⇒ `InvalidTextRepresentation`. Implementer thêm guard chỉ nhận số cho `value_min/max` — chấp nhận, đúng tinh thần spec §4.6 (nạp trọn 729, thang chữ để NULL). Chi phí nếu sai: 4 mã điểm VGM thiếu dải giá trị — mà nhóm này đã bị loại có chủ đích khỏi kho, không ai tiêu thụ.
- Task 5: complete (commits b92b009..3ef8851, review clean). 18 test store xanh trên Postgres thật. Minor (deferred): lần kiểm đầu với 0 dòng vẫn ghi một dòng `raw_payload` rỗng (code plan, không phải lỗi implementer); tham số list bind thành mảng Postgres nhờ psycopg tự thích nghi, không khai kiểu tường minh (cùng idiom `snapshot_store`).
- Task 6: complete (commits 3ef8851..6f8201c, review clean). 7 test job xanh; **toàn bộ 586 passed, 2 skipped** (trước lát: 533 + 2). Minor (deferred): dòng `monkeypatch.setattr(fs, "QUOTA", 1)` trong test backfill là vô hiệu (đã ghi ở pre-flight); 1 warning trong full-suite chưa định danh — soi ở bước verify.

## 2. Review toàn nhánh (Opus, 2026-09-04) — merge được sau khi sửa

Không Critical. Một Important (A1) + 9 Minor + hai gate không giao được (định danh warning, AC2–AC8). Bảng chi tiết trong report của reviewer (scratchpad); những gì thành hành động:

- **A1 — mốc nước nhảy qua issuer bị cắt trần trigger.** `due_list` cắt 300 issuer nhưng mốc đẩy tới `max(public_date)` toàn cục ⇒ phần bị cắt mất trigger vĩnh viễn (chờ quét sàn 90 ngày). **Ruling:** KHÔNG dùng cách reviewer gợi ý (mốc = ngày cắt − 1) vì ngày hạn nộp có hàng trăm mã cùng `public_date`, mốc theo ngày + thứ tự cố định sẽ phục vụ đúng 300 mã cũ lặp lại mãi. Sửa bằng cách loại khỏi trigger những cặp `(issuer, kind)` đã kiểm **sau** ngày công bố (`checked_at` VN ≥ `public_date`), rồi mới cắt và đặt mốc = ngày cắt − 1; cặp đã phục vụ bị loại bằng sổ kiểm chứ không bằng mốc. Chi phí nếu sai: một cặp bị kiểm đúng ngày công bố mà nguồn chưa nạp sẽ không được trigger lại, rơi về quét sàn 90 ngày — cùng lưới an toàn spec đã có.
- **Cùng lỗi A1 tồn tại ở lát 4** (`snapshot_store.new_watermark` / `due_list` trần 300). **Ruling:** không sửa trong nhánh này (§4.4.3 — không tiện tay sửa hàng xóm); ghi vào *Điểm vào cho lát 6* của roadmap để sửa riêng bằng cùng công thức. Chi phí nếu sai: mùa báo cáo, snapshot của mã bị cắt trễ tới 64 ngày.
- Minor sửa luôn trong fix wave: monkeypatch vô hiệu (A8), test không dọn nền (A9), dict rỗng dùng chung (A5), tên test AC6 nói dối (A3), thiếu mốc khi giữ (A6), docstring downgrade (A10), biên `MIN_SAMPLE` (T4).
- Minor hoãn có lý do: `attempted` phồng khi cắt giờ (A2, giống `snapshot_job`, guard chỉ yếu đi trên lượt vốn dở dang); `float` thay `Decimal` (A4, `json.loads` đã trả float, cột `numeric` nhận đúng); cột `com_type_code` chết trong `_UNIVERSE` (A7, chép nguyên văn); list bind mảng không khai kiểu (T5); first-check rỗng ghi một dòng `raw_payload` (T5); trùng khuôn `Fetcher` (T2); `bool` lọt `isinstance(int)` (T3).
- Gate còn lại, kiến trúc sư làm: định danh 1 warning ⇒ AC1; AC2–AC8 dưới credential production; checklist tài liệu §8 (roadmap sửa số test: spec ghi 523 nhưng trước lát này thật là 533 + 2 skipped vì `4d193f5` thêm 10 test sau merge lát 4).
- Fix wave: commits 6f8201c..de60dd9 (`9725948` mốc nước + `de60dd9` vệ sinh test/fetch/docstring). 371 test etl+schema xanh. Implementer phải nâng `_checked(…, 1)` → `30` ở hai test cũ vì ngày sự kiện hardcode 2026-09-03 đụng luật "đã kiểm sau ngày công bố" — đưa vào re-review.

## 3. Nghiệm thu trên kho production (credential `ETL_DATABASE_URL`, role `dlck_etl`)

### AC2 — `--codes A32,BAB,AAS` (18:40, code tại 6f8201c)

```
{'tally': {'attempted': 12, 'failed': 0, 'bad_shape': 0, 'empty': 0, 'checked': 12, 'first': 12, ...},
 'rows_written': 41123, 'calls': 12, 'retries': 0, 'dictionary_rows': 729, 'remaining': 6080, 'subset': True}
```

| Mã | `financial_statement` BS / IS / CF (kho) | `count_rows.py` trên payload thô của chính lượt | `financial_report_file` |
|---|---|---|---|
| A32 | 1.749 / 980 / 916 = **3.645** | **3.645** | 8 |
| BAB | 6.600 / 4.658 / 5.213 = **16.471** | **16.471** | 106 (105 URL phân biệt) |
| AAS | 9.743 / 5.539 / 5.563 = **20.845** | **20.845** | 48 |

`metric_dictionary` 729 · `ops.fundamentals_check` 12 · `staging.raw_payload` 12 · 0 mã viết hoa trong kho, `bsi141` 82 dòng. Số khảo sát 16.785 / 21.194 đúng là lớn hơn vì đếm cả 8 khoá phi chỉ tiêu.
- Fix wave re-review: 9/9 phát hiện ADDRESSED; **1 Important mới**: hai test cũ ở `test_e34` dùng ngày sự kiện hardcode 2026-09-0x với `_checked(…, 30)` tương đối `now()` ⇒ đỏ từ 2026-10-01/03 (vi phạm §4.4.4); test mới `test_trigger_skips_a_pair_already_checked_after_publication` cùng bệnh (đỏ từ 2026-09-11). ⇒ fix round 2.

### AC4 — lượt hai cùng ngày (18:44 và 18:50)

Cả hai lượt: BAB và AAS `unchanged` 6/6, `rows_written 0`, `raw_payload` không tăng — đúng AC4. **Nhưng A32 `bad_shape` 3/3 báo cáo** ("sai hình dạng response") trong khi lượt 18:40 nạp A32 sạch 3.645 dòng. Guard không nổ vì `attempted` 12 < `MIN_SAMPLE` 20 — lượt con nhỏ không được chốt (iii) bảo vệ, đúng thiết kế. Đang chẩn đoán bằng lời gọi thẳng.

**Chẩn đoán AC4 (18:55):** gọi thẳng ASECO32 ba endpoint ⇒ `"quarterly": null` (sáng: `[]`), `yearly` bình thường, `status "Success"`. Hai cách tuần tự hoá của "không có kỳ quý" trên cùng endpoint — cùng họ bẫy `status` 0/"Success". `classify` hiện coi `null` là `bad_shape` ⇒ phải sửa (coi null là rỗng), có mẫu thật `A32-cf-quarterly-null.json`.

## 4. TẠM DỪNG 2026-09-04 ~19:00 — chủ dự án khởi động lại máy. Điểm nối lại

- HEAD nhánh `feat/fundamentals-etl` = `de60dd9` + commit ledger này. Kho production đã ở migration `0017`, có 12 cặp đã kiểm (A32 · BAB · AAS), 41.123 dòng BCTC, 729 dòng từ điển.
- **Việc kế tiếp:** giao **fix round 2** theo [fix-round2-brief.md](fix-round2-brief.md) (đã chép vào thư mục này): (A) ba test trigger dùng ngày hardcode ⇒ đổi sang `date.today()` tương đối; (B) `classify` coi `quarterly`/`yearly` `null` là `[]`, fixture `backend/tests/etl/fixtures/fundamentals/A32-cf-quarterly-null.json` đã có sẵn. Subagent Sonnet, TDD, hai commit; sau đó re-review có phạm vi.
- Rồi: định danh 1 warning trong full-suite ⇒ AC1 · AC4 chạy lại (`--codes A32,BAB,AAS` ⇒ A32 phải `unchanged`) · AC3 `--backfill --max-minutes 30` ngoài giờ ⇒ ghi calls/retries/remaining · AC6 ép hỏng · AC7 lượt thường sau khi có mốc · checklist tài liệu §8 (roadmap có "Điểm vào cho lát 6" kèm lỗi A1 của lát 4; tài liệu nguồn 05 thêm bẫy `quarterly: null` đo 2026-09-04) · review lại · merge `main`.
- Artifact điều phối (brief task 1–6, report, gói diff) ở scratchpad Temp của phiên `ea5dca87…`; mất cũng không sao — mọi quyết định đã nằm trong ledger này.

## 5. Nối lại (máy chưa tắt, hook mục tiêu không cho dừng) — làm bước ngắn, commit từng bước

- Fix round 2: `6c325d4` (test trigger/watermark lấy ngày từ `date.today()`) + `ef6ed24` (`classify` coi `quarterly`/`yearly` null là rỗng, fixture thật). tests/etl 312 + tests/schema 60 xanh. Chờ re-review có phạm vi.
- Re-review round 2: A và B đều ADDRESSED, không breakage mới. Còn đúng một ngày hardcode trong `test_due_list_skips_the_trigger_branch_on_cold_start` — an toàn vì cold start bỏ nhánh trigger bất kể ngày.

### AC4 — chạy lại sau fix (19:01, code tại ef6ed24)

```
{'tally': {'attempted': 12, 'failed': 0, 'bad_shape': 0, 'empty': 0, 'checked': 12, 'first': 0,
           'floor_compared': 12, 'changed_floor': 0, 'unchanged': 12}, 'rows_written': 0, 'calls': 12, 'retries': 0}
```
A32 hết `bad_shape`; 12/12 `unchanged`; `remaining` vẫn 6.080. ✅

### AC1 · AC6 (19:05, code tại ef6ed24)

- **AC1:** `uv run pytest tests -q` ⇒ **590 passed, 2 skipped** *(trước lát: 533 + 2)*. Warning duy nhất ở chế độ mặc định là `ResourceWarning` (file `owner.lock` chưa đóng) của `tests/ingester/test_i15_recovery_drain.py` — có từ trước, ngoài lát 5.
- **AC6:** ép `get` giả trả 503 cho 20 mã kind `bs` ⇒ guard từ chối "tỷ lệ lời gọi hỏng 100.0% > 20% (20/20)", exit 1, run 103 `failed`, `financial_statement` 40.961 dòng trước/sau không đổi, `fundamentals_check` vẫn 12. ✅ (0 dòng `raw_payload` — đúng giới hạn đã ghi: mọi target hỏng thì không có payload nào để lưu.)
- **AC3 lô 1** `--backfill --max-minutes 30 --stop-before-open` khởi chạy 19:05, **bị dừng tay ~19:10** vì chủ dự án cần tắt máy — lượt bị giết trước `apply` nên không ghi gì, `checked_at` không nhúc nhích, chạy lại từ đầu là đúng thiết kế.

## 6. TẠM DỪNG LẦN HAI ~19:10 — chủ dự án tắt máy. Điểm nối lại

Code xong, review sạch tới `ef6ed24`; còn: AC3 (backfill trọn sàn theo lô 30 phút, ngoài giờ, tới `remaining = 0`), AC7 (lượt thường sau khi có mốc nước), checklist tài liệu spec §8 (chưa sửa dòng nào — các chỗ cần sửa: roadmap dòng 117 + mục "Điểm vào cho lát 5" → viết "Lát 5 ✅" và "Điểm vào cho lát 6" kèm lỗi A1 của lát 4; `market-data-store` §4.1 dòng BCTC + §5.4; `00-conventions` §10.1 dòng BCTC; `database/README` 17 migration + `test_s14`; `backend/README` mục "Chạy job fundamentals" trước "## Lịch chạy"; `05-fiin-financial-statements` thêm bẫy `quarterly: null` đo 2026-09-04 18:5x; khảo sát README §6.6; `90-records/README` dòng plan), rồi merge `main`.
