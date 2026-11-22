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
        bismillah = resource_path("assets", "sounds", "bismillah.wav")
        assert bismillah.exists() and bismillah.stat().st_size > 2000, "missing bismillah clip"
        from .sounds import BISMILLAH_VOICES, bismillah_path

        for key, *_ in BISMILLAH_VOICES:
            assert bismillah_path(key) is not None, f"missing bismillah clip: {key}"

        from .sounds import ALERT_BUNDLED, alert_clip_path

        for kind, entries in ALERT_BUNDLED.items():
            for key, _name, _f in entries:
                assert alert_clip_path(kind, key) is not None, f"missing alert clip: {kind}/{key}"

    @check("bundled-adhkar")
    def _():
        from .sounds import bundled_adhkar

        clips = bundled_adhkar()
        assert len(clips) >= 10, f"only {len(clips)} bundled adhkar clips"
        for path, text in clips:
            assert path.exists() and path.stat().st_size > 2000, f"bad clip {path}"
            assert text.strip(), f"clip without text: {path}"

    @check("translations-complete")
    def _():
        from . import strings

        ar = strings._AR
        for code, table in strings._TABLES.items():
            missing = sorted(set(ar) - set(table))
            extra = sorted(set(table) - set(ar))
            assert not missing, f"{code} missing keys: {missing}"
            assert not extra, f"{code} unknown keys: {extra}"
        for code in strings.LANGUAGES:
            strings.set_language(code)
            assert strings.tr("APP_NAME").strip(), f"empty APP_NAME in {code}"
            assert "{prayer}" not in strings.msg_adhan_now("X"), f"format broken in {code}"
        strings.set_language("ar")
        assert strings.prayer_name("fajr") == "الفجر"
        strings.set_language("en")
        assert strings.prayer_name("fajr") == "Fajr"
        strings.set_language("ar")

    @check("updater-module")
    def _():
        from . import updater

        assert updater.is_newer("9.9.9") is True
        assert updater.is_newer("0.0.1") is False
        assert updater.current_arch() in ("x64", "x86")
        assert updater.LATEST_JSON_URL.startswith("https://")

    @check("nvda-dll-matches-arch")
    def _():
        import sys
        from .sounds import resource_path

        x86 = resource_path("assets", "nvda", "x86", "nvdaControllerClient.dll")
        x64 = resource_path("assets", "nvda", "nvdaControllerClient.dll")
        assert x86.exists() and x64.exists(), "an NVDA client DLL is missing"
        want = x86 if sys.maxsize <= 2**32 else x64
        assert want.exists(), f"missing DLL for this arch: {want}"
        import struct
        for dll_path, machine in ((x86, 0x14c), (x64, 0x8664)):
            data = dll_path.read_bytes()
            offset = struct.unpack_from("<I", data, 0x3c)[0]
            assert data[offset:offset+4] == b"PE\0\0"
            assert struct.unpack_from("<H", data, offset+4)[0] == machine
        if sys.platform == "win32":
            from .speech import NvdaSpeech
            speech = NvdaSpeech()
            speech._load()
            assert speech._dll is not None, "matching NVDA client DLL failed to load"
            # Loading the client is NOT a running-NVDA speech/acapela test.
            speech._dll.nvdaController_testIfRunning()

    @check("world-data")
    def _():
        from . import world

        assert len(world.countries()) >= 200
        cairo = [c for c in world.cities_of("EG") if "القاهرة" in world.city_display(c)]
        assert cairo, "Cairo missing from world data"
        assert cairo[0]["tz"] == "Africa/Cairo"

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
    # Windowed (console=False) exes cannot print or reliably signal via exit
    # code, so also record the outcome in app.log for CI and diagnostics.
    try:
        from .bootstrap import milestone

        milestone(f"self-test result: {'PASS' if failed == 0 else 'FAIL'} ({len(checks) - failed}/{len(checks)})")
    except Exception:
        pass
    return 0 if failed == 0 else 1
