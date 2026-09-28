#!/usr/bin/env python3
"""CVE-2023-2640 (OverlayFS lost uid/gid validation) - authorized-lab local privesc deploy.

Kernel-range gate (5.11-6.3, per the registry convention) plus local
staging: in a forked child inside a fresh user namespace the launcher
attempts a real overlayfs mount over lowerdir/upperdir/workdir staging
directories and a copy-up write through the merged view - the exact
filesystem configuration the GameOver(Lag) privilege-escalation chain
(CVE-2023-2640 + CVE-2023-32629) requires. Outside the range (or
non-Linux / userns unavailable) the launcher returns a clean check-only
result instead of staging.
"""
import argparse
import ctypes
import json
import os
import platform
import re
import shutil
import sys
import tempfile

CVE = "CVE-2023-2640"
LO, HI = (5, 11), (6, 3)
CLONE_NEWUSER = 0x10000000


def _kernel_release():
    m = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", platform.release())
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def _libc():
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        libc.unshare.argtypes = [ctypes.c_int]
        libc.unshare.restype = ctypes.c_int
        libc.mount.argtypes = [ctypes.c_char_p, ctypes.c_char_p,
                               ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p]
        libc.mount.restype = ctypes.c_int
        return libc
    except OSError:
        return None


def _read(path, default=""):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return default


def _write(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(data)


def _stage_child(libc, stage, report_fd):
    """Runs inside the forked child: userns + overlay mount + copy-up write."""
    report = {}
    try:
        if libc.unshare(CLONE_NEWUSER) != 0:
            report["error"] = "unshare(CLONE_NEWUSER) failed: errno %d" % ctypes.get_errno()
            os.write(report_fd, json.dumps(report).encode())
            os._exit(3)
        _write("/proc/self/setgroups", "deny")
        _write("/proc/self/uid_map", "0 %d 1\n" % os.getuid())
        _write("/proc/self/gid_map", "0 %d 1\n" % os.getgid())

        lower = os.path.join(stage, "lower")
        upper = os.path.join(stage, "upper")
        work = os.path.join(stage, "work")
        merged = os.path.join(stage, "merged")
        for d in (lower, upper, work, merged):
            os.makedirs(d, exist_ok=True)
        with open(os.path.join(lower, "lower_file"), "w") as fh:
            fh.write("lower-content")

        opts = ("lowerdir=%s,upperdir=%s,workdir=%s" % (lower, upper, work)).encode()
        if libc.mount(b"overlay", merged.encode(), b"overlay", 0, opts) != 0:
            report["error"] = "mount(overlay) failed: errno %d" % ctypes.get_errno()
            os.write(report_fd, json.dumps(report).encode())
            os._exit(4)
        report["overlay_mount"] = True

        merged_file = os.path.join(merged, "lower_file")
        with open(merged_file, "w") as fh:  # copy-up + write-through
            fh.write("copied-up")
        with open(merged_file, "r") as fh:
            if fh.read() != "copied-up":
                raise OSError("readback mismatch")
        report["copyup_write"] = True
        upper_copy = os.path.join(upper, "lower_file")
        report["upper_copyup_exists"] = os.path.isfile(upper_copy)
        report["ok"] = True
        os.write(report_fd, json.dumps(report).encode())
        os._exit(0)
    except Exception as exc:
        report["error"] = "%s: %s" % (type(exc).__name__, exc)
        try:
            os.write(report_fd, json.dumps(report).encode())
        except OSError:
            pass
        os._exit(5)


def run(args):
    maj, minr, patch = _kernel_release()
    linux = sys.platform.startswith("linux")
    result = {
        "cve": CVE,
        "target": "local",
        "vulnerable": False,
        "verified_by": None,
        "kernel": "%d.%d.%d" % (maj, minr, patch),
        "platform": sys.platform,
        "in_range": linux and LO <= (maj, minr) <= HI,
        "userns": False,
        "overlay_fs": "overlay" in _read("/proc/filesystems"),
        "overlay_mounts": [ln.split()[1] for ln in _read("/proc/mounts").splitlines()
                           if ln.split() and len(ln.split()) > 2 and ln.split()[2] == "overlay"],
        "staging": {},
        "error": None,
    }
    if not linux:
        result["error"] = "check-only: not Linux"
        return result
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        result["error"] = "already root (chain expects an unprivileged user)"
        result["vulnerable"] = None
        return result
    if not result["in_range"]:
        result["error"] = ("check-only: kernel %s outside the vulnerable 5.11-6.3 range"
                           % result["kernel"])
        return result
    libc = _libc()
    if libc is None:
        result["error"] = "check-only: libc.so.6 unavailable"
        return result
    if not result["overlay_fs"]:
        result["error"] = "check-only: overlay filesystem not supported by this kernel"
        return result
    if args.check_only:
        result["error"] = "check-only requested"
        return result

    stage = tempfile.mkdtemp(prefix="qcli_overlay_")
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        _stage_child(libc, stage, write_fd)
        os._exit(9)  # unreachable
    os.close(write_fd)
    chunks = b""
    try:
        while True:
            chunk = os.read(read_fd, 65536)
            if not chunk:
                break
            chunks += chunk
        _, status = os.waitpid(pid, 0)
        exitcode = os.waitstatus_to_exitcode(status)
    finally:
        os.close(read_fd)
        shutil.rmtree(stage, ignore_errors=True)

    staging = {}
    if chunks:
        try:
            staging = json.loads(chunks.decode("utf-8", "replace"))
        except ValueError:
            staging = {"raw": chunks.decode("utf-8", "replace")[:500]}
    staging["child_exit"] = exitcode
    result["staging"] = staging
    result["userns"] = "unshare" not in (staging.get("error") or "")

    if staging.get("ok"):
        result["vulnerable"] = True
        result["verified_by"] = ("vulnerable kernel range + unprivileged user namespace + "
                                 "working overlayfs copy-up staging (GameOver(Lag) chain "
                                 "preconditions all present)")
    elif not result["userns"]:
        result["error"] = "user namespaces unavailable: %s" % staging.get("error")
    else:
        result["error"] = "overlay staging failed: %s" % staging.get("error")
    return result


def main():
    p = argparse.ArgumentParser(description="CVE-2023-2640 OverlayFS authorized-lab deploy")
    p.add_argument("--check-only", action="store_true",
                   help="report kernel range/filesystem only; do not stage")
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
