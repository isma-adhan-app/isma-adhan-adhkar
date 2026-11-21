"""Installer close-gracefully hooks: importable everywhere, in sync with Inno."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from isma_adhan import win32_integration as w32

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_hooks_behave_per_platform():
    class _Frame:  # minimal stand-in; must never get a real quit call
        def GetHandle(self):
            raise AssertionError("no real window handle in unit tests")

        def on_quit(self, _e):
            raise AssertionError("no quit in unit tests")

    if sys.platform == "win32":
        # The mutex is really held (the installer detection point); a bogus
        # frame must degrade to False, never raise.
        assert w32.create_installer_mutex() is True
        assert w32.install_quit_handler(_Frame()) is False
    else:
        # Off Windows both hooks are harmless no-ops.
        assert w32.create_installer_mutex() is False
        assert w32.install_quit_handler(_Frame()) is False


def test_installer_uses_same_mutex_and_message_names():
    iss = (REPO_ROOT / "build" / "installer.iss").read_text(encoding="utf-8")
    assert f"AppMutex={w32.MUTEX_NAME}" in iss
    assert f"INSTALLER_MUTEX = '{w32.MUTEX_NAME}'" in iss
    assert f"QUIT_MESSAGE_NAME = '{w32.QUIT_MESSAGE_NAME}'" in iss


def test_installer_closes_running_instance_before_copy():
    iss = (REPO_ROOT / "build" / "installer.iss").read_text(encoding="utf-8")
    # The deterministic close lives in PrepareToInstall: broadcast the quit
    # message, wait for the mutex, then force-close leftovers (old builds).
    assert re.search(r"function\s+PrepareToInstall", iss)
    assert "RegisterWindowMessageW(QUIT_MESSAGE_NAME)" in iss
    assert "CheckForMutexes(INSTALLER_MUTEX)" in iss
    assert "taskkill.exe" in iss and "/IM IsmaAdhan.exe /F" in iss
    assert "CloseApplications=yes" in iss


def test_version_bumped_and_consistent():
    from isma_adhan import __version__

    iss = (REPO_ROOT / "build" / "installer.iss").read_text(encoding="utf-8")
    assert f'#define AppVersion "{__version__}"' in iss
