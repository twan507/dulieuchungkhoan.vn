"""Khoá nút X của cửa sổ console trong lúc job chạy — test bằng kernel32/user32 GIẢ, không đụng
cửa sổ thật của người chạy pytest (khoá thật là mất nút X của chính terminal dev)."""
from core import console


class Fake:
    def __init__(self, hwnd=42, menu=7, delete_ok=1):
        self.hwnd, self.menu, self.delete_ok, self.calls = hwnd, menu, delete_ok, []

    def GetConsoleWindow(self):
        return self.hwnd

    def GetSystemMenu(self, hwnd, revert):
        self.calls.append(("GetSystemMenu", hwnd, revert))
        return self.menu

    def DeleteMenu(self, menu, item, flags):
        self.calls.append(("DeleteMenu", menu, item, flags))
        return self.delete_ok


def test_locks_sc_close_on_the_console_window_system_menu():
    f = Fake()
    assert console.lock_close_button(kernel32=f, user32=f) is True
    assert f.calls == [("GetSystemMenu", 42, False), ("DeleteMenu", 7, console.SC_CLOSE, console.MF_BYCOMMAND)]
    assert console.SC_CLOSE == 0xF060                       # hằng số Win32, không tính lại


def test_no_console_window_means_nothing_to_lock():
    f = Fake(hwnd=0)                                        # chạy không có console (service, pipe)
    assert console.lock_close_button(kernel32=f, user32=f) is False
    assert f.calls == []


def test_delete_failure_is_reported_not_raised():
    f = Fake(delete_ok=0)
    assert console.lock_close_button(kernel32=f, user32=f) is False


def test_non_windows_without_win32_api_is_a_noop(monkeypatch):
    monkeypatch.setattr(console.sys, "platform", "linux")
    assert console.lock_close_button() is False


def test_manual_runs_do_not_touch_the_terminal_only_scheduler_runs_lock(monkeypatch):
    """Chạy tay từ terminal của người dùng không được khoá nút X của terminal đó (menu conhost giữ
    tới khi đóng cửa sổ); chỉ wrapper Task Scheduler đặt DLCK_LOCK_CONSOLE=1 mới khoá."""
    f = Fake()
    monkeypatch.delenv(console.ENV_FLAG, raising=False)
    assert console.lock_if_scheduled(kernel32=f, user32=f) is False and f.calls == []
    monkeypatch.setenv(console.ENV_FLAG, "1")
    assert console.lock_if_scheduled(kernel32=f, user32=f) is True
    assert f.calls[-1] == ("DeleteMenu", 7, console.SC_CLOSE, console.MF_BYCOMMAND)
