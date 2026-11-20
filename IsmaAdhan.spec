# -*- mode: python ; coding: utf-8 -*-
# PyInstaller build spec for اسمع أذان وأذكار (IsmaAdhan).
# ONEDIR build (not onefile): the onefile self-extracting bootloader is what
# antivirus engines most often false-flag; onedir ships a plain exe + DLLs.
# Build on Windows with:  pyinstaller IsmaAdhan.spec
# Output: dist/IsmaAdhan/IsmaAdhan.exe (+ support files, packaged into the
# Inno Setup installer by build/installer.iss)

from PyInstaller.utils.hooks import collect_all

datas = [("assets", "assets")]
binaries = []
hiddenimports = []

# IANA timezone database for zoneinfo on Windows
tmp = collect_all("tzdata")
datas += tmp[0]
binaries += tmp[1]
hiddenimports += tmp[2]

a = Analysis(
    ["launcher.py"],
    pathex=["src", "."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="IsmaAdhan",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="assets/icon.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="IsmaAdhan",
)
