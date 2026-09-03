from datetime import date

from etl import price_guard as pg

TODAY = date(2026, 9, 4)
D = date(2026, 9, 3)
BASE = {"with_data": 1523, "latest_trading_date": "2026-09-03"}


def test_missing_codes_over_two_percent_are_refused_and_under_are_not():
    bad = pg.check(1523, 1492, invalid=21, failed=10, latest=D, today=TODAY, baseline=None)
    ok = pg.check(1523, 1493, invalid=20, failed=10, latest=D, today=TODAY, baseline=None)
    assert not bad.ok and "31/1523" in bad.reasons[0] and "21 mã sai" in bad.reasons[0]
    assert ok.ok


def test_drop_against_the_last_success_uses_two_percent():
    assert not pg.check(1523, 1480, 0, 0, D, TODAY, BASE).ok        # −2,8 %
    assert pg.check(1523, 1500, 0, 0, D, TODAY, BASE).ok             # −1,5 %


def test_future_or_regressing_latest_date_is_refused_with_the_dates_named():
    fut = pg.check(1523, 1523, 0, 0, date(2026, 9, 5), TODAY, BASE)
    back = pg.check(1523, 1523, 0, 0, date(2026, 9, 2), TODAY, BASE)
    assert not fut.ok and "2026-09-05" in fut.reasons[0] and "2026-09-04" in fut.reasons[0]
    assert not back.ok and "2026-09-02" in back.reasons[0] and "2026-09-03" in back.reasons[0]


def test_no_data_at_all_is_refused_even_without_a_baseline():
    v = pg.check(1523, 0, 0, 0, None, TODAY, None)
    assert not v.ok and "nguồn hỏng" in v.reasons[0]


def test_first_run_without_baseline_passes_on_clean_numbers():
    assert pg.check(1523, 1523, 0, 0, D, TODAY, None) == pg.GuardVerdict(True, ())
