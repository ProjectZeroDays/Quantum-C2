"""quantum.core.jurgen — QBrain, the deterministic decision brain (no AI)."""
from __future__ import annotations

import json


class QBrain:
    """Deterministic decision/CVE brain. The --no-ai path runs ONLY this."""

    PORT_CVES = {
        445: ["CVE-2020-1472", "CVE-2017-0144"],
        139: ["CVE-2017-0144"],
        3389: ["CVE-2017-0144"],
        8080: ["CVE-2021-44228"],
        443: ["CVE-2021-26855"],
        7001: ["CVE-2020-14882"],
    }
    SERVICE_CVES = {
        "smb": ["CVE-2020-1472", "CVE-2017-0144"],
        "rtsp": ["CVE-2017-7921", "CVE-2021-33044"],
        "ssh": ["CVE-2016-5195"],
        "exchange": ["CVE-2021-26855"],
        "weblogic": ["CVE-2020-14882"],
        "citrix": ["CVE-2023-4966"],
        "panos": ["CVE-2024-3400"],
        "vmware": ["CVE-2021-21972"],
        "confluence": ["CVE-2022-26134"],
    }

    @staticmethod
    def decide(state, acts, camera_only=False):
        """Pick the next autonomous action from the whitelist, deterministically."""
        cams = state.get("cams", [])
        fired = state.get("fired", [])
        if cams and any(c.get("controlled") for c in cams):
            pick = "cam_control"
        elif not cams:
            pick = "cam_war" if "cam_war" in acts else "cam_discover"
        elif fired and "harvest" in acts:
            pick = "harvest"
        elif "exploit" in acts and state.get("targets"):
            pick = "exploit"
        elif "brute" in acts and cams:
            pick = "brute"
        else:
            pick = "rest" if "rest" in acts else acts[-1]
        if pick not in acts:
            pick = acts[0] if acts else "rest"
        target = ""
        if pick == "exploit" and fired:
            target = fired[-1]
        return {"action": pick, "target": target,
                "reason": f"QBrain deterministic: state has {len(cams)} cams, "
                          f"{len(fired)} fired"}

    @classmethod
    def plan_attack(cls, recon):
        """recon dict -> a registry CVE string (deterministic)."""
        from quantum.weapons.registry import ZERO_DAY_REGISTRY
        cands = []
        for key, cves in cls.SERVICE_CVES.items():
            if recon.get(key):
                cands.extend(cves)
        for port in recon.get("ports", []):
            cands.extend(cls.PORT_CVES.get(int(port), []))
        for cve in cands:
            if cve in ZERO_DAY_REGISTRY:
                return cve
        for cve in ZERO_DAY_REGISTRY:
            return cve
        return "CVE-2021-44228"

    @staticmethod
    def phish_body(email, subject="Payroll"):
        return (f"Hi,\n\nPlease review the updated {subject} document for your "
                f"account ({email}). Open the attachment to confirm your details "
                f"before Friday.\n\nRegards,\nPayroll Team")

    @staticmethod
    def summary(params):
        return f"QBrain summary: {json.dumps(params, default=str)[:300]}"
