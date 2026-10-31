#!/usr/bin/env python3
"""Cloud Deploy Wizard — real AWS/GCP/Azure deploy prompts; no external dependency required to configure."""
from __future__ import annotations
import sys, os, json, tempfile, subprocess

def prompt(label, default=""):
    try:
        return input(f"[{label}] ({default}): ").strip() or default
    except Exception:
        return default

def main():
    print("=== QUANTUM CLI — Cloud Deploy Wizard (Authorized Only) ===")
    provider = prompt("Provider", "aws")
    region = prompt("Region", "us-east-1")
    key_id = prompt("Access Key ID (env/secret, not stored)", "")
    key_secret = prompt("Secret Key (env/secret, not stored)", "")
    deploy_target = prompt("Target", "ecs/docker")
    config = {"provider": provider, "region": region, "target": deploy_target,
              "key_id_env": "QCLI_KEY_ID", "key_secret_env": "QCLI_KEY_SECRET"}
    out = "packaging/cloud_deploy_config.json"
    with open(out, "w") as f:
        json.dump(config, f, indent=2)
    print(f"[OK] Config written to {out} (keys referenced by env, never saved)")
    # Verify env presence (no network call; local check only)
    missing = [k for k in ["QCLI_KEY_ID", "QCLI_KEY_SECRET"] if not os.environ.get(k)]
    if missing:
        print(f"[WARN] Missing env vars: {missing} — set before deploy")
    else:
        print("[OK] Env keys present — ready for auth")

if __name__ == "__main__":
    main()
