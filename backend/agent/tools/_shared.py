"""Khuôn dùng chung cho 9 function của tầng ngữ nghĩa.

BỐN hình dạng trạng thái dữ liệu, phân biệt bằng TRƯỜNG TƯỜNG MINH chứ không bằng độ dài
mảng — model không được phép nhầm "0 bản ghi" với "kho không có loại dữ liệu này". Kho có
danh tính 18 chỉ số nhưng không một điểm giá nào, nên hai ca đó khác hẳn nhau về ý nghĩa.
"""
from __future__ import annotations

import json
import re
from datetime import date

import sqlalchemy as sa

_RE_NGAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def to_json(payload: dict) -> str:
    """SDK đặt NGUYÊN giá trị trả về vào tool_result.content và không kiểm kiểu ⇒ phải là str."""
    return json.dumps(payload, ensure_ascii=False, default=str)


def kiem_ngay(gia_tri: str | None, ten_tham_so: str) -> dict | None:
    """Kiểm một tham số ngày do MODEL sinh — input không tin được (đầu file CLAUDE.md).

    Đo thật 2026-09-07: mọi hàm ghép `from_date`/`to_date` thẳng vào `CAST(:x AS date)` rồi
    giao cho Postgres soát — model sinh '2025-13-45' (đúng hình dạng, tháng không có thật) hay
    'hôm qua'/'tháng trước' (model tự ý dùng ngôn ngữ tự nhiên) đều làm Postgres ném thẳng
    `DataError`, thoát khỏi thân hàm mà không qua bất kỳ khuôn lỗi nào của tầng ngữ nghĩa.

    Trả None khi hợp lệ (bỏ trống luôn hợp lệ — nghĩa là "không lọc theo mốc này"). Trả lỗi có
    cấu trúc khi không, để model tự sửa mà không cần đọc traceback SQL.
    """
    if gia_tri is None:
        return None
    if isinstance(gia_tri, str) and _RE_NGAY.match(gia_tri):
        try:
            date.fromisoformat(gia_tri)
            return None
        except ValueError:
            pass  # đúng hình dạng nhưng không phải ngày thật, vd '2025-13-45' — rơi xuống lỗi
    return {"loi": True, "ly_do": f"{ten_tham_so} phải theo định dạng YYYY-MM-DD, nhận được: {gia_tri!r}",
            "dinh_dang_hop_le": "YYYY-MM-DD"}


def cap_limit(limit: int | None, mac_dinh: int, tran: int) -> int:
    """Trả giới hạn thật để dùng cho LIMIT.

    KHÔNG trả kèm cờ "đã cắt": hàm này chạy TRƯỚC khi truy vấn, nên không biết kết quả THẬT
    có đủ dòng để bị cắt hay không — xin 500 dòng trên một bảng chỉ có 3 dòng thì bị hạ về
    trần nhưng chẳng có gì bị cắt cả. Bên gọi tự tính cờ sau khi có kết quả thật, ví dụ
    `da_cat = len(rows) >= lim`, hoặc so với tổng đã đếm riêng (như get_news.tim_tin dùng
    tong_khop) nếu có sẵn con số đó.
    """
    if limit is None:
        return mac_dinh
    if limit > tran:
        return tran
    return max(1, limit)


def khong_tim_thay(ma: str, goi_y: list[str]) -> dict:
    return {"tim_thay": False, "ma_da_tra": ma, "goi_y": goi_y}


def khong_co_du_lieu(loai: str, ly_do: str) -> dict:
    return {"tim_thay": True, "co_du_lieu": False, "loai": loai, "ly_do": ly_do}


def rong(khoang: dict | None = None) -> dict:
    out: dict = {"tim_thay": True, "co_du_lieu": True, "so_dong": 0}
    if khoang:
        out["khoang_co_du_lieu"] = khoang
    return out


def co_du_lieu(du_lieu: list, **extra) -> dict:
    return {"tim_thay": True, "co_du_lieu": True, "so_dong": len(du_lieu), "du_lieu": du_lieu, **extra}


_SQL_TRA_MA = sa.text("""
    SELECT s.security_id, s.issuer_id, s.ticker, s.security_type, s.status, s.exchange
    FROM market.security s
    WHERE upper(s.ticker) = upper(:t)
    ORDER BY (s.status = 'listed') DESC, s.security_id
    LIMIT 1
""")

# Gợi ý khi tra trượt: khớp mờ trên chính ticker và trên tên doanh nghiệp.
# KHÔNG dùng news.trade_name — bảng đó rỗng (0 dòng, đo 2026-09-07); khi nào có dữ liệu thì
# thêm một nhánh UNION vào đây, hình dạng kết quả không đổi.
_SQL_GOI_Y = sa.text("""
    SELECT s.ticker
    FROM market.security s
    LEFT JOIN market.issuer i USING (issuer_id)
    WHERE s.status = 'listed'
      AND (extensions.similarity(upper(s.ticker), upper(:t)) > 0.3
           OR extensions.similarity(coalesce(i.short_name, ''), :t) > 0.3)
    ORDER BY extensions.similarity(upper(s.ticker), upper(:t)) DESC
    LIMIT 5
""")


def resolve_ticker(conn: sa.Connection, ticker: str) -> dict:
    """Tra mã về danh tính thật. Mã huỷ niêm yết vẫn trả về, kèm trang_thai để bên gọi quyết."""
    row = conn.execute(_SQL_TRA_MA, {"t": ticker}).first()
    if row is None:
        goi_y = [r[0] for r in conn.execute(_SQL_GOI_Y, {"t": ticker})]
        return khong_tim_thay(ticker, goi_y)
    return {"tim_thay": True, "security_id": row.security_id, "issuer_id": row.issuer_id,
            "ticker": row.ticker, "loai": row.security_type, "trang_thai": row.status,
            "san": row.exchange}


# industry_code là từ vựng ĐÓNG dùng chung ở get_news/screen_stocks/compare_peers (mỗi hàm lọc
# theo mã ngành, không tra riêng một mã như resolve_ticker) — một chủ (CLAUDE.md §1.7), tránh
# chép lại câu SQL này ba lần rồi lệch nhau. get_industry_tree KHÔNG dùng hàm này: nó tra industry_code
# như một ĐỐI TƯỢNG chính (không phải bộ lọc phụ) nên đã có nhánh gợi ý riêng bằng similarity (F5).
_SQL_NGANH_HOP_LE = sa.text("SELECT code FROM market.industry WHERE level = 2 ORDER BY code")


def kiem_industry_code(conn: sa.Connection, ma: str | None) -> dict | None:
    """Kiểm industry_code khi dùng làm BỘ LỌC PHỤ — 24 mã ngành cấp 2 (đo 2026-09-07).

    Trả None khi bỏ trống hoặc khớp đúng một trong 24 mã. Trả lỗi có cấu trúc khi không, kèm
    TOÀN BỘ danh sách hợp lệ — không được để lọt xuống dưới rồi lặng lẽ ra 0 dòng: 0 dòng vì
    "mã ngành không tồn tại" và 0 dòng vì "mã ngành có thật nhưng không khớp gì trong khoảng
    hỏi" là hai lý do khác hẳn nhau (đúng bẫy đổ lỗi sai nguyên nhân CLAUDE.md §3.6 nhắc tới).
    """
    if ma is None:
        return None
    hop_le = [r[0] for r in conn.execute(_SQL_NGANH_HOP_LE)]
    if ma not in hop_le:
        return {"loi": True, "ly_do": f"khong co ma nganh '{ma}'", "industry_code_hop_le": hop_le}
    return None
