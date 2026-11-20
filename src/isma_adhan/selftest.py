"""Headless self-test for the packaged build.

Runs every non-interactive subsystem without creating a window, so it works
in a CI session with no display and no user. Exit code 0 = all checks passed.
"""
from __future__ import annotations


def run_self_test() -> int:
    checks = []

    def check(name):
        def decorator(fn):
            try:
                fn()
                checks.append((name, True, ""))
            except Exception as exc:
                checks.append((name, False, f"{type(exc).__name__}: {exc}"))
            return fn

        return decorator

    @check("bundled-alert-tones")
    def _():
        from .sounds import default_tone, resource_path

        for kind in ("pre_adhan", "iqama", "fallback_adhan", "kahf"):
            p = default_tone(kind)
            assert p.exists(), f"missing {p}"
        assert resource_path("assets", "icon.ico").exists(), "missing icon"

    @check("timezone-database")
    def _():
        from datetime import datetime
        from zoneinfo import ZoneInfo

        tz = ZoneInfo("Africa/Cairo")
        assert datetime(2026, 7, 15, 12, tzinfo=tz).utcoffset().total_seconds() == 3 * 3600

    @check("prayer-times")
    def _():
        from datetime import date

        from .prayer_times import PRAYERS, PrayerTimeCalculator

        calc = PrayerTimeCalculator(30.0444, 31.2357)
        t = calc.for_date(date(2026, 11, 21)).times
        ordered = [t[p] for p in PRAYERS]
        assert ordered == sorted(ordered), "disordered prayer times"

    @check("scheduler")
    def _():
        from datetime import datetime

        from .config import Settings
        from .prayer_times import PrayerTimeCalculator
        from .scheduler import SchedulerEngine

        calc = PrayerTimeCalculator(30.0444, 31.2357)
        engine = SchedulerEngine(Settings(), lambda d: calc.for_date(d).times)
        engine.tick(datetime.now(calc.tz))
        assert engine.upcoming(datetime.now(calc.tz)), "no upcoming events"

    @check("config-save-load")
    def _():
        import pathlib
        import tempfile

        from .config import Settings, load_settings, save_settings

        s = Settings(city="أسوان")
        with tempfile.TemporaryDirectory() as td:
            save_settings(s, base=pathlib.Path(td))
            assert load_settings(base=pathlib.Path(td)) == s

    @check("audio-backend")
    def _():
        from .audio import create_player

        player = create_player()  # NullPlayer fallback is fine on servers
        player.set_volume(50)
        player.stop()

    @check("wx-import")
    def _():
        import wx  # noqa: F401
        import wx.adv  # noqa: F401

    @check("ui-module-import")
    def _():
        from . import app, main_window  # noqa: F401

    failed = 0
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}: {name}" + (f"  ({detail})" if detail else ""))
        if not ok:
            failed += 1
    print(f"SELF-TEST {'PASS' if failed == 0 else 'FAIL'} ({len(checks) - failed}/{len(checks)})")
    return 0 if failed == 0 else 1
