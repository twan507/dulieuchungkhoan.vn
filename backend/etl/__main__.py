import time
from datetime import datetime, timezone

from etl.heartbeat import heartbeat


def main() -> None:
    while True:
        print(heartbeat(datetime.now(timezone.utc)), flush=True)
        time.sleep(15)


if __name__ == "__main__":
    main()
