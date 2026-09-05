"""CLI lát 7b: `--intraday` cho yahoo/binance, loại trừ `--backfill`, fred/fx/lbma không có cờ này (spec §4.6-IV)."""
import pytest

import etl.__main__ as m


def test_yahoo_and_binance_intraday_flag_reaches_the_job(monkeypatch):
    import etl.binance_job
    import etl.yahoo_job
    seen = {}
    monkeypatch.setattr(etl.yahoo_job, "run", lambda **kw: seen.setdefault("yahoo", kw) and 0)
    monkeypatch.setattr(etl.binance_job, "run", lambda **kw: seen.setdefault("binance", kw) and 0)
    assert m.main(["yahoo", "--intraday"]) == 0
    assert m.main(["binance", "--keys", "BTCUSDT", "--intraday", "--dry-run"]) == 0
    assert seen["yahoo"] == {"keys": None, "dry_run": False, "backfill": False, "intraday": True}
    assert seen["binance"] == {"keys": ["BTCUSDT"], "dry_run": True, "backfill": False, "intraday": True}


def test_intraday_and_backfill_are_mutually_exclusive_and_fred_has_no_intraday():
    with pytest.raises(SystemExit) as e:
        m.main(["yahoo", "--intraday", "--backfill"])
    assert e.value.code == 2
    with pytest.raises(SystemExit) as e:
        m.main(["fred", "--intraday"])
    assert e.value.code == 2


def test_wichart_intraday_flag_reaches_the_job(monkeypatch):
    import etl.wichart_job
    seen = {}
    monkeypatch.setattr(etl.wichart_job, "run", lambda **kw: seen.update(kw) or 0)
    assert m.main(["wichart", "--intraday"]) == 0
    assert seen == {"keys": None, "dry_run": False, "intraday": True}
