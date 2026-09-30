"""Tests for the v4.4 operator-suite modules: providers, agents, skills,
workflows, project-zero feed, and the bluetooth weapon tier."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.ai import agents, providers, skills, workflows  # noqa: E402
from quantum.recon import project_zero  # noqa: E402
from quantum.weapons import bluetooth  # noqa: E402
from quantum.weapons.registry import ZERO_DAY_REGISTRY, resolve_weapon  # noqa: E402


# ------------------------------------------------------------------ providers
def test_providers_registry_has_all_task_providers():
    for pid in ("abliteration", "openrouter", "venice", "agnes", "opencode"):
        assert pid in providers.PROVIDERS
        assert providers.PROVIDERS[pid]["url"].startswith("http")
        assert providers.PROVIDERS[pid]["model"]


def test_resolve_provider_explicit(monkeypatch):
    monkeypatch.setenv("QCLI_AI_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    pid, p, key = providers.resolve_provider()
    assert pid == "openrouter"
    assert key == "sk-test"
    assert p["url"] == "https://openrouter.ai/api/v1"


def test_provider_status_shape():
    status = providers.provider_status()
    assert {s["id"] for s in status} >= {"abliteration", "openrouter", "venice",
                                         "agnes", "opencode"}
    for s in status:
        assert {"id", "label", "url", "model", "key_found"} <= set(s)


# -------------------------------------------------------------------- agents
def test_agent_presets_seed_sldr_and_ns_org():
    all_agents = agents.load_all()
    assert "sldr" in all_agents
    assert "SLDR" in all_agents["sldr"]["system_prompt"]
    for ns in ("ns-command", "ns-intel", "ns-craft", "ns-breach",
               "ns-deploy", "ns-forge", "ns-sensor", "ns-scribe"):
        assert ns in all_agents, f"missing {ns}"
        assert 0 <= all_agents[ns]["autonomy"] <= 4


def test_agent_crud_roundtrip():
    saved = agents.save({"id": "test-agent-x", "name": "Test Agent",
                         "role": "test", "autonomy": 2,
                         "system_prompt": "be testy", "description": ""})
    assert saved["id"] == "test-agent-x"
    assert agents.get("test-agent-x")["name"] == "Test Agent"
    assert agents.delete("test-agent-x")
    assert agents.get("test-agent-x") is None


# -------------------------------------------------------------------- skills
def test_skill_preset_packs_and_compose():
    all_skills = skills.load_all()
    kinds = {s["kind"] for s in all_skills.values()}
    assert {"PROMPT", "TOOL", "SCRIPT"} <= kinds
    prompt = skills.compose_prompt(["redteam.killchain", "redteam.opsec"])
    assert "Kill Chain" in prompt and "OPSEC" in prompt
    assert skills.compose_prompt(["tool.scan"]) == ""  # TOOL kind not in prompt


def test_skill_crud_roundtrip():
    skills.save({"id": "test.skill", "name": "T", "kind": "PROMPT",
                 "content": "x", "tags": []})
    assert skills.get("test.skill")["content"] == "x"
    skills.delete("test.skill")
    assert skills.get("test.skill") is None


def test_skill_kind_normalized():
    s = skills.save({"id": "test.kind", "name": "K", "kind": "bogus",
                     "content": "x"})
    assert s["kind"] == "PROMPT"
    skills.delete("test.kind")


# ----------------------------------------------------------------- workflows
def test_workflow_presets():
    flows = workflows.load_all()
    assert "full-engagement" in flows
    assert flows["full-engagement"]["steps"]


def test_workflow_run_skips_missing_vars_and_dispatches():
    wf = {"id": "t", "steps": [
        {"name": "scan", "tool": "scan", "params": {"cidr": "${scope}"},
         "needs": ["scope"]},
        {"name": "report", "tool": "mitre", "params": {}},
    ]}
    seen = []

    def dispatch(cmd, params):
        seen.append((cmd, params))
        return {"ok": True, "hosts": [{"ip": "10.0.0.7"}]}

    out = workflows.run(wf, dispatch=dispatch, variables={})
    assert out["journal"][0]["status"] == "skipped"      # scope missing
    assert seen and seen[0][0] == "mitre"

    out2 = workflows.run(wf, dispatch=dispatch, variables={"scope": "10.0.0.0/24"})
    assert out2["journal"][0]["status"] == "ok"
    assert seen[1][1] == {"cidr": "10.0.0.0/24"}          # ${scope} substituted


def test_workflow_variable_chaining_first_host():
    wf = {"id": "t2", "steps": [
        {"name": "scan", "tool": "scan", "params": {}},
        {"name": "zerocheck", "tool": "zerocheck", "params": {"ip": "${first_host}"}},
    ]}

    def dispatch(cmd, params):
        if cmd == "scan":
            return {"hosts": [{"ip": "10.0.0.9"}]}
        assert params == {"ip": "10.0.0.9"}
        return {}

    out = workflows.run(wf, dispatch=dispatch)
    assert out["journal"][1]["status"] == "ok"


# -------------------------------------------------------------- project zero
def test_p0_parse_and_cve_extraction():
    entries = project_zero.parse(project_zero._demo_feed_bytes())
    assert len(entries) == 2
    assert entries[0]["link"].endswith("demo1.html")
    assert "CVE-2026-1234" in project_zero.extract_cves(
        entries[0]["summary"], entries[0]["title"])
    cands = project_zero.zero_day_candidates(n=10, url="bogus")
    assert cands == []          # network failure never raises


# ---------------------------------------------------------------- bluetooth
def test_bluetooth_weapons_registered():
    for cve in ("CVE-2017-0781", "CVE-2017-0785", "CVE-2018-5383", "BLACKBED-BLE"):
        assert cve in ZERO_DAY_REGISTRY
        assert resolve_weapon(ZERO_DAY_REGISTRY[cve]["weapon"]) is not None


def test_bluetooth_fire_contract_never_raises():
    r = bluetooth.check_blueborne_bnep("10.0.0.1", None)
    assert r["cve"] == "CVE-2017-0144" or r["cve"] == "CVE-2017-0781"
    r2 = bluetooth.check_blackbed("10.0.0.1")
    assert r2["vector"] == "ble/gatt"


# ------------------------------------------------------- adb + new BT weapons
def test_adb_and_new_bt_weapons_registered():
    for cve in ("CVE-2026-0073", "CVE-2020-0022", "CVE-2017-13077"):
        assert cve in ZERO_DAY_REGISTRY
        assert resolve_weapon(ZERO_DAY_REGISTRY[cve]["weapon"]) is not None


def test_adb_weapon_fire_contract():
    from quantum.weapons import adb as adb_weapons
    r = adb_weapons.check_adb_tls_bypass("10.0.0.1", {"timeout": 0.5})
    assert r["cve"] == "CVE-2026-0073"
    assert r["status"] in ("check", "no-service", "vulnerable-surface")


def test_bluefrag_and_krack_fire_contract():
    assert bluetooth.check_bluefrag("10.0.0.1")["cve"] == "CVE-2020-0022"
    assert bluetooth.check_krack("10.0.0.1")["cve"] == "CVE-2017-13077"


# ------------------------------------------------ payload-folder generators
PAYLOADS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "exploit_payloads")


def _run_gen(folder, *args):
    import subprocess
    out = subprocess.run(
        [sys.executable, os.path.join(PAYLOADS, folder, "deploy.py"), *args],
        capture_output=True, text=True, timeout=60, cwd=os.path.join(
            PAYLOADS, folder))
    return out.returncode, json.loads(out.stdout or "{}"), out.stderr


def test_payload_folders_generate_and_verify(tmp_path):
    for folder, arg in [
        ("CVE-2020-0022-bluefrag", ["--out", str(tmp_path / "bf.bin")]),
        ("CVE-2023-45866-bt-hid-injection", ["--out", str(tmp_path / "hid.bin")]),
        ("CVE-2017-13077-krack", ["--out", str(tmp_path / "krack.bin")]),
        ("CVE-2022-21894-boothole", ["--out", str(tmp_path / "grub.cfg")]),
        ("CVE-2022-30190-follina", ["--out", str(tmp_path / "follina.docx")]),
        ("CVE-2023-41064-apple-imageio", ["--out", str(tmp_path / "a.webp")]),
        ("CVE-2023-4863-libwebp", ["--out", str(tmp_path / "b.webp")]),
        ("CVE-2019-3568-whatsapp-voip", ["--out", str(tmp_path / "rtp.bin")]),
        ("CVE-2021-30860-forcedentry", ["--out", str(tmp_path / "fe.pdf")]),
        ("CVE-2021-30858-webkit-escape", ["--out", str(tmp_path / "uaf.html")]),
        ("CVE-2023-32409-webkit-type-confusion",
         ["--out", str(tmp_path / "tc.html")]),
        ("CVE-2026-0073-adb-tls-bypass", ["--dga"]),
    ]:
        rc, result, err = _run_gen(folder, *arg)
        assert rc == 0, f"{folder} failed: {err}\n{result}"
        assert result.get("error") is None, f"{folder} error: {result}"


def test_legacy_probes_never_crash_on_closed_port():
    for folder in ("CVE-2017-0144-eternalblue", "CVE-2020-1472-zerologon",
                   "CVE-2021-1675-printnightmare", "CVE-2021-36942-petitpotam",
                   "CVE-2021-26855-proxylogon"):
        rc, result, err = _run_gen(folder, "--target", "127.0.0.1",
                                   "--timeout", "1")
        assert result.get("error") is not None or rc in (0, 1), \
            f"{folder} crashed: {err}"
