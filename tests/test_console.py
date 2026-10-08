"""Tests for quantum.ai.console + the new C2 dashboard routes."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

import quantum.ai.agents as _agents  # noqa: E402
import quantum.ai.console as console  # noqa: E402
import quantum.ai.skills as _skills  # noqa: E402
import quantum.ai.workflows as _flows  # noqa: E402
from quantum.c2.app import make_c2  # noqa: E402


@pytest.fixture()
def isolated(tmp_path, monkeypatch):
    adir = str(tmp_path / "agents")
    sdir = str(tmp_path / "skills")
    wdir = str(tmp_path / "workflows")
    monkeypatch.setattr(_agents, "AGENTS_DIR", adir)
    monkeypatch.setattr(_skills, "SKILLS_DIR", sdir)
    monkeypatch.setattr(_flows, "WORKFLOWS_DIR", wdir)
    monkeypatch.setattr(console, "AGENTS_DIR", adir)
    monkeypatch.setattr(console, "ACTIVE_DEPLOYMENT",
                        os.path.join(adir, "active.json"))
    return tmp_path


def _client():
    return make_c2({"default": "# agent"}).test_client()


def test_console_agent_crud_deploy(isolated):
    agent = console.save_agent({"id": "t-op", "name": "T",
                                "role": "operator"})
    assert agent["id"] == "t-op"
    assert console.get_agent("t-op")["name"] == "T"
    dep = console.deploy_agent("t-op")
    assert dep["agent_id"] == "t-op"
    assert console.active_deployment()["agent_id"] == "t-op"
    assert console.delete_agent("t-op")["existed"] is True
    assert "error" in console.get_agent("t-op")


def test_console_skill_workflow_crud(isolated):
    assert console.save_skill({"id": "t-sk", "name": "S"})["id"] == "t-sk"
    assert console.get_skill("t-sk")["name"] == "S"
    flow = console.save_workflow({"id": "t-wf", "name": "W",
                                  "steps": []})
    assert flow["id"] == "t-wf"
    res = console.run_workflow("t-wf", dispatch=lambda c, p: {"ok": True})
    assert res["journal"] == []
    assert console.delete_skill("t-sk")["existed"] is True
    assert console.delete_workflow("t-wf")["existed"] is True
    assert "error" in console.run_workflow("nope")


def test_console_state_and_tasks(isolated):
    from quantum.postexploit.killswitch import TASKQ
    st = console.console_dashboard_state()
    assert {"agents", "skills", "workflows", "commands", "tasks"} <= \
        set(st)
    assert st["commands"]["count"] == 13
    # TASKQ is process-global (other suites enqueue hosts) —
    # assert shape, not emptiness.
    tq = console.task_queue()
    assert tq["hosts"] == len(TASKQ) == len(tq["tasks"])
    assert console.clear_task("ghost") == {"cleared": "ghost",
                                           "existed": False}


def test_routes_vendors_and_crack_state():
    c = _client()
    assert c.get("/api/osint/intelx/state").status_code == 200
    assert c.get("/api/osint/shadowdragon/state").status_code == 200
    assert c.get("/api/osint/darkowl/state").status_code == 200
    assert c.get("/api/osint/intelx/tools").status_code == 200
    assert c.get("/api/osint/shadowdragon/matrix").status_code == 200
    assert c.get("/api/osint/shadowdragon/license").status_code == 200
    assert c.get("/api/crack/formats").status_code == 200
    assert c.get("/api/crack/hash/state").status_code == 200
    assert c.get("/api/crack/service/state").status_code == 200
    assert c.get("/api/crack/vault/state").status_code == 200
    assert c.get("/api/crack/state").status_code == 200
    assert c.get("/api/console/state").status_code == 200
    assert c.get("/api/console/commands").status_code == 200
    assert c.get("/api/console/tasks").status_code == 200
    assert b"Crack" in c.get("/dash").data
    assert b"Console" in c.get("/dash").data


def test_route_shadowdragon_plan():
    c = _client()
    r = c.post("/api/osint/shadowdragon/plan",
               json={"subject_type": "email",
                     "subject_value": "a@b.c"})
    assert r.status_code == 200
    assert r.get_json()["subject"]["type"] == "email"


def test_route_hash_crack_and_identify():
    import hashlib
    c = _client()
    h = hashlib.md5(b"secret1").hexdigest()
    r = c.post("/api/crack/hash",
               json={"targets": [h], "wordlist": ["x", "secret1"],
                     "fmt": "md5"})
    assert r.status_code == 200
    assert r.get_json()["hits"][0]["password"] == "secret1"
    r = c.post("/api/crack/hash/identify", json={"hash": h})
    assert "md5" in r.get_json()["formats"]


def test_route_console_crud(isolated):
    c = _client()
    assert c.post("/api/console/agents",
                  json={"id": "r-op", "name": "R"}).status_code == 200
    assert c.get("/api/console/agents/r-op").status_code == 200
    assert c.get("/api/console/agents/nope").status_code == 404
    assert c.post("/api/console/agents/deploy",
                  json={"agent_id": "r-op"}).status_code == 200
    assert c.post("/api/console/agents/deploy",
                  json={}).status_code == 400
    assert c.delete("/api/console/agents/r-op").status_code == 200
    assert c.post("/api/console/workflows",
                  json={"id": "r-wf", "steps": []}).status_code == 200
    assert c.post("/api/console/workflows/r-wf/run",
                  json={}).status_code == 200
    assert c.delete("/api/console/workflows/r-wf").status_code == 200
    assert c.delete("/api/console/tasks/ghost").status_code == 200
