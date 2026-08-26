"""Hot path Redis — HASH state + PUBLISH delta (spec §3.4). Chỉ leader gọi apply."""
from __future__ import annotations

import json

from ingester.normalize import Normalized

_TTL_S = 86400
_EVENT_OF_TABLE = {"snapshot_delta": "i", "trade": "t", "quote": "o",
                   "index_delta": "idx", "pt_match": "ptm"}


class RedisSink:
    def __init__(self, redis):
        self.redis = redis

    async def init_state(self, base: dict[str, dict[str, str]]) -> None:
        pipe = self.redis.pipeline(transaction=False)
        for sym, fields in base.items():
            if fields:
                pipe.hset(f"rt:state:{sym}", mapping=fields)
                pipe.expire(f"rt:state:{sym}", _TTL_S)
        await pipe.execute()

    async def apply(self, n: Normalized) -> None:
        event = _EVENT_OF_TABLE[n.table]
        if n.table == "pt_match":
            key = n.row["market"]
        else:
            key = n.symbol
        pipe = self.redis.pipeline(transaction=False)
        if n.table == "snapshot_delta":
            pipe.hset(f"rt:state:{n.symbol}", mapping=n.delta)
            pipe.expire(f"rt:state:{n.symbol}", _TTL_S)
        elif n.table == "index_delta":
            pipe.hset(f"rt:state:idx:{n.symbol}", mapping=n.delta)
            pipe.expire(f"rt:state:idx:{n.symbol}", _TTL_S)
        pipe.publish(f"rt:pub:{event}:{key}", json.dumps({"symbol": n.symbol, **n.delta},
                                                         ensure_ascii=False))
        await pipe.execute()
