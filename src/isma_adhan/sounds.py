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


def bundled_adhkar() -> list:
    """Bundled dhikr clips shipped with the app: [(path, arabic_text)].

    Real recitations from the Hisn al-Muslim audiobook (Sheikh Sulaiman
    Al-Shuwayhi, via IslamHouse - see README licensing); the mapping file
    records the chapter title of each clip so the UI/log can show it.
    """
    import json

    index = resource_path("assets", "sounds", "adhkar_bundled.json")
    if not index.exists():
        return []
    try:
        data = json.loads(index.read_text(encoding="utf-8"))
    except Exception:
        return []
    base = resource_path("assets", "sounds", "adhkar_bundled")
    out = []
    for name, text in data.items():
        p = base / name
        if p.exists():
            out.append((p, text))
    return out


def all_adhkar(user_dir: Path) -> list:
    """Merged adhkar rotation pool: bundled clips + the user's own clips.

    Returns [(path, display_label)]; user clips show their file name.
    """
    out = [(p, text) for p, text in bundled_adhkar()]
    out += [(p, display_name(p)) for p in list_sounds(user_dir)]
    return out


BISMILLAH_VOICES = [
    # key, arabic display name, clip length in seconds (measured at fetch time)
    ("husary", "محمود خليل الحصري", 5.2),
    ("banna", "محمود علي البنا", 9.3),
    ("abdulbasit", "عبد الباسط عبد الصمد", 4.5),
    ("minshawi", "محمد صديق المنشاوي", 5.0),
]


def resolve_bismillah_voice(voice: str) -> str:
    """'random' picks one reciter per call; anything else passes through."""
    if voice == "random":
        import random

        return random.choice([k for k, *_ in BISMILLAH_VOICES])
    return voice


def bismillah_path(voice: str) -> "Path | None":
    """Bundled Bismillah clip for one reciter (real recordings, EveryAyah -
    see README licensing note). None when unknown/missing; caller falls back
    to the generated bismillah.wav."""
    keys = {k for k, *_ in BISMILLAH_VOICES}
    if voice not in keys:
        return None
    p = resource_path("assets", "sounds", "bismillah", f"{voice}.mp3")
    return p if p.exists() else None


def bismillah_voice_name(voice: str) -> str:
    for k, name, *_ in BISMILLAH_VOICES:
        if k == voice:
            return name
    return voice


def bismillah_voice_seconds(voice: str) -> float:
    for k, _, secs, *_ in BISMILLAH_VOICES:
        if k == voice:
            return secs
    return 5.0


ADHAN_VOICES = [
    # key, arabic display name, clip length in seconds (measured at fetch time)
    ("husary", "محمود خليل الحصري - أذان القاهرة", 127.5),
    ("minshawi", "محمد صديق المنشاوي", 251.6),
    ("mustafa", "مصطفى إسماعيل", 184.0),
    ("refaat", "محمد رفعت - أذان القاهرة", 203.7),
]
ADHAN_DEFAULT_VOICE = "husary"
ADHAN_BUNDLED_PREFIX = "bundled:"
ADHAN_RANDOM_TOKEN = "bundled:random"


def adhan_voice_path(key: str) -> "Path | None":
    """Bundled adhan clip for one muezzin (real recordings, IslamWeb - see
    README licensing note). None when unknown/missing."""
    keys = {k for k, *_ in ADHAN_VOICES}
    if key not in keys:
        return None
    p = resource_path("assets", "sounds", "adhan", f"{key}.mp3")
    return p if p.exists() else None


def adhan_voice_name(key: str) -> str:
    for k, name, *_ in ADHAN_VOICES:
        if k == key:
            return name
    return key


def bundled_adhan() -> list:
    """Bundled adhan recordings shipped with the app: [(path, label)]."""
    out = []
    for key, name, *_ in ADHAN_VOICES:
        p = adhan_voice_path(key)
        if p is not None:
            out.append((p, name))
    return out


def resolve_adhan(value: "str | None", user_dir: "Path | None" = None) -> "Path | None":
    """Resolve a stored adhan_sounds entry to a playable path.

    Empty/None -> the default bundled muezzin; 'bundled:random' -> a random
    clip from the bundled muezzins AND the user's own adhan folder (a new
    pick on every call); 'bundled:<key>' -> that muezzin; anything else is a
    user file path and is returned only when the file exists.
    """
    if not value:
        return adhan_voice_path(ADHAN_DEFAULT_VOICE)
    if value == ADHAN_RANDOM_TOKEN:
        pool = [p for p, _ in bundled_adhan()]
        if user_dir is not None:
            pool += list_sounds(Path(user_dir))
        return random.choice(pool) if pool else None
    if value.startswith(ADHAN_BUNDLED_PREFIX):
        return adhan_voice_path(value[len(ADHAN_BUNDLED_PREFIX):])
    p = Path(value)
    return p if p.exists() else None


def adhan_display(value: "str | None") -> str:
    """Arabic label for a stored adhan_sounds entry, for the settings UI."""
    if not value:
        return adhan_voice_name(ADHAN_DEFAULT_VOICE)
    if value == ADHAN_RANDOM_TOKEN:
        return "عشوائي"
    if value.startswith(ADHAN_BUNDLED_PREFIX):
        return adhan_voice_name(value[len(ADHAN_BUNDLED_PREFIX):])
    return display_name(Path(value))


# ---------------------------------------------------------------------------
# Alert sounds (v1.7): the pre-adhan reminder and the iqama alert each get
# the same treatment as adhan voices - built-in clips we ship, the user's own
# files (one library folder per kind), per-prayer assignment, and a random
# option drawing from bundled clips AND the user's folder.

ALERT_KINDS = ("pre_adhan", "iqama")

ALERT_BUNDLED = {
    # key, arabic display name, wav file under assets/sounds (generated by
    # tools/make_tones.py - our own tones, no licensing constraints)
    "pre_adhan": [
        ("soft_chime", "جرس هادئ", "soft_chime.wav"),
        ("chime_up", "نغمة صاعدة", "pre_chime_up.wav"),
        ("chime_triple", "ثلاث نغمات هادئة", "pre_chime_triple.wav"),
    ],
    "iqama": [
        ("iqama_tone", "تنبيه قصير", "iqama_tone.wav"),
        ("iqama_low", "نغمة منخفضة", "iqama_low.wav"),
        ("iqama_triple", "ثلاث نغمات قصيرة", "iqama_triple.wav"),
    ],
}
ALERT_BUNDLED_PREFIX = "alerts:"
ALERT_RANDOM_TOKEN = "alerts:random"


def alert_clip_path(kind: str, key: str) -> "Path | None":
    """Bundled alert clip for one kind+key; None when unknown/missing."""
    for k, _name, filename in ALERT_BUNDLED.get(kind, []):
        if k == key:
            p = resource_path("assets", "sounds", filename)
            return p if p.exists() else None
    return None


def alert_clip_name(kind: str, key: str) -> str:
    for k, name, _f in ALERT_BUNDLED.get(kind, []):
        if k == key:
            return name
    return key


def bundled_alerts(kind: str) -> list:
    """Bundled alert clips for one kind: [(path, label)].

    Kind "post_adhkar" means the bundled adhkar recitations."""
    if kind == "post_adhkar":
        return bundled_adhkar()
    out = []
    for key, name, _f in ALERT_BUNDLED.get(kind, []):
        p = alert_clip_path(kind, key)
        if p is not None:
            out.append((p, name))
    return out


def alert_default_key(kind: str) -> str:
    """The bundled clip used when nothing is chosen (today's behavior)."""
    return ALERT_BUNDLED[kind][0][0]


def resolve_alert(kind: str, value: "str | None", user_dir: "Path | None" = None) -> "Path | None":
    """Resolve a stored alert-sound entry to a playable path.

    Empty/None -> the kind's default bundled tone (the pre-v1.7 behavior);
    'alerts:random' -> a random clip from the bundled tones AND the user's
    own folder for this kind (a new pick on every call); 'alerts:<key>' ->
    that bundled tone; anything else is a user file path and is returned
    only when the file exists.

    Kind "post_adhkar" draws from the adhkar library (bundled clips + the
    user's adhkar folder) and its empty value returns None: the caller keeps
    the pre-v1.7 shuffled-rotation behavior as the default.
    """
    if kind == "post_adhkar":
        if not value:
            return None
        if value == ALERT_RANDOM_TOKEN:
            pool = [p for p, _ in bundled_adhkar()]
            if user_dir is not None:
                pool += list_sounds(Path(user_dir))
            return random.choice(pool) if pool else None
        if value.startswith(ALERT_BUNDLED_PREFIX):
            key = value[len(ALERT_BUNDLED_PREFIX):]
            for p, _text in bundled_adhkar():
                if p.name == key:
                    return p
            return None
        p = Path(value)
        return p if p.exists() else None
    if not value:
        return alert_clip_path(kind, alert_default_key(kind))
    if value == ALERT_RANDOM_TOKEN:
        pool = [p for p, _ in bundled_alerts(kind)]
        if user_dir is not None:
            pool += list_sounds(Path(user_dir))
        return random.choice(pool) if pool else None
    if value.startswith(ALERT_BUNDLED_PREFIX):
        return alert_clip_path(kind, value[len(ALERT_BUNDLED_PREFIX):])
    p = Path(value)
    return p if p.exists() else None


def alert_display(kind: str, value: "str | None") -> str:
    """Arabic label for a stored alert-sound entry, for the settings UI."""
    if kind == "post_adhkar":
        if not value:
            return "تدوير مكتبة الأذكار"
        if value == ALERT_RANDOM_TOKEN:
            return "عشوائي"
        if value.startswith(ALERT_BUNDLED_PREFIX):
            key = value[len(ALERT_BUNDLED_PREFIX):]
            for p, text in bundled_adhkar():
                if p.name == key:
                    return text
            return key
        return display_name(Path(value))
    if not value:
        return alert_clip_name(kind, alert_default_key(kind))
    if value == ALERT_RANDOM_TOKEN:
        return "عشوائي"
    if value.startswith(ALERT_BUNDLED_PREFIX):
        return alert_clip_name(kind, value[len(ALERT_BUNDLED_PREFIX):])
    return display_name(Path(value))


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
