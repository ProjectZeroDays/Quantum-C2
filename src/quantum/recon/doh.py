"""quantum.recon.doh — DNS-over-HTTPS resolver (JSON API, multi-resolver).

Network op — only on explicit call; never on the --no-ai path.

Resolver rotation: Cloudflare -> Google -> AliDNS. The first answer wins;
if every resolver fails the last error is RAISED so callers can drive their
own retry/backoff policy (see quantum.c2.agents.ghostdns.PersistentDoHChannel).
"""
from __future__ import annotations

from quantum.core.deps import requests


class DoH:
    # JSON-API DoH endpoints, tried in order until one answers.
    ENDPOINTS = (
        "https://cloudflare-dns.com/dns-query",
        "https://dns.google/resolve",
        "https://dns.alidns.com/resolve",
    )

    def resolve(self, name, rtype="A", timeout=8):
        if requests is None:
            raise RuntimeError("requests not installed — DoH unavailable")
        last = None
        for url in self.ENDPOINTS:
            try:
                r = requests.get(
                    url,
                    params={"name": name, "type": rtype},
                    headers={"Accept": "application/dns-json"},
                    timeout=timeout,
                )
                r.raise_for_status()
                return r.json().get("Answer") or []
            except Exception as e:  # rotate to the next resolver
                last = e
        raise RuntimeError(f"DoH failed on all {len(self.ENDPOINTS)} resolvers: {last}")
