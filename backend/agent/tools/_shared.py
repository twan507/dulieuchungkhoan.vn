"""Khuôn dùng chung cho 9 function của tầng ngữ nghĩa.

BỐN hình dạng trạng thái dữ liệu, phân biệt bằng TRƯỜNG TƯỜNG MINH chứ không bằng độ dài
mảng — model không được phép nhầm "0 bản ghi" với "kho không có loại dữ liệu này". Kho có
danh tính 18 chỉ số nhưng không một điểm giá nào, nên hai ca đó khác hẳn nhau về ý nghĩa.
"""
from __future__ import annotations

import json

import sqlalchemy as sa


def to_json(payload: dict) -> str:
    """SDK đặt NGUYÊN giá trị trả về vào tool_result.content và không kiểm kiểu ⇒ phải là str."""
    return json.dumps(payload, ensure_ascii=False, default=str)


def cap_limit(limit: int | None, mac_dinh: int, tran: int) -> tuple[int, bool]:
    """Trả (giới hạn thật, có bị cắt không)."""
    if limit is None:
        return mac_dinh, False
    if limit > tran:
        return tran, True
    return max(1, limit), False


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
