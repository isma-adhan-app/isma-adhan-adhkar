"""Installer close-gracefully hooks: importable everywhere, in sync with Inno."""
from __future__ import annotations

import re
from pathlib import Path

from isma_adhan import win32_integration as w32

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_module_imports_and_noops_off_windows():
    # On Linux (CI unit tests) both hooks must be harmless no-ops.
    assert w32.create_installer_mutex() is False

    class _Frame:  # minimal stand-in; must not be touched off Windows
        def GetHandle(self):  # pragma: no cover - only used on win32
            raise AssertionError("should not be called off Windows")

        def on_quit(self, _e):  # pragma: no cover
            raise AssertionError("should not be called off Windows")

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
