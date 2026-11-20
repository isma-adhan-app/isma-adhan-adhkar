"""Audio playback through pygame.mixer.

pygame plays MP3/WAV/OGG, starts playback asynchronously (does not block the
UI), and packages cleanly with PyInstaller. A NullPlayer is used when no
audio device is available so the rest of the app keeps working.
"""
from __future__ import annotations

from pathlib import Path


class PygamePlayer:
    def __init__(self):
        import pygame

        if not pygame.mixer.get_init():
            pygame.mixer.init()
        self._pygame = pygame
        self._volume = 0.8

    def set_volume(self, percent: int) -> None:
        self._volume = max(0, min(100, int(percent))) / 100.0
        self._pygame.mixer.music.set_volume(self._volume)

    def play(self, path) -> None:
        path = str(Path(path))
        self._pygame.mixer.music.load(path)
        self._pygame.mixer.music.set_volume(self._volume)
        self._pygame.mixer.music.play()

    def stop(self) -> None:
        self._pygame.mixer.music.stop()
        try:
            self._pygame.mixer.music.unload()
        except Exception:
            pass

    def is_playing(self) -> bool:
        return bool(self._pygame.mixer.music.get_busy())


class NullPlayer:
    """Used when audio initialisation fails; every call is a safe no-op."""

    def __init__(self, reason: str = ""):
        self.reason = reason

    def set_volume(self, percent: int) -> None:
        pass

    def play(self, path) -> None:
        pass

    def stop(self) -> None:
        pass

    def is_playing(self) -> bool:
        return False


def create_player() -> object:
    try:
        return PygamePlayer()
    except Exception as exc:  # no audio device, missing drivers, etc.
        return NullPlayer(str(exc))
