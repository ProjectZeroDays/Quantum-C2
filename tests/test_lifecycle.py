"""Tests for quantum.overlord.lifecycle — chained 7-phase lifecycle."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.overlord.lifecycle import (  # noqa: E402
    LIFE_CYCLE,
    lifecycle_dashboard_state,
    loot_stats,
    phase_agent,
    phase_loot,
    phase_phish,
    phase_reuse,
    run_lifecycle,
)


def _stub(status="ok", summary="stub", data=None):
    def fn(ctx, dispatch=None, ai=None):
        return {"status": status, "summary": summary,
                "data": data or {}}
    return fn


def test_chain_has_seven_phases_in_order():
    assert [p["id"] for p in LIFE_CYCLE] == [
        "osint", "recon", "phish", "exploit", "postex", "loot",
        "reuse"]
    assert all(p["agent_role"] and p["tools"] for p in LIFE_CYCLE)


def test_phase_agent_falls_back_to_sldr():
    assert phase_agent("nonexistent-role-xyz") == "sldr"


def test_run_chains_journal_with_stub_runners(tmp_path):
    runners = {p["id"]: _stub(summary=f"did-{p['id']}")
               for p in LIFE_CYCLE}
    seen = []
    res = run_lifecycle("10.9.9.0/30", runners=runners,
                        loot_dir=str(tmp_path),
                        on_phase=seen.append)
    assert [j["phase"] for j in res["journal"]] == [
        p["id"] for p in LIFE_CYCLE]
    assert all(j["agent"] for j in res["journal"])
    assert len(seen) == 7
    assert res["loot_creds"] == []


def test_run_survives_phase_exceptions(tmp_path):
    def boom(ctx, dispatch=None, ai=None):
        raise RuntimeError("nope")
    runners = {p["id"]: _stub() for p in LIFE_CYCLE}
    runners["recon"] = boom
    res = run_lifecycle("10.9.9.1", runners=runners,
                        loot_dir=str(tmp_path))
    recon = next(j for j in res["journal"]
                 if j["phase"] == "recon")
    assert recon["status"] == "error"
    assert len(res["journal"]) == 7


def test_phish_stages_without_launch():
    ctx = {"scope": "example.com", "variables": {}, "loot_creds": [],
           "loot_dir": "x", "artifacts": {}}
    r = phase_phish(ctx)
    assert r["status"] == "ok" and r["data"]["launched"] is False


def test_loot_reuse_interconnection(tmp_path):
    host = tmp_path / "h1"
    host.mkdir()
    (host / "creds.txt").write_text(
        "breach dump\nUsername: operator Password: L00tP@ss!\n")
    ctx = {"scope": "t", "variables": {}, "loot_creds": [],
           "loot_dir": str(tmp_path), "artifacts": {}}
    r = phase_loot(ctx)
    assert ctx["loot_creds"] == ["L00tP@ss!"], r
    import hashlib as _h
    ntlm = _h.new("md4", "L00tP@ss!".encode("utf-16le")).hexdigest() \
        if "md4" in _h.algorithms_available else None
    if ntlm is None:
        from quantum.brute.hashes import compute_hash
        ntlm = compute_hash("L00tP@ss!", fmt="ntlm")
    ctx["variables"] = {"hash_targets": [ntlm], "hash_fmt": "ntlm"}
    r2 = phase_reuse(ctx, dispatch=lambda c, p: {"ok": True})
    assert r2["data"]["cracked"]["hits"][0]["password"] == "L00tP@ss!"


def test_loot_stats_counts(tmp_path):
    host = tmp_path / "h2"
    host.mkdir()
    (host / "parsed.txt").write_text("a:b\nc:d\nnope\n")
    assert loot_stats(str(tmp_path)) == {"hosts": 1, "parsed_creds": 2}


def test_dashboard_state_shape():
    s = lifecycle_dashboard_state()
    assert s["chain"].startswith("osint")
    assert set(s["agents"]) >= {"intel", "breach", "operator"}
    assert "hosts" in s["loot"]


def test_lifecycle_routes():
    from quantum.c2.app import make_c2
    c = make_c2({"default": "# agent"}).test_client()
    assert len(c.get("/api/lifecycle/phases").get_json()) == 7
    st = c.get("/api/lifecycle/state").get_json()
    assert st["chain"].startswith("osint")
    assert c.post("/api/lifecycle/run", json={}).status_code == 400
    assert b"Lifecycle" in c.get("/dash").data
