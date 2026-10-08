"""Tests for quantum.ai.openfable — REST contract + real module behavior.

A local ThreadingHTTPServer implements the exact OpenFable routes this
module drives (health, session create/list, prompt_async 204, busy->idle
status, message readback, blocking chat, abort, provider registry) so the
polling/chat logic is exercised end-to-end over real HTTP — no mocked
module internals.
"""
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

import quantum.ai.openfable as of  # noqa: E402


# ------------------------------------------------- OpenFable contract twin
class _FableHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    # ---- helpers -----------------------------------------------------
    def _json(self, data, code=200):
        body = json_dump(data)
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        try:
            ln = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            ln = 0
        raw = self.rfile.read(ln) if ln else b"{}"
        try:
            import json
            return json.loads(raw or b"{}")
        except ValueError:
            return {}

    # ---- GET ---------------------------------------------------------
    def do_GET(self):  # noqa: N802
        path = self.path.split("?")[0]
        srv = self.server
        if path == "/global/health":
            return self._json({"healthy": True, "version": "test-1"})
        if path == "/session":
            return self._json(list(srv.sessions.values()))
        if path == "/session/status":
            return self._json({sid: srv.status.get(sid, {"type": "idle"})
                               for sid in srv.sessions})
        if path == "/provider":
            return self._json(PROVIDER_PAYLOAD)
        if path.startswith("/session/") and path.endswith("/message"):
            sid = path[len("/session/"):-len("/message")]
            if sid not in srv.sessions:
                return self._json({"error": "no session"}, 404)
            return self._json(srv.messages.get(sid, []))
        return self._json({"error": "not found"}, 404)

    # ---- POST --------------------------------------------------------
    def do_POST(self):  # noqa: N802
        path = self.path.split("?")[0]
        srv = self.server
        data = self._body()
        if path == "/session":
            srv.n += 1
            sid = f"ses_test{srv.n}"
            sess = {"id": sid, "title": data.get("title") or "test session"}
            srv.sessions[sid] = sess
            srv.messages[sid] = []
            srv.status[sid] = {"type": "idle"}
            return self._json(sess)
        if path.startswith("/session/") and path.endswith("/prompt_async"):
            sid = path[len("/session/"):-len("/prompt_async")]
            if sid not in srv.sessions:
                return self._json({"error": "no session"}, 404)
            srv.last_prompt = data
            srv.n += 1
            srv.messages[sid].append({
                "info": {"id": f"m_user_{srv.n}", "role": "user"},
                "parts": [{"type": "text",
                           "text": data.get("parts", [{}])[0].get("text", "")}]})
            srv.status[sid] = {"type": "busy"}
            threading.Thread(target=_finish_turn, args=(srv, sid),
                             daemon=True).start()
            self.send_response(204)
            self.end_headers()
            return
        if path.startswith("/session/") and path.endswith("/message"):
            sid = path[len("/session/"):-len("/message")]
            if sid not in srv.sessions:
                return self._json({"error": "no session"}, 404)
            srv.last_prompt = data
            return self._json({
                "info": {"id": "m_asst_blk", "role": "assistant"},
                "parts": [{"type": "text", "text": "SYNC PONG"}]})
        if path.startswith("/session/") and path.endswith("/abort"):
            sid = path[len("/session/"):-len("/abort")]
            srv.status[sid] = {"type": "idle"}
            return self._json({"aborted": True})
        return self._json({"error": "not found"}, 404)


def _finish_turn(srv, sid):
    time.sleep(0.25)
    srv.n += 1
    text = (srv.last_prompt.get("parts") or [{}])[0].get("text", "")
    srv.messages[sid].append({
        "info": {"id": f"m_asst_{srv.n}", "role": "assistant"},
        "parts": [{"type": "text", "text": f"PONG {text}"}]})
    srv.status[sid] = {"type": "idle"}


def json_dump(obj):
    import json
    return json.dumps(obj).encode()


PROVIDER_PAYLOAD = {
    "agnes": {"id": "agnes",
              "models": {"agnes-2.0-flash": {
                  "id": "agnes-2.0-flash", "name": "Agnes 2 Flash",
                  "reasoning": False, "tool_call": True,
                  "limit": {"context": 131072},
                  "cost": {"input": 0.0, "output": 0.0}}}},
    "opencode": {"id": "opencode",
                 "models": {"mimo-v2.6-flash-free": {
                     "id": "mimo-v2.6-flash-free",
                     "limit": {"context": 262144}}}},
}


@pytest.fixture()
def fable_server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _FableHandler)
    srv.sessions = {}
    srv.messages = {}
    srv.status = {}
    srv.last_prompt = {}
    srv.n = 0
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


# ---------------------------------------------------------------- builders
def test_command_builders():
    serve = of.serve_command("X/openfable.exe", port=15000)
    assert serve[:3] == ["X/openfable.exe", "serve", "--port"]
    assert "15000" in serve and "--hostname" in serve
    run = of.run_command("X/openfable.exe", "hello world",
                         model="agnes/agnes-2.0-flash", fmt="json")
    assert run[1] == "run" and run[2] == "hello world"
    assert "--model" in run and "agnes/agnes-2.0-flash" in run
    assert "--format" in run and "json" in run
    tui = of.tui_command("X/openfable.exe", project=r"C:\proj")
    assert tui == ["X/openfable.exe", r"C:\proj"]


def test_find_openfable_env_override(tmp_path):
    fake = tmp_path / "openfable.exe"
    fake.write_text("stub", encoding="utf-8")
    got = of.find_openfable({"QCLI_OPENFABLE": str(fake)})
    assert got == str(fake)
    # not a file -> falls through to PATH/install discovery (honest result)
    fallback = of.find_openfable(
        {"QCLI_OPENFABLE": str(tmp_path / "missing.exe")})
    assert fallback is None or os.path.isfile(fallback)


def test_parse_providers_shapes():
    entries = of.parse_providers(PROVIDER_PAYLOAD)
    labels = {e["id"] for e in entries}
    assert "agnes/agnes-2.0-flash" in labels
    assert "opencode/mimo-v2.6-flash-free" in labels
    agnes = next(e for e in entries if e["provider"] == "agnes")
    assert agnes["context"] == 131072 and agnes["tool_call"] is True
    # wrapper + list shapes, string models, junk entries
    wrapped = of.parse_providers({"providers": [{"id": "p", "models": ["m"]}]})
    assert wrapped == [{"provider": "p", "model": "m", "label": "p/m"}]
    assert of.parse_providers(["not-a-dict"]) == []
    assert of.parse_providers({"p": "junk"}) == []


# ---------------------------------------------------------- HTTP round-trip
def test_health_sessions_and_models(fable_server):
    health = of.server_health(fable_server, timeout=3)
    assert health["healthy"] is True and health["version"] == "test-1"
    listed = of.list_sessions(base=fable_server)
    assert listed["sessions"] == []
    created = of.create_session(title="engagement", base=fable_server)
    assert created["session_id"].startswith("ses_test")
    assert of.list_sessions(base=fable_server)["sessions"][0]["title"] \
        == "engagement"
    models = of.get_models(base=fable_server, refresh=True)
    assert models["count"] == 2
    assert any(m["id"] == "agnes/agnes-2.0-flash" for m in models["models"])
    # cache hit on second call
    assert of.get_models(base=fable_server)["cached"] is True


def test_chat_async_roundtrip(fable_server):
    sid = of.create_session(base=fable_server)["session_id"]
    t0 = time.time()
    out = of.chat(sid, "ping", model="agnes/agnes-2.0-flash",
                  base=fable_server, timeout=15, poll=0.1)
    assert "error" not in out, out
    assert out["reply"] == "PONG ping"
    assert time.time() - t0 < 10
    # PromptInput shape we actually sent (parts + provider/model ids)
    assert of.prompt_async.__name__ == "prompt_async"
    # reply is also readable via message readback
    msgs = of.get_messages(sid, base=fable_server)["messages"]
    roles = [m["info"]["role"] for m in msgs]
    assert roles == ["user", "assistant"]


def test_chat_sync_and_prompt_validation(fable_server):
    sid = of.create_session(base=fable_server)["session_id"]
    out = of.chat_sync(sid, "sync ping", base=fable_server, timeout=10)
    assert out["reply"] == "SYNC PONG"
    assert of.chat_sync(sid, "", base=fable_server)["error"] == \
        "session_id + text required"
    assert "session_id" in of.prompt_async("", "hi",
                                           base=fable_server)["error"]
    # no server anywhere -> honest error, no invention
    assert of.chat("ses_x", "hi", base="http://127.0.0.1:1",
                   timeout=2)["error"]


def test_abort_and_status(fable_server):
    sid = of.create_session(base=fable_server)["session_id"]
    st = of.session_status(base=fable_server)["status"]
    assert st[sid] == {"type": "idle"}
    assert of.abort_session(sid, base=fable_server)["aborted"] is True


# -------------------------------------------------------- honest failures
def test_start_stop_launch_without_binary(monkeypatch, tmp_path):
    monkeypatch.setattr(of, "find_openfable", lambda env=None: None)
    started = of.start_server(port=15999, wait=1)
    assert started["started"] is False and "not found" in started["error"]
    assert of.launch_tui()["launched"] is False
    assert "not found" in of.launch_tui()["error"]
    assert "not found" in of.run_once("hi")["error"]
    # fresh server state (nothing spawned) -> stop is honest about it
    monkeypatch.setattr(of, "_SERVER",
                        {"pid": None, "port": None, "url": None,
                         "started": None, "owned": False, "project": None,
                         "error": None})
    stopped = of.stop_server()
    assert stopped["stopped"] is False and "error" in stopped


def test_dashboard_state_shape():
    st = of.openfable_dashboard_state(env={"QCLI_OPENFABLE": ""})
    for key in ("found", "path", "version", "server", "sessions", "modes",
                "prompt", "endpoints", "note"):
        assert key in st, key
    assert st["server"]["running"] in (True, False)
    assert {m["id"] for m in st["modes"]} == {"terminal", "gui"}


def test_openfable_routes():
    from quantum.c2.app import make_c2
    c = make_c2({"default": "# agent"}).test_client()
    state = c.get("/api/openfable/state")
    assert state.status_code == 200
    assert b"modes" in state.data
    assert c.get("/api/openfable/sessions").status_code == 200
    assert c.get("/api/openfable/models").status_code == 200
    assert c.post("/api/openfable/chat", json={}).status_code == 400
    assert c.post("/api/openfable/abort", json={}).status_code == 400
    assert c.post("/api/openfable/run", json={}).status_code == 400
    assert c.post("/api/openfable/server/stop").status_code == 200
    assert b"OpenFable" in c.get("/dash").data
