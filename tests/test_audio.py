import time
import wave
from pathlib import Path

from isma_adhan.audio import NullPlayer, PygamePlayer, create_player


def _mk_wav(path: Path, seconds: float = 1.0) -> Path:
    import math

    rate = 44100
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = b"".join(
            int(0.5 * math.sin(2 * math.pi * 440 * t / rate) * 32767).to_bytes(2, "little", signed=True)
            for t in range(int(rate * seconds))
        )
        w.writeframes(frames)
    return path


def test_pygame_player_play_stop(tmp_path):
    wav = _mk_wav(tmp_path / "tone.wav", seconds=2.0)
    player = PygamePlayer()
    player.set_volume(50)
    player.play(wav)
    time.sleep(0.2)
    assert player.is_playing()
    player.stop()
    time.sleep(0.1)
    assert not player.is_playing()


def test_create_player_returns_working_player(tmp_path):
    player = create_player()
    player.set_volume(10)
    player.play(_mk_wav(tmp_path / "t.wav"))
    player.stop()


def test_null_player_noops(tmp_path):
    p = NullPlayer("no device")
    p.set_volume(100)
    p.play(tmp_path / "missing.wav")
    p.stop()
    assert not p.is_playing()
