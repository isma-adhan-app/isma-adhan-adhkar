"""Scheduler engine tests with a fixed fake clock and fixed prayer times."""
from datetime import date, datetime, time, timedelta, timezone

import pytest

from isma_adhan.config import Settings
from isma_adhan.scheduler import ADHAN, ADHKAR, IQAMA, KAHF, PRE_ADHAN, SchedulerEngine

TZ = timezone(timedelta(hours=2))  # Africa/Cairo winter offset, fixed for tests

FIXED = {
    "fajr": time(5, 0),
    "sunrise": time(6, 30),
    "dhuhr": time(12, 0),
    "asr": time(15, 0),
    "maghrib": time(17, 30),
    "isha": time(19, 0),
}


def provider(day: date):
    return {name: datetime.combine(day, t, TZ) for name, t in FIXED.items()}


def make_engine(**overrides):
    s = Settings(
        pre_adhan_minutes=5,
        iqama_minutes=10,
        adhkar_enabled=False,
        adhkar_interval_minutes=0,
        kahf_enabled=True,
        kahf_time="10:00",
    )
    for k, v in overrides.items():
        setattr(s, k, v)
    return SchedulerEngine(s, provider), s


def at(day, hh, mm):
    return datetime.combine(day, time(hh, mm), TZ)


# 2026-11-21 is a Saturday; 2026-11-20 is a Friday
SAT = date(2026, 11, 21)
FRI = date(2026, 11, 20)


def tick_kinds(engine, now):
    return [(e.kind, e.prayer) for e in engine.tick(now)]


def test_adhan_fires_exactly_once():
    engine, _ = make_engine()
    assert (ADHAN, "fajr") in tick_kinds(engine, at(SAT, 5, 0))
    assert tick_kinds(engine, at(SAT, 5, 0)) == []  # second tick same minute: no refire
    assert tick_kinds(engine, at(SAT, 5, 0) + timedelta(seconds=30)) == []


def test_pre_adhan_offset():
    engine, _ = make_engine()
    assert (PRE_ADHAN, "fajr") in tick_kinds(engine, at(SAT, 4, 55))
    engine2, _ = make_engine(pre_adhan_minutes=20)
    assert tick_kinds(engine2, at(SAT, 4, 40)) == [(PRE_ADHAN, "fajr")]


def test_pre_adhan_off():
    engine, _ = make_engine(pre_adhan_minutes=0)
    assert tick_kinds(engine, at(SAT, 4, 55)) == []


def test_iqama_offset_and_off():
    engine, _ = make_engine()
    assert (IQAMA, "fajr") in tick_kinds(engine, at(SAT, 5, 10))
    engine2, _ = make_engine(iqama_minutes=0)
    assert tick_kinds(engine2, at(SAT, 5, 10)) == []


def test_no_late_fire_after_app_start():
    # app opens at noon: this morning's events must not fire
    engine, _ = make_engine()
    assert tick_kinds(engine, at(SAT, 12, 1)) == [(ADHAN, "dhuhr")]


def test_grace_window():
    engine, _ = make_engine(grace_seconds=90)
    # 60 seconds late still fires
    assert (ADHAN, "fajr") in tick_kinds(engine, at(SAT, 5, 1))
    engine2, _ = make_engine(grace_seconds=90)
    # 5 minutes late does not
    assert tick_kinds(engine2, at(SAT, 5, 5)) == []


def test_no_adhan_for_sunrise():
    engine, _ = make_engine()
    assert tick_kinds(engine, at(SAT, 6, 30)) == []


def test_kahf_friday_only():
    engine, _ = make_engine()
    assert tick_kinds(engine, at(FRI, 10, 0)) == [(KAHF, None)]
    engine2, _ = make_engine()
    assert tick_kinds(engine2, at(SAT, 10, 0)) == []
    engine3, _ = make_engine(kahf_enabled=False)
    assert tick_kinds(engine3, at(FRI, 10, 0)) == []


def test_adhkar_cadence():
    engine, s = make_engine(adhkar_enabled=True, adhkar_interval_minutes=15, adhkar_quiet_hours=False)
    start = at(SAT, 8, 0)
    assert engine.tick(start) == []  # first tick only arms the timer
    assert tick_kinds(engine, start + timedelta(minutes=15)) == [(ADHKAR, None)]
    assert tick_kinds(engine, start + timedelta(minutes=29)) == []
    assert tick_kinds(engine, start + timedelta(minutes=30)) == [(ADHKAR, None)]


def test_adhkar_disabled():
    engine, _ = make_engine(adhkar_enabled=False, adhkar_interval_minutes=15, adhkar_quiet_hours=False)
    now = at(SAT, 8, 0)
    for i in range(60):
        assert engine.tick(now + timedelta(minutes=i)) == []


def test_adhkar_quiet_hours():
    engine, _ = make_engine(
        adhkar_enabled=True,
        adhkar_interval_minutes=10,
        adhkar_quiet_hours=True,
        quiet_start="23:00",
        quiet_end="05:00",
    )
    assert engine.tick(at(SAT, 23, 30)) == []
    assert engine.tick(at(SAT, 23, 45)) == []  # inside quiet hours: nothing
    assert engine.tick(at(SAT, 0, 30)) == []
    # after quiet hours the timer re-arms, first clip one interval later
    assert engine.tick(at(SAT, 5, 30)) == []
    assert tick_kinds(engine, at(SAT, 5, 40)) == [(ADHKAR, None)]


def test_adhkar_suppressed_near_prayer():
    engine, _ = make_engine(adhkar_enabled=True, adhkar_interval_minutes=5, adhkar_quiet_hours=False)
    # arm at 11:51 so the next clip would land at 11:56, inside the 3-minute
    # margin around the 11:55 pre-adhan alert - the clip must be skipped while
    # the pre-adhan alert itself still fires
    engine.tick(at(SAT, 11, 51))
    kinds = tick_kinds(engine, at(SAT, 11, 56))
    assert (ADHKAR, None) not in kinds
    assert (PRE_ADHAN, "dhuhr") in kinds


def test_clock_backwards_resets():
    engine, _ = make_engine()
    assert (ADHAN, "fajr") in tick_kinds(engine, at(SAT, 5, 0))
    # user fixes a wrong clock backwards, then forwards again: may refire
    engine.tick(at(SAT, 4, 0))
    assert (ADHAN, "fajr") in tick_kinds(engine, at(SAT, 5, 0))


def test_upcoming():
    engine, _ = make_engine()
    ups = engine.upcoming(at(SAT, 13, 0))
    kinds = [e.kind for e in ups]
    assert (ADHAN, "asr") in [(e.kind, e.prayer) for e in ups]
    assert all(e.at > at(SAT, 13, 0) for e in ups)
