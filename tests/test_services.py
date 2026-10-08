"""Tests for quantum.brute.services — builders + loopback HTTP basic."""
import base64
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.brute.services import (  # noqa: E402
    HYDRA_PROTOCOLS,
    brute_http_basic,
    detect_hydra,
    hydra_command,
    hydra_run,
    services_dashboard_state,
)


class _Basic(BaseHTTPRequestHandler):
    USER, PASS = "op", "s3cret"
    def do_GET(self):  # noqa: N802
        want = "Basic " + base64.b64encode(
            f"{self.USER}:{self.PASS}".encode()).decode()
        if self.headers.get("Authorization") == want:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="t"')
            self.end_headers()

    def log_message(self, *a):
        pass


@pytest.fixture()
def basic_url():
    srv = HTTPServer(("127.0.0.1", 0), _Basic)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}/"
    srv.shutdown()


def test_http_basic_hit_and_miss(basic_url):
    hit = brute_http_basic(basic_url, users=["op"],
                           wordlist=["nope", "s3cret"])
    assert len(hit["hits"]) == 1
    assert hit["hits"][0]["password"] == "s3cret"
    assert hit["tried"] == 2
    miss = brute_http_basic(basic_url, users=["op"], wordlist=["nope"])
    assert miss["hits"] == []


def test_hydra_command_ssh():
    argv = hydra_command("10.0.0.5", "ssh", user="root",
                         wordlist="w.txt")
    assert argv[:2] == ["hydra", "-l"] and "root" in argv
    assert "-P" in argv and "ssh" in argv


def test_hydra_command_rejects_bad_protocol():
    with pytest.raises(ValueError):
        hydra_command("h", "gopher", user="u", wordlist="w")


def test_hydra_run_honest_when_absent():
    if detect_hydra() is None:
        r = hydra_run("10.0.0.5", "ssh", user="root",
                      wordlist="w.txt")
        assert r.get("error") and r.get("argv")


def test_dashboard_state_shape():
    s = services_dashboard_state()
    assert set(HYDRA_PROTOCOLS) <= set(s["hydra_protocols"])
    assert "ftp" in s["embedded_engines"]
