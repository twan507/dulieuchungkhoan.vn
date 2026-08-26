"""Packet Engine.IO v3 + envelope sails.io — 11-bvsc-realtime.md §1.

Ack statusCode:200 KHÔNG chứng minh topic hợp lệ (§1.4) — caller không dùng ack
làm bằng chứng; bằng chứng duy nhất là frame dữ liệu về.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

WSS_URL = ("wss://wss.bvsc.com.vn/market/socket.io/?EIO=3&transport=websocket"
           "&__sails_io_sdk_version=1.2.1&__sails_io_sdk_platform=browser"
           "&__sails_io_sdk_language=javascript")
PING = "2"


@dataclass(frozen=True)
class Open:
    ping_interval_ms: int
    ping_timeout_ms: int


@dataclass(frozen=True)
class Event:
    name: str
    payload: dict


@dataclass(frozen=True)
class Ack:
    ack_id: int
    body: list


@dataclass(frozen=True)
class Control:
    kind: str


def _split_id(rest: str) -> tuple[int | None, str]:
    i = 0
    while i < len(rest) and rest[i].isdigit():
        i += 1
    return (int(rest[:i]) if i else None, rest[i:])


def parse_packet(raw: str):
    try:
        if raw.startswith("0"):
            d = json.loads(raw[1:])
            return Open(int(d["pingInterval"]), int(d["pingTimeout"]))
        if raw in ("1", "2", "3", "6", "40", "41"):
            return Control(raw)
        if raw.startswith("42"):
            _, rest = _split_id(raw[2:])
            arr = json.loads(rest)
            if isinstance(arr, list) and arr and isinstance(arr[0], str):
                payload = arr[1] if len(arr) > 1 and isinstance(arr[1], dict) else {}
                return Event(arr[0], payload)
            return None
        if raw.startswith("43"):
            ack_id, rest = _split_id(raw[2:])
            return Ack(ack_id or 0, json.loads(rest))
    except (ValueError, KeyError, TypeError):
        return None
    return None


def build_subscribe(ack_id: int, args: list[str], op: str = "subscribe") -> str:
    body = ["get", {"url": "/client/subscribe", "method": "get", "headers": {},
                    "data": {"op": op, "args": args}}]
    return f"42{ack_id}" + json.dumps(body, separators=(",", ":"))


def chunk(seq, n: int = 100):
    for i in range(0, len(seq), n):
        yield list(seq[i:i + n])
