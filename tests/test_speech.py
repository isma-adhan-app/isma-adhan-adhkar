
from isma_adhan.speech import pick_voice_id


class _V:
    def __init__(self, id="", name="", languages=()):
        self.id = id
        self.name = name
        self.languages = list(languages)


def test_prefers_arabic_voice_by_name():
    voices = [_V("v1", "Microsoft David - English (United States)"), _V("v2", "Microsoft Hoda Desktop - Arabic (Egypt)")]
    assert pick_voice_id(voices) == "v2"


def test_prefers_arabic_voice_by_id_locale():
    voices = [_V("MSTTS_V110_enUS_MarkM", "Mark"), _V("MSTTS_V110_arSA_NaayfM", "Naayf")]
    assert pick_voice_id(voices) == "MSTTS_V110_arSA_NaayfM"


def test_no_arabic_voice_returns_none():
    voices = [_V("v1", "Microsoft Zira - English (United States)", ["en-US"])]
    assert pick_voice_id(voices) is None


def test_empty_and_broken_voice_list():
    assert pick_voice_id([]) is None
    assert pick_voice_id([object()]) is None
