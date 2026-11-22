"""In-app updates (v1.8): check GitHub releases, download, verify, hand the
installer to the user.

Update safety:
- a check only REPORTS; the installer never runs without the user pressing
  the Update button in Settings
- downloads are verified against the SHA-256 published in the release's
  latest.json before anything is launched
- offline or any failure = quiet no-op on the automatic check, a spoken
  failure message on a manual one

wx-free so it is unit-testable; the caller passes callbacks and marshals
them onto the UI thread.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
from urllib.parse import urlsplit
from dataclasses import dataclass
from pathlib import Path

from . import __version__

LATEST_JSON_URL = (
    "https://github.com/isma-adhan-app/isma-adhan-adhkar/"
    "releases/latest/download/latest.json"
)
TIMEOUT_SECONDS = 25
MAX_INSTALLER_BYTES = 250 * 1024 * 1024


@dataclass
class UpdateInfo:
    version: str
    url: str
    sha256: str
    newer: bool


def version_tuple(text: str) -> tuple:
    """'1.8.0' -> (1, 8, 0); non-numeric parts count as 0."""
    match = re.fullmatch(r"v?(\d+)(?:\.(\d+))(?:\.(\d+))?", str(text).strip())
    if not match:
        raise ValueError("invalid version")
    return tuple(int(x or 0) for x in match.groups())


def is_newer(remote: str, current: str = __version__) -> bool:
    a, b = version_tuple(remote), version_tuple(current)
    n = max(len(a), len(b))
    return a + (0,) * (n - len(a)) > b + (0,) * (n - len(b))


def current_arch() -> str:
    """Installer architecture matching THIS process: a 32-bit build is a
    32-bit Python even on 64-bit Windows (WoW64)."""
    return "x86" if sys.maxsize <= 2**32 else "x64"


def valid_installer_url(url: str) -> bool:
    parsed = urlsplit(url)
    prefix = "/isma-adhan-app/isma-adhan-adhkar/releases/download/"
    return (parsed.scheme == "https" and parsed.netloc == "github.com"
            and parsed.path.startswith(prefix)
            and parsed.path.rsplit("/", 1)[-1] in
                ("IsmaAdhan-Setup.exe", "IsmaAdhan-Setup-x86.exe")
            and not parsed.query and not parsed.fragment)


def fetch_latest(url: str = LATEST_JSON_URL) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "IsmaAdhan-Updater"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read(65537).decode("utf-8-sig"))


def check(url: str = LATEST_JSON_URL) -> "UpdateInfo | None":
    """Latest release as UpdateInfo, or None on any fetch/parse problem."""
    data = fetch_latest(url)
    version = str(data.get("version", "")).strip()
    installer = data.get("installers", {}).get(current_arch(), {})
    dl_url = str(installer.get("url", ""))
    sha = str(installer.get("sha256", "")).lower()
    expected = "IsmaAdhan-Setup-x86.exe" if current_arch() == "x86" else "IsmaAdhan-Setup.exe"
    if urlsplit(dl_url).path.rsplit("/", 1)[-1] != expected:
        return None
    if not version or not valid_installer_url(dl_url) or not re.fullmatch(r"[0-9a-f]{64}", sha):
        return None
    return UpdateInfo(version=version, url=dl_url, sha256=sha,
                      newer=is_newer(version))


def check_async(callback, url: str = LATEST_JSON_URL) -> None:
    """callback(info, error): info is UpdateInfo (newer flag set) or None;
    error is None or the exception. Runs on a daemon thread."""

    def work():
        try:
            callback(check(url), None)
        except Exception as exc:
            callback(None, exc)

    threading.Thread(target=work, daemon=True).start()


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(info: UpdateInfo, dest_dir: Path = None) -> Path:
    """Download the installer and verify it against the published SHA-256.
    Raises ValueError('hash') on mismatch."""
    if not valid_installer_url(info.url):
        raise ValueError("invalid installer source")
    dest_dir = Path(tempfile.mkdtemp(prefix="IsmaAdhan-update-", dir=dest_dir))
    dest = dest_dir / "IsmaAdhan-Update.exe"
    req = urllib.request.Request(info.url, headers={"User-Agent": "IsmaAdhan-Updater"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp, open(dest, "wb") as out:
            total = 0
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_INSTALLER_BYTES:
                    raise ValueError("installer too large")
                out.write(chunk)
        if sha256_of(dest) != info.sha256:
            raise ValueError("hash")
    except Exception:
        shutil.rmtree(dest_dir, ignore_errors=True)
        raise
    return dest


def download_async(info: UpdateInfo, callback) -> None:
    """callback(path, error): path is the verified installer or None; error is
    None, 'hash', or the exception. Runs on a daemon thread."""

    def work():
        try:
            callback(download(info), None)
        except ValueError as exc:
            callback(None, "hash" if "hash" in str(exc) else exc)
        except Exception as exc:
            callback(None, exc)

    threading.Thread(target=work, daemon=True).start()


def launch_installer(path) -> None:
    """Hand the verified installer to Windows. The installer itself closes
    the running app (InitializeSetup) and upgrades in place, preserving
    settings and custom sounds in %APPDATA%."""
    subprocess.Popen([str(path)], shell=False, cwd=str(Path(path).parent))
