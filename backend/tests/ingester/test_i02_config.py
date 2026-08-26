import pytest

import ingester.config as config_mod
from ingester.config import load


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    """Cách ly khỏi .env thật của máy — nếu không, load_dotenv nạp lại đúng biến
    mà test vừa xoá và phép kiểm 'thiếu env thì thoát' thành vô nghĩa."""
    monkeypatch.setattr(config_mod, "load_dotenv", lambda: None)


def test_load_measure_mode_needs_no_db(monkeypatch):
    monkeypatch.delenv("CLICKHOUSE_INGESTER_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    cfg = load(need_db=False)
    assert cfg.measure_dir.name == "measure"


def test_load_run_mode_requires_db(monkeypatch):
    monkeypatch.delenv("CLICKHOUSE_INGESTER_URL", raising=False)
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    with pytest.raises(SystemExit):
        load(need_db=True)


def test_load_run_mode_ok_when_both_present(monkeypatch):
    monkeypatch.setenv("CLICKHOUSE_INGESTER_URL", "http://u:p@127.0.0.1:8123")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    cfg = load(need_db=True)
    assert cfg.clickhouse_url.endswith(":8123") and cfg.redis_url.endswith("/0")
