"""Tests for quantum.control.iot — real LAN protocols on loopback."""
import json
import os
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.control.iot import (  # noqa: E402
    IOT_EXPLOITS,
    IOT_FAMILIES,
    cve_whitepaper,
    drone_wifi_scan,
    esp_probe,
    generate_iot_payload,
    iot_dashboard_state,
    kasa_command,
    kasa_decrypt,
    kasa_encrypt,
    mavlink_status,
    mqtt_probe,
    nvd_search,
    shelly_gen1_command,
    shelly_rpc,
    tasmota_command,
    tello_command,
    tello_state,
    tuya_build_command,
    tuya_send,
)


def test_kasa_crypto_roundtrip():
    raw = json.dumps({"system": {"get_sysinfo": {}}}).encode()
    assert kasa_decrypt(kasa_encrypt(raw)) == raw


def _kasa_plug():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def serve():
        conn, _ = srv.accept()
        with conn:
            data = conn.recv(4096)
            cmd = json.loads(kasa_decrypt(data))
            assert "system" in cmd
            conn.sendall(kasa_encrypt(json.dumps(
                {"system": {"get_sysinfo": {"alias": "plug-1"}}}
            ).encode()))
        srv.close()

    threading.Thread(target=serve, daemon=True).start()
    return port


def test_kasa_command_loopback():
    res = kasa_command("127.0.0.1",
                       {"system": {"get_sysinfo": {}}},
                       port=_kasa_plug())
    assert res["ok"] is True
    assert res["reply"]["system"]["get_sysinfo"]["alias"] == "plug-1"


class _IotHttp(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/cm?"):
            self._json({"Status": {"Power": "ON"}})
        elif self.path == "/status":
            self._json({"relays": [{"ison": False}]})
        elif self.path == "/":
            self._json({"app": "esphome"})
        else:
            self._json({"error": "nf"}, code=404)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        assert body["method"] == "Switch.GetStatus"
        self._json({"result": {"output": False}})

    def log_message(self, *a):
        pass


def _http_port():
    srv = HTTPServer(("127.0.0.1", 0), _IotHttp)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_port


def test_tasmota_shelly_esp_loopback():
    import quantum.control.iot as iot
    port = _http_port()
    real = iot._http_json

    def patched(url, method="GET", payload=None, timeout=10):
        return real(url.replace(":80/", f":{port}/"), method, payload,
                    timeout)

    iot._http_json, saved = patched, iot._http_json
    try:
        assert tasmota_command("127.0.0.1", "Power On",
                               port=80)["data"]["Status"]["Power"] == "ON"
        assert shelly_gen1_command("127.0.0.1")["data"]["relays"] \
            == [{"ison": False}]
        assert shelly_rpc("127.0.0.1", "Switch.GetStatus",
                          {"id": 0})["data"]["result"]["output"] is False
        probe = esp_probe("127.0.0.1")
        assert probe["family"] == "tasmota"
    finally:
        iot._http_json = saved


def test_tuya_frame_structure():
    built = tuya_build_command("dev123", "0123456789abcdef",
                               {"1": True, "2": 50}, seqno=7)
    frame = bytes.fromhex(built["frame_hex"])
    assert frame[:2] == b"\x55\xaa" and frame[-2:] == b"\xaa\x55"
    assert b"3.3" in frame and built["seqno"] == 7


def test_tuya_send_loopback():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def serve():
        conn, _ = srv.accept()
        with conn:
            data = conn.recv(4096)
            assert data[:2] == b"\x55\xaa"
            conn.sendall(b"\x55\xaa\x00\x00" + data[4:20])
        srv.close()

    threading.Thread(target=serve, daemon=True).start()
    built = tuya_build_command("d", "k" * 16, {"1": False})
    res = tuya_send("127.0.0.1", built["frame_hex"], port=port)
    assert res["ok"] is True and res["reply_len"] > 0


def test_tello_command_loopback():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]

    def serve():
        data, addr = sock.recvfrom(1024)
        assert data == b"command"
        sock.sendto(b"ok", addr)
        sock.close()

    threading.Thread(target=serve, daemon=True).start()
    res = tello_command("command", tello_ip="127.0.0.1", port=port)
    assert res == {"ok": True, "command": "command", "reply": "ok"}


def test_tello_state_parses():
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send():
        import time
        time.sleep(0.5)
        sender.sendto(b"bat:78;h:0;tof:10;",
                      ("127.0.0.1", 8890))

    threading.Thread(target=send, daemon=True).start()
    res = tello_state(timeout=5)
    sender.close()
    assert res["ok"] is True
    assert res["telemetry"]["bat"] == "78"


def test_mqtt_probe_loopback():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def serve():
        conn, _ = srv.accept()
        with conn:
            data = conn.recv(256)
            assert data[0] == 0x10 and b"MQTT" in data
            conn.sendall(b"\x20\x02\x00\x00")
        srv.close()

    threading.Thread(target=serve, daemon=True).start()
    res = mqtt_probe("127.0.0.1", port=port)
    assert res == {"ok": True, "connack": 0, "meaning": "accepted"}


def test_drone_wifi_shape_and_mavlink_gate():
    res = drone_wifi_scan()
    assert set(res) >= {"ok", "drone_indicators"} or "error" in res
    assert mavlink_status()["available"] is False


def test_nvd_error_path():
    res = nvd_search("tasmota", results=1, timeout=3,
                     base="http://127.0.0.1:9/cves/2.0")
    assert res["ok"] is False and res.get("error")


def test_whitepaper_from_fixture():
    cve = {"id": "CVE-2024-0001", "published": "2024-01-01",
           "descriptions": [{"lang": "en",
                             "value": "Tasmota buffer overflow."}],
           "metrics": {"cvssMetricV31": [
               {"cvssData": {"baseScore": 9.8,
                             "baseSeverity": "CRITICAL",
                             "vectorString": "CVSS:3.1/AV:N"}}]},
           "weaknesses": [{"description": [
               {"value": "CWE-120"}]}],
           "references": [{"url": "https://example.com/a",
                           "tags": ["vendor"]}]}

    # NVD weakness shape
    cve["weaknesses"] = [{"description": [{"lang": "en",
                                            "value": "CWE-120"}]}]
    wp = cve_whitepaper(cve)
    assert wp["id"] == "CVE-2024-0001"
    assert "9.8" in wp["markdown"] and "CWE-120" in wp["markdown"]
    assert wp["references"] == 1


def test_payload_generator():
    assert "get_sysinfo" in generate_iot_payload("kasa")["artifact"]
    tel = generate_iot_payload("tello-script",
                               {"moves": ["takeoff", "land"]})
    assert tel["artifact"].splitlines()[0] == "command"
    esp = generate_iot_payload("esp32-monitor")["artifact"]
    assert "WiFi.begin" in esp and "CHANGEME" in esp
    assert "error" in generate_iot_payload("nope")


def test_state_and_routes():
    from quantum.c2.app import make_c2
    c = make_c2({"default": "# agent"}).test_client()
    st = c.get("/api/iot/state").get_json()
    assert len(st["families"]) == len(IOT_FAMILIES) == 10
    assert len(st["exploits"]) == len(IOT_EXPLOITS) == 15
    assert iot_dashboard_state()["families"][0]["id"] == "kasa"
    assert c.post("/api/iot/kasa", json={}).status_code == 400
    assert c.post("/api/iot/payload",
                  json={"kind": "kasa"}).status_code == 200
    assert c.post("/api/iot/whitepaper", json={}).status_code == 400
    assert b"IoT" in c.get("/dash").data
