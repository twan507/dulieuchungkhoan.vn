from datetime import datetime, timezone


def heartbeat(now: datetime) -> str:
    return f"[etl] alive at {now.astimezone(timezone.utc).isoformat()}"
