# Review trục SPEC — vòng 3 (vòng cuối trước merge), lát 10, nhánh `feat/semantic-layer`

**Ngày:** 2026-09-07 · **Reviewer:** độc lập, chỉ đọc · **HEAD lúc review:** `ef00826`, cây sạch
**Thước đo:** `spec.md` (§1 · §4.2–§4.7 · §6 · §7 · §9), `plan.md`, `ledger.md`, `regression-round7.md`, `round7-results-2026-09-07.md`; hai báo cáo vòng trước dùng để **không lặp lại**, chỉ để kiểm "đã đóng thật chưa".

**Đã chạy để tự kiểm — không đọc code rồi tin:**

- `pytest tests -q` toàn bộ ⇒ **986 passed, 2 skipped in 82.33s**; `pytest tests/agent -q` ⇒ **109 passed in 3.47s**
- **Gọi thẳng cả 9 function** trên kho dev qua `AGENT_DATABASE_URL` (role `dlck_api`): **52 lời gọi**, phủ ca có dữ liệu · mã không tồn tại · sai loại chứng khoán (index · etf · fund_cert · delisted) · khoảng rỗng · vượt trần · tham số sai kiểu
- Truy vấn chỉ-đọc `market.security`, `market.corporate_event`, `macro.observation_spliced`, `ops.llm_call` để dựng ca biên và đối chiếu số
- `git grep` bốn phép kiểm AC10; `git diff main...HEAD` toàn bộ tài liệu §9
- **Không gọi model thật.** Không sửa file nào trong repo.

---

## 0. Tóm tắt

| | Số |
|---|---|
| **CHẶN** | **1** *(cụm AC10 — tài liệu sống nói sai cấu hình đang xuất xưởng)* |
| **NÊN SỬA** | 6 |
| **GHI NHẬN** | 8 |
| **DƯ (scope creep)** | **không tìm thấy** |

**Ba câu trả lời ngắn cho ba câu hỏi của đề bài:**

1. **Các trường mới có nằm trong bốn hình dạng §4.6 không?** `tong_khop` và `da_cat` — **có**, chúng là trường phụ trên hình dạng #4, cùng họ với `ngay_du_lieu`/`ghi_chu` mà spec đã cho phép. `khoang_co_du_lieu` — **spec gọi tên đúng trường này**, nhưng code dùng **hai bộ khoá con khác nhau** (`tu`/`den` với ngày, `tu_nam`/`den_nam` với năm) và mới vá **2/5** chỗ cần. `ly_do` mới của `compare_peers` và hình dạng chuẩn hoá của `get_industry_tree` — **KHÔNG nằm trong bốn hình dạng**: chúng là hai tổ hợp mới (§2, N1 và N6). Ngoài ra kho hiện có **hai hình dạng nữa chưa từng được đặt tên ở bất cứ đâu**: `{"loi": true, …}` (6/9 function) và `{"kieu": "danh_muc", …}` (§3 G6). Không chỗ nào trong tài liệu **sống** mô tả bốn hình dạng, nên không có nơi để ghi cái thứ năm.
2. **`MAX_TOKENS = 32000` có phá con số ngân sách nào không?** **Không phá số học** — §4.3 tính theo token *thực dùng*, `max_tokens` là trần. Ledger `ef00826` ghi đủ quyết định + số đo. Nhưng **tài liệu thiết kế sống vẫn ghi `8000`** (§2 C1), và bảng AC8 được đo dưới cấu hình **khác** cấu hình sắp merge (§3 G2).
3. **AC4 đứng lại chưa?** **Có, phần "dữ liệu sai" đã hết** — `compare_peers(["ABCDE"])` nay trả hình dạng "không tìm thấy", tôi gọi lại và xác nhận. Nhưng AC4 nói *"trả **đúng** dữ liệu thật"*, và bản sửa đó **đánh rơi hai trường mà §4.6 gọi tên** (`ma_da_tra`, `goi_y`) — xem N1. Tôi xếp AC4 là **đạt**, kèm ghi chú.

---

## 1. Tám bản sửa của đợt 2 — có làm lệch thêm không?

| # | Bản sửa | Đóng đúng chỗ? | Có đẻ lệch mới? |
|---|---|---|---|
| 1 | `compare_peers`: mọi mã tra trượt ⇒ dừng | ✅ **đóng thật.** `so_sanh_cung_nganh(["ABCDE"])` → `{"tim_thay": false, "khong_tim_thay": ["ABCDE"], "so_dong": 0, "du_lieu": []}` — không còn 10 mã bất kỳ. Có test `test_hoi_toan_ma_khong_ton_tai_thi_khong_tra_ma_bat_ky`, **và** test đối xứng giữ nhánh lọc-theo-ngành | ⚠️ **có** — hình dạng trả về **không phải** #1 của spec: mất `ma_da_tra` và `goi_y`, mượn `so_dong`/`du_lieu` của #4. Xem **N1** |
| 2 | `get_corporate_events` chuyển sang `issuer_id is None` | ✅ **đóng thật, và sửa đúng theo §3.6.** `FUCVREIT` (etf) → **14 sự kiện thật**, gồm 2 `CashDividend`; `FUCTVGF4` (fund_cert, delisted) → 5 sự kiện; `VNINDEX` → hình dạng #2. Test `test_etf_co_issuer_van_tra_su_kien_that_khong_phai_hinh_dang_2` canh đúng chỗ cũ hỏng | ⚠️ nhẹ — `ly_do` viết bằng thuật ngữ lược đồ cho model đọc (§3 G5) |
| 3 | `get_price_series` thêm `da_cat`/`tong_khop` | ✅ **đóng thật.** `gia_theo_ngay(BT6)` → `so_dong: 400, da_cat: true, tong_khop: 5764`, `ghi_chu` nói rõ đây là phiên **gần nhất**, không phải phiên đầu khoảng. `tong` đếm trước `LIMIT` nên cờ suy từ kết quả thật | Không |
| 4 | `get_financials` + `get_corporate_events` thêm `khoang_co_du_lieu` | ✅ **đóng đúng hai hàm reviewer gọi tên.** `bao_cao_tai_chinh(HPG,1990,1991)` → `khoang_co_du_lieu: {"tu_nam":2005,"den_nam":2026}`; `su_kien_doanh_nghiep(HPG, 1990…)` → `{"tu":"2007-12-07","den":"2026-09-03"}` | ⚠️ **có** — vá **đúng và chỉ đúng** hai hàm được điểm danh; `get_macro_series` và `get_news` còn nguyên khuyết tật y hệt. Xem **N2** |
| 5 | `get_news` đổi cách khoá revision (`JOIN` + `NOT EXISTS`) | ✅ **đóng thật.** Không nhân đôi (`test_join_revision_khoa_ban_moi_nhat_khong_nhan_doi`), vị từ `tsv` nằm lại trên `article_revision`. Gọi thật: `tim_tin("lãi suất điều hành")` chạy bình thường, `phraseto`→`kieu_tim: "cum"`, chuỗi vô nghĩa → 0 dòng | Không. *(Một chi tiết bé: nhánh không-`query` đếm `tong` trên `news.article` **không** join revision — bài không có revision nào sẽ vào `tong` mà không vào `du_lieu`. Trên kho hiện tại không xảy ra.)* |
| 6 | `get_industry_tree` chuẩn hoá hình dạng | ⚠️ **đóng nửa.** Nhánh **cây** nay có `tim_thay/co_du_lieu/so_dong` ✅. Nhánh **ticker** không đụng tới: vẫn thiếu `loai`, và `ly_do` vẫn nói sai loại. Xem **N6** | ⚠️ nhánh cây sinh tổ hợp `co_du_lieu:false` + `so_dong:0` **không có** trong bốn hình dạng |
| 7 | `screen_stocks` chặn `bool` | ✅ **đóng thật.** `value: True` → `{"loi": true, "ly_do": "value phai la so, nhan duoc: True"}`; test `test_criteria_value_bool_bi_tu_choi_khong_lot_qua_isinstance_int` | Không |
| 8 | `chat.py` đổi điều kiện nhận lịch sử + `MAX_TOKENS` 4.000 → 32.000 | ✅ **đóng thật.** Điều kiện nay là **hình dạng lịch sử** (`not any(b.type == "tool_use" …)`), không phải `stop_reason` — ba test canh ba đường (`cham_tran_vong_lap`, `het_max_tokens_giua_luot_cong_cu`, `max_tokens_ma_luot_cuoi_chi_co_chu`). 32.000 có ledger + số đo | ⚠️ tài liệu sống không theo kịp: xem **C1** |

**Kết luận mục 1:** mẫu *"sửa đúng triệu chứng, sai phạm vi"* của hai đợt trước **không lặp lại theo chiều quét-quá-tay** — đợt 3 không có bản sửa nào làm mất dữ liệu thật hay tạo dữ liệu sai. Mẫu hỏng của đợt này **đảo chiều**: sửa **hẹp hơn** phạm vi thật — vá đúng những hàm reviewer điểm danh, bỏ những hàm cùng bệnh mà không ai gọi tên (N2), và bỏ luôn các mục NÊN SỬA của vòng 2 mà không sửa cũng không ghi nợ (N3, N4, N5, N6).

---

## 2. Bảng 9 function × các ca — gọi thật, đối chiếu §4.4 và §4.6

Cột "hình dạng" ghi số hình dạng §4.6 mà kết quả thật rơi vào; ✗ nghĩa là không khớp hình dạng nào.

| # | Function | Ca có dữ liệu | Ca mã không tồn tại | Ca sai loại chứng khoán | Ca khoảng rỗng |
|---|---|---|---|---|---|
| 1 | `get_price_series` | ✅ #4 — `HPG` 60 phiên, `da_cat:false`, `tong_khop:60`; `BT6` 400/5.764 `da_cat:true` | ✅ #1 — `{"tim_thay":false,"ma_da_tra":"ZZZZ","goi_y":[]}` | ✅ #2 — index / etf / fund_cert đều có `loai` + `ly_do` riêng; `delisted` thêm `trang_thai` | ✅ #3 — `khoang_co_du_lieu:{"tu":"2026-06-09","den":"2026-09-03"}` |
| 2 | `get_financials` | ✅ #4 — `HPG` 8 kỳ, tên hiển thị đúng bảng nhãn, `-2.633,6 tỷ VND` giữ dấu | ✅ #1 | ✅ #2 — index `"kho không có báo cáo tài chính cho chỉ số"`; etf/fund_cert có câu riêng | ✅ #3 — `{"tu_nam":2005,"den_nam":2026}` ⚠️ **khoá con khác** `tu`/`den` mà §4.6 viết |
| 3 | `get_corporate_events` | ✅ #4 — `HPG` 20 sự kiện, `da_cat:true`; **`FUCVREIT` (etf) 14 sự kiện** | ✅ #1 | ✅ #2 — chỉ `VNINDEX` (không `issuer_id`); etf/fund_cert **không còn bị chặn nhầm** | ✅ #3 — `{"tu":"2007-12-07","den":"2026-09-03"}` |
| 4 | `compare_peers` | ✅ #4 — `["HPG","HSG"]` đủ 7 tỷ số, `ngay_du_lieu:"2026-09-04"` | ⚠️ **✗** — `{"tim_thay":false,"khong_tim_thay":[…],"so_dong":0,"du_lieu":[],"ly_do":…}`; **không** `ma_da_tra`, **không** `goi_y` (**N1**) | ✅ tách ba loại đúng: `["HPG","VNINDEX","ZZZZ"]` → `khong_tim_thay:["ZZZZ"]` + `khong_co_du_lieu_phien:["VNINDEX"]` | ✅ #3 — ngành lạ → `so_dong:0` + `ngay_du_lieu` |
| 5 | `screen_stocks` | ✅ #4 — 3 mã, `da_cat` đúng; `exchange="HOSE"` lọc đúng | ✅ lỗi có cấu trúc — mã chỉ tiêu lạ, `criteria` sai dạng, `value` bool đều `{"loi":true,…}` | n/a (không nhận ticker) — ngành lạ → #3 | ✅ #3 — `{…,"so_dong":0,"ngay_du_lieu":"2026-09-04"}` |
| 6 | `get_industry_tree` | ✅ 24 ngành / 6 nhóm; ticker `HPG` → `nganh`+`nhom`+`nguon_gan:"icb"` | ✅ #1 | ⚠️ **#2 khuyết `loai`**, và `ly_do` nói *"quỹ/ETF theo thiết kế không có ngành"* cho **`VNINDEX` là chỉ số** (**N6**) | ⚠️ **✗** — `industry_code` lạ → `{"tim_thay":true,"co_du_lieu":false,"so_dong":0,"nhom":[]}` (tổ hợp #2+#3, không có trong bốn hình dạng) |
| 7 | `get_macro_series` | ✅ #4 — `us.cpi` (macro), `btc` (ohlc), `wti` (price_daily có `loai_gia`); `vn.gdp.real` trả `gia_tri_cong_bo` đúng §4.4 #8 | ✅ #1 — `{"tim_thay":false,"ma_da_tra":"khongco.xyz","goi_y":[]}` | n/a — thay bằng **danh mục**: `{"kieu":"danh_muc",…}` ⚠️ **thiếu khoảng ngày** spec §4.4 #8 đòi (**N5**) | ⚠️ **#3 khuyết** — `{"tim_thay":true,"co_du_lieu":true,"so_dong":0,"ma":"us.cpi"}`, **không** `khoang_co_du_lieu` (**N2**) |
| 8 | `get_news` | ✅ #4 — `tong_khop:1033`, `da_cat:true` khi xin 999 (cắt về 30), `kieu_tim:"cum"` | ✅ #1 — `resolve_ticker` chạy trước, **không** còn đổ lỗi "chưa phân loại" | ✅ ticker index có thật ⇒ 0 bài + `ghi_chu` đúng nguyên nhân | ⚠️ **#3 khuyết** — `{"…","so_dong":0,"tong_khop":0,"kieu_tim":"cum","du_lieu":[]}`, không `khoang_co_du_lieu` (**N2**) |
| 9 | `load_knowledge_reference` | ✅ `valuation` trả nội dung bắt đầu bằng tiêu đề thật | ✅ lỗi có cấu trúc kèm 9 chủ đề hợp lệ | ✅ `../../../etc/passwd` và chuỗi rỗng đều bị từ chối ở **cả** schema (`enum` 9 giá trị, đã dump) lẫn thân hàm | n/a |

**Hình dạng thật đang tồn tại — đếm đủ.** Ngoài bốn hình dạng §4.6 (đều có mặt và đều đúng ở phần lớn hàm), kho đang có thêm:

| Hình dạng | Ở đâu | Có được đặt tên ở đâu chưa? |
|---|---|---|
| `{"loi": true, "ly_do": …, "<danh sách hợp lệ>": […]}` | 6/9 function (mã chỉ tiêu lạ, loại sự kiện lạ, `sub` lạ, `criteria` sai dạng, `topic` lạ) | **Chưa.** Không có trong §4.6, không có trong tài liệu sống. Nhất quán trong code, nhưng là hình dạng thứ năm trên thực tế |
| `{"kieu": "danh_muc", "danh_muc": […], "tong_khop", "da_cat"}` | `get_macro_series` | §4.4 #8 cho phép **khái niệm** danh mục, nhưng không nói nó nằm ngoài bốn hình dạng (không có `tim_thay`/`co_du_lieu`) |
| `{"tim_thay":false, "khong_tim_thay":[…], "so_dong":0, "du_lieu":[]}` | `compare_peers` | **Chưa** — N1 |
| `{"tim_thay":true,"co_du_lieu":false,"so_dong":0,"nhom":[]}` | `get_industry_tree` | **Chưa** — N6 |

Thêm một cái bẫy tên: khoá **`khong_tim_thay`** mang **hai nghĩa** — trong `compare_peers` nó là *mảng mã*, còn `_shared.khong_tim_thay()` là *hàm sinh hình dạng #1*. Vòng 2 đã gợn chuyện này (G2); nay bản sửa N1 làm nó nặng thêm vì `compare_peers` dùng **cả hai** trong cùng một payload.

---

## 3. Lệch — phân loại, mức, trích cam kết, trích thực tế

### C1 · SAI · 🔴 **CHẶN** — AC10 tự khai "không còn chỗ đá nhau", nhưng bốn chỗ tài liệu **sống** đang nói sai trạng thái nhánh

**Cam kết** — spec §7 AC10: *"Tài liệu §9 đã cập nhật, **không còn chỗ đá nhau** — chạy phép kiểm `git grep` của §1.7, dán kết quả"*. Và `round7-results` §4 khai **AC10 ✅**. CLAUDE.md §1.7: *"Bỏ sót một chỗ là để tài liệu tự đá nhau"*; §1.6: *"Index lệch cây là nói dối"*.

**Thực tế** — bốn chỗ, tất cả đều do **chính bốn commit cuối** tạo ra:

| Chỗ | Tài liệu nói | Code / cây nói |
|---|---|---|
| `docs/20-design/chatbot-semantic-layer.md:98` | *"Sửa: nâng lên **`8000`**"* | `backend/agent/chat.py:36` — `MAX_TOKENS = 32000` |
| `docs/00-overview/roadmap.md:154` và `:436` | *"**976 test** (877 → +99)"*, *"**976 test xanh**, 2 skipped"* | `pytest tests -q` ⇒ **986 passed, 2 skipped** |
| `docs/90-records/README.md:44` | *"**AC5 chỉ 2/4** (hai câu từ chối chạy mà không lưu transcript)"* | `acceptance-transcript-2026-09-07.md` có **đủ 4/4** + một ca nửa-trong-nửa-ngoài; `roadmap.md:151` đã sửa lên 4/4 |
| `docs/90-records/README.md:44` | liệt **11/13 file**, gọi là *"**hai** báo cáo review"*, và khai *"tất cả đã sửa"* | thư mục có **13 file**, **bốn** báo cáo review (thiếu `review-chuan-v2`, `review-spec-v2`); bốn mục NÊN SỬA của vòng 2 vẫn còn mở (N3–N6 dưới) |

Chỗ nặng nhất là dòng đầu: `chatbot-semantic-layer.md` là **tài liệu thiết kế sống** — nơi CLAUDE.md §1.1 bắt phải mang đủ tri thức vận hành. Nó đang nói cấu hình xuất xưởng là `8000` trong khi nhánh merge `32000`. Đây đúng họ *"sửa số mà không đo"* của §1.2, chỉ khác chiều: **đo rồi mà không sửa số ở chỗ có chủ**. Ledger `ef00826` ghi rất kỹ quyết định 32k — nhưng ledger nằm ở `90-records/`, tức bản ghi tại-thời-điểm, **không phải nhà của sự thật này**.

Chỗ thứ tư là chỗ mà **vòng 2 đã bắt một lần rồi** (commit `34071fc` — "plans index listed 5 of 11 files"): index lại lệch cây, lần này vì chính hai báo cáo vòng 2 được thêm vào sau khi index đã viết.

**Đề xuất** *(≈ 5 dòng sửa, không đụng code)*: `chatbot-semantic-layer.md:98` đổi `8000` → `32000` kèm một câu ghi lý do và ngày; `roadmap.md:154`/`:436` và `90-records/README.md:44` đổi `976` → `986`; `90-records/README.md:44` sửa AC5 lên 4/4, thêm hai file `*-v2-*`, và bỏ chữ *"tất cả đã sửa"* (thay bằng con số thật của các mục còn mở); rồi **chạy lại phép kiểm §1.7 và dán output mới** vào `round7-results` §8 — vì §8 hiện dán kết quả grep của một cây đã đổi bốn commit.

---

### N1 · THIẾU · NÊN SỬA — hình dạng "không tìm thấy" mới của `compare_peers` đánh rơi đúng hai trường §4.6 gọi tên

**Cam kết** — spec §4.6, hình dạng #1, nguyên văn: `{"tim_thay": false, "ma_da_tra": "XYZ", "goi_y": [...]}`. Và cùng §4.6: *"**Gợi ý mã** (hình dạng #1) chạy trên `market.security.ticker` + `market.issuer.name`/`short_name` bằng `extensions.similarity`"*.

**Thực tế** — gọi thật, cùng một mã gõ nhầm, hai function:

```
so_sanh_cung_nganh(["HPGG"])
→ {"tim_thay": false, "khong_tim_thay": ["HPGG"], "so_dong": 0, "du_lieu": [],
   "ly_do": "không mã nào trong danh sách tồn tại trong danh bạ"}

gia_theo_ngay("HPGG")
→ {"tim_thay": false, "ma_da_tra": "HPGG", "goi_y": ["HPG"]}
```

`compare_peers` **đã tính ra gợi ý rồi vứt đi**: vòng phân giải viết `(ma_hop_le if resolve_ticker(conn, t)["tim_thay"] else khong_ton_tai).append(t)` — `resolve_ticker` trả về nguyên hình dạng #1 kèm `goi_y`, code chỉ lấy cờ `tim_thay`. Nhánh thoát sớm rồi tự dựng payload bằng tay thay vì gọi helper `khong_tim_thay()`.

**Vì sao đáng sửa dù không phải CHẶN.** Nó không tạo dữ liệu sai — chỗ nguy hiểm của vòng 2 đã bịt. Nhưng đây là ca **người dùng gõ nhầm mã**, ca thường gặp nhất của một chatbot; ở tám function khác model nhận được *"ý bạn là HPG?"*, riêng ở đây model nhận về một câu phủ định trơ và phải tự đoán. Test mới (`test_hoi_toan_ma_khong_ton_tai_thi_khong_tra_ma_bat_ky`) assert `du_lieu == []`, `so_dong == 0`, `khong_tim_thay == ["ABCDE"]` — **không** assert `goi_y`, nên chỗ hở này không có ai canh.

**Đề xuất:** khi danh sách chỉ có **một** mã, trả thẳng `khong_tim_thay(ma, goi_y)` của `_shared`; khi nhiều mã, giữ mảng `khong_tim_thay` nhưng gộp thêm `goi_y` (hợp nhất gợi ý của từng mã) và bỏ `so_dong`/`du_lieu` cho khỏi lai hình dạng. Thêm assert `goi_y` vào test hiện có.

---

### N2 · THIẾU · NÊN SỬA — `khoang_co_du_lieu` vá đúng hai hàm được điểm danh, hai hàm cùng bệnh còn nguyên

**Cam kết** — spec §4.6 hình dạng #3 viết trường bắt buộc: `{"tim_thay": true, "co_du_lieu": true, "so_dong": 0, "khoang_co_du_lieu": {"tu": "…", "den": "…"}}`.

**Thực tế** — gọi thật, bốn hàm cùng rơi vào "khoảng ngày rỗng":

```
gia_theo_ngay(HPG,"1990-01-01","1990-12-31") → …"khoang_co_du_lieu":{"tu":"2026-06-09","den":"2026-09-03"}   ✅
bao_cao_tai_chinh(HPG,1990,1991)             → …"khoang_co_du_lieu":{"tu_nam":2005,"den_nam":2026}          ✅ (khoá con khác)
chuoi_vi_mo("us.cpi","1900-01-01","1900-12-31") → {"tim_thay":true,"co_du_lieu":true,"so_dong":0,"ma":"us.cpi"}  ❌
tim_tin("lãi suất", from="1990-01-01", to="1990-12-31") → {…,"so_dong":0,"tong_khop":0,"kieu_tim":"cum","du_lieu":[]} ❌
```

Vòng 2 (M6) nêu đích danh `get_financials` và `get_corporate_events`; bản sửa `5943534` vá **đúng và chỉ đúng** hai hàm đó. `get_macro_series` là chỗ khuyết tật **đau nhất** trong bốn: model tìm được mã qua danh mục, hỏi một khoảng, nhận `so_dong: 0` mà không biết chuỗi bắt đầu từ năm nào — trong khi `macro.observation_spliced` sẵn `min/max(obs_date)` chỉ một câu đếm.

Đây là **mẫu hỏng của đợt 3**: hai đợt trước sửa **rộng quá** phạm vi bug; đợt này sửa **hẹp bằng đúng danh sách reviewer đọc tên**. Cả hai đều là "sai phạm vi".

**Đề xuất:** thêm một câu `min/max` cho nhánh rỗng của `get_macro_series` (cả ba nhánh macro / price_daily / ohlc) và của `get_news` (khoảng ngày có bài). Đồng thời **thống nhất khoá con** — hoặc luôn `tu`/`den` (năm ghi thành `"2005"`/`"2026"`), hoặc ghi rõ trong `_shared.rong()` rằng khoá con do bên gọi quyết; hiện `rong(khoang)` nhận `dict` bất kỳ nên hai bộ khoá cùng tồn tại mà không ai canh.

---

### N3 · SAI · NÊN SỬA — docstring `llm_log` vẫn khẳng định điều code không làm *(lần thứ ba bị nêu)*

**Cam kết** — spec §4.7: *"`'failed'` cho mọi kết thúc khác (`max_tokens`, chạm `max_iterations`, exception) kèm `error` mô tả"*. Và `backend/agent/llm_log.py:6` chép lại nguyên câu đó: *"`'failed'` dành cho `'max_tokens'`, chạm max_iterations, và exception."*

**Thực tế** — `log_llm_call` chỉ được gọi **bên trong** `for message in runner` (`chat.py:51`), và chỉ đọc `message.stop_reason`:

- **chạm `max_iterations`**: SDK dừng ngay sau một lượt `tool_use` ⇒ dòng cuối ghi `stop_reason='tool_use'` ⇒ **`status='ok'`**, không có dòng `failed` nào.
- **exception**: `except` nằm ở `repl` (`chat.py:99`), ngoài vòng lặp ⇒ **không ghi dòng nào**.

Kiểm chứng gián tiếp trên `ops.llm_call` (53 dòng `purpose='chat'`): chỉ có `('failed','stop_reason=max_tokens',3)` và một dòng `('failed','stop_reason=tool_use',1)` — dòng cuối là di tích của **ánh xạ cũ** trước khi sửa; không có dòng nào cho `max_iterations` hay exception.

Vòng 1 ghi là G3 *("lệch thật, chưa ghi ở đâu")*; vòng 2 nâng lên M2 vì bản sửa **viết docstring khẳng định điều chưa có** — đúng loại §3.2. Vòng 3: **vẫn nguyên**, và vẫn không có dòng nợ nào trong `ledger.md` §"Nợ".

**Đề xuất:** chọn một trong hai, đừng để lửng — hoặc ghi dòng `failed` ở `chat.py` khi `not ket_sach` và trong `except` của `repl`; hoặc sửa docstring thành *"chỉ phủ `max_tokens`; `max_iterations` và exception chưa có dòng sổ — nợ"* **và** thêm dòng đó vào ledger. Cái rẻ hơn là vế thứ hai.

---

### N4 · SAI · NÊN SỬA — câu đính chính overclaim vẫn nêu tên một test không tồn tại

**Cam kết** — `round7-results-2026-09-07.md:81`, đoạn viết ra để **đóng** lỗi §3.2 của vòng 1:

> *"Hai test còn thiếu đã bổ sung sau lượt review (`test_ket_thuc_sach_nhung_khong_co_chu_van_khong_tra_rong` cho lỗi 1, **`test_luot_tool_use_ghi_so_la_ok`** cho lỗi 3)."*

**Thực tế** — `grep -rn "test_luot_tool_use_ghi_so_la_ok" backend/` ⇒ **0 hit** (chỉ ra hai file tài liệu: chính câu này, và báo cáo vòng 2 chỉ ra nó). `test_a12_tools_log.py` có đúng 6 test, không tên nào như vậy. Phép kiểm `tool_use → 'ok'` **có thật**, nằm bên trong `test_ghi_so_duoi_role_etl_that`.

Vòng 2 (M3) đã nêu và đề xuất câu thay thế. Không sửa, không ghi nợ. Một dòng chữ — nhưng nó nằm trong đúng đoạn văn viết ra để chữa loại lỗi "khẳng định chưa grep".

**Đề xuất:** đổi thành *"nhánh `tool_use` bổ sung vào `test_ghi_so_duoi_role_etl_that`"*.

---

### N5 · THIẾU · NÊN SỬA — danh mục `get_macro_series` vẫn thiếu khoảng ngày; và `compare_peers` báo `da_cat` sai

Hai mục nhỏ cùng thuộc quy ước §4.4, cùng bị vòng 2 nêu, cùng chưa xử lý.

**(a) Danh mục thiếu khoảng ngày.** Spec §4.4 ghi chú #8: *"`code=None, keyword=...` ⇒ trả **danh mục** chuỗi khớp (**mã + tên + đơn vị + khoảng ngày**)"*. Gọi thật:

```
chuoi_vi_mo(keyword="dầu")
→ {"kieu":"danh_muc","danh_muc":[{"ma":"diesel_vn","ten":"Giá dầu diesel bán lẻ","don_vi":"VND/lít","nguon":"asset"}, …],
   "tong_khop":4,"da_cat":false}
```

Có `nguon` (không ai xin), **không có khoảng ngày** (spec xin). Danh mục là **cửa duy nhất** để model tìm mã, nên thiếu khoảng ngày ⇒ model chọn mã xong vẫn phải gọi thêm một vòng để biết chuỗi có phủ khoảng nó cần không. Vòng 1 (§2.7a) và vòng 2 (M5) đều nêu.

**(b) `da_cat` báo nhầm khi xin đúng 10 mã.** Spec §4.4: *"vượt trần thì cắt và ghi `da_cat: true`"* — trần của #5 là *"≤ 10 mã"*. Gọi thật với **đúng 10 mã hợp lệ, không mã nào bị cắt**:

```
so_sanh_cung_nganh(["HPG","HSG","NKG","SSI","VCB","VND","FPT","MWG","MBB","CTG"])
→ {"tim_thay":true,"co_du_lieu":true,"so_dong":10, …, "da_cat": true}
```

Nguyên nhân: `da_cat = len(mas_xin) > TRAN_MA or len(rows) >= TRAN_MA` — vế sau bật cờ mọi lúc kết quả **chạm** trần, kể cả khi chẳng cắt gì. Vòng 2 đã chỉ ra trong G1; docstring `cap_limit` cũng chốt nghĩa mới là *"kết quả **bị cắt**"*, tức chính hàm này đang lệch với luật nó viết ra. Cùng lỗi ngược lại: **cắt `metric_codes` thì hoàn toàn câm** — xin 9 mã chỉ tiêu, hàm giữ 8 rồi trả 7, `da_cat: false`.

**Đề xuất:** (a) thêm `min/max(obs_date)` vào hai nhánh của `_SQL_DANH_MUC` (macro và asset); (b) tách cờ theo nguyên nhân — `da_cat` chỉ khi `len(mas_xin) > TRAN_MA` hoặc (dùng `industry_code`) khi tổng mã của ngành > `TRAN_MA` đếm riêng; thêm cờ cho phần `metric_codes` bị cắt.

---

### N6 · SAI · NÊN SỬA — `get_industry_tree` chuẩn hoá nhánh cây, bỏ quên nhánh ticker (và `ly_do` vẫn nói sai loại)

**Cam kết** — spec §4.6: *"Phân biệt bằng trường tường minh, **không** bằng độ dài mảng"*; hình dạng #2 nguyên văn có **`loai`**: `{"tim_thay": true, "co_du_lieu": false, "ly_do": "…", "loai": "index"}`.

**Thực tế** — gọi thật:

```
cay_nganh(ticker="VNINDEX")   → {"tim_thay":true,"co_du_lieu":false,"ma":"VNINDEX",
                                 "ly_do":"mã này chưa được gán ngành (quỹ/ETF theo thiết kế không có ngành)"}
cay_nganh(ticker="E1VFVN30")  → y hệt câu ly_do đó
cay_nganh(industry_code="KHONGCO") → {"tim_thay":true,"co_du_lieu":false,"so_dong":0,"nhom":[]}
```

Ba chỗ lệch: (1) nhánh ticker **thiếu `loai`** nên model không biết đây là chỉ số hay quỹ; (2) `ly_do` nói *"quỹ/ETF"* cho một **chỉ số** — sai loại, và là một khẳng định *"theo thiết kế"* áp cho đối tượng chưa kiểm, đúng họ §3.6; (3) nhánh cây sinh tổ hợp `co_du_lieu:false` + `so_dong:0` **không nằm trong bốn hình dạng** (#2 không có `so_dong`, #3 có `co_du_lieu:true`).

Vòng 2 nêu ở G6 và ghi rõ *"một trong hai mục NÊN SỬA của trục Chuẩn không được sửa mà cũng không được ghi là nợ"*. Bản sửa `b937ba2` **có chạm đúng file này** (F7) và sửa nhánh cây — nhưng nhánh ticker, tức chỗ vòng 2 mô tả kỹ hơn, thì không.

**Đề xuất:** nhánh ticker dùng `khong_co_du_lieu(ma["loai"], ly_do)` của `_shared` với `ly_do` viết theo `ma["loai"]` thật (chỉ số / quỹ / mã chưa gán ngành); nhánh cây khi 0 dòng trả `{**rong(), "nhom": []}` hoặc `khong_co_du_lieu("industry_code", …)` để không đẻ tổ hợp thứ năm.

---

## 4. `MAX_TOKENS = 32000` — có phá ngân sách nào không?

**Cam kết đọc lại nguyên văn.** Spec §4.2 khối mã ghi `max_tokens=4000`, và mô tả nó là tham số của `tool_runner`, không kèm luật nào cấm đổi. Spec §4.3 chốt **ngân sách theo số REQUEST**, mọi dòng trong bảng là **token vào**, riêng dòng cuối *"Đầu ra (thinking + trả lời) — ≈ 1.500 token"*. §7 AC8 đòi *"Chi phí và độ trễ thật mỗi câu được đo"*. §8 xếp *"`max_iterations=8`, `REMINDER` chưa đo hiệu quả"* vào nợ.

**Kiểm số.** Đọc `ops.llm_call` (`purpose='chat'`, 53 dòng):

```
gio (UTC)      status  n   ra_p50  ra_max  ms_max
2026-09-06 18  failed  4    3999    4000   41816     <- thời max_tokens=4000, chạm trần thật
2026-09-06 18  ok     38     668    3748   35198
2026-09-06 19  ok      5    1579    5989   38019     <- thời 8000
2026-09-07 00  ok      3     186    3493   29990     <- thời 32000
2026-09-07 01  ok      3    1697    3589   37267     <- thời 32000
```

**Kết luận: không phá con số nào.** `max_tokens` là trần, không phải mục tiêu; §4.3 tính theo token thực dùng và đỉnh quan sát được sau khi nới là **3.589** — thấp hơn cả đỉnh 5.989 đo ở thời `8000`. Lý lẽ của ledger đứng vững, và ledger `ef00826` ghi đủ: trích nguyên văn quyết định chủ dự án, khai *"MiniMax **nhận** `max_tokens=32000`"* kèm bảng 4 request thật, và tự khai **một quan sát chưa xử lý** (câu trả lời trôi sát ranh giới khuyến nghị) thay vì im lặng. Đó là cách ghi đúng.

**Hai chỗ hồ sơ chưa theo kịp** *(không phải lỗi số học)*:

- `chatbot-semantic-layer.md:98` — tài liệu **sống** vẫn ghi `8000`. Xem **C1**.
- Bảng AC8 (`round7-results` §3) đo **47 request / 22 câu** dưới cấu hình `4000`→`8000`; sổ nay có **53 dòng**, và cấu hình sắp merge là `32000`. Xem **G2** dưới.

---

## 5. Bảng AC1–AC10 — trạng thái tại `ef00826`

| AC | Bằng chứng có gì | Bằng chứng có chứng minh đúng điều AC nói? | Kết |
|---|---|---|---|
| **AC1** `tool_runner` × MiniMax | Ledger Task 0 dán nguyên văn `SCHEMA:` + hai dòng `STOP:` + `SO LAN TOOL CHAY THAT: 1` | ✅ Có — chạy thật, đóng luôn A1/A2/G6/G8 trước khi xây gì | ✅ **đạt** |
| **AC2** không test xanh thành đỏ | `round7-results` §7 dán **cả hai** dòng tóm tắt (`main` 877 / nhánh 976) | ✅ Về thực chất: tôi chạy lại nhánh ⇒ **986 passed, 2 skipped**; `tests/agent` **109**; 2 skipped ở cả hai phía ⇒ **không skip mới**; 109 ≥ 7 seam §6. ⚠️ Con số dán trong hồ sơ (**976**) đã **mục 10 test** so với cây | ✅ **đạt**, số cần cập nhật (C1) |
| **AC3** đọc dưới `dlck_api`, role không ghi được | §7 dán nguyên văn `thuoc dlck_api: True` · `co quyen INSERT: False` · `ghi bi chan dung: ProgrammingError` | ✅ Tôi tự kiểm lại: 52 lời gọi function qua `AGENT_DATABASE_URL` chạy tốt, `assert_read_only()` nằm trong `read_engine()` nên **chạy trên đúng đường khởi động** của `python -m agent` (`__main__.py:26`). Lệch chữ "chạy tay `python -m agent`" đã được vòng 2 chấp nhận là đủ về thực chất | ✅ **đạt** |
| **AC4** cả 9 function trả **đúng** dữ liệu thật | S4+S5 xanh (109 test); `round7-results` §2 liệt 9/9 function model gọi đúng chỗ | ✅ **Đứng lại rồi.** Tôi gọi thẳng cả 9 function, 52 ca (bảng §2): **không ca nào trả dữ liệu sai**, ca CHẶN của vòng 2 đã bịt. Số đối chiếu được: `HPG` P/E 7,89 lần · ROE 17,38% · BVPS 16.683 đ/cp trùng khít số spec §4.5.1 dùng làm ví dụ; `vn.gdp.real` trả `gia_tri_cong_bo` đúng §4.4 #8. ⚠️ Còn **hình dạng** lệch ở 4 chỗ (N1, N2, N6) — không phải "dữ liệu sai" | ✅ **đạt** |
| **AC5** 4 câu ngoài lĩnh vực bị từ chối gọn trong một câu | `acceptance-transcript` §AC5.1–5.4 đủ **4/4** (ẩm thực · lập trình · sức khoẻ · pháp lý), cộng một ca nửa-trong-nửa-ngoài | ✅ Có, và đúng nghĩa *"gọn trong một câu"*: hai câu bổ sung dài đúng 1 câu. ⚠️ `90-records/README.md` còn khai **2/4** (C1); dòng mở đầu chính file transcript vẫn nói "không lưu transcript" trong khi phần dưới có (G4) | ✅ **đạt** *(vòng 1 và 2 đều ❌)* |
| **AC6** VN-Index nói thẳng kho chưa có | Transcript `AC6b` + khai rõ lượt đầu model **không gọi function** | ✅ Tôi kiểm đường dữ liệu: `gia_theo_ngay("VNINDEX")` → `co_du_lieu:false, loai:"index", ly_do:"kho chưa có dữ liệu giá cho chỉ số"` — không bịa số, không thay bằng chỉ số khác | ✅ **đạt** |
| **AC7** 15/15 số · ≥ 14/15 hình dạng | Hai bảng chấm (12/15 và 13/15) + 15 transcript, giữ **cả hai** bảng | ✅ Bằng chứng đủ và trung thực; tôi đếm lại bảng v2 ⇒ 13 ĐẠT / 2 TRƯỢT, khớp công bố | ❌ **không đạt** (13 < 14) — **spec §7 nói rõ đây không phải cổng chặn merge**; báo nguyên trạng là đúng |
| **AC8** đo chi phí và độ trễ thật | Bảng §3: 47 request / 22 câu, token vào "lạnh" ≈ 36.750, ra p50 854, p50 6,9 s · p90 34,5 s · max 41,8 s, $0,016/câu | ✅ Đủ **mọi** chỉ số AC8 liệt kê, và còn khai một phát hiện **ngược** ghi chép cũ (cache không trúng giữa hai câu). ⚠️ Đo dưới `max_tokens` 4000/8000, cấu hình merge là 32000; sổ nay 53 dòng (G2) | ✅ **đạt** |
| **AC9** không còn `idle in transaction` của `agent_reader` | §7 dán `idle in transaction: 0 / tổng kết nối agent_reader: 0` | ✅ Thiết kế khớp: mỗi tool `with engine.connect()` trong `build_tools.chay`, không giữ kết nối bắc qua lời gọi model | ✅ **đạt** |
| **AC10** tài liệu §9 đã cập nhật, không còn chỗ đá nhau | §8 dán kết quả 4 phép `git grep` + giải thích hai hit còn lại là đúng | ❌ **Không còn đứng.** Tôi chạy lại 4 phép grep: hai hit cũ vẫn **đúng như giải thích** (`icb_level` ở chỗ nói nó không tồn tại; `roadmap.md:321` trong khối gạch ngang đã dùng xong). Nhưng **bốn chỗ mới** do chính bốn commit cuối tạo ra (C1), và §8 đang dán kết quả grep của một cây đã đổi | ❌ **không đạt** |

**Bảy AC đạt, một không đạt có tuyên bố trước là không chặn (AC7), một không đạt cần sửa trước merge (AC10).** AC5 là AC duy nhất **chuyển từ ❌ sang ✅** giữa vòng 2 và vòng 3 — và chuyển bằng cách **chạy lại thật rồi lưu transcript**, không phải bằng cách hạ ngưỡng.

---

## 6. Tài liệu §9 — bảy file, đọc code rồi mới đối chiếu

| File spec §9 yêu cầu | Yêu cầu gì | Trạng thái |
|---|---|---|
| `docs/20-design/chatbot-semantic-layer.md` | bỏ "chưa duyệt"; bỏ `icb_level`; 8→9 function; chép hợp đồng thật; đóng 3/4 "điều chưa biết" | ⚠️ **Sáu phần đúng, một phần sai.** Banner đã ✅; chín chữ ký §2 **chép đúng từng ký tự** khỏi `tools/__init__.py` (tôi so từng dòng); `icb_level` chỉ còn ở chỗ nói nó không tồn tại; **4/4** "điều chưa biết" đã đóng bằng số đo. ❌ §5.1 ghi `8000`, code `32000` (**C1**). Thêm: tài liệu **không mô tả bốn hình dạng §4.6** (G6) |
| `docs/20-design/market-data-store.md` §6.2–§6.3 | đồng bộ danh sách function; ghi rõ ví dụ §6.2 dùng tên bảng cũ | ✅ **Đúng, và làm đúng cách §1.7**: liệt 9 tên rồi **trỏ** sang `chatbot-semantic-layer.md §2` thay vì chép hợp đồng lần thứ hai (*"một sự thật một chủ"*). Cảnh báo `organization`/`organ_code` đã thêm |
| `docs/30-skills/maintenance.md` §6 | ghi chú bộ vòng 6 mất; "FCFF 260" không đối chiếu được; trỏ sang vòng 7 | ✅ **Đúng, và đúng tinh thần §1.2**: *"Giữ nguyên con số 260, không sửa thành 270 — sửa số mà không đo là nói dối"*. Có trỏ sang `regression-round7.md` |
| `docs/00-overview/roadmap.md` | đóng lát 10; ghi lát 11 gộp; gỡ dòng embedding; viết "Điểm vào cho lát 12" | ⚠️ Bốn việc **đều làm**: lát 10 ✅ XONG · lát 11 ⛔ GỘP với lý do · `"DỜI sang lát 10"` không còn hit sống · §"Điểm vào cho lát 12" có, kèm ba việc để lại xếp theo giá trị. ❌ Số test `976` ở hai chỗ (**C1**) |
| `database/README.md` | thêm user login `agent_reader IN ROLE dlck_api` | ✅ Đủ, và ghi cả **kết quả kiểm thật** dưới credential production, không chỉ mô tả |
| `docs/90-records/README.md` | thêm hồ sơ plan mới vào index | ❌ **Lệch cây ba chỗ** — 11/13 file, AC5 2/4, 976 test, và câu *"tất cả đã sửa"* (**C1**). §1.6: *"Index lệch cây là nói dối"* |
| `.env` | thêm `AGENT_DATABASE_URL` | ✅ Biến tồn tại và dùng được (tôi kết nối qua nó); `.env` bị `.gitignore` che, không giá trị nào lọt vào repo hay vào báo cáo này |

Hai file **ngoài** danh sách §9 cũng đã sửa và đều đúng: `architecture.md` §3.3 (5→9 function) và `20-design/README.md` (🟡 chưa duyệt → ✅ đã dựng). Cả hai do chính phép kiểm AC10 bắt được — ledger ghi lại chuyện đó, đúng lý do §1.7 tồn tại.

---

## 7. Ghi nhận — lệch có lý do đứng vững, hoặc chưa đủ nặng để chặn

| # | Nội dung | Đánh giá |
|---|---|---|
| **G1** | `compare_peers` nhận mã BCTC (`isa3`, `bsa53`) vì bảng nhãn dùng chung, rồi trả `chi_tieu: {}` **không kèm lý do**: `so_sanh_cung_nganh(["HPG","HSG"], ["isa3","isa20","bsa53"])` → `{"so_dong":2,"du_lieu":[{"ma":"HPG","chi_tieu":{}}, …]}` | **Lệch thật, chưa ai nêu, nhưng có sẵn từ trước đợt sửa 2.** Đúng họ *"0 bản ghi ≠ không có loại dữ liệu này"* mà §4.6 dựng ra để chặn, chỉ ở mức **từng chỉ tiêu**. Mô tả function không nói mã nào dùng được cho screener, nên model rất dễ rơi vào. Đề xuất: tách bảng nhãn screener khỏi bảng nhãn BCTC, hoặc trả `{"loi":true,…}` khi mọi mã xin đều ngoài tập screener |
| **G2** | Bảng AC8 đo **47 request** dưới `max_tokens` 4000/8000; sổ nay **53 dòng**, cấu hình merge là 32000. Ledger khai *"Ngân sách … **không đổi** vì nó tính theo token thực dùng"* | **Lý do đứng vững cho số đã đo, không tự động đúng về sau** — nới trần *có thể* làm câu trả lời dài ra, và chính ledger ghi nhận đúng hiện tượng đó ở mục 🟡. Số hiện có (đỉnh 3.589 < đỉnh 5.989 thời `8000`) nói là chưa xảy ra. Không cần đo lại trước merge; nên **ghi một dòng** rằng AC8 đo dưới cấu hình khác |
| **G3** | `max_iterations = 8` vẫn *"số chọn, chưa đo"* (spec §4.2 và §8) | Ledger `ef00826` nhắc một câu định giá cần *"8 lượt gọi công cụ"* nhưng chỉ sinh **4 dòng sổ** ⇒ nhiều `tool_use` trong một lượt, trần vòng lặp **chưa bị chạm**. Nợ vẫn mở, không nặng thêm |
| **G4** | `acceptance-transcript-2026-09-07.md:5` vẫn viết *"Hai câu ngoài phạm vi còn lại … **không lưu transcript**"*, trong khi §"Bổ sung" cùng file có đủ hai transcript đó | Tự đá nhau trong **một file**, nhưng phần bổ sung nói rõ *"Lượt nghiệm thu đầu … chỉ lưu hai transcript"* nên câu mở đầu đọc được thành mô tả lượt đầu. Một dòng ghi *"(đã đóng ở mục Bổ sung dưới)"* là xong |
| **G5** | `get_corporate_events` trả `ly_do` bằng thuật ngữ lược đồ: *"mã này không có **`issuer_id`** trong kho — sự kiện doanh nghiệp gắn theo issuer"* | §4.4 chỉ cấm **khoá** là mã chỉ tiêu thô, không cấm giá trị; nhưng đây là chuỗi model đọc rồi nhắc lại cho người dùng. Viết lại thành *"mã này không gắn với một tổ chức phát hành nào trong kho"* là đủ |
| **G6** | Bốn hình dạng §4.6 **không có nhà ở tài liệu sống** — chỉ nằm ở `90-records/spec.md` (bản ghi tại-thời-điểm, không sửa được) và docstring `_shared.py` | **Đây là gốc của N1/N2/N6.** Phép thử §1.1: xoá `90-records/` thì mất **tri thức vận hành**, không chỉ mất lịch sử. Đề xuất: chép bảng bốn hình dạng (kèm hai hình dạng mới `{"loi":…}` và `{"kieu":"danh_muc",…}`) vào `chatbot-semantic-layer.md` — đó cũng là chỗ đúng để ghi quyết định 32k của C1 |
| **G7** | `trang_thai: "delisted"` chỉ xuất hiện ở `get_price_series`; `get_corporate_events` trả 5 sự kiện của `FUCTVGF4` (delisted) mà không cờ | §4.6 nói `trang_thai` là *"cờ **kèm thêm** trên bất kỳ hình dạng nào"* — không bắt buộc ở đâu. Trên kho hiện tại không mã `delisted` nào có BCTC (tôi đếm: 0), nên rủi ro hiểu nhầm hẹp. Ghi lại để lát API không bỏ sót |
| **G8** | Rubric lớp 2 có 6 mục, `spec.md` §5.3 chốt 5 | Vòng 2 đã xét (G5) và kết luận minh bạch: ghi chú in nghiêng có ngày + trích nguyên văn quyết định chủ dự án, **giữ cả bảng chấm lượt đầu**. Không mở lại |

---

## 8. Ngoài phạm vi (spec §1) — vẫn sạch, kiểm lại lần cuối

```
grep -rn "fastapi|APIRouter|uvicorn|embedding" backend/agent backend/tests/agent   ⇒ 0 hit
backend/api/  không đổi · backend/etl/  không đổi · scripts/ deploy/  không đổi
migration head vẫn 0020 (spec §4.7: "Lát 10 không thêm migration nào")
không task Scheduler nào được đăng ký hay bật
```

Bốn commit sửa của đợt 2 **không thêm một dòng nào ngoài phạm vi**. `git diff --stat main...HEAD` chạm đúng `backend/agent/`, `backend/tests/agent/`, và bảy file tài liệu §9 (+ hai file AC10 bắt được). **Không có scope creep, kể cả trong các bản sửa** — ba vòng review liên tiếp cùng kết luận này.

---

## 9. Phán quyết

**Nhánh này đã làm đúng cam kết ở phần khó nhất, và ba vòng review đã đưa nó tới chỗ tôi tự kiểm được từng dòng thay vì phải tin lời khai: cả 9 function chạy thật trên 52 ca biên đều trả đúng dữ liệu — không còn ca nào trả dữ liệu sai một cách tự tin như vòng 2, ETF lấy lại được 114 sự kiện mà bản sửa vòng 1 đã chôn, `get_price_series` hết cắt câm, AC5 chuyển từ ❌ sang ✅ bằng cách chạy lại thật chứ không bằng cách hạ ngưỡng, và AC4 đứng vững trở lại. 986 test xanh, không skip mới, không một dòng ngoài phạm vi.**

**Nhưng chưa merge được, vì đúng một lý do và nó không nằm trong code: AC10 — tiêu chí mà nhánh tự khai là ✅ — hiện sai ở bốn chỗ do chính bốn commit cuối tạo ra, nặng nhất là tài liệu thiết kế sống `chatbot-semantic-layer.md` nói cấu hình xuất xưởng là `max_tokens=8000` trong khi code merge `32000`. Đó là một tài liệu sống nói sai về hệ thống của chính mình — cùng họ với "sửa số mà không đo", chỉ ngược chiều. Cùng cụm: hai chỗ ghi 976 test (thật là 986), và index `90-records` liệt 11/13 file, khai AC5 2/4 (thật là 4/4) và khai "tất cả đã sửa" trong khi bốn mục NÊN SỬA của vòng 2 vẫn mở. Cả cụm là năm dòng sửa, không đụng một dòng code, rồi chạy lại phép kiểm §1.7 và dán output mới.**

**Sáu mục NÊN SỬA còn lại chia làm hai nhóm, và nhóm thứ hai mới là điều tôi muốn nói với người sau. Nhóm một là lệch mới do bản sửa vòng 2 đẻ ra: `compare_peers` bịt được chỗ nguy hiểm nhưng dựng hình dạng "không tìm thấy" bằng tay và đánh rơi đúng hai trường §4.6 gọi tên — nó **đã tính ra** gợi ý "ý bạn là HPG?" rồi vứt đi. Nhóm hai là bốn mục vòng 2 đã nêu mà đợt sửa bỏ qua và cũng không ghi thành nợ: docstring sổ `llm_log` khẳng định phủ `max_iterations` và exception (lần thứ ba bị nêu), tên test không tồn tại nằm trong chính câu đính chính viết ra để chữa loại lỗi ấy, danh mục vĩ mô thiếu khoảng ngày, và `get_industry_tree` bảo `VNINDEX` là "quỹ/ETF". Hai đợt trước hỏng vì **sửa rộng quá** phạm vi bug; đợt này hỏng vì **sửa hẹp bằng đúng danh sách reviewer đọc tên** — `khoang_co_du_lieu` vá đúng hai hàm được điểm danh, còn `get_macro_series` và `get_news` cùng bệnh thì để nguyên. Cả ba lần đều là "sai phạm vi", và cả ba lần test viết cùng lượt sửa đều không bắt được vì nó chỉ phủ đúng ca đã nghĩ tới.**

**Gốc chung của ba mục N1/N2/N6 đáng sửa trước khi mở lát API: bốn hình dạng trạng thái dữ liệu chỉ sống ở `90-records/spec.md` — bản ghi tại-thời-điểm không được sửa — và trong một docstring. Không có tài liệu sống nào mô tả chúng, nên khi kho mọc thêm hình dạng thứ năm và thứ sáu (`{"loi":…}` ở 6/9 function, `{"kieu":"danh_muc",…}` ở một function) thì không có chỗ nào để ghi, và không có thước nào để đo lệch. Chép bảng bốn hình dạng vào `chatbot-semantic-layer.md` — cùng lượt với việc sửa dòng `8000` — vừa đóng C1 vừa cho N1/N2/N6 một cái thước.**

**Đóng cụm C1 (năm dòng tài liệu + chạy lại `git grep` và dán kết quả), rồi merge. Sáu mục NÊN SỬA đều nhỏ và không mục nào tạo dữ liệu sai — nhưng lần này phải **hoặc sửa hoặc ghi thành nợ có tên trong ledger**, đừng để chúng biến mất giữa vòng review thứ ba và lần merge. Bốn trong sáu mục đã sống sót qua đúng ba vòng bằng cách không ai viết chúng vào chỗ nào cả.**
