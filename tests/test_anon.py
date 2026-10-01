"""Tests for quantum.anon (Kodachi-style anonymous networking).

Honesty gates: the stack must never claim bundled Kodachi binaries or a
working anonymization path that isn't probed. No network I/O here.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.anon import kodachi as K  # noqa: E402


def test_status_is_honest_about_bundling():
    st = K.anon_status()
    assert st["kodachi_bundled"] is False
    assert "NOT bundled" in st["note"]
    for name in ("tor", "dnscrypt", "proxychains", "obfs4", "kodachi"):
        assert name in st["components"]
        entry = st["components"][name]
        # binary is a path or None — never a fake boolean
        assert entry["binary"] is None or isinstance(entry["binary"], str)


def test_detect_finds_installed_binary(monkeypatch, tmp_path):
    fake = tmp_path / ("tor.exe" if os.name == "nt" else "tor")
    fake.write_text("#!/bin/sh\n")
    def fake_which(name, path=None):
        return str(fake) if name == "tor" else None
    monkeypatch.setattr(K.shutil, "which", fake_which)
    monkeypatch.setattr(K, "tcp_probe", lambda *a, **k: True)
    comps = K.detect()
    assert comps["tor"]["binary"] == str(fake)
    assert comps["tor"]["running"] is True
    assert comps["proxychains"]["binary"] is None


def test_detect_marks_missing_tools(monkeypatch):
    monkeypatch.setattr(K.shutil, "which", lambda name, path=None: None)
    comps = K.detect()
    for spec in comps.values():
        assert spec["binary"] is None
    # no port probe happens when the binary is absent
    st = K.anon_status()
    assert st["tor_socks_ready"] is False


def test_proxychains_config_is_generated(tmp_path):
    p = K.write_proxychains(path=str(tmp_path / "proxychains.conf"))
    txt = open(p, encoding="utf-8").read()
    assert "strict_chain" in txt
    assert "proxy_dns" in txt
    assert "socks5 127.0.0.1 9050" in txt


def test_dnscrypt_config_is_doh_local_and_dnssec(tmp_path):
    p = K.write_dnscrypt_config(path=str(tmp_path / "dnscrypt.toml"))
    txt = open(p, encoding="utf-8").read()
    assert "https://cloudflare-dns.com/dns-query" in txt
    assert "https://dns.google/dns-query" in txt
    assert "127.0.0.1:5353" in txt          # unprivileged local listener
    assert "require_dnssec = true" in txt
    assert "require_nolog = true" in txt


def test_launch_unknown_component_is_honest_error():
    res = K.launch("nope")
    assert res["launched"] is False
    assert "unknown" in res["error"]


def test_launch_missing_binary_reports_missing(monkeypatch):
    monkeypatch.setattr(K.shutil, "which", lambda name, path=None: None)
    res = K.launch("tor")
    assert res["launched"] is False
    assert "not installed" in res["error"]
    assert "NOT bundled" in res["note"]


def test_anon_fetch_without_tor_is_honest(monkeypatch):
    monkeypatch.setattr(K, "detect", lambda: {
        "tor": {"binary": None, "running": False, "role": ""}})
    res = K.anon_fetch("http://example.onion/")
    assert "error" in res
    assert "9050" in res["error"]
    # and it must NOT silently fall back to a clearnet request
    assert "status" not in res
