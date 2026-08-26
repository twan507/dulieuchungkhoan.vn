"""Leader lock Redis — SET NX PX + Lua renew so id (spec §3.6, market-data-store §3.1)."""
from __future__ import annotations

import asyncio
import os
import secrets
import socket

_RENEW_LUA = ("if redis.call('get', KEYS[1]) == ARGV[1] then"
              " return redis.call('pexpire', KEYS[1], ARGV[2]) else return 0 end")


class LeaderLock:
    KEY = "rt:ingester:leader"

    def __init__(self, redis, ttl_ms: int = 5000, renew_s: float = 2.0, retry_s: float = 0.5):
        self.redis = redis
        self.ttl_ms = ttl_ms
        self.renew_s = renew_s
        self.retry_s = retry_s
        self.id = f"{socket.gethostname()}:{os.getpid()}:{secrets.token_hex(4)}"

    async def try_acquire(self) -> bool:
        return bool(await self.redis.set(self.KEY, self.id, nx=True, px=self.ttl_ms))

    async def renew(self) -> bool:
        return bool(await self.redis.eval(_RENEW_LUA, 1, self.KEY, self.id, str(self.ttl_ms)))

    async def run(self, is_leader: asyncio.Event) -> None:
        self._net_fail = 0
        while True:
            try:
                if is_leader.is_set():
                    if not await self.renew():
                        is_leader.clear()        # khoá mất về tay khác → hạ cấp NGAY
                    self._net_fail = 0
                    await asyncio.sleep(self.renew_s)
                else:
                    won = await self.try_acquire()
                    self._net_fail = 0           # gọi Redis thành công (dù thắng hay thua) → hết lỗi mạng
                    if won:
                        is_leader.set()
                        continue
                    await asyncio.sleep(self.retry_s)
            except (ConnectionError, OSError):
                self._net_fail += 1
                if self._net_fail >= 2 and is_leader.is_set():
                    is_leader.clear()            # mất Redis 2 nhịp → ngừng ghi
                await asyncio.sleep(self.retry_s)
