"""quantum.recon.doh — DNS-over-HTTPS resolver (Cloudflare JSON API).

Network op — only on explicit call; never on the --no-ai path.
"""
from __future__ import annotations

from quantum.core.deps import requests


class DoH:
    def resolve(self, name, rtype="A", timeout=8):
        url = ("https://cloudflare-dns.com/dns-query?name="
               + requests.utils.quote(name) + "&type=" + rtype)
        r = requests.get(url, headers={"Accept": "application/dns-json"},
                         timeout=timeout)
        return r.json().get("Answer", [])
