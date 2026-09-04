from etl import snapshot_guard as sg


def test_a_normal_run_passes():
    t = sg.Tally(attempted=234, floor_compared=200, changed_floor=3, changed_event=8, unchanged=220)
    assert sg.check(t).ok


def test_an_empty_due_list_is_success_not_failure():
    """Chốt (iv): không có mã nào tới hạn là chuyện bình thường, không phải lỗi."""
    v = sg.check(sg.Tally())
    assert v.ok and v.reasons == []


def test_too_many_floor_changes_refuse_the_run():
    """Tập trắng sai hoặc nguồn đổi cách tính trông y hệt 'cả sàn cùng công bố'."""
    t = sg.Tally(attempted=234, floor_compared=200, changed_floor=60)
    v = sg.check(t)
    assert not v.ok and any("đổi" in r for r in v.reasons)


def test_a_small_sample_does_not_trip_the_change_threshold():
    """§4.4.4: lượt --codes 3 mã mà 1 mã đổi là 33% — hệ thống chạy bình thường không được tự phạm luật."""
    assert sg.check(sg.Tally(attempted=3, floor_compared=3, changed_floor=1)).ok


def test_a_cold_start_run_does_not_trip_the_change_threshold():
    """Lượt đầu tiên: mọi mã là 'first', chưa có hash cũ để so ⇒ floor_compared = 0."""
    assert sg.check(sg.Tally(attempted=234, first=234, floor_compared=0)).ok


def test_too_many_failed_calls_refuse_the_run():
    t = sg.Tally(attempted=234, failed=60, floor_compared=170)
    v = sg.check(t)
    assert not v.ok and any("hỏng" in r for r in v.reasons)


def test_too_many_bad_shapes_refuse_the_run():
    t = sg.Tally(attempted=234, bad_shape=20, floor_compared=210)
    v = sg.check(t)
    assert not v.ok and any("hình dạng" in r for r in v.reasons)


def test_all_broken_reasons_are_reported_together():
    t = sg.Tally(attempted=234, failed=60, bad_shape=20, floor_compared=100, changed_floor=50)
    assert len(sg.check(t).reasons) == 3
