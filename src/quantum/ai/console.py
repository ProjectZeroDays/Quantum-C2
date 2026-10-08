"""quantum.ai.console — operator management of the AI surface.

CRUD over the real registries (agents, skills,
workflows), the QCLI command surface
(QCLI_API.COMMANDS), and the implant task queue
(TASKQ). Every mutation is journaled to the audit
log (tag CONSOLE) so the dashboard's activity feed
shows real events — nothing is simulated.

Deploy: deploy_agent() records the active operator
agent in agents/active.json (id, role, autonomy,
provider/model, timestamp) and journals the
deployment. The CLI (`agents` command) and the AI
supervisor read the same record.
"""
from __future__ import annotations

import json
import os
import time

from quantum.ai.agents import (AGENTS_DIR, delete as
                                  delete_agent_reg,
                                  get as get_agent_reg,
                                  load_all as load_agents_reg,
                                  presets as agent_presets,
                                  save as save_agent_reg)
from quantum.ai.skills import (delete as delete_skill_reg,
                                  get as get_skill_reg,
                                  load_all as load_skills_reg,
                                  save as save_skill_reg)
from quantum.ai.workflows import (delete as
                                     delete_workflow_reg,
                                     get as get_workflow_reg,
                                     load_all as
                                     load_workflows_reg,
                                     run as run_workflow_reg,
                                     save as
                                     save_workflow_reg)
from quantum.core.logging import log

ACTIVE_DEPLOYMENT = os.path.join(AGENTS_DIR,
                                 "active.json")


# ------------------------------------------------------------------ agents
def list_agents():
    """All agents (persisted first, presets as
    defaults) with the active deployment marked."""
    active = active_deployment()
    agents = load_agents_reg()
    return {"agents": agents,
            "presets": agent_presets(),
            "active": active,
            "count": len(agents)}


def get_agent(agent_id):
    agent = get_agent_reg(agent_id)
    if agent is None:
        return {"error": f"unknown agent: {agent_id}"}
    return agent


def save_agent(agent):
    """Create or update an agent (id required)."""
    if not agent or not agent.get("id"):
        return {"error": "agent.id required"}
    saved = save_agent_reg(agent)
    log(f"CONSOLE agent saved: {saved['id']}",
        "CONSOLE")
    return saved


def delete_agent(agent_id):
    """Delete a persisted agent (presets
    reappear)."""
    existed = delete_agent_reg(agent_id)
    log(f"CONSOLE agent deleted: {agent_id} "
        f"(existed={existed})", "CONSOLE")
    return {"deleted": agent_id,
            "existed": bool(existed)}


def deploy_agent(agent_id):
    """Deploy an agent as the active operator agent.

    Persists the deployment record
    (agents/active.json) and journals it. The agent
    must exist (persisted or preset).
    """
    agent = get_agent_reg(agent_id)
    if agent is None:
        return {"error": f"unknown agent: {agent_id}"}
    record = {
        "agent_id": agent["id"],
        "name": agent.get("name", agent["id"]),
        "role": agent.get("role", "operator"),
        "autonomy": agent.get("autonomy", 0),
        "provider": agent.get("provider", ""),
        "model": agent.get("model", ""),
        "deployed_at": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    os.makedirs(AGENTS_DIR, exist_ok=True)
    with open(ACTIVE_DEPLOYMENT, "w",
              encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
    log(f"CONSOLE agent deployed: {agent_id} "
        f"(role={record['role']})", "CONSOLE")
    return record


def active_deployment():
    """The currently deployed agent record, or
    None when nothing is deployed."""
    if not os.path.isfile(ACTIVE_DEPLOYMENT):
        return None
    try:
        with open(ACTIVE_DEPLOYMENT,
                  encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


# ------------------------------------------------------------------ skills
def list_skills():
    return {"skills": load_skills_reg(),
            "count": len(load_skills_reg())}


def get_skill(skill_id):
    skill = get_skill_reg(skill_id)
    if skill is None:
        return {"error": f"unknown skill: {skill_id}"}
    return skill


def save_skill(skill):
    if not skill or not skill.get("id"):
        return {"error": "skill.id required"}
    saved = save_skill_reg(skill)
    log(f"CONSOLE skill saved: {saved['id']}",
        "CONSOLE")
    return saved


def delete_skill(skill_id):
    existed = delete_skill_reg(skill_id)
    log(f"CONSOLE skill deleted: {skill_id} "
        f"(existed={existed})", "CONSOLE")
    return {"deleted": skill_id,
            "existed": bool(existed)}


# ------------------------------------------------------------------ workflows
def list_workflows():
    flows = load_workflows_reg()
    return {"workflows": flows,
            "count": len(flows)}


def get_workflow(workflow_id):
    flow = get_workflow_reg(workflow_id)
    if flow is None:
        return {"error":
                f"unknown workflow: {workflow_id}"}
    return flow


def save_workflow(workflow):
    if not workflow or not workflow.get("id"):
        return {"error": "workflow.id required"}
    saved = save_workflow_reg(workflow)
    log(f"CONSOLE workflow saved: "
        f"{saved['id']}", "CONSOLE")
    return saved


def delete_workflow(workflow_id):
    existed = delete_workflow_reg(workflow_id)
    log(f"CONSOLE workflow deleted: {workflow_id} "
        f"(existed={existed})", "CONSOLE")
    return {"deleted": workflow_id,
            "existed": bool(existed)}


def run_workflow(workflow_id, variables=None,
                   dispatch=None):
    """Execute a workflow through the real QCLI
    command surface.

    dispatch: callable(cmd, params) -> dict.
    Defaults to a QCLI_API instance (the same
    dispatcher the C2's /ai endpoint uses).
    """
    flow = get_workflow_reg(workflow_id)
    if flow is None:
        return {"error":
                f"unknown workflow: {workflow_id}"}
    if dispatch is None:
        from quantum.c2.app import QCLI_API
        dispatch = QCLI_API().handle
    result = run_workflow_reg(flow, dispatch=dispatch,
                                variables=variables)
    log(f"CONSOLE workflow ran: {workflow_id} "
        f"({len(result.get('journal', []))} steps)",
        "CONSOLE")
    return result


# ------------------------------------------------------------------ commands
def commands():
    """The QCLI /ai command surface."""
    from quantum.c2.app import QCLI_API
    return {"commands": QCLI_API.COMMANDS,
            "count": len(QCLI_API.COMMANDS)}


# ------------------------------------------------------------------ tasks
def task_queue():
    """The implant task queue (host -> task)."""
    from quantum.postexploit.killswitch import TASKQ
    return {"tasks": dict(TASKQ),
            "hosts": len(TASKQ)}


def clear_task(host):
    """Clear the queued task for one host."""
    from quantum.postexploit.killswitch import TASKQ
    if host in TASKQ:
        TASKQ.pop(host, None)
        log(f"CONSOLE task cleared: {host}",
            "CONSOLE")
        return {"cleared": host, "existed": True}
    return {"cleared": host, "existed": False}


# ------------------------------------------------------------------ state
def console_dashboard_state():
    """Webcard state for the console dashboard."""
    return {
        "agents": {"count": len(load_agents_reg()),
                     "presets": len(agent_presets()),
                     "active": active_deployment()},
        "skills": {"count": len(load_skills_reg())},
        "workflows": {"count": len(
            load_workflows_reg())},
        "commands": commands(),
        "tasks": task_queue(),
        "dirs": {"agents": AGENTS_DIR},
    }


def console_recent_events(limit=20):
    """Recent console events from the audit log."""
    from quantum.core.env import LOG_DIR
    from quantum.core.logging import _tail_jsonl
    out = []
    for rec in _tail_jsonl(os.path.join(LOG_DIR,
                                        "audit.jsonl"),
                           200):
        try:
            msg = str(rec.get("msg", ""))
        except AttributeError:
            continue
        if "CONSOLE" in msg:
            out.append(rec)
            if len(out) >= limit:
                break
    return out
