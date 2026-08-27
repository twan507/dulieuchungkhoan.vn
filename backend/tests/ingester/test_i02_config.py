from pathlib import Path

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


def test_load_exits_2_when_a_runtime_dir_cannot_be_created(monkeypatch, capsys):
    """Ba `mkdir` nằm trần trên đường khởi động: ổ chỉ đọc, quyền sai, đường dẫn env trỏ
    vào chỗ không tạo được — cả ba ném `OSError` và thoát ra thành traceback trần exit 1,
    đi vòng đúng hợp đồng "thiếu điều kiện khởi động thì exit 2" mà `load()` đã dựng."""
    monkeypatch.setenv("CLICKHOUSE_INGESTER_URL", "http://u:p@127.0.0.1:8123")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")

    def _boom(self, parents=False, exist_ok=False):
        raise PermissionError("ổ đĩa chỉ đọc")

    monkeypatch.setattr(Path, "mkdir", _boom)
    with pytest.raises(SystemExit) as ei:
        load(need_db=True)
    assert ei.value.code == 2
    assert "ingester:" in capsys.readouterr().err
