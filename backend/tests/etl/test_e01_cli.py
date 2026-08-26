from unittest.mock import patch

from etl.__main__ import main


def test_omo_subcommand_dispatches_to_job():
    with patch("etl.omo_job.run", return_value=0) as run:
        assert main(["omo"]) == 0
    run.assert_called_once()


def test_unknown_subcommand_exits_2():
    assert main(["gibberish"]) == 2
