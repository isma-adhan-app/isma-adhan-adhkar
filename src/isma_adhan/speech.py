"""Spoken announcements via SAPI (pyttsx3), hardened for first-run machines.

Design notes:
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

import re
import threading

from .bootstrap import milestone

_ARABIC_RE = re.compile(r"arab|ar[-_]?(?:eg|sa|ae|qa|kw|bh|om|jo|lb|sy|iq|ma|dz|tn|ly|sd|ye)(?![a-z])")


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
    def __init__(self):
        self._lock = threading.Lock()
        self.available = True  # flips False after a hard engine failure

    def speak(self, text: str) -> bool:
        """Speak ``text`` in the background. False if speech is known-dead."""
        if not self.available:
            return False
        threading.Thread(target=self._run, args=(text,), daemon=True).start()
        return True

    def _run(self, text: str) -> None:
        with self._lock:
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
