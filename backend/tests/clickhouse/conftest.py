import os
import socket
import subprocess
import time
import uuid
from pathlib import Path

import clickhouse_connect
import pytest

IMAGE = "clickhouse/clickhouse-server:26.3.22.7"
REPO_ROOT = Path(__file__).resolve().parents[3]
CH_CONF_DIR = REPO_ROOT / "deploy" / "infra" / "clickhouse"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def ch_backup_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("ch-backups")


@pytest.fixture(scope="session")
def ch(ch_backup_dir):
    """Container ClickHouse ephemeral — không đụng CH dev. Xoá khi hết session."""
    name = f"ch-test-{uuid.uuid4().hex[:8]}"
    port = _free_port()
    cmd = [
        "docker", "run", "-d", "--name", name,
        "--ulimit", "nofile=262144:262144",
        "-e", "CLICKHOUSE_PASSWORD=testpass",
        "-e", "CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1",
        "-e", "TZ=Asia/Ho_Chi_Minh",
        "-v", f"{CH_CONF_DIR / 'backups.xml'}:/etc/clickhouse-server/config.d/backups.xml:ro",
        "-v", f"{ch_backup_dir}:/backups",
        "-p", f"127.0.0.1:{port}:8123",
        IMAGE,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    url = f"http://default:testpass@127.0.0.1:{port}"
    client = None
    try:
        for _ in range(60):
            try:
                client = clickhouse_connect.get_client(dsn=url)
                client.command("SELECT 1")
                break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("ClickHouse test container không lên sau 60s")
        os.environ["CLICKHOUSE_URL"] = url
        yield client
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
