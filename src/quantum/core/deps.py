"""quantum.core.deps — guarded optional dependencies (single import point)."""
from __future__ import annotations

try:
    import requests
    from requests.auth import HTTPBasicAuth, HTTPDigestAuth
    HAS_REQUESTS = True
except Exception:
    requests = None
    HTTPBasicAuth = HTTPDigestAuth = None
    HAS_REQUESTS = False

try:
    import flask
    from flask import Flask, Response, jsonify, request
    HAS_FLASK = True
except Exception:
    flask = Flask = Response = jsonify = request = None
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

try:
    import colorama
    colorama.just_fix_windows_console()
    from colorama import Fore
except Exception:
    class _Fore:
        CYAN = GREEN = LIGHTRED_EX = RESET = ""
    Fore = _Fore


def check_deps() -> dict:
    """Report optional dependency availability."""
    import sys
    return {
        "requests": HAS_REQUESTS,
        "flask": HAS_FLASK,
        "cryptography(AESGCM)": HAS_AESGCM,
        "pycryptodome": HAS_PYCRYPTO,
        "impacket": HAS_IMPACKET,
        "pysmb": HAS_PYSMB,
        "python": sys.version.split()[0],
        "platform": sys.platform,
    }
