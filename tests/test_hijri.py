from datetime import date

from isma_adhan.hijri import gregorian_to_hijri, hijri_label, weekday_label


def test_known_period_hijri_year():
    # late November 2026 is in hijri year 1448 (1448 began ~June 2026)
    hy, hm, hd = gregorian_to_hijri(2026, 11, 20)
    assert hy == 1448
    assert hm in (5, 6)  # Jumada al-Ula / al-Akhirah (astronomical approx.)


def test_month_bounds():
    for month in range(1, 13):
        hy, hm, hd = gregorian_to_hijri(2026, month, 15)
        assert 1 <= hm <= 12
        assert 1 <= hd <= 30
        assert 1446 <= hy <= 1448


def test_labels():
    d = date(2026, 11, 20)  # a Friday
    assert weekday_label(d) == "الجمعة"
    label = hijri_label(d)
    assert "1448" in label
    assert label.endswith("هـ")


def test_gregorian_label_arabic():
    from isma_adhan.hijri import gregorian_label

    assert gregorian_label(date(2026, 11, 21)) == "21 نوفمبر 2026 م"
    assert gregorian_label(date(2026, 1, 1)) == "1 يناير 2026 م"


def test_hijri_gregorian_roundtrip():
    from datetime import date, timedelta

    from isma_adhan.hijri import gregorian_to_hijri, hijri_to_gregorian

    d = date(2024, 1, 1)
    for _ in range(800):
        hy, hm, hd = gregorian_to_hijri(d.year, d.month, d.day)
        assert hijri_to_gregorian(hy, hm, hd) == (d.year, d.month, d.day)
        d += timedelta(days=1)


def test_notable_dates():
    from datetime import date, timedelta

    from isma_adhan.hijri import NOTABLE_DATES, notable_announcement, notable_label

    assert NOTABLE_DATES[(9, 1)] == "أول شهر رمضان"
    # find a gregorian day that is 1 Ramadan in the covered range
    from isma_adhan.hijri import gregorian_to_hijri

    d = date(2026, 1, 1)
    found = None
    for _ in range(800):
        hy, hm, hd = gregorian_to_hijri(d.year, d.month, d.day)
        if (hm, hd) == (9, 1):
            found = d
            break
        d += timedelta(days=1)
    assert found is not None
    assert notable_label(found) == "أول شهر رمضان"
    assert "اليوم أول شهر رمضان" in notable_announcement(found)
    assert "غداً أول شهر رمضان" in notable_announcement(found - timedelta(days=1))
    assert notable_announcement(found + timedelta(days=5)) == ""
