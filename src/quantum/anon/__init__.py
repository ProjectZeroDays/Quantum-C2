"""quantum.anon — Kodachi-style anonymous networking (honestly wired)."""
from quantum.anon.kodachi import (
    KODACHI_NOTE,
    anon_fetch,
    anon_status,
    detect,
    launch,
    write_dnscrypt_config,
    write_proxychains,
)

__all__ = [
    "KODACHI_NOTE",
    "anon_fetch",
    "anon_status",
    "detect",
    "launch",
    "write_dnscrypt_config",
    "write_proxychains",
]
