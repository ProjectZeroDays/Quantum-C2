#!/usr/bin/env python3
"""Update Check — auto-checks releases; downloads assets locally (authorized, no external call unless configured)."""
from __future__ import annotations
import os, json

def main():
    manifest = "release/manifest.json"
    version = "4.6.5"
    if os.path.exists(manifest):
        with open(manifest) as f:
            data = json.load(f)
        version = data.get("version", version)
    print(f"[UPDATE] Current: {version}; check release/manifest.json or remote URL for updates")
    # No external fetch by default (authorized offline safety); only local comparison

if __name__ == "__main__":
    main()
