"""Multilingual strings registry (v1.8): key parity, fallback, formatting,
language detection mapping, prayer names."""
from __future__ import annotations

import pytest

from isma_adhan import strings


@pytest.fixture(autouse=True)
def _restore_language():
    yield
    strings.set_language("ar")


def test_all_languages_have_identical_keys():
    ar = set(strings._AR)
    for code, table in strings._TABLES.items():
        assert set(table) == ar, f"{code} key mismatch: " \
            f"missing={sorted(ar - set(table))} extra={sorted(set(table) - ar)}"


def test_every_value_is_nonempty_str():
    for code, table in strings._TABLES.items():
        for key, value in table.items():
            assert isinstance(value, str) and value.strip(), f"{code}.{key} empty"


def test_attribute_access_resolves_current_language():
    strings.set_language("ar")
    assert strings.APP_NAME == "اسمع أذان وأذكار"
    strings.set_language("en")
    assert strings.APP_NAME == "Isma Adhan & Adhkar"
    strings.set_language("fr")
    assert strings.MENU_EXIT == "Quitter"


def test_unknown_key_raises_attribute_error():
    with pytest.raises(AttributeError):
        strings.NO_SUCH_KEY_AT_ALL


def test_format_templates_render_in_each_language():
    for code in strings.LANGUAGES:
        strings.set_language(code)
        out = strings.msg_pre_adhan(strings.prayer_name("dhuhr"), 10)
        assert "{" not in out and "}" not in out
        assert "10" in out
        assert strings.prayer_name("dhuhr") in out
        about = strings.msg_about("1.8.0")
        assert "1.8.0" in about
        upd = strings.msg_update_available("1.9.0")
        assert "1.9.0" in upd and "{" not in upd


def test_language_from_langid():
    assert strings.language_from_langid(0x0401) == "ar"  # ar-SA
    assert strings.language_from_langid(0x0C01) == "ar"  # ar-EG
    assert strings.language_from_langid(0x0409) == "en"  # en-US
    assert strings.language_from_langid(0x0809) == "en"  # en-GB
    assert strings.language_from_langid(0x040C) == "fr"  # fr-FR
    assert strings.language_from_langid(0x0C0C) == "fr"  # fr-CA
    assert strings.language_from_langid(0x0419) == "ar"  # ru-RU -> default


def test_prayer_and_method_labels():
    strings.set_language("en")
    assert strings.prayer_name("isha") == "Isha"
    assert strings.method_label("egypt") == "Egyptian General Survey Authority"
    strings.set_language("ar")
    assert strings.prayer_name("isha") == "العشاء"
    assert strings.method_label("egypt") == "الهيئة المصرية العامة للمساحة"
    assert strings.method_label("unknown-method") == "unknown-method"


def test_hijri_labels_follow_language():
    from datetime import date

    from isma_adhan import hijri

    d = date(2026, 11, 22)
    strings.set_language("ar")
    assert "هـ" in hijri.hijri_label(d) and "م" in hijri.gregorian_label(d)
    strings.set_language("en")
    assert "AH" in hijri.hijri_label(d)
    assert "November" in hijri.gregorian_label(d)
    assert hijri.weekday_label(d) == "Sunday"
    strings.set_language("fr")
    assert "novembre" in hijri.gregorian_label(d)
    assert hijri.weekday_label(d) == "dimanche"


def test_convert_and_export_follow_language():
    from isma_adhan import date_tools

    strings.set_language("en")
    out = date_tools.convert_date_text("21/11/2026")
    assert "AH" in out and "corresponds to" in out
    strings.set_language("ar")
    out = date_tools.convert_date_text("21/11/2026")
    assert "يوافق" in out
    strings.set_language("fr")
    assert "hégire" in date_tools.convert_date_text("21/11/2026")


def test_notable_dates_and_sound_labels():
    from isma_adhan import hijri, sounds
    from datetime import date
    day = date(*hijri.hijri_to_gregorian(1448,1,1))
    for code in ('en','fr'):
        strings.set_language(code)
        assert hijri.notable_label(day)
        assert not any('\u0600' <= x <= '\u06ff' for x in hijri.notable_label(day))
        assert not any('\u0600' <= x <= '\u06ff' for x in sounds.bismillah_voice_name('husary'))
        assert sounds.alert_clip_name('pre_adhan','soft_chime') != sounds.ALERT_BUNDLED['pre_adhan'][0][1]
