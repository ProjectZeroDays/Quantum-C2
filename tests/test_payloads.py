#!/usr/bin/env python3
"""Smoke + structural regression tests. No hardware required."""
import hashlib, importlib.util, json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
EXPLOITS = ROOT / "exploits"

PAYLOADS = {
    "cve_2023_41064_blastpass_webp":    dict(magic=b"RIFF", contains=[b"WEBP"]),
    "cve_2021_30860_forcedentry_jbig2": dict(magic=b"%PDF", contains=[b"/JBIG2Decode"], tail=b"%%EOF"),
    "cve_2023_41991_imessage_blastdoor":dict(magic=b"GIF89a"),
    "cve_2023_2569_whatsapp_mp4":       dict(magic=None, contains=[b"ftyp", b"stsc"]),
    "cve_2023_21268_mediacodec":        dict(magic=None, contains=[b"ftyp", b"stsc"]),
    "cve_2023_47081_imessage_mp4":      dict(magic=None, contains=[b"ftyp", b"stsc", b"mvhd"]),
    "cve_2017_13077_krack":             dict(magic=b"\x02\x03"),
    "cve_2023_31864_kdtree":            dict(exact_len=22),  # BB(2)+ii(8)+d(8)+I(4)
    "cve_2023_35964_schema":            dict(magic=b"SCHM"),
    "cve_2023_32780_rt_table":          dict(exact_len=18),  # 3xIPv4(12)+IH(6)
    "cve_2022_0847_dirtypipe":          dict(tail=b"\x0f\x05"),
}
DRIVERS = ["cve_2020_0022_bluefrag", "cve_2026_0073_adb_tls_bypass"]

def _load(stem):
    p = EXPLOITS / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(stem, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

@pytest.mark.parametrize("stem", sorted(PAYLOADS) + DRIVERS)
def test_module_loads(stem):
    assert (EXPLOITS / f"{stem}.py").exists()
    _load(stem)

@pytest.mark.parametrize("stem", sorted(PAYLOADS))
def test_build_returns_bytes(stem):
    data = _load(stem).build()
    assert isinstance(data, bytes) and len(data) > 0

@pytest.mark.parametrize("stem", sorted(PAYLOADS))
def test_build_is_deterministic(stem):
    mod = _load(stem)
    assert mod.build() == mod.build()

@pytest.mark.parametrize("stem", sorted(PAYLOADS))
def test_structural_invariants(stem):
    spec, data = PAYLOADS[stem], _load(stem).build()
    if spec.get("magic"):
        assert data.startswith(spec["magic"])
    for needle in spec.get("contains", []):
        assert needle in data, f"{stem}: missing {needle!r}"
    if spec.get("tail"):
        assert data.endswith(spec["tail"])
    if spec.get("exact_len"):
        assert len(data) == spec["exact_len"]

def test_drivers_have_no_build_or_are_importable():
    for stem in DRIVERS:
        mod = _load(stem)
        assert hasattr(mod, "main")

def test_manifest_matches_dist_if_present():
    mj = ROOT / "dist" / "manifest.json"
    if not mj.exists():
        pytest.skip("no dist/manifest.json")
    manifest = json.loads(mj.read_text())
    for e in manifest["artifacts"]:
        p = ROOT / "dist" / e["file"]
        assert p.exists(), f"missing {e['file']}"
        assert hashlib.sha256(p.read_bytes()).hexdigest() == e["sha256"], f"hash drift {e['file']}"

def test_manifest_has_no_error_entries():
    mj = ROOT / "dist" / "manifest.json"
    if not mj.exists():
        pytest.skip("no dist/manifest.json")
    manifest = json.loads(mj.read_text())
    errors = [e for e in manifest["non_payload"] if e["status"].endswith("error")]
    assert not errors, f"build/load errors: {errors}"
