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


def lock_if_scheduled(**win32) -> bool:
    """Chỉ khoá khi chạy từ Task Scheduler (`DLCK_LOCK_CONSOLE=1`). Chạy tay từ terminal của người
    dùng thì KHÔNG đụng: menu thuộc về conhost, giữ tới khi đóng cửa sổ — khoá là terminal đó mất
    nút X cho tới hết phiên."""
    # .strip(): wrapper cmd `set DLCK_LOCK_CONSOLE=1 && …` đưa cả khoảng trắng trước `&&` vào giá trị
    # ("1 ") — đo 2026-09-04, chính nó làm lần chạy thật đầu tiên không khoá gì.
    if os.environ.get(ENV_FLAG, "").strip() != "1":
        return False
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
