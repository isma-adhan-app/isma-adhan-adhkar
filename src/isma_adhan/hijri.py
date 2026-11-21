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

GREGORIAN_MONTHS_AR = [
    "يناير",
    "فبراير",
    "مارس",
    "أبريل",
    "مايو",
    "يونيو",
    "يوليو",
    "أغسطس",
    "سبتمبر",
    "أكتوبر",
    "نوفمبر",
    "ديسمبر",
]


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


def gregorian_label(day: date) -> str:
    """Gregorian date in Arabic words, e.g. '21 نوفمبر 2026 م' - the form a
    screen reader speaks naturally, instead of digits and dashes."""
    return f"{day.day} {GREGORIAN_MONTHS_AR[day.month - 1]} {day.year} م"


def _jd_to_gregorian(jd: int) -> tuple:
    """(year, month, day) for an integer Julian day."""
    l = jd + 68569
    n = (4 * l) // 146097
    l -= (146097 * n + 3) // 4
    i = (4000 * (l + 1)) // 1461001
    l -= (1461 * i) // 4 - 31
    j = (80 * l) // 2447
    d = l - (2447 * j) // 80
    l = j // 11
    m = j + 2 - 12 * l
    y = 100 * (n - 49) + i + l
    return y, m, d


def hijri_to_gregorian(hy: int, hm: int, hd: int) -> tuple:
    """(gregorian_year, month, day) for a Hijri date - inverse of
    gregorian_to_hijri (same Kuwaiti algorithm, so round-trips are exact)."""
    jd = (
        hd
        + int(29.5 * (hm - 1) + 0.999999)
        + (hy - 1) * 354
        + (3 + 11 * hy) // 30
        + 1948440
        - 1
    )
    return _jd_to_gregorian(jd)


# Notable Islamic dates: (hijri_month, hijri_day) -> arabic label.
NOTABLE_DATES = {
    (1, 1): "رأس السنة الهجرية",
    (1, 10): "يوم عاشوراء",
    (3, 12): "المولد النبوي الشريف",
    (7, 27): "ليلة الإسراء والمعراج",
    (8, 15): "ليلة النصف من شعبان",
    (9, 1): "أول شهر رمضان",
    (9, 27): "ليلة القدر",
    (10, 1): "أول أيام عيد الفطر",
    (12, 9): "يوم عرفة",
    (12, 10): "أول أيام عيد الأضحى",
}


def notable_label(day: date) -> "str | None":
    hy, hm, hd = gregorian_to_hijri(day.year, day.month, day.day)
    return NOTABLE_DATES.get((hm, hd))


def notable_announcement(day: date) -> str:
    """Sentence for the launch speech when today/tomorrow is a notable date,
    e.g. 'غداً أول شهر رمضان.'; empty string otherwise."""
    from datetime import timedelta

    today = notable_label(day)
    tomorrow = notable_label(day + timedelta(days=1))
    if today and tomorrow:
        return f"اليوم {today}، وغداً {tomorrow}."
    if today:
        return f"اليوم {today}."
    if tomorrow:
        return f"غداً {tomorrow}."
    return ""
