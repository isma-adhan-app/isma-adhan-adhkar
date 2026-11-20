"""Approximate Hijri (Islamic) date, Kuwaiti algorithm. Offline, no deps.

Astronomical approximation: can differ by +/-1 day from moon-sighting based
calendars. Displayed as informational text in the main window.
"""
from __future__ import annotations

from datetime import date

HIJRI_MONTHS_AR = [
    "محرم",
    "صفر",
    "ربيع الأول",
    "ربيع الآخر",
    "جمادى الأولى",
    "جمادى الآخرة",
    "رجب",
    "شعبان",
    "رمضان",
    "شوال",
    "ذو القعدة",
    "ذو الحجة",
]

WEEKDAYS_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]


def _jd(y: int, m: int, d: int) -> int:
    """Integer Julian day for a Gregorian date."""
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524


def gregorian_to_hijri(y: int, m: int, d: int) -> tuple:
    """(hijri_year, hijri_month, hijri_day); hijri_month is 1..12."""
    jd = _jd(y, m, d)
    l = jd - 1948440 + 10632
    n = (l - 1) // 10631
    l = l - 10631 * n + 354
    j = ((10985 - l) // 5316) * ((50 * l) // 17719) + (l // 5670) * ((43 * l) // 15238)
    l = l - ((30 - j) // 15) * ((17719 * j) // 50) - (j // 16) * ((15238 * j) // 43) + 29
    month = (24 * l) // 709
    day = l - (709 * month) // 24
    year = 30 * n + j - 30
    return year, month, day


def hijri_label(day: date) -> str:
    hy, hm, hd = gregorian_to_hijri(day.year, day.month, day.day)
    return f"{hd} {HIJRI_MONTHS_AR[hm - 1]} {hy} هـ"


def weekday_label(day: date) -> str:
    return WEEKDAYS_AR[day.weekday()]
