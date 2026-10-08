"""quantum.ai.openfable — OpenFable agent-runner integration.

OpenFable (https://github.com/OpenFable, built from ``C:\\Projects\\OpenFable``)
is a local OpenCode-compatible agent runner with three front ends this
module drives so the dashboard can offer a real terminal session **or** a
GUI chat widget:

* terminal — ``openfable [project]`` TUI launched in a new console window
  (``CREATE_NEW_CONSOLE`` on Windows), or one-shot ``openfable run``
* GUI chat — headless ``openfable serve`` (Hono REST server) + REST chat

REST contract (verified against OpenFable ``0.0.0-prod`` sources at
``packages/opencode/src/server``):

* ``GET  /global/health`` -> ``{healthy: true, version}``
* ``POST /session`` -> create (optional ``{title}``); ``GET /session`` list
* ``POST /session/:id/message`` blocking chat, body
  ``{parts:[{type:"text",text}], model:{providerID,modelID}}``
* ``POST /session/:id/prompt_async`` -> 204 (non-blocking); completion is
  observed via ``GET /session/status`` -> ``{id: {type: idle|busy|retry}}``
  then ``GET /session/:id/message`` (MessageV2.WithParts: ``info.role`` +
  ``parts[]``)
* ``POST /session/:id/abort`` stops a running turn
* ``GET  /provider`` returns the connected-provider registry (huge; cached)
* auth: basic ``username:password`` when ``OPENFABLE_SERVER_PASSWORD`` is
  set (username ``OPENFABLE_SERVER_USERNAME`` or ``openfable``)

Known boundary: the default ``opencode`` provider's free tier 403s from
outside OpenCode — the chat exposes a model picker so the operator picks a
provider that works (e.g. a hosted key or a local model). Honest errors are
surfaced, never faked.

Authorized engagements only.
"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
import time

DEFAULT_PORT = 14096
_BUSY = ("busy", "retry")

# headless-server state (only ever our own process / adopted URL)
_SERVER = {"pid": None, "port": None, "url": None, "started": None,
           "owned": False, "project": None, "error": None}
_VERSION_CACHE = {"path": None, "version": None}
_MODELS_CACHE = {"models": None, "fetched": 0.0}


# ------------------------------------------------------------------ install
def find_openfable(env=None):
    """Locate the openfable binary (env override, PATH, install globs)."""
    env = os.environ if env is None else env
    cand = env.get("QCLI_OPENFABLE") or ""
    if cand and os.path.isfile(cand):
        return cand
    for name in ("openfable", "openfable.exe"):
        hit = shutil.which(name)
        if hit:
            return hit
    roots = [env.get("QCLI_OPENFABLE_HOME") or "",
             r"C:\Projects\OpenFable",
             os.path.join(os.path.expanduser("~"), "OpenFable"),
             "/opt/openfable", "/usr/local/lib/openfable"]
    patterns = [os.path.join("packages", "opencode", "dist", "*", "bin",
                             "openfable*"),
                os.path.join("dist", "*", "bin", "openfable*"),
                os.path.join("bin", "openfable*")]
    for root in roots:
        if not root:
            continue
        for pat in patterns:
            for hit in sorted(glob.glob(os.path.join(root, pat))):
                if os.path.isfile(hit) and \
                        os.path.basename(hit).startswith("openfable"):
                    return hit
    return None


def openfable_version(exe, timeout=10):
    """``openfable --version`` (cached; None when the build has no flag)."""
    if not exe:
        return None
    if _VERSION_CACHE["path"] == exe and _VERSION_CACHE["version"]:
        return _VERSION_CACHE["version"]
    try:
        proc = subprocess.run([exe, "--version"], capture_output=True,
                              text=True, timeout=timeout, encoding="utf-8",
                              errors="replace")
        out = (proc.stdout or proc.stderr or "").strip().splitlines()
        ver = out[0].strip() if proc.returncode == 0 and out else None
    except (OSError, subprocess.SubprocessError):
        ver = None
    _VERSION_CACHE.update(path=exe, version=ver)
    return ver


# ------------------------------------------------------------ CLI builders
def serve_command(exe, port=DEFAULT_PORT, hostname="127.0.0.1",
                  extra=None):
    """Real ``openfable serve`` argv (network flags from cli/network.ts)."""
    cmd = [exe, "serve", "--port", str(int(port)),
           "--hostname", str(hostname)]
    return cmd + list(extra or [])


def run_command(exe, message, model=None, attach=None, fmt="json",
                port=None, session=None, extra=None):
    """Real ``openfable run`` argv (cli/cmd/run.ts flags)."""
    cmd = [exe, "run", str(message or "")]
    if model:
        cmd += ["--model", str(model)]
    if attach:
        cmd += ["--attach", str(attach)]
    if port is not None:
        cmd += ["--port", str(int(port))]
    if session:
        cmd += ["--session", str(session)]
    if fmt:
        cmd += ["--format", str(fmt)]
    return cmd + list(extra or [])


def tui_command(exe, project=None, model=None, extra=None):
    """Real interactive TUI argv (default command = ``openfable``)."""
    cmd = [exe]
    if project:
        cmd.append(str(project))
    if model:
        cmd += ["--model", str(model)]
    return cmd + list(extra or [])


# ------------------------------------------------------------------ HTTP
def _base_url(env=None, probe=True):
    """URL of our tracked server, or an externally running local one."""
    if _SERVER["url"]:
        return _SERVER["url"]
    if not probe:
        return None
    for port in (DEFAULT_PORT,):
        got = server_health(f"http://127.0.0.1:{port}", timeout=1.5)
        if got.get("healthy"):
            return f"http://127.0.0.1:{port}"
    return None


def _auth_headers(env=None):
    """Basic-auth header when OPENFABLE_SERVER_PASSWORD is set."""
    env = os.environ if env is None else env
    pw = env.get("OPENFABLE_SERVER_PASSWORD") or ""
    if not pw:
        return {}
    import base64
    user = env.get("OPENFABLE_SERVER_USERNAME") or "openfable"
    tok = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {tok}"}


def _http(method, url, payload=None, timeout=15, env=None):
    """One REST call; returns {ok, status, data|error} (never raises)."""
    from quantum.core.deps import requests
    if requests is None:
        return {"ok": False, "status": 0,
                "error": "requests library not installed"}
    try:
        kwargs = {"timeout": timeout, "headers": _auth_headers(env)}
        if payload is not None:
            kwargs["json"] = payload
        if method == "POST":
            r = requests.post(url, **kwargs)
        else:
            r = requests.get(url, **kwargs)
        out = {"ok": r.status_code < 400, "status": r.status_code}
        try:
            out["data"] = r.json()
        except ValueError:
            out["data"] = r.text[:4000]
        if r.status_code >= 400:
            out["error"] = f"HTTP {r.status_code}: " + str(out.get("data"))[:500]
        return out
    except Exception as exc:  # noqa: BLE001 — honest transport error
        return {"ok": False, "status": 0, "error": str(exc)}


# ------------------------------------------------------- server lifecycle
def server_health(base=None, timeout=3):
    """GET /global/health -> {healthy, version} (or honest error)."""
    base = base or _SERVER["url"] or _base_url(probe=False)
    if not base:
        return {"healthy": False, "error": "no server url"}
    got = _http("GET", f"{base}/global/health", timeout=timeout)
    if got.get("ok") and isinstance(got.get("data"), dict):
        data = got["data"]
        return {"healthy": bool(data.get("healthy")),
                "version": data.get("version"), "url": base}
    return {"healthy": False, "url": base,
            "error": got.get("error", "unreachable")}


def start_server(port=DEFAULT_PORT, project=None, wait=30, env=None):
    """Launch headless ``openfable serve`` detached and health-poll it."""
    env = os.environ if env is None else env
    exe = find_openfable(env)
    if not exe:
        return {"started": False, "error":
                "openfable binary not found (set QCLI_OPENFABLE)"}
    url = f"http://127.0.0.1:{int(port)}"
    live = server_health(url, timeout=2)
    if live.get("healthy"):
        _SERVER.update(pid=_SERVER["pid"], port=int(port), url=url,
                       owned=_SERVER["owned"] or False, error=None)
        return {"started": True, "already": True, "url": url,
                "version": live.get("version")}
    try:
        flags = 0
        if os.name == "nt":
            flags = getattr(subprocess, "DETACHED_PROCESS", 0x08) | \
                getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200)
            proc = subprocess.Popen(
                serve_command(exe, port), stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=flags, cwd=project or None)
        else:
            proc = subprocess.Popen(
                serve_command(exe, port), stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True, cwd=project or None)
    except OSError as exc:
        return {"started": False, "error": f"spawn failed: {exc}"}
    _SERVER.update(pid=proc.pid, port=int(port), url=url, owned=True,
                   started=time.time(), project=project, error=None)
    deadline = time.time() + wait
    while time.time() < deadline:
        live = server_health(url, timeout=2)
        if live.get("healthy"):
            from quantum.core.logging import log
            log(f"OPENFABLE server up on {url} (pid {proc.pid})",
                "OPENFABLE")
            return {"started": True, "url": url, "pid": proc.pid,
                    "version": live.get("version")}
        if proc.poll() is not None:
            _SERVER.update(pid=None, owned=False,
                           error=f"serve exited rc={proc.returncode}")
            return {"started": False, "error":
                    f"serve exited rc={proc.returncode}"}
        time.sleep(0.5)
    _SERVER["error"] = f"not healthy within {wait}s"
    return {"started": False, "url": url, "pid": proc.pid,
            "error": f"server did not become healthy within {wait}s"}


def stop_server():
    """Stop the headless server we started (never an adopted one)."""
    pid, url, owned = _SERVER["pid"], _SERVER["url"], _SERVER["owned"]
    if not pid:
        _SERVER.update(pid=None, owned=False, url=None, port=None,
                       started=None)
        return {"stopped": False, "error": "no server started by this "
                "instance (adopted/external servers are left running)"}
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, timeout=10)
        else:
            import signal
            os.kill(pid, signal.SIGTERM)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"stopped": False, "pid": pid, "error": str(exc)}
    _SERVER.update(pid=None, owned=False, url=None, port=None,
                   started=None, error=None)
    from quantum.core.logging import log
    log(f"OPENFABLE server stopped (pid {pid} was={url})", "OPENFABLE")
    return {"stopped": True, "pid": pid, "was": url}


# --------------------------------------------------------------- sessions
def list_sessions(base=None, env=None, timeout=10):
    """GET /session -> session list (id/title/time), or honest error."""
    base = base or _base_url(env)
    if not base:
        return {"error": "server not running", "sessions": []}
    got = _http("GET", f"{base}/session", timeout=timeout, env=env)
    if not got.get("ok"):
        return {"error": got.get("error", "list failed"), "sessions": []}
    data = got.get("data")
    return {"sessions": data if isinstance(data, list) else []}


def create_session(title=None, base=None, env=None, timeout=15):
    """POST /session (CreateInput: optional {title}); returns session id."""
    base = base or _base_url(env)
    if not base:
        return {"error": "server not running"}
    body = {"title": title} if title else {}
    got = _http("POST", f"{base}/session", body, timeout=timeout, env=env)
    if not got.get("ok"):
        return {"error": got.get("error", "create failed")}
    data = got.get("data") or {}
    sid = data.get("id") or data.get("sessionID")
    if not sid:
        return {"error": f"no session id in response: {str(data)[:300]}"}
    return {"session_id": sid, "title": data.get("title"),
            "session": data}


def get_messages(session_id, base=None, env=None, limit=None, timeout=15):
    """GET /session/:id/message (MessageV2.WithParts[])."""
    base = base or _base_url(env)
    if not base:
        return {"error": "server not running", "messages": []}
    url = f"{base}/session/{session_id}/message"
    if limit:
        url += f"?limit={int(limit)}"
    got = _http("GET", url, timeout=timeout, env=env)
    if not got.get("ok"):
        return {"error": got.get("error", "fetch failed"), "messages": []}
    data = got.get("data")
    return {"messages": data if isinstance(data, list) else []}


def session_status(base=None, env=None, timeout=6):
    """GET /session/status -> {id: {type: idle|busy|retry, ...}}."""
    base = base or _base_url(env)
    if not base:
        return {"error": "server not running", "status": {}}
    got = _http("GET", f"{base}/session/status", timeout=timeout, env=env)
    if not got.get("ok"):
        return {"error": got.get("error", "status failed"), "status": {}}
    data = got.get("data")
    return {"status": data if isinstance(data, dict) else {}}


def abort_session(session_id, base=None, env=None, timeout=10):
    """POST /session/:id/abort — stop a running turn."""
    base = base or _base_url(env)
    if not base:
        return {"error": "server not running"}
    got = _http("POST", f"{base}/session/{session_id}/abort", {},
                timeout=timeout, env=env)
    if not got.get("ok"):
        return {"error": got.get("error", "abort failed")}
    return {"aborted": True, "session_id": session_id}


def _message_text(msg):
    """Flatten one MessageV2.WithParts into {id, role, text}."""
    info = msg.get("info") or {}
    texts = []
    for part in msg.get("parts") or []:
        if isinstance(part, dict) and part.get("type") == "text" and \
                part.get("text"):
            texts.append(part["text"])
        elif isinstance(part, dict) and part.get("type") == "reasoning" and \
                part.get("text"):
            texts.append(f"[thinking] {part['text']}")
    return {"id": info.get("id"), "role": info.get("role"),
            "text": "\n".join(texts)}


def prompt_async(session_id, text, model=None, agent=None, base=None,
                 env=None, timeout=20):
    """POST /session/:id/prompt_async (204 = accepted; returns immediately)."""
    base = base or _base_url(env)
    if not base:
        return {"error": "server not running"}
    if not session_id or not text:
        return {"error": "session_id + text required"}
    body = {"parts": [{"type": "text", "text": str(text)}]}
    if model and "/" in str(model):
        prov, mid = str(model).split("/", 1)
        body["model"] = {"providerID": prov, "modelID": mid}
    if agent:
        body["agent"] = str(agent)
    got = _http("POST", f"{base}/session/{session_id}/prompt_async", body,
                timeout=timeout, env=env)
    if not got.get("ok"):
        return {"error": got.get("error", "prompt rejected"),
                "status": got.get("status")}
    return {"accepted": True, "session_id": session_id,
            "model": model, "status": got.get("status")}


def chat(session_id, text, model=None, agent=None, timeout=120, poll=0.35,
         base=None, env=None):
    """Async chat: prompt_async + poll status until idle, then read reply.

    Completion is ``status[id].type == "idle"`` after it has been
    ``busy``/``retry`` (or after a grace period for instant replies); the
    assistant message(s) appended since the baseline are returned. A
    timeout is reported as a timeout — never invented output.
    """
    started = time.time()
    base = base or _base_url(env)
    if not base:
        return {"error": "server not running"}
    before = {m.get("info", {}).get("id")
              for m in get_messages(session_id, base=base, env=env)
              .get("messages", [])}
    ack = prompt_async(session_id, text, model=model, agent=agent,
                       base=base, env=env)
    if not ack.get("accepted"):
        return ack
    seen_busy = False
    last = None
    while time.time() - started < timeout:
        time.sleep(poll)
        st = session_status(base=base, env=env).get("status", {})
        typ = (st.get(session_id) or {}).get("type")
        last = typ
        if typ in _BUSY:
            seen_busy = True
            continue
        elapsed = time.time() - started
        if typ == "idle" and (seen_busy or elapsed >= 1.0):
            msgs = get_messages(session_id, base=base,
                                env=env).get("messages", [])
            fresh = [_message_text(m) for m in msgs
                     if m.get("info", {}).get("id") not in before]
            reply = next((m["text"] for m in reversed(fresh)
                          if m["role"] == "assistant" and m["text"]), "")
            if reply or seen_busy:
                out = {"session_id": session_id, "model": model,
                       "reply": reply,
                       "messages": [m for m in fresh if m["text"]],
                       "elapsed_s": round(elapsed, 2)}
                if not reply:
                    out["warning"] = ("turn finished with no assistant "
                                      "reply (provider error?) — check "
                                      "the session messages")
                return out
    return {"error": f"timeout after {timeout}s waiting for reply",
            "timeout": True, "session_id": session_id,
            "last_status": last, "elapsed_s": round(time.time() - started,
                                                    2),
            "messages": [_message_text(m)
                         for m in get_messages(session_id, base=base,
                                               env=env).get("messages", [])
                         if m.get("info", {}).get("id") not in before]}


def chat_sync(session_id, text, model=None, agent=None, timeout=90,
              base=None, env=None):
    """Blocking chat: POST /session/:id/message (server waits for reply)."""
    base = base or _base_url(env)
    if not base:
        return {"error": "server not running"}
    if not session_id or not text:
        return {"error": "session_id + text required"}
    body = {"parts": [{"type": "text", "text": str(text)}]}
    if model and "/" in str(model):
        prov, mid = str(model).split("/", 1)
        body["model"] = {"providerID": prov, "modelID": mid}
    if agent:
        body["agent"] = str(agent)
    started = time.time()
    got = _http("POST", f"{base}/session/{session_id}/message", body,
                timeout=timeout, env=env)
    if not got.get("ok"):
        return {"error": got.get("error", "chat failed"),
                "status": got.get("status"),
                "elapsed_s": round(time.time() - started, 2)}
    data = got.get("data")
    out = {"session_id": session_id, "model": model,
           "elapsed_s": round(time.time() - started, 2)}
    if isinstance(data, dict):
        out["reply"] = _message_text(data).get("text") or ""
        out["message"] = data
    elif isinstance(data, list):
        fresh = [_message_text(m) for m in data]
        out["reply"] = next((m["text"] for m in reversed(fresh)
                             if m["role"] == "assistant" and m["text"]), "")
        out["messages"] = [m for m in fresh if m["text"]]
    else:
        out["data"] = data
    return out


# ------------------------------------------------------------ model picker
def parse_providers(payload):
    """Flatten GET /provider into [{provider, model, label, ...}] entries.

    Handles the registry shapes OpenFable serves (dict of provider ->
    {models: dict|list}, a bare list of providers, or a {providers: [...]}
    wrapper) without inventing entries.
    """
    out = []
    entries = []
    if isinstance(payload, dict):
        if isinstance(payload.get("providers"), list):
            entries = [(p.get("id"), p) for p in payload["providers"]
                       if isinstance(p, dict)]
        else:
            entries = list(payload.items())
    elif isinstance(payload, list):
        entries = [(p.get("id"), p) for p in payload if isinstance(p, dict)]
    for pid, prov in entries:
        if not isinstance(prov, dict):
            continue
        pid = prov.get("id") or pid or "?"
        models = prov.get("models") or {}
        if isinstance(models, dict):
            mlist = list(models.values())
        elif isinstance(models, list):
            mlist = models
        else:
            mlist = []
        for m in mlist:
            if isinstance(m, str):
                out.append({"provider": pid, "model": m,
                            "label": f"{pid}/{m}"})
                continue
            if not isinstance(m, dict):
                continue
            mid = m.get("id")
            if not mid:
                continue
            limit = m.get("limit") or {}
            cost = m.get("cost") or {}
            out.append({"provider": pid, "model": mid,
                        "label": m.get("name") or f"{pid}/{mid}",
                        "id": f"{pid}/{mid}",
                        "context": limit.get("context"),
                        "cost_input": cost.get("input"),
                        "reasoning": bool(m.get("reasoning")),
                        "tool_call": bool(m.get("tool_call"))})
    return out


def get_models(base=None, env=None, refresh=False, ttl=300, timeout=60):
    """GET /provider -> cached model picker list (payload is large)."""
    now = time.time()
    if not refresh and _MODELS_CACHE["models"] is not None and \
            now - _MODELS_CACHE["fetched"] < ttl:
        models = _MODELS_CACHE["models"]
        return {"models": models, "count": len(models),
                "cached": True, "fetched": _MODELS_CACHE["fetched"]}
    base = base or _base_url(env)
    if not base:
        return {"error": "server not running", "models": []}
    got = _http("GET", f"{base}/provider", timeout=timeout, env=env)
    if not got.get("ok"):
        return {"error": got.get("error", "provider list failed"),
                "models": []}
    models = parse_providers(got.get("data"))
    _MODELS_CACHE.update(models=models, fetched=now)
    return {"models": models, "count": len(models), "cached": False,
            "fetched": now}


# ------------------------------------------------------ terminal front ends
def launch_tui(project=None, model=None, env=None):
    """Open the interactive OpenFable TUI in a new console window.

    Windows: ``CREATE_NEW_CONSOLE`` gives a real terminal window. POSIX:
    a terminal emulator (x-terminal-emulator/gnome-terminal/xterm) when
    one exists, otherwise the exact command is returned for the operator
    to run — no fake launch.
    """
    env = os.environ if env is None else env
    exe = find_openfable(env)
    if not exe:
        return {"launched": False, "error":
                "openfable binary not found (set QCLI_OPENFABLE)"}
    cmd = tui_command(exe, project=project, model=model)
    try:
        if os.name == "nt":
            proc = subprocess.Popen(
                cmd, cwd=project or None, close_fds=True,
                creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE",
                                      0x10))
            return {"launched": True, "pid": proc.pid, "command": cmd,
                    "mode": "terminal"}
        for term, build in (
                ("x-terminal-emulator", lambda c: c),
                ("gnome-terminal", lambda c: ["gnome-terminal", "--"] + c),
                ("xterm", lambda c: ["xterm", "-e"] + c)):
            if shutil.which(term):
                proc = subprocess.Popen(build(cmd), cwd=project or None,
                                        start_new_session=True)
                return {"launched": True, "pid": proc.pid,
                        "command": cmd, "mode": "terminal",
                        "emulator": term}
        return {"launched": False, "command": cmd, "mode": "terminal",
                "error": "no terminal emulator found — run: " +
                " ".join(cmd)}
    except OSError as exc:
        return {"launched": False, "command": cmd, "error": str(exc)}


def run_once(message, model=None, timeout=180, project=None, env=None,
             attach=None):
    """One-shot ``openfable run "<message>"`` (real subprocess, real out)."""
    env = os.environ if env is None else env
    exe = find_openfable(env)
    if not exe:
        return {"ok": False, "error":
                "openfable binary not found (set QCLI_OPENFABLE)"}
    if not message:
        return {"ok": False, "error": "message required"}
    cmd = run_command(exe, message, model=model, attach=attach)
    started = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, cwd=project or None,
                              encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"run timed out after {timeout}s",
                "command": cmd}
    except OSError as exc:
        return {"ok": False, "error": str(exc), "command": cmd}
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    return {"ok": proc.returncode == 0, "exit": proc.returncode,
            "output": out[-8000:], "stderr": err[-2000:] if err else "",
            "command": cmd, "elapsed_s": round(time.time() - started, 2)}


# ------------------------------------------------------------ dash state
def openfable_dashboard_state(env=None):
    """Webcard state for the OpenFable widget (install + server + modes)."""
    env = os.environ if env is None else env
    exe = find_openfable(env)
    base = _base_url(env)
    health = server_health(base, timeout=1.5) if base else {
        "healthy": False, "error": "server not running"}
    cached = _MODELS_CACHE["models"]
    return {
        "found": bool(exe),
        "path": exe,
        "version": openfable_version(exe) or health.get("version"),
        "server": {
            "running": bool(health.get("healthy")),
            "url": health.get("url") or _SERVER["url"],
            "pid": _SERVER["pid"],
            "owned": _SERVER["owned"],
            "port": _SERVER["port"] or DEFAULT_PORT,
            "version": health.get("version"),
            "error": health.get("error") if not health.get("healthy")
            else None,
        },
        "sessions": list_sessions(env=env).get("sessions", []),
        "models_cached": len(cached) if cached else 0,
        "modes": [
            {"id": "terminal", "label": "Terminal (OpenFable TUI)",
             "how": "launches openfable in a new console window"},
            {"id": "gui", "label": "GUI chat widget",
             "how": "headless serve + REST chat with model picker"},
        ],
        "prompt": "OpenFable is available — how do you want to work "
                  "with it?",
        "endpoints": ["/global/health", "/session", "/session/:id/message",
                      "/session/:id/prompt_async", "/session/:id/abort",
                      "/session/status", "/provider", "/event (SSE)"],
        "note": "Both modes drive the real openfable binary (TUI or "
                "headless REST server); pick a working model — the "
                "opencode free tier 403s outside OpenCode. Authorized "
                "engagements only.",
    }
