"""SIGTERM → cùng đường dừng với Ctrl+C (spec lát 12 §5.5, đã đính chính khi thực thi).

`docker compose stop/down` gửi SIGTERM rồi đợi `stop_grace_period`; không handler thì Python chết ngay.
Nâng thành `KeyboardInterrupt` để mọi `except KeyboardInterrupt` đã có ở 11 họ job (khuôn `price_job`,
`test_e42`) chạy y hệt: sổ `ops.etl_run` đóng `failed: dừng tay (Ctrl+C)`, exit 130.

Ingester là vòng asyncio KHÔNG có `except KeyboardInterrupt`: handler này chỉ cho nó mã thoát như Ctrl+C,
không xả hàng đợi. Đường đóng phiên tử tế (xả + đối chứng) đi qua `ingester.main.install_loop_stop`
(SIGTERM/SIGINT → `stop.set()` trên loop), cài ở lát 12 Task 6.

Windows: `etl.scheduler.runner._stop_child` gửi `CTRL_BREAK_EVENT` cho nhóm tiến trình con — Python ánh
xạ tín hiệu đó thành `SIGBREAK`, KHÔNG phải `SIGINT`. Đăng ký thêm SIGBREAK vào cùng handler để con đóng
sổ `ops.etl_run` với `130` như Ctrl+C thật, thay vì chết cứng `0xC000013A` (đo tay 2026-09-09).
"""
from __future__ import annotations

import signal


def _raise_interrupt(signum, frame):  # noqa: ARG001 — chữ ký handler của `signal`
    raise KeyboardInterrupt


def install_signal_handlers() -> None:
    signal.signal(signal.SIGTERM, _raise_interrupt)
    if hasattr(signal, "SIGBREAK"):        # chỉ Windows — CTRL_BREAK từ runner đi qua đây (ruling R23)
        signal.signal(signal.SIGBREAK, _raise_interrupt)
