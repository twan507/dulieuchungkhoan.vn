# Ledger — ETL dữ liệu tham chiếu

## 2026-08-26 (đêm) — review spec bản 1: hai đường độc lập, đối chiếu, sửa thành bản 2

Theo yêu cầu chủ dự án: một reviewer opus độc lập (không có ngữ cảnh hội thoại) + controller tự review song song, rồi controller kiểm chứng từng finding trước khi sửa.

**Đối chiếu hai danh sách:** controller tự tìm được 3/6 Critical (huỷ nhầm 18 chỉ số · `exchange` NOT NULL cho dòng FiinTrade-only · `security_external_id` thiếu luật) + 2 Important (ngưỡng 2% giòn ở N nhỏ · ngữ nghĩa `icb_industry`) — trùng độc lập với reviewer ⇒ gần chắc chắn thật. Reviewer tìm thêm 3 Critical controller trượt: **#2** lỗ phân loại cho dòng chỉ-có-ở-instruments (kéo cả 14 phái sinh vào mà không luật nào chặn) · **#4** §4.3 đảo quyết định staging của step-07 mà không nói · **#6** mốc chốt chặn đặt vào `ops.contract_snapshot` — bảng **đã có chủ khác** (bộ giám sát hợp đồng; test `test_s08` seed sẵn `getAllQuotes`).

**Kiểm chứng trước khi sửa** (không tin nguyên văn):
- #4: đúng — [step-07 §1](../2026-08-25-postgres-data-schema/step-07-staging-ops.md) bảng "KHÔNG vào staging" có dòng danh bạ, lý do *"crawl lại rẻ"*.
- #5: đúng — TVC chỉ đo 3/18 mã ([02-bvsc-tvcharts.md](../../../10-sources/market/02-bvsc-tvcharts.md)); `HNX`/`UPCOM` trả `no_data`.
- #6: đúng — `\d ops.contract_snapshot` không có status/run_id; test s08 xác nhận chủ sở hữu là bộ giám sát.
- #13 (24 issuer `QU` mồ côi), #16 (tay-thắng-máy), #19 (7 bảng · 8 FK), #23 (PK `(source, external_code)` không chứa `external_sub`): kiểm trên DB sống + step-02, đều đúng.

**Ba chỗ xử KHÁC toa reviewer** (điểm mấu chốt của vòng kiểm chứng):

1. **Critical #1 — luật huỷ niêm yết.** Toa reviewer: loại trừ `security_type='index'` khỏi tập ứng viên. Chốt khác: so với **trạng thái đích hợp nhất của lượt** (đã gồm hằng số 18 chỉ số). Cùng chặn lỗi, nhưng dạng này trả lời luôn câu hỏi mở #1 của reviewer (ETF vắng mọi nguồn ⇒ huỷ đúng) và cho chỉ số một đường huỷ có chủ đích (gỡ khỏi hằng số = thay đổi code).
2. **Critical #4 — staging.** Toa reviewer: đảo step-07 tường minh + áp luật hash. Chốt khác: **giữ nguyên step-07 cho đường bình thường**, chỉ ghi staging **khi chốt chặn từ chối** (giao dịch riêng). Được cả hai: quyết định cũ nguyên vẹn, bằng chứng khám nghiệm vẫn sống sót qua rollback, và khỏi bàn dung lượng (~1,2 GB/năm của phương án ghi mọi lượt).
3. **Critical #2 — dòng chỉ-có-ở-instruments.** Toa reviewer: thêm luật thứ năm lọc chúng. Chốt khác, mạnh hơn: **gỡ hẳn `/datafeed/instruments` khỏi lát** (4 endpoint thay vì 5) — đóng góp độc quyền đo được của nó chỉ là 14 phái sinh (đã hoãn), phần còn lại phân loại không tin được (bẫy 10). Đây là thu hẹp có chủ đích luật 5b step-02, ghi tường minh ở spec §2 + §9; endpoint quay lại cùng lát phái sinh. Tiện thể finding #8 (đếm 4 vs 5) tự khỏi.

**Các finding còn lại → bản 2:** #3 mapping `comGroupCode` (luật 5 mới) · #5 bảng hằng số 18 dòng đầy đủ + chỉ ghi TVC cho 3 mã đã đo + §3.2 cho non-index · #6 mốc dời sang `etl_run.stats` của lượt success gần nhất (luật §4.2 thành tự-thi-hành) · #7 đổi chữ "dựng lại trọn" → "tính trạng thái đích rồi áp, không xoá" · #9 `indexsnaps` chuyển khớp-tập, đếm sau normalize, thêm ca soi ngược N nhỏ · #10 cờ `--accept-drop` (§4.4) · #11 ánh xạ cột issuer + `language=vi` chốt cứng + `data_domain_state` hai dòng · #12 cổ phiếu không issuer ⇒ NULL + đếm (~400+, chủ yếu UPCOM) · #13 nối issuer `QU` cho ETF/quỹ · #14 khớp theo ticker một mình (ca chuyển sàn giữ `security_id`) · #15 ngữ nghĩa `icb_industry` đầy đủ + `ingested_at` chỉ INSERT · #16 `industry_id` không nằm trong danh sách UPDATE · #17 seam mở rộng (external_id/seam-2b, chỉ số không bị huỷ oan, assert-giao, tay-thắng-máy) · #18 phân loại instruments + `getSymbolMapping` vào §9 · #19–#24 minor đã sửa hết.

**Câu hỏi mở GIỮ LẠI cho plan/fixture** (không tự trả lời trong spec):
- Trùng ticker trong `GetListOrganization` — **chưa đo**; luật 6 định hướng xử lý, plan phải kiểm fixture thật và ghi kết quả về đây.
- Tách `etf`/`fund_cert` (luật 2b) — chưa có cách đo.
- Mã TVC của 15/18 chỉ số — chưa kiểm, không bịa.

**Trạng thái:** spec bản 2 đã commit, **chờ chủ dự án duyệt** trước khi sang `writing-plans`.


## 2026-08-26 (đêm) — chụp fixture + hai phát hiện làm sửa spec

Chụp 4 endpoint thật (8 lời gọi kể cả lượt hỏng vì lỗi đường dẫn — trong tải an toàn §4.3). Bản FULL để scratchpad ngoài repo; fixture cắt đại diện + `indexsnaps`/`icb` giữ nguyên vào `backend/tests/etl/fixtures/refdata/`.

**Đo được (2026-08-26):** `/quotes` 2.524 (StockType 2: 1.976 · 3: 31 · 4: 329 · 12: 188) · org 1.550 · indexsnaps 20 (đúng 18 mã + 2 rác `'0'`/`'indexCode'` như spec) · ICB 176 (level 11/19/40/106) · giao 18 mã ∩ symbols = **rỗng** (assert §3.1 hiện an toàn) · `comTypeCode QU` = 24 · org-only (huỷ niêm yết thật) = **4** · CP thật không issuer = **437**.

**Phát hiện 1 — đóng luật 6:** `GetListOrganization` **không có trùng ticker**. Spec sửa từ "chưa đo" thành đã đo, giữ phòng thủ.

**Phát hiện 2 — bẫy mới, sửa luật 2:** **14 bản ghi `StockType=2` không phải cổ phiếu** — quyền mua ("Quyền L40 03.06.2026"), tín phiếu Kho bạc (`TPKB16003`), TPCP (`TD1623483`) dán nhãn 2. Nạp theo luật 2 bản cũ là 14 mã rác vào `market.security`. Vá: cổ phiếu = StockType 2 **và** symbol khớp `^[A-Z0-9]{3}$` (1.962 mã thoả — khớp phân bố độ dài). Cùng họ bẫy 3/4 của roadmap §6: *nhãn nguồn tự khai không khớp dữ liệu nguồn tự trả*.

Fixture chọn có chủ đích: `ACV`/`VHM` (organCode≠ticker) · `SHB` (NH) · `HTB`+1 (CP không issuer) · `L40_WFT_01` (ca rác StockType=2) · `FUEMAVND` (ETF khớp QU) · `E1SSHN30`/`FUEVCDIV` (ETF không QU) · `EGL`/`FUCTVGF4` (org-only ⇒ delisted) · 2 CW + 2 bond (ca bị bỏ).
