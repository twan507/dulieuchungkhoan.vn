"""Parser bảng OMO SBV — sbv-omo.md §4/§5, luật phòng thủ Giới hạn 3.

- Ngày: ưu tiên div `ls01-date` dạng "Ngày DD tháng MM năm YYYY"; nếu vắng,
  thử tiêu đề dạng cũ `KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ (dd.mm.yy)` — markup viết
  tay có thể quay lại dạng cũ (omo_page.expected.md). Không thấy dạng nào → fail.
- Bảng dò theo tiêu đề cột "Loại hình giao dịch", class ls01-* chỉ là gợi ý;
  header ≠ 4 cột → fail.
- Nhóm ngoài ba loại đã biết → fail to, không đoán (markup 'Bán kỳ hạn'/'Bán hẳn'
  chưa từng quan sát — sbv-omo.md §10).
- Đối chiếu dòng "Tổng cộng" của nhóm với tổng các dòng kỳ hạn — lệch là parse
  sai đâu đó.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup

GROUPS = {"Mua kỳ hạn": "reverse_repo", "Bán kỳ hạn": "repo", "Bán hẳn": "outright_sale"}
DATE_DIV_RE = re.compile(r"Ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})")
TITLE_DATE_RE = re.compile(r"KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ\s*\((\d{2})\.(\d{2})\.(\d{2})\)")
TENOR_RE = re.compile(r"(\d+)\s*ngày")
BILLION = Decimal(10) ** 9


class ParseError(ValueError): ...


@dataclass(frozen=True)
class OmoRow:
    op_type: str          # 'reverse_repo' | 'repo' | 'outright_sale'
    tenor_days: int
    participants: int | None
    winners: int | None
    volume_vnd: Decimal   # VND gốc (nguồn tỷ đồng × 1e9)
    rate_pct: Decimal | None


@dataclass(frozen=True)
class OmoResult:
    session_date: date
    rows: list[OmoRow]
    groups_present: frozenset[str]   # op_type có mặt


def parse_vn_number(s: str) -> Decimal:
    try:
        return Decimal(s.strip().replace(".", "").replace(",", "."))
    except InvalidOperation as e:
        raise ParseError(f"số Việt hỏng: {s!r}") from e


def _cells(tr) -> list[str]:
    return [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]


def _find_session_date(soup: BeautifulSoup) -> date:
    date_div = soup.find(class_="ls01-date")
    if date_div is not None:
        m = DATE_DIV_RE.search(date_div.get_text(" ", strip=True))
        if m:
            dd, mm, yyyy = (int(g) for g in m.groups())
            return date(yyyy, mm, dd)
    m = TITLE_DATE_RE.search(soup.get_text(" ", strip=True))
    if m:
        dd, mm, yy = (int(g) for g in m.groups())
        return date(2000 + yy, mm, dd)
    raise ParseError("không tìm thấy ngày phiên (cả div ls01-date lẫn tiêu đề dạng cũ)")


def parse(html: str) -> OmoResult:
    soup = BeautifulSoup(html, "html.parser")
    if "KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ" not in soup.get_text(" ", strip=True):
        raise ParseError("không tìm thấy tiêu đề 'KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ'")
    session_date = _find_session_date(soup)

    table = None
    for t in soup.find_all("table"):
        if "Loại hình giao dịch" in t.get_text():
            table = t
            break
    if table is None:
        raise ParseError("không tìm thấy bảng có cột 'Loại hình giao dịch'")

    rows: list[OmoRow] = []
    current: str | None = None
    group_sum: dict[str, Decimal] = {}
    group_total: dict[str, Decimal] = {}
    header_seen = False
    for tr in table.find_all("tr"):
        cells = _cells(tr)
        if not cells or not any(cells):
            continue
        text0 = cells[0]

        if "Loại hình giao dịch" in " ".join(cells):      # header
            if len(cells) != 4:
                raise ParseError(f"header {len(cells)} cột, kỳ vọng 4 — markup đổi?")
            header_seen = True
            continue

        classes = tr.get("class") or []

        if "ls01-group" in classes or text0 in GROUPS:
            if text0 not in GROUPS:
                raise ParseError(f"nhóm không nhận diện được: {text0!r}")
            current = GROUPS[text0]
            continue

        if "ls01-total" in classes or text0.lstrip("- ").startswith("Tổng"):
            if current is None:
                raise ParseError(f"dòng Tổng trước khi có nhóm: {cells!r}")
            if len(cells) >= 3 and cells[2]:
                group_total[current] = parse_vn_number(cells[2]) * BILLION
            continue

        tm = TENOR_RE.search(text0)
        if tm:
            if current is None:
                raise ParseError(f"dòng kỳ hạn trước khi có nhóm: {cells!r}")
            tenor = int(tm.group(1))
            part = win = None
            if len(cells) > 1 and "/" in cells[1]:
                p, _, w = cells[1].partition("/")
                part, win = int(p), int(w)
            vol = parse_vn_number(cells[2]) * BILLION
            rate = parse_vn_number(cells[3]) if len(cells) > 3 and cells[3] else None
            rows.append(OmoRow(current, tenor, part, win, vol, rate))
            group_sum[current] = group_sum.get(current, Decimal(0)) + vol
            continue

        # dòng không nhận diện được (không phải header/nhóm/tổng/kỳ hạn) → nghi markup lạ
        raise ParseError(f"dòng không nhận diện được trong bảng OMO: {cells!r}")

    if not header_seen:
        raise ParseError("không tìm thấy header 'Loại hình giao dịch'")
    if not rows:
        raise ParseError("không parse được dòng kỳ hạn nào")
    for g, total in group_total.items():
        if g in group_sum and group_sum[g] != total:
            raise ParseError(f"tổng nhóm {g} lệch: Σdòng={group_sum[g]} vs Tổng={total}")
    return OmoResult(session_date, rows, frozenset(group_sum))
