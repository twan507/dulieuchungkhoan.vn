import asyncio
import contextlib

import redis.asyncio as aioredis

from ingester.leader import LeaderLock


def test_lock_exclusive_and_renew(redis_url):
    async def scenario():
        r1 = aioredis.Redis.from_url(redis_url, decode_responses=True)
        r2 = aioredis.Redis.from_url(redis_url, decode_responses=True)
        a = LeaderLock(r1, ttl_ms=800)
        b = LeaderLock(r2, ttl_ms=800)
        assert await a.try_acquire() is True
        assert await b.try_acquire() is False
        assert await a.renew() is True
        assert await b.renew() is False          # không đè/đụng khoá của a
        await asyncio.sleep(1.0)                 # TTL hết, a không renew nữa
        assert await b.try_acquire() is True     # tiếp quản
        await r1.aclose(); await r2.aclose()
    asyncio.run(scenario())


def test_run_resets_net_fail_on_standby_success():
    """MINOR 5 review wave 2 — trước fix, net_fail chỉ reset ở nhánh leader; một lỗi
    mạng khi đang standby sẽ ở lại "treo" mãi dù các lần try_acquire sau đó vẫn thành
    công (không exception), làm sai điều kiện hạ cấp "mất Redis 2 nhịp liên tiếp"."""
    class _FlakyRedis:
        def __init__(self):
            self.calls = 0

        async def set(self, *a, **kw):
            self.calls += 1
            if self.calls == 1:
                raise ConnectionError("mạng chập chờn 1 nhịp")
            return None                          # các lần sau: gọi được nhưng không giành được khoá

    async def scenario():
        lock = LeaderLock(_FlakyRedis(), retry_s=0.01)
        is_leader = asyncio.Event()
        task = asyncio.create_task(lock.run(is_leader))
        await asyncio.sleep(0.08)                # đủ vài vòng lặp: 1 lỗi rồi nhiều lần thành công
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        assert lock._net_fail == 0               # đã reset ở lần try_acquire thành công kế tiếp
    asyncio.run(scenario())
