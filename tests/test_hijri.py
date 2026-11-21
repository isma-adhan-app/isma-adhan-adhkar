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
