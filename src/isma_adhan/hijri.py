"""Approximate Hijri (Islamic) date, Kuwaiti algorithm. Offline, no deps.

Astronomical approximation: can differ by +/-1 day from moon-sighting based
calendars. Displayed as informational text in the main window.
"""
from __future__ import annotations

from datetime import date

from . import strings

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

HIJRI_MONTHS_EN = [
    "Muharram", "Safar", "Rabi al-Awwal", "Rabi al-Thani",
    "Jumada al-Ula", "Jumada al-Akhirah", "Rajab", "Shaban",
    "Ramadan", "Shawwal", "Dhul-Qadah", "Dhul-Hijjah",
]

HIJRI_MONTHS_FR = [
    "Mouharram", "Safar", "Rabi al-Awwal", "Rabi al-Thani",
    "Joumada al-Oula", "Joumada al-Akhira", "Rajab", "Chaabane",
    "Ramadan", "Chawwal", "Dhou al-Qada", "Dhou al-Hijja",
]

WEEKDAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
               "Saturday", "Sunday"]

WEEKDAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi",
               "samedi", "dimanche"]

GREGORIAN_MONTHS_EN = [
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
]

GREGORIAN_MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
    "août", "septembre", "octobre", "novembre", "décembre",
]

_HIJRI_MONTHS = {"ar": HIJRI_MONTHS_AR, "en": HIJRI_MONTHS_EN, "fr": HIJRI_MONTHS_FR}
_WEEKDAYS = {"ar": WEEKDAYS_AR, "en": WEEKDAYS_EN, "fr": WEEKDAYS_FR}
_GREGORIAN_MONTHS = {"ar": GREGORIAN_MONTHS_AR, "en": GREGORIAN_MONTHS_EN,
                     "fr": GREGORIAN_MONTHS_FR}
_HIJRI_SUFFIX = {"ar": "هـ", "en": "AH", "fr": "de l'hégire"}
_GREGORIAN_SUFFIX = {"ar": "م", "en": "AD", "fr": ""}


def hijri_month_name(month: int) -> str:
    """1-based Hijri month name in the current UI language."""
    return _HIJRI_MONTHS.get(strings.current_language(), HIJRI_MONTHS_AR)[month - 1]


def gregorian_month_name(month: int) -> str:
    """1-based Gregorian month name in the current UI language."""
    return _GREGORIAN_MONTHS.get(strings.current_language(), GREGORIAN_MONTHS_AR)[month - 1]


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
    suffix = _HIJRI_SUFFIX.get(strings.current_language(), "هـ")
    return f"{hd} {hijri_month_name(hm)} {hy} {suffix}".strip()


def weekday_label(day: date) -> str:
    return _WEEKDAYS.get(strings.current_language(), WEEKDAYS_AR)[day.weekday()]


def gregorian_label(day: date) -> str:
    """Gregorian date in words in the current UI language, e.g. '21 نوفمبر 2026 م'
    - the form a screen reader speaks naturally, instead of digits and dashes."""
    suffix = _GREGORIAN_SUFFIX.get(strings.current_language(), "م")
    return f"{day.day} {gregorian_month_name(day.month)} {day.year} {suffix}".strip()


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


_NOTABLE_EN = dict(zip(NOTABLE_DATES, [
    "Islamic New Year", "Ashura", "the Prophet's birthday", "Isra and Miraj",
    "the middle of Shaban", "the first day of Ramadan", "Laylat al-Qadr",
    "the first day of Eid al-Fitr", "the Day of Arafah", "the first day of Eid al-Adha",
]))
_NOTABLE_FR = dict(zip(NOTABLE_DATES, [
    "le Nouvel An hégirien", "Achoura", "la naissance du Prophète", "Al-Isra et Al-Miraj",
    "la mi-Chaabane", "le premier jour du Ramadan", "Laylat al-Qadr",
    "le premier jour de l'Aïd al-Fitr", "le jour d'Arafat", "le premier jour de l'Aïd al-Adha",
]))

def notable_label(day: date) -> "str | None":
    hy, hm, hd = gregorian_to_hijri(day.year, day.month, day.day)
    table = {"en": _NOTABLE_EN, "fr": _NOTABLE_FR}.get(strings.current_language(), NOTABLE_DATES)
    return table.get((hm, hd))


def notable_announcement(day: date) -> str:
    """Sentence for the launch speech when today/tomorrow is a notable date,
    e.g. 'غداً أول شهر رمضان.'; empty string otherwise."""
    from datetime import timedelta

    today = notable_label(day)
    tomorrow = notable_label(day + timedelta(days=1))
    lang = strings.current_language()
    if lang == "en":
        return " ".join(x for x in (f"Today is {today}." if today else "",
                                     f"Tomorrow is {tomorrow}." if tomorrow else "") if x)
    if lang == "fr":
        return " ".join(x for x in (f"Aujourd'hui : {today}." if today else "",
                                     f"Demain : {tomorrow}." if tomorrow else "") if x)
    if today and tomorrow:
        return f"اليوم {today}، وغداً {tomorrow}."
    if today:
        return f"اليوم {today}."
    if tomorrow:
        return f"غداً {tomorrow}."
    return ""
