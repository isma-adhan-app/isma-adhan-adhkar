"""Spoken announcements.

On Windows this uses SAPI via pyttsx3, so a user hears "حان الآن وقت صلاة
الفجر" even before adding his own adhan audio. Everything is optional: if
pyttsx3 or a voice is unavailable, speaking silently becomes a no-op and the
visual/notification path still works.
"""
from __future__ import annotations

import threading


class Speaker:
    def __init__(self):
        self._engine = None
        self._lock = threading.Lock()
        self._failed = False

    def _get_engine(self):
        if self._engine is not None or self._failed:
            return self._engine
        try:
            import pyttsx3

            self._engine = pyttsx3.init()
        except Exception:
            self._failed = True
            self._engine = None
        return self._engine

    def speak(self, text: str) -> bool:
        """Speak ``text`` in the background. Returns False if speech is unavailable."""
        engine = self._get_engine()
        if engine is None:
            return False

        def _run():
            with self._lock:
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception:
                    pass

        threading.Thread(target=_run, daemon=True).start()
        return True
