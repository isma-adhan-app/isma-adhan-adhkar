"""World location data: countries, cities, coordinates, timezones.

Data lives in assets/world.json (GeoNames, CC-BY 4.0) and
assets/windows_zones.json (CLDR windowsZones). Display names are Arabic where
known, English otherwise.
"""
from __future__ import annotations

import json
import sys

from .sounds import resource_path
from . import strings

_world = None
_zones = None


def _load():
    global _world
    if _world is None:
        with open(resource_path("assets", "world.json"), encoding="utf-8") as f:
            _world = json.load(f)["countries"]
    return _world


def _load_zones() -> dict:
    global _zones
    if _zones is None:
        with open(resource_path("assets", "windows_zones.json"), encoding="utf-8") as f:
            _zones = json.load(f)
    return _zones


def countries() -> list:
    """[(iso, display_name)] sorted for the picker (Arabic name preferred)."""
    out = []
    for c in _load():
        out.append((c["iso"], (c.get("ar") or c["en"]) if strings.current_language() == "ar" else c["en"]))
    return out


def country_display(iso: str) -> str:
    for c in _load():
        if c["iso"] == iso:
            return (c.get("ar") or c["en"]) if strings.current_language() == "ar" else c["en"]
    return iso


def country_iso(display: str) -> str:
    """Resolve stored legacy names without changing location when UI changes."""
    for c in _load():
        if display in (c["iso"], c["en"], c.get("ar")):
            return c["iso"]
    return ""


def cities_of(iso: str) -> list:
    """[{'en','ar'?,'lat','lng','tz','pop'}] for one country, biggest first."""
    for c in _load():
        if c["iso"] == iso:
            return c["cities"]
    return []


def city_display(city: dict) -> str:
    return (city.get("ar") or city["en"]) if strings.current_language() == "ar" else city["en"]


def _iana_from_windows_tz(windows_name: str):
    return _load_zones().get(windows_name)


def _windows_timezone_name() -> str:
    if sys.platform != "win32":
        return ""
    try:
        import ctypes

        class DYNAMIC_TIME_ZONE_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("Bias", ctypes.c_long),
                ("StandardName", ctypes.c_wchar * 32),
                ("StandardDate", ctypes.c_byte * 16),
                ("StandardBias", ctypes.c_long),
                ("DaylightName", ctypes.c_wchar * 32),
                ("DaylightDate", ctypes.c_byte * 16),
                ("DaylightBias", ctypes.c_long),
                ("TimeZoneKeyName", ctypes.c_wchar * 128),
                ("DynamicDaylightTimeDisabled", ctypes.c_ushort),
            ]

        info = DYNAMIC_TIME_ZONE_INFORMATION()
        ctypes.windll.kernel32.GetDynamicTimeZoneInformation(ctypes.byref(info))
        return info.TimeZoneKeyName or ""
    except Exception:
        return ""


def _windows_geo_iso() -> str:
    if sys.platform != "win32":
        return ""
    try:
        import ctypes

        buf = ctypes.create_unicode_buffer(16)
        # GetUserDefaultGeoName returns ISO 3166-1 alpha-2 (Windows 10 1709+)
        n = ctypes.windll.kernel32.GetUserDefaultGeoName(buf, 16)
        return buf.value if n else ""
    except Exception:
        return ""


def detect_location() -> "dict | None":
    """Best-guess location from Windows timezone + region settings.

    Returns {'iso', 'city'} where city is an entry from cities_of(iso),
    or None when detection is impossible. Never raises.
    """
    try:
        iana = _iana_from_windows_tz(_windows_timezone_name())
        if not iana:
            return None
        geo_iso = _windows_geo_iso()
        if geo_iso:
            local = [c for c in cities_of(geo_iso) if c["tz"] == iana]
            if local:
                return {"iso": geo_iso, "city": max(local, key=lambda c: c["pop"])}
        anywhere = [
            (c["iso"], city)
            for c in _load()
            for city in c["cities"]
            if city["tz"] == iana
        ]
        if not anywhere:
            return None
        best_iso, best = max(anywhere, key=lambda ic: ic[1]["pop"])
        return {"iso": best_iso, "city": best}
    except Exception:
        return None
