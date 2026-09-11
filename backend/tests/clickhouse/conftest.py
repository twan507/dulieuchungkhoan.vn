"""Helper riêng cho bộ test ClickHouse.

Ba fixture `ch_backup_dir` / `ch` / `migrated` đã DỜI về `backend/tests/conftest.py`
(2026-09-07). Lý do: `tests/ingester/conftest.py` import lại chúng từ đây, mà pytest coi
import-lại-vào-conftest-ANH-EM là HAI FixtureDef ⇒ đo được **2 container ClickHouse**
trong một lượt `pytest tests/clickhouse tests/ingester`, dù comment ở đó khai là "mượn".
Đúng anti-pattern mà test-strategy.md §6 đã cấm cho Postgres, tái diễn cho ClickHouse.
"""
from datetime import date, datetime, timedelta

TODAY = date.today()


def dt_ago(days: int, h: int = 9, m: int = 15, s: int = 1, micro: int = 0) -> datetime:
    d = TODAY - timedelta(days=days)
    return datetime(d.year, d.month, d.day, h, m, s, micro)


def part_of(dt: datetime) -> str:
    return dt.strftime("%Y%m")
