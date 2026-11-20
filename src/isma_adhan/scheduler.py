"""Scheduling engine: decides what fires when. Pure logic, no UI, no audio.

Given a prayer-times provider and the current Settings, ``tick(now)`` returns
the events that should fire right now (each fires exactly once).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Callable, Dict, List, Optional

from .prayer_times import ADHAN_PRAYERS

# event kinds
PRE_ADHAN = "pre_adhan"
ADHAN = "adhan"
IQAMA = "iqama"
ADHKAR = "adhkar"
KAHF = "kahf"

FRIDAY = 4  # datetime.weekday()


@dataclass(frozen=True)
class Event:
    kind: str
    at: datetime
    prayer: Optional[str] = None

    def key(self) -> str:
        return f"{self.kind}|{self.prayer or ''}|{self.at.isoformat()}"


def _parse_hhmm(value: str) -> time:
    hh, mm = value.split(":")
    return time(int(hh), int(mm))


def _in_quiet_hours(now: datetime, start: time, end: time) -> bool:
    t = now.time()
    if start <= end:
        return start <= t < end
    # overnight window, e.g. 23:00 -> 05:00
    return t >= start or t < end


class SchedulerEngine:
    """Stateless-per-day event source.

    - prayer-based events fire when ``now`` reaches their time, with a grace
      window so events missed while the app was closed do not fire late.
    - adhkar events fire every N minutes while enabled, suppressed during
      quiet hours and around prayer alerts.
    """

    def __init__(
        self,
        settings,
        times_provider: Callable[[date], Dict[str, datetime]],
        grace_seconds: int = 90,
    ):
        self.settings = settings
        self.times_provider = times_provider
        self.grace = timedelta(seconds=grace_seconds)
        self._fired: set = set()
        self._next_adhkar: Optional[datetime] = None
        self._last_now: Optional[datetime] = None

    # ------------------------------------------------------------------
    def day_events(self, day: date, tz) -> List[Event]:
        s = self.settings
        events: List[Event] = []
        times = self.times_provider(day)
        for prayer in ADHAN_PRAYERS:
            t = times[prayer]
            if s.pre_adhan_minutes > 0:
                events.append(Event(PRE_ADHAN, t - timedelta(minutes=s.pre_adhan_minutes), prayer))
            events.append(Event(ADHAN, t, prayer))
            if s.iqama_minutes > 0:
                events.append(Event(IQAMA, t + timedelta(minutes=s.iqama_minutes), prayer))
        if s.kahf_enabled and day.weekday() == FRIDAY:
            at = datetime.combine(day, _parse_hhmm(s.kahf_time)).replace(tzinfo=tz)
            events.append(Event(KAHF, at))
        return sorted(events, key=lambda e: e.at)

    # ------------------------------------------------------------------
    def tick(self, now: datetime) -> List[Event]:
        if self._last_now is not None and now < self._last_now:
            # system clock moved backwards: forget what fired
            self._fired.clear()
        self._last_now = now

        due: List[Event] = []
        tz = now.tzinfo
        # look at yesterday too so an event right after midnight still fires
        for day in (now.date() - timedelta(days=1), now.date()):
            for ev in self.day_events(day, tz):
                if ev.at > now:
                    continue
                if now - ev.at > self.grace:
                    continue  # missed while app was off: do not fire late
                if ev.key() in self._fired:
                    continue
                self._fired.add(ev.key())
                due.append(ev)

        due.extend(self._adhkar_due(now))
        return sorted(due, key=lambda e: e.at)

    # ------------------------------------------------------------------
    def _adhkar_due(self, now: datetime) -> List[Event]:
        s = self.settings
        interval = s.adhkar_interval_minutes if s.adhkar_enabled else 0
        if interval <= 0:
            self._next_adhkar = None
            return []
        if s.adhkar_quiet_hours and _in_quiet_hours(now, _parse_hhmm(s.quiet_start), _parse_hhmm(s.quiet_end)):
            # disarm during quiet hours; the next tick afterwards re-arms
            self._next_adhkar = None
            return []
        step = timedelta(minutes=interval)
        if self._next_adhkar is None:
            self._next_adhkar = now + step
            return []
        out = []
        if now >= self._next_adhkar:
            at = self._next_adhkar
            # advance past now so a long sleep fires one clip, not a backlog
            while self._next_adhkar <= now:
                self._next_adhkar += step
            if not self._near_prayer(at):
                out.append(Event(ADHKAR, at))
        return out

    def _near_prayer(self, at: datetime, margin_minutes: int = 3) -> bool:
        """True if a prayer alert is within ``margin_minutes`` of ``at``."""
        margin = timedelta(minutes=margin_minutes)
        for ev in self.day_events(at.date(), at.tzinfo):
            if ev.kind in (ADHAN, PRE_ADHAN, IQAMA) and abs(ev.at - at) <= margin:
                return True
        return False

    # ------------------------------------------------------------------
    def upcoming(self, now: datetime) -> List[Event]:
        """All remaining prayer events today + tomorrow's (for the UI)."""
        tz = now.tzinfo
        events = self.day_events(now.date(), tz)
        events += self.day_events(now.date() + timedelta(days=1), tz)
        return [e for e in events if e.at > now]
