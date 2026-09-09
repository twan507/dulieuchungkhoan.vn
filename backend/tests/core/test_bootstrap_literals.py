"""`_ch_literal` — hàm escape DUY NHẤT đứng giữa mật khẩu do người dùng đặt và câu SQL ghép chuỗi
của `provision_clickhouse` (bootstrap.py). Luật escape ClickHouse: backslash trước, rồi nháy đơn.

Test thuần, không cần DB — expected viết tay theo luật escape (CLAUDE.md §4.5.3), không tính lại
theo đúng cách hàm tính. Để dành T8b (review toàn nhánh lát 12, Chuẩn): review đã soi tay xác nhận
cài đặt hiện tại đúng; test này là chốt hồi quy cho hàm đó, không phải một phát hiện lỗi mới.
"""
from core.bootstrap import _ch_literal


def test_no_special_chars_is_just_quoted():
    assert _ch_literal("abc") == "'abc'"


def test_single_quote_is_escaped_with_a_leading_backslash():
    assert _ch_literal("it's") == "'it\\'s'"


def test_backslash_is_doubled():
    assert _ch_literal("a\\b") == "'a\\\\b'"


def test_quote_and_backslash_together_escape_backslash_first_then_quote():
    """`x'\\y` (nháy đơn rồi backslash) ⇒ `'x\\'\\\\y'` — thứ tự escape đúng luật: nhân đôi backslash
    TRƯỚC, rồi mới chèn backslash trước nháy đơn (đảo thứ tự sẽ escape luôn backslash vừa chèn)."""
    assert _ch_literal("x'\\y") == "'x\\'\\\\y'"
