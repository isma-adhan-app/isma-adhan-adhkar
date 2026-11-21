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
- bundled adhan recordings by famous Egyptian muezzins - الحصري /
  المنشاوي / مصطفى إسماعيل / محمد رفعت - selectable in the الأصوات tab,
  plus an عشوائي option (a different muezzin every prayer, picked from the
  bundled clips AND the user's own adhan folder); the user can still add
  their own adhan files on top
- audio adhkar clips played in random order every 10/15/20/30 minutes,
  with quiet hours (default 23:00-05:00, toggleable)
- monthly prayer-times export: one button writes a plain-text file
  (arabic, screen-reader friendly, one compact line per day) to the
  Documents folder, with spoken confirmation
- spoken Hijri/Gregorian date converter on the main tab: type a date like
  21/11/2026 (or 1/9/1447) and hear it in the other calendar
- notable Islamic dates (Ramadan start, both Eids, Ashura, the Prophet's
  birthday, ...) announced in the launch speech ("غداً أول شهر رمضان")
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

## Screen-reader speech (v1.6)

All spoken announcements go through the running NVDA first, using the
official NVDA Controller Client (`assets/nvda/nvdaControllerClient.dll`), so
they use the user's own screen-reader voice and speed; when NVDA is not
running the app falls back to SAPI. The DLL is the unmodified prebuilt x64
binary from NV Access's official `nvda_2026.3.1_controllerClient.zip`
(https://download.nvaccess.org/releases/stable/), licensed LGPL-2.1 and
explicitly redistributable (its license ships alongside it in
assets/nvda/license.txt). sha256 of the DLL:
8c8d9e1952c8b52820988081ea58c26175e69c0fbb5a09e8f2034aae70d55f0a

## Upgrading over a running instance (v1.6)

The app holds a named mutex (`IsmaAdhanAppMutex`) and answers a broadcast
quit message (`ISMA_ADHAN_REQUEST_QUIT`) with its normal quit path. Before
copying files the installer broadcasts that message, waits for the mutex to
clear, then force-closes any leftover `IsmaAdhan.exe` (covers pre-1.5.1
builds that have neither hook). The app also quits for real on Windows
session-end instead of hiding to the tray. The workflow's E2E steps prove
all three paths on a clean runner: fresh silent install, install over a
running same-version instance, install over a running pre-fix instance.

## Known limitations of v1.1

- The wxPython UI was developed on Linux without wxPython available, so it is
  code-reviewed and unit-tested below the UI layer but not yet click-tested on
  Windows. First Windows run may surface small UI bugs.
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

The 4 adhan recordings in `assets/sounds/adhan/` are classical Egyptian
radio adhans (أذان القاهرة), fetched from IslamWeb's free-download audio
library (audio.islamweb.net, Qatari Ministry of Endowments and Islamic
Affairs; `tools/fetch_adhan.py` re-downloads them with sha256 checks):

- husary.mp3   - محمود خليل الحصري - https://audio.islamweb.net/audio/info/122667
- minshawi.mp3 - محمد صديق المنشاوي - https://audio.islamweb.net/audio/info/88639
- mustafa.mp3  - مصطفى إسماعيل    - https://audio.islamweb.net/audio/info/176760
- refaat.mp3   - محمد رفعت        - https://audio.islamweb.net/audio/info/122665

Licensing basis (verified 2026-11-21): محمد رفعت (d. 1950) and محمد صديق
المنشاوي (d. 1969) are public domain in Egypt (life + 50 years). The adhans
of مصطفى إسماعيل (d. 1978) and محمود خليل الحصري (d. 1980) are heritage
recordings broadcast continuously by Egyptian state radio (the National
Media Authority added مصطفى إسماعيل's adhan to the Quran Radio adhan lineup
in 2025) and published as free downloads by IslamWeb, but carry no explicit
redistribution license; they ship with attribution, and this is the
residual risk we accept knowingly. The app is free and non-commercial.

The fallback `assets/sounds/bismillah.wav` (used only if a reciter clip is
missing) is the earlier eSpeak NG TTS clip. eSpeak NG is GPL as a *program*;
its license places no restrictions on audio output generated with it, so
this generated clip may be redistributed with the app.

Location data: GeoNames (cities15000, countryInfo - CC-BY 4.0,
geonames.org) and the CLDR Windows-zones mapping (unicode.org license).
Regenerate with `tools/build_world.py`.
