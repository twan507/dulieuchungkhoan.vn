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


def fetch_base_state(client: httpx.Client | None = None) -> dict[str, dict[str, str]]:
    own = client is None
    client = client or httpx.Client(base_url=BASE)
    try:
        rows = _instruments(client)
        return {r["symbol"]: {k: str(r[k]) for k in _BASE_FIELDS if r.get(k) not in (None, "")}
                for r in rows}
    finally:
        if own:
            client.close()


def fetch_derivative_symbols(client: httpx.Client | None = None) -> list[str]:
    """Mã phái sinh (FloorCode == '03') — CHỈ dùng cho chế độ đo (spec §3.5)."""
    own = client is None
    client = client or httpx.Client(base_url=BASE)
    try:
        return sorted(r["symbol"] for r in _instruments(client) if r.get("FloorCode") == "03")
    finally:
        if own:
            client.close()


def build_catalog(client: httpx.Client | None = None) -> Catalog:
    own = client is None
    client = client or httpx.Client(base_url=BASE)
    try:
        quotes = _get(client, "/quotes", symbols="ALL")
        inst = fetch_base_state(client)
        symbols, base_state = [], {}
        for q in quotes:
            if q.get("StockType") not in ("2", "3"):
                continue
            sym = q["symbol"]
            symbols.append(sym)
            base_state[sym] = inst.get(sym) or {
                k: str(q[k]) for k in ("ceiling", "floor", "reference") if q.get(k) is not None
            }
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
