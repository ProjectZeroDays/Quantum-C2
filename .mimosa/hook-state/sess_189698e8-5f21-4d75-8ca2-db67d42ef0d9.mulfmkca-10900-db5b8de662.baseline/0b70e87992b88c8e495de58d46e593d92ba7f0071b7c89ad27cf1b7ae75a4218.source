"""quantum.recon.scan — CIDR scan + ReconModule (scan/fingerprint/osint)."""
from __future__ import annotations

import ipaddress
import threading

from quantum.core.logging import log
from quantum.core.opsec import tcp_probe
from quantum.recon.fingerprint import fingerprint
from quantum.recon.osint import osint_lookup


class ReconModule:
    """Scan/fingerprint/OSINT. Authorized scope only."""

    COMMON = [21, 22, 23, 80, 443, 445, 554, 1433, 3389, 7001, 8000, 8080, 8443, 8899]

    def scan(self, cidr):
        out = {}
        try:
            hosts = [str(h) for h in ipaddress.ip_network(cidr, strict=False).hosts()]
        except ValueError as exc:
            log(f"scan bad CIDR {cidr}: {exc}", "ERR")
            return out
        lock = threading.Lock()

        def work(ip):
            open_ports = [p for p in self.COMMON if tcp_probe(ip, p, timeout=0.4)]
            if open_ports:
                with lock:
                    out[ip] = {"ip": ip, "ports": open_ports}
        _par_map(work, hosts)
        log(f"recon scan {cidr}: {len(out)} live host(s)", "RECON")
        return out

    def fingerprint(self, ip):
        return fingerprint(ip)

    def osint(self, domain):
        return osint_lookup(domain)


def _par_map(work, hosts):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=32) as ex:
        list(ex.map(work, hosts))
