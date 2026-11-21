"""Generate the built-in alert tones (WAV) shipped with the app.

Run from the repo root:  python tools/make_tones.py
Creates assets/sounds/{soft_chime,iqama_tone,attention}.wav plus the
v1.7 alert variants (pre_chime_up, pre_chime_triple, iqama_low, iqama_triple).
These are neutral alert tones. The app speaks the prayer name alongside them
and the user is expected to add a real adhan recording himself.
"""
import math
import wave
from pathlib import Path

SAMPLE_RATE = 44100
OUT = Path(__file__).resolve().parents[1] / "assets" / "sounds"


def write_wav(name: str, samples: list) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        frames = b"".join(int(max(-1.0, min(1.0, s)) * 32767).to_bytes(2, "little", signed=True) for s in samples)
        w.writeframes(frames)
    return path


def tone(freq: float, seconds: float, volume: float = 0.5, decay: float = 3.0) -> list:
    n = int(SAMPLE_RATE * seconds)
    return [
        volume * math.sin(2 * math.pi * freq * t / SAMPLE_RATE) * math.exp(-decay * t / SAMPLE_RATE)
        for t in range(n)
    ]


def mix(*parts: list) -> list:
    length = max(len(p) for p in parts)
    out = [0.0] * length
    for p in parts:
        for i, s in enumerate(p):
            out[i] += s
    peak = max(abs(s) for s in out) or 1.0
    if peak > 1.0:
        out = [s / peak for s in out]
    return out


def silence(seconds: float) -> list:
    return [0.0] * int(SAMPLE_RATE * seconds)


def main() -> None:
    # soft chime: two gentle descending notes (pre-adhan reminder, kahf)
    soft = tone(880, 0.6, 0.4) + silence(0.15) + tone(660, 0.8, 0.4)
    write_wav("soft_chime.wav", soft)

    # iqama: single firm double beep
    iqama = tone(1046, 0.25, 0.5, decay=6.0) + silence(0.12) + tone(1046, 0.4, 0.5, decay=6.0)
    write_wav("iqama_tone.wav", iqama)

    # v1.7 pre-adhan variants
    # two gentle rising notes
    up = tone(660, 0.5, 0.4) + silence(0.15) + tone(880, 0.7, 0.4)
    write_wav("pre_chime_up.wav", up)
    # three soft descending notes
    triple = tone(988, 0.4, 0.35) + silence(0.12) + tone(784, 0.4, 0.35) + silence(0.12) + tone(659, 0.6, 0.35)
    write_wav("pre_chime_triple.wav", triple)

    # v1.7 iqama variants
    # firm lower double beep
    low = tone(784, 0.25, 0.5, decay=6.0) + silence(0.12) + tone(784, 0.4, 0.5, decay=6.0)
    write_wav("iqama_low.wav", low)
    # three short beeps
    three = tone(1046, 0.18, 0.5, decay=7.0) + silence(0.10) + tone(1046, 0.18, 0.5, decay=7.0) + silence(0.10) + tone(1046, 0.3, 0.5, decay=7.0)
    write_wav("iqama_triple.wav", three)

    # attention: three rising notes (fallback when no adhan file is chosen)
    attention = mix(tone(523, 1.5, 0.35), tone(659, 1.5, 0.25), tone(784, 1.5, 0.2))
    write_wav("attention.wav", attention)

    print(f"wrote tones to {OUT}")


if __name__ == "__main__":
    main()
