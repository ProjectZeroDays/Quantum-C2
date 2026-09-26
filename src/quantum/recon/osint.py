"""quantum.recon.osint — domain OSINT (DoH + RDAP)."""
from __future__ import annotations

from datetime import datetime

from quantum.core.deps import requests
from quantum.recon.doh import DoH


def osint_lookup(domain):
    out = {"domain": domain, "created": datetime.now().isoformat()}
    try:
        out["addrs"] = [a.get("data") for a in DoH().resolve(domain, "A")]
    except Exception as exc:
        out["addrs_error"] = str(exc)
    try:
        from quantum.core.opsec import OPSEC
        r = OPSEC.web("https://rdap.org/domain/" + requests.utils.quote(domain))
        out["rdap"] = r.json()
    except Exception as exc:
        out["rdap_error"] = str(exc)
    return out
