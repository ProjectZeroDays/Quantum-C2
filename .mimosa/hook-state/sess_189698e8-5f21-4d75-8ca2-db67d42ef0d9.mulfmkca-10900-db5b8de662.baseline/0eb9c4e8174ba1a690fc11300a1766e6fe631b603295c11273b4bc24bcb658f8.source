"""quantum.core.env — paths, platform, environment helpers."""
from __future__ import annotations

import os
import sys

__version__ = "3.1.0"
OS_NAME = "Windows" if os.name == "nt" else ("Darwin" if sys.platform == "darwin" else "POSIX")

for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

_BASE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
# walk up from src/quantum/core/env.py to the repo root (stops past src/)
try:
    _PKG = os.path.dirname(os.path.abspath(__file__))
    for _level in ("core", "quantum", "src"):
        if os.path.basename(_PKG) == _level:
            _PKG = os.path.dirname(_PKG)
except NameError:
    _PKG = os.getcwd()

QCLI_DIR = os.path.join(_PKG, "qcli")
LOG_DIR = os.path.join(_PKG, "logs")
LOOT_DIR = os.path.join(_PKG, "loot")
MODELS_DIR = os.path.join(_PKG, "models")
KEYS_DIR = os.path.join(QCLI_DIR, "keys")
PRIV = os.path.join(KEYS_DIR, "priv.pem")
PUB = os.path.join(KEYS_DIR, "pub.xml")
AGENT = os.path.join(QCLI_DIR, "obsidian.ps1")

for _d in (QCLI_DIR, LOG_DIR, LOOT_DIR, KEYS_DIR, MODELS_DIR):
    try:
        os.makedirs(_d, exist_ok=True)
    except OSError:
        pass


def no_ai_mode():
    """True when running fully deterministic (QBrain) — --no-ai / QCLI_NO_AI=1."""
    return os.environ.get("QCLI_NO_AI") == "1"


def load_env_file(path=None):
    """Parse .env KEY=VALUE lines into a dict (no interpolation)."""
    env = {}
    path = path or os.path.join(_PKG, ".env")
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
    import socket
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
