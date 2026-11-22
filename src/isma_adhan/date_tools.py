"""Date converter + monthly prayer-times export (v1.5).

Pure functions so the logic is unit-tested without wx; main_window only
collects input, calls these, and speaks/shows the results.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from . import strings
from .hijri import (
    gregorian_month_name,
    gregorian_to_hijri,
    hijri_month_name,
    hijri_to_gregorian,
    weekday_label,
)
from .prayer_times import PRAYERS

def bad_date_msg() -> str:
    return strings.tr("MSG_CONVERT_BAD")


def __getattr__(name: str):
    # `from .date_tools import BAD_DATE_MSG` resolves in the language active
    # at import time (Arabic by default, which is what the tests compare).
    if name == "BAD_DATE_MSG":
        return bad_date_msg()
    raise AttributeError(name)


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
    """Convert a typed date between calendars; returns a spoken-ready
    sentence in the current UI language, or the bad-date message when the
    input is unreadable/ambiguous.

    Direction heuristic: year >= 1700 means a Gregorian date, year < 1700 a
    Hijri one (Hijri years today are ~1446; Gregorian are ~2026 - they never
    collide in practice).
    """
    parsed = _parse_dmy(text)
    if parsed is None:
        return bad_date_msg()
    d, m, y = parsed
    try:
        if y >= 1700:
            date(y, m, d)  # validates
            hy, hm, hd = gregorian_to_hijri(y, m, d)
            return strings.tr("MSG_CONVERT_G2H").format(
                d=d, gmonth=gregorian_month_name(m), y=y,
                hd=hd, hmonth=hijri_month_name(hm), hy=hy)
        gy, gm, gd = hijri_to_gregorian(y, m, d)
        date(gy, gm, gd)  # validates
        return strings.tr("MSG_CONVERT_H2G").format(
            d=d, hmonth=hijri_month_name(m), y=y,
            gd=gd, gmonth=gregorian_month_name(gm), gy=gy)
    except ValueError:
        return bad_date_msg()


def month_export_lines(calc, year: int, month: int, city: str, country: str, method: str) -> list:
    """One compact line per day for a Gregorian month, screen-reader friendly.

    calc: PrayerTimeCalculator; each line carries weekday, gregorian, hijri
    and all six times so the file reads well top to bottom in NVDA.
    """
    method_name = strings.method_label(method)
    out = [
        strings.tr("MSG_EXPORT_HEADER").format(
            month=gregorian_month_name(month), year=year, city=city, country=country),
        strings.tr("MSG_EXPORT_METHOD").format(method=method_name),
        "",
    ]
    day = date(year, month, 1)
    while day.month == month:
        times = calc.for_date(day).times
        hy, hm, hd = gregorian_to_hijri(day.year, day.month, day.day)
        parts = " | ".join(
            f"{strings.prayer_name(p)} {times[p].strftime('%H:%M')}" for p in PRAYERS)
        out.append(
            f"{weekday_label(day)} {day.day} {gregorian_month_name(month)} {day.year}"
            f" ({hd} {hijri_month_name(hm)} {hy}):"
        )
        out.append(parts)
        day += timedelta(days=1)
    return out
