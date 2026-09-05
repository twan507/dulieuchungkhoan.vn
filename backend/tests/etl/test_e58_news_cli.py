"""CLI `etl news`: cờ thu thập, vòng lặp, backfill sitemap (Task 5 nối thêm)."""
import pytest

import etl.__main__ as m


def test_news_flags_reach_run(monkeypatch):
    import etl.news_job
    seen = {}
    monkeypatch.setattr(etl.news_job, "run", lambda **kw: seen.update(kw) or 0)
    assert m.main(["news", "--loop", "--minutes", "90", "--sources", "cafef,bnews"]) == 0
    assert seen == {"sources": ["cafef", "bnews"], "dry_run": False, "loop": True, "minutes": 90.0}
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
    assert seen == {"from_month": "2026-08", "to_month": "2026-09", "max_minutes": 30.0, "stop_before_open": True}
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
