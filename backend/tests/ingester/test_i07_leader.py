import asyncio
import contextlib

import redis.asyncio as aioredis
import redis.exceptions

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
                # redis.exceptions.ConnectionError — KHÔNG kế thừa builtin ConnectionError
                raise redis.exceptions.ConnectionError("mạng chập chờn 1 nhịp")
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


def test_run_survives_redis_error_and_regains_leadership():
    """CRITICAL 2 review cuối — `redis.exceptions.ConnectionError` KHÔNG kế thừa builtin
    ConnectionError/OSError, nên `except (ConnectionError, OSError)` không bắt được:
    blip Redis đầu tiên giết task `run()`, `is_leader` đóng băng ở giá trị cuối. Nếu lúc
    đó đang là leader thì tiến trình ghi mãi trong khi instance khác đã tiếp quản.

    Kịch bản: đang leader, Redis hỏng 2 nhịp LIÊN TIẾP → phải hạ cấp (is_leader.clear())
    NHƯNG vòng run() vẫn sống, và khi Redis lành thì giành lại được khoá.
    """
    class _BlipRedis:
        def __init__(self):
            self.fail_left = 2                   # 2 nhịp lỗi liên tiếp rồi lành

        def _maybe_fail(self):
            if self.fail_left > 0:
                self.fail_left -= 1
                raise redis.exceptions.ConnectionError("Error 10061 connecting to redis")

        async def eval(self, *a, **kw):          # renew (đang leader)
            self._maybe_fail()
            return 1

        async def set(self, *a, **kw):           # try_acquire (đang standby)
            self._maybe_fail()
            return True

    async def _wait_until(pred, timeout=2.0):
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            if pred():
                return True
            await asyncio.sleep(0.005)
        return False

    async def scenario():
        lock = LeaderLock(_BlipRedis(), renew_s=0.01, retry_s=0.01)
        is_leader = asyncio.Event()
        is_leader.set()                          # đang là leader khi Redis bắt đầu hỏng
        task = asyncio.create_task(lock.run(is_leader))
        try:
            assert await _wait_until(lambda: not is_leader.is_set()), "2 nhịp lỗi phải hạ cấp"
            assert not task.done(), "vòng run() không được chết vì lỗi Redis"
            assert await _wait_until(is_leader.is_set), "Redis lành phải giành lại được khoá"
            assert not task.done()
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
    asyncio.run(scenario())
