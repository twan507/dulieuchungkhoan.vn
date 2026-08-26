import pytest

from ingester.config import load


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
