"""Spoken announcements: NVDA's own voice first, SAPI as fallback.

Amrw hears his computer through NVDA (Acapela voice). Speaking through the
running screen reader - via the official NVDA Controller Client DLL
(assets/nvda/nvdaControllerClient.dll, LGPL-2.1, redistributable) - means
every announcement uses the voice, speed and language he already configured.
When NVDA is not running we fall back to the SAPI path below.

SAPI design notes (unchanged):
- The pyttsx3/SAPI engine is created AND used inside the same worker thread.
  Creating it on the main thread and driving it from another breaks COM
  threading on some machines and can hang or crash the caller; here the main
  thread never touches the engine, so window creation can never be blocked
  or broken by speech.
- If no Arabic voice is installed we still speak with the system default
  voice (the caller may also pass an English fallback text); if SAPI itself
  is missing/broken, speaking becomes a logged no-op and the app keeps
  working silently - the startup chime in app.py still gives an audible cue.
"""
from __future__ import annotations

import ctypes
import re
import sys
import threading

from .bootstrap import milestone
from .sounds import resource_path

_ARABIC_RE = re.compile(r"arab|ar[-_]?(?:eg|sa|ae|qa|kw|bh|om|jo|lb|sy|iq|ma|dz|tn|ly|sd|ye)(?![a-z])")


class NvdaSpeech:
    """Thin wrapper over the NVDA Controller Client DLL (Windows only)."""

    def __init__(self):
        self._dll = None
        self._failed = False

    def _load(self) -> None:
        if self._dll is not None or self._failed:
            return
        if sys.platform != "win32":
            self._failed = True
            return
        try:
            dll_path = resource_path("assets", "nvda", "nvdaControllerClient.dll")
            dll = ctypes.CDLL(str(dll_path))
            dll.nvdaController_testIfRunning.argtypes = []
            dll.nvdaController_testIfRunning.restype = ctypes.c_long
            dll.nvdaController_speakText.argtypes = [ctypes.c_wchar_p]
            dll.nvdaController_speakText.restype = ctypes.c_long
            self._dll = dll
        except Exception as exc:
            self._failed = True
            milestone(f"nvda speech: dll load failed: {exc!r}")

    def speak(self, text: str) -> bool:
        """Speak through the running NVDA. False when NVDA is unavailable."""
        self._load()
        if self._dll is None:
            return False
        try:
            if self._dll.nvdaController_testIfRunning() != 0:
                return False
            return self._dll.nvdaController_speakText(text) == 0
        except Exception:
            return False


def pick_voice_id(voices) -> "str | None":
    """Return the id of an Arabic voice from a pyttsx3 voice list, else None."""
    for v in voices:
        try:
            blob = " ".join(
                str(getattr(v, attr, "") or "") for attr in ("id", "name")
            ).lower()
            langs = getattr(v, "languages", None) or []
            blob += " " + " ".join(str(l).lower() for l in langs)
        except Exception:
            continue
        if _ARABIC_RE.search(blob):
            return getattr(v, "id", None)
    return None


class Speaker:
    def __init__(self, nvda=None):
        self._lock = threading.Lock()
        self.available = True  # flips False after a hard engine failure
        self._nvda = nvda if nvda is not None else NvdaSpeech()

    def speak(self, text: str) -> bool:
        """Speak ``text`` in the background. False if speech is known-dead."""
        if not self.available:
            return False
        threading.Thread(target=self._run, args=(text,), daemon=True).start()
        return True

    def _run(self, text: str) -> None:
        with self._lock:
            try:
                if self._nvda is not None and self._nvda.speak(text):
                    return  # NVDA spoke with the user's own screen-reader voice
            except Exception:
                pass  # fall through to SAPI
            self._sapi_speak(text)

    def _sapi_speak(self, text: str) -> None:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            try:
                voice_id = pick_voice_id(engine.getProperty("voices") or [])
                if voice_id:
                    engine.setProperty("voice", voice_id)
            except Exception:
                pass  # default voice is an acceptable fallback
            engine.say(text)
            engine.runAndWait()
            try:
                engine.stop()
            except Exception:
                pass
        except Exception as exc:
            self.available = False
            milestone(f"speech unavailable: {exc!r}")
