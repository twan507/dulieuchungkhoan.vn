import argparse
import sys
import time
from datetime import datetime, timezone

from core.console import lock_if_scheduled
from etl.heartbeat import heartbeat


def _heartbeat_loop() -> int:
    while True:
        print(heartbeat(datetime.now(timezone.utc)), flush=True)
        time.sleep(15)


def main(argv: list[str] | None = None) -> int:
    if lock_if_scheduled():           # cửa sổ task Interactive: bấm nhầm X không giết được job
        print("[dlck] nút X của cửa sổ đã khoá — dừng bằng Ctrl+C hoặc Stop-ScheduledTask", file=sys.stderr)
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
    if args[0] == "snapshot":
        import etl.snapshot_job
        parser = argparse.ArgumentParser(prog="etl snapshot")
        parser.add_argument("--codes", type=lambda s: [t.strip().upper() for t in s.split(",") if t.strip()])
        parser.add_argument("--kinds", type=lambda s: [k.strip() for k in s.split(",") if k.strip()])
        parser.add_argument("--max-minutes", type=float, dest="max_minutes")
        parsed = parser.parse_args(args[1:])
        return etl.snapshot_job.run(codes=parsed.codes, kinds=parsed.kinds,
                                    max_minutes=parsed.max_minutes)
    if args[0] == "fundamentals":
        import etl.fundamentals_job
        parser = argparse.ArgumentParser(prog="etl fundamentals")
        parser.add_argument("--codes", type=lambda s: [t.strip().upper() for t in s.split(",") if t.strip()])
        parser.add_argument("--kinds", type=lambda s: [k.strip() for k in s.split(",") if k.strip()])
        parser.add_argument("--max-minutes", type=float, dest="max_minutes")
        parser.add_argument("--backfill", action="store_true")
        parser.add_argument("--stop-before-open", action="store_true", dest="stop_before_open")
        parsed = parser.parse_args(args[1:])
        return etl.fundamentals_job.run(codes=parsed.codes, kinds=parsed.kinds, max_minutes=parsed.max_minutes,
                                        backfill=parsed.backfill, stop_before_open=parsed.stop_before_open)
    if args[0] == "wichart":
        import etl.wichart_job
        parser = argparse.ArgumentParser(prog="etl wichart")
        parser.add_argument("--keys", type=lambda s: [k.strip() for k in s.split(",") if k.strip()])
        parser.add_argument("--dry-run", action="store_true", dest="dry_run")
        parser.add_argument("--intraday", action="store_true")
        parsed = parser.parse_args(args[1:])
        if parsed.keys is not None and parsed.intraday:
            parser.error("--keys và --intraday loại trừ nhau")
        return etl.wichart_job.run(keys=parsed.keys, dry_run=parsed.dry_run, intraday=parsed.intraday)
    if args[0] == "news":
        import etl.news_job
        parser = argparse.ArgumentParser(prog="etl news")
        parser.add_argument("--dry-run", action="store_true", dest="dry_run")
        parser.add_argument("--sources", type=lambda s: [k.strip() for k in s.split(",") if k.strip()])
        parser.add_argument("--loop", action="store_true")
        parser.add_argument("--minutes", type=float)
        parser.add_argument("--backfill-sitemap", action="store_true", dest="backfill_sitemap")
        parser.add_argument("--from", dest="from_month")
        parser.add_argument("--to", dest="to_month")
        parser.add_argument("--max-minutes", type=float, dest="max_minutes")
        parser.add_argument("--stop-before-open", action="store_true", dest="stop_before_open")
        parsed = parser.parse_args(args[1:])
        if parsed.backfill_sitemap:
            if not parsed.from_month or not etl.news_job.MONTH.match(parsed.from_month):
                parser.error("--backfill-sitemap cần --from dạng YYYY-MM")
            if parsed.loop or parsed.dry_run or parsed.sources is not None:
                parser.error("--backfill-sitemap không đi cùng --loop/--dry-run/--sources")
            return etl.news_job.run_backfill(from_month=parsed.from_month, to_month=parsed.to_month,
                                             max_minutes=parsed.max_minutes, stop_before_open=parsed.stop_before_open)
        if parsed.minutes is not None and not parsed.loop:
            parser.error("--minutes chỉ đi với --loop")
        return etl.news_job.run(sources=parsed.sources, dry_run=parsed.dry_run, loop=parsed.loop, minutes=parsed.minutes)
    if args[0] in ("fred", "fx", "lbma", "yahoo", "binance"):
        import importlib
        mod = importlib.import_module(f"etl.{args[0]}_job")
        parser = argparse.ArgumentParser(prog=f"etl {args[0]}")
        parser.add_argument("--keys", type=lambda s: [k.strip() for k in s.split(",") if k.strip()])
        parser.add_argument("--dry-run", action="store_true", dest="dry_run")
        if args[0] in ("yahoo", "binance"):
            parser.add_argument("--backfill", action="store_true")
            parser.add_argument("--intraday", action="store_true")        # cửa sổ ngắn, chạy trong phiên (lát 7b)
        parsed = parser.parse_args(args[1:])
        if getattr(parsed, "intraday", False) and getattr(parsed, "backfill", False):
            parser.error("--intraday và --backfill loại trừ nhau")
        extra = {"intraday": parsed.intraday} if args[0] in ("yahoo", "binance") else {}
        return mod.run(keys=parsed.keys, dry_run=parsed.dry_run, backfill=getattr(parsed, "backfill", False), **extra)
    print(f"etl: subcommand không hợp lệ: {args[0]!r} (hỗ trợ: omo, refdata, screener, events, price, snapshot, fundamentals,"
          " wichart, news, fred, fx, lbma, yahoo, binance)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
