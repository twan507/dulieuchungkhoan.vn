# SDD ledger — plan: docs/90-records/plans/2026-09-03-screener-daily-etl/plan.md

Sổ thực thi. Nhánh `feat/screener-daily-etl` từ `70da066` (main). Artifact tạm (brief, report, gói diff review) ở scratchpad ngoài repo — **không** `.superpowers/` trong repo. Mỗi task: implementer Sonnet (model chỉ định tường minh) → review hai trục (spec + chất lượng) → vòng sửa ≤ 5.

## Rà xung đột tiền-thực-thi (2026-09-03)

| Cặp / task | Bên sản xuất | Bên tiêu thụ | Kết quả |
|---|---|---|---|
| T1 ↔ T2 | `market-field-selection.json` 193 dòng Screener, `keep is True` | `KEEP` nạp `keep is True`, test đếm lại từ chính JSON | khớp — test không phụ thuộc con số 77 |
| T2 ↔ T3 | `fetch() -> (pages: list[str], retries)` | `normalize(pages: list[str])` | khớp |
| T2 ↔ T4 | `ScreenerRow.close_price` | test guard đếm `r.close_price > 0` | khớp |
| T2 ↔ T5 | `ScreenerRow.ticker/exchange/trading_date/payload` | `merge`, `apply` | khớp |
| T3 ↔ T6 | `fetch(post=None, sleep=…)` | job gọi `fetch()`; test patch `lambda: (pages, 0)` | khớp |
| T4 ↔ T6 | `check(total_count, collected, priced, unmapped, baseline)` | job truyền `collected = len(rows) + unknown_com_group` | **xung đột 1** — xem ruling |
| T5 ↔ T6 | `load_baseline/merge/apply/store_refusal_evidence/upsert_domain_state` | job | khớp |
| T5 nội bộ | `apply` set `ingested_at = now()` | test `t2 > t1` trong **một** transaction (fixture `db`) | **xung đột 2** — `now()` là giờ bắt đầu transaction |
| T3 nội bộ | test `test_paginates…` | dòng `assert all(b == 30 for b in [30])` | **xung đột 3** — assert rỗng, rubric coi là lỗi |
| T1 nội bộ | số đếm dự kiến `keep True 77 / False 112 / None 4` | tiêu chí đỗ | chỉ **193 dòng** và **thiếu = []** là tiêu chí; ba số kia ghi số thật |
| T2 nội bộ | `SELECTION_JSON = parents[2]/docs/…` | `backend/etl/x.py` → parents[2] = gốc repo | đúng |
| T6 nội bộ | fixture POST có `totalCount = 1545` nhưng chỉ 30 item (một trang) | guard (ii) `collected != total_count` | cùng gốc với xung đột 1 |
| T8 | đăng ký task Scheduler cần shell **elevated** | shell agent không elevated (đo 2026-09-03) | bước 2–4 do chủ dự án chạy — điểm dừng hợp lệ (side effect ngoài worktree) |

**Ruling 1 (T6 test):** fixture một trang mang `totalCount 1545` ⇒ guard (ii) từ chối là **đúng** với code; sai là ở test. `_patch` trong `test_e15` phải ghi đè `totalCount` = số item của trang (30) trước khi tiêm — `json.loads → d["totalCount"] = len(d["items"]) → json.dumps` — kèm comment nói rõ vì sao. `counts.items` kỳ vọng **30**. — *Vì:* spec §5.4 (ii) là hợp đồng, test phải mô phỏng một lượt đủ trang. — *Nếu sai:* test giả trang đầy đủ hơi lỏng; lượt thật AC3 (52 trang) mới là nghiệm thu.

**Ruling 2 (T5 apply):** nhánh `DO UPDATE` đặt `ingested_at = clock_timestamp()` thay vì `now()`. — *Vì:* `now()` đóng băng theo transaction nên test một-transaction không phân biệt được hai lượt; `clock_timestamp()` là giờ câu lệnh, tương đương production (mỗi lượt job một transaction). — *Nếu sai:* không có hậu quả dữ liệu; chỉ là mốc ghi lệch vài ms so với `now()`.

**Ruling 3 (T3 test):** bỏ dòng `assert all(b == 30 for b in [30])` — assert rỗng; `pageSize == 30` đã được kiểm ở `test_body_sends_exactly_one_criterion_and_page_size_30`. — *Nếu sai:* không.

**Ruling 4 (T1 số đếm):** tiêu chí đỗ T1 = 193 dòng Screener + `thiếu = []` + §7.3 "Chưa liệt kê" = 0. Số `keep` ghi số đếm thật vào ledger; **không** sửa cho bằng 77. — *Vì:* spec §4.3.

**Ruling 5 (worktree):** dùng nhánh trong cùng checkout, không worktree — implementer chạy tuần tự (không song song), và worktree không có `.venv` (bài học post-session 28/08). — *Nếu sai:* không có agent song song nên không có rủi ro giẫm commit.

## Tiến độ

- Task 1: implementer DONE (commit 72f3200, agent ae5c983bfe7abb8e0) — 193/193, keep True 77 · False 112 · None 4, unlisted 0. Chờ review.
- Task 1: review sạch (sonnet a3b026bfbaa837db3) — 2 mục ⚠️ tự kiểm: README.md không có hit "80/193"; cả 193 khoá của HAI mẫu thật đều có dòng. Task 1: minor (deferred): `gen_field_selection.py:770` — mục nhật ký §9 đề ngày 2026-08-15 render số tổng HIỆN TẠI ({total_rows}…) nên số của dòng lịch sử trôi theo mỗi lần sinh — đặc tính có sẵn của generator, không do task này; đưa vào review cuối.
- Task 1: complete (commits 70da066..72f3200, review clean)
- Task 2: implementer DONE (commit a77aff7, agent a37c4e5627bc231ca) — 6/6, full suite 327 passed 2 skipped. Chờ review.
- Task 2: review (sonnet ada72893826b09677) — 1 Important **plan-mandated**: `screener_normalize.py:66,68` truy cập `pi["tradingDate"]`/`pi["ticker"]` không guard ⇒ một item thiếu khoá làm KeyError cả lượt. **Ruling 6:** giữ nguyên, không sửa — `ticker`/`tradingDate` là khoá BẮT BUỘC của hợp đồng nguồn; thiếu là nguồn đổi schema, job phải **chết to** (spec §5.1: mọi Exception → `etl_run failed`, exit 2, không ghi gì) chứ không được lặng lẽ bỏ dòng (00-conventions §10.5). Chạy lại cùng ngày sau khi soi là lấy lại được. *Nếu sai:* một dòng hỏng chặn screener một ngày cho tới khi có người nhìn — chấp nhận được, và đó chính là tín hiệu giám sát hợp đồng [8] cần. Task 2: minor (deferred): `log` khai báo không dùng (`screener_normalize.py:14`); `import pytest` thừa trong test_e11; `_row()` trả tuple 3 ngôi hơi khó đọc. ⚠️ số 327 chưa tự chạy — review cuối chạy trọn bộ.
- Task 2: complete (commits 72f3200..a77aff7, review clean với 1 parked-by-ruling)
- Task 3: implementer DONE (commit 5171201, agent afd76995a32411e87) — 4/4, bộ 331 passed 2 skipped. Chờ review.
- Task 3: review sạch (sonnet a781da87ae74eb4b5). Task 3: minor (deferred): `screener_fetch.py:146-155` `int(json.loads(first)["totalCount"])` không guard — thiếu/null thì TypeError/KeyError thay vì FetchError (plan-mandated; job vẫn failed loud). Task 3: minor (deferred): `totalCount == 0` không có test (code trả 1 trang, không rỗng).
- Task 3: complete (commits a77aff7..5171201, review clean)
- Task 4: implementer DONE (commit bdeaee0, agent a3649c0aef0b1e081) — 5/5, bộ 336 passed 2 skipped. Chờ review.
- Task 4: review sạch (sonnet a048965fa0f23cf74) — test clause (i) trên fixture pre-open thật là load-bearing (bỏ clause (i) thì test đỏ). Task 4: minor (deferred): `screener_guard.py:45` có `collected > 0 and` — chặn ca chia cho 0, plan-mandated, vô hại.
- Task 4: complete (commits 5171201..bdeaee0, review clean)
- Task 5: implementer BLOCKED (agent ab5fb6fadea34560e, chưa commit) — 5/5 file riêng xanh; cả bộ 3 fail: `_seed_securities` INSERT mù đụng unique `(ticker, exchange) WHERE status=listed` vì `test_e10` (job refdata thật) đã commit `CLI/UPCOM` vào DB test ngoài rollback. **Ruling 7 (lỗi plan T5):** `_seed_securities` đổi sang `INSERT … SELECT … WHERE NOT EXISTS (… ticker=:t AND exchange=:e AND status='listed')` — y khuôn `_seed` của T6 trong plan; các assert giữ nguyên (mã có sẵn vẫn map được, số mapped/unmapped không đổi). *Nếu sai:* chỉ ảnh hưởng test.
- Task 5: implementer DONE sau Ruling 7 (commit b446ec3) — 5/5, bộ 341 passed 2 skipped. Chờ review.
- Task 5: review (sonnet aa3a065a09e9d12f2) — 1 Important plan-mandated: `test_refusal_evidence_and_domain_state` (migrated_engine, không rollback) chỉ dọn raw_payload TRƯỚC, không dọn SAU, và không dọn `data_domain_state(market.scores)` bao giờ ⇒ để rác committed trong DB test. Kiểm chéo: T6 `_seed` xoá raw_payload source=screener trước khi chạy và domain_state là upsert nên không vỡ test nào — nhưng vẫn là lỗi vệ sinh của plan. **Ruling 8:** sửa (vòng 1) — dọn cả hai bảng trước VÀ sau, y khuôn `test_baseline_reads_items_of_last_success`. *Nếu sai:* không.
- Task 5: fix round 1/5 (1 addressed, 0 open — dọn cả hai bảng trước và sau; commit b446ec3..4d76162; re-review sonnet ab613194a9cfbab89 sạch). Task 5: minor (deferred): khối dọn sau assert không nằm trong try/finally (cùng khuôn với test baseline có sẵn) — assert đỏ thì để rác.
- Task 5: complete (commits bdeaee0..4d76162, review clean sau 1 vòng sửa)
- Task 6: implementer DONE (commit bb87d71, agent a8f716da8f70b8125) — 4/4 kể cả test dưới role dlck_etl, bộ 345 passed 2 skipped. Chờ review.
- Task 6: review sạch (sonnet adf7c9bb358a459eb) — guard trong engine.begin(), bằng chứng ghi sau rollback, test role thật sự chạy mọi truy vấn dưới dlck_etl. Task 6: minor (deferred): test_e15 seed/dọn ĐẦU mỗi test nhưng không teardown cuối (cùng khuôn test_e10).
- Task 6: complete (commits 4d76162..bb87d71, review clean)
- **Ruling 9:** review toàn nhánh chạy NGAY sau T6 thay vì sau T8 — T7 là nghiệm thu chạy thật bị khoá theo giờ (AC3 sau 15:05, AC5 trước 09:00 hôm sau), T8 cần cửa sổ admin của chủ dự án; cả hai không sinh code ngoài 3 dòng ps1 (sẽ có re-review riêng ở T8). *Nếu sai:* T8 thêm code thì phải review bổ sung — chi phí một lượt re-review nhỏ.
- Controller tự chạy `uv run pytest tests` 2026-09-03: **345 passed, 2 skipped, 1 warning** (StarletteDeprecationWarning có sẵn của fastapi/testclient, không thuộc lát này) — khớp báo cáo T6.
- **Review cuối toàn nhánh** (opus aaca98e752e290621, 70da066..bb87d71): 1 Critical · 5 Important · 8 Minor · triage minor treo. Verdict "With fixes". Rulings cho đợt sửa duy nhất (brief: scratchpad `final-fix-brief.md`):
  - **Ruling 10 (Critical #1 — lỗi SPEC):** 10 khoá keep có ở cả `stockScreenerItem` lẫn `financial`; `rtq12/rtq27/rtq83` **khác nhau 52/90 cặp, có đổi dấu**. Spec §2.1 chỉ xét kích thước, không xét hai bản có bằng nhau — lỗi của tôi khi viết spec. Quyết tạm **không mất dữ liệu**: giữ cả hai bản, thêm `dup_conflicts` vào stats, ghi rõ ở §5.5 và spec; **khối chuẩn cho 3 mã là quyết định của chủ dự án** (cần nghĩa mã) — treo ở spec §9.4. *Nếu sai:* consumer phải chỉ rõ khối khi đọc — đã ghi doc; không có gì bị xoá nên đảo được.
  - **Ruling 11 (Important #1, reproduce được):** test_e15 để 30 security committed trong DB test ⇒ đảo thứ tự file làm guard huỷ niêm yết của refdata nổ. Sửa: fixture module-scoped có finalizer dọn theo id; e14 dọn trong try/finally. Ghi thêm phép kiểm chạy đảo thứ tự vào nghiệm thu.
  - **Ruling 12 (Important #2):** clause (i) đổi từ `priced > 0` sang tỷ lệ `MIN_PRICED_RATIO = 0.5` — một mã lẻ có giá trong ngày lễ không được mở cửa ghi 1.545 dòng ma; phiên thật 30/30 vẫn qua. Chuỗi lý do đổi theo, test cập nhật literal. *Nếu sai:* phiên nào <50% mã có giá sẽ bị từ chối — không có phiên nào như vậy.
  - **Ruling 13 (Important #3):** thêm clause (iv) `unknown_com_group ≤ 2%` — nguồn đổi tên sàn thì không được im lặng mất trọn một sàn.
  - **Ruling 14 (Important #4 + minor T1):** bảng đối soát §7.1/§7.2 của file sinh không khép (64/112, 59/77) vì 66 khoá mang block tag mới; dòng nhật ký 2026-08-15 bị render số hiện tại (viết lại quá khứ — §1.7); thiếu dòng nhật ký 2026-09-03. Sửa generator, hard-code dòng 08-15, thêm dòng 09-03, chứng minh sinh lại byte-bằng-byte.
  - **Ruling 15 (Minor #6):** 4 mã `rtd39 rtd53 rtd54 rtq81` đang `keep=None` (cần kiểm API) bị bỏ dù có giá trị thật — áp cùng luật chủ dự án đã duyệt hôm nay cho 13 mã ("lưu trước, giải mã sau") ⇒ `keep=True`, `chưa giải mã`; keep dự kiến 81. *Nếu sai:* thừa 4 khoá jsonb, bỏ qua được — chi phí ~0, còn không lưu thì mất theo ngày.
  - **Ruling 16 (Minor #7):** bằng chứng từ chối lưu **trang 1** (đủ cho vế i/iii/iv), lưu mọi trang khi lý do là "thiếu trang" — tránh ~9,6 MB jsonb mỗi ngày nghỉ vào staging không có retention.
  - **Ruling 17 (Important #5):** `backend/README.md` là index sở hữu job backend mà spec §8/plan T8 bỏ sót, grep kiểm của T8 cũng không quét `backend/` — sửa README ngay trong đợt này, mở rộng T8 Bước 5.
  - Minor #8 (đọc `docs/` lúc import): **giữ nguyên, nợ đã ghi** (spec/plan) — xử lý khi đóng gói ETL vào container. Minor #9/#10/#11/#12/#13: sửa trong đợt (nhỏ).
  - Triage minor treo: T1 §9 row → sửa (Ruling 14); T5/T6 dọn DB → sửa (Ruling 11); các minor còn lại giữ treo theo lời reviewer.
- Đợt sửa review cuối: DONE_WITH_CONCERNS (opus a263e37182e01f75c), 8 commit bb87d71..780a0ec; fixer báo tests/etl 91, bộ 349 passed 2 skipped, đảo thứ tự e15→e10 xanh, generator sinh lại byte-bằng-byte. Concerns: (1) brief §E.1 tự mâu thuẫn — fixer chọn hàng "Ngoài nhóm 48" + sửa nhãn (hợp lý); (2) §7.2 cần thêm hàng 4 mã flip vì keep=81; (3) sửa 4 đoạn văn arithmetic; (4) chưa đụng: spec §5.5 còn ghi `now()` (Ruling 2 là clock_timestamp) và 10-fiin-dictionary:290 "113 trường bị bỏ" vs 112 — controller sẽ đồng bộ sau re-review. Chờ re-review.
- Re-review đợt sửa (sonnet a2241a083ac2c59c4): **A–I đều ADDRESSED, không có breakage mới**; Skip #8 nguyên vẹn. Hai quan sát ngoài phạm vi (spec §5.5 `now()`, 10-fiin-dictionary "113") controller đồng bộ ở commit bc58fd5. Controller tự chạy: bộ 349 passed 2 skipped 1 warning; đảo thứ tự e15→e10: 8 passed.
- **Review cuối: ĐÓNG.** Còn lại theo plan: Task 7 (chạy thật AC3/AC4 sau 15:05 ngày giao dịch, AC5 trước 09:00 hôm sau) và Task 8 (đăng ký task trong cửa sổ admin của chủ dự án, để Disabled). Nhánh CHƯA merge cho tới khi AC3 có số.

## Vòng giải mã 2026-09-03 (~10:40) — chủ dự án yêu cầu "check luôn mấy mã"

**Bốn lời gọi thật** *(trong mức đã đo an toàn)*: `GetScreenerItems` trang 1 · `GetScreenerParameters` *(lưu ở `samples/screener-params-20260903.json`)* · HTML app · `main.42cb52b1.chunk.js` (3,06 MB).

**Kết quả 1 — khối chuẩn: `stockScreenerItem`.** Hai bằng chứng độc lập: bundle khai bản đồ cột `"stockScreenerItem.rtq12"` cho ROE; đẳng thức ROE = LNST(TTM) × P/B ÷ vốn hoá cho `stockScreenerItem` sai số trung vị 8,1 % (4/22 mã khớp trong 2 %) vs `financial` 23,0 % (0/22). Giả thuyết "`financial` là kỳ khác" **bị bác** (0/26 khớp `rqq`/`ryq`). Thử đo riêng `rtq83` bằng `isa20TTM/isa20Y − 1`: **không kết luận được**, cả hai bản lệch >76 % ⇒ công thức thử sai, ghi nguyên trạng.

**Kết quả 2 — 🔴 sửa lỗi của chính tôi.** `roe` `grossMargin` `profitGrowth` `revenueGrowth` trả **chuỗi** `'Tốt'`/`'Trung bình'`/`'Cảnh báo'` — **nhãn xếp hạng**, thuộc nhóm chấm điểm chủ dự án đã loại. Vòng 09-03 đầu tiên xếp nhầm vào tỷ số vì suy nghĩa từ **tên khoá** thay vì đọc **giá trị** — đúng bẫy §3.4 mà tài liệu dự án đã ghi. Lật về `keep=False` ⇒ keep **81 → 77**.

**Kết quả 3 — đặt tên 11/13 mã:** `rtd53` EPS Forward · `rtq81` T.trưởng lợi nhuận (YoY) *(bundle, nhóm `pr`)* · `rtd54` P/E Forward *(suy theo hàng xóm, chưa chắc)* · `rqd25` P/B quý · `rqd52` T.trưởng EPS quý *(cả hai **60/60 null**)* · `rtq160`/`rtq166`/`rtq176` T.trưởng KD/LN ròng/vốn CSH 3 năm (TTM) · `ryq4` Nợ dài hạn/VCSH năm · `rtd20`/`rtd36Avg` tỉ suất cổ tức. **Chưa giải:** `fryq30`, `rtd39` — không có ở bundle chính lẫn chunk vendor.

- **Ruling 18:** khối chuẩn `stockScreenerItem`, mỗi mã lưu **một bản** (`BLOCK_PRIORITY`); `financial` chỉ giữ 7 mã riêng nó. Làm **trước Task 7** vì kho chưa có dòng nào ⇒ đổi hình dạng payload lúc này miễn phí, sau AC3 thành lịch sử. Giữ `dup_conflicts` làm chỉ báo sức khoẻ nguồn. *Nếu sai:* `rtq27`/`rtq83` lấy nhầm khối — đảo được bằng một dòng `BLOCK_PRIORITY` + chạy lại ngày đó.
- **Ruling 19:** 4 nhãn xếp hạng → `keep=False` (không cần hỏi lại: quyết định "không dùng điểm bên thứ ba" đang đứng, đây là sửa lỗi phân loại). *Nếu sai:* mất 4 nhãn theo ngày — nhưng chúng là điểm bên thứ ba, đúng thứ đã loại có chủ đích.

Nghiệm thu: `tests/etl` **93 passed** · cả bộ **351 passed, 2 skipped** · đảo thứ tự e15→e10 **8 passed** · generator sinh lại **byte-bằng-byte** (không sửa tay). Payload DDB: **77 khoá, 0 trùng lặp**, `financial` = đúng 7 mã.

**Vòng hai cùng ngày — chủ dự án hỏi "chốt nguồn rồi thì `financial` còn dùng được không".** Đi kiểm 7 mã còn lại thì bắt thêm một chỗ tôi xếp nhầm: **`isa3` (Doanh số thuần) và `isa5` (Lãi gộp) không phải tỷ số** — từ điển 729 mã xếp chúng vào `chi_tieu_bao_cao_tai_chinh`, `bao_cao=ket-qua-kinh-doanh`, y hệt `isa1`/`isa20`/`isa22` đã bị bỏ theo luật đang đứng *"nguồn chuẩn cho mọi mã `bs*` `is*` `cf*` `no*` là bộ 556 mã"*. Lý do tôi viết cho chúng (*"không rơi vào nhóm bỏ nào"*) **sai sự thật**.

- **Ruling 20:** `isa3`/`isa5` → `keep=False`, nguồn chuẩn **BCTC đầy đủ**, block `Trùng BCTC (đo 2026-09-03)`. Biến thể TTM/Y (`isa3TTM`…) **giữ nguyên** vì BCTC không cấp kỳ TTM — đúng lý do cụm TTM/Y được giữ trọn từ đầu. ⇒ keep **77 → 75**; `financial` còn **5 mã** (`fryq30` `rtd39` `rtd53` `rtd54` `rtq81`), đều họ tỷ số/thị trường mà cả `stockScreenerItem` lẫn BCTC đều không có. *Nếu sai:* mất doanh thu/lãi gộp theo ngày từ Screener — nhưng BCTC có đủ hai chỉ tiêu này theo quý, và lấy hai nguồn cho cùng chỉ tiêu chính là "trộn nguồn" mà `architecture.md` §3.4 cấm.

Nghiệm thu vòng hai: cả bộ **351 passed, 2 skipped** · generator sinh lại **byte-bằng-byte** · payload DDB **75 khoá** (`stockScreenerItem` 70 + `financial` 5), 0 trùng lặp.

## Task 7 — chạy thật 2026-09-03 (GIỮA PHIÊN, theo yêu cầu chủ dự án)

Chủ dự án chốt: giai đoạn dev không cần dữ liệu EOD, cần ETL chạy đúng. Nên hai lượt dưới đây chạy lúc **13:38 và 13:40**, giữa phiên — **KHÔNG đóng AC3** (AC3 đòi sau 15:05, khi nguồn đã chốt giá phiên). Chúng nghiệm thu **đường chạy**, không nghiệm thu ảnh chụp EOD.

```
lượt 1  13:38:28  exit 0  {'counts': {'items': 1545, 'pages': 52, 'priced': 831, 'trading_dates': 1},
                           'rows_written': 1541, 'unmapped': 4, 'unknown_com_group': 0,
                           'null_blocks': 5, 'dup_conflicts': 3348, 'retries': 0,
                           'trading_date': '2026-09-03'}   — 69,8 s
lượt 2  13:40:17  exit 0  y hệt, priced 832  → kho VẪN 1.541 dòng, 1 trading_date  (idempotent ✅)
```

Kiểm trên DB: `screener_daily` **1.541 dòng / 1.541 mã / 1 ngày** · `etl_run` hai lượt `success` · `data_domain_state('market.scores','fiintrade')` watermark `2026-09-03` · payload **70 `stockScreenerItem` + 5 `financial` = 75 khoá**, đúng thiết kế. Giá trị thật hợp lý: ACB ROE 16,3 % P/E 8,4 · FPT 26,5 % / 12,5 · VNM 33,9 % / 11,9 · HPG 17,4 % / 8,0.

**Ba phát hiện của lượt chạy thật:**

1. 🔴 **Ngưỡng guard quá sát — đã sửa.** Toàn thị trường giữa phiên chỉ **831/1545 = 53,8 %** có giá (nhiều mã UPCOM chưa khớp), trong khi `MIN_PRICED_RATIO` đặt **0.5** — chỉ hơn 3,8 điểm. Ngưỡng cũ suy từ số đo **trang 1** (30/30 sau phiên vs 0/30 trước mở cửa), không đại diện toàn thị trường. **Ruling 21: hạ 0.5 → 0.2.** Hai hậu quả lệch hẳn nhau: từ chối nhầm một phiên thật = **mất vĩnh viễn** ảnh chụp ngày đó (Screener không backfill), nhận nhầm ngày nghỉ = vài dòng ma xoá được. 0.2 nằm giữa 0 % (không phiên, đo 2 lần) và 53,8 % (phiên thật tệ nhất đo được). *Nếu sai:* một ngày nghỉ mà nguồn vẫn trả >20 % mã có giá sẽ lọt — chưa quan sát thấy ca nào như vậy.
2. ✅ **Ca `status:"Success"` + `items:null` CÓ THẬT** — gặp ngay ở lời gọi thăm dò lúc 13:37. Đây đúng ca reviewer Task 3 nêu ra và `_valid()` đã chặn bằng `isinstance(items, list)`. Hai lượt chạy sau đó `retries = 0`.
3. **4 mã `unmapped` truy được nguyên nhân:** `refdata` đỏ 3 ngày liên tiếp (01·02·03/09, `guard refused: sắp lật delisted 438 mã`) nên danh bạ đứng ở **31/08**; 4 mã Screener mới chưa có trong `market.security`. Không phải lỗi lát này — lượt dọn `--accept-drop` chạy xong là hết.

**Còn lại của lát:** AC3/AC5 thật (sau 15:05 và trước 09:00 hôm sau) · Task 8 (đăng ký task, cần cửa sổ admin).

## AC3 · AC4 — lượt thật SAU PHIÊN 2026-09-03 15:06 và 15:08

```
AC3  15:06:14  exit 0  {'counts': {'items': 1545, 'pages': 52, 'priced': 1545, 'trading_dates': 1},
                        'rows_written': 1541, 'unmapped': 4,
                        'unmapped_tickers': ['EGL/UPCOM','FUCTVGF4/HOSE','FUCTVGF5/HOSE','FUEKIVND/HOSE'],
                        'unknown_com_group': 0, 'null_blocks': 5, 'dup_conflicts': 3348,
                        'retries': 0, 'trading_date': '2026-09-03'}          67 s
AC4  15:08:53  exit 0  y hệt                                                 29 s
```

Kho sau hai lượt: **1.541 dòng · 1.541 mã · 1 trading_date** — không đổi ⇒ **idempotent ✅**. Giá trị EOD hợp lý: ACB ROE 0,1633 P/E 8,39 P/B 1,32 · FPT 0,2647 / 12,48 / 3,15 · VNM 0,3386 / 11,88 / 4,09.

**🎯 `priced` = 1545/1545 = 100 % sau phiên** — cùng ngày đo được ba mức: **0 %** trước mở cửa · **53,8 %** giữa phiên · **100 %** sau phiên. Ngưỡng `MIN_PRICED_RATIO = 0.2` (Ruling 21) vì thế có biên rất rộng ở cả hai phía; ngưỡng cũ 0.5 thì chỉ hơn mức giữa phiên 3,8 điểm. Số đo xác nhận việc hạ ngưỡng là đúng.

**4 mã `unmapped` — nguyên nhân thật, công cụ vừa vá trả lời ngay:** `EGL/UPCOM` `FUCTVGF4/HOSE` `FUCTVGF5/HOSE` `FUEKIVND/HOSE`, cả bốn mang `status='delisted'` trong `market.security`. Chúng thuộc nhóm `fiin_only_delisted` của refdata — có trong danh bạ FiinTrade nhưng **vắng khỏi bảng giá BVSC**, nên refdata cố ý lật `delisted`.

🔴 **Nhưng giả định đó SAI với bốn mã này:** cả bốn có `closePrice > 0` sau phiên hôm nay (nằm trong 1545/1545), tức **vẫn đang giao dịch** — chỉ là BVSC không niêm yết chúng trên bảng giá. Ba trong bốn là chứng chỉ quỹ (`FUC*`/`FUE*`). Đây là **lỗi phân loại của refdata**, không phải của lát screener; 4/1545 = 0,26 %, dưới ngưỡng guard 2 % nên không chặn. *(Sửa trước đây tôi đoán sai hai lần: lần đầu bảo do danh bạ cũ — bác bởi lượt refdata thành công `sec_inserted: 0`; lần này mới có tên mã nên truy được.)*

**Mục treo mới cho refdata:** *"vắng khỏi `/quotes` của BVSC" ≠ "đã huỷ niêm yết"* — cần một luật phân biệt, hoặc một `status` thứ ba (kiểu `not_on_bvsc`). Chưa gấp: 4 mã, và hệ quả chỉ là screener không ghi được 4 dòng/ngày.

**Trạng thái AC:** AC1 ✅ · AC2 ✅ (351 passed, 2 skipped) · **AC3 ✅** · **AC4 ✅** · AC5 ⏳ *(chạy trước 09:00 mai, phải bị từ chối)* · AC6 ⏳ *(cần cửa sổ admin của chủ dự án)*.
