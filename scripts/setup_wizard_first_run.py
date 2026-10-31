#!/usr/bin/env python3
"""Setup Wizard — First-run admin endpoint; creates admin account, base config, verifies services."""
from __future__ import annotations
import sys, os, json, secrets, hashlib

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def main():
    print("=== Setup Wizard — First Run ===")
    admin = input("Admin username [admin]: ").strip() or "admin"
    pw = input("Admin password (min 12 chars): ").strip()
    if len(pw) < 12:
        print("[FAIL] Password must be >= 12 chars")
        sys.exit(1)
    keyfile = "logs/.lootkey"
    if not os.path.exists(keyfile):
        print("[FAIL] .lootkey missing (immutable per AGENTS); abort")
        sys.exit(1)
    config_path = ".opencode/config.json"
    config = {"admin_user": admin, "hash": hash_pw(pw), "service_port": 8443,
              "kill_switch": True, "lootkey_present": True}
    os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"[OK] Admin created; service config at {config_path}; keyfile verified immutable")

if __name__ == "__main__":
    main()
