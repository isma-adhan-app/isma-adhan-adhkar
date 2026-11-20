"""Very-early startup instrumentation.

Imported and initialised BEFORE wx/pygame/pyttsx3 so that a crash at any
later stage leaves a trace in %APPDATA%/IsmaAdhan/app.log. Must stay free of
third-party imports.

Milestones appended to app.log let a diagnostic read pinpoint exactly where
startup stopped on a machine where the window never appears:
    startup: entry -> imports ok -> wx.App created -> player created ->
    main window constructed -> tray icon ok -> window shown -> event loop
A marker file (startup.ok) records that the window was shown; if the next
launch finds it missing from the previous run, the last attempt died before
the window appeared and the app says so on-screen and in the log.
"""
from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

_log_file: Path | None = None
_marker_file: Path | None = None
_previous_crashed = False
_fault_handle = None


def _data_dir() -> Path:
    import os

    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / "IsmaAdhan"
    return Path.home() / ".isma_adhan"


def _excepthook(exc_type, exc, tb):
    try:
        milestone("FATAL (unhandled): " + "".join(traceback.format_exception(exc_type, exc, tb)))
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc, tb)


def init() -> None:
    """Set up logging + crash hooks. Call before importing anything risky."""
    global _log_file, _marker_file, _previous_crashed, _fault_handle
    try:
        d = _data_dir()
        d.mkdir(parents=True, exist_ok=True)
        _log_file = d / "app.log"
        _marker_file = d / "startup.ok"
        _previous_crashed = _log_file.exists() and not _marker_file.exists() and _had_prior_start()
        try:
            _marker_file.unlink(missing_ok=True)
        except OSError:
            pass
        try:
            import faulthandler

            _fault_handle = open(_log_file, "a", encoding="utf-8")
            faulthandler.enable(file=_fault_handle)
        except Exception:
            pass
        sys.excepthook = _excepthook
        milestone("startup: entry")
    except Exception:
        pass


def _had_prior_start() -> bool:
    try:
        with open(_log_file, "r", encoding="utf-8", errors="replace") as f:
            return "startup: entry" in f.read()
    except Exception:
        return False


def milestone(step: str) -> None:
    try:
        if _log_file is None:
            return
        with open(_log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {step}\n")
    except Exception:
        pass


def window_shown() -> None:
    """Mark that the main window reached the screen; clears crash detection."""
    try:
        if _marker_file is not None:
            _marker_file.write_text("ok", encoding="utf-8")
    except Exception:
        pass


def previous_run_crashed() -> bool:
    """True when the previous launch logged a start but never showed a window."""
    return _previous_crashed
