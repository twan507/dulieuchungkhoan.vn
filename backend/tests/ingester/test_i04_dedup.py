from ingester.dedup import FrameDedup, Stamper, frame_key


def test_same_content_same_key_diff_content_diff_key():
    a = frame_key("t", {"SB": "ACV", "SM": "1"})
    assert a == frame_key("t", {"SM": "1", "SB": "ACV"})     # thứ tự khoá không đổi hash
    assert a != frame_key("t", {"SB": "ACV", "SM": "2"})
    assert a != frame_key("o", {"SB": "ACV", "SM": "1"})     # cùng payload khác event


def test_dedup_window():
    d = FrameDedup(window_s=10)
    k = frame_key("t", {"SM": "1"})
    assert d.seen(k, 100.0) is False
    assert d.seen(k, 105.0) is True          # trong cửa sổ → trùng
    assert d.seen(k, 200.0) is False         # ra ngoài cửa sổ → ghi lại (lưới block CH đỡ dưới)


def test_stamper_monotonic_per_symbol():
    s = Stamper()
    a = s.stamp("ACV", 1000)
    b = s.stamp("ACV", 1000)                 # cùng ms → +1
    c = s.stamp("ACV", 900)                  # đồng hồ lùi → vẫn tăng
    assert (a, b, c) == (1000, 1001, 1002)
    assert s.stamp("BID", 1000) == 1000      # mã khác độc lập
