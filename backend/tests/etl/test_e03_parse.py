from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from etl.omo_parse import OmoRow, ParseError, parse, parse_vn_number

FIXTURE = (Path(__file__).parent / "fixtures" / "omo_page.html").read_text(encoding="utf-8")


def test_parse_vn_number():
    assert parse_vn_number("6.307,47") == Decimal("6307.47")
    assert parse_vn_number("4,5") == Decimal("4.5")
    with pytest.raises(Exception):
        parse_vn_number("abc")


def test_float_style_parse_would_be_wrong():
    # '6.307,47' đọc kiểu float() phải KHÁC kết quả đúng — bắt bẫy định dạng Việt
    assert float("6.307") != float(parse_vn_number("6.307,47"))


def test_parse_fixture_hand_solved():
    r = parse(FIXTURE)
    assert r.session_date == date(2026, 8, 25)
    assert r.groups_present == frozenset({"reverse_repo"})
    assert len(r.rows) == 4
    assert r.rows[0] == OmoRow("reverse_repo", 14, 2, 2, Decimal("5131.64") * 10**9, Decimal("4.5"))
    assert r.rows[1] == OmoRow("reverse_repo", 35, 2, 2, Decimal("3447.79") * 10**9, Decimal("4.5"))
    assert r.rows[2] == OmoRow("reverse_repo", 63, 2, 2, Decimal("3897.22") * 10**9, Decimal("4.5"))
    assert r.rows[3] == OmoRow("reverse_repo", 91, 3, 3, Decimal("4569.61") * 10**9, Decimal("4.5"))


def test_parse_rejects_unknown_group():
    bad = FIXTURE.replace("Mua kỳ hạn", "Mua đứt bán đoạn", 1)
    with pytest.raises(ParseError):
        parse(bad)


def test_parse_rejects_missing_title():
    with pytest.raises(ParseError):
        parse("<html><body><p>trang khác</p></body></html>")


def test_parse_rejects_header_wrong_column_count():
    bad = FIXTURE.replace(
        "<th>Lãi suất trúng thầu<br>(%/năm)</th>", "", 1
    )
    with pytest.raises(ParseError):
        parse(bad)


def test_parse_rejects_group_total_mismatch():
    bad = FIXTURE.replace("17.046,26", "17.000,00", 1)
    with pytest.raises(ParseError):
        parse(bad)


TWO_SESSIONS_HTML = """
<div class="ls01-date">Ngày 03 tháng 02 năm 2026</div>
<h4 class="ls01-subheading">KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ</h4>
<table class="ls01-table">
<tr><th>Loại hình giao dịch</th><th>Số thành viên tham gia/trúng thầu</th><th>Khối lượng trúng thầu</th><th>Lãi suất trúng thầu</th></tr>
<tr class="ls01-group"><td colspan="4">Mua kỳ hạn</td></tr>
<tr><td>- Kỳ hạn 7 ngày</td><td>3/3</td><td>4.747,77</td><td>4,5</td></tr>
<tr><td>- Kỳ hạn 7 ngày</td><td>13/13</td><td>35.983,63</td><td>4,5</td></tr>
<tr><td>- Kỳ hạn 28 ngày</td><td>4/4</td><td>5.398,65</td><td>4,5</td></tr>
<tr class="ls01-total"><td>Tổng cộng</td><td></td><td>46.130,05</td><td></td></tr>
</table>"""


def test_two_rows_same_tenor_are_merged_and_counted():
    r = parse(TWO_SESSIONS_HTML)
    seven = [x for x in r.rows if x.tenor_days == 7]
    assert len(seven) == 1
    assert seven[0].volume_vnd == Decimal("40731.40") * 10**9
    assert (seven[0].participants, seven[0].winners) == (16, 16)
    assert r.merged == 1
    assert len(r.rows) == 2


def test_two_rows_same_tenor_with_different_rate_is_a_parse_error():
    html = TWO_SESSIONS_HTML.replace("<td>13/13</td><td>35.983,63</td><td>4,5</td>", "<td>13/13</td><td>35.983,63</td><td>4,4</td>")
    with pytest.raises(ParseError, match="lãi suất"):
        parse(html)
