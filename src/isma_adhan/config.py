"""App configuration: paths, defaults, JSON persistence.

Config and user sounds live in %APPDATA%\\IsmaAdhan on Windows
(falls back to a platform-appropriate home directory elsewhere).
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from .cities import DEFAULT_CITY, has_city

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
        "alerts": base / "sounds" / "alerts",
    }


@dataclass
class Settings:
    # location / calculation
    city: str = DEFAULT_CITY
    use_custom_coords: bool = False
    custom_lat: float = 30.0444
    custom_lng: float = 31.2357
    timezone_name: str = "Africa/Cairo"
    method: str = "egypt"

    # alerts
    pre_adhan_minutes: int = 5      # 0 = off, else 5 / 10 / 15
    iqama_minutes: int = 10         # 0 = off
    volume: int = 80                # 0..100
    adhan_sound: str = ""           # file path; empty = chime + spoken name
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

    def lat_lng(self) -> tuple:
        if self.use_custom_coords:
            return self.custom_lat, self.custom_lng
        if has_city(self.city):
            from .cities import city_coords

            return city_coords(self.city)
        from .cities import city_coords

        return city_coords(DEFAULT_CITY)


def settings_path(base: Path = None) -> Path:
    return (base or app_data_dir()) / "settings.json"


def load_settings(base: Path = None) -> Settings:
    path = settings_path(base)
    if not path.exists():
        return Settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        # a corrupt config must never break the app
        return Settings()
    known = {f.name for f in fields(Settings)}
    clean = {k: v for k, v in data.items() if k in known}
    try:
        return Settings(**clean)
    except TypeError:
        return Settings()


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
