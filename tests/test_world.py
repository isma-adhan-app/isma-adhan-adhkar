"""World data integrity: countries/cities/coordinates/timezones."""
from zoneinfo import ZoneInfo

from isma_adhan import world


def test_countries_loaded():
    cs = world.countries()
    assert len(cs) >= 200
    isos = {iso for iso, _ in cs}
    assert "EG" in isos and "SA" in isos and "US" in isos


def test_egypt_cities():
    cities = world.cities_of("EG")
    assert cities
    names = [world.city_display(c) for c in cities]
    assert any("القاهرة" in n for n in names)
    cairo = next(c for c in cities if "القاهرة" in world.city_display(c))
    assert abs(cairo["lat"] - 30.0444) < 0.1
    assert abs(cairo["lng"] - 31.2357) < 0.1
    assert cairo["tz"] == "Africa/Cairo"


def test_all_cities_valid():
    for iso, _ in world.countries():
        for c in world.cities_of(iso):
            assert -90 <= c["lat"] <= 90, (iso, c)
            assert -180 <= c["lng"] <= 180, (iso, c)
            ZoneInfo(c["tz"])  # raises when the timezone name is invalid
            assert c["en"]


def test_country_display():
    assert world.country_display("EG") == "مصر"
    assert world.country_display("SA") == "السعودية"
    assert world.country_display("XX") == "XX"  # unknown: echo the code


def test_detect_location_never_raises():
    # On non-Windows hosts detection is impossible and must return None;
    # on Windows it returns a city from the dataset. Either way, no raise,
    # and a result must be internally consistent.
    found = world.detect_location()
    if found is not None:
        iso, city = found["iso"], found["city"]
        assert city in world.cities_of(iso)
