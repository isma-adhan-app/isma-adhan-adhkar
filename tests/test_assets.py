"""Bundled media assets must ship complete (CI guards the release contents)."""
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def test_bismillah_clip():
    p = ASSETS / "sounds" / "bismillah.wav"
    assert p.exists() and p.stat().st_size > 20000


def test_bundled_adhkar_complete():
    import json

    index = ASSETS / "sounds" / "adhkar_bundled.json"
    data = json.loads(index.read_text(encoding="utf-8"))
    assert len(data) >= 10
    for name, text in data.items():
        clip = ASSETS / "sounds" / "adhkar_bundled" / name
        assert clip.exists() and clip.stat().st_size > 20000, name
        assert text.strip()


def test_world_data_files():
    assert (ASSETS / "world.json").exists()
    assert (ASSETS / "windows_zones.json").exists()
