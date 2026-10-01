"""Tests for the Quantum C2 Tier-1 ports: kev, gitdork, lockknife,
quantum_android."""
import json
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.recon import gitdork, kev  # noqa: E402
from quantum.weapons.techniques import lockknife  # noqa: E402


# ---------------------------------------------------------------------- kev
def test_kev_engine_sample_fallback(tmp_path, monkeypatch):
    eng = kev.ThreatIntelEngine(cache_dir=str(tmp_path))
    # dead URL -> sample fallback, never raises
    monkeypatch.setattr(kev, "KEV_URL_PRIMARY", "http://127.0.0.1:1/kev.json")
    monkeypatch.setattr(kev, "KEV_URL_BACKUP", "http://127.0.0.1:1/kev2.json")
    vulns = eng.fetch_kev()
    assert vulns, "sample fallback should return entries"
    assert eng.source == "sample"
    zc = eng.analyze_zero_click(vulns)
    assert any(v.get("zero_click") for v in zc), \
        "sample set includes a zero-click entry"
    assert eng.analyze_pre_auth(vulns)
    assert eng.vendor_breakdown(vulns)


def test_kev_analyze_indicators():
    vulns = [
        {"cveID": "CVE-2020-1111", "title": "Crafted message RCE",
         "short_description": "remote code execution with no user interaction"},
        {"cveID": "CVE-2020-2222", "title": "Local file read"},
    ]
    zc = kev._filter_indicators(vulns, kev.ZERO_CLICK_INDICATORS,
                                "zero_click")
    assert len(zc) == 1 and zc[0]["cveID"] == "CVE-2020-1111"
    pa = kev._filter_indicators(vulns, kev.PRE_AUTH_INDICATORS,
                               "pre_auth")
    assert len(pa) == 1 and pa[0]["cveID"] == "CVE-2020-1111"


def test_kev_lookup_via_cache(tmp_path, monkeypatch):
    # write a small cache and point the engine at it — hermetic, no net
    cache = tmp_path / "kev.json"
    cache.write_text(json.dumps([
        {"cveID": "CVE-2023-34362", "vendor": "Progress Software",
         "product": "MOVEit Transfer", "title": "MOVEit Transfer SQL Injection",
         "short_description": "unauthenticated SQL injection RCE",
         "notes": "exploited in the wild"}]), encoding="utf-8")
    eng = kev.ThreatIntelEngine(cache_dir=str(tmp_path))
    monkeypatch.setattr(kev, "_engine", eng)
    r = kev.lookup("CVE-2023-34362")
    assert r["ok"] and r["in_kev"] and r["pre_auth"] is True
    r2 = kev.lookup("CVE-9999-0001")
    assert r2["ok"] and r2["in_kev"] is False


def test_kev_check_kev_json_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(kev, "KEV_URL_PRIMARY", "http://127.0.0.1:1/kev.json")
    monkeypatch.setattr(kev, "KEV_URL_BACKUP", "http://127.0.0.1:1/kev2.json")
    eng = kev.ThreatIntelEngine(cache_dir=str(tmp_path))
    monkeypatch.setattr(kev, "_engine", eng)
    r = kev.check_kev()
    assert r["ok"] is True and r["total"] >= 3


# ----------------------------------------------------------------- gitdork
def test_gitdork_list_dorks():
    r = gitdork.list_dorks()
    assert r["ok"] and r["count"] >= 50
    assert any("id_rsa" in d for d in r["dorks"])


def test_gitdork_search_without_credentials_clean_error(monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_USER", raising=False)
    monkeypatch.delenv("GH_PWD", raising=False)
    r = gitdork.search_dork("filename:.npmrc _auth")
    assert r["ok"] is False and "GH_TOKEN" in r["error"]


def test_gitdork_scan_requires_scope():
    r = gitdork.scan()
    assert r["ok"] is False and "repo=" in r["error"]


def test_gitdork_scan_custom_dorks_no_creds(monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_USER", raising=False)
    monkeypatch.delenv("GH_PWD", raising=False)
    r = gitdork.scan(repo="octocat/hello-world",
                      dorks=["filename:secret"], max_dorks=1)
    assert r["ok"] is True and r["checked"] == 1 and r["hit_count"] == 0


# --------------------------------------------------------------- lockknife
def test_lockknife_devices_json_safe():
    r = lockknife.devices()
    assert isinstance(r, dict) and "devices" in r
    # ok=True when adb exists, ok=False with a clean error otherwise
    assert r["ok"] in (True, False)
    if not r["ok"]:
        assert r["error"]


def test_lockknife_extractions_never_raise():
    for fn in (lockknife.device_info, lockknife.extract_packages,
               lockknife.extract_settings, lockknife.extract_app_data,
               lockknife.full_report):
        r = fn()
        assert isinstance(r, dict)
        assert "ok" in r
        if not r.get("ok"):
            assert r.get("error")


def test_lockknife_screenshot_bad_path_never_raises(tmp_path):
    r = lockknife.screenshot(str(tmp_path / "cap.png"))
    assert isinstance(r, dict) and "ok" in r


def test_lockknife_connect_unreachable_clean():
    r = lockknife.connect("127.0.0.1", 59998)
    assert isinstance(r, dict) and "ok" in r


# ---------------------------------------------------------------- quantum_android
def test_quantum_android_imports_and_crypto():
    from quantum.weapons import quantum_android as qa
    assert hasattr(qa, "QuantumAndroidFramework")
    # XOR payload crypto is self-inverse; DGA is deterministic
    key = os.urandom(32)
    data = b"quantum test payload"
    assert qa.CryptoEngine.encrypt_payload(
        qa.CryptoEngine.encrypt_payload(data, key), key) == data
    domains = qa.CryptoEngine.generate_dga("example.com", 7, count=5)
    assert len(domains) == 5 and len(set(domains)) == 5
