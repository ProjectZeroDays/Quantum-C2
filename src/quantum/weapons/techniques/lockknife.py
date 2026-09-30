"""quantum.weapons.techniques.lockknife — Android device forensics.

Python port of the LockKnife (github.com/RyanDCarter/lockknife) core:
ADB device detection, state management, and the most-used forensic
extractions (device info, installed packages, settings, app data
listings, screenshots). The original is a bash framework driving
`adb`; this port drives the same adb surface from Python.

Honesty: this module needs a connected, authorized Android device (USB
or TCP/IP adb) — every extraction reports `ok: false` with a clean
error when no device/adb is present. JSON-safe, never raises.
"""
from __future__ import annotations

import os
import shutil
import subprocess

ADB_TIMEOUT = 30

DEVICE_STATES = {
    "device": "authorized",
    "offline": "offline",
    "unauthorized": "unauthorized",
    "recovery": "recovery",
    "sideload": "sideload",
    "no device": "disconnected",
}


def _adb_path():
    p = os.environ.get("ADB_PATH") or shutil.which("adb")
    return p


def _run_adb(args, serial=None, timeout=ADB_TIMEOUT):
    adb = _adb_path()
    if not adb:
        return None, "adb not found on PATH (set ADB_PATH)"
    cmd = [adb]
    if serial:
        cmd += ["-s", serial]
    cmd += args
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout)
        return proc, None
    except FileNotFoundError:
        return None, "adb executable missing"
    except subprocess.TimeoutExpired:
        return None, "adb timed out after %ss" % timeout
    except OSError as exc:
        return None, str(exc)


def _serials():
    proc, err = _run_adb(["devices"], timeout=10)
    if err:
        return [], err
    out = []
    for line in (proc.stdout or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            out.append({"serial": parts[0],
                        "state": DEVICE_STATES.get(parts[1], parts[1])})
    return out, None


def devices() -> dict:
    """List attached adb devices + states. JSON-safe, never raises."""
    try:
        found, err = _serials()
        if err:
            return {"ok": False, "error": err, "devices": []}
        return {"ok": True, "devices": found,
                "authorized": [d["serial"] for d in found
                              if d["state"] == "authorized"]}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc),
                "devices": []}


def connect(target: str, port: int = 5555) -> dict:
    """adb connect to a TCP/IP device (authorized-lab use only)."""
    try:
        proc, err = _run_adb(["connect", "%s:%d" % (target, port)],
                            timeout=15)
        if err:
            return {"ok": False, "error": err}
        text = (proc.stdout or "") + (proc.stderr or "")
        ok = "connected" in text or "already connected" in text
        return {"ok": ok, "target": "%s:%d" % (target, port),
                "output": text.strip()[:500]}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def device_info(serial=None) -> dict:
    """Key device properties (model, android version, API, security patch)."""
    try:
        found, err = _serials()
        if err:
            return {"ok": False, "error": err}
        if not found:
            return {"ok": False, "error": "no adb devices attached"}
        serial = serial or next(
            (d["serial"] for d in found if d["state"] == "authorized"),
            None)
        if not serial:
            return {"ok": False, "error": "no authorized device",
                    "devices": found}
        props = {}
        for prop in ("ro.product.model", "ro.product.brand",
                     "ro.build.version.release",
                     "ro.build.version.sdk",
                     "ro.build.version.security_patch",
                     "ro.build.fingerprint", "ro.hardware",
                     "ro.product.cpu.abi"):
            proc, err = _run_adb(["-s", serial, "shell",
                                  "getprop", prop], timeout=10)
            if not err and proc.returncode == 0:
                props[prop] = (proc.stdout or "").strip()
        state = next((d["state"] for d in found
                     if d["serial"] == serial), None)
        return {"ok": True, "serial": serial, "state": state,
                "model": props.get("ro.product.model"),
                "brand": props.get("ro.product.brand"),
                "android_version": props.get("ro.build.version.release"),
                "api_level": props.get("ro.build.version.sdk"),
                "security_patch": props.get(
                    "ro.build.version.security_patch"),
                "fingerprint": props.get("ro.build.fingerprint"),
                "abi": props.get("ro.product.cpu.abi")}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def extract_packages(serial=None, third_party_only=True) -> dict:
    """Installed package list (third-party by default)."""
    try:
        args = ["shell", "pm", "list", "packages"]
        if third_party_only:
            args.append("-3")
        proc, err = _run_adb(args, serial=serial)
        if err:
            return {"ok": False, "error": err}
        if proc.returncode != 0 and not (proc.stdout or "").strip():
            return {"ok": False,
                    "error": (proc.stderr or "adb error").strip()[:300]}
        pkgs = sorted(
            l.replace("package:", "").strip()
            for l in (proc.stdout or "").splitlines()
            if l.startswith("package:"))
        return {"ok": True, "count": len(pkgs), "packages": pkgs[:2000],
                "truncated": len(pkgs) > 2000}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def extract_settings(serial=None) -> dict:
    """`settings get` for the common forensic namespaces."""
    try:
        out = {}
        failed = None
        for ns in ("secure", "global", "system"):
            proc, err = _run_adb(
                ["shell", "settings", "list", ns], serial=serial, timeout=15)
            if err:
                failed = failed or err
                out[ns] = {}
            elif proc.returncode != 0 and not (proc.stdout or "").strip():
                failed = failed or (proc.stderr or "adb error").strip()[:300]
                out[ns] = {}
            else:
                out[ns] = dict(_parse_kv(proc.stdout or ""))
        if failed and not any(out.values()):
            return {"ok": False, "error": failed, "settings": out}
        return {"ok": True, "settings": out}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def _parse_kv(text):
    for line in text.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip()
            if k and not v.startswith("null"):
                yield k, v


def extract_app_data(serial=None, package=None) -> dict:
    """List /data/data/<package> (rooted devices) or a package's
    external files."""
    try:
        if package:
            proc, err = _run_adb(
                ["shell", "ls", "-la",
                 "/data/data/%s" % package], serial=serial, timeout=10)
            if err:
                return {"ok": False, "error": err}
            if proc.returncode != 0 or "Permission denied" in \
                    (proc.stdout or "") + (proc.stderr or ""):
                # fall back to external storage listing
                proc2, err2 = _run_adb(
                    ["shell", "ls", "-la",
                     "/sdcard/Android/data/%s" % package],
                    serial=serial, timeout=10)
                return {"ok": True, "package": package, "rooted": False,
                        "listing": (proc2.stdout or
                                   (proc.stderr or "")).strip()[:4000]}
            return {"ok": True, "package": package, "rooted": True,
                    "listing": (proc.stdout or "").strip()[:4000]}
        proc, err = _run_adb(["shell", "ls", "/data/data"],
                             serial=serial, timeout=10)
        if err:
            return {"ok": False, "error": err}
        apps = sorted(l.strip() for l in (proc.stdout or "").splitlines()
                      if l.strip())
        return {"ok": len(apps) > 0 and proc.returncode == 0,
                "error": None if (apps and proc.returncode == 0)
                else "no /data/data listing (device not rooted or no device)",
                "rooted": len(apps) > 0,
                "packages": apps[:2000],
                "listing": (proc.stdout or "").strip()[:2000]}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def screenshot(path, serial=None) -> dict:
    """Capture a device screenshot to `path` (screencap + pull)."""
    try:
        remote = "/sdcard/.lk_cap.png"
        proc, err = _run_adb(["shell", "screencap", "-p", remote],
                            serial=serial, timeout=20)
        if err:
            return {"ok": False, "error": err}
        proc, err = _run_adb(["pull", remote, path], serial=serial,
                             timeout=30)
        _run_adb(["shell", "rm", remote], serial=serial, timeout=10)
        if err:
            return {"ok": False, "error": err}
        ok = proc.returncode == 0 and os.path.isfile(path)
        return {"ok": ok, "path": path if ok else None,
                "bytes": os.path.getsize(path) if ok else 0}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def full_report(serial=None) -> dict:
    """Device info + packages + settings in one JSON-safe report."""
    try:
        info = device_info(serial=serial)
        report = {"ok": info.get("ok", False), "device": info,
                  "packages": extract_packages(serial=serial),
                  "settings": extract_settings(serial=serial)}
        if not report["ok"]:
            report["error"] = info.get("error") or "device report incomplete"
        return report
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
