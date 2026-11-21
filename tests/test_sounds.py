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


def test_resolve_adhan():
    from isma_adhan.sounds import (
        ADHAN_VOICES,
        ADHAN_RANDOM_TOKEN,
        adhan_display,
        resolve_adhan,
    )

    default = resolve_adhan("")
    assert default is not None and default.name == "husary.mp3"
    fixed = resolve_adhan("bundled:refaat")
    assert fixed is not None and fixed.name == "refaat.mp3"
    picks = {resolve_adhan(ADHAN_RANDOM_TOKEN).name for _ in range(60)}
    assert len(picks) > 1
    assert all(name in {f"{k}.mp3" for k, *_ in ADHAN_VOICES} for name in picks)
    missing = resolve_adhan("/nonexistent/user clip.mp3")
    assert missing is None
    assert adhan_display("") == "محمود خليل الحصري - أذان القاهرة"
    assert adhan_display(ADHAN_RANDOM_TOKEN) == "عشوائي"
    assert adhan_display("bundled:minshawi") == "محمد صديق المنشاوي"
    assert adhan_display("/x/y/my adhan.mp3") == "my adhan"


def test_resolve_adhan_random_includes_user_files(tmp_path):
    from isma_adhan.sounds import ADHAN_RANDOM_TOKEN, resolve_adhan

    own = tmp_path / "my adhan.mp3"
    own.write_bytes(b"x" * 1000)
    picks = {resolve_adhan(ADHAN_RANDOM_TOKEN, tmp_path).name for _ in range(80)}
    assert "my adhan.mp3" in picks
    assert len(picks) > 1


def test_resolve_alert_defaults_match_pre17_behavior():
    from isma_adhan.sounds import ALERT_KINDS, resolve_alert

    assert set(ALERT_KINDS) == {"pre_adhan", "iqama"}
    assert resolve_alert("pre_adhan", "").name == "soft_chime.wav"
    assert resolve_alert("iqama", "").name == "iqama_tone.wav"
    assert resolve_alert("pre_adhan", None).name == "soft_chime.wav"


def test_resolve_alert_bundled_keys():
    from isma_adhan.sounds import ALERT_BUNDLED, resolve_alert

    for kind, entries in ALERT_BUNDLED.items():
        for key, _name, filename in entries:
            p = resolve_alert(kind, f"alerts:{key}")
            assert p is not None and p.name == filename, (kind, key)
            assert p.exists(), f"generated tone missing: {p}"


def test_resolve_alert_random_covers_bundled():
    from isma_adhan.sounds import ALERT_BUNDLED, ALERT_RANDOM_TOKEN, resolve_alert

    for kind, entries in ALERT_BUNDLED.items():
        names = {resolve_alert(kind, ALERT_RANDOM_TOKEN).name for _ in range(120)}
        assert names == {f for *_x, f in entries}, (kind, names)


def test_resolve_alert_random_includes_user_files(tmp_path):
    from isma_adhan.sounds import ALERT_RANDOM_TOKEN, resolve_alert

    own = tmp_path / "اقتربت صلاة الظهر.mp3"
    own.write_bytes(b"x" * 1000)
    picks = {resolve_alert("pre_adhan", ALERT_RANDOM_TOKEN, tmp_path).name for _ in range(150)}
    assert own.name in picks
    assert len(picks) > 1


def test_resolve_alert_missing_user_file_returns_none():
    from isma_adhan.sounds import resolve_alert

    assert resolve_alert("iqama", "/nonexistent/my iqama.mp3") is None


def test_resolve_alert_user_file(tmp_path):
    from isma_adhan.sounds import resolve_alert

    own = tmp_path / "tone.wav"
    own.write_bytes(b"RIFFfake")
    assert resolve_alert("pre_adhan", str(own), tmp_path) == own


def test_alert_display():
    from isma_adhan.sounds import ALERT_RANDOM_TOKEN, alert_display

    assert alert_display("pre_adhan", "") == "جرس هادئ"
    assert alert_display("iqama", "") == "تنبيه قصير"
    assert alert_display("pre_adhan", ALERT_RANDOM_TOKEN) == "عشوائي"
    assert alert_display("iqama", "alerts:iqama_low") == "نغمة منخفضة"
    assert alert_display("pre_adhan", "/x/y/my reminder.mp3") == "my reminder"


def test_resolve_alert_post_adhkar():
    from isma_adhan.sounds import ALERT_RANDOM_TOKEN, bundled_adhkar, resolve_alert

    # empty = keep the shuffled rotation (caller handles the default)
    assert resolve_alert("post_adhkar", "") is None
    assert resolve_alert("post_adhkar", None) is None
    bundled = bundled_adhkar()
    assert bundled, "bundled adhkar required for this test"
    key = bundled[0][0].name
    assert resolve_alert("post_adhkar", f"alerts:{key}") == bundled[0][0]
    assert resolve_alert("post_adhkar", "alerts:no-such-clip.mp3") is None
    pool = {str(p) for p, _ in bundled}
    picks = {str(resolve_alert("post_adhkar", ALERT_RANDOM_TOKEN)) for _ in range(30)}
    assert picks and picks <= pool
    assert resolve_alert("post_adhkar", "/nonexistent/ذكر.mp3") is None


def test_resolve_alert_post_adhkar_random_includes_user_files(tmp_path):
    from isma_adhan.sounds import ALERT_RANDOM_TOKEN, resolve_alert

    own = tmp_path / "my dhikr.mp3"
    own.write_bytes(b"x" * 1000)
    picks = {resolve_alert("post_adhkar", ALERT_RANDOM_TOKEN, tmp_path).name for _ in range(200)}
    assert own.name in picks


def test_alert_display_post_adhkar():
    from isma_adhan.sounds import ALERT_RANDOM_TOKEN, alert_display, bundled_adhkar

    assert alert_display("post_adhkar", "") == "تدوير مكتبة الأذكار"
    assert alert_display("post_adhkar", ALERT_RANDOM_TOKEN) == "عشوائي"
    bundled = bundled_adhkar()
    assert alert_display("post_adhkar", f"alerts:{bundled[0][0].name}") == bundled[0][1]
    assert alert_display("post_adhkar", "/x/y/ذكري.mp3") == "ذكري"
