# Kết quả bộ hồi quy vòng 7 — chạy thật 2026-09-07

Bộ câu: [`regression-round7.md`](regression-round7.md) · Transcript đầy đủ: [`round7-transcript-2026-09-07.md`](round7-transcript-2026-09-07.md) · Bảng chấm chi tiết: [`round7-grading-2026-09-07.md`](round7-grading-2026-09-07.md)

Chạy bằng `python -m agent` trên kho dev, **tiền cảnh, chia khối** 3–6 câu. Chấm bằng subagent Sonnet độc lập, không biết câu trả lời do đâu sinh ra.

---

## 1. Kết quả hai lớp

🔴 **Chấm hai lượt — rubric lượt đầu sai, đã sửa.** Chủ dự án chốt 2026-09-07: **"phép tính phải ghi số chứ không ghi văn xuôi"**. Rubric lượt đầu chấm mục 1 là *"mạch lập luận, không phải tờ công thức"* nên **phạt nhầm** hai câu tính toán trình bày đúng cách. Rubric đã sửa (chia mục 1 theo loại câu, thêm cổng *"số dẫn xuất phải kèm phép tính"*), và **chấm lại từ đầu cả 15 câu** trên thước đo mới. Bảng chấm: [lượt đầu](round7-grading-2026-09-07.md) · [lượt sửa](round7-grading-v2-2026-09-07.md).

| | Kết quả | Ngưỡng AC7 | |
|---|---|---|---|
| **Lớp 1 — số** | **15/15 đúng** | 15/15 | ✅ đạt |
| **Lớp 2 — hình dạng L1** | **13/15 đạt** *(12/15 ở lượt chấm đầu)* | ≥ 14/15 | ❌ **không đạt** |

**Hai câu còn trượt — cả hai là lỗi thật, không phải do thước đo:**

| Câu | Trượt vì |
|---|---|
| A4b (Gordon) | 🔴 **bịa số dẫn xuất**: tự thêm dải nhạy "23.500–32.500 đồng" cho `Ke ± 1%` mà **không hiện phép tính nào**; tính đúng phải là **≈ 24.643–30.962 đồng** — lệch 4–5% ở cả hai đầu, không phải làm tròn. Vi phạm cổng 6 |
| B5 (cổ tức FPT) | chỉ liệt kê hai sự kiện rồi dừng, không diễn giải, không nêu điều kiện đổi kết luận — 3/5, dưới ngưỡng |

**Câu đổi kết quả:** A3 (WACC) từ trượt sang **đạt** — nó trình bày phép tính bằng số, đúng cách; rubric cũ phạt nó vì lý do sai. B5 giữ nguyên trượt: lượt đầu chấm đúng.

**Mẫu hỏng lặp lại nhất** (giữ nguyên qua cả hai lượt): mục *"phân biệt số nào tra được, số nào là giả định của đề"* bị bỏ ở **5/15 câu** — mục dễ đạt nhất lại hay quên nhất.

**Rà quét lại toàn bộ 15 câu theo cổng mới:** ngoài A4b, **không còn con số dẫn xuất nào bị nêu trần** — mọi số trung gian ở nhóm A đều kèm phép tính tại chỗ, mọi số ở nhóm B đều gắn với kết quả tra cứu.

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
| **AC2** không test nào xanh thành đỏ | ✅ — `main` **877 passed, 2 skipped**; nhánh **953 passed, 2 skipped** (+76, không skip mới) |
| **AC3** đường đọc dưới `dlck_api`, không ghi được | ✅ — chạy tay dưới đúng credential production, output nguyên văn ở §7 |
| **AC4** cả 9 function trả đúng dữ liệu thật | ✅ — bảng §2 |
| **AC5** câu ngoài lĩnh vực bị từ chối gọn | ⚠️ **2/4 có transcript** — ẩm thực và lập trình lưu ở [acceptance-transcript](acceptance-transcript-2026-09-07.md); hai câu còn lại (sức khoẻ, pháp lý) chạy nhưng **không lưu transcript**, nên chỉ tính hai câu có bằng chứng |
| **AC6** VN-Index: nói thẳng kho chưa có | ⚠️ **đạt sau khi sửa**. Lượt đầu model **không gọi function nào**, tự đoán là không tra được rồi đẩy sang trang ngoài — đúng kết quả nhưng sai đường. Sau khi mô tả function nói rõ "luôn gọi trước khi nói về giá hay điểm của bất kỳ mã nào, kể cả VN-Index", model gọi `get_price_series`, nhận "kho chưa có dữ liệu giá cho chỉ số VNINDEX" và nói đúng điều đó |
| **AC7** bộ hồi quy | ❌ **không đạt** — số 15/15, hình dạng **13/15** sau khi sửa rubric (ngưỡng 14). Hai câu trượt là lỗi thật: một ca bịa số dẫn xuất, một ca tra cứu không diễn giải |
| **AC8** đo chi phí | ✅ — §3 |
| **AC9** không rò kết nối | ✅ — output nguyên văn ở §7 |

## 5. Ba lỗi code mà lượt chạy thật lộ ra

🔴 **Đính chính 2026-09-07 (review trục Spec bắt được):** mục này ban đầu viết *"đã sửa, **có test canh**"*. Sai — `git show --stat d23913c` cho thấy **chỉ 1/3 lỗi có test** lúc đó (lỗi 2). Viết một khẳng định chưa kiểm chính là loại lỗi tự đầu độc mà CLAUDE.md §3.2 cấm: nó chặn mất phép kiểm sẽ tìm ra chỗ hở. Hai test còn thiếu đã bổ sung sau lượt review (`test_ket_thuc_sach_nhung_khong_co_chu_van_khong_tra_rong` cho lỗi 1, `test_luot_tool_use_ghi_so_la_ok` cho lỗi 3).

| # | Lỗi | Bằng chứng | Sửa |
|---|---|---|---|
| 1 | **`max_tokens = 4000` cắt câu trả lời, im lặng** | 3/40 request `stop_reason=max_tokens`; một request tiêu **3.999 token chỉ cho thinking** rồi hết chỗ cho chữ ⇒ A2, A4, B9 trả về **rỗng** | nâng lên 8.000; vòng chat không bao giờ trả rỗng im lặng nữa mà nói rõ model dừng vì lý do gì |
| 2 | **Model từ chối tra dữ liệu vì tưởng mốc thời gian nằm ngoài tri thức của nó** | hỏi CPI tháng 8/2026, model trả *"mốc cập nhật gần nhất của tôi là tháng 1/2026"* và **không gọi function** — trong khi kho có đúng số 4,45% | thêm block system thứ ba: neo ngày hôm nay + bắt gọi công cụ trước khi nói "không có" |
| 3 | **Sổ `ops.llm_call` ghi mọi lượt gọi công cụ thành `failed`** | ánh xạ `status='ok'` chỉ cho `end_turn` | `tool_use` cũng là `ok` — nó là bước bình thường giữa chừng |

Cả ba nay đều có test canh. Lỗi 1 và 2 thuộc loại **hỏng im lặng**: không exception, không cờ lỗi, chỉ có câu trả lời rỗng hoặc câu trả lời sai một cách tự tin. Đúng họ với bẫy mà CLAUDE.md §3.4 đã ghi.

## 6. Kết luận về hợp đồng

**Hợp đồng đứng vững ở phần dữ kiện, chưa vững ở phần hình dạng.**

- Function calling **không** làm hỏng độ chính xác: 15/15 số đúng, 9/9 function được gọi đúng chỗ, và model biết nói "kho chưa có" thay vì bịa khi được mô tả function bảo nó phải tra trước.
- Chỗ hỏng thật còn lại có **hai** kiểu, và chỉ một trong hai liên quan tới hình dạng: (a) model **bịa số dẫn xuất** — dải nhạy của A4b, function calling không cứu được vì đó là số tự tính chứ không phải số tra; (b) một câu tra cứu thuần (B5) tụt xuống mức liệt kê, không diễn giải.
- Câu nhắc "quay lại mạch L1" chèn ở lượt `tool_result` **chưa đo được tác dụng** — mọi lượt đều chạy *có* nhắc nên không có số đối chứng.

**Đây là kết quả của lát, không phải lỗi cần giấu.** Hai việc kế tiếp, xếp theo giá trị: (1) buộc mọi số **dẫn xuất** phải kèm phép tính — đã đưa vào rubric thành cổng loại trực tiếp, còn cần đưa thành luật ở tầng prompt để chặn từ đầu chứ không chỉ bắt lúc chấm; (2) đo xem `REMINDER` có tác dụng thật không, bằng cách chạy một lượt **không** nhắc để đối chứng.

*(Việc "sửa L1 cho câu tính toán viết văn xuôi" đã bị **loại** — chủ dự án chốt 2026-09-07: bài tính phải hiện phép tính bằng số. Không đụng vào L1.)*


## 7. Output nguyên văn của AC3 và AC9

**AC3 — chạy tay `agent.db.read_engine()` dưới đúng credential production** *(2026-09-07)*:

```
doc duoc market.security: 2017
current_user: agent_reader
thuoc dlck_api: True
co quyen INSERT: False
ghi bi chan dung: ProgrammingError
assert_read_only da chay va qua
ops engine doc duoc ops.llm_call: 230
```

**AC9 — sau khi thoát vòng chat** *(2026-09-07)*:

```
AC9 — ket noi ro ri cua agent_reader:
   idle in transaction: 0
   tong ket noi agent_reader dang mo: 0
```

**AC2 — hai lượt chạy đối chứng:**

```
main:                877 passed, 2 skipped in 79.77s
feat/semantic-layer: 953 passed, 2 skipped in 85.57s
```
