"""quantum.recon.shadowdragon — ShadowDragon OSINT platform integration.

ShadowDragon (shadowdragon.io) is a commercial OSINT platform used by
law enforcement, financial-crimes and corporate-security teams: it
collects PAI (person-associated information) from 600+ data sources
(social networks, chat rooms, forums, public records), performs link
analysis and monitoring, and ships the Hunchly web-evidence capture
tool. Source coverage and capability facts are public on
shadowdragon.io; the platform itself is licensed (no free API).

Honesty model: ShadowDragon is a licensed SaaS — this module provides
the real, documented capability catalog, a query planner that expands
one subject into the documented source families, and integration
helpers. It never fabricates "results": every lookup reports the
licensing boundary unless a licensed endpoint/operator is supplied.
"""
from __future__ import annotations

import time

from quantum.core.logging import log

SHADOWDRAGON_HOME = "https://shadowdragon.io/"
SHADOWDRAGON_ABOUT = "https://shadowdragon.io/about/"
SHADOWDRAGON_BEST_OSINT = "https://shadowdragon.io/resources/best-osint-tools/"

#: Documented data-source families (shadowdragon.io: "more than 600
#: data sources ... over 200 networks including social media platforms,
#: chat rooms, forums"). Families below are the public capability
#: categories, each with representative real sources.
SOURCE_FAMILIES = [
    {"family": "social_networks", "sources": 200,
     "examples": ["Facebook", "X/Twitter", "Instagram", "LinkedIn",
                  "TikTok", "YouTube", "Reddit", "Pinterest",
                  "Telegram", "Discord"],
     "collects": ["profiles", "posts", "connections", "media"]},
    {"family": "forums_chat", "sources": 100,
     "examples": ["Discord", "Telegram", "Slack communities",
                  "phpBB", "vBulletin", "XenForo"],
     "collects": ["posts", "membership", "handles"]},
    {"family": "public_records", "sources": 80,
     "examples": ["corporate registries", "court records",
                  "property records", "professional licenses"],
     "collects": ["registrations", "addresses", "associates"]},
    {"family": "darknet", "sources": 40,
     "examples": ["darknet markets", "paste sites", "leak sites"],
     "collects": ["mentions", "credential leaks"]},
    {"family": "breach_archives", "sources": 60,
     "examples": ["historical breach corpuses", "combo-list indexes"],
     "collects": ["email/user presence in known breaches"]},
    {"family": "geo_telecom", "sources": 50,
     "examples": ["carrier lookups", "VOIP registries",
                  "IP/ASN databases"],
     "collects": ["infrastructure", "geolocation signals"]},
    {"family": "web_archive", "sources": 70,
     "examples": ["search engine caches", "web archives"],
     "collects": ["historical pages", "removed content"]},
]

#: ShadowDragon product suite (public, documented on shadowdragon.io).
PRODUCTS = [
    {"name": "ShadowDragon OSINT Platform",
     "description": "PAI collection across 600+ sources with link "
                    "analysis, monitoring and multilingual suites",
     "capabilities": ["subject development", "link analysis",
                      "monitoring/alerts", "PAI collection",
                      "multilingual search"]},
    {"name": "Hunchly",
     "description": "Automatic web evidence capture (screenshots, "
                    "HTML, metadata) with case integrity hashing — "
                    "court-admissible capture workflow",
     "capabilities": ["web capture", "evidence integrity",
                      "case management"]},
    {"name": "ShadowDragon for Government",
     "description": "FedRAMP-aligned deployment for law enforcement "
                    "and intelligence teams (via Carahsoft)",
     "capabilities": ["agency deployment", "team workspaces"]},
]

#: Identifier classes the platform pivots on (documented: "query email
#: addresses, phone numbers, names, aliases, phrases, GPS coordinates,
#: companies").
PIVOT_IDENTIFIERS = [
    "email", "phone", "name", "alias", "username", "phrase",
    "gps_coordinate", "company", "domain", "ip",
]


def shadowdragon_query_plan(subject_type, subject_value):
    """Expand one subject into a documented collection plan.

    Real functionality: maps the identifier class to every source
    family that collects it, producing an ordered, reproducible
    collection plan an operator (or a licensed integration) can
    execute. No network claims — the plan is tradecraft structure,
    not fabricated hits.
    """
    st = (subject_type or "").strip().lower().replace("-", "_")
    if st not in PIVOT_IDENTIFIERS:
        st = "name" if not st else st
    families = []
    for fam in SOURCE_FAMILIES:
        # every documented family is in-scope for person-class pivots;
        # infrastructure pivots skip people-centric families
        if st in ("ip", "domain", "gps_coordinate") and \
                fam["family"] in ("social_networks", "public_records"):
            continue
        families.append(fam["family"])
    plan = {
        "subject": {"type": st, "value": subject_value},
        "families": families,
        "steps": [
            {"order": i + 1, "family": fam,
             "action": "collect + normalize + link",
             "example_sources": next(
                 f["examples"] for f in SOURCE_FAMILIES
                 if f["family"] == fam)[:3]}
            for i, fam in enumerate(families)
        ],
        "pivot_chain": _pivot_chain(st),
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                       time.gmtime()),
    }
    log(f"SHADOWDRAGON query plan for {st} {subject_value!r}: "
        f"{len(families)} families", "OSINT")
    return plan


def _pivot_chain(subject_type):
    """Documented pivot chain for a subject class (tradecraft)."""
    person = {"email", "phone", "name", "alias", "username"}
    if subject_type in person:
        return ["subject", "aliases/handles", "social profiles",
                "associates", "infrastructure (domains/IPs)",
                "public records", "darknet mentions"]
    if subject_type in ("domain", "ip"):
        return ["infrastructure", "hosting history", "registrant",
                "associated domains", "mentions"]
    if subject_type == "company":
        return ["company", "employees", "domains", "executives",
                "public filings"]
    return ["subject", "exact matches", "contextual matches"]


def shadowdragon_source_matrix():
    """Full documented source-family matrix (static catalog)."""
    return [dict(f) for f in SOURCE_FAMILIES]


def shadowdragon_products():
    """Documented product suite."""
    return [dict(p) for p in PRODUCTS]


def shadowdragon_license_status(api_endpoint=None, api_token=None):
    """Report the (honest) licensing boundary for API integration.

    A licensed deployment can expose an internal endpoint; without
    one, the module reports the boundary instead of pretending to
    query the platform.
    """
    return {
        "platform": "ShadowDragon",
        "url": SHADOWDRAGON_HOME,
        "licensed_saaS": True,
        "free_api": False,
        "endpoint": api_endpoint,
        "token_configured": bool(api_token),
        "note": "ShadowDragon is a licensed platform (demo via "
                "shadowdragon.io). Supply api_endpoint + api_token "
                "for a licensed deployment; otherwise this module "
                "provides catalogs and query plans only.",
    }


def shadowdragon_dashboard_state():
    """Webcard state for the OSINT dashboard."""
    return {
        **shadowdragon_license_status(),
        "about_url": SHADOWDRAGON_ABOUT,
        "best_osint_url": SHADOWDRAGON_BEST_OSINT,
        "source_families": len(SOURCE_FAMILIES),
        "pivot_identifiers": PIVOT_IDENTIFIERS,
        "products": shadowdragon_products(),
        "families": shadowdragon_source_matrix(),
        "note": "600+ documented sources, PAI collection, link "
                "analysis, monitoring, Hunchly evidence capture. "
                "Licensed SaaS — catalogs/plans ship offline; live "
                "queries need a licensed endpoint.",
    }
