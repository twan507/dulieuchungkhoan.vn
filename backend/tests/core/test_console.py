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


def test_console_say_writes_to_the_console_device_not_to_redirected_stdout():
    """Output của job đi vào file log (`>> log 2>&1`); lời chào cuối phải ra CỬA SỔ nên ghi thẳng
    thiết bị console CONOUT$ — người dùng thấy được vì sao cửa sổ sắp đóng."""
    written = []

    class FakeFile:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def write(self, s):
            written.append(s)

    opened = []

    def opener(path, mode, **kw):
        opened.append((path, mode))
        return FakeFile()

    assert console.console_say("xin chào", opener=opener) is True
    assert opened == [("CONOUT$", "w")] and written == ["xin chào\n"]


def test_console_say_swallows_a_missing_console():
    def opener(path, mode, **kw):
        raise OSError("no console")

    assert console.console_say("x", opener=opener) is False


def test_banner_and_farewell_only_speak_when_run_from_the_scheduler(monkeypatch):
    said = []
    monkeypatch.setattr(console, "console_say", lambda t, opener=open: said.append(t) or True)
    monkeypatch.setattr(console, "hold", lambda s, sleep=None: True)
    monkeypatch.delenv(console.ENV_FLAG, raising=False)
    assert console.banner("bắt đầu") is False and console.farewell("xong") is False and said == []
    monkeypatch.setenv(console.ENV_FLAG, "1")
    assert console.banner("bắt đầu") is True and console.farewell("xong", 20) is True
    assert said[0] == "bắt đầu" and said[1].startswith("xong — cửa sổ tự đóng sau 20 giây")


def test_hold_waits_the_given_seconds_and_a_second_ctrl_c_cuts_it_short():
    slept = []
    assert console.hold(20, sleep=slept.append) is True and slept == [20]

    def impatient(s):
        raise KeyboardInterrupt

    assert console.hold(20, sleep=impatient) is False           # Ctrl+C lần hai: đóng luôn, không ném


def test_flag_with_trailing_space_from_cmd_set_still_counts(monkeypatch):
    """Đo 2026-09-04: `set DLCK_LOCK_CONSOLE=1 && …` trong cmd cho giá trị '1 ' (có dấu cách) —
    lần chạy thật đầu tiên vì thế không khoá gì. So sánh sau strip()."""
    f = Fake()
    monkeypatch.setenv(console.ENV_FLAG, "1 ")
    assert console.lock_if_scheduled(kernel32=f, user32=f) is True
