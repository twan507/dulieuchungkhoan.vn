"""Khoá nút X của cửa sổ console trong lúc job chạy (chỉ Windows).

Task Scheduler chạy Interactive (quyết định chủ dự án 2026-09-04) nên mỗi job có một cửa sổ cmd —
tiện thấy task nào đang chạy, nhưng bấm nhầm X là giết job (với ingester là mất tick không lấy lại
được). Console không thể "hỏi lại xác nhận": Windows gửi CTRL_CLOSE_EVENT rồi giết tiến trình sau vài
giây, code không huỷ được. Cái làm được là xoá mục Close khỏi system menu của chính cửa sổ: X mờ đi,
Alt+F4 và "Close window" trên taskbar cũng bị chặn. Dừng có chủ đích: Ctrl+C trong cửa sổ, hoặc
Stop-ScheduledTask / Task Manager. Job xong thì cửa sổ tự đóng như thường.
"""
from __future__ import annotations

import ctypes
import os
import sys

SC_CLOSE = 0xF060          # WM_SYSCOMMAND: Close
MF_BYCOMMAND = 0x0
ENV_FLAG = "DLCK_LOCK_CONSOLE"   # wrapper của Task Scheduler đặt =1; chạy tay từ terminal thì không


def console_say(text: str, opener=open) -> bool:
    """Ghi thẳng ra THIẾT BỊ console (CONOUT$) — output thường của job đã bị `>> log 2>&1` nuốt,
    còn đây là dòng người ngồi trước cửa sổ phải thấy. Không có console thì im lặng."""
    try:
        with opener("CONOUT$", "w", encoding="utf-8", errors="replace") as f:
            f.write(text + "\n")
        return True
    except OSError:
        return False


def banner(text: str) -> bool:
    """Dòng mở đầu cho cửa sổ task (bắt đầu lúc nào, làm gì, hạn ở đâu) — chỉ khi chạy từ Scheduler."""
    if os.environ.get(ENV_FLAG, "").strip() != "1":
        return False
    return console_say(text)


STD_INPUT_HANDLE = -10
ENABLE_QUICK_EDIT_MODE = 0x0040
ENABLE_EXTENDED_FLAGS = 0x0080


def disable_quick_edit(kernel32=None) -> bool:
    """Tắt QuickEdit của console: bật thì bấm chuột vào cửa sổ là vào chế độ Select — tiến trình bị
    TẠM DỪNG và Ctrl+C thành copy, không gửi ngắt (đo 2026-09-04: chủ dự án Ctrl+C mà job "treo")."""
    if kernel32 is None:
        if sys.platform != "win32":
            return False
        kernel32 = ctypes.windll.kernel32
        kernel32.GetStdHandle.restype = ctypes.c_void_p
        kernel32.GetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
        kernel32.SetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    h = kernel32.GetStdHandle(STD_INPUT_HANDLE)
    if not h:
        return False
    mode = ctypes.c_uint()
    if not kernel32.GetConsoleMode(h, ctypes.byref(mode)):
        return False
    new = (mode.value | ENABLE_EXTENDED_FLAGS) & ~ENABLE_QUICK_EDIT_MODE
    return bool(kernel32.SetConsoleMode(h, new))


def lock_if_scheduled(**win32) -> bool:
    """Chỉ khoá khi chạy từ Task Scheduler (`DLCK_LOCK_CONSOLE=1`). Chạy tay từ terminal của người
    dùng thì KHÔNG đụng: menu thuộc về conhost, giữ tới khi đóng cửa sổ — khoá là terminal đó mất
    nút X cho tới hết phiên. Cùng cổng: tắt QuickEdit để Ctrl+C luôn là ngắt, không phải copy."""
    # .strip(): wrapper cmd `set DLCK_LOCK_CONSOLE=1 && …` đưa cả khoảng trắng trước `&&` vào giá trị
    # ("1 ") — đo 2026-09-04, chính nó làm lần chạy thật đầu tiên không khoá gì.
    if os.environ.get(ENV_FLAG, "").strip() != "1":
        return False
    disable_quick_edit(win32.get("kernel32"))
    return lock_close_button(**win32)


def lock_close_button(kernel32=None, user32=None) -> bool:
    """True nếu đã khoá; False nếu không có console, không phải Windows, hoặc Win32 từ chối.
    `kernel32`/`user32` tiêm được để test không đụng cửa sổ thật của người chạy pytest."""
    if kernel32 is None or user32 is None:
        if sys.platform != "win32":
            return False
        kernel32, user32 = ctypes.windll.kernel32, ctypes.windll.user32
        # Handle là con trỏ 64-bit; mặc định ctypes coi là int 32-bit — khai báo để không bị cắt.
        kernel32.GetConsoleWindow.restype = ctypes.c_void_p
        user32.GetSystemMenu.restype = ctypes.c_void_p
        user32.GetSystemMenu.argtypes = [ctypes.c_void_p, ctypes.c_bool]
        user32.DeleteMenu.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
    hwnd = kernel32.GetConsoleWindow()
    if not hwnd:
        return False
    menu = user32.GetSystemMenu(hwnd, False)
    if not menu:
        return False
    return bool(user32.DeleteMenu(menu, SC_CLOSE, MF_BYCOMMAND))
