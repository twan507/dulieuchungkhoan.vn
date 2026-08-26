# SDD ledger — plan: docs/90-records/plans/2026-08-26-ingester-omo-first-slice/plan.md

Spec: spec.md cùng thư mục (authority). Workspace artifact subagent: scratchpad ngoài repo (CLAUDE.md cấm `.superpowers/`).

## Preflight scan (2026-08-26 12:50)

Cặp task chia sẻ file/interface:

| Cặp | Produce vs consume | Kết quả |
|---|---|---|
| T1 `core/env.py` ↔ T9 `config.py`, T8 `omo_job` | `load_dotenv()` + `REPO_ROOT` | khớp — T9/T8 import đúng tên |
| T2 stub `omo_job.run` ↔ T8 thay thật | `run() -> int` | khớp |
| T5 `OmoResult/OmoRow` ↔ T6 store, T8 job | dataclass field thứ tự (op_type, tenor, part, win, vol, rate) | khớp test T6 |
| T6 `store(result, html, conn)` ↔ T8 | conn = SQLAlchemy Connection, caller giữ tx | khớp |
| T7 `rebuild(conn)` ↔ T8 | gọi trong cùng tx với store | khớp |
| T10 `Normalized/Metrics/COLUMNS` ↔ T13 state, T14 chwriter, T15 reconcile, T16 main | tên bảng + row dict | khớp |
| T11 `frame_key/FrameDedup/Stamper` ↔ T16 | chữ ký như plan | khớp |
| T12 `Catalog/topics/fetch_base_state` ↔ T16 | tên hàm | ⚠️ plan Interfaces T12 có dòng đánh máy "fetch_instруments := fetch_base_state" (ký tự Cyrillic) — **Ruling:** tên đúng là `fetch_base_state`, dòng kia là ghi chú đặt tên, không phải hai hàm. Chi phí nếu sai: không — test T12 chỉ dùng build_catalog/topics |
| T15 `MeasureWriter.write(received_at_ms, packet)` ↔ T16 measure mode | lưu packet nguyên văn | khớp spec §3.5 (đã sửa spec cùng lượt) |
| T16 `run(mode, minutes, out, d)` ↔ `__main__` | chữ ký thống nhất | khớp |

Task tự nhất quán: T5 test expected phải chép từ fixture thật (T4 đứng trước) — plan ghi rõ; T14 test poison dùng giá trị tràn Decimal64 thật; T16 test server giả có một assert viết gọn (`state["subs"][1] == ...replace("421","421")`) — **Ruling:** assert đó viết lại thành so sánh `args` lần 2 == `args` lần 1 (plan tự ghi chú ngay dưới). Không có task nào mâu thuẫn Global Constraints.

**Ruling (điều phối, 12:50):** hôm nay là ngày giao dịch, phiên chiều mở 13:00 — controller tự làm gấp T1 + T9 + T15(measure) + T16(measure-mode tối thiểu) để bật capture `--measure` trong phiên chiều nay làm dữ liệu bổ sung. Gate AC3 vẫn đòi phiên đo TRỌN (08:40–15:05) ở phiên kế tiếp — capture chiều nay không thay thế gate. Vì làm lệch thứ tự, các phần controller tự viết sẽ đi qua vòng review khi task tương ứng được rà lại (T9/T15/T16 vẫn được review theo diff như thường). Chi phí nếu sai: mất ~40 phút nếu không kịp giờ — chấp nhận.

## Tiến trình

- Task 1: complete (self, trong commit 302c114) — core/env.py + deps; test tests/core 2 pass.
- **Ruling (T1/T9 plan defect):** plan bảo tạo `tests/core/__init__.py`, `tests/ingester/__init__.py` — tạo xong pytest (import-mode prepend, `tests/` không có `__init__`) phân giải package tên `core`/`ingester` vào thư mục test, CHE package thật → ModuleNotFoundError. Đã xoá hai file đó; luật mới: **không đặt `__init__.py` trong `tests/<tên trùng package thật>/`**. Chi phí nếu sai: không — 18 test xanh sau sửa.
- Task 9 + 12 + 15(measure) + 16(partial: socket_loop + measure mode): complete (self, commit 302c114) — 18 test xanh. Mode run/reconcile là stub có chủ đích (gate spec §3.5), hoàn thiện ở T16.
- Fix trong 302c114: socket_loop kẹt `ws.recv()` không thấy stop → thêm task closer đóng ws khi stop bật (test i10 bắt được).
- **12:56 capture phiên chiều bật**: `--measure` nối thật, 2.007 mã CP/ETF + 14 phái sinh, 6.322 topic/64 lô, ghi `D:\twan_projects\dlck-runtime\measure\20260826`, chạy tới 15:10. 13:01: i=10.5k · o=35.8k · t=3k · idx=810 · ptm=1k frames — AC2 coi như đã chứng minh sống (sẽ xác nhận lại ở T17).
- Task 4: complete (controller) — fixture `backend/tests/etl/fixtures/omo_page.html` (phiên 25/08/2026, 2.835 byte) + `omo_page.expected.md` giải tay. **Phát hiện đo 2026-08-26: markup SBV đã đổi** (ngày ở `ls01-date` dạng "Ngày DD tháng MM năm YYYY", không còn `(dd.mm.yy)` trong tiêu đề; nhãn tổng "Tổng cộng"; kỳ hạn có tiền tố "- ") → đã cập nhật `sbv-omo.md` (kèm ngày đo) + addendum vào brief T5. Hôm 26/08 SBV còn treo phiên 25/08 lúc 13:00 — dữ kiện đầu tiên về giờ đăng bài.
- Task 11: complete (subagent sonnet, chưa commit) — dedup.py, 3 test pass.
- Task 2+3: complete (subagent sonnet, chưa commit) — etl CLI + omo_fetch, tests/etl 6 pass (8 với bộ cũ).
- Task 10: complete (subagent sonnet, chưa commit) — normalize.py, 9 test mới, 30 pass toàn bộ ingester+core. Concern của agent: chưa đối chiếu COLUMNS với DDL spec — reviewer Wave 1 được giao đối chiếu tường minh.
- 13:05 Reviewer Wave 1 (T2/3/10/11) dispatched (sonnet). Implementer T5, T13, T14, T15(reconcile) đang chạy song song.
- Task 13: complete (subagent sonnet, chưa commit) — state.py + leader.py, 3 test pass trên Redis container thật.
- Task 5: complete (subagent sonnet, chưa commit) — omo_parse.py theo markup THẬT (addendum), 7 test mới, tests/etl 13 pass. Concern giữ lại: (a) luật dòng-lạ chặt hơn pseudocode — chấp nhận (phòng thủ đúng hướng, không nới luật nào); (b) markup nhóm repo/outright_sale chưa từng quan sát — đã có trong spec §4.2, gặp phiên đầu phải đối chiếu tay.
- Task 14: complete (subagent sonnet, chưa commit) — chwriter.py, 4 test pass trên CH container thật (poison bisect, retry nguyên block, block cap); 35 test ingester xanh.
- Task 6+7 dispatched (sonnet).
- Task 15 (reconcile): complete (subagent sonnet, chưa commit) — reconcile.py + 2 test mới, 4/4 pass; agent tự đối chiếu SQL với 0002_rt_schema.sql thật.
- Task 6+7: complete (subagent sonnet, chưa commit) — omo_store.py + omo_flow.py + conftest etl, 5 test mới, tests/etl 18 pass; đã kiểm cột `trading_date` trong migration 0004 khớp SQL. Minor (deferred): nhánh `complete=true` của omo_flow chưa có test phủ — **Ruling:** chấp nhận để lại; điều kiện cần ≥140 ngày lịch sử + price_daily có dữ liệu, dựng test seed nặng; nhánh này không thể kích hoạt trong 140 ngày đầu vận hành, sẽ phủ khi ETL giá dựng xong (final review được trỏ tới dòng này). Chi phí nếu sai: cờ complete bật sai sau ~5 tháng — có thời gian dài để phát hiện.
- Task 16 dispatched (sonnet).
- Review Wave 1 (T2/3/10/11): T2 ✅ · T3 ✅ · T11 ✅ (reviewer hand-trace dedup/stamper) · T10 ❌ 2 Critical: (a) B1-3/S1-3 của `i` xếp nhầm ô UInt — DDL là Decimal64(2), giá lẻ bị NormalizeError oan; (b) `PTV` của `idx` xếp nhầm UInt — cột `pt_value` là Decimal. COLUMNS đối chiếu DDL: khớp tuyệt đối cả 5 bảng. Minor ghi nhận: cột non-nullable trade/quote không được để None khi thiếu trường → gộp vào fix round.
- Task 10: fix round 1/5 dispatched (resume implementer cũ, 2 Critical + 1 minor non-nullable defaults).
- Task 10: fix round 1/5 (3/3 addressed — re-review xác nhận bằng đối chiếu DDL + test; đếm trường khớp: i 15 dec + 16 uint = 31, idx 5+9 = 14). Residual disclose: side/top non-nullable → fix round 2.
- Task 10: fix round 2/5 — TOP thiếu/ngoài 1..3 → NormalizeError (poison), LC thiếu → side "". 14 test file, 51 toàn cụm. **Ruling:** chấp nhận round 2 KHÔNG chạy re-review riêng — thay đổi 2 dòng đúng nguyên văn toa của re-reviewer round 1, test đỏ-xanh đủ, final review toàn nhánh (opus) sẽ soi lại. Chi phí nếu sai: một khe 2 dòng lọt tới final review.
- Task 10: complete (chưa commit — commit theo mốc sau Wave 2).
- Task 8: complete (subagent sonnet, chưa commit) — omo_job orchestration, 2 test mới, tests/etl 20 pass.
- Task 16: complete (subagent sonnet, chưa commit) — run/reconcile mode wiring, make_on_packet factory, 9 test file i10, 46→51 toàn cụm. Concerns ghi nhận: standby-drop dùng mốc thời gian đơn giản (đúng gợi ý plan), init_state_watcher polling 0.2s — chấp nhận.
- 13:15 Reviewer Wave 2 dispatched (sonnet, gói 2.232 dòng diff — toàn bộ phần chưa review gồm cả code controller trong 302c114).
- Review Wave 2 về: T1/T5/T6/T7/T8/T9/T12/T13/T14/T15 ✅ spec; T16 ⚠️. 2 Critical: (1) race ChWriter.add (event loop) vs flush_once (to_thread) — mất tick im lặng được; (2) standby gọi sink.init_state khi reconnect — vỡ "chỉ leader ghi". Important: (3) measure đăng ký cả 14 mã phái sinh thay vì 2–3; (4) httpx trùng ở dev group. Minor: (5) net_fail không reset ở nhánh standby; (6) P1 log warning thay vì error; (7) thứ tự reconnect ngược spec §3.1; (8) reconcile đòi REDIS_URL không cần.
- **Ruling (Important #3):** GIỮ đăng ký đo cả 14 mã phái sinh — "2–3 mã" của roadmap §5.1 là thiết kế probe tối thiểu (sàn), không phải trần; phủ cả 14 cho biết chính xác hợp đồng nào đẩy dữ liệu, tải thêm ~280 topic không đáng kể (capture chiều nay đang chạy chính cấu hình này). Sẽ ghi rõ trong báo cáo đo. Chi phí nếu sai: không — dữ liệu thừa vô hại.
- **Ruling (Minor #8):** PARK — reconcile mode đòi REDIS_URL là over-strict nhưng nhất quán config; không sửa lượt này. Chi phí: bất tiện nhỏ khi chạy --reconcile trên máy không có Redis.
- **Resolve "cannot verify" (phân loại lỗi poison):** test T14 `test_poison_row_isolated` đã chạy trên CH THẬT và pass nhanh — nếu `_is_transient` phân loại nhầm thì test đã treo trong vòng retry; coi như đã kiểm bằng chứng cứ chạy thật.
- Fix wave 2 dispatched (resume implementer T16): Critical 1+2, Important 4, Minor 5/6/7.
- **13:4x — chủ dự án yêu cầu tiết kiệm ngân sách phiên (limit 5h còn ít):** ưu tiên capture chạy trọn tới 15:10; sau fix wave 2 chỉ chạy pytest + commit mốc rồi DỪNG. Việc dời ra phiên làm việc sau: (a) re-review scoped cho fix wave 2; (b) T17 vận hành (env/user DB/Task Scheduler/chạy thật OMO/AC2 chính thức); (c) T18 quét tài liệu sống; (d) final review toàn nhánh (opus); (e) phân tích file đo + T19 gate. Điểm nối lại: đọc ledger này từ dòng này.
- **Ruling (item "cannot verify" của reviewer — assert `TD == toDate(ts)`):** với đường parse hiện tại, `ts` dựng TRỰC TIẾP từ TD+FT nên assert là tautology — spec CH §3.1 viết assert này cho kịch bản ts đến từ nguồn khác. Chốt: không thêm assert chết; guard thật là strptime fail → NormalizeError (đã có). Nếu sau này đổi nguồn dựng ts thì bắt buộc thêm assert lại. Chi phí nếu sai: không có đường dữ liệu nào hiện tại làm TD ≠ toDate(ts).
- **15:10 capture phiên chiều 2026-08-26 ĐÓNG SẠCH** (chạy trọn 12:56→15:10, không rớt hẳn, 320 packet control = ping/pong + vài lần reconnect tự lành). Tổng frame: `o` 1.647.375 · `i` 519.133 · `t` 130.869 · `idx` 17.770 · `ptm` 1.426 · ack 64. Dung lượng **52 MB gzip** / 4 file giờ trong `D:\twan_projects\dlck-runtime\measure\20260826`. Đây là nguyên liệu phân tích SM/phái sinh/pth cho gate T19 (phiên sau phân tích offline).
- Đã commit 3 mốc: 56ba33b (track OMO) · 23dbbdb (track ingester) · 57a8728 (ledger). Toàn bộ `uv run pytest tests` = **148 passed** (AC1 tạm đạt ở mức bộ test; AC2/AC4/AC5 còn chờ T17/T19).
- **DỪNG PHIÊN TẠI ĐÂY theo yêu cầu tiết kiệm.** Việc còn lại đã liệt kê ở dòng "13:4x" phía trên.

## Phiên làm việc tiếp (2026-08-26 chiều/tối)

- Re-review fix wave 2: **6/6 ADDRESSED**, không breakage mới (stress test race chạy lại 5 lần đều xanh).
- Task 17 (vận hành): CH dev bật + migrate (`0001_roles`, `0002_rt_schema`); **Postgres dev chưa từng migrate** → chạy `alembic upgrade head` (0010); tạo user `ingester_worker` (CH) + `etl_worker` (PG), 3 biến env mới vào `.env` (mật khẩu sinh ngẫu nhiên, không in ra); `.env.example` + `scripts/register-tasks.ps1` + `backend/README.md`.
- **AC5 đạt**: `python -m etl omo` chạy thật — ghi phiên 26/08 (4 dòng đấu thầu, 5 dòng flow, HTML 406 KB vào staging, `etl_run` success, `data_domain_state` watermark). Chạy lại → `{"skipped": true}`, không ghi đè.
- **BUG THẬT do chạy thật mới lộ:** `omo_flow.rebuild` dùng `TRUNCATE` — đòi quyền chủ bảng, `dlck_etl` chỉ có DML ⇒ job chết. Test cũ không bắt vì chạy bằng user owner. Sửa `DELETE FROM` + thêm test chạy dưới `SET LOCAL ROLE dlck_etl`.
- **AC2 đạt**: `--measure --minutes 2` ngoài giờ — nối thật, 64 lô ack, file JSONL sinh ra, 0 frame dữ liệu (đúng vì thị trường đóng).
- **AC6 đạt**: 4 task OMO `Ready`, `dlck-ingester` `Disabled` (gate).
- Sửa lỗi cách ly test `test_load_run_mode_requires_db` — nó chỉ xanh khi `.env` còn thiếu khoá; giờ patch `load_dotenv`.
- **Phân tích phiên đo (agent) + kiểm chéo của controller** → phát hiện lớn: **frame thật có vỏ `{"a":…,"d":[…]}`**. Code normalize viết theo tài liệu sẽ từ chối MỌI frame thật. Đã sửa `records_of()` + `on_packet` duyệt mảng; test dùng packet nguyên văn từ capture. **Ruling:** giữ fallback "payload trần" trong `records_of` để mẫu tài liệu/test literal vẫn dùng được — chi phí nếu sai: một shape lạ lọt qua thay vì báo lỗi, đổi lại tương thích tài liệu nguồn.
- Sửa kèm: chuỗi rỗng ở `B1`/`S1` (0,12% frame `i`) → NULL thay vì đầu độc block.
- **Ruling (OP/LO):** đo được `open`/`low` CÓ đẩy, nhưng **không** thêm cột lượt này — để `extra` JSON (đúng mục đích cột đó), nâng cột là migration riêng. Chi phí nếu sai: truy vấn OP/LO phải qua JSON cho tới khi có migration.
- **Ruling (phái sinh):** đã đo được là thu được qua `i`/`o`/`t`, nhưng **không mở rộng danh mục** lượt này — spec §8 xếp phái sinh ngoài phạm vi, mở rộng cần chốt lược đồ. Chi phí nếu sai: chưa thu tick phái sinh, mất dữ liệu phái sinh cho tới khi quyết.
- Tài liệu: hồ sơ khảo sát `surveys/2026-08-26-bvsc-realtime-session/` + cập nhật `11-bvsc-realtime.md` (7 chỗ, kèm ngày đo) + roadmap §0/§5.1 + index. `git grep` bắt 2 chỗ tài liệu tự đá nhau (§11 tóm tắt và bảng roadmap §0) → đã sửa.
- Test: **161 passed** toàn backend. Commit: 1eca9a3 (ops) · c88cda2 (vỏ bọc) · 960351b (tài liệu đo).
- Minor deferred cho final review: `log_loop` ngủ 60 s nên tiến trình đo/ghi thoát trễ tối đa ~60 s sau deadline (vô hại, thấy khi smoke `--minutes 2` kết thúc lúc phút thứ 3).

## Final review toàn nhánh (opus) + đợt sửa

- **C1 (Critical, controller tự sửa ngay):** `scripts/register-tasks.ps1` đăng ký **lệnh rỗng** `python -m ` — tham số hàm đặt tên `$args`, trùng BIẾN TỰ ĐỘNG PowerShell nên thân hàm đọc ra rỗng. Cả 5 task "Ready" và chết câm ⇒ **các mốc OMO hôm nay đã lỡ**. Nghiệm thu AC6 của tôi kiểm TRẠNG THÁI task chứ không kiểm LỆNH — cùng họ lỗi với bug TRUNCATE. Đã viết lại bằng cmdlet `ScheduledTasks` + `Assert-TaskCommand` (kiểm lệnh) + restart-on-crash + chạy bù; chạy thử thật qua Scheduler: `LastTaskResult=0`, log đúng.
- **Ruling (ghi nhận sai lầm phương pháp):** mọi AC "đã đăng ký/đã cấu hình" từ nay phải nghiệm thu bằng **thứ nó thực sự chạy**, không bằng trạng thái hiển thị. Đã mã hoá thành `Assert-TaskCommand` trong chính script.
- **Ruling (reviewer nói đúng, tôi nhận):** ledger trước đó "resolve" câu hỏi phân loại lỗi poison bằng lập luận một chiều (test poison chạy nhanh ⇒ phân loại đúng). Nó KHÔNG phủ chiều nguy hiểm (transient bị đọc nhầm thành tất định = vứt sạch block) — chính là finding I1. Phán quyết cũ **sai**, đã sửa code theo I1.
- 9 finding còn lại giao một agent (opus) sửa trọn gói, TDD từng cái: C2 (bắt sai lớp exception redis-py → run() chết câm → hai người ghi) · C3 (buffer standby → ghi đôi khi tiếp quản) · I1 (đảo luật transient/tất định + `DataError`) · I4 (mutex pha xả, race mất block lúc tắt) · I6 (`_has` cho cả 5 topic) · I7 (cột non-nullable) · I2+I3 (merge base_state, lọc theo catalog) · I5 (hai cột dòng tiền OMO thành hai chiều không âm) · M1 (`join_use_nulls=1`).
- Agent tự phát hiện thêm 3 thứ trong lúc sửa: dòng độc thật ném `DataError` không kèm mã lỗi CH (phải bắt theo TYPE, không chỉ theo chuỗi); một test I4 ban đầu **pass nhầm** vì exception rơi trong thread phụ (pytest chỉ warning) — đã sửa test thu exception; `rebuild()` cắt SQL bằng `split(";")` nên dấu `;` trong chú thích tiếng Việt làm vỡ câu lệnh.
- **179 test xanh.** Đang chạy re-review scoped (opus) cho đợt sửa này.

## Re-review đợt sửa cuối (opus) — 9/9 ADDRESSED, merge được

Re-reviewer tự dựng phản chứng thay vì tin báo cáo: khôi phục bản `flush_once` cũ trong subclass (scratchpad, không sửa repo) → đo được **25.003 dòng cho 20.003 seq** (ghi đôi) + `IndexError` 3/3 lần; bản mới sạch 3/3. Cũng kiểm `join_use_nulls` trên CH thật (0 → tên rỗng, 1 → đúng mã) và giải tay lại công thức OMO hỗn hợp: `net`/`outstanding` **bằng đúng giá trị cũ từng bit**.

**Bốn minor MỚI sinh ra từ đợt sửa — park có ruling, không chặn merge:**

- **M-new-1 (đáng làm trước phiên ghi thật đầu tiên):** `_is_deterministic` dò chuỗi trong `str(e)` theo danh sách đóng — thiếu `INCORRECT_DATA` (117) và `DECIMAL_OVERFLOW` (407), và nếu server tắt `show_clickhouse_errors` thì mọi lỗi thành "transient". Hậu quả khi trượt: retry 60 s rồi **bỏ CẢ BLOCK** thay vì cô lập một dòng — đúng chiều ngược của bug vừa sửa. **Ruling:** park, nhưng ghi vào việc-phải-làm trước khi bật ghi thật (AC4); sửa rẻ: dò thêm `getattr(e, "name", "")` và bổ sung hai mã. Chi phí nếu bỏ qua: mất một block (~1 giây dữ liệu) mỗi lần gặp lỗi dữ liệu ngoài danh sách.
- **M-new-2:** lỗi tất định **không phải dữ liệu** (`UNKNOWN_TABLE`, `AUTHENTICATION_FAILED`) nay thành transient → 60 s retry mỗi block khi cấu hình sai. **Ruling:** chấp nhận — `assert_migrated` chặn từ lúc khởi động, và thà retry còn hơn vứt.
- **M-new-3:** cuối phiên, nếu thread flush đang trong backoff thì vòng chờ có trần (~3 s) hết trước khi đuôi dữ liệu kịp ghi ⇒ `reconcile()` đọc sớm → **P2 giả + exit code 1**. Dữ liệu không mất, chỉ sai phán quyết cuối phiên. **Ruling:** park; nâng trần chờ lên quá ngân sách retry (>60 s) là sửa một dòng, làm cùng M-new-1.
- **M-new-4:** `exchange`/`market` default `""` có thể `HSET` đè giá trị tốt trong Redis nếu frame thiếu `EX`. Đo được độ phủ `EX` = 100% ⇒ phòng thủ thuần. **Ruling:** park.

**Trạng thái nhánh:** 179 test xanh · 12 commit · reviewer kết luận **merge được**.

## Bốn quyết định chủ dự án 2026-08-26 (tối)

| # | Quyết định | Ghi ở đâu |
|---|---|---|
| 1 | **Backup lên Cloudflare R2**, không giữ nhiều bản trên VPS (~50 GB không đủ: chính sách 7 bản tại chỗ chạm 17–19 GB ở năm 3). Gói free 10 GB + băng thông ra miễn phí; dùng ~12–14 GB ⇒ dưới 2.000 đ/tháng | [database/README.md](../../../../database/README.md) |
| 2 | **Giữ TTL frame thô 3 tháng**, không nới 6 tháng — ràng buộc là VPS 50 GB dùng chung, không phải máy dev. Không cần migration (schema đã là 3 tháng) | [hồ sơ đo §10](../../surveys/2026-08-26-bvsc-realtime-session/README.md) |
| 3 | **Embedding `halfvec(768)`** — tối ưu dung lượng, chênh 4× so với 1536 chiều float32 (0,6 vs 2,3 GB/năm). Mô hình cụ thể còn ngỏ, chọn bằng cách đo tách tin trùng | [news-pipeline §9.5](../../../20-design/news-pipeline.md) |
| 4 | **Chưa bật ghi tick** — vẫn giai đoạn dev, hoàn thiện rồi bật một thể. `dlck-ingester` giữ DISABLED; **không session nào tự bật** | [roadmap §2 việc 4](../../../00-overview/roadmap.md) |

**Việc cần làm trước khi bật ghi tick** (theo quyết định #4): M-new-1 (bổ sung `INCORRECT_DATA`/`DECIMAL_OVERFLOW`, dò cả `e.name`) · M-new-3 (nâng trần chờ flush cuối phiên quá ngân sách retry) · một phiên `--measure` trọn ngày phủ phiên sáng + ATO.


## Đóng M-new-1 và M-new-3 (2026-08-26 tối, nhánh `fix/chwriter-error-classification-and-drain`)

Hai minor park ở đợt re-review cuối, làm trước khi bật ghi tick theo quyết định #4. TDD đỏ→xanh từng cái, **185 test xanh** toàn backend (179 + 6 mới).

- **M-new-3 — xong** (`319e7d7`). Vòng xả cuối phiên tách thành seam `drain_writer()` để lái được bằng đồng hồ giả; ngân sách **suy từ `RETRY_BUDGET_S`** (`+15 s`) thay vì viết lại số, để hai bên không trôi lệch. Xả thất bại nay log error nói rõ phán quyết reconcile bên dưới có thể sai — trước đó hỏng im lặng.
  - *Phép kiểm đỏ đúng lý do:* tách seam giữ **nguyên hành vi cũ** (trần 3 s) trước, chạy test → `assert False is True`; đổi ngân sách → xanh. Không nhảy thẳng sang bản sửa.

- **M-new-1 — xong** (`2684bc1`), **nhưng toa sửa trong ledger cũ SAI, đã sửa hướng.**

  Toa cũ: *"dò thêm `getattr(e, "name", "")` và bổ sung hai mã"*. Đo lại trên ClickHouse 26.3.22.7 thật rồi đọc `build_http_error` của `clickhouse_connect` thì thấy **`name` không cứu được lỗ mà chính toa nêu ra**:

  ```python
  code = error_code_from_header(err_code)                          # LUÔN có — từ header HTTP
  name = error_name_from_body(full_body) if show_detail else None  # None khi tắt detail
  ```

  `name` rút từ **body**, nên khi `show_clickhouse_errors=False` nó rơi cùng body, và `str(e)` rút gọn còn `"The ClickHouse server returned an error"` — sạch marker. Chỉ **`code`** sống sót vì đến từ **header**. Nên chốt: bắt theo **mã số**, chuỗi chỉ còn là đường lùi cho exception không mang mã (lỗi transport).

  Đo được kèm (2026-08-26, `errorCodeToName` trên server thật):

  | Đường lỗi | type | `code` | `name` |
  |---|---|---|---|
  | Decimal tràn qua SQL server | `DatabaseError` | 407 | `DECIMAL_OVERFLOW` |
  | Decimal tràn qua `client.insert` mảng native | `DataError` | `None` | `None` |
  | Tắt `show_clickhouse_errors` | `DatabaseError` | **còn** | `None` |
  | `UNKNOWN_TABLE` (đối chứng) | `DatabaseError` | 60 | `UNKNOWN_TABLE` |

  Dòng 2 giải thích vì sao `test_poison_row_isolated` cũ vẫn xanh dù luật sai: đường `insert()` mảng native ném `DataError`, đã được bắt **theo type** từ trước. Lỗi chỉ lộ ở đường server-side — chính là đường mà dữ liệu tick thật sẽ đi.

  Test mới phủ cả **ranh giới ngược**: `TOO_MANY_PARTS` (252) phải **giữ transient**, không được chia đôi thành 5.000 INSERT một dòng.

- **Bài học phương pháp:** toa sửa park lại trong ledger là **giả thuyết chưa kiểm**, không phải kết luận đã đo. Cùng họ với §3.4 CLAUDE.md (*mẫu trong tài liệu ≠ frame thật*): ở đây là *toa trong ledger ≠ hành vi thư viện thật*. Lần này toa đúng **triệu chứng** nhưng sai **thuốc**; đọc source thư viện mới ra.

**Còn lại trước khi bật ghi tick:** đúng một điều kiện — phiên `--measure` trọn ngày phủ phiên sáng + ATO.


## Mở gate ghi tick (2026-08-26 tối)

Chủ dự án quyết bật ghi. Điều kiện thứ ba (phiên đo trọn ngày) **không bỏ**, mà chuyển từ *chạy trước* sang *chạy song song*: `--measure` dùng `config.load(need_db=False)`, không đụng Redis/ClickHouse, không lấy leader lock ⇒ hai tiến trình độc lập. Bản thô vì thế vừa trả lời câu hỏi `SM`/ATO của [spec CH §4.1](../2026-08-25-clickhouse-realtime-store/spec.md), vừa là **lưới an toàn** cho chính phiên ghi đầu tiên — normalize từ chối frame lạ thì frame vẫn còn trên đĩa để dựng lại.

- `dlck-ingester` — BẬT, hằng ngày 08:30, `python -m ingester`.
- `dlck-ingester-measure` — **một lần** 27/08 08:30, `python -m ingester --measure`. Một lần vì gate cần đúng một ngày trọn (~110 MB gzip); chạy hằng ngày chỉ tích rác đĩa.
- `Assert-TaskCommand` thêm `-MustNotContain`: hai task nay chỉ khác nhau một cờ, lẫn nhau là **ghi hụt cả phiên mà mọi bảng trạng thái vẫn báo `Ready`**.

### 🔴 Bug chặn hẳn, bắt được nhờ chạy thật trước khi bật

Chạy `python -m ingester --minutes 2` dưới **đúng credential production** (ngoài giờ, thị trường đóng) trước khi bật:

```
Code: 497. DB::Exception: ingester_worker: Not enough privileges.
To execute this query, it's necessary to have the grant CREATE DATABASE ON rt.*. (ACCESS_DENIED)
```

`assert_migrated` — hợp đồng khởi động, gọi **trước khi nối socket** — đi qua `applied_versions` → `_bootstrap` → `CREATE DATABASE`. Role `dlck_ingester` chỉ có `SELECT, INSERT`. Ingester chết ngay dòng đầu, **mỗi phiên, im lặng**: task vẫn `Ready`, vẫn nổ đúng 08:30.

**Cùng họ với bug `TRUNCATE` của `omo_flow`, và lọt vì cùng một lý do: mọi test cũ chạy bằng user owner.** Bài học §3.5 CLAUDE.md đã viết ra rồi mà vẫn cắn lần nữa — lần này ở một đường khác (đường ĐỌC lúc khởi động, không phải đường ghi).

Sửa: `applied_versions` thành thuần đọc — hỏi `system.tables`, không có sổ thì trả rỗng (câu trả lời đúng, và để `assert_migrated` tự ném lỗi "chưa migrate" của nó); `_bootstrap` chuyển vào `upgrade()`, đường duy nhất có ghi. Test mới chạy `assert_migrated` qua user mang **đúng role production**, nên DDL quay lại đường này là bộ test đỏ chứ không phải một phiên chết.

**Nghiệm thu sau khi sửa** — chạy lại đúng lệnh đã bắt lỗi: `assert_migrated` qua · giành leader · subscribe **6.039 topic / 2.007 mã** trong 61 lô · `drain_writer` (code M-new-3 mới) chạy êm · `reconcile: p1=0 p2=0 ok=0` · **exit 0**. 0 frame dữ liệu là đúng vì thị trường đã đóng.

**188 test xanh** toàn backend.

### Việc của phiên sau (27/08)

1. Sáng: xác nhận cả hai task thật sự chạy — soi log `ingester-task.log` và `ingester-measure.log`, **không soi trạng thái task**.
2. Chiều sau 15:05: đọc `reconcile` cuối phiên, đối chiếu số dòng `rt.trade`/`rt.bar_1m` với counter trong log.
3. Phân tích bản đo trọn ngày → chốt tính chất `SM` (đơn điệu? duy nhất? bộ đếm toàn sở?) cho spec CH §4.1, và hành vi phiên ATO.
4. Sau khi phân tích xong: cân nhắc gỡ `dlck-ingester-measure` (task một lần, đã bắn thì thôi) và dọn file đo cũ.


## Review hai trục sau khi mở gate (2026-08-26 tối) — và đợt sửa

Hai reviewer opus độc lập, chạy song song, báo riêng theo §4.1. **Không finding Critical nào.** Cả hai kết luận merge được.

Điều đáng giá nhất: reviewer trục Spec **không tin commit message**, tự đọc `build_http_error` xác nhận lại khẳng định `code` (header) vs `name` (body); reviewer trục Chuẩn tự đối chiếu cả 14 mã với danh mục lỗi ClickHouse và xác nhận **không mã backpressure nào lọt vào** (252/241/159/209/210/242 đều vắng), tức hồi quy mà review trước đã vá không quay lại được qua bộ mã này.

### 🔴 Important 1 — bất biến của M-new-3 KHÔNG đứng vững. Tôi suy sai, reviewer đúng.

`DRAIN_BUDGET_S = RETRY_BUDGET_S + 15` giả định thread flush cũ kẹt tối đa `RETRY_BUDGET_S` **giây thực**. Nhưng `_write_block` cộng `spent += delay` — **chỉ thời gian NGỦ**. Thời gian nằm trong `client.insert` không vào sổ, mà driver mặc định `send_receive_timeout=300`.

Đo bằng test đồng hồ giả: server treo cho ra **8 lần thử × 300 s = 2.400 giây (40 phút)** trong khi bộ đếm mới tới 63 s — và log tự khai *"sau 63.0s retry"*, tức **log nói sai luôn**. Vượt 40 lần ngân sách, và vượt xa cửa sổ dedup ~100 s mà chính hằng số này tự khai là phải nằm dưới.

Nghĩa là comment tôi viết khẳng định một bất biến **không đúng** — nguy hiểm hơn bug gốc ở chỗ nó **trông như đã suy ra**. Test đồng hồ giả của tôi cũng không thể thấy: `_FakeClock` chỉ nhích khi `sleep`, tức mặc định insert tốn 0 giây.

**Sửa:** `_write_block` đếm thời gian thực (`self.clock()`), `ChWriter` nhận `clock` tiêm được; thêm `CH_IO_TIMEOUT_S = 20` tường minh cho client ingester (cho ~3 lần thử nằm gọn trong ngân sách; ghi 5.000 dòng bình thường dưới một giây). Nay `RETRY_BUDGET_S` mới đúng nghĩa nó tự khai.

### Các finding còn lại — đã sửa hết trong cùng đợt

| # | Trục | Việc |
|---|---|---|
| Missing 1 | Spec | Nhánh lùi (exception không mang mã) vẫn thiếu `INCORRECT_DATA`/`DECIMAL_OVERFLOW` — đã bổ sung vào `_DETERMINISTIC_MARKERS` |
| I2 | Chuẩn | `90-records/README.md` còn ghi "179 test · chờ gate" — **cột Trạng thái của index là khẳng định về HIỆN TẠI**, không phải bản ghi tại-thời-điểm, nên thuộc diện phải sửa. Quét §1.7 của tôi trượt vì grep "DISABLED/chưa bật" chứ không grep con số |
| I3 | Chuẩn | Script tự khai idempotent nhưng task `-Once` nạp lại mốc mới mỗi lần chạy — đã thêm chốt "đã tồn tại thì giữ nguyên" |
| M4 | Chuẩn | Log drop/poison nay in cả `e.code` — khi tắt `show_clickhouse_errors` thì mã là thứ DUY NHẤT còn lần ra được nguyên nhân |
| M5 | Chuẩn | `drain_writer` trả `bool` mà không ai dùng — nay xả không sạch thì in thẳng "PHÁN QUYẾT KHÔNG ĐÁNG TIN" cạnh kết quả reconcile |
| M7 | Chuẩn | Hợp đồng khởi động chỉ bắt `RuntimeError` — chính sự cố ACCESS_DENIED thoát ra dạng traceback trần, đi vòng qua hợp đồng exit 3. Nay bắt cả `ClickHouseError` |
| M8 | Chuẩn | Phần tử tuple chết trong bảng `CH_ERR` của test |
| M9 | Chuẩn | Test drain dùng biên `+5` nên nới `DRAIN_BUDGET_S` vẫn xanh — nay assert thẳng quan hệ hai hằng số, và ca hành vi lấy đúng `RETRY_BUDGET_S` làm mốc |
| M10 | Chuẩn | `Enable-ScheduledTask` không được nghiệm thu — đúng thứ commit sinh ra để đổi lại là thứ duy nhất không kiểm. Đã thêm throw |
| M11 | Chuẩn | `ParseExact('HH:mm', $null)` phụ thuộc culture — chuyển `InvariantCulture` |
| — | (tự thấy khi sửa) | Cùng index `90-records/README.md` còn dòng deploy-scaffold ghi "chờ merge" trong khi `main..feat/deploy-scaffold` = **0 commit**. Sửa luôn vì cùng file, cùng luật |

### Đã nhận, không sửa

- **M6** (thông điệp "chưa migrate" đánh lừa nếu role không thấy bảng) — **PARK**. Grant hiện tại là `SELECT, INSERT ON rt.*` nên không xảy ra, và test role thật đang phủ. Chi phí nếu sai: một lần đọc nhầm thông điệp khi ai đó đổi grant.
- **M12** (commit `27e3bbd` vào thẳng `main`) — **nhận, không đảo**. §4.7 không có ngoại lệ docs-only sau khi repo đã có code; viết lại lịch sử để sửa một commit tài liệu thì hại hơn lợi.
- **Scope creep dòng `.gitignore`** — nhận. §4.4.3 nói rác có sẵn thì báo, không tự dọn; đúng ra phải hỏi trước.
- **Cảnh báo phụ thuộc ngầm** (bộ 14 mã đủ *vì* `rt.*` chỉ dùng String/UInt/Decimal64/DateTime) — ghi lại ở đây làm mốc: **thêm cột `UUID`/`Float`/`IPv*` vào `rt.*` thì phải rà lại `_DETERMINISTIC_CODES`**, không có gì tự báo.

**190 test xanh.** Chạy lại đường ghi thật sau đợt sửa: giành leader · 6.039 topic · `reconcile: p1=0 p2=0 ok=0` · exit 0.
