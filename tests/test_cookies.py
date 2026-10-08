"""Tests for quantum.postexploit.cookies — jar CRUD + session replay."""
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

import quantum.postexploit.cookies as cookies  # noqa: E402


@pytest.fixture()
def lootdir(tmp_path, monkeypatch):
    monkeypatch.setattr(cookies, "LOOT_DIR", str(tmp_path))
    return tmp_path


class _CookieSrv(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if "sessionid=good" in (self.headers.get("Cookie") or ""):
            self.send_response(200)
            self.send_header("Set-Cookie", "sessionid=rotated; Path=/")
            self.end_headers()
            self.wfile.write(b"welcome back")
        else:
            self.send_response(401)
            self.end_headers()

    def log_message(self, *a):
        pass


@pytest.fixture()
def app_url():
    srv = HTTPServer(("127.0.0.1", 0), _CookieSrv)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}/"
    srv.shutdown()


def test_parse_netscape(lootdir):
    recs = cookies.parse_netscape(
        "#HttpOnly_.example.com\tTRUE\t/\tTRUE\t0\tsessionid\tabc123\n"
        ".example.com\tTRUE\t/\tFALSE\t0\tprefs\tlight\n"
        "garbage-line\n")
    assert len(recs) == 2
    assert recs[0]["httpOnly"] is True and recs[0]["value"] == "abc123"


def test_save_load_delete_roundtrip(lootdir):
    r = cookies.save_jar("h1", [{"name": "a", "value": "1"},
                                {"name": "", "value": "x"}])
    assert r["count"] == 1
    assert cookies.load_jar("h1")[0]["name"] == "a"
    assert cookies.cookie_hosts() == [{"host": "h1", "count": 1}]
    assert cookies.delete_jar("h1")["existed"] is True
    assert cookies.load_jar("h1") == []


def test_import_merges(lootdir):
    cookies.save_jar("h1", [{"name": "a", "value": "1"}])
    r = cookies.import_jar(
        "h1", ".x.com\tTRUE\t/\tFALSE\t0\tsessionid\ts3\n")
    assert r["count"] == 2
    bad = cookies.import_jar("h1", "not json", fmt="json")
    assert "error" in bad


def test_replay_valid_and_invalid(lootdir, app_url):
    cookies.save_jar("h1", [{"name": "sessionid", "value": "good",
                             "domain": "127.0.0.1"}])
    ok = cookies.replay_session("h1", app_url)
    assert ok["valid"] is True and ok["status"] == 200
    assert ok["session_rotated"] == ["sessionid"]
    cookies.save_jar("h1", [{"name": "sessionid", "value": "stale"}])
    bad = cookies.replay_session("h1", app_url)
    assert bad["valid"] is False and bad["status"] == 401
    assert "error" in cookies.replay_session("ghost", app_url)


def test_cookie_routes(lootdir):
    from quantum.c2.app import make_c2
    c = make_c2({"default": "# agent"}).test_client()
    assert c.get("/api/cookies/state").status_code == 200
    assert c.post("/api/cookies/h9",
                  json={"cookies": [{"name": "a",
                                     "value": "b"}]}).status_code == 200
    assert c.get("/api/cookies/h9").get_json()["cookies"][0]["name"] \
        == "a"
    assert c.post("/api/cookies/h9/replay", json={}).status_code == 400
    assert c.get("/api/loot/state").status_code == 200
    assert b"Loot" in c.get("/dash").data
    assert c.delete("/api/cookies/h9").status_code == 200
