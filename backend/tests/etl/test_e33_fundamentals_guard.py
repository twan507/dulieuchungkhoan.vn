from etl import fundamentals_guard as fg


def test_a_normal_run_passes():
    t = fg.Tally(attempted=80, checked=80, first=10, floor_compared=70, changed_floor=5, unchanged=65)
    assert fg.check(t).ok


def test_first_checks_do_not_count_as_changes():
    """Cold start: mọi mã đều 'first' — hệ thống chạy bình thường không được tự phạm luật (§4.4.4)."""
    t = fg.Tally(attempted=80, checked=80, first=80)
    assert fg.check(t).ok


def test_floor_change_rate_above_twenty_percent_refuses():
    t = fg.Tally(attempted=80, checked=80, floor_compared=80, changed_floor=17, unchanged=63)
    v = fg.check(t)
    assert not v.ok and "quét sàn" in v.reasons[0] and "21.2%" in v.reasons[0]


def test_floor_change_rate_needs_a_minimum_sample():
    t = fg.Tally(attempted=12, checked=12, floor_compared=12, changed_floor=12)     # lượt --codes 3 mã
    assert fg.check(t).ok


def test_failed_bad_shape_and_empty_each_have_their_own_gate():
    assert not fg.check(fg.Tally(attempted=40, failed=9)).ok            # 22.5 % > 20 %
    assert fg.check(fg.Tally(attempted=40, failed=8)).ok                # 20 % không vượt
    assert not fg.check(fg.Tally(attempted=40, bad_shape=3)).ok         # 7.5 % > 5 %
    assert not fg.check(fg.Tally(attempted=40, empty=3)).ok             # rỗng trên mã từng có dữ liệu
    assert fg.check(fg.Tally(attempted=40, empty=2)).ok
    v = fg.check(fg.Tally(attempted=40, failed=9, bad_shape=3, empty=3))
    assert len(v.reasons) == 3


def test_an_empty_due_list_is_a_success():
    assert fg.check(fg.Tally()).ok


def test_min_sample_boundary_is_inclusive_at_twenty():
    assert fg.check(fg.Tally(attempted=19, failed=19)).ok           # dưới cỡ mẫu ⇒ bỏ qua chốt
    assert not fg.check(fg.Tally(attempted=20, failed=19)).ok        # đạt cỡ mẫu ⇒ áp chốt
    assert fg.check(fg.Tally(floor_compared=19, changed_floor=19)).ok
    assert not fg.check(fg.Tally(floor_compared=20, changed_floor=19)).ok
