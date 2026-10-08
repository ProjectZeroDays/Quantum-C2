"""quantum.recon.darkowl — DarkOwl Vision darknet-intelligence integration.

DarkOwl (darkowl.com) runs the world's largest index of darknet,
deep-web and high-risk surface content ("DARKINT"). The Vision
Search API (api.darkowl.com /api/v1/search) is authenticated with
an OWL HMAC-SHA1 scheme:

    Authorization: OWL <public_key>:<base64(HMAC-SHA1(private_key,
                                    "GET" + path + query + date))>
    X-Vision-DATE: <RFC 2822 GMT date>

and returns {"total": N, "results": [{"id": ...}, ...]}. The API
family also exposes Entity (email/domain/IP), Markets, DarkSonar,
Score, Ransomware and Actor endpoints, plus a Test endpoint that
answers {"answer": "hoot"}.

Honesty model: the Vision API is licensed (demo via darkowl.com).
Without keys the client builds and signs nothing — it reports the
missing credential. The HMAC signing scheme below is the documented
one from DarkOwl's public API example code, so a licensed key
works against the real endpoint as-is.
"""
from __future__ import annotations

import base64
import datetime
import hmac
import hashlib
from urllib.parse import urlencode

from quantum.core.deps import requests
from quantum.core.logging import log

DARKOWL_HOST = "api.darkowl.com"
DARKOWL_BASE = f"https://{DARKOWL_HOST}"
DARKOWL_SEARCH = "/api/v1/search"
DARKOWL_TEST = "/api/v1/test"
DARKOWL_HOME = "https://www.darkowl.com/"
DARKOWL_VISION_LOGIN = "https://vision.darkowl.com/"
DARKOWL_API_DOCS = "https://docs.api.darkowl.com/"

#: Documented Vision API endpoint family (darkowl.com/products).
ENDPOINTS = [
    {"name": "Search", "path": "/api/v1/search",
     "description": "Full-text darknet search (q, crawlFrom/to, "
                    "sourceType, market, language, ...); paginate "
                    "via crawlDate"},
    {"name": "Entity", "path": "/api/v1/entity",
     "description": "Email address, email-domain and IP entity "
                    "lookups"},
    {"name": "Markets", "path": "/api/v1/markets",
     "description": "Darknet market summary/details endpoints"},
    {"name": "DarkSonar", "path": "/api/v1/darksonar",
     "description": "Relative risk rating for a domain"},
    {"name": "Score", "path": "/api/v1/score",
     "description": "DarkOwl risk score requests"},
    {"name": "Ransomware", "path": "/api/v1/ransomware",
     "description": "Ransomware-group leak-site data"},
    {"name": "Actor", "path": "/api/v1/actor",
     "description": "Threat-actor profiles"},
    {"name": "Test", "path": "/api/v1/test",
     "description": "Connectivity check — responds "
                    "{\"answer\": \"hoot\"}"},
]

#: Documented search parameters (docs.api.darkowl.com).
SEARCH_PARAMS = [
    "q", "crawlFrom", "crawlTo", "sourceType", "market",
    "language", "excludeSource", "includeDeadLinks",
]


def darkowl_keys(env=None):
    """(public, private) keys from DARKOWL_PUBLIC_KEY /
    DARKOWL_PRIVATE_KEY env vars, or (None, None)."""
    import os
    env = env if env is not None else os.environ
    return (env.get("DARKOWL_PUBLIC_KEY") or None,
            env.get("DARKOWL_PRIVATE_KEY") or None)


def darkowl_auth_header(method, abs_path, private_key, public_key,
                        date_stamp=None):
    """Documented OWL authorization header for a request.

    string-to-hash = METHOD + absPath + date; signature =
    base64(HMAC-SHA1(private_key, string2hash)); header =
    "OWL <public_key>:<signature>". This is the exact scheme
    from DarkOwl's public API example code.
    """
    date_stamp = date_stamp or datetime.datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S GMT")
    string2hash = method + abs_path + date_stamp
    sig = hmac.new(private_key.encode("utf-8"),
                   string2hash.encode("utf-8"),
                   hashlib.sha1).digest()
    return ("OWL " + public_key + ":" +
            base64.b64encode(sig).decode("utf-8"), date_stamp)


def darkowl_search(query, public_key=None, private_key=None,
                   extra_params=None, timeout=20):
    """Search the DarkOwl Vision index for one query.

    Real Vision Search API call. Returns {"query":..., "total": N,
    "results":[...]} on success; honest {"error": ...} otherwise
    (missing keys / network / HTTP status).
    """
    public_key = public_key or darkowl_keys()[0]
    private_key = private_key or darkowl_keys()[1]
    if not public_key or not private_key:
        return {"query": query, "total": 0, "results": [],
                "error": "no API keys — set DARKOWL_PUBLIC_KEY + "
                         "DARKOWL_PRIVATE_KEY (licensed at "
                         "darkowl.com)"}
    payload = [("q", query)]
    for k, v in (extra_params or {}).items():
        if k in SEARCH_PARAMS:
            payload.append((k, str(v)))
    search = "?" + urlencode(payload)
    url = DARKOWL_BASE + DARKOWL_SEARCH + search
    auth, date_stamp = darkowl_auth_header("GET",
                                            DARKOWL_SEARCH + search,
                                            private_key, public_key)
    headers = {"Authorization": auth, "X-VISION-DATE": date_stamp,
               "Accept": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return {"query": query, "total": 0, "results": [],
                    "error": f"darkowl search HTTP {r.status_code}"}
        data = r.json()
        results = data.get("results", [])
        log(f"DARKOWL search {query!r}: {data.get('total', 0)} "
            "results", "OSINT")
        return {"query": query, "total": data.get("total", 0),
                "results": results, "api": "darkowl-vision"}
    except Exception as exc:  # noqa: BLE001 — honest error
        return {"query": query, "total": 0, "results": [],
                "error": f"darkowl search failed: {exc}"}


def darkowl_test(public_key=None, private_key=None, timeout=20):
    """DarkOwl Test endpoint — real connectivity + auth check.

    Responds {"answer": "hoot"} on a successful authenticated
    connection (documented behaviour).
    """
    public_key = public_key or darkowl_keys()[0]
    private_key = private_key or darkowl_keys()[1]
    if not public_key or not private_key:
        return {"ok": False, "error":
                "no API keys — set DARKOWL_PUBLIC_KEY + "
                "DARKOWL_PRIVATE_KEY"}
    auth, date_stamp = darkowl_auth_header("GET", DARKOWL_TEST,
                                            private_key, public_key)
    headers = {"Authorization": auth, "X-VISION-DATE": date_stamp,
               "Accept": "application/json"}
    try:
        r = requests.get(DARKOWL_BASE + DARKOWL_TEST,
                         headers=headers, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            ok = data.get("answer") == "hoot"
            return {"ok": ok, "answer": data.get("answer"),
                    "api": "darkowl-vision"}
        return {"ok": False, "error": f"HTTP {r.status_code}"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def darkowl_entity(entity_type, value, public_key=None,
                   private_key=None, timeout=20):
    """Entity endpoint pivot (email / email_domain / ip).

    Documented Entity API: /api/v1/entity/<type>?value=...
    """
    public_key = public_key or darkowl_keys()[0]
    private_key = private_key or darkowl_keys()[1]
    if entity_type not in ("email", "email_domain", "ip"):
        return {"error": "entity_type must be email|email_domain|ip"}
    if not public_key or not private_key:
        return {"entity_type": entity_type, "value": value,
                "error": "no API keys — set DARKOWL_PUBLIC_KEY + "
                         "DARKOWL_PRIVATE_KEY"}
    path = f"/api/v1/entity/{entity_type}"
    search = "?value=" + requests.utils.quote(str(value))
    auth, date_stamp = darkowl_auth_header("GET", path + search,
                                            private_key, public_key)
    headers = {"Authorization": auth, "X-VISION-DATE": date_stamp,
               "Accept": "application/json"}
    try:
        r = requests.get(DARKOWL_BASE + path + search,
                         headers=headers, timeout=timeout)
        if r.status_code != 200:
            return {"entity_type": entity_type, "value": value,
                    "error": f"HTTP {r.status_code}"}
        return {"entity_type": entity_type, "value": value,
                "data": r.json(), "api": "darkowl-vision"}
    except Exception as exc:  # noqa: BLE001
        return {"entity_type": entity_type, "value": value,
                "error": str(exc)}


def darkowl_dashboard_state():
    """Webcard state for the OSINT dashboard."""
    pub, _priv = darkowl_keys()
    return {
        "service": "DarkOwl Vision",
        "url": DARKOWL_HOME,
        "vision_login": DARKOWL_VISION_LOGIN,
        "api_docs": DARKOWL_API_DOCS,
        "api_base": DARKOWL_BASE,
        "key_configured": bool(pub),
        "key_hint": (pub[:4] + "…") if pub else "missing",
        "endpoints": ENDPOINTS,
        "search_params": SEARCH_PARAMS,
        "auth_scheme": "OWL HMAC-SHA1 (X-VISION-DATE)",
        "test_endpoint": DARKOWL_TEST,
        "test_response": {"answer": "hoot"},
        "note": "Largest documented DARKINT index (darknet, deep "
                "web, high-risk surface). Licensed API — with "
                "DARKOWL_*_KEY set the Search/Entity/Test calls "
                "above hit the real endpoint.",
    }
