from etl import events_guard as eg

OK_COUNTS = {"AGM": 100, "Earning": 200}


def _check(**kw):
    args = dict(counts=OK_COUNTS, collected=dict(OK_COUNTS), baseline=None,
                issuers_new=0, dup_conflicts=0, rows_kept=300)
    args.update(kw)
    return eg.check(**args)


def test_clean_run_passes():
    assert _check().ok is True


def test_short_page_set_is_refused_and_names_the_family():
    v = _check(collected={"AGM": 99, "Earning": 200})
    assert v.ok is False and v.families == ("AGM",)
    assert "99" in v.reasons[0] and "100" in v.reasons[0]


def test_a_drop_smaller_than_two_percent_passes():
    # Earning MẤT 150 bản ghi trong 24 ngày (57.176 → 57.026) — biến động thật lớn nhất đo được
    v = eg.check(counts={"Earning": 57026}, collected={"Earning": 57026},
                 baseline={"Earning": 57176}, issuers_new=0, dup_conflicts=0, rows_kept=57026)
    assert v.ok is True                            # −0,26% < 2%


def test_a_drop_past_two_percent_is_refused():
    v = eg.check(counts={"Earning": 56000}, collected={"Earning": 56000},
                 baseline={"Earning": 57176}, issuers_new=0, dup_conflicts=0, rows_kept=56000)
    assert v.ok is False and v.families == ("Earning",)


def test_minting_too_many_issuers_is_refused_unless_accepted():
    assert _check(issuers_new=21).ok is False
    assert _check(issuers_new=20).ok is True                       # đúng mép
    assert _check(issuers_new=517, accept_new=True).ok is True     # lượt backfill có người nhìn


def test_duplicate_ratio_threshold():
    # Vùng thật đo được: 42/110.737 = 0,037%
    assert eg.check(counts=OK_COUNTS, collected=dict(OK_COUNTS), baseline=None, issuers_new=0,
                    dup_conflicts=42, rows_kept=110695).ok is True
    assert eg.check(counts=OK_COUNTS, collected=dict(OK_COUNTS), baseline=None, issuers_new=0,
                    dup_conflicts=600, rows_kept=109400).ok is False


def test_every_broken_rule_is_reported_not_just_the_first():
    v = _check(collected={"AGM": 99, "Earning": 199}, issuers_new=21)
    assert len(v.reasons) == 3 and v.families == ("AGM", "Earning")
