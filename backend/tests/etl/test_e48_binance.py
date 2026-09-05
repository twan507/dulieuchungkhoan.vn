"""Binance: nến định danh bằng thời điểm MỞ theo UTC, giá chuỗi ⇒ Decimal, bỏ nến chưa đóng, header weight."""
import dataclasses
import json
import os
import pathlib
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import binance_fetch as bf
from etl import binance_job as bj
from etl import binance_normalize as bn
from etl import binance_registry as br
from etl.registry import SeriesError

FIX = pathlib.Path(__file__).parent / "fixtures" / "global"
PAXG = json.loads((FIX / "binance-PAXGUSDT-5.json").read_text(encoding="utf-8"))
BTC3 = json.loads((FIX / "binance-BTCUSDT-first3.json").read_text(encoding="utf-8"))
REG = {s.external_key: s for s in br.build()}
NOW = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def test_registry_11_usdt_24x7():
    s = br.build()
    assert len(s) == 11 and all(x.quote_currency == "USDT" and x.calendar == "24x7" and x.asset_class == "crypto"
                                and x.shape == "ohlc" and x.max_lag_days == 2 and x.source == "binance" for x in s)
    assert REG["PAXGUSDT"].code == "paxg" and REG["BTCUSDT"].code == "btc" and REG["DOGEUSDT"].band == (Decimal("0.008"), Decimal("0.85"))


def test_url_and_classify():
    assert bf.url("PAXGUSDT", 40) == "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1d&limit=40&timeZone=0"
    assert bf.url("BTCUSDT", 1000, 0).endswith("&startTime=0")
    assert bf.classify(200, json.dumps(PAXG))[0] == "ok"
    assert bf.classify(200, "[[1,2,3]]") == ("bad_shape", None)
    assert bf.classify(429, "") == ("retry", None)


def test_open_time_utc_date_string_prices_and_the_running_candle_is_kept():
    bars = bn.bars(REG["PAXGUSDT"], PAXG, NOW)
    assert [b.obs_date for b in bars] == [date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 3), date(2026, 9, 4), date(2026, 9, 5)]
    b = bars[-2]
    assert (b.open, b.high, b.low, b.close, b.volume, b.close_adj, b.code) == (
        Decimal("4481.95"), Decimal("4489.97"), Decimal("4375.00"), Decimal("4431.81"), Decimal("5744.5282"), None, "paxg")
    assert bars[-1].close == Decimal("4433.56")                                       # nến 09-05 đang chạy (fixture chụp 05/09)
    assert len(bn.bars(REG["PAXGUSDT"], PAXG, datetime(2026, 9, 6, 0, 30, tzinfo=timezone.utc))) == 5


def test_limit_3_fixture_has_two_closed_and_one_running_candle_for_today():
    btc3 = json.loads((FIX / "binance-BTCUSDT-3.json").read_text(encoding="utf-8"))
    bars = bn.bars(REG["BTCUSDT"], btc3, NOW)
    assert [b.obs_date for b in bars] == [date(2026, 9, 3), date(2026, 9, 4), date(2026, 9, 5)] and btc3[-1][6] > NOW.timestamp() * 1000


def test_seam4_step5_epoch_is_utc_not_vietnam():
    k = [[1786752000000, "1", "1", "1", "1", "1", 1786838399999, "0", 0, "0", "0", "0"]]
    assert bn.bars(REG["BTCUSDT"], [[k[0][0], "70000", "70000", "70000", "70000", "1", k[0][6], "0", 0, "0", "0", "0"]],
                   datetime(2026, 8, 17, tzinfo=timezone.utc))[0].obs_date == date(2026, 8, 15)


def test_first_btc_candle_literal_and_shape_stale():
    # Dải `band` là chốt cho GIÁ TRỊ HIỆN TẠI (bắt lỗi đơn vị); fixture 3 nến 2017 (~4.140) nằm ngoài dải hôm nay
    # (7.900–800.000) theo đúng thiết kế — nới dải riêng trong test để kiểm phép parse nến đầu, không sửa registry.
    btc_2017 = dataclasses.replace(REG["BTCUSDT"], band=(Decimal("1000"), Decimal("800000")))
    assert bn.bars(btc_2017, BTC3, datetime(2017, 8, 21, tzinfo=timezone.utc))[0].open == Decimal("4261.48")
    with pytest.raises(SeriesError) as e:
        bn.bars(REG["PAXGUSDT"], [PAXG[0][:11]], NOW)
    assert e.value.reason == "shape"
    with pytest.raises(SeriesError) as e:
        bn.bars(REG["PAXGUSDT"], PAXG, datetime(2026, 9, 10, tzinfo=timezone.utc))
    assert e.value.reason == "stale"


def test_weight_header_pauses_and_418_aborts():
    slept = []
    docs, texts, failed, calls, _ = bf.fetch_all([REG["PAXGUSDT"]], lambda u, t: (200, json.dumps(PAXG), {"x-mbx-used-weight-1m": "3500"}),
                                                 lambda s: slept.append(s), False)
    assert failed == [] and 60 in slept
    with pytest.raises(bf.Banned):
        bf.fetch_all([REG["PAXGUSDT"]], lambda u, t: (418, "banned", {}), lambda s: None, False)


def test_intraday_uses_limit_3_and_the_job_reports_the_flag(clean):
    calls = []
    docs, *_ = bf.fetch_all([REG["PAXGUSDT"]], lambda u, t: (calls.append(u), (200, json.dumps(PAXG), {}))[1], lambda s: None, False, True)
    assert bf.INTRADAY_LIMIT == 3 and calls and "limit=3" in calls[0] and "limit=40" not in calls[0]
    calls.clear()
    assert bj.run(intraday=True, get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    assert len(calls) == 11 and all("limit=3" in u for u in calls)
    status, stats = _last(clean)
    assert status == "success" and stats["intraday"] is True and "watermark" in stats


CODES = [s.code for s in br.build()]


def _synthetic(sym):
    v = str(REG[sym].band[0] * 10)
    return json.dumps([[k[0], v, v, v, v, "1", k[6], "0", 0, "0", "0", "0"] for k in PAXG])


def _fake_get(calls=None):
    def get(u, timeout):
        sym = u.split("symbol=")[1].split("&")[0]
        if calls is not None:
            calls.append(u)
        if "startTime=0" in u:
            page = [[PAXG[0][0] + i * 86400000, "1", "1", "1", "1", "1", PAXG[0][0] + i * 86400000 + 86399999, "0", 0, "0", "0", "0"] for i in range(1000)]
            return 200, json.dumps(page), {}
        if "startTime=" in u:
            return 200, _synthetic(sym), {}
        return 200, (json.dumps(PAXG) if sym == "PAXGUSDT" else _synthetic(sym)), {}
    return get


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM asset.ohlc_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='binance')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='binance'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job='global.binance'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source='binance'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='binance'"))
        c.execute(sa.text("DELETE FROM asset.asset WHERE code = ANY(:c)"), {"c": CODES})


@pytest.fixture()
def clean(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.series_job.load_dotenv", lambda *a, **k: None)
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def _last(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats FROM ops.etl_run WHERE job='global.binance' ORDER BY run_id DESC LIMIT 1")).one()


def test_job_writes_55_bars_including_the_running_one(clean):
    calls = []
    assert bj.run(get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    assert len(calls) == 11 and all("limit=40" in u for u in calls)
    status, stats = _last(clean)
    assert status == "success" and stats["bars"] == 55 and stats["inserted"] == 55 and stats["tally"]["ok"] == 11
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT close FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id)"
                                 " WHERE a.code='paxg' AND obs_date='2026-09-04'")).scalar() == Decimal("4431.81")
        assert c.execute(sa.text("SELECT count(*) FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id)"
                                 " WHERE a.code='paxg' AND obs_date='2026-09-05'")).scalar() == 1
        assert c.execute(sa.text("SELECT quote_currency, calendar FROM asset.asset WHERE code='btc'")).one() == ("USDT", "24x7")
    assert bj.run(get=_fake_get(), sleep=lambda s: None, now=NOW) == 0
    assert (_last(clean)[1]["inserted"], _last(clean)[1]["changed"]) == (0, 0)


def test_backfill_pages_from_start_time_zero(clean):
    calls = []
    assert bj.run(backfill=True, keys=["BTCUSDT"], get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    assert len(calls) == 2 and "startTime=0" in calls[0] and "limit=1000" in calls[0] and "startTime=" in calls[1]
