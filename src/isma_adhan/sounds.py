"""Sound library management.

Categories:
- adhan: full adhan recordings, one is selected as the adhan sound
- adhkar: short dhikr clips, played in random order on the adhkar interval
- alerts: short tones (pre-adhan reminder, iqama); built-in defaults ship
  with the app, the user can add his own
"""
from __future__ import annotations

import random
import shutil
import sys
from pathlib import Path

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg"}

DEFAULT_ALERT_TONES = {
    "pre_adhan": "soft_chime.wav",
    "iqama": "iqama_tone.wav",
    "fallback_adhan": "attention.wav",
    "kahf": "soft_chime.wav",
}


def resource_path(*parts: str) -> Path:
    """Path to a bundled resource, works both from source and PyInstaller."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base, *parts)
    return Path(__file__).resolve().parents[2].joinpath(*parts)


def default_tone(kind: str) -> Path:
    return resource_path("assets", "sounds", DEFAULT_ALERT_TONES[kind])


def list_sounds(directory: Path) -> list:
    if not directory.exists():
        return []
    return sorted(
        (p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS),
        key=lambda p: p.name.lower(),
    )


def display_name(path: Path) -> str:
    return Path(path).stem


def add_sound(source: Path, directory: Path) -> Path:
    """Copy an audio file into a library folder; returns the new path."""
    source = Path(source)
    if source.suffix.lower() not in AUDIO_EXTENSIONS:
        raise ValueError(f"unsupported audio type: {source.suffix}")
    directory.mkdir(parents=True, exist_ok=True)
    dest = directory / source.name
    if dest.resolve() == source.resolve():
        return dest
    stem, suffix, i = source.stem, source.suffix, 1
    while dest.exists():
        dest = directory / f"{stem} ({i}){suffix}"
        i += 1
    shutil.copy2(source, dest)
    return dest


class ShuffledRotation:
    """Plays every clip once per cycle, in random order (a shuffled bag).

    When the bag empties it is refilled from the current library and
    reshuffled, so repeats only happen after every clip has played.
    Files removed from the library are dropped from the bag.
    """

    def __init__(self, rng: random.Random = None):
        self._rng = rng or random.Random()
        self._bag: list = []

    def next(self, paths) -> Path:
        paths = [str(p) for p in paths]
        if not paths:
            self._bag = []
            return None
        self._bag = [p for p in self._bag if p in paths]
        if not self._bag:
            self._bag = list(paths)
            self._rng.shuffle(self._bag)
        return Path(self._bag.pop(0))
