"""quantum.rat — fleet-console remote access (RAT dashboard backend)."""
from quantum.rat.agent import generate_rat_agent
from quantum.rat.commands import (
    CAPABILITIES,
    build,
    capability_names,
    describe,
    dispatch,
    wrap_exfil,
)
from quantum.rat.fleet import STALE_AFTER_S, is_stale, snapshot

__all__ = [
    "CAPABILITIES",
    "STALE_AFTER_S",
    "build",
    "capability_names",
    "describe",
    "dispatch",
    "generate_rat_agent",
    "is_stale",
    "snapshot",
    "wrap_exfil",
]
