from etl import wichart_guard as wg


def _t(**kw):
    base = dict(keys_total=68, keys_failed=0, keys_bad_shape=0, series_total=105,
                series_shape=0, series_freq=0, series_band=0, series_ok=105)
    base.update(kw)
    return wg.Tally(**base)


def test_clean_run_passes_and_zero_changes_is_not_an_error():
    assert wg.check(_t()).ok


def test_failed_keys_threshold_is_twenty_percent_inclusive():
    assert wg.check(_t(keys_total=20, keys_failed=4)).ok                       # 20 % — chưa vượt
    v = wg.check(_t(keys_total=20, keys_failed=5))                              # 25 %
    assert not v.ok and "hỏng" in v.reasons[0] and "5/20" in v.reasons[0]


def test_shape_and_band_thresholds_are_five_percent_of_series():
    assert wg.check(_t(series_total=20, series_shape=1)).ok
    assert not wg.check(_t(series_total=20, series_shape=2)).ok
    assert wg.check(_t(series_total=20, series_band=1)).ok
    v = wg.check(_t(series_total=20, series_band=2))
    assert not v.ok and "dải" in v.reasons[0]


def test_freq_drift_is_reported_not_refused():
    assert wg.check(_t(series_freq=50)).ok


def test_below_min_sample_nothing_refuses():
    assert wg.check(_t(keys_total=19, keys_failed=19, series_total=19, series_shape=19, series_band=19)).ok
