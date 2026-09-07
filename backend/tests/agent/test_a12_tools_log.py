# backend/tests/agent/test_a12_tools_log.py
"""Seam — đăng ký tool và sổ lời gọi model.

Bẫy đã đo: tham số tuỳ chọn KHÔNG có giá trị mặc định sẽ rơi vào 'required' của schema, và
MiniMax bỏ hẳn khoá mảng required khi giá trị rỗng ⇒ hỏng schema. Test canh đúng chỗ đó.
ops.llm_call ràng buộc thật: status ∈ ok|repaired|failed, thinking ∈ adaptive|disabled.
"""
import sqlalchemy as sa

from agent.llm_log import log_llm_call
from agent.skills import L2_TOPICS
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


def test_topic_la_enum_dong_du_9_gia_tri(migrated_engine):
    """spec §4.4 #9 / §6 S5: topic phải bị từ chối Ở TẦNG SCHEMA (Literal đóng), không chỉ ở
    thân doc_tri_thuc — trước sửa, schema sinh ra chỉ có {"type": "string"}, không có "enum"."""
    for t in build_tools(migrated_engine):
        if t.name == "load_knowledge_reference":
            enum = t.input_schema["properties"]["topic"]["enum"]
            assert set(enum) == set(L2_TOPICS)
            assert len(enum) == 9
            break
    else:
        raise AssertionError("khong thay tool load_knowledge_reference")


class _KetNoiKhongDong:
    """Bọc connection thật của fixture `db`: execute() đi thẳng vào nó (SET LOCAL ROLE và các
    INSERT sau đó cùng một transaction), commit() là NO-OP và __exit__ không đóng connection —
    để transaction của fixture `db` còn sống, rollback ở cuối test dọn sạch như mọi test khác.
    Không cần commit thật: SELECT ngay sau đó đọc được dòng vừa ghi trong CÙNG transaction."""
    def __init__(self, conn):
        self._conn = conn

    def execute(self, *a, **kw):
        return self._conn.execute(*a, **kw)

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _EngineGia:
    def __init__(self, conn):
        self._conn = conn

    def connect(self):
        return _KetNoiKhongDong(self._conn)


def _msg_gia(stop_reason: str):
    return type("Msg", (), {
        "stop_reason": stop_reason,
        "usage": type("U", (), {"input_tokens": 1, "output_tokens": 1,
                                "cache_read_input_tokens": 0})(),
    })()


def test_ghi_so_duoi_role_etl_that(db):
    """§3.5: đường ghi phải chạy dưới đúng quyền production, và phải gọi CHÍNH log_llm_call —
    bản cũ chạy một câu INSERT viết tay, chứng minh role ghi được bảng chứ không chứng minh
    seam llm_log.log_llm_call ghi đúng. Vì thế lỗi ánh xạ trạng thái (mọi lượt tool_use từng bị
    ghi thành 'failed', đo 2026-09-07) chỉ lộ ra khi chạy thật, không có test nào canh (§2.3)."""
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    eng = _EngineGia(db)

    log_llm_call(eng, _msg_gia("end_turn"), model="MiniMax-M3", latency_ms=1234)
    row = db.execute(sa.text(
        "SELECT status, error FROM ops.llm_call ORDER BY call_id DESC LIMIT 1")).one()
    assert row.status == "ok"
    assert row.error is None

    # G2: một lượt tool_use là bước BÌNH THƯỜNG giữa chừng của vòng chat nhiều lượt, không phải
    # hỏng — KHÔNG được ghi 'failed'.
    log_llm_call(eng, _msg_gia("tool_use"), model="MiniMax-M3", latency_ms=1234)
    row = db.execute(sa.text(
        "SELECT status, error FROM ops.llm_call ORDER BY call_id DESC LIMIT 1")).one()
    assert row.status == "ok"
    assert row.error is None

    log_llm_call(eng, _msg_gia("max_tokens"), model="MiniMax-M3", latency_ms=1234)
    row = db.execute(sa.text(
        "SELECT status, error FROM ops.llm_call ORDER BY call_id DESC LIMIT 1")).one()
    assert row.status == "failed"
    assert "max_tokens" in row.error


def test_loi_ghi_so_khong_lam_sap_chat():
    class EngineHong:
        def connect(self):
            raise RuntimeError("DB sap")

    class Msg:
        stop_reason = "end_turn"
        usage = type("U", (), {"input_tokens": 1, "output_tokens": 1,
                               "cache_read_input_tokens": 0})()
    log_llm_call(EngineHong(), Msg(), model="MiniMax-M3", latency_ms=5)   # không được ném
