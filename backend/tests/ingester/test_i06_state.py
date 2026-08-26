import asyncio
import json

import pytest
import redis.asyncio as aioredis

from ingester.normalize import Metrics, normalize
from ingester.state import RedisSink

RECV = 1786342136000


@pytest.fixture()
def run(redis_url):
    def _run(coro):
        return asyncio.run(coro)
    return _run


def test_init_and_apply_i(redis_url, run):
    async def scenario():
        r = aioredis.Redis.from_url(redis_url, decode_responses=True)
        sink = RedisSink(r)
        await sink.init_state({"BID": {"open": "39550", "reference": "39050"}})
        assert await r.hget("rt:state:BID", "open") == "39550"

        pubsub = r.pubsub()
        await pubsub.subscribe("rt:pub:i:BID")
        await pubsub.get_message(timeout=2)          # subscribe ack
        n = normalize("i", {"EX": "HOSE", "t": 1786330492737, "U2": "43500", "SB": "BID"}, RECV, Metrics())
        await sink.apply(n)
        assert await r.hget("rt:state:BID", "u2") == "43500"
        assert await r.hget("rt:state:BID", "open") == "39550"   # trường cũ giữ nguyên
        assert await r.ttl("rt:state:BID") > 0
        msg = await pubsub.get_message(timeout=2)
        body = json.loads(msg["data"])
        assert body["symbol"] == "BID" and body["u2"] == "43500"
        await r.aclose()
    run(scenario())


def test_apply_trade_publishes_no_hash(redis_url, run):
    async def scenario():
        r = aioredis.Redis.from_url(redis_url, decode_responses=True)
        sink = RedisSink(r)
        n = normalize("t", {"TD": "10/08/2026", "FT": "13:08:56", "SB": "ACV", "FV": "100",
                            "LC": "S", "FMP": "42100.0", "FCV": "1000.0", "SM": "74027",
                            "AVO": "590000", "AVA": "24983210000.0"}, RECV, Metrics())
        pubsub = r.pubsub()
        await pubsub.subscribe("rt:pub:t:ACV")
        await pubsub.get_message(timeout=2)
        await sink.apply(n)
        msg = await pubsub.get_message(timeout=2)
        assert json.loads(msg["data"])["price"] == "42100.00"
        assert await r.exists("rt:state:ACV") == 0    # t không đụng HASH
        await r.aclose()
    run(scenario())
