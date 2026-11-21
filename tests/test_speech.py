
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


class _FakeNvda:
    def __init__(self, ok=True, raises=False):
        self.ok = ok
        self.raises = raises
        self.spoken = []

    def speak(self, text):
        if self.raises:
            raise RuntimeError("dll blew up")
        self.spoken.append(text)
        return self.ok


class _FakeSpeakerForTest:
    pass


def _run_sync(speaker, text):
    # Drive _run directly: the thread wrapper is irrelevant to routing.
    speaker._run(text)


def test_nvda_is_preferred_when_it_speaks(monkeypatch):
    from isma_adhan.speech import Speaker

    nvda = _FakeNvda(ok=True)
    s = Speaker(nvda=nvda)
    monkeypatch.setattr(s, "_sapi_speak", lambda t: (_ for _ in ()).throw(AssertionError("must not touch SAPI")))
    _run_sync(s, "السلام عليكم")
    assert nvda.spoken == ["السلام عليكم"]
    assert s.available is True


def test_falls_back_to_sapi_when_nvda_cannot_speak(monkeypatch):
    from isma_adhan.speech import Speaker

    calls = []
    for nvda in (_FakeNvda(ok=False), _FakeNvda(raises=True), None):
        s = Speaker(nvda=nvda)
        monkeypatch.setattr(s, "_sapi_speak", lambda t: calls.append(t))
        _run_sync(s, "اختبار")
    assert calls == ["اختبار"] * 3


def test_speak_queues_background_and_respects_availability():
    from isma_adhan.speech import Speaker

    s = Speaker(nvda=_FakeNvda())
    s.available = False
    assert s.speak("x") is False
