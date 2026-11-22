"""App configuration: paths, defaults, JSON persistence, v1.1 migration.

Config and user sounds live in %APPDATA%\IsmaAdhan on Windows
(falls back to a platform-appropriate home directory elsewhere).

v1.1 changes with automatic migration of a v1.0 settings file:
- location is stored as explicit lat/lng/timezone + country/city names;
  an old Egyptian ``city`` name is resolved through the built-in city list.
- pre_adhan_minutes / iqama_minutes scalars become per-prayer dicts.
- the single adhan_sound becomes adhan_sounds["all"].
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from .cities import DEFAULT_CITY, city_coords, has_city
from .prayer_times import ADHAN_PRAYERS

APP_NAME = "IsmaAdhan"


def app_data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME
    # dev / testing on other platforms
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME


def sound_dirs(base: Path = None) -> dict:
    base = base or app_data_dir()
    return {
        "adhan": base / "sounds" / "adhan",
        "adhkar": base / "sounds" / "adhkar",
        # v1.7: one user library folder per alert kind (pre-adhan reminder,
        # iqama). The old shared "alerts" folder was never exposed in the UI.
        "pre_adhan": base / "sounds" / "pre_adhan",
        "iqama": base / "sounds" / "iqama",
    }


def _per_prayer(default: int) -> dict:
    return {p: default for p in ADHAN_PRAYERS}


@dataclass
class Settings:
    # location / calculation
    country: str = "مصر"
    city: str = DEFAULT_CITY
    lat: float = 30.0444
    lng: float = 31.2357
    timezone_name: str = "Africa/Cairo"
    method: str = "egypt"
    # v1.8: UI language - "auto" follows the Windows display language
    language: str = "auto"

    # per-prayer alerts (minutes; 0 = off for pre/post)
    pre_adhan_per: dict = field(default_factory=lambda: _per_prayer(5))
    iqama_per: dict = field(default_factory=lambda: _per_prayer(10))
    post_adhkar_per: dict = field(default_factory=lambda: _per_prayer(0))

    # sounds
    volume: int = 80                # 0..100
    adhan_sounds: dict = field(default_factory=dict)  # "all" or prayer name -> adhan entry
    # v1.7: same vocabulary as adhan_sounds but "alerts:<key>" entries, for
    # the pre-adhan reminder and the iqama alert
    pre_adhan_sounds: dict = field(default_factory=dict)
    iqama_sounds: dict = field(default_factory=dict)
    # post-prayer adhkar: empty entry keeps the shuffled-rotation default
    post_adhkar_sounds: dict = field(default_factory=dict)
    bismillah_voice: str = "husary"   # key into sounds.BISMILLAH_VOICES
    speak_prayer_name: bool = True  # spoken announcement alongside sounds

    # adhkar loop
    adhkar_enabled: bool = True
    adhkar_interval_minutes: int = 15   # 0 = off
    adhkar_quiet_hours: bool = True     # don't play adhkar clips overnight
    quiet_start: str = "23:00"          # HH:MM local
    quiet_end: str = "05:00"

    # friday surat al-kahf reminder
    kahf_enabled: bool = True
    kahf_time: str = "10:00"            # HH:MM local, Friday

    # system
    autostart: bool = False
    start_minimized: bool = False

    # ------------------------------------------------------------ accessors
    def lat_lng(self) -> tuple:
        return self.lat, self.lng

    def pre_adhan_for(self, prayer: str) -> int:
        return int(self.pre_adhan_per.get(prayer, self.pre_adhan_per.get("all", 5)))

    def iqama_for(self, prayer: str) -> int:
        return int(self.iqama_per.get(prayer, self.iqama_per.get("all", 10)))

    def post_adhkar_for(self, prayer: str) -> int:
        return int(self.post_adhkar_per.get(prayer, self.post_adhkar_per.get("all", 0)))

    def adhan_sound_for(self, prayer: str) -> str:
        return self.adhan_sounds.get(prayer) or self.adhan_sounds.get("all") or ""

    def pre_adhan_sound_for(self, prayer: str) -> str:
        return self.pre_adhan_sounds.get(prayer) or self.pre_adhan_sounds.get("all") or ""

    def iqama_sound_for(self, prayer: str) -> str:
        return self.iqama_sounds.get(prayer) or self.iqama_sounds.get("all") or ""

    def post_adhkar_sound_for(self, prayer: str) -> str:
        return self.post_adhkar_sounds.get(prayer) or self.post_adhkar_sounds.get("all") or ""


def settings_path(base: Path = None) -> Path:
    return (base or app_data_dir()) / "settings.json"


def _migrate(data: dict) -> dict:
    """Translate v1.0 keys/values in-place to the v1.1 shape."""
    if isinstance(data.get("pre_adhan_minutes"), int):
        data["pre_adhan_per"] = _per_prayer(data.pop("pre_adhan_minutes"))
    else:
        data.pop("pre_adhan_minutes", None)
    if isinstance(data.get("iqama_minutes"), int):
        data["iqama_per"] = _per_prayer(data.pop("iqama_minutes"))
    else:
        data.pop("iqama_minutes", None)
    old_adhan = data.pop("adhan_sound", None)
    if old_adhan and not data.get("adhan_sounds"):
        data["adhan_sounds"] = {"all": old_adhan}
    # old model: city name + use_custom_coords flag -> explicit coordinates.
    # Only touch lat/lng when the file does not already carry explicit values
    # (a v1.1 file round-trips unchanged).
    use_custom = data.pop("use_custom_coords", False)
    old_lat, old_lng = data.pop("custom_lat", None), data.pop("custom_lng", None)
    has_explicit = isinstance(data.get("lat"), (int, float)) and isinstance(data.get("lng"), (int, float))
    if not has_explicit:
        if use_custom and isinstance(old_lat, (int, float)) and isinstance(old_lng, (int, float)):
            data["lat"], data["lng"] = old_lat, old_lng
        elif isinstance(data.get("city"), str) and has_city(data["city"]):
            data["lat"], data["lng"] = city_coords(data["city"])
            data.setdefault("country", "مصر")
    return data


def load_settings(base: Path = None) -> Settings:
    path = settings_path(base)
    if not path.exists():
        return first_run_settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        # a corrupt config must never break the app
        return Settings()
    data = _migrate(data)
    known = {f.name for f in fields(Settings)}
    clean = {k: v for k, v in data.items() if k in known}
    try:
        return Settings(**clean)
    except TypeError:
        return Settings()


def first_run_settings() -> Settings:
    """Defaults for a brand-new install: detect location from Windows when possible."""
    s = Settings()
    try:
        from .world import country_display, detect_location

        found = detect_location()
        if found:
            city = found["city"]
            s.country = country_display(found["iso"])
            s.city = city.get("ar") or city["en"]
            s.lat, s.lng, s.timezone_name = city["lat"], city["lng"], city["tz"]
    except Exception:
        pass
    return s


def save_settings(settings: Settings, base: Path = None) -> Path:
    path = settings_path(base)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def ensure_dirs(base: Path = None) -> None:
    for d in sound_dirs(base).values():
        d.mkdir(parents=True, exist_ok=True)
