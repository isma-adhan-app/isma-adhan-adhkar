import json
from pathlib import Path

from isma_adhan.config import Settings, load_settings, save_settings, settings_path
from isma_adhan.prayer_times import ADHAN_PRAYERS


def test_defaults():
    s = Settings()
    assert s.city == "القاهرة"
    assert s.country == "مصر"
    assert s.method == "egypt"
    assert all(v == 5 for v in s.pre_adhan_per.values())
    assert all(v == 10 for v in s.iqama_per.values())
    assert all(v == 0 for v in s.post_adhkar_per.values())
    assert 0 <= s.volume <= 100


def test_accessors_with_fallback():
    s = Settings()
    assert s.pre_adhan_for("fajr") == 5
    assert s.iqama_for("isha") == 10
    assert s.post_adhkar_for("dhuhr") == 0
    s.pre_adhan_per = {"all": 7, "fajr": 15}
    assert s.pre_adhan_for("fajr") == 15
    assert s.pre_adhan_for("maghrib") == 7
    assert s.adhan_sound_for("fajr") == ""
    s.adhan_sounds = {"all": "/x/all.mp3", "fajr": "/x/fajr.mp3"}
    assert s.adhan_sound_for("fajr") == "/x/fajr.mp3"
    assert s.adhan_sound_for("asr") == "/x/all.mp3"


def test_roundtrip(tmp_path):
    s = Settings(
        city="أسوان",
        volume=55,
        adhan_sounds={"all": "/x/adhan.mp3"},
        pre_adhan_per={p: 15 for p in ADHAN_PRAYERS},
        post_adhkar_per={p: 10 for p in ADHAN_PRAYERS},
    )
    save_settings(s, base=tmp_path)
    loaded = load_settings(base=tmp_path)
    assert loaded == s
    assert settings_path(tmp_path).exists()


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    settings_path(tmp_path).parent.mkdir(parents=True, exist_ok=True)
    settings_path(tmp_path).write_text("{not valid json", encoding="utf-8")
    assert load_settings(base=tmp_path) == Settings()


def test_unknown_keys_ignored(tmp_path):
    settings_path(tmp_path).parent.mkdir(parents=True, exist_ok=True)
    settings_path(tmp_path).write_text(
        json.dumps({"country": "مصر", "city": "الأقصر", "future_option": 1}), encoding="utf-8"
    )
    s = load_settings(base=tmp_path)
    assert s.city == "الأقصر"
    assert not hasattr(s, "future_option")


def test_migration_from_v1_0(tmp_path):
    old = {
        "city": "الإسكندرية",
        "pre_adhan_minutes": 15,
        "iqama_minutes": 20,
        "adhan_sound": "/x/adhan.mp3",
        "use_custom_coords": False,
        "volume": 70,
    }
    settings_path(tmp_path).parent.mkdir(parents=True, exist_ok=True)
    settings_path(tmp_path).write_text(json.dumps(old), encoding="utf-8")
    s = load_settings(base=tmp_path)
    assert all(v == 15 for v in s.pre_adhan_per.values())
    assert all(v == 20 for v in s.iqama_per.values())
    assert s.adhan_sounds.get("all") == "/x/adhan.mp3"
    assert s.volume == 70
    # Alexandria resolves to its coordinates through the built-in city list
    assert abs(s.lat - 31.2001) < 0.01
    assert abs(s.lng - 29.9187) < 0.01
    assert s.country == "مصر"


def test_migration_custom_coords_win(tmp_path):
    old = {
        "city": "القاهرة",
        "use_custom_coords": True,
        "custom_lat": 25.6872,
        "custom_lng": 32.6396,
    }
    settings_path(tmp_path).parent.mkdir(parents=True, exist_ok=True)
    settings_path(tmp_path).write_text(json.dumps(old), encoding="utf-8")
    s = load_settings(base=tmp_path)
    assert abs(s.lat - 25.6872) < 0.001
    assert abs(s.lng - 32.6396) < 0.001


def test_lat_lng_accessor():
    s = Settings(lat=31.2001, lng=29.9187)
    assert s.lat_lng() == (31.2001, 29.9187)


def test_date_tools_convert():
    from isma_adhan.date_tools import BAD_DATE_MSG, convert_date_text

    out = convert_date_text("21/11/2026")
    assert "2026 م يوافق" in out and "هـ." in out
    out = convert_date_text("2026-11-21")
    assert "يوافق" in out
    out = convert_date_text("1/9/1447")
    assert "1447 هـ يوافق" in out and "م." in out
    assert convert_date_text("blah") == BAD_DATE_MSG
    assert convert_date_text("32/13/2026") == BAD_DATE_MSG


def test_alert_sound_settings_roundtrip_and_fallback(tmp_path):
    from isma_adhan.config import Settings, load_settings, save_settings

    s = Settings()
    # defaults: empty dicts -> empty entry -> the built-in default tone
    assert s.pre_adhan_sound_for("dhuhr") == ""
    assert s.iqama_sound_for("fajr") == ""
    s.pre_adhan_sounds = {"all": "alerts:random", "dhuhr": "/x/اقتربت صلاة الظهر.mp3"}
    s.iqama_sounds = {"maghrib": "alerts:iqama_low"}
    save_settings(s, base=tmp_path)
    loaded = load_settings(base=tmp_path)
    assert loaded.pre_adhan_sound_for("dhuhr") == "/x/اقتربت صلاة الظهر.mp3"
    assert loaded.pre_adhan_sound_for("fajr") == "alerts:random"  # falls back to "all"
    assert loaded.iqama_sound_for("maghrib") == "alerts:iqama_low"
    assert loaded.iqama_sound_for("dhuhr") == ""  # no "all", no prayer entry


def test_sound_dirs_include_alert_folders(tmp_path):
    from isma_adhan.config import ensure_dirs, sound_dirs

    dirs = sound_dirs(tmp_path)
    assert dirs["pre_adhan"].name == "pre_adhan"
    assert dirs["iqama"].name == "iqama"
    ensure_dirs(tmp_path)
    for d in dirs.values():
        assert d.is_dir()


def test_post_adhkar_sound_settings_roundtrip(tmp_path):
    from isma_adhan.config import Settings, load_settings, save_settings

    s = Settings()
    assert s.post_adhkar_sound_for("dhuhr") == ""  # default = shuffled rotation
    s.post_adhkar_sounds = {"all": "alerts:random", "maghrib": "alerts:001.mp3"}
    save_settings(s, base=tmp_path)
    loaded = load_settings(base=tmp_path)
    assert loaded.post_adhkar_sound_for("maghrib") == "alerts:001.mp3"
    assert loaded.post_adhkar_sound_for("fajr") == "alerts:random"
    assert loaded.post_adhkar_sound_for("isha") == "alerts:random"
