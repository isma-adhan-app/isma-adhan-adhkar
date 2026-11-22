"""In-app updater (v1.8): version compare, manifest parsing, hash-verified
download. No network in tests - download is exercised against a local file.
"""
from __future__ import annotations

import hashlib

import pytest

from isma_adhan import updater


def test_version_tuple():
    assert updater.version_tuple("1.8.0") == (1, 8, 0)
    assert updater.version_tuple("v1.10.2") == (1, 10, 2)
    assert updater.version_tuple("1.8") == (1, 8, 0)


def test_is_newer():
    assert updater.is_newer("1.9.0", "1.8.0") is True
    assert updater.is_newer("1.8.0", "1.8.0") is False
    assert updater.is_newer("1.8.0", "1.8.1") is False
    assert updater.is_newer("2.0", "1.99.99") is True
    assert updater.is_newer("1.8.1", "1.8") is True


def test_current_arch_is_one_of_the_two():
    assert updater.current_arch() in ("x64", "x86")


def test_check_parses_manifest(monkeypatch):
    data = {
        "version": "9.9.9",
        "tag": "t",
        "installers": {
            "x64": {"url": "https://github.com/isma-adhan-app/isma-adhan-adhkar/releases/download/test/IsmaAdhan-Setup.exe", "sha256": "a" * 64},
            "x86": {"url": "https://github.com/isma-adhan-app/isma-adhan-adhkar/releases/download/test/IsmaAdhan-Setup-x86.exe", "sha256": "b" * 64},
        },
    }
    monkeypatch.setattr(updater, "fetch_latest", lambda url=None: data)
    info = updater.check()
    assert info is not None
    assert info.version == "9.9.9"
    assert info.newer is True  # 9.9.9 > any real current version
    assert info.url == data["installers"][updater.current_arch()]["url"]


def test_check_rejects_bad_manifests(monkeypatch):
    monkeypatch.setattr(updater, "fetch_latest", lambda url=None: {"version": "", "installers": {}})
    assert updater.check() is None
    monkeypatch.setattr(updater, "fetch_latest", lambda url=None: {
        "version": "9.9.9",
        "installers": {"x64": {"url": "ftp://nope", "sha256": "a" * 64},
                        "x86": {"url": "ftp://nope", "sha256": "b" * 64}},
    })
    assert updater.check() is None


def test_check_network_failure_raises(monkeypatch):
    def boom(url=None):
        raise OSError("offline")

    monkeypatch.setattr(updater, "fetch_latest", boom)
    with pytest.raises(OSError):
        updater.check()


def test_download_verifies_hash(tmp_path, monkeypatch):
    payload = b"installer-bytes-" * 1000
    good = hashlib.sha256(payload).hexdigest()

    class FakeResp:
        def __init__(self, data):
            self._data = data
            self._pos = 0

        def read(self, n=-1):
            chunk = self._data[self._pos:self._pos + (n if n > 0 else len(self._data))]
            self._pos += len(chunk)
            return chunk

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(updater.urllib.request, "urlopen",
                        lambda req, timeout=None: FakeResp(payload))
    info = updater.UpdateInfo(version="9.9.9", url="https://github.com/isma-adhan-app/isma-adhan-adhkar/releases/download/test/IsmaAdhan-Setup.exe",
                              sha256=good, newer=True)
    out = updater.download(info, tmp_path)
    assert out.read_bytes() == payload

    info_bad = updater.UpdateInfo(version="9.9.9", url="https://github.com/isma-adhan-app/isma-adhan-adhkar/releases/download/test/IsmaAdhan-Setup.exe",
                                  sha256="0" * 64, newer=True)
    with pytest.raises(ValueError, match="hash"):
        updater.download(info_bad, tmp_path)
    # a failed verification must not leave the unverified file behind
    assert list(tmp_path.rglob("IsmaAdhan-Update.exe")) == [out]

@pytest.mark.parametrize('value', ['1.8-beta', '', 'foo', '1', '1.8.0.1'])
def test_invalid_versions(value):
    with pytest.raises(ValueError):
        updater.version_tuple(value)

@pytest.mark.parametrize('url', [
    'http://github.com/isma-adhan-app/isma-adhan-adhkar/releases/download/x/IsmaAdhan-Setup.exe',
    'https://github.com.evil.invalid/isma-adhan-app/isma-adhan-adhkar/releases/download/x/IsmaAdhan-Setup.exe',
    'https://github.com/other/repo/releases/download/x/IsmaAdhan-Setup.exe',
    'https://github.com/isma-adhan-app/isma-adhan-adhkar/releases/download/x/IsmaAdhan-Setup.exe?x=1',
])
def test_rejects_untrusted_urls(url):
    assert not updater.valid_installer_url(url)

@pytest.mark.parametrize('arch,name', [('x86','IsmaAdhan-Setup.exe'),('x64','IsmaAdhan-Setup-x86.exe')])
def test_manifest_cannot_swap_architectures(monkeypatch, arch, name):
    monkeypatch.setattr(updater, 'current_arch', lambda: arch)
    monkeypatch.setattr(updater, 'fetch_latest', lambda url: {
        'version':'9.9.9', 'installers': {arch: {
            'url':'https://github.com/isma-adhan-app/isma-adhan-adhkar/releases/download/test/'+name,
            'sha256':'a'*64}}})
    assert updater.check() is None


def test_download_cleans_partial_file_on_network_error(tmp_path, monkeypatch):
    class Broken:
        def __enter__(self): return self
        def __exit__(self,*a): return False
        def read(self,n): raise OSError('offline')
    monkeypatch.setattr(updater.urllib.request, 'urlopen', lambda *a,**kw: Broken())
    info=updater.UpdateInfo('9.9.9','https://github.com/isma-adhan-app/isma-adhan-adhkar/releases/download/test/IsmaAdhan-Setup.exe','a'*64,True)
    with pytest.raises(OSError): updater.download(info,tmp_path)
    assert not list(tmp_path.iterdir())
