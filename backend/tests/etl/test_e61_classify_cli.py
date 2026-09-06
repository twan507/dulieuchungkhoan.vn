"""CLI `etl classify`: trần bắt buộc (mọi lượt tốn quota), --out chỉ đi với --dry-run, thinking hai giá trị."""
import pytest

import etl.__main__ as m


def test_classify_flags_reach_run(monkeypatch):
    import etl.news_classify
    seen = {}
    monkeypatch.setattr(etl.news_classify, "run", lambda **kw: seen.update(kw) or 0)
    assert m.main(["classify", "--per-group", "100"]) == 0
    assert seen == {"limit": None, "per_group": 100, "thinking": "adaptive", "dry_run": False, "out": None, "max_minutes": None, "cap": 3000, "ids": None}
    assert m.main(["classify", "--limit", "5", "--dry-run", "--out", "x.jsonl", "--thinking", "disabled", "--max-minutes", "2.5", "--cap-chars", "4000"]) == 0
    assert seen == {"limit": 5, "per_group": None, "thinking": "disabled", "dry_run": True, "out": "x.jsonl", "max_minutes": 2.5, "cap": 4000, "ids": None}


@pytest.mark.parametrize("bad", [["classify"], ["classify", "--limit", "5", "--per-group", "5"], ["classify", "--limit", "5", "--out", "x"],
                                 ["classify", "--limit", "5", "--thinking", "deep"], ["classify", "--limit", "0"]])
def test_classify_rejects_missing_or_conflicting_bounds(bad):
    with pytest.raises(SystemExit) as e:
        m.main(bad)
    assert e.value.code == 2


def test_ids_file_only_with_dry_run(monkeypatch, tmp_path):
    import json
    import etl.news_classify
    seen = {}
    monkeypatch.setattr(etl.news_classify, "run", lambda **kw: seen.update(kw) or 0)
    f = tmp_path / "ids.json"; f.write_text(json.dumps([7, 3, 11]), encoding="utf-8")
    assert m.main(["classify", "--dry-run", "--ids-file", str(f)]) == 0 and seen["ids"] == [7, 3, 11] and seen["limit"] is None
    for bad in (["classify", "--ids-file", str(f)], ["classify", "--dry-run", "--ids-file", str(f), "--limit", "5"]):
        with pytest.raises(SystemExit) as e:
            m.main(bad)
        assert e.value.code == 2
