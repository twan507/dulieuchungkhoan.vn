from pathlib import Path
from unittest.mock import patch

import sqlalchemy as sa

from etl import omo_job

FIXTURE = (Path(__file__).parent / "fixtures" / "omo_page.html").read_text(encoding="utf-8")


def test_run_happy_path(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", str(migrated_engine.url.render_as_string(hide_password=False)))
    with patch("etl.omo_job.omo_fetch.fetch", return_value=FIXTURE):
        assert omo_job.run() == 0
    with migrated_engine.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM macro.omo_session")).scalar_one() == 1
        run_row = c.execute(sa.text(
            "SELECT status FROM ops.etl_run WHERE job='macro.omo_crawl'"
            " ORDER BY run_id DESC LIMIT 1")).scalar_one()
        assert run_row == "success"
        c.execute(sa.text("TRUNCATE macro.omo_flow, macro.omo_auction, macro.omo_session,"
                          " staging.raw_payload, ops.etl_run, ops.data_domain_state"))
        c.commit()


def test_run_waf_blocked_records_failed(migrated_engine, monkeypatch):
    monkeypatch.setenv("ETL_DATABASE_URL", str(migrated_engine.url.render_as_string(hide_password=False)))
    from etl.omo_fetch import WafBlocked
    with patch("etl.omo_job.omo_fetch.fetch", side_effect=WafBlocked("nghi chặn")):
        assert omo_job.run() != 0
    with migrated_engine.connect() as c:
        assert c.execute(sa.text(
            "SELECT status FROM ops.etl_run ORDER BY run_id DESC LIMIT 1")).scalar_one() == "failed"
        assert c.execute(sa.text("SELECT count(*) FROM staging.raw_payload")).scalar_one() == 0
        c.execute(sa.text("TRUNCATE ops.etl_run")); c.commit()
