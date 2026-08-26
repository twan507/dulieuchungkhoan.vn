"""Chuẩn hoá frame BVSC → dòng ClickHouse rt.* + delta Redis — spec §3.3.

MỘT từ điển ánh xạ dùng chung cho cả hai đường ghi (quyết định #9 spec lát cắt).
Nguồn sự thật tên cột: DDL spec ClickHouse §3. Frame hỏng tất định → NormalizeError
(đường block độc §5.8 — log + metric, không ghi sai).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Ho_Chi_Minh")

COLUMNS = {
    "trade": ["symbol", "ts", "seq", "price", "volume", "side", "change",
              "cum_volume", "cum_value", "received_at"],
    "quote": ["symbol", "ts", "top", "action", "bid_price", "bid_qty", "ask_price",
              "ask_qty", "cum_bid", "cum_ask", "received_at"],
    "snapshot_delta": ["symbol", "exchange", "ts",
                       "b1", "b2", "b3", "v1", "v2", "v3", "s1", "s2", "s3",
                       "u1", "u2", "u3", "total_bid", "total_offer",
                       "close_price", "change", "change_pct", "avg_price", "high",
                       "last_vol", "last_vol2", "last_price", "total_vol", "total_value",
                       "foreign_buy", "foreign_sell", "foreign_remain",
                       "pt_price", "pt_qty", "pt_total_qty", "pt_total_val",
                       "extra", "received_at"],
    "index_delta": ["symbol", "ts", "index_value", "change", "change_pct",
                    "total_vol", "total_value", "advances", "declines", "unchanged",
                    "ceiling_cnt", "adv_vol", "dec_vol", "unch_vol",
                    "pt_total", "pt_value", "extra", "received_at"],
    "pt_match": ["symbol", "market", "ts", "price", "volume", "ref_price",
                 "ceil_price", "floor_price", "order_id", "extra", "received_at"],
}


class NormalizeError(ValueError): ...


@dataclass
class Metrics:
    counters: dict[str, int] = field(default_factory=dict)

    def inc(self, key: str, n: int = 1) -> None:
        self.counters[key] = self.counters.get(key, 0) + n


@dataclass(frozen=True)
class Normalized:
    table: str
    row: dict
    delta: dict
    symbol: str


def _dec2(v, metrics: Metrics) -> Decimal:
    try:
        d = Decimal(str(v))
    except InvalidOperation as e:
        raise NormalizeError(f"không phải số: {v!r}") from e
    q = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    if q != d:
        metrics.inc("decimal_normalized")
    return q


def _uint(v):
    try:
        d = Decimal(str(v))
    except InvalidOperation as e:
        raise NormalizeError(f"không phải số: {v!r}") from e
    i = int(d)
    if i != d or i < 0:
        raise NormalizeError(f"không phải số nguyên không âm: {v!r}")
    return i


def _ts_ms(v) -> datetime:
    return datetime.fromtimestamp(_uint(v) / 1000, tz=TZ)


def symbol_of(event: str, payload: dict):
    return payload.get("MC" if event == "idx" else "SB")


def _received_at(received_at_ms: int) -> datetime:
    return datetime.fromtimestamp(received_at_ms / 1000, tz=TZ)


def _delta_of(table: str, row: dict, ts_ms: int) -> dict:
    """Cột→str của các cột frame vừa mang (khác None), bỏ extra/received_at,
    thêm ts = epoch ms dạng chuỗi."""
    delta = {
        k: str(row[k])
        for k in COLUMNS[table]
        if k not in ("extra", "received_at", "ts") and row.get(k) is not None
    }
    delta["ts"] = str(ts_ms)
    return delta


def _count_unknown(event: str, payload: dict, known: set[str], metrics: Metrics) -> None:
    for k in payload:
        if k not in known:
            metrics.inc(f"unknown_key.{event}.{k}")


def _normalize_t(payload: dict, received_at_ms: int, metrics: Metrics) -> Normalized:
    known = {"TD", "FT", "SB", "FV", "LC", "FMP", "FCV", "SM", "AVO", "AVA"}
    _count_unknown("t", payload, known, metrics)

    try:
        symbol = payload["SB"]
        ts = datetime.strptime(f"{payload['TD']} {payload['FT']}", "%d/%m/%Y %H:%M:%S")
        ts = ts.replace(tzinfo=TZ)
    except (KeyError, ValueError) as e:
        raise NormalizeError(f"frame t hỏng: {e}") from e

    row = {
        "symbol": symbol,
        "ts": ts,
        "seq": _uint(payload["SM"]),
        "price": _dec2(payload["FMP"], metrics),
        "volume": _uint(payload["FV"]),
        # DDL §3.1: side không Nullable — LC thiếu mặc định "" (LowCardinality(String) chấp nhận,
        # nến chỉ cộng v_bu/v_sd khi side=='B'/'S' nên "" vô hại).
        "side": payload.get("LC", ""),
        # DDL §3.1: change/cum_volume/cum_value không Nullable — thiếu frame mặc định 0.
        "change": _dec2(payload["FCV"], metrics) if "FCV" in payload else Decimal("0.00"),
        "cum_volume": _uint(payload["AVO"]) if "AVO" in payload else 0,
        "cum_value": _dec2(payload["AVA"], metrics) if "AVA" in payload else Decimal("0.00"),
        "received_at": _received_at(received_at_ms),
    }
    delta = _delta_of("trade", row, int(ts.timestamp() * 1000))
    return Normalized(table="trade", row=row, delta=delta, symbol=symbol)


def _normalize_o(payload: dict, received_at_ms: int, metrics: Metrics) -> Normalized:
    known = {"SB", "t", "TOP", "ACT", "BP", "BQ", "SP", "SQ", "CBV", "CSV", "id"}
    _count_unknown("o", payload, known, metrics)

    try:
        symbol = payload["SB"]
        ts = _ts_ms(payload["t"])
        # DDL §3.2: top không Nullable — TOP thiếu hoặc không phải bậc 1..3 là frame hỏng tất định.
        top = _uint(payload["TOP"])
        if top not in (1, 2, 3):
            raise NormalizeError(f"TOP ngoài phạm vi 1..3: {top!r}")
    except KeyError as e:
        raise NormalizeError(f"frame o hỏng: {e}") from e

    row = {
        "symbol": symbol,
        "ts": ts,
        "top": top,
        # DDL §3.2: action/bid_*/ask_*/cum_* không Nullable — thiếu frame mặc định "" / 0.
        "action": payload.get("ACT", ""),
        "bid_price": _dec2(payload["BP"], metrics) if "BP" in payload else Decimal("0.00"),
        "bid_qty": _uint(payload["BQ"]) if "BQ" in payload else 0,
        "ask_price": _dec2(payload["SP"], metrics) if "SP" in payload else Decimal("0.00"),
        "ask_qty": _uint(payload["SQ"]) if "SQ" in payload else 0,
        "cum_bid": _uint(payload["CBV"]) if "CBV" in payload else 0,
        "cum_ask": _uint(payload["CSV"]) if "CSV" in payload else 0,
        "received_at": _received_at(received_at_ms),
    }
    delta = _delta_of("quote", row, int(ts.timestamp() * 1000))
    return Normalized(table="quote", row=row, delta=delta, symbol=symbol)


# snapshot_delta ("i"): cột Decimal vs cột UInt, còn lại unmapped -> extra.
# DDL §3.3: b1..b3/s1..s3 là Nullable(Decimal64(2)) (giá, VND) — v1..v3/u1..u3 mới là UInt.
_I_DEC_FIELDS = {
    "B1": "b1", "B2": "b2", "B3": "b3", "S1": "s1", "S2": "s2", "S3": "s3",
    "CP": "close_price", "CH": "change", "CHP": "change_pct", "AP": "avg_price",
    "HI": "high", "P2": "last_price", "TV": "total_value",
    "PMP": "pt_price", "PTV": "pt_total_val",
}
_I_UINT_FIELDS = {
    "V1": "v1", "V2": "v2", "V3": "v3", "U1": "u1", "U2": "u2", "U3": "u3",
    "TB": "total_bid", "TO": "total_offer",
    "CV": "last_vol", "P1": "last_vol2", "TT": "total_vol",
    "FB": "foreign_buy", "FS": "foreign_sell", "FR": "foreign_remain",
    "PMQ": "pt_qty", "PTQ": "pt_total_qty",
}
_I_KNOWN_TOP = {"SB", "EX", "t"}


def _normalize_i(payload: dict, received_at_ms: int, metrics: Metrics) -> Normalized:
    try:
        symbol = payload["SB"]
        exchange = payload.get("EX")
        ts = _ts_ms(payload["t"])
    except KeyError as e:
        raise NormalizeError(f"frame i hỏng: {e}") from e

    row: dict = {"symbol": symbol, "exchange": exchange, "ts": ts}
    for src, col in _I_DEC_FIELDS.items():
        row[col] = _dec2(payload[src], metrics) if src in payload else None
    for src, col in _I_UINT_FIELDS.items():
        row[col] = _uint(payload[src]) if src in payload else None

    if "CV" in payload and "P1" in payload and row["last_vol"] != row["last_vol2"]:
        metrics.inc("cv_ne_p1")

    known = _I_KNOWN_TOP | set(_I_DEC_FIELDS) | set(_I_UINT_FIELDS)
    extra = {k: v for k, v in payload.items() if k not in known}
    row["extra"] = json.dumps(extra, ensure_ascii=False, sort_keys=True) if extra else ""
    row["received_at"] = _received_at(received_at_ms)

    delta = _delta_of("snapshot_delta", row, int(ts.timestamp() * 1000))
    return Normalized(table="snapshot_delta", row=row, delta=delta, symbol=symbol)


# index_delta ("idx"): IT/TD bỏ có chủ đích (không vào extra); còn lại lạ -> extra.
# DDL §3.4: pt_value là Nullable(Decimal64(2)) — pt_total (PTT) vẫn UInt.
_IDX_DEC_FIELDS = {
    "MI": "index_value", "ICH": "change", "IPC": "change_pct", "TVA": "total_value",
    "PTV": "pt_value",
}
_IDX_UINT_FIELDS = {
    "TV": "total_vol", "ADV": "advances", "DE": "declines", "NC": "unchanged",
    "NOC": "ceiling_cnt", "AV": "adv_vol", "DV": "dec_vol", "NCV": "unch_vol",
    "PTT": "pt_total",
}
_IDX_KNOWN_TOP = {"MC", "t"}
_IDX_DROPPED = {"IT", "TD"}


def _normalize_idx(payload: dict, received_at_ms: int, metrics: Metrics) -> Normalized:
    try:
        symbol = payload["MC"]
        ts = _ts_ms(payload["t"])
    except KeyError as e:
        raise NormalizeError(f"frame idx hỏng: {e}") from e

    row: dict = {"symbol": symbol, "ts": ts}
    for src, col in _IDX_DEC_FIELDS.items():
        row[col] = _dec2(payload[src], metrics) if src in payload else None
    for src, col in _IDX_UINT_FIELDS.items():
        row[col] = _uint(payload[src]) if src in payload else None

    known = _IDX_KNOWN_TOP | set(_IDX_DEC_FIELDS) | set(_IDX_UINT_FIELDS) | _IDX_DROPPED
    extra = {k: v for k, v in payload.items() if k not in known}
    row["extra"] = json.dumps(extra, ensure_ascii=False, sort_keys=True) if extra else ""
    row["received_at"] = _received_at(received_at_ms)

    delta = _delta_of("index_delta", row, int(ts.timestamp() * 1000))
    return Normalized(table="index_delta", row=row, delta=delta, symbol=symbol)


# pt_match ("ptm"): LS là epoch GIÂY; MKI/IAC luôn vào extra (có chủ đích); TD/TI bỏ.
_PTM_KNOWN_TOP = {"SB", "MC", "LS"}
_PTM_DROPPED = {"TD", "TI"}
_PTM_ALWAYS_EXTRA = {"MKI", "IAC"}


def _normalize_ptm(payload: dict, received_at_ms: int, metrics: Metrics) -> Normalized:
    try:
        symbol = payload["SB"]
        market = payload.get("MC")
        ts = datetime.fromtimestamp(_uint(payload["LS"]), tz=TZ)
    except KeyError as e:
        raise NormalizeError(f"frame ptm hỏng: {e}") from e

    row = {
        "symbol": symbol,
        "market": market,
        "ts": ts,
        "price": _dec2(payload["PR"], metrics) if "PR" in payload else None,
        "volume": _uint(payload["MVL"]) if "MVL" in payload else None,
        "ref_price": _dec2(payload["RE"], metrics) if "RE" in payload else None,
        "ceil_price": _dec2(payload["CE"], metrics) if "CE" in payload else None,
        "floor_price": _dec2(payload["FL"], metrics) if "FL" in payload else None,
        "order_id": payload.get("CNO"),
    }

    known = _PTM_KNOWN_TOP | {"PR", "MVL", "RE", "CE", "FL", "CNO"} | _PTM_DROPPED | _PTM_ALWAYS_EXTRA
    extra = {k: v for k, v in payload.items() if k in _PTM_ALWAYS_EXTRA or k not in known}
    row["extra"] = json.dumps(extra, ensure_ascii=False, sort_keys=True) if extra else ""
    row["received_at"] = _received_at(received_at_ms)

    delta = _delta_of("pt_match", row, int(ts.timestamp() * 1000))
    return Normalized(table="pt_match", row=row, delta=delta, symbol=symbol)


# --- mỗi topic một hàm normalize_<topic>, dispatch qua: ---
_NORMALIZERS = {"t": _normalize_t, "o": _normalize_o, "i": _normalize_i,
                "idx": _normalize_idx, "ptm": _normalize_ptm}


def normalize(event, payload, received_at_ms, metrics):
    fn = _NORMALIZERS.get(event)
    if fn is None:
        raise NormalizeError(f"event không hỗ trợ: {event}")
    return fn(payload, received_at_ms, metrics)
