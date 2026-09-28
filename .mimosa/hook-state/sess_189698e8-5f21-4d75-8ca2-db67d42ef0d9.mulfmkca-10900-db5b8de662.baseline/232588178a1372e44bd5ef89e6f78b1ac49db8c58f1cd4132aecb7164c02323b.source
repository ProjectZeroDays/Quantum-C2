"""quantum.core.opsec — OPSEC helpers, probes, jitter, subprocess."""
from __future__ import annotations

import os
import random
import socket
import subprocess
import time

from quantum.core.deps import requests
from quantum.core.logging import log


def run(cmd, timeout=90):
    """shell command runner -> CompletedProcess (text mode, captured)."""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          timeout=timeout)


def tcp_probe(ip, port, timeout=0.8):
    """TCP connect check -> bool."""
    try:
        with socket.create_connection((ip, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def network_aware_jitter(base=15.0):
    """Return a human-ish pause duration for the caller to sleep
    (network-look pacing): base scaled by 0.2–1.0."""
    return base * random.uniform(0.2, 1.0)


def rand_hex(n=32):
    return os.urandom(n).hex()[:n]


class OPSEC:
    """OPSEC helpers: safe web fetch, Tor check, jittered agents."""

    AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (X11; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    ]

    @classmethod
    def web(cls, url, params=None, timeout=10):
        r = requests.get(url, params=params, timeout=timeout,
                         headers={"User-Agent": random.choice(cls.AGENTS)})
        r.raise_for_status()
        return r

    @staticmethod
    def ensure_tor():
        """Check/control local Tor; log the honest state."""
        if os.path.exists(r"C:\Program Files\Tor Browser") or _tor_binary():
            log("Tor present — covert egress available", "OPSEC")
            return True
        if tcp_probe("127.0.0.1", 9050, timeout=1):
            log("Tor SOCKS on 9050 — covert egress active", "OPSEC")
            return True
        log("Tor not installed — direct egress in use (install Tor for .onion)", "WARN")
        return False


def _tor_binary():
    for d in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.isfile(os.path.join(d, "tor")) or \
                os.path.isfile(os.path.join(d, "tor.exe")):
            return True
    return False
