# Plan lát 11 — đóng hợp đồng tầng ngữ nghĩa và trả hết bảy nợ

> **Cho người thực thi:** dùng `superpowers:subagent-driven-development` hoặc `executing-plans`. Mỗi bước là một checkbox.

**Mục tiêu:** Đưa luật trình bày và luật cấm khuyến nghị xuống tầng prompt, chạy lại bộ hồi quy 15 câu đạt **≥ 14/15 hình dạng**, và đóng cả bảy nợ lát 10.

**Kiến trúc:** Thêm **một block system ổn định** (`ANSWER_RULES`) giữa L1 và khối luật công cụ — không đụng nội dung skill, không đụng `SCOPE_GUARD`. Ba thay đổi code còn lại đều nhỏ và rời nhau: một lệnh `/moi` trong REPL, một test canh đường khởi động, một lần cắt trường dư khỏi payload chuỗi giá. Hai lượt chạy model là **phép đo**, không phải test.

**Tech stack:** Python 3.12 · pytest · SQLAlchemy · MiniMax M3 qua SDK `anthropic` · Postgres (role `agent_reader` đọc, `dlck_etl` ghi sổ).

**Spec:** [`spec.md`](spec.md) — đã duyệt 2026-09-07.

## Global Constraints

- Nhánh `feat/semantic-layer-closeout`; **không** commit thẳng `main`, **không** `--no-verify`, **không** force push.
- Mọi lệnh Python chạy **từ trong `backend/`**: `cd backend && uv run --project . …`. Chạy `uv run --project backend` sẽ ra `No module named agent` *(đính chính đã trả giá ở lát 10)*.
- Luôn `PYTHONIOENCODING=utf-8`, nếu không sẽ crash cp1252 khi in tiếng Việt.
- Mọi lượt gọi model chạy **tiền cảnh** — chạy nền thì tiến trình bị đóng băng (lát 10 đã trả giá).
- **Đỏ trước xanh** ở từng task; không viết implementation trước khi có test đỏ và nêu rõ assertion nào đỏ.
- Subagent (chỉ Task 7) **bắt buộc chỉ định model `sonnet`**; sàn thấp nhất là Sonnet.
- Tài liệu sống sửa **cùng commit** với thay đổi tạo ra nó.
- Không sửa `L1`/`L2` (nội dung skill), không thêm function mới, không đụng hình dạng kết quả của 9 function ngoài mục Task 5.

---

## Cây file

| File | Trách nhiệm | Task |
|---|---|---|
| `backend/agent/system_prompt.py` | Thêm hằng `ANSWER_RULES`, chèn vào `build_system_blocks()` | 1 |
| `backend/tests/agent/test_a03_system_prompt.py` | Seam: số block, thứ tự, block mới có mặt | 1 |
| `backend/tests/agent/test_a13_chat.py` | Sửa test cũ đang khẳng định **3** block | 1 |
| `backend/agent/chat.py` | `la_lenh_moi()` + xử lý trong `repl()` | 2 |
| `backend/tests/agent/test_a13_chat.py` | Seam `/moi`: hàm thuần + `repl` xoá lịch sử | 2 |
| `backend/tests/agent/test_a14_startup.py` *(mới)* | Canh đường khởi động dưới đúng role production | 3 |
| `backend/agent/tools/get_price_series.py` | Bỏ trường `ngay_hien_thi` khỏi payload | 5 |
| `backend/tests/agent/test_a05_price.py` | Sửa assertion theo payload mới | 5 |
| `docs/20-design/chatbot-semantic-layer.md` · `backend/README.md` · `docs/00-overview/roadmap.md` | Tài liệu sống | 1, 2, 8 |
| `docs/90-records/plans/2026-09-07-semantic-layer-closeout/` | `round8-*.md`, `ledger.md` | 4, 6, 8 |

---

## Task 1 — khối `ANSWER_RULES`

**Files:**
- Modify: `backend/agent/system_prompt.py`
- Test: `backend/tests/agent/test_a03_system_prompt.py`, `backend/tests/agent/test_a13_chat.py:143`

**Interfaces:**
- Produces: hằng `ANSWER_RULES: str`; `build_system_blocks()` trả **4** block theo thứ tự `SCOPE_GUARD` · L1 · `ANSWER_RULES` · tool rules.

- [ ] **Bước 1: viết test đỏ**

Thêm vào `backend/tests/agent/test_a03_system_prompt.py`:

```python
from agent.system_prompt import ANSWER_RULES, SCOPE_GUARD, build_system_blocks


def test_bon_block_dung_thu_tu_va_answer_rules_dung_thu_ba():
    blocks = build_system_blocks()
    assert len(blocks) == 4
    assert blocks[0]["text"] == SCOPE_GUARD
    assert blocks[2]["text"] == ANSWER_RULES


def test_khoi_mang_ngay_van_nam_cuoi_de_khong_pha_tien_to_cache():
    """Ba block đầu phải bất biến theo ngày; chỉ block cuối đổi."""
    import datetime as dt
    a = build_system_blocks(dt.date(2026, 9, 7))
    b = build_system_blocks(dt.date(2026, 9, 8))
    assert [x["text"] for x in a[:3]] == [x["text"] for x in b[:3]]
    assert a[3]["text"] != b[3]["text"]
```

- [ ] **Bước 2: chạy cho thấy đỏ**

```bash
cd backend && PYTHONIOENCODING=utf-8 uv run --project . pytest tests/agent/test_a03_system_prompt.py -q
```

Đỏ ở: `ImportError: cannot import name 'ANSWER_RULES'`. Ghi lại nguyên văn.

- [ ] **Bước 3: implement tối thiểu**

Trong `backend/agent/system_prompt.py`, thêm sau `SCOPE_GUARD`:

```python
ANSWER_RULES = """Mọi con số bạn tự tính ra — không có trong câu hỏi và không do công cụ trả về — phải hiện phép tính BẰNG SỐ ngay tại chỗ: thay số vào công thức, ra kết quả. Nêu một con số dẫn xuất trần, kể cả dải nhạy hay ước lượng nhanh, là bịa.

Nói rõ số nào tra được từ dữ liệu, số nào là giả định của đề.

Không nêu tỷ trọng danh mục, điểm mua, điểm bán hay vùng giá cụ thể cho bất kỳ mã nào, và không dùng câu mang nghĩa hành động ("gom dần", "mua thêm khi giá về…"). Nêu điều kiện làm kết luận đổi thì được."""
```

và trong `build_system_blocks`, chèn giữa L1 và tool rules:

```python
    return [
        {"type": "text", "text": SCOPE_GUARD},
        {"type": "text", "text": _L1_CACHE},
        {"type": "text", "text": ANSWER_RULES},
        {"type": "text", "text": build_tool_rules(hom_nay)},
    ]
```

Cập nhật docstring module: nói rõ `ANSWER_RULES` là **luật trình bày của tầng sản phẩm**, sinh ra sau vòng 7 (hình dạng 13/15, A4b bịa dải nhạy), và vì sao nó **không** nằm trong `TOOL_RULES` (khối đó mang ngày, đổi mỗi ngày).

- [ ] **Bước 4: sửa hai test cũ đang khẳng định 3 block**

`test_a03_system_prompt.py::test_block_dau_tien_la_scope_guard` và `test_a13_chat.py::test_system_du_ba_block_va_scope_guard_dung_truoc` — đổi `== 3` thành `== 4`, đổi tên test thứ hai thành `test_system_du_bon_block_va_scope_guard_dung_truoc`.

- [ ] **Bước 5: chạy toàn bộ**

```bash
cd backend && PYTHONIOENCODING=utf-8 uv run --project . pytest tests/agent -q
```

Kỳ vọng: xanh, số test tăng đúng **+2**.

- [ ] **Bước 6: commit**

```bash
git add backend/agent/system_prompt.py backend/tests/agent/test_a03_system_prompt.py backend/tests/agent/test_a13_chat.py
git commit -m "feat(agent): the rule we grade by now lives where the model reads it"
```

---

## Task 2 — lệnh `/moi` thoát phiên tràn

**Files:**
- Modify: `backend/agent/chat.py:128-150`
- Test: `backend/tests/agent/test_a13_chat.py`

**Interfaces:**
- Produces: `la_lenh_moi(cau: str) -> bool` — `True` khi chuỗi đã strip, hạ chữ thường bằng `/moi` hoặc `/mới`.

- [ ] **Bước 1: viết test đỏ**

```python
from agent.chat import la_lenh_moi


def test_la_lenh_moi_nhan_dung_bien_the():
    assert la_lenh_moi("/moi") and la_lenh_moi("  /MOI  ") and la_lenh_moi("/mới")
    assert not la_lenh_moi("/moi gi do") and not la_lenh_moi("moi") and not la_lenh_moi("")


def test_repl_xoa_lich_su_khi_go_lenh_moi(monkeypatch, tool_dem, model_gia):
    """Sau /moi, lượt kế phải gửi đi lịch sử RỖNG — không mang câu cũ theo."""
    from agent import chat as chat_mod
    cau = iter(["câu một", "/moi", "câu hai", EOFError])
    def gia_input(_prompt):
        v = next(cau)
        if v is EOFError:
            raise EOFError
        return v
    monkeypatch.setattr("builtins.input", gia_input)
    lich_su_da_gui = []
    that = chat_mod.run_turn
    def ghi_lai(llm, read_eng, ops_eng, history, cau_hoi):
        lich_su_da_gui.append(list(history))
        return that(llm, read_eng, ops_eng, history, cau_hoi)
    monkeypatch.setattr(chat_mod, "run_turn", ghi_lai)
    chat_mod.repl(model_gia, None, None)
    assert lich_su_da_gui[0] == []          # lượt đầu: rỗng
    assert lich_su_da_gui[1] == []          # sau /moi: RỖNG lại, đây là assertion đỏ
```

- [ ] **Bước 2: chạy cho thấy đỏ** — `ImportError: cannot import name 'la_lenh_moi'`.

- [ ] **Bước 3: implement**

```python
LENH_MOI = {"/moi", "/mới"}


def la_lenh_moi(cau: str) -> bool:
    return cau.strip().lower() in LENH_MOI
```

trong `repl`, ngay sau `if not cau: continue`:

```python
        if la_lenh_moi(cau):
            history.clear()
            print("\n[đã xoá lịch sử — bắt đầu phiên mới]\n")
            continue
```

Sửa dòng chào đầu `repl` thành: `"Hỏi về chứng khoán, tài chính, kinh tế. /moi để xoá lịch sử, Ctrl+C để thoát.\n"`.

- [ ] **Bước 4: chạy lại** — hai test mới xanh, `tests/agent` xanh toàn bộ.

- [ ] **Bước 5: cập nhật `backend/README.md`** — mục vòng chat thêm một dòng: `/moi` xoá lịch sử, dùng khi phiên tràn cửa sổ ngữ cảnh (`review-chuan-v4 §G3`).

- [ ] **Bước 6: commit**

```bash
git add backend/agent/chat.py backend/tests/agent/test_a13_chat.py backend/README.md
git commit -m "feat(agent): a full context window is no longer a dead end"
```

---

## Task 3 — test canh đường khởi động, chạy dưới đúng role production

**Files:**
- Create: `backend/tests/agent/test_a14_startup.py`

**Interfaces:** không đổi code sản phẩm. Nếu `LLMSettings` đổi tên trường hoặc `read_engine` mất `assert_read_only`, test này phải đỏ.

- [ ] **Bước 1: viết test đỏ (đỏ bằng cách phá tạm)**

```python
"""§3.5 — kiểm LỆNH chứ không kiểm trạng thái, và chạy dưới đúng quyền production.

`main()` là đường DUY NHẤT dựng client thật: `replace(LLMSettings.from_env(), timeout_s=CHAT_TIMEOUT_S)`.
Lát 10 chỉ kiểm tay một lần (review-chuan-v4 §G5).
"""
import os
import pytest
import agent.__main__ as m


@pytest.mark.skipif(not os.getenv("AGENT_DATABASE_URL"), reason="cần credential production")
def test_main_dung_timeout_dai_va_mo_duoc_ket_noi_doc(monkeypatch):
    bat = {}
    def repl_gia(llm, read_eng, ops_eng):
        bat["timeout"] = llm._client.timeout          # timeout thật của client đã dựng
        bat["doc_duoc"] = read_eng.connect() is not None
    monkeypatch.setattr(m, "repl", repl_gia)
    assert m.main() == 0
    assert bat["timeout"] == m.CHAT_TIMEOUT_S == 600.0
    assert bat["doc_duoc"]
```

- [ ] **Bước 2: chứng minh test thật sự canh** — sửa tạm `__main__.py` bỏ `timeout_s=CHAT_TIMEOUT_S`, chạy test, **phải đỏ**; dán output; hoàn nguyên.

```bash
cd backend && PYTHONIOENCODING=utf-8 uv run --project . pytest tests/agent/test_a14_startup.py -q
```

- [ ] **Bước 3: chạy lại sau khi hoàn nguyên** — xanh. Nếu `llm._client.timeout` không phải thuộc tính đúng, đọc `core/llm/client.py` rồi sửa **test** cho khớp thực tế, không sửa code sản phẩm.

- [ ] **Bước 4: commit**

```bash
git add backend/tests/agent/test_a14_startup.py
git commit -m "test(agent): the startup path now has a guard, run under the real role"
```

---

## Task 4 — bộ hồi quy vòng 8 (AC2, AC3)

**Files:**
- Create: `docs/90-records/plans/2026-09-07-semantic-layer-closeout/round8-transcript-2026-09-07.md`, `round8-grading-2026-09-07.md`

- [ ] **Bước 1: chốt cách chạy — một tiến trình cho mỗi câu**

15 câu ở [`regression-round7.md`](../2026-09-07-semantic-layer/regression-round7.md), hỏi **nguyên văn**. Mỗi câu một tiến trình riêng (lịch sử rỗng) — sạch hơn vòng 7 (chạy theo khối) và **không đắt hơn**: lát 10 đo được cache MiniMax *không* trúng giữa hai câu khác nhau (`cache_read = 128` ở mọi request đầu câu).

```bash
cd backend && PYTHONIOENCODING=utf-8 printf '%s\n' "<câu hỏi nguyên văn>" | uv run --project . python -m agent
```

- [ ] **Bước 2: chạy đủ 15 câu, lưu transcript** — mỗi câu ghi: đề, đáp nguyên văn, thời gian, function đã gọi.

- [ ] **Bước 3: chấm hai lớp theo đúng rubric vòng 7** (`regression-round7.md` §Chấm — 5 mục, đạt khi ≥ 4/5 và không vi phạm mục 5 hoặc 6).

- [ ] **Bước 4: kiểm AC3 bằng grep trên transcript**

```bash
grep -niE "gom dần|mua thêm|tỷ trọng|điểm mua|vùng giá|giải ngân" docs/90-records/plans/2026-09-07-semantic-layer-closeout/round8-transcript-2026-09-07.md
```

Kỳ vọng: 0 dòng mang nghĩa khuyến nghị. Hit nào cũng phải đọc tay và ghi lại lý do chấp nhận.

- [ ] **Bước 5: đối chiếu hai câu trượt của vòng 7** — A4b (dải nhạy phải có phép tính) và B5 (phải diễn giải, không chỉ liệt kê). Ghi rõ đạt hay không.

- [ ] **Bước 6: dán số chi phí**

```sql
select count(*) as request, sum(input_tokens) as vao, sum(output_tokens) as ra,
       round(avg(latency_ms)) as tre_tb
from ops.llm_call where created_at >= '<mốc bắt đầu lượt>';
```

- [ ] **Bước 7: commit hồ sơ** *(kể cả khi chưa đạt — báo nguyên trạng, §4.1.6)*

```bash
git add docs/90-records/plans/2026-09-07-semantic-layer-closeout/round8-*.md
git commit -m "docs: round 8 — what the rule change actually did"
```

**Cổng:** đạt **≥ 14/15** thì sang Task 5. Không đạt thì **dừng, báo chủ dự án** kèm bảng chấm — spec §9 điểm 4 đã ghi: quyết định sau khi có số, không tự sửa tiếp.

---

## Task 5 — cắt trường dư khỏi payload chuỗi giá (nợ #7)

**Files:**
- Modify: `backend/agent/tools/get_price_series.py:74`
- Test: `backend/tests/agent/test_a05_price.py:27`

Số đo nền (review-chuan-v4 §G2): `get_price_series("BT6")` = **292.009 ký tự**, trong đó **19,9 %** là `ngay_hien_thi` lặp lại chính `ngay` (58.000 ký tự cho 2.000 phiên).

- [ ] **Bước 1: đo lại trước khi cắt** — chạy một lời gọi trần 2.000 phiên, ghi số ký tự.
- [ ] **Bước 2: sửa test trước** — `test_a05_price.py:27` bỏ assertion `ngay_hien_thi`, thêm assertion **không còn** khoá đó:

```python
    assert "ngay_hien_thi" not in phien
    assert phien["ngay"] == "2026-09-03"
```

- [ ] **Bước 3: chạy cho thấy đỏ** — `KeyError`/assertion về khoá còn tồn tại.
- [ ] **Bước 4: bỏ `"ngay_hien_thi": format_date_vi(r.trading_date),` khỏi dict**; nếu `format_date_vi` thành import mồ côi thì dọn (§4.4.3 — rác do chính thay đổi tạo ra).
- [ ] **Bước 5: đo lại sau khi cắt**, kỳ vọng giảm **≈ 19–20 %**; dán hai số.
- [ ] **Bước 6:** `pytest tests/agent -q` xanh, rồi commit.

⚠️ **Chỉ sửa `get_price_series`.** `get_macro_series` và `get_news` cũng có cùng trường lặp — **báo, không tự sửa**: chưa ai đo phần dư của chúng, và spec giới hạn ở chuỗi giá.

---

## Task 6 — lượt A/B `REMINDER` (AC4, nợ #3)

- [ ] **Bước 1: sửa tạm, không commit** — trong `backend/agent/chat.py` đổi `REMINDER` thành chuỗi rỗng (hoặc bỏ dòng chèn ở `chat.py:91`). Đây là **thủ tục đo**, không phải thay đổi sản phẩm: không thêm biến môi trường cho một lượt đo (§4.4.2).
- [ ] **Bước 2: chạy lại đúng 15 câu** như Task 4, lưu `round8-noreminder-transcript-2026-09-07.md`.
- [ ] **Bước 3: chấm cùng rubric**, đặt hai bảng cạnh nhau: có nhắc / không nhắc.
- [ ] **Bước 4: hoàn nguyên** `git checkout backend/agent/chat.py`, xác nhận `git status` sạch.
- [ ] **Bước 5: kết luận** — không khác biệt đáng kể ⇒ đề xuất **bỏ** `REMINDER` (tiết kiệm ~215 token mỗi lượt gọi công cụ); khác biệt rõ ⇒ giữ. **Chủ dự án quyết**, ghi vào ledger.

---

## Task 7 — review độc lập hai trục (nợ #6)

- [ ] **Bước 1: gói diff** — bốn commit lát 10 (`56ceeaa`, `943bcfd`, `8624c38`, `7ec99c7`) **cộng** toàn bộ commit của lát này, xuất ra scratchpad ngoài repo.
- [ ] **Bước 2: giao subagent `sonnet`** *(bắt buộc chỉ định model — bỏ trống là kế thừa Fable, vi phạm ngầm)*, đề bài **tự đủ**: đường dẫn file, spec, tiêu chí. Hai trục báo **riêng**, không gộp, không xếp hạng chéo:
  - **Chuẩn**: đúng luật repo (CLAUDE.md §4.4, §4.5) + code smell.
  - **Spec**: thiếu · sai · scope-creep so với `spec.md`.
- [ ] **Bước 3: xử từng finding** — Critical/Important sửa ngay (TDD); Minor hoãn phải ghi **lý do** vào ledger.
- [ ] **Bước 4:** nếu đợt sửa đụng prompt hoặc payload ⇒ **chạy lại bộ hồi quy**; vòng 2 và vòng 4 của lát 10 đều bắt được hồi quy do chính đợt sửa trước đẻ ra.

---

## Task 8 — tài liệu sống, ledger, đóng nợ

- [ ] **Bước 1: `docs/20-design/chatbot-semantic-layer.md`** — bốn block và thứ tự; luật mới thuộc tầng sản phẩm.
- [ ] **Bước 2: `docs/00-overview/roadmap.md`** — bảng bảy nợ ở "Điểm vào cho lát 11" chuyển sang trạng thái thật; `ops.llm_call` và `news.trade_name` chuyển thành nợ **có phân loại** ở lát API / ETL tin (§1.4).
- [ ] **Bước 3: ledger** `docs/90-records/plans/2026-09-07-semantic-layer-closeout/ledger.md` — tiến trình từng task, rulings, AC1–AC8 kèm bằng chứng, nợ còn lại.
- [ ] **Bước 4: phép kiểm §1.7** — `git grep` các số/tên vừa đổi (`ba block`, `13/15`, `1.025 test`), xác nhận mọi hit còn lại **hoặc đã đúng, hoặc thuộc vùng lịch sử** (`90-records/`, `decisions/`). Dán kết quả.
- [ ] **Bước 5: verify trước khi báo xong** — `pytest tests -q` toàn repo, dán output thật.
- [ ] **Bước 6: viết "Điểm vào cho lát 12"** trong roadmap và merge `--no-ff` vào `main`.

---

## Tự rà plan này

**Phủ spec:** §3.1 → Task 1 · §3.2 → Task 2 · §3.3 → Task 3 · AC2/AC3 → Task 4 · §5 payload → Task 5 · AC4 → Task 6 · AC7 → Task 7 · §8 tài liệu → Task 8. **Không mục nào của spec không có task.**

**Chỗ trống:** không có bước nào ghi "TBD" hay "xử lý lỗi phù hợp"; mọi bước code đều có code thật.

**Nhất quán tên:** `ANSWER_RULES` (Task 1) · `la_lenh_moi` (Task 2) · `CHAT_TIMEOUT_S` (Task 3) · `ngay_hien_thi` (Task 5) — dùng đúng một tên ở mọi chỗ.

**Rủi ro đã biết:** Task 5 bỏ trường hiển thị có thể làm model in ngày dạng ISO ⇒ ảnh hưởng mục 1 của rubric. Task 6 chạy lại đủ 15 câu **sau** Task 5 nên sẽ bắt được; nếu bắt được thì hoàn nguyên Task 5 và ghi lại, không sửa rubric.
