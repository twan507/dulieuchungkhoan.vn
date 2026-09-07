"""Seam S6 — vòng chat, chạy với model GIẢ (không gọi API thật).

🔴 Test quan trọng nhất của lát: `generate_tool_call_response()` CÓ CACHE, còn
`append_messages()` XOÁ cache (`anthropic/lib/tools/_beta_runner.py:150`). Gọi `generate` rồi
`append` thì vòng lặp bên trong SDK gọi `generate` lần nữa với cache rỗng ⇒ **mọi function
chạy HAI LẦN**, mà lịch sử message vẫn đúng nên không có gì báo. `test_tool_chay_dung_mot_lan`
là chốt canh đúng lỗi đó — nó đỏ nếu ai đó "sửa cho gọn" bằng cách gọi lại append_messages.

Model giả dựng bằng `httpx2.MockTransport`, cùng khuôn đã dùng ở tests/core/test_llm_client.py.
"""
import json

import httpx2
import pytest
from anthropic import beta_tool

from agent import chat as chat_mod
from agent.chat import REMINDER, run_turn
from core.llm.client import LLMClient
from core.llm.settings import LLMSettings


def _msg(blocks, stop):
    return {"id": "msg_1", "type": "message", "role": "assistant", "model": "MiniMax-M3",
            "content": blocks, "stop_reason": stop, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5}}


@pytest.fixture()
def model_gia():
    """Lượt 1 gọi công cụ (kèm block thinking có signature), lượt 2 trả lời."""
    ghi = {"requests": [], "n": 0}

    def handler(request: httpx2.Request) -> httpx2.Response:
        ghi["n"] += 1
        ghi["requests"].append(json.loads(request.content))
        if ghi["n"] == 1:
            return httpx2.Response(200, json=_msg(
                [{"type": "thinking", "thinking": "can tra gia", "signature": "SIG-1"},
                 {"type": "tool_use", "id": "tu_1", "name": "get_price_series",
                  "input": {"ticker": "HPG"}}], "tool_use"))
        return httpx2.Response(200, json=_msg(
            [{"type": "text", "text": "Giá đóng cửa HPG là 21.600 đồng."}], "end_turn"))

    s = LLMSettings(api_key="khoa-gia", base_url="https://api.minimax.io/anthropic",
                    model="MiniMax-M3", timeout_s=30)
    llm = LLMClient(s, http_client=httpx2.Client(transport=httpx2.MockTransport(handler)))
    yield llm, ghi
    llm.close()


@pytest.fixture()
def tool_dem(monkeypatch):
    """Thay 9 tool thật bằng một tool đếm số lần chạy."""
    dem = {"n": 0}

    @beta_tool
    def get_price_series(ticker: str, from_date: str | None = None,
                         to_date: str | None = None, adjusted: bool = True) -> str:
        """Giá cổ phiếu."""
        dem["n"] += 1
        return json.dumps({"ma": ticker, "dong_cua": "21.600 đ"}, ensure_ascii=False)

    monkeypatch.setattr(chat_mod, "build_tools", lambda engine: [get_price_series])
    return dem


def test_tool_chay_dung_mot_lan(model_gia, tool_dem):
    llm, _ = model_gia
    tra_loi, _ = run_turn(llm, None, None, [], "Giá HPG?")
    assert tool_dem["n"] == 1, "tool bị gọi lại — xem lại chỗ cache của generate_tool_call_response"
    assert "21.600" in tra_loi


def test_loi_nhac_di_kem_tool_result(model_gia, tool_dem):
    llm, ghi = model_gia
    run_turn(llm, None, None, [], "Giá HPG?")
    khoi = ghi["requests"][1]["messages"][-1]["content"]
    assert any(b.get("type") == "tool_result" for b in khoi)
    assert any(b.get("type") == "text" and REMINDER[:30] in b["text"] for b in khoi)


def test_thinking_signature_duoc_echo_nguyen_van(model_gia, tool_dem):
    llm, ghi = model_gia
    run_turn(llm, None, None, [], "Giá HPG?")
    assistant = ghi["requests"][1]["messages"][-2]
    assert assistant["role"] == "assistant"
    assert any(b.get("signature") == "SIG-1" for b in assistant["content"])


def test_lich_su_dung_hinh_dang_sau_mot_luot(model_gia, tool_dem):
    llm, ghi = model_gia
    _, lich_su = run_turn(llm, None, None, [], "Giá HPG?")
    assert lich_su[0]["role"] == "user" and lich_su[0]["content"] == "Giá HPG?"
    assert lich_su[-1]["role"] == "assistant"
    assert len(lich_su) == 4          # user · assistant(tool_use) · user(tool_result) · assistant


def test_luot_thu_hai_that_su_gui_lai_lich_su_luot_dau(tool_dem):
    """Bẫy G5: runner của SDK cạn iterator sau một lượt, gọi lại KHÔNG ném lỗi và KHÔNG gửi
    request — nó lặng lẽ trả message cũ. Chỉ gọi run_turn một lần thì không ai canh chỗ đó.
    Test này gọi HAI lượt và soi request thứ hai có mang câu hỏi lượt đầu hay không."""
    ghi = {"requests": [], "n": 0}

    def handler(request):
        ghi["n"] += 1
        ghi["requests"].append(json.loads(request.content))
        if ghi["n"] == 1:
            return httpx2.Response(200, json=_msg(
                [{"type": "text", "text": "Đáp lượt một."}], "end_turn"))
        return httpx2.Response(200, json=_msg(
            [{"type": "text", "text": "Đáp lượt hai."}], "end_turn"))

    llm = _llm_gia(handler)
    try:
        tra1, ls1 = run_turn(llm, None, None, [], "Câu một?")
        tra2, ls2 = run_turn(llm, None, None, ls1, "Câu hai?")
    finally:
        llm.close()

    assert tra1 == "Đáp lượt một." and tra2 == "Đáp lượt hai."
    assert ghi["n"] == 2, "lượt hai phải gửi request THẬT, không được trả lại message cũ"
    noi_dung = [m["content"] for m in ghi["requests"][1]["messages"]]
    assert "Câu một?" in noi_dung and "Câu hai?" in noi_dung
    assert len(ls2) == 4              # hai cặp user/assistant


def test_ket_thuc_sach_nhung_khong_co_chu_van_khong_tra_rong(tool_dem):
    """Lưới của lỗi `max_tokens` đo được 2026-09-07: không bao giờ in ra `Trợ lý: ` trống."""
    def handler(request):
        return httpx2.Response(200, json=_msg([], "end_turn"))

    llm = _llm_gia(handler)
    try:
        tra_loi, lich_su = run_turn(llm, None, None, [], "Giá HPG?")
    finally:
        llm.close()
    assert tra_loi.strip()
    assert "không sinh câu trả lời" in tra_loi
    assert len(lich_su) == 2


def test_system_du_bon_block_va_scope_guard_dung_truoc(model_gia, tool_dem):
    """L1 phải có mặt từ request ĐẦU TIÊN — không bao giờ đến sau function.

    Bốn block từ lát 11: SCOPE_GUARD · L1 · ANSWER_RULES · luật công cụ mang ngày.
    """
    llm, ghi = model_gia
    run_turn(llm, None, None, [], "Giá HPG?")
    system = ghi["requests"][0]["system"]
    assert len(system) == 4
    assert "chỉ trả lời trong lĩnh vực chứng khoán" in system[0]["text"]
    assert len(system[1]["text"]) > 50_000


# --- Hai đường thoát dở dang: lịch sử không được nhiễm độc (review trục Chuẩn, C2) ---
#
# Chạm MAX_ITERATIONS: `_should_stop()` của SDK kiểm ở ĐẦU vòng nên runner dừng ngay sau một
# lượt `tool_use`, không có lượt assistant cuối ⇒ lịch sử kết thúc bằng role=user, lượt sau
# thành HAI lượt `user` liên tiếp — Messages API từ chối. Còn `stop_reason='max_tokens'` rơi
# giữa một block `tool_use` để lại `tool_use` KHÔNG có `tool_result` theo sau. Cả hai đều làm
# mọi lượt chat SAU đó nổ, mà `repl` lại "giữ nguyên lịch sử" nên hỏng là hỏng cả phiên.


def _llm_gia(handler):
    from core.llm.client import LLMClient
    from core.llm.settings import LLMSettings
    s = LLMSettings(api_key="khoa-gia", base_url="https://api.minimax.io/anthropic",
                    model="MiniMax-M3", timeout_s=30)
    return LLMClient(s, http_client=httpx2.Client(transport=httpx2.MockTransport(handler)))


def test_cham_tran_vong_lap_thi_giu_nguyen_lich_su_cu(tool_dem):
    """Model gọi công cụ mãi không dừng ⇒ bỏ lượt, trả lại đúng lịch sử đã có."""
    def handler(request):
        return httpx2.Response(200, json=_msg(
            [{"type": "tool_use", "id": "tu_x", "name": "get_price_series",
              "input": {"ticker": "HPG"}}], "tool_use"))

    llm = _llm_gia(handler)
    try:
        cu = [{"role": "user", "content": "câu trước"}, {"role": "assistant", "content": "đáp trước"}]
        tra_loi, moi = run_turn(llm, None, None, cu, "Giá HPG?")
    finally:
        llm.close()
    assert moi == cu, "lịch sử phải giữ nguyên, không được nhận lượt dở dang"
    assert tra_loi.strip(), "không được trả chuỗi rỗng"
    assert "dừng giữa chừng" in tra_loi


def test_het_max_tokens_giua_luot_cong_cu_thi_bo_luot(tool_dem):
    """max_tokens rơi giữa tool_use ⇒ lịch sử sẽ có tool_use không tool_result — phải bỏ lượt."""
    def handler(request):
        return httpx2.Response(200, json=_msg(
            [{"type": "tool_use", "id": "tu_y", "name": "get_price_series",
              "input": {"ticker": "HPG"}}], "max_tokens"))

    llm = _llm_gia(handler)
    try:
        tra_loi, moi = run_turn(llm, None, None, [], "Giá HPG?")
    finally:
        llm.close()
    assert moi == [], "lịch sử rỗng ban đầu phải giữ rỗng, không nhận lượt hỏng"
    assert "max_tokens" in tra_loi


def test_max_tokens_ma_luot_cuoi_chi_co_chu_thi_van_giu_cau_tra_loi(tool_dem):
    """Review vòng 2, F3: bản sửa C2 quét quá tay.

    `max_tokens` chỉ nguy hiểm khi nó rơi GIỮA một lượt `tool_use` (để lại tool_use không có
    tool_result). Nếu lượt cuối chỉ có chữ thì lịch sử hợp lệ hoàn toàn, và câu trả lời — dù
    bị cắt — vẫn đáng giá hơn là vứt đi cùng mọi kết quả tra cứu đã tốn công lấy về.
    """
    def handler(request):
        return httpx2.Response(200, json=_msg(
            [{"type": "text", "text": "Doanh thu thuần năm 2024 là 62.848,8 tỷ và"}], "max_tokens"))

    llm = _llm_gia(handler)
    try:
        tra_loi, lich_su = run_turn(llm, None, None, [], "Doanh thu FPT?")
    finally:
        llm.close()
    assert "62.848,8 tỷ" in tra_loi, "không được vứt câu trả lời hợp lệ"
    assert "cắt" in tra_loi, "phải nói rõ câu trả lời bị cắt giữa chừng"
    assert len(lich_su) == 2 and lich_su[-1]["role"] == "assistant"


def test_tran_cua_so_ngu_canh_thi_bo_luot_khong_lam_chet_phien(tool_dem):
    """Review vòng 3, F3: `ket_sach` chỉ nhìn `tool_use` là chưa đủ.

    `model_context_window_exceeded` nghĩa là lịch sử ĐÃ tràn cửa sổ. Nhận lượt đó vào lịch sử
    rồi nối tiếp chính nó ⇒ mọi lượt sau đều tràn, phiên chết cứng. Phải bỏ lượt và giữ lịch
    sử cũ — đó là trạng thái duy nhất còn hồi phục được.
    """
    def handler(request):
        return httpx2.Response(200, json=_msg([], "model_context_window_exceeded"))

    llm = _llm_gia(handler)
    try:
        cu = [{"role": "user", "content": "câu trước"}, {"role": "assistant", "content": "đáp trước"}]
        tra_loi, moi = run_turn(llm, None, None, cu, "câu dài quá?")
    finally:
        llm.close()
    assert moi == cu
    assert "model_context_window_exceeded" in tra_loi


def test_model_tu_choi_thi_bo_luot_khong_giu_vao_lich_su(tool_dem):
    """`refusal` cũng không phải kết thúc dùng lại được — nối tiếp từ đó dễ kích lại chính nó."""
    def handler(request):
        return httpx2.Response(200, json=_msg([], "refusal"))

    llm = _llm_gia(handler)
    try:
        tra_loi, moi = run_turn(llm, None, None, [], "câu gì đó")
    finally:
        llm.close()
    assert moi == []
    assert "refusal" in tra_loi


def test_mot_luot_co_han_chot_khong_cho_vo_han(tool_dem, monkeypatch):
    """Review vòng 4, N3: nới `MAX_TOKENS` và `MAX_ITERATIONS` mà quên đặt hạn cho CẢ LƯỢT.

    16 vòng × timeout 600 s ⇒ một lượt bệnh chờ tối đa 2,7 giờ (10,7 giờ nếu tính `max_retries`).
    Trần vòng lặp chặn số lượt, không chặn thời gian. Phải có hạn theo đồng hồ, và khi chạm hạn
    thì bỏ lượt như mọi kết thúc dở dang khác — lịch sử giữ nguyên, người dùng hỏi lại được.
    """
    monkeypatch.setattr(chat_mod, "TRAN_GIAY_MOT_LUOT", 0.0)      # hạn 0 giây: chạm ngay lượt đầu

    def handler(request):
        return httpx2.Response(200, json=_msg(
            [{"type": "tool_use", "id": "tu_z", "name": "get_price_series",
              "input": {"ticker": "HPG"}}], "tool_use"))

    llm = _llm_gia(handler)
    try:
        cu = [{"role": "user", "content": "câu trước"}, {"role": "assistant", "content": "đáp trước"}]
        tra_loi, moi = run_turn(llm, None, None, cu, "câu hỏi nặng?")
    finally:
        llm.close()
    assert moi == cu, "chạm hạn thì lịch sử phải giữ nguyên"
    assert "quá hạn" in tra_loi
    assert tool_dem["n"] <= 1, "phải dừng ngay khi chạm hạn, không chạy tiếp vòng nữa"


# --- Lệnh /moi: đường ra khỏi phiên tràn cửa sổ ngữ cảnh (review-chuan-v4 §G3) ---


def test_la_lenh_moi_nhan_dung_bien_the():
    assert chat_mod.la_lenh_moi("/moi")
    assert chat_mod.la_lenh_moi("  /MOI  ")
    assert chat_mod.la_lenh_moi("/mới")
    assert not chat_mod.la_lenh_moi("/moi gi do")
    assert not chat_mod.la_lenh_moi("moi")
    assert not chat_mod.la_lenh_moi("")


def test_repl_xoa_lich_su_khi_go_lenh_moi(monkeypatch, model_gia, tool_dem):
    """Lượt sau /moi phải gửi đi lịch sử RỖNG — nếu không thì phiên tràn vẫn tràn."""
    llm, _ = model_gia
    cau = iter(["Giá HPG?", "/moi", "Giá HPG?"])

    def gia_input(_prompt=""):
        try:
            return next(cau)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("builtins.input", gia_input)
    da_gui = []
    that = chat_mod.run_turn

    def ghi_lai(llm_, read_eng, ops_eng, history, cau_hoi):
        da_gui.append(list(history))
        return that(llm_, read_eng, ops_eng, history, cau_hoi)

    monkeypatch.setattr(chat_mod, "run_turn", ghi_lai)
    chat_mod.repl(llm, None, None)

    assert len(da_gui) == 2                    # "/moi" không được tính là một lượt hỏi
    assert da_gui[0] == []
    assert da_gui[1] == []                     # đỏ trước khi có lệnh: lượt hai mang lịch sử lượt một
