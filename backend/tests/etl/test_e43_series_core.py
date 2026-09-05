"""Lõi chung của lát 7: registry theo source, apply/apply_ohlc, guard hai chế độ, runner. DB thật (fixture `db` rollback)."""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa

from etl import registry as rg
from etl import series_store as ss
from etl import wichart_registry as wr
from etl import wichart_store as ws
from etl.registry import Bar, Point, Series


def _count(db, sql, **p):
    return db.execute(sa.text(sql), p).scalar()


FAKE = [
    Series(source="zz", external_key="DGS10", domain="macro", code="zz.yield.10y", name_vi="ZZ 10y", unit="%", freq="d",
           region="us", band=(Decimal(-1), Decimal(25))),
    Series(source="zz", external_key="DCOILWTICO", domain="asset", code="wti", name_vi="Giá dầu WTI giao ngay", unit="USD/thùng",
           freq="d", region="us", asset_class="commodity", quote_currency="USD", price_type="spot", calendar="trading_days",
           band=(Decimal(5), Decimal(500)), max_lag_days=10),
    Series(source="zz", external_key="^GSPC", domain="asset", code="zz.idx.sp500", name_vi="ZZ S&P", unit="điểm", freq="d",
           region="us", asset_class="index", quote_currency="USD", calendar="trading_days", shape="ohlc",
           band=(Decimal(700), Decimal(80000)), max_lag_days=14, extra={"tz": "America/New_York"}),
]


def test_load_registry_scoped_by_source_reuses_wti_asset_and_leaves_wichart_rows_alone(db):
    ws.load_registry(db, wr.build())                                    # 53 + 52 dòng wichart có trước
    wti_id = _count(db, "SELECT asset_id FROM asset.asset WHERE code='wti'")
    resolved, stats = rg.load_registry(db, FAKE, "zz")
    assert stats == {"macro": 1, "asset": 2, "removed": 0}
    assert resolved["wti"].row_id == wti_id and resolved["wti"].price_type == "spot"   # cùng asset_id, thêm dòng ánh xạ
    assert resolved["zz.idx.sp500"].price_type is None and resolved["zz.yield.10y"].domain == "macro"
    assert _count(db, "SELECT count(*) FROM asset.asset_external_id WHERE asset_id=:a", a=wti_id) == 2   # wichart + zz
    assert _count(db, "SELECT count(*) FROM macro.indicator_source WHERE source='wichart'") == 53
    assert _count(db, "SELECT count(*) FROM asset.asset_external_id WHERE source='wichart'") == 52
    row = db.execute(sa.text("SELECT meta->>'max_lag_days', meta->'band', meta->>'tz' FROM asset.asset_external_id"
                             " WHERE source='zz' AND external_code='^GSPC'")).one()
    assert tuple(row) == ("14", ["700", "80000"], "America/New_York")
    _, stats2 = rg.load_registry(db, FAKE[:2], "zz")                     # bỏ 1 series: xoá đúng dòng của zz
    assert stats2["removed"] == 1
    assert _count(db, "SELECT count(*) FROM asset.asset_external_id WHERE source='wichart'") == 52


def test_apply_reports_a_sample_of_changed_rows_with_old_and_new_values(db):
    resolved, _ = rg.load_registry(db, FAKE, "zz")
    pts = [Point("macro", "zz.yield.10y", date(2026, 9, 2), Decimal("4.79"), None),
           Point("macro", "zz.yield.10y", date(2026, 9, 3), Decimal("4.77"), None),
           Point("asset", "wti", date(2026, 9, 1), Decimal("91.48"), "spot")]
    w = ss.apply(db, pts, resolved)
    assert (w.inserted, w.changed, w.changes_sample) == (3, 0, [])
    w = ss.apply(db, pts, resolved)
    assert (w.inserted, w.changed, w.changes_sample) == (0, 0, [])
    pts[0] = Point("macro", "zz.yield.10y", date(2026, 9, 2), Decimal("4.80"), None)      # vá hồi tố
    w = ss.apply(db, pts, resolved)
    assert (w.inserted, w.changed) == (0, 1)
    assert w.changes_sample == [("zz.yield.10y", "2026-09-02", Decimal("4.79"), Decimal("4.80"))]
    assert _count(db, "SELECT count(*) FROM asset.price_daily p JOIN asset.asset a USING (asset_id)"
                      " WHERE a.code='wti' AND price_type='spot'") == 1
    pts[2] = Point("asset", "wti", date(2026, 9, 1), Decimal("92.00"), "spot")     # đổi giá trị wti spot
    w = ss.apply(db, pts, resolved)
    assert (w.inserted, w.changed) == (0, 1)
    assert w.changes_sample == [("wti", "2026-09-01", Decimal("91.48"), Decimal("92.00"))]


def test_apply_ohlc_upserts_only_when_a_field_changes_and_keeps_close_when_close_adj_changes(db):
    resolved, _ = rg.load_registry(db, FAKE, "zz")
    bar = Bar("zz.idx.sp500", date(2026, 9, 4), Decimal("7750.19"), Decimal("7760"), Decimal("7700"), Decimal("7718.60"),
              Decimal("7718.60"), Decimal("4103570000"))
    w = ss.apply_ohlc(db, [bar], resolved)
    assert (w.inserted, w.changed) == (1, 0)
    ts1 = _count(db, "SELECT max(ingested_at) FROM asset.ohlc_daily")
    w = ss.apply_ohlc(db, [bar], resolved)
    assert (w.inserted, w.changed) == (0, 0)
    assert _count(db, "SELECT max(ingested_at) FROM asset.ohlc_daily") == ts1
    w = ss.apply_ohlc(db, [Bar("zz.idx.sp500", date(2026, 9, 4), Decimal("7750.19"), Decimal("7760"), Decimal("7700"),
                              Decimal("7718.60"), Decimal("7700.00"), Decimal("4103570000"))], resolved)
    assert (w.inserted, w.changed) == (0, 1)
    row = db.execute(sa.text("SELECT close, close_adj FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id)"
                             " WHERE a.code='zz.idx.sp500'")).one()
    assert tuple(row) == (Decimal("7718.60"), Decimal("7700.00"))          # seam 3 bước 5: close giữ nguyên


def test_wichart_store_still_works_through_the_shared_core(db):
    resolved, stats = ws.load_registry(db, wr.build())
    assert stats == {"macro": 53, "asset": 52, "removed": 0} and resolved["wti"].price_type == "futures"
    w = ws.apply(db, [Point("asset", "wti", date(2026, 9, 4), Decimal("62.1"), "futures")], resolved)
    assert (w.inserted, w.changed) == (1, 0)


def test_core_works_under_etl_role_including_ohlc_daily(db):
    db.execute(sa.text("SET LOCAL ROLE dlck_etl"))
    resolved, _ = rg.load_registry(db, FAKE, "zz")
    assert ss.apply(db, [Point("macro", "zz.yield.10y", date(2026, 9, 3), Decimal("4.77"), None)], resolved).inserted == 1
    assert ss.apply(db, [Point("asset", "wti", date(2026, 9, 1), Decimal("91.48"), "spot")], resolved).inserted == 1
    assert ss.apply_ohlc(db, [Bar("zz.idx.sp500", date(2026, 9, 4), None, None, None, Decimal("7718.6"), None, None)], resolved).inserted == 1
    assert ss.apply_ohlc(db, [Bar("zz.idx.sp500", date(2026, 9, 4), None, None, None, Decimal("7720.0"), None, None)], resolved).changed == 1


# ---- guard ----
from etl import series_guard as sg  # noqa: E402


def test_guard_all_or_nothing_refuses_on_a_single_stale_series():
    t = sg.Tally(total=15, ok=14, stale=1, details=["DTWEXBGS stale: 2026-08-28 < 2026-09-03"])
    v = sg.check(t, "all_or_nothing")
    assert not v.ok and "DTWEXBGS" in v.reasons[0]
    assert sg.check(sg.Tally(total=15, ok=15), "all_or_nothing").ok


def test_guard_ratio_uses_min_sample_and_per_kind_caps():
    assert sg.check(sg.Tally(total=37, ok=36, shape=1), "ratio").ok                   # 2,7 % ≤ 5 %
    assert not sg.check(sg.Tally(total=37, ok=35, shape=2), "ratio").ok               # 5,4 % > 5 %
    assert not sg.check(sg.Tally(total=37, ok=29, stale=8), "ratio").ok               # 21,6 % > 20 %
    assert sg.check(sg.Tally(total=37, ok=30, stale=7), "ratio").ok                   # 18,9 %
    assert sg.check(sg.Tally(total=19, ok=10, failed=9), "ratio").ok                  # dưới MIN_SAMPLE: không xét
    assert not sg.check(sg.Tally(total=20, ok=15, failed=5), "ratio").ok              # 25 % > 20 %


# ---- runner: một nguồn giả trọn vòng (engine thật, dọn theo source 'zz') ----
import os  # noqa: E402

from etl import series_job as sj  # noqa: E402


def _cleanup_zz(engine):
    with engine.begin() as c:
        c.execute(sa.text("DELETE FROM macro.observation WHERE indicator_id IN (SELECT indicator_id FROM macro.indicator_source WHERE source='zz')"))
        c.execute(sa.text("DELETE FROM asset.price_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='zz')"
                          " AND price_type = 'spot'"))   # 'wti' dùng chung: không đụng dòng 'futures' của wichart
        c.execute(sa.text("DELETE FROM asset.ohlc_daily WHERE asset_id IN (SELECT asset_id FROM asset.asset_external_id WHERE source='zz')"))
        c.execute(sa.text("DELETE FROM staging.raw_payload WHERE source='zz'"))
        c.execute(sa.text("DELETE FROM ops.etl_run WHERE job='global.zz'"))
        c.execute(sa.text("DELETE FROM ops.data_domain_state WHERE source='zz'"))
        c.execute(sa.text("DELETE FROM macro.indicator_source WHERE source='zz'"))
        c.execute(sa.text("DELETE FROM asset.asset_external_id WHERE source='zz'"))
        c.execute(sa.text("DELETE FROM macro.indicator WHERE code='zz.yield.10y'"))
        c.execute(sa.text("DELETE FROM asset.asset WHERE code='zz.idx.sp500'"))
        # 'wti' dùng chung với wichart: chỉ xoá khi không còn dòng ánh xạ nào trỏ tới — để lại là test_s06_asset
        # (literal 'wti') vỡ UNIQUE(code) khi chạy cả bộ (cùng bẫy I6 lát 6)
        c.execute(sa.text("DELETE FROM asset.asset a WHERE a.code='wti'"
                          " AND NOT EXISTS (SELECT 1 FROM asset.asset_external_id x WHERE x.asset_id = a.asset_id)"))


@pytest.fixture()
def zz(migrated_engine):
    _cleanup_zz(migrated_engine)
    yield migrated_engine
    _cleanup_zz(migrated_engine)


def _fake_fetch_all(series, get, sleep, backfill, intraday=False):
    docs = {s.external_key: {"k": s.external_key} for s in series}
    return docs, {k: '{"k": "%s"}' % k for k in docs}, [], len(docs), 0


def _fake_normalize(s, doc, now):
    if s.shape == "ohlc":
        return [Bar(s.code, date(2026, 9, 4), None, None, None, Decimal("7718.6"), Decimal("7718.6"), None)]
    if s.external_key == "DGS10":
        return [Point("macro", s.code, date(2026, 9, 3), Decimal("4.77"), None)]
    return [Point("asset", s.code, date(2026, 9, 1), Decimal("91.48"), "spot")]


def _spec(normalize=_fake_normalize, mode="all_or_nothing", supports_backfill=False):
    return sj.SourceSpec(job="global.zz", source="zz", domains=("macro.indicator", "asset"), guard_mode=mode,
                         log_name="zz", build=lambda: FAKE, fetch_all=_fake_fetch_all, normalize=normalize,
                         supports_backfill=supports_backfill)


def _wire(monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("etl.series_job.load_dotenv", lambda *a, **k: None)


def _last_run(engine, job="global.zz"):
    with engine.connect() as c:
        return c.execute(sa.text("SELECT status, stats, error FROM ops.etl_run WHERE job=:j ORDER BY run_id DESC LIMIT 1"), {"j": job}).one()


def test_runner_full_run_writes_points_and_bars_and_two_domain_states(zz, monkeypatch):
    _wire(monkeypatch)
    now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    assert sj.run(_spec(), get=lambda u, t: (200, "{}", {}), sleep=lambda s: None, now=now) == 0
    status, stats, _ = _last_run(zz)
    assert status == "success" and stats["registry"] == {"macro": 1, "asset": 2, "removed": 0}
    assert (stats["inserted"], stats["changed"], stats["points"], stats["bars"]) == (3, 0, 2, 1)
    assert stats["tally"]["ok"] == 3 and stats["watermark"] == "2026-09-05"
    with zz.connect() as c:
        rows = dict(c.execute(sa.text("SELECT domain, watermark FROM ops.data_domain_state WHERE source='zz'")).all())
        n = c.execute(sa.text("SELECT count(*) FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id) WHERE a.code='zz.idx.sp500'")).scalar()
    assert rows == {"macro.indicator": "2026-09-05", "asset": "2026-09-05"} and n == 1
    assert sj.run(_spec(), get=lambda u, t: (200, "{}", {}), sleep=lambda s: None, now=now) == 0
    assert (_last_run(zz)[1]["inserted"], _last_run(zz)[1]["changed"]) == (0, 0)


def _backfill_normalize(s, doc, now):
    if s.shape == "ohlc":
        return [Bar(s.code, date(2026, 9, 4), None, None, None, Decimal("7718.6"), Decimal("7718.6"), None)]
    if s.external_key == "DGS10":
        return [Point("macro", s.code, date(2026, 9, 3), Decimal("4.77"), None)]
    return []                                   # 'wti': không sinh điểm nào trong hai test backfill dưới đây


def test_backfill_writes_one_transaction_per_code_and_reports_the_backfill_flag(zz, monkeypatch):
    _wire(monkeypatch)
    now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    assert sj.run(_spec(_backfill_normalize, supports_backfill=True), backfill=True,
                  get=lambda u, t: (200, "{}", {}), sleep=lambda s: None, now=now) == 0
    status, stats, _ = _last_run(zz)
    assert status == "success" and stats["backfill"] is True
    assert (stats["inserted"], stats["changed"]) == (2, 0)      # 1 bar (zz.idx.sp500) + 1 điểm macro (zz.yield.10y)


def test_backfill_per_code_transaction_keeps_the_code_already_committed_when_a_later_code_fails(zz, monkeypatch):
    _wire(monkeypatch)
    now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)

    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr("etl.series_store.apply", boom)         # chỉ chặn apply() (điểm) — apply_ohlc() vẫn chạy thật
    assert sj.run(_spec(_backfill_normalize, supports_backfill=True), backfill=True,
                  get=lambda u, t: (200, "{}", {}), sleep=lambda s: None, now=now) == 2
    status, _, error = _last_run(zz)
    assert status == "failed" and "boom" in error
    with zz.connect() as c:
        n_bar = c.execute(sa.text("SELECT count(*) FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id)"
                                  " WHERE a.code='zz.idx.sp500'")).scalar()
        n_macro = c.execute(sa.text("SELECT count(*) FROM macro.observation o JOIN macro.indicator i USING (indicator_id)"
                                    " WHERE i.code='zz.yield.10y'")).scalar()
    assert n_bar == 1 and n_macro == 0           # mã 'zz.idx.sp500' (< 'zz.yield.10y') đã commit riêng trước khi vỡ


def test_runner_intraday_passes_the_flag_to_fetch_all_and_still_pushes_the_watermark(zz, monkeypatch):
    _wire(monkeypatch)
    seen = []

    def fa(series, get, sleep, backfill, intraday):
        seen.append((backfill, intraday))
        return _fake_fetch_all(series, get, sleep, backfill, intraday)
    spec = _spec()
    spec.fetch_all, spec.supports_intraday = fa, True
    now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    assert sj.run(spec, intraday=True, get=lambda u, t: (200, "{}", {}), sleep=lambda s: None, now=now) == 0
    status, stats, _ = _last_run(zz)
    assert seen == [(False, True)] and status == "success" and stats["intraday"] is True and stats["watermark"] == "2026-09-05"
    with zz.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM ops.data_domain_state WHERE source='zz'")).scalar() == 2   # lượt trọn registry ⇒ đẩy mốc (spec §4.6-I)


def test_runner_rejects_intraday_when_unsupported_or_combined_with_backfill_before_open_run(zz, monkeypatch):
    _wire(monkeypatch)
    assert sj.run(_spec(), intraday=True, get=lambda u, t: (200, "{}", {}), sleep=lambda s: None) == 2
    spec = _spec(supports_backfill=True)
    spec.supports_intraday = True
    assert sj.run(spec, intraday=True, backfill=True, get=lambda u, t: (200, "{}", {}), sleep=lambda s: None) == 2
    with zz.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM ops.etl_run WHERE job='global.zz'")).scalar() == 0


def test_runner_refuses_whole_run_on_one_stale_series_and_keeps_evidence(zz, monkeypatch):
    _wire(monkeypatch)

    def stale_one(s, doc, now):
        if s.external_key == "DGS10":
            raise rg.SeriesError("stale", "DGS10 stale")
        return _fake_normalize(s, doc, now)
    assert sj.run(_spec(stale_one), get=lambda u, t: (200, "{}", {}), sleep=lambda s: None,
                  now=datetime(2026, 9, 5, tzinfo=timezone.utc)) == 1
    status, stats, error = _last_run(zz)
    assert status == "failed" and error.startswith("guard refused") and stats["tally"]["stale"] == 1
    with zz.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload WHERE source='zz' AND (meta->>'refused')::bool")).scalar() == 3
        assert c.execute(sa.text("SELECT count(*) FROM macro.indicator_source WHERE source='zz'")).scalar() == 0   # không ghi gì, kể cả registry


def test_runner_keys_subset_skips_guard_and_domain_state_and_dry_run_writes_nothing(zz, monkeypatch):
    _wire(monkeypatch)
    now = datetime(2026, 9, 5, tzinfo=timezone.utc)

    def stale_one(s, doc, now):
        if s.external_key == "DGS10":
            raise rg.SeriesError("stale", "DGS10 stale")
        return _fake_normalize(s, doc, now)
    assert sj.run(_spec(stale_one), keys=["^GSPC"], get=lambda u, t: (200, "{}", {}), sleep=lambda s: None, now=now) == 0
    status, stats, _ = _last_run(zz)
    assert status == "success" and stats["subset"] is True and "watermark" not in stats and stats["bars"] == 1
    with zz.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM ops.data_domain_state WHERE source='zz'")).scalar() == 0
        assert c.execute(sa.text("SELECT count(*) FROM macro.indicator_source WHERE source='zz'")).scalar() == 1   # registry vẫn nạp trọn
    n_before = _last_run(zz)[1]                                       # lượt con vừa ghi 1 nến; dry-run không được thêm gì
    assert sj.run(_spec(), dry_run=True, get=lambda u, t: (200, "{}", {}), sleep=lambda s: None, now=now) == 0
    status, stats, _ = _last_run(zz)
    assert status == "success" and stats["dry_run"] is True and "inserted" not in stats and n_before["bars"] == 1
    with zz.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM asset.ohlc_daily o JOIN asset.asset a USING (asset_id) WHERE a.code='zz.idx.sp500'")).scalar() == 1
        assert c.execute(sa.text("SELECT count(*) FROM macro.observation o JOIN macro.indicator i USING (indicator_id) WHERE i.code='zz.yield.10y'")).scalar() == 0


def test_runner_unknown_key_fails_before_any_call_and_ctrl_c_closes_the_run(zz, monkeypatch):
    _wire(monkeypatch)
    calls = []
    assert sj.run(_spec(), keys=["NOPE"], get=lambda u, t: (calls.append(u), (200, "{}", {}))[1], sleep=lambda s: None) == 2
    assert calls == [] and _last_run(zz)[0] == "failed"

    def boom(*a, **k):
        raise KeyboardInterrupt
    spec = _spec()
    spec.fetch_all = boom
    assert sj.run(spec, get=lambda u, t: (200, "{}", {}), sleep=lambda s: None) == 130
    assert _last_run(zz)[2] == "dừng tay (Ctrl+C)"
