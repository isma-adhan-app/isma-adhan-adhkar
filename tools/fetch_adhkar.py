"""Download the bundled adhkar audio clips (real recitations, not TTS).

Source: the Hisn al-Muslim audiobook read by Sheikh سليمان الشويهي
(Sulaiman Al-Shuwayhi), reviewed by د. سعيد بن علي بن وهف القحطاني,
published by IslamHouse as one mp3 per book chapter:
    item page:  https://islamhouse.com/ar/audios/2799103
    files:      https://d1.islamhouse.com/data/ar/ih_sounds/chain_01/
                Hisn_Almuslim/Hisn_Almuslim_AlShwehi/ar_NNN_Hisn_Almuslim_Alshwehi.mp3

Licensing basis (verified 2026-11-21): IslamHouse's site policy
(https://d1.islamhouse.com/html/faq.htm) allows using and republishing site
content by any means, unchanged, with attribution to the source. The clips
are shipped byte-identical (sha256-checked below) and attribution is given
in the README ("Bundled audio licensing") and in the app.

The old eSpeak TTS generator was removed when these recordings replaced the
synthetic clips. `assets/sounds/bismillah.wav` is still that earlier TTS
clip, kept only as a fallback when a reciter Bismillah file is missing.

Usage:
    python tools/fetch_adhkar.py     # re-download, verify, rebuild the index

Outputs:
    assets/sounds/adhkar_bundled/NN.mp3    one clip per chapter
    assets/sounds/adhkar_bundled.json      {"NN.mp3": chapter_title}
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "sounds" / "adhkar_bundled"
INDEX_FILE = ROOT / "assets" / "sounds" / "adhkar_bundled.json"

BASE = (
    "https://d1.islamhouse.com/data/ar/ih_sounds/chain_01/"
    "Hisn_Almuslim/Hisn_Almuslim_AlShwehi/ar_{track}_Hisn_Almuslim_Alshwehi.mp3"
)

# bundled file -> (islamhouse chapter track, arabic chapter title, size, sha256)
CLIPS = [
    ("01.mp3", "027", "الأذكار بعد السلام من الصلاة", 3686182, "bf76ce00381a76cd"),
    ("02.mp3", "026", "الدعاء بعد التشهد الأخير وقبل السلام", 4094546, "98e222fa1d700e06"),
    ("03.mp3", "025", "الصلاة على النبي صلى الله عليه وسلم بعد التشهد", 1058923, "e5bd6d8b3e1563b4"),
    ("04.mp3", "108", "فضل الصلاة على النبي صلى الله عليه وسلم", 1066876, "92d92ba1656d8981"),
    ("05.mp3", "022", "دعاء الجلسة بين السجدتين", 319517, "a7892f847ada0831"),
    ("06.mp3", "130", "الاستغفار والتوبة", 1424187, "cf7742938a72544d"),
    ("07.mp3", "131", "فضل التسبيح والتحميد والتهليل والتكبير", 3588012, "71dc99ee545b99f5"),
    ("08.mp3", "029", "أذكار الصباح والمساء", 8049242, "ee3a0e1b6d372c2d"),
    ("09.mp3", "030", "أذكار النوم", 5634292, "333bf07da5a9b3c1"),
    ("10.mp3", "003", "أذكار الاستيقاظ من النوم", 2922563, "a2e8558d7143e943"),
    ("11.mp3", "017", "أذكار الأذان", 1298789, "6afacd0d7d1412aa"),
    ("12.mp3", "028", "دعاء صلاة الاستخارة", 1612689, "1be9a28155054bdc"),
    ("13.mp3", "035", "دعاء الهم والحزن", 961500, "215fe6ec29b1580f"),
    ("14.mp3", "036", "دعاء الكرب", 834847, "61c5b57db346d225"),
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.mp3"):
        old.unlink()

    index = {}
    for name, track, title, want_size, want_sha in CLIPS:
        url = BASE.format(track=track)
        out = OUT_DIR / name
        with urllib.request.urlopen(url, timeout=120) as r:
            data = r.read()
        out.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        assert len(data) == want_size, f"{name}: size {len(data)} != {want_size}"
        assert sha.startswith(want_sha), f"{name}: sha256 {sha[:16]} != {want_sha}"
        index[name] = title
        print(f"{name}: {len(data)} bytes  <- islamhouse track {track}  {title}")

    INDEX_FILE.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n{len(index)} clips -> {OUT_DIR}")
    print(f"index -> {INDEX_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
