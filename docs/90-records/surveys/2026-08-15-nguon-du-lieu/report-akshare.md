# akshare làm nguồn vĩ mô quốc tế — khảo sát 2026-08-15

**37/40 lời gọi** (32 akshare + 4 WebFetch + 1 pip) · tuần tự, nghỉ 1,5 s · không dò ngưỡng chặn

*(Agent không ghi được `.md`; controller ghi lại. Raw: `scratchpad/akshare-raw/` — 29 file, 2.740 KiB CSV + 3 kịch bản chạy lại được.)*

## 0. Kết luận

**Dùng có chọn lọc, tier B — KHÔNG làm nguồn sản xuất cho vĩ mô Mỹ.**

## 1. 🔴 Phát hiện nặng nhất: hỏng IM LẶNG

**Toàn bộ vĩ mô Mỹ của akshare đã chết ~1 năm mà vẫn trả HTTP 200.** 8/8 chuỗi đi qua `jin10.com` dừng ở 2025-08 → 2025-10, chậm **289–349 ngày** so với ngày đo.

Lãi suất Fed lấy về mới nhất là **4,5% của 2025-07-31**.

DataFrame đủ **294 dòng**, **không exception**, **không cờ báo**. Đây là loại hỏng tệ nhất: mọi kiểm tra kỹ thuật đều xanh, chỉ có dữ liệu là sai.

| Hàm | Phủ đến | Trễ | Giá trị cuối |
|---|---|---:|---|
| `macro_bank_usa_interest_rate` | 2025-10-30 | **289d** | Fed 4,5% (2025-07-31) |
| `macro_usa_gdp_monthly` | 2025-09-25 | 324d | 3,3 |
| `macro_china_cpi_yearly` | 2025-09-10 | 339d | 0,0 |
| `macro_china_exports_yoy` | 2025-09-08 | 341d | 7,2 |
| `macro_usa_non_farm` | 2025-09-05 | 344d | 7,3 |
| `macro_usa_unemployment_rate` | 2025-09-05 | 344d | 4,2% |
| `macro_usa_ism_pmi` | 2025-09-02 | 347d | 48,7 |
| `macro_china_pmi_yearly` | 2025-08-31 | **349d** | 49,4 |

## 2. Chia cắt sạch theo host — quy tắc nhận biết

**jin10 = chết** (98/198 hàm ứng viên, gồm gần trọn `macro_usa_*`, `macro_euro_*`, `macro_bank_*`).
**eastmoney + sina = còn sống**, trễ 1–45 ngày (10/10 chuỗi).

**Quy tắc nghiệm đúng 8/8 lần:** hàm **không** có hậu tố `_yearly`/`_monthly` là hàm eastmoney và là hàm tươi.
Ví dụ: `macro_china_pmi` (7/2026 = 49,2) ✅ vs `macro_china_pmi_yearly` (chết ở 8/2025) ❌.

## 3. Kiến trúc — scrape API nội bộ, không phải API chính thức

| Host thượng nguồn | Số hàm |
|---|---:|
| `datacenter.jin10.com` + biến thể | **98** |
| `data.eastmoney.com` + biến thể | **61** |
| `finance.sina.com.cn` + biến thể | 19 |
| `api.currencyscoop.com` (cần key) | 5 |
| `push2.eastmoney.com` / `push2his.eastmoney.com` | 5 |
| `data.stats.gov.cn` (cổng chính thức TQ) | 3 |
| `s3.amazonaws.com/files.fred.stlouisfed.org` (**FRED chính chủ**) | 2 |
| `chinamoney` · `safe.gov.cn` · `mofcom` · `cn.investing.com` | 5 |

Chuỗi phụ thuộc thành **4 tầng**: nguồn gốc → jin10/eastmoney/sina → akshare → Finext. Dài hơn WiChart **một mắt xích**, và mắt xích thêm vào là dự án mã nguồn mở **không có nghĩa vụ với ai**.

**Bảo trì:** PyPI 1.18.91 · MIT · 22.034 sao · 0 issue mở · commit cuối 2026-08-13 · **11/19 commit gần nhất là `fix(...)` vá interface gãy** (~1 interface/2–3 ngày). Đây không phải lời khen mà là **số đo trực tiếp của rủi ro scraping**.

**Giấy phép:** mã nguồn MIT. Dữ liệu — tài liệu akshare ghi rõ *"chỉ dành cho mục đích nghiên cứu học thuật"*, và đó là tuyên bố của akshare về dữ liệu **akshare không sở hữu**. **Không có đối tác nào để đi mua giấy phép** như đã làm với WiFeed.

## 4. Tỉ lệ gãy và độ trễ

| Vòng | Lời gọi | OK | Rỗng | Gãy |
|---|---:|---:|---:|---:|
| 1 — 22 hàm đại diện | 21 | 14 | 1 | **6** |
| 2 — gọi lại 6 hàm hỏng | 6 | 3 | 0 | 2 |
| 3 — đường thay thế | 4 | 4 | 0 | 0 |
| 4 — sửa tham số | 1 | 1 | 0 | 0 |

**Gãy 33% ngay lần đầu.** Gọi lại thì 4 hàm hồi phục. **2 hàm gãy vĩnh viễn từ Việt Nam** — `index_global_hist_em` và `forex_hist_em`, cả hai trỏ `push2his.eastmoney.com`, gãy 2/2 lần bằng `RemoteDisconnected`. **Mất đường lịch sử DXY và lịch sử tỷ giá.** *(`push2.eastmoney.com` vẫn chạy tốt → chặn theo host, không phải chặn IP Việt Nam.)*

🔴 **Độ trễ không tương thích ETL đồng bộ.** Trung vị 22 lời gọi thành công **≈53 giây**. `macro_shipping_bdi` **754 s** · `macro_global_sox_index` **413 s** · `macro_usa_ism_pmi` **231 s**.

Nguyên nhân: akshare **phân trang ngầm** (SOX bung 33 request con ~43 s/trang) và hầu hết hàm **không có tham số cắt ngày** — luôn kéo toàn bộ lịch sử từ 1988/1994/1996 để lấy 1 dòng mới.
**Hệ quả phụ nghiêm trọng: trần lời gọi không kiểm soát được ở tầng gọi hàm** — số HTTP request thật vượt xa 37.

Theo host: sina trung vị **5,53 s** · eastmoney **44,16 s** · jin10 **~110 s**.

## 5. Tập con dùng được thật

| Hàm | Nguồn | Trễ | Ghi chú |
|---|---|---:|---|
| **`bond_zh_us_rate`** | eastmoney | 1d | Lợi suất TPCP Mỹ+TQ 2/5/10/30 + chênh 10y-2y · **1,07 s** · **có tham số cắt ngày** — tốt nhất cả khảo sát |
| `index_global_spot_em` | push2.em | <1d | **1 lời gọi = 56 chỉ số toàn cầu + DXY 99,64 + BDI + CRB + cả VNINDEX** — nhưng chỉ là **ảnh chụp**, không lịch sử |
| `index_us_stock_sina` | sina | 1d | S&P500 **5.693 phiên từ 2004** · 0,51 s |
| `macro_china_money_supply` · `_new_financial_credit` · `_pmi` · `macro_china_lpr` · `_reserve_requirement_ratio` | eastmoney | 26–45d | Vĩ mô Trung Quốc |
| `futures_foreign_hist('CL')` | sina | 1d | WTI **7.690 phiên từ 1996** |
| `macro_global_sox_index` · `macro_shipping_bdi` | eastmoney | 1d | SOX từ 1994 · BDI từ 1988 |

## 6. 🔵 Giá trị ít ai để ý — backfill lịch sử WiChart

WiChart cắt **cửa sổ trượt 2 năm** trên toàn bộ 61 mặt hàng và nhóm tỷ giá/lãi suất ngày (`WIN2Y`). **akshare không cắt.**

→ Dùng akshare **một lần** để backfill phần lịch sử WiChart **vĩnh viễn không trả**, rồi WiChart lo cập nhật hằng ngày.

Cách dùng này **né đúng ba điểm yếu nặng nhất** của akshare: chậm (backfill chạy một lần, có người ngồi xem), gãy vặt (gọi lại được), phải chạy hằng ngày (không cần).

⚠️ **Phải đối chiếu chồng lấn 2 năm trước khi ghép** — hai nguồn khác nhau (SunSirs vs sina/eastmoney) có thể không cùng benchmark. **Chưa kiểm.**

## 7. Bảy bẫy tích hợp

1. **Cột tiếng Trung, 5 quy ước cùng tồn tại:** jin10 `商品/日期/今值/预测值/前值` · eastmoney nước ngoài `时间/发布日期/现值/前值` · eastmoney TQ `月份/当月/当月-同比增长/累计` · LPR tên máy thô `TRADE_DATE/LPR1Y/RATE_1` · sina tiếng Anh. **Không có từ điển trường nào trong akshare.**
2. 🔴 **Thứ tự sắp xếp NGƯỢC NHAU giữa hai hàm cùng nguồn.** `macro_usa_cpi_yoy` tăng dần (dòng cuối = mới nhất); `macro_china_money_supply`/`_new_financial_credit`/`_pmi` giảm dần (dòng **đầu** = mới nhất). `df.iloc[-1]` đúng ở hàm này và **sai 18 năm** ở hàm kia.
3. 🔴 **Có dòng của kỳ CHƯA công bố.** `macro_usa_cpi_yoy` dòng cuối: `时间=2026-08-01`, `发布日期=2026-09-11`, `现值=null` — đó là **lịch công bố tương lai**, không phải dữ liệu.
4. **Đơn vị nhét trong tên cột, hoặc không có ở đâu cả.** `货币和准货币(M2)-数量(亿元)` có đơn vị; `macro_china_new_financial_credit` cột `当月` **không ghi đơn vị ở bất cứ đâu**. Không có trường `unit`, không metadata — **kém hơn cả WiChart**.
5. **Đơn vị chỉ tiêu không tự hiển nhiên.** `macro_usa_non_farm` giá trị `7,3` là **vạn người** (quy ước TQ), không phải nghìn người như quy ước Mỹ. **Đọc nhầm là sai 10 lần.**
6. **Cột rác.** `futures_foreign_hist('CL')` trả 9 cột nhưng `volume/position/s/settlement` = 0 ở cả dòng 1996 lẫn 2026 → **4/9 cột vô dụng**.
7. **Không có múi giờ.** `index_global_spot_em` trả `2026-08-15 04:58:53` cho DXY và `2026-08-14 15:59:59` cho VNINDEX — **hai múi giờ trong cùng một bảng**, không cột nào nói múi giờ nào (*suy đoán*: giờ Bắc Kinh). Không có epoch để parse, chỉ có chuỗi giờ địa phương không nhãn.

## 8. Đối chiếu nguồn đã có

**Trùng:** giá hàng hoá thế giới (WiChart đã có 61 mặt hàng) · VN-Index (akshare thua xa BVSC).
**akshare không đóng góp gì:** vĩ mô Việt Nam · tiền tệ/lãi suất VN.
**Bổ sung thật:** lợi suất TPCP Mỹ+TQ theo ngày · vĩ mô Trung Quốc (M2/tín dụng/LPR/RRR/PMI) · SOX từ 1994 · BDI/BCI/BPI từ 1988 · 56 chỉ số toàn cầu · lịch sử S&P500/Dow/Nasdaq từ 2004.

## 9. 🔴 Ba mâu thuẫn với tài liệu hiện có

1. **`10-sources/README.md` §2 "Ngoài phạm vi"** liệt "Cổ phiếu và chỉ số quốc tế". Nếu nhận chỉ số quốc tế thì dòng này phải **tách**: chỉ số quốc tế **vào** phạm vi, cổ phiếu quốc tế vẫn ở ngoài.
2. **§7** khẳng định *"Tình trạng pháp lý hai nguồn nay đều đã rõ"*. akshare là nguồn thứ ba **chưa rõ** — câu hiện tại **không được phép phủ sang nó**.
3. **§1** viết *"Mọi thông tin đều được kiểm chứng bằng lời gọi thật"*. akshare vừa chứng minh **gọi thật là chưa đủ**: gọi thành công, nhận 294 dòng, dữ liệu chết 1 năm.
   ➜ **Tiêu chí phải nâng thành: gọi thật + đối chiếu độ tươi với lịch công bố.** Đây là bài học phương pháp áp cho **toàn bộ** repo, không riêng akshare.

## 10. Khuyến nghị

**Dùng** 8 hàm eastmoney/sina đã đo tươi, kèm **ba điều kiện bắt buộc**:
- **(a) Cổng kiểm độ tươi trước khi ghi** — mỗi series khai ngưỡng trễ tối đa theo lịch công bố; vượt ngưỡng thì **từ chối ghi và báo động**. Đây là lá chắn duy nhất chống kiểu hỏng im lặng ở §1.
- **(b) Ghim `akshare==1.18.91`**, không bao giờ `pip install -U` tự động.
- **(c) Bọc timeout + retry backoff và kiểm `len(df)>0` riêng** — `macro_bank_usa_interest_rate` **nuốt lỗi rồi trả rỗng, không ném exception**.

**Không dùng:** toàn bộ nhóm jin10 · hai hàm `push2his` · mọi thứ liên quan Việt Nam.

**Ưu tiên hơn akshare cho vĩ mô Mỹ: FRED** — API có hợp đồng, miễn phí, khác hẳn về chất so với scrape jin10. *(Đã khảo sát — xem `report-fred.md`.)*
