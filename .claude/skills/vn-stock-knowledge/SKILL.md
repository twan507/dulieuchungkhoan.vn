---
name: vn-stock-knowledge
description: Tầng tra cứu kiến thức chứng khoán Việt Nam — công thức, định nghĩa, quy trình tính, ở mức tự thực hiện được. Đây là tầng dưới của `vn-stock-advisor`, chỉ tải khi câu trả lời cần một thứ chấm được đúng/sai mà tầng trên không có: một con số phải tính ra, một công thức hoặc định nghĩa chính xác, một quy trình phải làm đủ bước, hoặc người dùng muốn được dạy lại một phần kiến thức. KHÔNG dùng để nhận định thị trường hay tư vấn tỷ trọng — việc đó thuộc `vn-stock-advisor`. Các chủ đề có ở đây: định giá DCF, FCFF và FCFE, WACC, CAPM, định giá so sánh, đọc bảng cân đối kế toán hay báo cáo lưu chuyển tiền tệ, đọc báo cáo tài chính ngân hàng hoặc công ty chứng khoán hoặc bảo hiểm, bóc tách ROE, đòn bẩy, số nhân tiền, dự trữ bắt buộc, cung tiền M0–M3, cơ chế ngân hàng tạo tiền, nới lỏng định lượng, công cụ chính sách tiền tệ, thị trường liên ngân hàng, chỉ báo kỹ thuật, trung bình động, phân kỳ, mẫu hình giá, khoảng trống giá, lý thuyết Dow hay Wyckoff hay Elliott, đồ thị nến, quan hệ giá và khối lượng, lý thuyết danh mục, tỷ suất Sharpe, đa dạng hoá, rebalancing, luân chuyển ngành và dòng tiền, lý thuyết trò chơi, thông tin bất cân xứng, tài chính hành vi, thị trường hiệu quả, Fama-French, APT, hợp đồng tương lai, hedging, Open Interest. Dùng cả khi người dùng hỏi "tính thế nào", "công thức là gì", "lấy số ở đâu", "cái này nghĩa là gì", hoặc muốn được dạy lại một phần kiến thức.
---

# Kiến thức chứng khoán Việt Nam

Bộ kiến thức nền ở mức **tự làm được** — người đọc phải tự thực hiện được phép tính, không chỉ hiểu kết quả người khác đưa ra. Mỗi file có ít nhất một ví dụ chạy đủ đầu-cuối bằng số giả định.

## Quan hệ với skill tư duy

Skill này **không thay thế** `vn-stock-advisor`. Hai skill chia việc rõ ràng:

| | `vn-stock-advisor` | Skill này |
|---|---|---|
| Trả lời | *Nên nghĩ thế nào về tình huống này* | *Cái này tính ra sao, nghĩa là gì* |
| Dùng khi | Nhận định thị trường, phân tích một mã, quyết định tỷ trọng | Hỏi công thức, khái niệm, quy trình, cách đọc số |

Khi đang phân tích mà cần một phép tính cụ thể thì mở file tương ứng ở đây, xong quay lại mạch lập luận của skill kia. Đừng dùng skill này để đưa ra nhận định thị trường.

## Định tuyến

| Người dùng hỏi về | Mở file |
|---|---|
| Tiền được tạo ra thế nào, cung tiền, dự trữ bắt buộc, số nhân tiền, lãi suất điều hành, công cụ chính sách, nới lỏng định lượng, chính sách tài khoá, liên ngân hàng, chu kỳ kinh tế, phân nhóm ngành | `references/macro-money-creation.md` |
| Ba báo cáo tài chính, cách đọc từng dòng, dựng ngược báo cáo, bóc tách ROE, đòn bẩy, tăng vốn, thủ thuật kế toán, chỉ tiêu chất lượng, **báo cáo ngân hàng / chứng khoán / bảo hiểm** | `references/financial-statements.md` |
| Định giá bất kỳ dạng nào: chiết khấu dòng tiền, FCFF, FCFE, WACC, CAPM, PE, PB, mô hình cổ tức, thu nhập còn lại, định giá so sánh, quy trình bảy bước | `references/valuation.md` |
| Giá và khối lượng, cung cầu, hỗ trợ kháng cự, đường xu hướng, phá vỡ, đồ thị nến, ghép nến, điểm uốn | `references/technical-supply-demand.md` |
| Chỉ báo kỹ thuật, trung bình động, sức mạnh xu hướng, phân kỳ, mẫu hình giá, khoảng trống, Dow, Wyckoff, Elliott, quy trình sáu bước | `references/technical-indicators.md` |
| Xây danh mục, tỷ trọng, đa dạng hoá, rủi ro và lợi nhuận, Sharpe, phân bổ tài sản, hai đòn bẩy, luân chuyển ngành và dòng tiền, rebalancing | `references/portfolio-and-rotation.md` |
| Lý thuyết trò chơi, cân bằng Nash, thông tin bất cân xứng, event study, thị trường hiệu quả, tài chính hành vi, thiên lệch tâm lý | `references/psychology-information.md` |
| Fama-French, APT, hạn chế của CAPM, phân loại nhân tố giá, hợp đồng tương lai, hedging, Open Interest | `references/advanced.md` |

Câu hỏi lớn thường cần hai file. Ví dụ *"cổ phiếu này đắt hay rẻ"* cần `valuation` để tính và `financial-statements` để biết lấy số ở đâu.

## Từ vựng chung — hai trục luân chuyển

Dùng thống nhất trong mọi file. Tên tự mang thứ tự tiền chảy, không cần nhớ quy ước.

| Bậc | Trục ngành — theo độ nhạy chu kỳ | Trục dòng tiền — theo mức rủi ro trong ngành |
|---|---|---|
| 1 | **ngành dẫn dắt** — đòn bẩy tài chính cao, hoặc bán thứ chỉ được mua thêm khi tiền rẻ | **dòng tiền dẫn dắt** — vốn hoá lớn, đầu ngành, thanh khoản cao |
| 2 | **ngành lan toả** — doanh thu gắn sản lượng thực của nền kinh tế | **dòng tiền lan toả** — vốn hoá trung bình |
| 3 | **ngành phòng thủ** — nhu cầu tồn tại bất kể chu kỳ | **dòng tiền đầu cơ** — vốn hoá nhỏ, thị giá thấp |

Hai trục ghép lại thành **ma trận luân chuyển dòng tiền** — chín ô, mô tả đầy đủ ở `references/portfolio-and-rotation.md`.

**Skill này không chốt danh sách ngành nào thuộc bậc nào** — chỉ nêu tiêu chí phân bậc. Xếp một ngành cụ thể thì chấm theo bốn thành phần rủi ro ở `references/portfolio-and-rotation.md`, dùng khung phân ngành mà hệ thống dữ liệu đang áp dụng.

Trùng chữ ở bậc 1–2 là cố ý: cùng một cơ chế lan tiền ở hai cấp độ. Tách ở bậc 3 vì khác thật — ngành bậc ba là nơi tiền **trú lại** cuối chu kỳ, dòng tiền bậc ba là tiền **đuổi theo** sóng đã chạy.

**Hai chu kỳ lồng nhau, đừng lẫn:** luân chuyển ngành là chu kỳ lớn theo tháng, dựa trên kỳ vọng lợi nhuận, điều khiển bởi chính sách tiền tệ. Luân chuyển dòng tiền là chu kỳ nhỏ theo tuần, dựa trên khẩu vị rủi ro.

## Quy tắc đọc số liệu — bắt buộc

Nguồn của bộ kiến thức này là các buổi giảng **2022–2024**. Mọi con số quan sát trong đó đã chết.

- ✅ **Công thức và định nghĩa còn nguyên giá trị.** *Số nhân tiền = 1 / tỷ lệ dự trữ bắt buộc* đúng ở mọi thời điểm.
- ❌ **Không bao giờ trích số liệu như thể nó là hiện tại.** Các con số trong file chỉ là **tham số ví dụ** để minh hoạ phép tính.
- Khi cần số thật: có công cụ tra dữ liệu thì gọi và dùng số hiện hành, không có thì nói rõ là cần tra. Không suy số hiện tại từ ví dụ trong file.
- Mọi ví dụ dùng doanh nghiệp giả định. Không mã cổ phiếu thật nào trong bộ này là khuyến nghị.

## Giới hạn của bộ kiến thức

Nêu rõ khi gặp, đừng lấp bằng suy đoán:

- **Không có phần mềm hay chỉ báo độc quyền.** Nguồn có nhắc vài công cụ riêng nhưng không đưa công thức, nên không tái tạo được. Gặp câu hỏi về chúng thì nói thẳng là không có.
- **Không có nhận định thị trường theo thời điểm.** Phần đó đã bị loại có chủ đích.
- **Một số điểm nguồn tự mâu thuẫn giữa các thế hệ giáo trình.** Chỗ nào như vậy, file đã ghi cả hai phương án kèm điều kiện áp dụng — trình bày đủ cả hai, đừng chọn hộ.
- **Vài chỗ nguồn có lỗi đã được sửa** (rõ nhất là lỗi tính trùng khấu hao trong công thức FCFE). Bản trong file là bản đã sửa.

## Cách trả lời

- Hỏi công thức thì **đưa công thức trước**, giải thích sau. Nêu rõ từng biến lấy ở báo cáo nào, dòng nào.
- Quy trình nhiều bước thì **giữ nguyên số bước**, không gộp cho gọn.
- Có ví dụ chạy được trong file thì **dùng lại nó** thay vì bịa ví dụ mới — nó đã được kiểm tính toán.
- Không rào đón, không giảng đạo lý, không kết bằng câu hỏi ngược.
- Người dùng hỏi kiến thức thì trả lời kiến thức. Chỉ chuyển sang mạch nhận định khi họ hỏi nhận định — lúc đó dùng `vn-stock-advisor`.
- **Hỏi về cổ phiếu hay danh mục *của chính họ* thì kiến thức chỉ là phần lõi, không phải cả câu trả lời.** Lúc đó `vn-stock-advisor` quyết định hình dạng: ba nhịp, kết luận có điều kiện, một câu disclaimer. Đưa công thức xong mà không ra được hành động là trả lời hụt.
