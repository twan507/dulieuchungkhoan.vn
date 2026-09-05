"""Yahoo: 37 chỉ số, ba cổng (granularity · instrumentType · độ tươi), múi giờ sàn, nến chưa đóng — fixture 2026-09-05."""
import json
import os
import pathlib
import urllib.parse
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import yahoo_fetch as yf
from etl import yahoo_job as yj
from etl import yahoo_normalize as yn
from etl import yahoo_registry as yr
from etl.registry import SeriesError

FIX = pathlib.Path(__file__).parent / "fixtures" / "global"
REG = {s.external_key: s for s in yr.build()}
NOW = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def _doc(name):
    return json.loads((FIX / f"yahoo-{name}.json").read_text(encoding="utf-8"))


def test_registry_37_indices_all_ohlc():
    s = yr.build()
    assert len(s) == 37 and all(x.shape == "ohlc" and x.asset_class == "index" and x.price_type is None and x.source == "yahoo"
                                and x.unit == "điểm" and x.calendar == "trading_days" and x.max_lag_days == 14 for x in s)
    assert REG["^GSPC"].code == "idx.sp500" and REG["DX-Y.NYB"].code == "dxy.ice" and REG["^KS11"].code == "idx.kospi"
    assert REG["^N225"].quote_currency == "JPY" and REG["^MERV"].quote_currency == "ARS" and REG["^GSPC"].band == (Decimal(700), Decimal(80000))
    assert len({x.code for x in s}) == 37


def test_url_uses_period_not_range_and_backfill_period1_is_negative():
    assert yf.url("^GSPC", -2208988800, 1000) == "https://query1.finance.yahoo.com/v8/finance/chart/^GSPC?period1=-2208988800&period2=1000&interval=1d"
    assert yf.BACKFILL_PERIOD1 == -2208988800 and yf.DAILY_WINDOW_DAYS == 400


def test_intraday_window_is_five_days_daily_is_400_and_backfill_is_1900():
    def window(**kw):
        calls = []
        yf.fetch_all([REG["^GSPC"]], lambda u, t: (calls.append(u), (200, json.dumps(_doc("GSPC-10d")), {}))[1], lambda s: None, **kw)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(calls[0]).query)
        return int(q["period2"][0]) - int(q["period1"][0])
    assert yf.INTRADAY_WINDOW_DAYS == 5
    assert window(backfill=False, intraday=True) == 5 * 86400
    assert window(backfill=False, intraday=False) == 400 * 86400
    assert window(backfill=True, intraday=False) > 100 * 365 * 86400          # period1 = 1900-01-01


def test_classify():
    assert yf.classify(200, json.dumps(_doc("GSPC-10d")))[0] == "ok"
    assert yf.classify(200, '{"chart":{"result":null,"error":{"code":"Not Found"}}}') == ("bad_shape", None)
    assert yf.classify(404, "") == ("bad_shape", None)                  # period1/period2 cố định: 404 = mã đã chết
    assert yf.classify(503, "") == ("retry", None)
    assert yf.classify(200, "not json") == ("retry", None)


def test_gspc_bars_are_dated_in_new_york_and_carry_literal_close_open_volume():
    bars = yn.bars(REG["^GSPC"], _doc("GSPC-10d"), NOW)
    assert len(bars) == 8 and bars[0].obs_date == date(2026, 8, 26)
    b = bars[-1]
    assert (b.obs_date, b.close, b.open, b.volume, b.close_adj, b.code) == (
        date(2026, 9, 4), Decimal("7718.60009765625"), Decimal("7750.18994140625"), Decimal("4103570000"), Decimal("7718.60009765625"), "idx.sp500")


def test_exchange_timezone_decides_the_date_for_tokyo_and_ice():
    assert yn.bars(REG["^N225"], _doc("N225-10d"), NOW)[-1].obs_date == date(2026, 9, 4)          # 00:00 UTC = 09:00 Tokyo
    dxy = yn.bars(REG["DX-Y.NYB"], _doc("DXY-10d"), NOW)
    assert len(dxy) == 8 and dxy[-1].obs_date == date(2026, 9, 4) and dxy[-1].close == Decimal("99.16000366210938")   # 9 nến − 1 null


import dataclasses
FX_EUR = dataclasses.replace(REG["^GSPC"], external_key="EUR=X", code="fx.usd_eur.market", quote_currency="EUR",
                             band=(Decimal("0.08"), Decimal("9")), max_lag_days=6)
FX_CAD = dataclasses.replace(FX_EUR, external_key="CAD=X", code="fx.usd_cad.market", quote_currency="CAD",
                             band=(Decimal("0.13"), Decimal("14")))


def test_open_candle_is_kept_while_the_regular_session_is_still_running():
    during = datetime(2026, 9, 4, 15, 0, tzinfo=timezone.utc)                          # trong phiên NY (13:30–20:00)
    bars = yn.bars(REG["^GSPC"], _doc("GSPC-10d"), during)
    assert len(bars) == 8 and bars[-1].obs_date == date(2026, 9, 4) and bars[-1].close == Decimal("7718.60009765625")
    early = datetime(2026, 9, 5, 2, 0, tzinfo=timezone.utc)                            # DXY regular.end = 03:59 UTC 09-05 — không còn cắt
    assert yn.bars(REG["DX-Y.NYB"], _doc("DXY-10d"), early)[-1].obs_date == date(2026, 9, 4)


def test_fx_two_candles_on_the_same_london_date_keep_the_live_one():
    # EUR=X 2026-09-05: nến 2026-09-03T23:00Z (London 09-04, close≈open "rỗng") và nến live 2026-09-04T21:29Z (London 09-04)
    s = FX_EUR
    bars = yn.bars(s, _doc("EURX-5d"), NOW)
    by = {b.obs_date: b for b in bars}
    assert sorted(by) == [date(2026, 8, 31), date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 3), date(2026, 9, 4)]
    b = by[date(2026, 9, 4)]
    assert (b.close, b.high, b.low) == (Decimal("0.8604999780654907"), Decimal("0.8626999855041504"), Decimal("0.8593999743461609"))
    assert b.close != Decimal("0.859969973564148")                                        # nến rỗng 23:00 bị nến live đè


def test_fx_weekend_candle_lands_on_its_london_date():
    bars = yn.bars(FX_CAD, _doc("CADX-5d"), NOW)                                    # nến cuối 2026-09-05T04:21Z = thứ 7 London
    assert bars[-1].obs_date == date(2026, 9, 5) and bars[-1].close == Decimal("1.3837000131607056")
    assert bars[-2].obs_date == date(2026, 9, 4) and bars[-2].close == Decimal("1.3789499998092651")


def test_three_gates_altsymbol_stale_granularity_and_currency():
    with pytest.raises(SeriesError) as e:
        yn.bars(REG["^GSPC"], _doc("TIO=F-40d"), NOW)
    assert e.value.reason == "shape" and "ALTSYMBOL" in str(e.value)
    with pytest.raises(SeriesError) as e:
        yn.bars(REG["^GSPC"], _doc("BCOM-40d"), NOW)
    assert e.value.reason == "stale"
    doc = json.loads(json.dumps(_doc("GSPC-10d")))
    doc["chart"]["result"][0]["meta"]["dataGranularity"] = "1mo"
    with pytest.raises(SeriesError) as e:
        yn.bars(REG["^GSPC"], doc, NOW)
    assert e.value.reason == "shape"
    doc = json.loads(json.dumps(_doc("GSPC-10d")))
    doc["chart"]["result"][0]["meta"]["currency"] = "EUR"
    with pytest.raises(SeriesError) as e:
        yn.bars(REG["^GSPC"], doc, NOW)
    assert e.value.reason == "shape"
    assert yn.bars(REG["^MERV"], _doc("MERV-10d"), NOW)[-1].close == Decimal("3049122.0")   # currency rỗng ⇒ qua


def test_missing_regular_market_time_or_indicators_is_a_shape_error_not_a_crash():
    doc = json.loads(json.dumps(_doc("GSPC-10d")))
    del doc["chart"]["result"][0]["meta"]["regularMarketTime"]
    with pytest.raises(SeriesError) as e:
        yn.bars(REG["^GSPC"], doc, NOW)
    assert e.value.reason == "shape"
    doc = json.loads(json.dumps(_doc("GSPC-10d")))
    del doc["chart"]["result"][0]["indicators"]
    with pytest.raises(SeriesError) as e:
        yn.bars(REG["^GSPC"], doc, NOW)
    assert e.value.reason == "shape"


def test_band_catches_100x_error():
    doc = json.loads(json.dumps(_doc("GSPC-10d")))
    q = doc["chart"]["result"][0]["indicators"]["quote"][0]
    q["close"] = [c * 100 if c else c for c in q["close"]]
    with pytest.raises(SeriesError) as e:
        yn.bars(REG["^GSPC"], doc, NOW)
    assert e.value.reason == "band"


# ---- job ----
CODES = [s.code for s in yr.build()]
FIXTURE_OF = {"^GSPC": "GSPC-10d", "^N225": "N225-10d", "DX-Y.NYB": "DXY-10d", "^MERV": "MERV-10d"}


def _synthetic(sym):
    doc = _doc("GSPC-10d")
    res = doc["chart"]["result"][0]
    s = REG[sym]
    v = float(s.band[0] * 10)
    res["meta"].update(symbol=sym, currency=s.quote_currency)
    q = res["indicators"]["quote"][0]
    for k in ("open", "high", "low", "close"):
        q[k] = [v] * len(q[k])
    res["indicators"]["adjclose"][0]["adjclose"] = [v] * len(q["close"])
    return json.dumps(doc)


def _fake_get(calls=None, dead=(), stale=()):
    def get(u, timeout):
        sym = urllib.parse.unquote(u.split("/chart/")[1].split("?")[0])
        if calls is not None:
            calls.append(u)
        if sym in dead:
            return 200, json.dumps(_doc("TIO=F-40d")), {}
        if sym in stale:
            return 200, json.dumps(_doc("BCOM-40d")), {}
        return 200, (json.dumps(_doc(FIXTURE_OF[sym])) if sym in FIXTURE_OF else _synthetic(sym)), {}
    return get


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM asset.ohlc_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='yahoo')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='yahoo'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job='global.yahoo'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source='yahoo'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='yahoo'"))
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
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job='global.yahoo' ORDER BY run_id DESC LIMIT 1")).one()


def test_job_writes_296_bars_and_is_idempotent(clean):
    calls = []
    assert yj.run(get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    assert len(calls) == 37 and all("period1=" in u and "range=" not in u for u in calls)
    status, stats, _ = _last(clean)
    assert status == "success" and stats["tally"]["ok"] == 37 and stats["bars"] == 296 and stats["inserted"] == 296
    with clean.connect() as c:
        row = c.execute(sa.text("SELECT close, volume FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id)"
                                " WHERE a.code='idx.sp500' AND obs_date='2026-09-04'")).one()
        assert tuple(row) == (Decimal("7718.60009765625"), Decimal("4103570000"))
        assert c.execute(sa.text("SELECT price_type FROM asset.asset_external_id WHERE source='yahoo' AND external_code='^GSPC'")).scalar() is None
        assert dict(c.execute(sa.text("SELECT domain, watermark FROM ops.data_domain_state WHERE source='yahoo'")).all()) == {"asset": "2026-09-05"}
    assert yj.run(get=_fake_get(), sleep=lambda s: None, now=NOW) == 0
    assert (_last(clean)[1]["inserted"], _last(clean)[1]["changed"]) == (0, 0)


def test_backfill_uses_negative_period1(clean):
    calls = []
    assert yj.run(backfill=True, keys=["^GSPC"], get=_fake_get(calls), sleep=lambda s: None, now=NOW) == 0
    assert len(calls) == 1 and "period1=-2208988800" in calls[0]


def test_ratio_guard_refuses_three_dead_symbols_but_tolerates_one(clean):
    assert yj.run(get=_fake_get(dead=("^AEX", "^BFX", "^OMX")), sleep=lambda s: None, now=NOW) == 1      # 8,1 % > 5 %
    status, stats, error = _last(clean)
    assert status == "failed" and stats["tally"]["shape"] == 3 and "sai hình dạng" in error
    with clean.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM asset.asset_external_id WHERE source='yahoo'")).scalar() == 0
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source='yahoo' AND (meta->>'refused')::bool")).scalar() == 37
    assert yj.run(get=_fake_get(dead=("^AEX",)), sleep=lambda s: None, now=NOW) == 0                      # 2,7 %: bỏ series đó
    status, stats, _ = _last(clean)
    assert status == "success" and stats["tally"]["shape"] == 1 and stats["bars"] == 288
