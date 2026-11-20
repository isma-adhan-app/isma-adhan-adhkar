"""Prayer-time calculation tests.

Verified two ways:
1. structural rules (ordering, sane ranges for Cairo across seasons, DST)
2. cross-check against the independent `adhan` library (tools/compare_with_adhan_js.py)
"""
from datetime import date

import pytest

from isma_adhan.prayer_times import PRAYERS, PrayerTimeCalculator

CAIRO = (30.0444, 31.2357)
LUXOR = (25.6872, 32.6396)


@pytest.fixture
def cairo():
    return PrayerTimeCalculator(*CAIRO)


def times(calc, y, m, d):
    return calc.for_date(date(y, m, d)).times


def test_ordering_all_year(cairo):
    for month in range(1, 13):
        t = times(cairo, 2026, month, 15)
        ordered = [t[p] for p in PRAYERS]
        assert ordered == sorted(ordered), f"disordered in month {month}"


def test_all_prayers_same_day_winter(cairo):
    t = times(cairo, 2026, 1, 15)
    for p in PRAYERS:
        assert t[p].date() == date(2026, 1, 15), p


@pytest.mark.parametrize(
    "day,prayer,lo,hi",
    [
        # mid-January in Cairo, broad sanity windows (24h clock)
        (date(2026, 1, 15), "fajr", (4, 55), (5, 25)),
        (date(2026, 1, 15), "sunrise", (6, 20), (7, 0)),
        (date(2026, 1, 15), "dhuhr", (11, 50), (12, 20)),
        (date(2026, 1, 15), "asr", (14, 40), (15, 30)),
        (date(2026, 1, 15), "maghrib", (17, 10), (17, 45)),
        (date(2026, 1, 15), "isha", (18, 20), (19, 0)),
        # mid-July in Cairo (summer, DST UTC+3 since Egypt restored DST in 2023)
        (date(2026, 7, 15), "fajr", (4, 0), (4, 40)),
        (date(2026, 7, 15), "sunrise", (5, 45), (6, 20)),
        (date(2026, 7, 15), "dhuhr", (12, 50), (13, 20)),
        (date(2026, 7, 15), "asr", (16, 10), (16, 50)),
        (date(2026, 7, 15), "maghrib", (19, 40), (20, 10)),
        (date(2026, 7, 15), "isha", (21, 0), (21, 40)),
        # late November (today-ish)
        (date(2026, 11, 20), "fajr", (4, 45), (5, 25)),
        (date(2026, 11, 20), "dhuhr", (11, 30), (12, 5)),
        (date(2026, 11, 20), "maghrib", (16, 50), (17, 20)),
    ],
)
def test_cairo_sane_ranges(cairo, day, prayer, lo, hi):
    t = times(cairo, day.year, day.month, day.day)[prayer]
    assert (t.hour, t.minute) >= lo, (day, prayer, t)
    assert (t.hour, t.minute) <= hi, (day, prayer, t)


def test_dst_offsets(cairo):
    # Egypt DST in 2026: UTC+2 in winter, UTC+3 from late April to late October
    winter = times(cairo, 2026, 1, 15)["dhuhr"]
    summer = times(cairo, 2026, 7, 15)["dhuhr"]
    assert winter.utcoffset().total_seconds() == 2 * 3600
    assert summer.utcoffset().total_seconds() == 3 * 3600


def test_luxor_fajr_earlier_than_cairo(cairo):
    # Luxor is further east, so its prayers start earlier the same day
    luxor = PrayerTimeCalculator(*LUXOR)
    for day in (date(2026, 3, 15), date(2026, 9, 15)):
        d_c = times(cairo, day.year, day.month, day.day)["dhuhr"]
        d_l = times(luxor, day.year, day.month, day.day)["dhuhr"]
        diff = (d_c - d_l).total_seconds() / 60
        assert 5 < diff < 20, diff  # ~9 degrees longitude apart, but DST-free zone math


def test_next_prayer_rollover(cairo):
    t = times(cairo, 2026, 11, 20)
    after_isha = t["isha"].replace(hour=23, minute=30)
    name, at = cairo.next_prayer(after_isha)
    assert name == "fajr"
    assert at.date() == date(2026, 11, 21)


def test_reproducible(cairo):
    a = times(cairo, 2026, 6, 1)
    b = times(cairo, 2026, 6, 1)
    assert a == b
