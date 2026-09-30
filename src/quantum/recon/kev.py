"""quantum.recon.kev — CISA KEV feed + zero-click analysis.

Ported from Quantum C2 `modules/intelligence/threat_intel.py` (Tier-1
module, approved for app integration). Fetches the CISA Known Exploited
Vulnerabilities catalog (24h cache in ~/.qcli/catalog/), and analyzes
entries for zero-click / pre-auth exploitation indicators.

Falls back to a small built-in sample set when offline and no cache —
`source` in the report says which. All public entry points are JSON-safe
and never raise.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

KEV_URL_PRIMARY = "https://www.cisa.gov/sites/default/files/cve/kev.json"
KEV_URL_BACKUP = ("https://www.cisa.gov/sites/default/files/2025-01/"
                  "kev_crowd-sourced-trends_2025-01-14.json")

ZERO_CLICK_INDICATORS = [
    "zero-click", "zero click", "zero-click exploit",
    "no user interaction", "no user action", "automatic exploitation",
    "crafted pdf", "crafted image", "crafted message", "crafted video",
    "crafted file", "crafted content",
]

PRE_AUTH_INDICATORS = [
    "pre-auth", "pre authentication", "unauthenticated",
    "remote code execution", "buffer overflow", "use after free",
    "heap overflow", "stack overflow",
]

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".qcli", "catalog")
CACHE_PATH = os.path.join(CACHE_DIR, "kev.json")
CACHE_TTL = timedelta(hours=24)

_engine = None


class ThreatIntelEngine:
    """CISA KEV fetch + zero-click / pre-auth indicator analysis."""

    def __init__(self, cache_dir: str | None = None):
        self.cache_dir = cache_dir or CACHE_DIR
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except OSError:
            pass
        self._kev_cache_path = os.path.join(self.cache_dir, "kev.json")
        self._cache_ttl = CACHE_TTL
        self.source = None       # "network" | "cache" | "sample"

    # ------------------------------------------------------------- cache
    def _cache_valid(self) -> bool:
        try:
            if not os.path.isfile(self._kev_cache_path):
                return False
            age = datetime.now() - datetime.fromtimestamp(
                os.path.getmtime(self._kev_cache_path))
            return age < self._cache_ttl
        except OSError:
            return False

    def _load_cache(self) -> list[dict[str, Any]]:
        try:
            with open(self._kev_cache_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list) and data:
                return data
        except (OSError, json.JSONDecodeError):
            pass
        return []

    def _save_cache(self, entries: list[dict[str, Any]]) -> None:
        try:
            with open(self._kev_cache_path, "w", encoding="utf-8") as fh:
                json.dump(entries, fh)
        except OSError:
            pass

    # ------------------------------------------------------------- fetch
    def fetch_kev(self) -> list[dict[str, Any]]:
        """Latest KEV entries: cache -> network -> cache-stale -> sample."""
        if self._cache_valid():
            cached = self._load_cache()
            if cached:
                self.source = "cache"
                return cached
        for url in (KEV_URL_PRIMARY, KEV_URL_BACKUP):
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "quantum-cli/4.4"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                entries = (data.get("vulnerabilities")
                           if isinstance(data, dict) else data) or []
                if isinstance(entries, list) and entries:
                    self._save_cache(entries)
                    self.source = "network"
                    return entries
            except (urllib.error.URLError, OSError, ValueError,
                    json.JSONDecodeError):
                continue
        stale = self._load_cache()
        if stale:
            self.source = "cache-stale"
            return stale
        self.source = "sample"
        return _sample_kev_entries()

    # ---------------------------------------------------------- analysis
    def analyze_zero_click(self, vulns):
        return _filter_indicators(vulns, ZERO_CLICK_INDICATORS, "zero_click")

    def analyze_pre_auth(self, vulns):
        return _filter_indicators(vulns, PRE_AUTH_INDICATORS, "pre_auth")

    def vendor_breakdown(self, vulns) -> dict[str, int]:
        out: dict[str, int] = {}
        for v in vulns:
            vendor = v.get("vendor", "Unknown") or "Unknown"
            out[vendor] = out.get(vendor, 0) + 1
        return out


def _filter_indicators(vulns, indicators, flag):
    out = []
    for v in vulns:
        text = " ".join(str(v.get(k, "")) for k in
                        ("notes", "short_description", "title",
                         "notes_field", "required_action")).lower()
        for ind in indicators:
            if ind.lower() in text:
                v = dict(v)
                v[flag] = True
                v[flag + "_indicator"] = ind
                out.append(v)
                break
    return out


def _sample_kev_entries() -> list[dict[str, Any]]:
    """Small built-in sample set (offline fallback; marked as such)."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [
        {"cveID": "CVE-2023-47138", "vendor": "Microsoft",
         "product": "Windows DHCP Server",
         "title": "Windows DHCP Server Remote Code Execution",
         "short_description": "Buffer overflow in DHCP service allows "
                               "remote code execution.",
         "date_added": "2023-10-10", "due_date": "2024-01-08",
         "exploit_public": "Yes",
         "notes": "Remote code execution via crafted DHCP request.",
         "cwes": ["CWE-121", "CWE-787"]},
        {"cveID": "CVE-2024-37041", "vendor": "Ivanti",
         "product": "Connect Secure",
         "title": "Ivanti Connect Secure Memory Corruption",
         "short_description": "Memory corruption allows remote code "
                              "execution without authentication.",
         "date_added": now, "due_date": now,
         "exploit_public": "Yes",
         "notes": "Zero-click exploitation without authentication.",
         "cwes": ["CWE-121", "CWE-787"]},
        {"cveID": "CVE-2023-34362", "vendor": "Progress Software",
         "product": "MOVEit Transfer",
         "title": "MOVEit Transfer SQL Injection",
         "short_description": "Unauthenticated SQL injection leads to "
                              "remote code execution.",
         "date_added": "2023-06-02", "due_date": "2023-06-23",
         "exploit_public": "Yes",
         "notes": "Pre-auth SQLi RCE, exploited in the wild.",
         "cwes": ["CWE-89"]},
    ]


def engine() -> ThreatIntelEngine:
    global _engine
    if _engine is None:
        _engine = ThreatIntelEngine()
    return _engine


# ---------------------------------------------------------------- wrappers
def check_kev(timeout=None) -> dict:
    """Fetch + analyze the KEV catalog. JSON-safe, never raises."""
    try:
        eng = engine()
        vulns = eng.fetch_kev()
        zc = eng.analyze_zero_click(vulns)
        pa = eng.analyze_pre_auth(vulns)
        return {
            "ok": True,
            "source": eng.source,
            "total": len(vulns),
            "zero_click_count": len(zc),
            "pre_auth_count": len(pa),
            "zero_click": [v.get("cveID") for v in zc][:100],
            "pre_auth": [v.get("cveID") for v in pa][:100],
            "vendors": dict(sorted(eng.vendor_breakdown(vulns).items(),
                                   key=lambda kv: -kv[1])[:20]),
        }
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def lookup(cve_id: str) -> dict:
    """Is this CVE in the KEV catalog (and is it zero-click/pre-auth)?"""
    try:
        cve_id = (cve_id or "").upper().strip()
        vulns = engine().fetch_kev()
        for v in vulns:
            if (v.get("cveID") or "").upper() == cve_id:
                zc = bool(_filter_indicators([v], ZERO_CLICK_INDICATORS,
                                             "zero_click"))
                pa = bool(_filter_indicators([v], PRE_AUTH_INDICATORS,
                                             "pre_auth"))
                return {"ok": True, "in_kev": True, "cve": cve_id,
                        "zero_click": zc, "pre_auth": pa,
                        "title": v.get("title"),
                        "vendor": v.get("vendor"),
                        "product": v.get("product"),
                        "due_date": v.get("dueDate") or v.get("due_date"),
                        "notes": v.get("notes")}
        return {"ok": True, "in_kev": False, "cve": cve_id}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
