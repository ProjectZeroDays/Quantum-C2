"""test_dist_parity — dist/quantum-cli-v3.1-single.py must stay in contract
with the src/ package it was flattened from. Guards the manual-sync drift that
bit us once (the Dirty Pipe byref fix was applied to src but initially not to
dist). If this test fails, dist/ is stale: regenerate or re-sync it."""
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import pytest

DIST = Path(__file__).resolve().parents[1] / "dist" / "quantum-cli-v3.1-single.py"

pytestmark = pytest.mark.skipif(
    not DIST.exists(), reason="dist single-file build not present")


def _load_dist():
    spec = importlib.util.spec_from_file_location("quantum_cli_dist_parity", DIST)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_dist_byref_fix_present():
    # the EFAULT bug fix (off_in must be ctypes.byref, not a value) is
    # textual: a naive re-flatten that drops it fails here
    src_text = DIST.read_text(encoding="utf-8")
    assert "libc.splice(fd, ctypes.byref(off), w, None, 1, SPLICE_F_MOVE)" in src_text


def test_dist_registry_parity():
    dist = _load_dist()
    assert len(dist.ZERO_DAY_REGISTRY) >= 25
    import quantum_cli as q
    # every CVE the launcher registry knows must exist in dist too
    missing = set(q.ZERO_DAY_REGISTRY) - set(dist.ZERO_DAY_REGISTRY)
    assert not missing, f"dist/ registry is stale, missing: {sorted(missing)}"


def test_dist_dirtypipe_contract_parity():
    dist = _load_dist()
    import quantum_cli as q
    # non-Linux: both must return the same linux-only check-only status
    if not sys.platform.startswith("linux"):
        a = dist.exploit_dirtypipe("/nonexistent", offset=0, data=b"x")
        b = q.exploit_dirtypipe("/nonexistent", offset=0, data=b"x")
        assert a.get("status") == b.get("status") == "linux-only"
        assert a.get("cve") == b.get("cve") == "CVE-2022-0847"
        return
    # Linux: run the real splice contract against dist's copy (mirrors
    # test_dirtypipe: vulnerable kernel MUST overwrite, patched must NOT)
    path = os.path.join(tempfile.gettempdir(), ".qcli_dp_dist_test")
    with open(path, "wb") as fh:
        fh.write(b"A" * 4096)
    try:
        payload = b"QUANTUM-DP-DIST\n"
        res = dist.exploit_dirtypipe(path, offset=16, data=payload)
        assert res.get("status") == "fired", res
        with open(path, "rb") as fh:
            fh.seek(16)
            got = fh.read(len(payload))
        if res.get("kernel_fixed"):
            assert res.get("verified") is False
            assert got == b"A" * len(payload), got
        else:
            assert res.get("verified") is True
            assert got == payload, got
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
