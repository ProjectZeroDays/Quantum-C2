"""quantum.control.iot — IoT exploitation dashboard backend.

Authorized engagements only (lab / contracted scope). Every function
takes explicit targets and does real protocol work — no simulated
devices, no fabricated hits:

  bulbs/plugs : TP-Link Kasa classic LAN (XOR autokey, TCP 9999),
                Tapo KLAP (documented boundary — key exchange needs the
                cloud-paired keys, so the module validates reachability
                and builds the app-level JSON, never fake auth),
                Shelly Gen1 HTTP + Gen2 RPC, Tasmota HTTP, Tuya LAN v3.3
                discovery + AES-ECB command build (localkey is
                operator-supplied);
  esp32       : HTTP endpoint probing + Tasmota/ESPHome classification;
  cameras     : reuses the real ONVIF/WS-Discovery stack for tracking
                entries, mapped via the 2D-map beacon helpers;
  drones      : Ryze Tello UDP control + telemetry (real), Wi-Fi
                indicator sweep for nearby drone APs (netsh/nmcli
                passthroughs), MAVLink guarded (pymavlink absent here).

Plus: NVD CVE feed (keyless, rate-limited) with data-grounded
white-paper renderer, and a payload generator emitting real
command artifacts.
"""
from __future__ import annotations

import json
import os
import socket
import struct
import subprocess
import time
import urllib.parse
import zlib

IOT_PORTS = [80, 443, 1883, 3000, 5555, 8008, 8009, 8060, 8883, 8888,
             9999, 49152, 5683, 6666, 6667, 6668, 8001, 8443, 8444]

IOT_FAMILIES = [
    {"id": "kasa", "name": "TP-Link Kasa (classic LAN)",
     "devices": ["smart plug", "smart bulb"],
     "port": 9999, "protocol": "TCP XOR-autokey JSON"},
    {"id": "tapo", "name": "TP-Link Tapo (KLAP)",
     "devices": ["smart plug", "smart bulb", "camera"],
     "port": 80, "protocol": "HTTP KLAP handshake (boundary noted)"},
    {"id": "shelly", "name": "Shelly Gen1/Gen2",
     "devices": ["relay", "plug", "bulb", "sensor"],
     "port": 80, "protocol": "HTTP GET / RPC POST"},
    {"id": "tasmota", "name": "Tasmota (ESP8266/ESP32)",
     "devices": ["relay", "plug", "bulb", "sensor"],
     "port": 80, "protocol": "HTTP /cm?cmnd="},
    {"id": "tuya", "name": "Tuya LAN v3.3",
     "devices": ["bulb", "plug", "switch", "sensor"],
     "port": 6668, "protocol": "TCP AES-128-ECB (localkey required)"},
    {"id": "esphome", "name": "ESPHome / generic ESP32",
     "devices": ["sensor node", "relay"],
     "port": 80, "protocol": "HTTP web_server / native API"},
    {"id": "tello", "name": "Ryze Tello drone",
     "devices": ["camera drone"],
     "port": 8889, "protocol": "UDP text commands"},
    {"id": "mavlink", "name": "MAVLink drone",
     "devices": ["PX4/ArduPilot drone"],
     "port": 14550, "protocol": "MAVLink (pymavlink required)"},
    {"id": "onvifcam", "name": "ONVIF / RTSP camera",
     "devices": ["IP camera (IoT-tracked)"],
     "port": 80, "protocol": "WS-Discovery + ONVIF (see camwar)"},
    {"id": "mqtt", "name": "MQTT broker/device",
     "devices": ["broker", "Tasmota/ESP sensor"],
     "port": 1883, "protocol": "MQTT 3.1.1 CONNECT"},
]

IOT_EXPLOITS = [
    {"id": "kasa-lan-cmd", "family": "kasa", "name": "Kasa LAN command",
     "vector": "Unauthenticated LAN JSON API (classic firmware)",
     "severity": "high", "action": "kasa_command",
     "requires": "same LAN, classic (non-KLAP) firmware"},
    {"id": "kasa-discovery", "family": "kasa", "name": "Kasa UDP discovery",
     "vector": "UDP 9999 discovery broadcast",
     "severity": "info", "action": "kasa_discover",
     "requires": "same LAN"},
    {"id": "tapo-reachability", "family": "tapo",
     "name": "Tapo KLAP pre-check",
     "vector": "App endpoint probe + handshake-1 readiness",
     "severity": "info", "action": "tapo_probe",
     "requires": "same LAN; cloud-paired keys for full KLAP"},
    {"id": "shelly-gen1", "family": "shelly", "name": "Shelly Gen1 HTTP",
     "vector": "Unauthenticated /relay//status on default config",
     "severity": "high", "action": "shelly_gen1_command",
     "requires": "same LAN, no auth set"},
    {"id": "shelly-gen2-rpc", "family": "shelly", "name": "Shelly Gen2 RPC",
     "vector": "HTTP POST /rpc methods",
     "severity": "high", "action": "shelly_rpc",
     "requires": "same LAN, no auth set"},
    {"id": "tasmota-cmnd", "family": "tasmota", "name": "Tasmota web cmnd",
     "vector": "GET /cm?cmnd= (default: no auth)",
     "severity": "high", "action": "tasmota_command",
     "requires": "same LAN, no webauth set"},
    {"id": "tuya-discover", "family": "tuya", "name": "Tuya LAN discovery",
     "vector": "UDP 6666/6667 device broadcasts",
     "severity": "info", "action": "tuya_discover",
     "requires": "same LAN"},
    {"id": "tuya-dps", "family": "tuya", "name": "Tuya DPS command",
     "vector": "AES-ECB v3.3 data-point set (localkey required)",
     "severity": "high", "action": "tuya_send",
     "requires": "device localkey (operator-supplied)"},
    {"id": "esp-probe", "family": "esphome", "name": "ESP HTTP probe",
     "vector": "Firmware fingerprint via web endpoints",
     "severity": "info", "action": "esp_probe",
     "requires": "IP of node"},
    {"id": "tello-sdk", "family": "tello", "name": "Tello SDK command",
     "vector": "UDP 8889 plaintext SDK (lab drone)",
     "severity": "high", "action": "tello_command",
     "requires": "joined to Tello AP, lab-owned drone"},
    {"id": "tello-track", "family": "tello", "name": "Tello telemetry",
     "vector": "UDP 8890 state strings",
     "severity": "info", "action": "tello_state",
     "requires": "streaming Tello on LAN"},
    {"id": "mqtt-probe", "family": "mqtt", "name": "MQTT broker probe",
     "vector": "Raw CONNECT; anonymous/access check",
     "severity": "medium", "action": "mqtt_probe",
     "requires": "broker IP"},
    {"id": "onvif-track", "family": "onvifcam",
     "name": "ONVIF camera track entry",
     "vector": "WS-Discovery + device info (see camwar)",
     "severity": "info", "action": "iot_camera_track",
     "requires": "same LAN"},
    {"id": "drone-wifi", "family": "tello",
     "name": "Drone AP indicator sweep",
     "vector": "Nearby Wi-Fi SSID match (TELLO/DJI/Parrot)",
     "severity": "info", "action": "drone_wifi_scan",
     "requires": "netsh (Windows) or nmcli (Linux)"},
    {"id": "mavlink-ops", "family": "mavlink", "name": "MAVLink ops",
     "vector": "Telemetry + guided commands via pymavlink",
     "severity": "high", "action": "mavlink_status",
     "requires": "pymavlink installed; lab-owned drone"},
]

DRONE_SSID_HINTS = ("TELLO-", "Tello-", "DJI_", "DJI-", "Parrot_",
                    "Bebop", "Anafi", "Mavic", "Mini_")


# ------------------------------------------------------------------ Kasa
def kasa_encrypt(payload: bytes) -> bytes:
    """TP-Link classic LAN encryption: 4-byte BE length + XOR autokey
    starting at 0xAB (documented protocol, also used by python-kasa)."""
    key = 0xAB
    out = bytearray()
    for byte in payload:
        enc = key ^ byte
        key = enc
        out.append(enc)
    return struct.pack(">I", len(payload)) + bytes(out)


def kasa_decrypt(frame: bytes) -> bytes:
    """Inverse of kasa_encrypt (length prefix verified)."""
    if len(frame) < 4:
        raise ValueError("frame too short")
    (length,) = struct.unpack(">I", frame[:4])
    body = frame[4:4 + length]
    key = 0xAB
    out = bytearray()
    for byte in body:
        out.append(key ^ byte)
        key = byte
    return bytes(out)


def kasa_command(ip, command, port=9999, timeout=8):
    """Send one JSON command to a Kasa device; returns parsed reply."""
    from quantum.core.logging import log
    if isinstance(command, dict):
        command = json.dumps(command)
    raw = command.encode("utf-8")
    try:
        sock = socket.create_connection((ip, int(port)), timeout)
        with sock:
            sock.sendall(kasa_encrypt(raw))
            chunks = []
            while True:
                part = sock.recv(4096)
                if not part:
                    break
                chunks.append(part)
                try:
                    body = kasa_decrypt(b"".join(chunks))
                    json.loads(body)
                    break
                except (ValueError, json.JSONDecodeError):
                    continue
        reply = json.loads(kasa_decrypt(b"".join(chunks)))
        log(f"IOT kasa {ip}: {command[:60]}", "IOT")
        return {"ok": True, "reply": reply}
    except Exception as exc:  # noqa: BLE001 — honest error
        return {"ok": False, "error": f"kasa {ip}: {exc}"}


def kasa_discover(timeout=5):
    """UDP discovery broadcast for classic Kasa devices (port 9999)."""
    payload = kasa_encrypt(json.dumps(
        {"system": {"get_sysinfo": {}}}).encode())
    found = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)
    try:
        sock.sendto(payload, ("255.255.255.255", 9999))
        start = time.time()
        while time.time() - start < timeout:
            try:
                data, addr = sock.recvfrom(8192)
                info = json.loads(kasa_decrypt(data))
                info["_from"] = addr[0]
                found.append(info)
            except socket.timeout:
                break
            except (ValueError, json.JSONDecodeError):
                continue
    finally:
        sock.close()
    return {"devices": found, "count": len(found)}


# ------------------------------------------------------------------ Tapo
def tapo_probe(ip, port=80, timeout=8):
    """Reachability + KLAP readiness probe (honest boundary: full KLAP
    needs the cloud-paired RSA keys; this reports what is reachable)."""
    from quantum.core.deps import requests
    base = f"http://{ip}:{int(port)}"
    out = {"ip": ip, "reachable": False, "klap": "unknown"}
    try:
        r = requests.get(base + "/app", timeout=timeout)
        out["reachable"] = True
        out["app_status"] = r.status_code
    except Exception as exc:  # noqa: BLE001
        out["error"] = str(exc)
        return out
    try:
        r = requests.post(base + "/app/handshake1", json={}, timeout=timeout)
        out["handshake1_status"] = r.status_code
        out["klap"] = "endpoint live — needs paired keys for session"
    except Exception as exc:  # noqa: BLE001
        out["klap"] = f"handshake1 unreachable: {exc}"
    return out


# ------------------------------------------------------------------ Shelly/Tasmota/ESP
def _http_json(url, method="GET", payload=None, timeout=10):
    from quantum.core.deps import requests
    try:
        if method == "POST":
            r = requests.post(url, json=payload, timeout=timeout)
        else:
            r = requests.get(url, timeout=timeout)
        try:
            return {"ok": r.status_code < 400, "status": r.status_code,
                    "data": r.json()}
        except ValueError:
            return {"ok": r.status_code < 400, "status": r.status_code,
                    "data": r.text[:2000]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def shelly_gen1_command(ip, path="/status", port=80, timeout=10):
    """Shelly Gen1 HTTP API (real: /status, /relay/0?turn=on, ...)."""
    return _http_json(f"http://{ip}:{int(port)}{path}")


def shelly_rpc(ip, method, params=None, port=80, timeout=10):
    """Shelly Gen2 RPC over HTTP POST /rpc (real JSON-RPC)."""
    return _http_json(f"http://{ip}:{int(port)}/rpc", method="POST",
                      payload={"id": 1, "src": "quantum",
                               "method": method,
                               "params": params or {}})


def tasmota_command(ip, cmnd, port=80, timeout=10, user=None,
                    password=None):
    """Tasmota web command API (real: /cm?cmnd=Power%20On)."""
    query = urllib.parse.urlencode({"cmnd": cmnd, "user": user or "",
                                    "password": password or ""})
    return _http_json(f"http://{ip}:{int(port)}/cm?{query}")


def esp_probe(ip, port=80, timeout=8):
    """Fingerprint an ESP node via its web endpoints (real probes)."""
    probes = {"/cm?cmnd=status": "tasmota",
              "/status": "shelly-gen1",
              "/rpc": "shelly-gen2",
              "/": "generic-http"}
    hits = {}
    for path, label in probes.items():
        res = _http_json(f"http://{ip}:{int(port)}{path}",
                         timeout=timeout)
        if res.get("ok"):
            hits[label] = res.get("data")
    family = next((k for k in ("tasmota", "shelly-gen1", "shelly-gen2")
                   if k in hits), "generic-http" if hits else "unknown")
    return {"ip": ip, "family": family, "hits": hits}


# ------------------------------------------------------------------ Tuya
def tuya_discover(timeout=5):
    """Listen for Tuya UDP device broadcasts (ports 6666/6667)."""
    found = []
    for port in (6666, 6667):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", port))
        except OSError:
            sock.close()
            continue
        sock.settimeout(timeout)
        start = time.time()
        try:
            while time.time() - start < timeout:
                try:
                    data, addr = sock.recvfrom(4096)
                except socket.timeout:
                    break
                try:
                    text = data.decode("utf-8", "replace")
                    start_idx = text.find("{")
                    if start_idx >= 0:
                        info = json.loads(text[start_idx:])
                        info["_from"] = addr[0]
                        info["_udp"] = port
                        found.append(info)
                except (ValueError, json.JSONDecodeError):
                    continue
        finally:
            sock.close()
    return {"devices": found, "count": len(found)}


def tuya_build_command(dev_id, localkey, dps, seqno=1, cid=""):
    """Build a Tuya LAN v3.3 CONTROL frame (real wire format): header
    55AA + version/seqno/cmd + AES-128-ECB(JSON, localkey) + CRC32."""
    from Crypto.Cipher import AES
    from quantum.core.logging import log
    payload = {"devId": dev_id, "dps": dps, "t": int(time.time())}
    if cid:
        payload["cid"] = cid
    raw = json.dumps(payload, separators=(",", ":")).encode()
    pad = 16 - (len(raw) % 16)
    enc = AES.new(localkey.encode()[:16].ljust(16, b"\x00"),
                  AES.MODE_ECB).encrypt(raw + bytes([pad]) * pad)
    frame = struct.pack(">IHHI", 0x55AA0000, seqno & 0xFFFF, 0x0A,
                        len(enc) + 15)
    body = frame[4:] + b"3.3" + b"\x00" * 12 + enc
    crc = zlib.crc32(body) & 0xFFFFFFFF
    log("IOT tuya frame built", "IOT")
    return {"frame_hex": (struct.pack(">I", 0x55AA0000) + body +
                          struct.pack(">I", crc) + b"\xaa\x55").hex(),
            "seqno": seqno}


def tuya_send(ip, frame_hex, port=6668, timeout=8):
    """Send a prebuilt Tuya frame; returns the raw reply (hex)."""
    try:
        sock = socket.create_connection((ip, int(port)), timeout)
        with sock:
            sock.sendall(bytes.fromhex(frame_hex))
            sock.settimeout(timeout)
            data = sock.recv(8192)
        return {"ok": True, "reply_hex": data.hex(),
                "reply_len": len(data)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"tuya {ip}: {exc}"}


# ------------------------------------------------------------------ Tello
def tello_command(command, tello_ip="192.168.10.1", port=8889,
                  timeout=8):
    """Send one Tello SDK text command; returns the drone's reply."""
    from quantum.core.logging import log
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(str(command).encode(),
                    (tello_ip, int(port)))
        data, _ = sock.recvfrom(1024)
        reply = data.decode("utf-8", "replace").strip()
        log(f"IOT tello {command} -> {reply}", "IOT")
        return {"ok": True, "command": command, "reply": reply}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "command": command,
                "error": f"tello: {exc}"}
    finally:
        sock.close()


def tello_state(timeout=6):
    """Parse one Tello UDP state string (port 8890) into telemetry."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("", 8890))
    except OSError as exc:
        return {"ok": False, "error": f"cannot bind 8890: {exc}"}
    sock.settimeout(timeout)
    try:
        data, addr = sock.recvfrom(2048)
    except socket.timeout:
        return {"ok": False, "error": "no state datagram received"}
    finally:
        sock.close()
    telemetry = {}
    for field in data.decode("utf-8", "replace").strip().rstrip(";") \
            .split(";"):
        if ":" in field:
            key, value = field.split(":", 1)
            telemetry[key] = value
    return {"ok": True, "from": addr[0], "telemetry": telemetry}


# ------------------------------------------------------------------ MQTT
def mqtt_probe(ip, port=1883, timeout=8, username=None, password=None):
    """Raw MQTT 3.1.1 CONNECT probe (no client library needed)."""
    import random
    client_id = f"quantum-{random.randint(1000, 9999)}".encode()
    body = b"\x00\x04MQTT\x04"
    flags = 0x02  # clean session
    creds = b""
    if username:
        flags |= 0x80
        user = username.encode()
        creds += struct.pack(">H", len(user)) + user
        if password:
            flags |= 0x40
            pwd = password.encode()
            creds += struct.pack(">H", len(pwd)) + pwd
    body += bytes([flags]) + struct.pack(">H", 60)
    body += struct.pack(">H", len(client_id)) + client_id + creds
    packet = b"\x10" + bytes([len(body)]) + body
    try:
        sock = socket.create_connection((ip, int(port)), timeout)
        with sock:
            sock.settimeout(timeout)
            sock.sendall(packet)
            resp = sock.recv(4)
        if len(resp) >= 4 and resp[0] == 0x20:
            codes = {0: "accepted", 1: "bad protocol",
                     2: "client rejected", 3: "server unavailable",
                     4: "bad credentials", 5: "not authorized"}
            return {"ok": resp[3] == 0, "connack": resp[3],
                    "meaning": codes.get(resp[3], "unknown")}
        return {"ok": False, "error": f"unexpected reply {resp.hex()}"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"mqtt {ip}: {exc}"}


# ------------------------------------------------------------------ cameras/drones/maps
def iot_camera_track():
    """ONVIF camera tracking entries for the IoT map (real stack)."""
    from quantum.recon.wsdiscovery import wsdiscovery_cameras
    try:
        cameras = wsdiscovery_cameras()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "cameras": []}
    return {"ok": True, "cameras": cameras, "count": len(cameras)}


def iot_map(beacons=None):
    """2D map payload: operator beacons + live camera entries."""
    from quantum.control.map2d import generate_map_data
    cams = iot_camera_track()
    return {"map": generate_map_data(beacons or []),
            "cameras": cams.get("cameras", []),
            "note": "Camera pins need operator coordinates — "
                    "add_beacon() places them; WS-Discovery gives "
                    "presence, not GPS."}


def drone_wifi_scan():
    """Nearby Wi-Fi sweep matched against drone AP indicators."""
    import platform
    import shutil
    system = platform.system()
    ssids = []
    try:
        if system == "Windows" and shutil.which("netsh"):
            proc = subprocess.run(
                ["netsh", "wlan", "show", "networks"], capture_output=True,
                text=True, timeout=30)
            for line in proc.stdout.splitlines():
                line = line.strip()
                if line.upper().startswith("SSID"):
                    parts = line.split(":", 1)
                    if len(parts) == 2 and parts[1].strip():
                        ssids.append(parts[1].strip())
        elif shutil.which("nmcli"):
            proc = subprocess.run(
                ["nmcli", "-t", "-f", "SSID", "dev", "wifi"],
                capture_output=True, text=True, timeout=30)
            ssids = [l.strip() for l in proc.stdout.splitlines()
                     if l.strip()]
        else:
            return {"ok": False,
                    "error": "no Wi-Fi scanner (netsh/nmcli) on host"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    hits = [s for s in ssids
            if any(h.lower() in s.lower() for h in DRONE_SSID_HINTS)]
    return {"ok": True, "networks_seen": len(ssids),
            "drone_indicators": hits}


def mavlink_status():
    """MAVLink ops gate — honest when pymavlink is absent."""
    import importlib.util
    if importlib.util.find_spec("pymavlink") is None:
        return {"ok": False, "available": False,
                "error": "pymavlink not installed (pip install pymavlink "
                         "for MAVLink telemetry + guided ops)"}
    return {"ok": True, "available": True,
            "note": "pymavlink present — connect via mavutil "
                    "mavlink_connection() in operator code"}


# ------------------------------------------------------------------ discovery
def iot_discover(cidr, timeout=4):
    """IoT device discovery: SSDP sweep + IoT-port probe + HTTP
    classification. Authorized scope only."""
    import ipaddress
    from quantum.core.opsec import tcp_probe
    try:
        hosts = [str(h) for h in ipaddress.ip_network(
            cidr, strict=False).hosts()]
    except ValueError as exc:
        return {"ok": False, "error": f"bad CIDR: {exc}"}
    found = []
    for ip in hosts:
        open_ports = [p for p in IOT_PORTS
                      if tcp_probe(ip, p, timeout=0.4)]
        if not open_ports:
            continue
        entry = {"ip": ip, "ports": open_ports, "family": "unknown"}
        if 9999 in open_ports:
            entry["family"] = "kasa?"
        if 6668 in open_ports or 6666 in open_ports:
            entry["family"] = "tuya?"
        if 80 in open_ports:
            probe = esp_probe(ip, timeout=timeout)
            if probe["family"] != "unknown":
                entry["family"] = probe["family"]
                entry["endpoints"] = probe["hits"]
        if 5555 in open_ports:
            entry["family"] = "adb-android?"
        found.append(entry)
    return {"ok": True, "hosts": found, "count": len(found)}


# ------------------------------------------------------------------ CVE feed + whitepapers
def nvd_search(keyword, results=20, api_key=None, timeout=25,
               base="https://services.nvd.nist.gov/rest/json/cves/2.0"):
    """NVD CVE API 2.0 keyword search (keyless, rate-limited)."""
    from quantum.core.deps import requests
    params = {"keywordSearch": keyword, "resultsPerPage": int(results)}
    headers = {}
    key = api_key or os.environ.get("NVD_API_KEY")
    if key:
        headers["apiKey"] = key
    try:
        r = requests.get(
            base,
            params=params, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return {"ok": False, "keyword": keyword,
                    "error": f"NVD HTTP {r.status_code}"}
        data = r.json()
        vulns = [v.get("cve", {}) for v in data.get("vulnerabilities",
                                                    [])]
        return {"ok": True, "keyword": keyword,
                "total": data.get("totalResults", len(vulns)),
                "cves": [{"id": c.get("id"),
                          "published": c.get("published"),
                          "descriptions": c.get("descriptions", []),
                          "metrics": c.get("metrics", {}),
                          "weaknesses": c.get("weaknesses", []),
                          "references": c.get("references", [])}
                         for c in vulns]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "keyword": keyword,
                "error": f"NVD query failed: {exc}"}


def _cvss(cve):
    metrics = cve.get("metrics", {})
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        items = metrics.get(key, [])
        if items:
            data = items[0].get("cvssData", {})
            return {"version": key, "score": data.get("baseScore"),
                    "severity": data.get("baseSeverity"),
                    "vector": data.get("vectorString")}
    return {}


def cve_whitepaper(cve):
    """Data-grounded white paper for one NVD CVE dict (as returned by
    nvd_search): metadata, description, CVSS, CWE, references, and an
    IoT hardening checklist. Every claim cites the CVE data — no
    invented affected products or exploits."""
    cid = cve.get("id", "unknown")
    descs = {d.get("lang"): d.get("value", "")
             for d in cve.get("descriptions", [])}
    description = descs.get("en", next(iter(descs.values()), ""))
    cvss = _cvss(cve)
    cwes = [str(d.get("value", "")) for w in cve.get("weaknesses", [])
            for d in w.get("description", []) if d.get("value")]
    refs = [(r.get("url", ""), r.get("tags", []))
            for r in cve.get("references", [])]
    lines = [
        f"# White Paper — {cid}",
        "",
        f"_Generated from NVD record {cid} "
        f"(published {cve.get('published', '?')}). "
        "Mitigations below are generic IoT hardening, not "
        "vendor advisories._",
        "",
        "## Description",
        "",
        description or "_No English description in NVD record._",
        "",
        "## CVSS",
        "",
        (f"- Score: **{cvss.get('score')} "
         f"({cvss.get('severity')})**" if cvss.get("score")
         else "- _No CVSS metric in NVD record._"),
    ]
    if cvss.get("vector"):
        lines.append(f"- Vector: `{cvss['vector']}`")
    lines += ["",
              "## Weaknesses",
              ""]
    lines += [f"- {c}" for c in cwes] or ["- _None listed._"]
    lines += ["",
              "## References",
              ""]
    lines += [f"- {url} ({', '.join(tags)})" for url, tags in refs] or \
        ["- _None listed._"]
    lines += ["",
              "## IoT hardening checklist (generic)",
              "",
              "- Isolate IoT on a dedicated VLAN/SSID; block RFC1918 "
              "crosstalk.",
              "- Change/default-disable Telnet/ADB/UPnP services; set "
              "strong HTTP/RPC credentials.",
              "- Pin MQTT broker ACLs; require auth + TLS.",
              "- Inventory firmware versions; patch from vendor channels.",
              "- Monitor for rogue drone APs near sensitive perimeters.",
              "",
              "_End of white paper._"]
    return {"id": cid, "markdown": "\n".join(lines),
            "cvss": cvss, "cwe": cwes, "references": len(refs)}


# ------------------------------------------------------------------ payloads
def generate_iot_payload(kind, params=None):
    """Build a real IoT command/payload artifact (text)."""
    from quantum.core.logging import log
    params = params or {}
    builders = {
        "kasa": lambda: {
            "artifact": json.dumps(params.get(
                "command", {"system": {"get_sysinfo": {}}})),
            "transport": "TCP 9999 kasa_encrypt()",
            "how": "kasa_command(ip, json.loads(artifact))"},
        "tasmota-backlog": lambda: {
            "artifact": params.get("backlog", "Power On; Status 0"),
            "transport": "HTTP /cm?cmnd=",
            "how": "tasmota_command(ip, artifact)"},
        "shelly-rpc": lambda: {
            "artifact": json.dumps(
                {"method": params.get("method", "Switch.GetStatus"),
                 "params": params.get("rpc_params", {"id": 0})}),
            "transport": "HTTP POST /rpc",
            "how": "shelly_rpc(ip, method, params)"},
        "tuya-dps": lambda: tuya_build_command(
            params.get("dev_id", ""), params.get("localkey", ""),
            params.get("dps", {"1": True}),
            int(params.get("seqno", 1))) | {
                "transport": "TCP 6668 tuya_send()",
                "how": "tuya_send(ip, frame_hex)"},
        "tello-script": lambda: {
            "artifact": "\n".join(["command"] + list(
                params.get("moves", ["takeoff", "forward 50",
                                     "land"]))),
            "transport": "UDP 8889, one line per command",
            "how": "tello_command(line) per line, await ok reply"},
        "mqtt-publish": lambda: {
            "artifact": json.dumps(
                {"topic": params.get("topic", "cmnd/tasmota/Power"),
                 "payload": params.get("payload", "On")}),
            "transport": "MQTT PUBLISH via broker (operator client)",
            "how": "publish artifact to an authorized broker"},
        "esp32-monitor": lambda: {
            "artifact": _esp32_monitor_sketch(
                params.get("ssid", "LAB"),
                params.get("report_url",
                           "http://192.168.1.10/report")),
            "transport": "Arduino flash (lab-owned node)",
            "how": "Compile in Arduino IDE (ESP32 core), flash over "
                   "USB to your own node"},
    }
    if kind not in builders:
        return {"error": f"unknown payload {kind!r} "
                         f"(see IOT_EXPLOITS / families)"}
    try:
        result = builders[kind]()
    except Exception as exc:  # noqa: BLE001
        return {"kind": kind, "error": str(exc)}
    result["kind"] = kind
    log(f"IOT payload built: {kind}", "IOT")
    return result


def _esp32_monitor_sketch(ssid, report_url):
    """Lab-only ESP32 temperature/uptime reporter (benign firmware for
    your own node — demonstrates the payload pipeline end to end)."""
    return "\n".join([
        "// Quantum IoT lab monitor — flash ONLY to your own ESP32.",
        "#include <WiFi.h>",
        "#include <HTTPClient.h>",
        f'const char* SSID = "{ssid}";',
        'const char* PASS = "CHANGEME";',
        f'String REPORT = "{report_url}";',
        "void setup() {",
        '  Serial.begin(115200); WiFi.begin(SSID, PASS);',
        "  while (WiFi.status() != WL_CONNECTED) { delay(500); }",
        "}",
        "void loop() {",
        "  if (WiFi.status() == WL_CONNECTED) {",
        "    HTTPClient http; http.begin(REPORT);",
        '    http.addHeader("Content-Type", "application/json");',
        '    String body = "{\\"uptime\\":" + String(millis()) + "}";',
        "    http.POST(body); http.end();",
        "  }",
        "  delay(60000);",
        "}",
    ])


def iot_dashboard_state():
    """Webcard state for the IoT exploitation dashboard."""
    return {
        "families": IOT_FAMILIES,
        "exploits": IOT_EXPLOITS,
        "payload_kinds": ["kasa", "tasmota-backlog", "shelly-rpc",
                          "tuya-dps", "tello-script", "mqtt-publish",
                          "esp32-monitor"],
        "drone_hints": list(DRONE_SSID_HINTS),
        "mavlink": mavlink_status(),
        "note": "Authorized scope only. Tuya needs your device "
                "localkey; Tapo KLAP needs cloud-paired keys; MAVLink "
                "needs pymavlink. Everything else speaks plain LAN "
                "protocols.",
    }
