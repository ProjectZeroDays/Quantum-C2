"""quantum.recon.fingerprint — target fingerprinting + pre-fire validator."""
from __future__ import annotations

from quantum.camwar.vendors import vendor_from_str
from quantum.core.deps import requests
from quantum.core.opsec import tcp_probe


class Validator:
    """Pre-fire risk scoring (cameras + appliances win)."""

    CAM_PORTS = {554, 37777, 37778, 8000, 8001, 8081, 8899, 34567, 34571, 34599}
    APPLIANCE_HINTS = ("citrix", "pan-os", "panos", "vmware", "vcenter",
                      "weblogic", "confluence", "cisco ios", "moveit")

    def score(self, ip, fp):
        s = 10
        ports = set(fp.get("ports", []) or [])
        if ports & self.CAM_PORTS or fp.get("camera"):
            s += 50
        if fp.get("vendor"):
            s += 40
        import json
        hay = json.dumps(fp, default=str).lower()
        if any(h in hay for h in self.APPLIANCE_HINTS):
            s += 40
        if fp.get("ms17_010") is True:
            s += 30
        s += min(len(ports), 10)
        decision = "high_value" if s >= 60 else "low_value"
        return {"score": s, "decision": decision, "ip": ip}


def fingerprint(ip, common_ports=None):
    """Fingerprint a host: ports + banners + camera hints."""
    common = common_ports or [21, 22, 23, 80, 443, 445, 554, 1433, 3389,
                              7001, 8000, 8080, 8443, 8899]
    fp = {"ip": ip, "ports": [], "banners": {}, "smb": {}, "camera": False,
          "vendor": None, "ms17_010": None}
    fp["ports"] = [p for p in common if tcp_probe(ip, p, timeout=0.5)]
    for port in fp["ports"]:
        if port in (80, 443, 7001, 8000, 8080, 8443):
            try:
                scheme = "https" if port in (443, 8443) else "http"
                r = requests.get(f"{scheme}://{ip}:{port}/", timeout=3, verify=False)
                hay = (r.text or "")[:2000] + " " + r.headers.get("Server", "") \
                      + " " + r.headers.get("WWW-Authenticate", "")
                fp["banners"][port] = hay[:200]
            except Exception:
                continue
    if 445 in fp["ports"] or 139 in fp["ports"]:
        fp["smb"] = {"open": True}
    for port, banner in fp["banners"].items():
        v = vendor_from_str(banner)
        if v != "unknown":
            fp["vendor"] = v
            fp["camera"] = True
            break
    if 554 in fp["ports"]:
        fp["camera"] = True
    return fp


VALIDATOR = Validator()
