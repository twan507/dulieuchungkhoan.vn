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
