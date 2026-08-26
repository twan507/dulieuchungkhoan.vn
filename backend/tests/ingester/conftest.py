# Fixture dùng chung cho test ingester.
# - Mượn container ClickHouse ephemeral + schema rt của bộ test clickhouse.
# - Redis ephemeral riêng (không đụng Redis dev).
import socket
import subprocess
import time
import uuid

import pytest

from tests.clickhouse.conftest import ch, ch_backup_dir, migrated  # noqa: F401


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def redis_url():
    name = f"redis-test-{uuid.uuid4().hex[:8]}"
    port = _free_port()
    subprocess.run(["docker", "run", "-d", "--name", name,
                    "-p", f"127.0.0.1:{port}:6379", "redis:7-alpine"],
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
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
