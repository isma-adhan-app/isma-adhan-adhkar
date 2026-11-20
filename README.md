# اسمع أذان وأذكار (Isma Adhan wa Adhkar)

A Windows desktop app for prayer times, adhan audio, and periodic audio
adhkar, designed from the start for blind users with screen readers (NVDA).

- Arabic UI, right-to-left
- every control reachable and usable with the keyboard alone (Tab + shortcuts)
- prayer times computed fully offline with the Egyptian General Authority of
  Survey method (Fajr 19.5°, Isha 17.5°) - no internet needed after install
- Egyptian city picker (28 cities), Cairo by default
- adhan at each prayer with a user-managed sound library (add your own
  MP3/WAV/OGG); until a sound is chosen the app chimes and speaks the prayer
  name through Windows speech (SAPI)
- iqama alert a configurable number of minutes after each adhan
- pre-adhan reminder, configurable 5-60 minutes before (steps of 5)
- audio adhkar clips played in random order every 10/15/20/30 minutes,
  with quiet hours (default 23:00-05:00, toggleable)
- Friday reminder for Surat Al-Kahf
- system tray presence, optional autostart with Windows
- Hijri date display (astronomical approximation, may differ by a day)

## Repository layout

```
src/isma_adhan/
  prayer_times.py   offline calculation (PrayTimes.org algorithm port)
  scheduler.py      what fires when (pure logic, fully unit-tested)
  config.py         settings, paths under %APPDATA%\IsmaAdhan
  cities.py         Egyptian city coordinates
  sounds.py         sound library + random adhkar rotation
  audio.py          pygame playback backend
  speech.py         SAPI announcements via pyttsx3
  autostart.py      Windows Run-key autostart
  hijri.py          Hijri date (Kuwaiti algorithm)
  strings.py        all Arabic UI text
  main_window.py    wxPython UI (Arabic, RTL, NVDA-friendly)
  app.py            wx.App + system tray
assets/             built-in alert tones + tray icon
tests/              pytest suite (56 tests)
tools/              tone/icon generators + JS cross-check script
IsmaAdhan.spec      PyInstaller build
```

## Run from source (Windows)

```
py -3.12 -m pip install -r requirements.txt
py -3.12 -m isma_adhan            # with src on PYTHONPATH, or:
python -m isma_adhan              # after: pip install -e . style path setup
```

Simplest from the repo root: `set PYTHONPATH=src` then `python -m isma_adhan`.

## Tests

```
python -m pytest tests/ -q
PYTHONPATH=src python3 tools/compare_with_adhan_js.py   # needs: cd tools/js-compare && npm i
```

The calculation module is verified against the independent `adhan` library:
worst difference over 7 dates x 6 prayers for Cairo is 1.3 minutes
(rounding conventions; both use Fajr 19.5° / Isha 17.5°).

## Packaging for Amrw

See docs/PACKAGING.md. Short version: `pyinstaller IsmaAdhan.spec` on
Windows produces one `IsmaAdhan.exe` he can run directly - no Python needed.

## Known limitations of v1

- The wxPython UI was developed on Linux without wxPython available, so it is
  code-reviewed and unit-tested below the UI layer but not yet click-tested on
  Windows. First Windows run may surface small UI bugs.
- No adhan recording ships with the app (copyright); Amrw adds his own in the
  الأصوات tab. Until then the app chimes and speaks the prayer name.
- Maghrib is computed exactly at sunset per the Egyptian method.
- Hijri date is the civil/astronomical calendar and can differ by +/-1 day
  from moon-sighting announcements.
- pyttsx3/SAPI speech quality depends on the installed Windows voices; an
  Arabic voice gives the best result.
