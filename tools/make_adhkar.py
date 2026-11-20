"""Generate the bundled adhkar audio clips with eSpeak NG Arabic TTS.

Why TTS instead of recorded recitations: every usable recording we found has
an unverifiable or restrictive license, and this app is redistributed to the
public. eSpeak NG is GPL as a *program*; its license places no restrictions
on audio you generate with it, so shipping these generated clips is safe.
See README (Arabic) for the licensing note.

Usage:
    python tools/make_adhkar.py            # regenerate everything
    ESPEAK_NG=/path/to/espeak-ng python tools/make_adhkar.py

Outputs:
    assets/sounds/adhkar_bundled/NN.wav    one clip per text
    assets/sounds/adhkar_bundled.json      {"NN.wav": arabic_text}
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXTS_FILE = ROOT / "tools" / "adhkar_texts.json"
OUT_DIR = ROOT / "assets" / "sounds" / "adhkar_bundled"
INDEX_FILE = ROOT / "assets" / "sounds" / "adhkar_bundled.json"

VOICE = "ar"
RATE = "130"  # words per minute: slow enough to follow along


def find_espeak() -> str:
    for cand in (os.environ.get("ESPEAK_NG"), "espeak-ng", "espeak"):
        if cand and shutil.which(cand):
            return cand
    sys.exit("espeak-ng not found on PATH (set ESPEAK_NG=/path/to/espeak-ng)")


def wav_seconds(path: Path) -> float:
    import wave

    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / w.getframerate()
    except Exception:
        return 0.0


def main() -> int:
    espeak = find_espeak()
    texts = json.loads(TEXTS_FILE.read_text(encoding="utf-8"))
    assert len(texts) >= 10, "expected at least 10 adhkar texts"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.wav"):
        old.unlink()

    index = {}
    total = 0.0
    for i, text in enumerate(texts, 1):
        name = f"{i:02d}.wav"
        out = OUT_DIR / name
        # -w writes a seekable file so the RIFF header gets patched with the
        # real data size (--stdout streams and leaves a bogus header)
        subprocess.run(
            [espeak, "-v", VOICE, "-s", RATE, "-w", str(out), text],
            check=True,
        )
        secs = wav_seconds(out)
        assert secs > 0.3, f"{name} looks empty ({secs}s)"
        index[name] = text
        total += secs
        print(f"{name}: {secs:.1f}s  {text}")

    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(index)} clips, {total:.0f}s total -> {OUT_DIR}")
    print(f"index -> {INDEX_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
