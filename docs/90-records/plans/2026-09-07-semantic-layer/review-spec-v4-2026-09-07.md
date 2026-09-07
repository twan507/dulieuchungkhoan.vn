# Review trục SPEC — vòng 4, cửa cuối trước merge

**Nhánh:** `feat/semantic-layer` · **HEAD lúc rà:** `b576643` *(docs: give the result-shape contract a home in the living design doc, 09:16)* · cây làm việc **sạch**
**Ngày:** 2026-09-07 · **Trục:** SPEC (thiếu / sai / dư so với cam kết). Không chấm chất lượng code.

⚠️ **Nhánh di chuyển trong lúc rà.** Bắt đầu ở `5e69011`, kết thúc ở `b576643` — hai commit `81dd1f8` và `b576643` rơi vào giữa. Mọi kết luận dưới đây đo trên `b576643`; nếu có commit mới sau đó thì phải đo lại phần tài liệu (§4).

**Cách lấy bằng chứng:** chạy trọn bộ test; gọi **thẳng 9 hàm tool** trên kho dev qua `AGENT_DATABASE_URL` (37 lời gọi, chỉ đọc); đọc `input_schema` thật của 9 tool; đọc mã SDK `anthropic/lib/tools/_beta_runner.py`. **Không gọi model.**

---

## 1. Bảng AC1–AC10

| AC | Nội dung | Phán quyết | Bằng chứng đã tự kiểm |
|---|---|---|---|
| **AC1** | `tool_runner` chạy với MiniMax | ✅ **đạt** | Ledger Task 0 dán output nguyên văn (`SO LAN TOOL CHAY THAT: 1`, không lỗi header) + transcript AC1/AC6b có `function gọi:`. Tôi kiểm phần kiểm được mà không gọi model: `build_tools()` trả **đúng 9** `BetaFunctionTool`, `required` chỉ chứa tham số thật sự bắt buộc (`ticker`×3, `topic`, còn lại `[]`) ⇒ bẫy G8 đã đóng |
| **AC2** | Không test xanh thành đỏ | ✅ **đạt** *(số trong tài liệu sai — xem P3)* | Chạy thật trên nhánh: **`997 passed, 2 skipped in 99.19s`**. `main` = 877 + 2 skipped (kiểm chéo bằng đếm `def test_`: main 859 → HEAD 979, **+120**, khớp 997−877). **2 skipped ở cả hai ⇒ không skip/xfail mới.** Test mới +120 ≫ 7 seam §6 |
| **AC3** | Đọc dưới `dlck_api`, role không ghi được, `assert_read_only` chặn cấu hình sai | ✅ **đạt** | Tự chạy `agent.db.read_engine()` dưới đúng credential production: `current_user: agent_reader` · `thuộc dlck_api: True` · `có INSERT market.security: False` · đọc `market.security` = 2017 dòng · `ops.llm_call` bị chặn `ProgrammingError` |
| **AC4** | Cả 9 function trả đúng dữ liệu thật | ✅ **đạt** | Gọi thật 9/9 (bảng §3). Đối chiếu **8/8 đáp án nhóm B** của bộ hồi quy — khớp tuyệt đối: B1 21.600 đ · B2 `NGANHANG`/`TAICHINH`/`icb` · B3 62.848,8 tỷ & 7.856,8 tỷ · B4 4,45% · B5 2 đợt, exright 12/06 và 01/12/2025 · B6 91,22 USD/thùng · B7 TIN 73,48 · HDB 24,84 · LPB 24,66 · B8 7,89 vs 11,82 lần · B9 `tong_khop=23`. Function thứ 9 trả đúng tiêu đề `valuation.md` |
| **AC5** | 4 câu ngoài lĩnh vực bị từ chối gọn | ✅ **đạt** | `acceptance-transcript` có **4/4** (ẩm thực · lập trình · sức khoẻ · pháp lý), mỗi câu 1–2 câu trả lời, không lái ngược; **thêm** một ca nửa-trong-nửa-ngoài tách đúng hai vế. Việc hạ 4/4→2/4 rồi chạy lại lấy transcript thật (`f651aa4`) là cách đóng đúng |
| **AC6** | VN-Index ⇒ nói thẳng kho chưa có | ✅ **đạt** *(sau sửa mô tả function)* | AC6b: model gọi `get_price_series`, nhận và nói lại đúng "kho chưa có dữ liệu giá cho chỉ số". Tôi kiểm chính đường đó: `gia_theo_ngay("VNINDEX")` → `{"tim_thay":true,"co_du_lieu":false,"loai":"index","ly_do":"kho chưa có dữ liệu giá cho chỉ số","ma":"VNINDEX"}` — hình dạng #2, không nhầm với #3 |
| **AC7** | 15/15 số · ≥ 14/15 hình dạng | ❌ **không đạt, báo nguyên trạng** | Số 15/15; hình dạng **13/15** sau khi sửa rubric. Spec ghi rõ **AC7 không phải cổng chặn merge**. Không đo lại được (cấm gọi model) — chấp nhận hồ sơ. Hai câu trượt được ghi rõ nguyên nhân, không tô hồng |
| **AC8** | Đo chi phí và độ trễ thật | ✅ **đạt** *(số đã lỗi thời một phần — G2)* | `round7-results §3`: 47 request / 22 câu, $0,3555 ⇒ ≈ $0,016/câu, p50 6,9 s · p90 34,5 s. Đo trên cấu hình **cũ** (`max_tokens=4000`, timeout 120 s). Sau khi nới, ledger có 4 dòng đo mới cho một câu 8 lượt công cụ ≈ **101k token vào / 54 s** — cao hơn hẳn "2,1 request/câu". Không phải lỗi, nhưng con số $0,016 không còn đại diện |
| **AC9** | Không còn `idle in transaction` của `agent_reader` | ✅ **đạt theo hồ sơ**, tôi kiểm được phần cấu trúc | Hồ sơ §7 dán `idle in transaction: 0 · tổng kết nối: 0`. Tôi **không tái kiểm được bằng số** vì quan sát `pg_stat_activity` bằng `etl_worker` (không superuser) bị che cột `state`. Kiểm được phần bất biến: mọi tool đóng gói `with engine.connect()`, không giữ kết nối bắc qua lời gọi model — đúng ràng buộc §4.1 |
| **AC10** | Tài liệu §9 đã cập nhật, không còn chỗ đá nhau | 🔴 **KHÔNG CÒN ĐẠT** | Đạt tại thời điểm đo (`8601759`), rồi **4 commit sau đó làm lệch lại**: 3 chỗ trong tài liệu sống nói sai số test và sai số file. Chi tiết P3 |

**Tổng:** 8/10 đạt · AC7 không đạt nhưng spec miễn trừ cổng merge · **AC10 hỏng lại**.

---

## 2. Bảng 9 function × 4 ca (gọi thật, `b576643`, kho dev 2026-09-07)

Hình dạng ghi theo bảng §2b của `chatbot-semantic-layer.md`: **#1** không có mã · **#1b** danh sách mã · **#2** sai loại/kho không giữ · **#3** khoảng rỗng · **#4** có dữ liệu · **#5** đầu vào sai · **#6** danh mục.

| # | Function | Ca có dữ liệu | Mã không tồn tại | Sai loại chứng khoán | Khoảng rỗng |
|---|---|---|---|---|---|
| 1 | `get_price_series` | ✅ **#4** — HPG 03/09 `21.600 đ`, `tong_khop`, `da_cat`, `ghi_chu` không có khối lượng | ✅ **#1** — `HPGG` → `goi_y:["HPG"]` | ✅ **#2** — `VNINDEX` *"kho chưa có dữ liệu giá cho chỉ số"*; `E1SSHN30` (etf) và `DAN` (delisted, kèm `trang_thai`) cũng #2 | ✅ **#3** — HPG 1999 → `khoang_co_du_lieu 2026-06-09..2026-09-03` |
| 2 | `get_financials` | ✅ **#4** — FPT 2024, 7 chỉ tiêu, nhãn tiếng Việt, `isa20`/`isa22` tách tên đúng | ✅ **#1** — `ZZZZ`, `goi_y:[]` | ✅ **#2** — `VNINDEX` và `E1SSHN30` *"kho không có báo cáo tài chính cho…"* | ⚠️ **#3 một nửa** — FPT 1990–91 có `khoang_co_du_lieu {2002..2025}` ✅; nhưng `DAN` (delisted, **không có BCTC nào**) → `so_dong:0` **không khoảng, không `trang_thai`** ⇒ P8/P9 |
| 3 | `get_corporate_events` | ✅ **#4** — FPT 2025 CashDividend 2 đợt; **FUCVREIT (etf) 14 sự kiện** — hồi quy vòng 2 đã đóng thật | ✅ **#1** — `ZZZZ` | ✅ **#2** — `VNINDEX` *"không có issuer_id…"* (lý do **cấu trúc**, đúng §3.6) | ✅ **#3** — FPT 1995 → `khoang 2007-02-27..2026-08-22` |
| 4 | `compare_peers` | ✅ **#4** — HPG 7,89 · VCB 11,82 lần; ngành `NGANHANG` cắt đúng 25 mã kèm `da_cat:true` | ✅ **#1b** — `["ABCDE"]` → `khong_tim_thay`, `goi_y` **dict**, `ly_do`. Ca lai `["HPG","ABCDE"]` trả cả `du_lieu` lẫn `khong_tim_thay` ✅ (hồi quy vòng 2 đã đóng) | ⚠️ **hình dạng thứ 7** — `["VNINDEX"]` → `so_dong:0` + khoá **`khong_co_du_lieu_phien`** *chưa có tên trong §2b* ⇒ P7 | ⚠️ **#3 thiếu khoảng** — ngành lạ → `so_dong:0`, chỉ có `ngay_du_lieu` ⇒ P8 |
| 5 | `screen_stocks` | ✅ **#4** — `NGANHANG` sort `rtq12` ra TIN/HDB/LPB đúng; `limit=9999` → cắt đúng 200 + `da_cat` | ✅ **#5** — mã chỉ tiêu lạ / toán tử lạ trả `loi:true` + danh sách hợp lệ | 🔴 **KHÔNG có** — `exchange` lạ và `industry_code` lạ đều trả **#3 câm** `so_dong:0` (trong khi `get_industry_tree` **có** kiểm `industry_code`) ⇒ P5 | ⚠️ **#3 thiếu khoảng** — chỉ có `ngay_du_lieu` ⇒ P8 |
| 6 | `get_industry_tree` | ✅ — VCB → `NGANHANG`/`TAICHINH`/`nguon_gan:"icb"`; cây đủ **6 nhóm × 24 ngành**, **không có `icb_level`** | ✅ **#1** — `ZZZZ`; ngành lạ cũng **#1** (`ma_da_tra`) | ✅ **#2** — `VNINDEX` *"(loại index) chưa được gán ngành"* | — (không có trục thời gian) |
| 7 | `get_macro_series` | ✅ **#4** — `vn.cpi` 4,45% (**không nhân 100** ✔), `wti` 91,22 USD/thùng kèm `loai_gia:"futures"` (ADR §2.3 ✔), `vn.gdp.real` có `gia_tri_cong_bo` + `ghi_chu` chuỗi đã nối (F11 ✔) | ✅ **#1** — code lạ | ✅ **#6** — `keyword` → `kieu:"danh_muc"`; **không keyword → 192/192, `da_cat:false`** (trần 250 đủ) | ✅ **#3** — `vn.cpi` 1900 → `khoang 2003-01-01..2026-08-01` |
| 8 | `get_news` | ✅ **#4** — cụm "lãi suất điều hành" 8/2026 `tong_khop=23`, `kieu_tim:"cum"`, `da_phan_loai` từng bài | ✅ **#1** — `ticker="ZZZZ"` (vòng 1 đã sửa) | ⚠️ **một nửa** — `sub` lạ → **#5** ✅; **`group_no=99` và `industry_code` lạ → #3 câm**, còn kèm `ghi_chu` đổ lỗi *"còn 7990 bài chưa phân loại"* ⇒ **đúng lỗi vòng 1 đã sửa cho `ticker`, còn nguyên ở 2 đường lọc khác** ⇒ P5 | ✅ **#3** — 1/2020 → `so_dong:0` + `khoang_co_du_lieu` |
| 9 | `load_knowledge_reference` | ✅ — `valuation` trả đúng tiêu đề `# Định giá cổ phiếu` | ✅ **#5** — `"../../../etc/passwd"` và `""` đều `loi:true` + 9 chủ đề hợp lệ; **`enum` 9 khoá có thật trong `input_schema`** | — | — |

**Ngoài bảng — ca ngày sai định dạng:** `gia_theo_ngay("HPG","khong-phai-ngay")` và `chuoi_vi_mo("vn.cpi",None,"abc")` **ném `DataError` của psycopg**, không trả hình dạng #5 ⇒ P6.

---

## 3. Hình dạng ngoài bốn cái spec liệt — đã có nhà chưa?

Câu hỏi này **đã được đóng ngay trước lúc rà** bởi `b576643`: `docs/20-design/chatbot-semantic-layer.md` §2b (dòng 57–77) đặt tên đủ **sáu** hình dạng, gồm cả `{loi:true,…}` (#5), `{kieu:"danh_muc",…}` (#6) và biến thể danh sách của `compare_peers` (#1b), kèm ba luật đi kèm và câu tuyên bố rõ *"đây là **nhà** của hợp đồng này"*. Đúng chỗ: `90-records/` không sửa được nên tầng sống phải sở hữu.

**Ba chỗ §2b nói chưa khớp thực đo:**

| §2b nói | Thật là |
|---|---|
| dòng 71 — #5 *"trả lỗi **có cấu trúc**, không ném exception"* | ngày sai định dạng **ném exception** (P6) |
| dòng 77 — *"🔴 Hình dạng #3 **phải** kèm khoảng kho thật có"* | 3 hàm không kèm: `screen_stocks`, `compare_peers`, và `get_financials` khi mã hoàn toàn không có BCTC (P8) |
| bảng 6 hàng | thiếu hàng cho `khong_co_du_lieu_phien` của `compare_peers`, và không nhắc `kieu_tim` / `trang_thai` (P7) |

---

## 4. Danh sách lệch tài liệu (file:dòng · nói gì · thật là gì)

| # | File:dòng | Tài liệu nói | Thật là |
|---|---|---|---|
| D1 | `docs/00-overview/roadmap.md:29` | **986 test** | **997 passed, 2 skipped** (chạy 2026-09-07 trên `b576643`) |
| D2 | `docs/00-overview/roadmap.md:152` | `986 test (877 → +109)` | `997 test (877 → +120)` |
| D3 | `docs/00-overview/roadmap.md:436` (Điểm vào lát 12 — **khối sống**, không gạch) | `986 test xanh, 2 skipped` | `997 test xanh, 2 skipped` |
| D4 | `docs/90-records/README.md:44` | **13 file** trong hồ sơ, liệt tên 13 file | **15 file** — thiếu `review-chuan-v3-2026-09-07.md` và `review-spec-v3-2026-09-07.md` (thêm ở `81dd1f8`) |
| D5 | `docs/90-records/README.md:44` | `nhánh 986 passed (+109, 0 skip mới)` | `997 passed (+120, 0 skip mới)` |
| D6 | `docs/20-design/market-data-store.md:626` | *"Hợp đồng đầy đủ — chữ ký, tham số, **trần**, **nguồn dữ liệu** — nằm ở `chatbot-semantic-layer.md §2`"* | `§2` chỉ có **chữ ký**. Không có một con trần nào, không có nguồn dữ liệu. Con trỏ trỏ vào chỗ trống |
| D7 | `backend/agent/tools/__init__.py:57` (mô tả **model đọc**) | `get_financials`: *"Tối đa **8 kỳ** mỗi lần gọi"* | `TRAN_KY = 20` |
| D8 | `backend/agent/tools/__init__.py:76` (mô tả **model đọc**) | `compare_peers`: *"Tối đa **10 mã**"* | `TRAN_MA = 25` |
| D9 | `docs/90-records/.../round7-results-2026-09-07.md:85` | `max_tokens` … *"nâng lên **8.000**"* | `chat.MAX_TOKENS = 32000` |
| D10 | `.../round7-results-2026-09-07.md:69, :130` | `986 passed` | `997 passed` |

**`ledger.md` — kiểm riêng theo yêu cầu: ĐẦY ĐỦ, không lệch câm.** Commit `81dd1f8` (09:14) đóng đúng khoảng trống này. Bảng *"Nới giới hạn (chủ dự án chốt 2026-09-07)"* liệt **đủ 9 dòng** kèm lý do và kèm câu trích quyết định của chủ dự án:

| Mục yêu cầu kiểm | Ledger ghi | Khớp code |
|---|---|---|
| trần token 4.000 → 32.000 | ✅ có, kèm số đo đỉnh 3.589 | ✅ `chat.py:MAX_TOKENS=32000` |
| thời gian chờ 120 → 600 s | ✅ có, kèm lý do SDK `expected_time` chỉ raise khi dùng timeout mặc định | ✅ `__main__.py:CHAT_TIMEOUT_S=600.0` |
| trần vòng lặp 8 → 16 | ✅ có, kèm ca thật 8 lượt công cụ | ✅ `chat.py:MAX_ITERATIONS=16` |
| `TRAN_PHIEN` 400 → 2000 | ✅ có, kèm `BT6` 5.764 phiên | ✅ (đo lại: `so_dong=2000, tong_khop=5764, da_cat=true`) |
| `TRAN_KY` 8 → 20 | ✅ có | ✅ |
| `TRAN_MA` 10 → 25 · `TRAN_CHI_TIEU` 8 → 15 | ✅ có | ✅ (đo lại: ngành `NGANHANG` trả 25, `da_cat=true`) |
| danh mục vĩ mô 40 → 250 | ✅ có, kèm số đo `tong_khop=192, da_cat=False` | ✅ (đo lại: 192/192, `da_cat=false`) |
| `limit` mặc định/trần 4 hàm | ✅ có | ✅ `screen 30/200` · `events 30/200` · `news 15/100` · `macro 120/2000` |

Ledger cũng ghi đủ hồi quy vòng 2, mẫu hỏng vòng 1 vs vòng 2, và một 🟡 để ngỏ *"nới trần làm câu trả lời trôi sát ranh giới khuyến nghị — chờ chủ dự án quyết"*. Đây là chỗ hồ sơ **mạnh nhất** của cả lát: nó ghi cả cái chưa xử lý.

---

## 5. Phát hiện, phân loại

### 🔴 CHẶN

**P3 — AC10 đã hỏng lại: bốn commit cuối làm tài liệu sống nói sai số** · Loại **SAI** · Mức **CHẶN**

`D1`–`D5`. Bốn chỗ trong hai tài liệu sống (`roadmap.md` ×3, `90-records/README.md` ×2 con số) khai **986 test** và **13 file**; thật là **997 test** và **15 file**. AC10 là tiêu chí nghiệm thu của chính spec, và spec **chỉ miễn trừ cổng merge cho AC7**, không miễn trừ AC10.

Đáng nói hơn con số: đây **đúng cái mẫu hỏng mà ledger vòng 3 vừa tự đặt tên** — *"Mục CHẶN duy nhất nằm ở TÀI LIỆU, do chính bốn commit trước đó tạo ra… Đúng lỗi §1.7 mà tôi tự dặn: sửa xong lại đổi code mà không quét lại."* Lần này lặp lại y hệt: `81dd1f8` thêm 2 file vào hồ sơ nhưng không sửa index đếm file (§1.6 bắt sửa **trong cùng lượt**), và `6b99fb9`+`5e69011` thêm 11 test nhưng không sửa số test.

Cách đóng rẻ: sửa 5 chỗ trên, rồi chạy lại đúng phép kiểm §1.7 (`git grep` "986", "13 file") trước khi tuyên bố đồng bộ. **Đừng dán số vào tài liệu mà không chạy `pytest` ngay lượt đó** — cả ba lần sai đều là con số chép lại từ lượt đo trước.

### 🟠 NÊN SỬA

**P1 — Mô tả gửi cho model vẫn nói trần cũ; quyết định "nới trần" mới thực hiện được một nửa** · Loại **SAI** · Mức **NÊN SỬA (nặng nhất trong nhóm)**

`D7`, `D8`. `backend/agent/tools/__init__.py:57` nói *"Tối đa 8 kỳ mỗi lần gọi"* (thật 20) và `:76` nói *"Tối đa 10 mã"* (thật 25). Hai câu này là **văn bản duy nhất model đọc được về trần** — nó không đọc `TRAN_KY`. Commit `5e69011` mang tên *"open up the result limits — the model was starving on caps"* nhưng để nguyên hai câu nói với model rằng trần vẫn là 8 và 10; model sẽ tiếp tục tự bó đúng ở mức cũ. Tức mục đích của commit bị chính commit đó bỏ lỡ ở nửa quan trọng hơn: nới trần trong code mà không nói với người dùng trần thì trần vẫn cũ.

Ba mô tả khác (`get_price_series`, `screen_stocks`, `get_news`, `get_macro_series`) **không nêu trần** — chấp nhận được vì kết quả có `da_cat`/`tong_khop` để model tự biết đã bị cắt; chỉ hai câu **nói sai** mới là vấn đề.

**P2 — Bảng trần mới không có chủ ở tầng tài liệu sống** · Loại **THIẾU** · Mức **NÊN SỬA**

`D6`. `market-data-store.md:626` hứa hợp đồng đầy đủ *"chữ ký, tham số, **trần**, nguồn dữ liệu"* nằm ở `chatbot-semantic-layer.md §2`; §2 chỉ có chữ ký. Số trần thật chỉ tồn tại ở hai chỗ: `ledger.md` (thuộc `90-records/` — bản-ghi-tại-thời-điểm, theo §1.7 **không phải** tài liệu sống) và chú thích trong code. Vi phạm §1.1 (*tài liệu sống phải tường minh, không trỏ về hồ sơ*) và §1.6 (*một sự thật một chủ*). Ba tháng nữa ai muốn biết `compare_peers` chịu được bao nhiêu mã sẽ phải đọc code hoặc đào ledger — đúng thứ §1.1 sinh ra để chặn.

Đề xuất rẻ nhất: thêm một cột **Trần** vào khối chữ ký §2 (hoặc một bảng nhỏ ngay dưới), rồi P1 và P2 đóng cùng một lượt vì cùng một bảng số.

**P5 — Hình dạng #5 chỉ phủ 6/11 tham số nhận giá trị từ vựng đóng** · Loại **THIẾU** · Mức **NÊN SỬA**

Đo thật từng tham số:

| Có kiểm (trả `loi:true` + danh sách hợp lệ) | **Không kiểm** (trả `so_dong:0` như thể dữ liệu rỗng) |
|---|---|
| `metric_codes` / `sort_by` (3 hàm) · `operator` · `event_type` · `sub` · `topic` · `industry_code` **của `get_industry_tree`** | `statement_type` (`"XX"` → `so_dong:0`) · `period` (`"thang"` **âm thầm rơi về quý**, trả 4 quý 2024) · `exchange` và `industry_code` **của `screen_stocks`** · `group_no` và `industry_code` **của `get_news`** |

Hai điểm làm nó nặng hơn một chuyện nhất quán:

1. **Cùng một tham số `industry_code`, hai hàm xử lý ngược nhau** — `get_industry_tree` trả `tim_thay:false` + gợi ý; `screen_stocks` và `get_news` trả "0 dòng". Model gõ sai mã ngành ở hàm này thì được sửa, ở hàm kia thì nhận một kết luận sai.
2. **`get_news` với `group_no=99` hoặc `industry_code` lạ vẫn trả** `ghi_chu: "không có bài nào khớp nhãn; trong khoảng này còn 7990 bài chưa phân loại nên chưa thể lọc theo nhãn"` — **chính xác lỗi đổ-lỗi-sai mà vòng 1 đã sửa** cho `ticker` không tồn tại. Bản sửa vòng 1 chỉ vá đúng đường `ticker` được điểm danh; hai đường lọc còn lại giữ nguyên bệnh. Đây lại là mẫu *"sửa hẹp đúng bằng danh sách reviewer đọc tên"* mà ledger vòng 3 tự nêu và tuyên đã đổi luật giao việc để chặn — luật mới đã bắt được `get_news` ở mục `khoang_co_du_lieu`, nhưng chưa quét mục `ghi_chu`.

**P6 — Ngày sai định dạng ném exception thay vì hình dạng #5** · Loại **SAI** · Mức **NÊN SỬA**

`gia_theo_ngay("HPG","khong-phai-ngay")` → `DataError: invalid input syntax for type date…` kèm **nguyên văn câu SQL và tên schema/bảng**. `chuoi_vi_mo("vn.cpi",None,"abc")` y hệt. Tài liệu sống §2b dòng 71 nói rõ #5 *"trả lỗi có cấu trúc, **không ném exception** — model tự sửa mà không phá vòng chat"*.

**Không phải CHẶN, vì đã kiểm mã SDK:** `_beta_runner.py:305` bắt mọi `Exception`, trả `tool_result` với `is_error: true`, nội dung `repr(exc)` (`_tool_dispatch.py:121`). Vòng chat **không** sập. Nhưng (a) tài liệu sống đang nói sai về hành vi thật, và (b) model nhận nguyên câu SQL — trái tinh thần `market-data-store §6.2` (không phơi tầng lưu trữ cho LLM). Ca này khả dĩ vì mô tả `get_macro_series`, `get_news`, `get_corporate_events` **không nói định dạng ngày** (chỉ `get_price_series` nói `'YYYY-MM-DD'`), mà model hay sinh `"2026-08"`.

Hai đường đóng, đều rẻ: parse ngày ở tầng Python và trả `{loi:true, ly_do, dinh_dang:"YYYY-MM-DD"}`; **hoặc** sửa §2b cho đúng sự thật và thêm định dạng ngày vào cả 4 mô tả.

**P8 — Luật "#3 phải kèm khoảng" sai ở 3 hàm; một ca để lại đúng sự nhập nhằng luật sinh ra để chặn** · Loại **SAI** · Mức **NÊN SỬA (ca `get_financials`) / GHI NHẬN (2 hàm screener)**

- `screen_stocks` và `compare_peers` trả `ngay_du_lieu` thay vì `khoang_co_du_lieu` — **hợp lý** (screener là ảnh chụp một phiên, không có khoảng), nhưng §2b dòng 77 viết luật ở dạng tuyệt đối 🔴 nên tài liệu đang nói sai. Sửa **tài liệu**, không sửa code.
- `get_financials("DAN")` (mã huỷ niêm yết, **không có một dòng BCTC nào**) → `{"tim_thay":true,"co_du_lieu":true,"so_dong":0,"ma":"DAN"}` — không khoảng, không lý do. Model không phân biệt được *"kho không giữ BCTC của mã này"* với *"khoảng năm bạn hỏi rỗng"* — **đúng cái nhập nhằng §2b viết luật để chặn**. Ca này nên ra hình dạng #2 (`co_du_lieu:false` + `ly_do`), không phải #3.

### ⚪ GHI NHẬN

**P4 — Hồ sơ `round7-results` còn hai con số chết** · Loại **SAI** · Mức **GHI NHẬN**
`D9` (*"nâng lên 8.000"*, thật 32.000) và `D10` (986, thật 997). Nếu coi `90-records/` là vùng lịch sử theo §1.7 thì để nguyên là **đúng**. Nhưng chính file này đã bị sửa nội dung một lần ở `8601759` ("close the drift"), nên lập luận "vùng lịch sử, không đụng" không còn sạch — hồ sơ đang ở trạng thái nửa-sống-nửa-chết. Cần một quyết định một lần: hoặc đóng băng hẳn, hoặc đồng bộ hẳn. Tài liệu **sống** (`chatbot-semantic-layer.md:120`) ghi đúng 32000, nên người đọc tầng sống không bị dẫn sai — vì thế chỉ GHI NHẬN.

**P7 — Hai khoá kết quả chưa có tên trong §2b** · Loại **THIẾU** · Mức **GHI NHẬN**
`compare_peers` trả `khong_co_du_lieu_phien: ["VNINDEX"]` khi mã có thật nhưng vắng mặt trong phiên screener — về thực chất là hình dạng thứ bảy, chưa có hàng trong bảng. `kieu_tim` (`get_news`) và `trang_thai` (`get_price_series`) cũng chưa được nhắc. Vừa mới lập §2b thì bổ sung rẻ.

**P9 — Cờ `trang_thai:"delisted"` chỉ có ở 1/3 hàm** · Loại **THIẾU** · Mức **GHI NHẬN**
Spec §4.6 chốt `trang_thai:"delisted"` là **cờ kèm trên bất kỳ hình dạng nào**. Thực đo: `get_price_series("DAN")` có ✅; `get_financials("DAN")` và `get_corporate_events("DAN")` **không có**. Cùng bệnh với P8, nên sửa cùng lượt.

**P10 — Số đo AC8 thuộc cấu hình trước khi nới** · Loại **GHI NHẬN**
$0,016/câu · p50 6,9 s đo với `max_tokens=4000`, timeout 120 s, trần kết quả cũ. Ledger có 4 dòng đo bổ sung cho một câu 8 lượt công cụ (≈ 101k token vào, 54 s) và lập luận *"ngân sách không đổi vì tính theo token thực dùng"* — lập luận đúng cho **giá mỗi token**, nhưng số **token mỗi câu** thì đã đổi: trần kết quả rộng gấp 2–5 lần nghĩa là `tool_result` dài hơn. Không phải lỗi, chỉ là con số AC8 không còn đại diện cho cấu hình sắp merge. Ngưỡng đảo ngược của spec ($0,15/câu) vẫn còn xa.

---

## 6. Scope creep — **KHÔNG CÓ**

Kiểm từng mục spec §1 liệt "ngoài phạm vi", trên `git diff main...HEAD`:

| Mục ngoài phạm vi | Kết quả kiểm |
|---|---|
| Endpoint HTTP / web chat | ✅ sạch — `grep fastapi\|uvicorn\|APIRouter\|@app\.` trong `backend/agent/` → 0 hit; `backend/api/` không đụng |
| Streaming | ✅ sạch — `grep stream` trong `backend/agent/` → 0 hit |
| Embedding / tìm kiếm khái niệm | ✅ sạch — 0 hit; roadmap đã gỡ dòng *"DỜI sang lát 10"* |
| Migration | ✅ sạch — `git diff --name-only main...HEAD` không chạm `database/migrations/`; head vẫn **`0020`** (`0020_news_title_trgm.py`). Chỉ `database/README.md` đổi, đúng cam kết §9 |
| Job tự động / task Scheduler | ✅ sạch — `scripts/` không đổi một dòng nào |
| Chạy lưới phân loại 7.900 bài | ✅ sạch — kho vẫn 7.990 bài chưa nhãn (đọc được từ `ghi_chu` của `get_news`) |
| Ba ô thiếu cây ngành / 83 chỉ tiêu screener | ✅ sạch — cây vẫn 6 nhóm × 24 ngành; bảng nhãn vẫn đóng ở **21 mã** |
| `.env` | ✅ đúng — thêm **đúng một** khoá `AGENT_DATABASE_URL` |

Ngược lại, có hai thứ **vượt spec theo hướng tốt và đã được ghi lý do**: block `system` thứ ba (`TOOL_RULES`, spec §4.3 chốt 2 block) — sinh từ lỗi đo được, ghi ở `chatbot-semantic-layer.md §5.2`; và `enum` 9 khoá thật trong `input_schema` (spec chốt `Literal`, bản đầu code khai `str`) — vòng 1 đã đóng.

---

## 7. Kết luận

**Chưa merge được: sửa xong P3 (bốn con số ở `roadmap.md:29,152,436` và `docs/90-records/README.md:44`) thì merge được — mọi phát hiện còn lại là NÊN SỬA hoặc GHI NHẬN, không cái nào chặn.**
