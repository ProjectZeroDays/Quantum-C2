"""quantum.weapons.adb — ADB-tier weapons (adbd TLS auth bypass).

CVE-2026-0073: adbd_tls_verify_cert() uses EVP_PKEY_cmp() as a
boolean; an EC/Ed25519 client cert against a stored RSA key returns -1
(truthy) → authorized. Remote probe: TCP to the adbd port, cleartext
CNXN, look for the STLS upgrade offer that gates the vulnerable TLS
path. Same never-raise fire contract as the other tiers.
"""
from __future__ import annotations

import socket
import struct

ADB_VERSION = 0x01000001
ADB_MAXDATA = 256 * 1024
ADB_BANNER = (b"host::features=shell_v2,cmd,stat_v2,ls_v2,fixed_push_mkdir,"
             b"apex,abb,fixed_push_symlink_timestamp,abb_exec,remount_shell,"
             b"track_app,sendrecv_v2,sendrecv_v2_brotli,sendrecv_v2_lz4,"
             b"sendrecv_v2_zstd,sendrecv_v2_dry_run_send,openscreen_mdns,"
             b"delayed_ack")

CMD_CNXN = 0x4E584E43
CMD_STLS = 0x534C5453
CMD_AUTH = 0x41555448


def _pack_packet(cmd, arg0, arg1, data=b""):
    csum = sum(data) & 0xFFFFFFFF
    return struct.pack("<IIIIII", cmd, arg0, arg1, len(data), csum,
                       cmd ^ 0xFFFFFFFF) + data


def _recv_packet(sock):
    header = b""
    while len(header) < 24:
        chunk = sock.recv(24 - len(header))
        if not chunk:
            raise ConnectionError("adbd closed the connection")
        header += chunk
    cmd, _, _, length, _, _ = struct.unpack("<IIIIII", header)
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            break
        data += chunk
    return cmd, data


def check_adb_tls_bypass(ip, params=None):
    """CVE-2026-0073 — adbd TLS auth-bypass surface (CNXN → STLS offer)."""
    params = params or {}
    port = params.get("adb_port", 5555)
    result = {"cve": "CVE-2026-0073", "status": "check",
              "vector": "adb/stls-ec-cert", "adb_port": port,
              "hint": "wireless debugging / ADB-over-TCP with a stored RSA "
                      "key; exploit via EC-cert TLS 1.3 (see "
                      "exploit_payloads/CVE-2026-0073-adb-tls-bypass)"}
    if not ip:
        return result
    try:
        with socket.create_connection((ip, port), timeout=params.get(
                "timeout", 4)) as s:
            s.settimeout(params.get("timeout", 4))
            s.sendall(_pack_packet(CMD_CNXN, ADB_VERSION, ADB_MAXDATA,
                                  ADB_BANNER))
            cmd, data = _recv_packet(s)
        result["adbd_banner"] = data.decode("utf-8", "replace")[:80]
        if cmd == CMD_STLS:
            result["stls"] = True
            result["status"] = "vulnerable-surface"
            result["verified_by"] = ("adbd offered STLS (TLS upgrade) — "
                                     "the CVE-2026-0073 path is reachable; "
                                     "fire the full chain from the payload "
                                     "folder for shell")
        elif cmd == CMD_AUTH:
            result["stls"] = False
            result["status"] = "check"
            result["verified_by"] = ("adbd answered AUTH (classic pairing "
                                     "path, not the TLS-bypass path)")
        else:
            result["stls"] = False
            result["verified_by"] = "adbd answered 0x%08x" % cmd
    except OSError as exc:
        result["status"] = "no-service"
        result["error"] = str(exc)
    return result
