"""Giãn cách ngẫu nhiên đều [1, 5] s giữa hai lời gọi liên tiếp cùng Fetcher, kể cả lần thử lại (spec lát 7b §5.1, §4.6-III)."""
import random

import httpx
import pytest

from etl import http_fetch as hf


def _ok(http, text):
    return ("ok", {"t": text}) if http == 200 else ("retry", None)


class _Rng:
    """rng giả: trả lần lượt các giá trị đã định, ghi lại (a, b) được hỏi."""
    def __init__(self, values):
        self.values, self.seen = list(values), []

    def uniform(self, a, b):
        self.seen.append((a, b))
        return self.values.pop(0)


def test_no_gap_before_the_first_call_and_one_gap_between_two_calls():
    slept = []
    f = hf.Fetcher(lambda u, t: (200, "a", {}), _ok, sleep=slept.append, rng=_Rng([1.0, 4.99]))
    f.fetch_one("u1", "a")
    assert slept == [] and f.gaps == []
    f.fetch_one("u2", "b")
    assert slept == [1.0] and f.gaps == [1.0] and f._rng.seen == [(1.0, 5.0)]


def test_retry_sleeps_backoff_then_a_gap_before_the_next_attempt():
    answers = [(500, "boom", {}), (200, "ok", {})]
    slept = []
    f = hf.Fetcher(lambda u, t: answers.pop(0), _ok, sleep=slept.append, rng=_Rng([3.2]))
    doc, text = f.fetch_one("u", "x")
    assert text == "ok" and slept == [2, 3.2] and f.calls == 2 and f.retries_done == 1 and f.gaps == [3.2]


def test_real_rng_stays_inside_one_to_five_and_is_not_constant():
    f = hf.Fetcher(lambda u, t: (200, "a", {}), _ok, sleep=lambda s: None, rng=random.Random(0))
    for i in range(21):
        f.fetch_one(f"u{i}", "a")
    assert len(f.gaps) == 20 and all(1.0 <= g <= 5.0 for g in f.gaps) and len(set(f.gaps)) > 1


def test_transport_error_walks_the_retry_path_with_backoff_and_gaps():
    def get(u, t):
        raise httpx.ReadTimeout("slow")
    slept = []
    f = hf.Fetcher(get, _ok, sleep=slept.append, rng=_Rng([1.5, 2.5, 3.5]))
    with pytest.raises(hf.FetchError, match="x hỏng sau 4 lần"):
        f.fetch_one("u", "x")
    assert slept == [2, 1.5, 4, 2.5, 8, 3.5] and f.calls == 4 and f.retries_done == 3


def test_open_fetcher_passes_rng_and_no_longer_accepts_min_interval():
    with hf.open_fetcher(_ok, get=lambda u, t: (200, "a", {}), sleep=lambda s: None, rng=_Rng([2.0])) as f:
        f.fetch_one("u1", "a")
        f.fetch_one("u2", "a")
        assert f.gaps == [2.0]
    with pytest.raises(TypeError):
        with hf.open_fetcher(_ok, get=lambda u, t: (200, "a", {}), min_interval=0.5):
            pass
