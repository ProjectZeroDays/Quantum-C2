#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tier1_gate.py — report whether any Tier-1 (high-confidence) exploit source
changed in a diff. CI uses this to run a strict gate only when it matters,
so Tier-2 churn never blocks a build.

  python3 tier1_gate.py --base origin/main --head HEAD
  python3 tier1_gate.py --base HEAD~1 --json
"""
import argparse, json, subprocess, sys

# high-confidence, public-PoC exploits — these must always compile
TIER1 = [
    "cve_2019_2215", "cve_2024_1086", "cve_2020_15999", "cve_2015_6602",
    "cve_2019_3568", "cve_2019_11931", "cve_2019_8641",
    "cve_2020_6418", "cve_2020_16040", "cve_2021_21224", "cve_2020_0674",
]


def changed_files(base, head):
    r = subprocess.run(["git", "diff", "--name-only", f"{base}...{head}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        r = subprocess.run(["git", "diff", "--name-only", base, head],
                           capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l]


def main() -> int:
    ap = argparse.ArgumentParser(prog="tier1_gate")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-if-changed", action="store_true")
    a = ap.parse_args()

    changed = changed_files(a.base, a.head)
    tier1 = sorted({f for f in changed for t in TIER1 if t in f})

    if a.json:
        print(json.dumps({"tier1_changed": tier1, "count": len(tier1)}))
    else:
        for f in tier1:
            print(f"tier1: {f}")
        print(f"[+] {len(tier1)} tier-1 file(s) changed")

    if a.fail_if_changed and tier1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
