#!/usr/bin/env python3
"""Comprehensive Feature Inventory — walks source tree, counts modules/pages/routes."""
from __future__ import annotations
import os, json

def inventory():
    counts = {"modules": 0, "lanes_files": 0, "pages": 0, "routes": 0}
    lanes = []
    lanef = os.path.join("src/quantum", "rat", "modules", "lanes")
    pages_dir = os.path.join("src/quantum", "web", "static", "pages")
    routes_dir = os.path.join("src/quantum", "web", "api")
    for root, _dirs, files in os.walk(lanef):
        counts["lanes_files"] += 1
        counts["modules"] += len(files)
        lanes.append(os.path.basename(root))
    for p in [lanef, pages_dir, routes_dir]:
        if not os.path.isdir(p): continue
        counts["pages"] += sum(1 for f in os.listdir(p) if f.endswith(".js")) + len([f for f in os.listdir(p) if f.endswith(".tsx")])
        counts["routes"] += 1
    return counts, lanes

def main():
    c, lanes = inventory()
    print(f"Feature inventory: {c['modules']} modules across {len(lanes)} lanes ({', '.join(lanes)})")
    print(f"Pages: {c['pages']}, Routes: {c['routes']}")
    with open("packaging/features-inventory.json", "w") as f:
        json.dump({"count": c, "lanes": lanes}, f, indent=2)
    print("[OK] Saved to packaging/features-inventory.json")

if __name__ == "__main__":
    main()
