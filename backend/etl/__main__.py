import sys
import time
from datetime import datetime, timezone

from etl.heartbeat import heartbeat


def _heartbeat_loop() -> int:
    while True:
        print(heartbeat(datetime.now(timezone.utc)), flush=True)
        time.sleep(15)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        return _heartbeat_loop()          # giữ tương thích compose deploy/app
    if args[0] == "omo":
        import etl.omo_job
        return etl.omo_job.run()
    print(f"etl: subcommand không hợp lệ: {args[0]!r} (hỗ trợ: omo)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
