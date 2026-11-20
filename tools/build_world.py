#!/usr/bin/env python3
"""Build assets/world.json + assets/windows_zones.json from GeoNames + CLDR.

Inputs (download first):
  /tmp/cities15000.txt   GeoNames cities15000 (CC-BY 4.0, geonames.org)
  /tmp/countryInfo.txt   GeoNames countryInfo (CC-BY 4.0)
  /tmp/windowsZones.xml  CLDR supplemental windowsZones (Unicode license)

Keeps per country: its capital plus up to 12 cities with population >= 50000
(fewer for small countries). Arabic city names are recovered from GeoNames
alternate names when a clean Arabic-script variant exists; Arabic country
names come from the curated table below.
"""
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

ARABIC_COUNTRIES = {
    "EG": "مصر", "SA": "السعودية", "AE": "الإمارات", "KW": "الكويت", "QA": "قطر",
    "BH": "البحرين", "OM": "عمان", "YE": "اليمن", "IQ": "العراق", "JO": "الأردن",
    "LB": "لبنان", "SY": "سوريا", "PS": "فلسطين", "LY": "ليبيا", "TN": "تونس",
    "DZ": "الجزائر", "MA": "المغرب", "SD": "السودان", "SS": "جنوب السودان", "SO": "الصومال",
    "DJ": "جيبوتي", "KM": "جزر القمر", "MR": "موريتانيا", "TR": "تركيا", "IR": "إيران",
    "PK": "باكستان", "AF": "أفغانستان", "BD": "بنجلاديش", "ID": "إندونيسيا", "MY": "ماليزيا",
    "IN": "الهند", "NG": "نيجيريا", "ML": "مالي", "NE": "النيجر", "TD": "تشاد",
    "SN": "السنغال", "GN": "غينيا", "BF": "بوركينا فاسو", "CI": "ساحل العاج", "GH": "غانا",
    "CM": "الكاميرون", "ET": "إثيوبيا", "ER": "إريتريا", "KE": "كينيا", "TZ": "تنزانيا",
    "UG": "أوغندا", "RW": "رواندا", "MZ": "موزمبيق", "MG": "مدغشقر", "ZA": "جنوب أفريقيا",
    "ZW": "زيمبابوي", "ZM": "زامبيا", "BW": "بوتسوانا", "NA": "ناميبيا", "AO": "أنجولا",
    "CD": "الكونغو الديمقراطية", "CG": "الكونغو", "GA": "الجابون", "GQ": "غينيا الاستوائية",
    "CF": "أفريقيا الوسطى", "BJ": "بنين", "TG": "توجو", "LR": "ليبيريا", "SL": "سيراليون",
    "GW": "غينيا بيساو", "GM": "جامبيا", "CV": "الرأس الأخضر", "ST": "ساو تومي وبرينسيب",
    "MU": "موريشيوس", "SC": "سيشل", "US": "الولايات المتحدة", "CA": "كندا", "MX": "المكسيك",
    "BR": "البرازيل", "AR": "الأرجنتين", "CL": "تشيلي", "CO": "كولومبيا", "PE": "بيرو",
    "VE": "فنزويلا", "EC": "الإكوادور", "BO": "بوليفيا", "PY": "باراجواي", "UY": "أوروجواي",
    "CU": "كوبا", "DO": "جمهورية الدومينيكان", "HT": "هايتي", "JM": "جامايكا", "GT": "جواتيمالا",
    "GB": "بريطانيا", "IE": "أيرلندا", "FR": "فرنسا", "DE": "ألمانيا", "IT": "إيطاليا",
    "ES": "إسبانيا", "PT": "البرتغال", "NL": "هولندا", "BE": "بلجيكا", "LU": "لوكسمبورج",
    "CH": "سويسرا", "AT": "النمسا", "SE": "السويد", "NO": "النرويج", "DK": "الدنمارك",
    "FI": "فنلندا", "IS": "أيسلندا", "PL": "بولندا", "CZ": "التشيك", "SK": "سلوفاكيا",
    "HU": "المجر", "RO": "رومانيا", "BG": "بلغاريا", "GR": "اليونان", "HR": "كرواتيا",
    "SI": "سلوفينيا", "RS": "صربيا", "BA": "البوسنة والهرسك", "ME": "الجبل الأسود",
    "MK": "مقدونيا الشمالية", "AL": "ألبانيا", "XK": "كوسوفو", "MD": "مولدوفا", "UA": "أوكرانيا",
    "BY": "بيلاروسيا", "RU": "روسيا", "LT": "ليتوانيا", "LV": "لاتفيا", "EE": "إستونيا",
    "MT": "مالطا", "CY": "قبرص", "CN": "الصين", "JP": "اليابان", "KR": "كوريا الجنوبية",
    "KP": "كوريا الشمالية", "MN": "منغوليا", "TH": "تايلاند", "VN": "فيتنام", "KH": "كمبوديا",
    "LA": "لاوس", "MM": "ميانمار", "PH": "الفلبين", "SG": "سنغافورة", "BN": "بروناي",
    "TL": "تيمور الشرقية", "NP": "نيبال", "LK": "سريلانكا", "MV": "جزر المالديف", "BT": "بوتان",
    "KZ": "كازاخستان", "UZ": "أوزبكستان", "TM": "تركمانستان", "KG": "قيرغيزستان", "TJ": "طاجيكستان",
    "AZ": "أذربيجان", "AM": "أرمينيا", "GE": "جورجيا", "AU": "أستراليا", "NZ": "نيوزيلندا",
    "FJ": "فيجي", "PG": "بابوا غينيا الجديدة", "IL": "إسرائيل", "XX": "",
}

# letters that mark a Persian/Urdu (not Arabic) spelling
NON_ARABIC_CHARS = set("گچپژڤڭںٹڈڑہۀە")
ARABIC_RE = re.compile(r"^[؀-ۿ\s\-'’.,()]+$")


def arabic_variant(alternates: str, fallback: str) -> str:
    for token in alternates.split(","):
        token = token.strip()
        if not token or len(token) < 2:
            continue
        if not ARABIC_RE.match(token):
            continue
        if any(c in NON_ARABIC_CHARS for c in token):
            continue
        if token == fallback:
            continue
        return token
    return ""


def main() -> None:
    countries = {}
    with open("/tmp/countryInfo.txt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 15:
                continue
            countries[p[0]] = {"en": p[4], "capital": p[5]}

    by_country = defaultdict(list)
    with open("/tmp/cities15000.txt", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 19:
                continue
            name, asciiname, alts = p[1], p[2], p[3]
            try:
                lat, lng, pop = float(p[4]), float(p[5]), int(p[14] or 0)
            except ValueError:
                continue
            code, fcode, tz = p[8], p[7], p[17]
            if not tz or "/" not in tz:
                continue
            by_country[code].append(
                {
                    "en": name,
                    "ar": arabic_variant(alts, name),
                    "lat": round(lat, 4),
                    "lng": round(lng, 4),
                    "tz": tz,
                    "pop": pop,
                    "capital": fcode == "PPLC",
                }
            )

    out = []
    for iso, info in sorted(countries.items(), key=lambda kv: (ARABIC_COUNTRIES.get(kv[0]) or kv[1]["en"])):
        cities = by_country.get(iso, [])
        if not cities:
            continue
        cities.sort(key=lambda c: -c["pop"])
        picked = [c for c in cities if c["capital"]][:1]
        picked += [c for c in cities if not c["capital"] and c["pop"] >= 50000][: 12 - len(picked)]
        if not picked:
            picked = cities[:1]
        for c in picked:
            c.pop("capital")
            if not c["ar"]:
                del c["ar"]
            if iso != "EG":
                pass
        out.append(
            {
                "iso": iso,
                "en": info["en"],
                "ar": ARABIC_COUNTRIES.get(iso, ""),
                "cities": picked,
            }
        )

    with open("assets/world.json", "w", encoding="utf-8") as f:
        json.dump({"countries": out}, f, ensure_ascii=False, separators=(",", ":"))

    zones = {}
    tree = ET.parse("/tmp/windowsZones.xml")
    for mz in tree.iter("mapZone"):
        if mz.get("territory") == "001":
            zones[mz.get("other")] = mz.get("type").split()[0]
    with open("assets/windows_zones.json", "w", encoding="utf-8") as f:
        json.dump(zones, f, ensure_ascii=False, separators=(",", ":"))

    total = sum(len(c["cities"]) for c in out)
    print(f"countries={len(out)} cities={total} zones={len(zones)}")


if __name__ == "__main__":
    main()
