"""quantum.anon.kodachi — Kodachi-style anonymous networking, honestly wired.

Kodachi (the privacy Linux distro) achieves anonymous networking with a
stack of desktop Linux tools: Tor, dnscrypt-proxy (DoH), proxychains,
obfs4proxy. Those are x86_64 Linux ELF binaries — they CANNOT be bundled
into the Android APK (arm64/armeabi Bionic target, no proot/chroot to run
desktop ELF), so this module never pretends otherwise:

  * it DISCOVERS those tools wherever they are actually installed on the
    current host (PATH scan — works on the Linux/macOS/Windows CLI),
  * it GENERATES the same configs Kodachi uses (proxychains -> Tor chain,
    dnscrypt-proxy with a DoH resolver list),
  * it LAUNCHES what exists, and
  * every status entry is an honest present/missing — there is no fake
    "enabled" flag anywhere; `kodachi_bundled` is always False.

Every network probe runs only on explicit call (no startup traffic).
"""
from __future__ import annotations

import os
import shutil
import subprocess

from quantum.core.deps import requests
from quantum.core.env import QCLI_DIR
from quantum.core.logging import log
from quantum.core.opsec import tcp_probe

KODACHI_NOTE = (
    "Kodachi binaries are Linux x86_64 ELF and are NOT bundled with this app "
    "(the Android build targets arm64/Bionic and cannot execute desktop ELF). "
    "Install Tor / dnscrypt-proxy / proxychains on this host — or on the phone "
    "via Termux — then use the generated configs below."
)

# component -> candidate binaries + optional local port probe
COMPONENTS = {
    "tor": {"bins": ("tor", "tor.exe"), "port": 9050,
            "role": "SOCKS5 anonymizing relay (default 127.0.0.1:9050)"},
    "dnscrypt": {"bins": ("dnscrypt-proxy", "dnscrypt-proxy.exe"), "port": 5353,
                 "role": "DNSCrypt/DoH resolver (generated config listens 127.0.0.1:5353)"},
    "proxychains": {"bins": ("proxychains4", "proxychains", "proxychains.exe"),
                    "port": None,
                    "role": "forces TCP apps through the Tor chain"},
    "obfs4": {"bins": ("obfs4proxy", "obfs4proxy.exe"), "port": None,
              "role": "pluggable transport for censored Tor circuits"},
    "kodachi": {"bins": ("kodachi",), "port": None,
                "role": "the Kodachi distro CLI itself (Linux only)"},
}


def _which(candidates):
    for name in candidates:
        found = shutil.which(name)
        if found:
            return found
    return None


def detect():
    """Locate each anonymous-networking component on THIS host.

    -> {component: {"binary": path|None, "running": bool|None, "role": str}}
    running is None when there is no port to probe (binary-only tools).
    """
    out = {}
    for name, spec in COMPONENTS.items():
        binary = _which(spec["bins"])
        running = None
        if spec["port"] is not None and binary:
            running = tcp_probe("127.0.0.1", spec["port"], timeout=0.5)
        out[name] = {"binary": binary, "running": running, "role": spec["role"]}
    return out


def anon_status():
    """JSON-ready stack status — honest booleans only, plus the bundling note."""
    comps = detect()
    tor_up = bool(comps["tor"]["binary"]) and comps["tor"]["running"] is True
    return {
        "kodachi_bundled": False,
        "note": KODACHI_NOTE,
        "components": comps,
        "tor_socks_ready": tor_up,
        "paths": {
            "proxychains_conf": os.path.join(QCLI_DIR, "proxychains.conf"),
            "dnscrypt_conf": os.path.join(QCLI_DIR, "dnscrypt-proxy.toml"),
        },
    }


PROXYCHAINS_CONF = """\
# quantum.anon — generated proxychains config (Kodachi-style Tor chain)
strict_chain
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000
[ProxyList]
socks5 127.0.0.1 9050
"""

DNSCRYPT_CONF = """\
# quantum.anon — generated dnscrypt-proxy config (DoH resolvers, DNSSEC)
listen = ['127.0.0.1:5353']
server_names = ['cloudflare', 'google']
urls = ['https://cloudflare-dns.com/dns-query', 'https://dns.google/dns-query']
require_dnssec = true
require_nolog = true
require_nofilter = false
force_tcp = false
timeout = 2500
keepalive = 30
"""


def write_proxychains(path=None):
    """Write the Tor-chain proxychains config; returns the file path."""
    path = path or os.path.join(QCLI_DIR, "proxychains.conf")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(PROXYCHAINS_CONF)
    log(f"proxychains config -> {path}", "OPSEC")
    return path


def write_dnscrypt_config(path=None):
    """Write the DoH dnscrypt-proxy config (port 5353, unprivileged); -> path."""
    path = path or os.path.join(QCLI_DIR, "dnscrypt-proxy.toml")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(DNSCRYPT_CONF)
    log(f"dnscrypt-proxy config -> {path}", "OPSEC")
    return path


def launch(component):
    """Start an installed component with its generated config (explicit call).

    Returns {"launched": bool, ...} — and an honest error when the binary is
    missing rather than pretending something started.
    """
    comps = detect()
    spec = comps.get(component)
    if spec is None:
        return {"launched": False, "error": f"unknown component {component!r}"}
    if not spec["binary"]:
        return {"launched": False, "error": f"{component} not installed",
                "note": KODACHI_NOTE}
    cmd = [spec["binary"]]
    if component == "tor":
        pass  # default torrc / built-in SOCKS 9050 is what we probe for
    elif component == "dnscrypt":
        cmd += ["-config", write_dnscrypt_config()]
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f"anon: launched {component} (pid {proc.pid})", "OPSEC")
        return {"launched": True, "pid": proc.pid, "cmd": cmd}
    except Exception as e:
        log(f"anon: launch {component} failed: {e}", "WARN")
        return {"launched": False, "error": str(e)}


def anon_fetch(url, timeout=15):
    """Fetch [url] through the local Tor SOCKS5 proxy if it is up.

    Honest failure modes: no Tor => error; requests lacks the socks extra =>
    error telling the operator exactly what to install (PySocks). Nothing is
    silently sent in the clear.
    """
    comps = detect()
    if not (comps["tor"]["binary"] and comps["tor"]["running"]):
        return {"error": "Tor SOCKS on 127.0.0.1:9050 not running — "
                         "start it first (launch('tor')) or install Tor",
                "note": KODACHI_NOTE}
    try:
        import socks  # noqa: F401 — presence check for requests[socks]
    except ImportError:
        return {"error": "PySocks not installed — install 'pysocks' so requests "
                         "can route via socks5h://127.0.0.1:9050"}
    try:
        r = requests.get(
            url,
            proxies={"http": "socks5h://127.0.0.1:9050",
                     "https": "socks5h://127.0.0.1:9050"},
            timeout=timeout,
        )
        return {"status": r.status_code, "bytes": len(r.content),
                "via": "tor-socks5h"}
    except Exception as e:
        return {"error": str(e), "via": "tor-socks5h"}
