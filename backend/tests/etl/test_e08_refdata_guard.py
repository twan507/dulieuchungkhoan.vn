from etl.refdata_guard import check

IDX = frozenset({"A", "B", "C"})

def _ok(v): return v.ok and v.reasons == ()

def test_tier1_ratio_boundary():
    base = {"quotes": 1000, "organization": 500, "icb": 176}
    # 979/1000 = sụt 2,1% > 2% → từ chối; 981 = 1,9% → qua
    assert not _ok(check({"quotes": 979, "organization": 500, "icb": 176}, base, IDX, IDX, 0, 2000))
    assert _ok(check({"quotes": 981, "organization": 500, "icb": 176}, base, IDX, IDX, 0, 2000))

def test_first_run_without_baseline_passes_ratio_but_still_checks_index_set():
    assert _ok(check({"quotes": 5}, None, IDX, IDX, 0, 0))
    v = check({"quotes": 5}, None, frozenset({"A", "B"}), IDX, 0, 0)
    assert not v.ok and any("C" in r for r in v.reasons)

def test_tier2_delist_boundary():
    # 21/2000 = 1,05% > 1% → từ chối; 19/2000 = 0,95% → qua
    assert not _ok(check({}, None, IDX, IDX, 21, 2000))
    assert _ok(check({}, None, IDX, IDX, 19, 2000))
    assert _ok(check({}, None, IDX, IDX, 0, 0))       # kho rỗng lần đầu

def test_real_weekly_drift_passes():
    # nhịp thật đo được: 2.530 → 2.534 trong 5 ngày; chiều sụt tương đương 4/2530 ≈ 0,16%
    assert _ok(check({"quotes": 2526}, {"quotes": 2530}, IDX, IDX, 4, 2000))
