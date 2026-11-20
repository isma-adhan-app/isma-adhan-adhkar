# Packaging IsmaAdhan for a non-technical Windows user

Goal: Amrw double-clicks one file and the app runs. No Python, no console
windows, nothing to configure before first use.

## Recommended: single-file PyInstaller build

On a Windows machine (any Windows 10/11 PC, does not have to be Amrw's):

```
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt pyinstaller
pyinstaller IsmaAdhan.spec
```

Result: `dist\IsmaAdhan.exe` (single file, ~40-60 MB, includes the alert
tones, icon, and the IANA timezone database).

Delivery:
1. Send him `IsmaAdhan.exe` (WhatsApp desktop, email, or a Drive link -
   WhatsApp may rename it to `.exe` after download; sending it inside a ZIP
   avoids SmartScreen friction less reliably but keeps the name intact).
2. Tell him where Windows saves it (`Downloads`) and that the first run may
   show a SmartScreen prompt ("Windows protected your PC") -> "More info" ->
   "Run anyway". This is normal for an unsigned app.
3. He can pin it or make a desktop shortcut and rename the shortcut to
   «اسمع أذان وأذكار». Autostart is one checkbox inside the app's settings.

## Nicer option later: Inno Setup installer

Once the exe build is confirmed working on his machine, wrap it with Inno
Setup (free) for a classic Next-Next-Finish installer that also creates the
Arabic-named shortcut and offers a "launch with Windows" checkbox. Not
needed for v1.

## Notes for the build machine

- Build on Windows. PyInstaller cannot cross-compile from Linux.
- `IsmaAdhan.spec` already bundles `assets/` and `tzdata`; if you add data
  files, add them there.
- Test the exe once with NVDA running: Tab through all three tabs, fire
  Ctrl+N, and check the tray menu with Insert+F11 / applications key.
- First run of the exe is slow (a few seconds) while it unpacks; subsequent
  starts are fast.

## Updating him later

New exe, same filename. Settings and sounds live in
`%APPDATA%\IsmaAdhan` and survive exe replacement.
