"""quantum.ai.skills — skill registry (PROMPT / TOOL / SCRIPT kinds).

Skills are composable capabilities an agent (or the chat) can load:
  PROMPT  — a reusable doctrine/prompt fragment
  TOOL    — a named QCLI API command the model may call
  SCRIPT  — a shell/python snippet executed by the workflow runner

Persisted as JSON under skills/ with seeded red-team + SDLC packs.
"""
from __future__ import annotations

import json
import os
import time

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "skills")

_PRESETS = [
    # ---- nation-state red-team pack ----
    {"id": "redteam.killchain", "name": "Kill Chain Doctrine", "kind": "PROMPT",
     "content": "Plan and execute through RECON -> ANALYZE -> STRIKE -> "
                "ESCALATE & MOVE -> LOOT -> DISRUPT -> AAR. Prefer minimal-"
                "footprint techniques; log every technique used.",
     "tags": ["redteam"]},
    {"id": "redteam.attck", "name": "ATT&CK Mapping", "kind": "PROMPT",
     "content": "Map every technique to MITRE ATT&CK (e.g. T1595 Active "
                "Scanning, T1210 Exploitation of Remote Services, T1005 Data "
                "from Local System). Cite sub-techniques.",
     "tags": ["redteam"]},
    {"id": "redteam.opsec", "name": "OPSEC Doctrine", "kind": "PROMPT",
     "content": "Assume defenders have EDR/SIEM/SOAR. Operate as if watched: "
                "prefer reversible techniques, rotate infrastructure, minimize "
                "attribution breadcrumbs, fall back to stealth posture when "
                "detection seems imminent.",
     "tags": ["redteam"]},
    {"id": "tool.scan", "name": "Network Scan", "kind": "TOOL",
     "content": "scan", "tags": ["tool"]},
    {"id": "tool.fingerprint", "name": "Target Fingerprint", "kind": "TOOL",
     "content": "fingerprint", "tags": ["tool"]},
    {"id": "tool.zerocheck", "name": "Zero-Day Check", "kind": "TOOL",
     "content": "zerocheck", "tags": ["tool"]},
    {"id": "tool.fire", "name": "Fire Exploit", "kind": "TOOL",
     "content": "fire", "tags": ["tool"]},
    {"id": "tool.camwar", "name": "Camera Sweep", "kind": "TOOL",
     "content": "camwar", "tags": ["tool"]},
    {"id": "tool.brute", "name": "Credential Brute", "kind": "TOOL",
     "content": "brute", "tags": ["tool"]},
    {"id": "tool.mitre", "name": "MITRE Report", "kind": "TOOL",
     "content": "mitre", "tags": ["tool"]},
    {"id": "script.p0feed", "name": "Project Zero Feed Scan", "kind": "SCRIPT",
     "content": "python -m quantum.cli_p0feed  # or: from quantum.recon.project_zero import latest",
     "tags": ["redteam", "script"]},
    # ---- SDLC / dev pack ----
    {"id": "dev.plan", "name": "App Architecture", "kind": "PROMPT",
     "content": "Produce: requirements list, data model, API contract, UI "
                "wireframe description, test plan, and a build order.",
     "tags": ["dev"]},
    {"id": "dev.tests", "name": "Test-First", "kind": "PROMPT",
     "content": "Write failing tests that encode the acceptance criteria, then "
                "the minimal implementation that passes them.",
     "tags": ["dev"]},
    {"id": "dev.review", "name": "Adversarial Code Review", "kind": "PROMPT",
     "content": "Review as an attacker: unvalidated input, injection, authz "
                "gaps, secrets handling, error-handling leaks, dependency "
                "risk.",
     "tags": ["dev"]},
    {"id": "script.build", "name": "Run Test Suite", "kind": "SCRIPT",
     "content": "python -m pytest tests -q", "tags": ["dev", "script"]},
]


def ensure_dir():
    os.makedirs(SKILLS_DIR, exist_ok=True)


def _path(skill_id):
    safe = "".join(c for c in skill_id if c.isalnum() or c in "-_.")[:64]
    return os.path.join(SKILLS_DIR, f"{safe}.json")


def load_all():
    ensure_dir()
    skills = {}
    for fn in sorted(os.listdir(SKILLS_DIR)):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(SKILLS_DIR, fn), encoding="utf-8") as fh:
                s = json.load(fh)
            if isinstance(s, dict) and s.get("id"):
                skills[s["id"]] = s
        except (OSError, ValueError):
            continue
    for p in _PRESETS:
        skills.setdefault(p["id"], dict(p))
    return skills


def get(skill_id):
    return load_all().get(skill_id)


def save(skill):
    if not skill or not skill.get("id"):
        raise ValueError("skill.id required")
    if skill.get("kind") not in ("PROMPT", "TOOL", "SCRIPT"):
        skill["kind"] = "PROMPT"
    ensure_dir()
    s = dict(skill)
    s["updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(_path(s["id"]), "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=2)
    return s


def delete(skill_id):
    path = _path(skill_id)
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False


def compose_prompt(skill_ids):
    """Compose PROMPT-kind skills into one system-prompt fragment."""
    all_skills = load_all()
    parts = []
    for sid in skill_ids:
        s = all_skills.get(sid)
        if s and s.get("kind") == "PROMPT":
            parts.append(f"[{s['name']}]\n{s['content']}")
    return "\n\n".join(parts)
