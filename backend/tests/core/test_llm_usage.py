"""Usage: cộng dồn và quy giá pay-go MiniMax (minimax.md §3, tài liệu 2026-09-06) — literal tính tay, không tính lại theo code."""
from types import SimpleNamespace

from core.llm import Usage


def test_estimate_usd_literal_from_brainstorm():
    # 1.850 vào mới × $0,30/M + 1.300 đọc cache × $0,06/M + 1.000 ra × $1,20/M = 0,000555 + 0,000078 + 0,0012
    u = Usage(input_tokens=1850, cache_read_tokens=1300, output_tokens=1000)
    assert round(u.estimate_usd(), 5) == 0.00183
    assert Usage().estimate_usd() == 0.0


def test_add_sums_every_field():
    a = Usage(100, 50, 10, 5, 1, 1.5)
    b = Usage(200, 0, 20, 0, 1, 2.5)
    c = a + b
    assert (c.input_tokens, c.cache_read_tokens, c.output_tokens, c.thinking_tokens, c.calls, c.latency_s) == (300, 50, 30, 5, 2, 4.0)
    assert a == Usage(100, 50, 10, 5, 1, 1.5)                    # không đổi toán hạng


def test_from_sdk_reads_cache_and_thinking_and_tolerates_none():
    sdk = SimpleNamespace(input_tokens=214, cache_read_input_tokens=2816, output_tokens=250,
                          output_tokens_details=SimpleNamespace(thinking_tokens=120))
    u = Usage.from_sdk(sdk, 3.2)
    assert (u.input_tokens, u.cache_read_tokens, u.output_tokens, u.thinking_tokens, u.calls, u.latency_s) == (214, 2816, 250, 120, 1, 3.2)
    bare = SimpleNamespace(input_tokens=3030, cache_read_input_tokens=None, output_tokens=7)     # lượt 1: chưa cache, không details
    u2 = Usage.from_sdk(bare, 1.0)
    assert (u2.cache_read_tokens, u2.thinking_tokens) == (0, 0)
