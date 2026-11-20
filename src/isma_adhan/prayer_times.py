"""Offline prayer-time calculation.

Implements the well-known PrayTimes.org astronomical algorithm (public domain,
Hamid Zarrabi-Zadeh), with the Egyptian General Authority of Survey method
(Fajr 19.5 degrees, Isha 17.5 degrees) as the default.

No network access is required. Timezone/DST handling uses the IANA database
through ``zoneinfo`` (ship the ``tzdata`` package in the Windows build).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

# Prayers the app reports, in daily order.
PRAYERS = ("fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha")

# Prayers that have an adhan (sunrise does not).
ADHAN_PRAYERS = ("fajr", "dhuhr", "asr", "maghrib", "isha")

ARABIC_NAMES = {
    "fajr": "الفجر",
    "sunrise": "الشروق",
    "dhuhr": "الظهر",
    "asr": "العصر",
    "maghrib": "المغرب",
    "isha": "العشاء",
}

# Calculation methods (angle-based). The Egyptian method is the default and
# the only one exposed in the v1 UI; the rest are here for future releases.
METHODS = {
    "egypt": {"fajr_angle": 19.5, "isha_angle": 17.5, "label_ar": "الهيئة المصرية العامة للمساحة"},
    "mwl": {"fajr_angle": 18.0, "isha_angle": 17.0, "label_ar": "رابطة العالم الإسلامي"},
    "isna": {"fajr_angle": 15.0, "isha_angle": 15.0, "label_ar": "ISNA"},
}

DEFAULT_METHOD = "egypt"


def _sin(deg: float) -> float:
    return math.sin(math.radians(deg))


def _cos(deg: float) -> float:
    return math.cos(math.radians(deg))


def _tan(deg: float) -> float:
    return math.tan(math.radians(deg))


def _arcsin(x: float) -> float:
    return math.degrees(math.asin(max(-1.0, min(1.0, x))))


def _arccos(x: float) -> float:
    return math.degrees(math.acos(max(-1.0, min(1.0, x))))


def _arccot(x: float) -> float:
    return math.degrees(math.atan(1.0 / x))


def _arctan2(y: float, x: float) -> float:
    return math.degrees(math.atan2(y, x))


def _fix_angle(a: float) -> float:
    a = a % 360.0
    return a + 360.0 if a < 0 else a


def _fix_hour(a: float) -> float:
    a = a % 24.0
    return a + 24.0 if a < 0 else a


def _julian(year: int, month: int, day: int) -> float:
    """Julian day number for a Gregorian date (as in the PrayTimes code)."""
    if month <= 2:
        year -= 1
        month += 12
    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)
    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day
        + b
        - 1524.5
    )


@dataclass(frozen=True)
class DailyPrayerTimes:
    """Prayer times for one day, as timezone-aware datetimes."""

    day: date
    times: dict  # prayer name -> datetime

    def ordered(self) -> list:
        return [(name, self.times[name]) for name in PRAYERS]

    def next_prayer(self, now: datetime) -> tuple:
        """(name, datetime) of the next prayer strictly after ``now``, or None."""
        for name in PRAYERS:
            if self.times[name] > now:
                return name, self.times[name]
        return None


class _Core:
    """Direct port of the PrayTimes.org math."""

    def __init__(self, lat: float, fajr_angle: float, isha_angle: float, asr_factor: int = 1):
        self.lat = lat
        self.fajr_angle = fajr_angle
        self.isha_angle = isha_angle
        self.asr_factor = asr_factor
        self.j_date = 0.0

    # --- sun position -----------------------------------------------------
    def sun_position(self, jd: float) -> tuple:
        d = jd - 2451545.0
        g = _fix_angle(357.529 + 0.98560028 * d)
        q = _fix_angle(280.459 + 0.98564736 * d)
        l = _fix_angle(q + 1.915 * _sin(g) + 0.020 * _sin(2 * g))
        e = 23.439 - 0.00000036 * d
        ra = _arctan2(_cos(e) * _sin(l), _cos(l)) / 15.0
        decl = _arcsin(_sin(e) * _sin(l))
        eqt = q / 15.0 - _fix_hour(ra)
        return decl, eqt

    def mid_day(self, time_portion: float) -> float:
        _, eqt = self.sun_position(self.j_date + time_portion)
        return _fix_hour(12.0 - eqt)

    @staticmethod
    def rise_set_angle() -> float:
        elv = 0.833
        return 0.0347 * math.sqrt(elv) + elv

    # --- times ------------------------------------------------------------
    def sun_angle_time(self, angle: float, time_portion: float, direction: str = None) -> float:
        decl, _ = self.sun_position(self.j_date + time_portion)
        noon = self.mid_day(time_portion)
        cos_t = (-_sin(angle) - _sin(decl) * _sin(self.lat)) / (_cos(decl) * _cos(self.lat))
        t = _arccos(cos_t) / 15.0
        return noon + (-t if direction == "ccw" else t)

    def asr_time(self, factor: int, time_portion: float) -> float:
        decl, _ = self.sun_position(self.j_date + time_portion)
        angle = -_arccot(factor + _tan(abs(self.lat - decl)))
        return self.sun_angle_time(angle, time_portion)

    def compute_float_hours(self, year: int, month: int, day: int, lng: float, tz_offset_hours: float) -> dict:
        """Prayer times as float hours on the local clock."""
        self.j_date = _julian(year, month, day) - lng / (15.0 * 24.0)
        seeds = {"fajr": 5, "sunrise": 6, "dhuhr": 12, "asr": 13, "sunset": 18, "maghrib": 18, "isha": 18}
        p = {k: v / 24.0 for k, v in seeds.items()}  # day portions
        out = {
            "fajr": self.sun_angle_time(self.fajr_angle, p["fajr"], "ccw"),
            "sunrise": self.sun_angle_time(self.rise_set_angle(), p["sunrise"], "ccw"),
            "dhuhr": self.mid_day(p["dhuhr"]),
            "asr": self.asr_time(self.asr_factor, p["asr"]),
            "sunset": self.sun_angle_time(self.rise_set_angle(), p["sunset"]),
            "maghrib": self.sun_angle_time(self.rise_set_angle(), p["maghrib"]),  # Egypt: maghrib == sunset
            "isha": self.sun_angle_time(self.isha_angle, p["isha"]),
        }
        # to local clock time: solar time is lng/15 ahead of UTC, then the
        # timezone (with DST) shifts it onto the wall clock
        return {k: v + tz_offset_hours - lng / 15.0 for k, v in out.items() if k != "sunset"}


class PrayerTimeCalculator:
    """High-level API: prayer times for a date/place as local datetimes."""

    def __init__(self, lat: float, lng: float, tz_name: str = "Africa/Cairo", method: str = DEFAULT_METHOD):
        self.lat = float(lat)
        self.lng = float(lng)
        self.tz = ZoneInfo(tz_name)
        params = METHODS[method]
        self.method = method
        self.fajr_angle = params["fajr_angle"]
        self.isha_angle = params["isha_angle"]

    def for_date(self, day: date) -> DailyPrayerTimes:
        core = _Core(self.lat, self.fajr_angle, self.isha_angle)
        # offset (incl. DST) at local noon; Egypt changes clocks at midnight,
        # so every prayer time of the day shares this offset
        noon = datetime(day.year, day.month, day.day, 12, tzinfo=self.tz)
        offset_hours = noon.utcoffset().total_seconds() / 3600.0
        hours = core.compute_float_hours(day.year, day.month, day.day, self.lng, offset_hours)
        midnight = datetime(day.year, day.month, day.day)
        result = {}
        for name in PRAYERS:
            h = hours[name]
            # round to the nearest minute, PrayTimes convention (add 30 s then floor)
            seconds = math.floor(h * 3600.0 + 30.0)
            dt = midnight + timedelta(seconds=seconds)
            result[name] = dt.replace(tzinfo=self.tz)
        return DailyPrayerTimes(day=day, times=result)

    def next_prayer(self, now: datetime) -> tuple:
        """(name, datetime) of the next prayer, looking at today and tomorrow."""
        today = self.for_date(now.date())
        nxt = today.next_prayer(now)
        if nxt:
            return nxt
        tomorrow = self.for_date(now.date() + timedelta(days=1))
        return tomorrow.ordered()[0]
