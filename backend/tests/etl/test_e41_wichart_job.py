"""Job trọn vòng trên Postgres thật. `get` giả: fixture thật cho 12 key, response tổng hợp cho phần còn lại
(một điểm, giá trị giữa dải đơn vị, neo đúng tần suất) — đủ để guard và apply đi qua đường thật."""
import json
import os
import pathlib
from datetime import datetime
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import wichart_job as wj
from etl import wichart_registry as wr
from etl import wichart_store as ws
from etl.wichart_normalize import VN

FIX = pathlib.Path(__file__).parent / "fixtures" / "wichart"
EPOCH = {"d": 1788454800000, "m": 1785517200000, "q": 1780246800000, "y": 1764522000000}   # 04/09/2026 · 08/2026 · 06/2026 (Q2) · 12/2025, giờ VN
DOC, _ = wr.load_doc()
OURS = {(s.key, s.idx): s for s in wr.build()}
MACRO_CODES = [s.code for s in OURS.values() if s.domain == "macro"]
ASSET_CODES = [s.code for s in OURS.values() if s.domain == "asset"]


def _synthetic(key: str) -> str:
    meta = DOC[key]
    series = []
    for idx, (name, unit_doc, scale, role, flags) in enumerate(meta["s"]):
        s = OURS.get((key, idx))
        if s is None:
            raw = 1.0                                          # series không nạp (chết) — giữ vị trí
        else:
            lo, hi = wr.BANDS.get(s.unit, (1, 1))
            lo_d, hi_d = Decimal(str(lo)), Decimal(str(hi))
            # dải cắt qua 0 (USD, %) nay so CÓ DẤU (I2) — chọn điểm giữa dương, xa cả hai biên và mọi LEVEL_FLOOR
            v = hi_d / 2 if lo_d < 0 else (lo_d * 10 if lo_d * 10 <= hi_d else lo_d)
            raw = float(v / s.scale)
        series.append({"name": name, "unit": unit_doc, "data": [[EPOCH[meta.get("freq", "d")], raw]]})
    return json.dumps({"title": key, "timeArray": [meta.get("freq", "d")], "chart": {"series": series}})


def _fake_get(calls=None, fail_all=False):
    def get(u, timeout):
        key = u.rsplit("name=", 1)[1]
        if calls is not None:
            calls.append(key)
        if fail_all:
            return 503, ""
        p = FIX / f"{key}.json"
        return 200, (p.read_text(encoding="utf-8") if p.exists() else _synthetic(key))
    return get


def _fake_get_partial_failure(fail_count, calls=None):
    """503 (mọi lần thử) cho `fail_count` key ĐẦU TIÊN theo thứ tự gọi lần đầu; phần còn lại như _fake_get."""
    order: list[str] = []

    def get(u, timeout):
        key = u.rsplit("name=", 1)[1]
        if calls is not None:
            calls.append(key)
        if key not in order:
            order.append(key)
        if order.index(key) < fail_count:
            return 503, ""
        p = FIX / f"{key}.json"
        return 200, (p.read_text(encoding="utf-8") if p.exists() else _synthetic(key))
    return get


def _last_run_id(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT run_id FROM ops.etl_run WHERE job = :j ORDER BY run_id DESC LIMIT 1"),
                         {"j": ws.JOB}).scalar()


def _wire(monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.wichart_job.load_dotenv", lambda *a, **k: None)


def _cleanup(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM macro.series_break WHERE indicator_id IN"
                          " (SELECT indicator_id FROM macro.indicator_source WHERE source='wichart')"))
        c.execute(sa.text("DELETE FROM macro.observation WHERE indicator_id IN"
                          " (SELECT indicator_id FROM macro.indicator_source WHERE source='wichart')"))
        c.execute(sa.text("DELETE FROM asset.price_daily WHERE asset_id IN"
                          " (SELECT asset_id FROM asset.asset_external_id WHERE source='wichart')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source = 'wichart'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job = :j"), {"j": ws.JOB})
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source = 'wichart'"))
        # Registry: dòng ánh xạ trước, rồi indicator_id/asset_id chủ — không thì test khác (vd test_s06_asset
        # ghi thẳng code='wti') vỡ UNIQUE(code) vì mã của wichart còn sót lại giữa các file test (I6).
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source = 'wichart'"))
        c.execute(sa.text("DELETE FROM macro.indicator_source WHERE source = 'wichart'"))
        c.execute(sa.text("DELETE FROM asset.asset WHERE code = ANY(:codes)"), {"codes": ASSET_CODES})
        c.execute(sa.text("DELETE FROM macro.indicator WHERE code = ANY(:codes)"), {"codes": MACRO_CODES})


def _last_run(engine):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job = :j ORDER BY run_id DESC LIMIT 1"),
                         {"j": ws.JOB}).one()


def _scalar(engine, sql):
    with engine.connect() as c:
        return c.execute(sa.text(sql)).scalar()


@pytest.fixture()
def clean(migrated_engine):
    _cleanup(migrated_engine)
    yield migrated_engine
    _cleanup(migrated_engine)


def test_full_run_writes_both_domains_and_pushes_two_domain_states(clean, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert wj.run(get=_fake_get(calls), sleep=lambda s: None) == 0
    assert len(calls) == 68 and len(set(calls)) == 68
    status, stats, _ = _last_run(clean)
    assert status == "success"
    assert stats["registry"] == {"macro": 53, "asset": 52, "removed": 0}
    assert stats["tally"]["keys_failed"] == 0 and stats["tally"]["series_shape"] == 0 and stats["tally"]["series_band"] == 0
    assert stats["tally"]["series_ok"] == 105 and stats["changed"] == 0 and stats["inserted"] > 1000
    assert _scalar(clean, "SELECT count(*) FROM macro.observation o JOIN macro.indicator i USING (indicator_id) WHERE i.code='vn.cpi'") == 284
    assert _scalar(clean, "SELECT value FROM macro.observation o JOIN macro.indicator i USING (indicator_id)"
                          " WHERE i.code='vn.cpi' AND obs_date='2026-08-01'") == Decimal("4.45")
    assert _scalar(clean, "SELECT value FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                          " WHERE a.code='gold.sjc_buy' AND obs_date='2026-09-04'") == Decimal("145600000")
    assert _scalar(clean, "SELECT count(*) FROM macro.series_break") == 1
    assert stats["payloads_stored"] == 68
    today = datetime.now(VN).date().isoformat()
    with clean.connect() as c:
        rows = dict(c.execute(sa.text("SELECT domain, watermark FROM ops.data_domain_state WHERE source='wichart'")).all())
    assert rows == {"macro.indicator": today, "asset": today}


def test_second_run_same_day_changes_nothing_and_stores_no_payload(clean, monkeypatch):
    _wire(monkeypatch)
    assert wj.run(get=_fake_get(), sleep=lambda s: None) == 0
    n_payload = _scalar(clean, "SELECT count(*) FROM staging.raw_payload WHERE source='wichart'")
    ts = _scalar(clean, "SELECT max(ingested_at) FROM macro.observation")
    assert wj.run(get=_fake_get(), sleep=lambda s: None) == 0
    _, stats, _ = _last_run(clean)
    assert stats["inserted"] == 0 and stats["changed"] == 0 and stats["payloads_stored"] == 0
    assert _scalar(clean, "SELECT count(*) FROM staging.raw_payload WHERE source='wichart'") == n_payload
    assert _scalar(clean, "SELECT max(ingested_at) FROM macro.observation") == ts


def test_all_keys_failing_is_refused_with_nothing_written(clean, monkeypatch):
    _wire(monkeypatch)
    assert wj.run(get=_fake_get(fail_all=True), sleep=lambda s: None) == 1
    status, stats, err = _last_run(clean)
    assert status == "failed" and "key hỏng" in err
    assert _scalar(clean, "SELECT count(*) FROM macro.observation") == 0
    assert _scalar(clean, "SELECT count(*) FROM ops.data_domain_state WHERE source='wichart'") == 0


def test_partial_source_failure_is_refused_and_every_fetched_body_is_kept_as_evidence(clean, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert wj.run(get=_fake_get_partial_failure(20, calls), sleep=lambda s: None) == 1
    run_id = _last_run_id(clean)
    status, stats, err = _last_run(clean)
    assert status == "failed" and "key hỏng" in err
    assert stats["tally"]["keys_failed"] == 20
    rows = None
    with clean.connect() as c:
        rows = c.execute(sa.text(
            "SELECT count(*) FROM staging.raw_payload"
            " WHERE source='wichart' AND meta->>'refused' = 'true' AND meta->>'run_id' = :rid"),
            {"rid": str(run_id)}).scalar()
    assert rows == 48
    assert _scalar(clean, "SELECT count(*) FROM macro.observation") == 0
    assert _scalar(clean, "SELECT count(*) FROM ops.data_domain_state WHERE source='wichart'") == 0


def test_keys_subset_writes_but_does_not_touch_domain_state(clean, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert wj.run(keys=["cpi", "vang"], get=_fake_get(calls), sleep=lambda s: None) == 0
    assert sorted(calls) == ["cpi", "vang"]
    _, stats, _ = _last_run(clean)
    assert stats["subset"] is True and stats["tally"]["keys_total"] == 2
    # vang.json: 522 điểm/series, bỏ 5 điểm T7/CN chép lại ⇒ 517 × 2 — đếm bằng script độc lập, ghi ở ledger
    assert _scalar(clean, "SELECT count(*) FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                          " WHERE a.code IN ('gold.sjc_buy','gold.sjc_sell')") == 1034
    assert _scalar(clean, "SELECT count(*) FROM ops.data_domain_state WHERE source='wichart'") == 0


def test_dry_run_writes_nothing_but_records_the_run(clean, monkeypatch):
    _wire(monkeypatch)
    assert wj.run(dry_run=True, get=_fake_get(), sleep=lambda s: None) == 0
    status, stats, _ = _last_run(clean)
    assert status == "success" and stats["dry_run"] is True and stats["tally"]["series_ok"] == 105
    assert _scalar(clean, "SELECT count(*) FROM macro.observation") == 0
    assert _scalar(clean, "SELECT count(*) FROM staging.raw_payload WHERE source='wichart'") == 0
    # dry-run không gọi load_registry — kho vừa được _cleanup dọn nên phải là 0, không phải "ổn định"
    assert _scalar(clean, "SELECT count(*) FROM macro.indicator_source WHERE source='wichart'") == 0
    assert _scalar(clean, "SELECT count(*) FROM asset.asset_external_id WHERE source='wichart'") == 0
    assert wj.run(dry_run=True, get=_fake_get(), sleep=lambda s: None) == 0
    assert _scalar(clean, "SELECT count(*) FROM macro.indicator_source WHERE source='wichart'") == 0


def test_unknown_key_is_an_error_before_any_call(clean, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert wj.run(keys=["cpi", "khong_co"], get=_fake_get(calls), sleep=lambda s: None) == 2
    assert calls == []


INTRADAY_KEYS = sorted({s.key for s in wr.build() if s.freq == "d"})


def test_intraday_run_hits_only_the_47_daily_keys_guards_and_leaves_domain_state_alone(clean, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert wj.run(intraday=True, get=_fake_get(calls), sleep=lambda s: None) == 0
    assert sorted(set(calls)) == INTRADAY_KEYS and len(INTRADAY_KEYS) == 47 and "cpi" not in calls and "dhtg" in calls and "lslnh" in calls
    status, stats, _ = _last_run(clean)
    assert status == "success" and stats["intraday"] is True and "watermark" not in stats and "subset" not in stats
    assert stats["tally"]["keys_total"] == 47 and stats["tally"]["series_ok"] == 61 and stats["payloads_stored"] == 0
    assert _scalar(clean, "SELECT count(*) FROM ops.data_domain_state WHERE source='wichart'") == 0
    assert _scalar(clean, "SELECT count(*) FROM staging.raw_payload WHERE source='wichart'") == 0
    assert _scalar(clean, "SELECT value FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                          " WHERE a.code='gold.sjc_buy' AND obs_date='2026-09-04'") == Decimal("145600000")
    assert _scalar(clean, "SELECT count(*) FROM macro.observation o JOIN macro.indicator i USING (indicator_id) WHERE i.code='vn.cpi'") == 0


def test_intraday_run_is_guarded_like_a_full_run(clean, monkeypatch):
    _wire(monkeypatch)
    bad = {"dau_wti", "bac", "dong", "kem"}                                             # 4 series đơn / 61 = 6,6 % > 5 %

    def get(u, timeout):
        key = u.rsplit("name=", 1)[1]
        if key in bad:
            return 200, json.dumps({"title": key, "chart": {}})                       # không có chart.series ⇒ bad_shape
        return _fake_get()(u, timeout)
    assert wj.run(intraday=True, get=get, sleep=lambda s: None) == 1
    status, stats, err = _last_run(clean)
    assert status == "failed" and "sai hình dạng" in err and stats["tally"]["keys_bad_shape"] == 4
    assert _scalar(clean, "SELECT count(*) FROM asset.price_daily") == 0


def test_intraday_with_keys_is_an_error_before_any_call(clean, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert wj.run(keys=["vang"], intraday=True, get=_fake_get(calls), sleep=lambda s: None) == 2
    assert calls == [] and _last_run(clean)[0] == "failed"
