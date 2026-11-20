import json
from pathlib import Path

from isma_adhan.config import Settings, load_settings, save_settings, settings_path


def test_defaults():
    s = Settings()
    assert s.city == "القاهرة"
    assert s.method == "egypt"
    assert s.pre_adhan_minutes == 5
    assert 0 <= s.volume <= 100


def test_roundtrip(tmp_path):
    s = Settings(city="أسوان", pre_adhan_minutes=15, volume=55, adhan_sound="/x/adhan.mp3")
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
        json.dumps({"city": "الأقصر", "future_option": 1}), encoding="utf-8"
    )
    s = load_settings(base=tmp_path)
    assert s.city == "الأقصر"
    assert not hasattr(s, "future_option")


def test_lat_lng_from_city():
    s = Settings(city="الإسكندرية")
    lat, lng = s.lat_lng()
    assert abs(lat - 31.2001) < 0.01
    assert abs(lng - 29.9187) < 0.01


def test_lat_lng_unknown_city_falls_back_to_cairo():
    s = Settings(city="مدينة غير موجودة")
    lat, lng = s.lat_lng()
    assert abs(lat - 30.0444) < 0.01
    assert abs(lng - 31.2357) < 0.01
