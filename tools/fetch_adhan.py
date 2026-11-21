"""Download the bundled adhan recordings (classical Egyptian muezzins).

Source: IslamWeb audio library (audio.islamweb.net, run by the Qatari
Ministry of Endowments and Islamic Affairs), which publishes these as free
downloads:
    husary.mp3    أذان القاهرة - محمود خليل الحصري   item 122667  Adan/1030.mp3
    minshawi.mp3  أذان محمد صديق المنشاوي            item 88639   Adan/4032.mp3
    mustafa.mp3   أذان - مصطفى إسماعيل              item 176760  Adan/4035.mp3
    refaat.mp3    أذان القاهرة - محمد رفعت          item 122665  Adan/1027.mp3

Licensing basis (verified 2026-11-21, see README "Bundled audio licensing"
for the full note): محمد رفعت (d. 1950) and محمد صديق المنشاوي (d. 1969) are
public domain in Egypt (life + 50). مصطفى إسماعيل (d. 1978) and محمود خليل
الحصري (d. 1980) remain in copyright term in Egypt until 2029/2031; their
adhan recordings are heritage material broadcast continuously by Egyptian
state radio and published as free downloads by IslamWeb, but carry no
explicit license - shipped with attribution, residual risk documented.

Usage:
    python tools/fetch_adhan.py     # re-download and verify (sha256-checked)
"""
from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "sounds" / "adhan"

CLIPS = [
    ("husary.mp3", "1030", 256128, "3866a11de8d78f42"),
    ("minshawi.mp3", "4032", 503264, "95b48f013fa9f611"),
    ("mustafa.mp3", "4035", 737408, "06e6376fb4243d85"),
    ("refaat.mp3", "1027", 407680, "39964e1b6df88cfc"),
]

BASE = "https://dl2.islamweb.net/Audio3/Adan/{n}.mp3"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, n, want_size, want_sha in CLIPS:
        url = BASE.format(n=n)
        out = OUT_DIR / name
        with urllib.request.urlopen(url, timeout=120) as r:
            data = r.read()
        out.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        assert len(data) == want_size, f"{name}: size {len(data)} != {want_size}"
        assert sha.startswith(want_sha), f"{name}: sha256 {sha[:16]} != {want_sha}"
        print(f"{name}: {len(data)} bytes <- {url}")
    print(f"\n{len(CLIPS)} clips -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
