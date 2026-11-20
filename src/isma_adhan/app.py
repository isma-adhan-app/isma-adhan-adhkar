"""wx.App bootstrap, system tray icon, startup announcement, crash logging."""
from __future__ import annotations

import traceback
from datetime import datetime

import wx
import wx.adv

from . import sounds as snd
from . import strings as S


def _log_path():
    from .config import app_data_dir

    d = app_data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / "app.log"


def _log(line: str) -> None:
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {line}\n")
    except OSError:
        pass


class TrayIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        super().__init__()
        self.frame = frame
        icon_path = snd.resource_path("assets", "icon.ico")
        if icon_path.exists():
            self.SetIcon(wx.Icon(str(icon_path), wx.BITMAP_TYPE_ICO), S.TRAY_TOOLTIP)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, lambda e: self.frame.show_window())

    def CreatePopupMenu(self):
        menu = wx.Menu()
        show_item = menu.Append(wx.ID_ANY, S.TRAY_SHOW)
        play_item = menu.Append(wx.ID_ANY, S.TRAY_PLAY)
        stop_item = menu.Append(wx.ID_ANY, S.MENU_STOP)
        menu.AppendSeparator()
        quit_item = menu.Append(wx.ID_ANY, S.TRAY_QUIT)
        self.Bind(wx.EVT_MENU, lambda e: self.frame.show_window(), show_item)
        self.Bind(wx.EVT_MENU, lambda e: self.frame.play_adhan_now(), play_item)
        self.Bind(wx.EVT_MENU, lambda e: self.frame.stop_audio(), stop_item)
        self.Bind(wx.EVT_MENU, lambda e: self.frame.on_quit(e), quit_item)
        return menu


def run(minimized: bool = False) -> int:
    from .audio import create_player
    from .main_window import MainFrame
    from .speech import Speaker

    _log("app starting")
    app = wx.App()
    try:
        frame = MainFrame(player=create_player(), speaker=Speaker())
        frame.tray = TrayIcon(frame)
        if not minimized:
            frame.Show()
        frame.announce_startup()
        _log("main window shown")
        app.MainLoop()
        _log("app exited normally")
        return 0
    except Exception:
        tb = traceback.format_exc()
        _log("FATAL: " + tb)
        try:
            wx.MessageBox(
                "حدث خطأ في البرنامج. التفاصيل محفوظة في ملف app.log داخل مجلد البرنامج في AppData.\n\n"
                + tb.splitlines()[-1],
                S.APP_NAME,
                style=wx.OK | wx.ICON_ERROR,
            )
        except Exception:
            pass
        return 1
