# backend/tests/agent/test_a12_tools_log.py
"""Seam — đăng ký tool và sổ lời gọi model.

Bẫy đã đo: tham số tuỳ chọn KHÔNG có giá trị mặc định sẽ rơi vào 'required' của schema, và
MiniMax bỏ hẳn khoá mảng required khi giá trị rỗng ⇒ hỏng schema. Test canh đúng chỗ đó.
ops.llm_call ràng buộc thật: status ∈ ok|repaired|failed, thinking ∈ adaptive|disabled.
"""
import sqlalchemy as sa

from agent.db import ops_engine
from agent.llm_log import log_llm_call
from agent.tools import build_tools


def test_dung_chin_tool(migrated_engine):
    tools = build_tools(migrated_engine)
    assert len(tools) == 9
    ten = {t.name for t in tools}
    assert ten == {"screen_stocks", "get_financials", "get_price_series", "get_corporate_events",
                   "compare_peers", "get_news", "get_industry_tree", "get_macro_series",
                   "load_knowledge_reference"}


def test_khong_tham_so_tuy_chon_nao_bi_required(migrated_engine):
    bat_buoc = {"get_financials": {"ticker"}, "get_price_series": {"ticker"},
                "get_corporate_events": {"ticker"}, "load_knowledge_reference": {"topic"}}
    for t in build_tools(migrated_engine):
        req = set(t.input_schema.get("required", []))
        assert req == bat_buoc.get(t.name, set()), f"{t.name} required sai: {req}"


def test_moi_tool_deu_co_mo_ta_tieng_viet(migrated_engine):
    for t in build_tools(migrated_engine):
        assert t.description and len(t.description) > 40


def test_ghi_so_duoi_role_etl_that(db):
    """§3.5: đường ghi phải chạy dưới đúng quyền production."""
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    db.execute(sa.text("""
        INSERT INTO ops.llm_call (purpose, model, thinking, status, http_calls, input_tokens,
                                  output_tokens, latency_ms)
        VALUES ('chat', 'MiniMax-M3', 'adaptive', 'ok', 1, 100, 20, 1234)"""))
    assert db.execute(sa.text("SELECT count(*) FROM ops.llm_call WHERE purpose='chat'")).scalar() == 1


def test_loi_ghi_so_khong_lam_sap_chat():
    class EngineHong:
        def connect(self):
            raise RuntimeError("DB sap")

    class Msg:
        stop_reason = "end_turn"
        usage = type("U", (), {"input_tokens": 1, "output_tokens": 1,
                               "cache_read_input_tokens": 0})()
    log_llm_call(EngineHong(), Msg(), model="MiniMax-M3", latency_ms=5)   # không được ném
