# اسمع أذان وأذكار (Isma Adhan wa Adhkar)

A Windows desktop app for prayer times, adhan audio, and periodic audio
adhkar, designed from the start for blind users with screen readers (NVDA).

- Arabic UI, right-to-left
- every control reachable and usable with the keyboard alone (Tab + shortcuts)
- prayer times computed fully offline with the Egyptian General Authority of
  Survey method (Fajr 19.5°, Isha 17.5°) - no internet needed after install
- works anywhere in the world: country + city picker covering 244 countries
  and 1700+ cities (GeoNames data), with one-click auto-detection from the
  Windows region and timezone settings
- adhan at each prayer with a user-managed sound library (add your own
  MP3/WAV/OGG); a different adhan sound can be assigned per prayer; until a
  sound is chosen the app chimes and speaks the prayer name through Windows
  speech (SAPI)
- iqama alert a configurable number of minutes after each adhan, per prayer
- pre-adhan reminder, configurable 5-60 minutes before (steps of 5), per prayer
- post-prayer adhkar reminder, configurable 5-60 minutes after (steps of 5),
  per prayer - plays a dhikr clip so the adhkar after prayer are not missed
- 14 adhkar clips bundled with the app: real recitations from the Hisn
  al-Muslim audiobook (see "Bundled audio licensing" below); the user can
  still add their own clips on top
- audio adhkar clips played in random order every 10/15/20/30 minutes,
  with quiet hours (default 23:00-05:00, toggleable)
- Friday reminder for Surat Al-Kahf
- system tray presence, optional autostart with Windows
- startup Bismillah: بسم الله الرحمن الرحيم plays on launch before any other
  sound, recited by a real reciter chosen in settings: الحصري / البنا /
  عبد الباسط عبد الصمد / المنشاوي / عشوائي - a random reciter each launch
  (licensing documented below); the announcement then speaks the day, the
  Gregorian and Hijri dates, and the next prayer
- Hijri + Gregorian date display in Arabic words (screen-reader friendly
  read-only field); Hijri uses the standard tabular (Kuwaiti) conversion and
  may differ by +/-1 day from moon-sighting announcements
- upgrading from v1.0 keeps all settings (the settings file migrates itself)

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

## Known limitations of v1.1

- The wxPython UI was developed on Linux without wxPython available, so it is
  code-reviewed and unit-tested below the UI layer but not yet click-tested on
  Windows. First Windows run may surface small UI bugs.
- No recorded adhan ships with the app (copyright); the user adds their own
  in the الأصوات tab. Until then the app chimes and speaks the prayer name.
- The bundled adhkar are chapter-length recordings (17 seconds to 8
  minutes), not one-dhikr snippets; the rotation plays one at a time.
- Maghrib is computed exactly at sunset per the Egyptian method.
- Hijri date is the civil/astronomical calendar and can differ by +/-1 day
  from moon-sighting announcements.
- pyttsx3/SAPI speech quality depends on the installed Windows voices; an
  Arabic voice gives the best result.

## Bundled audio licensing

Startup Bismillah recordings (`assets/sounds/bismillah/*.mp3`) are the
Al-Fatiha verse-1 clips from EveryAyah's verse-by-verse archives:

- husary.mp3    - محمود خليل الحصري  - https://everyayah.com/data/Husary_128kbps/001001.mp3
- banna.mp3     - محمود علي البنا    - https://everyayah.com/data/mahmoud_ali_al_banna_32kbps/001001.mp3
- abdulbasit.mp3 - عبد الباسط عبد الصمد - https://everyayah.com/data/Abdul_Basit_Murattal_64kbps/001001.mp3
- minshawi.mp3  - محمد صديق المنشاوي - https://everyayah.com/data/Minshawy_Murattal_128kbps/001001.mp3

Licensing basis (verified 2026-11-21): Islamic Network (islamic.network, the
organization that mirrors these exact files through the AlQuran Cloud CDN)
states that these classical reciter recordings sourced from everyayah.com are
public domain, may be redistributed inside applications, and that attribution
is expected - given above and here. The app is free and non-commercial. See:
https://community.islamic.network/d/231-clarification-on-licensing-and-usage-rights-for-quran-recitation-api

The 14 clips in `assets/sounds/adhkar_bundled/` are chapters of the Hisn
al-Muslim audiobook read by Sheikh سليمان الشويهي (Sulaiman Al-Shuwayhi),
reviewed by د. سعيد بن علي بن وهف القحطاني and published by IslamHouse
(item https://islamhouse.com/ar/audios/2799103, one mp3 per chapter on
d1.islamhouse.com; `tools/fetch_adhkar.py` re-downloads them with sha256
checks). Licensing basis (verified 2026-11-21): IslamHouse's site policy
(https://d1.islamhouse.com/html/faq.htm) allows using and republishing site
content by any means, unchanged, with attribution to the source. The clips
ship byte-identical to the published files, attribution is given here and
in this section, and the app is free and non-commercial.

The fallback `assets/sounds/bismillah.wav` (used only if a reciter clip is
missing) is the earlier eSpeak NG TTS clip. eSpeak NG is GPL as a *program*;
its license places no restrictions on audio output generated with it, so
this generated clip may be redistributed with the app.

Location data: GeoNames (cities15000, countryInfo - CC-BY 4.0,
geonames.org) and the CLDR Windows-zones mapping (unicode.org license).
Regenerate with `tools/build_world.py`.
