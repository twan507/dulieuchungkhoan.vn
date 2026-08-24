# Việc còn treo sau đợt khảo sát nguồn — chốt 2026-08-15

Danh sách này để **không rơi mất** khi sang giai đoạn viết tài liệu và dựng ETL.

## 1. 🔴 Realtime phái sinh — CHƯA TEST ĐƯỢC, phải đo trong phiên

**Vì sao chưa test được:** đo ngày thứ Bảy 2026-08-15, thị trường đóng (`tradingSessionID: "CLOSED"`). Và `11-bvsc-realtime.md §1.4` đã ghi: **ack `statusCode: 200` không chứng minh topic hợp lệ** — server nhận mọi chuỗi topic rồi im lặng. Nên đăng ký ngoài giờ **không chứng minh được gì**.

**Đã biết chắc (rút từ mã nguồn `priceboard/static/js/12.3241ea7a.js`):**

| Mục | Giá trị |
|---|---|
| Máy chủ socket | `https://wss.bvsc.com.vn` (`API_MARKET_URL`) |
| Đường dẫn | `/market/socket.io` · thư viện **sails.io** · `transports: ["websocket"]` |
| Bảng hằng số topic *(dùng chung toàn bảng giá)* | `i` · `i_ol` · `o10` · `o_ol10` · `o` · `o_ol` · `t` · `t_ol` · `tm` · `e` · `e_ol` · `im` · `e_im` · `om` · `idx` · `pth` · `ptm` · `p` · `u` · `d` |
| Bảng phái sinh | `BoardTypes.PHAI_SINH` render từ `psStocks`, **ăn cùng module socket** với bảng cổ phiếu → hạ tầng realtime dùng chung, không phải kênh riêng |

**Chưa biết:** topic nào mang tick phái sinh; định dạng frame; tần suất; có `openInterest` realtime không.

**Cách đo khi tới phiên** *(sớm nhất thứ Hai 17/08, khung **08:45–15:00** — nhớ phái sinh mở sớm hơn cổ phiếu 15 phút)*:
1. Nối `wss.bvsc.com.vn/market/socket.io`.
2. Đăng ký **toàn bộ 20 topic** với 2–3 mã phái sinh thanh khoản (`41I1G8000` là mã duy nhất có thanh khoản thật).
3. Ghi frame trong ~5 phút, xem **topic nào thật sự đẩy dữ liệu** — đây là phép kiểm duy nhất có giá trị.
4. Đối chiếu giá trong frame với `/datafeed/instruments` cùng lúc.

## 2. UDF phái sinh — đã đo, có giới hạn phải ghi vào tài liệu

| Endpoint | Kết quả 2026-08-15 |
|---|---|
| `/config` | ✅ nhưng khai `supports_search: true` |
| `/search` | 🔴 **404** — mâu thuẫn với `/config` |
| `/symbols` | ✅ `session: "0845-1500"` · `has_intraday: true` · `pricescale: 10` · `timezone: Asia/Bangkok` |
| `/history` `resolution=1` · `D` | ✅ chạy |
| `/history` `5` · `15` · `60` · `W` | 🔴 **HTTP 200, body rỗng 0 byte** |

➜ Chỉ **2 khung thời gian**. Muốn 5/15/30/60 phút phải **tự gộp từ nến 1 phút**. Parser **bắt buộc kiểm độ dài body trước khi parse JSON**.

## 3. Quyết định chủ dự án: dầu lưu **cả hai** loại giá

| Loại | Nguồn | Bản chất | Độ tươi |
|---|---|---|---|
| **Giao ngay** | FRED `DCOILWTICO` (= EIA Cushing `RWTC`) | giao ngay thật | trễ 4 ngày |
| **Tương lai** | WiChart `dau_wti` *(hoặc Yahoo `CL=F`)* | hợp đồng tháng gần | T−1 |

Chênh lệch cơ sở đo được: **~+2,0% ổn định** (giao ngay cao hơn tương lai, thị trường backwardation).

**Lưu cả hai, không chọn một.** Lược đồ phải có cột phân biệt loại giá — nếu trộn chung một cột "giá dầu" thì lịch sử sẽ có bậc nhảy 2% tại điểm đổi nguồn.

**Tuỳ chọn nâng cao (chưa chốt):** dựng thêm cột giao ngay ước lượng bằng cách ghép mức FRED + suất sinh lời `CL=F` → sai số **0,18–0,42%**, tươi T−1. Nếu làm thì bắt buộc cờ `is_estimated` và **ghi đè bằng số FRED chính thức** khi EIA công bố.

## 4. Việc cần chủ dự án làm (không phải việc của agent)

- **Đăng ký khoá EIA miễn phí** — lấy `RWTC` thẳng từ nguồn gốc thay vì qua FRED, bớt một mắt xích. *(EIA API trả `403 API_KEY_MISSING` khi không có khoá.)*
- **`.gitignore` chưa bao giờ được commit** — đang che `.env` ở máy này nhưng bảo vệ đó không đi theo repo.

## 5. Câu hỏi đo được nhưng chưa đo

- **Backwardation:** giả thuyết giải thích chênh 2% giao ngay/tương lai **chưa xác nhận trực tiếp**. Cách kiểm rẻ: so hai kỳ hạn liền nhau của `CL=F` để đo cấu trúc kỳ hạn.
- **Đồng, thép, than:** chưa tìm được nguồn ngày miễn phí có mốc chuẩn để đối chiếu.
- **Bạc `XAGUSDT`, đồng `COPPERUSDT`** vs WiChart — chưa đối chiếu.
- **Nguồn gốc thật của WiChart `vang_the_gioi`** — mới suy luận từ việc trùng khít 10/10 ngày với Investing XAU/USD.
- **Rà lại các cờ `lệch x%` khác trong `wichart.md`** bằng phương pháp so chuỗi *(nhớ parse `Asia/Ho_Chi_Minh`)*.
- **TPCP phái sinh:** kết luận "chưa từng giao dịch" mới dựa trên 1 phiên.

## 6. 🔴 Hai bài học kỷ luật — áp cho mọi việc sau

1. **Mọi chuỗi WiChart phải parse bằng `Asia/Ho_Chi_Minh`, không bao giờ UTC.** Epoch là nửa đêm giờ VN (`1786726800000` = 14/08 17:00 UTC = 15/08 00:00 VN). Parse UTC làm lệch cả chuỗi một ngày — đã gây ra một kết luận sai hoàn toàn trong đợt này.
2. **Không viết "đã thử X" nếu chưa chạy X.** Đợt này có một câu như vậy trong báo cáo, và chính nó chặn đúng phép kiểm sẽ tìm ra lỗi múi giờ.
3. **Tiêu chí kiểm chứng phải nâng:** không chỉ "gọi thật" mà là **gọi thật + đối chiếu độ tươi với lịch công bố**. akshare chứng minh: gọi thành công, nhận đủ 294 dòng, dữ liệu chết 1 năm, không lỗi nào.
