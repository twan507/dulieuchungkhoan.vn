from unittest.mock import patch

from etl.__main__ import main


def test_omo_subcommand_dispatches_to_job():
    with patch("etl.omo_job.run", return_value=0) as run:
        assert main(["omo"]) == 0
    run.assert_called_once()


def test_unknown_subcommand_exits_2():
    assert main(["gibberish"]) == 2


def test_cli_dispatches_refdata_with_accept_drop(monkeypatch):
    """Final review M2: nhánh CLI refdata + --accept-drop chưa từng có test."""
    import etl.__main__ as m
    calls = []
    import etl.refdata_job
    monkeypatch.setattr(etl.refdata_job, "run",
                        lambda accept_drop=False: calls.append(accept_drop) or 0)
    assert m.main(["refdata"]) == 0
    assert m.main(["refdata", "--accept-drop"]) == 0
    assert calls == [False, True]


def test_events_subcommand_passes_accept_new_through(monkeypatch, capsys):
    import etl.events_job
    from etl.__main__ import main
    seen = {}

    def fake_run(accept_new=False):
        seen["accept_new"] = accept_new
        return 0

    monkeypatch.setattr(etl.events_job, "run", fake_run)
    assert main(["events", "--accept-new"]) == 0 and seen["accept_new"] is True
    assert main(["events"]) == 0 and seen["accept_new"] is False
    assert main(["nope"]) == 2 and "events" in capsys.readouterr().err
