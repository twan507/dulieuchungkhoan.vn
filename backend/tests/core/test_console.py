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

    # kernel32 phần QuickEdit — lock_if_scheduled gọi cả hai việc trên cùng một cổng
    def GetStdHandle(self, which):
        return 9

    def GetConsoleMode(self, h, pmode):
        pmode._obj.value = 0x0060
        return 1

    def SetConsoleMode(self, h, mode):
        self.calls.append(("SetConsoleMode", h, mode))
        return 1


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


class FakeKernel:
    """kernel32 giả cho QuickEdit: mode ban đầu có QUICK_EDIT (0x40) + INSERT (0x20)."""

    def __init__(self, handle=9, mode=0x0060, ok=1):
        self.handle, self.mode, self.ok, self.set_to = handle, mode, ok, None

    def GetStdHandle(self, which):
        assert which == console.STD_INPUT_HANDLE
        return self.handle

    def GetConsoleMode(self, h, pmode):
        pmode._obj.value = self.mode
        return self.ok

    def SetConsoleMode(self, h, mode):
        self.set_to = mode
        return self.ok


def test_disable_quick_edit_clears_the_flag_and_sets_extended_flags():
    k = FakeKernel()
    assert console.disable_quick_edit(kernel32=k) is True
    assert k.set_to == (0x0060 | console.ENABLE_EXTENDED_FLAGS) & ~console.ENABLE_QUICK_EDIT_MODE
    assert k.set_to & console.ENABLE_QUICK_EDIT_MODE == 0 and k.set_to & 0x0020   # INSERT giữ nguyên


def test_disable_quick_edit_without_a_console_is_a_noop():
    assert console.disable_quick_edit(kernel32=FakeKernel(handle=0)) is False
    assert console.disable_quick_edit(kernel32=FakeKernel(ok=0)) is False


def test_banner_only_speaks_when_run_from_the_scheduler(monkeypatch):
    said = []
    monkeypatch.setattr(console, "console_say", lambda t, opener=open: said.append(t) or True)
    monkeypatch.delenv(console.ENV_FLAG, raising=False)
    assert console.banner("bắt đầu") is False and said == []
    monkeypatch.setenv(console.ENV_FLAG, "1")
    assert console.banner("bắt đầu") is True and said == ["bắt đầu"]


def test_flag_with_trailing_space_from_cmd_set_still_counts(monkeypatch):
    """Đo 2026-09-04: `set DLCK_LOCK_CONSOLE=1 && …` trong cmd cho giá trị '1 ' (có dấu cách) —
    lần chạy thật đầu tiên vì thế không khoá gì. So sánh sau strip()."""
    f = Fake()
    monkeypatch.setenv(console.ENV_FLAG, "1 ")
    assert console.lock_if_scheduled(kernel32=f, user32=f) is True
