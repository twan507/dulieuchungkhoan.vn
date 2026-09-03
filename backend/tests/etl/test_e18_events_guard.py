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


def test_all_families_empty_is_refused_even_with_no_baseline():
    """Vế (0). Lượt ĐẦU TIÊN chưa có mốc nên vế (ii) không bắt được ca này; lọt qua thì
    `rows` rỗng và `max()` tính watermark ném ValueError — lượt bị ghi `failed` với lý do
    sai hoàn toàn. Chặn ở guard thì thông điệp nói đúng chuyện gì xảy ra."""
    v = eg.check(counts={"AGM": 0, "IPO": 0}, collected={"AGM": 0, "IPO": 0}, baseline=None,
                 issuers_new=0, dup_conflicts=0, rows_kept=0)
    assert v.ok is False and "cả sáu họ trả 0" in v.reasons[0]


def test_one_family_empty_is_not_enough_to_refuse_on_rule_zero():
    """Biên đúng chiều: chỉ TỔNG bằng 0 mới là nguồn hỏng. Một họ rỗng mà họ khác có dữ
    liệu thì vế (0) im — nếu đó là thiếu trang thật thì vế (i) mới là vế bắt."""
    v = eg.check(counts={"AGM": 0, "IPO": 5}, collected={"AGM": 0, "IPO": 5}, baseline=None,
                 issuers_new=0, dup_conflicts=0, rows_kept=5)
    assert v.ok is True


def test_every_broken_rule_is_reported_not_just_the_first():
    v = _check(collected={"AGM": 99, "Earning": 199}, issuers_new=21)
    assert len(v.reasons) == 3 and v.families == ("AGM", "Earning")
