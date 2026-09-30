"""quantum.ops.tools — external tool catalog.

Catalogs the operator tools vendored/referenced by Quantum C2
(ADDED/) plus standard red-team toolkit binaries, detects which are
installed on this machine, and records how to invoke each one.

Honesty: catalog entries describe tools; `detect()` reports
availability; nothing is executed by this module. JSON-safe.
"""
from __future__ import annotations

import os
import shutil

# name -> {kind, description, how (invocation hint), check (binary
# or file used to detect presence), source}
TOOLS = {
    "nikto": {
        "kind": "scanner",
        "description": "Web server scanner (plugins for 6700+ potential "
                       "issues).",
        "how": "perl nikto.pl -h <target>  (or docker run sullo/nikto)",
        "check": "nikto",
        "source": "github.com/sullo/nikto (Quantum C2 ADDED/nikto)"},
    "gitleaks": {
        "kind": "secret-scanner",
        "description": "SAST for git repos: finds committed secrets.",
        "how": "gitleaks detect --source <repo> --report <out.json>",
        "check": "gitleaks",
        "source": "github.com/gitleaks/gitleaks (Quantum C2 ADDED/gitleaks)"},
    "gitdorker": {
        "kind": "osint",
        "description": "GitHub dork enumeration using a dorks list "
                       "(needs GH token).",
        "how": "python3 GitDorker.py -tf tokens.txt -q <org> -d dorks.txt "
               "(or use quantum.recon.gitdork)",
        "check": "GitDorker.py",
        "source": "github.com/obheda12/GitDorker (Quantum C2 ADDED/gitdorker)"},
    "dnscrypt": {
        "kind": "tunnel",
        "description": "DNSCrypt proxy/resolver client — DNS secrecy "
                       "for C2 channels.",
        "how": "dnscrypt-proxy -config <toml>",
        "check": "dnscrypt-proxy",
        "source": "github.com/DNSCrypt/dnscrypt-proxy "
                 "(Quantum C2 ADDED/dnscrypt)"},
    "udp2raw": {
        "kind": "tunnel",
        "description": "UDP-over-raw-socket tunnel (traffic obfuscation, "
                       "anti-QoS).",
        "how": "udp2raw -s -l0.0.0.0:4096 -r127.0.0.1:22 ...",
        "check": "udp2raw",
        "source": "github.com/wangyu-/udp2raw "
                  "(Quantum C2 ADDED/udp2raw_tunnel)"},
    "whid_hid": {
        "kind": "hid",
        "description": "WHID Elite (WiFi HID injector) payloads and "
                       "pinouts — USB HID attack hardware.",
        "how": "flash WHID Elite over USB/OTA, serve payloads via "
               "whid-elite web UI",
        "check": None,
        "source": "github.com/whid-injector/WHID (Quantum C2 ADDED/whid_hid)"},
    "changemac": {
        "kind": "opsec",
        "description": "Change MAC Address (Windows tool) — interface "
                       "MAC randomization for OPSEC.",
        "how": "Change MAC Address 24.06.exe (GUI) or use quantum's "
               "macreset technique",
        "check": None,
        "source": "Technitium (Quantum C2 ADDED/change_mac_address)"},
    "adb": {
        "kind": "mobile",
        "description": "Android Debug Bridge — drives lockknife/"
                       "quantum_android device work.",
        "how": "adb devices; adb -s <serial> shell ...",
        "check": "adb",
        "source": "Android platform-tools"},
    "apksigner": {
        "kind": "mobile",
        "description": "APK signing/verification ground truth for the "
                       "Necro-class APK wrapper.",
        "how": "apksigner verify --print-certs <apk>",
        "check": "apksigner",
        "source": "Android build-tools"},
    "nmap": {
        "kind": "scanner",
        "description": "Network discovery/port scan baseline.",
        "how": "nmap -sV -p- <target>",
        "check": "nmap",
        "source": "nmap.org"},
}


def detect(name) -> dict:
    """Is one cataloged tool present on this machine? (PATH lookup,
    or ADB_PATH override for adb.)"""
    try:
        entry = TOOLS.get(str(name).lower())
        if not entry:
            return {"ok": False, "tool": name,
                    "error": "unknown tool (see list_tools())"}
        check = entry.get("check")
        found = None
        if check:
            if name == "adb" and os.environ.get("ADB_PATH"):
                found = os.environ["ADB_PATH"] if os.path.isfile(
                    os.environ["ADB_PATH"]) else None
            if not found:
                found = shutil.which(check)
            if not found:
                # also look beside the repo (common for checked-in tools)
                here = os.path.join(os.path.dirname(os.path.abspath(
                    __file__)), name)
                found = here if os.path.isfile(here) else None
        return {"ok": True, "tool": name, "kind": entry["kind"],
                "installed": bool(found), "path": found,
                "description": entry["description"],
                "how": entry["how"], "source": entry["source"]}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def detect_all() -> dict:
    """Availability of every cataloged tool."""
    try:
        rows = {name: detect(name) for name in sorted(TOOLS)}
        return {"ok": True, "tools": len(TOOLS),
                "installed": [n for n, r in rows.items() if r["installed"]],
                "detail": rows}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def list_tools(kind=None) -> dict:
    """Catalog listing (optionally by kind)."""
    try:
        rows = [{"name": n, "kind": e["kind"],
                 "description": e["description"], "how": e["how"],
                 "source": e["source"]}
                for n, e in sorted(TOOLS.items())
                if not kind or e["kind"] == kind]
        return {"ok": True, "tools": rows}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
