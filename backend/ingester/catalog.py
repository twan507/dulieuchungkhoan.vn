"""Danh mục runtime — hợp nhất /quotes + /datafeed/instruments (spec CH #8/#9).

- Phân loại CHỈ bằng StockType của /quotes (bẫy 10 — bảng mã theo endpoint).
- Không endpoint nào một mình đủ (bẫy 11) — hợp nhất, khử trùng theo symbol.
- Không đọc Postgres. Reconnect chỉ gọi lại fetch_base_state, không đổi danh mục.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

BASE = "https://online.bvsc.com.vn"
INDEX_CODES = ["HOSE", "30", "100", "MID", "SML", "XALL", "X50", "SI", "ALL",
               "DIAMOND", "FINLEAD", "FINSELECT", "HNX", "HNX30", "UPCOM"]
FLOORS = ["HOSE", "HNX", "UPCOM"]
_BASE_FIELDS = ("open", "low", "ceiling", "floor", "reference")


@dataclass(frozen=True)
class Catalog:
    symbols: list[str]
    base_state: dict[str, dict[str, str]]


def _get(client: httpx.Client, path: str, **params) -> list[dict]:
    r = client.get(path, params=params or None, timeout=30.0)
    r.raise_for_status()
    body = r.json()
    d = body.get("d")
    if body.get("s") != "ok" or not isinstance(d, list) or not d:
        raise RuntimeError(f"BVSC {path}: response bất thường (s={body.get('s')!r}, n={len(d or [])})")
    return d


def _instruments(client: httpx.Client) -> list[dict]:
    return _get(client, "/datafeed/instruments")


def _base_of(r: dict) -> dict[str, str]:
    return {k: str(r[k]) for k in _BASE_FIELDS if r.get(k) not in (None, "")}


def fetch_base_state(client: httpx.Client | None = None) -> dict[str, dict[str, str]]:
    own = client is None
    client = client or httpx.Client(base_url=BASE)
    try:
        return {r["symbol"]: _base_of(r) for r in _instruments(client)}
    finally:
        if own:
            client.close()


def _is_live_derivative(r: dict) -> bool:
    """Hợp đồng phái sinh CÒN HIỆU LỰC.

    Đo 2026-08-26: `/datafeed/instruments` trả **61** bản ghi `FloorCode='03'` nhưng chỉ
    **14 còn sống**; 47 hợp đồng đã đáo hạn vẫn nằm nguyên trong response, mất
    `tradingdate`/`Status`/`MaturityDate`, chỉ còn giá tham chiếu cũ (ví dụ `VN30F2509`
    = "HDTL VN30 9/2025"). Nhận bừa cả 61 là đăng ký thừa 47×20 topic và nạp danh mục rác.
    """
    return bool(r.get("tradingdate")) and bool(r.get("Status"))


def fetch_derivative_symbols(client: httpx.Client | None = None) -> list[str]:
    """Mã phái sinh CÒN SỐNG (FloorCode == '03' + còn hiệu lực)."""
    own = client is None
    client = client or httpx.Client(base_url=BASE)
    try:
        return sorted(r["symbol"] for r in _instruments(client)
                      if r.get("FloorCode") == "03" and _is_live_derivative(r))
    finally:
        if own:
            client.close()


def build_catalog(client: httpx.Client | None = None) -> Catalog:
    own = client is None
    client = client or httpx.Client(base_url=BASE)
    try:
        quotes = _get(client, "/quotes", symbols="ALL")
        instruments = _instruments(client)
        inst = {r["symbol"]: _base_of(r) for r in instruments}
        symbols, base_state = [], {}
        for q in quotes:
            if q.get("StockType") not in ("2", "3"):
                continue
            sym = q["symbol"]
            symbols.append(sym)
            base_state[sym] = inst.get(sym) or {
                k: str(q[k]) for k in ("ceiling", "floor", "reference") if q.get(k) is not None
            }
        # Phái sinh CÒN SỐNG: không có trong `/quotes` nên phải lấy từ instruments. Tick
        # của chúng đi chung ba topic `i`/`o10`/`t` với cổ phiếu, cấu trúc trường giống
        # hệt (đo 2026-08-26, 2,3 triệu frame) — không đăng ký thì không ghi được.
        for r in instruments:
            if r.get("FloorCode") == "03" and _is_live_derivative(r):
                symbols.append(r["symbol"])
                base_state[r["symbol"]] = inst[r["symbol"]]
        return Catalog(sorted(set(symbols)), base_state)
    finally:
        if own:
            client.close()


def topics(cat: Catalog) -> list[str]:
    out = []
    for s in cat.symbols:
        out += [f"i:{s}", f"o10:{s}", f"t:{s}"]  # o10 — bẫy 11-bvsc-realtime §3
    out += [f"idx:{c}" for c in INDEX_CODES]
    out += [f"ptm:{f}" for f in FLOORS]
    return out
