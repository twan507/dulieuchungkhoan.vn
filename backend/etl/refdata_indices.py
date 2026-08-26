"""Hằng số 18 chỉ số thị trường — chép nguyên văn spec 2026-08-26 §3.1.

Vì sao là hằng số trong ETL chứ không phải migration seed: `market.security`
có đường ghi runtime (chính ETL này) — seed vào đó tạo hai người ghi một bảng.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class IndexDef:
    snap_code: str      # mã trong indexsnaps
    ticker: str          # ticker chuẩn nội bộ (spec §3.1)
    name: str
    exchange: str        # 'HOSE' | 'HNX' | 'UPCOM'
    tvc_code: str | None  # CHỈ 3 mã đã đo; còn lại None


INDICES: tuple[IndexDef, ...] = (
    IndexDef("HOSE", "VNINDEX", "VN-Index", "HOSE", "VNINDEX"),
    IndexDef("30", "VN30", "VN30", "HOSE", "VN30"),
    IndexDef("100", "VN100", "VN100", "HOSE", None),
    IndexDef("MID", "VNMID", "VNMidcap", "HOSE", None),
    IndexDef("SML", "VNSML", "VNSmallcap", "HOSE", None),
    IndexDef("XALL", "VNXALL", "VNX AllShare", "HOSE", None),
    IndexDef("X50", "VNX50", "VNX50", "HOSE", None),
    IndexDef("SI", "VNSI", "VN Sustainability", "HOSE", None),
    IndexDef("ALL", "VNALL", "VNAllShare", "HOSE", None),
    IndexDef("DIAMOND", "VNDIAMOND", "VN Diamond", "HOSE", None),
    IndexDef("FINLEAD", "VNFINLEAD", "VN Financial Lead", "HOSE", None),
    IndexDef("FINSELECT", "VNFINSELECT", "VN Financial Select", "HOSE", None),
    IndexDef("HNX", "HNXINDEX", "HNX-Index", "HNX", "HNXIndex"),
    IndexDef("HNX30", "HNX30", "HNX30", "HNX", None),
    IndexDef("HNXFin", "HNXFIN", "HNX Finance", "HNX", None),
    IndexDef("HNXMSCap", "HNXMSCAP", "HNX Mid/Small Cap", "HNX", None),
    IndexDef("HNXMan", "HNXMAN", "HNX Manufacturing", "HNX", None),
    IndexDef("UPCOM", "UPINDEX", "UPCOM-Index", "UPCOM", None),
)

SNAP_CODES: frozenset[str] = frozenset(d.snap_code for d in INDICES)
