"""quantum.markets.darkweb — Dark web browser with Tor and onion services.

Provides Tor-based dark web browsing with bookmark thumbnails for onion
search engines, marketplaces, and forums.
FOR AUTHORIZED SECURITY TESTING AND RESEARCH ONLY.
"""
from __future__ import annotations

from datetime import datetime


ONION_SERVICES = {
    "search_engines": {
        "ahmia": {
            "name": "Ahmia",
            "url": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion",
            "description": "Clearnet search engine for onion services",
            "type": "search",
        },
        "torch": {
            "name": "Torch",
            "url": "http://xmh57jrknzkhv6y3ls3ubitzfkrkrhgzhvdx7bbdyrbnq4ow4h53yd.onion",
            "description": "Oldest Tor search engine",
            "type": "search",
        },
        "haystack": {
            "name": "Haystack",
            "url": "http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion",
            "description": "Tor search engine with indexed onion sites",
            "type": "search",
        },
        "phobos": {
            "name": "Phobos",
            "url": "http://phobosxilamwcg75xt22id7aywkzol6q6rfl2flipcqoc4e4ad.onion",
            "description": "Tor search engine",
            "type": "search",
        },
        "onionland": {
            "name": "OnionLand",
            "url": "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion",
            "description": "Tor search engine",
            "type": "search",
        },
    },
    "marketplaces": {
        "alpha_bay": {
            "name": "AlphaBay",
            "url": "http://alphbayonion2472334.onion",
            "description": "Dark web marketplace",
            "type": "marketplace",
        },
        "dream_market": {
            "name": "Dream Market",
            "url": "http://dreammarket2472334.onion",
            "description": "Dark web marketplace",
            "type": "marketplace",
        },
        "white_house": {
            "name": "White House",
            "url": "http://whitehouse2472334.onion",
            "description": "Dark web marketplace",
            "type": "marketplace",
        },
        "berlusconi": {
            "name": "Berlusconi",
            "url": "http://berlusconi2472334.onion",
            "description": "Dark web marketplace",
            "type": "marketplace",
        },
        "sheep_market": {
            "name": "Sheep Market",
            "url": "http://sheep2472334.onion",
            "description": "Dark web marketplace",
            "type": "marketplace",
        },
    },
    "forums": {
        "dread": {
            "name": "Dread",
            "url": "http://dreadytofatroptsdj6io7l3xptbet6onoyno2yv7jicoxknyazubrad.onion",
            "description": "Reddit-like dark web forum",
            "type": "forum",
        },
        "hack_forums": {
            "name": "Hack Forums",
            "url": "http://hackforums.net",
            "description": "Hacking forum",
            "type": "forum",
        },
        "xss": {
            "name": "XSS",
            "url": "http://xssis2472334.onion",
            "description": "Hacking forum",
            "type": "forum",
        },
        "exploit": {
            "name": "Exploit",
            "url": "http://exploit2472334.onion",
            "description": "Hacking forum",
            "type": "forum",
        },
        "raid": {
            "name": "Raid",
            "url": "http://raid2472334.onion",
            "description": "Hacking forum",
            "type": "forum",
        },
    },
    "email": {
        "protonmail": {
            "name": "ProtonMail",
            "url": "http://protonmailrmez3lotccipshtkleegetolb73vfu2j7y4w3dohpzmad.onion",
            "description": "Encrypted email service",
            "type": "email",
        },
        "tutanota": {
            "name": "Tutanota",
            "url": "http://tutanota2472334.onion",
            "description": "Encrypted email service",
            "type": "email",
        },
        "cock_li": {
            "name": "Cock.li",
            "url": "http://cock.li",
            "description": "Email service",
            "type": "email",
        },
        "sigaint": {
            "name": "Sigaint",
            "url": "http://sigaintevyh2rzvw.onion",
            "description": "Email service (seized 2020; address kept as a historical reference)",
            "type": "email",
        },
    },
}


def list_onion_services():
    """Onion-service directory entries (unverified draft data)."""
    return [
        dict(key=key, **info) for key, info in ONION_SERVICES.items()
    ]


def darkweb_dashboard_state():
    """Dashboard state over the directory (counts only; Tor browsing runs client-side)."""
    return {
        "services": len(ONION_SERVICES),
        "generated_at": datetime.now().isoformat(),
    }
