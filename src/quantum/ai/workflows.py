"""quantum.ai.workflows — task/workflow registry + chained runner.

A workflow is a named, ordered list of steps. Each step is either:
  {"tool": "<qcli cmd>", "params": {...}}   — dispatched via QCLI-style tools
  {"script": "<shell command>"}             — run via subprocess

The runner is deterministic and journals each step's outcome; failures do not
halt the chain by default (continue_on_error, overridable per step).
"""
from __future__ import annotations

import json
import os
import subprocess
import time

WORKFLOWS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "workflows")

_PRESETS = [
    {"id": "full-engagement", "name": "Full Engagement (J2 golden path)",
     "steps": [
         {"name": "recon", "tool": "scan", "params": {}},
         {"name": "fingerprint-first-host", "tool": "fingerprint",
          "params": {"ip": "${first_host}"}, "needs": ["first_host"]},
         {"name": "zerocheck", "tool": "zerocheck",
          "params": {"ip": "${first_host}"}, "needs": ["first_host"]},
         {"name": "report", "tool": "mitre", "params": {}},
     ]},
    {"id": "camera-campaign", "name": "Camera Campaign",
     "steps": [
         {"name": "sweep", "tool": "camwar", "params": {"cidr": "${scope}"},
          "needs": ["scope"]},
         {"name": "report", "tool": "mitre", "params": {}},
     ]},
    {"id": "cve-check", "name": "CVE Sweep",
     "steps": [
         {"name": "zerocheck", "tool": "zerocheck",
          "params": {"ip": "${target}"}, "needs": ["target"]},
     ]},
]


def ensure_dir():
    os.makedirs(WORKFLOWS_DIR, exist_ok=True)


def _path(workflow_id):
    safe = "".join(c for c in workflow_id if c.isalnum() or c in "-_.")[:64]
    return os.path.join(WORKFLOWS_DIR, f"{safe}.json")


def load_all():
    ensure_dir()
    flows = {}
    for fn in sorted(os.listdir(WORKFLOWS_DIR)):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(WORKFLOWS_DIR, fn), encoding="utf-8") as fh:
                w = json.load(fh)
            if isinstance(w, dict) and w.get("id"):
                flows[w["id"]] = w
        except (OSError, ValueError):
            continue
    for p in _PRESETS:
        flows.setdefault(p["id"], dict(p))
    return flows


def get(workflow_id):
    return load_all().get(workflow_id)


def save(workflow):
    if not workflow or not workflow.get("id"):
        raise ValueError("workflow.id required")
    if not isinstance(workflow.get("steps"), list):
        workflow["steps"] = []
    ensure_dir()
    w = dict(workflow)
    w["updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(_path(w["id"]), "w", encoding="utf-8") as fh:
        json.dump(w, fh, indent=2)
    return w


def delete(workflow_id):
    path = _path(workflow_id)
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False


def _subst(value, variables):
    """Replace ${var} placeholders inside strings / nested dicts."""
    if isinstance(value, str):
        out = value
        for k, v in (variables or {}).items():
            out = out.replace("${" + k + "}", str(v))
        return out
    if isinstance(value, dict):
        return {k: _subst(v, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [_subst(v, variables) for v in value]
    return value


def run(workflow, dispatch=None, variables=None, on_step=None):
    """Execute a workflow.

    dispatch: callable(cmd:str, params:dict) -> dict — the tool surface
    (e.g. the C2's QCLI API handle). When absent, script steps still run and
    tool steps are journaled as skipped.
    """
    variables = variables or {}
    journal = []
    steps = workflow.get("steps", [])
    resolved_vars = dict(variables)
    for idx, step in enumerate(steps):
        if any(not resolved_vars.get(n) for n in step.get("needs", [])):
            journal.append({"step": step.get("name", idx), "status": "skipped",
                            "reason": "missing variable(s) " +
                                      ",".join(step.get("needs", []))})
            continue
        if "tool" in step:
            params = _subst(step.get("params", {}), resolved_vars)
            if dispatch is None:
                journal.append({"step": step.get("name", idx),
                                "status": "skipped", "reason": "no dispatcher"})
                continue
            try:
                result = dispatch(step["tool"], params)
                journal.append({"step": step.get("name", idx), "status": "ok",
                                "result": result})
                _capture(step, result, resolved_vars)
            except Exception as exc:  # noqa: BLE001 — journal, never raise
                journal.append({"step": step.get("name", idx),
                                "status": "error", "error": str(exc)})
                if not step.get("continue_on_error", True):
                    break
        elif "script" in step:
            cmd = _subst(step["script"], resolved_vars)
            try:
                out = subprocess.run(cmd, shell=True, capture_output=True,
                                     text=True, timeout=120)
                journal.append({"step": step.get("name", idx),
                                "status": "ok" if out.returncode == 0 else "error",
                                "stdout": (out.stdout or "")[:2000],
                                "stderr": (out.stderr or "")[:2000]})
            except Exception as exc:  # noqa: BLE001
                journal.append({"step": step.get("name", idx),
                                "status": "error", "error": str(exc)})
                if not step.get("continue_on_error", True):
                    break
        if on_step:
            on_step(journal[-1])
    return {"workflow": workflow.get("id"), "ts": time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "journal": journal}


def _capture(step, result, resolved_vars):
    """First host from scan results feeds ${first_host} variable chaining."""
    if step.get("tool") == "scan" and isinstance(result, dict):
        hosts = result.get("hosts")
        if isinstance(hosts, list) and hosts:
            first = hosts[0].get("ip") if isinstance(hosts[0], dict) else None
            if first:
                resolved_vars["first_host"] = first
