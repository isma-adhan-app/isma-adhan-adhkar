"""Egyptian cities with coordinates, for the settings city picker.

Names are Arabic (the app UI is Arabic). Coordinates are city centers;
prayer-time differences within a city are well under a minute.
"""
from __future__ import annotations

# (arabic name, latitude, longitude) - ordered with the most populated first.
CITIES = [
    ("القاهرة", 30.0444, 31.2357),
    ("الجيزة", 30.0131, 31.2089),
    ("شبرا الخيمة", 30.1286, 31.2422),
    ("الإسكندرية", 31.2001, 29.9187),
    ("العبور", 30.2244, 31.4576),
    ("السادس من أكتوبر", 29.9527, 30.9219),
    ("القاهرة الجديدة", 30.0300, 31.4700),
    ("بورسعيد", 31.2653, 32.3019),
    ("السويس", 29.9668, 32.5498),
    ("الإسماعيلية", 30.5965, 32.2715),
    ("دمياط", 31.4165, 31.8133),
    ("الزقازيق", 30.5877, 31.5020),
    ("المنصورة", 31.0409, 31.3785),
    ("طنطا", 30.7865, 31.0004),
    ("دمنهور", 31.0341, 30.4682),
    ("كفر الشيخ", 31.1117, 30.9390),
    ("الفيوم", 29.3084, 30.8428),
    ("بني سويف", 29.0661, 31.0994),
    ("المنيا", 28.1099, 30.7503),
    ("أسيوط", 27.1809, 31.1837),
    ("سوهاج", 26.5560, 31.6948),
    ("قنا", 26.1551, 32.7160),
    ("الأقصر", 25.6872, 32.6396),
    ("أسوان", 24.0889, 32.8998),
    ("الغردقة", 27.2579, 33.8116),
    ("شرم الشيخ", 27.9158, 34.3299),
    ("مرسى مطروح", 31.3543, 27.2373),
    ("العريش", 31.1319, 33.7984),
]

DEFAULT_CITY = "القاهرة"


def city_names() -> list:
    return [c[0] for c in CITIES]


def city_coords(name: str) -> tuple:
    for n, lat, lng in CITIES:
        if n == name:
            return lat, lng
    raise KeyError(f"unknown city: {name}")


def has_city(name: str) -> bool:
    return any(c[0] == name for c in CITIES)
