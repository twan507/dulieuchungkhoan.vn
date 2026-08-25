from datetime import datetime, timezone

from etl.heartbeat import heartbeat


def test_heartbeat_formats_utc_iso():
    now = datetime(2026, 8, 24, 3, 0, 0, tzinfo=timezone.utc)
    assert heartbeat(now) == "[etl] alive at 2026-08-24T03:00:00+00:00"
