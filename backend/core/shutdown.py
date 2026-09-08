"""SIGTERM → cùng đường dừng với Ctrl+C (spec lát 12 §5.5).

`docker compose stop/down` gửi SIGTERM rồi đợi `stop_grace_period`. Không handler thì Python chết
ngay: job không đóng sổ `ops.etl_run`, ingester mất hàng đợi RAM chưa xả. Nâng thành
`KeyboardInterrupt` để mọi `except KeyboardInterrupt` đã có (khuôn `price_job`, `test_e42`) chạy y hệt.
"""
from __future__ import annotations

import signal


def _raise_interrupt(signum, frame):  # noqa: ARG001 — chữ ký handler của `signal`
    raise KeyboardInterrupt


def install_signal_handlers() -> None:
    signal.signal(signal.SIGTERM, _raise_interrupt)
