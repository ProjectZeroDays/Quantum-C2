#!/usr/bin/env python3
"""Setup Init Router — first-run admin endpoint; routes to wizard/service/bootstrap."""
from __future__ import annotations
import sys, os, json

def check_first_run():
    return not os.path.exists(".opencode/config.json")

def init():
    print("=== Setup Init Router ===")
    if check_first_run():
        print("First run detected — run 'python scripts/setup_wizard_first_run.py' first")
        sys.exit(1)
    print("[OK] Config present; service can start")

if __name__ == "__main__":
    init()
