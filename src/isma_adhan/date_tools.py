"""Date converter + monthly prayer-times export (v1.5).

Pure functions so the logic is unit-tested without wx; main_window only
collects input, calls these, and speaks/shows the results.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from .hijri import (
    GREGORIAN_MONTHS_AR,
    HIJRI_MONTHS_AR,
    gregorian_to_hijri,
    hijri_to_gregorian,
    weekday_label,
)
from .prayer_times import ARABIC_NAMES, METHODS, PRAYERS

BAD_DATE_MSG = "لم أفهم التاريخ. اكتبه مثل 21/11/2026 للميلادي أو 1/9/1447 للهجري."


def _parse_dmy(text: str) -> "tuple[int, int, int] | None":
    """(day, month, year) from '21/11/2026', '21-11-2026' or ISO '2026-11-21'."""
    nums = [int(x) for x in re.findall(r"\d+", text)]
    if len(nums) != 3:
        return None
    if nums[0] > 31:  # ISO order: year first
        y, m, d = nums
    else:
        d, m, y = nums
    if not (1 <= m <= 12 and 1 <= d <= 31 and 100 <= y <= 3000):
        return None
    return d, m, y


def convert_date_text(text: str) -> str:
    """Convert a typed date between calendars; returns a spoken-ready arabic
    sentence, or BAD_DATE_MSG when the input is unreadable/ambiguous.

    Direction heuristic: year >= 1700 means a Gregorian date, year < 1700 a
    Hijri one (Hijri years today are ~1446; Gregorian are ~2026 - they never
    collide in practice).
    """
    parsed = _parse_dmy(text)
    if parsed is None:
        return BAD_DATE_MSG
    d, m, y = parsed
    try:
        if y >= 1700:
            date(y, m, d)  # validates
            hy, hm, hd = gregorian_to_hijri(y, m, d)
            return (
                f"{d} {GREGORIAN_MONTHS_AR[m - 1]} {y} م "
                f"يوافق {hd} {HIJRI_MONTHS_AR[hm - 1]} {hy} هـ."
            )
        gy, gm, gd = hijri_to_gregorian(y, m, d)
        date(gy, gm, gd)  # validates
        return (
            f"{d} {HIJRI_MONTHS_AR[m - 1]} {y} هـ "
            f"يوافق {gd} {GREGORIAN_MONTHS_AR[gm - 1]} {gy} م."
        )
    except ValueError:
        return BAD_DATE_MSG


def month_export_lines(calc, year: int, month: int, city: str, country: str, method: str) -> list:
    """One compact line per day for a Gregorian month, screen-reader friendly.

    calc: PrayerTimeCalculator; each line carries weekday, gregorian, hijri
    and all six times so the file reads well top to bottom in NVDA.
    """
    method_ar = METHODS.get(method, {}).get("label_ar", method)
    out = [
        f"مواقيت الصلاة لشهر {GREGORIAN_MONTHS_AR[month - 1]} {year} م - {city}، {country}",
        f"طريقة الحساب: {method_ar}",
        "",
    ]
    day = date(year, month, 1)
    while day.month == month:
        times = calc.for_date(day).times
        hy, hm, hd = gregorian_to_hijri(day.year, day.month, day.day)
        parts = " | ".join(f"{ARABIC_NAMES[p]} {times[p].strftime('%H:%M')}" for p in PRAYERS)
        out.append(
            f"{weekday_label(day)} {day.day} {GREGORIAN_MONTHS_AR[month - 1]} {day.year} م"
            f" ({hd} {HIJRI_MONTHS_AR[hm - 1]} {hy} هـ):"
        )
        out.append(parts)
        day += timedelta(days=1)
    return out
