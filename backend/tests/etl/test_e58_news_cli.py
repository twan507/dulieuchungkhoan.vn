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
