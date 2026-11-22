"""Windows-only hooks that let the Inno Setup installer close us gracefully.

Two pieces:

1. A named mutex (MUTEX_NAME) held for the process lifetime. The installer's
   AppMutex directive uses it to detect a running instance.
2. A custom broadcast window message (QUIT_MESSAGE_NAME). The installer posts
   it to all top-level windows before copying files; the running app answers
   by taking its normal quit path (timer off, player off, window destroyed),
   which releases every file lock under _internal. Older builds never
   registered the message, so the installer also falls back to taskkill.

Both functions are no-ops off Windows so the code stays importable in CI and
unit tests on Linux.
"""
from __future__ import annotations

import ctypes
import sys

MUTEX_NAME = "IsmaAdhanAppMutex"
QUIT_MESSAGE_NAME = "ISMA_ADHAN_REQUEST_QUIT"

_GWL_WNDPROC = -4

# 64-bit-safe pointer types (ctypes.wintypes.WPARAM is wrong on x64).
_LRESULT = ctypes.c_ssize_t
_WPARAM = ctypes.c_size_t
_LPARAM = ctypes.c_ssize_t

_MUTEX_HANDLE = None
_WNDPROC_ORIGINAL = None
_WNDPROC_CALLBACK = None  # keep a reference so it is never garbage-collected
_QUIT_MESSAGE_ID = 0


def create_installer_mutex() -> bool:
    """Hold the named mutex the installer looks for. No-op off Windows."""
    global _MUTEX_HANDLE
    if sys.platform != "win32":
        return False
    if _MUTEX_HANDLE:
        return True
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        if not handle:
            return False
        _MUTEX_HANDLE = handle
        return True
    except Exception:
        return False


def install_quit_handler(frame, log=None) -> bool:
    """Answer the installer's broadcast quit message with a real quit.

    Subclasses the main frame's window procedure; when the installer posts
    QUIT_MESSAGE_NAME the frame runs its normal quit path (which stops the
    scheduler timer, stops audio and destroys the window) instead of hiding
    to the tray. Returns False (harmless) when anything is unavailable.
    """
    global _WNDPROC_ORIGINAL, _WNDPROC_CALLBACK, _QUIT_MESSAGE_ID
    if sys.platform != "win32":
        return False
    try:
        user32 = ctypes.windll.user32
        # Explicit prototypes: without them ctypes truncates 64-bit pointer
        # args/returns to c_int, and the truncated original WndProc pointer
        # makes CallWindowProcW jump to garbage (0xC0000409, ASLR-dependent).
        user32.RegisterWindowMessageW.argtypes = [ctypes.c_wchar_p]
        user32.RegisterWindowMessageW.restype = ctypes.c_uint
        set_wndproc = user32.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user32.SetWindowLongW
        set_wndproc.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
        set_wndproc.restype = ctypes.c_void_p
        user32.CallWindowProcW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, _WPARAM, _LPARAM]
        user32.CallWindowProcW.restype = _LRESULT
        _QUIT_MESSAGE_ID = user32.RegisterWindowMessageW(QUIT_MESSAGE_NAME)
        if not _QUIT_MESSAGE_ID:
            return False
        wndproc_type = ctypes.WINFUNCTYPE(
            _LRESULT, ctypes.c_void_p, ctypes.c_uint, _WPARAM, _LPARAM
        )

        def _wndproc(hwnd, msg, wparam, lparam):
            if msg == _QUIT_MESSAGE_ID:
                try:
                    import wx

                    frame._really_quit = True
                    wx.CallAfter(frame.Close)
                except Exception:
                    pass
                return 0
            return user32.CallWindowProcW(
                _WNDPROC_ORIGINAL, hwnd, msg, wparam, lparam
            )

        _WNDPROC_CALLBACK = wndproc_type(_wndproc)
        hwnd = frame.GetHandle()
        previous = set_wndproc(
            hwnd, _GWL_WNDPROC, ctypes.cast(_WNDPROC_CALLBACK, ctypes.c_void_p)
        )
        if not previous:
            return False
        _WNDPROC_ORIGINAL = previous
        if log:
            log("installer quit hook ready")
        return True
    except Exception:
        return False
