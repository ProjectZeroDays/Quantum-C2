"""quantum.weapons.registry — ZERO_DAY_REGISTRY + fire contract + orchestrator."""
from __future__ import annotations

import json
import subprocess

from quantum.core.logging import log

# ----------------------------------------------------------------------------
# ZERO_DAY_REGISTRY — weapon entries reference callables BY NAME; resolution
# happens at fire-time via resolve_weapon() so tiers stay lazy-importable.
# ----------------------------------------------------------------------------

ZERO_DAY_REGISTRY = {
    # ---- legacy ----
    "CVE-2020-1472": {"name": "Zerologon", "tier": "legacy", "weapon": "check_zerologon"},
    "CVE-2017-0144": {"name": "EternalBlue", "tier": "legacy", "weapon": "check_ms17010"},
    "CVE-2021-1675": {"name": "PrintNightmare", "tier": "legacy", "weapon": "check_printnightmare"},
    "CVE-2021-36942": {"name": "PetitPotam", "tier": "legacy", "weapon": "check_petitpotam"},
    "CVE-2022-30190": {"name": "Follina MSDT", "tier": "legacy", "weapon": "check_follina"},
    "CVE-2021-26855": {"name": "ProxyLogon", "tier": "legacy", "weapon": "check_proxylogon"},
    # ---- V3_HIGH ----
    "CVE-2021-44228": {"name": "Log4Shell", "tier": "V3_HIGH", "weapon": "v3_log4shell"},
    "CVE-2024-3400": {"name": "PAN-OS GlobalProtect", "tier": "V3_HIGH", "weapon": "v3_panos_cmd"},
    "CVE-2023-4966": {"name": "Citrix Bleed", "tier": "V3_HIGH", "weapon": "v3_citrixbleed"},
    "CVE-2019-19781": {"name": "Citrix Path Traversal", "tier": "V3_HIGH", "weapon": "v3_citrix_path"},
    "CVE-2023-20198": {"name": "IOS XE Web UI", "tier": "V3_HIGH", "weapon": "v3_ios_admin"},
    "CVE-2022-26134": {"name": "Confluence OGNL", "tier": "V3_HIGH", "weapon": "v3_confluence_ognl"},
    "CVE-2020-14882": {"name": "WebLogic Console", "tier": "V3_HIGH", "weapon": "v3_weblogic_console"},
    "CVE-2021-40444": {"name": "MSHTML Maldoc", "tier": "V3_HIGH", "weapon": "v3_mshtml_maldoc"},
    # ---- V3_MED ----
    "CVE-2017-7494": {"name": "SambaCry", "tier": "V3_MED", "weapon": "v3_sambacry"},
    "CVE-2021-21972": {"name": "vCenter Upload", "tier": "V3_MED", "weapon": "v3_vcenter_upload"},
    "CVE-2022-0847": {"name": "Dirty Pipe", "tier": "V3_HIGH", "weapon": "v3_dirtypipe"},
    "CVE-2016-5195": {"name": "Dirty COW", "tier": "V3_MED", "weapon": "v3_dirtypipe"},
    # ---- V3_CHECK ----
    "CVE-2023-34362": {"name": "MOVEit SQLi", "tier": "V3_CHECK", "weapon": "v3_moveit_probe"},
    "CVE-2021-3156": {"name": "Baron Samedit", "tier": "V3_CHECK", "weapon": "check_baron_samedit"},
    "CVE-2021-4034": {"name": "PwnKit", "tier": "V3_CHECK", "weapon": "check_pwnkit"},
    "CVE-2023-2640": {"name": "Overlayfs GameOver", "tier": "V3_CHECK", "weapon": "check_overlayfs"},
    "CVE-2023-32233": {"name": "nf_tables UAF", "tier": "V3_CHECK", "weapon": "check_nftables_uaf"},
    "CVE-2024-1086": {"name": "nf_tables dbl-free", "tier": "V3_CHECK", "weapon": "check_nftables_dblfree"},
    "CVE-2019-3568": {"name": "WhatsApp VOIP", "tier": "V3_CHECK", "weapon": "check_whatsapp_voip"},
    "CVE-2023-4863": {"name": "libwebp BLASTPAST", "tier": "V3_CHECK", "weapon": "check_libwebp"},
    "CVE-2023-41064": {"name": "Apple ImageIO", "tier": "V3_CHECK", "weapon": "check_apple_imageio"},
    "CVE-2021-30858": {"name": "WebKit Escape", "tier": "V3_CHECK", "weapon": "check_webkit_escape"},
    "CVE-2022-21894": {"name": "BootHole", "tier": "V3_CHECK", "weapon": "check_boothole"},
    # ---- bluetooth (BlueBorne family + BlackBED-class BLE) ----
    "CVE-2017-0781": {"name": "BlueBorne BNEP", "tier": "V3_CHECK", "weapon": "check_blueborne_bnep"},
    "CVE-2017-0785": {"name": "BlueBorne SDP", "tier": "V3_CHECK", "weapon": "check_blueborne_sdp"},
    "CVE-2018-5383": {"name": "Bluetooth KNOB", "tier": "V3_CHECK", "weapon": "check_knob"},
    "BLACKBED-BLE": {"name": "BlackBED BLE", "tier": "V3_CHECK", "weapon": "check_blackbed"},
    "CVE-2020-0022": {"name": "BlueFrag L2CAP", "tier": "V3_CHECK", "weapon": "check_bluefrag"},
    "CVE-2017-13077": {"name": "KRACK WPA2", "tier": "V3_CHECK", "weapon": "check_krack"},
    # ---- adb (adbd TLS auth bypass) ----
    "CVE-2026-0073": {"name": "adbd TLS Auth Bypass", "tier": "V3_CHECK", "weapon": "check_adb_tls_bypass"},
}


def resolve_weapon(name):
    """Resolve a weapon name (string) to its callable, tier by tier."""
    import quantum.weapons.kernel_v3 as _k
    import quantum.weapons.legacy as _l
    import quantum.weapons.media_v3 as _m
    import quantum.weapons.remote_v3 as _r
    import quantum.weapons.bluetooth as _b
    import quantum.weapons.adb as _a
    for mod in (_r, _k, _m, _l, _b, _a):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    return None


class _Registry:
    """registry.fire(cve, ip, params) — every weapon string in
    ZERO_DAY_REGISTRY resolves to a callable; never raises."""

    def __contains__(self, cve):
        return cve in ZERO_DAY_REGISTRY

    def __iter__(self):
        return iter(ZERO_DAY_REGISTRY)

    def cves(self):
        return list(ZERO_DAY_REGISTRY)

    def fire(self, cve, ip, params=None):
        entry = ZERO_DAY_REGISTRY.get(cve)
        if not entry:
            raise KeyError(f"unknown CVE: {cve}")
        fn = resolve_weapon(entry["weapon"])
        if not callable(fn):
            return {"cve": cve, "status": "error",
                    "error": f"weapon {entry['weapon']!r} unresolved"}
        try:
            res = fn(ip, params)
        except Exception as exc:
            return {"cve": cve, "status": "error", "error": str(exc)}
        if isinstance(res, dict):
            return res
        return {"cve": cve, "status": "ok", "result": res}


registry = _Registry()


class ExploitOrchestrator:
    """V3 registry-aware fire stage + appliance-aware auto-exploit."""

    def __init__(self):
        from quantum.ai.supervisor import AI_Supervisor
        self.ai = AI_Supervisor()

    def source_exploits(self, keyword):
        found = []
        try:
            try:
                out = subprocess.check_output(["searchsploit", keyword], text=True, timeout=30)
                found += [{"src": "exploit-db", "match": l} for l in out.splitlines() if keyword in l]
            except FileNotFoundError:
                from quantum.core.opsec import OPSEC
                r = OPSEC.web("https://api.github.com/search/repositories",
                              params={"q": f"{keyword} exploit"}, timeout=10)
                found += [{"src": "github", "match": i["full_name"]} for i in r.json().get("items", [])[:10]]
        except Exception as e:
            log(f"exploit-db search: {e}", "WARN")
        return found

    def fire(self, cve, ip, params=None):
        if cve not in ZERO_DAY_REGISTRY:
            log(f"fire: '{cve}' not in registry", "WARN"); return {"error": cve}
        rec = ZERO_DAY_REGISTRY[cve]
        fn = resolve_weapon(rec["weapon"])
        if not callable(fn):
            return {"cve": cve, "status": "error", "error": f"weapon {rec['weapon']!r} unresolved"}
        return fn(ip, params)

    def auto_exploit(self, ip, params=None, force=False):
        from quantum.recon.fingerprint import Validator
        from quantum.recon.scan import ReconModule
        fp = ReconModule().fingerprint(ip)
        verdict = Validator().score(ip, fp)
        if verdict["decision"] != "high_value" and not force:
            log(f"auto_exploit skipped {ip} (VALIDATOR: {verdict['score']})", "ATK")
            return {"skipped": ip, "validator": verdict}
        cve = self.ai.plan_attack(fp)   # returns a bare CVE id (AI or QBrain)
        if cve in ZERO_DAY_REGISTRY:
            r = self.fire(cve, ip, params)
            log(f"auto_exploit: {ip} -> {cve} ({ZERO_DAY_REGISTRY[cve]['name']})", "ATK")
            return r
        # registry march fallback (deterministic)
        for cve, ent in ZERO_DAY_REGISTRY.items():
            probe = {"CVE-2017-0144": fp.get("ms17_010") is True,
                     "CVE-2020-1472": any(p in fp.get("ports", []) for p in (445, 135, 3389)),
                     "CVE-2021-44228": any(p in fp.get("ports", []) for p in (80, 443, 8080, 8000, 8443)),
                     "CVE-2021-26855": any(p in fp.get("ports", []) for p in (80, 443))}.get(cve, False)
            if probe:
                log(f"auto_exploit: no dedicated match for '{cve}' — registry march fires {cve}", "ATK")
                return self.fire(cve, ip, params)
        return {"error": "no match in registry"}
