"""CLI `etl news`: cờ thu thập, vòng lặp, backfill sitemap (Task 5 nối thêm)."""
import pytest

import etl.__main__ as m


def test_news_flags_reach_run(monkeypatch):
    import etl.news_job
    seen = {}
    monkeypatch.setattr(etl.news_job, "run", lambda **kw: seen.update(kw) or 0)
    assert m.main(["news", "--loop", "--minutes", "90", "--sources", "cafef,bnews"]) == 0
    assert seen == {"sources": ["cafef", "bnews"], "dry_run": False, "loop": True, "minutes": 90.0, "classify_per_cycle": None}
    assert m.main(["news", "--dry-run"]) == 0 and seen["dry_run"] is True and seen["loop"] is False and seen["minutes"] is None


def test_minutes_requires_loop():
    with pytest.raises(SystemExit) as e:
        m.main(["news", "--minutes", "5"])
    assert e.value.code == 2


def test_backfill_flags_and_exclusions(monkeypatch):
    import etl.news_job
    seen = {}
    monkeypatch.setattr(etl.news_job, "run_backfill", lambda **kw: seen.update(kw) or 0)
    assert m.main(["news", "--backfill-sitemap", "--from", "2026-08", "--to", "2026-09", "--max-minutes", "30", "--stop-before-open"]) == 0
    assert seen == {"from_month": "2026-08", "to_month": "2026-09", "max_minutes": 30.0, "stop_before_open": True,
                     "source": "tinnhanhck"}
    for bad in (["news", "--backfill-sitemap"], ["news", "--backfill-sitemap", "--from", "2026-8"],
                ["news", "--backfill-sitemap", "--from", "2026-08", "--loop"],
                ["news", "--backfill-sitemap", "--from", "2026-08", "--minutes", "5"]):     # M4
        with pytest.raises(SystemExit) as e:
            m.main(bad)
        assert e.value.code == 2


def test_backfill_only_flags_require_backfill_sitemap():
    # M4: --to/--max-minutes/--stop-before-open không có --backfill-sitemap ⇒ lỗi (không âm thầm bị bỏ qua).
    for bad in (["news", "--to", "2026-09"], ["news", "--max-minutes", "30"], ["news", "--stop-before-open"]):
        with pytest.raises(SystemExit) as e:
            m.main(bad)
        assert e.value.code == 2


def test_backfill_source_flag(monkeypatch):
    import etl.news_job
    seen = {}
    monkeypatch.setattr(etl.news_job, "run_backfill", lambda **kw: seen.update(kw) or 0)
    assert m.main(["news", "--backfill-sitemap", "--source", "bnews", "--from", "2026-08", "--to", "2026-08"]) == 0
    assert seen["source"] == "bnews" and seen["from_month"] == "2026-08"
    assert m.main(["news", "--backfill-sitemap", "--source", "nguoiquansat", "--from", "2024-01"]) == 0 and seen["source"] == "nguoiquansat"
    for bad in (["news", "--backfill-sitemap", "--source", "cafef", "--from", "2026-08"],       # không có sitemap
                ["news", "--source", "bnews"],                                                 # --source chỉ đi cùng --backfill-sitemap
                ["news", "--loop", "--source", "bnews"]):
        with pytest.raises(SystemExit) as e:
            m.main(bad)
        assert e.value.code == 2


def test_classify_flag_requires_loop_and_positive(monkeypatch):
    # Lưới trong vòng lặp MẶC ĐỊNH TẮT (chủ dự án chưa bật live) — chỉ chạy khi truyền --classify N với --loop
    import etl.news_job
    seen = {}
    monkeypatch.setattr(etl.news_job, "run", lambda **kw: seen.update(kw) or 0)
    assert m.main(["news", "--loop", "--classify", "20"]) == 0 and seen["classify_per_cycle"] == 20
    assert m.main(["news", "--loop"]) == 0 and seen["classify_per_cycle"] is None
    for bad in (["news", "--classify", "20"], ["news", "--loop", "--classify", "0"], ["news", "--loop", "--dry-run", "--classify", "5"],
                ["news", "--backfill-sitemap", "--from", "2026-08", "--classify", "5"]):
        with pytest.raises(SystemExit) as e:
            m.main(bad)
        assert e.value.code == 2
