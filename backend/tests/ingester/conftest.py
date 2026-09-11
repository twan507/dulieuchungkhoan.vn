# Fixture dùng chung cho test ingester.
# - Container ClickHouse + schema rt: fixture `ch`/`migrated` nằm ở conftest GỐC
#   (backend/tests/conftest.py) nên dùng chung THẬT — trước 2026-09-07 file này
#   import lại từ tests/clickhouse/conftest và vì thế dựng container thứ hai.
# - Redis ephemeral riêng (không đụng Redis dev).
import socket
import subprocess
import time
import uuid

import pytest


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def redis_url():
    name = f"redis-test-{uuid.uuid4().hex[:8]}"
    port = _free_port()
    subprocess.run(["docker", "run", "-d", "--rm", "--name", name,      # --rm + `rm -v`: redis:7-alpine
                    "-p", f"127.0.0.1:{port}:6379", "redis:7-alpine"],  # khai VOLUME /data, xem tests/conftest.py
                   check=True, capture_output=True)
    url = f"redis://127.0.0.1:{port}/0"
    import redis as redis_sync
    try:
        r = redis_sync.Redis.from_url(url)
        for _ in range(30):
            try:
                if r.ping():
                    break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("redis test container không lên")
        yield url
    finally:
        subprocess.run(["docker", "rm", "-f", "-v", name], capture_output=True)
