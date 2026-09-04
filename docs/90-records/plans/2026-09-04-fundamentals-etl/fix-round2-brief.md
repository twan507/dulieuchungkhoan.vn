# Fix round 2 — slice 5 `etl fundamentals`

Repo `D:/twan_projects/dulieuchungkhoan.vn`, branch `feat/fundamentals-etl`, HEAD `de60dd9`. Work from `backend/`. Tests: `set -a; . ../.env; set +a; PYTHONIOENCODING=utf-8 uv run pytest <file> -q -p no:cacheprovider`. Never print `.env` values. Commit by path only; English commit messages ending with a blank line and `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. Vietnamese comments. TDD for finding B (RED then GREEN). One commit per finding (two commits).

A prior implementer did the first fix wave (report: `C:/Users/tuanb/AppData/Local/Temp/claude/D--twan-projects-dulieuchungkhoan-vn/ea5dca87-2629-4629-8834-652de7387c70/scratchpad/sdd/fix-wave-report.md`). You own round 2.

## Finding A — Important: three trigger tests are time bombs

`backend/tests/etl/test_e34_fundamentals_store.py` hard-codes `Earning` dates in September 2026 while `_checked(db, iid, kind, days_ago)` inserts `checked_at = now() - days_ago`. The new "served since publication" exclusion (`(checked_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date >= public_date`) therefore flips as the real clock advances:

- `test_due_list_trigger_fires_all_four_kinds_for_an_earning_after_the_watermark` — fails from 2026-10-03.
- `test_due_list_caps_the_trigger_branch_oldest_first` — fails from 2026-10-01.
- `test_trigger_skips_a_pair_already_checked_after_publication` — fails from 2026-09-11 (its "checked 10 days ago = before the 09-01 publication" premise).

Project rule (CLAUDE.md §4.4.4): acceptance criteria must stay true in three months on another machine.

**Fix:** derive every date in those three tests, and in `test_same_day_burst_is_served_across_runs_without_starving_anyone` and `test_due_list_merges_trigger_and_floor_into_one_target_per_issuer_and_kind`, from `TODAY = date.today()` (add `from datetime import date, timedelta` at the top; the DB and this machine are both on Asia/Ho_Chi_Minh, so a Python `date.today()` and the SQL VN date agree). Keep each test's semantics exactly:

- trigger_fires: A `Earning` at `TODAY - 1`, B at `TODAY - 40`, watermark `TODAY - 20`, checks `_checked(…, 10)` for both (checked 10 days ago = before A's publication, after B's — B is below the watermark anyway). Expect A × 4 kinds with `found_by == "event"`, B absent.
- caps_oldest_first: events at `TODAY - 3`, `TODAY - 2`, `TODAY - 1`, checks `_checked(…, 10)`, watermark `TODAY - 30`, `max_trigger=2` → `["ZZT0", "ZZT1"]`.
- skips_already_checked: `Earning` at `TODAY - 5`; `_checked(db, a, "bs", 0)` (today ≥ publication) → not due; then a second issuer with `_checked(…, 10)` (before publication) → due with `found_by == "event"`. (Use two issuers instead of mutating one check row, or delete and re-insert the check row — either is fine.)
- same_day_burst: `D = TODAY - 1`, watermark `TODAY - 30`; after "serving" two with `_checked(…, 0)`, second `plan_due` with watermark `D - 1 day` → only the third issuer; `new_watermark(db, None) == D`.
- merges_trigger_and_floor: `Earning` at `TODAY - 1`, watermark `TODAY - 30`.

Also make `test_new_watermark_is_the_latest_earning_public_date` relative (`TODAY - 1` for Earning, `TODAY` for the CashDividend row, expect `TODAY - 1`) so no hard-coded 2026 date remains in the trigger/watermark tests. Run the file; all tests must pass, and none may depend on the calendar.

## Finding B — Important (new contract, measured): `quarterly`/`yearly` can be `null`

Measured 2026-09-04 18:5x on `OrganCode=ASECO32`, all three statement endpoints: `"quarterly": null` with a normal `yearly` list, HTTP 200, `status "Success"`. The 09:5x survey sample of the same company had `"quarterly": []`. Same family as the `status` 0/"Success" trap — two serializations of "no data" from the same endpoint. Today `fundamentals_fetch.classify` returns `bad_shape` for `null`, so the AC4 run skipped A32 3/3 (`bad_shape: 3`) while the morning run had ingested it fine.

**Fix (TDD):**

1. Copy the captured raw response `C:/Users/tuanb/AppData/Local/Temp/claude/D--twan-projects-dulieuchungkhoan-vn/ea5dca87-2629-4629-8834-652de7387c70/scratchpad/sdd/A32-cf-quarterly-null.json` byte-for-byte into `backend/tests/etl/fixtures/fundamentals/A32-cf-quarterly-null.json`.
2. Add to `backend/tests/etl/test_e31_fundamentals_fetch.py`:

```python
def test_classify_reads_a_null_period_list_as_empty():
    """Đo 2026-09-04 18:5x: cùng A32, sáng nguồn trả "quarterly": [] (mẫu A32-cf.json), chiều trả
    "quarterly": null — hai cách tuần tự hoá của "không có kỳ quý", cùng họ với bẫy status 0/"Success".
    Coi null là rỗng; chỉ thiếu khoá hoặc kiểu khác list mới là bad_shape."""
    verdict, item = ff.classify("cf", 200, _text("A32-cf-quarterly-null.json"))
    assert verdict == "ok" and item["quarterly"] == [] and len(item["yearly"]) == 10
    assert ff.classify("cf", 200, '{"items": [{"quarterly": null, "yearly": null}], "status": "Success"}') == \
        ("ok", {"quarterly": [], "yearly": []})
    assert ff.classify("cf", 200, '{"items": [{"quarterly": "x", "yearly": []}], "status": "Success"}') == ("bad_shape", None)
    assert ff.classify("cf", 200, '{"items": [{"yearly": []}], "status": "Success"}') == ("bad_shape", None)
```

Run it: RED (`bad_shape` for the null case). Then change `classify` in `backend/etl/fundamentals_fetch.py` so that for statement kinds each of `quarterly`/`yearly` is normalised: key missing → `bad_shape`; value `None` → `[]`; value a list → kept; anything else → `bad_shape`. Return the normalised item (a fresh dict so the caller never sees `None`). Update the module docstring's measured-facts paragraph with the null observation and date. Run `test_e31` (all pass) and `test_e32` (unchanged, must still pass).

## Report

Append to `C:/Users/tuanb/AppData/Local/Temp/claude/D--twan-projects-dulieuchungkhoan-vn/ea5dca87-2629-4629-8834-652de7387c70/scratchpad/sdd/fix-wave-report.md` a "Fix round 2" section: per finding what changed, covering tests, commands, output (RED/GREEN for B). Finish by running `tests/etl` and `tests/schema` once and pasting totals. Reply with the short contract: Status, commits, one-line test summary, concerns, report path.
