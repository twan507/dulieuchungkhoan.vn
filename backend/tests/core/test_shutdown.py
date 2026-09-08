"""`docker stop` gửi SIGTERM; Python mặc định chết ngay, bỏ qua đường đóng sổ mà Ctrl+C đang có
(`test_e42`: `failed: dừng tay (Ctrl+C)`, exit 130). Handler nâng SIGTERM thành KeyboardInterrupt
để hai đường dừng là một. Windows đăng ký được nhưng không giao SIGTERM — ca thật chỉ chạy POSIX.
"""
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from core import shutdown

BACKEND = Path(__file__).resolve().parents[2]


def test_handler_raises_keyboard_interrupt():
    with pytest.raises(KeyboardInterrupt):
        shutdown._raise_interrupt(signal.SIGTERM, None)


def test_install_registers_the_handler_for_sigterm():
    old = signal.getsignal(signal.SIGTERM)
    try:
        shutdown.install_signal_handlers()
        assert signal.getsignal(signal.SIGTERM) is shutdown._raise_interrupt
    finally:
        signal.signal(signal.SIGTERM, old)


@pytest.mark.skipif(sys.platform == "win32", reason="Windows không giao SIGTERM cho handler Python")
def test_sigterm_in_a_real_process_lands_in_the_ctrl_c_path():
    code = ("import os, sys, time\n"
            "from core.shutdown import install_signal_handlers\n"
            "install_signal_handlers(); print('READY', flush=True)\n"
            "try:\n    time.sleep(30)\nexcept KeyboardInterrupt:\n    print('INTERRUPTED'); sys.exit(130)\n")
    p = subprocess.Popen([sys.executable, "-c", code], cwd=BACKEND, stdout=subprocess.PIPE, text=True)
    assert p.stdout.readline().strip() == "READY"
    p.send_signal(signal.SIGTERM)
    out, _ = p.communicate(timeout=10)
    assert p.returncode == 130 and "INTERRUPTED" in out
