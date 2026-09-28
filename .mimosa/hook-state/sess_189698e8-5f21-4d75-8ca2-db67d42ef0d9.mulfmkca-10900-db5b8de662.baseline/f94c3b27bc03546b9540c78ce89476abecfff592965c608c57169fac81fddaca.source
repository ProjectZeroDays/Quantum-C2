"""quantum.ai.supervisor — Abliterated.ai primary, local/QBrain fallback.

OpenAI-compatible /chat/completions; parses choices[0].message.content.
bootstrap() never touches the network; the --no-ai path never queries.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime

from quantum.core.deps import requests
from quantum.core.env import load_env_file, no_ai_mode
from quantum.core.logging import log


class AI_Supervisor:
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
        from quantum.core.env import LOG_DIR
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
        from quantum.core.jurgen import QBrain
        from quantum.weapons.registry import ZERO_DAY_REGISTRY
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
