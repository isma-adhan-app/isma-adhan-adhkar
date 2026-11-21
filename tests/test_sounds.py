import random
from pathlib import Path

import pytest

from isma_adhan.sounds import ShuffledRotation, add_sound, display_name, list_sounds


def _mkfile(path: Path):
    path.write_bytes(b"RIFFfake")
    return path


def test_add_sound_copies(tmp_path):
    src = _mkfile(tmp_path / "adhan_makkah.mp3")
    lib = tmp_path / "lib"
    dest = add_sound(src, lib)
    assert dest.exists() and dest.parent == lib
    assert dest.read_bytes() == src.read_bytes()


def test_add_sound_name_conflict(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    lib = tmp_path / "lib"
    a = add_sound(_mkfile(src_dir / "x.mp3"), lib)
    b = add_sound(_mkfile(src_dir / "x.mp3"), lib)
    assert a != b
    assert b.name.startswith("x (1)")


def test_add_sound_rejects_unknown_type(tmp_path):
    with pytest.raises(ValueError):
        add_sound(_mkfile(tmp_path / "notes.txt"), tmp_path / "lib")


def test_list_sounds_filters_and_sorts(tmp_path):
    _mkfile(tmp_path / "b.wav")
    _mkfile(tmp_path / "a.mp3")
    _mkfile(tmp_path / "c.txt")
    (tmp_path / "sub").mkdir()
    assert [p.name for p in list_sounds(tmp_path)] == ["a.mp3", "b.wav"]
    assert list_sounds(tmp_path / "missing") == []


def test_display_name():
    assert display_name(Path("/x/y/adhan al-aqsa.mp3")) == "adhan al-aqsa"


def test_rotation_empty():
    rot = ShuffledRotation(random.Random(1))
    assert rot.next([]) is None


def test_rotation_covers_all_once_per_cycle():
    clips = [Path(f"/lib/c{i}.mp3") for i in range(5)]
    rot = ShuffledRotation(random.Random(42))
    cycle1 = [rot.next(clips) for _ in range(5)]
    assert sorted(cycle1) == sorted(clips)
    cycle2 = [rot.next(clips) for _ in range(5)]
    assert sorted(cycle2) == sorted(clips)
    assert cycle1 != cycle2 or len(clips) == 1  # shuffled, not fixed order


def test_rotation_is_random_not_sequential():
    clips = [Path(f"/lib/c{i}.mp3") for i in range(6)]
    rot = ShuffledRotation(random.Random(7))
    order = [rot.next(clips) for _ in range(6)]
    assert order != clips  # not the input order


def test_rotation_drops_removed_files():
    clips = [Path(f"/lib/c{i}.mp3") for i in range(3)]
    rot = ShuffledRotation(random.Random(3))
    rot.next(clips)
    rot.next(clips)
    remaining = clips[:1]
    nxt = rot.next(remaining)
    assert nxt in remaining  # never returns a deleted file


def test_resolve_bismillah_voice():
    from isma_adhan.sounds import BISMILLAH_VOICES, resolve_bismillah_voice

    keys = {k for k, *_ in BISMILLAH_VOICES}
    assert resolve_bismillah_voice("husary") == "husary"
    picks = {resolve_bismillah_voice("random") for _ in range(40)}
    assert picks and picks <= keys
    assert len(picks) > 1  # 40 draws landing on one voice would be a miracle


def test_bismillah_random_setting_roundtrip(tmp_path):
    from isma_adhan.config import Settings, load_settings, save_settings

    s = Settings(bismillah_voice="random")
    save_settings(s, base=tmp_path)
    assert load_settings(base=tmp_path).bismillah_voice == "random"
