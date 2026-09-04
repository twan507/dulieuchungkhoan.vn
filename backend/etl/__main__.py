import argparse
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
    if args[0] == "refdata":
        import etl.refdata_job
        parser = argparse.ArgumentParser(prog="etl refdata")
        parser.add_argument("--accept-drop", action="store_true")
        parsed = parser.parse_args(args[1:])
        return etl.refdata_job.run(accept_drop=parsed.accept_drop)
    if args[0] == "screener":
        import etl.screener_job
        return etl.screener_job.run()
    if args[0] == "events":
        import etl.events_job
        parser = argparse.ArgumentParser(prog="etl events")
        parser.add_argument("--accept-new", action="store_true")
        parsed = parser.parse_args(args[1:])
        return etl.events_job.run(accept_new=parsed.accept_new)
    if args[0] == "price":
        import etl.price_job
        parser = argparse.ArgumentParser(prog="etl price")
        parser.add_argument("--backfill", action="store_true")
        parser.add_argument("--codes", type=lambda s: [t.strip().upper() for t in s.split(",") if t.strip()])
        parser.add_argument("--max-minutes", type=float, dest="max_minutes")
        parser.add_argument("--stop-before-open", action="store_true", dest="stop_before_open")
        parsed = parser.parse_args(args[1:])
        return etl.price_job.run(backfill=parsed.backfill, codes=parsed.codes,
                                 max_minutes=parsed.max_minutes,
                                 stop_before_open=parsed.stop_before_open)
    print(f"etl: subcommand không hợp lệ: {args[0]!r} (hỗ trợ: omo, refdata, screener, events, price)",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
