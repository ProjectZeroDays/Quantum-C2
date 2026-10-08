"""quantum.recon.intelx — Intelligence X (intelx.io) OSINT integration.

Intelligence X is a search engine and data archive indexing Tor, I2P,
data leaks and the public web by selector (email, domain, IP, CIDR,
Bitcoin address, ...). The Search API at ``https://intelx.io/api/``
returns every hit for a selector; the Phonebook API pivots one
identifier into related ones; intelx.io/tools hosts the public
OSINT tool suite (Mitaka, email/phone/name lookups, ...).

Honesty model: the Search/Phonebook APIs require a (free) API key
from intelx.io. With no key the client builds the exact request and
reports the missing credential instead of fabricating hits. Every
network call goes through OPSEC.web (randomised UA, timeout).
"""
from __future__ import annotations

import os

from quantum.core.logging import log
from quantum.core.opsec import OPSEC

INTELX_API = "https://intelx.io/api/"
INTELX_PHONEBOOK = "https://intelx.io/api/phonebook"
INTELX_TOOLS = "https://intelx.io/tools"
INTELX_HOME = "https://intelx.io/"

# Default search semantics (documented API defaults).
DEFAULT_MAXRESULTS = 100
DEFAULT_TERMINATE = "date"
DEFAULT_TIMEOUT = 5000  # ms — server-side search timeout

#: Public tool catalog served from intelx.io/tools (selector families
#: the platform pivots on — real entries, documented on the site).
INTELX_TOOLS_CATALOG = [
    {"name": "Search", "family": "selector",
     "description": "Full-archive selector search (email, domain, IP, "
                    "CIDR, Bitcoin address, URL, phone, name)",
     "url": "https://intelx.io/search"},
    {"name": "Phonebook", "family": "pivot",
     "description": "Pivot an identifier (email/phone/name/domain) "
                    "into every related identifier in the archive",
     "url": "https://intelx.io/phonebook"},
    {"name": "Email", "family": "pivot",
     "description": "Email address lookup across breach/leak archives",
     "url": "https://intelx.io/email"},
    {"name": "IP", "family": "pivot",
     "description": "IP address lookup: hosting history, domains, "
                    "blacklist presence",
     "url": "https://intelx.io/ip"},
    {"name": "Domain", "family": "pivot",
     "description": "Domain lookup: WHOIS history, subdomains, "
                    "related infrastructure",
     "url": "https://intelx.io/domain"},
    {"name": "BTC", "family": "pivot",
     "description": "Bitcoin address lookup across leak archives",
     "url": "https://intelx.io/btc"},
    {"name": "URL", "family": "pivot",
     "description": "URL lookup: archived snapshots, referrers",
     "url": "https://intelx.io/url"},
    {"name": "Map", "family": "geo",
     "description": "Geographic map view of archive hits",
     "url": "https://intelx.io/map"},
]

#: Selector types accepted by the Search API (documented).
SELECTOR_TYPES = [
    "email", "domain", "ip", "cidr", "bitcoin", "url", "phone",
    "name", "username", "creditcard", "ssn",
]


def intelx_key(env=None):
    """API key from INTELX_API_KEY / INTELX_KEY env vars, or None."""
    import os
    env = env if env is not None else os.environ
    return env.get("INTELX_API_KEY") or env.get("INTELX_KEY") or None


def intelx_search(query, api_key=None, maxresults=DEFAULT_MAXRESULTS,
                  terminate=DEFAULT_TERMINATE, timeout=DEFAULT_TIMEOUT,
                  buckets=None, media=0):
    """Search the Intelligence X archive for one selector.

    Real Search API call: GET https://intelx.io/api/?key=<key>&query=
    <query>&maxresults=<n>&terminate=<field>&timeout=<ms>
    (&buckets=, &media=). Returns {"query":..., "hits":[...],
    "total": n, "api": "intelx"} on success, or an honest
    {"error": ...} (missing key / network / HTTP status).
    """
    key = api_key or intelx_key()
    if not key:
        return {"query": query, "hits": [], "total": 0,
                "error": "no API key — set INTELX_API_KEY "
                         "(free key at intelx.io)",
                "request": intelx_build_search_url(query, maxresults,
                                                    terminate, timeout,
                                                    buckets, media)}
    params = {
        "key": key,
        "query": query,
        "maxresults": str(int(maxresults)),
        "terminate": terminate,
        "timeout": str(int(timeout)),
        "media": str(int(media)),
    }
    if buckets:
        params["buckets"] = buckets
    try:
        r = OPSEC.web(INTELX_API, params=params, timeout=20)
        data = r.json()
        hits = data.get("results", data.get("records", []))
        if isinstance(hits, dict):
            hits = list(hits.values())
        log(f"INTELX search {query!r}: {len(hits)} hits", "OSINT")
        return {"query": query, "hits": hits,
                "total": len(hits), "api": "intelx"}
    except Exception as exc:  # noqa: BLE001 — honest error, never raise
        return {"query": query, "hits": [], "total": 0,
                "error": f"intelx search failed: {exc}",
                "api": "intelx"}


def intelx_build_search_url(query, maxresults=DEFAULT_MAXRESULTS,
                            terminate=DEFAULT_TERMINATE,
                            timeout=DEFAULT_TIMEOUT, buckets=None,
                            media=0):
    """Exact Search API URL for a query (key redacted) — used for the
    dashboard webcard and for honest no-key reporting."""
    from urllib.parse import urlencode
    params = [("query", query), ("maxresults", str(int(maxresults))),
              ("terminate", terminate), ("timeout", str(int(timeout))),
              ("media", str(int(media)))]
    if buckets:
        params.append(("buckets", buckets))
    return INTELX_API + "?" + urlencode(params)


def intelx_phonebook(value, api_key=None, limit=100):
    """Phonebook pivot: one identifier -> related identifiers.

    Real API call: GET https://intelx.io/api/phonebook/?key=..&q=..&
    limit=..  (the phonebook endpoint of the Search API family).
    """
    key = api_key or intelx_key()
    if not key:
        return {"value": value, "related": [], "error":
                "no API key — set INTELX_API_KEY (free key at intelx.io)"}
    params = {"key": key, "q": value, "limit": str(int(limit))}
    try:
        r = OPSEC.web(INTELX_PHONEBOOK, params=params, timeout=20)
        data = r.json()
        related = data.get("results", data.get("related", []))
        log(f"INTELX phonebook {value!r}: {len(related)} related", "OSINT")
        return {"value": value, "related": related,
                "total": len(related), "api": "intelx-phonebook"}
    except Exception as exc:  # noqa: BLE001
        return {"value": value, "related": [], "error":
                f"intelx phonebook failed: {exc}"}


def intelx_tools():
    """Public intelx.io tools catalog (static, documented set)."""
    return [dict(t) for t in INTELX_TOOLS_CATALOG]


def intelx_dashboard_state():
    """Webcard state for the OSINT dashboard."""
    key = intelx_key()
    return {
        "service": "Intelligence X",
        "url": INTELX_HOME,
        "api": INTELX_API,
        "tools_url": INTELX_TOOLS,
        "key_configured": bool(key),
        "key_hint": (key[:4] + "…" + key[-4:]) if len(key or "") > 12
                    else ("set" if key else "missing"),
        "selector_types": SELECTOR_TYPES,
        "tools": intelx_tools(),
        "defaults": {"maxresults": DEFAULT_MAXRESULTS,
                     "terminate": DEFAULT_TERMINATE,
                     "timeout_ms": DEFAULT_TIMEOUT},
        "note": "Search/Phonebook APIs need a free intelx.io key "
                "(INTELX_API_KEY). Without it requests are built, "
                "never faked.",
    }


def intelx_recent_queries(limit=20, log_path=None):
    """Recent intelx queries from the engagement audit log (real)."""
    from quantum.core.logging import _tail_jsonl
    from quantum.core.env import LOG_DIR
    path = log_path or os.path.join(LOG_DIR, "audit.jsonl")
    out = []
    for rec in _tail_jsonl(path, 200):
        try:
            msg = str(rec.get("msg", ""))
        except AttributeError:
            continue
        if "INTELX" in msg:
            out.append(rec)
            if len(out) >= limit:
                break
    return out


def intelx_dashboard_state_full():
    """State + recent queries for the OSINT dashboard webcard."""
    state = intelx_dashboard_state()
    state["recent"] = intelx_recent_queries()
    return state
