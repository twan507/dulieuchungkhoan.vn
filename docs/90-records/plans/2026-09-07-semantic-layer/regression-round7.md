# Bộ hồi quy vòng 7 — 15 câu có đáp án xác định

**Ngày dựng:** 2026-09-07 · **Thay cho:** bộ vòng 6 (10 câu) đã **mất khỏi repo** — chỉ còn mô tả phương pháp ở [`maintenance.md §6`](../../../30-skills/maintenance.md), không còn câu hỏi, số liệu hay transcript. Không giả vờ đây là bộ cũ.

**Dùng khi:** sửa nội dung `valuation.md` · nối function calling vào skill · thêm skill mới vào hệ · trước khi merge một lát chạm tầng ngữ nghĩa.

**Cách chạy:** hỏi từng câu qua `python -m agent`, **tiền cảnh, chia khối** (job gọi model chạy nền bị đóng băng — nguyên nhân chưa xác định). Lưu transcript đầy đủ. Chấm bằng subagent **Sonnet** độc lập, nhận câu hỏi + đáp án + rubric, không biết câu trả lời đến từ đâu.

---

## Nhóm A — 6 câu tính toán (ép chạm tri thức L2)

Số liệu tự đặt, **khác** ví dụ trong `valuation.md` để không đo trí nhớ chép lại. Đáp án tính tay hai lượt độc lập.

### A1 — FCFF

> Một doanh nghiệp sản xuất có EBIT 800 tỷ, thuế suất 20%, khấu hao trong kỳ 200 tỷ, đầu tư vốn gộp 250 tỷ, đầu tư vốn lưu động mới 90 tỷ. Tính FCFF.

**Đáp án: 500 tỷ.** `800 × 0,8 + 200 − 250 − 90 = 640 + 200 − 250 − 90`

### A2 — FCFE (câu bẫy)

> Cùng doanh nghiệp đó: lợi nhuận sau thuế 520 tỷ, khấu hao 200 tỷ, đầu tư vốn 250 tỷ, đầu tư vốn lưu động mới 90 tỷ, **nợ dài hạn mới 80 tỷ**. Tính FCFE.

**Đáp án: 460 tỷ.** `520 + 200 − 250 − 90 + 80`

*Bẫy:* dùng công thức FCFF ra **500**; trừ thay vì cộng nợ dài hạn mới ra **300**. Đây là câu giữ vai trò mà câu FCFF của vòng 6 từng giữ.

### A3 — WACC

> Lãi suất phi rủi ro 5%, beta 1,1, phần bù thị trường 8%. Lãi vay trước thuế 9%, thuế suất 20%. Vốn hoá thị trường 3.000 tỷ, nợ vay 2.000 tỷ. Tính WACC.

**Đáp án: 11,16%.** `rE = 5 + 1,1×8 = 13,8%` · `rD sau thuế = 9 × 0,8 = 7,2%` · `wE = 0,6; wD = 0,4` · `0,6×13,8 + 0,4×7,2 = 8,28 + 2,88`

### A4 — Gordon trên FCFE

> Lấy FCFE 460 tỷ ở câu trên, tăng trưởng dài hạn 5%, chi phí vốn chủ 13,8%, doanh nghiệp có 200 triệu cổ phần. Tính giá trị vốn chủ sở hữu và giá mỗi cổ phần.

**Đáp án: 5.488,6 tỷ → 27.443 đ/cp.** `460 × 1,05 / (0,138 − 0,05) = 483 / 0,088 = 5.488,64 tỷ` · `5.488,64 tỷ / 200 triệu = 27.443 đ`

*Sai số cho phép ±0,5%* — câu duy nhất trong bộ có số vô hạn tuần hoàn.

### A5 — Dupont ba thành phần

> Lợi nhuận sau thuế 300 tỷ, doanh thu 2.500 tỷ, tổng tài sản 4.000 tỷ, vốn chủ sở hữu 1.500 tỷ. Tính ROE theo Dupont và **tách rõ ba thành phần**.

**Đáp án — cả bốn số:** biên lợi nhuận ròng **12,0%** · vòng quay tài sản **0,625** · đòn bẩy tài chính **2,667** · ROE **20,0%**. *(Kiểm chéo: 300/1.500 = 20%.)*

### A6 — EPS pha loãng và P/E

> Lợi nhuận sau thuế 480 tỷ, 240 triệu cổ phần lưu hành, giá thị trường 30.000 đ. Tính EPS và P/E. Sau đó doanh nghiệp phát hành thêm 60 triệu cổ phần để tăng vốn, lợi nhuận không đổi — EPS và P/E mới là bao nhiêu (giá giữ nguyên)?

**Đáp án — cả bốn số:** EPS **2.000 đ**, P/E **15,0**; sau phát hành EPS **1.600 đ**, P/E **18,75**.

---

## Nhóm B — 9 câu ép gọi function

Đáp án lấy từ kho bằng SQL chạy ngày **2026-09-07**. Ba câu B4, B5, B9 dùng **khoảng thời gian đóng trong quá khứ** để đáp án không hết hạn (kho tin vẫn nhận bài mới).

### B1 — `get_price_series`

> Giá đóng cửa của HPG phiên 2026-09-03 là bao nhiêu?

**Đáp án: 21.600 đ.** *(`close_raw` = `close_adj` = 21600; SQL: `price_daily ⋈ security WHERE ticker='HPG' AND trading_date='2026-09-03'`)*

### B2 — `get_industry_tree`

> VCB thuộc ngành nào trong bộ ngành của dự án?

**Đáp án: Ngân hàng và Tín dụng (`NGANHANG`), thuộc nhóm Dịch vụ Tài chính (`TAICHINH`); nguồn gán `icb`.** Trả lời bằng tên ngành ICB là **sai**.

### B3 — `get_financials`

> Doanh thu thuần và lợi nhuận sau thuế của FPT năm 2024 là bao nhiêu?

**Đáp án: doanh thu thuần 62.848,8 tỷ VND; LNST của cổ đông công ty mẹ 7.856,8 tỷ VND.**
*Chấp nhận **9.427,4 tỷ** nếu câu trả lời ghi rõ đó là LNST **toàn bộ, gồm cổ đông thiểu số** — trong nguồn, `isa20` và `isa22` mang **cùng một tên** "LỢI NHUẬN THUẦN" nhưng khác giá trị; chênh lệch đúng bằng `isa21` (lợi ích cổ đông thiểu số, 1.570,7 tỷ).*

### B4 — `get_macro_series` (nhánh macro)

> CPI Việt Nam tháng 8/2026 là bao nhiêu?

**Đáp án: 4,45%.** *(`macro.observation` ⋈ `indicator` `vn.cpi`, `obs_date='2026-08-01'`; đơn vị `%` — **không nhân 100**.)*

### B5 — `get_corporate_events`

> FPT có mấy đợt trả cổ tức tiền mặt công bố trong năm 2025, ngày giao dịch không hưởng quyền là ngày nào?

**Đáp án: 2 đợt**, ngày giao dịch không hưởng quyền **2025-06-12** và **2025-12-01**. *(Kho không lưu tỷ lệ chi trả cho hai đợt này — câu trả lời tốt nên nói rõ chỗ thiếu thay vì bịa số.)*

### B6 — `get_macro_series` (nhánh asset)

> Giá dầu WTI ngày 2026-09-05 là bao nhiêu?

**Đáp án: 91,22 USD/thùng.** *(`asset.price_daily` ⋈ `asset` `code='wti'`.)*

### B7 — `screen_stocks`

> Ba mã thuộc ngành Ngân hàng và Tín dụng có ROE (TTM) cao nhất theo dữ liệu screener phiên 2026-09-04 là những mã nào?

**Đáp án: TIN 73,48% · HDB 24,84% · LPB 24,66%.** *(TIN là số bất thường so với phần còn lại của ngành — câu trả lời tốt nên nêu nghi vấn, nhưng lớp chấm số vẫn theo đúng thứ tự này.)*

### B8 — `compare_peers`

> So sánh P/E (TTM) của HPG và VCB theo dữ liệu screener phiên 2026-09-04.

**Đáp án: HPG 7,89 lần · VCB 11,82 lần.**

### B9 — `get_news`

> Có bao nhiêu bài đăng trong tháng 8/2026 nhắc đúng cụm "lãi suất điều hành"?

**Đáp án: 23 bài.** *(`phraseto_tsquery('simple', news.immutable_unaccent('lãi suất điều hành'))` trên `article_revision.tsv`, `published_at` trong tháng 8/2026. Dùng `plainto_tsquery` sẽ ra **1.050 bài trên toàn kho** vì nó AND từng âm tiết — đó là câu trả lời sai.)*

---

## Chấm

### Lớp 1 — số

Một câu đạt khi **mọi** con số trong đáp án đúng. Sai số cho phép **±0,5% chỉ ở A4**. **15/15 mới đạt.**

### Lớp 2 — hình dạng L1

*(Rubric sửa 2026-09-07 sau lượt chấm đầu — chủ dự án chốt: **"phép tính phải ghi số chứ không ghi văn xuôi"**. Bản đầu chấm mục 1 là "mạch lập luận, không phải tờ công thức" và vì thế **phạt nhầm** hai câu tính toán trình bày đúng cách — bài tính thì hiện phép tính bằng số mới là thứ kiểm chứng được. Mục 1 nay chia theo loại câu, và thêm một cổng loại trực tiếp cho số dẫn xuất.)*

Mỗi câu chấm 5 mục; đạt khi **≥ 4/5** và **không vi phạm mục 5 hay mục 6** (hai mục này là cổng loại trực tiếp, không tính điểm).

| # | Mục | Đạt khi |
|---|---|---|
| 1 | Trình bày đúng loại câu | **Câu tính toán (nhóm A):** hiện **phép tính bằng số** — thay số vào công thức, ra kết quả từng bước. Chỉ nêu kết quả, hoặc diễn giải bằng lời mà không hiện số, là **không đạt**. Trình bày bằng công thức toán hay bảng bước tính **là đúng**, không bị trừ. · **Câu tra cứu (nhóm B):** có diễn giải dẫn tới kết luận, không phải bảng số trần |
| 2 | Kết luận có điều kiện | nêu điều kiện làm kết luận đổi, không phán chắc nịch |
| 3 | Phân biệt nguồn số | nói rõ số nào tra được từ dữ liệu, số nào là giả định của đề |
| 4 | Không khuyến nghị | không đưa lệnh mua/bán cụ thể |
| 5 | 🔴 Không lộ mã thô *(cổng)* | không xuất hiện `rtq12`, `isa3`, `bsa53`, `rtd21`… trong câu trả lời |
| 6 | 🔴 Số dẫn xuất phải kèm phép tính *(cổng)* | mọi con số **không có trong đề và không tra được từ công cụ** phải hiện cách tính. Một con số dẫn xuất nêu trần, không phép tính, là **bịa** — vi phạm mục này |

### Ghi kết quả

Lưu vào `round7-results-YYYY-MM-DD.md` cùng thư mục: 15 transcript đầy đủ, bảng chấm hai lớp, số lần model gọi mỗi function, và số đo chi phí lấy từ `ops.llm_call` (token vào/ra, độ trễ, số request mỗi câu).
