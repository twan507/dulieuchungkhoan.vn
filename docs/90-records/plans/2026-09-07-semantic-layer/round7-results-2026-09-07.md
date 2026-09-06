# Kết quả bộ hồi quy vòng 7 — chạy thật 2026-09-07

Bộ câu: [`regression-round7.md`](regression-round7.md) · Transcript đầy đủ: [`round7-transcript-2026-09-07.md`](round7-transcript-2026-09-07.md) · Bảng chấm chi tiết: [`round7-grading-2026-09-07.md`](round7-grading-2026-09-07.md)

Chạy bằng `python -m agent` trên kho dev, **tiền cảnh, chia khối** 3–6 câu. Chấm bằng subagent Sonnet độc lập, không biết câu trả lời do đâu sinh ra.

---

## 1. Kết quả hai lớp

| | Kết quả | Ngưỡng AC7 | |
|---|---|---|---|
| **Lớp 1 — số** | **15/15 đúng** | 15/15 | ✅ đạt |
| **Lớp 2 — hình dạng L1** | **12/15 đạt** | ≥ 14/15 | ❌ **không đạt** |

**Ba câu trượt hình dạng, cùng hai kiểu hỏng:**

| Câu | Điểm | Trượt vì |
|---|---|---|
| A3 (WACC) | 3/5 | trình bày thuần công thức LaTeX + heading "Bước 1/2/3" như tờ công thức, mất mạch lập luận; không phân biệt nguồn số |
| A4b (Gordon) | 3/5 | cùng kiểu trình bày như A3; không phân biệt nguồn số |
| B5 (cổ tức FPT) | 3/5 | chỉ liệt kê hai sự kiện rồi dừng, không diễn giải, không nêu điều kiện đổi kết luận |

**Mẫu hỏng lặp lại nhất:** mục *"phân biệt số nào tra được, số nào là giả định của đề"* bị bỏ ở **5/15 câu** (A3, A4b, A5, B3, B4b) — mục dễ đạt nhất lại hay quên nhất. Hai câu tính nặng nhất (A3, A4b) rơi vào lối trình bày tài liệu tham khảo, trong khi bốn câu tính khác cùng dạng (A1, A2b, A5, A6) giữ đúng văn phong.

**Một lỗi bịa số:** A4b tự thêm dải nhạy "23.500–32.500 đồng" cho `Ke ± 1%`; tính đúng phải là **≈ 24.643–30.962 đồng**. Lệch 4–5% ở cả hai đầu, không phải làm tròn. Hai con số chính của câu vẫn đúng nên lớp 1 không ảnh hưởng, nhưng đây là **lỗi nặng nhất của cả lượt**: model bịa một con số *dẫn xuất* mà không ai kiểm.

## 2. Chín function đều được model gọi đúng chỗ

| Function | Câu ép | Model gọi? |
|---|---|---|
| `get_price_series` | B1, AC1, AC6b | ✅ |
| `get_industry_tree` | B2, B7 | ✅ |
| `get_financials` | B3 | ✅ |
| `get_macro_series` | B4b (macro), B6 (asset) | ✅ cả hai nhánh |
| `get_corporate_events` | B5 | ✅ |
| `screen_stocks` | B7 | ✅ |
| `compare_peers` | B8 | ✅ |
| `get_news` | B9b | ✅ |
| `load_knowledge_reference` | A1, A2b, A4b, A6 | ✅ 4/6 câu nhóm A (A3, A5 model tự tính không cần tra) |

## 3. Số đo chi phí (AC8)

Đọc từ `ops.llm_call` (`purpose='chat'`), gồm cả các lượt nghiệm thu và lượt chạy lại:

| | Giá trị |
|---|---|
| Số request | **47** cho ≈ 22 câu hỏi ⇒ **≈ 2,1 request/câu** |
| Token vào p50 / request | 5.268 *(trung vị thấp vì lượt tiếp theo trong cùng câu đọc cache)* |
| Token vào của một request "lạnh" | **≈ 36.750** — khớp ước lượng 38.100 của spec §4.3 |
| Token ra p50 | 854 |
| Độ trễ p50 · p90 · max | **6,9 s · 34,5 s · 41,8 s** |
| Tổng token | vào 700.149 · đọc cache 1.190.706 · ra 61.637 |
| Chi phí quy giá pay-go | **$0,3555 cho 22 câu ⇒ ≈ $0,016/câu** |
| Quota Token Plan | cửa sổ 5 giờ tụt từ ~99% xuống **69%** sau toàn bộ lượt |

🔴 **Phát hiện về cache, khác với ghi chép cũ:** cache tự động của MiniMax trúng **rất tốt trong cùng một cuộc hội thoại** (lượt 2 của một câu: vào 409 token, đọc cache 36.886) nhưng **không trúng giữa hai câu hỏi khác nhau** dù tiền tố `tools + system` giống hệt và cách nhau vài giây (mọi request đầu câu đều `cache_read = 128`, mức nền). ⇒ ngân sách phải tính **một lần trả đủ ~36,7k token cho mỗi câu mới**, phần cache chỉ cứu các lượt gọi function tiếp theo.

Chi phí thật **$0,016/câu** thấp hơn ước lượng $0,022–0,048 của spec, vì spec giả định 3 request/câu đều trả đủ tiền còn thực tế chỉ request đầu là "lạnh".

## 4. Nghiệm thu khác

| AC | Kết quả |
|---|---|
| **AC1** `tool_runner` chạy với MiniMax | ✅ — spike Task 0 và mọi lượt chat |
| **AC2** không test nào xanh thành đỏ | ✅ — `main` **877 passed, 2 skipped**; nhánh **951 passed, 2 skipped** (+74, không skip mới) |
| **AC3** đường đọc dưới `dlck_api`, không ghi được | ✅ — `current_user=agent_reader`, thuộc `dlck_api`, `INSERT` bị chặn (`ProgrammingError`); `assert_read_only()` chạy ở khởi động |
| **AC4** cả 9 function trả đúng dữ liệu thật | ✅ — bảng §2 |
| **AC5** câu ngoài lĩnh vực bị từ chối gọn | ✅ — 4/4 (ẩm thực, lập trình, và hai câu trong lượt nghiệm thu) |
| **AC6** VN-Index: nói thẳng kho chưa có | ⚠️ **đạt sau khi sửa**. Lượt đầu model **không gọi function nào**, tự đoán là không tra được rồi đẩy sang trang ngoài — đúng kết quả nhưng sai đường. Sau khi mô tả function nói rõ "luôn gọi trước khi nói về giá hay điểm của bất kỳ mã nào, kể cả VN-Index", model gọi `get_price_series`, nhận "kho chưa có dữ liệu giá cho chỉ số VNINDEX" và nói đúng điều đó |
| **AC7** bộ hồi quy | ❌ **không đạt** — số 15/15 nhưng hình dạng 12/15 (ngưỡng 14) |
| **AC8** đo chi phí | ✅ — §3 |
| **AC9** không rò kết nối | ✅ — `idle in transaction` của `agent_reader` = **0**, tổng kết nối đang mở = 0 |

## 5. Ba lỗi code mà lượt chạy thật lộ ra (đã sửa, có test canh)

| # | Lỗi | Bằng chứng | Sửa |
|---|---|---|---|
| 1 | **`max_tokens = 4000` cắt câu trả lời, im lặng** | 3/40 request `stop_reason=max_tokens`; một request tiêu **3.999 token chỉ cho thinking** rồi hết chỗ cho chữ ⇒ A2, A4, B9 trả về **rỗng** | nâng lên 8.000; vòng chat không bao giờ trả rỗng im lặng nữa mà nói rõ model dừng vì lý do gì |
| 2 | **Model từ chối tra dữ liệu vì tưởng mốc thời gian nằm ngoài tri thức của nó** | hỏi CPI tháng 8/2026, model trả *"mốc cập nhật gần nhất của tôi là tháng 1/2026"* và **không gọi function** — trong khi kho có đúng số 4,45% | thêm block system thứ ba: neo ngày hôm nay + bắt gọi công cụ trước khi nói "không có" |
| 3 | **Sổ `ops.llm_call` ghi mọi lượt gọi công cụ thành `failed`** | ánh xạ `status='ok'` chỉ cho `end_turn` | `tool_use` cũng là `ok` — nó là bước bình thường giữa chừng |

Lỗi 1 và 2 đều thuộc loại **hỏng im lặng**: không exception, không cờ lỗi, chỉ có câu trả lời rỗng hoặc câu trả lời sai một cách tự tin. Đúng họ với bẫy mà CLAUDE.md §3.4 đã ghi.

## 6. Kết luận về hợp đồng

**Hợp đồng đứng vững ở phần dữ kiện, chưa vững ở phần hình dạng.**

- Function calling **không** làm hỏng độ chính xác: 15/15 số đúng, 9/9 function được gọi đúng chỗ, và model biết nói "kho chưa có" thay vì bịa khi được mô tả function bảo nó phải tra trước.
- Nhưng L1 **mất quyền định hình ở đúng những câu khó nhất**: hai câu tính nặng nhất rơi vào lối trình bày tài liệu tham khảo, và một câu tra cứu thuần (B5) tụt xuống mức liệt kê. Câu nhắc "quay lại mạch L1" chèn ở lượt `tool_result` **không cứu được** hai ca A3/A4b vì chúng không gọi function nào hoặc chỉ gọi một lần rồi tự trình bày.
- Model còn **bịa số dẫn xuất** (dải nhạy của A4b) — chỗ này function calling không giúp được gì vì đó là số tự tính, không phải số tra.

**Đây là kết quả của lát, không phải lỗi cần giấu.** Ba việc kế tiếp, xếp theo giá trị: (1) làm rõ trong L1 rằng phần trình bày phép tính vẫn phải là văn xuôi có mạch, không phải bảng công thức; (2) thêm một mục vào rubric buộc mọi số **dẫn xuất** phải kèm phép tính; (3) đo lại xem câu nhắc `REMINDER` có tác dụng thật không — hiện chưa có số đối chứng vì mọi lượt đều chạy **có** nhắc.
