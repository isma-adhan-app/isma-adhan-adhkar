"""wx.App bootstrap, system tray icon, startup announcement, crash logging.

Startup order is defensive: every risky step is wrapped and milestones are
appended to app.log so a machine where "nothing happens" still tells us, via
the log, exactly where startup stopped. The main window is ALWAYS shown and
raised on a manual launch (only the autostart entry passes --minimized), and
the first audible feedback is the bundled Bismillah (falling back to a
guaranteed Windows chime), then the spoken announcement once the event loop
is running.
"""
from __future__ import annotations

import traceback

import wx
import wx.adv

from . import bootstrap
from . import sounds as snd
from . import strings as S


def _resolve_startup_language() -> str:
    """Pick the UI language once, before any window exists: the saved setting
    wins; "auto" (and first run) follows the Windows display language."""
    try:
        from .config import load_settings

        saved = load_settings().language
    except Exception:
        saved = "auto"
    if saved in S.LANGUAGES:
        return saved
    try:
        import ctypes

        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return S.language_from_langid(langid)
    except Exception:
        return "ar"


def _log(line: str) -> None:
    bootstrap.milestone(line)


class TrayIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        super().__init__()
        self.frame = frame
        icon_path = snd.resource_path("assets", "icon.ico")
        if icon_path.exists():
            self.SetIcon(wx.Icon(str(icon_path), wx.BITMAP_TYPE_ICO), S.APP_NAME)
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


def _startup_chime() -> None:
    """A sound that does not depend on SAPI or the app's audio stack, so a
    blind user always gets an audible 'I started' signal."""
    try:
        import winsound

        winsound.PlaySound(
            "SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_NODEFAULT
        )
        _log("startup: chime played")
    except Exception as exc:
        _log(f"startup: chime failed: {exc!r}")


def _after_window_shown(frame) -> None:
    """Runs once the event loop is live and the window is on screen."""
    bootstrap.window_shown()
    # Bismillah before anything else (his explicit request); the chime is the
    # fallback when the clip cannot play
    bismillah_secs = 0.0
    try:
        bismillah_secs = frame.play_bismillah()
    except Exception as exc:
        _log(f"startup: bismillah failed: {exc!r}")
    if bismillah_secs > 0:
        _log("startup: bismillah playing")
    else:
        _startup_chime()
    if bootstrap.previous_run_crashed():
        msg = S.MSG_CRASH_INCOMPLETE
        frame.log(msg)
        _log("startup: previous launch did not reach the window")
    from .audio import NullPlayer

    if isinstance(frame.player, NullPlayer):
        msg = S.MSG_AUDIO_DEVICE_FAIL
        frame.log(msg)
        _log(f"startup: audio unavailable: {frame.player.reason}")
    try:
        if bismillah_secs > 0:
            # let the Bismillah finish before the spoken announcement starts
            wx.CallLater(int((bismillah_secs + 0.8) * 1000), frame.announce_startup)
        else:
            frame.announce_startup()
        _log("startup: announcement queued")
    except Exception as exc:
        _log(f"startup: announcement failed: {exc!r}")


def _bind_end_session(app, frame) -> None:
    """Quit for real when Windows ends the session or the Restart Manager
    asks. The normal close handler hides to the tray, which is what made
    installer-driven and shutdown-driven closes leave the process (and its
    locked DLLs) alive."""

    def _on_query_end_session(event):
        frame._really_quit = True
        event.Skip()

    def _on_end_session(event):
        frame._really_quit = True
        try:
            frame.timer.Stop()
            frame.player.stop()
        except Exception:
            pass
        frame.Destroy()
        event.Skip()

    try:
        app.Bind(wx.EVT_QUERY_END_SESSION, _on_query_end_session)
        app.Bind(wx.EVT_END_SESSION, _on_end_session)
        _log("startup: end-session handlers bound")
    except Exception as exc:
        _log(f"startup: end-session bind failed: {exc!r}")


def run(minimized: bool = False) -> int:
    _log("startup: importing ui modules")
    from .audio import create_player
    from .main_window import MainFrame
    from .speech import Speaker
    from . import win32_integration

    _log("startup: imports ok")
    language = _resolve_startup_language()
    S.set_language(language)
    _log(f"startup: ui language {language}")
    if win32_integration.create_installer_mutex():
        _log("startup: installer mutex held")
    app = wx.App()
    _log("startup: wx.App created")
    try:
        player = create_player()
        _log(f"startup: player created ({type(player).__name__})")
        speaker = Speaker()
        frame = MainFrame(player=player, speaker=speaker)
        _log("startup: main window constructed")
        if win32_integration.install_quit_handler(frame, log=_log):
            _log("startup: installer quit hook ok")
        _bind_end_session(app, frame)
        try:
            frame.tray = TrayIcon(frame)
            _log("startup: tray icon ok")
        except Exception as exc:
            _log(f"startup: tray icon failed: {exc!r}")
        if minimized:
            _log("startup: started minimized (autostart)")
        else:
            frame.show_window()
            _log("startup: window shown")
        wx.CallAfter(_after_window_shown, frame)
        wx.CallLater(60_000, frame.on_check_update, False)  # silent check once a minute in
        app.MainLoop()
        _log("app exited normally")
        return 0
    except Exception:
        tb = traceback.format_exc()
        _log("FATAL: " + tb)
        try:
            wx.MessageBox(
                S.MSG_CRASH_ERROR.format(details=tb.splitlines()[-1]),
                S.APP_NAME,
                style=wx.OK | wx.ICON_ERROR,
            )
        except Exception:
            pass
        return 1
