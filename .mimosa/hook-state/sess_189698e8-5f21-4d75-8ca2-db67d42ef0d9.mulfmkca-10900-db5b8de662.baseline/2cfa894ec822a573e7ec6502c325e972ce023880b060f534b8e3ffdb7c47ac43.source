"""quantum.overlord.decide — AI/QBrain decision extraction + whitelist guard."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime

from quantum.ai.supervisor import AI_Supervisor, no_ai_mode
from quantum.core.env import LOG_DIR
from quantum.core.jurgen import QBrain
from quantum.core.logging import log

DEFAULT_ACTS = ["cam_war", "cam_discover", "cam_control", "recon_scope", "exploit",
                "brute", "phish", "worm", "harvest", "router", "osint",
                "episcribe", "mitre_report", "rest"]
CAMERA_ONLY_ACTS = ["cam_war", "cam_discover", "cam_control", "mitre_report", "rest"]


def decide(overlord):
    """One decision: AI-driven JSON (when alive) with QBrain deterministic
    fallback. Always obeys the act whitelist; journaled to decisions.jsonl."""
    acts = overlord.ACTIONS if not overlord.camera_only else CAMERA_ONLY_ACTS
    budget = json.dumps(overlord.state, default=str)[:2000]
    p = (f"You are running an authorized red-team engagement (aggression: {overlord.aggression}). "
         f"Scope: {overlord.scope}. Cameras are AN important objective. "
         f"Campaign state so far: {budget}. Choose the single next action from this list ONLY: {acts}. "
         "Reply as strict JSON: {\"action\": \"...\", \"target\": \"ip-or-domain-or-blank\", "
         "\"reason\": \"one sentence\"}.")
    d = None
    if not AI_Supervisor.ai_dead and not no_ai_mode():
        raw = overlord.ai.query_bounded(p, timeout=120,
                                        system="You are an autonomous red-team commander. Output JSON only.")
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
        d = QBrain.decide(overlord.state, acts, overlord.camera_only)
        if d.get("action") not in acts:   # paranoia: QBrain must obey the whitelist
            d = {"action": "rest", "target": "", "reason": "fallback"}
    with open(os.path.join(LOG_DIR, "decisions.jsonl"), "a") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(), **d}) + "\n")
    return d
