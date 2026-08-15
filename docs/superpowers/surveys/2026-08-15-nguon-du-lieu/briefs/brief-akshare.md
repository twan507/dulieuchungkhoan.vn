# Brief — Khảo sát akshare làm nguồn VĨ MÔ QUỐC TẾ cho Finext

## Bối cảnh (đọc trước khi làm)

Repo: `D:\twan-projects\finext-v2` — nền tảng dữ liệu & phân tích chứng khoán Việt Nam.
Tầng dữ liệu hiện có, ĐỌC ĐỂ BIẾT CHỖ TRỐNG:

- `docs/10-sources/README.md` — bản đồ nguồn + mục "Ngoài phạm vi"
- `docs/10-sources/macro/wichart.md` — nguồn vĩ mô **trong nước** đã có (87 endpoint: 18 chỉ tiêu vĩ mô, 8 tiền tệ/lãi suất, 61 hàng hoá)
- `.claude/skills/vn-stock-advisor/` — phương pháp phân tích top-down của sản phẩm; nó cần những chỉ báo quốc tế nào (Fed, DXY, lợi suất TPCP Mỹ, CPI Mỹ, Trung Quốc, chỉ số toàn cầu…)

**Chỗ trống cần lấp:** dữ liệu **vĩ mô quốc tế**. `10-sources/README.md` đang liệt "Cổ phiếu và chỉ số quốc tế" trong mục *Ngoài phạm vi* — đây chính là khối đang mở rộng.

**Đây là khảo sát bước đầu.** Mục tiêu: biết akshare cho được GÌ, chất lượng ra sao, có dùng được từ Việt Nam không. KHÔNG phải xây pipeline.

## Nhiệm vụ

### Bước 1 — Nghiên cứu akshare
Dùng WebSearch/WebFetch: akshare là thư viện Python nguồn mở (Trung Quốc) gom dữ liệu tài chính. Tìm hiểu:
- Cài đặt, phiên bản hiện tại, tần suất cập nhật, mức độ bảo trì (commit gần nhất)
- Kiến trúc: nó **scrape trang web** (eastmoney, sina, stats.gov.cn…) hay gọi API chính thức? Đây là câu hỏi RỦI RO quan trọng nhất — scraping thì gãy bất cứ lúc nào.
- Có cần API key không, có giới hạn không, giấy phép (license) là gì

### Bước 2 — Lập danh sách interface liên quan
akshare có HÀNG NGHÌN hàm. Chỉ quan tâm nhóm phục vụ phân tích vĩ mô quốc tế cho TTCK Việt Nam:
- Vĩ mô Mỹ (lãi suất Fed, CPI, việc làm, GDP, lợi suất trái phiếu)
- Vĩ mô Trung Quốc (PMI, CPI, PPI, tín dụng, tỷ giá) — TQ là đối tác thương mại lớn của VN
- Chỉ số chứng khoán toàn cầu, DXY, tỷ giá
- Hàng hoá quốc tế (dầu, thép, vàng…) — đối chiếu xem có TRÙNG với 61 mặt hàng WiChart đã có không
- Bất kỳ dữ liệu Việt Nam nào akshare có (nếu có — đối chiếu chất lượng với nguồn đã có)

Lập bảng: tên hàm · nội dung · tần suất · nguồn gốc dữ liệu thật đằng sau.

### Bước 3 — GỌI THẬT, đo thật
**Trần cứng: 40 lời gọi mạng cho toàn bộ phiên.** Tuần tự, nghỉ ≥1 giây giữa các lời gọi. Không dò ngưỡng chặn.

Chọn ~10–15 hàm đại diện nhất, gọi thật và ghi:
- Thành công / thất bại (akshare hay gãy — ghi đúng tỉ lệ gãy thật, đây là phát hiện có giá trị)
- Độ trễ, kích thước dữ liệu, khoảng thời gian dữ liệu phủ (từ năm nào tới ngày nào), độ trễ cập nhật so với thực tế
- Lược đồ trả về: tên cột (thường là **tiếng Trung**), kiểu, đơn vị — ghi rõ vì đây là bẫy tích hợp lớn
- Có gọi được từ Việt Nam không (một số nguồn TQ chặn IP ngoài)

Môi trường: Python 3.12, Windows. Dùng `pip install akshare`. **Bắt buộc đặt `PYTHONIOENCODING=utf-8`** khi chạy python — nếu không sẽ crash cp1252 khi in tiếng Việt/tiếng Trung.

### Bước 4 — Kết luận có căn cứ
- akshare có xứng làm nguồn sản xuất không? Nếu KHÔNG, nói thẳng và nêu lý do đo được.
- Chỗ nào trùng nguồn đã có, chỗ nào bổ sung thật
- Rủi ro: scraping gãy · cột tiếng Trung · giấy phép · phụ thuộc hạ tầng TQ

## Luật viết (quan trọng — repo này rất nghiêm)

- **Chỉ ghi cái ĐO ĐƯỢC.** Cái chưa gọi thật phải đánh dấu rõ "chưa kiểm". Suy đoán phải gắn nhãn suy đoán. Không tô hồng, không làm tròn cho đẹp.
- Nếu phát hiện mâu thuẫn với tài liệu hiện có, ghi rõ mâu thuẫn.
- Ghi ngày đo (hôm nay 2026-08-15) bên cạnh mọi con số.
- Tiếng Việt.

## Đầu ra — CHỈ GHI ĐÚNG 2 CHỖ, KHÔNG ĐỘNG VÀO GIT

1. **Báo cáo chính:** `C:\Users\tuanb\AppData\Local\Temp\claude\D--twan-projects-finext-v2\8bdadd16-750b-49f9-979c-7dea29fe37ac\scratchpad\report-akshare.md`
2. **Log thô:** thư mục `...\scratchpad\akshare-raw\`

**CẤM TUYỆT ĐỐI:** `git add` / `git commit` / `git checkout` / tạo nhánh / sửa bất kỳ file nào trong `D:\twan-projects\finext-v2`. Repo đang có việc khác chạy song song; controller sẽ tự đưa kết quả vào repo. Bạn chỉ đọc repo, ghi ra scratchpad.

**KHÔNG dispatch subagent.** Tự làm.

Trả về ngắn gọn: trạng thái, số lời gọi đã dùng, 5 phát hiện quan trọng nhất, khuyến nghị dùng/không dùng. Chi tiết để trong file báo cáo.
